# Fuzz targets

Coverage-guided fuzzing with [Atheris](https://github.com/google/atheris) over
the two places ClawMetry parses input it did not write:

| Harness | Target | Why it is untrusted |
|---|---|---|
| `fuzz_otlp_json.py` | `clawmetry.otlp_json.decode` | The OTLP receiver (`/v1/traces`, `/v1/logs`, `/v1/metrics`) accepts a POST body from anything that can reach the dashboard port. This is an in-house stdlib decoder, so nothing else hardens it. |
| `fuzz_event_shape.py` | `clawmetry.event_shape.classify` / `typed_columns` | Session transcripts are JSONL written by the agent runtimes, not by us. A runtime that changes shape, or a half-written line, lands here. |

Each harness asserts a *contract*, not merely "it did not crash":

* `otlp_json.decode` must either return a request object or raise `ValueError`.
  Any other exception is a bug — `ValueError` is what the HTTP layer turns into
  a 400, so a `TypeError` escaping here is the difference between a clean
  rejection and a 500.
* `event_shape` must never raise, per the "never crash on bad input" rule in
  CLAUDE.md. It runs over every ingested transcript row, so one bad row
  raising would stall ingest for the whole session.

## Running

```bash
pip install atheris
python3 tests/fuzz/fuzz_otlp_json.py -atheris_runs=200000
python3 tests/fuzz/fuzz_event_shape.py -atheris_runs=200000
```

Drop a directory argument to fuzz from (and grow) a corpus:

```bash
python3 tests/fuzz/fuzz_otlp_json.py corpus/otlp/
```

CI runs both on a bounded run count in `supply-chain.yml`. The same contracts
are asserted over a fixed seed corpus by `tests/test_fuzz_targets.py`, which
needs no Atheris and so runs on every PR, on every OS in the matrix — that is
the regression net; the fuzzers are the search.

## Findings

The first run of these targets (2026-09-04) found three real contract
violations in `clawmetry/otlp_json.py`, all fixed in the same change:

1. `{"resourceSpans": 3}` — a scalar where OTLP specifies an array reached
   `for r in 3` and raised `TypeError`. Every repeated field had a per-item
   `isinstance(x, dict)` guard but no guard on the container itself, so this
   was one bug in fifteen places; fixed with the `_seq()` helper.
2. A non-gzip body sent with `Content-Encoding: gzip` raised
   `gzip.BadGzipFile` (an `OSError`).
3. A truncated gzip body raised `EOFError`.
