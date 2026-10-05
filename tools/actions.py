import subprocess


def restart_container(container: str) -> dict:
    """
    Restart a Docker container after explicit human approval.
    """

    if not container or not container.strip():
        return {
            "success": False,
            "error": "Container name is required.",
        }

    container = container.strip()

    print("\n" + "=" * 60)
    print("⚠️  ACTION REQUIRES APPROVAL")
    print("=" * 60)
    print(f"Action: Restart Docker container")
    print(f"Container: {container}")
    print("=" * 60)

    answer = input("Approve this action? [y/N]: ").strip().lower()

    if answer not in {"y", "yes"}:
        print("Action cancelled.\n")

        return {
            "success": False,
            "approved": False,
            "action": "restart_container",
            "container": container,
            "message": "User denied the action.",
        }

    print("Action approved. Restarting container...\n")

    try:
        result = subprocess.run(
            ["docker", "restart", container],
            capture_output=True,
            text=True,
            timeout=30,
        )

        return {
            "success": result.returncode == 0,
            "approved": True,
            "action": "restart_container",
            "container": container,
            "return_code": result.returncode,
            "stdout": result.stdout[-5000:],
            "stderr": result.stderr[-5000:],
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "approved": True,
            "action": "restart_container",
            "container": container,
            "error": "Docker restart timed out after 30 seconds.",
        }

    except Exception as e:
        return {
            "success": False,
            "approved": True,
            "action": "restart_container",
            "container": container,
            "error": str(e),
        }