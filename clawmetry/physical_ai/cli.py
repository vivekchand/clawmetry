"""Jumper telemetry import using the built-in OSS adapter, without a robot SDK."""

import argparse
import json
from pathlib import Path
import sys

from clawmetry.asimov.journal import MAX_EVENT_BYTES, journal_directory


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="clawmetry jumper",
        description="Observe named Jumper telemetry in ClawMetry. No motor commands are sent.",
    )
    commands = parser.add_subparsers(dest="command")
    for name, help_text in (("observe", "Receive JSONL telemetry from an application on stdin"),
                            ("import-recording", "Import a local named SI-unit telemetry JSONL recording")):
        command = commands.add_parser(name, help=help_text)
        if name == "import-recording":
            command.add_argument("source")
        command.add_argument("--robot-id", required=True)
        command.add_argument("--environment", choices=("hardware", "simulation"), required=True)
        command.add_argument("--journal-dir")
    status = commands.add_parser("status", help="Show recent Jumper recorder health")
    status.add_argument("--journal-dir")
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            paths = sorted(journal_directory(args.journal_dir).glob("*.status.json"),
                           key=lambda p: p.stat().st_mtime, reverse=True)[:50]
            recorders = []
            for path in paths:
                if path.is_symlink() or path.stat().st_size > MAX_EVENT_BYTES:
                    continue
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and isinstance(data.get("source_kind"), str) and data["source_kind"].startswith("jumper_"):
                        recorders.append(data)
                except (ValueError, OSError, TypeError, RecursionError):
                    continue
            result = {"recorders": recorders}
        elif args.command in ("observe", "import-recording"):
            from .adapters.jumper import JumperObserver
            recording = args.command == "import-recording"
            source = Path(args.source).expanduser().open("rb") if recording else sys.stdin.buffer
            accepted = invalid = 0
            try:
                with JumperObserver(args.robot_id, environment=args.environment, directory=args.journal_dir,
                                    recording=recording, sample_interval_s=0 if recording else .1) as observer:
                    for _index in range(100000):
                        line = source.readline(MAX_EVENT_BYTES + 1)
                        if not line:
                            break
                        if len(line) > MAX_EVENT_BYTES:
                            raise ValueError("A telemetry row exceeds 64 KiB")
                        try:
                            frame = json.loads(line)
                        except (ValueError, UnicodeError, RecursionError):
                            invalid += 1
                            continue
                        if observer.observe(frame, block=recording) is None:
                            invalid += 1
                        else:
                            accepted += 1
                    else:
                        raise ValueError("This import reached the 100,000-frame limit; start another run")
                result = dict(observer.status(), accepted_frames=accepted, invalid_frames=invalid)
            finally:
                if recording:
                    source.close()
            if invalid or result.get("incomplete"):
                print(json.dumps(result, allow_nan=False))
                return 2
        else:
            parser.print_help()
            return 0
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except KeyboardInterrupt:
        return 0
    except (ValueError, TypeError, OSError, RecursionError):
        print("Telemetry could not be recorded. Check the input, environment and journal path.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
