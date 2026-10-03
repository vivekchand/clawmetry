"""Assistant text-only CLI and Anthropic streaming transports (no SDK needed)."""
from __future__ import annotations

import json
import http.client
import os
import signal
import subprocess
import tempfile
import threading
import urllib.error

from clawmetry.assistant_stream import BrokenStream, MAX_LINE, MAX_TEXT, http_response

CLI_SECONDS = 75
MAX_WIRE = 4 * 1024 * 1024


class ProviderFailure(ValueError):
    """Only fixed, locally selected diagnostics may use this public exception."""

    def __init__(self, message, status=502):
        self.message = message
        self.status = status
        super().__init__(message)


def http_failure(exc):
    if exc.code in (401, 403):
        return ProviderFailure("The provider rejected this API key. Check the key and its permissions.")
    if exc.code in (402, 429):
        return ProviderFailure("The provider's usage limit was reached. Check your provider billing or retry later.")
    return ProviderFailure("The AI provider is unavailable. Please retry shortly.")


def harness_failure():
    return ProviderFailure("Your Claude harness could not answer. Check its sign-in or usage limit and retry.")


class TextEvents:
    """Allowlist text blocks; never forward reasoning, tools or provider metadata."""

    def __init__(self):
        self.blocks = {}
        self.started = False
        self.stopped = False
        self.reason = None

    def take(self, event):
        if not isinstance(event, dict):
            raise BrokenStream()
        kind = event.get("type")
        if kind == "error":
            raise BrokenStream()
        if kind == "message_start":
            if self.started:
                raise BrokenStream()
            self.started = True
        elif kind == "content_block_start":
            if not self.started or self.stopped:
                raise BrokenStream()
            block = event.get("content_block")
            if not isinstance(block, dict):
                raise BrokenStream()
            index = event.get("index")
            if not isinstance(index, int) or isinstance(index, bool) or index in self.blocks:
                raise BrokenStream()
            self.blocks[index] = block.get("type")
            if block.get("type") == "text":
                return self._text(block.get("text", ""))
        elif kind == "content_block_delta":
            if not self.started or self.stopped:
                raise BrokenStream()
            delta = event.get("delta")
            if not isinstance(delta, dict):
                raise BrokenStream()
            if delta.get("type") == "text_delta":
                if self.blocks.get(event.get("index")) != "text":
                    raise BrokenStream()
                return self._text(delta.get("text"))
        elif kind == "content_block_stop":
            self.blocks.pop(event.get("index"), None)
        elif kind == "message_delta":
            delta = event.get("delta")
            if not isinstance(delta, dict):
                raise BrokenStream()
            self.reason = delta.get("stop_reason")
        elif kind == "message_stop":
            if not self.started or self.stopped or self.blocks:
                raise BrokenStream()
            if self.reason not in ("end_turn", "stop_sequence"):
                raise BrokenStream()
            self.stopped = True
        return ""

    @staticmethod
    def _text(value):
        if not isinstance(value, str):
            raise BrokenStream()
        return value


def _lines(stream, control):
    size = 0
    while True:
        control.check()
        raw = stream.readline(MAX_LINE + 1)
        control.check()
        if not raw:
            return
        size += len(raw)
        if len(raw) > MAX_LINE or size > MAX_WIRE:
            raise BrokenStream()
        try:
            yield raw.decode("utf-8").rstrip("\r\n")
        except UnicodeError:
            raise BrokenStream() from None


def _sse_events(stream, control):
    data = []
    size = 0
    for line in _lines(stream, control):
        if not line:
            if data:
                try:
                    yield json.loads("\n".join(data))
                except ValueError:
                    raise BrokenStream() from None
            data, size = [], 0
        elif line.startswith("data:"):
            value = line[5:]
            if value.startswith(" "):
                value = value[1:]
            size += len(value)
            if size > MAX_LINE:
                raise BrokenStream()
            data.append(value)
    # An unterminated frame is not a successful transport terminator.
    if data:
        raise BrokenStream()


