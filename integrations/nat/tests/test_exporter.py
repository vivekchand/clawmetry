"""Tests for ClawMetryNATExporter."""
import json
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from clawmetry_nat.exporter import ClawMetryNATExporter


def _step(event_type, name="", metadata=None):
    return {"event_type": event_type, "name": name, "metadata": metadata or {}}


# ---------------------------------------------------------------------------
# JSONL fallback (no URL/API key)
# ---------------------------------------------------------------------------

class TestJSONLExport:
    def test_writes_jsonl_on_flush(self, tmp_path):
        exporter = ClawMetryNATExporter(
            jsonl_dir=str(tmp_path),
            flush_interval_sec=9999,   # disable auto-flush
            batch_size=100,
        )
        exporter.on_event(_step("WORKFLOW_START", name="test"))
        exporter.on_event(_step("LLM_END", name="s1", metadata={"output": "hi", "output_tokens": 5}))
        n = exporter.flush()
        exporter.close(timeout=1)

        assert n == 2
        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1
        lines = files[0].read_text().strip().splitlines()
        assert len(lines) == 2
        ev0 = json.loads(lines[0])
        assert ev0["type"] == "session"

    def test_unknown_events_not_written(self, tmp_path):
        exporter = ClawMetryNATExporter(
            jsonl_dir=str(tmp_path),
            flush_interval_sec=9999,
            batch_size=100,
        )
        exporter.on_event(_step("MYSTERY_TYPE"))
        n = exporter.flush()
        exporter.close(timeout=1)
        assert n == 0

    def test_auto_flush_triggered_by_batch_size(self, tmp_path):
        exporter = ClawMetryNATExporter(
            jsonl_dir=str(tmp_path),
            flush_interval_sec=9999,
            batch_size=3,
        )
        for _ in range(3):
            exporter.on_event(_step("WORKFLOW_START"))
        time.sleep(0.05)   # allow flush in same thread path

        files = list(tmp_path.glob("*.jsonl"))
        total_lines = sum(len(f.read_text().strip().splitlines()) for f in files)
        assert total_lines >= 3
        exporter.close(timeout=1)


# ---------------------------------------------------------------------------
# HTTP export
# ---------------------------------------------------------------------------

class TestHTTPExport:
    def test_posts_to_ingest_endpoint(self, tmp_path):
        responses = []

        def fake_urlopen(req, timeout=None):
            payload = json.loads(req.data)
            responses.append(payload)
            resp = MagicMock()
            resp.status = 200
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            exporter = ClawMetryNATExporter(
                clawmetry_url="http://localhost:3002",
                api_key="test-key",
                jsonl_dir=str(tmp_path),
                flush_interval_sec=9999,
                batch_size=100,
            )
            exporter.on_event(_step("WORKFLOW_START"))
            exporter.on_event(_step("LLM_END", metadata={"output": "done", "output_tokens": 10}))
            exporter.flush()
            exporter.close(timeout=1)

        assert len(responses) == 1
        assert "events" in responses[0]
        assert len(responses[0]["events"]) == 2
        assert responses[0]["source"] == "nat"

    def test_on_flush_error_callback(self, tmp_path):
        errors = []

        def fake_urlopen(req, timeout=None):
            import urllib.error
            raise urllib.error.HTTPError(url="", code=500, msg="err", hdrs=None, fp=None)

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            exporter = ClawMetryNATExporter(
                clawmetry_url="http://localhost:3002",
                api_key="test-key",
                jsonl_dir=str(tmp_path),
                flush_interval_sec=9999,
                batch_size=100,
                on_flush_error=errors.append,
            )
            exporter.on_event(_step("WORKFLOW_START"))
            exporter.flush()
            exporter.close(timeout=1)

        assert len(errors) == 1


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

class TestContextManager:
    def test_context_manager_closes(self, tmp_path):
        with ClawMetryNATExporter(jsonl_dir=str(tmp_path), flush_interval_sec=9999) as exp:
            exp.on_event(_step("WORKFLOW_START"))
        assert exp._closed is True

    def test_close_flushes_remaining(self, tmp_path):
        exp = ClawMetryNATExporter(jsonl_dir=str(tmp_path), flush_interval_sec=9999, batch_size=100)
        exp.on_event(_step("WORKFLOW_START"))
        exp.close(timeout=2)
        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1
