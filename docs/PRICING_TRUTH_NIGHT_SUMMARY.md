# /pricing truth: overnight 2026-05-28 to 29

Five OSS PRs shipped against the open-core pricing audit (#2262). Every
line on the Starter and Pro cards now has code backing it. Enterprise
tier has its catalogue keys reserved; the heavy implementations
(SSO / RBAC / Helm / air-gapped) are tomorrow.

## Shipped (all merged to main)

| PR | What | Tests |
|----|------|-------|
| [#2274](https://github.com/vivekchand/clawmetry/pull/2274) | Per-tier feature catalogue matched to /pricing + shared `@gate("feature_key")` 402 decorator + per-tier event-retention values on `Entitlement`. 11 routes gated. | 15 + 9 |
| [#2283](https://github.com/vivekchand/clawmetry/pull/2283) | Custom-runtime HTTP ingest API (`POST /api/v1/runs/*`). Localhost-trusted by default, token-gated via `CLAWMETRY_INGEST_TOKEN`. | 10 |
| [#2285](https://github.com/vivekchand/clawmetry/pull/2285) | OTLP/HTTP push exporter (Datadog / Grafana / Honeycomb). Background thread, bounded queue, refuses to start without Pro entitlement. | 13 |
| [#2286](https://github.com/vivekchand/clawmetry/pull/2286) | PagerDuty (Events API v2) + OpsGenie (createAlert) alert sinks. Vendor keys never leak into other sinks' bodies (tested). | 11 |
| [#2295](https://github.com/vivekchand/clawmetry/pull/2295) | Daemon-side per-tier events-table prune. Hourly tick, uses `created_at` (millis) not `ts` (ISO), reads entitlement live. | 9 |

Total: **5 PRs, 58 new tests, all green locally, all green in CI.**

## How each /pricing line is now backed

| /pricing line | Where it lives |
|---|---|
| Free: 7-day retention | `_TIER_RETENTION_DAYS[OSS] = 7`, enforced by retention-prune thread |
| Starter: multi-runtime, fleet, cloud sync, all channels, approval queue, budget limits, per-runtime health timeline | `STARTER_FEATURES` (7 keys); existing route gates |
| Starter: 30-day retention | `_TIER_RETENTION_DAYS[CLOUD_STARTER] = 30` |
| Pro: per-run waste flags + compare, error triage, Self-Evolve, asset registry, eval suite, tool policy | `PRO_ONLY_FEATURES`; routes/selfevolve.py + routes/assets.py gated |
| Pro: OTel export to Datadog / Grafana / Honeycomb | `clawmetry/otel_push.py` + `/api/otel/export` (pull) + `/api/otel/push/flush` (push) |
| Pro: Custom webhooks + PagerDuty + OpsGenie | `_dispatch_alert_to_all_sinks` + new payload builders |
| Pro: Custom runtime ingest API | `routes/runtime_ingest.py` |
| Pro: 90-day retention | `_TIER_RETENTION_DAYS[CLOUD_PRO] = 90` |
| Enterprise: SIEM export | `clawmetry/siem.py` already shipped; now gated on `siem_export` entitlement |
| Enterprise: unlimited retention | `_TIER_RETENTION_DAYS[ENTERPRISE] = None` |
| Enterprise: SSO / RBAC / audit logs / air-gapped / data residency | catalogue keys reserved (`sso`, `rbac`, `audit_logs`, `air_gapped_license`, `custom_data_residency`). No-code-yet placeholders for the "call sales" flow. |

## What's deliberately deferred

Big-surface Enterprise pieces, all separately tracked:

- **SSO / SAML / OIDC / RBAC** - real auth surgery; needs an entitlement
  middleware that runs before the route gates, plus session-management
  rework. Multi-day effort.
- **Helm chart / Terraform module / air-gapped license bundle** - new
  packaging surface; cross-team coordination with installer + license CLI.
- **Self-hosted cloud dashboard companion** - currently the cloud
  dashboard is a separate codebase; productising the on-prem story is
  itself a tier.
- **Custom data residency** - cloud-side region pinning; needs
  ingest.clawmetry.com + Cloud SQL work, not just OSS.

The morning question is which of these to slot next.

## Behaviour today

Grace mode is still on (`CLAWMETRY_ENFORCE=0` default). Nothing changed
for existing installs - everyone still has full access. Setting
`CLAWMETRY_ENFORCE=1` flips all gated routes to 402 and starts honoring
per-tier retention immediately.

The migration window is still grace; the [release-on-merge] auto-bump
will publish 0.12.355+ once the [RELEASE] PR for #2295 lands.
