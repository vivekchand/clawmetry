# Build your own UI

ClawMetry ships one dashboard. It is not the only one you are allowed to
have.

Every number the dashboard draws comes from a declared, versioned read
API called `q/1`. This page is about pointing something else at that same
API: a page you vibe-coded in an afternoon, a wall display for the team
room, a panel inside a tool you already use, a script that posts yesterday's
agent spend into Slack.

You create a scoped key, say which site may use it, and build.

```
clawmetry key create --name my-ui \
    --scope read:metrics --origin http://localhost:3000
```

## Two minutes, start to finish

**1. Create a key.** It is shown once.

```bash
clawmetry key create --name cost-board \
    --scope read:metrics \
    --origin http://localhost:3000
# -> cmk_a1b2c3d4_...
```

**2. Check it works.**

```bash
curl -H "Authorization: Bearer cmk_a1b2c3d4_..." \
     http://localhost:8900/api/q/1
```

That returns what the key can read: its scopes, and every query it may
run with the arguments each one takes.

**3. Ask for something real.**

```bash
curl -H "Authorization: Bearer cmk_a1b2c3d4_..." \
     "http://localhost:8900/api/q/1/aggregates?since=2026-09-01T00:00:00Z"
```

```json
{
  "shape": "aggregates",
  "rows": [
    {"day": "2026-09-08", "agent_id": "main",
     "event_count": 4059, "token_count": 887691, "cost_usd": 136.47}
  ],
  "count": 1,
  "contract": "q/1",
  "elapsed_ms": 38
}
```

That is the whole API. Everything below is detail.

## Building the UI with a coding agent

The API describes itself, in a form written for an agent to read in one
pass and scoped to the key you hand it:

```bash
curl -H "Authorization: Bearer $CLAWMETRY_KEY" \
     http://localhost:8900/api/q/1/llms.txt
```

Give that output to Claude Code, Cursor, v0, Lovable, or whatever you
build with, along with what you want. A prompt that works:

> Build a single-page dashboard for our team's AI agent spend.
>
> Data comes from the ClawMetry query API at `http://localhost:8900/api/q/1`.
> Authenticate with `Authorization: Bearer <key>`. The full API is below.
>
> I want: a line chart of daily cost for the last 30 days from
> `/aggregates`, a table of the top 10 models by spend from `/models`,
> and a per-runtime breakdown from `/runtimes`. Refresh every 60 seconds.
> Show the total spend for the period as the headline number.
>
> <paste the output of /api/q/1/llms.txt here>

Two things worth putting in the prompt, because they are what a generated
UI usually gets wrong:

- **The key belongs in an environment variable**, not in the page source.
  If it must be in the browser (a static page with no backend), give that
  page a `read:metrics` key and nothing more.
- **Link back into ClawMetry.** A custom view is best when it is narrow.
  When someone wants to know *why* a number moved, send them to
  `http://localhost:8900/#session=<id>` rather than rebuilding the session
  viewer.

There is a working starter in [`examples/custom-ui/`](../examples/custom-ui/)
if you would rather begin from something that already runs.

## Scopes

A key carries one or more scopes. It can run exactly the queries its
scopes cover and nothing else.

| Scope | Grants | Queries |
|---|---|---|
| `read:metrics` | Counts, tokens, cost and health. No prompts or replies. | `aggregates`, `models`, `runtimes`, `agent_graph`, `health` |
| `read:sessions` | One row per session: title, model, status, totals. | `sessions`, `rollup_sessions`, `search`, `similar_sessions` |
| `read:traces` | Spans, traces and outbound API calls. | `spans`, `traces`, `external_calls` |
| `read:content` | The turns themselves: prompts, replies, tool calls. | `events`, `transcript`, `transcript_page`, `replay_events`, `session_context` |

The generated table in [`QUERY_CONTRACT.md`](./QUERY_CONTRACT.md) is the
authority, along with every argument each query takes. Run
`clawmetry key scopes` for the same thing in a terminal.

Pick the narrowest scope that makes your UI work. `read:metrics` is
exactly the set of queries that cannot return a prompt, a reply or a file
path, which makes it the right choice for anything that renders in a
browser.

## What a key can and cannot do

**Can:** run the `q/1` read queries its scopes cover, from a site it
names, at up to 240 requests a minute.

**Cannot:** write anything. Pause, stop or kill an agent. Change a
policy, a budget, an alert or a cron. Create another key. Read a query
outside its scopes. Be used from an origin it does not name.

The API is GET only, so it cannot be the target of a cross-origin write
even in principle.

## About that origin

Every key must name the sites allowed to use it from a browser. There is
no wildcard, and the flag is not optional.

This is worth a paragraph, because it is the part people try to skip.
Your ClawMetry runs on `localhost`. Any page in any tab can already *send*
a request to `localhost`. The only reason that has never mattered is that
the browser refuses to let a page *read* the reply from an origin that
did not permit it. An API key with an origin allowlist is how you hand
out that permission one site at a time. A wildcard would hand it to every
site at once, including a page you did not open on purpose.

For a key used outside a browser (a cron job, a backend, a script), pass
`--origin none`. It gets no CORS header at all, which is correct: nothing
in a browser should be able to use it.

## Remote and self-hosted ClawMetry

The API works the same when ClawMetry is not on the caller's machine.
Point at that host instead of `localhost:8900`. The key is the whole
gate: unlike the rest of the dashboard, this surface does not trust a
request just because it came from the local machine.

If you use ClawMetry Cloud, note that session content is stored
end-to-end encrypted and decrypted in your browser, so the cloud cannot
serve it through a REST API even to you. Point custom UIs at the machine
your agents actually run on.

## Using MCP instead

If what you want is an agent that can *ask about* your runs rather than a
page that draws them, the MCP server is a better fit than this API:

```bash
clawmetry mcp install
```

It exposes sessions, cost, traces and health as MCP tools over stdio, so
Claude Code and other MCP clients can query them directly.

## When it does not work

**The browser console says "blocked by CORS policy".** The origin your
page is served from is not on the key's list. The message names the
origin the browser sent; create a key with that exact origin, scheme and
port included. `http://localhost:3000` and `http://127.0.0.1:3000` are
different origins.

**401 with "This API needs a key".** The `Authorization` header is not
arriving. Check for a proxy stripping it, and that the header is
`Authorization: Bearer cmk_...` with the word `Bearer`.

**401 with "not valid on this machine".** The key was revoked, or it
belongs to another install. `clawmetry key list` shows what this machine
knows about.

**403 with a scope name in it.** The key is real but does not cover that
query. The message says which scope is needed.

**429.** More than 240 requests in a minute on one key. Poll less often,
or raise `CLAWMETRY_API_RATE_LIMIT` on the machine running ClawMetry.

**503 saying the store could not be read.** Usually the sync daemon
restarting. If it persists, run `clawmetry doctor`.

## Managing keys

```bash
clawmetry key list              # what this machine has issued
clawmetry key list --all        # including revoked ones
clawmetry key scopes            # what each scope grants
clawmetry key revoke <id>       # takes effect on the next request
```

The same panel lives in the dashboard under **Security**.

Keys are stored in `~/.clawmetry/api_keys.json`, mode `0600`, as SHA-256
hashes. A stolen file cannot be replayed as a key, and a key you lose
cannot be recovered: create a new one and revoke the old.
