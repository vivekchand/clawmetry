'''
routes/usage.py — Usage / analytics / anomaly / attribution endpoints.

Extracted from dashboard.py as Phase 5.3 of the incremental modularisation.
Owns the 12 routes registered on bp_usage:

  GET  /api/usage                         — headline token/cost tracker
  GET  /api/usage/anomalies               — cost anomaly summary
  GET  /api/anomalies                     — rolling-baseline detector output
  POST /api/anomalies/<id>/ack            — acknowledge an anomaly
  GET  /api/usage/by-plugin               — plugin token/cost breakdown
  GET  /api/usage/by-plugin/trend         — plugin breakdown over time
  GET  /api/sessions/clusters             — behavioural session clustering
  GET  /api/usage/cost-comparison         — alt-model savings estimate
  GET  /api/usage/export                  — CSV export of usage
  GET  /api/model-attribution             — per-model turn/session split
  GET  /api/skill-attribution             — per-skill cost attribution
  GET  /api/token-velocity                — runaway-loop detection
  GET  /api/usage/cache-trends            — prompt-cache hit-rate analytics
  GET  /api/skills/fidelity              — dead-skill detector + body/linked-file stats

Module-level helpers (``_usage_cache``, ``_compute_transcript_analytics``,
``_detect_and_store_anomalies``, ``_get_anomaly_db``, ``SESSIONS_DIR`` etc.)
stay in ``dashboard.py`` and are reached via late ``import dashboard as _d``.
Pure mechanical move — zero behaviour change.
'''