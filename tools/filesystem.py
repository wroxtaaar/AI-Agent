import re
from pathlib import Path


SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".git-credentials",
    "credentials",
    "credentials.json",
    "secrets.json",
    "secret.json",
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
}


def _is_sensitive_path(target: Path) -> bool:
    name = target.name.lower()

    if name in SENSITIVE_NAMES:
        return True

    if name.endswith((".pem", ".key", ".p12", ".pfx", ".jks")):
        return True

    sensitive_parts = {".ssh", ".aws", ".gnupg"}
    return any(part.lower() in sensitive_parts for part in target.parts)


def _redact_sensitive_content(content: str) -> str:
    patterns = [
        (
            r"(?im)^([ 	]*(?:export[ 	]+)?[A-Z0-9_]*(?:API[_-]?KEY|TOKEN|PASSWORD|SECRET|PRIVATE[_-]?KEY)[A-Z0-9_]*[ 	]*=[ 	]*)(.+)$",
            r"\1[REDACTED]",
        ),
        (
            r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+",
            r"\1[REDACTED]",
        ),
        (
            r"(?i)(-----BEGIN [A-Z ]*PRIVATE KEY-----).*?(-----END [A-Z ]*PRIVATE KEY-----)",
            r"\1[REDACTED]\2",
        ),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL if "PRIVATE KEY" in pattern else re.MULTILINE)

    return content


def list_directory(path: str = ".") -> dict:
    """List files and directories at a path. Read-only."""

    target = Path(path).expanduser().resolve()

    if not target.exists():
        return {"success": False, "error": f"Path does not exist: {target}"}

    if not target.is_dir():
        return {"success": False, "error": f"Path is not a directory: {target}"}

    items = []
    for item in sorted(target.iterdir()):
        items.append({
            "name": item.name,
            "type": "directory" if item.is_dir() else "file",
        })

    return {
        "success": True,
        "path": str(target),
        "items": items,
    }


def read_text_file(path: str) -> dict:
    """Read a text file while blocking known secret files and redacting common secrets."""

    target = Path(path).expanduser().resolve()

    if _is_sensitive_path(target):
        return {
            "success": False,
            "error": "Reading sensitive credential/key files is not allowed.",
        }

    if not target.exists():
        return {"success": False, "error": f"File does not exist: {target}"}

    if not target.is_file():
        return {"success": False, "error": f"Path is not a file: {target}"}

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        return {
            "success": True,
            "path": str(target),
            "content": _redact_sensitive_content(content),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
