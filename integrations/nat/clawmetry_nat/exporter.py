"""
clawmetry_nat/exporter.py

ClawMetryNATExporter — the main integration point.

Accepts NAT IntermediateStep events via:
  1. on_event(step)         — callback (sync or async-friendly)
  2. as a NAT RawExporter   — plug directly into the NAT tracing pipeline

Events are buffered and flushed either:
  - To ClawMetry's /api/ingest HTTP endpoint  (CLAWMETRY_URL + CLAWMETRY_API_KEY)
  - Or to JSONL files in ~/.clawmetry/nat/    (fallback / offline mode)

Environment variables:
  CLAWMETRY_URL      — e.g. https://ingest.clawmetry.com  (or http://localhost:3002)
  CLAWMETRY_API_KEY  — your ClawMetry API key
  CLAWMETRY_NAT_JSONL_DIR — override JSONL output directory
  CLAWMETRY_NAT_BATCH_SIZE — max events per HTTP POST (default 50)
  CLAWMETRY_NAT_FLUSH_SEC  — flush interval in seconds (default 5)
"""

from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .mapper import NATEventMapper

log = logging.getLogger("clawmetry-nat")


# ---------------------------------------------------------------------------
# Defaults / env helpers
# ---------------------------------------------------------------------------


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# ClawMetryNATExporter
# ---------------------------------------------------------------------------


class ClawMetryNATExporter:
    """
    Bridge NVIDIA NeMo Agent Toolkit workflow events to ClawMetry.

    Usage (standalone / callback):
        exporter = ClawMetryNATExporter()
        exporter.on_event(nat_step)     # call from your NAT callback

    Usage (as a NAT RawExporter subclass):
        class MyNATExporter(ClawMetryNATExporter, RawExporter[IntermediateStep, IntermediateStep]):
            async def export_processed(self, item):
                self.on_event(item)

    The exporter runs a background flush thread so the hot path (on_event)
    is never blocked by network I/O.
    """

    def __init__(
        self,
        *,
        clawmetry_url: Optional[str] = None,
        api_key: Optional[str] = None,
        session_id: Optional[str] = None,
        model: str = "nat-agent",
        batch_size: int = 0,
        flush_interval_sec: float = 0,
        jsonl_dir: Optional[str] = None,
        on_flush_error: Optional[Callable[[Exception], None]] = None,
    ):
        """
        Args:
            clawmetry_url:      Override CLAWMETRY_URL env var.
            api_key:            Override CLAWMETRY_API_KEY env var.
            session_id:         Fixed session UUID. Auto-generated if None.
            model:              Model label used in events (default "nat-agent").
            batch_size:         Max events per HTTP POST (env: CLAWMETRY_NAT_BATCH_SIZE).
            flush_interval_sec: Seconds between auto-flushes (env: CLAWMETRY_NAT_FLUSH_SEC).
            jsonl_dir:          Local directory for JSONL fallback/offline mode.
            on_flush_error:     Optional callback(exc) when a flush fails.
        """
        self.url = (
            clawmetry_url or _env("CLAWMETRY_URL", "https://ingest.clawmetry.com")
        ).rstrip("/")
        self.api_key = api_key or _env("CLAWMETRY_API_KEY")
        self.batch_size = batch_size or _env_int("CLAWMETRY_NAT_BATCH_SIZE", 50)
        self.flush_sec = flush_interval_sec or float(
            _env_int("CLAWMETRY_NAT_FLUSH_SEC", 5)
        )
        self.on_flush_error = on_flush_error

        # JSONL output dir (fallback when no URL/API key, or explicitly set)
        _default_jsonl = str(Path.home() / ".clawmetry" / "nat")
        self.jsonl_dir = Path(
            jsonl_dir or _env("CLAWMETRY_NAT_JSONL_DIR", _default_jsonl)
        )

        self.session_id = session_id or str(uuid.uuid4())
        self.mapper = NATEventMapper(session_id=self.session_id, model=model)

        self._queue: queue.Queue[Dict[str, Any]] = queue.Queue()
        self._lock = threading.Lock()
        self._buffer: List[Dict[str, Any]] = []
        self._closed = False

        # Start background flush thread
        self._flush_thread = threading.Thread(
            target=self._flush_loop, daemon=True, name="clawmetry-nat-flush"
        )
        self._flush_thread.start()

        mode = "HTTP → " + self.url if self.api_key else f"JSONL → {self.jsonl_dir}"
        log.info(
            f"ClawMetryNATExporter started (session={self.session_id}, mode={mode})"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def on_event(self, step: Any) -> None:
        """
        Receive a NAT IntermediateStep event and enqueue it for export.

        This is the primary callback hook. Call it from your NAT exporter's
        export_processed() method, or from any NAT event callback.
        """
        if self._closed:
            return
        try:
            ev = self.mapper.map(step)
            if ev:
                with self._lock:
                    self._buffer.append(ev)
                    if len(self._buffer) >= self.batch_size:
                        self._flush_locked()
        except Exception as exc:
            log.warning(f"ClawMetryNATExporter.on_event error: {exc}")

    def flush(self) -> int:
        """Manually flush all buffered events. Returns number of events flushed."""
        with self._lock:
            return self._flush_locked()

    def close(self, timeout: float = 10.0) -> None:
        """Flush remaining events and stop the background thread."""
        self._closed = True
        self.flush()
        self._flush_thread.join(timeout=timeout)
        log.info("ClawMetryNATExporter closed")

    # Context manager support
    def __enter__(self) -> "ClawMetryNATExporter":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # NAT RawExporter compatibility shim
    # ------------------------------------------------------------------

    async def export_processed(self, item: Any) -> None:
        """
        Async shim for NAT RawExporter subclassing.

        If you subclass both ClawMetryNATExporter and NAT's RawExporter,
        NAT will call this method automatically for each IntermediateStep.
        """
        self.on_event(item)

    # ------------------------------------------------------------------
    # Internal flush machinery
    # ------------------------------------------------------------------

    def _flush_locked(self) -> int:
        """Flush buffer (must be called with self._lock held)."""
        acquired = self._lock.acquire(blocking=False)
        if acquired:
            self._lock.release()
            raise RuntimeError("_flush_locked() must be called with lock held")
        if not self._buffer:
            return 0
        batch = self._buffer[:]
        self._buffer.clear()
        # Release lock before I/O
        self._lock.release()
        try:
            self._send(batch)
        except Exception as exc:
            log.warning(f"ClawMetryNATExporter flush error: {exc}")
            if self.on_flush_error:
                self.on_flush_error(exc)
        finally:
            self._lock.acquire()
        return len(batch)

    def _flush_loop(self) -> None:
        """Background thread: flush every flush_sec seconds."""
        while not self._closed:
            time.sleep(self.flush_sec)
            try:
                with self._lock:
                    self._flush_locked()
            except Exception as exc:
                log.debug(f"Flush loop error: {exc}")

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------

    def _send(self, events: List[Dict[str, Any]]) -> None:
        """Send a batch of events to ClawMetry or write to JSONL."""
        if self.api_key and self.url:
            self._http_post(events)
        else:
            self._write_jsonl(events)

    def _http_post(self, events: List[Dict[str, Any]]) -> None:
        """POST events to ClawMetry /api/ingest."""
        payload = json.dumps({"events": events, "source": "nat"}).encode()
        req = urllib.request.Request(
            self.url + "/api/ingest",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": self.api_key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                log.debug(f"Flushed {len(events)} events → HTTP {resp.status}")
        except urllib.error.HTTPError as exc:
            body = exc.read()[:200].decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} from {self.url}: {body}") from exc

    def _write_jsonl(self, events: List[Dict[str, Any]]) -> None:
        """Write events to a JSONL file under self.jsonl_dir."""
        self.jsonl_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        out_path = self.jsonl_dir / f"nat-{self.session_id[:8]}-{date_str}.jsonl"
        with out_path.open("a", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev) + "\n")
        log.debug(f"Wrote {len(events)} events → {out_path}")


# ---------------------------------------------------------------------------
# NAT plugin registration helper (optional — requires nvidia-nat installed)
# ---------------------------------------------------------------------------


def register_clawmetry_exporter(
    config_class_name: str = "clawmetry",
    **exporter_kwargs: Any,
) -> Optional[Any]:
    """
    Attempt to register ClawMetryNATExporter as a NAT tracing plugin.

    This is a best-effort helper — it silently returns None if nvidia-nat
    is not installed, so clawmetry-nat works without a full NAT installation.

    Usage in workflow.yaml after calling this function:
        general:
          telemetry:
            tracing:
              clawmetry:
                _type: clawmetry

    Args:
        config_class_name: The _type name used in workflow.yaml.
        **exporter_kwargs:  Passed to ClawMetryNATExporter().
    """
    try:
        from pydantic import Field as PydanticField
        from nat.builder.builder import Builder
        from nat.cli.register_workflow import register_telemetry_exporter
        from nat.data_models.telemetry_exporter import TelemetryExporterBaseConfig
        from nat.observability.exporter.raw_exporter import RawExporter
        from nat.data_models.intermediate_step import IntermediateStep

        class ClawMetryExporterConfig(
            TelemetryExporterBaseConfig, name=config_class_name
        ):
            url: str = PydanticField(default="", description="ClawMetry ingest URL")
            api_key: str = PydanticField(default="", description="ClawMetry API key")
            model: str = PydanticField(default="nat-agent", description="Model label")

        class _NATExporter(RawExporter[IntermediateStep, IntermediateStep]):
            def __init__(
                self,
                url: str = "",
                api_key: str = "",
                model: str = "nat-agent",
                context_state: Any = None,
                **kwargs: Any,
            ):
                super().__init__(context_state=context_state)
                self._claw = ClawMetryNATExporter(
                    clawmetry_url=url or None,
                    api_key=api_key or None,
                    model=model,
                    **exporter_kwargs,
                )

            async def export_processed(self, item: IntermediateStep) -> None:
                self._claw.on_event(item)

        @register_telemetry_exporter(config_type=ClawMetryExporterConfig)
        async def _clawmetry_nat_exporter(
            config: ClawMetryExporterConfig, builder: Builder
        ):
            yield _NATExporter(
                url=config.url, api_key=config.api_key, model=config.model
            )

        log.info(f"ClawMetry NAT plugin registered as _type: {config_class_name}")
        return _clawmetry_nat_exporter

    except ImportError:
        log.debug("nvidia-nat not installed — skipping NAT plugin registration")
        return None
