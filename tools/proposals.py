import os
from datetime import datetime
import hashlib
import json
from pathlib import Path

from tools.safety import is_sensitive_path, is_within, resolve_path


PROPOSAL_DIR = Path(os.getenv("AGENT_PROPOSAL_DIR", str(Path(__file__).resolve().parent.parent / "proposals")))


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, ValueError):
        return None


def create_fix_proposal(
    project: str,
    problem: str,
    explanation: str,
    files: list[str],
    proposed_changes: str,
    edits: list[dict],
) -> dict:
    """Create a structured coding-fix proposal without modifying source files.

    edits must contain the exact approved edit for each target file:
    {"file": "relative/path.py", "old_text": "...", "new_text": "..."}
    """

    if not isinstance(project, str) or not project.strip():
        return {"success": False, "error": "Project path is required."}

    if not isinstance(problem, str) or not problem.strip():
        return {"success": False, "error": "Problem description is required."}

    if not isinstance(proposed_changes, str) or not proposed_changes.strip():
        return {"success": False, "error": "Proposed changes are required."}

    if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
        return {"success": False, "error": "files must be a list of strings."}

    if not isinstance(edits, list) or not edits:
        return {
            "success": False,
            "error": "Exact edits are required for a new proposal.",
        }

    project_path = resolve_path(project)
    if not project_path.is_dir():
        return {
            "success": False,
            "error": f"Project directory does not exist: {project_path}",
        }

    file_hashes = {}
    normalized_edits = []

    for edit in edits:
        if not isinstance(edit, dict):
            return {"success": False, "error": "Each edit must be an object."}

        file_entry = edit.get("file")
        old_text = edit.get("old_text")
        new_text = edit.get("new_text")

        if not all(isinstance(value, str) for value in (file_entry, old_text, new_text)):
            return {
                "success": False,
                "error": "Each edit requires string file, old_text, and new_text fields.",
            }

        if file_entry not in files:
            return {
                "success": False,
                "error": f"Edit target is not listed in files: {file_entry}",
            }

        target = (project_path / file_entry).resolve()
        if is_sensitive_path(target):
            return {
                "success": False,
                "error": f"Proposal cannot target sensitive credential/key files: {file_entry}",
            }
        try:
            target.relative_to(project_path)
        except ValueError:
            return {
                "success": False,
                "error": f"Proposal edit is outside the project: {file_entry}",
            }

        if not target.is_file():
            return {
                "success": False,
                "error": f"Proposal edit target does not exist: {file_entry}",
            }

        current = target.read_text(encoding="utf-8", errors="replace")
        if current.count(old_text) != 1:
            return {
                "success": False,
                "error": (
                    f"old_text for {file_entry} must occur exactly once "
                    "in the current file."
                ),
            }

        file_hashes[file_entry] = _file_sha256(target)
        normalized_edits.append({
            "file": file_entry,
            "old_text": old_text,
            "new_text": new_text,
        })

    for file_entry in files:
        if file_entry not in file_hashes:
            target = (project_path / file_entry).resolve()
            if is_sensitive_path(target):
                return {
                    "success": False,
                    "error": f"Proposal cannot include sensitive credential/key files: {file_entry}",
                }
            try:
                target.relative_to(project_path)
            except ValueError:
                return {
                    "success": False,
                    "error": f"Proposal file is outside the project: {file_entry}",
                }

            if not target.is_file():
                return {
                    "success": False,
                    "error": f"Proposal file does not exist: {file_entry}",
                }

            file_hashes[file_entry] = _file_sha256(target)

    PROPOSAL_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    proposal = {
        "created_at": datetime.now().astimezone().isoformat(),
        "project": str(project_path),
        "problem": problem,
        "explanation": explanation,
        "files": files,
        "file_hashes": file_hashes,
        "proposed_changes": proposed_changes,
        "edits": normalized_edits,
        "status": "pending",
    }

    proposal_path = PROPOSAL_DIR / f"proposal_{timestamp}.json"

    try:
        proposal_path.write_text(
            json.dumps(proposal, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return {
            "success": True,
            "proposal_id": timestamp,
            "path": str(proposal_path),
            "status": "pending",
            "message": "Fix proposal created. No source files were modified.",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
