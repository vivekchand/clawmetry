"""Tests for NATEventMapper."""
import pytest
from clawmetry_nat.mapper import NATEventMapper


SESSION_ID = "test-session-1234"


def make_mapper():
    return NATEventMapper(session_id=SESSION_ID, model="test-model")


# ---------------------------------------------------------------------------
# Dict-style NAT step helpers
# ---------------------------------------------------------------------------

def _step(event_type, name="", metadata=None):
    return {"event_type": event_type, "name": name, "metadata": metadata or {}}


# ---------------------------------------------------------------------------
# Session events
# ---------------------------------------------------------------------------

class TestSessionEvents:
    def test_workflow_start_maps_to_session_start(self):
        mapper = make_mapper()
        ev = mapper.map(_step("WORKFLOW_START", name="my-workflow"))
        assert ev is not None
        assert ev["type"] == "session"
        assert ev["session_id"] == SESSION_ID
        assert ev["data"]["event"] == "start"

    def test_task_start_alias(self):
        mapper = make_mapper()
        ev = mapper.map(_step("task_start"))
        assert ev["data"]["event"] == "start"

    def test_workflow_end_maps_to_session_end(self):
        mapper = make_mapper()
        ev = mapper.map(_step("WORKFLOW_END", metadata={"total_tokens": 1000, "total_cost": 0.05}))
        assert ev["type"] == "session"
        assert ev["data"]["event"] == "end"
        assert ev["data"]["summary"]["total_tokens"] == 1000
        assert ev["data"]["summary"]["total_cost"] == pytest.approx(0.05)

    def test_task_end_alias(self):
        mapper = make_mapper()
        ev = mapper.map(_step("task_end"))
        assert ev["data"]["event"] == "end"


# ---------------------------------------------------------------------------
# LLM events
# ---------------------------------------------------------------------------

class TestLLMEvents:
    def test_llm_start_maps_to_user_message(self):
        mapper = make_mapper()
        ev = mapper.map(_step("LLM_START", metadata={"prompt": "Hello?", "model": "gpt-4"}))
        assert ev["type"] == "message"
        assert ev["message"]["role"] == "user"
        assert ev["message"]["content"] == "Hello?"
        assert ev["message"]["model"] == "gpt-4"

    def test_llm_end_maps_to_assistant_message_with_usage(self):
        mapper = make_mapper()
        # Simulate start first for span tracking
        start = _step("LLM_START", name="span-1", metadata={"prompt": "test"})
        mapper.map(start)

        end = _step("LLM_END", name="span-1", metadata={
            "output": "Hi there!",
            "input_tokens": 100,
            "output_tokens": 50,
            "cost": 0.002,
        })
        ev = mapper.map(end)
        assert ev["message"]["role"] == "assistant"
        assert ev["message"]["content"] == "Hi there!"
        assert ev["message"]["usage"]["input"] == 100
        assert ev["message"]["usage"]["output"] == 50
        assert ev["message"]["usage"]["cost"]["total"] == pytest.approx(0.002)

    def test_llm_end_duration_computed(self):
        mapper = make_mapper()
        mapper.map(_step("LLM_START", name="dur-test"))
        import time; time.sleep(0.01)
        ev = mapper.map(_step("LLM_END", name="dur-test", metadata={"output": "ok"}))
        assert ev["durationMs"] >= 0

    def test_llm_call_alias(self):
        mapper = make_mapper()
        ev = mapper.map(_step("llm_call", metadata={"input_tokens": 10, "output_tokens": 5}))
        # llm_call is in LLM_START_TYPES — maps to user message
        assert ev["message"]["role"] == "user"


# ---------------------------------------------------------------------------
# Tool events
# ---------------------------------------------------------------------------

class TestToolEvents:
    def test_tool_start_maps_to_tool_call(self):
        mapper = make_mapper()
        ev = mapper.map(_step("TOOL_START", name="web_search", metadata={
            "tool_input": {"query": "ClawMetry NAT"}
        }))
        assert ev["type"] == "message"
        assert ev["message"]["role"] == "assistant"
        content = ev["message"]["content"]
        assert isinstance(content, list)
        assert content[0]["type"] == "toolCall"
        assert content[0]["name"] == "web_search"
        assert content[0]["arguments"]["query"] == "ClawMetry NAT"

    def test_tool_end_maps_to_tool_result(self):
        mapper = make_mapper()
        mapper.map(_step("TOOL_START", name="my_tool"))
        ev = mapper.map(_step("TOOL_END", name="my_tool", metadata={
            "tool_output": "result text"
        }))
        assert ev["message"]["role"] == "tool"
        content = ev["message"]["content"]
        assert content[0]["type"] == "toolResult"
        assert content[0]["output"] == "result text"
        assert content[0]["error"] is None

    def test_tool_end_with_error(self):
        mapper = make_mapper()
        mapper.map(_step("TOOL_START", name="err_tool"))
        ev = mapper.map(_step("TOOL_END", name="err_tool", metadata={
            "error": "timeout"
        }))
        assert ev["message"]["content"][0]["error"] == "timeout"

    def test_tool_call_alias(self):
        mapper = make_mapper()
        ev = mapper.map(_step("tool_call", name="bash"))
        assert ev["message"]["content"][0]["name"] == "bash"


# ---------------------------------------------------------------------------
# Object-style NAT step (duck-typed)
# ---------------------------------------------------------------------------

class TestObjectStyleStep:
    def test_object_with_event_type_attr(self):
        class FakeStep:
            def __init__(self):
                self.event_type = "WORKFLOW_START"
                self.name = "obj-workflow"
                self.metadata = {}

        mapper = make_mapper()
        ev = mapper.map(FakeStep())
        assert ev["data"]["event"] == "start"

    def test_enum_event_type(self):
        class FakeEnum:
            def __init__(self, val): self.value = val

        class FakeStep:
            def __init__(self):
                self.event_type = FakeEnum("LLM_END")
                self.name = "enum-test"
                self.metadata = {"output": "done", "output_tokens": 42}

        mapper = make_mapper()
        ev = mapper.map(FakeStep())
        assert ev["message"]["role"] == "assistant"
        assert ev["message"]["usage"]["output"] == 42


# ---------------------------------------------------------------------------
# Unknown event type
# ---------------------------------------------------------------------------

class TestUnknownEvent:
    def test_unknown_type_returns_none(self):
        mapper = make_mapper()
        ev = mapper.map(_step("UNKNOWN_TYPE"))
        assert ev is None

    def test_missing_event_type_returns_none(self):
        mapper = make_mapper()
        ev = mapper.map({})
        assert ev is None
