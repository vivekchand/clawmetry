"""The CI scripts that fetch an operator-supplied URL must reject non-HTTP schemes.

Five scripts under ``scripts/`` build a request URL from a value that arrives
from outside the file -- ``--url``, ``--remote-url``, ``--base``, ``--cloud``,
``$CLAWMETRY_URL``, ``$CLAWMETRY_API_BASE`` -- or, in one case, from a URL named
by a remote document (the wheel URL inside the PyPI JSON response). They hand
that value to ``urllib.request.urlopen``, which opens whatever scheme has a
handler registered: ``file:``, ``ftp:``, ``data:``. Without a scheme check, a
misconfigured base turns an API fetch into a local file read and the script then
reports on, prints, or files whatever came back.

Each of those scripts now screens the URL through a ``require_web_url`` /
``_require_web_url`` helper. This pins that behaviour, because a guard with no
test is one refactor away from being a comment. It is the test half of the
bandit B310 declarations on those same call sites.
"""
import importlib.util
import pathlib
import sys

import pytest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"

# (module label, path, helper attribute)
GUARDED = [
    ("accuracy_harness/_lib.py", SCRIPTS / "accuracy_harness" / "_lib.py", "require_web_url"),
    ("verify_runtime_filtering.py", SCRIPTS / "verify_runtime_filtering.py", "_require_web_url"),
    ("verify_i18n_coverage.py", SCRIPTS / "verify_i18n_coverage.py", "_require_web_url"),
    ("verify_otel_recipe_langgraph.py", SCRIPTS / "verify_otel_recipe_langgraph.py", "_require_web_url"),
]

ACCEPTED = [
    "http://127.0.0.1:8900/api/overview",
    "http://localhost:8900/api/local/spans?limit=1",
    "https://app.clawmetry.com/api/v1/sessions",
    "https://pypi.org/pypi/clawmetry/json",
    "HTTPS://app.clawmetry.com/x",          # scheme comparison is case-insensitive
]

REJECTED = [
    "file:///etc/passwd",
    "file:///root/.clawmetry/config.json",  # the credential a harness would leak
    "ftp://example.com/payload",
    "data:text/plain,hello",
    "/api/overview",                        # no scheme at all
    "",
]


def _load(label, path, index):
    """Import a standalone script under a private module name."""
    name = f"_urlguard_{index}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def helpers():
    # accuracy_harness/_lib.py is imported by its siblings as a flat module.
    sys.path.insert(0, str(SCRIPTS / "accuracy_harness"))
    try:
        out = {}
        for i, (label, path, attr) in enumerate(GUARDED):
            module = _load(label, path, i)
            assert hasattr(module, attr), f"{label} lost its {attr} scheme guard"
            out[label] = getattr(module, attr)
        return out
    finally:
        sys.path.remove(str(SCRIPTS / "accuracy_harness"))


@pytest.mark.parametrize("label", [g[0] for g in GUARDED])
@pytest.mark.parametrize("url", ACCEPTED)
def test_http_and_https_are_accepted(helpers, label, url):
    assert helpers[label](url) == url, f"{label} rejected an ordinary HTTP URL"


@pytest.mark.parametrize("label", [g[0] for g in GUARDED])
@pytest.mark.parametrize("url", REJECTED)
def test_non_web_schemes_are_refused(helpers, label, url):
    with pytest.raises(ValueError) as excinfo:
        helpers[label](url)
    # The message has to name the offending URL: these run unattended in CI,
    # where the traceback is the whole report.
    assert "http(s)" in str(excinfo.value)


def test_pr_trace_join_screens_its_dashboard_url():
    """pr_trace_join.py is checked as source, not by import, on purpose.

    It has no ``if __name__ == "__main__"`` guard -- the module body runs the
    whole join, shelling out to git -- so importing it inside a test would run
    the script. This asserts the guard is still wired into the one urlopen
    call instead.
    """
    source = (SCRIPTS / "pr_trace_join.py").read_text(encoding="utf-8")
    assert "_require_web_url(DASH + path)" in source, (
        "pr_trace_join.py fetches $CLAWMETRY_URL without screening its scheme"
    )
    assert "def _require_web_url(" in source
