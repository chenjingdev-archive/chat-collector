---
tracker:
  kind: linear
  api_key: $LINEAR_API_KEY
  project_slug: "__SET_SYMPHONY_LINEAR_PROJECT_SLUG__"
  active_states:
    - Todo
    - In Progress
    - Rework
    - Merging
  terminal_states:
    - Done
    - Closed
    - Cancelled
    - Canceled
    - Duplicate
polling:
  interval_ms: 10000
workspace:
  root: $SYMPHONY_WORKSPACE_ROOT
hooks:
  after_create: |
    set -eu

    rsync -a \
      --exclude .git \
      --exclude .symphony/.env \
      --exclude .symphony/WORKFLOW.md \
      --exclude .symphony/logs \
      --exclude __pycache__ \
      "$SYMPHONY_SOURCE_REPO_PATH"/ ./
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
---

You are working on a Linear issue `{{ issue.identifier }}` in the `chat-collector` repository.

Product intent:
- Local coding agents and IDE assistants store their chats on the local machine.
- This repository exists to collect those chats and turn them into a clean memory source for a future memory system.
- The output should preserve meaningful conversational and memory-relevant content while excluding noisy execution context.
- Collector code belongs in this repository, but collected chat archives must live outside the repo at `/Users/chenjing/dev/chat-history`.
- Do not store real collected chat output inside this repository unless the work is explicitly about fixtures or tests.

Core objective:
- Build collectors that gather local agent chat history from multiple tools and normalize it into clean chat transcripts.
- Exclude irrelevant context such as raw tool calls, MCP invocation noise, internal reasoning traces, and other execution artifacts that do not help memory inference.
- Keep only the sources that are useful for reconstructing meaningful conversational memory.

Repository direction:
- Primary code lives under `src/llm_chat_archive`.
- Each agent family may store chats in different locations and formats.
- Work source-by-source and adapter-by-adapter.
- Prefer clear ownership boundaries per source so implementation can evolve independently.
- Supported and target sources include `codex`, `claude`, `cursor`, `antigravity`, and `gemini`, but the exact quality level may differ by source.

Ticket management posture:
- Treat Linear as an actively maintained work queue, not just a passive tracker.
- If a ticket is too broad, split the remaining work into smaller actionable Linear issues instead of keeping scope implicit.
- If meaningful follow-up work is discovered, create new Linear issues proactively instead of leaving vague notes for later.
- New tickets should include a concrete title, problem statement, scope, and acceptance criteria.
- For unattended overnight execution, create the next immediately actionable follow-up ticket in `Todo` so Symphony can keep pulling work without waiting for a human to reprioritize.
- Use `Backlog` only for lower-confidence ideas, optional future improvements, or work that should not be pulled immediately.
- If a follow-up ticket blocks the current ticket, link it with `blockedBy` and explain the dependency.
- Prefer one ticket per source, parser, cleanup pass, CLI control, or TUI milestone when those concerns can be delivered independently.
- Keep the current ticket focused on one shippable slice, and push adjacent ideas into separate tickets.

Implementation posture:
1. This is an unattended orchestration session. Do not ask a human to perform follow-up actions unless blocked by missing required auth, permissions, or secrets.
2. Start by locating the real on-disk storage path and format for the target source, and record concrete evidence before editing code.
3. Implement collectors one source at a time. If parallelization is available, split work by source or storage format rather than mixing concerns.
4. Treat source-specific collectors as modular components. New collectors should be easy to add without destabilizing existing ones.
5. Normalize outputs around memory usefulness, not raw forensic completeness.
6. Filter out non-memory noise aggressively, but do not throw away user/assistant conversational content that could later support memory inference.
7. Prefer targeted tests, fixtures, and reproducible samples over speculative abstractions.
8. Keep the operator experience practical. This project should be controllable from CLI first, and may grow TUI affordances where they clearly improve recurring memory collection workflows.
9. Design with future recurring collection in mind. The tool should be usable as a component of an automated memory ingestion pipeline.
10. Final response should report completed work and blockers only.
11. For real collection and validation flows, use the external archive target at `/Users/chenjing/dev/chat-history`.
12. When a task naturally decomposes into multiple useful next steps, create the follow-up Linear tickets during the run rather than deferring ticket writing to a human.
13. When operating unattended, keep the queue alive by ensuring there is at least one high-confidence `Todo` follow-up ticket for the next shippable slice, unless the project is blocked or there is no clear next step.

Expected outputs:
- Source discovery notes: storage paths, formats, caveats, and support level.
- Collector implementation per source.
- Clean normalized chat output focused on memory-relevant content, written to `/Users/chenjing/dev/chat-history` for real collection runs.
- Tests or fixtures that prove parsing and filtering behavior.
- Operator-facing controls through CLI, with TUI added only when it materially improves control of recurring collection tasks.
- When appropriate, newly created Linear tickets that capture discovered follow-up work, with immediate next work placed in `Todo`.
