def request_approval(action: str, details: str) -> dict:
    """
    Ask the human to approve a potentially modifying action.
    """

    print("\n" + "=" * 60)
    print("ACTION REQUIRES APPROVAL")
    print("=" * 60)

    print(f"\nAction: {action}")
    print(f"Details: {details}")

    answer = input("\nApprove this action? [y/N]: ").strip().lower()

    approved = answer in {"y", "yes"}

    if approved:
        print("\nApproved.\n")
    else:
        print("\nAction cancelled.\n")

    return {
        "approved": approved,
        "action": action,
    }