"""Bounded, explicit evidence windows shared by planning and answering.

Limits apply to the assembled prompt, not each row independently. Evidence
records are included whole; omitted records remain discoverable by their read
arguments and continuation cursor. Conversation prose is never fresh evidence.
"""
from __future__ import annotations

import json

MAX_CONTEXT_BYTES = 128 * 1024
MANAGED_PROMPT_CHARS = 29000  # Server limit 30000, with framing headroom.
MANAGED_SYSTEM_CHARS = 16000
MAX_SAVED_SOURCES = 112 * 1024
MAX_SAVED_PANELS = 80 * 1024


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), default=str)


def size(value):
    return len(encode(value).encode('utf-8'))


def clip_text(value, max_bytes):
    return str(value).encode('utf-8')[:max_bytes].decode('utf-8', errors='ignore')


def metric_contract(item, observed_at):
    declared = item.get('metric_contract')
    declared = declared if isinstance(declared, dict) else {}
    return {**{key: clip_text(declared[key], 400) for key in (
        'population', 'runtime', 'time_range', 'timezone', 'numerator',
        'denominator', 'token_basis',
    ) if key in declared}, 'observed_at': observed_at,
        'basis': 'Planner description; verify against the executed SQL.'}


def history_context(history, scrub):
    result = []
    for message in history[-6:]:
        item = {'role': message.get('role'),
                'content': scrub(str(message.get('content') or ''))[:3000]}
        sources = []
        for source in message.get('sources', [])[:8]:
            if not isinstance(source, dict):
                continue
            # Preserve filters, IDs and definitions, not a second copy of raw
            # outputs. A follow-up must retrieve its observations again.
            compact = {key: source[key] for key in (
                'label', 'kind', 'sql', 'read', 'coverage', 'metric_contract',
                'truncated', 'next_cursor',
            ) if key in source}
            refs = []
            for row in source.get('preview', [])[:20]:
                if isinstance(row, dict):
                    ref = {key: row[key] for key in (
                        'session_id', 'event_id', 'call_id', 'runtime', 'ts',
                    ) if key in row}
                    if ref:
                        refs.append(ref)
            if refs:
                compact['references'] = refs
            sources.append(scrub(compact))
        item['sources'] = sources
        item['panels'] = [scrub({key: p.get(key) for key in ('title', 'sql')})
                          for p in message.get('panels', [])[:4] if isinstance(p, dict)]
        result.append(item)
    # Drop older whole turns before sacrificing the latest follow-up context.
    while len(result) > 1 and size(result) > 20000:
        result.pop(0)
    if result and size(result) > 20000:
        result[-1]['sources'] = result[-1]['sources'][-2:]
        result[-1]['panels'] = []
    return result


def _envelope(source, index):
    envelope = {**{k: v for k, v in source.items() if k != 'rows'},
            'citation': index + 1, 'rows': [],
            'returned_rows': len(source['rows']), 'included_rows': 0,
            'preview_truncated': bool(source['rows'])}
    if source.get('kind') == 'session_evidence':
        envelope['available_event_ids'] = [row['event_id'] for row in source['rows']
                                           if isinstance(row, dict) and 'event_id' in row]
    return envelope


def prompt_context(context, evidence, system, mode, *, investigation=None):
    """Fit real records fairly across sources, with honest omission counts."""
    packet = {**context, 'evidence': [_envelope(e, i) for i, e in enumerate(evidence)]}
    if investigation is not None:
        packet['investigation'] = investigation

    def fits():
        text = encode(packet)
        return (len((system + text).encode('utf-8')) <= MAX_CONTEXT_BYTES
                and (mode != 'managed' or
                     (len(text) <= MANAGED_PROMPT_CHARS and len(system) <= MANAGED_SYSTEM_CHARS)))

    while not fits() and packet.get('conversation'):
        packet['conversation'] = packet['conversation'][1:]
    if not fits():
        raise ValueError('The analysis context is too large. Try a narrower question.')
    pending = list(range(len(evidence)))
    positions = [0] * len(evidence)
    while pending:
        next_pending = []
        for index in pending:
            rows = evidence[index]['rows']
            pos = positions[index]
            if pos >= len(rows):
                continue
            target = packet['evidence'][index]
            target['rows'].append(rows[pos])
            target['included_rows'] = pos + 1
            target['preview_truncated'] = pos + 1 < len(rows)
            if not fits() and packet.get('conversation'):
                # Fresh command/output evidence outranks older chat prose.
                # First prove removing history helps; a record larger than the
                # whole provider window must not erase useful follow-up scope.
                prior = packet['conversation']
                packet['conversation'] = []
                can_fit = fits()
                packet['conversation'] = prior
                if can_fit:
                    while packet['conversation'] and not fits():
                        packet['conversation'] = packet['conversation'][1:]
            if fits():
                positions[index] += 1
                next_pending.append(index)
            else:
                target['rows'].pop()
                target['included_rows'] = pos
                target['preview_truncated'] = pos < len(rows)
        pending = next_pending
    return encode(packet)


def saved_sources(evidence):
    sources = []
    for index, entry in enumerate(evidence):
        source = {k: v for k, v in entry.items() if k not in ('rows', 'visual')}
        source.update(label=f"[{index + 1}] {entry['label']}",
                      rows=len(entry['rows']), preview_rows=0, preview=[])
        sources.append(source)
    if size(sources) > MAX_SAVED_SOURCES - 2048:
        raise ValueError('The evidence references are too large to save.')
    # Keep the same bounded records available to the user after a reload.
    for pos in range(max((len(e['rows']) for e in evidence), default=0)):
        for index, entry in enumerate(evidence):
            if pos >= len(entry['rows']):
                continue
            source = sources[index]
            source['preview'].append(entry['rows'][pos])
            if size(sources) > MAX_SAVED_SOURCES - 2048:
                source['preview'].pop()
            source['preview_rows'] = len(source['preview'])
    for source in sources:
        source['preview_truncated'] = source['preview_rows'] < source['rows']
    return sources


def bound_panels(panels):
    # Chart rows come from the same bounded SQL read. Trim only whole rows and
    # disclose the truncation, keeping saved message + sources below 256 KiB.
    while panels and size(panels) > MAX_SAVED_PANELS:
        largest = max(panels, key=lambda panel: size(panel.get('rows', [])))
        if not largest.get('rows'):
            raise ValueError('The generated panels are too large.')
        largest['rows'].pop()
        largest['truncated'] = True
    return panels
