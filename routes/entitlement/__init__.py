"""routes/entitlement — the entitlement API surface.

This was one 1.84 MB, 47,675-line module holding 434 routes. That is five
times the next-largest route module in the repo, and past the point where
either a person or a tool can read it: a helper near the tail is
unreachable in practice, and automated readers that fetch a file whole
reported the module as absent rather than merely large.

The split is mechanical on purpose. Handlers keep their original order and
their original names; only the file they live in changed. ``_shared`` holds
the imports, the blueprint, the constants and every non-handler helper;
``_endpoints_NN`` hold the route handlers in runs sized to stay below the
largest route module we already ship comfortably. Everything is re-exported
here, so ``routes.entitlement.<anything>`` resolves exactly as before for
the 297 modules that import it.

The original module docstring follows.

routes/entitlement.py -- ``bp_entitlement``.

Exposes the resolved open-core entitlement so the frontend knows which
runtimes/features to surface (and, once enforcement is live, which to render
locked behind an upgrade CTA). Backed by :mod:`clawmetry.entitlements`, which
is the single source of truth -- handlers never re-derive tier logic here.

  GET  /api/entitlement              -- the current Entitlement as JSON.
  GET  /api/entitlement/diagnostic   -- the *inputs* the resolver consulted
                                        (license/cloud-plan presence, enforce
                                        env, cache liveness) for operator
                                        triage.
  POST /api/entitlement/refresh      -- drop the cache and return the freshly
                                        re-resolved Entitlement.
  GET  /api/entitlement/required-tier -- resolve the minimum purchasable tier
                                         for a feature=, runtime=, channels=,
                                         or retention_days= key. The capacity
                                         axes (channels / retention_days) wrap
                                         the matching ``min_tier_for_*`` Python
                                         helpers so the same endpoint answers
                                         all four "what tier do I need" axes
                                         off one URL.
  GET  /api/entitlement/lock-reason   -- human-readable explanation of why a
                                         feature=, runtime=, channels= or
                                         retention_days= key is locked,
                                         carrying the structured
                                         ``required_tier`` payload alongside
                                         the message so a paywall tooltip can
                                         render "Locked: <reason>. [Upgrade to
                                         <X>]" in one round-trip. The four
                                         axes match the ones on
                                         ``/api/entitlement/required-tier``.
  GET  /api/entitlement/upgrade-diff  -- features + runtimes a target tier
                                         would add on top of the current ent.
  GET  /api/entitlement/downgrade-diff -- features + runtimes a target tier
                                          would REMOVE from the current ent.
  GET  /api/entitlement/tier-diff     -- arbitrary-endpoint diff between any
                                         two tiers (``?from=&to=``);
                                         generalises ``/upgrade-diff`` /
                                         ``/downgrade-diff`` from "current vs
                                         target" to "any tier vs any tier" so
                                         a "Compare A vs B" pricing-page
                                         widget can render any pair without
                                         first switching the resolver.
  GET  /api/entitlement/preview        -- the full Entitlement.to_dict() shape
                                          rendered for an arbitrary tier so the
                                          upgrade-CTA card can show concrete
                                          numbers without per-tier derivation
                                          in JS.
  GET  /api/entitlement/required-tier-batch -- plural sibling of
                                          ``/required-tier``: takes
                                          ``features=a,b,c`` and/or
                                          ``runtimes=x,y,z`` (comma-separated)
                                          and returns the cheapest tier
                                          admitting *all* of them at once.
                                          Lets a dashboard answer "I'm using
                                          fleet + otel_export + sso -- what
                                          tier covers everything?" in a single
                                          round-trip.
  GET  /api/entitlement/required-tier-breakdown -- per-axis breakdown sibling
                                          of ``/required-tier-batch``: same
                                          inputs and top-level
                                          ``required_tier`` field, but
                                          additionally exposes each axis'
                                          individual ``min_tier`` and calls
                                          out which axis (or axes, on a tie)
                                          is the *binding* constraint driving
                                          the aggregate floor -- so a paywall
                                          CTA can render "You need Pro
                                          *because* you have 8 channels
                                          (Starter caps at 5)" off ONE
                                          round-trip.
  GET  /api/entitlement/lock-reason-batch -- per-item plural sibling of
                                          ``/lock-reason``: same CSV +
                                          capacity inputs as
                                          ``/required-tier-batch``, but
                                          preserves per-item ``reason`` /
                                          ``locked`` / ``required_tier`` rows
                                          so a Settings or paywall matrix UI
                                          renders N rows off one round-trip
                                          instead of N calls.
  GET  /api/entitlement/tier-unlocks-batch -- plural sibling of
                                          ``/tier-unlocks``: returns the full
                                          pricing-page marginal-unlock ladder
                                          in one pass.
  GET  /api/entitlement/tier-unlocks-path -- arbitrary-endpoint stepwise
                                          unlock path between any two tiers
                                          (``?from=&to=``); unlocks-focused
                                          analogue of ``/tier-path`` (full
                                          ``tier_diff`` per rung) and
                                          ``/capacity-diff-path`` (capacity-
                                          only per rung). Each row is a
                                          ``tier_unlocks`` payload between
                                          the previous step in the path and
                                          the current rung.
  GET  /api/entitlement/capacity-diff-batch -- plural sibling of
                                          ``/capacity-diff``: per-axis
                                          capacity transitions (channels /
                                          retention / nodes) for every
                                          purchasable tier in one pass so
                                          a pricing-page table can render
                                          the capacity column off one
                                          round-trip.
  GET  /api/entitlement/capacity-diff-path -- path analogue of
                                          ``/capacity-diff-batch``: per-rung
                                          capacity transition along an
                                          arbitrary ``?from=&to=`` segment,
                                          capacity-only mirror of
                                          ``/tier-path`` so a capacity-only
                                          pricing widget can render
                                          channel / retention / node
                                          marginal steps between two tiers
                                          off one round-trip.
  GET  /api/entitlement/capacity-headroom-path -- path analogue of
                                          ``/capacity-headroom-batch``:
                                          per-rung capacity-headroom envelope
                                          along an arbitrary ``?from=&to=``
                                          segment given caller-supplied
                                          per-axis usage. Headroom-shaped
                                          mirror of ``/capacity-diff-path``
                                          / ``/tier-unlocks-path`` /
                                          ``/tier-locks-path`` /
                                          ``/preview-path`` -- rungs line
                                          up rung-for-rung with those four
                                          siblings so an upgrade-walkthrough
                                          UI can render "watch your headroom
                                          recover rung by rung" off ONE
                                          round-trip.
  GET  /api/entitlement/capacity-headroom-path-batch -- batch sibling of
                                          ``/capacity-headroom-path`` and
                                          headroom-shaped twin of
                                          ``/capacity-diff-path-batch``: walk
                                          the per-rung headroom envelopes from
                                          ONE ``?from=`` to N candidate
                                          ``?to=a,b,c`` destinations in ONE
                                          round-trip. Fan-out shape matches
                                          ``/capacity-diff-path-batch`` and
                                          ``/tier-spec-path-batch``; unknown
                                          destinations bucket into
                                          ``unknown[]`` instead of 404ing.
  GET  /api/entitlement/next-tier-capacity-headroom -- scalar "one rung up"
                                          sibling of ``/capacity-headroom``:
                                          per-axis headroom envelope for the
                                          tier immediately above the resolved
                                          entitlement given caller-supplied
                                          usage. Envelope shape mirrors
                                          ``/next-tier-unlocks`` (current-tier
                                          context + null-at-ceiling), inner
                                          ``headroom`` matches
                                          ``/capacity-headroom-at`` byte-for-
                                          byte. Fills the "next-tier" slot on
                                          the capacity-headroom axis
                                          alongside the caps-only
                                          ``/next-tier-capacity-diff`` and
                                          the marginal-features
                                          ``/next-tier-unlocks``.
  GET  /api/entitlement/previous-tier-capacity-headroom -- downgrade twin of
                                          ``/next-tier-capacity-headroom``:
                                          per-axis headroom envelope for the
                                          tier immediately below the resolved
                                          entitlement given caller-supplied
                                          usage. Axes whose inner
                                          ``over_limit`` flips ``True`` are
                                          exactly the ones the caller would
                                          lose headroom on. Envelope shape
                                          matches
                                          ``/next-tier-capacity-headroom``
                                          byte-for-key with ``direction``
                                          echoing ``"downgrade"``.
  GET  /api/entitlement/preview-batch  -- plural sibling of ``/preview``:
                                         the full ``Entitlement.to_dict``
                                         shape rendered for every purchasable
                                         tier in one pass so a pricing-page
                                         table can render the cumulative-state
                                         column off one round-trip.
  GET  /api/entitlement/preview-path   -- arbitrary-endpoint stepwise
                                         cumulative-state path between any two
                                         tiers (``?from=&to=``); path analogue
                                         of ``/preview-batch`` and the
                                         cumulative-state sibling of
                                         ``/tier-path`` / ``/tier-unlocks-path``
                                         / ``/tier-locks-path`` /
                                         ``/capacity-diff-path``. Each row is
                                         the full ``/preview`` payload for that
                                         rung so an upgrade-walkthrough surface
                                         can render the "Cloud Pro: 90-day
                                         retention, ..." card at every step
                                         off one round-trip.
  GET  /api/entitlement/tier-locks    -- marginal-loss companion of
                                         ``/tier-unlocks``: features + runtimes
                                         that disappear when you step down to
                                         the named tier from the next-higher
                                         purchasable tier.
  GET  /api/entitlement/upgrade-path  -- ordered marginal-unlock ladder from
                                         the resolved tier upward (current-
                                         user-relative sibling of
                                         ``/tier-unlocks-batch``).
  GET  /api/entitlement/downgrade-path -- ordered cumulative-loss ladder from
                                         the resolved tier downward (direction-
                                         flipped sibling of ``/upgrade-path``).
  GET  /api/entitlement/tier-path     -- arbitrary-endpoint stepwise path
                                         between any two tiers (``?from=&to=``);
                                         path analogue of ``/tier-diff``,
                                         generalising ``/upgrade-path`` /
                                         ``/downgrade-path`` from "current vs
                                         target" to "any vs any" with each
                                         row a marginal-step ``tier_diff``
                                         payload.
  GET  /api/entitlement/affordable-tiers -- plural sibling of
                                         ``/required-tier-batch``: returns
                                         the full ordered list of purchasable
                                         tiers admitting a constraint bundle
                                         (not just the floor) so a pricing
                                         page can render "you need at least
                                         Starter -- Pro and Enterprise also
                                         qualify" off one round-trip.
  GET  /api/entitlement/tiers-for     -- inverse of ``/required-tier``: the
                                         full ladder of tiers that grant a
                                         ``feature=`` or ``runtime=`` key
                                         (the "Available in: Pro,
                                         Self-hosted Pro, Trial, Enterprise"
                                         availability list a pricing-page
                                         row or feature tooltip needs).
  GET  /api/entitlement/tiers-for-at  -- hypothetical-perspective sibling of
                                         ``/tiers-for``: same ladder scoped
                                         by a caller-supplied
                                         ``tier=<perspective>`` so an ``_at``
                                         walkthrough URL is uniform across
                                         every ``_at`` sibling.
  GET  /api/entitlement/tiers-for-batch-at -- hypothetical-perspective sibling
                                         of ``/tiers-for-batch``: every
                                         known feature + runtime in one pass
                                         scoped by ``tier=<perspective>``.
  GET  /api/runtimes                  -- the full runtime catalog.
  GET  /api/tiers                     -- the full tier ladder with per-tier metadata.
  GET  /api/entitlement/feature-catalog  -- bare sibling of
                                         ``/feature-catalog-at``: the resolved
                                         feature catalogue wrapped in the same
                                         ``{tier, features, grace, enforced}``
                                         envelope the ``-at`` sibling uses, so
                                         a client hydrating every catalog
                                         variant (bare, ``-at``,
                                         ``-at-batch``, ``-path``, ...) can do
                                         it off one prefix instead of mixing
                                         ``/api/features`` with
                                         ``/api/entitlement/feature-catalog-at``.
  GET  /api/entitlement/runtime-catalog  -- bare sibling of
                                         ``/runtime-catalog-at`` for the
                                         runtime axis; same envelope shape.
  GET  /api/entitlement/tier-catalog  -- bare sibling of
                                         ``/tier-catalog-at`` for the tier
                                         ladder; same envelope shape (with
                                         the resolved tier mirrored into the
                                         ``tier`` key to match the ``-at``
                                         sibling).
  GET  /api/entitlement/tier-spec     -- scalar sibling of ``/api/tiers``:
                                         full per-tier descriptor for one
                                         ``tier=`` key (label, rank,
                                         retention, channel/node limits,
                                         features + paid runtimes carried)
                                         so a pricing-page column / upsell
                                         tooltip can hydrate off one
                                         round-trip instead of walking the
                                         full ladder client-side.
  GET  /api/entitlement/tier-catalog-at -- what-if sibling of the tier
                                         ladder: returns the full
                                         ``tier_catalog`` rows but with
                                         ``is_current`` recomputed as if
                                         the install were on the named
                                         ``tier=`` instead of the live
                                         resolved entitlement. Mirrors
                                         ``/feature-catalog-at`` and
                                         ``/runtime-catalog-at`` for the
                                         tier ladder so a pricing-
                                         comparison UI can render any
                                         hypothetical "current tier"
                                         without first switching the live
                                         resolver.
  GET  /api/entitlement/tier-catalog-at-batch -- batch what-if sibling
                                         of ``/tier-catalog-at``: full tier
                                         ladders for N hypothetical source
                                         tiers (``?tiers=a,b,c``) off ONE
                                         call, each with ``is_current``
                                         flipped to its own source. Mirrors
                                         ``/feature-catalog-at-batch`` and
                                         ``/runtime-catalog-at-batch`` on the
                                         tier axis so a pricing-comparison
                                         matrix UI can render the ladder
                                         side-by-side from every hypothetical
                                         perspective off ONE round-trip
                                         instead of N calls.
  GET  /api/entitlement/tier-spec-at  -- scalar what-if sibling of
                                         ``/tier-catalog-at``: the single
                                         tier descriptor for ``target=`` with
                                         ``is_current`` computed as if the
                                         install were on ``tier=``. Lets a
                                         pricing-comparison tooltip hydrate
                                         against ONE tier descriptor from a
                                         hypothetical perspective in one
                                         round-trip instead of fetching the
                                         full ``/tier-catalog-at`` payload.
  GET  /api/entitlement/tier-spec-path -- arbitrary-endpoint stepwise spec-
                                         shaped path between any two tiers
                                         (``?from=&to=``); path-shaped
                                         sibling of ``/tier-spec-at-batch``
                                         and spec-shaped sibling of
                                         ``/tier-path`` / ``/capacity-diff-
                                         path`` / ``/tier-unlocks-path`` /
                                         ``/tier-locks-path`` / ``/preview-
                                         path``. Each row is a
                                         ``tier_spec_at`` row pinned on
                                         ``from=`` for ``target=<rung>``, so
                                         the marketing-shaped descriptor
                                         (``label``, ``is_paid``,
                                         ``unlocks_paid_runtimes``,
                                         ``retention_days``,
                                         ``channel_limit``, ``node_limit``,
                                         ``features``, ``runtimes``) hydrates
                                         at every rung between two tiers
                                         off one round-trip.
  GET  /api/entitlement/feature-catalog-path -- arbitrary-endpoint
                                         stepwise feature-catalog path between
                                         any two tiers (``?from=&to=``); the
                                         full-catalog sibling of
                                         ``/feature-spec-path`` and the path-
                                         shaped sibling of
                                         ``/feature-catalog-at-batch``. Each
                                         row is a ``/feature-catalog-at``
                                         payload at ``rung=<tier>`` so an
                                         upgrade-walkthrough surface hydrates
                                         every rung's full catalogue off one
                                         round-trip.
  GET  /api/entitlement/runtime-catalog-path -- runtime-axis twin of
                                         ``/feature-catalog-path``. Together
                                         the pair lets an upgrade-walkthrough
                                         UI render every feature + runtime
                                         column at every rung off two calls
                                         instead of first walking
                                         ``/tier-path`` and then hydrating
                                         each rung individually.
  GET  /api/entitlement/tier-catalog-path -- tier-axis twin of
                                         ``/feature-catalog-path`` /
                                         ``/runtime-catalog-path``. Each row
                                         is a ``/tier-catalog-at`` payload at
                                         ``rung=<tier>`` so an upgrade-
                                         walkthrough surface hydrates the
                                         full pricing ladder at every rung
                                         between two tiers off one round-
                                         trip. Together the three
                                         ``_catalog_path`` endpoints render
                                         every tier + feature + runtime
                                         column at every rung off three calls
                                         instead of walking ``/tier-path``
                                         and hydrating each rung
                                         individually.
  GET  /api/entitlement/runtime-detection -- pair the
                                         :mod:`clawmetry.runtime_probe`
                                         presence probes with the resolved
                                         entitlement so the dashboard can
                                         render "runtimes on this machine +
                                         which unlock at which tier" in one
                                         round-trip. Each probe row carries
                                         ``found`` (present on disk),
                                         ``allowed`` (granted by the current
                                         tier), and the paid ``required_tier``
                                         to unlock it if it is not; the
                                         envelope also carries
                                         ``actionable_tier`` -- the single
                                         cheapest tier that unlocks every
                                         detected-but-locked runtime -- so
                                         a paywall CTA does not need N
                                         extra ``/required-tier`` calls.
"""

