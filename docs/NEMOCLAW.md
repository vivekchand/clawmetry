# NemoClaw / OpenShell support

ClawMetry automatically detects [NemoClaw](https://github.com/NVIDIA/NemoClaw) — NVIDIA's enterprise security wrapper for OpenClaw that runs agents inside sandboxed OpenShell containers.

No extra configuration is needed in most cases. The sync daemon auto-discovers session files whether they live in `~/.openclaw/` on the host or inside an OpenShell container.

### How it works

ClawMetry detects NemoClaw in two ways:

1. **Binary detection** — checks for the `nemoclaw` CLI and runs `nemoclaw status` to get sandbox info
2. **Container detection** — scans running Docker containers for `openshell`, `nemoclaw`, or `ghcr.io/nvidia/` images, then reads sessions via volume mounts or `docker cp`

Session files synced from NemoClaw containers are tagged with `runtime=nemoclaw` and `container_id` metadata in the cloud dashboard, so you can tell them apart from standard OpenClaw sessions at a glance.

### Recommended setup: sync daemon on the HOST

For the best experience, run ClawMetry's sync daemon on the **host machine** (not inside the sandbox). This avoids NemoClaw network policy restrictions.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

The sync daemon will automatically find sessions inside any running OpenShell containers.

### Optional: explicit sandbox name

If auto-detection doesn't work, point ClawMetry at the right sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Running inside the sandbox (advanced)

If you must run the sync daemon **inside** the OpenShell sandbox, add this egress rule to your NemoClaw network policy so it can reach the ClawMetry ingest API:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Apply with:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Ports and endpoints

| Endpoint | Port | Protocol | Required |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Yes (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | Yes (local dashboard UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | For container session discovery |

The sync daemon only makes outbound HTTPS calls to `ingest.clawmetry.com`. No inbound ports are required.
