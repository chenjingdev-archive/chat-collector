# Claude Code IDE Local Artifacts

Updated: `2026-03-14`

Scope: local artifact reconnaissance for `Claude Code` in `ide_extension` execution context on macOS. This note stops at storage-path and format identification. It does not implement a collector or parser.

Support level:

- Queue key: `claude_code_ide`
- Priority: `P0`
- Support track: `target_now`
- State gravity: `hybrid`
- Local transcript likelihood: `high`

## High-Signal Summary

- No IDE-only transcript root was identified on this machine.
- The strongest transcript candidate remains the shared Claude root:
  - `~/.claude/projects/<encoded-project-path>/<session-uuid>.jsonl`
  - `~/.claude/history.jsonl`
  - `~/.claude.json`
- IDE bridge state does exist in the shared root:
  - `~/.claude.json` contains `autoConnectIde`, `officialMarketplaceAutoInstallAttempted`, `officialMarketplaceAutoInstalled`, `shiftEnterKeyBindingInstalled`, and `optionAsMetaKeyInstalled`
  - `~/.claude/keybindings.json` exists and is watched by Claude debug logging
  - `~/.claude/ide/` exists but was empty at inspection time
- VS Code-family host-side residue was observed in:
  - `~/Library/Application Support/Cursor/User/globalStorage/storage.json`
  - It retained recent-file references to `~/.claude/keybindings.json` and a transient `/var/folders/.../claude-prompt-<uuid>.md`
- JetBrains host-side residue was not observed on this machine:
  - No JetBrains config, cache, or plugin roots existed under the standard macOS locations checked
- Working conclusion: Claude Code IDE usage shares the same per-user Claude storage as the CLI, while the IDE host appears to add lightweight bridge sidecars and recent-file references rather than a separate durable transcript DB

## Observed macOS Roots

### Shared Claude Root

- `~/.claude.json`
  - Shared top-level product state
  - Observed IDE-related keys:
    - `autoConnectIde: true`
    - `officialMarketplaceAutoInstallAttempted: true`
    - `officialMarketplaceAutoInstalled: true`
    - `shiftEnterKeyBindingInstalled: true`
    - `optionAsMetaKeyInstalled: true`
  - Observed project state for `/Users/chenjing/dev/chat-collector` and `/Users/chenjing/dev/chat-collector/.claude/worktrees/hungry-shtern`
  - Project objects contained trust and MCP flags, not IDE transcript payloads
- `~/.claude/projects/`
  - Shared session store used by Claude Code regardless of CLI versus IDE bridge evidence
  - Example `/ide` session file:
    - `~/.claude/projects/-Users-chenjing-dev-sendbox/195bb925-f0ff-4ee0-bc69-123e882c84ce.jsonl`
- `~/.claude/history.jsonl`
  - Slash-command history index
  - Observed `2` `/ide` rows on this machine
- `~/.claude/keybindings.json`
  - Shared keybinding file with Claude-specific schema and contexts
  - Likely user-visible bridge companion file rather than transcript storage
- `~/.claude/ide/`
  - Directory exists
  - Empty at inspection time

### VS Code-Family Host Roots

- `~/Library/Application Support/Code/User/globalStorage/`
  - Exists
  - No `claude` or `anthropic` namespace directory or key space was found
- `~/Library/Application Support/Code/User/workspaceStorage/`
  - Exists
  - No Claude Code bridge files were found by name or content
- `~/Library/Application Support/Cursor/User/globalStorage/storage.json`
  - Positive host-side bridge evidence
  - Recent-file entries referenced:
    - `~/.claude/keybindings.json`
    - `/var/folders/cg/cr4bjzw168l7bh4b87yskltc0000gn/T/claude-prompt-73430a3b-12ec-4f63-8d51-7a8ea2e2c57e.md`
- `~/Library/Application Support/Cursor/User/workspaceStorage/`
  - Exists
  - No Claude-specific durable state or prompt handoff cache was identified

### JetBrains Host Roots

The following standard macOS roots were checked and were absent or empty:

- `~/Library/Application Support/JetBrains`
- `~/Library/Preferences/JetBrains`
- `~/Library/Caches/JetBrains`

No JetBrains plugin directory, config file, cache, or bridge artifact containing `claude` or `anthropic` was found.

## Shared Transcript Evidence

### Slash-Command Index

`~/.claude/history.jsonl` rows use the shape:

- `display`
- `pastedContents`
- `timestamp`
- `project`
- `sessionId`

Observed `/ide` examples:

- `{"display":"/ide ","timestamp":1769911780719,"project":"/Users/chenjing","sessionId":"cb94967c-1902-448e-a976-a393cf66c4d1"}`
- `{"display":"/ide ","timestamp":1769920413224,"project":"/Users/chenjing/dev/sendbox","sessionId":"195bb925-f0ff-4ee0-bc69-123e882c84ce"}`

This file is useful as bridge metadata and session lookup, not as a clean chat transcript.

### Session JSONL

The shared session file `~/.claude/projects/-Users-chenjing-dev-sendbox/195bb925-f0ff-4ee0-bc69-123e882c84ce.jsonl` recorded IDE actions inside the ordinary Claude session stream.

Observed `/ide` rows:

- `type: "system"`
- `subtype: "local_command"`
- `content: "<command-name>/ide</command-name> ..."`
- follow-up `content: "<local-command-stdout>IDE selection cancelled</local-command-stdout>"`

Observed related bridge-enablement row in the same shared session family:

- `type: "user"`
- `message.role: "user"`
- `message.content: "<local-command-stdout>Set response language to ... Enabled auto-connect to IDE</local-command-stdout>"`

This matters for collection:

- Message-like rows can contain bridge execution output, not human intent
- `system.subtype="local_command"` and `<local-command-stdout>` payloads are execution artifacts
- IDE bridge actions are mixed into the same session JSONL family that also stores ordinary conversation turns

## Host-Side Bridge Evidence

### `~/.claude/keybindings.json`

This file uses Claude's own schema:

- `$schema`
- `$docs`
- `bindings[]`

Observed binding contexts included:

- `Global`
- `Chat`
- `Transcript`
- `DiffDialog`
- `MessageSelector`
- `Plugin`

This is not transcript data, but it is positive evidence that IDE integration and Claude UI affordances share the same per-user root.

### Cursor Recent-File Residue

`~/Library/Application Support/Cursor/User/globalStorage/storage.json` contained `openRecentFile` entries pointing to:

- `~/.claude/keybindings.json`
- `/var/folders/.../claude-prompt-<uuid>.md`

The `claude-prompt-*.md` file was not still present on disk when checked, so it appears ephemeral. The filename pattern and placement under the macOS temp directory make it the best observed candidate for external-terminal or IDE prompt handoff sidecars.

### Claude Debug Logs

Observed debug evidence:

- `~/.claude/debug/cb94967c-1902-448e-a976-a393cf66c4d1.txt`
  - `Official marketplace auto-install skipped: already_attempted`
  - `Successfully refreshed marketplace: claude-plugins-official`
- `~/.claude/debug/60428285-e625-41e2-bdad-2d31ee442f57.txt`
  - `Watching for changes to /Users/chenjing/.claude/keybindings.json`
  - `Detected change to /Users/chenjing/.claude/keybindings.json`
  - `Loaded 94 user bindings from /Users/chenjing/.claude/keybindings.json`

These are bridge-state clues, not transcript material.

## Diff And Selection Handoff

Positive clues:

- `~/.claude/keybindings.json` includes a `DiffDialog` context
- Cursor recent files referenced a transient `claude-prompt-*.md`
- `/ide` command activity is indexed in `~/.claude/history.jsonl`

Negative findings:

- No dedicated diff cache DB, selection handoff DB, IndexedDB, or LevelDB was found under the standard VS Code-family storage roots checked
- `~/.claude/ide/` existed but contained no files
- No durable `claude-prompt-*.md` file remained in `/var/folders` or `/tmp`

Working interpretation:

- Persistent transcript storage is shared with CLI sessions
- IDE selection and prompt handoff likely use transient sidecars and in-memory or short-lived host state
- This last point is an inference from observed temp-file references plus the absence of a durable host-side store

## Shared Vs Independent Storage

This machine does not support an independent IDE-only storage conclusion.

Evidence for shared storage:

- Transcript-bearing sessions remain under `~/.claude/projects/...jsonl`
- `/ide` actions are recorded inside those same shared session logs
- `~/.claude.json` carries IDE enablement and marketplace auto-install flags
- `~/.claude/keybindings.json` is also under the same root

Evidence against a separate durable IDE root:

- `~/.claude/ide/` was empty
- No named Claude/Anthropic extension storage namespace was found under standard VS Code or Cursor storage roots
- No JetBrains-side storage was found at all on this machine

Working conclusion:

- `~/.claude/` plus `~/.claude.json` is the shared Claude Code local state root for both CLI and IDE bridge usage on this machine
- Host IDEs contribute lightweight state and ephemeral handoff artifacts, but not a separate durable transcript store that was observable here

## Collector Notes

- Primary transcript extraction should still start from `~/.claude/projects/<encoded-project>/<session>.jsonl`
- Use `~/.claude/history.jsonl` only as session lookup or slash-command metadata
- Exclude host-side or bridge-noise payloads from clean transcript output:
  - `system` rows where `subtype == "local_command"`
  - `user` rows whose content is `<local-command-stdout>...`
  - `user` rows whose content is `<local-command-caveat>...`
  - transient `claude-prompt-*.md`
  - debug logs
  - keybinding files
- Message-level fields remain available in the shared JSONL:
  - `message.role`
  - `timestamp`
  - `message.content`
- Noise separation is feasible because IDE bridge artifacts use distinct wrappers such as:
  - `<command-name>...</command-name>`
  - `<local-command-stdout>...</local-command-stdout>`
  - `system.subtype = "local_command"`

## Negative Results

- No IDE-only transcript directory was found
- No files were present under `~/.claude/ide/`
- No durable `claude-prompt-*.md` file remained in `/var/folders` or `/tmp`
- No `claude` or `anthropic` namespace directory was found under:
  - `~/Library/Application Support/Code/User/globalStorage`
  - `~/Library/Application Support/Code/User/workspaceStorage`
  - `~/Library/Application Support/Cursor/User/workspaceStorage`
- No clearly named Anthropic or Claude extension directory was found under:
  - `~/.vscode/extensions`
  - `~/.cursor/extensions`
- No JetBrains config, cache, or plugin root was present under standard macOS locations

## Windows And Linux Path Deltas

These were not verified on this machine. Only the likely path families are noted.

- VS Code-family
  - Windows: `%APPDATA%\\<IDE>\\User\\globalStorage`, `%APPDATA%\\<IDE>\\User\\workspaceStorage`
  - Linux: `~/.config/<IDE>/User/globalStorage`, `~/.config/<IDE>/User/workspaceStorage`
- JetBrains
  - Windows: `%APPDATA%\\JetBrains`, `%LOCALAPPDATA%\\JetBrains`
  - Linux: `~/.config/JetBrains`, `~/.cache/JetBrains`
- Shared Claude root
  - Windows: likely under `%USERPROFILE%\\.claude\\` plus `%USERPROFILE%\\.claude.json`
  - Linux: likely under `~/.claude/` plus `~/.claude.json`
