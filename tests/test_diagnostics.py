import unittest
from unittest.mock import patch

from tools.diagnostics import build_diagnostic_snapshot, extract_failure_signals


class DiagnosticTests(unittest.TestCase):
    def test_extracts_common_failure_signatures_and_redacts_secrets(self):
        result = extract_failure_signals(
            "502 Bad Gateway\nTraceback (most recent call last):\n"
            "Connection refused\nGEMINI_API_KEY=super-secret"
        )

        signatures = {item["signature"] for item in result["signals"]}
        self.assertIn("http_502", signatures)
        self.assertIn("traceback", signatures)
        self.assertIn("connection_refused", signatures)

        contexts = " ".join(item["context"] for item in result["signals"])
        self.assertNotIn("super-secret", contexts)
        self.assertIn("[REDACTED]", contexts)

    def test_rejects_invalid_limits(self):
        result = extract_failure_signals("502", limit=0)

        self.assertFalse(result["signals"])
        self.assertIn("between 1 and 100", result["error"])

    @patch("tools.diagnostics.investigate_container")
    @patch("tools.diagnostics.investigate_project")
    def test_builds_bounded_snapshot(
        self,
        investigate_project,
        investigate_container,
    ):
        investigate_project.return_value = {
            "success": True,
            "project": "/tmp/demo",
            "project_type": {"success": True, "type": "python"},
            "layout": {
                "file_count": 4,
                "directory_count": 1,
                "important_files": ["requirements.txt"],
            },
            "git": {
                "status": " M app.py",
                "branch": "master",
                "diff_stat": "app.py | 2 +-\n",
            },
        }
        investigate_container.return_value = {
            "success": True,
            "container": "demo",
            "inspection": "Status=running",
            "stats": "CPU=2%",
            "recent_logs": "502 Bad Gateway\nConnection refused",
        }

        result = build_diagnostic_snapshot(
            problem="API returns 502",
            project="/tmp/demo",
            container="demo",
            log_lines=80,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["project"]["project"], "/tmp/demo")
        self.assertEqual(result["container"]["containers"][0]["container"], "demo")
        signatures = {item["signature"] for item in result["failure_signals"]["signals"]}
        self.assertIn("http_502", signatures)
        self.assertIn("connection_refused", signatures)
        investigate_project.assert_called_once_with("/tmp/demo")
        investigate_container.assert_called_once_with("demo", lines=80)

    def test_requires_problem_description(self):
        result = build_diagnostic_snapshot("")

        self.assertFalse(result["success"])
        self.assertIn("problem description", result["error"].lower())


if __name__ == "__main__":
    unittest.main()
