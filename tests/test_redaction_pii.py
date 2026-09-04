"""Personal-data redaction tier (WO-61, REQ-PII-001).

Each category has a positive, the checksum categories have a
checksum-failure negative, and one fixture of near-misses (commit hashes,
timestamps, version strings, ports, UUIDs, epoch values, PIDs) must come
through untouched. The tier sits after the secret tier inside the same
scan cap, and the operator can turn it off per category or entirely.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import redaction as r  # noqa: E402


@pytest.fixture(autouse=True)
def _tier_on(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_REDACT", raising=False)
    monkeypatch.delenv("CLAWMETRY_REDACT_PII", raising=False)
    # Never read the developer's real config.json from a unit test.
    monkeypatch.setattr(r, "_CONFIG_PATH", str(tmp_path / "config.json"))
    r._pii_cfg_cache.update({"at": 0.0, "mtime": None, "value": {}})
    yield


def _write_cfg(path, pii):
    with open(path, "w") as f:
        json.dump({"redaction": {"pii": pii}}, f)
    r._pii_cfg_cache.update({"at": 0.0, "mtime": None, "value": {}})


# ── positives ────────────────────────────────────────────────────────────

def test_email_becomes_typed_placeholder():
    out = r.redact_text("ticket from alice.smith+dev@example.co.uk about it")
    assert "alice.smith" not in out
    assert out == "ticket from [email] about it"


def test_phone_e164_with_and_without_separators():
    out = r.redact_text("call +44 20 7946 0958 or +14155552671 now")
    assert out == "call [phone] or [phone] now"


def test_card_luhn_valid_with_separators():
    out = r.redact_text("visa 4111-1111-1111-1111 amex 3782 822463 10005 mc 5555555555554444")
    assert out == "visa [card] amex [card] mc [card]"


def test_iban_spaced_and_compact():
    out = r.redact_text("pay GB82 WEST 1234 5698 7654 32 or DE89370400440532013000")
    assert out == "pay [iban] or [iban]"


def test_us_ssn_dashed_form():
    assert r.redact_text("ssn 123-45-6789.") == "ssn [national_id]."


def test_uk_nino():
    # Q is not a valid NINO prefix letter (D, F, I, Q, U, V never are).
    assert r.redact_text("ref QQ123456A") == "ref QQ123456A"
    out = r.redact_text("NI number AB 12 34 56 C and JG103759A")
    assert out == "NI number [national_id] and [national_id]"


def _aadhaar_with_check(prefix11: str) -> str:
    for d in "0123456789":
        cand = prefix11 + d
        if r.verhoeff_valid(cand):
            return cand
    raise AssertionError("no Verhoeff digit found")


def test_india_aadhaar_verhoeff():
    good = _aadhaar_with_check("49994999499")
    spaced = f"{good[:4]} {good[4:8]} {good[8:]}"
    out = r.redact_text(f"aadhaar {spaced} and {good}")
    assert out == "aadhaar [national_id] and [national_id]"


def test_netherlands_bsn_11_proef():
    assert r.bsn_valid("111222333")
    assert r.redact_text("bsn 111222333 ok") == "bsn [national_id] ok"


# ── checksum negatives ───────────────────────────────────────────────────

def test_card_that_fails_luhn_is_kept():
    assert r.redact_text("ref 4111111111111112") == "ref 4111111111111112"


def test_card_with_unknown_prefix_is_kept_even_when_luhn_passes():
    # 13 digits starting 17 (epoch milliseconds shape). Find a Luhn-valid one.
    for tail in range(10):
        cand = f"172535040000{tail}"
        if r.luhn_valid(cand):
            break
    else:
        pytest.skip("no Luhn-valid epoch-shaped value in range")
    assert r.luhn_valid(cand)
    assert r.redact_text(f"epoch {cand}") == f"epoch {cand}"


def test_iban_with_bad_mod97_is_kept():
    assert not r.iban_valid("GB82WEST12345698765431")
    assert r.redact_text("iban GB82WEST12345698765431") == "iban GB82WEST12345698765431"


def test_iban_unknown_country_is_kept():
    assert not r.iban_valid("ZZ82WEST12345698765432")


def test_aadhaar_with_bad_verhoeff_is_kept():
    good = _aadhaar_with_check("49994999499")
    bad = good[:-1] + str((int(good[-1]) + 1) % 10)
    assert r.redact_text(f"id {bad}") == f"id {bad}"


def test_aadhaar_first_digit_rule():
    assert not r.aadhaar_valid("1" + _aadhaar_with_check("49994999499")[1:])


def test_bsn_with_bad_11_proef_is_kept():
    assert not r.bsn_valid("111222334")
    assert r.redact_text("n 111222334") == "n 111222334"


def test_ssn_area_rules():
    for bad in ("000-45-6789", "666-45-6789", "900-45-6789",
                "123-00-6789", "123-45-0000"):
        assert r.redact_text(bad) == bad


def test_phone_needs_eight_digits_and_a_plus():
    assert r.redact_text("+1234567 short") == "+1234567 short"
    assert r.redact_text("14155552671 bare") == "14155552671 bare"


# ── near-miss fixture: none of these is personal data ────────────────────

NEAR_MISSES = [
    "commit 96ef86dc0 and 3f2a9b1c7d4e8f01a2b3c4d5e6f70819",
    "2026-09-03T10:00:00+05:30 and 2026-09-03T10:00:00.123Z",
    "version 1.2.3 build 0.12.565 tag v2.1.259 python 3.11.9",
    "listening on 127.0.0.1:8900 and :18789",
    "uuid 550e8400-e29b-41d4-a716-446655440000",
    "epoch 1725350400 ms 1725350400000 ns 1725350400000000",
    "pid 48213 ppid 1 port 65535",
    "tokens 123456 cost 0.0042 rows 9876543210",
    "user@host log line and @dataclass decorator",
    "diff +3 -2, tag 1.2.3+4567, C++17",
    "sha256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "ipv4 10.0.0.1 ipv6 fe80::1 mac 00:1a:2b:3c:4d:5e",
    "12345 67890 order-1234-5678",
]


@pytest.mark.parametrize("line", NEAR_MISSES)
def test_near_misses_are_untouched(line):
    assert r.redact_text(line) == line


# ── switches ─────────────────────────────────────────────────────────────

def test_per_category_switch_from_config(tmp_path):
    _write_cfg(r._CONFIG_PATH, {"email": False})
    out = r.redact_text("alice@example.com +14155552671")
    assert out == "alice@example.com [phone]"
    st = r.pii_status()
    assert st["enabled"] is True
    assert st["categories"]["email"] is False
    assert "email" not in st["active"] and "phone" in st["active"]


def test_env_kill_switch(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_REDACT_PII", "0")
    out = r.redact_text("alice@example.com key sk-ant-abcdefghijklmnopqrstuvwx")
    assert "alice@example.com" in out          # tier off
    assert "sk-ant-abcdefghijklmnopqrstuvwx" not in out  # secrets still on
    assert r.pii_status()["enabled"] is False


def test_status_reports_every_category():
    st = r.pii_status()
    assert tuple(st["categories"]) == r.PII_CATEGORIES
    assert st["active"] == list(r.PII_CATEGORIES)


def test_posture_line_states_the_setting(tmp_path):
    line = r.pii_posture_check()
    assert line["status"] == "pass"
    assert line["detail"].startswith("Personal data redaction: email, IBAN, card, phone, national id")
    for banned in ("—", " -- "):
        assert banned not in line["detail"]
        assert banned not in (line.get("remediation") or "")
    _write_cfg(r._CONFIG_PATH, {"card": False})
    line = r.pii_posture_check()
    assert line["status"] == "warn" and "Off for: card" in line["detail"]


def test_posture_line_when_off(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_REDACT_PII", "off")
    line = r.pii_posture_check()
    assert line["status"] == "warn" and line["detail"].startswith("Off.")


# ── ordering + cap ───────────────────────────────────────────────────────

def test_secrets_are_fingerprinted_before_pii_typing():
    out = r.redact_text("Authorization: Bearer abcdefghijklmnop@example.com")
    assert "[REDACTED:" in out and "[email]" not in out


def test_scan_cap_still_applies():
    big = "alice@example.com " * 1 + "x" * (r._MAX_SCAN + 10)
    assert r.redact_text(big) is big


def test_event_payloads_get_the_tier():
    ev = r.redact_event({"id": "e1", "node_id": "n", "event_type": "tool.result",
                         "ts": "t", "data": {"content": "mail bob@example.com"}})
    assert ev["data"]["content"] == "mail [email]"
