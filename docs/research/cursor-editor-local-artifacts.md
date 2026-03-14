# Cursor Editor Local Artifacts

Updated: `2026-03-14`

Scope: local artifact reconnaissance for `Cursor` in `ide_native` execution context on macOS. This note stops at storage-path and format identification. It does not implement a collector or parser.

## High-Signal Summary

- Primary observed macOS roots: `~/.cursor/` and `~/Library/Application Support/Cursor/`
- Strongest native-editor session store: `~/Library/Application Support/Cursor/User/workspaceStorage/<workspace-id>/state.vscdb`
- Highest-signal native-editor keys observed in sampled workspace databases:
  - `composer.composerData`
  - `aiService.prompts`
  - `aiService.generations`
  - `workbench.backgroundComposer.workspacePersistentData`
  - `workbench.agentMode.exitInfo`
- Session-end metadata was also observed in `~/Library/Application Support/Cursor/logs/<timestamp>/window1/output_<timestamp>/cursor.hooks.log`
- Global storage exposed memory feature state, but not concrete memory payloads:
  - `cursor/memoriesEnabled == true`
  - `cursor/pendingMemories == []`
- No standalone export directory, no native `jsonl` transcript file, and no durable full bidirectional transcript with stable `role`, `timestamp`, `content` triples were observed on this macOS host
- Working conclusion: Cursor editor state lives inside shared Cursor-family roots that are also used by Cursor CLI; native-editor separation is by key space and subdirectory, not by an isolated per-context root

## Observed macOS Roots

- `~/.cursor/ai-tracking/ai-code-tracking.db`
  - Structurally interesting shared Cursor-family SQLite store
  - Observed tables:
    - `ai_code_hashes`
    - `conversation_summaries`
    - `scored_commits`
    - `tracking_state`
  - Observed relevant schemas:
    - `ai_code_hashes` includes `conversationId`, `requestId`, `timestamp`, `createdAt`, `model`
    - `conversation_summaries` includes `conversationId`, `title`, `tldr`, `overview`, `summaryBullets`, `model`, `mode`, `updatedAt`
  - Observed row counts on this host:
    - `ai_code_hashes`: `0`
    - `conversation_summaries`: `0`
    - `tracking_state`: `1`
  - Useful as a future correlation candidate, but unpopulated on this machine at inspection time
- `~/.cursor/projects/<project-slug>/mcps/*`
  - Observed only MCP sidecar artifacts such as `SERVER_METADATA.json` and `INSTRUCTIONS.md`
  - These are bridge and tool-registration artifacts, not chat transcript files
- `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb`
  - Shared IDE-wide SQLite store
  - Relevant Cursor-native keys observed:
    - `cursor/memoriesEnabled`
    - `cursor/pendingMemories`
    - `cursor/approvedProjectMcpServers`
    - `cursor/copyPasteMentions`
    - `workbench.backgroundComposer.persistentData`
  - Relevant non-native mixed state observed:
    - `openai.chatgpt`
  - `openai.chatgpt` is extension state inside the Cursor host, not Cursor-native editor state
- `~/Library/Application Support/Cursor/User/workspaceStorage/<workspace-id>/workspace.json`
  - Maps hashed workspace IDs back to concrete folder URIs
  - Sample observed shape:
    - `{ "folder": "file:///Users/chenjing/Downloads/%EA%B3%BC%EC%A0%9C" }`
- `~/Library/Application Support/Cursor/User/workspaceStorage/<workspace-id>/state.vscdb`
  - Per-workspace IDE SQLite store
  - Best observed native Cursor editor session and prompt metadata source on this host
- `~/Library/Application Support/Cursor/logs/<timestamp>/window1/output_<timestamp>/cursor.hooks.log`
  - Cursor hooks service log
  - Observed `5` log files on this machine
  - Carries session-end metadata, but not full conversation turns
