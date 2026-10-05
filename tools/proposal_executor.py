import json
from pathlib import Path

from tools.editor import replace_in_file


PROPOSAL_DIR = (
    Path(__file__).resolve().parent.parent / "proposals"
)


def load_proposal(proposal_id: str) -> dict:
    """Load a proposal by ID."""

    if not proposal_id or not proposal_id.strip():
        return {
            "success": False,
            "error": "Proposal ID is required.",
        }

    proposal_path = (
        PROPOSAL_DIR / f"proposal_{proposal_id}.json"
    )

    if not proposal_path.exists():
        return {
            "success": False,
            "error": f"Proposal not found: {proposal_path}",
        }

    try:
        proposal = json.loads(
            proposal_path.read_text(encoding="utf-8")
        )

        return {
            "success": True,
            "path": str(proposal_path),
            "proposal": proposal,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def show_proposal(proposal_id: str) -> dict:
    """Display a proposal for human review."""

    result = load_proposal(proposal_id)

    if not result["success"]:
        return result

    proposal = result["proposal"]

    print("\n" + "=" * 70)
    print("CODING FIX PROPOSAL")
    print("=" * 70)

    print("\nProject:")
    print(proposal["project"])

    print("\nProblem:")
    print(proposal["problem"])

    print("\nExplanation:")
    print(proposal["explanation"])

    print("\nFiles:")
    for file in proposal["files"]:
        print(f"  - {file}")

    print("\nProposed changes:")
    print(proposal["proposed_changes"])

    print("=" * 70)

    return {
        "success": True,
        "proposal_id": proposal_id,
        "status": proposal.get("status"),
        "message": "Proposal displayed for review.",
    }


def approve_proposal(proposal_id: str) -> dict:
    """Mark a pending proposal as approved."""

    result = load_proposal(proposal_id)

    if not result["success"]:
        return result

    proposal_path = Path(result["path"])
    proposal = result["proposal"]

    if proposal.get("status") != "pending":
        return {
            "success": False,
            "error": (
                f"Proposal is not pending. "
                f"Current status: {proposal.get('status')}"
            ),
        }

    answer = input(
        "\nApprove this coding proposal? [y/N]: "
    ).strip().lower()

    if answer not in {"y", "yes"}:
        return {
            "success": False,
            "approved": False,
            "status": "rejected",
            "message": "Proposal rejected.",
        }

    proposal["status"] = "approved"

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
        "approved": True,
        "status": "approved",
        "proposal_id": proposal_id,
    }


def create_edit_from_proposal(
    proposal_id: str,
    file_path: str,
    old_text: str,
    new_text: str,
) -> dict:
    """
    Convert an approved proposal into an exact file edit.

    Safety checks:
    1. Proposal must be approved.
    2. Target must be inside the approved project.
    3. Target must be explicitly listed in the proposal.
    4. The editor requires human approval.
    5. The editor creates a backup before writing.
    """

    result = load_proposal(proposal_id)

    if not result["success"]:
        return result

    proposal = result["proposal"]

    if proposal.get("status") != "approved":
        return {
            "success": False,
            "error": (
                "Proposal must be approved before "
                "creating an edit."
            ),
        }

    project = (
        Path(proposal["project"])
        .expanduser()
        .resolve()
    )

    target = (
        Path(file_path)
        .expanduser()
        .resolve()
    )

    # Security boundary #1:
    # Target must remain inside the approved project.
    try:
        target.relative_to(project)
    except ValueError:
        return {
            "success": False,
            "error": (
                "Edit target must be inside "
                "the approved project."
            ),
        }

    # Security boundary #2:
    # Target must be explicitly listed in the proposal.
    approved_files = proposal.get("files", [])

    if not isinstance(approved_files, list):
        return {
            "success": False,
            "error": (
                "Proposal contains an invalid "
                "'files' list."
            ),
        }

    approved_targets = set()

    for file_entry in approved_files:
        if not isinstance(file_entry, str):
            continue

        try:
            approved_target = (
                project / file_entry
            ).resolve()

            approved_target.relative_to(project)

            approved_targets.add(approved_target)

        except (ValueError, TypeError):
            continue

    if target not in approved_targets:
        return {
            "success": False,
            "error": (
                "Edit target is not listed in "
                "the approved proposal."
            ),
        }

    return replace_in_file(
        str(target),
        old_text,
        new_text,
        project=str(project),
    )
