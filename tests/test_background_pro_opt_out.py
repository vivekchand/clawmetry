"""Automatic package maintenance must not remove an operator's fixed overlay."""

import ast
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import time

import pytest

from clawmetry import license as lic


@pytest.fixture
def package_context(tmp_path, monkeypatch):
    package = tmp_path / 'overlay' / 'clawmetry_pro'
    package.mkdir(parents=True)
    asset = package / 'reviewed.txt'
    asset.write_text('reviewed source')
    calls = []
    probes = []
    entitlement = {'entitled': True, 'pro_available': True}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(entitlement).encode()

    def probe(request, **kwargs):
        probes.append(request.full_url)
        return Response()

    def install(*args, **kwargs):
        calls.append('install')
        asset.write_text('replacement source')
        return 'installed'

    monkeypatch.setenv('CLAWMETRY_AUTO_UPDATE', '0')
    monkeypatch.setattr(lic, '_offline_mode', lambda: False)
    monkeypatch.setattr('urllib.request.urlopen', probe)
    monkeypatch.setattr(lic, '_pro_installed_version', lambda: '0.7.51' if package.exists() else None)
    monkeypatch.setattr(lic, '_provision_pro_wheel', install)
    monkeypatch.setattr(lic, '_download_and_install_pro', install)
    monkeypatch.setattr(lic, '_pro_install_locations', lambda: [str(package.parent)])
    monkeypatch.setattr(lic, '_pip_run', lambda args: calls.append('pip') or (True, ''))
    monkeypatch.setattr(lic, '_purge_pro_from_memory', lambda: None)
    monkeypatch.setattr(lic, '_PRO_MARKER_PATH', str(tmp_path / 'marker'))
    monkeypatch.setattr(lic, 'load_license', lambda: object())
    monkeypatch.setattr(lic, 'verify_token', lambda token: {'tier': 'pro'})
    monkeypatch.setattr('clawmetry.extensions.load_plugins', lambda: None)
    return SimpleNamespace(asset=asset, calls=calls, probes=probes, entitlement=entitlement)


def run_daemon_pro_path(path, config):
    """Execute the actual startup block or one actual periodic worker tick."""
    tree = ast.parse((Path(__file__).parents[1] / 'clawmetry/sync.py').read_text())
    daemon = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'run_daemon')
    stopped = False

    def wait(**kwargs):
        nonlocal stopped
        stopped = True

    namespace = {'config': config, 'load_config': lambda: config, 'log': Mock(),
                 'time': SimpleNamespace(sleep=lambda seconds: None),
                 '_pro_stop': SimpleNamespace(is_set=lambda: stopped, wait=wait)}
    if path == 'startup':
        block = next(node for node in daemon.body if isinstance(node, ast.Try) and any(
            isinstance(part, ast.ImportFrom) and any(alias.asname == '_auto_pro' for alias in part.names)
            for part in ast.walk(node)))
        statements = [copy.deepcopy(block)]
    else:
        worker = next(node for node in ast.walk(daemon) if isinstance(node, ast.FunctionDef) and node.name == '_pro_entitlement_worker')
        statements = [copy.deepcopy(worker), ast.Expr(ast.Call(ast.Name('_pro_entitlement_worker', ast.Load()), [], []))]
    module = ast.fix_missing_locations(ast.Module(body=statements, type_ignores=[]))
    exec(compile(module, 'daemon-pro-path', 'exec'), namespace)


@pytest.mark.parametrize('path', ['startup', 'periodic'])
@pytest.mark.parametrize('setting', ['0', 'false', ' NO ', 'Off'])
def test_daemon_opt_out_checks_entitlement_without_install(path, setting, package_context, monkeypatch):
    monkeypatch.setenv('CLAWMETRY_AUTO_UPDATE', setting)
    checked = []
    monkeypatch.setattr(lic, 'should_deprovision_pro', lambda: checked.append(True) or False)
    run_daemon_pro_path(path, {'api_key': 'cm_test_package_policy', 'node_id': 'test-node'})
    assert package_context.probes, 'cloud entitlement remains evaluated'
    assert checked == ([True] if path == 'periodic' else [])
    assert not package_context.calls
    assert package_context.asset.read_text() == 'reviewed source'


@pytest.mark.parametrize('path', ['startup', 'periodic'])
def test_enabled_background_install_keeps_working(path, package_context, monkeypatch):
    monkeypatch.delenv('CLAWMETRY_AUTO_UPDATE')
    monkeypatch.setattr(lic, 'should_deprovision_pro', lambda: False)
    run_daemon_pro_path(path, {'api_key': 'cm_test_package_policy', 'node_id': 'test-node'})
    assert package_context.calls == ['install']


def test_periodic_signed_license_refresh_respects_opt_out(package_context, monkeypatch):
    checked = []
    monkeypatch.setattr(lic, 'load_license', lambda: checked.append(True) or object())
    run_daemon_pro_path('periodic', {'node_id': 'test-node'})
    assert checked == [True]
    assert not package_context.calls
    assert package_context.asset.read_text() == 'reviewed source'


def test_expired_entitlement_denies_features_while_background_retains_files(package_context, monkeypatch):
    from clawmetry import entitlements
    expired = entitlements._build(entitlements.TIER_CLOUD_FREE, 'cloud', expiry=time.time() - 3600, trial_used=True)
    monkeypatch.setattr(entitlements, 'get_entitlement', lambda **kwargs: expired)
    assert lic.should_deprovision_pro()
    run_daemon_pro_path('periodic', {'api_key': 'cm_test_package_policy', 'node_id': 'test-node'})
    assert not expired.allows_feature('robotics')
    assert not expired.allows_runtime('claude_code')
    assert not package_context.calls
    assert package_context.asset.read_text() == 'reviewed source'


def test_retained_package_does_not_make_unentitled_probe_successful(package_context):
    package_context.entitlement['entitled'] = False
    installed, _ = lic.auto_provision_pro('cm_test_package_policy', background=True)
    assert installed is False
    assert not package_context.calls


def test_explicit_connect_update_refresh_and_removal_ignore_background_opt_out(package_context):
    installed, _ = lic.auto_provision_pro('cm_test_package_policy', 'test-node')
    assert installed is True
    lic.sync_pro_from_config({'api_key': 'cm_test_package_policy', 'node_id': 'test-node'})
    lic.refresh_pro_from_license('test-node')
    assert package_context.calls == ['install', 'install', 'install']
    removed, _ = lic.deprovision_pro('explicit removal')
    assert removed is True
    assert not package_context.asset.exists()
