import os
from pathlib import Path

from tools.safety import is_sensitive_path


IGNORE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".gradle", "build", "dist", ".cache",
}


def _roots() -> list[Path]:
    raw = os.getenv("AGENT_WORKSPACE_ROOTS", "/home/ubuntu")
    roots = []
    for item in raw.split(":"):
        if item.strip():
            roots.append(Path(item.strip()).expanduser().resolve())
    return roots


def discover_projects(max_depth: int = 3, limit: int = 100) -> dict:
    """Discover Git repositories in configured VPS workspace roots."""
    try:
        max_depth = max(1, min(int(max_depth), 6))
        limit = max(1, min(int(limit), 200))
    except (TypeError, ValueError):
        max_depth, limit = 3, 100

    projects = []
    seen = set()

    for root in _roots():
        if not root.is_dir() or is_sensitive_path(root):
            continue

        queue = [(root, 0)]
        while queue and len(projects) < limit:
            current, depth = queue.pop(0)
            if current in seen:
                continue
            seen.add(current)

            if (current / ".git").exists() and current != root:
                projects.append({
                    "name": current.name,
                    "path": str(current),
                    "root": str(root),
                })
                continue

            if depth >= max_depth:
                continue

            try:
                children = sorted(current.iterdir())
            except OSError:
                continue

            for child in children:
                if not child.is_dir() or child.name in IGNORE_DIRS:
                    continue
                if is_sensitive_path(child):
                    continue
                queue.append((child, depth + 1))

    return {
        "success": True,
        "roots": [str(root) for root in _roots()],
        "projects": projects,
        "count": len(projects),
    }