- `~/Library/Application Support/Cursor/User/History/`
  - Editor file-history store
  - Not chat history
- `~/Library/Application Support/Cursor/logs/<timestamp>/window1/exthost/anysphere.cursor-agent-exec/*.log`
  - Execution and MCP orchestration logs
  - Useful for provenance and noise filtering, not for transcript extraction

## Session And Prompt Metadata Structures

- `workspaceStorage/<workspace-id>/state.vscdb` -> `composer.composerData`
  - JSON object with:
    - `allComposers[]`
    - `selectedComposerIds`
    - `lastFocusedComposerIds`
    - migration booleans
  - Observed `allComposers[]` fields included:
    - `composerId`
    - `name`
    - `createdAt`
    - `lastUpdatedAt`
    - `unifiedMode`
    - `forceMode`
    - `subtitle`
    - `contextUsagePercent`
    - `totalLinesAdded`
    - `totalLinesRemoved`
    - `hasUnreadMessages`
    - `hasBlockingPendingActions`
    - `isArchived`
    - `isWorktree`
    - `isSpec`
  - Best treated as a session index or composer-head registry, not as message bodies
- `workspaceStorage/<workspace-id>/state.vscdb` -> `aiService.prompts`
  - JSON array of prompt-like objects
  - Observed item shape:
    - `text`
    - `commandType`
  - Strong user-message candidate
  - Important caveat: prompt text may include pasted shell output, stack traces, URLs, or secrets, so content filtering is required
- `workspaceStorage/<workspace-id>/state.vscdb` -> `aiService.generations`
  - JSON array of generation-side objects
  - Observed item shape:
    - `unixMs`
    - `generationUUID`
    - `type`
    - `textDescription`
  - Observed `type`: `composer`
  - `unixMs` is the strongest timestamp field found for per-message-like entries
  - `textDescription` often looked like a prompt echo or generation description rather than a clean assistant reply, so assistant-content trust is currently low
- `workspaceStorage/<workspace-id>/state.vscdb` -> `workbench.backgroundComposer.workspacePersistentData`
  - JSON object with fields such as:
    - `setupPath2`
    - `terminals`
    - `ranTerminalCommands`
    - `installScript`
    - `startScript`
    - `currentSetupStep`
    - `furthestSetupStep`
    - `customDockerfileContents`
    - `isSideBarExpanded`
    - `cachedSelectedGitState`
    - sometimes `cachedSelectedRemote`
  - This is background-agent and workspace-setup metadata, not chat turn content
- `workspaceStorage/<workspace-id>/state.vscdb` -> `workbench.agentMode.exitInfo`
  - JSON object like `{"wasVisible": {...}, "showTabs": "multiple"}`
  - UI layout state only
- `workspaceStorage/<workspace-id>/state.vscdb` -> `workbench.panel.composerChatViewPane.<uuid>`
  - Pane layout and view visibility metadata only
  - Useful for linking pane UUIDs to `composerId`-scoped views, not for transcript extraction
- `workspaceStorage/<workspace-id>/state.vscdb` -> `interactive.sessions`
  - Observed as `[]` in sampled workspaces
  - No useful native Cursor chat-session rows were found there on this host
- `logs/<timestamp>/window1/output_<timestamp>/cursor.hooks.log`
  - Observed session-end input fields included:
    - `conversation_id`
    - `session_id`
    - `model`
    - `reason`
    - `duration_ms`
    - `is_background_agent`
    - `final_status`
    - `hook_event_name`
    - `cursor_version`
    - `workspace_roots`
    - `transcript_path`
  - Observed `model`: `composer-1`
  - Observed `hook_event_name`: `sessionEnd`
  - Observed `reason`: `window_close`
  - Observed `transcript_path`: `null`
- `globalStorage/state.vscdb` -> memory-related Cursor keys
  - `cursor/memoriesEnabled` was `true`
  - `cursor/pendingMemories` was `[]`
  - This shows memory features are enabled in product state, but no concrete persisted memory payload was located during this inspection

## Collector Notes

- Best current native Cursor collector candidate is `User/workspaceStorage/<workspace-id>/state.vscdb`
- `composer.composerData` should be used as a session index:
  - it gives session heads, titles, update times, modes, and coarse activity signals
  - it does not hold full message bodies
- `aiService.prompts` is the clearest observed user-content source
- `aiService.generations` adds timestamps and generation IDs, but its `textDescription` field should not be assumed to be assistant-visible reply text without further validation
- Message-level reconstruction is therefore only partial on this host:
  - likely user side: `aiService.prompts[].text`
  - likely time anchor: `aiService.generations[].unixMs`
  - not yet confirmed: durable assistant message body store
- Execution-noise exclusion should explicitly drop:
  - `~/.cursor/projects/*/mcps/*`
  - `~/.cursor/mcp.json`
  - `User/History/**`
  - `logs/**/exthost/anysphere.cursor-mcp/*.log`
  - `logs/**/exthost/anysphere.cursor-agent-exec/*.log`
  - hook runner output that reflects automation lifecycle rather than user or assistant prose
- Extension-state exclusion should explicitly avoid misattributing:
  - `globalStorage/state.vscdb` -> `openai.chatgpt`
  - `workspaceStorage/*/state.vscdb` -> `memento/webviewView.chatgpt.sidebarView`
  - those belong to the Codex extension running inside Cursor, not to Cursor-native editor chat
- Sensitive-content caution:
  - observed prompt-side caches can preserve pasted shell output and credentials
  - observed MCP logs can preserve connection details or auth-bearing headers
  - these should be treated as redactable input noise, not memory-quality transcript content

## Shared vs Independent Storage

This macOS host does not support an isolated Cursor-editor-only storage conclusion.

Observed storage is shared at the product-root level:

- `~/.cursor/` is shared with Cursor CLI and holds config, MCP sidecars, and shared tracking data
- `~/Library/Application Support/Cursor/logs/` is shared by the desktop editor, extensions, and related agent services
- `~/.cursor/ai-tracking/ai-code-tracking.db` is a shared Cursor-family structure rather than a clearly editor-only file

Native editor signal is concentrated in editor-specific subspaces:

- `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb`
- `~/Library/Application Support/Cursor/User/workspaceStorage/<workspace-id>/state.vscdb`
- `~/Library/Application Support/Cursor/logs/<timestamp>/window1/output_<timestamp>/cursor.hooks.log`

Working conclusion:

- Cursor editor and Cursor CLI appear to share top-level product roots on macOS
- Native-editor artifacts are separated mainly by workspace key space and log subdirectories
- Cursor host storage also mixes third-party extension state, so collector logic must separate `Cursor native` from `extension-in-Cursor`

## Negative Results

- No standalone export directory was found under `~/.cursor/` or `~/Library/Application Support/Cursor/`
- No native Cursor `*.jsonl` or `*.ndjson` transcript file was found under the inspected roots
- No durable assistant-message store with clear `role`, `timestamp`, `content` fields was found on this host
- No non-empty persisted memory payloads were found beyond feature toggles and empty pending-memory state
- `interactive.sessions` was empty in sampled workspace databases
- `~/.cursor/ai-tracking/ai-code-tracking.db` had the right-looking tables but no populated `conversation_summaries` or `ai_code_hashes` rows
- `cursor.hooks.log` exposed session metadata, but every observed sample had `transcript_path: null`

## Cross-Platform Note

Only macOS was directly inspected.

- Windows path translation guess, unverified:
  - `%APPDATA%\\Cursor\\`
  - `%USERPROFILE%\\.cursor\\`
- Linux path translation guess, unverified:
  - `$HOME/.config/Cursor/`
  - `$HOME/.cursor/`

Do not treat those non-macOS paths as confirmed until they are inspected on real hosts.
