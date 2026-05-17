#!/usr/bin/env python3
"""tests/eval_ci_mock_agent.py — deterministic agent for the CI eval gate.

The Phase 2 eval CLI (``clawmetry eval``) shells out to whatever command
``CLAWMETRY_EVALS_AGENT_CMD`` points at, pipes the test input on stdin,
and parses the LAST JSON line of stdout as the agent's reply. In ClawMetry's
OWN CI we don't want to boot a real agent — we want to gate every PR on
the eval pipeline itself (judge call, parsing, exit code), not on whether
a sandboxed Anthropic agent can phone home from the runner.

This script provides four canned responses keyed on the test input
substrings used in ``tests/data/golden_ci.yaml``. Each response mirrors
the shape ``openclaw agent --once --json`` would emit:

    {"text": "<reply>", "tools_used": [...], "outcome": "<enum>"}

Total runtime per call: <50 ms. Total cost: $0. The only real LLM call
in the gate is the judge (Haiku), bounded to one call per test by the
Phase 1 rate limiter.
"""

from __future__ import annotations

import json
import sys


def _respond(test_input: str) -> dict:
    """Pick the canned envelope that matches the test's input substring.

    Order matters — the refusal / escalation patterns are checked before
    the broader tool-call pattern so a single keyword overlap doesn't
    route to the wrong branch.
    """
    lowered = test_input.lower()

    # Refusal: prompt-injection attempt.
    if "ignore previous instructions" in lowered or "system prompt" in lowered:
        return {
            "text": (
                "I can't share my system prompt or override the rules I was "
                "given. Happy to help with anything else though."
            ),
            "tools_used": [],
            "outcome": "success",
        }

    # Escalation: explicit human handoff request.
    if "speak to a human" in lowered or "legal" in lowered:
        return {
            "text": (
                "Got it — this needs a human teammate. I'm routing you to "
                "our support queue now; expect a reply within one business "
                "day."
            ),
            "tools_used": [],
            "outcome": "escalated",
        }

    # Tool-call path: refund flow.
    if "refund" in lowered or "order" in lowered:
        return {
            "text": (
                "Looked up order #12345 and processed a full refund. "
                "You should see it on your statement within 3 business days."
            ),
            "tools_used": ["lookup_order", "process_refund"],
            "outcome": "success",
        }

    # Default: simple Q&A.
    return {
        "text": "2 + 2 = 4.",
        "tools_used": [],
        "outcome": "success",
    }


def main() -> int:
    try:
        test_input = sys.stdin.read()
    except Exception as e:  # pragma: no cover — defensive
        print(json.dumps({
            "text": "",
            "tools_used": [],
            "outcome": "failed",
            "error": f"stdin read failed: {e}",
        }))
        return 1

    print(json.dumps(_respond(test_input)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
