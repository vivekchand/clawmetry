"""
routes/brain.py — Brain event feed endpoints.

Extracted from dashboard.py as Phase 5.2 of the incremental modularisation.
Owns the two routes that power the Brain tab:

  GET  /api/brain-history   — unified JSONL + log scan, returns list
  GET  /api/brain-stream    — SSE tail of the same sources

Module-level helpers (``SESSIONS_DIR``, ``SSE_MAX_SECONDS``,
``_get_log_dirs``, ``_tail_lines``, ``_acquire_stream_slot``,
``_release_stream_slot``, ``_ext_emit``) stay in ``dashboard.py`` and are
reached via late ``import dashboard as _d``. Pure mechanical move — zero
behaviour change.
"""

import glob
import json
import os
import time
from datetime import datetime, timedelta, timezone

from flask import Blueprint, Response, jsonify, request
from clawmetry.config import is_local_store_read_enabled
from clawmetry.risk import compute_hallucination_risk, is_llm_event
from clawmetry.token_confidence import annotate_events as _annotate_token_confidence
from clawmetry.token_confidence import annotate_tool_alternatives as _annotate_tool_alternatives

bp_brain = Blueprint('brain', __name__)

PLACEHOLDER_BRAIN