# _shared first: it defines bp_entitlement, which every part decorates with.
from ._shared import *  # noqa: F401,F403
from ._shared import (  # noqa: F401
    _CAPACITY_PARAMS,
    _EMPTY_RUNTIME_DETECTION,
    _HAS_ALL_AT_KEYS,
    _MINIMAL_OSS_FREE_SNAPSHOT,
    _MISSING_ALL_AT_KEYS,
    _PAYWALL_DISTINCT_DIMS,
    _PAYWALL_LIFECYCLE_EVENTS,
    _activate_envelope,
    _bundle_batch_path_row_out,
    _capacity_batch_row_to_body,
    _deactivate_envelope,
    _has_all_at_batch_body,
    _has_all_at_batch_fallback,
    _has_all_at_body,
    _has_all_at_fallback,
    _has_all_at_path_batch_body,
    _has_all_at_path_batch_fallback,
    _has_all_at_path_body,
    _has_all_at_path_fallback,
    _has_all_body,
    _has_all_bundle_at_path_batch_fallback,
    _has_all_bundle_at_path_fallback,
    _has_all_bundle_batch_at_path_fallback,
    _has_all_bundle_from_path_batch_fallback,
    _has_all_bundle_row_at_to_body,
    _has_all_bundle_row_to_body,
    _has_all_fallback,
    _has_all_from_path_batch_body,
    _has_all_from_path_batch_fallback,
    _has_axis_at_body,
    _has_axis_at_fallback,
    _has_axis_body,
    _has_axis_fallback,
    _has_batch_at_fallback,
    _has_batch_fallback,
    _has_batch_rollup,
    _has_bundle_at_batch_body,
    _has_bundle_at_batch_fallback,
    _has_bundle_at_body,
    _has_bundle_at_fallback,
    _has_bundle_at_path_batch_body,
    _has_bundle_at_path_batch_fallback,
    _has_bundle_at_path_body,
    _has_bundle_at_path_fallback,
    _has_bundle_body,
    _has_bundle_fallback,
    _has_bundle_from_path_batch_body,
    _has_bundle_from_path_batch_fallback,
    _has_bundle_row_at_body,
    _has_bundle_row_body,
    _has_capacity_at_batch_body,
    _has_capacity_at_batch_fallback,
    _has_capacity_at_batch_row_to_body,
    _has_channel_count_at_fallback,
    _has_channel_count_batch_fallback,
    _has_channel_count_batch_row_to_body,
    _has_channel_count_fallback,
    _has_node_count_at_batch_fallback,
    _has_node_count_at_batch_row_to_body,
    _has_node_count_at_fallback,
    _has_node_count_batch_fallback,
    _has_node_count_batch_row_to_body,
    _has_node_count_fallback,
    _has_retention_window_at_fallback,
    _has_retention_window_batch_fallback,
    _has_retention_window_batch_row_to_body,
    _has_retention_window_fallback,
    _license_expires_snapshot,
    _license_expiry_snapshot,
    _license_features_at_snapshot,
    _license_gate_snapshot,
    _license_issued_snapshot,
    _license_nodes_snapshot,
    _license_permissions_snapshot,
    _license_presence_snapshot,
    _license_pubkey_fingerprint_snapshot,
    _license_state_at_snapshot,
    _license_state_snapshot,
    _license_subject_at_snapshot,
    _license_subject_snapshot,
    _license_tier_at_snapshot,
    _license_tier_snapshot,
    _min_tier_for_all_row_to_body,
    _min_tier_for_bundle_row_to_body,
    _min_tier_for_capacity_at_batch_body,
    _min_tier_for_capacity_at_batch_fallback,
    _min_tier_for_capacity_at_body,
    _min_tier_for_capacity_at_fallback,
    _min_tier_for_capacity_batch_fallback,
    _min_tier_for_capacity_body,
    _min_tier_for_capacity_fallback,
    _missing_all_at_batch_body,
    _missing_all_at_batch_fallback,
    _missing_all_at_body,
    _missing_all_at_fallback,
    _missing_all_at_path_batch_body,
    _missing_all_at_path_batch_fallback,
    _missing_all_at_path_body,
    _missing_all_at_path_fallback,
    _missing_all_body,
    _missing_all_bundle_at_path_batch_fallback,
    _missing_all_bundle_at_path_fallback,
    _missing_all_bundle_batch_at_path_fallback,
    _missing_all_bundle_from_path_batch_fallback,
    _missing_all_bundle_row_at_to_body,
    _missing_all_bundle_row_to_body,
    _missing_all_fallback,
    _missing_all_from_path_batch_body,
    _missing_all_from_path_batch_fallback,
    _missing_bundle_at_batch_body,
    _missing_bundle_at_batch_fallback,
    _missing_bundle_at_body,
    _missing_bundle_at_fallback,
    _missing_bundle_at_path_batch_body,
    _missing_bundle_at_path_batch_fallback,
    _missing_bundle_at_path_body,
    _missing_bundle_at_path_fallback,
    _missing_bundle_body,
    _missing_bundle_fallback,
    _missing_bundle_from_path_batch_body,
    _missing_bundle_from_path_batch_fallback,
    _missing_bundle_row_at_body,
    _missing_bundle_row_body,
    _neighbour_tier_headroom_envelope,
    _next_prev_lock_reason,
    _next_prev_lock_reason_at,
    _next_prev_lock_reason_at_batch,
    _next_prev_lock_reason_batch,
    _next_prev_lock_reason_batch_grace_body,
    _next_prev_lock_reason_grace_body,
    _next_prev_tier_axis_catalog_grace_body,
    _next_prev_tier_axis_spec_batch_grace_body,
    _next_prev_tier_axis_spec_grace_body,
    _next_prev_tier_channel_catalog_grace_body,
    _next_prev_tier_channel_spec_at_batch,
    _next_prev_tier_feature_spec_at_batch,
    _next_prev_tier_runtime_spec_at_batch,
    _parse_aggregate_bundles_body,
    _parse_bundles_body,
    _parse_capacity_arg,
    _parse_capacity_batch_csv,
    _parse_csv_arg,
    _parse_from_tiers_bundle_body,
    _parse_license_days_csv,
    _parse_license_epochs_csv,
    _parse_single_bundle_body,
    _parse_tiers_for_capacity_batch_csv,
    _perspective_envelope,
    _perspective_fallback,
    _ping_paywall_lifecycle,
    _pro_install_snapshot,
    _resolver_envelope,
    _route_actor,
    _runtime_detection_counts,
    _tiers_for_capacity_perval_at_body,
    _tiers_for_capacity_perval_at_fallback,
    _tiers_for_capacity_perval_fallback,
)
from ._endpoints_01 import *  # noqa: F401,F403
from ._endpoints_02 import *  # noqa: F401,F403
from ._endpoints_03 import *  # noqa: F401,F403
from ._endpoints_04 import *  # noqa: F401,F403
from ._endpoints_05 import *  # noqa: F401,F403
from ._endpoints_06 import *  # noqa: F401,F403
from ._endpoints_07 import *  # noqa: F401,F403
from ._endpoints_08 import *  # noqa: F401,F403

__all__ = ["bp_entitlement"]
