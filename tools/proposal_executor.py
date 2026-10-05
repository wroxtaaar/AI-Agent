import hashlib
import json
from pathlib import Path

from tools.editor import replace_in_file


PROPOSAL_DIR = Path(__file__).resolve().parent.parent / "proposals"


def load_proposal(proposal_id: str) -> dict:
    if not proposal_id or not proposal_id.strip():
        return {"success": False, "error": "Proposal ID is required."}

    proposal_path = PROPOSAL_DIR / f"proposal_{proposal_id}.json"

    if not proposal_path.exists():
        return {"success": False, "error": f"Proposal not found: {proposal_path}"}

    try:
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
        return {"success": True, "path": str(proposal_path), "proposal": proposal}
    except Exception as e:
        return {"success": False, "error": str(e)}


def show_proposal(proposal_id: str) -> dict:
    result = load_proposal(proposal_id)
    if not result["success"]:
        return result

    proposal = result["proposal"]

    print("\n" + "=" * 70)
    print("CODING FIX PROPOSAL")
    print("=" * 70)
    print(f"\nProject:\n{proposal.get('project')}")
    print(f"\nProblem:\n{proposal.get('problem')}")
    print(f"\nExplanation:\n{proposal.get('explanation')}")
    print("\nFiles:")
    for file_entry in proposal.get("files", []):
        print(f"  - {file_entry}")
    print(f"\nProposed changes:\n{proposal.get('proposed_changes')}")
    print("=" * 70)

    return {
        "success": True,
        "proposal_id": proposal_id,
        "status": proposal.get("status"),
        "message": "Proposal displayed for review.",
    }


def approve_proposal(proposal_id: str) -> dict:
    result = load_proposal(proposal_id)
    if not result["success"]:
        return result

    proposal_path = Path(result["path"])
    proposal = result["proposal"]

    if proposal.get("status") != "pending":
        return {
            "success": False,
            "error": f"Proposal is not pending. Current status: {proposal.get('status')}",
        }

    answer = input("\nApprove this coding proposal? [y/N]: ").strip().lower()
    if answer not in {"y", "yes"}:
        return {
            "success": False,
            "approved": False,
            "status": "rejected",
            "message": "Proposal rejected.",
        }

    proposal["status"] = "approved"
    proposal_path.write_text(
        json.dumps(proposal, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return {
        "success": True,
        "approved": True,
        "status": "approved",
        "proposal_id": proposal_id,
    }


def _current_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, ValueError):
        return None


def create_edit_from_proposal(
    proposal_id: str,
    file_path: str,
    old_text: str,
    new_text: str,
) -> dict:
    """Apply an approved proposal only if its target and snapshot still match."""

    result = load_proposal(proposal_id)
    if not result["success"]:
        return result

    proposal = result["proposal"]

    if proposal.get("status") != "approved":
        return {
            "success": False,
            "error": "Proposal must be approved before creating an edit.",
        }

    project = Path(proposal["project"]).expanduser().resolve()
    target = Path(file_path).expanduser().resolve()

    try:
        target.relative_to(project)
    except ValueError:
        return {
            "success": False,
            "error": "Edit target must be inside the approved project.",
        }

    approved_files = proposal.get("files", [])
    if not isinstance(approved_files, list):
        return {"success": False, "error": "Proposal contains an invalid 'files' list."}

    approved_targets = set()
    for file_entry in approved_files:
        if not isinstance(file_entry, str):
            continue
        try:
            approved_target = (project / file_entry).resolve()
            approved_target.relative_to(project)
            approved_targets.add(approved_target)
        except (ValueError, TypeError):
            continue

    if target not in approved_targets:
        return {
            "success": False,
            "error": "Edit target is not listed in the approved proposal.",
        }

    # New proposals record hashes. Older proposals do not, so they remain
    # usable, but new proposals get stale-file protection.
    expected_hash = proposal.get("file_hashes", {}).get(
        next((f for f in approved_files if (project / f).resolve() == target), ""),
    )

    if expected_hash:
        actual_hash = _current_sha256(target)
        if actual_hash != expected_hash:
            return {
                "success": False,
                "error": "The target file changed after the proposal was created. Create a new proposal.",
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
            }

    return replace_in_file(
        str(target),
        old_text,
        new_text,
        project=str(project),
    )
