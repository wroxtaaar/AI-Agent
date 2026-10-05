from functools import wraps
from datetime import datetime
import json


TRACE_FILE = "agent_trace.log"


def trace_tool(tool):
    """
    Wrap a tool so every execution is logged.

    We log the tool name and arguments, but not the tool result.
    This keeps potentially sensitive output such as file contents
    and container logs out of the trace.
    """

    @wraps(tool)
    def wrapper(*args, **kwargs):
        timestamp = datetime.now().astimezone().isoformat()

        try:
            arguments = {
                "args": args,
                "kwargs": kwargs,
            }

            argument_text = json.dumps(
                arguments,
                default=str,
                ensure_ascii=False,
            )

        except Exception:
            argument_text = "<unable to serialize arguments>"

        line = (
            f"[{timestamp}] "
            f"[TOOL] {tool.__name__} "
            f"{argument_text}"
        )

        print(f"\n{line}\n")

        with open(TRACE_FILE, "a", encoding="utf-8") as file:
            file.write(line + "\n")

        return tool(*args, **kwargs)

    return wrapper