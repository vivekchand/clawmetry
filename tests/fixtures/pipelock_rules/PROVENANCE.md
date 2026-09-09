# Vendored detection corpus — `pipelock-rules` (community bundle)

Upstream: <https://github.com/luckyPipewrench/pipelock-rules>
Revision: `a84903dc2ddf40930437bdfdfbe2a027ad26b88c`
License: Apache License 2.0 — full text in `LICENSE.apache-2.0.txt`
Copyright: Copyright 2026 Josh Waldrep and the pipelock contributors

## What is here and why

`rules/` and `fixtures/` are copied **unmodified** from the upstream
`pipelock-community` bundle (`rules/pipelock-community`,
`fixtures/pipelock-community`). Only the healthcare PHI/PII bundle was left
behind — it is not our use case.

Each rule ships a `-true-positive.txt` fixture (text the rule must match) and
usually a `-false-positive.txt` fixture (near-miss text it must **not** match:
`ops_short`, `operations_a1b2…`, `ops-a1b2…` against a rule for `ops_`). The
false-positive halves are why this corpus is worth vendoring — we had no
external corpus for over-firing at all.

`tests/test_detectors_secret_value_corpus.py` reads these files. It is the
only consumer; nothing in `clawmetry/` imports them.

## Relationship to harden.run AIF

The proprietary `aif` binary (VizopsAI, Inc.) states in its NOTICE that its
"enforcement, MCP-proxy, DLP/secret-scanning, and agent-configuration logic"
is derived from or modeled on pipelock. AIF itself ships no source and its beta
licence forbids using it to build a competing product. This corpus comes from
the Apache-2.0 upstream instead, which carries no such restriction.

## Updating

Re-copy from the upstream revision, bump the revision above, and re-run
`tests/test_detectors_secret_value_corpus.py`. Do not hand-edit the fixture or
rule files: divergence from upstream is what makes a refresh unreviewable.
