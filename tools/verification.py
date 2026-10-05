import subprocess
from pathlib import Path


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


def _find_python_files(root: Path, limit: int = 200) -> list[str]:
    files = []

    for item in root.rglob("*.py"):
        relative = item.relative_to(root)

        if any(part in IGNORE_DIRS for part in relative.parts):
            continue

        files.append(str(relative))

        if len(files) >= limit:
            break

    return sorted(files)


def detect_project_type(path: str = ".") -> dict:
    """
    Detect the basic project type.

    This function is read-only.
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

    markers = []

    if (
        (root / "pyproject.toml").exists()
        or (root / "requirements.txt").exists()
        or (root / "setup.py").exists()
    ):
        markers.append("python")

    if (root / "package.json").exists():
        markers.append("node")

    if (root / "pom.xml").exists():
        markers.append("maven")

    if (
        (root / "build.gradle").exists()
        or (root / "build.gradle.kts").exists()
    ):
        markers.append("gradle")

    if not markers:
        project_type = "unknown"
    elif len(markers) == 1:
        project_type = markers[0]
    else:
        project_type = "mixed"

    return {
        "success": True,
        "project": str(root),
        "project_type": project_type,
        "markers": markers,
    }


def verify_python_project(
    path: str = ".",
) -> dict:
    """
    Run Python syntax verification.

    This executes Python's compiler against project source files.
    Human approval is required.
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

    files = _find_python_files(root)

    if not files:
        return {
            "success": False,
            "error": "No Python source files found.",
        }

    print("\n" + "=" * 70)
    print("⚠️  VERIFICATION REQUIRES APPROVAL")
    print("=" * 70)
    print(f"Project: {root}")
    print("Check: Python syntax compilation")
    print(f"Files: {len(files)}")
    print("=" * 70)

    answer = input(
        "Run verification? [y/N]: "
    ).strip().lower()

    if answer not in {"y", "yes"}:
        return {
            "success": False,
            "approved": False,
            "message": "Verification cancelled.",
        }

    command = [
        "python",
        "-m",
        "py_compile",
        *files,
    ]

    try:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=60,
        )

        return {
            "success": result.returncode == 0,
            "approved": True,
            "project": str(root),
            "verification": "python_syntax",
            "file_count": len(files),
            "return_code": result.returncode,
            "stdout": result.stdout[-10000:],
            "stderr": result.stderr[-10000:],
            "message": (
                "Python syntax verification passed."
                if result.returncode == 0
                else "Python syntax verification failed."
            ),
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "approved": True,
            "project": str(root),
            "verification": "python_syntax",
            "error": "Verification timed out after 60 seconds.",
        }

    except Exception as e:
        return {
            "success": False,
            "approved": True,
            "project": str(root),
            "verification": "python_syntax",
            "error": str(e),
        }
