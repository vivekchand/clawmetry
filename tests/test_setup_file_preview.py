"""Regression coverage for file bytes, preview limits and root boundaries."""
import base64
import importlib.util
from pathlib import Path
import sys

import pytest


MODULE = Path(__file__).resolve().parents[1] / "clawmetry/runtime_memory.py"
spec = importlib.util.spec_from_file_location("setup_preview_memory", MODULE)
memory = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = memory
spec.loader.exec_module(memory)


@pytest.fixture
def root(tmp_path, monkeypatch):
    skill_root = tmp_path / "skills"
    skill_root.mkdir()
    entry = memory.RuntimeCatalogEntry("test", "Test", (
        memory.RootSpec("skills", str(skill_root)),
    ))
    monkeypatch.setattr(memory, "_entry_by_id", lambda runtime: entry)
    return skill_root


@pytest.mark.parametrize("name,raw,mime", [
    ("icon.png", b"\x89PNG\r\n\x1a\n\x00\xff", "image/png"),
    ("photo.JPG", b"\xff\xd8\xff\xe0", "image/jpeg"),
    ("animation.gif", b"GIF89a\x00", "image/gif"),
    ("icon.svg", b'<svg xmlns="http://www.w3.org/2000/svg"/>', "image/svg+xml"),
    ("icon.webp", b"RIFF\x00\x00\x00\x00WEBP", "image/webp"),
])
def test_images_preserve_original_bytes(root, name, raw, mime):
    (root / name).write_bytes(raw)
    data = memory.read_runtime_file("test", str(root), name)
    assert data["preview_type"] == "image"
    assert data["content"] == ""
    header, encoded = data["data_url"].split(",", 1)
    assert header == "data:" + mime + ";base64"
    assert base64.b64decode(encoded) == raw


@pytest.mark.parametrize("raw", [b"\x00\x01\x02", b"SQLite format 3\x00", b"\xff\xfe\xfd"])
def test_binary_never_becomes_garbled_text(root, raw):
    (root / "asset.bin").write_bytes(raw)
    data = memory.read_runtime_file("test", str(root), "asset.bin")
    assert data["binary"] is True
    assert data["preview_type"] == "binary"
    assert data["content"] == ""
    assert data["data_url"] is None


def test_markdown_is_readable_and_html_stays_text(root):
    for name in ("SKILL.md", "page.html"):
        (root / name).write_text("Hello, café <script>alert(1)</script>", encoding="utf-8")
        data = memory.read_runtime_file("test", str(root), name)
        assert data["preview_type"] == "text"
        assert data["content"] == "Hello, café <script>alert(1)</script>"
        assert data["data_url"] is None


def test_large_image_does_not_offer_a_partial_original(root):
    (root / "large.png").write_bytes(b"\x89PNG" + b"x" * 100)
    data = memory.read_runtime_file("test", str(root), "large.png", max_bytes=20)
    assert data["truncated"] is True
    assert data["preview_type"] == "image"
    assert data["data_url"] is None
    assert data["content"] == ""


def test_text_truncated_mid_codepoint_stays_text(root):
    (root / "unicode.md").write_bytes("ab€tail".encode())
    data = memory.read_runtime_file("test", str(root), "unicode.md", max_bytes=4)
    assert data["content"] == "ab"
    assert data["preview_type"] == "text"
    assert data["truncated"] is True


def test_incomplete_utf8_at_end_of_file_is_binary(root):
    (root / "broken.bin").write_bytes(b"ab\xc3")
    data = memory.read_runtime_file("test", str(root), "broken.bin", max_bytes=3)
    assert data["binary"] is True
    assert data["content"] == ""


def test_file_endpoint_returns_original_image_and_preserves_root_checks(root, monkeypatch):
    from flask import Flask
    monkeypatch.setitem(sys.modules, "clawmetry.runtime_memory", memory)
    route_spec = importlib.util.spec_from_file_location(
        "setup_preview_routes", MODULE.parents[1] / "routes/runtime_memory.py")
    routes = importlib.util.module_from_spec(route_spec)
    route_spec.loader.exec_module(routes)
    monkeypatch.setattr(routes, "_runtime_is_locked", lambda runtime: False)
    app = Flask(__name__)
    app.register_blueprint(routes.bp_runtime_memory)
    raw = b"\x89PNG\r\n\x1a\n\xff"
    (root / "icon.png").write_bytes(raw)
    client = app.test_client()
    response = client.get("/api/runtimes/test/file", query_string={"root":str(root), "path":"icon.png"})
    assert response.status_code == 200
    assert base64.b64decode(response.json["data_url"].split(",", 1)[1]) == raw
    assert response.json["content"] == ""
    assert client.get("/api/runtimes/test/file", query_string={"root":str(root), "path":"../private.png"}).status_code == 403


def test_image_cannot_escape_registered_root(root, tmp_path):
    outside = root.parent / (root.name + "-outside.png")
    outside.write_bytes(b"\x89PNG")
    try:
        assert memory.read_runtime_file("test", str(root), "../" + outside.name)["status"] == 403
    finally:
        outside.unlink()


def test_catalogued_shared_skill_symlink_stays_readable(root):
    shared = root.parent / "shared"
    shared.mkdir()
    (shared / "SKILL.md").write_text("Shared skill", encoding="utf-8")
    try:
        (root / "demo").symlink_to(shared, target_is_directory=True)
    except OSError:
        pytest.skip("This OS requires additional privileges for directory symlinks")
    listed = memory.list_files("test", "skills")
    assert any(f["path"] == "demo/SKILL.md" for g in listed["groups"] for f in g["files"])
    data = memory.read_runtime_file("test", str(root), "demo/SKILL.md")
    assert data["ok"] is True
    assert data["content"] == "Shared skill"
