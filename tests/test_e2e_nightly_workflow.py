from pathlib import Path

import yaml


WORKFLOW_PATH = Path(".github/workflows/e2e-nightly.yml")


def _load_steps():
    with WORKFLOW_PATH.open(encoding="utf-8") as f:
        workflow = yaml.safe_load(f)
    return workflow["jobs"]["e2e-nightly"]["steps"]


def test_setup_openclaw_runs_before_dashboard_boot():
    steps = _load_steps()
    setup_index = next(
        (
            i
            for i, step in enumerate(steps)
            if step.get("uses") == "./.github/actions/setup-openclaw"
        ),
        None,
    )
    boot_index = next(
        (
            i
            for i, step in enumerate(steps)
            if "dashboard.py" in str(step.get("run", ""))
        ),
        None,
    )

    assert setup_index is not None, "e2e-nightly must use setup-openclaw"
    assert boot_index is not None, "e2e-nightly must boot dashboard.py"
    assert (
        setup_index < boot_index
    ), "setup-openclaw must run before dashboard boot so the token is exported"


def test_openclaw_gateway_token_is_not_pinned_to_ci_test_token():
    for step in _load_steps():
        step_text = str(step)
        assert not (
            "OPENCLAW_GATEWAY_TOKEN" in step_text and "ci-test-token" in step_text
        ), (
            "OPENCLAW_GATEWAY_TOKEN must be inherited from setup-openclaw, "
            "not pinned to literal 'ci-test-token'"
        )


def test_clawmetry_token_reads_openclaw_gateway_token_env():
    for step in _load_steps():
        env = step.get("env", {})
        if "CLAWMETRY_TOKEN" not in env:
            continue

        assert (
            env["CLAWMETRY_TOKEN"] == "${{ env.OPENCLAW_GATEWAY_TOKEN }}"
        ), "CLAWMETRY_TOKEN must read from env.OPENCLAW_GATEWAY_TOKEN"
