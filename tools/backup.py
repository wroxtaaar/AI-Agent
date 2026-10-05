from pathlib import Path
from datetime import datetime
import shutil
import difflib


BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"


def create_backup(path: str) -> dict:
    """
    Create a timestamped backup of a file.
    """

    source = Path(path).expanduser().resolve()

    if not source.exists():
        return {
            "success": False,
            "error": f"File does not exist: {source}",
        }

    if not source.is_file():
        return {
            "success": False,
            "error": f"Path is not a file: {source}",
        }

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_name = (
        f"{source.name}.{timestamp}.bak"
    )

    backup_path = BACKUP_DIR / backup_name

    try:
        shutil.copy2(
            source,
            backup_path,
        )

        return {
            "success": True,
            "original": str(source),
            "backup": str(backup_path),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def generate_diff(
    path: str,
    new_content: str,
) -> dict:
    """
    Generate a unified diff between the current
    file contents and proposed new contents.
    """

    source = Path(path).expanduser().resolve()

    if not source.exists():
        return {
            "success": False,
            "error": f"File does not exist: {source}",
        }

    try:
        old_content = source.read_text(
            encoding="utf-8",
            errors="replace",
        )

        old_lines = old_content.splitlines(
            keepends=True
        )

        new_lines = new_content.splitlines(
            keepends=True
        )

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=str(source),
            tofile=f"{source} (proposed)",
        )

        return {
            "success": True,
            "path": str(source),
            "diff": "".join(diff),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }