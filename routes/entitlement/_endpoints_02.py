"""routes/entitlement/_endpoints_02.py — endpoint handlers api_entitlement_missing_features_at_path .. api_entitlement_affordable_tiers_at.

One of 8 handler modules split out of the former single-module
routes/entitlement.py. Handlers keep their original order; the split
points are size, not meaning, so read the package __init__ first.
"""
from __future__ import annotations


# Imported as a MODULE, not by name: a test that patches a helper (monkeypatch
# on routes.entitlement._shared) must still change what these handlers call.
# Binding the names here instead would freeze them at import time, which the
# single-module version never did.
from . import _shared

@_shared.bp_entitlement.route("/api/entitlement/missing-features-at-path")
def api_entitlement_missing_features_at_path():
    try:
        return _shared.jsonify(_shared._missing_bundle_at_path_body("features"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_features_at_path: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_bundle_at_path_fallback(
                "features", from_tier, to_tier, _shared._parse_csv_arg("features")
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-runtimes-at-path")
def api_entitlement_missing_runtimes_at_path():
    try:
        return _shared.jsonify(_shared._missing_bundle_at_path_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_runtimes_at_path: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_bundle_at_path_fallback(
                "runtimes", from_tier, to_tier, _shared._parse_csv_arg("runtimes")
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-features-at-path")
def api_entitlement_has_features_at_path():
    try:
        return _shared.jsonify(_shared._has_bundle_at_path_body("features"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_features_at_path: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_bundle_at_path_fallback(
                "features", from_tier, to_tier, _shared._parse_csv_arg("features")
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-runtimes-at-path")
def api_entitlement_has_runtimes_at_path():
    try:
        return _shared.jsonify(_shared._has_bundle_at_path_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_runtimes_at_path: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_bundle_at_path_fallback(
                "runtimes", from_tier, to_tier, _shared._parse_csv_arg("runtimes")
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-features-at-path-batch")
def api_entitlement_missing_features_at_path_batch():
    try:
        return _shared.jsonify(_shared._missing_bundle_at_path_batch_body("features"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_features_at_path_batch: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_bundle_at_path_batch_fallback(
                "features",
                from_tier,
                _shared._parse_csv_arg("to"),
                _shared._parse_csv_arg("features"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-runtimes-at-path-batch")
def api_entitlement_missing_runtimes_at_path_batch():
    try:
        return _shared.jsonify(_shared._missing_bundle_at_path_batch_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_runtimes_at_path_batch: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_bundle_at_path_batch_fallback(
                "runtimes",
                from_tier,
                _shared._parse_csv_arg("to"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-features-at-path-batch")
def api_entitlement_has_features_at_path_batch():
    try:
        return _shared.jsonify(_shared._has_bundle_at_path_batch_body("features"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_features_at_path_batch: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_bundle_at_path_batch_fallback(
                "features",
                from_tier,
                _shared._parse_csv_arg("to"),
                _shared._parse_csv_arg("features"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-runtimes-at-path-batch")
def api_entitlement_has_runtimes_at_path_batch():
    try:
        return _shared.jsonify(_shared._has_bundle_at_path_batch_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_runtimes_at_path_batch: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_bundle_at_path_batch_fallback(
                "runtimes",
                from_tier,
                _shared._parse_csv_arg("to"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-features-from-path-batch")
def api_entitlement_has_features_from_path_batch():
    try:
        return _shared.jsonify(_shared._has_bundle_from_path_batch_body("features"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_features_from_path_batch: error: %s", exc
        )
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_bundle_from_path_batch_fallback(
                "features",
                to_tier,
                _shared._parse_csv_arg("from"),
                _shared._parse_csv_arg("features"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-runtimes-from-path-batch")
def api_entitlement_has_runtimes_from_path_batch():
    try:
        return _shared.jsonify(_shared._has_bundle_from_path_batch_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_runtimes_from_path_batch: error: %s", exc
        )
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_bundle_from_path_batch_fallback(
                "runtimes",
                to_tier,
                _shared._parse_csv_arg("from"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-features-from-path-batch")
def api_entitlement_missing_features_from_path_batch():
    try:
        return _shared.jsonify(_shared._missing_bundle_from_path_batch_body("features"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_features_from_path_batch: error: %s", exc
        )
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_bundle_from_path_batch_fallback(
                "features",
                to_tier,
                _shared._parse_csv_arg("from"),
                _shared._parse_csv_arg("features"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-runtimes-from-path-batch")
def api_entitlement_missing_runtimes_from_path_batch():
    try:
        return _shared.jsonify(_shared._missing_bundle_from_path_batch_body("runtimes"))
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_runtimes_from_path_batch: error: %s", exc
        )
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_bundle_from_path_batch_fallback(
                "runtimes",
                to_tier,
                _shared._parse_csv_arg("from"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-all-at")
def api_entitlement_has_all_at():
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        return _shared.jsonify(_shared._has_all_at_body(tier_in))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_all_at: error: %s", exc)
        return _shared.jsonify(_shared._has_all_at_fallback(tier_in))

@_shared.bp_entitlement.route("/api/entitlement/missing-all-at")
def api_entitlement_missing_all_at():
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        return _shared.jsonify(_shared._missing_all_at_body(tier_in))
    except Exception as exc:
        _shared.logger.warning("api_entitlement_missing_all_at: error: %s", exc)
        return _shared.jsonify(_shared._missing_all_at_fallback(tier_in))

@_shared.bp_entitlement.route("/api/entitlement/missing-all-at-path")
def api_entitlement_missing_all_at_path():
    try:
        return _shared.jsonify(_shared._missing_all_at_path_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_all_at_path: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_all_at_path_fallback(
                from_tier,
                to_tier,
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-all-at-batch")
def api_entitlement_has_all_at_batch():
    try:
        return _shared.jsonify(_shared._has_all_at_batch_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_all_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            _shared._has_all_at_batch_fallback(
                _shared._parse_csv_arg("tiers"),
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-all-at-path")
def api_entitlement_has_all_at_path():
    try:
        return _shared.jsonify(_shared._has_all_at_path_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_all_at_path: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_all_at_path_fallback(
                from_tier,
                to_tier,
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-all-at-path-batch")
def api_entitlement_has_all_at_path_batch():
    try:
        return _shared.jsonify(_shared._has_all_at_path_batch_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_all_at_path_batch: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_all_at_path_batch_fallback(
                from_tier,
                _shared._parse_csv_arg("to"),
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-all-at-path-batch")
def api_entitlement_missing_all_at_path_batch():
    try:
        return _shared.jsonify(_shared._missing_all_at_path_batch_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_all_at_path_batch: error: %s", exc
        )
        from_tier = (_shared.request.args.get("from") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_all_at_path_batch_fallback(
                from_tier,
                _shared._parse_csv_arg("to"),
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-all-from-path-batch")
def api_entitlement_has_all_from_path_batch():
    try:
        return _shared.jsonify(_shared._has_all_from_path_batch_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_has_all_from_path_batch: error: %s", exc
        )
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._has_all_from_path_batch_fallback(
                to_tier,
                _shared._parse_csv_arg("from"),
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-all-from-path-batch")
def api_entitlement_missing_all_from_path_batch():
    try:
        return _shared.jsonify(_shared._missing_all_from_path_batch_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_all_from_path_batch: error: %s", exc
        )
        to_tier = (_shared.request.args.get("to") or "").strip().lower()
        return _shared.jsonify(
            _shared._missing_all_from_path_batch_fallback(
                to_tier,
                _shared._parse_csv_arg("from"),
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/missing-all-at-batch")
def api_entitlement_missing_all_at_batch():
    try:
        return _shared.jsonify(_shared._missing_all_at_batch_body())
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_missing_all_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            _shared._missing_all_at_batch_fallback(
                _shared._parse_csv_arg("tiers"),
                _shared._parse_csv_arg("features"),
                _shared._parse_csv_arg("runtimes"),
            )
        )

@_shared.bp_entitlement.route("/api/entitlement/has-all")
def api_entitlement_has_all():
    try:
        return _shared.jsonify(_shared._has_all_body())
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_all: error: %s", exc)
        return _shared.jsonify(_shared._has_all_fallback())

@_shared.bp_entitlement.route("/api/entitlement/missing-all")
def api_entitlement_missing_all():
    try:
        return _shared.jsonify(_shared._missing_all_body())
    except Exception as exc:
        _shared.logger.warning("api_entitlement_missing_all: error: %s", exc)
        return _shared.jsonify(_shared._missing_all_fallback())

@_shared.bp_entitlement.route("/api/entitlement/lock-reason")
def api_entitlement_lock_reason():
    try:
        from clawmetry import entitlements as _ent

        feature = (_shared.request.args.get("feature") or "").strip().lower()
        runtime = (_shared.request.args.get("runtime") or "").strip().lower()
        (
            channels_present,
            channels_ok,
            channels_n,
            channels_raw,
        ) = _shared._parse_capacity_arg("channels")
        (
            retention_present,
            retention_ok,
            retention_n,
            retention_raw,
        ) = _shared._parse_capacity_arg("retention_days")
        (
            nodes_present,
            nodes_ok,
            nodes_n,
            nodes_raw,
        ) = _shared._parse_capacity_arg("nodes")

        supplied = [
            bool(feature),
            bool(runtime),
            channels_present,
            retention_present,
            nodes_present,
        ]
        n_supplied = sum(1 for s in supplied if s)
        if n_supplied == 0:
            return (
                _shared.jsonify(
                    {
                        "error": (
                            "supply exactly one of feature=<id>, runtime=<id>, "
                            "channels=<int>, retention_days=<int>, or "
                            "nodes=<int>"
                        )
                    }
                ),
                400,
            )
        if n_supplied > 1:
            return (
                _shared.jsonify(
                    {
                        "error": (
                            "supply only one of feature=, runtime=, channels=, "
                            "retention_days=, or nodes="
                        )
                    }
                ),
                400,
            )

        ent = _ent.get_entitlement()
        if feature:
            key, kind = feature, "feature"
            allowed = ent.allows_feature(feature)
            required = _ent.min_tier_for_feature(feature)
            reason = ent.lock_reason(key, kind=kind)
        elif runtime:
            key, kind = runtime, "runtime"
            allowed = ent.allows_runtime(runtime)
            required = _ent.min_tier_for_runtime(runtime)
            reason = ent.lock_reason(key, kind=kind)
        elif channels_present:
            key, kind = channels_raw, "channels"
            if channels_ok:
                required = _ent.min_tier_for_channel_count(channels_n)
                allowed = ent.allows_channel_count(channels_n)
                reason = ent.lock_reason(str(channels_n), kind=kind)
            else:
                required = None
                allowed = True
                reason = None
        elif retention_present:
            key, kind = retention_raw, "retention_days"
            if retention_ok:
                required = _ent.min_tier_for_retention_window(retention_n)
                allowed = ent.allows_retention_window(retention_n)
                reason = ent.lock_reason(str(retention_n), kind=kind)
            else:
                required = None
                allowed = True
                reason = None
        else:
            key, kind = nodes_raw, "nodes"
            if nodes_ok:
                required = _ent.min_tier_for_node_count(nodes_n)
                allowed = ent.allows_node_count(nodes_n)
                reason = ent.lock_reason(str(nodes_n), kind=kind)
            else:
                required = None
                allowed = True
                reason = None
        cur_rank = _ent.tier_rank(ent.tier)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return _shared.jsonify(
            {
                "key": key,
                "kind": kind,
                "reason": reason,
                "locked": reason is not None,
                "allowed": allowed,
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "current_tier": ent.tier,
                "current_tier_rank": cur_rank,
                "upgrade_required": bool(required) and req_rank > cur_rank,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_lock_reason: error: %s", exc)
        feature = (_shared.request.args.get("feature") or "").strip().lower()
        runtime = (_shared.request.args.get("runtime") or "").strip().lower()
        channels_raw = (_shared.request.args.get("channels") or "").strip()
        retention_raw = (_shared.request.args.get("retention_days") or "").strip()
        nodes_raw = (_shared.request.args.get("nodes") or "").strip()
        if feature:
            key, kind = feature, "feature"
        elif runtime:
            key, kind = runtime, "runtime"
        elif channels_raw:
            key, kind = channels_raw, "channels"
        elif retention_raw:
            key, kind = retention_raw, "retention_days"
        elif nodes_raw:
            key, kind = nodes_raw, "nodes"
        else:
            key, kind = "", ""
        return _shared.jsonify(
            {
                "key": key,
                "kind": kind,
                "reason": None,
                "locked": False,
                "allowed": True,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "upgrade_required": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/lock-reason-at")
def api_entitlement_lock_reason_at():
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        feature = (_shared.request.args.get("feature") or "").strip().lower()
        runtime_in = (_shared.request.args.get("runtime") or "").strip().lower()
        (
            channels_present,
            channels_ok,
            channels_n,
            channels_raw,
        ) = _shared._parse_capacity_arg("channels")
        (
            retention_present,
            retention_ok,
            retention_n,
            retention_raw,
        ) = _shared._parse_capacity_arg("retention_days")
        (
            nodes_present,
            nodes_ok,
            nodes_n,
            nodes_raw,
        ) = _shared._parse_capacity_arg("nodes")

        supplied = [
            bool(feature),
            bool(runtime_in),
            channels_present,
            retention_present,
            nodes_present,
        ]
        n_supplied = sum(1 for s in supplied if s)
        if n_supplied == 0:
            return (
                _shared.jsonify(
                    {
                        "error": (
                            "supply exactly one of feature=<id>, runtime=<id>, "
                            "channels=<int>, retention_days=<int>, or "
                            "nodes=<int>"
                        )
                    }
                ),
                400,
            )
        if n_supplied > 1:
            return (
                _shared.jsonify(
                    {
                        "error": (
                            "supply only one of feature=, runtime=, channels=, "
                            "retention_days=, or nodes="
                        )
                    }
                ),
                400,
            )

        if feature:
            key, kind = feature, "feature"
            required = _ent.min_tier_for_feature(feature)
            reason = _ent.lock_reason_at(tier_in, feature, kind=kind)
            allowed = reason is None
        elif runtime_in:
            rt = _ent.canonical_runtime(runtime_in)
            key, kind = rt or runtime_in, "runtime"
            required = _ent.min_tier_for_runtime(rt) if rt else None
            reason = _ent.lock_reason_at(tier_in, rt or runtime_in, kind=kind)
            allowed = reason is None
        elif channels_present:
            key, kind = channels_raw, "channels"
            if channels_ok:
                required = _ent.min_tier_for_channel_count(channels_n)
                reason = _ent.lock_reason_at(
                    tier_in, str(channels_n), kind=kind
                )
                allowed = reason is None
            else:
                required = None
                reason = None
                allowed = True
        elif retention_present:
            key, kind = retention_raw, "retention_days"
            if retention_ok:
                required = _ent.min_tier_for_retention_window(retention_n)
                reason = _ent.lock_reason_at(
                    tier_in, str(retention_n), kind=kind
                )
                allowed = reason is None
            else:
                required = None
                reason = None
                allowed = True
        else:
            key, kind = nodes_raw, "nodes"
            if nodes_ok:
                required = _ent.min_tier_for_node_count(nodes_n)
                reason = _ent.lock_reason_at(tier_in, str(nodes_n), kind=kind)
                allowed = reason is None
            else:
                required = None
                reason = None
                allowed = True

        cur_rank = _ent.tier_rank(tier_in)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return _shared.jsonify(
            {
                "key": key,
                "kind": kind,
                "reason": reason,
                "locked": reason is not None,
                "allowed": allowed,
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "current_tier": tier_in,
                "current_tier_rank": cur_rank,
                "upgrade_required": bool(required) and req_rank > cur_rank,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_lock_reason_at: error: %s", exc)
        feature = (_shared.request.args.get("feature") or "").strip().lower()
        runtime_in = (_shared.request.args.get("runtime") or "").strip().lower()
        channels_raw = (_shared.request.args.get("channels") or "").strip()
        retention_raw = (_shared.request.args.get("retention_days") or "").strip()
        nodes_raw = (_shared.request.args.get("nodes") or "").strip()
        if feature:
            key, kind = feature, "feature"
        elif runtime_in:
            key, kind = runtime_in, "runtime"
        elif channels_raw:
            key, kind = channels_raw, "channels"
        elif retention_raw:
            key, kind = retention_raw, "retention_days"
        elif nodes_raw:
            key, kind = nodes_raw, "nodes"
        else:
            key, kind = "", ""
        return _shared.jsonify(
            {
                "key": key,
                "kind": kind,
                "reason": None,
                "locked": False,
                "allowed": True,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "current_tier": tier_in,
                "current_tier_rank": 0,
                "upgrade_required": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/required-tier-batch")
def api_entitlement_required_tier_batch():
    try:
        from clawmetry import entitlements as _ent

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, channels_raw) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, retention_raw) = _shared._parse_capacity_arg(
            "retention_days",
        )
        (_, nodes_ok, nodes_n, nodes_raw) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                _shared.jsonify(
                    {
                        "error": (
                            "supply at least one of features=<csv>, "
                            "runtimes=<csv>, channels=<int>, "
                            "retention_days=<int>, or nodes=<int>"
                        )
                    }
                ),
                400,
            )

        ent = _ent.get_entitlement()
        required = _ent.min_tier_for_all(
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )

        cur_rank = _ent.tier_rank(ent.tier)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None

        feat_allowed = all(ent.allows_feature(f) for f in features)
        runtime_allowed = all(ent.allows_runtime(r) for r in runtimes)
        channels_allowed = (
            ent.allows_channel_count(channels_n) if channels_ok else True
        )
        retention_allowed = (
            ent.allows_retention_window(retention_n) if retention_ok else True
        )
        nodes_allowed = ent.allows_node_count(nodes_n) if nodes_ok else True
        allowed = (
            feat_allowed
            and runtime_allowed
            and channels_allowed
            and retention_allowed
            and nodes_allowed
        )

        return _shared.jsonify(
            {
                "features": features,
                "runtimes": runtimes,
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "current_tier": ent.tier,
                "current_tier_rank": cur_rank,
                "upgrade_required": bool(required) and req_rank > cur_rank,
                "allowed": allowed,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_required_tier_batch: error: %s", exc)
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")
        return _shared.jsonify(
            {
                "features": _shared._parse_csv_arg("features"),
                "runtimes": _shared._parse_csv_arg("runtimes"),
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "upgrade_required": False,
                "allowed": True,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/required-tier-breakdown")
def api_entitlement_required_tier_breakdown():
    try:
        from clawmetry import entitlements as _ent

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (channels_present, channels_ok, channels_n, _) = _shared._parse_capacity_arg(
            "channels"
        )
        (retention_present, retention_ok, retention_n, _) = _shared._parse_capacity_arg(
            "retention_days"
        )
        (nodes_present, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_present
            and not retention_present
            and not nodes_present
        ):
            return (
                _shared.jsonify(
                    {
                        "error": (
                            "supply at least one of features=<csv>, "
                            "runtimes=<csv>, channels=<int>, "
                            "retention_days=<int>, or nodes=<int>"
                        )
                    }
                ),
                400,
            )

        breakdown = _ent.min_tier_for_all_breakdown(
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )

        ent = _ent.get_entitlement()
        required = breakdown.get("min_tier")
        required_label = breakdown.get("min_tier_label")
        req_rank = _ent.tier_rank(required) if required else -1
        cur_rank = _ent.tier_rank(ent.tier)

        return _shared.jsonify(
            {
                "features": features,
                "runtimes": runtimes,
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "current_tier": ent.tier,
                "current_tier_rank": cur_rank,
                "upgrade_required": bool(required) and req_rank > cur_rank,
                "axes": breakdown.get("axes")
                or {
                    "features": None,
                    "runtimes": None,
                    "channels": None,
                    "retention_days": None,
                    "nodes": None,
                },
                "binding_axes": breakdown.get("binding_axes") or [],
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_required_tier_breakdown: error: %s", exc
        )
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")
        return _shared.jsonify(
            {
                "features": _shared._parse_csv_arg("features"),
                "runtimes": _shared._parse_csv_arg("runtimes"),
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "upgrade_required": False,
                "axes": {
                    "features": None,
                    "runtimes": None,
                    "channels": None,
                    "retention_days": None,
                    "nodes": None,
                },
                "binding_axes": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/has-all-breakdown")
def api_entitlement_has_all_breakdown():
    try:
        from clawmetry import entitlements as _ent

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (channels_present, channels_ok, channels_n, channels_raw) = _shared._parse_capacity_arg(
            "channels"
        )
        (
            retention_present,
            retention_ok,
            retention_n,
            retention_raw,
        ) = _shared._parse_capacity_arg("retention_days")
        (nodes_present, nodes_ok, nodes_n, nodes_raw) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_present
            and not retention_present
            and not nodes_present
        ):
            return (
                _shared.jsonify(
                    {
                        "error": (
                            "supply at least one of features=<csv>, "
                            "runtimes=<csv>, channels=<int>, "
                            "retention_days=<int>, or nodes=<int>"
                        )
                    }
                ),
                400,
            )

        def _capacity_kw(present: bool, ok: bool, n: int | None, raw: str):
            if not present:
                return None
            if ok:
                return n
            return raw

        breakdown = _ent.has_all_breakdown(
            features=features or None,
            runtimes=runtimes or None,
            channels=_capacity_kw(channels_present, channels_ok, channels_n, channels_raw),
            retention_days=_capacity_kw(
                retention_present, retention_ok, retention_n, retention_raw
            ),
            nodes=_capacity_kw(nodes_present, nodes_ok, nodes_n, nodes_raw),
        )

        ent = _ent.get_entitlement()
        cur_rank = _ent.tier_rank(ent.tier)

        return _shared.jsonify(
            {
                "features": features,
                "runtimes": runtimes,
                "channels": channels_n if channels_ok else (channels_raw if channels_present else None),
                "retention_days": retention_n if retention_ok else (retention_raw if retention_present else None),
                "nodes": nodes_n if nodes_ok else (nodes_raw if nodes_present else None),
                "has_all": bool(breakdown.get("has_all")),
                "current_tier": ent.tier,
                "current_tier_rank": cur_rank,
                "grace": bool(getattr(ent, "grace", False)),
                "enforced": not bool(getattr(ent, "grace", False)),
                "axes": breakdown.get("axes")
                or {
                    "features": None,
                    "runtimes": None,
                    "channels": None,
                    "retention_days": None,
                    "nodes": None,
                },
                "blocking_axes": breakdown.get("blocking_axes") or [],
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_has_all_breakdown: error: %s", exc)
        (channels_present, channels_ok, channels_n, channels_raw) = _shared._parse_capacity_arg(
            "channels"
        )
        (
            retention_present,
            retention_ok,
            retention_n,
            retention_raw,
        ) = _shared._parse_capacity_arg("retention_days")
        (nodes_present, nodes_ok, nodes_n, nodes_raw) = _shared._parse_capacity_arg("nodes")
        return _shared.jsonify(
            {
                "features": _shared._parse_csv_arg("features"),
                "runtimes": _shared._parse_csv_arg("runtimes"),
                "channels": channels_n if channels_ok else (channels_raw if channels_present else None),
                "retention_days": retention_n if retention_ok else (retention_raw if retention_present else None),
                "nodes": nodes_n if nodes_ok else (nodes_raw if nodes_present else None),
                "has_all": False,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
                "axes": {
                    "features": None,
                    "runtimes": None,
                    "channels": None,
                    "retention_days": None,
                    "nodes": None,
                },
                "blocking_axes": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/feature-catalog-at")
def api_entitlement_feature_catalog_at():
    raw = _shared.request.args.get("tier")
    tier = (raw or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.feature_catalog_at(tier)
        if body is None:
            return _shared.jsonify({"error": "unknown tier", "tier": tier}), 404
        return _shared.jsonify({"tier": tier, "features": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_feature_catalog_at: error: %s", exc)
        return _shared.jsonify({"error": "feature-catalog-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/runtime-catalog-at")
def api_entitlement_runtime_catalog_at():
    raw = _shared.request.args.get("tier")
    tier = (raw or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.runtime_catalog_at(tier)
        if body is None:
            return _shared.jsonify({"error": "unknown tier", "tier": tier}), 404
        return _shared.jsonify({"tier": tier, "runtimes": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_runtime_catalog_at: error: %s", exc)
        return _shared.jsonify({"error": "runtime-catalog-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/tier-catalog-at")
def api_entitlement_tier_catalog_at():
    raw = _shared.request.args.get("tier")
    tier = (raw or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.tier_catalog_at(tier)
        if body is None:
            return _shared.jsonify({"error": "unknown tier", "tier": tier}), 404
        return _shared.jsonify({"tier": tier, "tiers": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_catalog_at: error: %s", exc)
        return _shared.jsonify({"error": "tier-catalog-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/tier-catalog-at-batch")
def api_entitlement_tier_catalog_at_batch():
    tiers = _shared._parse_csv_arg("tiers")
    if not tiers:
        return _shared.jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.tier_catalog_at_batch(tiers)
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tier_catalog_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/feature-catalog-at-batch")
def api_entitlement_feature_catalog_at_batch():
    tiers = _shared._parse_csv_arg("tiers")
    if not tiers:
        return _shared.jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.feature_catalog_at_batch(tiers)
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_feature_catalog_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/runtime-catalog-at-batch")
def api_entitlement_runtime_catalog_at_batch():
    tiers = _shared._parse_csv_arg("tiers")
    if not tiers:
        return _shared.jsonify({"error": "supply tiers=<csv>"}), 400
    try:
        from clawmetry import entitlements as _ent

        batch = _ent.runtime_catalog_at_batch(tiers)
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tiers": batch.get("tiers", []),
                "unknown": batch.get("unknown", []),
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_runtime_catalog_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-spec-at")
def api_entitlement_tier_spec_at():
    raw_tier = _shared.request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_target = _shared.request.args.get("target")
    target = (raw_target or "").strip().lower()
    if not target:
        return _shared.jsonify({"error": "missing target"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "which": "tier", "tier": tier}),
                404,
            )
        if target not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {
                        "error": "unknown target",
                        "which": "target",
                        "target": target,
                    }
                ),
                404,
            )
        body = _ent.tier_spec_at(tier, target)
        if body is None:
            return (
                _shared.jsonify(
                    {
                        "error": "tier-spec-at failed",
                        "tier": tier,
                        "target": target,
                    }
                ),
                404,
            )
        return _shared.jsonify({"tier": tier, "target": target, "spec": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_spec_at: error: %s", exc)
        return _shared.jsonify({"error": "tier-spec-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/feature-spec-at")
def api_entitlement_feature_spec_at():
    raw_tier = _shared.request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_feature = _shared.request.args.get("feature")
    feature = (raw_feature or "").strip().lower()
    if not feature:
        return _shared.jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "which": "tier", "tier": tier}),
                404,
            )
        if feature not in _ent.ALL_FEATURES:
            return (
                _shared.jsonify(
                    {
                        "error": "unknown feature",
                        "which": "feature",
                        "feature": feature,
                    }
                ),
                404,
            )
        body = _ent.feature_spec_at(tier, feature)
        if body is None:
            return (
                _shared.jsonify(
                    {
                        "error": "feature-spec-at failed",
                        "tier": tier,
                        "feature": feature,
                    }
                ),
                404,
            )
        return _shared.jsonify({"tier": tier, "feature": feature, "spec": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_feature_spec_at: error: %s", exc)
        return _shared.jsonify({"error": "feature-spec-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/runtime-spec-at")
def api_entitlement_runtime_spec_at():
    raw_tier = _shared.request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_runtime = _shared.request.args.get("runtime")
    runtime_in = (raw_runtime or "").strip().lower()
    if not runtime_in:
        return _shared.jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "which": "tier", "tier": tier}),
                404,
            )
        rt = _ent.canonical_runtime(runtime_in)
        if not rt or rt not in _ent.ALL_RUNTIMES:
            return (
                _shared.jsonify(
                    {
                        "error": "unknown runtime",
                        "which": "runtime",
                        "runtime": runtime_in,
                    }
                ),
                404,
            )
        body = _ent.runtime_spec_at(tier, rt)
        if body is None:
            return (
                _shared.jsonify(
                    {
                        "error": "runtime-spec-at failed",
                        "tier": tier,
                        "runtime": rt,
                    }
                ),
                404,
            )
        return _shared.jsonify({"tier": tier, "runtime": rt, "spec": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_runtime_spec_at: error: %s", exc)
        return _shared.jsonify({"error": "runtime-spec-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/feature-spec")
def api_entitlement_feature_spec():
    raw = _shared.request.args.get("feature")
    feature = (raw or "").strip().lower()
    if not feature:
        return _shared.jsonify({"error": "missing feature"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.feature_spec(feature)
        if body is None:
            return (
                _shared.jsonify({"error": "unknown feature", "feature": feature}),
                404,
            )
        return _shared.jsonify(body)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_feature_spec: error: %s", exc)
        return _shared.jsonify({"error": "feature-spec failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/runtime-spec")
def api_entitlement_runtime_spec():
    raw = _shared.request.args.get("runtime")
    runtime = (raw or "").strip().lower()
    if not runtime:
        return _shared.jsonify({"error": "missing runtime"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.runtime_spec(runtime)
        if body is None:
            return (
                _shared.jsonify({"error": "unknown runtime", "runtime": runtime}),
                404,
            )
        return _shared.jsonify(body)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_runtime_spec: error: %s", exc)
        return _shared.jsonify({"error": "runtime-spec failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/channel-spec")
def api_entitlement_channel_spec():
    raw = _shared.request.args.get("channel")
    channel = (raw or "").strip().lower()
    if not channel:
        return _shared.jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        body = _ent.channel_spec(channel)
        if body is None:
            return (
                _shared.jsonify({"error": "unknown channel", "channel": channel}),
                404,
            )
        return _shared.jsonify(body)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_channel_spec: error: %s", exc)
        return _shared.jsonify({"error": "channel-spec failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/channel-spec-batch")
def api_entitlement_channel_spec_batch():
    try:
        channels = _shared._parse_csv_arg("channels")
        if not channels:
            return (
                _shared.jsonify({"error": "supply channels=<csv>"}),
                400,
            )
        from clawmetry import entitlements as _ent

        batch = _ent.channel_spec_batch(channels)
        ent = _ent.get_entitlement()
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_channel_spec_batch: error: %s", exc)
        return _shared.jsonify(
            {
                "channels": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/channel-spec-at")
def api_entitlement_channel_spec_at():
    raw_tier = _shared.request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    if not tier:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_channel = _shared.request.args.get("channel")
    channel = (raw_channel or "").strip().lower()
    if not channel:
        return _shared.jsonify({"error": "missing channel"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier not in _ent._TIER_ORDER:
            return (
                _shared.jsonify({"error": "unknown tier", "which": "tier", "tier": tier}),
                404,
            )
        if channel not in _ent.ALL_CHANNELS:
            return (
                _shared.jsonify(
                    {
                        "error": "unknown channel",
                        "which": "channel",
                        "channel": channel,
                    }
                ),
                404,
            )
        body = _ent.channel_spec_at(tier, channel)
        if body is None:
            return (
                _shared.jsonify(
                    {
                        "error": "channel-spec-at failed",
                        "tier": tier,
                        "channel": channel,
                    }
                ),
                404,
            )
        return _shared.jsonify({"tier": tier, "channel": channel, "spec": body})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_channel_spec_at: error: %s", exc)
        return _shared.jsonify({"error": "channel-spec-at failed"}), 500

@_shared.bp_entitlement.route("/api/entitlement/channel-spec-at-batch")
def api_entitlement_channel_spec_at_batch():
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        channels = _shared._parse_csv_arg("channels")
        if not channels:
            return (
                _shared.jsonify({"error": "supply channels=<csv>"}),
                400,
            )
        batch = _ent.channel_spec_at_batch(tier_in, channels)
        if batch is None:
            batch = {"channels": [], "unknown": []}
        ent = _ent.get_entitlement()
        batch["perspective_tier"] = tier_in
        batch["perspective_tier_rank"] = _ent.tier_rank(tier_in)
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_channel_spec_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "channels": [],
                "unknown": [],
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/feature-spec-batch")
def api_entitlement_feature_spec_batch():
    try:
        features = _shared._parse_csv_arg("features")
        if not features:
            return (
                _shared.jsonify({"error": "supply features=<csv>"}),
                400,
            )
        from clawmetry import entitlements as _ent

        batch = _ent.feature_spec_batch(features)
        ent = _ent.get_entitlement()
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_feature_spec_batch: error: %s", exc)
        return _shared.jsonify(
            {
                "features": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/runtime-spec-batch")
def api_entitlement_runtime_spec_batch():
    try:
        runtimes = _shared._parse_csv_arg("runtimes")
        if not runtimes:
            return (
                _shared.jsonify({"error": "supply runtimes=<csv>"}),
                400,
            )
        from clawmetry import entitlements as _ent

        batch = _ent.runtime_spec_batch(runtimes)
        ent = _ent.get_entitlement()
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning("api_entitlement_runtime_spec_batch: error: %s", exc)
        return _shared.jsonify(
            {
                "runtimes": [],
                "unknown": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-spec-at-batch")
def api_entitlement_tier_spec_at_batch():
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        targets = _shared._parse_csv_arg("targets")
        if not targets:
            return (
                _shared.jsonify({"error": "supply targets=<csv>"}),
                400,
            )
        batch = _ent.tier_spec_at_batch(tier_in, targets)
        if batch is None:
            batch = {"tiers": [], "unknown": []}
        ent = _ent.get_entitlement()
        batch["perspective_tier"] = tier_in
        batch["perspective_tier_rank"] = _ent.tier_rank(tier_in)
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_tier_spec_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "unknown": [],
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/feature-spec-at-batch")
def api_entitlement_feature_spec_at_batch():
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        features = _shared._parse_csv_arg("features")
        if not features:
            return (
                _shared.jsonify({"error": "supply features=<csv>"}),
                400,
            )
        batch = _ent.feature_spec_at_batch(tier_in, features)
        if batch is None:
            batch = {"features": [], "unknown": []}
        ent = _ent.get_entitlement()
        batch["perspective_tier"] = tier_in
        batch["perspective_tier_rank"] = _ent.tier_rank(tier_in)
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_feature_spec_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "features": [],
                "unknown": [],
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/runtime-spec-at-batch")
def api_entitlement_runtime_spec_at_batch():
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        runtimes = _shared._parse_csv_arg("runtimes")
        if not runtimes:
            return (
                _shared.jsonify({"error": "supply runtimes=<csv>"}),
                400,
            )
        batch = _ent.runtime_spec_at_batch(tier_in, runtimes)
        if batch is None:
            batch = {"runtimes": [], "unknown": []}
        ent = _ent.get_entitlement()
        batch["perspective_tier"] = tier_in
        batch["perspective_tier_rank"] = _ent.tier_rank(tier_in)
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return _shared.jsonify(batch)
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_runtime_spec_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "runtimes": [],
                "unknown": [],
                "perspective_tier": tier_in,
                "perspective_tier_rank": 0,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-unlocks-at")
def api_entitlement_tier_unlocks_at():
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_target = _shared.request.args.get("target")
    target_in = (raw_target or "").strip().lower()
    if not target_in:
        return _shared.jsonify({"error": "missing target"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if target_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {
                        "error": "unknown target",
                        "which": "target",
                        "target": target_in,
                    }
                ),
                404,
            )
        row = _ent.tier_unlocks_at(tier_in, target_in)
        if row is None:
            return (
                _shared.jsonify(
                    {
                        "error": "tier-unlocks-at failed",
                        "tier": tier_in,
                        "target": target_in,
                    }
                ),
                404,
            )
        return _shared.jsonify({"tier": tier_in, "target": target_in, "row": row})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_unlocks_at: error: %s", exc)
        return (
            _shared.jsonify(
                {
                    "error": "tier-unlocks-at failed",
                    "tier": tier_in,
                    "target": target_in,
                }
            ),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-locks-at")
def api_entitlement_tier_locks_at():
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    raw_target = _shared.request.args.get("target")
    target_in = (raw_target or "").strip().lower()
    if not target_in:
        return _shared.jsonify({"error": "missing target"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        if target_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {
                        "error": "unknown target",
                        "which": "target",
                        "target": target_in,
                    }
                ),
                404,
            )
        row = _ent.tier_locks_at(tier_in, target_in)
        if row is None:
            return (
                _shared.jsonify(
                    {
                        "error": "tier-locks-at failed",
                        "tier": tier_in,
                        "target": target_in,
                    }
                ),
                404,
            )
        return _shared.jsonify({"tier": tier_in, "target": target_in, "row": row})
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_locks_at: error: %s", exc)
        return (
            _shared.jsonify(
                {
                    "error": "tier-locks-at failed",
                    "tier": tier_in,
                    "target": target_in,
                }
            ),
            404,
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-unlocks-at-batch")
def api_entitlement_tier_unlocks_at_batch():
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.tier_unlocks_at_batch(tier_in) or []
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_unlocks_at_batch: error: %s", exc)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/tier-locks-at-batch")
def api_entitlement_tier_locks_at_batch():
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        rows = _ent.tier_locks_at_batch(tier_in) or []
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_tier_locks_at_batch: error: %s", exc)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/affordable-tiers")
def api_entitlement_affordable_tiers():
    try:
        from clawmetry import entitlements as _ent

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg(
            "retention_days",
        )
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                _shared.jsonify(
                    {
                        "error": (
                            "supply at least one of features=<csv>, "
                            "runtimes=<csv>, channels=<int>, "
                            "retention_days=<int>, or nodes=<int>"
                        )
                    }
                ),
                400,
            )

        ent = _ent.get_entitlement()
        rows = _ent.affordable_tiers(
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        ) or []

        cur_tier = ent.tier
        cur_rank = _ent.tier_rank(cur_tier)
        minimum_tier = rows[0]["tier"] if rows else None
        minimum_label = rows[0]["tier_label"] if rows else None
        minimum_rank = rows[0]["tier_rank"] if rows else -1

        augmented: list[dict] = []
        for row in rows:
            augmented.append(
                {
                    "tier": row["tier"],
                    "tier_label": row["tier_label"],
                    "tier_rank": row["tier_rank"],
                    "is_minimum": row["is_minimum"],
                    "is_current": row["tier"] == cur_tier,
                    "is_current_or_better": row["tier_rank"] >= cur_rank,
                }
            )

        return _shared.jsonify(
            {
                "features": features,
                "runtimes": runtimes,
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
                "current_tier": cur_tier,
                "current_tier_rank": cur_rank,
                "minimum_tier": minimum_tier,
                "minimum_tier_label": minimum_label,
                "minimum_tier_rank": minimum_rank,
                "tiers": augmented,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_affordable_tiers: error: %s", exc)
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")
        return _shared.jsonify(
            {
                "features": _shared._parse_csv_arg("features"),
                "runtimes": _shared._parse_csv_arg("runtimes"),
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "minimum_tier": None,
                "minimum_tier_label": None,
                "minimum_tier_rank": -1,
                "tiers": [],
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/required-tier-at")
def api_entitlement_required_tier_at():
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg(
            "retention_days",
        )
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                _shared.jsonify(
                    {
                        "error": (
                            "supply at least one of features=<csv>, "
                            "runtimes=<csv>, channels=<int>, "
                            "retention_days=<int>, or nodes=<int>"
                        )
                    }
                ),
                400,
            )

        required = _ent.min_tier_for_all_at(
            tier_in,
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        )

        ent = _ent.get_entitlement()
        cur_rank = _ent.tier_rank(ent.tier)
        persp_rank = _ent.tier_rank(tier_in)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None

        return _shared.jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": _ent.tier_label(tier_in),
                "perspective_tier_rank": persp_rank,
                "features": features,
                "runtimes": runtimes,
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "current_tier": ent.tier,
                "current_tier_rank": cur_rank,
                "upgrade_required_from_perspective": (
                    bool(required) and req_rank > persp_rank
                ),
                "upgrade_required_from_current": (
                    bool(required) and req_rank > cur_rank
                ),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_required_tier_at: error: %s", exc)
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")
        return _shared.jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": None,
                "perspective_tier_rank": -1,
                "features": _shared._parse_csv_arg("features"),
                "runtimes": _shared._parse_csv_arg("runtimes"),
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "upgrade_required_from_perspective": False,
                "upgrade_required_from_current": False,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/affordable-tiers-at")
def api_entitlement_affordable_tiers_at():
    raw_tier = _shared.request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return _shared.jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                _shared.jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

        features = _shared._parse_csv_arg("features")
        runtimes = _shared._parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg(
            "retention_days",
        )
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                _shared.jsonify(
                    {
                        "error": (
                            "supply at least one of features=<csv>, "
                            "runtimes=<csv>, channels=<int>, "
                            "retention_days=<int>, or nodes=<int>"
                        )
                    }
                ),
                400,
            )

        ent = _ent.get_entitlement()
        rows = _ent.affordable_tiers_at(
            tier_in,
            features=features or None,
            runtimes=runtimes or None,
            channels=channels_n if channels_ok else None,
            retention_days=retention_n if retention_ok else None,
            nodes=nodes_n if nodes_ok else None,
        ) or []

        cur_tier = ent.tier
        cur_rank = _ent.tier_rank(cur_tier)
        persp_rank = _ent.tier_rank(tier_in)
        minimum_tier = rows[0]["tier"] if rows else None
        minimum_label = rows[0]["tier_label"] if rows else None
        minimum_rank = rows[0]["tier_rank"] if rows else -1

        augmented: list[dict] = []
        for row in rows:
            augmented.append(
                {
                    "tier": row["tier"],
                    "tier_label": row["tier_label"],
                    "tier_rank": row["tier_rank"],
                    "is_minimum": row["is_minimum"],
                    "is_current": row["tier"] == cur_tier,
                    "is_current_or_better": row["tier_rank"] >= cur_rank,
                    "is_perspective": row["tier"] == tier_in,
                    "is_at_or_better_than_perspective": (
                        row["tier_rank"] >= persp_rank
                    ),
                }
            )

        return _shared.jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": _ent.tier_label(tier_in),
                "perspective_tier_rank": persp_rank,
                "features": features,
                "runtimes": runtimes,
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
                "current_tier": cur_tier,
                "current_tier_rank": cur_rank,
                "minimum_tier": minimum_tier,
                "minimum_tier_label": minimum_label,
                "minimum_tier_rank": minimum_rank,
                "tiers": augmented,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_affordable_tiers_at: error: %s", exc)
        (_, channels_ok, channels_n, _) = _shared._parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _shared._parse_capacity_arg("retention_days")
        (_, nodes_ok, nodes_n, _) = _shared._parse_capacity_arg("nodes")
        return _shared.jsonify(
            {
                "perspective_tier": tier_in,
                "perspective_tier_label": None,
                "perspective_tier_rank": -1,
                "features": _shared._parse_csv_arg("features"),
                "runtimes": _shared._parse_csv_arg("runtimes"),
                "channels": channels_n if channels_ok else None,
                "retention_days": retention_n if retention_ok else None,
                "nodes": nodes_n if nodes_ok else None,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "minimum_tier": None,
                "minimum_tier_label": None,
                "minimum_tier_rank": -1,
                "tiers": [],
                "grace": True,
                "enforced": False,
            }
        )
