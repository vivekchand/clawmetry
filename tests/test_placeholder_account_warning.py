"""The daemon must not silently run on a temporary placeholder account (the
recurring 'connected but 0 nodes under my login' trap). _cmd_status + the connect
flow detect a @clawmetry.auto/.linked account and warn with the relink command."""
import io
from contextlib import redirect_stdout
from clawmetry.cli import _is_placeholder_account, _warn_if_placeholder_account


def test_detects_placeholder_domains():
    assert _is_placeholder_account("agent+90652efd@clawmetry.linked") is True
    assert _is_placeholder_account("agent+abc12345@clawmetry.auto") is True
    assert _is_placeholder_account("VIVEK@GMAIL.COM") is False
    assert _is_placeholder_account("vivekchand19@gmail.com") is False
    assert _is_placeholder_account("") is False
    assert _is_placeholder_account(None) is False


def test_warn_prints_actionable_relink_for_placeholder():
    buf = io.StringIO()
    with redirect_stdout(buf):
        warned = _warn_if_placeholder_account("cm_x", email="agent+abc@clawmetry.linked")
    out = buf.getvalue()
    assert warned is True
    assert "TEMPORARY" in out
    assert "clawmetry connect --key" in out  # the exact fix
    assert "app.clawmetry.com/cloud" in out


def test_warn_silent_for_real_account():
    buf = io.StringIO()
    with redirect_stdout(buf):
        warned = _warn_if_placeholder_account("cm_x", email="vivekchand19@gmail.com")
    assert warned is False
    assert buf.getvalue() == ""
