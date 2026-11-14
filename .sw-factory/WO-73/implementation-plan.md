# WO73: generic private robotics query seams

The owner requests detailed robot tracing/replay/guards/corrections. Paid capture,
storage, authorization and UI implementations stay in clawmetry-pro. The existing
normal-daemon robotics_query transport rejects new private operations before the
plugin, so add only constant allowlisted operation names and mutation protection.

1. Extract existing LocalStore.robotics_query validation, local-query token
   enforcement and RPC cache behavior. Preserve existing operations and plugin
   entitlement checks; no new HTTP transport or arbitrary operation dispatch.
2. Extend the read allowlist for trace_detail, trace_events, trace_spans,
   trace_artifact, trace_notes, trace_guard_get and trace_jobs. Extend mutation
   allowlist for trace_annotate, trace_guard_set and trace_evaluate; any additional
   name must be explicitly agreed with the private store implementation first.
3. Require the private daemon token for all new detailed reads and mutations,
   including the dashboard-mounted Blueprint. Detailed private handlers accept
   trusted operator scope, so authenticating writes alone is insufficient.
   Keep read-only operations read-only and preserve legacy read authorization.
   No direct DuckDB writer, raw filesystem telemetry handler, paid code or new
   actuator route is added. Existing robotics_query is not RPC-memoized.
4. Add regressions proving unknown operations fail, new declared operations reach
   entitled private handlers, and dashboard copies cannot mutate without the
   daemon token, including forged operator flags on detailed reads. Include
   trace_artifacts and trace_share in the explicit private operation contract.
   Preserve old route/function behavior and false entitlement.
5. Independent review and normal green PR/merge, then a separate [RELEASE] PR and
   verified PyPI artifact. Coordinate the Cloud pin and closed-wheel rollout;
   verify the actual shipped generic seam. Do not hand-edit version or tags.
