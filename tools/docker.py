import subprocess
from pathlib import Path


def _run_docker(args: list[str]) -> dict:
    try:
        result = subprocess.run(
            ["docker", *args],
            capture_output=True,
            text=True,
            timeout=15,
        )

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout[-10000:],
            "stderr": result.stderr[-5000:],
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Docker command timed out after 15 seconds.",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def list_containers() -> dict:
    """List currently running Docker containers."""

    return _run_docker([
        "ps",
        "--format",
        "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}",
    ])


def _resolve_host_project_path(project: Path) -> tuple[Path | None, dict]:
    """Translate an agent-container /workspace path into the Docker host path."""
    workspace = Path("/workspace").resolve()
    try:
        relative = project.relative_to(workspace)
    except ValueError:
        return None, {"success": True, "translated": False}

    self_result = _run_docker([
        "inspect",
        "--format",
        '{{range .Mounts}}{{.Source}}\t{{.Destination}}{{"\n"}}{{end}}',
        "ai-agent",
    ])
    if not self_result.get("success"):
        return None, {
            "success": False,
            "error": self_result.get("stderr")
            or self_result.get("error")
            or "Unable to inspect the agent container mount.",
        }

    for line in self_result.get("stdout", "").splitlines():
        if "\t" not in line:
            continue
        source, destination = line.split("\t", 1)
        if destination.rstrip("/") == "/workspace":
            return Path(source).resolve() / relative, {
                "success": True,
                "translated": True,
                "workspace_source": str(Path(source).resolve()),
            }

    return None, {
        "success": False,
        "error": "The ai-agent container does not expose a /workspace mount.",
    }


def find_containers_for_project(project_path: str) -> dict:
    """Find Docker containers whose bind mounts reference the supplied project path."""
    if not isinstance(project_path, str) or not project_path.strip():
        return {"success": False, "containers": [], "error": "Project path is required."}

    project = Path(project_path).expanduser().resolve()
    workspace = Path("/workspace").resolve()
    project_name = project.name

    host_project, translation = _resolve_host_project_path(project)
    if project.is_relative_to(workspace) and host_project is None and not translation.get("translated"):
        return {
            "success": False,
            "project": str(project),
            "host_project": None,
            "translation": translation,
            "containers": [],
            "error": translation.get(
                "error",
                "Unable to translate /workspace project path to the Docker host path.",
            ),
        }

    match_project = host_project if host_project is not None else project

    listed = _run_docker([
        "ps",
        "-a",
        "--format",
        "{{.Names}}",
    ])
    if not listed.get("success"):
        return {
            "success": False,
            "project": str(project),
            "host_project": str(host_project) if host_project else None,
            "translation": translation,
            "containers": [],
            "error": listed.get("stderr")
            or listed.get("error", "Docker container listing failed."),
        }

    matches = []
    inspect_failures = []

    for name in [line.strip() for line in listed.get("stdout", "").splitlines() if line.strip()]:
        inspected = _run_docker([
            "inspect",
            "--format",
            '{{range .Mounts}}{{.Type}}\t{{.Source}}\t{{.Destination}}{{"\n"}}{{end}}',
            name,
        ])
        if not inspected.get("success"):
            inspect_failures.append(name)
            continue

        mount_sources = []
        for line in inspected.get("stdout", "").splitlines():
            parts = line.split("\t", 2)
            if len(parts) != 3:
                continue
            mount_type, source, destination = parts
            if mount_type != "bind":
                continue
            mount_sources.append(source)

        if any(
            source == str(match_project)
            or source.startswith(str(match_project) + "/")
            or source == str(project)
            or source.startswith(str(project) + "/")
            or source.endswith("/" + project_name)
            for source in mount_sources
        ):
            matches.append({"name": name, "mounts": mount_sources})

    return {
        "success": True,
        "project": str(project),
        "host_project": str(host_project) if host_project else None,
        "translation": translation,
        "containers": matches,
        "inspect_failures": inspect_failures,
    }


def inspect_container(container: str) -> dict:
    """Inspect Docker container configuration and current state."""
    if not container or not container.strip():
        return {"success": False, "error": "Container name is required."}

    return _run_docker([
        "inspect",
        "--format",
        "Name={{.Name}}\nImage={{.Config.Image}}\nStatus={{.State.Status}}\nStartedAt={{.State.StartedAt}}\nRestartCount={{.RestartCount}}",
        container.strip(),
    ])


def get_container_stats(container: str) -> dict:
    """Read a one-shot Docker resource snapshot without streaming."""
    if not container or not container.strip():
        return {"success": False, "error": "Container name is required."}

    return _run_docker([
        "stats",
        "--no-stream",
        "--format",
        "table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.MemPerc}}\\t{{.NetIO}}\\t{{.BlockIO}}",
        container.strip(),
    ])


def get_container_logs(container: str, lines: int = 100) -> dict:
    """Read recent logs from a Docker container."""

    if not container:
        return {
            "success": False,
            "error": "Container name is required.",
        }

    try:
        lines = max(1, min(int(lines), 500))
    except (TypeError, ValueError):
        lines = 100

    return _run_docker([
        "logs",
        "--tail",
        str(lines),
        container,
    ])