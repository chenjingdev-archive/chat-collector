# Claude Code CLI Local Artifacts

Updated: `2026-03-14`

Scope: local artifact reconnaissance for `Claude Code` in `cli` execution context on macOS. This note stops at storage-path and format identification. It does not implement a collector or parser.

## High-Signal Summary

- Primary observed per-user roots: `~/.claude/` and `~/.claude.json`
- Primary transcript candidate: `~/.claude/projects/<encoded-project-path>/<session-uuid>.jsonl`
- Primary companion index: `~/.claude/projects/<encoded-project-path>/sessions-index.json`
- Global auth and project-state candidate: `~/.claude.json`
- Approval and machine-local config candidates: `~/.claude/settings.json` and `~/.claude/settings.local.json`
- Repo-local result in the operator checkout: no `.claude/` directory, no `.claude/commands/`, and no `CLAUDE.md` were found under `/Users/chenjing/dev/chat-collector` or `/Users/chenjing/code/workspaces/chat-collector/CHE-52`
- Shared storage evidence: no separate CLI-only root was found; the same per-user root also carries IDE bridge state, project trust state, MCP state, plugins, and worktree breadcrumbs

## Observed macOS Roots

- `~/.claude/projects/`
  - Observed `9` project directories, `35` session `*.jsonl` files, and `3` `sessions-index.json` files
  - Path pattern: `~/.claude/projects/<encoded-project-path>/<session-uuid>.jsonl`
  - Project directory names are path-derived slugs, and `sessions-index.json.entries[].projectPath` preserves the original path
  - Observed project-local companion directories:
    - `<session-uuid>/subagents/*.jsonl`
    - `<session-uuid>/tool-results/toolu_*.txt`
    - `memory/`
- `~/.claude.json`
  - Global user state and project registry
  - Observed top-level keys include `oauthAccount`, `projects`, `autoConnectIde`, `mcpServers`, `toolUsage`, `skillUsage`, and onboarding or feature-flag caches
  - Observed `projects` map keys were real repo paths such as `/Users/chenjing/dev/chat-collector` and worktree-style paths under `.claude/worktrees/...`
- `~/.claude/settings.json`
  - Observed top-level keys: `enabledPlugins`, `hooks`, `language`, `permissions`
  - `permissions.allow` is the clearest machine-level approval allowlist candidate
- `~/.claude/settings.local.json`
  - Observed top-level key: `permissions`
  - Same `permissions.allow` shape as the global settings file
- `~/.claude/mcp-needs-auth-cache.json`
  - Connector auth-needed timestamp cache
  - Auth-adjacent metadata, not transcript
- `~/.claude/history.jsonl`
  - Observed `144` JSONL rows
  - Row shape: `display`, `pastedContents`, `project`, `sessionId`, `timestamp`
  - Useful as prompt or paste history, not as a full bidirectional transcript
- `~/.claude/debug/*.txt`
  - Observed `152` plain-text debug logs
  - Diagnostics, not clean transcript material
- `~/.claude/session-env/<session-id>/`
  - Observed `127` session-scoped directories and `20` hook-script files
  - Included `sessionstart-hook-*.sh`
- `~/.claude/todos/*.json`
  - Observed `100` JSON files
  - Agent todo or plan state, not transcript
- `~/.claude/file-history/<session-id>/*@vN`
  - Observed `67` files
  - File revision snapshots, not transcript
- `~/.claude/shell-snapshots/*.sh`
  - Observed `5` shell snapshot scripts
  - Execution environment residue, not transcript
- `~/.claude/image-cache/<session-id>/*.png`
  - Observed image sidecars for at least one session
- `~/.claude/tasks/<session-id>/`
  - Observed lock or progress markers such as `.highwatermark` and `.lock`
- `~/.claude/ide/`
  - Root exists, but it was empty at inspection time

## Session JSONL Structure

Across `35` observed main session JSONL files, the primary top-level line types were:

- `progress`
- `assistant`
- `user`
- `system`
- `file-history-snapshot`
- `queue-operation`
- `summary`
- `custom-title`

Observed top-level counts:

- `progress`: `3911`
- `assistant`: `1301`
- `user`: `977`
- `system`: `166`
- `file-history-snapshot`: `148`
- `queue-operation`: `85`

Observed common top-level fields on transcript-bearing rows:

- `sessionId`
- `uuid`
- `timestamp`
- `cwd`
- `gitBranch`
- `isSidechain`
- `userType`
- `slug`
- `parentUuid`
- `message`

Observed `userType` values:

- `external`

Observed `assistant.message` fields include:

- `role`
- `content`
- `id`
- `model`
- `stop_reason`
- `stop_sequence`
- `type`
- `usage`
- optional `container`
- optional `context_management`

Observed `assistant.message.content[]` item types:

- `text`
- `tool_use`
- `thinking`

Observed `assistant.message.stop_reason` values:

- `tool_use`
- `end_turn`
- `stop_sequence`

Observed `user.message.content` storage patterns:

- `str`
  - Observed `207` rows
  - Best candidate for actual human-entered text
- `list`
  - Observed `770` rows
  - Content item types were overwhelmingly execution artifacts

Observed `user.message.content[]` item type patterns:

- `tool_result`
  - Observed `746` rows
  - Execution output wrapped in a `user` role message
- `text`
  - Observed `23` rows
- `image` plus `text`
  - Observed `1` row

Observed `progress.data.type` categories:

- `hook_progress`
- `bash_progress`
- `agent_progress`
- `mcp_progress`
- `waiting_for_task`
- `query_update`
- `search_results_received`

Observed `system.subtype` categories:

