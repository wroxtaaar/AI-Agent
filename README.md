# Oracle VPS AI Agent

A self-hosted AI control plane for the user's Oracle VPS. It can inspect projects, Docker services, Git repositories, system state, and durable agent memory, then create safe coding proposals. The same runtime is available through a mobile-friendly web UI and a terminal.

## AI

The default AI provider is OpenRouter's OpenAI-compatible API using the free `openrouter/free` router. OpenRouter currently provides free model variants and the free router filters for capabilities such as tool calling. The provider is replaceable through `OPENROUTER_MODEL`.

No AI software is installed on the user's PC. The agent runs on the VPS and calls the cloud model from the VPS.

## Architecture

    Phone / Browser
          |
          v
      FastAPI server
          |
          v
      AgentRuntime
          |
          +---- OpenRouter
          |
          +---- Tool registry
          |       |
          |       +-- VPS/system
          |       +-- Projects/Git
          |       +-- Docker
          |       +-- Files
          |       +-- Memory
          |       +-- Proposals
          |
          +---- Approval API
                  |
                  +-- apply approved coding proposal
                  +-- restart approved container

The model never executes commands itself. It requests a tool call; the local runtime validates and executes the tool, then returns the result to the model.

## Current capabilities

- Authenticated mobile web UI
- OpenRouter tool-calling loop
- VPS system information
- Automatic Git-project discovery under configured workspace roots
- Directory and redacted text-file inspection
- Strict read-only shell commands
- Git status, branch, log, and diff
- Docker container listing, logs, inspect, and resource stats
- Focused project and container investigations
- Persistent SQLite memory
- Exact coding proposals with file snapshots and old/new text
- Remote human approval and exact proposal application
- Timestamped backups before edits
- Container restart through an explicit approval endpoint

## Safety model

The model is the reasoning layer. The VPS application is the enforcement layer.

Read-only operations can be used directly by the model. Source edits and infrastructure actions are not exposed as unrestricted model tools. Coding changes go through:

1. investigate
2. diagnose
3. create exact proposal
4. human approval
5. exact application
6. backup
7. verification

The application checks project boundaries, sensitive paths, file hashes, exact edit contents, and proposal status.

Secrets such as `.env`, private keys, credential files, and common token/password patterns are blocked or redacted.

## Installation on the Oracle VPS

    git clone https://github.com/wroxtaaar/AI-Agent.git
    cd AI-Agent
    ./deploy-agent.sh

The script creates a virtual environment, installs dependencies, and creates `.env` from `.env.example`.

Set:

    OPENROUTER_API_KEY=your_key
    OPENROUTER_MODEL=openrouter/free
    AGENT_API_TOKEN=long_random_token
    AGENT_HOST=0.0.0.0
    AGENT_PORT=8787
    AGENT_WORKSPACE_ROOTS=/home/ubuntu

Never commit `.env`.

## Run

    source .venv/bin/activate
    python run_server.py

Then open:

    http://<your-vps-ip>:8787/

Use the configured `AGENT_API_TOKEN` in the UI.

## Test

    python -m unittest discover -s tests -v

    python -m py_compile agent.py model.py config.py ai_provider.py agent_runtime.py server.py run_server.py tools/*.py

## Project direction

The long-term goal is a practical VPS software/DevOps engineer that can understand all of the user's projects, diagnose failures, make controlled changes, run verification, and eventually support controlled deployments and scheduled monitoring.
