# Agent Architecture

## High-level flow

    User
      |
      v
    agent.py
      |
      +---- explicit approved-proposal request
      |             |
      |             v
      |       local deterministic workflow
      |
      +---- normal request
                    |
                    v
                 Gemini
                    |
                    v
                  Tools
                    |
          +---------+---------+
          |                   |
       Read-only           Approval-gated
          |                   |
          v                   v
   Investigate/Inspect      Propose/Act
          |                   |
          +--------+----------+
                   v
                Verify
                   |
                   v
                 Report

## Investigation layer

The Phase 2 investigation tools are bounded orchestration helpers built from existing read-only primitives.

`investigate_project(path)` gathers project layout, detected project type, Git status, current branch, and diff summary. It is intended as the first diagnostic call when the project path is already known.

`investigate_container(container)` gathers container state, a one-shot resource snapshot, and recent logs. Log output is redacted before it is returned by the summary.

These tools do not gain any new write capability. They reduce unnecessary multi-call discovery while keeping deeper inspection available when needed.

## Trust boundaries

Gemini is responsible for reasoning, choosing tools, interpreting results, and proposing fixes.

The local application is the enforcement layer. It validates path boundaries, sensitive paths, proposal status, SHA-256 snapshots, exact edit contents, human approval, backup creation, and verification approval.

## Coding workflow

A new proposal stores exact edits in the form:

    {
      "file": "relative/path.py",
      "old_text": "...",
      "new_text": "..."
    }

The proposal also stores SHA-256 hashes of relevant files.

When applying:

1. proposal must be approved
2. target must remain inside the approved project
3. target must be listed in the proposal
4. target hash must still match
5. the stored edit must exist exactly once
6. the user sees the generated diff
7. the user approves the edit
8. a backup is created
9. the file is changed
10. verification becomes mandatory

For an explicit already-approved request, the local application reads the stored edit and never asks Gemini to reconstruct it.

## Design principle

The model should be able to reason broadly, but execution should remain narrow.

If a tool can modify state, give it a small explicit capability and put human approval at the local enforcement layer rather than relying on the model to remember the rule.