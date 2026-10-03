## Summary
Deliver a chat opening screen and persistent data-backed visuals on the latest codebase.
## In Scope
Assistant route, provider dispatch, query safety, chat persistence, interactive rendering, navigation integration and live browser verification.
## Out of Scope
Executing generated arbitrary scripts or changing agent configuration from a chat answer.
## Requirements
requirements.md: REQ-ASSIST-001 through REQ-ASSIST-004.
## Blueprints
blueprint.md: AssistantRoute and AssistantPage.
## E2E Acceptance Tests
COV_ASSIST_001: Open local dashboard, verify composer, provider state, starters and accessible voice denial.
COV_ASSIST_002: Ask a real harness for cost and token panels, inspect plotted real rows, ask follow-up, verify missing-data honesty and unsafe SQL rejection. tests/test_assistant_route.py and tests/test_assistant_store.py.
COV_ASSIST_003: Save generated panel, reload Home and conversation, confirm persistence. Check failed storage gives visible error.
COV_ASSIST_004: Check provider status has no secrets or fictional balance; malformed credentials/requests yield safe errors.
