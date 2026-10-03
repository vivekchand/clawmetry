## Feature Summary
Implements REQ-ASSIST-001 through REQ-ASSIST-004 as a default Assistant page with conversational analytical artifacts.
## Component Blueprint Composition
Existing Dives schema descriptor and SQL validation inform constrained plans. Existing custom dashboard storage persists reusable panels. Existing Advisor provider authentication supplies local credentials.
## Feature Components
```component
name: AssistantRoute
container: Flask
responsibilities:
	- Generate bounded analytical plans through a tool-free local harness or provider API
	- Execute validated SELECT queries through the daemon and synthesize evidence-grounded answers
	- Persist conversations via LocalStore
```
```component
name: AssistantPage
container: Browser
responsibilities:
	- Render conversation, speech composer and validated chart specifications
	- Save dashboard definitions and reopen history
```
## System Contracts
POST /api/assistant/chat accepts message, conversation_id, provider and optional api_key. It returns answer, panels, sources, conversation_id and explicit all-runtime scope. GET /api/assistant/status exposes provider availability without credentials. The daemon owns all DuckDB writes. Model HTML and JavaScript are never executed.
## Architecture Decision Records
### ADR-001: Constrained artifacts
Context: Arbitrary generated code could act on agent files. Decision: Render declarative Chart.js/table/metric specifications from read-only queries. Consequences: Flexible analytical panels without running generated scripts.
### ADR-002: Explicit managed availability
Context: Local users cannot share anonymous hosted balances. Decision: Reuse authenticated hosted billing only where its contract exists; never create a pretend local balance. Consequences: Harness and BYOK remain useful while managed linking is separate.

## Hosted component blueprint
Published and reloaded in the existing ClawMetry project:
https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/blueprints/4be233ec-e717-4886-a6e3-8bf855597abb
