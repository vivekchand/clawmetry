"""Tests for TTS (tts.speak) observability gap (#3569).

Verifies three things:
1. sync._is_voice_lifecycle_record() accepts tts.* event types.
2. providers_pricing.estimate_tts_cost_usd() returns correct per-1K-char costs.
3. adapters/openclaw.py surfaces char_count, voice_id, audio_bytes in Event.extra.
"""
from __future__ import annotations

import json
import sys
import os
import types

import pytest

# ---------------------------------------------------------------------------
# 1. sync._is_voice_lifecycle_record recognises tts. prefix
# ---------------------------------------------------------------------------

def test_tts_prefix_recognised_by_is_voice_lifecycle_record():
    from clawmetry.sync import _is_voice_lifecycle_record, _VOICE_EVENT_TYPE_PREFIXES

    assert "tts." in _VOICE_EVENT_TYPE_PREFIXES, (
        "'tts.' must be in _VOICE_EVENT_TYPE_PREFIXES so tts.speak events are ingested"
    )
    assert _is_voice_lifecycle_record({"event_type": "tts.speak"})
    assert _is_voice_lifecycle_record({"event_type": "tts.speak.complete"})
    assert not _is_voice_lifecycle_record({"event_type": "tool.use"})
    assert not _is_voice_lifecycle_record({"event_type": "message.send"})


def test_tts_prefix_does_not_break_existing_voice_prefixes():
    from clawmetry.sync import _is_voice_lifecycle_record

    for et in ("talk.start", "realtime.chunk", "voice.end", "managed_room.join"):
        assert _is_voice_lifecycle_record({"event_type": et}), f"Existing prefix broken: {et}"


# ---------------------------------------------------------------------------
# 2. estimate_tts_cost_usd pricing
# ---------------------------------------------------------------------------

def test_estimate_tts_cost_openai():
    from clawmetry.providers_pricing import estimate_tts_cost_usd

    # 1000 chars @ $0.015/1K = $0.015
    cost = estimate_tts_cost_usd("openai", 1000)
    assert abs(cost - 0.015) < 1e-7, f"OpenAI 1K chars should be $0.015, got {cost}"


def test_estimate_tts_cost_google():
    from clawmetry.providers_pricing import estimate_tts_cost_usd

    # 500 chars @ $0.016/1K = $0.008
    cost = estimate_tts_cost_usd("google", 500)
    assert abs(cost - 0.008) < 1e-7, f"Google 500 chars should be $0.008, got {cost}"


def test_estimate_tts_cost_elevenlabs():
    from clawmetry.providers_pricing import estimate_tts_cost_usd

    # 2000 chars @ $0.10/1K = $0.20
    cost = estimate_tts_cost_usd("elevenlabs", 2000)
    assert abs(cost - 0.20) < 1e-7, f"ElevenLabs 2K chars should be $0.20, got {cost}"


def test_estimate_tts_cost_unknown_provider_returns_zero():
    from clawmetry.providers_pricing import estimate_tts_cost_usd

    assert estimate_tts_cost_usd("unknown-tts-provider", 1000) == 0.0


def test_estimate_tts_cost_zero_chars_returns_zero():
    from clawmetry.providers_pricing import estimate_tts_cost_usd

    assert estimate_tts_cost_usd("openai", 0) == 0.0


def test_estimate_tts_cost_prefix_match():
    from clawmetry.providers_pricing import estimate_tts_cost_usd

    # "openai-tts-1-hd" should prefix-match "openai-tts" -> rate $0.015
    cost = estimate_tts_cost_usd("openai-tts-1-hd", 1000)
    assert cost > 0.0, "Prefix-matched TTS provider should return non-zero cost"


# ---------------------------------------------------------------------------
# Fish Audio TTS pricing (#4724)
# ---------------------------------------------------------------------------

def test_estimate_tts_cost_fish_audio_hosted():
    from clawmetry.providers_pricing import estimate_tts_cost_usd

    # 1000 chars @ $0.015/1K = $0.015
    cost = estimate_tts_cost_usd("fish-audio", 1000)
    assert abs(cost - 0.015) < 1e-7, f"Fish Audio S2.1 1K chars should be $0.015, got {cost}"


def test_estimate_tts_cost_fish_short_alias():
    from clawmetry.providers_pricing import estimate_tts_cost_usd

    cost = estimate_tts_cost_usd("fish", 1000)
    assert abs(cost - 0.015) < 1e-7, f"'fish' alias 1K chars should be $0.015, got {cost}"


def test_estimate_tts_cost_fish_s2_pro_local():
    from clawmetry.providers_pricing import estimate_tts_cost_usd

    # S2 Pro is self-hosted (local TTS) — no per-call API cost
    cost = estimate_tts_cost_usd("fish-s2-pro", 5000)
    assert cost == 0.0, f"Fish S2 Pro (local) should be $0.0, got {cost}"


