from pathlib import Path

from tools.backup import create_backup, generate_diff


MAX_FILE_SIZE = 1_000_000


def _read_file(path: str) -> tuple[Path | None, str | None]:
    target = Path(path).expanduser().resolve()

    if not target.exists():
        return None, f"File does not exist: {target}"

    if not target.is_file():
        return None, f"Path is not a file: {target}"

    if target.stat().st_size > MAX_FILE_SIZE:
        return None, "File is too large to edit."

    try:
        content = target.read_text(
            encoding="utf-8",
            errors="replace",
        )
        return target, content
    except Exception as e:
        return None, str(e)


def replace_in_file(
    path: str,
    old_text: str,
    new_text: str,
    project: str | None = None,
) -> dict:
    """Replace exact text after proposal validation and human edit approval."""

    target, content_or_error = _read_file(path)

    if target is None:
        return {"success": False, "error": content_or_error}

    content = content_or_error

    if not old_text:
        return {"success": False, "error": "old_text cannot be empty."}

    occurrences = content.count(old_text)

    if occurrences == 0:
        return {"success": False, "error": "The specified old_text was not found."}

    if occurrences != 1:
        return {
            "success": False,
            "error": f"Expected exactly one occurrence, but found {occurrences}.",
        }

    updated_content = content.replace(old_text, new_text)

    diff_result = generate_diff(str(target), updated_content)
    if not diff_result["success"]:
        return diff_result

    diff = diff_result["diff"]

    print("\n" + "=" * 70)
    print("⚠️  FILE EDIT REQUIRES APPROVAL")
    print("=" * 70)
    print(f"File: {target}")
    print("\n--- PROPOSED DIFF ---")
    print(diff or "No changes detected.")
    print("=" * 70)

    answer = input("Apply this change? [y/N]: ").strip().lower()

    if answer not in {"y", "yes"}:
        return {
            "success": False,
            "approved": False,
            "path": str(target),
            "diff": diff,
            "message": "User denied the edit.",
        }

    backup_result = create_backup(str(target))
    if not backup_result["success"]:
        return {
            "success": False,
            "approved": True,
            "path": str(target),
            "diff": diff,
            "error": "Edit aborted because the backup could not be created.",
            "backup_error": backup_result,
        }

    try:
        target.write_text(updated_content, encoding="utf-8")
        return {
            "success": True,
            "approved": True,
            "path": str(target),
            "backup": backup_result["backup"],
            "diff": diff,
            "verification_required": True,
            "project": project or str(target.parent),
            "message": "File updated successfully. Verification is required.",
        }
    except Exception as e:
        return {
            "success": False,
            "approved": True,
            "path": str(target),
            "backup": backup_result["backup"],
            "error": str(e),
        }
