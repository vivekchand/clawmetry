"""Entitled recurring-error reads over the shared encrypted query contract."""
import logging

from flask import Blueprint, jsonify, request

from clawmetry._gate import gate
from routes.local_query import _dispatch

bp_error_groups = Blueprint('error_groups', __name__)
log = logging.getLogger(__name__)


@bp_error_groups.get('/api/error-triage/groups')
@gate('error_triage')
def groups():
    try:
        body = _dispatch('error_groups', request.args.to_dict())
        return jsonify(body), 200 if body.get('available') else 503
    except (ValueError, TypeError):
        return jsonify(available=False, error='Invalid error-group filters.'), 400
    except Exception:
        log.warning('Error groups could not be read', exc_info=True)
        return jsonify(available=False, reason='Error groups are unavailable from this node.'), 503
