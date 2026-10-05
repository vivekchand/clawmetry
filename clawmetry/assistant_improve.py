"""Seed an Improve conversation from an exact, redacted store occurrence."""
import logging
import time
from datetime import datetime, timedelta, timezone

_log = logging.getLogger(__name__)

GUIDANCE = """
When improve_review is present, investigate that occurrence. An Improve signal
is a wording-based candidate, not proof of a failure, recurrence or setup cause.
Use a short explanation and a practical next step, normally within 250 words;
leave detailed commands/logs in the cited sources unless the user asks for more.
Explain in plain English what the user wanted, what the agent actually attempted,
what the results establish, and what remains unknown. Inspect both earlier context
and later user corrections before concluding. Initial context reads are bounded;
use remaining reads/continuations when omitted detail could change the explanation.
Then propose one concrete, evidence-supported way to prevent a repeat and a
specific observation or test that would verify it in a future run. If a cause is
unconfirmed, propose the next diagnostic check instead of a speculative setup edit.
Do not turn one ambiguous request into a permanent word-to-action rule or infer a
durable preference. When several components fit a request, recommend identifying
the intended component from current context and clarifying only if still ambiguous.
Propose a persistent instruction only when supported by an explicit preference or
repeated evidence; do not invent absolute rules from one occurrence.
Distinguish a process starting, a tool returning, and the user's task succeeding.
A responding health endpoint does not prove its dependent device or workflow works.
When citing times, label UTC or the recorded offset; never assume the user's zone.
Do not claim a proposal was applied, a future run was checked, or monitoring was
enabled. You are explaining and advising, not changing files or controlling agents.
Keep technical detail in supporting sources unless it helps the user decide.
"""


def validate_reference(value):
    from clawmetry.local_store import (
        _NON_OPENCLAW_RUNTIME_PREFIXES,
        _runtime_of_session_id,
    )
    if not isinstance(value, dict) or set(value) != {'session_id', 'runtime', 'event_id'}:
        raise ValueError('Refresh Improve and select the message again.')
    for key, limit in (('session_id', 256), ('runtime', 64), ('event_id', 520)):
        text = value[key]
        if (not isinstance(text, str) or not text or len(text) > limit
                or any(ord(char) < 32 for char in text)):
            raise ValueError('Refresh Improve and select the message again.')
    if (value['runtime'] not in {'openclaw', *_NON_OPENCLAW_RUNTIME_PREFIXES}
            or _runtime_of_session_id(value['session_id']) != value['runtime']
            or not value['event_id'].startswith('events:') or not value['event_id'][7:]):
        raise ValueError('Refresh Improve and select the message again.')
    return dict(value)


def seed_review(store, reference, node_id, *, deadline=float('inf'), control=None,
                stage=lambda message: None):
    """Three existing evidence reads, never raw files or a second DB connection."""
    reference = validate_reference(reference)
    from clawmetry.entitlements import get_entitlement
    if not get_entitlement().allows_runtime(reference['runtime']):
        raise ValueError('This runtime is not available on your current plan. Check your connected runtimes before investigating.')
    scope = {'session_id': reference['session_id'], 'runtime': reference['runtime'],
             'node_id': node_id}
    reads = []

    def read(args):
        if control:
            control.check()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError('The investigation timed out before its context was read. Try again.')
        kwargs = {**args, 'timeout_secs': min(5.0, remaining)}
        if control:
            kwargs['cancel'] = control.check
        try:
            result = store('query_assistant_session_evidence', **kwargs)
        except (ValueError, TimeoutError):
            _log.warning('Improve Assistant evidence read was rejected or timed out')
            result = {'items': [], 'error': 'This part of the conversation could not be read.'}
        if control:
            control.check()
        if not isinstance(result, dict):
            result = {'items': [], 'error': 'This part of the conversation is unavailable.'}
        reads.append((args, result))
        return result

    stage('Reading the message you selected.')
    anchor = read({**scope, 'mode': 'event', 'event_id': reference['event_id'],
                   'limit': 1, 'offset': 0})
    items = anchor.get('items') or []
    if anchor.get('error') or len(items) != 1 or items[0].get('event_id') != reference['event_id']:
        raise ValueError('The selected message is no longer available on this computer. Refresh Improve and try again.')
    item = items[0]
    if item.get('role') not in ('user', 'human') or not item.get('fields', {}).get('text'):
        raise ValueError('The selected message could not be read. Refresh Improve and select another occurrence.')
    try:
        ts = datetime.fromisoformat(str(item['ts']).replace('Z', '+00:00'))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        end = (ts + timedelta(hours=1)).isoformat()
    except (KeyError, ValueError, TypeError, OverflowError):
        raise ValueError('The selected message has no usable timestamp. Open its conversation to review the evidence.') from None
    stage('Reading what happened before and after that message.')
    read({**scope, 'mode': 'recent', 'until': ts.isoformat(), 'limit': 10, 'offset': 0})
    read({**scope, 'mode': 'recent', 'since': ts.isoformat(), 'until': end, 'limit': 20, 'offset': 0})
    return {'source': 'Improve', **reference, 'selected_at': ts.isoformat(),
            'selected_message': item['fields']['text'][:100],
            'following_window_ends_at': end,
            'coverage_note': 'Initial context: up to 10 preceding items and 20 items in the following hour. Read more when needed.'}, reads
