"""The Memory & Skills catalog must resolve every one of the 20 runtimes.

2026-08-16 audit (one agent per runtime, disk + adapter + vendor-doc
evidence): several paid runtimes rendered empty Memory/Skills tabs because
their catalog roots were wrong or missing, and project-scoped roots resolved
into the OpenClaw workspace for every runtime ("why is it looking in the
openclaw folder"). Each test here pins one audited fix:

  - every runtime the entitlement catalogue advertises has a catalog entry
    (deepseek_harness and qm were missing entirely -> 404);
  - corrected roots find real files (hermes memories/ plural, pi AGENTS.md,
    per-agent deepagents layout, codex skills/.system, qwen/grok/copilot/
    cursor skills, antigravity builtin skills, nanoclaw checkout);
  - the removed roots stay removed (n8n's credential encryptionKey file
    must NEVER be surfaced — it shipped to cloud through the sync path);
  - project-scoped roots expand over the repos the user actually works in
    (Claude Code's ~/.claude.json registry), not just the OpenClaw ws;
  - skills counts count SKILL.md-bearing skills, not raw files.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Isolated HOME with a workspace; catalog env overrides cleared."""
    home = tmp_path / "home"
    home.mkdir()
    ws = tmp_path / "ws"
    ws.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("OPENCLAW_HOME", str(home / ".openclaw"))
    for var in ("CODEX_HOME", "HERMES_HOME", "CLAWMETRY_ANTIGRAVITY_HOME",
                "N8N_USER_FOLDER", "DSH_HOME", "DSH_AGENTS_HOME",
                "CLAWMETRY_GROK_HOME", "CLAWMETRY_COPILOT_HOME",
                "PICOCLAW_HOME", "PI_CODING_AGENT_DIR",
                "CLAWMETRY_NANOCLAW_DIR", "CLAWMETRY_QM_HOME",
                "AIDER_HISTORY_DIRS", "NEMOCLAW_MODEL_ROUTER_CONFIG"):
        monkeypatch.delenv(var, raising=False)
    # Patch the workspace resolver directly rather than importing
    # dashboard: importing the full app under a fake HOME leaves poisoned
    # module state behind for later test files (the sync tests reload
    # modules and would inherit it).
    import clawmetry.runtime_memory as rm
    monkeypatch.setattr(rm, "_workspace_root", lambda: str(ws))
    return home, ws


def _write(base, rel, body="content\n"):
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    return p


def _skill(base, rel_dir):
    return _write(base / rel_dir, "SKILL.md",
                  "---\nname: x\ndescription: d\n---\nbody\n")


def _files(rm, runtime, category):
    payload = rm.list_files(runtime, category=category)
    assert payload.get("error") is None, payload
    out = []
    for g in payload["groups"]:
        for f in g["files"]:
            out.append(os.path.join(g["root"], f["path"]) if f["path"]
                       else g["root"])
    return out


def _import_rm():
    import clawmetry.runtime_memory as rm
    return rm


def test_catalog_covers_every_advertised_runtime(fake_home):
    from clawmetry.entitlements import ALL_RUNTIMES
    rm = _import_rm()
    ids = {r["id"] for r in rm.list_runtimes()}
    missing = set(ALL_RUNTIMES) - ids
    assert not missing, f"runtimes with no Memory/Skills entry: {missing}"


def test_qm_is_an_honest_empty_entry_not_a_404(fake_home):
    rm = _import_rm()
    payload = rm.list_files("qm")
    assert payload.get("error") is None
    assert payload["groups"] == []
    assert "Postgres" in payload.get("note", "")


# ── per-runtime: the audited root fixes actually find files ────────────

def test_hermes_memories_plural_and_soul(fake_home):
    home, _ = fake_home
    _write(home, ".hermes/memories/MEMORY.md")
    _write(home, ".hermes/SOUL.md")
    rm = _import_rm()
    found = _files(rm, "hermes", "memory")
    assert any(p.endswith("memories/MEMORY.md") for p in found)
    assert any(p.endswith("SOUL.md") for p in found)


def test_codex_memories_and_system_skills(fake_home):
    home, _ = fake_home
    _write(home, ".codex/memories/2026-08.md")
    _skill(home, ".codex/skills/mine")
    _skill(home, ".codex/skills/.system/imagegen")
    rm = _import_rm()
    assert any(p.endswith("memories/2026-08.md")
               for p in _files(rm, "codex", "memory"))
    skills = _files(rm, "codex", "skills")
    assert any("skills/mine/SKILL.md" in p for p in skills)
    # .system is dot-prefixed: reachable only via its dedicated root
    assert any(".system/imagegen/SKILL.md" in p for p in skills)


