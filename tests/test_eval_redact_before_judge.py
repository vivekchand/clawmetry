"""The eval transcript must be redacted before it goes to the judge LLM.

The judge is the ONE place raw session text leaves the machine (everything else
is E2E encrypted). Secrets (API keys/tokens) and PII (emails) must be scrubbed
first, reusing the ingest secret redactor + an email pass.
"""
import clawmetry.eval_runner as er


SECRET_BLOB = (
    "User alice@example.com asked to deploy.\n"
    "export ANTHROPIC_API_KEY=sk-ant-api03-ABCDEF1234567890abcdefXYZ\n"
    "Authorization: Bearer ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n"
    "second contact bob.smith@corp.io\n"
)


def test_redact_for_judge_scrubs_secrets_and_emails(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_REDACT", raising=False)
    out = er._redact_for_judge(SECRET_BLOB)
    assert "alice@example.com" not in out
    assert "bob.smith@corp.io" not in out
    assert "sk-ant-api03-ABCDEF1234567890abcdefXYZ" not in out
    assert "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" not in out
    assert "[REDACTED:email]" in out


def test_build_prompt_redacts_transcript(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_REDACT", raising=False)
    runner = er.EvalRunner()
    prompt = runner._build_prompt({"prompt": "Rate this."}, SECRET_BLOB)
    # The composed judge prompt (what actually gets sent) carries no raw secrets.
    assert "alice@example.com" not in prompt
    assert "sk-ant-api03-ABCDEF1234567890abcdefXYZ" not in prompt
    assert "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" not in prompt
    assert "TRANSCRIPT:" in prompt  # structure preserved


def test_opt_out_keeps_raw(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_REDACT", "0")
    assert er._redact_for_judge("contact me at a@b.com") == "contact me at a@b.com"


def test_empty_is_safe():
    assert er._redact_for_judge("") == ""
    assert er._redact_for_judge(None) is None
