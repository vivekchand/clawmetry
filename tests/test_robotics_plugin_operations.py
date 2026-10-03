"""Only declared private operations cross the daemon plugin boundary."""
import pytest


@pytest.mark.parametrize('operation', ['runs', 'events', 'snapshot', 'inventory', 'guard_ack', 'guard_incidents'])
def test_robotics_operation_dispatches_to_private_plugin(monkeypatch, operation):
    from clawmetry import extensions
    from clawmetry.local_store import LocalStore
    store = object.__new__(LocalStore)
    calls = []
    monkeypatch.setattr(extensions, 'call', lambda event, payload, **kw: calls.append((event, payload)) or {'ok': True})
    assert store.robotics_query(operation, {'run_id': 'a' * 32}) == {'ok': True}
    assert calls == [('robotics.query', {'store': store, 'operation': operation, 'args': {'run_id': 'a' * 32}})]


def test_unknown_robotics_operation_is_rejected_before_plugin(monkeypatch):
    from clawmetry import extensions
    from clawmetry.local_store import LocalStore
    store = object.__new__(LocalStore)
    monkeypatch.setattr(extensions, 'call', lambda *a, **kw: pytest.fail('Unknown operation reached plugin'))
    with pytest.raises(ValueError):
        store.robotics_query('execute_sql', {})


def test_mutation_does_not_become_a_cloud_read_shape():
    from clawmetry.query_contract import QUERY_CONTRACT
    assert 'robotics_guard_ack' not in QUERY_CONTRACT
    assert 'robotics_control' not in QUERY_CONTRACT


def test_incident_read_shape_preserves_cursor_precision_and_clamps_page():
    from routes.local_query import _coerce_args, _dispatch
    from clawmetry.query_contract import QUERY_CONTRACT, TRUST_E2E
    assert QUERY_CONTRACT['robotics_incidents']['trust'] == TRUST_E2E
    args = _coerce_args('robotics_incidents', {'run_id': 'a' * 32, 'before_ns': '1790000000000000001',
                                            'before_id': 'b' * 32, 'limit': 10000, 'execute': 'forbidden'})
    assert args == {'run_id': 'a' * 32, 'before_ns': '1790000000000000001', 'before_id': 'b' * 32, 'limit': 64}
    with pytest.raises(ValueError):
        _coerce_args('robotics_incidents', {'run_id': '../untrusted'})