def test_qwen_skills_and_project_slug_memory(fake_home):
    home, _ = fake_home
    _skill(home, ".qwen/skills/deploy")
    _write(home, ".qwen/projects/-tmp-repo/memory/MEMORY.md")
    rm = _import_rm()
    assert any("skills/deploy/SKILL.md" in p
               for p in _files(rm, "qwen_code", "skills"))
    assert any(p.endswith("memory/MEMORY.md")
               for p in _files(rm, "qwen_code", "memory"))


def test_copilot_global_home_skills_and_hooks(fake_home):
    home, _ = fake_home
    _skill(home, ".copilot/skills/review")
    _skill(home, ".copilot/installed-plugins/tool/skills/run")
    _write(home, ".copilot/hooks/numbat.json", "{}")
    rm = _import_rm()
    skills = _files(rm, "copilot", "skills")
    assert any(".copilot/skills/review/SKILL.md" in p for p in skills)
    assert any("installed-plugins/tool/skills/run/SKILL.md" in p
               for p in skills)
    assert any(p.endswith("hooks/numbat.json")
               for p in _files(rm, "copilot", "hooks"))


def test_cursor_skills_agents_commands_hooks(fake_home):
    home, _ = fake_home
    _skill(home, ".cursor/skills/refactor")
    _write(home, ".cursor/agents/reviewer.md")
    _write(home, ".cursor/commands/deploy.md")
    _write(home, ".cursor/hooks.json", "{}")
    rm = _import_rm()
    assert any("skills/refactor/SKILL.md" in p
               for p in _files(rm, "cursor", "skills"))
    assert any(p.endswith("agents/reviewer.md")
               for p in _files(rm, "cursor", "agents"))
    assert any(p.endswith("commands/deploy.md")
               for p in _files(rm, "cursor", "commands"))
    assert any(p.endswith("hooks.json")
               for p in _files(rm, "cursor", "hooks"))


def test_antigravity_builtin_cli_skills(fake_home):
    home, _ = fake_home
    _skill(home, ".gemini/antigravity-cli/builtin/skills/agy-customizations")
    _write(home, ".gemini/config/hooks.json", "{}")
    rm = _import_rm()
    assert any("builtin/skills/agy-customizations/SKILL.md" in p
               for p in _files(rm, "antigravity", "skills"))
    assert any(p.endswith("config/hooks.json")
               for p in _files(rm, "antigravity", "hooks"))


def test_pi_agents_md_and_skills(fake_home):
    home, _ = fake_home
    _write(home, ".pi/agent/AGENTS.md")
    _skill(home, ".pi/agent/skills/browse")
    rm = _import_rm()
    assert any(p.endswith("agent/AGENTS.md")
               for p in _files(rm, "pi", "memory"))
    assert any("agent/skills/browse/SKILL.md" in p
               for p in _files(rm, "pi", "skills"))


def test_deepagents_per_agent_layout(fake_home):
    home, _ = fake_home
    _write(home, ".deepagents/agent/AGENTS.md")
    _write(home, ".deepagents/agent/memories/facts.md")
    _skill(home, ".deepagents/agent/skills/search")
    rm = _import_rm()
    mem = _files(rm, "deepagents", "memory")
    assert any(p.endswith("agent/AGENTS.md") for p in mem)
    assert any(p.endswith("memories/facts.md") for p in mem)
    assert any("agent/skills/search/SKILL.md" in p
               for p in _files(rm, "deepagents", "skills"))


def test_goose_agents_alias_and_recipes(fake_home):
    home, _ = fake_home
    _skill(home, ".agents/skills/plan")
    _write(home, ".config/goose/recipes/daily.yaml", "steps: []\n")
    rm = _import_rm()
    assert any(".agents/skills/plan/SKILL.md" in p
               for p in _files(rm, "goose", "skills"))
    assert any(p.endswith("recipes/daily.yaml")
               for p in _files(rm, "goose", "commands"))


def test_grok_skills_and_hooks(fake_home):
    home, _ = fake_home
    _skill(home, ".grok/skills/summarize")
    _write(home, ".grok/hooks/numbat.json", "{}")
    rm = _import_rm()
    assert any("skills/summarize/SKILL.md" in p
               for p in _files(rm, "grok", "skills"))
    assert any(p.endswith("hooks/numbat.json")
               for p in _files(rm, "grok", "hooks"))


