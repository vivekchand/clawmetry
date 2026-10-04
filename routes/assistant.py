"""Local Assistant JSON/SSE interface backed by the single daemon executor."""
from flask import Blueprint, jsonify, request

from clawmetry.assistant_http import invoke
from clawmetry.assistant_service import validate_chat, _ChatFailure

bp_assistant = Blueprint('assistant', __name__)


@bp_assistant.get('/api/assistant/status')
def assistant_status():
    return invoke('status', {})


@bp_assistant.post('/api/assistant/credits/checkout')
def assistant_checkout():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error='Select the $5 top-up to continue to checkout.'), 400
    return invoke('credits_checkout', payload)


@bp_assistant.get('/api/assistant/conversations')
def assistant_conversations():
    return invoke('conversations_list', {})


@bp_assistant.get('/api/assistant/conversations/<conversation_id>')
def assistant_conversation(conversation_id):
    return invoke('conversation_get', {'conversation_id': conversation_id})


@bp_assistant.post('/api/assistant/chat')
def assistant_chat():
    payload = request.get_json(silent=True)
    try:
        validate_chat(payload)
    except _ChatFailure as exc:
        return jsonify(error=exc.message), exc.status
    return invoke('chat', payload, stream=payload.get('stream') is True)
