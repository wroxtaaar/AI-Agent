import re
from pathlib import Path


SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".env.test",
    ".git-credentials",
    "credentials",
    "credentials.json",
    "secrets.json",
    "secret.json",
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
}

SENSITIVE_EXTENSIONS = {".pem", ".key", ".p12", ".pfx", ".jks"}
SENSITIVE_PARTS = {".ssh", ".aws", ".gnupg"}

SECRET_PATTERNS = [
    (
        re.compile(
            r"(?im)^([ \t]*(?:export[ \t]+)?[A-Z0-9_]*(?:API[_-]?KEY|TOKEN|PASSWORD|SECRET|PRIVATE[_-]?KEY|CLIENT[_-]?SECRET)[A-Z0-9_]*[ \t]*=[ \t]*)(.+)$"
        ),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(
            r"(?is)(-----BEGIN [A-Z ]*PRIVATE KEY-----).*?(-----END [A-Z ]*PRIVATE KEY-----)"
        ),
        r"\1[REDACTED]\2",
    ),
]


def resolve_path(path: str) -> Path:
    return Path(path).expanduser().resolve()


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def is_sensitive_path(path: Path) -> bool:
    target = path.resolve()
    if target.name.lower() in SENSITIVE_NAMES:
        return True
    if target.suffix.lower() in SENSITIVE_EXTENSIONS:
        return True
    return any(part.lower() in SENSITIVE_PARTS for part in target.parts)


def redact_text(content: str, max_length: int | None = None) -> str:
    value = content
    for pattern, replacement in SECRET_PATTERNS:
        value = pattern.sub(replacement, value)

    if max_length is not None and len(value) > max_length:
        return value[:max_length] + "...[TRUNCATED]"
    return value


def require_confirmation(title: str, details: str, prompt: str) -> bool:
    print("\n" + "=" * 70)
    print(f"⚠️  {title}")
    print("=" * 70)
    print(details)
    print("=" * 70)
    answer = input(f"{prompt} [y/N]: ").strip().lower()
    return answer in {"y", "yes"}
