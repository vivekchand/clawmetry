routes/usage.py — Usage / analytics / anomaly / attribution endpoints.

Extracted from dashboard.py as Phase 5.3 of the incremental modularisation.
Owns the 12 routes registered on bp_usage:

  GET  /api/usage                         — headline token/cost tracker
  GET  /api/usage/anomalies               — cost anomaly summary
  GET  /api/anomalies                     — rolling-baseline detector output
  POST /api/anomalies/<id>/ack            — acknowledge an anomaly
  GET  /api/usage/by-plugin               — plugin token/cost breakdown
  GET  /api/usage/by-plugin/trend         — plugin breakdown over time
  GET  /api/usage/by-model                — per-model cost/token breakdown with cost-per-call
  GET  /api/sessions/clusters             — behavioural session clustering
  GET  /api/usage/cost-comparison         — alt-model savings estimate
  GET  /api/usage/export                  — CSV export of usage
  GET  /api/model-attribution             — per-model turn/session split
  GET  /api/skill-attribution             — per-skill cost attribution
  GET  /api/usage/by-team                 — per-agent / per-team cost attribution
  GET  /api/usage/team-mappings           — list runtime→team label mappings
  POST /api/usage/team-mappings           — create/update a mapping
  DELETE /api/usage/team-mappings/<k>/<v> — delete a mapping
  GET  /api/token-velocity                — runaway-loop detection
  GET  /api/usage/cache-trends            — prompt-cache hit-rate analytics
  GET  /api/skills/fidelity              — dead-skill detector + body/linked-file stats
  GET  /api/efficiency                    — efficiency grade + measured savings
  GET  /api/usage/outcomes                — cost per merged change, rework rate,
                                            abandoned spend (REQ-OBS-CEA-022)

Module-level helpers (``_usage_cache``, ``_compute_transcript_analytics``,
``_detect_and_store_anomalies``, ``_get_anomaly_db``, ``SESSIONS_DIR`` etc.)
stay in ``dashboard.py`` and are reached via late ``import dashboard as _d``.
Pure mechanical move — zero behaviour change.
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from flask import Blueprint, jsonify, make_response, request
from clawmetry._gate import gate
from clawmetry import provenance as _prov
from clawmetry.config import is_local_store_read_enabled
from routes._dedupe import build_sibling_bucket_max, is_sibling_dup

bp_usage = Blueprint('usage', __name__)