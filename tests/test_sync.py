"""Tests for clawmetry.sync — state save race condition."""

import json
import threading

import pytest


@pytest.fixture(autouse=True)
def temp_openclaw_dir(tmp_path, monkeypatch):
    """Point OpenClaw dir to a temp directory so tests don't pollute real data."""
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))
    return tmp_path


def _reload_sync():
    """Reload sync module to get fresh state after patching."""
    import importlib
    from clawmetry import sync

    importlib.reload(sync)
    return sync


class TestStateSaveRace:
    """Test that concurrent state saves don't cause data corruption."""

    def test_concurrent_atomic_updates_preserve_data(self, tmp_path, monkeypatch):
        """
        Using atomic update_state(), concurrent updates are serialized
        and no data is lost.
        """
        sync = _reload_sync()

        state_file = tmp_path / "sync-state.json"
        monkeypatch.setattr(sync, "STATE_FILE", state_file)

        state_file.write_text(json.dumps({"counter": 0}))

        def writer_thread(iterations=50):
            for i in range(iterations):
                sync.update_state(lambda s: s.update(counter=s.get("counter", 0) + 1))

        t1 = threading.Thread(target=writer_thread, args=(50,))
        t2 = threading.Thread(target=writer_thread, args=(50,))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        final_state = json.loads(state_file.read_text())
        assert final_state["counter"] == 100, (
            f"Expected counter=100, got {final_state['counter']} - "
            "atomic updates should prevent data loss"
        )
