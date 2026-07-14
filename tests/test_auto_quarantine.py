#!/usr/bin/env python3
"""Unit tests for scripts/auto_quarantine.py (C7 quarantine pipeline).

Covers all pure functions and file-I/O helpers without a running server
or real GitHub API access.  Network calls inside detect_flaky_tests are
not exercised here (they require a live GITHUB_TOKEN); they are covered
by the daily auto-quarantine.yml cron run.

C7 tracking: vivekchand/clawmetry#3740
"""
from __future__ import annotations

import io
import os
import sys
import zipfile
import xml.etree.ElementTree as ET

import pytest

# Import from scripts/ without a package __init__.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import auto_quarantine as aq


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _junit_xml(cases):
    """Build minimal JUnit XML bytes from (classname, name, pass) tuples."""
    root = ET.Element("testsuite")
    for classname, name, ok in cases:
        tc = ET.SubElement(root, "testcase", classname=classname, name=name)
        if not ok:
            ET.SubElement(tc, "failure", message="test failed")
    return ET.tostring(root, encoding="unicode").encode()


def _make_zip(xml_bytes, filename="junit.xml"):
    """Wrap xml_bytes in an in-memory ZIP archive."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(filename, xml_bytes)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# _classname_to_file_and_class
# ---------------------------------------------------------------------------


class TestClassnameToFileAndClass:
    def test_module_level_function(self):
        path, cls = aq._classname_to_file_and_class("tests.test_e2e_oss_golden_path")
        assert path == "tests/test_e2e_oss_golden_path.py"
        assert cls is None

    def test_class_method(self):
        path, cls = aq._classname_to_file_and_class(
            "tests.test_e2e_oss_golden_path.TestGolden"
        )
        assert path == "tests/test_e2e_oss_golden_path.py"
        assert cls == "TestGolden"

    def test_nested_package_function(self):
        path, cls = aq._classname_to_file_and_class("a.b.c.test_foo")
        assert path == "a/b/c/test_foo.py"
        assert cls is None

    def test_nested_package_class(self):
        path, cls = aq._classname_to_file_and_class("a.b.c.TestFoo")
        # TestFoo is PascalCase -> class name; parent is a/b/c
        assert path == "a/b/c.py"
        assert cls == "TestFoo"

    def test_single_segment_lower(self):
        path, cls = aq._classname_to_file_and_class("test_something")
        assert path == "test_something.py"
        assert cls is None

    def test_empty_string(self):
        path, cls = aq._classname_to_file_and_class("")
        # empty split produces [""] -> lower -> no class
        assert path.endswith(".py")
        assert cls is None


# ---------------------------------------------------------------------------
# _parse_junit_xml
# ---------------------------------------------------------------------------


class TestParseJunitXml:
    def test_all_passing_returns_empty(self):
        xml = _junit_xml([
            ("tests.test_e2e", "test_foo", True),
            ("tests.test_e2e", "test_bar", True),
        ])
        assert aq._parse_junit_xml(xml) == set()

    def test_single_failure(self):
        xml = _junit_xml([("tests.test_e2e_oss_golden_path", "test_auth_check", False)])
        result = aq._parse_junit_xml(xml)
        assert result == {"tests/test_e2e_oss_golden_path.py::test_auth_check"}

    def test_mixed_pass_and_fail(self):
        xml = _junit_xml([
            ("tests.test_e2e", "test_ok", True),
            ("tests.test_e2e", "test_bad", False),
        ])
        result = aq._parse_junit_xml(xml)
        assert "tests/test_e2e.py::test_bad" in result
        assert "tests/test_e2e.py::test_ok" not in result

    def test_class_method_failure_builds_correct_node_id(self):
        xml = _junit_xml(
            [("tests.test_e2e_oss_all_tabs.TestAllTabs", "test_brain_tab", False)]
        )
        result = aq._parse_junit_xml(xml)
        assert "tests/test_e2e_oss_all_tabs.py::TestAllTabs::test_brain_tab" in result

    def test_error_element_treated_as_failure(self):
        root = ET.Element("testsuite")
        tc = ET.SubElement(root, "testcase", classname="tests.test_foo", name="test_err")
        ET.SubElement(tc, "error", message="setup error")
        xml_bytes = ET.tostring(root, encoding="unicode").encode()
        result = aq._parse_junit_xml(xml_bytes)
        assert "tests/test_foo.py::test_err" in result

    def test_invalid_xml_returns_empty(self):
        result = aq._parse_junit_xml(b"<not valid xml")
        assert result == set()

    def test_testsuites_wrapper_handled(self):
        root = ET.Element("testsuites")
        suite = ET.SubElement(root, "testsuite")
        tc = ET.SubElement(suite, "testcase", classname="tests.test_foo", name="test_x")
        ET.SubElement(tc, "failure", message="fail")
        xml_bytes = ET.tostring(root, encoding="unicode").encode()
        result = aq._parse_junit_xml(xml_bytes)
        assert "tests/test_foo.py::test_x" in result

    def test_empty_bytes_returns_empty(self):
        result = aq._parse_junit_xml(b"")
        assert result == set()


# ---------------------------------------------------------------------------
# _extract_junit_from_zip
# ---------------------------------------------------------------------------


class TestExtractJunitFromZip:
    def test_single_xml_in_zip(self):
        xml = _junit_xml([("tests.test_e2e", "test_bad", False)])
        result = aq._extract_junit_from_zip(_make_zip(xml))
        assert "tests/test_e2e.py::test_bad" in result

    def test_zip_with_no_xml_files(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("somefile.txt", "not xml")
        result = aq._extract_junit_from_zip(buf.getvalue())
        assert result == set()

    def test_corrupt_zip_returns_empty(self):
        result = aq._extract_junit_from_zip(b"not a zip file at all")
        assert result == set()

    def test_multiple_xml_files_merged(self):
        xml1 = _junit_xml([("tests.test_a", "test_fail1", False)])
        xml2 = _junit_xml([("tests.test_b", "test_fail2", False)])
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("junit-c1.xml", xml1)
            zf.writestr("junit-c5.xml", xml2)
        result = aq._extract_junit_from_zip(buf.getvalue())
        assert "tests/test_a.py::test_fail1" in result
        assert "tests/test_b.py::test_fail2" in result

    def test_passing_tests_not_included(self):
        xml = _junit_xml([
            ("tests.test_e2e", "test_pass", True),
            ("tests.test_e2e", "test_fail", False),
        ])
        result = aq._extract_junit_from_zip(_make_zip(xml))
        assert "tests/test_e2e.py::test_pass" not in result
        assert "tests/test_e2e.py::test_fail" in result


# ---------------------------------------------------------------------------
# _read_quarantine / _write_quarantine
# ---------------------------------------------------------------------------


class TestQuarantineFile:
    def test_read_missing_file_returns_empty(self, tmp_path):
        content, ids = aq._read_quarantine(str(tmp_path / "quarantine.txt"))
        assert content == ""
        assert ids == set()

    def test_read_empty_file_returns_empty_set(self, tmp_path):
        f = tmp_path / "quarantine.txt"
        f.write_text("")
        _, ids = aq._read_quarantine(str(f))
        assert ids == set()

    def test_comments_are_ignored(self, tmp_path):
        f = tmp_path / "quarantine.txt"
        f.write_text("# this is a comment\n# another comment\n")
        _, ids = aq._read_quarantine(str(f))
        assert ids == set()

    def test_blank_lines_are_ignored(self, tmp_path):
        f = tmp_path / "quarantine.txt"
        f.write_text("\n   \n\ntests/test_e2e.py::test_foo\n\n")
        _, ids = aq._read_quarantine(str(f))
        assert ids == {"tests/test_e2e.py::test_foo"}

    def test_valid_entries_read_correctly(self, tmp_path):
        f = tmp_path / "quarantine.txt"
        f.write_text(
            "# comment\n"
            "tests/test_e2e.py::test_foo\n"
            "tests/test_e2e.py::test_bar\n"
        )
        _, ids = aq._read_quarantine(str(f))
        assert ids == {
            "tests/test_e2e.py::test_foo",
            "tests/test_e2e.py::test_bar",
        }

    def test_write_creates_file_with_entries(self, tmp_path):
        f = tmp_path / "quarantine.txt"
        aq._write_quarantine(str(f), "", {"tests/test_e2e.py::test_new"})
        content = f.read_text()
        assert "tests/test_e2e.py::test_new" in content
        assert "Auto-quarantined" in content

    def test_write_appends_without_losing_existing(self, tmp_path):
        f = tmp_path / "quarantine.txt"
        existing = "# existing\ntests/test_e2e.py::test_old\n"
        f.write_text(existing)
        aq._write_quarantine(str(f), existing, {"tests/test_e2e.py::test_new"})
        content = f.read_text()
        assert "test_old" in content
        assert "test_new" in content

    def test_write_sorts_new_entries(self, tmp_path):
        f = tmp_path / "quarantine.txt"
        aq._write_quarantine(
            str(f),
            "",
            {"tests/test_z.py::test_z", "tests/test_a.py::test_a"},
        )
        lines = [
            l for l in f.read_text().splitlines()
            if l.strip() and not l.startswith("#")
        ]
        assert lines[0] == "tests/test_a.py::test_a"
        assert lines[1] == "tests/test_z.py::test_z"

    def test_roundtrip_write_then_read(self, tmp_path):
        f = tmp_path / "quarantine.txt"
        written = {"tests/test_e2e.py::test_foo", "tests/test_e2e.py::test_bar"}
        aq._write_quarantine(str(f), "", written)
        _, ids_back = aq._read_quarantine(str(f))
        assert ids_back == written

    def test_write_new_tests_not_duplicated_by_existing(self, tmp_path):
        f = tmp_path / "quarantine.txt"
        existing = "tests/test_e2e.py::test_already\n"
        f.write_text(existing)
        aq._write_quarantine(str(f), existing, {"tests/test_e2e.py::test_new"})
        content = f.read_text()
        # test_already appears once (from existing), test_new appears once (appended)
        assert content.count("test_already") == 1
        assert content.count("test_new") == 1
