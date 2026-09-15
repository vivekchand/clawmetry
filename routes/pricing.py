"""routes/pricing.py: the price book API (REQ-OBS-CEA-024, issue #5936).

Three endpoints, all gated on the ``price_book`` entitlement feature and all
local to this machine (the hosted dashboard refuses them: a negotiated rate is
commercially sensitive and the hosted container has no book to read):

* ``GET  /api/pricing/book``      the local book as validated: accepted entries
  and aliases, each rejected one with its reasons, the current version, and the
  versions recorded so far.
* ``POST /api/pricing/resolve``   which rate applies to each usage record and
  why: the resolved model (alias or reported), the contract entry with its
  effective interval or the reason none applies, the published-list basis, and
  whether the source counts cached tokens inside input tokens. Pass
  ``book_version`` to resolve against the book exactly as an earlier version
  held it.
* ``POST /api/pricing/valuations`` contract valuation and restatement. The
  engine is an extension answering ``pricing.value_usage``; no build ships one
  yet, so without it the route returns 501 ``valuation_engine_unavailable``
  (never an upgrade prompt for something no plan contains). Every record
  the engine returns is checked against the valuation contract and a record
  that does not state its basis is withheld, never passed through.

The contract and all selection logic live in ``clawmetry/price_book.py``.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from clawmetry._gate import gate

bp_pricing = Blueprint("pricing", __name__)

MAX_FACTS = 1000


def _no_store(resp, status=200):
    resp.headers["Cache-Control"] = "no-store"
    return resp, status


def _facts_from_request():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None, None, "Send a JSON object with a 'facts' list."
    facts = body.get("facts")
    if not isinstance(facts, list) or not facts:
        return None, None, "Send a non-empty 'facts' list of usage records."
    if len(facts) > MAX_FACTS:
        return None, None, f"Send at most {MAX_FACTS} usage records per request."
    return body, facts, None


def _book_for(body):
    """(book, error_response). Resolves ``book_version`` when given."""
    from clawmetry import price_book as pb

    version = body.get("book_version") if isinstance(body, dict) else None
    if version:
        book = pb.load_version(version)
        if book is None:
            return None, _no_store(jsonify({
                "error": "unknown_book_version",
                "message": "That price book version is not recorded on this machine, "
                           "or its file was changed after it was recorded.",
            }), 404)
        return book, None
    from clawmetry import price_book_edit as pe

    book = pb.load_price_book()
    # Reading the book is when a hand edit is first seen: record its version
    # and note when it came into effect (never later than now, never earlier
    # than the file changed).
    pe.activate(book)
    return book, None


@bp_pricing.route("/api/pricing/book", methods=["GET"])
@gate("price_book")
def api_pricing_book():
    from clawmetry import extensions
    from clawmetry import price_book as pb
    from clawmetry import price_book_edit as pe

    book = pb.load_price_book()
    pe.activate(book)
    out = pb.public_book(book)
    out["versions"] = pb.recorded_versions()
    out["timeline"] = pe.timeline()
    out["rejected"] = [dict(r, messages=pe.field_problems(r.get("problems")))
                       for r in out["rejected"]]
    out["path"] = pb.default_path()
    out["engine_available"] = pb.VALUE_USAGE_EVENT in extensions.registered_events()
    return _no_store(jsonify(out))


@bp_pricing.route("/api/pricing/entries", methods=["POST"])
@gate("price_book")
def api_pricing_entries():
    """Check or save one added or edited entry (REQ-OBS-CEA-024 .15/.16).

    Body: ``{"entry": {...}, "replace_id": <id being edited> | null,
    "base_version": <version the screen loaded> | null, "dry_run": bool,
    "confirm": bool}``. ``dry_run`` only validates. A save writes only with
    ``confirm: true`` and only while the book is still ``base_version``.
    """
    from clawmetry import price_book_edit as pe
    from routes.guard import _same_origin_ok

    if not _same_origin_ok():
        return _no_store(jsonify({"error": "cross_origin",
                                  "message": "Nothing was saved. The request did not come from this dashboard."}), 403)
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("entry"), dict):
        return _no_store(jsonify({"error": "bad_request",
                                  "message": "Send a JSON object with the entry to check or save."}), 400)
    replace_id = body.get("replace_id")
    if replace_id is not None and not isinstance(replace_id, str):
        return _no_store(jsonify({"error": "bad_request", "message": "replace_id must be an entry id."}), 400)
    if body.get("dry_run"):
        checked = pe.check_entry(body["entry"], replace_id=replace_id)
        return _no_store(jsonify({"ok": checked["ok"], "problems": checked["problems"],
                                  "version": checked["version"], "entry": checked["entry"]}))
    base = body.get("base_version")
    status, out = pe.save_entry(body["entry"], replace_id=replace_id,
                                base_version=base if isinstance(base, str) else None,
                                confirm=body.get("confirm") is True)
    return _no_store(jsonify(out), status)


@bp_pricing.route("/api/pricing/resolve", methods=["POST"])
@gate("price_book")
def api_pricing_resolve():
    from clawmetry import price_book as pb

    body, facts, err = _facts_from_request()
    if err:
        return _no_store(jsonify({"error": "bad_request", "message": err}), 400)
    book, err_resp = _book_for(body)
    if err_resp:
        return err_resp
    return _no_store(jsonify({
        "book_version": book.get("version") if book.get("present") and not book.get("errors") else None,
        "book_present": bool(book.get("present")),
        "resolutions": [pb.resolve_usage(f, book) for f in facts],
    }))


@bp_pricing.route("/api/pricing/valuations", methods=["POST"])
@gate("price_book")
def api_pricing_valuations():
    from clawmetry import extensions
    from clawmetry import price_book as pb

    body, facts, err = _facts_from_request()
    if err:
        return _no_store(jsonify({"error": "bad_request", "message": err}), 400)
    book, err_resp = _book_for(body)
    if err_resp:
        return err_resp
    resolutions = [pb.resolve_usage(f, book) for f in facts]
    restate_against = body.get("restate_against")
    restate_book = None
    if restate_against:
        restate_book = pb.load_version(restate_against)
        if restate_book is None:
            return _no_store(jsonify({
                "error": "unknown_book_version",
                "message": "The version to restate against is not recorded on this machine.",
            }), 404)
    payload = {
        "facts": facts,
        "resolutions": resolutions,
        "book": pb.public_book(book),
        "restate_against": pb.public_book(restate_book) if restate_book else None,
        "restated_resolutions": [pb.resolve_usage(f, restate_book) for f in facts] if restate_book else None,
    }
    result = extensions.call(pb.VALUE_USAGE_EVENT, payload, default=None)
    if result is None:
        # No build ships a valuation engine yet. An upgrade prompt here would
        # sell a plan that does not contain one, so say plainly it is absent.
        return _no_store(jsonify({
            "error": "valuation_engine_unavailable",
            "message": "Contract valuation is not available in this build yet. "
                       "Which rate applies to each record is available at /api/pricing/resolve.",
        }), 501)
    records = result.get("valuations") if isinstance(result, dict) else None
    if not isinstance(records, list):
        return _no_store(jsonify({
            "error": "valuation_engine_error",
            "message": "The valuation engine returned an answer in an unexpected shape, so nothing was shown.",
        }), 502)
    valuations, withheld = [], []
    for i, rec in enumerate(records):
        problems = pb.valuation_problems(rec)
        if problems:
            withheld.append({"index": i, "problems": problems})
        else:
            valuations.append({**rec, **pb.financial_basis(
                rec.get("priced_from"), rec.get("amount"), rec.get("rate_version"))})
    return _no_store(jsonify({
        "book_version": resolutions[0]["book_version"] if resolutions else None,
        "valuations": valuations,
        "withheld": withheld,
    }))