def test_deepseek_harness_entry_resolves(fake_home):
    home, _ = fake_home
    _write(home, ".dsh/AGENTS.md")
    _skill(home, ".dsh/skills/translate")
    _write(home, ".dsh/settings.yaml", "model: deepseek\n")
    rm = _import_rm()
    assert any(p.endswith(".dsh/AGENTS.md")
               for p in _files(rm, "deepseek_harness", "memory"))
    assert any("skills/translate/SKILL.md" in p
               for p in _files(rm, "deepseek_harness", "skills"))
    assert any(p.endswith("settings.yaml")
               for p in _files(rm, "deepseek_harness", "hooks"))


def test_exo_entry_resolves(fake_home, tmp_path, monkeypatch):
    ws = tmp_path / "exo-ws"
    _write(ws, ".exo/exo-profile.md", "# local profile\n")
    _write(ws, "exo/prompts/me.md", "# self prompt\n")
    _write(ws, ".exo/tools/registry.json", "{}\n")
    monkeypatch.setenv("CLAWMETRY_EXO_ROOTS", str(ws))
    rm = _import_rm()
    mem = _files(rm, "exo", "memory")
    assert any(p.endswith("exo-profile.md") for p in mem)
    assert any(p.endswith("prompts/me.md") for p in mem)
    assert any(p.endswith("tools/registry.json")
               for p in _files(rm, "exo", "skills"))


def test_picoclaw_workspace_and_global_skills(fake_home):
    home, _ = fake_home
    _write(home, ".picoclaw/workspace/memory/MEMORY.md")
    _write(home, ".picoclaw/workspace/AGENT.md")
    _skill(home, ".picoclaw/skills/relay")
    rm = _import_rm()
    mem = _files(rm, "picoclaw", "memory")
    assert any(p.endswith("memory/MEMORY.md") for p in mem)
    assert any(p.endswith("AGENT.md") for p in mem)
    assert any("skills/relay/SKILL.md" in p
               for p in _files(rm, "picoclaw", "skills"))


def test_nanoclaw_checkout_via_env(fake_home, tmp_path, monkeypatch):
    checkout = tmp_path / "nanoclaw"
    _write(checkout, "groups/CLAUDE.md")
    _write(checkout, "groups/tg_family/CLAUDE.md")
    _skill(checkout, ".claude/skills/setup")
    monkeypatch.setenv("CLAWMETRY_NANOCLAW_DIR", str(checkout))
    rm = _import_rm()
    mem = _files(rm, "nanoclaw", "memory")
    assert any(p.endswith("groups/CLAUDE.md") for p in mem)
    assert any(p.endswith("tg_family/CLAUDE.md") for p in mem)
    assert any(".claude/skills/setup/SKILL.md" in p
               for p in _files(rm, "nanoclaw", "skills"))


# ── the removed roots stay removed ─────────────────────────────────────

def test_n8n_encryption_key_is_never_surfaced(fake_home):
    home, _ = fake_home
    _write(home, ".n8n/config", '{"encryptionKey": "SECRET"}')
    _write(home, ".n8n/database.sqlite", "binary")
    _write(home, ".n8n/nodes/package.json", "{}")
    rm = _import_rm()
    for category in (None, "hooks", "skills", "memory"):
        for p in _files(rm, "n8n", category):
            assert not p.endswith(".n8n/config"), \
                "n8n credential encryptionKey exposed"
            assert "database.sqlite" not in p
    assert any(p.endswith("nodes/package.json")
               for p in _files(rm, "n8n", "skills"))


def test_invented_roots_are_gone(fake_home):
    rm = _import_rm()
    all_roots = {(r["id"], root["root"])
                 for r in rm.list_runtimes() for root in r["roots"]}
    home = os.path.expanduser("~")
    gone = [
        ("pi", os.path.join(home, ".pi/agent/memory")),
        ("deepagents", os.path.join(home, ".deepagents/memory")),
        ("nanoclaw", os.path.join(home, ".nanoclaw/memory")),
        ("nanoclaw", os.path.join(home, ".nanoclaw/MEMORY.md")),
        ("nemoclaw", os.path.join(home, ".nemoclaw/memory")),
        ("goose", os.path.join(home, ".config/goose/extensions")),
        ("hermes", os.path.join(home, ".hermes/memory")),
    ]
    for rt, root in gone:
        assert (rt, root) not in all_roots, f"invented root back: {rt} {root}"


