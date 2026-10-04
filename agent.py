from google.genai import types

from model import create_chat, send_message
from tools.system import get_system_info
from tools.filesystem import list_directory, read_text_file
from tools.shell import run_command
from tools.docker import list_containers, get_container_logs

TOOLS = [
    get_system_info,
    list_directory,
    read_text_file,
    run_command,
    list_containers,
    get_container_logs,
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