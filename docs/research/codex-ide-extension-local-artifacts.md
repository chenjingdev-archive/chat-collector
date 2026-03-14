# Codex IDE Extension Local Transcript Artifacts

Updated: `2026-03-14`

Scope: local artifact reconnaissance for `Codex` in `ide_extension` execution context on macOS. This note stops at storage-path and format identification. It does not implement a collector or parser.

## High-Signal Summary

- Shared Codex-family transcript root: `~/.codex/`
- Strongest IDE-extension discriminator inside shared rollout JSONL: `session_meta.payload.originator == "codex_vscode"`
- Observed `75` rollout JSONL files with `originator == "codex_vscode"` across `~/.codex/sessions/` and `~/.codex/archived_sessions/`
- Primary VS Code host roots:
  - `~/Library/Application Support/Code/User/globalStorage/state.vscdb`
  - `~/Library/Application Support/Code/User/workspaceStorage/<workspace-id>/state.vscdb`
  - `~/Library/Application Support/Code/logs/<timestamp>/window*/exthost/openai.chatgpt/Codex.log`
- Primary Cursor host roots:
  - `~/Library/Application Support/Cursor/User/workspaceStorage/<workspace-id>/state.vscdb`
  - `~/Library/Application Support/Cursor/logs/<timestamp>/window*/exthost/openai.chatgpt/Codex.log`
  - extension install roots under `~/.cursor/extensions/openai.chatgpt-*`
- Bridge payload path is referenced by extension logs as `~/Library/Application Support/com.openai.chat/app_pairing_extensions/<Host>-<uuid>`, but the directory was empty at inspection time
- Negative result: no Windsurf user-data root, logs root, or extension install was observed on this machine
- Working storage conclusion: Codex IDE sessions share canonical transcript storage with other Codex execution contexts under `~/.codex/`, while each editor keeps its own host-side view state, prompt history, and bridge or debug logs

## Observed macOS Roots

### Shared Codex-family Root: `~/.codex/`

- `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`
- `~/.codex/archived_sessions/rollout-*.jsonl`
  - `75` files matched `session_meta.payload.originator == "codex_vscode"`
  - Sample `session_meta.payload` fields observed:
    - `id`
    - `timestamp`
    - `cwd`
    - `originator`
    - `cli_version`
    - `source`
    - `model_provider`
    - `base_instructions`
- `~/.codex/state_5.sqlite`
  - `threads.source == 'vscode'` observed in `213` rows
  - `threads` does not carry `originator`
  - This means `state_5.sqlite` alone cannot cleanly separate IDE-extension sessions from Desktop-originated sessions that also record `source == 'vscode'`

### `codex_vscode` Rollout JSONL Structure

Across the `75` rollout JSONL files with `originator == "codex_vscode"`, observed `response_item.payload.type` counts were:

- `reasoning`: `2,946`
- `function_call`: `2,555`
- `function_call_output`: `2,555`
- `message`: `1,613`
- `custom_tool_call`: `267`
- `custom_tool_call_output`: `267`
- `ghost_snapshot`: `66`
- `web_search_call`: `28`

Observed `message` roles:

- `user`: `885`
- `assistant`: `656`
- `developer`: `72`

Observed `message.content[].type` values:

- `input_text`: `956`
- `output_text`: `656`
- `input_image`: `72`

Observed `event_msg.payload.type` values:

- `token_count`: `6,767`
- `agent_reasoning`: `3,009`
- `user_message`: `670`
- `agent_message`: `656`
- `turn_aborted`: `68`
- `task_started`: `22`
- `task_complete`: `22`
- `context_compacted`: `6`

Observed `turn_context.payload` keys across the `codex_vscode` subset:

- `approval_policy`
- `collaboration_mode`
- `cwd`
- `effort`
- `model`
- `personality`
- `sandbox_policy`
- `summary`
- `truncation_policy`
- `turn_id`
- `user_instructions`

Sample `turn_context` values included:

- `cwd`: `/Users/chenjing`
- `approval_policy`: `never`
- `sandbox_policy`: object with `type`
- `model`: `gpt-5.2-codex`
- `summary`: `auto`

## VS Code Host Storage

### Extension Install Root

- `~/.vscode/extensions/openai.chatgpt-0.4.79-darwin-arm64/package.json`
  - Declares activity-bar container `codexViewContainer`
  - Declares webview `chatgpt.sidebarView`
  - Declares commands such as `chatgpt.addToThread` and `chatgpt.addFileToThread`
  - This is evidence that the extension can hand file or selection context into a thread, but it does not by itself prove durable host-side transcript storage

