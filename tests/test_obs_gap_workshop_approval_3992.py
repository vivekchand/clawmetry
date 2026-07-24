"""Tests for _workshop_approval_config() in the OpenClaw adapter (#3992).

Gap: detect() metadata didn't include skills.workshop.approvalPolicy, so
cloud-synced fleet views couldn't surface whether autonomous skill
apply/reject/quarantine actions are gated by human approval.
"""
import json

import pytest

from clawmetry.adapters.openclaw import _workshop_approval_config


def test_policy_pending(tmp_path, monkeypatch):
    cfg = {"skills": {"workshop": {"approvalPolicy": "pending"}}}
    (tmp_path / "openclaw.json").write_text(json.dumps(cfg))
    monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
    assert _workshop_approval_config() == {"workshopApprovalPolicy": "pending"}


def test_policy_auto(tmp_path, monkeypatch):
    cfg = {"skills": {"workshop": {"approvalPolicy": "auto"}}}
    (tmp_path / "openclaw.json").write_text(json.dumps(cfg))
    monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
    assert _workshop_approval_config() == {"workshopApprovalPolicy": "auto"}


def test_policy_absent(tmp_path, monkeypatch):
    cfg = {"skills": {"workshop": {}}}
    (tmp_path / "openclaw.json").write_text(json.dumps(cfg))
    monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
    assert _workshop_approval_config() == {}


def test_no_config_file(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
    assert _workshop_approval_config() == {}


def test_non_dict_config(tmp_path, monkeypatch):
    (tmp_path / "openclaw.json").write_text("[1, 2, 3]")
    monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
    assert _workshop_approval_config() == {}
