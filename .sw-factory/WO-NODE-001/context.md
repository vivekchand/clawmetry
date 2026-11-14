<!--lint disable strong-marker-->

# Work Order Entity Index: WO-NODE-001

**Initialized At (UTC):** 2026-10-15T09:54:47Z
**Current Status:** in_review

## Work Order

- WO-NODE-001: Node activity: observe changes and review risk (`node-activity-2026-10-15`)

## Requirements

- Node activity: observe changes, review risk and show coverage (`7619d6bd-85f0-4a34-be97-4e7710f64621`)

## Blueprints

- Node activity observation, review and visual replay (`72d9ec38-2671-4258-a5ad-ffe36c84b27c`)
- Linked Node activity feature blueprint (`30fa3bd8-d322-4b39-8674-6a86d73fb229`)

## Referenced Blueprints

Blueprints reached through `@…` mentions and links while reading linked blueprints.

- Local Observability Service (`b6347b91-09ce-41fd-8aa1-f20066d82f5d`)
- Governance Policy and Approval (`b1dc4360-9a11-4e4b-9488-9b5ddead1cdc`)

## Delivery

- Branch: feat/node-activity
- Pull Request URL: https://github.com/vivekchand/clawmetry/pull/6412

## Factory API notes

The requirement automatically created linked feature blueprint 30fa3bd8-d322-4b39-8674-6a86d73fb229. Its generated template was read and replaced with the reviewed composition. The complete composition was first saved in component blueprint 72d9ec38-2671-4258-a5ad-ffe36c84b27c before code began, because the create API refuses the locked Feature Blueprints category. REST was used in place of unavailable Factory MCP.

Cloud counterpart: https://github.com/vivekchand/clawmetry-cloud/pull/2613 (held for verified published wheel and pin).

The initial composition was saved before code in the writable Components category because the create API refuses locked Feature Blueprints. The automatically linked feature template was read and populated through PATCH. Factory REST replaces unavailable MCP; local Work Order artifacts are the execution record.