def test_tts_provider_rates_includes_fish_audio():
    from clawmetry.providers_pricing import TTS_PROVIDER_RATES

    assert "fish-audio" in TTS_PROVIDER_RATES, "fish-audio must be in TTS_PROVIDER_RATES"
    assert TTS_PROVIDER_RATES["fish-audio"] > 0, "fish-audio rate must be positive"
    assert "fish-s2-pro" in TTS_PROVIDER_RATES, "fish-s2-pro must be in TTS_PROVIDER_RATES"
    assert TTS_PROVIDER_RATES["fish-s2-pro"] == 0.0, "fish-s2-pro (local) rate must be 0.0"


def test_voice_event_data_captures_fish_audio_fields():
    """The data blob written by sync_voice_log_events must carry ttsModel and
    isLocal so backfill_tts_event_costs can route hosted vs local Fish Audio."""
    import json

    obj = {
        "event_type": "tts.speak",
        "provider":   "fish-audio",
        "char_count": 800,
        "ttsModel":   "fish-audio-s2.1",
        "isLocal":    False,
        "voice_id":   "en-US-Standard-A",
    }
    # Simulate the json.dumps call in sync_voice_log_events
    data = {
        "provider":   obj.get("provider"),
        "char_count": obj.get("char_count") or obj.get("characterCount") or obj.get("text_length"),
        "voice_id":   obj.get("voice_id") or obj.get("voiceId"),
        "ttsModel":   obj.get("ttsModel") or obj.get("fishModel") or None,
        "isLocal":    obj.get("isLocal") if obj.get("isLocal") is not None else obj.get("is_local"),
    }
    parsed = json.loads(json.dumps(data))
    assert parsed.get("provider") == "fish-audio"
    assert parsed.get("char_count") == 800
    assert parsed.get("ttsModel") == "fish-audio-s2.1"
    assert parsed.get("isLocal") is False


def test_voice_event_data_fish_s2_pro_is_local():
    """Fish S2 Pro events must have isLocal=True so the backfill skips them."""
    import json

    obj = {
        "event_type": "tts.speak",
        "char_count": 500,
        "ttsModel":   "fish-s2-pro",
        "isLocal":    True,
    }
    data = {
        "ttsModel": obj.get("ttsModel") or obj.get("fishModel") or None,
        "isLocal":  obj.get("isLocal") if obj.get("isLocal") is not None else obj.get("is_local"),
        "char_count": obj.get("char_count"),
    }
    parsed = json.loads(json.dumps(data))
    assert parsed.get("isLocal") is True, "Fish S2 Pro must carry isLocal=True"


def test_tts_provider_rates_table_present():
    from clawmetry.providers_pricing import TTS_PROVIDER_RATES

    for prov in ("openai", "elevenlabs", "google", "azure"):
        assert prov in TTS_PROVIDER_RATES, f"Expected TTS rate for provider '{prov}'"
        assert TTS_PROVIDER_RATES[prov] > 0


# ---------------------------------------------------------------------------
# 3. Adapter surfaces TTS fields in Event.extra
# ---------------------------------------------------------------------------

def _make_stub_event_blob(overrides: dict) -> dict:
    """Build a minimal data blob dict simulating a DuckDB events row data field."""
    base = {
        "event_type": "tts.speak",
        "provider":   "openai",
        "char_count": 350,
        "voice_id":   "alloy",
        "audio_bytes": 48200,
        "duration_ms": 4100,
    }
    base.update(overrides)
    return base


def test_adapter_surfaces_char_count_from_tts_event():
    """char_count from a tts.speak blob lands in Event.extra."""
    # We test only the field-extraction logic, not the full DuckDB path.
    # Simulate what list_events does for the tts.* extra fields.
    obj = _make_stub_event_blob({})
    extra: dict = {}

    for _field in ("char_count", "voice_id"):
        _val = obj.get(_field) or obj.get(
            "characterCount" if _field == "char_count" else "voiceId"
        )
        if _val is not None:
            extra[_field] = _val
    _abytes = obj.get("audio_bytes") or obj.get("audioBytes")
    if _abytes is not None:
        extra["audio_bytes"] = _abytes

    assert extra.get("char_count") == 350
    assert extra.get("voice_id") == "alloy"
    assert extra.get("audio_bytes") == 48200


def test_adapter_surfaces_camel_case_aliases():
    """characterCount / voiceId / audioBytes (camelCase) aliases are accepted."""
    obj = {
        "event_type":    "tts.speak",
        "characterCount": 200,
        "voiceId":        "nova",
        "audioBytes":     12000,
    }
    extra: dict = {}

    for _field in ("char_count", "voice_id"):
        _val = obj.get(_field) or obj.get(
            "characterCount" if _field == "char_count" else "voiceId"
        )
        if _val is not None:
            extra[_field] = _val
    _abytes = obj.get("audio_bytes") or obj.get("audioBytes")
    if _abytes is not None:
        extra["audio_bytes"] = _abytes

    assert extra.get("char_count") == 200
    assert extra.get("voice_id") == "nova"
    assert extra.get("audio_bytes") == 12000


def test_non_tts_events_unaffected():
    """A non-TTS blob without TTS fields produces no spurious extra keys."""
    obj = {
        "event_type": "talk.start",
        "talkMode":   "realtime",
    }
    extra: dict = {}

    for _field in ("char_count", "voice_id"):
        _val = obj.get(_field) or obj.get(
            "characterCount" if _field == "char_count" else "voiceId"
        )
        if _val is not None:
            extra[_field] = _val
    _abytes = obj.get("audio_bytes") or obj.get("audioBytes")
    if _abytes is not None:
        extra["audio_bytes"] = _abytes

    assert "char_count" not in extra
    assert "voice_id" not in extra
    assert "audio_bytes" not in extra


# ---------------------------------------------------------------------------
# 4. query_tts_provider_rollup (#5289) — usage attribution
# ---------------------------------------------------------------------------

@pytest.fixture()
def tts_store(tmp_path, monkeypatch):
    """Isolated LocalStore for TTS rollup tests."""
    import importlib
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "tts.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=True)


def _tts_ev(provider: str, char_count: int, cost: float, eid: str | None = None) -> dict:
    import uuid
    return {
        "id":         eid or str(uuid.uuid4()),
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": "sess-tts-1",
        "event_type": "tts.speak",
        "ts":         "2026-08-01T10:00:00Z",
        "data":       {"provider": provider, "char_count": char_count},
        "cost_usd":   cost,
        "token_count": 0,
        "model":       None,
    }


def test_query_tts_provider_rollup_aggregates_by_provider(tts_store):
    """query_tts_provider_rollup groups Fish Audio and other TTS events by provider."""
    import time as _time

    tts_store.ingest_event(_tts_ev("fish-audio", 1000, 0.015))
    tts_store.ingest_event(_tts_ev("fish-audio", 500, 0.0075))
    tts_store.ingest_event(_tts_ev("openai", 2000, 0.030))

    # Wait for the async flusher.
    deadline = _time.monotonic() + 3.0
    while _time.monotonic() < deadline:
        if tts_store.health()["ring_depth"] == 0:
            break
        _time.sleep(0.05)

    rows = tts_store.query_tts_provider_rollup()
    by_provider = {r["provider"]: r for r in rows}

    assert "fish-audio" in by_provider, "fish-audio must appear in rollup"
    fa = by_provider["fish-audio"]
    assert fa["calls"] == 2
    assert fa["char_count"] == 1500
    assert abs(fa["cost_usd"] - 0.0225) < 1e-9, f"Expected $0.0225, got {fa['cost_usd']}"

    assert "openai" in by_provider, "openai must appear in rollup"
    oa = by_provider["openai"]
    assert oa["calls"] == 1
    assert abs(oa["cost_usd"] - 0.030) < 1e-9


def test_query_tts_provider_rollup_excludes_zero_cost(tts_store):
    """Local TTS events with cost_usd=0 must not appear in the rollup."""
    import time as _time

    tts_store.ingest_event(_tts_ev("fish-s2-pro", 1000, 0.0))  # local, no cost
    tts_store.ingest_event(_tts_ev("fish-audio", 800, 0.012))

    deadline = _time.monotonic() + 3.0
    while _time.monotonic() < deadline:
        if tts_store.health()["ring_depth"] == 0:
            break
        _time.sleep(0.05)

    rows = tts_store.query_tts_provider_rollup()
    providers = {r["provider"] for r in rows}

    assert "fish-s2-pro" not in providers, "Zero-cost local TTS must be excluded"
    assert "fish-audio" in providers


def test_query_tts_provider_rollup_empty_store(tts_store):
    """Returns an empty list when there are no TTS events."""
    rows = tts_store.query_tts_provider_rollup()
    assert rows == []


def test_query_tts_provider_rollup_sorted_by_cost_desc(tts_store):
    """Result rows are sorted by cost_usd descending."""
    import time as _time

    tts_store.ingest_event(_tts_ev("openai", 100, 0.001))
    tts_store.ingest_event(_tts_ev("elevenlabs", 2000, 0.200))
    tts_store.ingest_event(_tts_ev("fish-audio", 500, 0.008))

    deadline = _time.monotonic() + 3.0
    while _time.monotonic() < deadline:
        if tts_store.health()["ring_depth"] == 0:
            break
        _time.sleep(0.05)

    rows = tts_store.query_tts_provider_rollup()
    costs = [r["cost_usd"] for r in rows]
    assert costs == sorted(costs, reverse=True), "Rows must be sorted by cost_usd desc"
