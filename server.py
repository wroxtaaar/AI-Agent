import os
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from agent_runtime import AgentRuntime, ToolSpec
from ai_provider import AIError, OpenRouterProvider
from tools.coding import find_source_files
from tools.discovery import discover_projects
from tools.docker import get_container_logs, get_container_stats, inspect_container, list_containers
from tools.filesystem import list_directory, read_text_file
from tools.git import git_branch, git_diff, git_log, git_status
from tools.investigation import investigate_container, investigate_project
from tools.memory import save_memory, search_memory
from tools.project import inspect_project
from tools.proposals import create_fix_proposal
from tools.shell import run_command
from tools.system import get_system_info
from tools.verification import detect_project_type


app = FastAPI(title="Oracle VPS AI Agent", version="13.0.0")


def spec(name, description, function, properties=None, required=None):
    return ToolSpec(
        name=name,
        description=description,
        function=function,
        parameters={
            "type": "object",
            "properties": properties or {},
            "required": required or [],
            "additionalProperties": False,
        },
    )


TOOLS = [
    spec("get_system_info", "Get basic VPS system information.", get_system_info),
    spec("discover_projects", "Discover Git repositories under configured VPS workspace roots.", discover_projects,
         {"max_depth": {"type": "integer", "minimum": 1, "maximum": 6},
          "limit": {"type": "integer", "minimum": 1, "maximum": 200}}),
    spec("list_directory", "List a directory without reading secrets.", list_directory,
         {"path": {"type": "string"}}),
    spec("read_text_file", "Read a non-secret text file with secret redaction.", read_text_file,
         {"path": {"type": "string"}}, ["path"]),
    spec("run_command", "Run a strictly read-only allowlisted shell command.", run_command,
         {"command": {"type": "string"}}, ["command"]),
    spec("list_containers", "List running Docker containers.", list_containers),
    spec("get_container_logs", "Read recent Docker logs.", get_container_logs,
         {"container": {"type": "string"}, "lines": {"type": "integer", "minimum": 1, "maximum": 500}},
         ["container"]),
    spec("inspect_container", "Inspect Docker container state.", inspect_container,
         {"container": {"type": "string"}}, ["container"]),
    spec("get_container_stats", "Read one-shot Docker resource usage.", get_container_stats,
         {"container": {"type": "string"}}, ["container"]),
    spec("investigate_container", "Build a focused read-only Docker diagnostic snapshot.", investigate_container,
         {"container": {"type": "string"}, "lines": {"type": "integer", "minimum": 1, "maximum": 200}},
         ["container"]),
    spec("git_status", "Show Git status.", git_status, {"path": {"type": "string"}}),
    spec("git_branch", "Show current Git branch.", git_branch, {"path": {"type": "string"}}),
    spec("git_log", "Show recent Git commits.", git_log,
         {"path": {"type": "string"}, "count": {"type": "integer", "minimum": 1, "maximum": 50}}),
    spec("git_diff", "Show unstaged Git diff statistics.", git_diff, {"path": {"type": "string"}}),
    spec("investigate_project", "Build a focused project diagnostic snapshot.", investigate_project,
         {"path": {"type": "string"}}),
    spec("inspect_project", "Inspect project structure and important files.", inspect_project,
         {"path": {"type": "string"}}),
    spec("find_source_files", "Find source files in a project.", find_source_files,
         {"path": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 200}}),
    spec("detect_project_type", "Detect Python, Node, Maven, Gradle, or mixed project type.", detect_project_type,
         {"path": {"type": "string"}}),
    spec("save_memory", "Save a durable non-secret project fact.", save_memory,
         {"content": {"type": "string"}}, ["content"]),
    spec("search_memory", "Search durable agent memory when prior context is needed.", search_memory,
         {"query": {"type": "string"}}, ["query"]),
    spec("create_fix_proposal", "Create an exact, approval-gated coding proposal. This does not edit files.",
         create_fix_proposal,
         {
             "project": {"type": "string"},
             "problem": {"type": "string"},
             "explanation": {"type": "string"},
             "files": {"type": "array", "items": {"type": "string"}},
             "proposed_changes": {"type": "string"},
             "edits": {"type": "array", "items": {
                 "type": "object",
                 "properties": {
                     "file": {"type": "string"},
                     "old_text": {"type": "string"},
                     "new_text": {"type": "string"},
                 },
                 "required": ["file", "old_text", "new_text"],
                 "additionalProperties": False,
             }},
         },
         ["project", "problem", "explanation", "files", "proposed_changes", "edits"]),
]


runtime = None


def get_runtime():
    global runtime
    if runtime is None:
        runtime = AgentRuntime(TOOLS)
    return runtime


def require_auth(authorization: str | None = Header(default=None)):
    expected = os.getenv("AGENT_API_TOKEN")
    if not expected:
        raise HTTPException(status_code=503, detail="AGENT_API_TOKEN is not configured.")
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized.")
    return True


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    history: list[dict] = Field(default_factory=list, max_length=20)


@app.get("/health")
def health():
    return {"status": "ok", "service": "oracle-vps-ai-agent", "version": app.version}


@app.get("/api/status", dependencies=[Depends(require_auth)])
def status():
    return {
        "system": get_system_info(),
        "projects": discover_projects(limit=100),
        "containers": list_containers(),
        "model": os.getenv("OPENROUTER_MODEL", "openrouter/free"),
    }


@app.post("/api/chat", dependencies=[Depends(require_auth)])
def chat(request: ChatRequest):
    try:
        return get_runtime().run(request.message, request.history)
    except AIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/proposals/{proposal_id}", dependencies=[Depends(require_auth)])
def proposal(proposal_id: str):
    from tools.proposal_executor import load_proposal
    result = load_proposal(proposal_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result["proposal"]


@app.post("/api/proposals/{proposal_id}/approve", dependencies=[Depends(require_auth)])
def approve(proposal_id: str):
    from tools.remote_actions import approve_proposal_remote
    result = approve_proposal_remote(proposal_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.post("/api/proposals/{proposal_id}/apply", dependencies=[Depends(require_auth)])
def apply(proposal_id: str):
    from tools.remote_actions import apply_approved_proposal_remote
    result = apply_approved_proposal_remote(proposal_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.post("/api/actions/restart-container", dependencies=[Depends(require_auth)])
def restart_container(container: str):
    from tools.remote_actions import restart_container_remote
    result = restart_container_remote(container)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(Path(__file__).parent / "web" / "index.html")
