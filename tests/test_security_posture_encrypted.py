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


# ── Step 2: machine fingerprint (local_ips/os/arch/ram/cpu) → encrypted ──────

def test_machine_info_carries_local_ips():
    # The full local-IP list now rides the encrypted machineInfo snapshot.
    assert '"label": "Local IPs"' in SYNC


def test_node_meta_does_not_leak_machine_fingerprint():
    # _build_node_meta (plaintext heartbeat) must no longer set the machine
    # fingerprint; it lives in the encrypted snapshot now. Scope to the function.
    start = SYNC.index("def _build_node_meta(")
    end = SYNC.index("\ndef ", start)
    body = SYNC[start:end]
    for leaked in ('"local_ips"', '"os"', '"arch"', '"ram_gb"', '"cpu_count"'):
        assert leaked not in body, f"_build_node_meta still sets {leaked}"
