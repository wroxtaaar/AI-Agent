from server import get_runtime


def main():
    print("Oracle VPS AI Agent started.")
    print("AI: OpenRouter (default: openrouter/free)")
    print("UI: http://<vps-host>:8787/")
    print("Type 'exit' to quit.\n")

    runtime = get_runtime()

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            result = runtime.run(user_input)
            if result.get("success"):
                print(f"\nAI: {result.get('answer', '')}\n")
            else:
                print(f"\nAI: {result.get('answer') or result.get('error', 'Agent failed.')}\n")
        except KeyboardInterrupt:
            print("\nInterrupted. Type 'exit' to quit.\n")
        except Exception as exc:
            print(f"\nError: {exc}\n")


if __name__ == "__main__":
    main()
