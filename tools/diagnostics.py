import re
from collections import Counter

from tools.investigation import discover_project_containers, investigate_container, investigate_project
from tools.safety import redact_text


SIGNATURES = [
    ("oom", "critical", re.compile(r"(out of memory|oom killed|oomkill|killed process .* out of memory)", re.I)),
    ("disk_full", "critical", re.compile(r"(no space left on device|disk.*(?:100|full)|filesystem.*full)", re.I)),
    ("permission_denied", "high", re.compile(r"(permission denied|access denied|operation not permitted)", re.I)),
    ("connection_refused", "high", re.compile(r"(connection refused|connect(?:ion)? .*refused|econnrefused)", re.I)),
    ("connection_timeout", "high", re.compile(r"(connection timed out|connect(?:ion)? timeout|read timed out|timed out)", re.I)),
    ("http_502", "high", re.compile(r"(?:\b502\b|bad gateway)", re.I)),
    ("http_503", "high", re.compile(r"(?:\b503\b|service unavailable)", re.I)),
    ("http_504", "high", re.compile(r"(?:\b504\b|gateway timeout)", re.I)),
    ("http_500", "high", re.compile(r"(?:\b500\b|internal server error)", re.I)),
    ("port_conflict", "high", re.compile(r"(address already in use|port is already allocated|bind:.*address already in use)", re.I)),
    ("healthcheck_failed", "medium", re.compile(r"(health.?check.*(?:fail|unhealthy)|unhealthy)", re.I)),
    ("traceback", "high", re.compile(r"traceback \(most recent call last\):", re.I)),
    ("module_not_found", "high", re.compile(r"(modulenotfounderror|cannot find module|no module named)", re.I)),
    ("import_error", "high", re.compile(r"importerror:", re.I)),
    ("syntax_error", "high", re.compile(r"syntaxerror:", re.I)),
    ("database_error", "high", re.compile(r"(database.*(?:error|locked|unavailable)|operationalerror|psycopg.*error|sqlite.*error)", re.I)),
]


def extract_failure_signals(text: str, limit: int = 30) -> dict:
    """Extract common failure signatures from untrusted diagnostic text."""
    if not isinstance(text, str):
        return {"signals": [], "counts": {}, "error": "text must be a string"}

    if not isinstance(limit, int) or not 1 <= limit <= 100:
        return {"signals": [], "counts": {}, "error": "limit must be between 1 and 100"}

    safe_text = redact_text(text, max_length=12000)
    matches = []

    for name, severity, pattern in SIGNATURES:
        match = pattern.search(safe_text)
        if not match:
            continue

        start = max(0, match.start() - 120)
        end = min(len(safe_text), match.end() + 180)
        context = safe_text[start:end].replace("\n", " ").strip()

        matches.append({
            "signature": name,
            "severity": severity,
            "context": context,
        })

    matches = matches[:limit]
    counts = Counter(item["signature"] for item in matches)

    return {
        "signals": matches,
        "counts": dict(counts),
    }


def build_diagnostic_snapshot(
    problem: str,
    project: str = ".",
    container: str = "",
    log_lines: int = 120,
) -> dict:
    """Build a bounded evidence bundle for a reported software failure.

    This is evidence collection and classification only. Gemini remains
    responsible for root-cause reasoning and deciding whether a fix proposal
    is justified.
    """
    if not isinstance(problem, str) or not problem.strip():
        return {"success": False, "error": "A problem description is required."}

    if not isinstance(log_lines, int) or not 1 <= log_lines <= 500:
        return {"success": False, "error": "log_lines must be between 1 and 500."}

    project_result = investigate_project(project)
    if not project_result.get("success"):
        return project_result

    evidence_parts = [
        problem,
        project_result.get("git", {}).get("status", ""),
        project_result.get("git", {}).get("diff_stat", ""),
    ]

    discovery = None
    if container.strip():
        names = [container.strip()]
    else:
        discovery = discover_project_containers(project_result["project"])
        names = [
            item["name"]
            for item in discovery.get("containers", [])
            if item.get("name")
        ][:3]

    if names:
        results = [investigate_container(name, lines=log_lines) for name in names]
        container_result = {
            "success": any(item.get("success") for item in results),
            "containers": results,
            "auto_discovered": not bool(container.strip()),
            "discovery": discovery if not container.strip() else None,
        }
        for result in results:
            if result.get("recent_logs"):
                evidence_parts.append(result["recent_logs"])
            if result.get("inspection"):
                evidence_parts.append(result["inspection"])
    else:
        discovery_failed = bool(discovery and not discovery.get("success"))
        container_result = {
            "success": not discovery_failed,
            "skipped": True,
            "auto_discovered": not bool(container.strip()),
            "discovery": discovery if not container.strip() else None,
            "reason": (
                "Docker container discovery failed; no runtime container evidence was collected."
                if discovery_failed
                else "No related Docker container was found for this project."
            ),
        }

    evidence = "\n".join(str(part) for part in evidence_parts if part)
    signals = extract_failure_signals(evidence)

    return {
        "success": True,
        "problem": redact_text(problem, max_length=2000),
        "project": project_result,
        "container": container_result,
        "failure_signals": signals,
        "next_steps": [
            "Treat signals as observations, not proof of root cause.",
            "Confirm the strongest signal against the relevant source/configuration before proposing a fix.",
            "Read only files directly related to the confirmed failure path.",
            "Create a fix proposal only when the evidence supports an exact source change.",
            "Do not restart or modify services as part of diagnosis.",
        ],
    }
