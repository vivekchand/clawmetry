"""DeepEval bridge tests (clawmetry/deepeval_bridge.py).

CI does not install the ``deepeval`` extra, so these tests run against a FAKE
in-memory deepeval package installed via a meta-path loader. That is exactly
the point: the bridge must import, degrade, and stay honest with or without
the real package, and the telemetry opt-out contract must be provable without
letting real deepeval code anywhere near the test env.

The judge JSON-schema contract and the zero-egress claim were additionally
proven against REAL deepeval 4.1.5 + a local Ollama judge in the Phase 0
spike (socket-spy: zero external connects); the fakes here pin the wiring.
"""
from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
import json
import os
import sys
import types

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_FAKE_MODULES = (
    "deepeval",
    "deepeval.metrics",
    "deepeval.models",
    "deepeval.models.base_model",
    "deepeval.test_case",
)

# Captured by the fake loader at "import deepeval" time.
_IMPORT_TIME_ENV: dict[str, str | None] = {}


class _Recorder:
    """Shared mutable state the fake metrics write into."""

    def __init__(self):
        self.measured_cases: list = []
        self.metric_should_raise = False


def _build_fake_deepeval(recorder: _Recorder) -> dict[str, types.ModuleType]:
    deepeval = types.ModuleType("deepeval")
    deepeval.__version__ = "4.1.5-fake"
    deepeval.__path__ = []  # mark as package

    base_model = types.ModuleType("deepeval.models.base_model")

    class DeepEvalBaseLLM:
        pass

    base_model.DeepEvalBaseLLM = DeepEvalBaseLLM
    models_pkg = types.ModuleType("deepeval.models")
    models_pkg.__path__ = []

    test_case = types.ModuleType("deepeval.test_case")

    class _Simple:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    class LLMTestCase(_Simple):
        pass

    class ToolCall(_Simple):
        pass

    class ConversationalTestCase(_Simple):
        pass

    class Turn(_Simple):
        pass

    test_case.LLMTestCase = LLMTestCase
    test_case.ToolCall = ToolCall
    test_case.ConversationalTestCase = ConversationalTestCase
    test_case.Turn = Turn

    metrics = types.ModuleType("deepeval.metrics")

    class _FakeSchema:
        """Stands in for the pydantic response model DeepEval passes to
        ``generate`` — enough surface to exercise the bridge's contract."""

        @staticmethod
        def model_json_schema():
            return {"type": "object", "properties": {"verdict": {"type": "string"}}}

        @staticmethod
        def model_validate(data):
            if not isinstance(data, dict) or "verdict" not in data:
                raise ValueError("missing verdict")
            return {"validated": data}

    class _FakeMetric:
        def __init__(self, model=None, async_mode=True, include_reason=True):
            self.model = model
            self.async_mode = async_mode
            self.score = None
            self.reason = None

        def measure(self, case):
            if recorder.metric_should_raise:
                raise RuntimeError("judge exploded")
            recorder.measured_cases.append((type(self).__name__, case))
            # Exercise the judge's schema path exactly like a real metric.
            out = self.model.generate("judge this", schema=_FakeSchema)
            assert out == {"validated": {"verdict": "ok"}}
            self.score = 0.8
            self.reason = "fake reason"
            return self.score

        def is_successful(self):
            return (self.score or 0) >= 0.5

    class ArgumentCorrectnessMetric(_FakeMetric):
        pass

    class ConversationCompletenessMetric(_FakeMetric):
        pass

    metrics.ArgumentCorrectnessMetric = ArgumentCorrectnessMetric
    metrics.ConversationCompletenessMetric = ConversationCompletenessMetric

    return {
        "deepeval": deepeval,
        "deepeval.metrics": metrics,
        "deepeval.models": models_pkg,
        "deepeval.models.base_model": base_model,
        "deepeval.test_case": test_case,
    }


class _FakeDeepevalFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Serves the fake modules through the real import machinery so the
    bridge's ``import deepeval...`` statements trigger exec_module, letting
    us capture what the environment looked like AT import time."""

    def __init__(self, modules):
        self.modules = modules

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.modules:
            return importlib.util.spec_from_loader(fullname, self)
        return None

    def create_module(self, spec):
        return self.modules[spec.name]

    def exec_module(self, module):
        if module.__name__ == "deepeval":
            _IMPORT_TIME_ENV["telemetry_opt_out"] = os.environ.get(
                "DEEPEVAL_TELEMETRY_OPT_OUT")
            _IMPORT_TIME_ENV["error_reporting"] = os.environ.get(
                "ERROR_REPORTING")


@pytest.fixture
def bridge(monkeypatch):
    """Fresh bridge module + fake deepeval on the import path."""
    recorder = _Recorder()
    fakes = _build_fake_deepeval(recorder)
    finder = _FakeDeepevalFinder(fakes)
    for name in _FAKE_MODULES:
        monkeypatch.delitem(sys.modules, name, raising=False)
    sys.meta_path.insert(0, finder)
    monkeypatch.delenv("DEEPEVAL_TELEMETRY_OPT_OUT", raising=False)
    monkeypatch.delenv("CLAWMETRY_DEEPEVAL_METRICS", raising=False)
    _IMPORT_TIME_ENV.clear()

    sys.modules.pop("clawmetry.deepeval_bridge", None)
    import clawmetry.deepeval_bridge as deb
    importlib.reload(deb)

    yield deb, recorder

    try:
        sys.meta_path.remove(finder)
    except ValueError:
        pass
    for name in _FAKE_MODULES:
        sys.modules.pop(name, None)
    sys.modules.pop("clawmetry.deepeval_bridge", None)


class _FakeStore:
    def __init__(self, rows):
        self.rows = rows
        self.persisted: list[dict] = []

    def query_events(self, *, session_id=None, limit=500):
        return self.rows

    def persist_eval_metric(self, **kw):
        self.persisted.append(kw)


def _real_shape_rows(secret=""):
    """Rows in the REAL stored shape (data dict, repr-string nesting)."""
    return [
        {"event_type": "message", "ts": "2026-08-03T12:00:01+00:00",
         "data": {"role": "user", "content": "please check the deploy"}},
        {"event_type": "tool_call", "ts": "2026-08-03T12:00:02+00:00",
         "data": {"role": "assistant", "content": "",
                  "tool_calls": "[{'id': 't1', 'input': {'command': 'kubectl get pods'}, 'name': 'Bash'}]",
                  "tool_name": "Bash"}},
        {"event_type": "message", "ts": "2026-08-03T12:00:03+00:00",
         "data": {"role": "assistant",
                  "content": "Deploy is healthy." + secret}},
    ]


def _ok_judge(model, prompt, *, timeout=30.0, max_tokens=200):
    return '{"verdict": "ok"}'


# ── Import hygiene + telemetry contract ─────────────────────────────────────


def test_importing_bridge_never_imports_deepeval():
    for name in _FAKE_MODULES:
        sys.modules.pop(name, None)
    sys.modules.pop("clawmetry.deepeval_bridge", None)
    import clawmetry.deepeval_bridge  # noqa: F401
    assert "deepeval" not in sys.modules, (
        "clawmetry.deepeval_bridge must lazy-import deepeval; importing it "
        "at module load would put ~70 packages on the CLI startup path"
    )


def test_importing_clawmetry_never_imports_deepeval_bridge_eagerly():
    assert "deepeval" not in sys.modules


def test_telemetry_optout_set_before_deepeval_import(bridge):
    deb, recorder = bridge
    assert _IMPORT_TIME_ENV == {}  # nothing imported yet
    store = _FakeStore(_real_shape_rows())
    deb.score_session_deepeval(
        "s1", metrics=["argument-correctness"], store=store,
        judge_call=_ok_judge,
    )
    assert _IMPORT_TIME_ENV.get("telemetry_opt_out") == "1", (
        "DEEPEVAL_TELEMETRY_OPT_OUT must be set BEFORE the deepeval import "
        "(the v3.7.7 exfiltration incident, confident-ai/deepeval#2497)"
    )
    assert _IMPORT_TIME_ENV.get("error_reporting") == "0"


# ── Scoring end-to-end (fake engine, real-shape rows) ───────────────────────


def test_score_session_persists_engine_rows(bridge):
    deb, recorder = bridge
    store = _FakeStore(_real_shape_rows())
    results = deb.score_session_deepeval(
        "s1", metrics=["argument-correctness", "conversation-completeness"],
        store=store, judge_call=_ok_judge,
    )
    assert len(results) == 2
    assert all(r["engine"] == "deepeval" for r in results)
    assert all(r["score"] == 0.8 and r["passed"] is True for r in results)
    assert len(store.persisted) == 2
    assert {p["metric_slug"] for p in store.persisted} == {
        "argument-correctness", "conversation-completeness"}
    # The single-turn case carried the real tool call, revived from repr.
    kinds = {k for k, _ in recorder.measured_cases}
    assert kinds == {"ArgumentCorrectnessMetric", "ConversationCompletenessMetric"}
    single = next(c for k, c in recorder.measured_cases
                  if k == "ArgumentCorrectnessMetric")
    assert [tc.name for tc in single.tools_called] == ["Bash"]
    assert single.tools_called[0].input_parameters == {"command": "kubectl get pods"}


def test_secrets_are_redacted_before_metrics_see_them(bridge):
    deb, recorder = bridge
    secret = " Deploy key is sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123456789ABCDEF"
    store = _FakeStore(_real_shape_rows(secret=secret))
    deb.score_session_deepeval(
        "s1", metrics=["argument-correctness", "conversation-completeness"],
        store=store, judge_call=_ok_judge,
    )
    for _kind, case in recorder.measured_cases:
        blob = json.dumps(case.__dict__, default=lambda o: o.__dict__)
        assert "sk-ant-api03" not in blob, (
            "transcript text must pass _redact_for_judge before any metric"
        )


def test_judge_error_persists_skip_row_no_retry_burn(bridge):
    deb, recorder = bridge
    recorder.metric_should_raise = True
    store = _FakeStore(_real_shape_rows())
    results = deb.score_session_deepeval(
        "s1", metrics=["argument-correctness"], store=store,
        judge_call=_ok_judge,
    )
    assert results[0]["skipped"] is True
    assert results[0]["skip_reason"] == "judge_error"
    # Persisted anyway: the session must leave the pending set, otherwise the
    # scheduler would re-spend on the same broken session every tick.
    assert len(store.persisted) == 1
    assert store.persisted[0]["score"] is None


def test_no_input_skip_is_not_persisted(bridge):
    deb, _ = bridge
    store = _FakeStore([
        {"event_type": "message", "ts": "t",
         "data": {"role": "user", "content": "hello"}},
    ])  # no assistant reply -> neither case buildable
    results = deb.score_session_deepeval(
        "s1", metrics=["argument-correctness", "conversation-completeness"],
        store=store, judge_call=_ok_judge,
    )
    assert all(r["skip_reason"] == "no_input" for r in results)
    assert store.persisted == []


def test_missing_package_is_quiet_empty(bridge, monkeypatch):
    deb, _ = bridge
    monkeypatch.setattr(deb, "is_available", lambda: False)
    store = _FakeStore(_real_shape_rows())
    assert deb.score_session_deepeval("s1", store=store, judge_call=_ok_judge) == []
    assert store.persisted == []


def test_no_judge_key_never_spends(bridge, monkeypatch):
    deb, recorder = bridge
    monkeypatch.setattr(deb, "_judge_ready", lambda: False)
    store = _FakeStore(_real_shape_rows())
    assert deb.score_session_deepeval("s1", store=store) == []
    assert store.persisted == [] and recorder.measured_cases == []


def test_scheduler_entry_is_opt_in(bridge, monkeypatch):
    deb, _ = bridge
    calls = []
    monkeypatch.setattr(deb, "score_session_deepeval",
                        lambda sid, **kw: calls.append(sid) or [{"x": 1}])
    # No env -> off, even with everything else ready.
    monkeypatch.setattr(deb, "is_available", lambda: True)
    monkeypatch.setattr(deb, "_judge_ready", lambda: True)
    assert deb.score_pending_deepeval(store=_FakeStore([])) == 0
    assert calls == []
    # Env set -> runs over the pending set.
    monkeypatch.setenv("CLAWMETRY_DEEPEVAL_METRICS", "argument-correctness")

    class _S(_FakeStore):
        def query_sessions_missing_eval_metrics(self, **kw):
            assert kw.get("engine") == "deepeval"
            return [{"session_id": "a"}, {"session_id": "b"}]

    assert deb.score_pending_deepeval(store=_S([])) == 2
    assert calls == ["a", "b"]


# ── Catalogue honesty ───────────────────────────────────────────────────────


def test_catalogue_needs_extra_downgrade(monkeypatch):
    from clawmetry import evaluators

    class _Store:
        def query_eval_summary(self, **kw):
            return {"total": 1, "scored": 0}

        def query_outcomes(self, **kw):
            return []

    import clawmetry.deepeval_bridge as deb
    monkeypatch.setattr(deb, "is_available", lambda: False)
    p = evaluators.catalogue_with_coverage(_Store(), judge_ready=True)
    by = {e["slug"]: e for e in p["evaluators"]}
    assert by["argument-correctness"]["status"] == "needs_extra"
    assert by["conversation-completeness"]["status"] == "needs_extra"
    # needs_extra outranks needs_key: installing the engine is step one.
    p2 = evaluators.catalogue_with_coverage(_Store(), judge_ready=False)
    by2 = {e["slug"]: e for e in p2["evaluators"]}
    assert by2["argument-correctness"]["status"] == "needs_extra"

    # Cloud (no store): static status preserved, never mislabels a node.
    p3 = evaluators.catalogue_with_coverage(None, judge_ready=None)
    by3 = {e["slug"]: e for e in p3["evaluators"]}
    assert by3["argument-correctness"]["status"] == "live"

    # Extra installed + key present -> live on-box too.
    monkeypatch.setattr(deb, "is_available", lambda: True)
    p4 = evaluators.catalogue_with_coverage(_Store(), judge_ready=True)
    by4 = {e["slug"]: e for e in p4["evaluators"]}
    assert by4["argument-correctness"]["status"] == "live"

    # Installed but keyless -> needs_key (they are judge-backed).
    p5 = evaluators.catalogue_with_coverage(_Store(), judge_ready=False)
    by5 = {e["slug"]: e for e in p5["evaluators"]}
    assert by5["argument-correctness"]["status"] == "needs_key"


@pytest.mark.skipif(
    importlib.util.find_spec("deepeval") is None,
    reason="real deepeval not installed (clawmetry[deepeval] extra)",
)
def test_real_deepeval_judge_class_builds():
    """Smoke against the real package when present: the wrapper subclasses
    the real DeepEvalBaseLLM and the lazy namespace resolves."""
    sys.modules.pop("clawmetry.deepeval_bridge", None)
    import clawmetry.deepeval_bridge as deb
    ns = deb._deepeval_ns()
    judge = deb._judge_cls()("claude-haiku-4-5", judge_call=_ok_judge)
    assert judge.get_model_name().startswith("clawmetry-judge:")
    from deepeval.models.base_model import DeepEvalBaseLLM
    assert isinstance(judge, DeepEvalBaseLLM)
    assert ns["LLMTestCase"] is not None
