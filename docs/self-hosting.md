# Self-hosting ClawMetry

The operator guide for running the ClawMetry server inside your own
infrastructure. The step-by-step Compose runbook is
[`deploy/self-hosted/README.md`](../deploy/self-hosted/README.md); this page
covers what you deploy, how to check the image before you run it, how to
operate it, and what is not available yet.

## What you deploy

| | Local dashboard | Customer-hosted server |
|---|---|---|
| Where it runs | Each machine that runs agents (`pip install clawmetry`) | One container you operate |
| What it shows | That machine's sessions, cost and Guard, at `http://127.0.0.1:8900` | A fleet page (`/selfhosted`: node roster, daemon versions, liveness) plus node status and audit export APIs |
| Where data lives | A local store on that machine | Every connected node's heartbeats, sessions and events, in one volume |
| How nodes reach it | Not applicable | `CLAWMETRY_ENDPOINT=<your server> clawmetry connect --key cm_...` |

The server does not replace each node's own dashboard: detailed per-session
views stay on the node. It is single-tenant and runs as one instance.

## The image

`ghcr.io/vivekchand/clawmetry:<version>` is published for `linux/amd64` and
`linux/arm64` by
[`container-image.yml`](../.github/workflows/container-image.yml) after each
release. It is built from the wheel PyPI serves for that version, after that
wheel's build provenance has been verified, with the OTLP decoder extra. It
contains the open-source package and its public dependencies. It does not
contain the Pro plugin.

Image defaults, each of which you can override with `-e`: `SELF_HOSTED=true`,
`CLAWMETRY_NO_TELEMETRY=1`, `CLAWMETRY_NO_CLOUD=1`, and
`CLAWMETRY_AUTO_UPDATE=0` (a signed image never installs a different version
into itself; you upgrade by pulling a new digest).

**Has an image been published yet?** Open
`deploy/self-hosted/docker-compose.yml`. The release pipeline pins it to
`image: ghcr.io/vivekchand/clawmetry:<version>@sha256:<digest>` only after that
digest has passed every check below. While the file still has a `build:` block,
no image has passed verification and Compose builds from your checkout.

## Check the image before you run it

The signature is keyless and bound to the publishing workflow:

```bash
IMAGE=ghcr.io/vivekchand/clawmetry:<version>@sha256:<digest>
IDENTITY=https://github.com/vivekchand/clawmetry/.github/workflows/container-image.yml@refs/heads/main
ISSUER=https://token.actions.githubusercontent.com

cosign verify "$IMAGE" --certificate-identity "$IDENTITY" --certificate-oidc-issuer "$ISSUER"
```

The SBOM is SPDX JSON, one per platform, attested to that platform's manifest
digest (`docker buildx imagetools inspect "$IMAGE"` lists both digests):

```bash
cosign verify-attestation --type spdxjson \
  --certificate-identity "$IDENTITY" --certificate-oidc-issuer "$ISSUER" \
  ghcr.io/vivekchand/clawmetry@sha256:<platform digest>
```

Build provenance (needs a signed-in `gh`):

```bash
gh attestation verify "oci://$IMAGE" --repo vivekchand/clawmetry
```

Or run exactly what the release pipeline runs. It needs Docker, cosign and
Python 3.9 or newer, and it pulls with an empty Docker config, so a stored
registry login cannot make a private image look public:

```bash
python3 scripts/verify_selfhosted_image.py --anonymous --image "$IMAGE"
```

It checks the architecture, the signature and the SBOM, confirms no Pro plugin
is inside, then starts the image on a scratch volume, sends one non-sensitive
event through the node ingest API, restarts the container, and confirms the
event is still in the audit export and the node is still on the fleet page.

## Authentication and transport, as shipped

- **Nodes** authenticate with a token from `CLAWMETRY_API_TOKENS`
  (comma-separated, each starting with `cm_`).
- **Admins** authenticate as one HTTP Basic user, `CLAWMETRY_ADMIN_USER` and
  `CLAWMETRY_ADMIN_PASSWORD`. The fleet page, node list, status and audit export
  require it (the APIs also accept a node token). These credentials work from
  any network address, including through a container port.
- **Runtimes that export OpenTelemetry directly** authenticate as described in
  the runbook's "Onboarding without a per-machine daemon" section.
- There is no single sign-on, user directory or role model on the self-hosted
  server.
- The container speaks **plain HTTP** on port 8900. Terminate TLS in front of it.
- Node events arrive in plaintext inside your deployment by default.
  `CLAWMETRY_SELF_HOSTED_E2E=1` makes nodes send encrypted blobs instead, and
  the audit export then holds envelope metadata only. OpenTelemetry records
  always arrive in plaintext.
- The process runs as root inside the container, so the store stays at
  `/root/.clawmetry`, the path the Compose volume has always mounted.

## Update and roll back

Deploy by digest, never by tag alone.

1. Back up first (next section).
2. Set `image:` to the new `ghcr.io/vivekchand/clawmetry:<version>@sha256:<digest>`.
   The pin pull request each release opens carries the verified value. Then run
   `docker compose pull && docker compose up -d`.
3. To roll back, set `image:` back to the previous digest and run
   `docker compose up -d`. Schema changes are additive, but running an older
   server against a store a newer one has written is not supported: restore the
   backup from step 1.

Not yet exercised in automation: an upgrade from one published digest to the
next, a rollback, and a restore. The release pipeline exercises one digest
restarting with its data intact.

## Back up and restore

All state is on the Compose volume (`docker volume ls` shows its name; Compose
prefixes it with the project directory, for example
`self-hosted_clawmetry-data`): `selfhosted.db` (the SQLite ingest and audit
store), the local event store, and `config.json`.

Online backup of the SQLite store. The image has no `sqlite3` binary, and
Python's backup API is safe while the server is writing:

```bash
docker compose exec clawmetry python3 -c "import sqlite3; s = sqlite3.connect('/root/.clawmetry/selfhosted.db'); d = sqlite3.connect('/root/.clawmetry/backup.db'); s.backup(d); d.close(); s.close()"
docker cp "$(docker compose ps -q clawmetry)":/root/.clawmetry/backup.db ./selfhosted-backup.db
```

Whole volume, with the server stopped:

```bash
docker compose stop
docker run --rm --entrypoint tar -v self-hosted_clawmetry-data:/data -v "$PWD":/backup \
  "$IMAGE" czf /backup/clawmetry-data.tgz -C /data .
docker compose start
```

To restore, stop the server, empty the volume, extract the archive into it the
same way (`tar xzf /backup/clawmetry-data.tgz -C /data`), and start the server.
Test a restore in a scratch Compose project before you rely on it.

## Retention and removal

- Nothing is deleted automatically. The ingest log is append-only and the
  server never updates or deletes its rows, so the volume grows with event
  volume. Size it for that.
- `docker compose down` removes the container and keeps the volume.
  `docker compose down -v` also deletes the volume, which permanently deletes
  every stored event and node record.
- Removing the server does not change your nodes. Each keeps its local
  dashboard; point one elsewhere by setting `CLAWMETRY_ENDPOINT` and running
  `clawmetry connect` again.

## Not available yet

None of these is supported for the self-hosted server today, and none is
implied by the image starting:

- Single sign-on: Entra ID, OIDC or SAML login.
- Platform quickstarts: Azure Container Apps, AWS ECS, Kubernetes or Helm.
- Offline or air-gapped installation. No offline install path has been
  verified, and the image's outbound traffic has not been measured.
- Automated retention or deletion.
- A non-root image.
- More than one server instance, or high availability.
