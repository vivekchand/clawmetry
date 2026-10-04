"""Local HTTP adapters for typed daemon Assistant jobs; no inference here."""
from __future__ import annotations

import os
import sys
import time
import uuid

from flask import Response, jsonify

from clawmetry import assistant_stream
from clawmetry.assistant_stream import _frame

UNAVAILABLE = 'The local sync service is unavailable. Start it and retry.'


def rpc(method, **kwargs):
    from routes.local_query import local_store_via_daemon
    return local_store_via_daemon(method, **kwargs)


def invoke(operation, payload, *, stream=False):
    # A hosted container must never execute using its own credentials or data.
    if os.environ.get('CLOUD_MODE') == '1' or getattr(sys.modules.get('dashboard'), 'CLOUD_MODE', False):
        return jsonify(error='Connect the encrypted node transport to use Assistant.'), 503
    rid = uuid.uuid4().hex
    try:
        started = rpc('start_assistant_job', request_id=rid, operation=operation, payload=payload)
    except Exception:
        started = None
    if not isinstance(started, dict):
        return jsonify(error=UNAVAILABLE), 503
    if started.get('error'):
        return jsonify(error=started['error']), started.get('http_status', 503)

    def cancel():
        try:
            rpc('cancel_assistant_job', request_id=rid)
        except Exception:
            pass

    def events():
        cursor = 0
        deadline = time.monotonic()+180
        heartbeat = time.monotonic()+assistant_stream.HEARTBEAT_SECONDS
        try:
            while time.monotonic() < deadline:
                try:
                    data = rpc('read_assistant_job', request_id=rid, renew=True)
                except Exception:
                    data = None
                if not isinstance(data, dict) or data.get('error'):
                    yield 'error', {'error': UNAVAILABLE}, 503
                    return
                for item in data.get('events', []):
                    seq = item.get('seq')
                    if seq <= cursor:
                        continue
                    if seq != cursor+1:
                        yield 'error', {'error': 'The live reply was interrupted. Please retry.'}, 502
                        return
                    cursor = seq
                    yield item['event'], item['data'], data.get('http_status', 200)
                if data.get('terminal'):
                    return
                if time.monotonic() >= heartbeat:
                    yield 'heartbeat', None, 200
                    heartbeat = time.monotonic()+assistant_stream.HEARTBEAT_SECONDS
                time.sleep(0.1)
            yield 'error', {'error': 'The assistant took too long. Try a narrower question.'}, 504
        finally:
            cancel()

    if stream:
        def generate():
            for event, data, _status in events():
                yield ': keepalive\n\n' if event == 'heartbeat' else _frame(event, data)
        response = Response(generate(), mimetype='text/event-stream', headers={
            'Cache-Control': 'no-cache, no-store, no-transform', 'X-Accel-Buffering': 'no'})
        response.call_on_close(cancel)
        return response
    for event, data, status in events():
        if event in ('done', 'error'):
            return jsonify(data), status
    return jsonify(error='The assistant did not complete its response. Please retry.'), 502
