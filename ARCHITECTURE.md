# Agent Architecture

## High-level flow

    User phone/browser
          |
          v
       FastAPI
          |
          v
     AgentRuntime
       |       |
       |       +---- tool calls
       |                |
       v                v
    OpenRouter       VPS tools
       |             /  |  \
       |           Git Docker Files
       |                |
       +<---------------+
          tool results
              |
              v
          final answer

## AI boundary

The LLM is the reasoning and planning layer. It does not directly execute shell commands, edit files, or restart containers.

The application:
1. receives the model's structured tool call
2. validates the tool name and arguments
3. executes the local Python function
4. trims/redacts results
5. returns the result to the model

The loop supports multiple tool calls and stops when the model returns a final response.

## Project discovery

`discover_projects` scans configured `AGENT_WORKSPACE_ROOTS` for Git repositories up to a bounded depth. This gives the agent a current project inventory without hardcoding the user's repository list.

## Trust boundaries

The local application is the security boundary. Known credential/key files are blocked, common secrets are redacted, paths are resolved, and write-capable operations are not exposed as unrestricted model tools.

## Coding workflow

A coding request should normally become:

1. focused investigation
2. source/config inspection
3. diagnosis
4. exact proposal with old_text/new_text
5. human approval
6. SHA-256 snapshot check
7. exact application
8. timestamped backup
9. verification
10. report

Remote approval is handled by authenticated API endpoints rather than terminal stdin, so the agent can be operated from a phone.

## Infrastructure actions

Container restart is also outside the model's unrestricted tool set. The user explicitly approves the action through the authenticated API.

Future controlled actions such as deploy, rollback, branch creation, and service configuration should follow the same pattern.

## Design principle

The model should be able to reason broadly, but execution should remain narrow. Every new tool should have a clear capability, bounded inputs, redacted outputs where needed, and an explicit approval path for side effects.
