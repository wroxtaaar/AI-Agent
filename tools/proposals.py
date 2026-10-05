from pathlib import Path
from datetime import datetime
import json


PROPOSAL_DIR = (
    Path(__file__).resolve().parent.parent / "proposals"
)


def create_fix_proposal(
    project: str,
    problem: str,
    explanation: str,
    files: list[str],
    proposed_changes: str,
) -> dict:
    """
    Create a structured coding-fix proposal.

    This tool does NOT modify any source files.
    """

    if not project.strip():
        return {
            "success": False,
            "error": "Project path is required.",
        }

    if not problem.strip():
        return {
            "success": False,
            "error": "Problem description is required.",
        }

    if not proposed_changes.strip():
        return {
            "success": False,
            "error": "Proposed changes are required.",
        }

    if not isinstance(files, list):
        return {
            "success": False,
            "error": "files must be a list.",
        }

    PROPOSAL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    proposal = {
        "created_at": datetime.now().astimezone().isoformat(),
        "project": project,
        "problem": problem,
        "explanation": explanation,
        "files": files,
        "proposed_changes": proposed_changes,
        "status": "pending",
    }

    proposal_path = (
        PROPOSAL_DIR /
        f"proposal_{timestamp}.json"
    )

    try:
        proposal_path.write_text(
            json.dumps(
                proposal,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return {
            "success": True,
            "proposal_id": timestamp,
            "path": str(proposal_path),
            "status": "pending",
            "message": (
                "Fix proposal created. "
                "No source files were modified."
            ),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }

