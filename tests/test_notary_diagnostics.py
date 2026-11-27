"""Diagnostic reports cannot expose credentials or enable installer publishing."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("notary_diagnostics", ROOT / ".github/scripts/notary_diagnostics.py")
diagnostic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostic)


class NotaryDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.environment = dict(APPLE_ID="private-owner@example.test", APPLE_TEAM_ID="8LVH596RA5",
            APPLE_APP_SPECIFIC_PASSWORD="private-app-password",
            MACOS_SIGN_IDENTITY="Developer ID Application: Private Name (8LVH596RA5)",
            GITHUB_TOKEN="must-not-reach-notarytool", PATH="/usr/bin:/bin", HOME="/private/runner/home")
        self.secret_text = " ".join(self.environment[name] for name in diagnostic.SECRET_NAMES)

    def assert_sanitized(self, report):
        encoded = json.dumps(report)
        for value in self.environment.values():
            self.assertNotIn(value, encoded)
        self.assertEqual(set(report), {"configuration_complete", "configured_team_matches_expected",
            "configured_team_matches_identity_suffix", "notary_history_accessible", "http_status",
            "submission_count", "classification"})

    def run_response(self, code, stdout=b"", stderr=b""):
        def runner(command, **kwargs):
            self.assertEqual(command[:3], ["xcrun", "notarytool", "history"])
            self.assertNotIn("submit", command)
            self.assertEqual(kwargs["timeout"], 90)
            self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
            self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
            self.assertFalse(set(diagnostic.SECRET_NAMES) & set(kwargs["env"]))
            return subprocess.CompletedProcess(command, code, stdout, stderr)
        result = diagnostic.diagnose(self.environment, runner)
        self.assert_sanitized(result[0])
        return result

    def test_success_reports_only_history_count(self):
        body = json.dumps({"history": [{"name": self.secret_text, "id": self.secret_text}],
                           "message": self.secret_text}).encode()
        report, code = self.run_response(0, body, self.secret_text.encode())
        self.assertEqual(code, 0)
        self.assertTrue(report["notary_history_accessible"])
        self.assertEqual(report["submission_count"], 1)

    def test_agreement_rejection_is_not_a_package_rejection(self):
        error = (self.secret_text + " HTTP status code: 403. A required agreement is missing or has expired.").encode()
        report, code = self.run_response(1, self.secret_text.encode(), error)
        self.assertEqual((code, report["classification"], report["http_status"]), (0, "apple_agreement_gate", 403))
        self.assertFalse(report["notary_history_accessible"])

    def test_other_statuses_are_classified_without_raw_output(self):
        for http, classification in [(401, "authentication_rejected"),
                                      (403, "authorization_rejected"), (503, "notary_request_failed")]:
            with self.subTest(http=http):
                report, code = self.run_response(1, (self.secret_text + f" HTTP status code: {http}").encode())
                self.assertEqual((code, report["classification"]), (0, classification))
                self.assertFalse(report["notary_history_accessible"])

    def test_unexpected_or_oversized_output_never_escapes(self):
        for body in [self.secret_text.encode(), b'[]', b'{"history": "private-app-password"}',
                     b'{"history": ["private-app-password"]}', b'\xff']:
            with self.subTest(body=body):
                report, code = self.run_response(0, body)
                self.assertEqual((code, report["classification"]), (1, "unexpected_response"))
        report, code = self.run_response(0, b"x" * (diagnostic.MAX_RESPONSE_BYTES + 1))
        self.assertEqual((code, report["classification"]), (1, "response_too_large"))

    def test_exception_messages_and_argv_are_not_reported(self):
        for error in [subprocess.TimeoutExpired([self.secret_text], 90, output=self.secret_text.encode()),
                      OSError(self.secret_text), ValueError(self.secret_text)]:
            with self.subTest(kind=type(error).__name__):
                def runner(*args, **kwargs):
                    raise error
                report, code = diagnostic.diagnose(self.environment, runner)
                self.assertEqual(code, 1)
                self.assert_sanitized(report)

    def test_invalid_configuration_makes_no_request(self):
        cases = [dict(APPLE_ID=""), dict(APPLE_TEAM_ID="OTHERTEAM1"),
                 dict(APPLE_TEAM_ID="8LVH596RA5 "), dict(APPLE_ID="bad\0value"),
                 dict(MACOS_SIGN_IDENTITY="Developer ID Application: Other (OTHERTEAM1)")]
        for changes in cases:
            with self.subTest(changes=changes):
                def runner(*args, **kwargs):
                    self.fail("Invalid configuration must not reach Apple")
                report, code = diagnostic.diagnose({**self.environment, **changes}, runner)
                self.assertEqual(code, 1)
                self.assert_sanitized(report)

    def test_diagnostic_dispatch_excludes_all_build_and_publish_jobs(self):
        import yaml
        workflow = yaml.safe_load((ROOT / ".github/workflows/desktop-artifacts.yml").read_text())
        jobs = workflow["jobs"]
        for name in ("macos", "windows", "linux", "release"):
            self.assertIn("inputs.notarization_diagnostics != true", jobs[name]["if"])
        job = jobs["notary-diagnostics"]
        self.assertIn("github.event_name == 'workflow_dispatch'", job["if"])
        self.assertIn("inputs.notarization_diagnostics == true", job["if"])
        self.assertNotIn("env", job)
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        secret_steps = [step for step in job["steps"] if step.get("env")]
        self.assertEqual(len(secret_steps), 1)
        self.assertEqual(set(secret_steps[0]["env"]), set(diagnostic.SECRET_NAMES))
        self.assertIn(".github/scripts/notary_diagnostics.py", secret_steps[0]["run"])


if __name__ == "__main__":
    unittest.main()
