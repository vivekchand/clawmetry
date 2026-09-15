"""Compliance tab shell: entitlement-gated, honest locked and hosted states.

REQ-COMP-FWM-004 and AC-COMP-FWM-005.3 (Factory requirement
https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/requirements/2b319261-73a2-4f64-b497-3dd80b99a72e,
vivekchand/clawmetry-pro#250). The evaluation, printable report and ATLAS
scenario traceability are clawmetry-pro; this repo ships the tab and a 402
stub for every compliance route.

The rendering rules (a fabricated ``effective`` is shown unrecognised and not
counted, a 402 is an upgrade prompt with no code, the hosted state offers no
upgrade) run against the shipped JS in ``tests/test_compliance_tab_js.js``.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from flask import Flask

ROOT = Path(__file__).resolve().parent.parent
JS = ROOT / "clawmetry" / "static" / "js" / "compliance.js"
TEMPLATE = ROOT / "clawmetry" / "templates" / "tabs" / "compliance.html"


def _client():
    from routes.compliance import bp_compliance

    app = Flask(__name__)
    app.register_blueprint(bp_compliance)
    return app.test_client()


@pytest.mark.parametrize("method,path", [
    ("GET", "/api/compliance/frameworks"),
    ("GET", "/api/compliance/controls?framework=mitre-atlas"),
    ("GET", "/api/compliance/report?framework=mitre-atlas&from=2026-07-01&to=2026-07-31"),
    ("POST", "/api/compliance/bundle?framework=mitre-atlas"),
])
def test_every_compliance_route_is_an_upgrade_prompt_without_pro(method, path):
    """AC-COMP-FWM-005.3: the OSS stub answers 402 upgrade_required for the
    Compliance Pack on every route the pro blueprint serves, the printable
    report included."""
    resp = _client().open(path, method=method)
    assert resp.status_code == 402
    body = resp.get_json()
    assert body["error"] == "upgrade_required"
    assert body["feature"] == "compliance_pack"


def test_stub_mirrors_the_pro_route_table():
    """The stub and the pro blueprint must register the same four URL rules,
    or an OSS-only install 404s where it should offer the upgrade."""
    from routes.compliance import bp_compliance

    app = Flask(__name__)
    app.register_blueprint(bp_compliance)
    rules = sorted((r.rule, tuple(sorted(r.methods - {"HEAD", "OPTIONS"})))
                   for r in app.url_map.iter_rules() if r.endpoint.startswith("compliance."))
    assert rules == [
        ("/api/compliance/bundle", ("POST",)),
        ("/api/compliance/controls", ("GET",)),
        ("/api/compliance/frameworks", ("GET",)),
        ("/api/compliance/report", ("GET",)),
    ]


def test_tab_is_a_page_panel_with_nav_loader_and_script():
    """AC-COMP-FWM-004.1: reachable from the Govern nav, loaded by switchTab."""
    tpl = TEMPLATE.read_text(encoding="utf-8")
    assert 'id="page-compliance"' in tpl and 'class="page"' in tpl
    for hook in ("complianceEvaluate()", "complianceOpenReport()", "complianceDownloadBundle()"):
        assert hook in tpl
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    assert "{% include 'tabs/compliance.html' %}" in dash
    assert "filename='js/compliance.js'" in dash
    assert 'data-tab="compliance" onclick="switchTab(\'compliance\')"' in dash
    app_js = (ROOT / "clawmetry" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert "if (name === 'compliance') { if (typeof loadComplianceTab === 'function') loadComplianceTab(); }" in app_js
    node_tabs = re.search(r"var _CM_NODE_TABS = \[([^\]]*)\]", app_js).group(1)
    all_tabs = re.search(r"var _CM_RT_ALL_TABS = \[([^\]]*)\]", app_js, re.S).group(1)
    # Node-level: a runtime filter must not hide a node-wide evaluation.
    assert "'compliance'" in node_tabs and "'compliance'" in all_tabs


def test_template_renders_for_every_tier():
    """AC-COMP-FWM-004.3: the pro route's own gate decides entitlement. A
    server-side `is_pro` paywall would lock out an entitled self-hosted
    licence, so the shell renders and the 402 decides."""
    tpl = TEMPLATE.read_text(encoding="utf-8")
    assert "is_pro" not in re.sub(r"<!--.*?-->", "", tpl, flags=re.S)
    assert "paywall_modal" not in tpl


def test_hosted_dashboard_fetches_nothing():
    """AC-COMP-FWM-004.4: every entry point checks CLOUD_MODE before any fetch."""
    src = JS.read_text(encoding="utf-8")
    for fn in ("loadComplianceTab", "complianceEvaluate", "complianceOpenReport",
               "complianceDownloadBundle"):
        body = src[src.index(f"function {fn}("):]
        body = body[:body.index("\n  }\n")]
        assert "root.CLOUD_MODE" in body, fn
        calls = [i for i in (body.find("fetch("), body.find("fetchBlob(")) if i >= 0]
        assert calls, f"{fn} makes no request; the check below would be vacuous"
        assert body.index("root.CLOUD_MODE") < min(calls), fn


def test_no_new_user_copy_carries_an_em_dash_or_percentage():
    """AC-COMP-FWM-004.6"""
    for path in (JS, TEMPLATE):
        text = path.read_text(encoding="utf-8")
        copy = re.sub(r"(/\*.*?\*/|<!--.*?-->|^\s*//.*$)", "", text, flags=re.S | re.M)
        assert "—" not in copy, path.name
        assert not re.search(r"\d\s*%|percent", copy, re.I), path.name


@pytest.mark.skipif(shutil.which("node") is None,
                    reason="node not on PATH; the JS rendering suite only runs when Node is available")
def test_compliance_tab_js_suite():
    """AC-COMP-FWM-004.2, AC-COMP-FWM-004.5: runs tests/test_compliance_tab_js.js
    against the shipped compliance.js."""
    proc = subprocess.run(["node", str(ROOT / "tests" / "test_compliance_tab_js.js")],
                          capture_output=True, text=True, timeout=60, cwd=str(ROOT),
                          env=dict(os.environ))
    out = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, "compliance.js tests failed:\n" + out
    assert "tests PASS" in out, out
