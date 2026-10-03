# Capability-gap export

ClawMetry records when an agent asked for something it could not get. A tool
that does not exist on the machine. A permission check that refused the call.
A rate limit, a timeout or a context ceiling. A budget boundary that the
enforcement proxy closed. Each of these is a demand signal, and an external
measurement tool can consume them without reading any transcript.

This export is off by default. It sends nothing over the network. It adds no
dependency. It writes one JSONL file in a directory you choose.

## Turn it on

Set the variable for the daemon and restart it:

```bash
export CLAWMETRY_CAPGAP_EXPORT_DIR=~/.clawmetry/capability-gaps
clawmetry daemon restart
```

The daemon then appends to `capability_gaps.jsonl` in that directory on each
detector tick. The file is created with mode `0600` and is never truncated.
A second file, `capability_gaps.seen.json`, holds the dedup memory, so a
daemon restart does not replay the same records.

Unset the variable and restart to turn the export off. Existing files are
left in place.

## What a record carries

Each line is one JSON object. It has exactly these fields.

| Field | Meaning |
| --- | --- |
| `v` | Record schema version. `1` today. |
| `code` | One of the taxonomy codes below. |
| `taxonomy` | Always `MIX-E01-E08`. |
| `ts` | The timestamp of the recorded event. |
| `observed_at` | When the daemon classified it, in UTC. |
| `session_id` | The ClawMetry session id. |
| `runtime` | The runtime name, for example `codex` or `claude_code`. |
| `tool` | The tool name, capped at 120 characters. Empty for a model error. |
| `source` | `tool_result`, `api_error` or `approval`. |
| `marker` | The rule that fired. Always one of ClawMetry's own fixed strings. |
| `http_status` | The HTTP status on the event, or `null`. |
| `event_id` | The store id of the event or approval row. |

A record never carries prompts, task text, tool arguments, result bodies,
exception text, credentials or transcript content. The `marker` is the name
of the rule, such as `command not found` or `status:429`. It is never a
slice of the agent's output.

## Taxonomy

| Code | Meaning | Emitted today |
| --- | --- | --- |
| `E01_NO_MATCH` | The agent asked for a tool or capability that does not exist here. | Yes |
| `E02_NO_ACCESS` | An authentication or permission check refused the call. | Yes |
| `E03_NO_FIT` | The call did not fit the schema or a policy. | No |
| `E04_NEED_ALTERNATIVE` | The agent asked for a fallback. | No |
| `E05_CAPACITY_GAP` | A rate limit, timeout, context limit or capacity ceiling stopped the call. | Yes |
| `E06_RIGHTS_GAP` | A licensing or rights check refused the call. | No |
| `E07_EVIDENCE_GAP` | Provenance or verification was missing. | No |
| `E08_CAPITAL_NEED` | An explicit budget or billing boundary stopped the call. | Yes |

Four codes are emitted. The other four are declared so a consumer can rely
on the vocabulary. They stay silent until a recorded event shape maps to
them without guessing.

## How events are classified

Only two kinds of rows are candidates. A tool result that failed, by its
structured error flag, a non-zero exit code or a known failure phrase. An
error row from a model or runtime API. A successful tool result that mentions
a 429 in its output is not a gap. An assistant text turn is never classified.

The rules run in this order and the first match wins: `E08`, then `E05`,
then `E02`, then `E01`. Each rule reads the HTTP status, the structured
error type, then the failure text. A denied approval in the approvals table
is recorded as `E02_NO_ACCESS` with source `approval`.

Rows that fail without a mapped marker are failures, not gaps. They are not
exported. The classifier reads the same 200 event window per active session
that the Guard detectors read. The export runs on the detector cadence and
adds no new store query.

## Read it from the API

`GET /api/capability-gaps` classifies recent store rows on request. It
answers whether or not the export is on, so you can inspect the mapping
before you enable the file.

| Parameter | Meaning |
| --- | --- |
| `window` | Lookback, such as `1h`, `24h` or `7d`. Default `24h`. |
| `session` | One session id. The whole session is read. |
| `runtime` | One runtime name. |
| `code` | One taxonomy code. |
| `limit` | Records returned, default 200, maximum 2000. |

The response carries `gaps`, `count`, `by_code`, the taxonomy, the list of
emitted and declared-only codes, the record field list, and the export
state. `store_available` is `false` when the daemon did not answer, and
`gaps` is then an honest empty list. At most 5000 rows are scanned per
request. `scanned_rows` reports how many were read.

## Limits

- The mapping is conservative. A real gap with an unusual error text is not
  exported.
- Markers are substrings. A tool that prints `permission denied` while it
  fails for another reason is recorded as `E02_NO_ACCESS`.
- Records describe what the agent could not do. They do not say why, and they
  do not prove the agent needed it.
- The export covers sessions the detector pass considers active. Sessions
  idle longer than the detector window are not re-read.

Source: `clawmetry/capability_gaps.py`, `routes/capability_gaps.py`, and the
hook in `clawmetry/sync.py`. Tests: `tests/test_capability_gaps.py`.
Proposal: vivekchand/clawmetry#5412.
