"""Out-loop source tagging: a production agent built on any SDK can name itself
so it becomes a first-class source in ClawMetry (clawmetry.track.set_source)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import clawmetry.interceptor as I
import clawmetry.track as T


def test_default_no_source():
    I.set_source("")
    os.environ.pop("CLAWMETRY_SOURCE", None)
    assert I._get_source() == ""


def test_set_source_tags_calls():
    T.set_source("support-agent")
    assert I._get_source() == "support-agent"
    I.set_source("")


def test_env_var_fallback():
    I.set_source("")
    os.environ["CLAWMETRY_SOURCE"] = "investment-agent"
    try:
        assert I._get_source() == "investment-agent"
    finally:
        os.environ.pop("CLAWMETRY_SOURCE", None)


def test_source_is_bounded_and_stripped():
    I.set_source("  " + "x" * 500 + "  ")
    assert len(I._get_source()) <= 120
    I.set_source("")
