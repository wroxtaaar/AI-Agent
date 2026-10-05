"""Container health check for the AI agent image."""


def main() -> int:
    import agent
    import model

    print("agent import ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
