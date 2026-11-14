"""Free local Asimov recording import, inspection and optional live observation."""

import argparse
import json
import os

from .journal import MAX_EVENT_BYTES, journal_directory


def main(argv=None):
    """Run the dedicated Asimov command without loading optional robot libraries."""
    parser = argparse.ArgumentParser(
        prog="clawmetry asimov",
        description="Observe Asimov 1 and import official Menlo SDK recordings. Hardware validation is pending.",
    )
    commands = parser.add_subparsers(dest="command")
    load = commands.add_parser(
        "import-recording", help="Import official SDK JSONL without a live robot"
    )
    load.add_argument("source", help="Official Menlo SDK JSONL file")
    load.add_argument(
        "--robot-id", required=True, help="Your identifier for the physical robot"
    )
    load.add_argument("--source-label", help="Optional name for this recording")
    load.add_argument(
        "--environment", choices=("hardware", "simulation"), default="hardware"
    )
    load.add_argument("--journal-dir")
    live = commands.add_parser(
        "observe",
        help="Receive telemetry with an Observe credential; no media or commands",
    )
    live.add_argument("--robot-id", help="Defaults to the manager's robot room")
    live.add_argument("--manager-url", default=os.environ.get("MENLO_MANAGER_URL"))
    live.add_argument(
        "--duration", type=float, help="Collect this many seconds, or Ctrl+C to finish"
    )
    live.add_argument("--journal-dir")
    inspect_cmd = commands.add_parser(
        "inspect", help="Inspect a local journal explicitly, outside the web server"
    )
    inspect_cmd.add_argument("run_id")
    inspect_cmd.add_argument("--journal-dir")
    status = commands.add_parser(
        "status", help="Show bounded recorder health summaries"
    )
    status.add_argument("--journal-dir")
    args = parser.parse_args(argv)
    try:
        if args.command == "import-recording":
            from .recording import import_recording

            result = import_recording(
                args.source,
                robot_id=args.robot_id,
                directory=args.journal_dir,
                environment=args.environment,
                source=args.source_label,
            )
        elif args.command == "observe":
            from .observer import observe_live

            result = observe_live(
                manager_url=args.manager_url,
                credential=os.environ.get("MENLO_CREDENTIAL"),
                robot_id=args.robot_id,
                directory=args.journal_dir,
                duration=args.duration,
            )
        elif args.command == "status":
            root = journal_directory(args.journal_dir)
            paths = sorted(
                root.glob("*.status.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )[:50]
            result = {
                "recorders": [
                    json.loads(p.read_text(encoding="utf-8"))
                    for p in paths
                    if p.stat().st_size <= MAX_EVENT_BYTES
                ]
            }
        elif args.command == "inspect":
            if len(args.run_id) != 32 or any(
                c not in "0123456789abcdef" for c in args.run_id
            ):
                raise ValueError("Use a run identifier from clawmetry asimov status")
            path = journal_directory(args.journal_dir) / (args.run_id + ".jsonl")
            count, latest, first = 0, None, None
            with path.open("rb") as fh:
                while True:
                    line = fh.readline(MAX_EVENT_BYTES + 1)
                    if not line:
                        break
                    if len(line) > MAX_EVENT_BYTES:
                        raise ValueError("Journal contains an oversized row")
                    event = json.loads(line)
                    count += 1
                    first = first or event
                    if event.get("kind") == "observation":
                        latest = event
            result = {
                "run_id": args.run_id,
                "events": count,
                "started": first,
                "latest_observation": latest,
                "hardware_verified": False,
            }
        else:
            parser.print_help()
            return 0
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except Exception as exc:  # noqa: BLE001 - optional SDK errors must not leak credentials
        # Credential-bearing SDK exceptions are deliberately not printed.
        message = (
            str(exc)
            if type(exc) in (ValueError, RuntimeError)
            else "The operation could not finish. Check the recording path, robot connection and Observe credential."
        )
        if "token" in message.lower() and "Observe token" not in message:
            message = "The Observe connection could not start. Check your robot and Observe credential in Asimov Manager."
        print(message)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
