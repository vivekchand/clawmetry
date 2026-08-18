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

**Opt out** (any one of these disables it permanently):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

A network failure here never blocks `clawmetry` from running — the
ping is fire-and-forget on a daemon thread with a 3 s timeout.

