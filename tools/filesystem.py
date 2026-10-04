from pathlib import Path


def list_directory(path: str = ".") -> dict:
    """
    List files and directories at a path.

    This tool is read-only.
    """

    target = Path(path).expanduser().resolve()

    if not target.exists():
        return {
            "success": False,
            "error": f"Path does not exist: {target}",
        }

    if not target.is_dir():
        return {
            "success": False,
            "error": f"Path is not a directory: {target}",
        }

    items = []

    for item in sorted(target.iterdir()):
        items.append({
            "name": item.name,
            "type": "directory" if item.is_dir() else "file",
        })

    return {
        "success": True,
        "path": str(target),
        "items": items,
    }


def read_text_file(path: str) -> dict:
    """
    Read a text file from the server.

    This tool is read-only.
    """

    target = Path(path).expanduser().resolve()

    if not target.exists():
        return {
            "success": False,
            "error": f"File does not exist: {target}",
        }

    if not target.is_file():
        return {
            "success": False,
            "error": f"Path is not a file: {target}",
        }

    try:
        content = target.read_text(
            encoding="utf-8",
            errors="replace",
        )

        return {
            "success": True,
            "path": str(target),
            "content": content,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }