"""Contracts the fuzz targets assert, importable without Atheris.

The property lives here, not in the harnesses, so `tests/test_fuzz_targets.py`
can assert exactly the same thing over a fixed seed corpus on every PR. Atheris
is a Linux/CPython wheel and is not installed in the normal test matrix; a
contract that only ran under the fuzzer would go stale the first time someone
refactored the parser.
"""

from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

OTLP_KINDS = ("traces", "logs", "metrics")


class ContractViolation(AssertionError):
    """Raised when a target breaks its documented contract."""


def check_otlp_json(payload: bytes, kind: str, content_encoding: str | None) -> None:
    """`otlp_json.decode` returns a request object or raises ValueError.

    Nothing else. `_otlp_receive` maps a raised ValueError onto HTTP 400; any
    other exception type is a bug that would otherwise surface as a 500 (or, in
    the sync daemon, as an ingest stall) on a body a stranger controls.
    """
    from clawmetry import otlp_json

    try:
        otlp_json.decode(payload, kind, content_encoding=content_encoding)
    except ValueError:
        # The documented rejection path. UnicodeDecodeError and
        # json.JSONDecodeError are both ValueError subclasses, so a malformed
        # body of any encoding lands here.
        return
    except RecursionError:
        # Deeply nested JSON is rejected by the interpreter before our code
        # sees it. Not a decoder defect, and not something a guard can fix.
        return
    except Exception as exc:  # noqa: BLE001 - the point is to catch the leak
        raise ContractViolation(
            f"otlp_json.decode({payload!r:.120}, {kind!r}, "
            f"content_encoding={content_encoding!r}) raised "
            f"{type(exc).__name__}: {exc}"
        ) from exc


def check_event_shape(event_type, data) -> None:
    """`event_shape.classify` / `typed_columns` must never raise.

    Both run over every ingested transcript row. Transcript JSONL is written by
    the agent runtimes, so its shape is theirs to change; CLAUDE.md's "never
    crash on bad input" rule is what keeps one odd row from stalling ingest for
    the whole session.
    """
    from clawmetry import event_shape

    for fn in (event_shape.classify, event_shape.typed_columns):
        try:
            fn(event_type, data)
        except RecursionError:
            return
        except Exception as exc:  # noqa: BLE001
            raise ContractViolation(
                f"event_shape.{fn.__name__}({event_type!r:.60}, {data!r:.120}) "
                f"raised {type(exc).__name__}: {exc}"
            ) from exc
