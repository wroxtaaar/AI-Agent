# Oracle VPS AI Agent

A self-hosted DevOps and coding agent designed to run directly on an Oracle VPS.

The agent uses Gemini for reasoning and tool selection, while local Python code enforces the safety boundary around filesystem edits, shell commands, Docker actions, proposals, backups, and verification.

## What it is

This is not an unrestricted shell chatbot.

The intended workflow is:

1. Investigate — gather a focused, read-only snapshot of the relevant project or service.
2. Inspect — read only the additional files/evidence needed.
3. Diagnose — reason about the evidence.
4. Propose — create an exact coding proposal containing the intended old/new text.
5. Approve — a human explicitly approves the proposal.
6. Apply — the local executor applies only the exact stored edit.
7. Verify — the changed project is verified with a separate human approval.
8. Report — the agent clearly distinguishes proposal, edit, and verification results.

Already-approved proposal requests are routed locally so Gemini cannot reinterpret an approved edit.

## Current capabilities

- System information
- Directory listing
- Secret-filtered text-file reading
- Project structure detection
- Focused project investigation: layout, project type, Git status/branch/diff
- Source-file discovery
- Git status, branch, log, and diff
- Docker container listing, logs, inspect, and non-streaming stats
- Focused container investigation: state, resource snapshot, and redacted recent logs
- Persistent SQLite memory
- Approval-gated Docker restart
- Exact proposal-gated source edits
- Timestamped backups
- Python syntax verification

## Investigation layer

For a known project path, investigate_project gives the model a bounded diagnostic snapshot before it starts opening unrelated files.

For a known Docker container, investigate_container combines:

- container state
- resource usage
- recent logs
- secret redaction

These tools are read-only. They do not replace the underlying tools when a deeper, specific inspection is required.

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

Known credential/key files are blocked. Text returned from normal files is filtered for common API-key, token, password, secret, bearer-token, and private-key patterns. Focused Docker investigation also redacts its returned logs.

## Project direction

The long-term goal is a practical VPS software/DevOps engineer that can investigate failures, understand projects, propose safe changes, verify them, and eventually support controlled deployment workflows without giving the language model unrestricted server access.

## GitHub Actions deployment

The repository has two workflows:

- **Agent Tests** — runs automatically on pushes and pull requests to `master`.
- **Deploy AI Agent** — runs manually from GitHub Actions and deploys to the Oracle VPS only after the same test suite passes.

Configure these GitHub Actions secrets:

    VPS_HOST
    VPS_USER
    VPS_SSH_KEY

The deployment expects the repository at:

    ~/ai-agent

It updates the VPS with:

    git fetch origin master
    git merge --ff-only origin/master

This preserves untracked files on the VPS. It does not overwrite `.env`, runtime data, or unrelated untracked files.

The deployment then updates the Python virtual environment, compiles the source, and runs the full test suite. A failed test stops the deployment.

To deploy manually:

1. Open the repository's **Actions** tab.
2. Select **Deploy AI Agent**.
3. Click **Run workflow**.
4. Select `master`.
5. Wait for the Test job to pass.
6. The Deploy job then connects to the VPS and updates `~/ai-agent`.
