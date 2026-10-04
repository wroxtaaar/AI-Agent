import subprocess


ALLOWED_COMMANDS = {
    "pwd",
    "whoami",
    "uname",
    "df",
    "free",
    "uptime",
    "hostname",
    "ls",
    "git",
    "docker",
}


def run_command(command: str) -> dict:
    """
    Run a safe, allowlisted shell command.

    This tool intentionally does not allow arbitrary shell commands.
    """

    command = command.strip()

    if not command:
        return {
            "success": False,
            "error": "No command provided.",
        }

    parts = command.split()

    if parts[0] not in ALLOWED_COMMANDS:
        return {
            "success": False,
            "error": (
                f"Command '{parts[0]}' is not allowed. "
                f"Allowed commands: {', '.join(sorted(ALLOWED_COMMANDS))}"
            ),
        }

    try:
        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            timeout=15,
        )

        return {
            "success": result.returncode == 0,
            "command": command,
            "return_code": result.returncode,
            "stdout": result.stdout[-10000:],
            "stderr": result.stderr[-5000:],
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 15 seconds.",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