### Global Storage

- `~/Library/Application Support/Code/User/globalStorage/state.vscdb`
  - Relevant keys observed:
    - `openai.chatgpt`
    - `workbench.view.extension.chatgpt-activitybar.state.hidden`
    - `workbench.view.extension.codexViewContainer.state.hidden`
  - `openai.chatgpt` stored:
    - `persisted-atom-state.codexCloudAccess`
    - `persisted-atom-state.environment`
    - `persisted-atom-state.prompt-history`
    - `thread-titles.order`
    - `thread-titles.titles`
  - Observed `prompt-history` was an array of `10` strings, not a structured bidirectional transcript
  - Observed `thread-titles.order[0]` was a shared Codex thread ID, and it resolved in `~/.codex/state_5.sqlite` to a `source == 'vscode'` thread

### Workspace Storage

- `~/Library/Application Support/Code/User/workspaceStorage/<workspace-id>/state.vscdb`
  - `8` workspace databases on this machine contained `agentSessions.model.cache`
  - One sampled workspace cache contained `50` `openai-codex://route/local/<thread-id>` resources
  - For that sampled cache, the referenced shared-thread sources split into:
    - `22` `vscode`
    - `28` `cli`
  - This means the VS Code host cache mixes shared Codex threads from more than one execution context and should not be used alone to isolate IDE-only sessions
- `~/Library/Application Support/Code/User/workspaceStorage/<workspace-id>/chatSessions/*`
- `~/Library/Application Support/Code/User/workspaceStorage/<workspace-id>/chatEditingSessions/*`
  - These generic VS Code chat and editing-session paths exist on this machine
  - No `openai-codex`, `openai.chatgpt`, or `Codex` markers were observed in those files
  - A sampled `chatSessions/*.jsonl` file belonged to `GitHub Copilot`, not Codex
  - No direct evidence was found that Codex persists diff or selection handoff into these host-managed chat-session files on this machine

### Logs

- `~/Library/Application Support/Code/logs/<timestamp>/window*/exthost/openai.chatgpt/Codex.log`
  - Observed log lines included:
    - `Activating Codex extension`
    - `Spawning codex app-server`
    - `ChatGPT desktop bridge active`
    - `Desktop bridge wrote payload sessionPath=".../app_pairing_extensions/Visual Studio Code-<uuid>"`
    - `Desktop bridge listening on UNIX socket socketPath="/tmp/Visual Studio Code-<uuid>.sock"`
    - warning for `thread-stream-state-changed`
  - This log is useful for bridge and lifecycle diagnostics, not for clean memory extraction

## Cursor Host Storage

### Extension Install Roots

- `~/.cursor/extensions/openai.chatgpt-0.4.69-universal`
- `~/.cursor/extensions/openai.chatgpt-0.4.71-universal`
  - Package manifest matches the VS Code extension shape:
    - `codexViewContainer`
    - `chatgpt.sidebarView`
    - `chatgpt.addToThread`
    - `chatgpt.addFileToThread`

### Global Storage

- `~/Library/Application Support/Cursor/User/globalStorage/`
  - No `openai.chatgpt` directory was observed under the top-level `globalStorage` directory
  - Observed top-level directories were unrelated extensions such as `alefragnani.project-manager`, `mhutchie.git-graph`, and `ms-edgedevtools.vscode-edge-devtools`

### Workspace Storage

- `~/Library/Application Support/Cursor/User/workspaceStorage/<workspace-id>/state.vscdb`
  - `0` workspace databases on this machine exposed `agentSessions.model.cache`
  - Multiple workspace databases stored:
    - `memento/webviewView.chatgpt.sidebarView`
    - `workbench.view.extension.codexViewContainer.state`
    - `workbench.view.extension.codexViewContainer.numberOfVisibleViews`
  - Sample `memento/webviewView.chatgpt.sidebarView` value shape:
    - top-level object with string field `webviewState`
    - decoded inner JSON keys:
      - `codexCloudAccess`
      - `defaultApprovalDecision`
      - `environment`
      - `prompt-history`
      - `reasoning-effort`
  - Sample decoded inner values:
    - `codexCloudAccess`: `enabled`
    - `defaultApprovalDecision`: `approved`
    - `reasoning-effort`: `high`
    - `environment.id`: `6848ddff259881918f77be882f15ea8b`
    - `environment.label`: `chenjingdev/llm-chess`
    - `environment.workspace_dir`: `/workspace`
  - Observed `prompt-history` was an array of strings
  - No `thread-titles` field was observed in the sampled Cursor webview state
