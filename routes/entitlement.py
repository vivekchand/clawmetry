routes/entitlement.py -- ``bp_entitlement``.

Exposes the resolved open-core entitlement so the frontend knows which
runtimes/features to surface (and, once enforcement is live, which to render
locked behind an upgrade CTA). Backed by :mod:`clawmetry.entitlements`, which
is the single source of truth -- handlers never re-derive tier logic here.

  GET  /api/entitlement              -- resolved entitlement (tier, features, runtimes).
  POST /api/entitlement/refresh      -- invalidate + re-resolve (no side effects).
  GET  /api/entitlement/upgrade-diff -- features gained / lost when moving to a target tier.
  GET  /api/entitlement/preview      -- hypothetical entitlement for a tier the user doesn't hold.
  GET  /api/entitlement/tier-unlocks -- features + runtimes a specific tier unlocks.
  GET  /api/entitlement/tier-locks   -- features + runtimes locked at a specific tier.
  GET  /api/entitlement/min-tier     -- cheapest purchasable tier that unlocks a feature or runtime.
  GET  /api/entitlement/tier-spec    -- scalar spec for a single tier (used by upgrade-CTA rows).
  GET  /api/features                 -- the full feature catalog (all features, resolved).
  GET  /api/runtimes                 -- the full runtime catalog.
  GET  /api/tiers                    -- the full tier ladder with per-tier metadata.
  GET  /api/entitlement/tier-spec    -- scalar sibling of ``/api/tiers``:
                                        full per-tier descriptor for one
                                        ``tier=`` key (label, rank,
                                        retention, channel/node limits,
                                        features + paid runtimes carried)
                                        so a pricing-page column / upsell
                                        tooltip can hydrate off one
                                        round-trip instead of walking the
                                        full ladder client-side.
  GET  /api/entitlement/feature-spec -- scalar sibling of ``/api/features``:
                                        single ``feature_catalog()`` row for
                                        ``feature=<id>`` so a feature-detail
                                        page or upgrade tooltip can hydrate
                                        without filtering the full catalogue
                                        client-side.
  GET  /api/entitlement/runtime-spec -- scalar sibling of ``/api/runtimes``:
                                        single ``runtime_catalog()`` row for
                                        ``runtime=<id>`` (canonical id or
                                        alias) so a runtime-detail page or
                                        upgrade tooltip can hydrate without
                                        filtering the full catalogue
                                        client-side.
"""