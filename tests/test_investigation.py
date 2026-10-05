import unittest
from unittest.mock import patch

from tools.investigation import investigate_container, investigate_project


class InvestigationTests(unittest.TestCase):
    @patch("tools.investigation.git_diff")
    @patch("tools.investigation.git_branch")
    @patch("tools.investigation.git_status")
    @patch("tools.investigation.detect_project_type")
    @patch("tools.investigation.inspect_project")
    def test_project_investigation_is_focused_and_redacted(
        self,
        inspect_project,
        detect_project_type,
        git_status,
        git_branch,
        git_diff,
    ):
        inspect_project.return_value = {
            "success": True,
            "project": "/tmp/demo",
            "file_count": 12,
            "directory_count": 3,
            "important_files": ["README.md", "pyproject.toml"],
        }
        detect_project_type.return_value = {"success": True, "type": "python"}
        git_status.return_value = {
            "success": True,
            "stdout": " M app.py\n",
        }
        git_branch.return_value = {
            "success": True,
            "stdout": "master\n",
        }
        git_diff.return_value = {
            "success": True,
            "stdout": "app.py | 1 +\n",
        }

        result = investigate_project("/tmp/demo")

        self.assertTrue(result["success"])
        self.assertEqual(result["project"], "/tmp/demo")
        self.assertEqual(result["layout"]["important_files"], ["README.md", "pyproject.toml"])
        self.assertEqual(result["git"]["branch"].strip(), "master")
        self.assertIn("M app.py", result["git"]["status"])
        inspect_project.assert_called_once_with("/tmp/demo")

    @patch("tools.investigation.get_container_logs")
    @patch("tools.investigation.get_container_stats")
    @patch("tools.investigation.inspect_container")
    def test_container_investigation_redacts_secrets(
        self,
        inspect_container,
        get_container_stats,
        get_container_logs,
    ):
        inspect_container.return_value = {
            "success": True,
            "stdout": "Status=running\n",
        }
        get_container_stats.return_value = {
            "success": True,
            "stdout": "CPU=1%\n",
        }
        get_container_logs.return_value = {
            "success": True,
            "stdout": "GEMINI_API_KEY=super-secret\nservice started\n",
        }

        result = investigate_container("demo", lines=50)

        self.assertTrue(result["success"])
        self.assertNotIn("super-secret", result["recent_logs"])
        self.assertIn("[REDACTED]", result["recent_logs"])
        get_container_logs.assert_called_once_with("demo", lines=50)


if __name__ == "__main__":
    unittest.main()
