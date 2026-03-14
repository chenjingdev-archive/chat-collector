# Codex CLI Local Transcript Artifacts

Updated: `2026-03-14`

Scope: local artifact reconnaissance for `Codex` in `cli` execution context on macOS. This note stops at storage-path and format identification. It does not implement a collector or parser.

## High-Signal Summary

- Primary observed per-user root: `~/.codex/`
- Primary transcript candidate: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`
- Archived transcript candidate: `~/.codex/archived_sessions/rollout-*.jsonl`
- Companion indexes: `~/.codex/session_index.jsonl`, `~/.codex/history.jsonl`
- Shared storage evidence: the same `~/.codex` root contains threads whose recorded originators include CLI, VS Code, Desktop, exec, and subagent flows
- Repo-local result: no repo-local `.codex/` directory or breadcrumb-like file was found under `/Users/chenjing/dev/chat-collector` or `/Users/chenjing/code/workspaces/chat-collector/CHE-50`

## Observed macOS Roots

- `~/.codex/sessions/`
  - Observed `843` active `*.jsonl` files
  - Path pattern: `~/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<thread-id>.jsonl`
- `~/.codex/archived_sessions/`
  - Observed `22` archived `*.jsonl` files
  - Same JSONL rollout pattern as active sessions
- `~/.codex/session_index.jsonl`
  - Observed `140` JSONL rows
  - Row shape: `id`, `thread_name`, `updated_at`
  - Fast thread index, not full transcript
- `~/.codex/history.jsonl`
  - Observed `1,432` JSONL rows
  - Row shape: `session_id`, `ts`, `text`
  - Looks like prompt or command history, not a clean bidirectional conversation log
- `~/.codex/state_5.sqlite`
  - Thread registry and metadata cache
  - `threads` table includes `id`, `rollout_path`, `source`, `model_provider`, `cwd`, `title`, `sandbox_policy`, `approval_mode`, `git_sha`, `git_branch`, `git_origin_url`, `cli_version`, `first_user_message`, `agent_nickname`, `agent_role`, `memory_mode`
  - `thread_dynamic_tools` table stores per-thread dynamic tool schemas
  - Observed `853` total threads, with `405` rows carrying `git_sha`, `406` carrying `git_branch`, `131` carrying `git_origin_url`, and `22` marked archived
- `~/.codex/logs_1.sqlite`
  - Runtime log table keyed by `thread_id` and `process_uuid`
  - Useful for diagnostics, not for clean memory extraction
- `~/.codex/config.toml`
  - Contains default runtime config, project trust, MCP server setup, feature flags, approval policy default, and enabled or disabled skills
- `~/.codex/auth.json`
  - Sensitive auth state
  - Observed top-level keys include auth mode, refresh timestamp, token container, and API key material
- `~/.codex/.codex-global-state.json`
  - UI and workspace state
  - Observed keys include pinned thread IDs, thread titles, workspace roots, and Electron window state
- `~/.codex/log/`
  - Observed plain-text logs such as `codex-login.log` and `codex-tui.log`
- `~/.codex/shell_snapshots/*.sh`
  - Shell snapshot artifacts
  - Execution noise, not transcript
- `~/.codex/skills/`
  - Skill packages and system skill markers under the same root
- `~/.codex/memories/`
  - Root exists, but no populated files were observed on this machine at inspection time
- `~/.codex/sqlite/codex-dev.db`
  - Automation-related tables: `automations`, `automation_runs`, `inbox_items`
  - `automation_runs` includes `archived_user_message` and `archived_assistant_message`, which may matter for later automation-specific collection

## Session JSONL Structure

Across `865` observed session JSONL files, the primary top-level line types were:

- `session_meta`
- `response_item`
- `event_msg`
- `turn_context`

Observed `session_meta.payload` fields include:

- `id`
- `timestamp`
- `cwd`
- `source`
- `originator`
- `cli_version`
- `model_provider`
- `dynamic_tools`
- `base_instructions`

Observed `response_item.payload.type` categories include:

- `message`
- `reasoning`
- `function_call`
- `function_call_output`
- `custom_tool_call`
- `custom_tool_call_output`
- `web_search_call`
- `tool_search_call`
- `tool_search_output`
- `ghost_snapshot`

Observed `response_item` shapes:

- `message`
  - Keep candidate
  - Carries `role` plus `content[]`
  - Observed content item types: `input_text`, `output_text`, `input_image`
- `function_call`, `function_call_output`
  - Exclude from clean transcript
  - Tool invocation name, arguments, call ID, and raw output
- `custom_tool_call`, `custom_tool_call_output`
  - Exclude from clean transcript
  - Same noise class as tool calls
- `reasoning`
  - Exclude from collector output
  - Contains reasoning summary and encrypted reasoning payload, not memory-safe chat content

Observed `event_msg.payload.type` categories include:

- `user_message`
- `agent_message`
- `agent_reasoning`
- `token_count`
- `task_started`
- `task_complete`
- `turn_aborted`
- `context_compacted`
- `entered_review_mode`
- `exited_review_mode`
- `item_completed`
- `thread_rolled_back`

Observed `turn_context.payload` fields include:

- `cwd`
- `approval_policy`
- `sandbox_policy`
- `model`
- `effort`
- `timezone`
- `current_date`
- `personality`
- `summary`
- `collaboration_mode`

## Collector Notes

- The safest transcript extraction rule is to keep only `response_item` rows whose `payload.type == "message"` and whose `payload.role` is one of `user`, `assistant`, or `developer`.
- `event_msg` rows are lifecycle and accounting metadata. They should not be treated as user-visible transcript lines.
- `response_item` rows with null role were heavily associated with reasoning and tool activity on this machine. They should default to exclusion.
- `function_call`, `function_call_output`, `custom_tool_call`, `custom_tool_call_output`, shell snapshots, runtime logs, and SQLite log rows are execution artifacts, not memory-relevant conversation.
- `turn_context` is useful for provenance, approval mode, cwd, and sandbox attribution, but it is not a transcript message.
- `history.jsonl` is useful as a fallback prompt history source, but it is lossy and should not outrank session rollout JSONL when both are present.

## Approvals, Auth, Skills, Worktree Metadata

- Approval state was observed in two places:
  - `config.toml` default runtime config
  - per-turn `turn_context.payload.approval_policy`
- Observed per-turn approval values included `never`, `on-request`, and `untrusted`
- No standalone approvals database or approvals-specific file was identified under `~/.codex/`
- Auth state exists in `auth.json` and is sensitive
- Skills are stored under `~/.codex/skills/` and also referenced from `config.toml`
- Worktree and repo metadata are present in `state_5.sqlite.threads` via `cwd`, `git_sha`, `git_branch`, and `git_origin_url`

## Shared vs Independent Storage

This machine does not support a CLI-only storage conclusion.

Evidence points to a shared per-user Codex root:

- `session_meta.originator` values observed in session JSONL included `codex_cli_rs`, `codex_vscode`, `Codex Desktop`, `codex_exec`, `symphony-orchestrator`, and `codex_sdk_ts`
- `state_5.sqlite.threads.source` included at least `cli`, `vscode`, `exec`, and serialized subagent source objects
- `.codex-global-state.json` includes Electron-specific UI state, which also suggests non-CLI surfaces participate in the same root

Working conclusion:

- `~/.codex/` is a shared Codex-family root on macOS for multiple execution contexts
- CLI sessions are distinguishable inside shared storage by `source` and `originator`, not by an isolated top-level directory

## Negative Results

- No repo-local `.codex/` directory was found in the operator checkout: `/Users/chenjing/dev/chat-collector`
- No repo-local `.codex/` directory was found in the scratch workspace: `/Users/chenjing/code/workspaces/chat-collector/CHE-50`
- No breadcrumb-like file matched by `*.breadcrumb*` was found in either repo tree
- No dedicated approvals file or approvals table was identified beyond config and per-turn context

## Cross-Platform Note

Only macOS was directly inspected.

- Windows path translation guess, unverified: `%USERPROFILE%\\.codex\\`
- Linux path translation guess, unverified: `$HOME/.codex/`

Do not treat those non-macOS paths as confirmed until they are inspected on real hosts.
