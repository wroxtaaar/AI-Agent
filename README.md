# Oracle VPS AI Agent

A self-hosted DevOps and coding agent designed to run directly on an Oracle VPS.

The agent uses Gemini for reasoning and tool selection, while local Python code enforces the safety boundary around filesystem edits, shell commands, Docker actions, proposals, backups, and verification.

## What it is

This is not an unrestricted shell chatbot.

The intended workflow is:

1. Inspect — read server/project state with read-only tools.
2. Diagnose — reason about the evidence.
3. Propose — create an exact coding proposal containing the intended old/new text.
4. Approve — a human explicitly approves the proposal.
5. Apply — the local executor applies only the exact stored edit.
6. Verify — the changed project is verified with a separate human approval.
7. Report — the agent clearly distinguishes proposal, edit, and verification results.

Already-approved proposal requests are routed locally so Gemini cannot reinterpret an approved edit.

## Current capabilities

- System information
- Directory listing
- Secret-filtered text-file reading
- Project structure detection
- Source-file discovery
- Git status, branch, log, and diff
- Docker container listing, logs, inspect, and non-streaming stats
- Persistent SQLite memory
- Approval-gated Docker restart
- Exact proposal-gated source edits
- Timestamped backups
- Python syntax verification

## Shell safety

The generic shell is intentionally small and read-only.

Allowed commands include:

    pwd
    ls
    find
    whoami
    uname
    hostname
    df
    free
    uptime

It does not provide a generic path to git, docker, python, redirection, pipelines, command substitution, or write-capable find options.

## Installation

    git clone https://github.com/wroxtaaar/AI-Agent.git
    cd AI-Agent
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Create .env:

    GEMINI_API_KEY=your_key_here
    GEMINI_MODEL=gemini-3.8-flash

Never commit .env.

## Run

    source .venv/bin/activate
    python agent.py

## Test

    python -m unittest discover -s tests -v

Syntax/import smoke check:

    python -m py_compile agent.py model.py config.py tools/*.py
    python -c "import model, agent; print('Agent import OK')"

## Safety model

### Read-only tools

Inspection tools do not intentionally modify project state.

### Proposal-gated edits

A coding proposal records:

- project path
- target files
- SHA-256 snapshots
- exact old_text
- exact new_text

The executor refuses to apply an edit if the file changed since proposal creation or if the requested edit differs from the approved edit.

### Human approval

Human confirmation is required before:

- changing source files
- restarting containers
- running verification

### Secrets

Known credential/key files are blocked. Text returned from normal files is filtered for common API-key, token, password, secret, bearer-token, and private-key patterns.

## Project direction

The long-term goal is a practical VPS software/DevOps engineer that can investigate failures, understand projects, propose safe changes, verify them, and eventually support controlled deployment workflows without giving the language model unrestricted server access.