def api_text(credential, system, prompt, model, control):
    payload = json.dumps({
        "model": model, "max_tokens": 2400, "stream": True, "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    with http_response(
        "https://api.anthropic.com/v1/messages", payload=payload,
        headers={"Content-Type": "application/json", "Accept": "text/event-stream",
                 "anthropic-version": "2023-06-01", "x-api-key": credential},
        control=control,
    ) as response:
        if response.getheader("Content-Type", "").split(";", 1)[0].strip().lower() != "text/event-stream":
            raise BrokenStream()
        parser = TextEvents()
        for event in _sse_events(response, control):
            text = parser.take(event)
            if text:
                yield text
            if parser.stopped:
                return
        raise BrokenStream()


def _kill_process(proc):
    if os.name == "nt":
        job = getattr(proc, "_assistant_job", None)
        if job is not None:
            # The launcher may already be dead while descendants retain stdout.
            # A job handle owns those descendants without looking up a PID.
            job.close()
        elif proc.poll() is None:
            # Startup failed before assignment. Popen.kill uses the original
            # process HANDLE, never taskkill against a potentially reused PID.
            proc.kill()
    else:
        # Only the new session created below is targeted, never the dashboard's
        # own process group. This also closes stdout inherited by descendants.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError:
            # Some platforms deny a second group signal while a killed child
            # is becoming a zombie. Reap it; never mask the original outcome.
            if proc.poll() is None:
                proc.kill()


class _WindowsJob:
    """Private kill-on-close job, assigned before a suspended launcher can run."""

    def __init__(self):
        import ctypes as c

        class BasicLimits(c.Structure):
            _fields_ = [
                ("process_time", c.c_int64), ("job_time", c.c_int64),
                ("flags", c.c_uint32), ("min_working_set", c.c_size_t),
                ("max_working_set", c.c_size_t), ("active_processes", c.c_uint32),
                ("affinity", c.c_size_t), ("priority", c.c_uint32),
                ("scheduling", c.c_uint32),
            ]

        class ExtendedLimits(c.Structure):
            _fields_ = [
                ("basic", BasicLimits), ("io_counters", c.c_uint64 * 6),
                ("process_memory", c.c_size_t), ("job_memory", c.c_size_t),
                ("peak_process_memory", c.c_size_t), ("peak_job_memory", c.c_size_t),
            ]

        self._lock = threading.Lock()
        self._handle = None
        self._kernel = c.WinDLL("kernel32", use_last_error=True)
        # Explicit pointer-sized HANDLE signatures are essential on Win64.
        for name, args, result in (
            ("CreateJobObjectW", [c.c_void_p, c.c_wchar_p], c.c_void_p),
            ("SetInformationJobObject", [c.c_void_p, c.c_int, c.c_void_p, c.c_uint32], c.c_int),
            ("AssignProcessToJobObject", [c.c_void_p, c.c_void_p], c.c_int),
            ("CloseHandle", [c.c_void_p], c.c_int),
            ("GetProcessId", [c.c_void_p], c.c_uint32),
            ("CreateToolhelp32Snapshot", [c.c_uint32, c.c_uint32], c.c_void_p),
            ("Thread32First", [c.c_void_p, c.c_void_p], c.c_int),
            ("Thread32Next", [c.c_void_p, c.c_void_p], c.c_int),
            ("OpenThread", [c.c_uint32, c.c_int, c.c_uint32], c.c_void_p),
            ("GetProcessIdOfThread", [c.c_void_p], c.c_uint32),
            ("WaitForSingleObject", [c.c_void_p, c.c_uint32], c.c_uint32),
            ("ResumeThread", [c.c_void_p], c.c_uint32),
        ):
            function = getattr(self._kernel, name)
            function.argtypes, function.restype = args, result
        self._handle = self._kernel.CreateJobObjectW(None, None)
        if not self._handle:
            raise OSError("Could not create the Assistant process job")
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self._kernel.SetInformationJobObject(self._handle, 9, c.byref(limits), c.sizeof(limits)):
            self.close()
            raise OSError("Could not configure the Assistant process job")

    def assign_and_resume(self, proc):
        # Popen retains the original kernel process handle on Windows.
        handle = int(proc._handle)
        if not self._kernel.AssignProcessToJobObject(self._handle, handle):
            raise OSError("Could not contain the Assistant process")
        self._resume_initial_thread(handle)

    def _resume_initial_thread(self, process_handle):
        """Use documented Toolhelp/OpenThread/ResumeThread APIs only.

        CREATE_SUSPENDED keeps the initial thread from spawning any others.
        Verify the opened thread against the retained process handle before
        resuming it, rather than trusting a potentially stale snapshot ID.
        """
        import ctypes as c

        class ThreadEntry(c.Structure):
            _fields_ = [
                ("size", c.c_uint32), ("usage", c.c_uint32),
                ("thread_id", c.c_uint32), ("owner_pid", c.c_uint32),
                ("base_priority", c.c_int32), ("delta_priority", c.c_int32),
                ("flags", c.c_uint32),
            ]

        kernel = self._kernel
        pid = kernel.GetProcessId(process_handle)
        if not pid:
            raise OSError("Could not identify the Assistant process")
        snapshot = kernel.CreateToolhelp32Snapshot(0x4, 0)  # TH32CS_SNAPTHREAD
        if snapshot in (None, 0, c.c_void_p(-1).value):
            raise OSError("Could not find the Assistant initial thread")
        try:
            entry = ThreadEntry()
            entry.size = c.sizeof(entry)
            found = kernel.Thread32First(snapshot, c.byref(entry))
            while found:
                if entry.size >= 16 and entry.owner_pid == pid:
                    # THREAD_SUSPEND_RESUME | THREAD_QUERY_LIMITED_INFORMATION
                    thread = kernel.OpenThread(0x802, False, entry.thread_id)
                    if not thread:
                        raise OSError("Could not open the Assistant initial thread")
                    try:
                        if (kernel.GetProcessIdOfThread(thread) != pid or
                                kernel.WaitForSingleObject(process_handle, 0) != 258):
                            raise OSError("The Assistant process identity changed")
                        if kernel.ResumeThread(thread) != 1:
                            raise OSError("Could not resume the Assistant initial thread")
                        return
                    finally:
                        kernel.CloseHandle(thread)
                entry.size = c.sizeof(entry)
                found = kernel.Thread32Next(snapshot, c.byref(entry))
            raise OSError("The Assistant initial thread is unavailable")
        finally:
            kernel.CloseHandle(snapshot)

    def close(self):
        with self._lock:
            if self._handle is not None:
                if not self._kernel.CloseHandle(self._handle):
                    raise OSError("Could not close the Assistant process job")
                self._handle = None


def _spawn_cli(argv, **kwargs):
    windows = os.name == "nt"
    job = _WindowsJob() if windows else None
    proc = None
    try:
        proc = subprocess.Popen(
            argv, **kwargs, start_new_session=not windows,
            creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP | 0x4) if windows else 0,
        )  # 0x4 = CREATE_SUSPENDED: no child can escape before job assignment.
        if job is not None:
            job.assign_and_resume(proc)
            proc._assistant_job = job
        return proc
    except BaseException:
        try:
            if job is not None:
                job.close()
        finally:
            if proc is not None:
                try:
                    if proc.poll() is None:
                        proc.kill()
                    proc.wait(timeout=2)
                finally:
                    proc.stdout.close()
        raise


