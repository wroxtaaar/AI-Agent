from pathlib import Path


SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".kt",
    ".kts",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".h",
    ".cs",
    ".php",
    ".rb",
}


IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".gradle",
    "build",
    "dist",
}


def find_source_files(
    path: str = ".",
    limit: int = 50,
) -> dict:
    """
    Find source-code files in a project.

    Read-only operation.
    """

    root = Path(path).expanduser().resolve()

    if not root.exists():
        return {
            "success": False,
            "error": f"Path does not exist: {root}",
        }

    if not root.is_dir():
        return {
            "success": False,
            "error": f"Path is not a directory: {root}",
        }

    files = []

    try:
        for item in root.rglob("*"):
            if not item.is_file():
                continue

            relative = item.relative_to(root)

            if any(
                part in IGNORE_DIRS
                for part in relative.parts
            ):
                continue

            if item.suffix.lower() in SOURCE_EXTENSIONS:
                files.append(str(relative))

            if len(files) >= limit:
                break

        return {
            "success": True,
            "project": str(root),
            "files": sorted(files),
            "count": len(files),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }

