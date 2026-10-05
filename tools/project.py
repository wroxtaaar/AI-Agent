from pathlib import Path


IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".idea",
    ".gradle",
    "build",
    "dist",
}


IMPORTANT_FILES = {
    "README.md",
    "README",
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
}


def inspect_project(path: str = ".") -> dict:
    """
    Inspect a software project without modifying anything.
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
    directories = []
    important_files = []

    try:
        for item in root.rglob("*"):
            relative = item.relative_to(root)

            if any(
                part in IGNORE_DIRS
                for part in relative.parts
            ):
                continue

            if item.is_dir():
                directories.append(str(relative))

            elif item.is_file():
                files.append(str(relative))

                if item.name in IMPORTANT_FILES:
                    important_files.append(str(relative))

        return {
            "success": True,
            "project": str(root),
            "file_count": len(files),
            "directory_count": len(directories),
            "important_files": sorted(important_files),
            "files": sorted(files)[:500],
            "directories": sorted(directories)[:300],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }

