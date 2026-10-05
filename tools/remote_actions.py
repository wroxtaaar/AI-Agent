import hashlib
import json
import re
import subprocess
from pathlib import Path

from tools.backup import create_backup
from tools.proposal_executor import load_proposal
from tools.safety import is_sensitive_path


def approve_proposal_remote(proposal_id: str) -> dict:
    result = load_proposal(proposal_id)
    if not result["success"]:
        return result

    proposal_path = Path(result["path"])
    proposal = result["proposal"]

    if proposal.get("status") != "pending":
        return {"success": False, "error": f"Proposal is not pending: {proposal.get('status')}"}

    proposal["status"] = "approved"
    proposal["approved_at"] = __import__("datetime").datetime.now().astimezone().isoformat()
    proposal_path.write_text(json.dumps(proposal, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"success": True, "proposal_id": proposal_id, "status": "approved"}


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def apply_approved_proposal_remote(proposal_id: str) -> dict:
    """Apply an approved exact proposal without interactive stdin."""
    result = load_proposal(proposal_id)
    if not result["success"]:
        return result

    proposal = result["proposal"]
    if proposal.get("status") != "approved":
        return {"success": False, "error": "Proposal must be approved first."}

    project = Path(proposal["project"]).expanduser().resolve()
    edits = proposal.get("edits") or []
    if len(edits) != 1:
        return {"success": False, "error": "Remote apply currently requires exactly one edit."}

    edit = edits[0]
    file_entry = edit.get("file")
    old_text = edit.get("old_text")
    new_text = edit.get("new_text")

    if not all(isinstance(value, str) for value in (file_entry, old_text, new_text)):
        return {"success": False, "error": "Proposal edit is incomplete."}

    target = (project / file_entry).resolve()
    try:
        target.relative_to(project)
    except ValueError:
        return {"success": False, "error": "Edit target is outside the project."}

    if is_sensitive_path(target) or not target.is_file():
        return {"success": False, "error": "Edit target is invalid or sensitive."}

    expected_hash = proposal.get("file_hashes", {}).get(file_entry)
    actual_hash = _sha256(target)
    if expected_hash and actual_hash != expected_hash:
        return {"success": False, "error": "Target changed after proposal creation. Create a new proposal."}

    content = target.read_text(encoding="utf-8", errors="replace")
    if content.count(old_text) != 1:
        return {"success": False, "error": "Approved old_text is not present exactly once."}

    backup = create_backup(str(target))
    if not backup.get("success"):
        return {"success": False, "error": "Backup failed; no edit was made.", "backup": backup}

    target.write_text(content.replace(old_text, new_text), encoding="utf-8")
    proposal["status"] = "applied"
    proposal["applied_at"] = __import__("datetime").datetime.now().astimezone().isoformat()
    proposal["backup"] = backup.get("backup")
    Path(result["path"]).write_text(json.dumps(proposal, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "success": True,
        "proposal_id": proposal_id,
        "project": str(project),
        "file": file_entry,
        "backup": backup.get("backup"),
        "verification_required": True,
    }


def restart_container_remote(container: str) -> dict:
    if not container or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", container.strip()):
        return {"success": False, "error": "Invalid Docker container name."}

    name = container.strip()
    result = subprocess.run(
        ["docker", "restart", name],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return {
        "success": result.returncode == 0,
        "container": name,
        "return_code": result.returncode,
        "stdout": result.stdout[-5000:],
        "stderr": result.stderr[-5000:],
    }
