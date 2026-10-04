import subprocess
from pathlib import Path


def _run_git(args: list[str], path: str = ".") -> dict:
    try:
        repo = Path(path).expanduser().resolve()

        if not repo.exists():
            return {
                "success": False,
                "error": f"Path does not exist: {repo}",
            }

        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=15,
        )

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "repository": str(repo),
            "stdout": result.stdout[-10000:],
            "stderr": result.stderr[-5000:],
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Git command timed out after 15 seconds.",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def git_status(path: str = ".") -> dict:
    """Show the current Git status of a repository."""

    return _run_git(
        ["status", "--short", "--branch"],
        path,
    )


def git_branch(path: str = ".") -> dict:
    """Show Git branches."""

    return _run_git(
        ["branch", "--show-current"],
        path,
    )


def git_log(path: str = ".", count: int = 10) -> dict:
    """Show recent Git commits."""

    try:
        count = max(1, min(int(count), 50))
    except (TypeError, ValueError):
        count = 10

    return _run_git(
        [
            "log",
            f"-{count}",
            "--oneline",
            "--decorate",
        ],
        path,
    )


def git_diff(path: str = ".") -> dict:
    """Show unstaged Git changes."""

    return _run_git(
        ["diff", "--stat", "--", "."],
        path,
    )