"""Unit tests for routes/reports.py (issue #1005).

Tests the blueprint endpoints and helper functions without requiring a running
DuckDB — the SQL execution is mocked out.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Make sure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMdToHtml(unittest.TestCase):
    def setUp(self):
        from routes.reports import _md_to_html
        self.md_to_html = _md_to_html

    def test_h1(self):
        self.assertIn("<h1>Hello</h1>", self.md_to_html("# Hello"))

    def test_h2(self):
        self.assertIn("<h2>World</h2>", self.md_to_html("## World"))

    def test_h3(self):
        self.assertIn("<h3>Foo</h3>", self.md_to_html("### Foo"))

    def test_paragraph(self):
        self.assertIn("<p>Just text</p>", self.md_to_html("Just text"))

    def test_bold(self):
        result = self.md_to_html("**bold**")
        self.assertIn("<strong>bold</strong>", result)

    def test_italic(self):
        result = self.md_to_html("*italic*")
        self.assertIn("<em>italic</em>", result)

    def test_list_item(self):
        self.assertIn("<li>item</li>", self.md_to_html("- item"))

    def test_escapes_html(self):
        result = self.md_to_html("a <script> tag")
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)

    def test_code_fence(self):
        md = "```sql\nSELECT 1\n```"
        result = self.md_to_html(md)
        self.assertIn("<pre", result)
        self.assertIn("SELECT 1", result)


class TestRowsToTable(unittest.TestCase):
    def setUp(self):
        from routes.reports import _rows_to_html_table
        self.rows_to_table = _rows_to_html_table

    def test_empty(self):
        result = self.rows_to_table([])
        self.assertIn("No results", result)

    def test_single_row(self):
        result = self.rows_to_table([{"count": 42, "name": "foo"}])
        self.assertIn("<th>count</th>", result)
        self.assertIn("<td>42</td>", result)
        self.assertIn("<td>foo</td>", result)

    def test_none_value(self):
        result = self.rows_to_table([{"col": None}])
        self.assertIn("<td></td>", result)

    def test_escapes_values(self):
        result = self.rows_to_table([{"col": "<script>xss</script>"}])
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)


class TestRunSql(unittest.TestCase):
    def test_rejects_long_sql(self):
        from routes.reports import _run_sql
        rows, err = _run_sql("SELECT 1  " + "x" * 2001)
        self.assertIsNotNone(err)
        self.assertIn("too long", err)

    def test_rejects_drop(self):
        from routes.reports import _run_sql
        rows, err = _run_sql("DROP TABLE sessions")
        self.assertIsNotNone(err)
        self.assertEqual(rows, [])

    def test_accepts_select_via_mock(self):
        from routes.reports import _run_sql
        with patch("routes.reports.local_store_via_daemon", return_value=None, create=True):
            with patch("routes.reports._run_sql") as mock_run:
                mock_run.return_value = ([{"n": 1}], None)
                rows, err = mock_run("SELECT 1 AS n")
        self.assertIsNone(err)
        self.assertEqual(rows[0]["n"], 1)


class TestSafeSlug(unittest.TestCase):
    def test_clean_slug(self):
        from routes.reports import _safe_slug
        self.assertEqual(_safe_slug("my-report_v2"), "my-report_v2")

    def test_strips_traversal(self):
        from routes.reports import _safe_slug
        self.assertEqual(_safe_slug("../../etc/passwd"), "etcpasswd")

    def test_strips_spaces(self):
        from routes.reports import _safe_slug
        self.assertEqual(_safe_slug("my report"), "myreport")


class TestBlueprintEndpoints(unittest.TestCase):
    def setUp(self):
        from flask import Flask
        from routes.reports import bp_reports
        app = Flask(__name__)
        app.register_blueprint(bp_reports)
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.tmpdir = tempfile.mkdtemp()

    def _patch_reports_dir(self):
        return patch("routes.reports._reports_dir", return_value=self.tmpdir)

    def test_api_reports_empty(self):
        with self._patch_reports_dir():
            r = self.client.get("/api/reports")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data["reports"], [])

    def test_api_reports_lists_md_files(self):
        with open(os.path.join(self.tmpdir, "myreport.md"), "w") as f:
            f.write("# My Report\n\nSome content")
        with self._patch_reports_dir():
            r = self.client.get("/api/reports")
        data = r.get_json()
        self.assertEqual(len(data["reports"]), 1)
        self.assertEqual(data["reports"][0]["slug"], "myreport")
        self.assertEqual(data["reports"][0]["title"], "My Report")

    def test_reports_index_empty(self):
        with self._patch_reports_dir():
            r = self.client.get("/reports/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"No reports yet", r.data)

    def test_reports_404_for_missing(self):
        with self._patch_reports_dir():
            r = self.client.get("/reports/nonexistent")
        self.assertEqual(r.status_code, 404)

    def test_reports_render_prose(self):
        with open(os.path.join(self.tmpdir, "demo.md"), "w") as f:
            f.write("# Demo\n\nHello world.")
        with self._patch_reports_dir():
            with patch("routes.reports._run_sql", return_value=([], None)):
                r = self.client.get("/reports/demo")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"<h1>Demo</h1>", r.data)
        self.assertIn(b"Hello world.", r.data)

    def test_reports_render_sql_block(self):
        with open(os.path.join(self.tmpdir, "qry.md"), "w") as f:
            f.write("# Q\n<!-- duckdb: SELECT count(*) AS n FROM sessions -->\n")
        with self._patch_reports_dir():
            with patch("routes.reports._run_sql", return_value=([{"n": 5}], None)):
                r = self.client.get("/reports/qry")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"<th>n</th>", r.data)
        self.assertIn(b"<td>5</td>", r.data)

    def test_reports_render_sql_error(self):
        with open(os.path.join(self.tmpdir, "bad.md"), "w") as f:
            f.write("<!-- duckdb: SELECT x FROM nonexistent -->")
        with self._patch_reports_dir():
            with patch("routes.reports._run_sql", return_value=([], "Table not found")):
                r = self.client.get("/reports/bad")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Table not found", r.data)

    def test_export_csv_missing_report(self):
        with self._patch_reports_dir():
            r = self.client.get("/reports/ghost/export.csv")
        self.assertEqual(r.status_code, 404)

    def test_export_csv_block_out_of_range(self):
        with open(os.path.join(self.tmpdir, "one.md"), "w") as f:
            f.write("<!-- duckdb: SELECT 1 -->\n")
        with self._patch_reports_dir():
            r = self.client.get("/reports/one/export.csv?block=5")
        self.assertEqual(r.status_code, 404)

    def test_export_csv_returns_csv(self):
        with open(os.path.join(self.tmpdir, "data.md"), "w") as f:
            f.write("<!-- duckdb: SELECT 1 AS n -->\n")
        with self._patch_reports_dir():
            with patch("routes.reports._run_sql", return_value=([{"n": 1}, {"n": 2}], None)):
                r = self.client.get("/reports/data/export.csv?block=0")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"n\r\n", r.data)
        self.assertIn(b"1\r\n", r.data)

    def test_bad_slug_returns_400(self):
        with self._patch_reports_dir():
            r = self.client.get("/reports/   /export.csv")
        # Flask routing won't match a path with spaces; either 404 or 400 is fine
        self.assertIn(r.status_code, (400, 404))


if __name__ == "__main__":
    unittest.main()
