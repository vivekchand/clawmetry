"""Conversations time-window filter: /api/transcripts must ship `started`.

The tab's window filter runs an overlap test on [started, modified] so a
conversation that began before the picked window but was still active inside
it is listed. The DuckDB fast path derives `started` from the session row's
started_at; 0 = unknown (client falls back to started = modified).
"""
from __future__ import annotations

from unittest.mock import patch

import routes.sessions as sessions_mod


def test_fast_path_emits_started_ms():
    rows = [{
        "session_id": "sess-window-1",
        "started_at": "2026-07-29T01:00:00+00:00",
        "updated_at": "2026-07-29T09:30:00+00:00",
        "message_count": 4,
    }]
    with patch.object(sessions_mod, "_ls_call", return_value=rows), \
         patch.object(sessions_mod, "_first_user_title", return_value="hello"), \
         patch.object(sessions_mod, "hide_clawmetry_session", return_value=False):
        out = sessions_mod._try_local_store_transcripts()
    assert out and out["transcripts"], "fast path returned nothing"
    t = out["transcripts"][0]
    assert t["started"] == 1785286800000   # 2026-07-29T01:00:00Z in ms
    assert t["modified"] == 1785317400000  # 2026-07-29T09:30:00Z in ms
    assert t["started"] <= t["modified"]


def test_fast_path_started_defaults_to_zero_when_missing():
    rows = [{
        "session_id": "sess-window-2",
        "updated_at": "2026-07-29T09:30:00+00:00",
        "message_count": 1,
    }]
    with patch.object(sessions_mod, "_ls_call", return_value=rows), \
         patch.object(sessions_mod, "_first_user_title", return_value=""), \
         patch.object(sessions_mod, "hide_clawmetry_session", return_value=False):
        out = sessions_mod._try_local_store_transcripts()
    assert out["transcripts"][0]["started"] == 0