- No `chatSessions/` or `chatEditingSessions/` directories were observed anywhere under `~/Library/Application Support/Cursor/User/workspaceStorage/`

### Logs

- `~/Library/Application Support/Cursor/logs/<timestamp>/window*/exthost/openai.chatgpt/Codex.log`
  - Observed log lines included:
    - `Activating Codex extension`
    - `Spawning codex app-server`
    - `ChatGPT desktop bridge active`
    - `Desktop bridge wrote payload to .../app_pairing_extensions/Cursor-<uuid>`
    - `Desktop bridge listening on UNIX socket: /tmp/Cursor-<uuid>.sock`
    - `Codex chat session item provider not registered: lt.chat.registerChatSessionItemProvider is not a function`
  - That missing-provider log line is evidence that Cursor host integration diverges from VS Code host capabilities

## Desktop Bridge Files

- `~/Library/Application Support/com.openai.chat/app_pairing_extensions/`
  - Directory exists
  - `0` files were present at inspection time
  - VS Code and Cursor `Codex.log` files both referenced payload files under this root during activation
- No matching `Visual Studio Code-*.sock`, `Cursor-*.sock`, or `Windsurf-*.sock` UNIX sockets were present under `/tmp` at inspection time

Working conclusion:

- The desktop bridge payload path exists, but the actual payload files appear ephemeral or cleanup-prone on this machine
- No durable JSON, SQLite, or LevelDB artifact under `app_pairing_extensions/` was available to inspect after activation

## Windsurf Negative Results

- `~/Library/Application Support/Windsurf/User/` was not present
- `~/Library/Application Support/Windsurf/logs/` was not present
- `~/.windsurf/extensions/` was not present
- No local Codex extension state was confirmed for Windsurf on this machine

## Collector Notes

- Canonical transcript candidate for the IDE extension remains the shared rollout JSONL under `~/.codex/`, but collection should first restrict to files whose `session_meta.payload.originator == "codex_vscode"`
- Inside those files, the safest memory-oriented extraction rule is still: keep only `response_item` rows where `payload.type == "message"`
- Keep roles `user`, `assistant`, and `developer`
- Treat `reasoning`, `function_call`, `function_call_output`, `custom_tool_call`, `custom_tool_call_output`, `ghost_snapshot`, `web_search_call`, and `event_msg` lifecycle rows as execution noise
- VS Code and Cursor host-side `prompt-history` arrays are useful as fallback breadcrumbs or UX state, but they are lossy and should not outrank shared rollout JSONL
- `state_5.sqlite.threads.source` alone is not enough to isolate IDE-extension sessions, because host-side caches can reference both `cli` and `vscode` threads and Desktop flows can also produce `source == 'vscode'`
- Inference from the extension manifest, bridge logs, and negative host-file results: file or selection handoff likely travels through webview or desktop-bridge state and may not persist as a durable Codex-specific diff-session file on disk

## Shared vs Independent Storage

- Shared storage:
  - `~/.codex/` holds the transcript-like JSONL and thread registry shared across Codex CLI, IDE extension, Desktop, and related flows
- Host-specific storage:
  - VS Code keeps extension global state, prompt history, thread-title hints, view state, agent-session cache, and logs under the standard VS Code user-data roots
  - Cursor keeps view state, webview state, prompt history, and logs under the standard Cursor user-data roots
- Practical separation rule:
  - use shared rollout `originator == "codex_vscode"` for transcript selection
  - use host roots for editor attribution, environment metadata, prompt-history breadcrumbs, and bridge diagnostics

## Cross-Platform Note

Only macOS was directly inspected.

- Windows path translation guess, unverified:
  - `%USERPROFILE%\\.codex\\`
  - `%APPDATA%\\Code\\User\\globalStorage`
  - `%APPDATA%\\Code\\User\\workspaceStorage`
  - `%APPDATA%\\Cursor\\User\\globalStorage`
  - `%APPDATA%\\Cursor\\User\\workspaceStorage`
  - `%APPDATA%\\Windsurf\\User\\globalStorage`
- Linux path translation guess, unverified:
  - `$HOME/.codex/`
  - `$HOME/.config/Code/User/globalStorage`
  - `$HOME/.config/Code/User/workspaceStorage`
  - `$HOME/.config/Cursor/User/globalStorage`
  - `$HOME/.config/Cursor/User/workspaceStorage`
  - `$HOME/.config/Windsurf/User/globalStorage`

Do not treat those non-macOS paths as confirmed until they are inspected on real hosts.
