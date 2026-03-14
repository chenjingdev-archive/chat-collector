---
tracker:
  kind: linear
  api_key: $LINEAR_API_KEY
  project_slug: "__SET_SYMPHONY_LINEAR_PROJECT_SLUG__"
  active_states:
    - Todo
    - In Progress
  terminal_states:
    - Done
    - Closed
    - Cancelled
    - Canceled
    - Duplicate
polling:
  interval_ms: 10000
observability:
  dashboard_enabled: true
workspace:
  root: $SYMPHONY_WORKSPACE_ROOT
hooks:
  timeout_ms: 300000
agent:
  max_concurrent_agents: 1
  max_turns: 20
codex:
  command: $CODEX_BIN app-server
  approval_policy: never
  thread_sandbox: workspace-write
  turn_sandbox_policy:
    type: workspaceWrite
    writableRoots:
      - "__SET_SYMPHONY_WORKSPACE_ROOT__"
      - "__SET_CHAT_ARCHIVE_ROOT__"
      - "__SET_LOCAL_REPO_ROOT__"
    readOnlyAccess:
      type: fullAccess
    networkAccess: false
    excludeTmpdirEnvVar: false
    excludeSlashTmp: false
---

You are working on a Linear issue `{{ issue.identifier }}` in the `chat-collector` repository.

{% if attempt %}
Continuation context:

- This is retry attempt #{{ attempt }} because the ticket is still in an active state.
- Resume from the current workspace state instead of restarting from scratch.
- Do not repeat already-completed investigation or validation unless needed for new changes.
- Do not end the turn while the issue remains in an active state unless blocked by missing required auth, permissions, or secrets.
{% endif %}

Issue context:
Identifier: {{ issue.identifier }}
Title: {{ issue.title }}
Current status: {{ issue.state }}
Labels: {{ issue.labels }}
URL: {{ issue.url }}

Description:
{% if issue.description %}
{{ issue.description }}
{% else %}
No description provided.
{% endif %}

Product intent:
- Local coding agents and IDE assistants store their chats on the local machine.
- This repository exists to collect those chats and turn them into a clean memory source for a future memory system.
- Collector code belongs in this repository, but collected chat archives must live outside the repo at `/Users/chenjing/dev/chat-history`.
- Do not store real collected chat output inside this repository unless the work is explicitly about fixtures or tests.
- Normalize outputs around memory usefulness rather than raw forensic completeness.
- Exclude tool calls, MCP invocation noise, internal reasoning traces, and execution artifacts that do not help memory inference.

Repository direction:
- Treat the operator local checkout at `/Users/chenjing/dev/chat-collector` as the intended starting point, even if it is minimal.
- Do not assume missing old files are corruption or something to recover.
- If the repo is sparse, scaffold only the minimum code needed for the current issue.
- Primary code lives under `src/llm_chat_archive`.
- Build collectors source-by-source and adapter-by-adapter.
- Keep source-specific collectors modular so they can evolve independently.
- Supported and target sources include `codex`, `claude`, `cursor`, `antigravity`, and `gemini`, but support level may differ by source.
- Prefer targeted tests, fixtures, and reproducible samples over speculative abstractions.
- CLI is the primary operator interface; add TUI only when it materially improves recurring collection control.

Source of truth and git rules:
- The workspace exists only as a per-issue scratch area for notes and temporary artifacts.
- Write product code changes directly in the operator local checkout at `/Users/chenjing/dev/chat-collector`.
- Use the local checkout as the only canonical source of code during the run.
- Prefer running shell commands from `/Users/chenjing/dev/chat-collector` when inspecting, testing, or editing repository files.
- Never treat old Symphony workspaces, old Linear attachments, or prior recovery artifacts as canonical source unless the current issue explicitly asks for them.
- Keep changes in git when practical, but do not let push, PR, auth, or review plumbing become the main scope unless the issue is explicitly about publication.
- A coding ticket may finish with local commits and clear validation when remote publication is out of scope or unavailable.
- If `/Users/chenjing/dev/chat-collector/.git` is missing, record one concise blocker note and stop instead of inventing recovery work.

Ticket management posture:
- Treat Linear as an active work queue, not a passive tracker.
- Default to finishing the current ticket directly instead of reshaping the queue.
- Create a new Linear issue only when a clearly independent next slice is required and the current ticket cannot reasonably absorb it.
- Keep follow-up creation sparse. Prefer zero new tickets; create at most one immediate `Todo` follow-up when it is truly needed.
- Do not create GitHub, auth, browser, or infrastructure blocker tickets unless the current issue is explicitly about those topics.
- Do not create `Backlog` tickets for vague future ideas during implementation work.

Default posture:
1. This is an unattended orchestration session. Do not ask a human to perform follow-up actions unless blocked by missing required auth, permissions, or secrets.
2. Start every task by determining the current Linear status and following the matching flow below.
3. Keep Linear comments sparse. Use at most one concise progress comment, updating it in place only when starting, blocked, or done.
4. Treat the current issue description as the primary scope boundary. Do not invent adjacent recovery or publication work.
5. Use the scratch workspace only for temporary notes or artifacts, and do repository work directly in `/Users/chenjing/dev/chat-collector`.
6. Reproduce current behavior when it is needed to guide implementation, not as a ritual.
7. Final response must report completed actions, validation, and blockers only.

Status map:
- `Backlog` -> out of scope for active execution. Do not modify.
- `Todo` -> immediately move to `In Progress`, then execute.
- `In Progress` -> implementation actively underway.
- `Done` -> terminal state; no further action.
- `Canceled`, `Cancelled`, `Closed`, `Duplicate` -> terminal state; no further action.
- Any other non-active state -> out of scope. Leave it unchanged unless the issue explicitly asks for it.

Execution flow:
1. Read the current issue state and route using the status map above.
2. If the issue is `Todo`, move it to `In Progress`.
3. Inspect the current repo structure and accept it as the intended baseline.
4. Implement the smallest end-to-end slice that satisfies the issue.
5. When you materially change code, create a local git commit in the workspace so the result can land back in the operator local checkout.
6. Validate the exact behavior you changed with focused commands or tests.
7. For real collection runs and validation output, write archives under `/Users/chenjing/dev/chat-history`, not inside this repo.
8. If you create a progress comment, keep it short and update the same comment in place.
9. When the current issue's acceptance criteria are met, move it to `Done`.

Guardrails:
- Do not treat missing historical code, deleted files, or old workspace artifacts as something to restore unless the issue explicitly says so.
- Do not let GitHub push, PR creation, browser automation, or auth debugging hijack a product implementation ticket.
- Do not expand scope silently; only create a follow-up ticket when it is necessary and clearly bounded.
- Do not touch paths outside the workspace except the external archive target `/Users/chenjing/dev/chat-history` when the task explicitly requires real collection output.
- Do not rewrite or reset the operator local checkout directly from the workspace; only land changes there through normal git fast-forwarding.
- Do not spam Linear comments with logs, transcript dumps, repeated validation output, or large handoff notes.
- If blocked by missing local source data, missing required auth, or missing write permission that the current issue explicitly depends on, write one concise blocker note and stop.

Expected outputs:
- Source discovery notes: storage paths, formats, caveats, and support level.
- Collector implementation per source.
- Clean normalized chat output focused on memory-relevant content, written to `/Users/chenjing/dev/chat-history` for real collection runs.
- Tests or fixtures that prove parsing and filtering behavior.
- Operator-facing CLI controls, with TUI added only when it materially improves recurring collection tasks.
- When truly needed, one small follow-up Linear ticket that directly continues shipped code work.
