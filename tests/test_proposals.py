import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.actions import restart_container
from tools.proposal_executor import create_edit_from_proposal
from tools.proposals import create_fix_proposal
import tools.proposals as proposals_module
import tools.proposal_executor as executor_module


class ProposalSafetyTests(unittest.TestCase):
    def test_proposal_records_exact_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "example.py"
            source.write_text('def hello():\n    return "hello"\n', encoding="utf-8")

            with patch.object(proposals_module, "PROPOSAL_DIR", root / "proposals"):
                result = create_fix_proposal(
                    project=str(root),
                    problem="Test",
                    explanation="Test",
                    files=["example.py"],
                    proposed_changes="Change hello",
                    edits=[{
                        "file": "example.py",
                        "old_text": 'def hello():\n    return "hello"',
                        "new_text": 'def hello():\n    return "V12"',
                    }],
                )

            self.assertTrue(result["success"])
            proposal_path = Path(result["path"])
            self.assertTrue(proposal_path.exists())
            proposal = proposal_path.read_text(encoding="utf-8")
            self.assertIn('return "V12"', proposal)

    def test_changed_file_is_rejected_after_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "example.py"
            source.write_text('VALUE = "one"\n', encoding="utf-8")

            with patch.object(proposals_module, "PROPOSAL_DIR", root / "proposals"):
                created = create_fix_proposal(
                    project=str(root),
                    problem="Test",
                    explanation="Test",
                    files=["example.py"],
                    proposed_changes="Change value",
                    edits=[{
                        "file": "example.py",
                        "old_text": 'VALUE = "one"',
                        "new_text": 'VALUE = "two"',
                    }],
                )

            proposal_id = created["proposal_id"]
            proposal_path = root / "proposals" / f"proposal_{proposal_id}.json"
            proposal_data = proposal_path.read_text(encoding="utf-8")
            proposal_data = proposal_data.replace('"status": "pending"', '"status": "approved"')
            proposal_path.write_text(proposal_data, encoding="utf-8")

            source.write_text('VALUE = "changed"\n', encoding="utf-8")

            with patch.object(executor_module, "PROPOSAL_DIR", root / "proposals"):
                result = create_edit_from_proposal(
                    proposal_id,
                    str(source),
                    'VALUE = "one"',
                    'VALUE = "two"',
                )

            self.assertFalse(result["success"])
            self.assertIn("changed after", result["error"])


class ActionSafetyTests(unittest.TestCase):
    def test_invalid_container_name_never_reaches_docker(self):
        with patch("tools.actions.subprocess.run") as docker_run:
            result = restart_container("bad/name")
            self.assertFalse(result["success"])
            docker_run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
