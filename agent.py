from model import create_chat, send_message

from tools.system import get_system_info
from tools.filesystem import list_directory, read_text_file
from tools.shell import run_command
from tools.docker import (
    list_containers,
    get_container_logs,
    inspect_container,
    get_container_stats,
)
from tools.investigation import investigate_project, investigate_container
from tools.git import git_status, git_branch, git_log, git_diff
from tools.memory import save_memory, search_memory, list_memories
from tools.actions import restart_container
from tools.project import inspect_project
from tools.tracing import trace_tool
from tools.coding import find_source_files
from tools.proposals import create_fix_proposal
from tools.proposal_executor import (
    show_proposal,
    approve_proposal,
    create_edit_from_proposal,
    apply_approved_proposal,
)
from tools.verification import detect_project_type, verify_python_project


TOOLS = [
    trace_tool(get_system_info),
    trace_tool(list_directory),
    trace_tool(read_text_file),
    trace_tool(run_command),

    trace_tool(list_containers),
    trace_tool(get_container_logs),
    trace_tool(inspect_container),
    trace_tool(get_container_stats),
    trace_tool(investigate_container),

    trace_tool(git_status),
    trace_tool(git_branch),
    trace_tool(git_log),
    trace_tool(git_diff),
    trace_tool(investigate_project),

    trace_tool(save_memory),
    trace_tool(search_memory),
    trace_tool(list_memories),

    trace_tool(restart_container),

    trace_tool(inspect_project),
    trace_tool(find_source_files),
    trace_tool(detect_project_type),
    trace_tool(verify_python_project),
    trace_tool(create_fix_proposal),

    trace_tool(show_proposal),
    trace_tool(create_edit_from_proposal),
]


def _run_approved_proposal_workflow(user_input: str) -> bool:
    """Handle explicit already-approved proposal requests without Gemini."""
    import re

    lowered = user_input.lower()
    if "approved" not in lowered:
        return False
    if "apply" not in lowered and "complete" not in lowered:
        return False

    match = re.search(
        r"\b(?:proposal|fix proposal)\s+([A-Za-z0-9_-]+)",
        user_input,
        re.IGNORECASE,
    )
    if not match:
        return False

    proposal_id = match.group(1)

    print(f"\n[LOCAL WORKFLOW] Applying approved proposal {proposal_id}...")
    result = apply_approved_proposal(proposal_id)

    if not result.get("success"):
        print(
            f"\nAI: Approved proposal workflow failed: "
            f"{result.get('error', 'Unknown error')}\n"
        )
        return True

    print(f"\nAI: Approved proposal {proposal_id} was applied successfully.")

    if result.get("verification_required"):
        project = result.get("project")
        if project:
            print("\n[LOCAL WORKFLOW] Running required Python verification...")
            verification = verify_python_project(project)
            if verification.get("success"):
                print(
                    f"\nAI: Python syntax verification succeeded for {project}.\n"
                )
            else:
                print(
                    f"\nAI: The edit succeeded, but verification failed: "
                    f"{verification.get('error') or verification.get('message', 'Unknown verification failure')}\n"
                )
        else:
            print(
                "\nAI: Edit succeeded, but no project path was returned "
                "for verification.\n"
            )

    return True


def main():
    chat = create_chat(TOOLS)

    print("AI Agent started.")
    print("Model tools:")
    print("  - get_system_info")
    print("  - list_directory")
    print("  - read_text_file [SECRET FILTERED]")
    print("  - run_command [READ-ONLY]")
    print("  - list_containers")
    print("  - get_container_logs")
    print("  - inspect_container")
    print("  - get_container_stats")
    print("  - investigate_container [READ-ONLY SUMMARY]")
    print("  - git_status")
    print("  - git_branch")
    print("  - git_log")
    print("  - git_diff")
    print("  - investigate_project [READ-ONLY SUMMARY]")
    print("  - save_memory")
    print("  - search_memory")
    print("  - list_memories")
    print("  - restart_container [APPROVAL REQUIRED]")
    print("  - inspect_project")
    print("  - find_source_files")
    print("  - detect_project_type")
    print("  - verify_python_project [APPROVAL REQUIRED]")
    print("  - create_fix_proposal")
    print("  - show_proposal")
    print("  - create_edit_from_proposal [APPROVAL REQUIRED]")
    print()
    print("Human-only proposal approval: use tools.proposal_executor.approve_proposal")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            if _run_approved_proposal_workflow(user_input):
                continue

            response = send_message(chat, user_input)

            if response is None:
                continue

            print(f"\nAI: {response.text}\n")

        except KeyboardInterrupt:
            print("\nInterrupted. Type 'exit' to quit.\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
