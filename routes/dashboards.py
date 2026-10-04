"""Saved dashboard HTTP contracts using the node's shared Assistant service."""
from flask import Blueprint, jsonify, request

from clawmetry.assistant_http import invoke

bp_dashboards = Blueprint('dashboards', __name__)


@bp_dashboards.get('/api/dashboard/panels')
def dashboard_panels_list():
    return invoke('panels_list', {'limit': request.args.get('limit', '50')})


@bp_dashboards.post('/api/dashboard/panels')
def dashboard_panels_create():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error='Send a panel as a JSON object.'), 400
    return invoke('panel_create', payload)


@bp_dashboards.get('/api/dashboard/panels/<panel_id>')
def dashboard_panel_get(panel_id):
    return invoke('panel_get', {'panel_id': panel_id})


@bp_dashboards.delete('/api/dashboard/panels/<panel_id>')
def dashboard_panel_delete(panel_id):
    return invoke('panel_delete', {'panel_id': panel_id})