# ── project scope resolves real repos, not just the OpenClaw ws ────────

def test_project_roots_expand_over_claude_registry(fake_home, tmp_path):
    home, ws = fake_home
    repo = tmp_path / "realrepo"
    _write(repo, ".cursor/rules/style.mdc", "rule\n")
    _write(repo, "AGENTS.md")
    (home / ".claude.json").write_text(json.dumps(
        {"projects": {str(repo): {}}}))
    rm = _import_rm()
    cursor_mem = _files(rm, "cursor", "memory")
    assert any(str(repo) in p and p.endswith("style.mdc")
               for p in cursor_mem), cursor_mem
    codex_mem = _files(rm, "codex", "memory")
    assert any(p == str(repo / "AGENTS.md") for p in codex_mem)


def test_registry_repo_without_runtime_files_stays_quiet(fake_home, tmp_path):
    home, _ = fake_home
    repo = tmp_path / "plainrepo"
    repo.mkdir()
    (home / ".claude.json").write_text(json.dumps(
        {"projects": {str(repo): {}}}))
    rm = _import_rm()
    for r in rm.list_runtimes():
        for root in r["roots"]:
            assert not root["root"].startswith(str(repo)), \
                f"phantom root {root['root']} for {r['id']}"


def test_decode_project_slug_round_trip(fake_home, tmp_path):
    rm = _import_rm()
    deep = tmp_path / "my.dir" / "sub_name"
    deep.mkdir(parents=True)
    # Build the slug the way the runtimes do: every path char (including
    # "." and "_") becomes "-".
    slug = "-" + "-".join(
        rm._encode_seg(seg) for seg in str(deep)[1:].split("/"))
    assert rm._decode_project_slug(slug, max_nodes=5000) == str(deep)
    assert rm._decode_project_slug("-no/such") is None
    assert rm._decode_project_slug("garbage") is None


# ── env overrides the verify pass proved broken ────────────────────────

def test_n8n_user_folder_is_the_parent_of_dot_n8n(fake_home, tmp_path,
                                                  monkeypatch):
    data = tmp_path / "n8ndata"
    _write(data, ".n8n/nodes/package.json", "{}")
    monkeypatch.setenv("N8N_USER_FOLDER", str(data))
    rm = _import_rm()
    assert any(p == str(data / ".n8n/nodes/package.json")
               for p in _files(rm, "n8n", "skills"))


def test_nemoclaw_model_router_env_override(fake_home, tmp_path, monkeypatch):
    alt = tmp_path / "alt-router.yaml"
    alt.write_text("routes: []\n")
    monkeypatch.setenv("NEMOCLAW_MODEL_ROUTER_CONFIG", str(alt))
    rm = _import_rm()
    assert str(alt) in _files(rm, "nemoclaw", "hooks")


def test_aider_history_dirs_feed_project_discovery(fake_home, tmp_path,
                                                   monkeypatch):
    repo = tmp_path / "aiderrepo"
    _write(repo, ".aider.chat.history.md", "# chat\n")
    monkeypatch.setenv("AIDER_HISTORY_DIRS", str(repo))
    rm = _import_rm()
    assert any(p == str(repo / ".aider.chat.history.md")
               for p in _files(rm, "aider", "memory"))


# ── count semantics ────────────────────────────────────────────────────

def test_skills_count_counts_skills_not_files(fake_home):
    home, _ = fake_home
    _skill(home, ".hermes/skills/coding/review")
    _write(home, ".hermes/skills/coding/review/references/a.md")
    _write(home, ".hermes/skills/coding/review/references/b.md")
    _skill(home, ".hermes/skills/ops/deploy")
    rm = _import_rm()
    hermes = next(r for r in rm.list_runtimes() if r["id"] == "hermes")
    assert hermes["counts"]["skills"] == 2


# ── file reads work through the corrected roots ────────────────────────

def test_read_file_through_new_root(fake_home):
    home, _ = fake_home
    _write(home, ".hermes/memories/MEMORY.md", "remember this\n")
    rm = _import_rm()
    root = os.path.join(str(home), ".hermes", "memories")
    got = rm.read_runtime_file("hermes", root, "MEMORY.md")
    assert got["ok"] and "remember this" in got["content"]
