"""clawmetry/gateway_protocol.py — the single source of the OpenClaw gateway
WebSocket protocol range every connect frame must advertise.

Burned 2026-08-01: the WS tap was bumped to negotiate 3..4 (OpenClaw
2026.5.28+ rejects a 3..3 window with ``protocol-mismatch``) but three
sibling connect frames (dashboard discover, helpers/gateway webchat RPCs,
routes/meta validate) kept their own ``"maxProtocol": 3`` literals. The
founder's dashboard reported a perfectly healthy gateway as "not running"
while the webchat retried a rejected handshake in a tight loop, flooding
the gateway log. Four copies of the same literal is how one upgrade misses
three of them; every connect frame imports these constants instead, and
``tests/test_gateway_protocol_single_source.py`` fails the build if a
literal creeps back in.
"""

# Oldest gateway protocol we can still speak (pre-2026.5 gateways).
GATEWAY_MIN_PROTOCOL = 3
# Newest gateway protocol we understand (OpenClaw 2026.5.28+ requires 4).
GATEWAY_MAX_PROTOCOL = 4
