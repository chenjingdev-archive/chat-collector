# Gemini Code Assist IDE Local Artifacts

Updated: `2026-03-14`

Scope: local artifact reconnaissance for `Gemini Code Assist` in `ide_extension` execution context on macOS. This note stops at storage-path and format identification. It does not implement a collector or parser.

Support level:

- Queue key: `gemini_code_assist_ide`
- Priority: `P0`
- Support track: `target_now`
- State gravity: `hybrid`
- Local transcript likelihood: `high`

## High-Signal Summary

- Directly observed macOS roots with Gemini Code Assist IDE state:
  - `~/Library/Application Support/google-vscode-extension/`
  - `~/Library/Application Support/cloud-code/`
  - `~/Library/Application Support/Code/User/globalStorage/state.vscdb`
  - `~/Library/Application Support/Code/User/workspaceStorage/<workspace-id>/state.vscdb`
  - `~/.vscode/extensions/google.geminicodeassist-2.73.0/`
- Strongest durable local artifacts on this host were auth, install, and UI state, not transcript files:
  - `google-vscode-extension/auth/credentials.json`
  - `google-vscode-extension/auth/application_default_credentials.json`
  - VS Code global key `google.geminicodeassist`
  - VS Code workspace keys `workbench.view.extension.geminiChat.state`, `workbench.view.extension.geminiOutline.state`, `chat.ChatSessionStore.index`
- Observed `google.geminicodeassist` global state included agent-mode and lifecycle flags:
  - `newChatIsAgent`
  - `lastChatModeWasAgent`
  - `geminicodeassist.hasRunOnce`
  - `geminicodeassist.lastOpenedVersion`
  - `cloudcode.session-index`
  - `cloudcode.duetAI.showAgentTipsCard.agent`
- No Gemini transcript-bearing JSON, SQLite table, IndexedDB, or LevelDB was confirmed under `google-vscode-extension`, `cloud-code`, or VS Code `chatSessions` on this machine.
- Shared-state evidence exists in the bundled local agent backend:
  - `agent/a2a-server.mjs` vendors Gemini CLI-style storage paths under `~/.gemini/`
  - referenced shared files include `settings.json`, `google_accounts.json`, `oauth_creds.json`, `mcp-oauth-tokens-v2.json`, `GEMINI.md`, and `.geminiignore`
- Working conclusion:
  - Gemini Code Assist IDE on this host keeps auth and install state in extension-specific macOS roots and lightweight UI state in VS Code storage
  - config and memory primitives are shared with Gemini CLI under `~/.gemini/`
  - durable local IDE transcript persistence was not observed

## Observed macOS Roots

Only the VS Code-family surface was directly observed on this machine. JetBrains, Android Studio, and Cloud Shell were checked for local residue but not installed or not locally inspectable on macOS.

### `~/Library/Application Support/google-vscode-extension/`

Observed files:

- `auth/credentials.json`
- `auth/application_default_credentials.json`

Observed top-level JSON keys:

- `credentials.json`
  - `accessToken`
  - `accessTokenExpirySecond`
  - `credentials`
  - `email`
  - `refreshToken`
- `application_default_credentials.json`
  - `client_id`
  - `client_secret`
  - `quota_project_id`
  - `refresh_token`
  - `type`

Working interpretation:

- This root is a durable auth sidecar for the VS Code extension.
- It is not a clean transcript source and should be treated as sensitive credential storage, not memory content.

### `~/Library/Application Support/cloud-code/`

Observed files:

- `install_id.txt`
- `cloudcode_cli/cloudcode_cli/75da7dd/cloudcode_cli`

Observed file types:

- `install_id.txt`: ASCII text
- `cloudcode_cli`: Mach-O 64-bit executable arm64

Working interpretation:

- This root is install and bundled-backend state.
- No local JSON, SQLite, IndexedDB, or LevelDB transcript cache was observed here on this host.

## VS Code Host State

### Extension Install Root

Observed install root:

- `~/.vscode/extensions/google.geminicodeassist-2.73.0/`

Observed package-level capabilities:

- commands:
  - `geminicodeassist.startagent`
  - `geminicodeassist.stopagent`
  - `geminicodeassist.chat.resume`
  - `geminicodeassist.editor.addSelectionToChatContext`
  - `geminicodeassist.terminal.addSelectionToChatContext`
  - `geminicodeassist.addFileToContext`
  - `geminicodeassist.addFolderToContext`
- settings:
  - `geminicodeassist.agentYoloMode`
  - `geminicodeassist.agentDebugMode`
  - `geminicodeassist.beta.enableSidebarChatDiff`
  - `geminicodeassist.inlineSuggestions.nextEditPredictions`
- views:
  - `cloudcode.gemini.chatView`
  - `cloudcode.gemini.outlineView`
- bundled backend artifacts:
  - `cloudcode_cli.zip`
  - `agent/a2a-server.mjs`

Observed Cloud Shell gating in the manifest:

