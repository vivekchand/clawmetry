"""Scoped, bounded, redacted session evidence on the daemon's own connection.

Generated SQL never sees payload columns. This reader projects recorded facts,
not executable tools, and does not open another database or read agent files.
"""
from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timezone
import json
import logging
import math
import re
import time

from clawmetry.ccr import maybe_decompress
from clawmetry.event_shape import classify
from clawmetry.redaction import scrub_export_payload

MAX_RECORDS = 256
MAX_DECODED_BYTES = 2 * 1024 * 1024
MAX_EVENT_BYTES = 256 * 1024
MAX_RESPONSE_BYTES = 48 * 1024
MAX_FIELD_CHARS = 4096
_FIELDS = frozenset({'text', 'command', 'arguments', 'output', 'error', 'exit_code'})
_HIDDEN = frozenset({'thinking', 'reasoning', 'analysis', 'redacted_thinking',
                     'system', 'developer', 'compaction', 'context.compiled'})
_LOG = logging.getLogger(__name__)


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def _size(value):
    return len(_json(value).encode('utf-8'))


def _string(value, name, maximum, *, optional=False):
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value or len(value) > maximum or '\x00' in value:
        raise ValueError('Invalid evidence ' + name)
    return value


def _date(value):
    if value is None:
        return None
    _string(value, 'date', 64)
    try:
        date = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        return date.astimezone(timezone.utc).isoformat()
    except (ValueError, OverflowError):
        raise ValueError('Invalid evidence date') from None


def _integer(value, name, maximum, minimum=0):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError('Invalid evidence ' + name)
    return value


def _visible_text(value):
    """Only explicit display text; never stringify arbitrary content blocks."""
    if isinstance(value, str):
        # Family adapters sometimes store a JSON-encoded content-block list.
        # Recognize that wrapper only; ordinary command stdout stays text.
        if value.lstrip().startswith('['):
            try:
                blocks = json.loads(value)
            except (ValueError, TypeError):
                blocks = None
            known = {'text', 'input_text', 'output_text', 'thinking', 'reasoning',
                     'analysis', 'redacted_thinking', 'tool_use', 'tool_result',
                     'image', 'input_image', 'output_image', 'document'}
            if isinstance(blocks, list) and blocks:
                has_hidden = any(isinstance(block, dict) and any(
                    str(block.get(key, '')).lower() in _HIDDEN for key in ('type', 'phase', 'channel')
                ) for block in blocks)
                if has_hidden or all(isinstance(block, dict) and isinstance(block.get('type'), str)
                                     and block['type'] in known for block in blocks):
                    return _visible_text(blocks)
        return value
    if isinstance(value, list):
        parts = [text for part in value if (text := _visible_text(part))]
        return '\n'.join(parts) if parts or not value else None
    if isinstance(value, dict):
        if any(str(value.get(key, '')).lower() in _HIDDEN for key in ('type', 'phase', 'channel')):
            return None
        if value.get('type') in {'text', 'input_text', 'output_text'}:
            return value.get('text') if isinstance(value.get('text'), str) else ''
    return ''


def _output_text(value):
    if isinstance(value, dict) and 'type' not in value:
        parts = []
        for name in ('stdout', 'stderr', 'output', 'content', 'text', 'message', 'error'):
            if name in value:
                text = _visible_text(value[name])
                if text:
                    parts.append(name+': '+text)
        # An unknown, nonempty structure is unread, not recorded empty text.
        return '\n'.join(parts) if parts or not value else None
    return _visible_text(value)


def _arguments(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return value
    return value


def _no_hidden(value, depth=0):
    if depth > 32:
        raise ValueError('Evidence nesting is too deep')
    if isinstance(value, dict):
        if any(str(value.get(key, '')).lower() in _HIDDEN for key in ('type', 'phase', 'channel')):
            return None
        return {key: _no_hidden(part, depth+1) for key, part in value.items()
                if str(key).lower() not in _HIDDEN and str(key).lower() not in
                {'system_prompt', 'system_instructions', 'thinking_blocks', 'reasoning_content'}}
    if isinstance(value, list):
        return [_no_hidden(part, depth+1) for part in value
                if not isinstance(part, dict) or str(part.get('type', '')).lower() not in _HIDDEN]
    return value


def _first(data, names):
    for name in names:
        value = data.get(name)
        if value is not None:
            return value
    return None


def _project(meta, data):
    """Use the shared runtime normalizer, then retain only the export fields."""
    source, eid, ts, event_type, role, block, tool, error, _length = meta
    item = {'event_id': source+':'+eid, 'ts': ts, 'kind': block or event_type,
            'role': role or '', 'call_id': None, 'tool_name': tool or '',
            'is_error': bool(error), 'fields': {}, 'field_status': {}}
    if not isinstance(data, dict):
        return item, [], 'malformed_payload'
    if str(event_type).lower() in _HIDDEN or str(block).lower() in _HIDDEN:
        return item, [], 'excluded_content'
    data = _no_hidden(data)
    if data is None:
        return item, [], 'excluded_content'
    fields = item['fields']
    calls = []
    if source == 'replay':
        if event_type not in {'tool.call', 'tool.result', 'llm.call', 'llm.response'}:
            return item, [], 'excluded_content'
        if str(data.get('phase', '')).lower() in _HIDDEN or str(data.get('role', '')).lower() in _HIDDEN:
            return item, [], 'excluded_content'
        item['kind'] = event_type
        item['role'] = data.get('role') or ('tool' if event_type == 'tool.result' else 'assistant')
        item['tool_name'] = data.get('tool') or ''
        item['call_id'] = data.get('call_id')
        item['is_error'] = data.get('is_error') is True
        if event_type == 'tool.call':
            fields['arguments'] = _arguments(data.get('args'))
            calls = [{'id': item['call_id'], 'name': item['tool_name'], 'input': fields['arguments']}]
        elif event_type == 'tool.result':
            fields['output'] = _output_text(data.get('output')) if 'output' in data else None
            if data.get('output') and fields['output'] is None:
                item['_unread_fields'] = ['output']
        else:
            fields['text'] = _visible_text(data.get('text')) if 'text' in data else None
    else:
        shape = classify(event_type, data)
        if shape['block_kind'] in _HIDDEN or shape['role'] in _HIDDEN:
            # Runtime error records are allowed, but not system instructions.
            if event_type not in {'error', 'api_error', 'tool.error', 'tool_error'}:
                return item, [], 'excluded_content'
        item.update(kind=shape['block_kind'], role=shape['role'],
                    tool_name=shape['tool_name'], is_error=bool(error or shape['is_error']))
        extra = data.get('extra') if isinstance(data.get('extra'), dict) else {}
        inner = data.get('data') if isinstance(data.get('data'), dict) else data
        item['call_id'] = _first(inner, ('call_id', 'callId', 'tool_call_id', 'tool_use_id', 'toolUseId')) or _first(extra, ('callId', 'call_id', 'tool_call_id', 'tool_use_id', 'toolUseId'))
        calls = shape['tool_uses']
        results = shape['tool_results']
        if calls:
            # Never select one of several embedded invocations arbitrarily.
            if len(calls) == 1:
                item['call_id'] = calls[0].get('id') or item['call_id']
                fields['arguments'] = _arguments(calls[0].get('input'))
            item['_calls'] = calls
        if results:
            if len(results) == 1:
                item['call_id'] = results[0].get('tool_use_id') or item['call_id']
                content = results[0].get('content')
                if content is None:
                    content = _first(inner, ('output', 'result', 'content'))
                fields['output'] = _output_text(content) if content is not None else None
                if content and fields['output'] is None:
                    item['_unread_fields'] = ['output']
            else:
                fields['output'] = None
        elif shape['role'] in {'user', 'assistant'} and not calls:
            fields['text'] = _visible_text(shape['text']) if shape['text'] or 'content' in inner else None
            if shape['text'] and fields['text'] is None:
                item['_unread_fields'] = ['text']
        if item['is_error']:
            err = _first(inner, ('error', 'message'))
            if isinstance(err, str):
                fields['error'] = err
        data = inner
    exit_code = _first(data, ('exit_code', 'exitCode', 'returncode'))
    if exit_code is None and isinstance(data.get('extra'), dict):
        exit_code = _first(data['extra'], ('exit_code', 'exitCode', 'returncode'))
    if exit_code is None:
        for name in ('result', 'output', 'details'):
            if isinstance(data.get(name), dict):
                exit_code = _first(data[name], ('exit_code', 'exitCode', 'returncode'))
                if exit_code is not None:
                    break
    if type(exit_code) is int:
        fields['exit_code'] = exit_code
    if isinstance(fields.get('arguments'), dict):
        command = _first(fields['arguments'], ('command', 'cmd'))
        if isinstance(command, str):
            fields['command'] = command
    # A result's output is error evidence; an error flag alone is not text.
    if item['is_error'] and 'error' not in fields:
        fields['error'] = None
    if item['kind'] in {'tool_result', 'tool.result'}:
        for name in ('output', 'arguments', 'command', 'exit_code'):
            fields.setdefault(name, None)
    return item, calls, None


class _Read:
    def __init__(self, fetch, check, scope, mode, search, state):
        self.fetch, self.check = fetch, check
        self.scope, self.mode, self.search, self.state = scope, mode, search, state
        self.decoded = 0
        self.scanned = 0
        self.withheld = 0
        self.pair_scanned = 0
        self.pair_limited = False
        self.scan_limited = False
        self.cache = {}

    def predicate(self, source, *, window=True):
        if source == 'events':
            clauses = ['session_id = ?', 'node_id = ?']
            params = [self.scope['session_id'], self.scope['node_id']]
            ts = 'TRY_CAST(ts AS TIMESTAMPTZ)'
        else:
            clauses = ['session_id = ?', 'runtime = ?']
            params = [self.scope['session_id'], self.scope['runtime']]
            ts = 'to_timestamp(ts)'
        clauses.append('created_at <= ?')
        params.append(self.state['ingested_before'])
        if window:
            for name, op in (('since', '>='), ('until', '<=')):
                if self.scope[name]:
                    clauses.append(ts+' '+op+' CAST(? AS TIMESTAMPTZ)')
                    params.append(self.scope[name])
        clauses.append(ts+' <= CAST(? AS TIMESTAMPTZ)')
        params.append(self.state['as_of'])
        return clauses, params, ts

    def metadata(self, source, *, cap, after=None, upper=None, event_id=None, pairs=False, anchor=None):
        clauses, params, ts = self.predicate(source)
        eid = 'id' if source == 'events' else 'span_id'
        if source == 'events':
            # Payloads are not read by this query, including for a broad search.
            cols = "event_type, role, block_kind, tool_name, is_error, octet_length(data)"
            if not event_id:
                clauses.append("(block_kind IS NULL OR block_kind NOT IN ('thinking','system','other') OR event_type IN ('error','api_error','tool.error','tool_error'))")
                clauses.append("event_type NOT IN ('thinking','reasoning','analysis','compaction','context.compiled','usage')")
            if pairs:
                clauses.append("(block_kind = 'tool_use' OR event_type IN ('tool_call','tool.call','tool_use','tool.invoked','model.completed','assistant','message'))")
            elif self.mode == 'errors':
                clauses.append("(is_error = TRUE OR (is_error IS NULL AND event_type IN ('tool_result','tool.result','tool_error','tool.error','error','api_error','message')))")
        else:
            cols = 'kind, NULL, NULL, NULL, NULL, octet_length(payload)'
            kinds = ['tool.call'] if pairs else ['tool.call', 'tool.result', 'llm.call', 'llm.response']
            if self.mode == 'errors' and not pairs:
                kinds = ['tool.result']
            if not event_id:
                clauses.append('kind IN ('+','.join('?' for _ in kinds)+')')
                params.extend(kinds)
        for key, op in ((upper, '<='), (after, '<' if self.mode == 'recent' else '>')):
            if key:
                # Spell out the keyset comparison: DuckDB's struct filter
                # pushdown can reject mixed timestamp/string tuple keys.
                direction = '<' if op.startswith('<') else '>'
                clauses.append(f'({ts} {direction} CAST(? AS TIMESTAMPTZ) OR '
                               f'({ts} = CAST(? AS TIMESTAMPTZ) AND {eid} {op} ?))')
                params.extend([key[0], key[0], key[1]])
        if event_id:
            clauses.append(eid+' = ?')
            params.append(event_id)
        if anchor:
            clauses.append(ts+' <= CAST(? AS TIMESTAMPTZ)')
            params.append(anchor)
        direction = 'DESC' if pairs or self.mode == 'recent' else 'ASC'
        table = 'main.events' if source == 'events' else 'main.replay_events'
        sql = f"SELECT {eid}, CAST({ts} AS VARCHAR), {cols} FROM {table} WHERE "+' AND '.join(clauses)+f' ORDER BY {ts} {direction}, {eid} {direction} LIMIT ?'
        params.append(cap)
        return [(source, row[0], _date(row[1]), *row[2:]) for row in self.fetch(sql, params)]

    def load(self, meta, *, pair=False):
        key = meta[:2]
        if key in self.cache:
            return self.cache[key]
        self.check()
        if self.scanned >= MAX_RECORDS or self.decoded >= MAX_DECODED_BYTES:
            self.scan_limited = True
            return None
        self.scanned += 1
        self.pair_scanned += int(pair)
        source, eid = key
        available = min(MAX_EVENT_BYTES, MAX_DECODED_BYTES-self.decoded)
        item = None
        reason = None
        if meta[3] in _HIDDEN or meta[5] in _HIDDEN or meta[4] in {'system', 'developer'}:
            reason = 'excluded_content'
        elif meta[-1] is None:
            reason = 'missing_payload'
        elif meta[-1] > available:
            reason = 'payload_size_limit'
        else:
            column, table, idcol = ('data', 'main.events', 'id') if source == 'events' else ('payload', 'main.replay_events', 'span_id')
            clauses, params, _ts = self.predicate(source)
            clauses.extend([idcol+' = ?', f'octet_length({column}) <= ?'])
            params.extend([eid, available])
            rows = self.fetch(f'SELECT {column} FROM {table} WHERE '+' AND '.join(clauses)+' LIMIT 1', params)
            if not rows or rows[0][0] is None:
                reason = 'payload_unavailable'
            else:
                raw = maybe_decompress(bytes(rows[0][0]), max_bytes=available)
                if raw is None or len(raw) > available:
                    reason = 'decoded_size_limit'
                    # Inflation may have produced the whole allowance before
                    # detecting overflow. Failed decodes consume budget too.
                    self.decoded += available
                else:
                    self.decoded += len(raw)
                    try:
                        data = json.loads(raw)
                        item, _calls, reason = _project(meta, data)
                    except (ValueError, TypeError, RecursionError, UnicodeError):
                        reason = 'malformed_payload'
        if item is None:
            item, _calls, _ = _project(meta, {})
            if item['kind'] in {'tool_result', 'tool.result'}:
                item['fields']['output'] = None
        if reason:
            self.withheld += int(reason != 'missing_payload')
            item['_withheld'] = reason
        self.cache[key] = item
        return item

    def pair(self, item):
        pairing = {'status': 'unresolved', 'basis': 'call_id', 'call_event_id': None,
                   'result_event_id': item['event_id'], 'reason': 'call_id_not_recorded'}
        item['pairing'] = pairing
        if item['kind'] not in {'tool_result', 'tool.result'} or not item.get('call_id'):
            pairing['reason'] = 'not_a_result' if item['kind'] not in {'tool_result', 'tool.result'} else 'call_id_not_recorded'
            return
        matches = []
        # Prefer canonical replay arguments. Fall back to the normalized event
        # stream. Time orders candidates, but ONLY an explicit ID forms a link.
        for source in ('replay', 'events'):
            available = MAX_RECORDS-self.scanned
            cached = sum(key[0] == source for key in self.cache)
            if available <= 0 and not cached:
                self.pair_limited = True
                continue
            cap = min(128, available+cached)
            metas = self.metadata(source, cap=cap+1, pairs=True, anchor=item['ts'])
            if len(metas) > cap:
                self.pair_limited = True
            for meta in metas[:cap]:
                candidate = self.load(meta, pair=True)
                if candidate is None:
                    self.pair_limited = True
                    continue
                if candidate.get('_withheld'):
                    continue
                calls = candidate.get('_calls')
                if calls is None:
                    calls = [{'id': candidate.get('call_id'), 'input': candidate['fields'].get('arguments'), 'name': candidate.get('tool_name')}]
                for index, call in enumerate(calls):
                    if call.get('id') and call['id'] == item['call_id']:
                        matches.append((candidate, index, call))
            if matches:
                break
        if len(matches) > 1:
            pairing.update(status='ambiguous', reason='multiple_calls_with_id')
        elif len(matches) == 1:
            call, _index, invocation = matches[0]
            args = _arguments(invocation.get('input'))
            item['fields']['arguments'] = args
            if isinstance(args, dict):
                command = _first(args, ('command', 'cmd'))
                if isinstance(command, str):
                    item['fields']['command'] = command
            item['tool_name'] = invocation.get('name') or item['tool_name']
            pairing.update(status='paired', call_event_id=call['event_id'], reason='exact_call_id_in_scanned_records')
        else:
            pairing['reason'] = 'pair_scan_limit' if self.pair_limited else 'call_not_found_in_window'


def _export(item, field=None, offset=0, *, slice_fields=True, slice_chars=MAX_FIELD_CHARS):
    """Redact complete projected values before display or continuation slicing."""
    reason = item.get('_withheld')
    exported = {key: value for key, value in item.items() if not key.startswith('_')}
    exported['fields'] = {}
    statuses = exported['field_status'] = {}
    try:
        labels, errors = scrub_export_payload({'tool_name': item['tool_name'], 'call_id': item['call_id']})
        if errors or not isinstance(labels, dict):
            raise ValueError()
        exported.update(labels)
    except Exception:
        exported.update(tool_name='', call_id=None)
        reason = 'redaction_failed'
    wanted = [field] if field else sorted(set(item['fields']) or {'text'})
    if reason:
        for name in wanted:
            statuses[name] = {'status': 'missing' if reason == 'missing_payload' else 'withheld', 'reason': reason}
        return exported
    try:
        projected = _no_hidden(item['fields'])
        safe, withheld = scrub_export_payload(projected)
        if withheld or not isinstance(safe, dict):
            raise ValueError('Evidence could not be redacted')
        for name in wanted:
            if name in item.get('_unread_fields', ()):
                statuses[name] = {'status': 'unread', 'reason': 'unsupported_recorded_shape'}
                continue
            value = safe.get(name)
            if value is None:
                statuses[name] = {'status': 'missing'}
                continue
            text = value if isinstance(value, str) else _json(value)
            start = offset if field else 0
            end = min(len(text), start+slice_chars) if slice_fields else len(text)
            exported['fields'][name] = text[start:end]
            statuses[name] = {'status': 'empty' if not text else 'truncated' if end < len(text) or start else 'available',
                              'offset': start, 'total_chars': len(text),
                              'next_offset': end if end < len(text) else None}
    except Exception:
        exported['fields'] = {}
        for name in wanted:
            statuses[name] = {'status': 'withheld', 'reason': 'redaction_failed'}
    return exported


def _cursor_encode(scope, filters, state, source, after):
    return base64.urlsafe_b64encode(_json({'v': 1, 'scope': scope, 'filters': filters,
        'state': state, 'source': source, 'after': after}).encode()).decode().rstrip('=')


def _cursor_decode(token, scope, filters):
    try:
        _string(token, 'cursor', 8192)
        obj = json.loads(base64.b64decode(token+'='*(-len(token) % 4), altchars=b'-_', validate=True))
        if not isinstance(obj, dict) or obj.get('v') != 1 or obj.get('scope') != scope or obj.get('filters') != filters or obj.get('source') not in {'events', 'replay'}:
            raise ValueError()
        state = obj['state']
        _integer(state['ingested_before'], 'cursor', int(time.time()*1000))
        if _date(state['as_of']) > datetime.now(timezone.utc).isoformat():
            raise ValueError()
        for key in (obj['after'], state['upper']):
            if not isinstance(key, list) or len(key) != 2:
                raise ValueError()
            _date(key[0])
            _string(key[1], 'cursor', 512)
        return obj
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        raise ValueError('Invalid or changed evidence cursor scope') from None


def _finish(result):
    result['coverage']['returned'] = len(result['items'])
    result['bytes'] = 0
    # Account for the byte-count field's own digits.
    for _ in range(4):
        size = _size(result)
        if result['bytes'] == size:
            break
        result['bytes'] = size
    return result


def read_evidence(store, *, session_id, runtime, node_id, mode='errors', since=None,
                  until=None, event_id=None, search=None, cursor=None, limit=20,
                  field=None, offset=0, timeout_secs=5, cancel=None):
    """Read one evidence page. ``cancel`` is an internal callable, never wire data."""
    from clawmetry.local_store import _runtime_of_session_id, _NON_OPENCLAW_RUNTIME_PREFIXES, _assistant_read_cursor
    _string(session_id, 'session', 256)
    _string(node_id, 'node', 256)
    _string(runtime, 'runtime', 64)
    if runtime not in {'openclaw', *_NON_OPENCLAW_RUNTIME_PREFIXES} or _runtime_of_session_id(session_id) != runtime:
        raise ValueError('Invalid evidence runtime scope')
    if not isinstance(mode, str) or mode not in {'errors', 'recent', 'event', 'search'}:
        raise ValueError('Invalid evidence mode')
    limit = _integer(limit, 'limit', 20, 1)
    offset = _integer(offset, 'offset', MAX_EVENT_BYTES)
    if field is not None and (not isinstance(field, str) or field not in _FIELDS or mode != 'event') or offset and field is None:
        raise ValueError('Invalid evidence field')
    if cancel is not None and not callable(cancel):
        raise ValueError('Invalid evidence cancellation')
    try:
        seconds = float(timeout_secs)
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError()
        seconds = min(seconds, 5.)
    except (TypeError, ValueError):
        raise ValueError('Invalid evidence timeout') from None
    scope = {'session_id': session_id, 'runtime': runtime, 'node_id': node_id,
             'since': _date(since), 'until': _date(until)}
    if scope['since'] and scope['until'] and scope['since'] > scope['until']:
        raise ValueError('Invalid evidence time window')
    if mode == 'search':
        _string(search, 'search', 256)
    elif search is not None:
        raise ValueError('Search requires search mode')
    selected = None
    if mode == 'event':
        _string(event_id, 'event', 520)
        source, sep, selected = event_id.partition(':')
        if not sep or source not in {'events', 'replay'} or not selected:
            raise ValueError('Invalid evidence event identity')
        if cursor:
            raise ValueError('Event detail does not accept a page cursor')
    elif event_id is not None:
        raise ValueError('Event identity requires event mode')
    # Bind the literal without embedding potentially private search text in a
    # cursor that will be retained alongside provider evidence.
    search_tag = hashlib.sha256(search.encode()).hexdigest() if search is not None else None
    filters = {'mode': mode, 'search_tag': search_tag, 'field': field, 'offset': offset}
    saved = _cursor_decode(cursor, scope, filters) if cursor else None
    state = saved['state'] if saved else {'as_of': datetime.now(timezone.utc).isoformat(),
                                       'ingested_before': int(time.time()*1000)-1}
    result = {'schema_version': 1, 'scope': scope, 'items': [], 'next_cursor': None,
              'coverage': {'scanned': 0, 'returned': 0, 'matched': 0, 'withheld': 0,
                           'scan_limited': False, 'pair_scanned': 0, 'pair_scan_limited': False,
                           'decoded_bytes': 0, 'as_of': state['as_of'],
                           'traversal': 'bounded_live', 'ingested_before': state['ingested_before']}}
    reader = None
    try:
        with _assistant_read_cursor(store, seconds, cancel) as (fetch, check, _cursor):
            # Replay has no node column: require an unambiguous session owner.
            owners = fetch('SELECT DISTINCT node_id FROM main.sessions WHERE session_id = ? LIMIT 2', [session_id])
            if owners != [(node_id,)]:
                result['error'] = 'Session evidence is unavailable for this scope.'
                result['coverage']['availability'] = 'unavailable'
                return _finish(result)
            reader = _Read(fetch, check, scope, mode, search, state)
            if saved:
                source = saved['source']
            elif mode != 'event':
                source = 'events'
                if not reader.metadata('events', cap=1):
                    source = 'replay'
            if not saved:
                # Capture the greatest eligible key independently of traversal.
                original_mode = reader.mode
                reader.mode = 'recent'
                newest = reader.metadata(source, cap=1, event_id=selected)
                reader.mode = original_mode
                if not newest:
                    result['coverage']['availability'] = 'empty'
                    return _finish(result)
                state['upper'] = list(newest[0][2:3])+[newest[0][1]]
            cap = 128 if mode == 'search' or source == 'replay' else limit+1
            metas = reader.metadata(source, cap=cap+1, upper=state['upper'],
                                    after=saved['after'] if saved else None, event_id=selected)
            more = len(metas) > cap
            last = saved['after'] if saved else None
            pending = []
            scanned_last = last
            # Reserve the primary page before spending any budget on partners.
            # One unmatched result must not hide the rest of the error page.
            for meta in metas[:cap]:
                if len(pending) >= limit:
                    more = True
                    break
                item = reader.load(meta)
                if item is None:
                    more = True
                    break
                key = [meta[2], meta[1]]
                scanned_last = key
                if item.get('_withheld') == 'excluded_content' and mode != 'event':
                    continue
                if mode == 'errors' and not item['is_error'] and not item.get('_withheld'):
                    continue
                if mode == 'search':
                    complete = _export(item, slice_fields=False)
                    if not item.get('_withheld') and any(s.get('status') == 'withheld' for s in complete['field_status'].values()):
                        reader.withheld += 1
                    matches = [(name, re.search(re.escape(search), text, re.IGNORECASE))
                               for name, text in complete['fields'].items()]
                    match = next(((name, found) for name, found in matches if found), None)
                    if match is None:
                        continue
                    # The model can request a detail segment at this redacted
                    # character offset even when the hit is beyond the preview.
                    item['match'] = {'field': match[0], 'offset': match[1].start()}
                pending.append((key, item))
                result['coverage']['matched'] += 1
            for key, raw_item in pending:
                if raw_item['kind'] in {'tool_result', 'tool.result'}:
                    reader.pair(raw_item)
                item = _export(raw_item, field, offset)
                if mode != 'search' and not raw_item.get('_withheld') and any(s.get('status') == 'withheld' for s in item['field_status'].values()):
                    reader.withheld += 1
                # A large Unicode record still gets a usable first segment.
                # Metadata and the next cursor count against the wire bound.
                slice_chars = MAX_FIELD_CHARS
                while _size(item) > MAX_RESPONSE_BYTES//2 and slice_chars > 64:
                    slice_chars //= 2
                    item = _export(raw_item, field, offset, slice_chars=slice_chars)
                next_token = _cursor_encode(scope, filters, state, source, key) if mode != 'event' else None
                if _size({**result, 'items': result['items']+[item], 'next_cursor': next_token,
                          'bytes': MAX_RESPONSE_BYTES}) > MAX_RESPONSE_BYTES-512:
                    more = True
                    reader.scan_limited = True
                    break
                result['items'].append(item)
                last = key
                check()
            else:
                last = scanned_last
            if mode != 'event' and more and last is not None:
                result['next_cursor'] = _cursor_encode(scope, filters, state, source, last)
            reader.scan_limited |= more
            result['coverage']['availability'] = 'available' if result['items'] else 'empty_in_scanned_range'
    except TimeoutError:
        result['error'] = 'Session evidence read timed out. Try a narrower window.'
        result['coverage']['scan_limited'] = True
    except Exception as exc:
        from clawmetry.assistant_stream import Cancelled
        if isinstance(exc, Cancelled):
            raise
        _LOG.warning('Assistant evidence read failed (%s)', type(exc).__name__)
        result['error'] = 'Session evidence could not be read.'
    if reader is not None:
        result['coverage'].update(scanned=reader.scanned, decoded_bytes=reader.decoded,
            withheld=reader.withheld, pair_scanned=reader.pair_scanned,
            pair_scan_limited=reader.pair_limited,
            scan_limited=result['coverage']['scan_limited'] or reader.scan_limited)
    return _finish(result)