def cli_text(executable, system, prompt, control):
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)
    argv = [
        executable, "-p", "--output-format", "stream-json", "--verbose",
        "--include-partial-messages", "--tools", "", "--disable-slash-commands",
        "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--no-session-persistence", "--setting-sources", "", "--safe-mode",
        "--system-prompt", system,
    ]
    with tempfile.TemporaryDirectory(prefix="clawmetry-assistant-") as workdir:
        # A private anonymous stdin file avoids a pipe-write deadlock if a
        # harness stops consuming a long prompt. It is deleted on every exit.
        with tempfile.TemporaryFile(dir=workdir) as stdin:
            stdin.write(prompt.encode("utf-8"))
            stdin.seek(0)
            control.check()
            proc = _spawn_cli(
                argv, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                cwd=workdir, env=env,
            )
            timer = threading.Timer(CLI_SECONDS, lambda: control.abort(timeout=True))
            timer.daemon = True
            try:
                with control.resource(lambda: _kill_process(proc)):
                    timer.start()
                    parser = TextEvents()
                    completed = False
                    for line in _lines(proc.stdout, control):
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                        except ValueError:
                            raise BrokenStream() from None
                        if not isinstance(event, dict):
                            raise BrokenStream()
                        if event.get("type") == "stream_event":
                            text = parser.take(event.get("event"))
                            if text:
                                yield text
                        elif event.get("type") == "result":
                            if event.get("is_error"):
                                raise harness_failure()
                            if (completed or event.get("subtype") != "success" or
                                    not isinstance(event.get("result"), str)):
                                raise BrokenStream()
                            # result duplicates the text deltas. It is a success
                            # check, not an additional source of visible text.
                            completed = True
                    if proc.wait(timeout=2):
                        raise harness_failure()
                    if not completed or not parser.stopped:
                        raise BrokenStream()
            finally:
                timer.cancel()
                try:
                    _kill_process(proc)
                    proc.wait(timeout=2)
                finally:
                    proc.stdout.close()


def generate(mode, credential, system, prompt, *, model, executable, control, on_text=None):
    """Accumulate a private plan or emit synthesis text from real provider events."""
    iterator = (cli_text(executable, system, prompt, control) if mode == "claude_cli"
                else api_text(credential, system, prompt, model, control))
    parts = []
    size = 0
    try:
        for text in iterator:
            control.check()
            size += len(text)
            if size > MAX_TEXT:
                raise BrokenStream()
            parts.append(text)
            if on_text is not None:
                on_text(text)
    except urllib.error.HTTPError as exc:
        try:
            raise http_failure(exc) from None
        finally:
            exc.close()
    except TimeoutError:
        raise
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise TimeoutError() from None
        raise ProviderFailure("Could not reach the AI provider. Check your connection and retry.") from None
    except http.client.HTTPException:
        raise BrokenStream() from None
    except OSError:
        if mode == "claude_cli":
            raise harness_failure() from None
        raise ProviderFailure("Could not reach the AI provider. Check your connection and retry.") from None
    finally:
        iterator.close()
    if not parts or not "".join(parts).strip():
        raise BrokenStream()
    return "".join(parts)