- multiple commands and sign-in flows were guarded by `!runningOnCloudShell`

Working interpretation:

- The extension clearly supports agent mode, chat resume, and explicit file or selection handoff.
- Cloud Shell likely diverges in local persistence behavior, but that could not be validated from this macOS host.

### User Settings

Observed `~/Library/Application Support/Code/User/settings.json` values:

- `geminicodeassist.displayInlineContextHint: false`
- `geminicodeassist.project: "elite-sanctuary-pv00q"`

Negative result:

- No user-level override for `geminicodeassist.agentYoloMode` or `geminicodeassist.agentDebugMode` was found in the inspected user settings file.

This means:

- some Gemini Code Assist configuration is user-visible and file-backed
- agent-mode enablement on this host was better evidenced by global state flags than by explicit user settings

### Global Storage

Observed DB:

- `~/Library/Application Support/Code/User/globalStorage/state.vscdb`

Observed Gemini-related keys:

- `google.geminicodeassist`
- `workbench.view.extension.geminiChat.state.hidden`
- `workbench.view.extension.geminiOutline.state.hidden`

Observed `google.geminicodeassist` JSON object keys included:

- `cloudcode.session-index`
- `geminicodeassist.survey.useractivity`
- `geminicodeassist.hasRunOnce`
- `geminicodeassist.lastOpenedVersion`
- `cloudcode.hats-index`
- `telemetry_setting_updated`
- `geminicodeassist.toolDeprecationNoticationDisplayed`
- `geminicodeassist.survey.lastsurvey`
- `newChatIsAgent`
- `geminicodeassist.gemini3AnnouncementDismissed`
- `lastChatModeWasAgent`
- `geminicodeassist.gemini3ProAnnouncementDismissed`
- `cloudcode.duetAI.showAgentTipsCard.agent`
- `geminicodeassist.showReleaseNotesInChatMessage`
- `geminicodeassist.codeCustomizationStatusEnableNotificationCheck`
- `geminicodeassist.upsellMessageLastShown`
- `cloudcode.duetAI.onboardingTooltipInvokedOnce`

Observed hidden-view values:

- `workbench.view.extension.geminiChat.state.hidden`
  - `[{"id":"cloudcode.gemini.chatView","isHidden":false}]`
- `workbench.view.extension.geminiOutline.state.hidden`
  - `[{"id":"cloudcode.gemini.outlineView","isHidden":false}]`

Working interpretation:

- `google.geminicodeassist` is the strongest confirmed Gemini-specific local key space on this host.
- It stores lifecycle flags, onboarding state, counters, and agent-mode breadcrumbs.
- It does not by itself store a recoverable message transcript.

### Workspace Storage

Observed workspace DB:

- `~/Library/Application Support/Code/User/workspaceStorage/<workspace-id>/state.vscdb`

Observed Gemini-related keys across several workspaces:

- `chat.ChatSessionStore.index`
- `workbench.view.extension.geminiChat.state`
- `workbench.view.extension.geminiOutline.state`
- `memento/webviewView.cloudcode.gemini.chatView`
- `workbench.view.extension.geminiChat.numberOfVisibleViews`

Observed `chat.ChatSessionStore.index` structure:

- top-level:
  - `version`
  - `entries`
- per-entry fields:
  - `sessionId`
  - `title`
  - `lastMessageDate`
  - `timing`
  - `initialLocation`
  - `hasPendingEdits`
  - `isEmpty`
  - `isExternal`
  - `lastResponseState`

Observed sample values:

- one sampled workspace entry was:
  - `title: "새 채팅"`
  - `isEmpty: true`
  - `initialLocation: "panel"`
- another sampled workspace stored:
  - `memento/webviewView.cloudcode.gemini.chatView = {}`
  - `workbench.view.extension.geminiChat.state = {"cloudcode.gemini.chatView":{"collapsed":false,"isHidden":true,"size":972}}`

Important negative result:

- searching `workspaceStorage/**/chatSessions/*` found no Gemini markers by content
- the sampled `chatSessions/*.json` files in the same workspace that had Gemini view state belonged to `GitHub Copilot`
- those sampled files were empty chat shells with:
  - `responderUsername: "GitHub Copilot"`
  - `requests: []`
  - `mode.kind: "agent"`
  - `selectedModel.metadata.extension.value: "GitHub.copilot-chat"`

Working interpretation:

- `chat.ChatSessionStore.index` should be treated as a generic VS Code host breadcrumb, not proof of Gemini-owned transcript persistence.
- On this machine, Gemini view state and generic host chat-session files coexisted, but the durable chat-session files inspected were clearly owned by another provider.

### Logs

Negative result:

- searching `~/Library/Application Support/Code/logs/` by `gemini`, `cloud-code`, and `google` names returned no matching log files

This means:

- no named Gemini Code Assist host log file was available as a local artifact clue on this machine

## Bundled Local Agent And Shared Gemini State

Observed extension bundle:

