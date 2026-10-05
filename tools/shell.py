import subprocess


# Only commands that are inherently read-only are exposed here.
# Git and Docker have dedicated read-only tools and are intentionally
# not available through the generic command runner.
ALLOWED_COMMANDS = {
    "pwd",
    "whoami",
    "uname",
    "df",
    "free",
    "uptime",
    "hostname",
    "ls",
    "find",
}


FORBIDDEN_TOKENS = {
    "-exec",
    "-execdir",
    "-delete",
    "-ok",
    "-okdir",
    "-fls",
    "-fprint",
    "-fprintf",
}


def run_command(command: str) -> dict:
    """Run a strictly read-only, allowlisted command."""

    command = command.strip()

    if not command:
        return {"success": False, "error": "No command provided."}

    # subprocess is already shell=False, but reject shell syntax explicitly
    # so the tool contract is clear and future changes cannot accidentally
    # turn it into a command-injection primitive.
    forbidden_shell = (";", "|", ">", "<", "\\n", "\\r", "`", "$(", "&&", "||")
    if any(token in command for token in forbidden_shell):
        return {
            "success": False,
            "error": "Shell operators and command substitution are not allowed.",
        }

    parts = command.split()
    executable = parts[0]

    if executable not in ALLOWED_COMMANDS:
        return {
            "success": False,
            "error": (
                f"Command '{executable}' is not allowed. "
                f"Allowed commands: {', '.join(sorted(ALLOWED_COMMANDS))}"
            ),
        }

    lowered_parts = {part.lower() for part in parts[1:]}
    dangerous = sorted(lowered_parts & FORBIDDEN_TOKENS)
    if dangerous:
        return {
            "success": False,
            "error": f"Unsafe find options are not allowed: {', '.join(dangerous)}",
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
