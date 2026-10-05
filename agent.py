from google.genai import types

from model import create_chat, send_message

from tools.system import get_system_info
from tools.filesystem import list_directory, read_text_file
from tools.shell import run_command
from tools.docker import list_containers, get_container_logs
from tools.git import git_status, git_branch, git_log, git_diff
from tools.memory import save_memory, search_memory, list_memories
from tools.actions import restart_container
from tools.editor import replace_in_file
from tools.project import inspect_project
from tools.tracing import trace_tool
from tools.coding import find_source_files
from tools.proposals import create_fix_proposal
from tools.proposal_executor import (
    show_proposal,
    approve_proposal,
    create_edit_from_proposal,
)
from tools.verification import (
    detect_project_type,
    verify_python_project,
)


TOOLS = [
    trace_tool(get_system_info),
    trace_tool(list_directory),
    trace_tool(read_text_file),
    trace_tool(run_command),

    trace_tool(list_containers),
    trace_tool(get_container_logs),

    trace_tool(git_status),
    trace_tool(git_branch),
    trace_tool(git_log),
    trace_tool(git_diff),

    trace_tool(save_memory),
    trace_tool(search_memory),
    trace_tool(list_memories),

    trace_tool(restart_container),
    trace_tool(replace_in_file),

    trace_tool(inspect_project),
    trace_tool(find_source_files),
    trace_tool(detect_project_type),
    trace_tool(verify_python_project),
    trace_tool(create_fix_proposal),

    trace_tool(show_proposal),
    trace_tool(create_edit_from_proposal),
]




def main():
    chat = create_chat(TOOLS)

    print("AI Agent started.")
    print("Available tools:")
    print("  - get_system_info")
    print("  - list_directory")
    print("  - read_text_file")
    print("  - run_command")
    print("  - list_containers")
    print("  - get_container_logs")
    print("  - git_status")
    print("  - git_branch")
    print("  - git_log")
    print("  - git_diff")
    print("  - save_memory")
    print("  - search_memory")
    print("  - list_memories")
    print("  - restart_container [APPROVAL REQUIRED]")
    print("  - replace_in_file [APPROVAL REQUIRED]")
    print("  - inspect_project")
    print("  - find_source_files")
    print("  - create_fix_proposal")
    print("  - show_proposal")
    print("  - approve_proposal [APPROVAL REQUIRED]")
    print("  - create_edit_from_proposal [APPROVAL REQUIRED]")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            response = send_message(chat, user_input)

            if response is None:
                continue

            print(f"\nAI: {response.text}\n")

        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()