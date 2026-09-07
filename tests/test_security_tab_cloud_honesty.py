"""The hosted Security tab shows only the parts of itself that have data.

Founder report 2026-09-06, hosted dashboard, runtime switcher on Codex: the
Security tab rendered a posture score card of dashes, a "Threat Detection &
Anomaly Alerts" heading over 0/0/0/0 tiles, severity filters that filtered
nothing, and Policy Events + API Key Scan stuck on "Scanning..." forever.
None of those can work there — the cloud container has no ~/.openclaw config
and no local DuckDB, so every one of those scans has nothing to read. His
words: *"if this security is not functional why to show it ... & make users
feel it's a vibe coded software?"*

The rule these tests pin (FLYWHEEL "minimal that works beats broad that
half-works"): a panel that cannot be filled is REMOVED on cloud, not filled
with dashes or an apology. What stays is what the encrypted snapshot really
carries — the tamper-evident log (``securityIntegrity``), the plan's
retention, and the audit log (``auditLog``) when it has entries — plus one
line saying where the local-only scans actually run.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
APP_JS = REPO / "clawmetry" / "static" / "js" / "app.js"
SEC_HTML = REPO / "clawmetry" / "templates" / "tabs" / "security.html"
EN_JSON = REPO / "clawmetry" / "static" / "locales" / "en.json"

# Every panel on the tab whose data source does not exist in the cloud
# container. Each one must be reachable by id, because hiding it is how the
# hosted view stays honest.
CLOUD_DEAD_PANEL_IDS = [
    "security-scan-btn",         # nothing to scan
    "security-posture-panel",    # reads the machine's agent config
    "security-threat-heading",   # promises detection that does not run here
    "security-allclear",
    "security-summary",          # the 0/0/0/0 tiles
    "security-filter-pills",     # filters over an empty list
    "security-threat-panel",
    "security-findings-panel",   # security_events is not in the snapshot
    "policy-events-panel",       # was stuck on "Scanning..." forever
    "credential-scan-panel",     # was stuck on "scanning..." forever
    "security-catalog-panel",    # a catalogue of scans that do not run here
]


def _js():
    return APP_JS.read_text(encoding="utf-8")


def _html():
    return SEC_HTML.read_text(encoding="utf-8")


@pytest.mark.parametrize("panel_id", CLOUD_DEAD_PANEL_IDS)
def test_every_local_only_panel_can_be_addressed_by_id(panel_id):
    assert f'id="{panel_id}"' in _html(), (
        f"{panel_id} has no id in security.html, so the hosted view cannot "
        "hide it and it renders empty for every trial user"
    )


@pytest.mark.parametrize("panel_id", CLOUD_DEAD_PANEL_IDS)
def test_the_cloud_trim_hides_every_local_only_panel(panel_id):
    js = _js()
    i = js.index("function _cmSecurityCloudTrim(")
    lst = js[js.index("_CM_SECURITY_CLOUD_HIDDEN = ["):i]
    assert f"'{panel_id}'" in lst, (
        f"{panel_id} is not in _CM_SECURITY_CLOUD_HIDDEN, so it survives on "
        "the hosted dashboard with nothing in it"
    )


def test_the_trim_only_fires_on_cloud():
    js = _js()
    i = js.index("function _cmSecurityCloudTrim(")
    body = js[i:i + 700]
    assert "if (!window.CLOUD_MODE) return;" in body, (
        "the local dashboard runs these scans for real; the trim must never "
        "touch it"
    )
    assert "security-cloud-note" in body, "the hosted view must say where the scans run"


def test_posture_hides_its_card_instead_of_painting_dashes():
    """'--' next to 'Security Posture' is an empty score card claiming a scan."""
    js = _js()
    i = js.index("async function loadSecurityPosture(")
    branch = js[i:js.index("try {", i)]
    assert "_cmSecurityCloudTrim()" in branch
    code = "\n".join(l for l in branch.splitlines() if not l.strip().startswith("//"))
    assert "'--'" not in code, "the hosted posture card must be gone, not blank"
    assert "Local dashboard only" not in code


def test_the_threat_page_keeps_only_the_slices_the_snapshot_carries():
    js = _js()
    i = js.index("async function loadSecurityPage(")
    branch = js[i:i + 1200]
    cloud = branch[branch.index("if (window.CLOUD_MODE) {"):branch.index("return;\n  }")]
    assert "_cmSecurityCloudTrim()" in cloud
    # securityIntegrity + auditLog are real snapshot slices (cm-cloud-security).
    assert "loadSecurityIntegrity()" in cloud
    assert "loadSecurityAudit()" in cloud
    # security_events is not, so the findings feed must not be started here.
    assert "loadSecurityFindings()" not in cloud


def test_an_empty_hosted_audit_log_removes_its_panel():
    """No governance activity recorded means nothing to show, not an empty box."""
    js = _js()
    i = js.index("async function loadSecurityAudit(")
    body = js[i:js.index("function openDetailView(", i)]
    empty = body[body.index("if (!rows.length) {"):body.index("} else {")]
    assert "security-audit-panel" in empty
    assert "'none'" in empty
    # ...and it comes back when there is something to say.
    assert "_ap2.style.display = ''" in body


def test_the_hosted_note_is_hidden_by_default_and_i18n_keyed():
    html = _html()
    note = html[html.index('id="security-cloud-note"'):]
    note = note[:note.index("</div>")]
    assert "display:none" in note, (
        "the local dashboard runs these scans, so it must not carry the "
        "'they run elsewhere' line"
    )
    key = re.search(r'data-i18n="(security\.cloud_note)"', html)
    assert key, "the hosted note must be translatable like the rest of the tab"
    import json
    assert key.group(1) in json.loads(EN_JSON.read_text(encoding="utf-8")), (
        "a data-i18n key missing from en.json renders the raw key on screen"
    )


def test_the_note_names_no_raw_error_code_and_says_what_to_do():
    import json
    txt = json.loads(EN_JSON.read_text(encoding="utf-8"))["security.cloud_note"]
    for code in ("forbidden", "500", "undefined", "null", "no_auth", "DuckDB"):
        assert code not in txt, f"user-facing copy must not carry {code!r}"
    assert "localhost:8900" in txt, "tell the reader where to go, not just what is missing"