- `~/.vscode/extensions/google.geminicodeassist-2.73.0/agent/a2a-server.mjs`

Observed shared Gemini CLI-style storage references inside the bundled server:

- `GEMINI_DIR = ".gemini"`
- `getGlobalGeminiDir() -> path.join(homeDir, ".gemini")`
- `google_accounts.json`
- `oauth_creds.json`
- `mcp-oauth-tokens-v2.json`
- `GEMINI.md`
- `.geminiignore`

Observed preview-feature and auth behavior inside the bundled server:

- `refreshAuth()` called `this.geminiClient.stripThoughtsFromHistory()`
- preview features could be hydrated from remote experiments when local preview settings were unset

Observed message-shape clues inside the bundled server:

- `this.geminiClient.addHistory({ role: "user", parts: parts2 })`
- role and content parts are explicit in the local agent code path

Observed bundled backend protocol clues:

- the bundled `cloudcode_cli` executable exposed strings for:
  - `conversation/agent/chat`
  - `conversation/chat/updateHistory`
  - `GetCodeAssistGlobalUserSetting`
  - `SetCodeAssistGlobalUserSetting`
  - request shapes containing `threadId`, `history`, and optional `a2aTaskId`

Working interpretation:

- Gemini Code Assist IDE does share Gemini-family config, memory, and token primitives with Gemini CLI.
- The bundled local agent clearly reasons over message history using `role` plus `parts`.
- However, no on-disk IDE transcript file corresponding to that protocol history was found in the inspected local roots.
- Inference:
  - transcript persistence may be remote
  - or stored in a non-obvious cleanup-prone cache
  - or written only after agent flows not exercised on this host

## JetBrains, Android Studio, And Cloud Shell Negative Results

The following standard macOS roots were checked and absent:

- `~/Library/Application Support/JetBrains`
- `~/Library/Application Support/Google/Cloud Code`
- `~/Library/Application Support/Google/AndroidStudio`
- `~/Library/Application Support/Google/AndroidStudio2024.2`

Observed implication:

- No JetBrains or Android Studio plugin cache, settings file, or transcript-bearing state was available to inspect on this machine.
- Cloud Shell was only visible indirectly through manifest conditions like `runningOnCloudShell`, not as a local macOS storage root.

## Collector Notes

- Highest-confidence local collection targets from this ticket:
  - `google.geminicodeassist` in VS Code global `state.vscdb`
  - Gemini-related view and session-index keys in workspace `state.vscdb`
  - extension-install metadata and bundled agent code for future parser design
- Treat the following as non-transcript or high-noise by default:
  - `google-vscode-extension/auth/*`
  - `cloud-code/install_id.txt`
  - bundled `cloudcode_cli` executable
  - generic VS Code `chatSessions/*` unless provider ownership is explicitly Gemini
  - tool approvals, A2A task ids, CLI protocol residue, logs, auth tokens, and install metadata
- Message-level field guidance for future parser work:
  - confirmed on-disk message fields for Gemini IDE were not found on this machine
  - bundled agent code suggests a likely message shape centered on `role` and `parts`
  - `stripThoughtsFromHistory()` is explicit evidence that hidden reasoning or thought content should be filtered from memory-oriented output
  - tool response payloads fed back into the model are execution artifacts and should not be mistaken for user-authored chat turns

## Shared Vs Independent Storage

This machine does not support an independent IDE-only transcript storage conclusion.

Evidence for shared storage:

- the bundled local agent vendors Gemini CLI-style `~/.gemini/` config and memory paths
- the same bundle references `GEMINI.md`, `.geminiignore`, OAuth token stores, and Google account files already associated with Gemini CLI

Evidence against shared transcript storage being confirmed locally:

- no Gemini transcript file was found under `~/.gemini/` by IDE-specific name or content
- no Gemini-owned `chatSessions/*` file was found under VS Code workspace storage
- `google-vscode-extension` and `cloud-code` held auth and install residue, not durable transcript content

Working conclusion:

- config and memory primitives are shared with Gemini CLI
- local transcript persistence for the IDE extension was not confirmed and should currently be treated as separate, remote, or cleanup-prone until a host with active Gemini IDE sessions yields a durable file

## Cross-Platform Note

Only macOS was directly inspected.

Windows path translation guesses, unverified:

- `%APPDATA%\\google-vscode-extension\\`
- `%APPDATA%\\cloud-code\\`
- `%APPDATA%\\Code\\User\\globalStorage\\`
- `%APPDATA%\\Code\\User\\workspaceStorage\\`

Linux path translation guesses, unverified:

- `~/.config/google-vscode-extension/`
- `~/.config/cloud-code/`
- `~/.config/Code/User/globalStorage/`
- `~/.config/Code/User/workspaceStorage/`

## Public Product References

- Supported interfaces:
  - `https://developers.google.com/gemini-code-assist/docs/supported-languages`
- Agent mode:
  - `https://developers.google.com/gemini-code-assist/docs/use-agentic-chat-pair-programmer`
