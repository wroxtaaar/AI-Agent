import platform
import os


def get_system_info() -> dict:
    """Get basic information about the server running this agent."""

    return {
        "operating_system": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "hostname": platform.node(),
        "python_version": platform.python_version(),
        "current_user": os.getenv("USER", "unknown"),
    }


if __name__ == "__main__":
    print(get_system_info())