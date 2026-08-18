# Track any SDK agent — out-loop cost attribution

The runtimes above all write sessions to disk. Your own **production agent** — the one you built on the OpenAI Agents SDK, LangChain, the Vercel AI SDK, LlamaIndex, E2B, or a plain `httpx` loop — doesn't. ClawMetry's zero-config interceptor still captures its LLM calls (cost, tokens, latency, errors) by monkey-patching `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (or the `CLAWMETRY_SOURCE=support-agent` env var) tags each call with a **named source**, so every product you run shows up as its own first-class, cost-attributable line in the dashboard's **🔌 Out-loop sources** card on Overview — calls, providers, latency, error rate per agent. No source set? The calls are still tracked; the card just stays hidden.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

This is the same data layer the runtime adapters feed (DuckDB → cloud snapshot), so out-loop sources sync to the cloud dashboard the same as everything else, E2E-encrypted.

