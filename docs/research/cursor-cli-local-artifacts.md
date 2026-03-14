# Cursor CLI Local Artifacts

Updated: `2026-03-14`

Scope: local artifact reconnaissance for `Cursor CLI` in `cli` execution context on macOS. This note stops at storage-path and format identification. It does not implement a collector or parser.

## High-Signal Summary

- Primary observed CLI config root: `~/.cursor/`
- Primary observed CLI log root: `~/Library/Application Support/Cursor/logs/<timestamp>/cli.log`
- Primary observed IDE host-side state root: `~/Library/Application Support/Cursor/User/`
- IDE-connect bridge sidecars were observed under `~/.cursor/projects/<project-slug>/mcps/`
- No `jsonl` or `ndjson` transcript file was observed under the inspected Cursor roots on this macOS host
- Best observed session-like metadata store: `~/Library/Application Support/Cursor/User/workspaceStorage/<workspace-id>/state.vscdb` with `composer.composerData`
- Working conclusion: Cursor CLI config, invocation logs, and IDE bridge state are split across shared Cursor roots; no isolated CLI-only transcript store was identified on this machine

## Observed macOS Roots

- `~/.cursor/cli-config.json`
  - Primary CLI config candidate
  - Observed top-level keys: `version`, `editor`, `hasChangedDefaultModel`, `permissions`, `network`
  - Model-state clue was limited to `hasChangedDefaultModel: false`
  - No concrete model identifier was observed in this file
- `~/.cursor/projects/`
  - Observed `9` top-level project directories
  - Observed `4` project directories with `mcps/` sidecars
  - Workspace-slug directories such as `Users-chenjing-dev-qmk-firmware` existed but were empty at inspection time
  - Temp-slug directories under `/var/folders/...` carried the bridge metadata described below
- `~/.cursor/projects/<temp-slug>/mcps/cursor-ide-browser/SERVER_METADATA.json`
  - Observed fields: `serverIdentifier`, `serverName`
- `~/.cursor/projects/<temp-slug>/mcps/cursor-ide-browser/INSTRUCTIONS.md`
  - Browser MCP usage instructions, lock workflow, and interaction rules
  - Bridge metadata, not transcript content
- `~/.cursor/projects/<temp-slug>/mcps/cursor-browser-extension/*`
  - Same sidecar pattern as `cursor-ide-browser`
  - Bridge metadata, not transcript content
- `~/.cursor/ide_state.json`
  - Observed `recentlyViewedFiles[]` with `relativePath` and `absolutePath`
  - IDE state, not conversation history
- `~/.cursor/mcp.json`
  - Sensitive MCP server config with auth-bearing headers
  - Relevant as shared product state, not as transcript material
- `~/.cursor/ai-tracking/ai-code-tracking.db`
  - Observed tables: `ai_code_hashes`, `conversation_summaries`, `tracking_state`, `scored_commits`
  - `ai_code_hashes` schema includes `conversationId`, `requestId`, `timestamp`, `createdAt`, and `model`
  - `conversation_summaries` schema includes `conversationId`, `title`, `tldr`, `overview`, `summaryBullets`, `model`, `mode`, `updatedAt`
  - On this host, `ai_code_hashes` and `conversation_summaries` both had `0` rows at inspection time
  - `tracking_state` contained only a `trackingStartTime` JSON value
- `~/Library/Application Support/Cursor/logs/`
  - Observed `9` CLI log files at `logs/<timestamp>/cli.log`
  - Each sampled `cli.log` contained a JSON-serialized argv record for the invocation plus `logsPath`
  - Observed fields included `headless`, `list-extensions`, `show-versions`, `verbose`, `status`, `trace`, and many Electron or VS Code runtime flags
  - Every observed run on this machine recorded `headless: false`
- `~/Library/Application Support/Cursor/User/workspaceStorage/<workspace-id>/workspace.json`
  - Maps workspace storage IDs back to concrete folders such as `file:///Users/chenjing/dev/css-test2`
- `~/Library/Application Support/Cursor/User/workspaceStorage/<workspace-id>/state.vscdb`
  - Per-workspace IDE state database
  - Best observed Cursor-native session metadata store on this machine
- `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb`
  - Shared IDE-wide SQLite store
  - Accessible via immutable SQLite URI because the file is WAL-backed
  - Observed keys included `anysphere.cursor-browser-extension`, `anysphere.cursor-mcp`, `chat.workspaceTransfer`, `cursor/memoriesEnabled`, `cursor/pendingMemories`, `cursor/approvedProjectMcpServers`, `cursor/terminalExecutionServiceV3HealthCheckResult`, `cursorAuth/*`, and `workbench.backgroundComposer.persistentData`
- `~/Library/Application Support/Cursor/User/History/`
  - File-edit history store, not chat history
  - `entries.json` rows used `resource`, `id`, `source`, `timestamp`
  - Companion files stored editor buffer snapshots such as `.toml`, `.md`, `.py`, `.json`
