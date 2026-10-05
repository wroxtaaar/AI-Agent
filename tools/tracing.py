from datetime import datetime
from functools import wraps
import json
import re


TRACE_FILE = "agent_trace.log"


SENSITIVE_KEY_PATTERN = re.compile(
    r"(?:api[_-]?key|token|password|secret|private[_-]?key|authorization|credential)",
    re.IGNORECASE,
)


def _redact(value):
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if SENSITIVE_KEY_PATTERN.search(str(key))
            else _redact(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]

    if isinstance(value, str):
        if len(value) > 2000:
            return value[:2000] + "...[TRUNCATED]"
        return value

    return value


def trace_tool(tool):
    """Log tool name and redacted arguments, never tool results."""

    @wraps(tool)
    def wrapper(*args, **kwargs):
        timestamp = datetime.now().astimezone().isoformat()

        try:
            arguments = _redact({
                "args": args,
                "kwargs": kwargs,
            })
            argument_text = json.dumps(
                arguments,
                default=str,
                ensure_ascii=False,
            )
        except Exception:
            argument_text = "<unable to serialize arguments>"

        line = f"[{timestamp}] [TOOL] {tool.__name__} {argument_text}"
        print(f"\n{line}\n")

        with open(TRACE_FILE, "a", encoding="utf-8") as file:
            file.write(line + "\n")

        return tool(*args, **kwargs)

    return wrapper
