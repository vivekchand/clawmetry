"""Guard: security_posture rides the ENCRYPTED snapshot, not the plaintext
heartbeat (cloud #1569 / encrypt-everything).

The daemon must put the machine security scan into the E2E-encrypted system
snapshot (key `securityPosture`) and must NOT attach it to the plaintext
heartbeat payload (the cloud stored that in cleartext).
"""
import pathlib

SYNC = (pathlib.Path(__file__).resolve().parents[1] / "clawmetry" / "sync.py").read_text()


def test_security_posture_in_encrypted_snapshot():
    # sync_system_snapshot builds the AES-GCM-encrypted payload; it must include
    # the securityPosture key.
    assert '"securityPosture": _collect_security_posture()' in SYNC


def test_security_posture_not_on_plaintext_heartbeat():
    # send_heartbeat must not stash the scan on the plaintext payload.
    assert 'payload["security_posture"]' not in SYNC
    assert "payload['security_posture']" not in SYNC
