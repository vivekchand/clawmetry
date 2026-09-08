# Telemetry — the anonymous install ping

ClawMetry sends anonymous install-lifecycle pings to
`https://app.clawmetry.com/api/install`: one `install` ping the first
time you run the `clawmetry` CLI on a new machine, one `update` ping
the first run after upgrading to a new version, and one `onboarded`
ping when you complete the in-dashboard onboarding choice. We use this
to count real installs (raw PyPI download numbers are ~98% mirrors, CI,
and auto-update re-downloads) and to learn which agent frameworks and
versions are actually in the wild.

**At most one POST per lifecycle event per version**, containing:

| Field | Example | Why |
|---|---|---|
| `install_id` | random UUID stored at `~/.clawmetry/install_id` | dedup; anonymous until you explicitly connect Cloud sync (the authenticated daemon heartbeat then carries it, linking this install to your account) |
| `event` | `install` / `update` / `onboarded` | fresh install vs upgrade of an existing one |
| `version` | `0.12.167` | what versions are in the wild |
| `os` / `os_version` | `Darwin` / `25.3.0` | platform support priorities |
| `python` | `3.11.15` | Python version support matrix |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | which agents we should integrate with next |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separate human installs from CI noise |

**What we do NOT send**: IP (cloud derives the country code server-side
from the request, then discards the IP), hostname, username, workspace
path, file contents, your api_key, your email, anything PII or
workspace-specific. The wire payload is auditable in
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

## The desktop app's open ping

The macOS/Windows/Linux desktop app additionally posts to
`https://app.clawmetry.com/api/desktop/open` **once per launch**, so we
can tell a download apart from an actual open, and a first open apart
from the fiftieth. It goes out in two stages: the shell pings the moment
the window appears (this one fires even when the app fails to bootstrap
its Python runtime — otherwise we would never hear about the launches
that break), and the daemon pings once the dashboard is actually live.

| Field | Example | Why |
|---|---|---|
| `install_id` | the same UUID as above | one machine is one install, not two |
| `session_id` | random UUID per launch | pairs the two stages of one launch |
| `open_count` / `first_open` | `7` / `false` | first open vs nth; opens counted locally, so offline launches still count |
| `stage` | `shell` / `daemon` | opened vs opened-and-working |
| `desktop_version` / `version` | `0.12.900` / `0.12.900` | which bundle, and which pip release it pulled |
| `os` / `os_version` / `arch` | `Windows` / `11` / `AMD64` | platform support priorities |
| `mode` | `cloud` / `local` / `unknown` | how many installs sync to Cloud vs stay entirely local |
| `runtimes` | `["openclaw", "claude_code"]` | which agent runtimes this machine has data for — **ids only**, no paths, no session contents, no counts |

If the app is paired with a Cloud account, the ping carries your API key
as a bearer header — never in the stored body — purely so the machine
shows up under **Desktop apps** on your own account page. Unpaired
installs stay anonymous.

Everything above is subject to the same opt-outs, and an enterprise
endpoint (`CLAWMETRY_ENDPOINT`, or `endpoint` in
`~/.clawmetry/config.json`) disables both pings entirely — a self-hosted
deployment's data stays inside the deployment.

**Opt out** (any one of these disables it permanently):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

A network failure here never blocks `clawmetry` from running — the
ping is fire-and-forget on a daemon thread with a 3 s timeout.

