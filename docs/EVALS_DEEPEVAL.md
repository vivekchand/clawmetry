# DeepEval metric engine (optional)

ClawMetry can run a curated set of [DeepEval](https://github.com/confident-ai/deepeval) agent metrics on your finished sessions, fully locally, using your own judge API key. DeepEval is Apache-2.0 and ships the strongest open-source catalogue of agent metrics; ClawMetry embeds it as an optional engine without giving up its privacy posture: your transcripts never leave your machine except to the judge provider you configured.

## Install

```bash
pip install "clawmetry[deepeval]"
```

The extra exists because DeepEval pulls roughly 70 packages. The base ClawMetry install stays small and never imports it. Python 3.10+ is required for the extra.

## Turn it on

The engine costs judge calls, so it is off until you name the metrics you want:

```bash
export CLAWMETRY_DEEPEVAL_METRICS="argument-correctness,conversation-completeness"
```

Then restart the sync daemon. Sessions are scored a few minutes after they finish, on the same scheduler as the answer-quality judge. Results land in the local DuckDB `eval_metrics` table and are served by `GET /api/evals/metrics`.

The judge key and provider are the same ones the answer-quality judge uses: set them in the dashboard (Evals tab) or via `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY` / `OPENROUTER_API_KEY`, or point the `custom` provider at a local OpenAI-compatible server such as Ollama for a completely key-free, offline setup.

## Metrics

| Slug | Question it answers | Needs |
|------|--------------------|-------|
| `argument-correctness` | Did each tool call use sensible inputs for the task? | judge key |
| `conversation-completeness` | Was what the user asked for actually delivered by the end? | judge key |

DeepEval's Task Completion metric is not offered: it requires DeepEval's own tracing decorators inside the agent process, which does not fit ClawMetry's read-only, post-hoc model. Tool Correctness (comparing against expected tools) belongs to golden suites, where the suite YAML supplies the expectation.

## Privacy contract

- DeepEval telemetry is force-disabled in code before the library is ever imported (`DEEPEVAL_TELEMETRY_OPT_OUT=1`, error reporting off). This is not configurable through ClawMetry.
- No Confident AI account is used or required; nothing is uploaded.
- All judge traffic goes through ClawMetry's own provider-direct HTTP judge: your configured provider, your key, with secrets and emails redacted from transcripts before they leave the box.
- Verified in development with a socket audit: a full metric run against a local Ollama judge makes zero external network connections.

## Knobs

| Env var | Default | Meaning |
|---------|---------|---------|
| `CLAWMETRY_DEEPEVAL_METRICS` | empty (off) | Comma-separated metric slugs to run |
| `CLAWMETRY_DEEPEVAL_BATCH` | 5 | Sessions per scheduler tick |
| `CLAWMETRY_DEEPEVAL_RATE_LIMIT` | 50 | Judge-call budget per hour for this engine |
| `CLAWMETRY_DEEPEVAL_JUDGE_MAX_TOKENS` | 1500 | Judge reply budget (JSON verdicts) |
| `CLAWMETRY_DEEPEVAL_MAX_TURNS` | 40 | Conversation tail length fed to multi-turn metrics |

`CLAWMETRY_EVALS_ENABLED=0` turns this engine off along with the rest of the eval system.
