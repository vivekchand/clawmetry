<!--lint disable strong-marker-->

# Work Order Entity Index: WO-ASIMOV-001

**Initialized At (UTC):** 2026-10-15T20:04:27Z
**Current Status:** in_progress

## Work Order

- WO-ASIMOV-001: Asimov 1 observation connector (`local:WO-ASIMOV-001`)

## Requirements

- [Asimov 1 observation connector](https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/requirements/a508a5c5-8821-4964-8930-3561b7d02f2b), mirrored in requirements.md and hosted-requirements.json

## Blueprints

- [Asimov 1 observation architecture](https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/blueprints/706e78ef-e74a-4ced-9f17-68eade47ca94), local design in blueprint.md

## Referenced Blueprints

Blueprints reached through `@…` mentions and links while reading linked blueprints.

## Delivery

- Branch: feat/asimov-support
- Pull Request URL: https://github.com/vivekchand/clawmetry/pull/6442

## Execution notes
- User authorized implementation and teamwork; root owns OSS ingest/query/UI and SDK delegate owns collector/tracer/import.
- Local plan, requirements and blueprint written before source changes.
- Hosted records were published through the authenticated Factory editor, then verified by authenticated API GET. See factory-status.md.
- Requirement acceptance: REQ-ASIMOV-001 through REQ-ASIMOV-006, including free local inspection without Pro under license enforcement and client-decrypted payload.asimov cloud parity.
- Referenced blueprints: none beyond local self-contained blueprint.md. Prior Pro/cloud code was inspected as implementation contracts, not as invented blueprint mentions.
- Shared ownership: RP1 #340 owns humanoid.js/app.js/catalogue and candidate rollout. Do not edit .worktrees/rp1-pro or .worktrees/rp1-cloud.
- Reused merged implementation: Pro #338 at 92368cacdb7434f994700020de8406ba15c79e5a; cloud #2623 at ecf7e7dab5abe4f4458715aa31359ae01626c2f5.
- Live hardware qualification and founder outreach remain separate from this work order. No robot credential, hardware test or outreach is implied by these records.
