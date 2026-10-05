import subprocess


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