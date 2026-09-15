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
    book = pb.load_price_book()
    if book.get("present") and not book.get("errors"):
        pb.record_version(book)
    return book, None


@bp_pricing.route("/api/pricing/book", methods=["GET"])
@gate("price_book")
def api_pricing_book():
    from clawmetry import price_book as pb

    book = pb.load_price_book()
    out = pb.public_book(book)
    out["versions"] = pb.recorded_versions()
    out["path"] = pb.default_path()
    return _no_store(jsonify(out))


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