- `~/Library/Application Support/Cursor/User/workspaceStorage/*/ms-vscode.js-debug/.headless-profile/*.db`
  - Browser debugger profile residue from the JS debug extension
  - Headless-looking name, but not Cursor CLI transcript state

## Session And Prompt Metadata Structures

- `workspaceStorage/<workspace-id>/state.vscdb` -> `composer.composerData`
  - JSON object with `allComposers[]`, `selectedComposerIds`, `lastFocusedComposerIds`
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
  - Useful for composer or agent session heads, but not a full message transcript
- `workspaceStorage/<workspace-id>/state.vscdb` -> `workbench.backgroundComposer.workspacePersistentData`
  - JSON object with `setupPath2`, `terminals`, `ranTerminalCommands`, `installScript`, `startScript`, `currentSetupStep`, `furthestSetupStep`, `customDockerfileContents`, `isSideBarExpanded`, `cachedSelectedGitState`
  - Background or automation setup metadata, not conversation turns
- `workspaceStorage/<workspace-id>/state.vscdb` -> `aiService.prompts`
  - Observed sample shape: `{text, commandType}`
  - Prompt-sidecar cache, not bidirectional transcript
- `workspaceStorage/<workspace-id>/state.vscdb` -> `aiService.generations`
  - Observed sample shape: `{unixMs, generationUUID, type, textDescription}`
  - Generation metadata, not clean assistant reply content
- `workspaceStorage/<workspace-id>/state.vscdb` -> `interactive.sessions`
  - Observed empty arrays in sampled workspaces
- `workspaceStorage/<workspace-id>/state.vscdb` -> `workbench.panel.composerChatViewPane.<uuid>`
  - View layout metadata only
  - No message body was observed in sampled rows

## Collector Notes

- No Cursor CLI-local store with stable `role`, `timestamp`, `content` message triples was found on this host.
- `composer.composerData` is the highest-signal local session metadata currently visible, but it only exposes composer heads and UI selection state.
- `aiService.prompts` and `aiService.generations` may preserve prompt-adjacent text plus timestamps for some IDE workspaces, but they are partial sidecars rather than trustworthy full transcripts.
- `cli.log` is useful only for provenance about how the CLI was invoked. It should not be treated as transcript content.
- `User/History/**` is editor file-history residue. It should be excluded from any chat collector.
- `cursor-ide-browser` and `cursor-browser-extension` MCP sidecars are bridge metadata, not user or assistant messages.
- `mcp.json` is sensitive config and should be treated as auth or connector state, not transcript content.
- `ai-tracking/ai-code-tracking.db` is structurally interesting because it has `conversationId` and `model` columns, but it was unpopulated on this machine at inspection time.
- Model selection remains only partially confirmed locally:
  - observed: `hasChangedDefaultModel: false`
  - not observed: a persisted concrete model ID for Cursor CLI
- Headless support also remains only partially confirmed locally:
  - observed: `cli.log` records a `headless` flag
  - observed on this host: all sampled runs were `headless: false`
  - not observed: a dedicated headless transcript output or `headless: true` sample run

## Shared vs Independent Storage

This machine does not support an isolated CLI-only storage conclusion.

Evidence points to shared Cursor-family roots:

- `~/.cursor/` mixes CLI config, IDE state, MCP bridge directories, skills, and extensions
- `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb` carries shared Cursor-wide keys such as memories, auth, MCP, and background-composer state
- `~/Library/Application Support/Cursor/User/workspaceStorage/<workspace-id>/state.vscdb` carries IDE workspace-specific composer metadata and background-composer setup state
- CLI logs live under the same `~/Library/Application Support/Cursor/logs/` root used by the desktop editor

Working conclusion:

- Cursor CLI is not storing a clearly separate transcript root on this machine
- CLI config and IDE bridge state are split across shared product roots
- Any CLI versus IDE separation is more likely encoded in log files, workspace keys, or bridge sidecars than in an isolated transcript directory

## Negative Results

- No `*.jsonl` or `*.ndjson` files were found under `~/.cursor` or `~/Library/Application Support/Cursor`
- No full Cursor CLI transcript file with message-level `role`, `timestamp`, `content` fields was found under the inspected roots
- No concrete persisted model ID for Cursor CLI was found in the inspected local files
- No populated `conversation_summaries` or `ai_code_hashes` rows were found in `~/.cursor/ai-tracking/ai-code-tracking.db`
- No repo-local `.cursor/` directory or breadcrumb-like file was found in `/Users/chenjing/dev/chat-collector`
- No repo-local `.cursor/` directory or breadcrumb-like file was found in `/Users/chenjing/code/workspaces/chat-collector/CHE-56`

## Cross-Platform Note

Only macOS was directly inspected.

- Windows path translation guess, unverified: `%APPDATA%\\Cursor\\` plus `%USERPROFILE%\\.cursor\\`
- Linux path translation guess, unverified: `$HOME/.config/Cursor/` plus `$HOME/.cursor/`

Do not treat those non-macOS paths as confirmed until they are inspected on real hosts.
