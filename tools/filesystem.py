from tools.safety import is_sensitive_path, redact_text, resolve_path


def list_directory(path: str = ".") -> dict:
    """List files and directories at a path. Read-only."""

    target = resolve_path(path)

    if is_sensitive_path(target):
        return {
            "success": False,
            "error": "Listing sensitive credential/key directories or files is not allowed.",
        }

    if not target.exists():
        return {"success": False, "error": f"Path does not exist: {target}"}

    if not target.is_dir():
        return {"success": False, "error": f"Path is not a directory: {target}"}

    items = []
    for item in sorted(target.iterdir()):
        if is_sensitive_path(item):
            items.append({
                "name": item.name,
                "type": "file" if item.is_file() else "directory",
                "filtered": True,
            })
            continue

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
    """Read a text file while blocking known secret files and redacting common secrets."""

    target = resolve_path(path)

    if is_sensitive_path(target):
        return {
            "success": False,
            "error": "Reading sensitive credential/key files is not allowed.",
        }

    if not target.exists():
        return {"success": False, "error": f"File does not exist: {target}"}

    if not target.is_file():
        return {"success": False, "error": f"Path is not a file: {target}"}

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        return {
            "success": True,
            "path": str(target),
            "content": redact_text(content),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
