"""Gateway protocol range must come from ONE place (#gateway-protocol-drift).

Burned 2026-08-01: the WS tap negotiated 3..4 but three sibling connect
frames (dashboard discover, webchat RPC helper, meta validate) kept their
own ``"maxProtocol": 3`` literals. OpenClaw 2026.5.28+ rejects a 3..3
window with ``protocol-mismatch``, so the dashboard reported a healthy
gateway as "not running" and the webchat retried a rejected handshake in a
tight loop. Every connect frame now imports
``clawmetry.gateway_protocol``; this guard fails the build if a hardcoded
protocol literal creeps back into any connect frame.
"""

import re
from pathlib import Path

from clawmetry.gateway_protocol import GATEWAY_MAX_PROTOCOL, GATEWAY_MIN_PROTOCOL

_REPO = Path(__file__).resolve().parents[1]
_SCAN = [_REPO / "dashboard.py"]
_SCAN += sorted((_REPO / "clawmetry").rglob("*.py"))
_SCAN += sorted((_REPO / "routes").rglob("*.py"))
_SCAN += sorted((_REPO / "helpers").rglob("*.py"))

_LITERAL = re.compile(r"\"(?:min|max)Protocol\"\s*:\s*\d")


def test_protocol_range_is_sane():
    assert GATEWAY_MIN_PROTOCOL == 3
    assert GATEWAY_MAX_PROTOCOL >= 4
    assert GATEWAY_MIN_PROTOCOL <= GATEWAY_MAX_PROTOCOL


def test_no_control_ui_impersonation():
    """Protocol-4 gateways reject a control-ui identity carrying a bearer
    token (control-ui-insecure-auth), so the #1720 impersonation must stay
    dead — it turned a healthy gateway into "not running" in the UI."""
    offenders = []
    for path in _SCAN:
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            code = line.split("#", 1)[0]
            # Only a CLIENT IDENTITY is impersonation; channel-label maps
            # legitimately reference the string to classify senders.
            if re.search(r"\"id\"\s*:\s*\"openclaw-control-ui\"", code):
                offenders.append(f"{path.relative_to(_REPO)}:{lineno}")
    assert offenders == [], (
        f"control-ui impersonation in a connect frame: {offenders}"
    )


def test_no_hardcoded_protocol_literals_in_connect_frames():
    offenders = []
    for path in _SCAN:
        if path.name == "gateway_protocol.py":
            continue
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            code = line.split("#", 1)[0]
            if _LITERAL.search(code):
                offenders.append(f"{path.relative_to(_REPO)}:{lineno}")
    assert offenders == [], (
        "hardcoded gateway protocol literal(s) — import "
        f"clawmetry.gateway_protocol instead: {offenders}"
    )
