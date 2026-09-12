"""routes/entitlement/_endpoints_04.py — endpoint handlers api_license_state_at .. api_entitlement_previous_tier_capacity_headroom_at_batch.

One of 8 handler modules split out of the former single-module
routes/entitlement.py. Handlers keep their original order; the split
points are size, not meaning, so read the package __init__ first.
"""

# Imported as a MODULE, not by name: a test that patches a helper (monkeypatch
# on routes.entitlement._shared) must still change what these handlers call.
# Binding the names here instead would freeze them at import time, which the
# single-module version never did.
from . import _shared

@_shared.bp_entitlement.route("/api/license/state-at")
def api_license_state_at():
    """``GET /api/license/state-at?epoch=<int>`` -- scalar view of the
    installed license's high-level lifecycle state evaluated as of
    ``epoch`` -- the perspective-epoch flavour of ``/api/license/state``,
    for a scheduled-audit / retrospective status badge that wants to
    answer "would we have shown the expired banner on <date>?" without
    the caller having to snapshot the license state at that time.

    Response shape (always HTTP 200)::

        {
          "state_at": "<active|expired|invalid|no_license>",  # evaluated at epoch
          "requested_epoch": <int|null>,      # int-coerced input, or null on typo
          "state": "<active|expired|invalid|no_license>",     # current-time state
          "expires_at": <int|null>,           # on-disk exp for comparison
          "has_license": <bool>,              # is a license file installed at all?
          "valid": <bool>                     # signature-valid AND not expired NOW
        }

    ``state_at`` mirrors :func:`clawmetry.license.license_state_at`
    exactly:

      * ``"active"``   -- signature-valid AND (perpetual OR ``exp > epoch``).
      * ``"expired"``  -- signature-valid, carries an ``exp`` claim, AND
        ``exp <= epoch``. Retrospective on a lapsed key when ``epoch``
        equals "now"; prospective on an active key when ``epoch`` is in
        the future beyond ``exp``.
      * ``"invalid"``  -- file exists but signature is bogus (time-
        independent).
      * ``"no_license"`` -- no license file on disk (also time-
        independent, and the fallback on missing / non-integer ``epoch``
        so a caller cannot silently mis-gate on a typo).

    Unlike ``/api/license/tier`` / ``/api/license/subject`` /
    ``/api/license/nodes`` (which surface ``null`` on the invalid /
    expired / no-license branches), this endpoint always carries a
    non-null string for ``state_at`` -- "no license" is a real answer
    here, not a missing answer, so a UI switch can bind directly on
    ``data.state_at`` without a null branch.

    Query parameter:

      * ``epoch`` -- required. Unix epoch seconds as an integer. A
        missing / non-integer / bool value collapses to
        ``state_at="no_license"`` with ``requested_epoch=null`` so a
        caller cannot silently mis-gate on a typo. HTTP status is 200
        either way -- the "bad input" signal is ``requested_epoch=null``
        plus the ``"no_license"`` state, not a 4xx, matching the never-
        crash posture of the surrounding license endpoints.

    Pairs with ``/api/license/is-expired-at`` /
    ``/api/license/is-expiring-at`` / ``/api/license/days-until-expiry-at``
    -- all four share the perspective-epoch input pattern and the
    ``_license_state_at_snapshot`` reader here carries ``expires_at`` /
    ``has_license`` / ``valid`` on the same shape those three carry, so
    a UI binding two for the same install cannot catch them
    disagreeing on the current-time reference fields.

    When ``epoch`` equals "now", the ``state_at`` field must byte-equal
    ``state`` (both derive from the same signed ``exp`` claim and use
    the same ``exp <= cutoff`` boundary via :func:`license_state_at` /
    :func:`license_state`), so a UI binding both cannot catch them
    disagreeing at the boundary.

    Never 5xxs -- any underlying failure degrades to
    ``{state_at: "no_license", requested_epoch: <echo>, state:
    "no_license", expires_at: null, has_license: false, valid: false}``
    (the OSS-free branch shape).
    """
    raw = _shared.request.args.get("epoch", "")
    try:
        requested = int(str(raw).strip())
    except (TypeError, ValueError):
        requested = None
    try:
        snap = _shared._license_state_at_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_state_at: snapshot error: %s", exc)
        snap = {
            "state": "no_license",
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    state_at = "no_license"
    if requested is not None:
        try:
            from clawmetry import license as _lic

            state_at = _lic.license_state_at(requested)
        except Exception as exc:
            _shared.logger.warning("api_license_state_at: derive error: %s", exc)
            state_at = "no_license"
    if not isinstance(state_at, str):
        state_at = "no_license"
    return _shared.jsonify(
        {
            "state_at": state_at,
            "requested_epoch": requested,
            "state": snap["state"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/is-state-at")
def api_license_is_state_at():
    """``GET /api/license/is-state-at?state=<name>&epoch=<int>`` --
    boolean gate for "was the installed license in state <X> evaluated
    as of ``epoch``?" -- the perspective-epoch flavour of
    ``/api/license/is-state``, for a scheduled-audit tile that wants to
    answer "would we have shown the expired banner on <date>?" without
    the caller having to snapshot the license state at that time or
    string-compare themselves.

    Query parameters:
      * ``state`` (str, required) -- the state to test against. One of
        ``"active"``, ``"expired"``, ``"invalid"``, ``"no_license"``.
        Compared case-insensitively after strip, matching
        :func:`clawmetry.license.is_state_at`. Missing / empty / unknown
        input degrades to ``is_state_at=false`` rather than a 4xx.
      * ``epoch`` (int, required) -- Unix epoch seconds. Missing / non-
        integer / bool input collapses ``state_at`` to ``"no_license"``
        and the predicate to ``false`` (unless ``state=no_license`` is
        also requested, in which case the answer is truthfully ``true``
        -- the perspective is unusable so the conservative "no
        entitlement" fallback holds).

    Response shape (always HTTP 200)::

        {
          "is_state_at": <bool>,
          "state_at": "<active|expired|invalid|no_license>",  # evaluated at epoch
          "requested_state": <str>,          # normalised echo of query
          "requested_epoch": <int|null>,     # int-coerced input, or null on typo
          "state": "<active|expired|invalid|no_license>",     # current-time state
          "expires_at": <int|null>,
          "has_license": <bool>,
          "valid": <bool>                    # signature-valid AND not expired NOW
        }

    ``is_state_at`` is ``True`` iff the perspective-epoch state
    byte-equals ``requested_state`` (after both are lower/stripped) AND
    the requested value is one of the four canonical states -- a typo
    like ``?state=actiev`` returns ``is_state_at=false`` so a caller
    cannot silently mis-gate on a mis-spelled state name.

    Mirrors :func:`clawmetry.license.is_state_at` -- the HTTP shape
    layers ``state_at`` / ``requested_state`` / ``requested_epoch`` /
    ``state`` / ``expires_at`` / ``has_license`` / ``valid`` on top of
    that bool so a widget never needs a second call to
    ``/api/license/state-at`` (or ``/api/license/state``) to render the
    accompanying "you're in state <X>" copy.

    When ``epoch`` equals "now" and ``state`` is a canonical value, this
    endpoint must agree with ``/api/license/is-state`` at the boundary
    for the same install -- both derive from the same signed ``exp``
    claim via :func:`license_state_at` / :func:`license_state`, so a UI
    binding both cannot catch them disagreeing at the boundary.

    Never 5xxs -- any underlying failure degrades to the OSS-free
    branch shape (``is_state_at=false``, ``state_at="no_license"``,
    ``state="no_license"``, ``expires_at=null``, ``has_license=false``,
    ``valid=false``), matching the never-crash posture of the
    surrounding license endpoints.
    """
    from clawmetry.license import LICENSE_STATES

    raw_state = _shared.request.args.get("state", "") or ""
    try:
        requested_state = str(raw_state).strip().lower()
    except Exception:
        requested_state = ""
    raw_epoch = _shared.request.args.get("epoch", "")
    try:
        requested_epoch = int(str(raw_epoch).strip())
    except (TypeError, ValueError):
        requested_epoch = None
    try:
        snap = _shared._license_state_at_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_is_state_at: snapshot error: %s", exc)
        snap = {
            "state": "no_license",
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    state_at = "no_license"
    if requested_epoch is not None:
        try:
            from clawmetry import license as _lic

            state_at = _lic.license_state_at(requested_epoch)
        except Exception as exc:
            _shared.logger.warning("api_license_is_state_at: derive error: %s", exc)
            state_at = "no_license"
    if not isinstance(state_at, str):
        state_at = "no_license"
    match = bool(
        requested_state
        and requested_state in LICENSE_STATES
        and state_at == requested_state
    )
    return _shared.jsonify(
        {
            "is_state_at": match,
            "state_at": state_at,
            "requested_state": requested_state,
            "requested_epoch": requested_epoch,
            "state": snap["state"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/state-at-batch")
def api_license_state_at_batch():
    """``GET /api/license/state-at-batch?epochs=<int>,<int>,...`` --
    per-value batch sibling of ``/api/license/state-at``.

    Where the singular endpoint folds ONE perspective epoch to ONE
    license-state string, this preserves per-value rows so a scheduled-
    audit tile that wants to plot state across a sequence of dates
    ("was the key active at each of these audit dates?") renders off
    ONE round-trip instead of N calls to ``/api/license/state-at``.
    Wraps :func:`clawmetry.license.license_state_at_batch`.

    ``epochs=`` is required. Missing / blank / only-commas -> ``400
    missing epochs``. Comma-separated tokens are normalised the way the
    underlying batch helper normalises them: whitespace-stripped, then
    handed to :func:`clawmetry.license.license_state_at_batch`, which
    dedupes by parsed int key preserving first-seen order and collapses
    non-int / ``bool`` / ``None`` tokens to a row with
    ``state="no_license"`` (never-mis-gate posture matching the scalar
    endpoint). Never 5xxs: a resolver failure returns the empty-rows
    envelope with the current-time snapshot fields intact.

    Response shape (always HTTP 200)::

        {
          "kind":  "license_state_at",
          "count": <int>,               # len(rows)
          "rows":  [
            {"epoch": <int|"<raw>">, "state": "<active|expired|invalid|no_license>"},
            ...
          ],
          "state":       "<active|expired|invalid|no_license>",  # NOW
          "expires_at":  <int|null>,    # on-disk exp for comparison
          "has_license": <bool>,
          "valid":       <bool>         # signature-valid AND not expired NOW
        }

    Per-row parity with ``/api/license/state-at?epoch=<n>`` is pinned in
    the test suite so the batch cannot silently drift from the scalar
    endpoint.
    """
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._license_state_at_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_state_at_batch: snapshot error: %s", exc)
        snap = {
            "state": "no_license",
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        rows = _lic.license_state_at_batch(tokens)
    except Exception as exc:
        _shared.logger.warning("api_license_state_at_batch: derive error: %s", exc)
        rows = []
    return _shared.jsonify(
        {
            "kind": "license_state_at",
            "count": len(rows),
            "rows": rows,
            "state": snap["state"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/is-state-at-batch")
def api_license_is_state_at_batch():
    """``GET /api/license/is-state-at-batch?state=<name>&epochs=<int>,<int>,...``
    -- shared-``state`` batch sibling of ``/api/license/is-state-at``.

    Where the singular endpoint folds ONE ``(state, epoch)`` pair to ONE
    "was the license in state <X> as-of epoch?" bool, this preserves
    per-value rows for a fixed ``state`` across a sequence of
    perspective epochs so a scheduled-audit tile answering "would we
    have shown the <state> banner on each of these audit dates?" (e.g.
    "expired on any of my quarterly review dates?") hydrates the whole
    column in ONE round-trip instead of fanning out N calls to the
    scalar. Wraps :func:`clawmetry.license.is_state_at_batch`. Same
    "shared threshold applied to EVERY row, per-row epoch" shape as
    ``/api/license/expiring-within-at`` -- both take one gate query
    parameter plus a batch of epochs.

    Query parameters:
      * ``state`` (str, required in-spirit) -- the state to test
        against. One of ``"active"``, ``"expired"``, ``"invalid"``,
        ``"no_license"``. Compared case-insensitively after strip,
        matching :func:`clawmetry.license.is_state_at`. Missing / empty
        / unknown value degrades EVERY row to ``is_state=false``
        (matches the never-mis-gate posture of the scalar) rather
        than a 4xx -- a caller on a stale UI shouldn't have the whole
        batch hidden behind a typo.
      * ``epochs`` (CSV of ints, required) -- Missing / blank / only-
        commas -> ``400 missing epochs``. Comma-separated tokens are
        stripped, then handed to
        :func:`clawmetry.license.is_state_at_batch`, which dedupes by
        parsed int key preserving first-seen order and collapses
        non-int / ``bool`` / ``None`` tokens to a row with
        ``is_state=false`` (unless ``state="no_license"`` is requested,
        in which case the bad-epoch row truthfully reports
        ``is_state=true`` -- the perspective is unusable so the
        conservative "no entitlement" fallback of
        :func:`license_state_at` holds; the batch inherits that
        semantics from the scalar).

    Response shape (always HTTP 200)::

        {
          "kind":            "is_state_at",
          "count":           <int>,               # len(rows)
          "requested_state": <str>,               # normalised echo of query
          "rows":  [
            {"epoch": <int|"<raw>">, "is_state": <bool>},
            ...
          ],
          "state":       "<active|expired|invalid|no_license>",  # NOW
          "expires_at":  <int|null>,              # on-disk exp for comparison
          "has_license": <bool>,
          "valid":       <bool>                   # signature-valid AND not expired NOW
        }

    Envelope carries the same current-time snapshot fields (``state`` /
    ``expires_at`` / ``has_license`` / ``valid``) as the surrounding
    ``/api/license/*-at-batch`` quartet so a UI binding several
    endpoints for the same install cannot catch them disagreeing. Row
    shape mirrors ``/api/license/is-expired-at-batch`` /
    ``/api/license/is-expiring-at-batch`` so a caller assembling a
    timeline can zip the responses index-for-index by epoch.

    Per-row parity with ``/api/license/is-state-at?state=<X>&epoch=<n>``
    is pinned in the test suite so the batch cannot silently drift from
    the scalar endpoint.

    Deliberately strict on the ``state`` parameter, matching the
    scalar: an ill-typed or unknown state collapses every row to
    ``false`` rather than returning something a caller might treat as
    a soft-match. Never 5xxs -- any underlying failure degrades to
    the OSS-free branch shape (empty rows envelope with the OSS-free
    snapshot fields intact).
    """
    raw_state = _shared.request.args.get("state", "") or ""
    try:
        requested_state = str(raw_state).strip().lower()
    except Exception:
        requested_state = ""
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._license_state_at_snapshot()
    except Exception as exc:
        _shared.logger.warning(
            "api_license_is_state_at_batch: snapshot error: %s", exc
        )
        snap = {
            "state": "no_license",
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        rows = _lic.is_state_at_batch(requested_state, tokens)
    except Exception as exc:
        _shared.logger.warning(
            "api_license_is_state_at_batch: derive error: %s", exc
        )
        rows = []
    return _shared.jsonify(
        {
            "kind": "is_state_at",
            "count": len(rows),
            "requested_state": requested_state,
            "rows": rows,
            "state": snap["state"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/is-expired-at-batch")
def api_license_is_expired_at_batch():
    """``GET /api/license/is-expired-at-batch?epochs=<int>,<int>,...``
    -- per-value batch sibling of ``/api/license/is-expired-at``.

    Boolean-expiry-axis twin of ``/api/license/state-at-batch``. Where
    the singular endpoint folds ONE perspective epoch to ONE "was it
    expired?" bool, this preserves per-value rows so a scheduled audit
    can hydrate an "was it expired at each of these dates?" column in
    one call. Wraps :func:`clawmetry.license.is_expired_at_batch`.

    Row shape mirrors ``/api/license/state-at-batch`` per-row so a
    caller assembling a timeline can zip the two responses index-for-
    index. Same query-string posture: ``epochs=`` required (missing /
    blank / only-commas -> ``400``), comma-separated tokens deduped by
    parsed int key preserving first-seen order, non-int / ``bool`` /
    ``None`` tokens collapse to ``expired=false``. Never 5xxs.

    Response shape (always HTTP 200)::

        {
          "kind":  "is_expired_at",
          "count": <int>,
          "rows":  [
            {"epoch": <int|"<raw>">, "expired": <bool>},
            ...
          ],
          "state":       "<active|expired|invalid|no_license>",  # NOW
          "expires_at":  <int|null>,
          "has_license": <bool>,
          "valid":       <bool>
        }

    Per-row parity with ``/api/license/is-expired-at?epoch=<n>`` is
    pinned in the test suite so the batch cannot silently drift from the
    scalar endpoint.
    """
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._license_state_at_snapshot()
    except Exception as exc:
        _shared.logger.warning(
            "api_license_is_expired_at_batch: snapshot error: %s", exc
        )
        snap = {
            "state": "no_license",
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        rows = _lic.is_expired_at_batch(tokens)
    except Exception as exc:
        _shared.logger.warning(
            "api_license_is_expired_at_batch: derive error: %s", exc
        )
        rows = []
    return _shared.jsonify(
        {
            "kind": "is_expired_at",
            "count": len(rows),
            "rows": rows,
            "state": snap["state"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/is-valid-at-batch")
def api_license_is_valid_at_batch():
    """``GET /api/license/is-valid-at-batch?epochs=<int>,<int>,...``
    -- per-value batch sibling of ``/api/license/is-valid-at``.

    Entitlement-boolean axis batch companion to
    ``/api/license/state-at-batch`` /
    ``/api/license/is-expired-at-batch`` /
    ``/api/license/days-until-expiry-at-batch``. Where the singular
    endpoint folds ONE perspective epoch to ONE "was this node
    entitled?" bool, this preserves per-value rows so a scheduled-audit
    tile can hydrate a "would we have granted Pro on each of these
    dates?" column in ONE call instead of fanning out N calls to the
    scalar endpoint. Wraps :func:`clawmetry.license.is_license_valid_at_batch`.

    Row shape mirrors ``/api/license/is-expired-at-batch`` per-row so a
    caller assembling an entitlement timeline can zip the two responses
    index-for-index; ``is_valid`` is exactly the complement of the
    matching ``expired`` field on a signature-valid, non-perpetual key
    and both collapse to ``false`` together on the no-license /
    invalid-signature branches. Same query-string posture: ``epochs=``
    required (missing / blank / only-commas -> ``400``), comma-separated
    tokens deduped by parsed int key preserving first-seen order,
    non-int / ``bool`` / ``None`` tokens collapse to ``is_valid=false``.
    Never 5xxs.

    Response shape (always HTTP 200)::

        {
          "kind":  "is_license_valid_at",
          "count": <int>,
          "rows":  [
            {"epoch": <int|"<raw>">, "is_valid": <bool>},
            ...
          ],
          "state":       "<active|expired|invalid|no_license>",  # NOW
          "expires_at":  <int|null>,
          "has_license": <bool>,
          "valid":       <bool>
        }

    Per-row parity with ``/api/license/is-valid-at?epoch=<n>`` is pinned
    in the test suite so the batch cannot silently drift from the scalar
    endpoint. The never-mis-gate posture matches
    :func:`clawmetry.license.is_license_valid_at`: a bad row cannot
    silently unlock a Pro feature retroactively.
    """
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._license_state_at_snapshot()
    except Exception as exc:
        _shared.logger.warning(
            "api_license_is_valid_at_batch: snapshot error: %s", exc
        )
        snap = {
            "state": "no_license",
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        rows = _lic.is_license_valid_at_batch(tokens)
    except Exception as exc:
        _shared.logger.warning(
            "api_license_is_valid_at_batch: derive error: %s", exc
        )
        rows = []
    return _shared.jsonify(
        {
            "kind": "is_license_valid_at",
            "count": len(rows),
            "rows": rows,
            "state": snap["state"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/days-until-expiry-at-batch")
def api_license_days_until_expiry_at_batch():
    """``GET /api/license/days-until-expiry-at-batch?epochs=<int>,<int>,...``
    -- per-value batch sibling of ``/api/license/days-until-expiry-at``.

    Days-remaining axis twin of ``/api/license/state-at-batch`` /
    ``/api/license/is-expired-at-batch``. Where the singular endpoint
    folds ONE perspective epoch to ONE signed day-count, this preserves
    per-value rows so a scheduled audit can plot a countdown across a
    sequence of perspective dates in one call. Wraps
    :func:`clawmetry.license.days_until_expiry_at_batch`.

    Row shape mirrors the other two ``_at_batch`` license endpoints so a
    caller assembling an audit timeline can zip all three responses
    index-for-index. Same query-string posture: ``epochs=`` required
    (missing / blank / only-commas -> ``400``), comma-separated tokens
    deduped by parsed int key preserving first-seen order, non-int /
    ``bool`` / ``None`` tokens collapse to ``days=null``. Never 5xxs.

    Response shape (always HTTP 200)::

        {
          "kind":  "days_until_expiry_at",
          "count": <int>,
          "rows":  [
            {"epoch": <int|"<raw>">, "days": <int|null>},
            ...
          ],
          "state":       "<active|expired|invalid|no_license>",  # NOW
          "expires_at":  <int|null>,
          "has_license": <bool>,
          "valid":       <bool>
        }

    Per-row parity with ``/api/license/days-until-expiry-at?epoch=<n>``
    is pinned in the test suite so the batch cannot silently drift from
    the scalar endpoint.
    """
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._license_state_at_snapshot()
    except Exception as exc:
        _shared.logger.warning(
            "api_license_days_until_expiry_at_batch: snapshot error: %s", exc
        )
        snap = {
            "state": "no_license",
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        rows = _lic.days_until_expiry_at_batch(tokens)
    except Exception as exc:
        _shared.logger.warning(
            "api_license_days_until_expiry_at_batch: derive error: %s", exc
        )
        rows = []
    return _shared.jsonify(
        {
            "kind": "days_until_expiry_at",
            "count": len(rows),
            "rows": rows,
            "state": snap["state"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/is-expiring-at-batch")
def api_license_is_expiring_at_batch():
    """``GET /api/license/is-expiring-at-batch?epochs=<int>,<int>,...``
    -- per-value batch sibling of ``/api/license/is-expiring-at``.

    Renewal-detection axis batch companion to
    ``/api/license/state-at-batch`` /
    ``/api/license/is-expired-at-batch`` /
    ``/api/license/days-until-expiry-at-batch``. Where the singular
    endpoint folds ONE candidate ``exp`` value to ONE "does the on-disk
    key still expire on that date?" bool, this preserves per-value
    rows so a renewal-reminder tile that binds several cached ``exp``
    candidates (e.g. "we warned about <date>; then <date>; then
    <date>") can detect a renewal on the on-disk key in one call
    instead of fanning out to the scalar endpoint. Wraps
    :func:`clawmetry.license.is_expiring_at_batch`.

    Row shape mirrors ``/api/license/is-expired-at-batch`` per-row so
    a caller assembling a renewal timeline can zip the two responses
    index-for-index. Same query-string posture: ``epochs=`` required
    (missing / blank / only-commas -> ``400``), comma-separated tokens
    deduped by parsed int key preserving first-seen order, non-int /
    ``bool`` / ``None`` tokens collapse to ``is_expiring=false``.
    Never 5xxs.

    Response shape (always HTTP 200)::

        {
          "kind":  "is_expiring_at",
          "count": <int>,
          "rows":  [
            {"epoch": <int|"<raw>">, "is_expiring": <bool>},
            ...
          ],
          "state":       "<active|expired|invalid|no_license>",  # NOW
          "expires_at":  <int|null>,
          "has_license": <bool>,
          "valid":       <bool>
        }

    Deliberately strict on validity, unlike the sibling
    ``/api/license/days-until-expiry-at-batch`` (which is lenient on
    expiry so a support tile can render "expired 12 days ago"). See
    :func:`clawmetry.license.is_expiring_at` for the rationale: a
    predicate that fired ``true`` on a lapsed key would push callers
    to gate renewal UI on a value that no longer implies entitlement.

    Per-row parity with ``/api/license/is-expiring-at?epoch=<n>`` is
    pinned in the test suite so the batch cannot silently drift from
    the scalar endpoint.
    """
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._license_state_at_snapshot()
    except Exception as exc:
        _shared.logger.warning(
            "api_license_is_expiring_at_batch: snapshot error: %s", exc
        )
        snap = {
            "state": "no_license",
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        rows = _lic.is_expiring_at_batch(tokens)
    except Exception as exc:
        _shared.logger.warning(
            "api_license_is_expiring_at_batch: derive error: %s", exc
        )
        rows = []
    return _shared.jsonify(
        {
            "kind": "is_expiring_at",
            "count": len(rows),
            "rows": rows,
            "state": snap["state"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/expiring-within-at-batch")
def api_license_expiring_within_at_batch():
    """``GET /api/license/expiring-within-at-batch?days=<int>&epochs=
    <int>,<int>,...`` -- per-value batch sibling of
    ``/api/license/expiring-within-at``.

    Renewal-window axis batch companion to the existing ``exp``-derived
    ``/api/license/*-at-batch`` quartet
    (``state-at-batch`` / ``is-expired-at-batch`` /
    ``days-until-expiry-at-batch`` / ``is-expiring-at-batch``). Where
    the singular endpoint folds ONE perspective epoch to ONE "would we
    have shown a renewal warning as of that date?" bool, this preserves
    per-value rows so a scheduled-audit tile that wants to plot the
    renewal-window banner across a sequence of perspective dates
    ("would the renewal banner have fired on each of these audit
    dates?") renders off ONE round-trip instead of N calls to the
    scalar. Wraps :func:`clawmetry.license.is_expiring_within_at_batch`.

    Row shape mirrors ``/api/license/is-expiring-at-batch`` per-row so
    a caller assembling a full renewal timeline can zip the batches
    index-for-index. Same query-string posture on ``epochs=`` as the
    surrounding quartet: required (missing / blank / only-commas ->
    ``400 missing epochs``), comma-separated tokens deduped by parsed
    int key preserving first-seen order, non-int / ``bool`` / ``None``
    tokens collapse to ``expiring_within=false``. Never 5xxs.

    Query parameters:

      * ``days`` (int, optional) -- the renewal-window threshold applied
        to EVERY row. Defaults to ``30`` (matches the singular
        ``/api/license/expiring-within-at`` default). Negative input
        clamps to ``0``; non-numeric / ``bool`` input collapses to
        ``expiring_within=false`` on every row with
        ``threshold_days=0`` rather than a 4xx, matching the surrounding
        endpoints' never-5xx / never-4xx posture. Callers wanting
        per-row thresholds should call the scalar N times.
      * ``epochs`` (CSV, required) -- perspective epochs (Unix seconds).

    Response shape (always HTTP 200)::

        {
          "kind":          "expiring_within_at",
          "count":         <int>,               # len(rows)
          "threshold_days": <int>,              # int-coerced days, clamped >= 0
          "rows":  [
            {"epoch": <int|"<raw>">, "expiring_within": <bool>},
            ...
          ],
          "state":       "<active|expired|invalid|no_license>",  # NOW
          "expires_at":  <int|null>,
          "has_license": <bool>,
          "valid":       <bool>
        }

    Deliberately strict on validity, mirroring the singular
    ``/api/license/expiring-within-at`` and the sibling
    ``/api/license/is-expiring-at-batch``: a predicate that fired
    ``true`` on a lapsed key would push callers to gate renewal UI on a
    value that no longer implies entitlement. See
    :func:`clawmetry.license.is_expiring_within_at` for the rationale.

    Per-row parity with ``/api/license/expiring-within-at?days=<d>
    &epoch=<n>`` is pinned in the test suite so the batch cannot
    silently drift from the scalar endpoint.
    """
    raw_days = _shared.request.args.get("days", "30")
    if isinstance(raw_days, bool):
        threshold = 0
        threshold_ok = False
    else:
        try:
            threshold = int(raw_days)
            threshold_ok = True
        except (TypeError, ValueError):
            threshold = 0
            threshold_ok = False
    if threshold < 0:
        threshold = 0
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._license_state_at_snapshot()
    except Exception as exc:
        _shared.logger.warning(
            "api_license_expiring_within_at_batch: snapshot error: %s",
            exc,
        )
        snap = {
            "state": "no_license",
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        if threshold_ok:
            rows = _lic.is_expiring_within_at_batch(threshold, tokens)
        else:
            # Bad ``days=`` collapses every row to False while preserving
            # the row slots so the response length still matches the input
            # (mirrors the singular endpoint's never-4xx posture on a
            # typo). Delegate to the same batch helper with a sentinel
            # bool that the helper refuses -- keeps the dedup / bad-token
            # bucketing consistent with the "good" path.
            rows = _lic.is_expiring_within_at_batch(True, tokens)
    except Exception as exc:
        _shared.logger.warning(
            "api_license_expiring_within_at_batch: derive error: %s", exc
        )
        rows = []
    # Batch helper emits ``is_expiring_within`` per row; rename to
    # ``expiring_within`` here so the HTTP row field matches the
    # scalar endpoint's ``/api/license/expiring-within-at`` response
    # shape (``expiring_within``) and a caller can hydrate a paywall
    # tile off either endpoint interchangeably.
    rows = [
        {
            "epoch": row["epoch"],
            "expiring_within": bool(row["is_expiring_within"]),
        }
        for row in rows
    ]
    return _shared.jsonify(
        {
            "kind": "expiring_within_at",
            "count": len(rows),
            "threshold_days": threshold,
            "rows": rows,
            "state": snap["state"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/expiring-within-days-at-batch")
def api_license_expiring_within_days_at_batch():
    """``GET /api/license/expiring-within-days-at-batch?days=<int>,<int>,
    ...&epoch=<int>`` -- days-axis batch sibling of
    ``/api/license/expiring-within-at``.

    Complement of ``/api/license/expiring-within-at-batch`` on the
    orthogonal axis: where that endpoint fans a fixed ``days`` threshold
    across N perspective epochs, this fans N ``days`` thresholds across
    a SINGLE perspective epoch. The natural shape for a "renewal
    urgency" tile that wants to fire at multiple thresholds (7 / 14 /
    30 / 60 days) off ONE hydration rather than 4 calls to
    ``/api/license/expiring-within-at?days=<d>``. Wraps
    :func:`clawmetry.license.is_expiring_within_days_at_batch`.

    Query parameters:

      * ``days`` (CSV, required) -- comma-separated renewal-window
        thresholds. Missing / blank / only-commas -> ``400 missing days``.
        Tokens are int-coerced by the helper; non-int / ``bool`` /
        ``None`` / negative tokens collapse to
        ``expiring_within=false`` per-row (their slot is preserved so
        the row length still matches N).
      * ``epoch`` (int, optional) -- the perspective epoch (Unix
        seconds) applied to EVERY row. Defaults to the current time
        (matches the singular ``/api/license/expiring-within-at`` on the
        "as of now" branch). Non-numeric / ``bool`` collapses every row
        to ``expiring_within=false`` with ``epoch`` echoed back as the
        raw token, matching the never-4xx / never-5xx posture of the
        surrounding batch endpoints.

    Response shape (always HTTP 200)::

        {
          "kind":  "expiring_within_days_at",
          "count": <int>,               # len(rows)
          "epoch": <int>|"<raw>",       # int-coerced epoch (or the
                                        #   original token if bad)
          "rows":  [
            {"days": <int|"<raw>">, "expiring_within": <bool>},
            ...
          ],
          "state":       "<active|expired|invalid|no_license>",  # NOW
          "expires_at":  <int|null>,
          "has_license": <bool>,
          "valid":       <bool>
        }

    Shares the current-time snapshot fields with the sibling
    ``/api/license/expiring-within-at-batch`` so a UI binding both for
    the same install cannot catch them disagreeing on ``state`` /
    ``expires_at`` / ``has_license`` / ``valid``. Never 5xxs: an
    underlying snapshot / batch failure degrades to the OSS-free
    fallback shape.

    Deliberately strict on validity, mirroring
    ``/api/license/expiring-within-at`` and its sibling epochs-axis
    batch: a predicate that fired ``true`` on a lapsed key would push
    callers to gate renewal UI on a value that no longer implies
    entitlement. Per-row parity with ``/api/license/expiring-within-at
    ?days=<d>&epoch=<n>`` is pinned in the test suite so the batch
    cannot silently drift from the scalar endpoint.
    """
    raw_epoch = _shared.request.args.get("epoch")
    if raw_epoch is None:
        parsed_epoch = int(_shared.time.time())
        epoch_field: object = parsed_epoch
        epoch_ok = True
    else:
        if isinstance(raw_epoch, bool):
            parsed_epoch = 0
            epoch_field = str(raw_epoch)
            epoch_ok = False
        else:
            try:
                parsed_epoch = int(raw_epoch)
                epoch_field = parsed_epoch
                epoch_ok = True
            except (TypeError, ValueError):
                parsed_epoch = 0
                epoch_field = str(raw_epoch)
                epoch_ok = False
    tokens, err = _shared._parse_license_days_csv("days")
    if err == "missing":
        return _shared.jsonify({"error": "missing days"}), 400
    try:
        snap = _shared._license_state_at_snapshot()
    except Exception as exc:
        _shared.logger.warning(
            "api_license_expiring_within_days_at_batch: snapshot error: %s",
            exc,
        )
        snap = {
            "state": "no_license",
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        if epoch_ok:
            rows = _lic.is_expiring_within_days_at_batch(tokens, parsed_epoch)
        else:
            # Bad ``epoch=`` collapses every row to False while preserving
            # the row slots. Delegate to the same batch helper with a
            # sentinel bool that the helper refuses -- keeps the dedup /
            # bad-token bucketing consistent with the "good" path.
            rows = _lic.is_expiring_within_days_at_batch(tokens, True)
    except Exception as exc:
        _shared.logger.warning(
            "api_license_expiring_within_days_at_batch: derive error: %s",
            exc,
        )
        rows = []
    # Batch helper emits ``is_expiring_within`` per row; rename to
    # ``expiring_within`` here so the HTTP row field matches the scalar
    # endpoint's ``/api/license/expiring-within-at`` response shape
    # (``expiring_within``) and a caller can hydrate a paywall tile off
    # either endpoint interchangeably.
    rows = [
        {
            "days": row["days"],
            "expiring_within": bool(row["is_expiring_within"]),
        }
        for row in rows
    ]
    return _shared.jsonify(
        {
            "kind": "expiring_within_days_at",
            "count": len(rows),
            "epoch": epoch_field,
            "rows": rows,
            "state": snap["state"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/age-days-at-batch")
def api_license_age_days_at_batch():
    """``GET /api/license/age-days-at-batch?epochs=<int>,<int>,...`` --
    per-value batch sibling of ``/api/license/age-days-at``.

    License-age axis batch companion to the ``exp``-derived
    ``/api/license/days-until-expiry-at-batch``. Where the singular
    endpoint folds ONE perspective epoch to ONE signed "days from
    ``iat`` to epoch" scalar, this preserves per-value rows so a
    scheduled-audit / retrospective tile that wants to plot license
    age across a sequence of perspective dates (e.g. "how old was the
    key when we shipped each of these builds?") renders off ONE
    round-trip instead of N calls to the scalar. Wraps
    :func:`clawmetry.license.license_age_days_at_batch`.

    Row shape mirrors ``/api/license/days-until-expiry-at-batch``
    per-row so a caller assembling a full audit timeline can zip the
    two responses index-for-index -- "N days old and M days
    remaining" per epoch. Same query-string posture: ``epochs=``
    required (missing / blank / only-commas -> ``400``), comma-
    separated tokens deduped by parsed int key preserving first-seen
    order, non-int / ``bool`` / ``None`` tokens collapse to
    ``days=null``. Never 5xxs.

    Response shape (always HTTP 200)::

        {
          "kind":  "license_age_days_at",
          "count": <int>,
          "rows":  [
            {"epoch": <int|"<raw>">, "days": <int|null>},
            ...
          ],
          "issued_at":   <int|null>,        # current on-disk iat
          "age_days":    <int|null>,        # age NOW (clamped >= 0)
          "has_license": <bool>,
          "valid":       <bool>             # signature-valid AND not expired NOW
        }

    Snapshot fields are drawn from :func:`_license_issued_snapshot`
    (the ``iat``-derived quartet), matching the singular
    ``/api/license/age-days-at`` endpoint, so a UI binding both for
    the same install cannot catch them disagreeing on ``issued_at`` /
    ``has_license`` / ``valid`` / current-time ``age_days``. Note the
    snapshot's ``age_days`` is the "now" flavour (clamped to ``>= 0``
    for clock-skew), whereas per-row ``days`` in ``rows`` is the
    signed perspective value -- deliberately different by design so
    the retrospective column can render "N days before issuance" while
    the header still hides clock-skew.

    Deliberately lenient on expiry, mirroring
    ``/api/license/age-days-at``: a signed-but-lapsed key still
    surfaces its real per-row ``days`` and current ``age_days`` so a
    support/audit tile can render "was 12 days old as of that date"
    without special-casing the expired branch. The ``valid`` field
    independently carries the "signature-valid AND not expired"
    signal for callers that DO want to hide the row on lapsed keys.

    Per-row parity with ``/api/license/age-days-at?epoch=<n>`` is
    pinned in the test suite so the batch cannot silently drift from
    the scalar endpoint.
    """
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._license_issued_snapshot()
    except Exception as exc:
        _shared.logger.warning(
            "api_license_age_days_at_batch: snapshot error: %s", exc
        )
        snap = {
            "issued_at": None,
            "age_days": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        rows = _lic.license_age_days_at_batch(tokens)
    except Exception as exc:
        _shared.logger.warning(
            "api_license_age_days_at_batch: derive error: %s", exc
        )
        rows = []
    return _shared.jsonify(
        {
            "kind": "license_age_days_at",
            "count": len(rows),
            "rows": rows,
            "issued_at": snap["issued_at"],
            "age_days": snap["age_days"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/tier-at")
def api_license_tier_at():
    """``GET /api/license/tier-at?epoch=<int>`` -- scalar view of the
    installed license's tier claim evaluated as of ``epoch`` -- the
    perspective-epoch flavour of ``/api/license/tier``, for a
    scheduled-audit / retrospective badge that wants to answer "what
    tier was this node on <date>?" without the caller having to
    snapshot the license state at that time or compare ``exp`` to a
    caller-supplied epoch themselves.

    Response shape (always HTTP 200)::

        {
          "tier_at": <str|null>,          # tier as of epoch
          "requested_epoch": <int|null>,  # int-coerced input, or null on typo
          "tier": <str|null>,             # current-time tier
          "expires_at": <int|null>,       # on-disk exp for comparison
          "has_license": <bool>,          # is a license file installed at all?
          "valid": <bool>                 # signature-valid AND not expired NOW
        }

    ``tier_at`` mirrors :func:`clawmetry.license.license_tier_at`:
    ``None`` for no license, invalid signature, an ``exp`` claim
    that has already lapsed at ``epoch``, or a signed payload whose
    ``tier`` claim is absent / non-string / empty; otherwise the
    normalised (lowercased, stripped) tier string.

    Query parameter:

      * ``epoch`` -- required. Unix epoch seconds as an integer. A
        missing / non-integer / bool value collapses to
        ``tier_at=null`` with ``requested_epoch=null`` so a caller
        cannot silently mis-gate on a typo. HTTP status is 200 either
        way -- the "bad input" signal is ``requested_epoch=null`` plus
        the ``null`` tier, not a 4xx, matching the never-crash posture
        of the surrounding license endpoints.

    Pairs with ``/api/license/state-at`` / ``/api/license/is-expired-at``
    / ``/api/license/days-until-expiry-at`` / ``/api/license/expiring-
    within-at`` -- all five share the perspective-epoch input pattern
    and the ``_license_tier_at_snapshot`` reader here carries
    ``expires_at`` / ``has_license`` / ``valid`` on the same shape the
    state-derived trio carries, so a UI binding two for the same
    install cannot catch them disagreeing on the current-time
    reference fields.

    When ``epoch`` equals "now", the ``tier_at`` field must byte-equal
    ``tier`` (both derive from the same signed ``tier`` claim, refuse
    the invalid-signature branch, and use the same ``exp <= cutoff``
    boundary via :func:`license_tier_at` / :func:`license_tier`), so
    a UI binding both cannot catch them disagreeing at the boundary.

    Never 5xxs -- any underlying failure degrades to
    ``{tier_at: null, requested_epoch: <echo>, tier: null,
    expires_at: null, has_license: false, valid: false}`` (the OSS-
    free branch shape).
    """
    raw = _shared.request.args.get("epoch", "")
    try:
        requested = int(str(raw).strip())
    except (TypeError, ValueError):
        requested = None
    try:
        snap = _shared._license_tier_at_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_tier_at: snapshot error: %s", exc)
        snap = {
            "tier": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    tier_at: str | None = None
    if requested is not None:
        try:
            from clawmetry import license as _lic

            tier_at = _lic.license_tier_at(requested)
        except Exception as exc:
            _shared.logger.warning("api_license_tier_at: derive error: %s", exc)
            tier_at = None
    if tier_at is not None and not isinstance(tier_at, str):
        tier_at = None
    return _shared.jsonify(
        {
            "tier_at": tier_at,
            "requested_epoch": requested,
            "tier": snap["tier"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/tier-at-batch")
def api_license_tier_at_batch():
    """``GET /api/license/tier-at-batch?epochs=<int>,<int>,...`` --
    per-value batch sibling of ``/api/license/tier-at``.

    Where the singular endpoint folds ONE perspective epoch to ONE
    license-tier answer, this preserves per-value rows so a scheduled-
    audit tile that wants to plot tier across a sequence of dates
    ("what tier was this node on each of these audit dates?") renders
    off ONE round-trip instead of N calls to ``/api/license/tier-at``.
    Wraps :func:`clawmetry.license.license_tier_at_batch`.

    ``epochs=`` is required. Missing / blank / only-commas -> ``400
    missing epochs``. Comma-separated tokens are normalised the way
    the underlying batch helper normalises them: whitespace-stripped,
    then handed to :func:`clawmetry.license.license_tier_at_batch`,
    which dedupes by parsed int key preserving first-seen order and
    collapses non-int / ``bool`` / ``None`` tokens to a row with
    ``tier=null`` (never-mis-gate posture matching the scalar
    endpoint). Never 5xxs: a resolver failure returns the empty-rows
    envelope with the current-time snapshot fields intact.

    Response shape (always HTTP 200)::

        {
          "kind":  "license_tier_at",
          "count": <int>,               # len(rows)
          "rows":  [
            {"epoch": <int|"<raw>">, "tier": <str|null>},
            ...
          ],
          "tier":        <str|null>,    # current-time tier
          "expires_at":  <int|null>,    # on-disk exp for comparison
          "has_license": <bool>,
          "valid":       <bool>         # signature-valid AND not expired NOW
        }

    Per-row parity with ``/api/license/tier-at?epoch=<n>`` is pinned in
    the test suite so the batch cannot silently drift from the scalar
    endpoint. Shares :func:`_license_tier_at_snapshot` with the scalar
    endpoint so the current-time reference fields (``tier`` /
    ``expires_at`` / ``has_license`` / ``valid``) cannot disagree
    between the two for the same install.
    """
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._license_tier_at_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_tier_at_batch: snapshot error: %s", exc)
        snap = {
            "tier": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        rows = _lic.license_tier_at_batch(tokens)
    except Exception as exc:
        _shared.logger.warning("api_license_tier_at_batch: derive error: %s", exc)
        rows = []
    return _shared.jsonify(
        {
            "kind": "license_tier_at",
            "count": len(rows),
            "rows": rows,
            "tier": snap["tier"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/is-tier-at")
def api_license_is_tier_at():
    """``GET /api/license/is-tier-at?tier=<name>&epoch=<int>`` -- boolean
    gate for "was the installed license on tier <X> evaluated as of
    ``epoch``?" -- the perspective-epoch flavour of ``/api/license/
    is-tier``, for a scheduled-audit tile that wants to answer "was
    this node Pro on <date>?" without the caller having to snapshot
    the license state at that time or compare ``exp`` to a caller-
    supplied epoch themselves.

    Query parameters:
      * ``tier`` (str, required in-spirit) -- the tier to test against.
        Compared case-insensitively after strip, matching
        :func:`clawmetry.license.is_tier_at`. Missing / empty / non-
        string input degrades to ``is_tier_at=false`` rather than a
        4xx, matching the surrounding endpoints' never-5xx / never-4xx
        posture. Unlike ``/api/license/is-state-at`` (which validates
        against the closed ``LICENSE_STATES`` set), the tier axis is
        deliberately open-ended -- a future tier lands without a code
        change here, matching :func:`clawmetry.license.is_tier`'s
        open-ended posture.
      * ``epoch`` (int, required in-spirit) -- Unix epoch seconds.
        Missing / non-integer / bool input collapses ``tier_at`` to
        ``null`` and the predicate to ``false`` (there is no tier to
        match against once the perspective is unusable -- the
        conservative "no entitlement" fallback matching the never-mis-
        gate posture of the surrounding ``_at`` family).

    Response shape (always HTTP 200)::

        {
          "is_tier_at":      <bool>,
          "tier_at":         <str|null>,    # tier as of epoch
          "requested_tier":  <str>,         # normalised echo of query
          "requested_epoch": <int|null>,    # int-coerced input, or null on typo
          "tier":            <str|null>,    # current-time tier
          "expires_at":      <int|null>,
          "has_license":     <bool>,
          "valid":           <bool>         # signature-valid AND not expired NOW
        }

    ``is_tier_at`` is ``True`` iff the perspective-epoch tier byte-
    equals ``requested_tier`` (after both are lower/stripped) AND the
    requested value is a non-empty string -- an empty / missing
    ``tier=`` query returns ``is_tier_at=false`` so a caller cannot
    silently claim a tier that would grant unearned entitlement.

    Mirrors :func:`clawmetry.license.is_tier_at` -- the HTTP shape
    layers ``tier_at`` / ``requested_tier`` / ``requested_epoch`` /
    ``tier`` / ``expires_at`` / ``has_license`` / ``valid`` on top of
    that bool so a widget never needs a second call to
    ``/api/license/tier-at`` (or ``/api/license/tier``) to render the
    accompanying "you were on tier <X>" copy.

    When ``epoch`` equals "now" and ``tier`` is a non-empty string,
    this endpoint must agree with ``/api/license/is-tier`` at the
    boundary for the same install -- both derive from the same signed
    ``tier`` claim via :func:`license_tier_at` / :func:`license_tier`,
    so a UI binding both cannot catch them disagreeing at the boundary.

    Shares :func:`_license_tier_at_snapshot` with ``/api/license/
    tier-at{,-batch}`` so the current-time reference fields (``tier``
    / ``expires_at`` / ``has_license`` / ``valid``) cannot disagree
    between the sibling endpoints for the same install.

    Never 5xxs -- any underlying failure degrades to the OSS-free
    branch shape (``is_tier_at=false``, ``tier_at=null``,
    ``tier=null``, ``expires_at=null``, ``has_license=false``,
    ``valid=false``), matching the never-crash posture of the
    surrounding license endpoints.
    """
    raw_tier = _shared.request.args.get("tier", "") or ""
    try:
        requested_tier = str(raw_tier).strip().lower()
    except Exception:
        requested_tier = ""
    raw_epoch = _shared.request.args.get("epoch", "")
    try:
        requested_epoch = int(str(raw_epoch).strip())
    except (TypeError, ValueError):
        requested_epoch = None
    try:
        snap = _shared._license_tier_at_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_is_tier_at: snapshot error: %s", exc)
        snap = {
            "tier": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    tier_at: str | None = None
    if requested_epoch is not None:
        try:
            from clawmetry import license as _lic

            tier_at = _lic.license_tier_at(requested_epoch)
        except Exception as exc:
            _shared.logger.warning("api_license_is_tier_at: derive error: %s", exc)
            tier_at = None
    if tier_at is not None and not isinstance(tier_at, str):
        tier_at = None
    match = bool(
        requested_tier
        and isinstance(tier_at, str)
        and tier_at == requested_tier
    )
    return _shared.jsonify(
        {
            "is_tier_at": match,
            "tier_at": tier_at,
            "requested_tier": requested_tier,
            "requested_epoch": requested_epoch,
            "tier": snap["tier"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/is-tier-at-batch")
def api_license_is_tier_at_batch():
    """``GET /api/license/is-tier-at-batch?tier=<name>&epochs=<int>,<int>,...``
    -- shared-``tier`` batch sibling of ``/api/license/is-tier-at``.

    Where the singular endpoint folds ONE ``(tier, epoch)`` pair to
    ONE "was the license on tier <X> as-of epoch?" bool, this
    preserves per-value rows for a fixed ``tier`` across a sequence
    of perspective epochs so a scheduled-audit tile answering "was
    this node Pro on each of these audit dates?" hydrates the whole
    column in ONE round-trip instead of fanning out N calls to the
    scalar. Wraps :func:`clawmetry.license.is_tier_at_batch`. Same
    "shared threshold applied to EVERY row, per-row epoch" shape as
    ``/api/license/is-state-at-batch`` -- both take one gate query
    parameter plus a batch of epochs.

    Query parameters:
      * ``tier`` (str, required in-spirit) -- the tier to test
        against. Compared case-insensitively after strip, matching
        :func:`clawmetry.license.is_tier_at`. Missing / empty / non-
        string value degrades EVERY row to ``is_tier=false`` (matches
        the never-mis-gate posture of the scalar) rather than a 4xx
        -- a caller on a stale UI shouldn't have the whole batch
        hidden behind a typo. Deliberately open-ended (no ``LICENSE_
        STATES``-style whitelist) so a future tier lands without a
        code change.
      * ``epochs`` (CSV of ints, required) -- Missing / blank /
        only-commas -> ``400 missing epochs``. Comma-separated tokens
        are stripped, then handed to
        :func:`clawmetry.license.is_tier_at_batch`, which dedupes by
        parsed int key preserving first-seen order and collapses
        non-int / ``bool`` / ``None`` tokens to a row with
        ``is_tier=false`` (unlike ``/api/license/is-state-at-batch``,
        there is no meaningful "no-license tier" the caller could
        ask for, since :func:`license_tier` already returns ``None``
        -- not a sentinel string -- on that branch).

    Response shape (always HTTP 200)::

        {
          "kind":           "is_tier_at",
          "count":          <int>,             # len(rows)
          "requested_tier": <str>,             # normalised echo of query
          "rows":  [
            {"epoch": <int|"<raw>">, "is_tier": <bool>},
            ...
          ],
          "tier":        <str|null>,           # current-time tier
          "expires_at":  <int|null>,           # on-disk exp for comparison
          "has_license": <bool>,
          "valid":       <bool>                # signature-valid AND not expired NOW
        }

    Envelope carries the same current-time snapshot fields (``tier`` /
    ``expires_at`` / ``has_license`` / ``valid``) as the surrounding
    ``/api/license/tier-at{,-batch}`` and ``/api/license/is-tier-at``
    endpoints so a UI binding several endpoints for the same install
    cannot catch them disagreeing. Row shape mirrors ``/api/license/
    is-state-at-batch`` so a caller assembling a timeline can zip the
    responses index-for-index by epoch.

    Per-row parity with ``/api/license/is-tier-at?tier=<X>&epoch=<n>``
    is pinned in the test suite so the batch cannot silently drift
    from the scalar endpoint.

    Never 5xxs -- any underlying failure degrades to the OSS-free
    branch shape (empty rows envelope with the OSS-free snapshot
    fields intact).
    """
    raw_tier = _shared.request.args.get("tier", "") or ""
    try:
        requested_tier = str(raw_tier).strip().lower()
    except Exception:
        requested_tier = ""
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._license_tier_at_snapshot()
    except Exception as exc:
        _shared.logger.warning(
            "api_license_is_tier_at_batch: snapshot error: %s", exc
        )
        snap = {
            "tier": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        rows = _lic.is_tier_at_batch(requested_tier, tokens)
    except Exception as exc:
        _shared.logger.warning(
            "api_license_is_tier_at_batch: derive error: %s", exc
        )
        rows = []
    return _shared.jsonify(
        {
            "kind": "is_tier_at",
            "count": len(rows),
            "requested_tier": requested_tier,
            "rows": rows,
            "tier": snap["tier"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/is-subject-at-batch")
def api_license_is_subject_at_batch():
    """``GET /api/license/is-subject-at-batch?subject=<value>&epochs=<int>,<int>,...``
    -- shared-``subject`` batch sibling of ``/api/license/is-subject-at``.

    Where the singular endpoint folds ONE ``(subject, epoch)`` pair to
    ONE "was this node licensed to <account> as-of epoch?" bool, this
    preserves per-value rows for a fixed ``subject`` across a sequence
    of perspective epochs so a scheduled-audit tile answering "was
    this node bound to <account> on each of these audit dates?"
    hydrates the whole column in ONE round-trip instead of fanning
    out N calls to the scalar. Wraps
    :func:`clawmetry.license.is_subject_at_batch`. Same "shared
    threshold applied to EVERY row, per-row epoch" shape as
    ``/api/license/is-state-at-batch`` /
    ``/api/license/is-tier-at-batch`` -- one gate query parameter
    plus a batch of epochs.

    Query parameters:
      * ``subject`` (str, required in-spirit) -- the subject to test
        against. Compared case-insensitively after strip, matching
        :func:`clawmetry.license.is_subject_at`. Missing / empty /
        non-string value degrades EVERY row to ``is_subject=false``
        (matches the never-mis-gate posture of the scalar) rather
        than a 4xx -- a caller on a stale UI shouldn't have the whole
        batch hidden behind a typo. Deliberately open-ended (no
        ``LICENSE_STATES``-style whitelist) since a subject typically
        encodes an account id / email / tenant handle that the code
        here has no business whitelisting, matching :func:`is_subject`
        / :func:`is_subject_at` posture on the singular axes.
      * ``epochs`` (CSV of ints, required) -- Missing / blank /
        only-commas -> ``400 missing epochs``. Comma-separated tokens
        are stripped, then handed to
        :func:`clawmetry.license.is_subject_at_batch`, which dedupes
        by parsed int key preserving first-seen order and collapses
        non-int / ``bool`` / ``None`` tokens to a row with
        ``is_subject=false`` (unlike ``/api/license/is-state-at-batch``,
        there is no meaningful "no-license subject" the caller could
        ask for, since :func:`license_subject` already returns
        ``None`` -- not a sentinel string -- on that branch).

    Response shape (always HTTP 200)::

        {
          "kind":              "is_subject_at",
          "count":             <int>,           # len(rows)
          "requested_subject": <str>,           # normalised echo of query
          "rows":  [
            {"epoch": <int|"<raw>">, "is_subject": <bool>},
            ...
          ],
          "subject":     <str|null>,            # current-time subject (case preserved)
          "expires_at":  <int|null>,            # on-disk exp for comparison
          "has_license": <bool>,
          "valid":       <bool>                 # signature-valid AND not expired NOW
        }

    Envelope carries the same current-time snapshot fields
    (``subject`` / ``expires_at`` / ``has_license`` / ``valid``) as
    the surrounding ``/api/license/subject-at{,-batch}`` and
    ``/api/license/is-subject-at`` endpoints so a UI binding several
    endpoints for the same install cannot catch them disagreeing.
    Row shape mirrors ``/api/license/is-tier-at-batch`` /
    ``/api/license/is-state-at-batch`` so a caller assembling a
    timeline can zip the responses index-for-index by epoch.

    Per-row parity with
    ``/api/license/is-subject-at?subject=<X>&epoch=<n>`` is pinned in
    the test suite so the batch cannot silently drift from the scalar
    endpoint.

    Shares :func:`_license_subject_at_snapshot` with the sibling
    ``/api/license/subject-at`` and ``/api/license/is-subject-at``
    endpoints so the current-time reference fields cannot disagree
    between siblings for the same install.

    Never 5xxs -- any underlying failure degrades to the OSS-free
    branch shape (empty rows envelope with the OSS-free snapshot
    fields intact).
    """
    raw_subject = _shared.request.args.get("subject", "") or ""
    try:
        requested_subject = str(raw_subject).strip().lower()
    except Exception:
        requested_subject = ""
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._license_subject_at_snapshot()
    except Exception as exc:
        _shared.logger.warning(
            "api_license_is_subject_at_batch: snapshot error: %s", exc
        )
        snap = {
            "subject": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        rows = _lic.is_subject_at_batch(requested_subject, tokens)
    except Exception as exc:
        _shared.logger.warning(
            "api_license_is_subject_at_batch: derive error: %s", exc
        )
        rows = []
    return _shared.jsonify(
        {
            "kind": "is_subject_at",
            "count": len(rows),
            "requested_subject": requested_subject,
            "rows": rows,
            "subject": snap["subject"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/features-at")
def api_license_features_at():
    """``GET /api/license/features-at?epoch=<int>`` -- scalar view of
    the installed license's ``features`` claim evaluated as of
    ``epoch`` -- the perspective-epoch flavour of
    ``/api/license/features``, for a scheduled-audit / retrospective
    diagnostic tile that wants to answer "which paid features was this
    node entitled to on <date>?" without the caller having to snapshot
    the license state at that time or compare ``exp`` to a caller-
    supplied epoch themselves.

    Response shape (always HTTP 200)::

        {
          "features_at": [<id>, ...] | null,   # features as of epoch
          "requested_epoch": <int|null>,       # int-coerced input, or null on typo
          "features": [<id>, ...] | null,      # current-time features
          "expires_at": <int|null>,            # on-disk exp for comparison
          "has_license": <bool>,               # is a license file installed at all?
          "valid": <bool>                      # signature-valid AND not expired NOW
        }

    ``features_at`` mirrors :func:`clawmetry.license.license_features_at`:

      * ``null`` on no license, invalid signature, an ``exp`` claim
        that has already lapsed at ``epoch``, or missing / non-integer
        / bool ``epoch`` so a caller cannot silently mis-gate on a
        typo.
      * ``[]`` on a signature-valid license AS OF ``epoch`` whose
        payload carries no explicit ``features`` claim. Distinct from
        ``null``: a UI binding this endpoint must render both branches
        (``null`` -> "no entitlement at that time", ``[]`` -> "entitled
        but no features itemised") without collapsing them.
      * A sorted, deduplicated, normalised (lower/strip) list of
        feature ids otherwise.

    Query parameter:

      * ``epoch`` -- required. Unix epoch seconds as an integer. A
        missing / non-integer / bool value collapses to
        ``features_at=null`` with ``requested_epoch=null`` so a caller
        cannot silently mis-gate on a typo. HTTP status is 200 either
        way -- the "bad input" signal is ``requested_epoch=null`` plus
        the ``null`` features, not a 4xx, matching the never-crash
        posture of the surrounding license endpoints.

    Pairs with ``/api/license/state-at`` / ``/api/license/tier-at`` /
    ``/api/license/is-expired-at`` / ``/api/license/days-until-expiry-at``
    -- all four share the perspective-epoch input pattern and the
    ``_license_features_at_snapshot`` reader here carries
    ``expires_at`` / ``has_license`` / ``valid`` on the same shape the
    state-derived siblings carry, so a UI binding two for the same
    install cannot catch them disagreeing on the current-time
    reference fields.

    When ``epoch`` equals "now", the ``features_at`` field must byte-
    equal ``features`` (both derive from the same signed ``features``
    claim, refuse the invalid-signature branch, and use the same
    ``exp <= cutoff`` boundary via :func:`license_features_at` /
    :func:`license_features`), so a UI binding both cannot catch them
    disagreeing at the boundary.

    Note: the ``features`` claim is a SUPPLEMENTAL string list carried
    on the license token; it is NOT the canonical open-core feature
    catalogue. For the resolved feature set actually enforced by
    gates, read ``/api/entitlement`` (which layers this claim on top of
    the FREE-tier baseline). This endpoint surfaces the claim exactly
    as written on the token with the perspective-epoch validity gate on
    top.

    Never 5xxs -- any underlying failure degrades to
    ``{features_at: null, requested_epoch: <echo>, features: null,
    expires_at: null, has_license: false, valid: false}`` (the OSS-
    free branch shape).
    """
    raw = _shared.request.args.get("epoch", "")
    try:
        requested = int(str(raw).strip())
    except (TypeError, ValueError):
        requested = None
    try:
        snap = _shared._license_features_at_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_features_at: snapshot error: %s", exc)
        snap = {
            "features": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    features_at: list | None = None
    if requested is not None:
        try:
            from clawmetry import license as _lic

            features_at = _lic.license_features_at(requested)
        except Exception as exc:
            _shared.logger.warning("api_license_features_at: derive error: %s", exc)
            features_at = None
    if features_at is not None and not isinstance(features_at, list):
        features_at = None
    return _shared.jsonify(
        {
            "features_at": features_at,
            "requested_epoch": requested,
            "features": snap["features"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/features-at-batch")
def api_license_features_at_batch():
    """``GET /api/license/features-at-batch?epochs=<int>,<int>,...`` --
    per-value batch sibling of ``/api/license/features-at``.

    Where the singular endpoint folds ONE perspective epoch to ONE
    features answer, this preserves per-value rows so a scheduled-audit
    tile that wants to plot the ``features`` claim across a sequence of
    dates ("which features was this node entitled to on each of these
    audit dates?") renders off ONE round-trip instead of N calls to
    ``/api/license/features-at``. Wraps
    :func:`clawmetry.license.license_features_at_batch`.

    ``epochs=`` is required. Missing / blank / only-commas -> ``400
    missing epochs``. Comma-separated tokens are normalised the way the
    underlying batch helper normalises them: whitespace-stripped, then
    handed to :func:`clawmetry.license.license_features_at_batch`,
    which dedupes by parsed int key preserving first-seen order and
    collapses non-int / ``bool`` / ``None`` tokens to a row with
    ``features=null`` (never-mis-gate posture matching the scalar
    endpoint). Never 5xxs: a resolver failure returns the empty-rows
    envelope with the current-time snapshot fields intact.

    Response shape (always HTTP 200)::

        {
          "kind":  "license_features_at",
          "count": <int>,               # len(rows)
          "rows":  [
            {"epoch": <int|"<raw>">, "features": [<id>, ...]|null},
            ...
          ],
          "features":    [<id>, ...] | null,   # current-time features
          "expires_at":  <int|null>,           # on-disk exp for comparison
          "has_license": <bool>,
          "valid":       <bool>                # signature-valid AND not expired NOW
        }

    Per-row parity with ``/api/license/features-at?epoch=<n>`` is
    pinned in the test suite so the batch cannot silently drift from
    the scalar endpoint. Shares :func:`_license_features_at_snapshot`
    with the scalar endpoint so the current-time reference fields
    (``features`` / ``expires_at`` / ``has_license`` / ``valid``)
    cannot disagree between the two for the same install.
    """
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._license_features_at_snapshot()
    except Exception as exc:
        _shared.logger.warning(
            "api_license_features_at_batch: snapshot error: %s", exc
        )
        snap = {
            "features": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        rows = _lic.license_features_at_batch(tokens)
    except Exception as exc:
        _shared.logger.warning(
            "api_license_features_at_batch: derive error: %s", exc
        )
        rows = []
    return _shared.jsonify(
        {
            "kind": "license_features_at",
            "count": len(rows),
            "rows": rows,
            "features": snap["features"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/has-feature-at")
def api_license_has_feature_at():
    """``GET /api/license/has-feature-at?feature=<id>&epoch=<int>`` --
    boolean gate for "did the installed license claim feature <X>
    evaluated as of ``epoch``?" -- the perspective-epoch flavour of
    ``/api/license/has-feature``, for a scheduled-audit tile that
    wants to answer "was this node entitled to feature <X> on <date>?"
    without the caller having to snapshot the license state at that
    time or compare ``exp`` to a caller-supplied epoch themselves.

    Query parameters:
      * ``feature`` (str, required in-spirit) -- the feature id to
        test against. Compared case-insensitively after strip, matching
        :func:`clawmetry.license.has_feature_at`. Missing / empty /
        non-string input degrades to ``has_feature_at=false`` rather
        than a 4xx, matching the surrounding endpoints' never-5xx /
        never-4xx posture.
      * ``epoch`` (int, required in-spirit) -- Unix epoch seconds.
        Missing / non-integer / bool input collapses ``features_at``
        to ``null`` and the predicate to ``false`` (there is no
        features list to search once the perspective is unusable --
        the conservative "no entitlement" fallback matching the never-
        mis-gate posture of the surrounding ``_at`` family).

    Response shape (always HTTP 200)::

        {
          "has_feature_at":    <bool>,
          "features_at":       [<id>, ...] | null,   # features as of epoch
          "requested_feature": <str>,                # normalised echo of query
          "requested_epoch":   <int|null>,           # int-coerced input, or null on typo
          "features":          [<id>, ...] | null,   # current-time features
          "expires_at":        <int|null>,
          "has_license":       <bool>,
          "valid":             <bool>                # signature-valid AND not expired NOW
        }

    ``has_feature_at`` is ``True`` iff the perspective-epoch features
    list is a list AND contains the normalised ``requested_feature``
    AND the requested value is a non-empty string -- an empty /
    missing ``feature=`` query returns ``has_feature_at=false`` so a
    caller cannot silently claim a feature that would grant unearned
    entitlement.

    Mirrors :func:`clawmetry.license.has_feature_at` -- the HTTP shape
    layers ``features_at`` / ``requested_feature`` / ``requested_epoch``
    / ``features`` / ``expires_at`` / ``has_license`` / ``valid`` on
    top of that bool so a widget never needs a second call to
    ``/api/license/features-at`` (or ``/api/license/features``) to
    render the accompanying "you had feature <X> then" copy.

    When ``epoch`` equals "now" and ``feature`` is a non-empty string,
    this endpoint must agree with ``/api/license/has-feature`` at the
    boundary for the same install -- both derive from the same signed
    ``features`` claim via :func:`license_features_at` /
    :func:`license_features`, so a UI binding both cannot catch them
    disagreeing at the boundary.

    Shares :func:`_license_features_at_snapshot` with ``/api/license/
    features-at{,-batch}`` so the current-time reference fields
    (``features`` / ``expires_at`` / ``has_license`` / ``valid``)
    cannot disagree between the sibling endpoints for the same
    install.

    Note: the ``features`` claim is a SUPPLEMENTAL string list carried
    on the license token; it is NOT the canonical open-core feature
    catalogue. This endpoint answers *"did the KEY carry this feature
    id at <epoch>?"*, not *"was this feature enforced at <epoch>?"*.
    For the resolved feature set actually enforced by gates, read
    ``/api/entitlement`` (which layers this claim on top of the
    FREE-tier baseline).

    Never 5xxs -- any underlying failure degrades to the OSS-free
    branch shape (``has_feature_at=false``, ``features_at=null``,
    ``features=null``, ``expires_at=null``, ``has_license=false``,
    ``valid=false``), matching the never-crash posture of the
    surrounding license endpoints.
    """
    raw_feature = _shared.request.args.get("feature", "") or ""
    try:
        requested_feature = str(raw_feature).strip().lower()
    except Exception:
        requested_feature = ""
    raw_epoch = _shared.request.args.get("epoch", "")
    try:
        requested_epoch = int(str(raw_epoch).strip())
    except (TypeError, ValueError):
        requested_epoch = None
    try:
        snap = _shared._license_features_at_snapshot()
    except Exception as exc:
        _shared.logger.warning("api_license_has_feature_at: snapshot error: %s", exc)
        snap = {
            "features": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    features_at: list | None = None
    if requested_epoch is not None:
        try:
            from clawmetry import license as _lic

            features_at = _lic.license_features_at(requested_epoch)
        except Exception as exc:
            _shared.logger.warning(
                "api_license_has_feature_at: derive error: %s", exc
            )
            features_at = None
    if features_at is not None and not isinstance(features_at, list):
        features_at = None
    match = bool(
        requested_feature
        and isinstance(features_at, list)
        and requested_feature in features_at
    )
    return _shared.jsonify(
        {
            "has_feature_at": match,
            "features_at": features_at,
            "requested_feature": requested_feature,
            "requested_epoch": requested_epoch,
            "features": snap["features"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/has-feature-at-batch")
def api_license_has_feature_at_batch():
    """``GET /api/license/has-feature-at-batch?feature=<id>&epochs=<int>,<int>,...``
    -- shared-``feature`` batch sibling of ``/api/license/has-feature-at``.

    Where the singular endpoint folds ONE ``(feature, epoch)`` pair to
    ONE "did the KEY claim feature <X> as-of epoch?" bool, this
    preserves per-value rows for a fixed ``feature`` across a sequence
    of perspective epochs so a scheduled-audit tile answering "was this
    node entitled to feature <X> on each of these audit dates?" (e.g.
    "did alerts fire on any of my quarterly review dates?") hydrates
    the whole column in ONE round-trip instead of fanning out N calls
    to ``/api/license/has-feature-at``. Wraps
    :func:`clawmetry.license.has_feature_at_batch`. Same "shared
    threshold applied to EVERY row, per-row epoch" shape as
    ``/api/license/is-state-at-batch`` / ``/api/license/expiring-within-at-batch``
    -- one gate query parameter plus a batch of epochs.

    Query parameters:
      * ``feature`` (str, required in-spirit) -- the feature id to
        test against. Compared case-insensitively after strip, matching
        :func:`clawmetry.license.has_feature_at`. Missing / empty /
        whitespace-only degrades EVERY row to ``has_feature=false``
        (matches the never-mis-gate posture of the scalar) rather than
        a 4xx -- a caller on a stale UI shouldn't have the whole batch
        hidden behind a typo.
      * ``epochs`` (CSV of ints, required) -- Missing / blank / only-
        commas -> ``400 missing epochs``. Comma-separated tokens are
        stripped, then handed to
        :func:`clawmetry.license.has_feature_at_batch`, which dedupes
        by parsed int key preserving first-seen order and collapses
        non-int / ``bool`` / ``None`` tokens to a row with
        ``has_feature=false`` (matches the ``has_feature_at`` scalar's
        rejection of unusable epochs -- there is no features list to
        search once the perspective is unusable, so the conservative
        "no entitlement" fallback holds).

    Response shape (always HTTP 200)::

        {
          "kind":              "has_feature_at",
          "count":             <int>,               # len(rows)
          "requested_feature": <str>,               # normalised echo of query
          "rows":  [
            {"epoch": <int|"<raw>">, "has_feature": <bool>},
            ...
          ],
          "features":    [<id>, ...] | null,   # current-time features
          "expires_at":  <int|null>,           # on-disk exp for comparison
          "has_license": <bool>,
          "valid":       <bool>                # signature-valid AND not expired NOW
        }

    Envelope carries the same current-time snapshot fields (``features`` /
    ``expires_at`` / ``has_license`` / ``valid``) as the surrounding
    ``/api/license/features-at{,-batch}`` / ``/api/license/has-feature-at``
    trio so a UI binding several endpoints for the same install cannot
    catch them disagreeing. Row shape mirrors
    ``/api/license/is-state-at-batch`` /
    ``/api/license/is-expired-at-batch`` so a caller assembling a
    timeline can zip the responses index-for-index by epoch.

    Per-row parity with ``/api/license/has-feature-at?feature=<X>&epoch=<n>``
    is pinned in the test suite so the batch cannot silently drift from
    the scalar endpoint. Shares :func:`_license_features_at_snapshot`
    with ``/api/license/features-at{,-batch}`` /
    ``/api/license/has-feature-at`` so the current-time reference fields
    (``features`` / ``expires_at`` / ``has_license`` / ``valid``)
    cannot disagree between the sibling endpoints for the same install.

    Note: the ``features`` claim is a SUPPLEMENTAL string list carried
    on the license token; it is NOT the canonical open-core feature
    catalogue. This endpoint answers *"did the KEY carry this feature
    id at each of <epochs>?"*, not *"was this feature enforced at each
    of <epochs>?"*. For the resolved feature set actually enforced by
    gates, read ``/api/entitlement`` (which layers this claim on top of
    the FREE-tier baseline).

    Never 5xxs -- any underlying failure degrades to the OSS-free
    branch shape (empty rows envelope with the OSS-free snapshot fields
    intact), matching the never-crash posture of the surrounding
    license endpoints.
    """
    raw_feature = _shared.request.args.get("feature", "") or ""
    try:
        requested_feature = str(raw_feature).strip().lower()
    except Exception:
        requested_feature = ""
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._license_features_at_snapshot()
    except Exception as exc:
        _shared.logger.warning(
            "api_license_has_feature_at_batch: snapshot error: %s", exc
        )
        snap = {
            "features": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        rows = _lic.has_feature_at_batch(requested_feature, tokens)
    except Exception as exc:
        _shared.logger.warning(
            "api_license_has_feature_at_batch: derive error: %s", exc
        )
        rows = []
    return _shared.jsonify(
        {
            "kind": "has_feature_at",
            "count": len(rows),
            "requested_feature": requested_feature,
            "rows": rows,
            "features": snap["features"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/license/subject-at-batch")
def api_license_subject_at_batch():
    """``GET /api/license/subject-at-batch?epochs=<int>,<int>,...`` --
    per-value batch sibling of ``/api/license/subject-at``.

    Where the singular endpoint folds ONE perspective epoch to ONE
    ``subject`` answer, this preserves per-value rows so a scheduled-
    audit tile that wants to plot the ``sub`` claim across a sequence of
    dates ("who was this node licensed to on each of these audit
    dates?") renders off ONE round-trip instead of N calls to
    ``/api/license/subject-at``. Wraps
    :func:`clawmetry.license.license_subject_at_batch`. Same row-shape
    axis as ``/api/license/tier-at-batch`` /
    ``/api/license/state-at-batch`` / ``/api/license/features-at-batch``
    so a caller assembling an audit timeline can zip the responses
    index-for-index by epoch column.

    ``epochs=`` is required. Missing / blank / only-commas -> ``400
    missing epochs``. Comma-separated tokens are normalised the way the
    underlying batch helper normalises them: whitespace-stripped, then
    handed to :func:`clawmetry.license.license_subject_at_batch`, which
    dedupes by parsed int key preserving first-seen order and collapses
    non-int / ``bool`` / ``None`` tokens to a row with ``subject=null``
    (never-mis-gate posture matching the scalar endpoint). Never 5xxs:
    a resolver failure returns the empty-rows envelope with the
    current-time snapshot fields intact.

    Response shape (always HTTP 200)::

        {
          "kind":  "license_subject_at",
          "count": <int>,               # len(rows)
          "rows":  [
            {"epoch": <int|"<raw>">, "subject": <str|null>},
            ...
          ],
          "subject":     <str|null>,    # current-time subject
          "expires_at":  <int|null>,    # on-disk exp for comparison
          "has_license": <bool>,
          "valid":       <bool>         # signature-valid AND not expired NOW
        }

    Per-row parity with ``/api/license/subject-at?epoch=<n>`` is pinned
    in the test suite so the batch cannot silently drift from the scalar
    endpoint. Shares :func:`_license_subject_at_snapshot` with the
    scalar endpoint so the current-time reference fields (``subject`` /
    ``expires_at`` / ``has_license`` / ``valid``) cannot disagree
    between the two for the same install.
    """
    tokens, err = _shared._parse_license_epochs_csv("epochs")
    if err == "missing":
        return _shared.jsonify({"error": "missing epochs"}), 400
    try:
        snap = _shared._license_subject_at_snapshot()
    except Exception as exc:
        _shared.logger.warning(
            "api_license_subject_at_batch: snapshot error: %s", exc
        )
        snap = {
            "subject": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    try:
        from clawmetry import license as _lic

        rows = _lic.license_subject_at_batch(tokens)
    except Exception as exc:
        _shared.logger.warning(
            "api_license_subject_at_batch: derive error: %s", exc
        )
        rows = []
    return _shared.jsonify(
        {
            "kind": "license_subject_at",
            "count": len(rows),
            "rows": rows,
            "subject": snap["subject"],
            "expires_at": snap["expires_at"],
            "has_license": snap["has_license"],
            "valid": snap["valid"],
        }
    )

@_shared.bp_entitlement.route("/api/paywall/event", methods=["POST"])
def api_paywall_event():
    body: dict = {}
    try:
        body = _shared.request.get_json(silent=True) or {}
        event = str(body.get("event", ""))[:64]
        harness = str(body.get("harness", ""))[:64]
        source = str(body.get("source", ""))[:64]
        feature = str(body.get("feature", ""))[:128]
        _shared.logger.info(
            "paywall: event=%s harness=%s feature=%s source=%s",
            event, harness, feature, source,
        )
    except Exception as exc:
        _shared.logger.debug("api_paywall_event: ignored error: %s", exc)
    # Best-effort rolling store for `/api/paywall/events/summary` +
    # `/api/paywall/events/recent`. Never raises; the beacon stays 204 even
    # if the store import fails on a broken install.
    try:
        from clawmetry import _paywall_events as _pe

        _pe.record_event(body)
    except Exception as exc:
        _shared.logger.debug("api_paywall_event: store swallowed error: %s", exc)
    _shared._ping_paywall_lifecycle(body)
    return "", 204

@_shared.bp_entitlement.route("/api/paywall/events/summary")
def api_paywall_events_summary():
    """``GET /api/paywall/events/summary`` -- rolling in-process aggregate
    of client-side ``POST /api/paywall/event`` beacons.

    Optional filter query params narrow the aggregation to rows whose
    corresponding field matches the supplied value exactly (case-
    sensitive, ``AND``-combined). Same names + semantics as
    ``/api/paywall/events/recent`` so a dashboard tile can bind one
    filter set to both endpoints without translation::

      ?event=<paywall_view|paywall_cta_click|...>
      ?feature=<feature-key>
      ?harness=<harness-key>
      ?source=<source-key>
      ?plan_chosen=<plan-code>

    Optional time-window params further restrict to rows whose ``ts``
    falls in the half-open ``[since, until)`` epoch-seconds interval::

      ?since=<float-epoch-seconds>
      ?until=<float-epoch-seconds>

    Either bound may be omitted or blank (= "unbounded on that side").
    A non-numeric, NaN, or negative bound collapses to "not supplied"
    so an operator typo cannot silently drop every row.

    Body shape::

        {
          "total": <int>,        # all-time recorded events (survives eviction)
          "in_window": <int>,    # currently in the ring, unfiltered
          "dropped": <int>,      # events evicted by ring rotation
          "capacity": <int>,     # ring size (CLAWMETRY_PAYWALL_EVENT_CAPACITY)
          "first_ts": <float|null>,  # epoch seconds of first-ever event
          "last_ts":  <float|null>,  # epoch seconds of most-recent event
          "by_event": {"<name>": <int>, ...},        # in-window, post-filter
          "by_feature": {"<key>":  <int>, ...},
          "by_harness": {"<key>":  <int>, ...},
          "by_source":  {"<key>":  <int>, ...},
          "by_plan_chosen": {"<plan>": <int>, ...},
          "filters": {"<key>": "<value>", ...},      # echo of applied categorical filters
          "matched": <int>,                          # rows the by_* aggregate covers
          "time_window": {"since": <float|null>, "until": <float|null>}
                                                     # echo of resolved bounds
        }

    Process-lifetime counters (``total``, ``dropped``, ``first_ts``,
    ``last_ts``, ``capacity``) and ``in_window`` are NEVER filtered --
    they describe the ring itself, not the subset the caller cares about,
    so a filtered dashboard tile can still see churn / evictions in
    context. The ``by_*`` breakdowns and ``matched`` count reflect the
    filtered subset (categorical + time-window). On a fully-unfiltered
    request ``matched`` byte-equals ``in_window``.

    Ships in GRACE -- no entitlement gate, no capacity accounting. Grace-
    mode read of a grace-mode write.

    Never 5xxs -- on any failure the endpoint returns the neutral empty
    snapshot so a paywall-dashboard tile keeps rendering.
    """
    try:
        from clawmetry import _paywall_events as _pe

        filter_kwargs = {
            key: _shared.request.args.get(key, "") or None
            for key in ("event", "feature", "harness", "source", "plan_chosen")
        }
        # ``since`` / ``until`` share the same "blank means not supplied"
        # posture as the categorical filters; the store layer does the
        # numeric coercion + NaN / negative guarding.
        for key in ("since", "until"):
            filter_kwargs[key] = _shared.request.args.get(key, "") or None
        return _shared.jsonify(_pe.summary(**filter_kwargs))
    except Exception as exc:
        _shared.logger.warning("api_paywall_events_summary: error: %s", exc)
        return _shared.jsonify(
            {
                "total": 0,
                "in_window": 0,
                "dropped": 0,
                "capacity": 0,
                "first_ts": None,
                "last_ts": None,
                "by_event": {},
                "by_feature": {},
                "by_harness": {},
                "by_source": {},
                "by_plan_chosen": {},
                "filters": {},
                "matched": 0,
                "time_window": {"since": None, "until": None},
            }
        )

@_shared.bp_entitlement.route("/api/paywall/events/recent")
def api_paywall_events_recent():
    """``GET /api/paywall/events/recent?limit=N`` -- most-recent N paywall
    beacons, newest first.

    ``limit`` defaults to 50 and is clamped into ``[0, 200]`` -- a caller
    passing a bad, negative, or oversized value falls back to the default so
    the response size stays bounded.

    Optional filter query params narrow the returned rows to those whose
    corresponding field matches the supplied value exactly (case-
    sensitive, ``AND``-combined across dimensions)::

      ?event=<paywall_view|paywall_cta_click|...>
      ?feature=<feature-key>
      ?harness=<harness-key>
      ?source=<source-key>
      ?plan_chosen=<plan-code>

    A blank or missing filter is "not supplied" and does not restrict on
    that dimension -- there is deliberately no way to query for rows with
    an empty field via this API. Filter mismatches never fail the request:
    they simply return an empty ``events`` list and ``matched=0``.

    Optional time-window params restrict to rows whose ``ts`` falls in the
    half-open ``[since, until)`` epoch-seconds interval::

      ?since=<float-epoch-seconds>
      ?until=<float-epoch-seconds>

    Either bound may be omitted or blank. Bad bounds (non-numeric, NaN,
    negative) collapse to "not supplied".

    Body shape::

        {
          "events": [
            {"event": "...", "feature": "...", "harness": "...",
             "source": "...", "plan_chosen": "...", "ts": <float>},
            ...
          ],
          "count": <int>,          # events actually returned (post-filter, post-limit)
          "matched": <int>,        # rows matching the filters + window, pre-limit (>= count)
          "limit": <int>,          # the resolved (post-clamp) limit
          "in_window": <int>,      # size of the underlying ring right now
          "filters": {"<key>": "<value>", ...},  # echo of applied categorical filters
          "time_window": {"since": <float|null>, "until": <float|null>}
                                                 # echo of resolved bounds
        }

    ``matched`` lets a UI render "showing N of M matches" without a second
    round-trip. On a fully-unfiltered request ``matched`` byte-equals
    ``in_window``.

    Ships in GRACE. Never 5xxs -- on any failure returns an empty envelope.
    """
    raw_limit = _shared.request.args.get("limit", "")
    try:
        from clawmetry import _paywall_events as _pe

        try:
            limit_val = int(raw_limit) if raw_limit != "" else _pe.RECENT_DEFAULT_LIMIT
        except (TypeError, ValueError):
            limit_val = _pe.RECENT_DEFAULT_LIMIT
        if limit_val < 0:
            limit_val = _pe.RECENT_DEFAULT_LIMIT
        if limit_val > _pe.RECENT_MAX_LIMIT:
            limit_val = _pe.RECENT_MAX_LIMIT
        filter_kwargs = {
            key: _shared.request.args.get(key, "") or None
            for key in ("event", "feature", "harness", "source", "plan_chosen")
        }
        window_kwargs = {
            key: _shared.request.args.get(key, "") or None
            for key in ("since", "until")
        }
        # `_pe.recent` / `count_matching` treat empty / whitespace strings as
        # "not supplied" so the query-string echo below is the canonical
        # applied-filter set. Time bounds go through their own numeric
        # coercion in the store, so we ask the store what it actually
        # resolved to (via `summary(**window_kwargs)["time_window"]`)
        # rather than echoing the raw string.
        events = _pe.recent(limit_val, **filter_kwargs, **window_kwargs)
        matched = _pe.count_matching(**filter_kwargs, **window_kwargs)
        summary = _pe.summary(**window_kwargs)
        applied_filters = {
            key: value.strip()
            for key, value in filter_kwargs.items()
            if isinstance(value, str) and value.strip()
        }
        return _shared.jsonify(
            {
                "events": events,
                "count": len(events),
                "matched": matched,
                "limit": limit_val,
                "in_window": summary.get("in_window", 0),
                "filters": applied_filters,
                "time_window": summary.get(
                    "time_window", {"since": None, "until": None},
                ),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_paywall_events_recent: error: %s", exc)
        return _shared.jsonify(
            {
                "events": [],
                "count": 0,
                "matched": 0,
                "limit": 0,
                "in_window": 0,
                "filters": {},
                "time_window": {"since": None, "until": None},
            }
        )

@_shared.bp_entitlement.route("/api/paywall/events/last")
def api_paywall_events_last():
    """``GET /api/paywall/events/last`` -- the single most-recent paywall
    beacon matching the supplied filters, or ``null`` if none.

    Scalar sibling of ``/api/paywall/events/recent`` for the common case
    where a dashboard tile only needs "the most recent one" (e.g. "last
    CTA click for feature X was at 12:03:41"). Avoids the one-element-
    list unwrap and skips paying the ``dict(e)`` copy cost on every
    ring entry.

    Same categorical filter query params + semantics as
    ``/api/paywall/events/recent`` -- ``?event=`` / ``?feature=`` /
    ``?harness=`` / ``?source=`` / ``?plan_chosen=``, case-sensitive
    exact match, ``AND`` combined, blank / missing = "not supplied".

    Optional time-window params restrict to rows whose ``ts`` falls in
    the half-open ``[since, until)`` epoch-seconds interval::

      ?since=<float-epoch-seconds>
      ?until=<float-epoch-seconds>

    Either bound may be omitted or blank. Bad bounds (non-numeric, NaN,
    negative) collapse to "not supplied" -- matching the semantics of
    ``/api/paywall/events/recent`` so a caller can rebind the same
    window pair without translation.

    Body shape::

        {
          "event": {"event": "...", "feature": "...", "harness": "...",
                    "source": "...", "plan_chosen": "...", "ts": <float>} | null,
          "matched": <int>,  # rows matching the filters + window (0 iff event is null)
          "in_window": <int>,  # size of the underlying ring right now
          "filters": {"<key>": "<value>", ...},
          "time_window": {"since": <float|null>, "until": <float|null>}
                                                 # echo of resolved bounds
        }

    ``matched`` uses the same helper as ``/api/paywall/events/recent`` so
    a UI can render "last of M matches" without a second round-trip.
    ``time_window`` is always present so the top-level key set stays
    stable regardless of whether time bounds were supplied.

    Ships in GRACE. Never 5xxs -- on any failure returns the neutral
    ``event=null`` envelope (still carrying ``time_window``).
    """
    try:
        from clawmetry import _paywall_events as _pe

        filter_kwargs = {
            key: _shared.request.args.get(key, "") or None
            for key in ("event", "feature", "harness", "source", "plan_chosen")
        }
        window_kwargs = {
            key: _shared.request.args.get(key, "") or None
            for key in ("since", "until")
        }
        event_row = _pe.last_matching(**filter_kwargs, **window_kwargs)
        matched = _pe.count_matching(**filter_kwargs, **window_kwargs)
        summary = _pe.summary(**window_kwargs)
        applied_filters = {
            key: value.strip()
            for key, value in filter_kwargs.items()
            if isinstance(value, str) and value.strip()
        }
        return _shared.jsonify(
            {
                "event": event_row,
                "matched": matched,
                "in_window": summary.get("in_window", 0),
                "filters": applied_filters,
                "time_window": summary.get(
                    "time_window", {"since": None, "until": None},
                ),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_paywall_events_last: error: %s", exc)
        return _shared.jsonify(
            {
                "event": None,
                "matched": 0,
                "in_window": 0,
                "filters": {},
                "time_window": {"since": None, "until": None},
            }
        )

@_shared.bp_entitlement.route("/api/paywall/events/first")
def api_paywall_events_first():
    """``GET /api/paywall/events/first`` -- the single oldest paywall
    beacon matching the supplied filters, or ``null`` if none.

    Twin of ``/api/paywall/events/last`` for the other end of the ring:
    same filter contract, same envelope shape, same never-5xx posture.
    Anchored to what the ring currently holds -- because the ring evicts
    oldest-first, "first" means "oldest still resident", not "all-time
    first". Matches the rest of this module's semantics (aggregations
    reflect what's live, not what's been evicted).

    A dashboard tile rendering "first paywall CTA click of this session"
    binds this rather than paging the full ring via
    ``/api/paywall/events/recent`` and inspecting the tail.

    Optional time-window params (``?since=`` / ``?until=``) restrict to
    rows whose ``ts`` falls in the half-open ``[since, until)`` epoch-
    seconds interval. With a window supplied, "first" means "oldest
    resident row in the window" -- rows evicted from the ring cannot be
    re-surfaced by a wider window. Same coercion contract as
    ``/api/paywall/events/recent``.

    Body shape is identical to ``/api/paywall/events/last`` and always
    carries ``time_window``. Ships in GRACE. Never 5xxs -- on any
    failure returns the neutral ``event=null`` envelope.
    """
    try:
        from clawmetry import _paywall_events as _pe

        filter_kwargs = {
            key: _shared.request.args.get(key, "") or None
            for key in ("event", "feature", "harness", "source", "plan_chosen")
        }
        window_kwargs = {
            key: _shared.request.args.get(key, "") or None
            for key in ("since", "until")
        }
        event_row = _pe.first_matching(**filter_kwargs, **window_kwargs)
        matched = _pe.count_matching(**filter_kwargs, **window_kwargs)
        summary = _pe.summary(**window_kwargs)
        applied_filters = {
            key: value.strip()
            for key, value in filter_kwargs.items()
            if isinstance(value, str) and value.strip()
        }
        return _shared.jsonify(
            {
                "event": event_row,
                "matched": matched,
                "in_window": summary.get("in_window", 0),
                "filters": applied_filters,
                "time_window": summary.get(
                    "time_window", {"since": None, "until": None},
                ),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_paywall_events_first: error: %s", exc)
        return _shared.jsonify(
            {
                "event": None,
                "matched": 0,
                "in_window": 0,
                "filters": {},
                "time_window": {"since": None, "until": None},
            }
        )

@_shared.bp_entitlement.route("/api/paywall/events/count")
def api_paywall_events_count():
    """``GET /api/paywall/events/count`` -- scalar count of ring rows
    matching the supplied filters + time-window.

    Scalar sibling of ``/api/paywall/events/{summary,recent,first,last}``
    for the common case where a dashboard tile only needs the number
    (e.g. "42 CTA clicks in the last hour") and does not want to pay
    the per-row ``dict(e)`` copy cost of ``/recent`` or the five
    ``by_*`` aggregations of ``/summary``. A pricing-page widget
    binding "how many paywall_view beacons in this window?" to a
    single number reaches for this instead of unwrapping
    ``summary()['matched']``.

    Same categorical filter query params + semantics as
    ``/api/paywall/events/recent`` -- ``?event=`` / ``?feature=`` /
    ``?harness=`` / ``?source=`` / ``?plan_chosen=``, case-sensitive
    exact match, ``AND`` combined, blank / missing = "not supplied".

    Same time-window params as ``/api/paywall/events/{summary,recent}``::

      ?since=<float-epoch-seconds>
      ?until=<float-epoch-seconds>

    Half-open ``[since, until)``; either bound may be omitted or blank.
    Bad bounds (non-numeric, NaN, negative) collapse to "not supplied"
    so an operator typo cannot silently drop every row.

    Body shape::

        {
          "count": <int>,      # rows matching filters + window
          "in_window": <int>,  # size of the underlying ring right now
          "filters": {"<key>": "<value>", ...},  # echo of applied categorical filters
          "time_window": {"since": <float|null>, "until": <float|null>}
                                                 # echo of resolved bounds
        }

    ``count`` byte-equals ``/api/paywall/events/recent``'s ``matched``
    for the same filter + window inputs (both call
    :func:`_paywall_events.count_matching`), and byte-equals
    ``/api/paywall/events/summary``'s ``matched`` for the same inputs.
    On a fully-unfiltered request ``count`` byte-equals ``in_window``.

    Ships in GRACE. Never 5xxs -- on any failure returns the neutral
    ``count=0`` envelope so a paywall-dashboard tile keeps rendering.
    """
    try:
        from clawmetry import _paywall_events as _pe

        filter_kwargs = {
            key: _shared.request.args.get(key, "") or None
            for key in ("event", "feature", "harness", "source", "plan_chosen")
        }
        window_kwargs = {
            key: _shared.request.args.get(key, "") or None
            for key in ("since", "until")
        }
        # `count_matching` and `summary` treat empty / whitespace strings
        # as "not supplied" so the query-string echo below is the
        # canonical applied-filter set. Time bounds go through their
        # own numeric coercion in the store, so we ask the store what
        # it actually resolved to (via `summary(**window_kwargs)`)
        # rather than echoing the raw string.
        count = _pe.count_matching(**filter_kwargs, **window_kwargs)
        summary = _pe.summary(**window_kwargs)
        applied_filters = {
            key: value.strip()
            for key, value in filter_kwargs.items()
            if isinstance(value, str) and value.strip()
        }
        return _shared.jsonify(
            {
                "count": count,
                "in_window": summary.get("in_window", 0),
                "filters": applied_filters,
                "time_window": summary.get(
                    "time_window", {"since": None, "until": None},
                ),
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_paywall_events_count: error: %s", exc)
        return _shared.jsonify(
            {
                "count": 0,
                "in_window": 0,
                "filters": {},
                "time_window": {"since": None, "until": None},
            }
        )

@_shared.bp_entitlement.route("/api/paywall/events/distinct")
def api_paywall_events_distinct():
    """``GET /api/paywall/events/distinct`` -- sorted distinct values per
    categorical dimension currently in the ring.

    Populates filter-dropdown options for the paywall-events dashboard:
    a UI wanting to render "Filter by feature: [ dropdown ]" needs to
    know which features have actually fired at least one beacon this
    session so the dropdown never lists dead options. This endpoint
    hands back exactly that list for each of the five categorical
    dimensions in one round-trip.

    Same categorical filter query params + semantics as the sibling
    paywall-events endpoints -- ``?event=`` / ``?feature=`` /
    ``?harness=`` / ``?source=`` / ``?plan_chosen=``, case-sensitive
    exact match, ``AND`` combined, blank / missing = "not supplied".
    Filters narrow the ring BEFORE the distinct set is computed, so a
    caller can drive a "further narrow by:" dropdown UX -- passing
    ``?event=paywall_cta_click`` returns only the features that
    actually co-occur with CTA clicks in the current ring.

    Same time-window params as ``/api/paywall/events/{summary,recent,count}``::

      ?since=<float-epoch-seconds>
      ?until=<float-epoch-seconds>

    Half-open ``[since, until)``; either bound may be omitted or blank.
    Bad bounds (non-numeric, NaN, negative) collapse to "not supplied"
    so an operator typo cannot silently drop every row.

    Body shape::

        {
          "distinct": {
            "event":       [<str>, ...],   # sorted ascending, non-empty only
            "feature":     [<str>, ...],
            "harness":     [<str>, ...],
            "source":      [<str>, ...],
            "plan_chosen": [<str>, ...],
          },
          "in_window": <int>,            # ring size right now, unfiltered
          "matched":   <int>,            # rows the distinct set covers (post-filter, post-window)
          "filters":   {"<key>": "<value>", ...},   # echo of applied categorical filters
          "time_window": {"since": <float|null>, "until": <float|null>}
                                                    # echo of resolved bounds
        }

    The per-dimension lists are byte-equal to the sorted keys of
    ``/api/paywall/events/summary``'s corresponding ``by_*`` dict for
    the same filter + window inputs -- pinned in the test suite so the
    two views cannot silently drift. On a fully-unfiltered request
    ``matched`` byte-equals ``in_window``.

    Ships in GRACE. Never 5xxs -- on any failure returns the neutral
    empty envelope so a paywall-dashboard dropdown keeps rendering
    (empty options are correct: the store has nothing to offer).
    """
    try:
        from clawmetry import _paywall_events as _pe

        filter_kwargs = {
            key: _shared.request.args.get(key, "") or None
            for key in _shared._PAYWALL_DISTINCT_DIMS
        }
        window_kwargs = {
            key: _shared.request.args.get(key, "") or None
            for key in ("since", "until")
        }
        # The store treats blank / whitespace strings as "not supplied"
        # and does its own numeric coercion on the time bounds, so the
        # response's ``filters`` / ``time_window`` echoes come from the
        # store's normalised view rather than the raw query string.
        return _shared.jsonify(_pe.distinct_values(**filter_kwargs, **window_kwargs))
    except Exception as exc:
        _shared.logger.warning("api_paywall_events_distinct: error: %s", exc)
        return _shared.jsonify(
            {
                "distinct": {k: [] for k in _shared._PAYWALL_DISTINCT_DIMS},
                "in_window": 0,
                "matched": 0,
                "filters": {},
                "time_window": {"since": None, "until": None},
            }
        )

@_shared.bp_entitlement.route("/api/license/activate", methods=["POST"])
def api_license_activate():
    """``POST /api/license/activate`` -- install a signed license key.

    Shape parity across all four branches (missing-key / healthy-success /
    healthy-failure / introspection-exception): every branch populates
    ``{ok, message, error}`` so a UI can bind to ``data.message`` without
    checking whether it's the missing-key branch (which used to only
    populate ``error``) or the exception branch (which used to only
    populate ``error``). ``error`` is a back-compat alias populated on
    the two failure branches -- pre-parity consumers reading
    ``data.error`` keep working unchanged.

    Still 4xx / 5xx on the failure branches -- this is a POST mutation
    and the client legitimately needs to know the write failed. The
    healthy-failure branch (bad/expired/duplicate-node key) stays 400;
    the introspection-exception branch (import failure, corrupt install)
    stays 500. Only the SHAPE of the failure body changes -- the status
    codes match what shipped before this PR.
    """
    try:
        body = _shared.request.get_json(silent=True) or {}
        key = str(body.get("key", "")).strip()
        if not key:
            return _shared.jsonify(_shared._activate_envelope(False, "key is required", error="key is required")), 400
        from clawmetry import license as _lic

        ok, msg = _lic.activate(key, actor=_shared._route_actor())
        status_code = 200 if ok else 400
        return _shared.jsonify(_shared._activate_envelope(ok, msg, error=None if ok else msg)), status_code
    except Exception as exc:
        _shared.logger.warning("api_license_activate: error: %s", exc)
        return _shared.jsonify(_shared._activate_envelope(False, str(exc), error=str(exc))), 500

@_shared.bp_entitlement.route("/api/license/verify", methods=["POST"])
def api_license_verify():
    """``POST /api/license/verify`` -- dry-run key inspection.

    Verifies ``key`` OFFLINE against the embedded Ed25519 trust anchor
    and returns what it would unlock, without writing anything to disk.
    Wrapper around :func:`clawmetry.license.inspect_key`.

    Shape parity across all three branches (valid / invalid signature /
    introspection failure): every branch carries the SAME field set as
    :func:`clawmetry.license.inspect_key`'s return so a UI can render the
    verify card through one code path. The invalid + error branches also
    populate ``pubkey_fingerprint_sha256`` when the fingerprint helper is
    reachable, so an operator pasting a bogus key still sees the trust
    anchor their install would have verified against.

    Never 5xxs: introspection failure degrades to the same shape as an
    invalid signature at HTTP 200, matching the never-crash posture of
    :func:`api_license_status`.
    """

    def _dry_run_envelope(status, extras=None):
        pubkey_fp = None
        try:
            from clawmetry import license as _lic

            pubkey_fp = _lic.pubkey_fingerprint()
        except Exception as exc:
            _shared.logger.debug("api_license_verify: pubkey fingerprint failed: %s", exc)
        payload = {
            "valid": False,
            "status": status,
            "tier": None,
            "nodes": None,
            "sub": None,
            "exp": None,
            "days_left": None,
            "pubkey_fingerprint_sha256": pubkey_fp,
            "permissions_safe": None,
            "file_mode": None,
            "dry_run": True,
        }
        if extras:
            payload.update(extras)
        return payload

    try:
        body = _shared.request.get_json(silent=True) or {}
        key = str(body.get("key", "")).strip()
        if not key:
            return _shared.jsonify({"ok": False, "error": "key is required"}), 400
        from clawmetry import license as _lic

        info = _lic.inspect_key(key)
        if info is None:
            return _shared.jsonify(_dry_run_envelope("invalid"))
        info = dict(info)
        info["dry_run"] = True
        return _shared.jsonify(info)
    except Exception as exc:
        _shared.logger.warning("api_license_verify: error: %s", exc)
        return _shared.jsonify(_dry_run_envelope("invalid", {"error": str(exc)}))

@_shared.bp_entitlement.route("/api/license/deactivate", methods=["POST"])
def api_license_deactivate():
    """``POST /api/license/deactivate`` -- remove the on-disk license file.

    Shape parity across all four branches (healthy-noop / healthy-removed /
    remove-failed / introspection-exception): every branch populates
    ``{ok, removed, message, error}``. ``removed`` no longer disappears
    on the exception branch, so a UI can bind to ``data.removed`` without
    a guard. ``error`` is a back-compat alias populated on the two
    failure branches -- the pre-parity remove-failed shape already
    carried ``error="remove_failed"`` and that string is preserved.

    Still 5xx on the two failure branches -- deactivation is a mutation
    and the client legitimately needs to know disk removal or module
    import failed. Only the SHAPE of the failure body changes.
    """
    try:
        from clawmetry import license as _lic

        ok, removed = _lic.deactivate(actor=_shared._route_actor())
        if not ok:
            return _shared.jsonify(_shared._deactivate_envelope(
                False, False, message="remove_failed", error="remove_failed",
            )), 500
        message = "license file removed" if removed else "no license file to remove"
        return _shared.jsonify(_shared._deactivate_envelope(True, removed, message=message)), 200
    except Exception as exc:
        _shared.logger.warning("api_license_deactivate: error: %s", exc)
        return _shared.jsonify(_shared._deactivate_envelope(
            False, False, message=str(exc), error=str(exc),
        )), 500

@_shared.bp_entitlement.route("/api/entitlement/next-tier-unlocks-at")
def api_entitlement_next_tier_unlocks_at():
    """``GET /api/entitlement/next-tier-unlocks-at?tier=<source>`` --
    scalar what-if sibling of ``/api/entitlement/next-tier-unlocks``:
    marginal unlocks row at the rung above the caller-supplied
    ``tier``, in :func:`clawmetry.entitlements.tier_unlocks` shape.

    Lets a pricing page render the "what's new at the next rung above
    X" upgrade-CTA cell for any hypothetical ``X`` without first asking
    the resolver and without monkey-patching the entitlement context --
    the scalar what-if the live ``/next-tier-unlocks`` endpoint surfaces
    against the resolved entitlement, parameterised over the source.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<next-above tier id>" | null,
          "target_label":   "<next-above label>" | null,
          "target_rank":    <next-above rank> | null,
          "row":            {<tier_unlocks row>} | null,
        }

    The inner ``row`` matches the live ``/next-tier-unlocks`` ``locks``-
    style row shape (``tier``, ``tier_label``, ``tier_rank``,
    ``previous_tier``, ``previous_tier_label``, ``previous_tier_rank``,
    ``features``, ``runtimes``). The row IS the tier-property row of
    the rung above (its ``previous_tier`` is that rung's natural next-
    lower purchasable, NOT the caller-supplied ``tier``) -- the same
    posture the live endpoint surfaces. Callers who want the source-
    anchored ``previous_tier`` should use ``/tier-unlocks-at`` with the
    explicit ``(tier, target)`` pair.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``), matching the other ``_at`` family endpoints. ``target``
    / ``row`` collapse to ``null`` at the ceiling (no rung strictly
    above the source) -- the surface stays 200 with a populated
    envelope so callers can render "you're at the top" copy without
    a status-code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the CTA surface stays mute.
    """
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
        target = _ent._next_purchasable_tier_after(tier_in)
        row = _ent.next_tier_unlocks_at(tier_in)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_next_tier_unlocks_at: error: %s", exc)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-locks-at")
def api_entitlement_next_tier_locks_at():
    """``GET /api/entitlement/next-tier-locks-at?tier=<source>`` --
    scalar what-if sibling of ``/api/entitlement/next-tier-locks``:
    marginal locks row at the rung above the caller-supplied ``tier``,
    in :func:`clawmetry.entitlements.tier_locks` shape.

    Marginal-loss mirror of ``/next-tier-unlocks-at`` and pairs with
    the live ``/next-tier-locks`` (source pinned to the resolver) the
    same way ``/tier-locks-at`` pairs with ``/tier-locks``. Lets a
    pricing page render the "what does the rung above X first lose vs
    the rung above IT" detail cell for any hypothetical ``X`` without
    asking the resolver.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<next-above tier id>" | null,
          "target_label":   "<next-above label>" | null,
          "target_rank":    <next-above rank> | null,
          "row":            {<tier_locks row>} | null,
        }

    The inner ``row`` matches the live ``/next-tier-locks`` ``locks``
    row shape (``tier``, ``tier_label``, ``tier_rank``, ``next_tier``,
    ``next_tier_label``, ``next_tier_rank``, ``lost_features``,
    ``lost_runtimes``). At the rung where the next-above IS the ladder
    ceiling (enterprise), the row's ``next_tier`` is ``null`` and the
    ``lost_*`` lists collapse to ``[]`` -- :func:`tier_locks` shape
    for "this rung has no rung above to step down from", not ``null``
    on the envelope.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``target`` / ``row`` collapse to ``null`` at the
    source-side ceiling (enterprise as source -- no rung strictly
    above) -- the surface stays 200 with a populated envelope.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so
      a caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the CTA surface stays mute.
    """
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
        target = _ent._next_purchasable_tier_after(tier_in)
        row = _ent.next_tier_locks_at(tier_in)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_next_tier_locks_at: error: %s", exc)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-unlocks-at")
def api_entitlement_previous_tier_unlocks_at():
    """``GET /api/entitlement/previous-tier-unlocks-at?tier=<source>`` --
    scalar what-if sibling of ``/api/entitlement/previous-tier-unlocks``:
    marginal unlocks row at the rung below the caller-supplied
    ``tier``, in :func:`clawmetry.entitlements.tier_unlocks` shape.

    Source-anchored mirror of ``/api/entitlement/next-tier-unlocks-at``
    and downgrade-side counterpart of the live
    ``/api/entitlement/previous-tier-unlocks`` endpoint. Lets a pricing
    page render the "what would still be granted at the rung below X"
    downgrade-CTA cell for any hypothetical ``X`` without first asking
    the resolver and without monkey-patching the entitlement context.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<rung-below tier id>" | null,
          "target_label":   "<rung-below label>" | null,
          "target_rank":    <rung-below rank> | null,
          "row":            {<tier_unlocks row>} | null,
        }

    The inner ``row`` matches the live ``/previous-tier-unlocks`` row
    shape (``tier``, ``tier_label``, ``tier_rank``, ``previous_tier``,
    ``previous_tier_label``, ``previous_tier_rank``, ``features``,
    ``runtimes``). The row IS the tier-property row of the rung below
    (its ``previous_tier`` is that rung's natural next-lower
    purchasable, NOT the caller-supplied ``tier``). Callers who want
    the source-anchored ``previous_tier`` should use ``/tier-unlocks-at``
    with the explicit ``(tier, target)`` pair.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``), matching the other ``_at`` family endpoints. ``target``
    / ``row`` collapse to ``null`` at the floor (no rung strictly below
    the source -- oss / cloud_free) -- the surface stays 200 with a
    populated envelope so callers can render "you're at the bottom"
    copy without a status-code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the CTA surface stays mute.
    """
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
        target = _ent._previous_purchasable_tier_before(tier_in)
        row = _ent.previous_tier_unlocks_at(tier_in)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_previous_tier_unlocks_at: error: %s", exc)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-locks-at")
def api_entitlement_previous_tier_locks_at():
    """``GET /api/entitlement/previous-tier-locks-at?tier=<source>`` --
    scalar what-if sibling of ``/api/entitlement/previous-tier-locks``:
    marginal locks row at the rung below the caller-supplied ``tier``,
    in :func:`clawmetry.entitlements.tier_locks` shape.

    Source-anchored mirror of ``/api/entitlement/next-tier-locks-at``.
    Marginal-loss companion to ``/previous-tier-unlocks-at`` on a
    hypothetical pricing matrix cell -- where the unlocks form shows
    "what the rung below still grants" the locks form shows "what the
    rung below first loses vs the rung above IT".

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<rung-below tier id>" | null,
          "target_label":   "<rung-below label>" | null,
          "target_rank":    <rung-below rank> | null,
          "row":            {<tier_locks row>} | null,
        }

    The inner ``row`` matches the live ``/previous-tier-locks`` row
    shape (``tier``, ``tier_label``, ``tier_rank``, ``next_tier``,
    ``next_tier_label``, ``next_tier_rank``, ``lost_features``,
    ``lost_runtimes``). The row's ``next_tier`` is the rung-below's
    natural next-higher purchasable, NOT the caller-supplied source.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``target`` / ``row`` collapse to ``null`` at the floor
    (no rung strictly below the source -- oss / cloud_free) -- the
    surface stays 200 with a populated envelope.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the CTA surface stays mute.
    """
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
        target = _ent._previous_purchasable_tier_before(tier_in)
        row = _ent.previous_tier_locks_at(tier_in)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_previous_tier_locks_at: error: %s", exc)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-unlocks-at-batch")
def api_entitlement_next_tier_unlocks_at_batch():
    """``GET /api/entitlement/next-tier-unlocks-at-batch`` -- batch
    sibling of ``/api/entitlement/next-tier-unlocks-at``: one
    ``next-tier-unlocks-at`` envelope per purchasable source tier, in
    one round-trip.

    Composes the scalar what-if (``/next-tier-unlocks-at``) and the
    live batch (``/tier-unlocks-batch``) -- same envelope shape per row
    as the scalar what-if, same source axis as the live batch. Lets a
    pricing-comparison matrix UI render the "what's new at the rung
    above each rung" upgrade-CTA column off **one** call instead of N
    calls to ``/next-tier-unlocks-at``.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-unlocks-batch``
    endpoint, so the envelopes fold into the same pricing-page table
    byte-for-byte on the source axis.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches ``/api/entitlement/next-tier-unlocks-at?tier=<source>``
    for that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). At the
    source-side ceiling (``enterprise`` as source -- no rung strictly
    above) the envelope carries ``target=null`` and ``row=null`` rather
    than being dropped, so the matrix keeps a row for every purchasable
    rung.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.next_tier_unlocks_at_batch() or []
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_next_tier_unlocks_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-locks-at-batch")
def api_entitlement_next_tier_locks_at_batch():
    """``GET /api/entitlement/next-tier-locks-at-batch`` -- batch
    sibling of ``/api/entitlement/next-tier-locks-at``: one
    ``next-tier-locks-at`` envelope per purchasable source tier, in one
    round-trip.

    Marginal-loss mirror of ``/next-tier-unlocks-at-batch`` and pairs
    with ``/tier-locks-batch`` the same way
    ``/next-tier-unlocks-at-batch`` pairs with ``/tier-unlocks-batch``.
    Pair the two ``_at_batch`` endpoints to render the upgrade-CTA +
    downgrade-warning columns of an "above each rung" pricing matrix
    in two round-trips.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-locks-batch`` endpoint.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches ``/api/entitlement/next-tier-locks-at?tier=<source>``
    for that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). At the
    source-side ceiling (``enterprise`` as source) the envelope
    carries ``target=null`` and ``row=null``. At a source rung whose
    next-above IS the ladder ceiling (``cloud_pro`` / ``pro`` ->
    ``enterprise``) the row carries ``next_tier=null`` and empty
    ``lost_*`` lists -- :func:`tier_locks` shape for "the target has no
    rung above to step down from", NOT ``null`` on the envelope.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.next_tier_locks_at_batch() or []
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_next_tier_locks_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-unlocks-at-batch")
def api_entitlement_previous_tier_unlocks_at_batch():
    """``GET /api/entitlement/previous-tier-unlocks-at-batch`` -- batch
    sibling of ``/api/entitlement/previous-tier-unlocks-at``: one
    ``previous-tier-unlocks-at`` envelope per purchasable source tier,
    in one round-trip.

    Source-anchored downgrade-side mirror of
    ``/api/entitlement/next-tier-unlocks-at-batch``. Composes the
    scalar what-if (``/previous-tier-unlocks-at``) and the live batch
    (``/tier-unlocks-batch``) -- same envelope shape per row as the
    scalar what-if, same source axis as the live batch. Lets a
    pricing-comparison matrix UI render the "what would still be
    granted at the rung below each rung" downgrade-CTA column off
    **one** call instead of N calls to ``/previous-tier-unlocks-at``.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-unlocks-batch``
    endpoint, so the envelopes fold into the same pricing-page table
    byte-for-byte on the source axis.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches ``/api/entitlement/previous-tier-unlocks-at?tier=<source>``
    for that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). At the
    source-side floor (``oss`` / ``cloud_free`` as source -- no rung
    strictly below) the envelope carries ``target=null`` and
    ``row=null`` rather than being dropped, so the matrix keeps a row
    for every purchasable rung.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.previous_tier_unlocks_at_batch() or []
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_previous_tier_unlocks_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-locks-at-batch")
def api_entitlement_previous_tier_locks_at_batch():
    """``GET /api/entitlement/previous-tier-locks-at-batch`` -- batch
    sibling of ``/api/entitlement/previous-tier-locks-at``: one
    ``previous-tier-locks-at`` envelope per purchasable source tier,
    in one round-trip.

    Marginal-loss mirror of ``/previous-tier-unlocks-at-batch`` and
    pairs with ``/tier-locks-batch`` the same way
    ``/previous-tier-unlocks-at-batch`` pairs with
    ``/tier-unlocks-batch``. Pair the two ``previous-*-at-batch``
    endpoints to render the downgrade-CTA + downgrade-warning columns
    of a "below each rung" pricing matrix in two round-trips.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-locks-batch`` endpoint.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches ``/api/entitlement/previous-tier-locks-at?tier=<source>``
    for that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). At the
    source-side floor (``oss`` / ``cloud_free`` as source) the
    envelope carries ``target=null`` and ``row=null``. At a source
    rung whose next-below IS the ladder floor (``cloud_starter`` ->
    ``oss``) the row carries populated ``lost_features`` /
    ``lost_runtimes`` lists -- :func:`tier_locks` shape against the
    floor's next-above rung -- NOT ``null`` on the envelope.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.previous_tier_locks_at_batch() or []
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_previous_tier_locks_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-diff-at")
def api_entitlement_next_tier_diff_at():
    """``GET /api/entitlement/next-tier-diff-at?tier=<source>`` --
    scalar what-if sibling of the live ``Entitlement.next_tier_diff``:
    full :func:`clawmetry.entitlements.tier_diff` row from the caller-
    supplied ``tier`` to the rung above it.

    Lets a pricing-comparison or upgrade-CTA card render the full
    upgrade payload (``added_*``, ``lost_*``, ``capacity_changes``,
    ``direction``) for any hypothetical source rung off **one** round-
    trip, without first hitting ``/api/entitlement`` and without
    monkey-patching the entitlement context. Pairs with
    ``/api/entitlement/next-tier-unlocks-at`` and
    ``/api/entitlement/next-tier-locks-at`` (the marginal-grant /
    marginal-loss views of the same step) on a hypothetical pricing
    matrix cell.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<next-above tier id>" | null,
          "target_label":   "<next-above label>" | null,
          "target_rank":    <next-above rank> | null,
          "row":            {<tier_diff row>} | null,
        }

    Unlike ``/api/entitlement/next-tier-unlocks-at`` -- which surfaces
    the target's own ``tier_unlocks`` row (target-anchored,
    ``previous_tier`` is the target's natural next-lower purchasable,
    NOT the caller-supplied source) -- this endpoint pins **both**
    endpoints, so ``row.from`` is byte-equal to ``tier``. That mirrors
    the live ``Entitlement.next_tier_diff`` posture and is the natural
    shape for a two-endpoint diff. ``row.direction`` is always
    ``"upgrade"`` for any purchasable source that has a strictly-higher
    rung above; from ``trial`` ``row.direction`` is ``"upgrade"`` too
    (next strictly-higher purchasable resolves to enterprise).

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``), matching the other ``_at`` family endpoints. ``target``
    / ``row`` collapse to ``null`` at the ceiling (no rung strictly
    above the source -- enterprise as source) -- the surface stays 200
    with a populated envelope so callers can render "you're at the top"
    copy without a status-code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the CTA surface stays mute.
    """
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
        target = _ent._next_purchasable_tier_after(tier_in)
        row = _ent.next_tier_diff_at(tier_in)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        _shared.logger.warning("api_entitlement_next_tier_diff_at: error: %s", exc)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-diff-at")
def api_entitlement_previous_tier_diff_at():
    """``GET /api/entitlement/previous-tier-diff-at?tier=<source>`` --
    scalar what-if sibling of the live
    ``Entitlement.previous_tier_diff``: full
    :func:`clawmetry.entitlements.tier_diff` row from the caller-
    supplied ``tier`` to the rung below it.

    Source-anchored mirror of ``/api/entitlement/next-tier-diff-at``
    and downgrade-side counterpart of the live
    ``Entitlement.previous_tier_diff``. Lets a downgrade-confirmation
    card or pricing-comparison cell render the full step-down payload
    for any hypothetical source rung off **one** round-trip.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<rung-below tier id>" | null,
          "target_label":   "<rung-below label>" | null,
          "target_rank":    <rung-below rank> | null,
          "row":            {<tier_diff row>} | null,
        }

    Like ``/api/entitlement/next-tier-diff-at`` (and unlike
    ``/api/entitlement/previous-tier-unlocks-at`` which surfaces the
    target's own ``tier_unlocks`` row), this endpoint pins **both**
    endpoints, so ``row.from`` is byte-equal to ``tier``. That mirrors
    the live ``Entitlement.previous_tier_diff`` posture and is the
    natural shape for a two-endpoint diff. ``row.direction`` is always
    ``"downgrade"`` for any purchasable source that has a strictly-
    lower rung below; from ``trial`` ``row.direction`` is
    ``"downgrade"`` (next strictly-lower purchasable resolves to
    cloud_starter).

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``), matching the other ``_at`` family endpoints. ``target``
    / ``row`` collapse to ``null`` at the floor (no rung strictly
    below the source -- oss / cloud_free) -- the surface stays 200
    with a populated envelope so callers can render "you're at the
    bottom" copy without a status-code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the CTA surface stays mute.
    """
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
        target = _ent._previous_purchasable_tier_before(tier_in)
        row = _ent.previous_tier_diff_at(tier_in)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_previous_tier_diff_at: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-diff-at-batch")
def api_entitlement_next_tier_diff_at_batch():
    """``GET /api/entitlement/next-tier-diff-at-batch`` -- batch sibling
    of ``/api/entitlement/next-tier-diff-at``: one ``next-tier-diff-at``
    envelope per purchasable source tier, in one round-trip.

    Composes the scalar what-if (``/next-tier-diff-at``) and the live
    batch (``/tier-diff-batch``) -- same envelope shape per row as the
    scalar what-if, same source axis as the live batch. Lets a
    pricing-comparison matrix UI render the "full marginal vs the rung
    above each rung" upgrade-CTA column off **one** call instead of N
    calls to ``/next-tier-diff-at``.

    The "all-slices-in-one-row" member of the ``next-*-at-batch``
    family alongside ``/next-tier-unlocks-at-batch`` (feature / runtime
    grant slice) and ``/next-tier-locks-at-batch`` (feature / runtime
    loss slice). Where each of those siblings carries a single slice of
    the per-rung transition, this batch carries ALL slices in one row
    so a UI can render the whole upgrade matrix off one call instead of
    two.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-diff-batch`` endpoint,
    so the envelopes fold into the same pricing-page table byte-for-
    byte on the source axis.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches ``/api/entitlement/next-tier-diff-at?tier=<source>``
    for that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). The
    ``row`` carries the full :func:`tier_diff` payload pinned on both
    endpoints (``row.from`` is byte-equal to the envelope's ``tier``).
    At the source-side ceiling (``enterprise`` as source -- no rung
    strictly above) the envelope carries ``target=null`` and
    ``row=null`` rather than being dropped, so the matrix keeps a row
    for every purchasable rung.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.next_tier_diff_at_batch() or []
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_next_tier_diff_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-diff-at-batch")
def api_entitlement_previous_tier_diff_at_batch():
    """``GET /api/entitlement/previous-tier-diff-at-batch`` -- batch
    sibling of ``/api/entitlement/previous-tier-diff-at``: one
    ``previous-tier-diff-at`` envelope per purchasable source tier, in
    one round-trip.

    Source-anchored downgrade-side mirror of
    ``/api/entitlement/next-tier-diff-at-batch``. Composes the scalar
    what-if (``/previous-tier-diff-at``) and the live batch
    (``/tier-diff-batch``) -- same envelope shape per row as the
    scalar what-if, same source axis as the live batch. Lets a
    pricing-comparison matrix UI render the "full marginal vs the rung
    below each rung" downgrade-CTA column off **one** call instead of N
    calls to ``/previous-tier-diff-at``.

    The "all-slices-in-one-row" member of the ``previous-*-at-batch``
    family alongside ``/previous-tier-unlocks-at-batch`` (feature /
    runtime grant slice on a downgrade) and
    ``/previous-tier-locks-at-batch`` (feature / runtime loss slice on
    a downgrade). Where each of those siblings carries a single slice
    of the per-rung transition, this batch carries ALL slices in one
    row so a UI can render the whole downgrade matrix off one call
    instead of two.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-diff-batch`` endpoint.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches ``/api/entitlement/previous-tier-diff-at?tier=<source>``
    for that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). The
    ``row`` carries the full :func:`tier_diff` payload pinned on both
    endpoints (``row.from`` is byte-equal to the envelope's ``tier``).
    At the source-side floor (``oss`` / ``cloud_free`` as source -- no
    rung strictly below) the envelope carries ``target=null`` and
    ``row=null`` rather than being dropped, so the matrix keeps a row
    for every purchasable rung.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.previous_tier_diff_at_batch() or []
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_previous_tier_diff_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-capacity-diff-at")
def api_entitlement_next_tier_capacity_diff_at():
    """``GET /api/entitlement/next-tier-capacity-diff-at?tier=<source>`` --
    scalar what-if sibling of the live
    ``Entitlement.next_tier_capacity_diff``: per-axis capacity
    transition from the caller-supplied ``tier`` to the rung above it.

    Capacity-only narrow lens of
    ``/api/entitlement/next-tier-diff-at`` -- the latter returns the
    full :func:`tier_diff` payload for the same step; this endpoint
    returns only the capacity slice
    (``{target, channel_limit, retention_days, node_limit}``) so a
    capacity-only tooltip on a pricing-comparison cell can render the
    upgrade-side capacity delta for any hypothetical source rung off
    **one** round-trip.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<next-above tier id>" | null,
          "target_label":   "<next-above label>" | null,
          "target_rank":    <next-above rank> | null,
          "row":            {<capacity_diff_at row>} | null,
        }

    ``row`` is byte-equal to
    ``/api/entitlement/next-tier-diff-at?tier=<source>``'s
    ``row.capacity_changes`` for the same source (modulo the outer
    :func:`_capacity_row` ``target`` key the diff row does not carry).
    The ``before`` side of each axis comes off the static per-tier
    caps anchored at the caller-supplied ``tier`` (NOT the resolved
    entitlement), so the endpoint is independent of grace mode.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``), matching the other ``_at`` family endpoints. ``target``
    / ``row`` collapse to ``null`` at the ceiling (no rung strictly
    above the source -- enterprise as source) -- the surface stays 200
    with a populated envelope so callers can render "you're at the top"
    copy without a status-code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the tooltip surface stays mute.
    """
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
        target = _ent._next_purchasable_tier_after(tier_in)
        row = _ent.next_tier_capacity_diff_at(tier_in)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_next_tier_capacity_diff_at: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-capacity-diff-at")
def api_entitlement_previous_tier_capacity_diff_at():
    """``GET /api/entitlement/previous-tier-capacity-diff-at?tier=<source>``
    -- scalar what-if sibling of the live
    ``Entitlement.previous_tier_capacity_diff``: per-axis capacity
    transition from the caller-supplied ``tier`` to the rung below it.

    Source-anchored downgrade-side mirror of
    ``/api/entitlement/next-tier-capacity-diff-at`` and capacity-only
    narrow lens of ``/api/entitlement/previous-tier-diff-at``. Lets a
    downgrade-confirmation tooltip render the step-down capacity
    delta for any hypothetical source rung off **one** round-trip.

    Response shape::

        {
          "tier":           "<source tier id>",
          "tier_label":     "<source label>",
          "tier_rank":      <source rank>,
          "target":         "<rung-below tier id>" | null,
          "target_label":   "<rung-below label>" | null,
          "target_rank":    <rung-below rank> | null,
          "row":            {<capacity_diff_at row>} | null,
        }

    ``row`` is byte-equal to
    ``/api/entitlement/previous-tier-diff-at?tier=<source>``'s
    ``row.capacity_changes`` for the same source (modulo the outer
    :func:`_capacity_row` ``target`` key the diff row does not carry).

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``), matching the other ``_at`` family endpoints. ``target``
    / ``row`` collapse to ``null`` at the floor (no rung strictly
    below the source -- oss / cloud_free) -- the surface stays 200
    with a populated envelope so callers can render "you're at the
    bottom" copy without a status-code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``row=null``
      on the same 200 envelope so the tooltip surface stays mute.
    """
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
        target = _ent._previous_purchasable_tier_before(tier_in)
        row = _ent.previous_tier_capacity_diff_at(tier_in)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "row": row,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_previous_tier_capacity_diff_at: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "row": None,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-capacity-diff-at-batch")
def api_entitlement_next_tier_capacity_diff_at_batch():
    """``GET /api/entitlement/next-tier-capacity-diff-at-batch`` --
    batch sibling of ``/api/entitlement/next-tier-capacity-diff-at``:
    one ``next-tier-capacity-diff-at`` envelope per purchasable source
    tier, in one round-trip.

    Capacity-only narrow lens of
    ``/api/entitlement/next-tier-diff-at-batch``. Lets a pricing-
    comparison matrix UI render the "capacity at the rung above each
    rung" upgrade-tooltip column off **one** call instead of N calls
    to ``/next-tier-capacity-diff-at``.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-diff-batch`` endpoint
    and the sibling diff / unlocks / locks ``_at_batch`` endpoints, so
    the four batches fold into the same pricing-page table byte-for-
    byte on the source axis.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches
    ``/api/entitlement/next-tier-capacity-diff-at?tier=<source>`` for
    that source exactly (``tier``, ``tier_label``, ``tier_rank``,
    ``target``, ``target_label``, ``target_rank``, ``row``). The
    ``row`` carries the :func:`capacity_diff_at` row pinned on both
    endpoints. At the source-side ceiling (``enterprise`` as source --
    no rung strictly above) the envelope carries ``target=null`` and
    ``row=null`` rather than being dropped, so the matrix keeps a row
    for every purchasable rung.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.next_tier_capacity_diff_at_batch() or []
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_next_tier_capacity_diff_at_batch: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-capacity-diff-at-batch")
def api_entitlement_previous_tier_capacity_diff_at_batch():
    """``GET /api/entitlement/previous-tier-capacity-diff-at-batch`` --
    batch sibling of ``/api/entitlement/previous-tier-capacity-diff-at``:
    one ``previous-tier-capacity-diff-at`` envelope per purchasable
    source tier, in one round-trip.

    Source-anchored downgrade-side mirror of
    ``/api/entitlement/next-tier-capacity-diff-at-batch`` and capacity-
    only narrow lens of
    ``/api/entitlement/previous-tier-diff-at-batch``. Lets a pricing-
    comparison matrix UI render the "capacity at the rung below each
    rung" downgrade-tooltip column off **one** call instead of N calls
    to ``/previous-tier-capacity-diff-at``.

    No query params. The source list is :data:`entitlements._PURCHASABLE_TIERS`
    (trial excluded), matching the live ``/tier-diff-batch`` endpoint
    and the sibling diff / unlocks / locks ``_at_batch`` endpoints.

    Response shape::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` matches
    ``/api/entitlement/previous-tier-capacity-diff-at?tier=<source>``
    for that source exactly. At the source-side floor (``oss`` /
    ``cloud_free`` as source -- no rung strictly below) the envelope
    carries ``target=null`` and ``row=null`` rather than being
    dropped, so the matrix keeps a row for every purchasable rung.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers``
      list and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        rows = _ent.previous_tier_capacity_diff_at_batch() or []
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_previous_tier_capacity_diff_at_batch: error: %s",
            exc,
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-capacity-headroom-at")
def api_entitlement_next_tier_capacity_headroom_at():
    """``GET /api/entitlement/next-tier-capacity-headroom-at?tier=<source>
    &channels=<int>&retention_days=<int>&nodes=<int>`` -- scalar what-if
    sibling of ``/api/entitlement/next-tier-capacity-headroom``: per-axis
    capacity-headroom envelope for the rung immediately above the caller-
    supplied ``tier``, given the caller-supplied per-axis usage.

    Headroom-shaped mirror of
    ``/api/entitlement/next-tier-capacity-diff-at``: same source-anchored
    "if I were at A, one rung up" posture, headroom envelope instead of
    the capacity-transition triple. Lets a pricing-comparison tooltip
    render "on the rung above <hypothetical A>, given my usage, here's
    what my gauges would look like" for any ``A`` off **one** round-trip
    -- without first hitting ``/api/entitlement`` and without
    monkey-patching the entitlement context.

    Response shape (envelope keys mirror
    ``/api/entitlement/next-tier-capacity-diff-at`` byte-for-key on the
    source / target metadata, with ``row`` renamed to ``headroom`` to
    match the neighbour-tier headroom envelope, plus ``direction`` echoing
    ``"upgrade"``)::

        {
          "tier":         "<source tier id>",
          "tier_label":   "<source label>",
          "tier_rank":    <source rank>,
          "target":       "<next-above tier id>" | null,
          "target_label": "<next-above label>" | null,
          "target_rank":  <next-above rank> | null,
          "direction":    "upgrade",
          "headroom":     {<capacity_headroom_at row>} | null,
        }

    ``headroom`` (when non-null) matches
    ``/api/entitlement/capacity-headroom-at?tier=<target>&channels=...`` for
    the resolved ``target`` byte-for-byte -- pinned in the test suite so
    the convenience cannot drift from the explicit composition.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``), matching the other ``_at`` family endpoints. ``target`` /
    ``headroom`` collapse to ``null`` at the ceiling (no rung strictly
    above the source -- ``enterprise`` as source) -- the surface stays
    200 with a populated envelope so callers can render "you're at the
    top" copy without a status-code branch. Same per-axis "None means
    axis not supplied" posture as ``/capacity-headroom-at`` -- an axis
    the caller didn't pass stays ``None`` on the inner row; a blank /
    non-int / negative value short-circuits that axis to ``None``.

    Decoupled from grace vs enforce: the underlying helper walks the
    static per-tier caps, so inner rows are byte-identical across modes.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``headroom=null``
      on the same 200 envelope so the tooltip surface stays mute.
    """
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
        kwargs: dict[str, int] = {}
        for name in ("channels", "retention_days", "nodes"):
            present, ok, val, _raw = _shared._parse_capacity_arg(name)
            if present and ok and val is not None and val >= 0:
                kwargs[name] = val
        target = _ent._next_purchasable_tier_after(tier_in)
        headroom = _ent.next_tier_capacity_headroom_at(tier_in, **kwargs)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "direction": "upgrade",
                "headroom": headroom,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_next_tier_capacity_headroom_at: error: %s", exc
        )
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "direction": "upgrade",
                "headroom": None,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-capacity-headroom-at")
def api_entitlement_previous_tier_capacity_headroom_at():
    """``GET /api/entitlement/previous-tier-capacity-headroom-at?tier=<source>
    &channels=<int>&retention_days=<int>&nodes=<int>`` -- scalar what-if
    sibling of ``/api/entitlement/previous-tier-capacity-headroom``:
    per-axis capacity-headroom envelope for the rung immediately below
    the caller-supplied ``tier``, given the caller-supplied per-axis
    usage.

    Source-anchored downgrade-side mirror of
    ``/api/entitlement/next-tier-capacity-headroom-at`` and headroom-
    shaped mirror of ``/api/entitlement/previous-tier-capacity-diff-at``.
    Lets a downgrade-confirmation tooltip render "on the rung below
    <hypothetical A>, given my usage, here's what would break" for any
    ``A`` off **one** round-trip -- axes whose inner ``over_limit`` flips
    ``True`` are exactly the ones the caller would lose headroom on.

    Envelope shape matches
    ``/api/entitlement/next-tier-capacity-headroom-at`` byte-for-key
    with ``direction`` echoing ``"downgrade"``. Same per-axis "None means
    unsupplied" posture, bad-arg short-circuit, and grace / enforce
    invariance.

    ``headroom`` (when non-null) matches
    ``/api/entitlement/capacity-headroom-at?tier=<target>&channels=...`` for
    the resolved ``target`` byte-for-byte.

    Accepts any tier id in :data:`entitlements._TIER_ORDER` (including
    ``trial``). ``target`` / ``headroom`` collapse to ``null`` at the
    floor (no rung strictly below the source -- ``oss`` /
    ``cloud_free``) -- the surface stays 200 with a populated envelope
    so callers can render "you're at the bottom" copy without a
    status-code branch.

    - **400** when ``tier=`` is missing / blank
    - **404** when ``tier`` is unknown. The body carries ``which`` so a
      caller can render the right "unknown ..." message.
    - **Never 5xxs**: builder failure short-circuits to ``headroom=null``
      on the same 200 envelope so the tooltip surface stays mute.
    """
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
        kwargs: dict[str, int] = {}
        for name in ("channels", "retention_days", "nodes"):
            present, ok, val, _raw = _shared._parse_capacity_arg(name)
            if present and ok and val is not None and val >= 0:
                kwargs[name] = val
        target = _ent._previous_purchasable_tier_before(tier_in)
        headroom = _ent.previous_tier_capacity_headroom_at(tier_in, **kwargs)
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "direction": "downgrade",
                "headroom": headroom,
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_previous_tier_capacity_headroom_at: error: %s",
            exc,
        )
        return _shared.jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "direction": "downgrade",
                "headroom": None,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/next-tier-capacity-headroom-at-batch")
def api_entitlement_next_tier_capacity_headroom_at_batch():
    """``GET /api/entitlement/next-tier-capacity-headroom-at-batch?
    channels=<int>&retention_days=<int>&nodes=<int>`` -- batch sibling
    of ``/api/entitlement/next-tier-capacity-headroom-at``: one
    ``next-tier-capacity-headroom-at`` envelope per purchasable source
    tier, in one round-trip, given the caller-supplied per-axis usage.

    Headroom-shaped mirror of
    ``/api/entitlement/next-tier-capacity-diff-at-batch``: where that
    batch returns the marginal capacity-transition triple per source,
    this batch returns the per-axis headroom envelope for the same
    source -> next-above-source pair computed off the ``target`` rung's
    static per-tier caps. Lets a pricing-comparison matrix UI render
    the "on the rung above each rung, given my usage, here's what my
    gauges would look like" upgrade-tooltip column off **one** call
    instead of N calls to ``/next-tier-capacity-headroom-at``.

    Response shape (envelope keys mirror
    ``/api/entitlement/next-tier-capacity-diff-at-batch`` byte-for-key
    on the source / target metadata, with each envelope's ``row``
    replaced by ``headroom`` and augmented with ``direction`` echoing
    ``"upgrade"``)::

        {
          "tiers":             [<envelope>, ...],
          "current_tier":      "<resolved tier id>",
          "current_tier_rank": <int>,
          "grace":             <bool>,
          "enforced":          <bool>,
        }

    Each ``<envelope>`` carries::

        {
          "tier":         "<source tier id>",
          "tier_label":   "<source label>",
          "tier_rank":    <source rank>,
          "target":       "<next-above tier id>" | null,
          "target_label": "<next-above label>" | null,
          "target_rank":  <next-above rank> | null,
          "direction":    "upgrade",
          "headroom":     {<capacity_headroom_at row>} | null,
        }

    ``headroom`` (when non-null) matches
    ``/api/entitlement/capacity-headroom-at?tier=<target>&channels=...`` for
    the resolved ``target`` byte-for-byte -- pinned in the test suite so
    the batch what-if cannot drift from the singular ``_at`` sibling.
    Envelope metadata is byte-parallel to
    ``/api/entitlement/next-tier-capacity-diff-at-batch`` on the
    source / target keys so a UI can fold the two batches into one
    matrix row-for-row.

    No source query param (batch walks
    :data:`entitlements._PURCHASABLE_TIERS`, trial excluded). At the
    source-side ceiling (``enterprise`` as source -- no rung strictly
    above) the envelope carries ``target=null`` and ``headroom=null``
    rather than being dropped, so the matrix keeps a row for every
    purchasable rung.

    Per-axis ``None`` on every envelope means "axis not supplied"
    (matches ``/capacity-headroom-batch``'s posture). A blank / non-int
    / negative / ``bool``-in-disguise value on any axis short-circuits
    that axis to ``None`` on every envelope's inner headroom row -- a
    stray query string cannot silently blank the whole matrix.

    Decoupled from grace vs enforce: the underlying helper walks the
    static per-tier caps, so ``tiers`` is byte-identical across modes.
    The envelope's ``current_tier`` / ``grace`` / ``enforced`` still
    track the live resolver so the UI can highlight the caller's
    current rung.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers`` list
      and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        kwargs: dict[str, int] = {}
        for name in ("channels", "retention_days", "nodes"):
            present, ok, val, _raw = _shared._parse_capacity_arg(name)
            if present and ok and val is not None and val >= 0:
                kwargs[name] = val
        rows = _ent.next_tier_capacity_headroom_at_batch(**kwargs)
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_next_tier_capacity_headroom_at_batch: error: %s",
            exc,
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

@_shared.bp_entitlement.route("/api/entitlement/previous-tier-capacity-headroom-at-batch")
def api_entitlement_previous_tier_capacity_headroom_at_batch():
    """``GET /api/entitlement/previous-tier-capacity-headroom-at-batch?
    channels=<int>&retention_days=<int>&nodes=<int>`` -- batch sibling
    of ``/api/entitlement/previous-tier-capacity-headroom-at``: one
    ``previous-tier-capacity-headroom-at`` envelope per purchasable
    source tier, in one round-trip, given the caller-supplied per-axis
    usage.

    Source-anchored downgrade-side mirror of
    ``/api/entitlement/next-tier-capacity-headroom-at-batch`` and
    headroom-shaped mirror of
    ``/api/entitlement/previous-tier-capacity-diff-at-batch``. Lets a
    pricing-comparison matrix UI render the "on the rung below each
    rung, given my usage, here's what would break" downgrade-tooltip
    column off **one** call instead of N calls to
    ``/previous-tier-capacity-headroom-at``.

    Response shape mirrors
    ``/api/entitlement/next-tier-capacity-headroom-at-batch``
    byte-for-key; each envelope carries ``direction="downgrade"``.
    ``headroom`` (when non-null) matches
    ``/api/entitlement/capacity-headroom-at?tier=<target>&channels=...`` for
    the resolved ``target`` byte-for-byte.

    No source query param (batch walks
    :data:`entitlements._PURCHASABLE_TIERS`, trial excluded). At the
    source-side floor (``oss`` / ``cloud_free`` as source -- no rung
    strictly below) the envelope carries ``target=null`` and
    ``headroom=null`` rather than being dropped.

    Same per-axis "None means axis not supplied" posture and bad-arg
    short-circuits as
    ``/api/entitlement/next-tier-capacity-headroom-at-batch``.
    Grace / enforce yields byte-identical ``tiers`` payloads.

    - **Never 5xxs**: a resolver failure yields an empty ``tiers`` list
      and the grace-shape envelope so the matrix keeps rendering.
    """
    try:
        from clawmetry import entitlements as _ent

        kwargs: dict[str, int] = {}
        for name in ("channels", "retention_days", "nodes"):
            present, ok, val, _raw = _shared._parse_capacity_arg(name)
            if present and ok and val is not None and val >= 0:
                kwargs[name] = val
        rows = _ent.previous_tier_capacity_headroom_at_batch(**kwargs)
        ent = _ent.get_entitlement()
        return _shared.jsonify(
            {
                "tiers": rows,
                "current_tier": ent.tier,
                "current_tier_rank": _ent.tier_rank(ent.tier),
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        _shared.logger.warning(
            "api_entitlement_previous_tier_capacity_headroom_at_batch: error: %s",
            exc,
        )
        return _shared.jsonify(
            {
                "tiers": [],
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )
