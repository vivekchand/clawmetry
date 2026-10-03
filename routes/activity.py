"""Persisted activity transports; source logs are only read by the daemon."""
import json
import logging
import time

from flask import Blueprint, Response, jsonify, request, stream_with_context

from routes.local_query import _dispatch

bp_activity = Blueprint('activity', __name__)
log = logging.getLogger('clawmetry.activity')


@bp_activity.get('/api/activity')
def activity():
    try:
        return jsonify(dict(_dispatch('activity', request.args.to_dict()), available=True))
    except ValueError:
        return jsonify(available=False, reason='Choose a valid activity scope.'), 400
    except Exception:
        log.warning('Persisted activity is unavailable', exc_info=True)
        return jsonify(available=False, coverage={'node_reachable': False},
                       reason='Reconnect to this node to resume activity.'), 503


def brain_stream():
    """Legacy SSE clients get bounded pages and Last-Event-ID replay support.

    Cursor IDs are emitted AFTER every event in the batch, so a disconnected
    partial batch replays safely. New UI consumers share /api/activity reads.
    """
    import dashboard
    if not dashboard._acquire_stream_slot('brain'):
        return jsonify(error='Too many active activity streams'), 429
    args = {k: request.args[k] for k in ('node_id', 'runtime', 'session_id') if request.args.get(k)}
    cursor = request.headers.get('Last-Event-ID') or request.args.get('cursor')

    @stream_with_context
    def generate():
        nonlocal cursor
        started = time.monotonic()
        connected = False
        try:
            while time.monotonic() - started < dashboard.SSE_MAX_SECONDS:
                try:
                    page = _dispatch('activity', dict(args, cursor=cursor, limit=100))
                except Exception:
                    log.warning('Activity stream read unavailable', exc_info=True)
                    yield 'event: unavailable\ndata: {"available":false}\n\n'
                    return
                if page.get('resync_required'):
                    cursor = None
                    yield 'id:\nevent: resync\ndata: {"resync_required":true}\n\n'
                    continue
                if not connected:
                    connected = True
                    yield 'event: connected\ndata: {"source":"persisted"}\n\n'
                for event in page.get('brain_events', []):
                    yield 'data: ' + json.dumps(event) + '\n\n'
                cursor = page['cursor']
                yield 'id: ' + cursor + '\nevent: checkpoint\ndata: {}\n\n'
                if not page.get('has_more'):
                    time.sleep(2)
        finally:
            dashboard._release_stream_slot('brain')
    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