- `stop_hook_summary`
- `local_command`
- `turn_duration`
- `compact_boundary`

Observed non-message auxiliary row families:

- `queue-operation`
  - Queue metadata such as enqueue or dequeue events
- `file-history-snapshot`
  - File snapshot payloads keyed by `messageId`
- `summary`
  - Compact summary rows keyed by `leafUuid`

## Subagents And Sidecars

- `subagents/*.jsonl`
  - Observed `25` JSONL files
  - Same broad shape as the main session logs, but with extra `agentId`
  - Observed row counts across those files:
    - `progress`: `1321`
    - `assistant`: `514`
    - `user`: `399`
- `tool-results/toolu_*.txt`
  - Observed `7` plain-text files
  - Sidecar captures of tool output, not conversation
- `memory/`
  - Present in multiple project directories
  - Usually empty on this machine
  - One observed populated example: `~/.claude/projects/-Users-chenjing-dev-webmcp/memory/MEMORY.md`

## Collector Notes

- Do not keep rows only because `message.role` is `user` or `assistant`.
- `user` rows are not clean human turns by default on this machine.
  - The dominant `user` payload shape was `tool_result`, not freeform human text.
- Safest current extraction rule:
  - Keep `user` rows when `message.content` is a string, or a list whose item types are human-facing such as `text` or `image`
  - Keep `assistant` rows only for `message.content[]` items of type `text`
- Exclude these from clean transcript output:
  - `assistant.message.content[]` items of type `tool_use`
  - `assistant.message.content[]` items of type `thinking`
  - `user.message.content[]` items of type `tool_result`
  - top-level `progress` rows
  - top-level `system` rows
  - `queue-operation`
  - `file-history-snapshot`
  - `summary`
  - `custom-title`
  - `tool-results/*.txt`
  - `debug/*.txt`
  - `session-env/`
  - `shell-snapshots/`
  - `file-history/`
  - `todos/`
- `subagents/*.jsonl` look like real subordinate conversation traces, but they should stay separate from the main parent session unless the collector is explicitly asked to merge delegated work.

## Approvals, Auth, Slash Commands, Repo Breadcrumbs

- Approval or trust state was observed in `~/.claude.json.projects[<projectPath>]`
  - Observed keys include `allowedTools`, `hasTrustDialogAccepted`, `hasClaudeMdExternalIncludesApproved`, `enabledMcpjsonServers`, `disabledMcpjsonServers`, and `mcpContextUris`
- Machine-level allowlists were observed in:
  - `~/.claude/settings.json`
  - `~/.claude/settings.local.json`
  - both use `permissions.allow`
- Auth-adjacent state was observed in:
  - `~/.claude.json.oauthAccount`
  - `~/.claude/mcp-needs-auth-cache.json`
- No standalone auth-token database or dedicated approvals database was identified during this inspection
- Repo-local breadcrumb observations:
  - A repo-local `.claude/settings.local.json` was observed in `/Users/chenjing/dev/webmcp/.claude/settings.local.json`
  - `CLAUDE.md` was observed in `/Users/chenjing/dev/memory/openclaw_official/CLAUDE.md`
  - `CLAUDE.md` was observed in `/Users/chenjing/dev/n8n-mcp/CLAUDE.md`
  - No repo-local `.claude/` directory or `CLAUDE.md` was found in `/Users/chenjing/dev/chat-collector`
  - No repo-local `.claude/` directory or `CLAUDE.md` was found in `/Users/chenjing/code/workspaces/chat-collector/CHE-52`
- Slash-command metadata result:
  - No `.claude/commands/` directory was found under `~/.claude/`, `/Users/chenjing/dev`, or `/Users/chenjing/code/workspaces`
  - On this machine, slash-command metadata is therefore unconfirmed and should be treated as a negative result for now

## Shared vs Independent Storage

This machine does not support an isolated CLI-only storage conclusion.

Evidence points to a shared Claude-family per-user root:

- `~/.claude.json` carries both terminal-oriented project state and IDE-related state such as `autoConnectIde`
- `~/.claude/ide/` exists under the same root, even though it was empty at inspection time
- `~/.claude.json.projects` contained worktree-like paths under `.claude/worktrees/...`
- No alternative top-level root such as a separate CLI-only transcript store or IDE-only transcript store was found

Working conclusion:

- `~/.claude/` plus `~/.claude.json` is the shared Claude Code local state root on macOS for this machine
- CLI session transcripts are stored under the shared root rather than under a CLI-only top-level directory
- Any CLI versus IDE distinction is more likely encoded in project state, bridge files, or empty-or-ephemeral sidecar directories than in a separate transcript root

## Negative Results

- No repo-local `.claude/` directory was found in `/Users/chenjing/dev/chat-collector`
- No repo-local `.claude/` directory was found in `/Users/chenjing/code/workspaces/chat-collector/CHE-52`
- No `.claude/commands/` directory was found under the inspected user roots
- No dedicated approvals database or approvals-specific table was identified
- No standalone auth-token file beyond the observed global JSON state and auth-needed cache was identified
- `~/.claude/ide/` existed but was empty at inspection time
- Worktree-like paths recorded in `~/.claude.json.projects` for `chat-collector` and `webmcp` did not currently exist on disk

## Cross-Platform Note

Only macOS was directly inspected.

- Windows path translation guess, unverified: `%USERPROFILE%\\.claude\\` and `%USERPROFILE%\\.claude.json`
- Linux path translation guess, unverified: `$HOME/.claude/` and `$HOME/.claude.json`

Do not treat those non-macOS paths as confirmed until they are inspected on real hosts.
