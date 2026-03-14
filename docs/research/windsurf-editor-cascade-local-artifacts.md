# Windsurf Editor Cascade Local Artifacts

Updated: `2026-03-14`

Scope: local artifact reconnaissance for `Windsurf` in `ide_native` execution context on macOS. This note stops at storage-path and format identification. It does not implement a collector or parser.

Support level:

- Queue key: `windsurf_editor_cascade`
- Priority: `P0`
- Support track: `candidate_local_first`
- State gravity: `hybrid`
- Local transcript likelihood: `high`

## High-Signal Summary

- Confirmed macOS Windsurf-specific root on this host: `~/.codeium/windsurf/`
- Confirmed repo-level Windsurf metadata root on this host: `./.windsurf/`
- Observed global root contents were minimal:
  - `~/.codeium/windsurf/mcp_config.json`
  - `~/.codeium/windsurf/skills/`
- Observed repo-level root contents were also minimal:
  - `/Users/chenjing/dev/이력서/.windsurf/skills/`
- No transcript-bearing store was observed on this macOS host:
  - no `~/.codeium/windsurf/memories`
  - no `~/Library/Application Support/Windsurf`
  - no `state.vscdb`, `sqlite`, IndexedDB, LevelDB, `jsonl`, or export directory
- No Windsurf app bundle, log root, saved-state root, or preferences plist was found under standard macOS locations
- No account or auth-bearing file was observed under `~/.codeium`
- Working conclusion:
  - this host has Windsurf config and repo-metadata scaffolding, but no concrete local Cascade chat-session payload
  - the highest-signal observed artifacts are MCP config plus project-global skill directories
  - transcript collection logic for Windsurf should remain gated on finding a populated `memories` or editor-host database root on a machine that has actually run the native editor

## Official Path Expectations Vs Observed State

Official Windsurf docs referenced by this ticket describe these roots:

- config and memories:
  - `~/.codeium/windsurf/`
  - `~/.codeium/windsurf/memories`
- global rules:
  - `~/.codeium/windsurf/global_rules.md`
- project rules:
  - `<repo>/.windsurf/rules/`
- global skills:
  - `~/.codeium/windsurf/skills/`
- project skills:
  - `<repo>/.windsurf/skills/`

Observed on this macOS host:

- present:
  - `~/.codeium/windsurf/`
  - `~/.codeium/windsurf/mcp_config.json`
  - `~/.codeium/windsurf/skills/`
  - `/Users/chenjing/dev/이력서/.windsurf/`
  - `/Users/chenjing/dev/이력서/.windsurf/skills/`
- absent:
  - `~/.codeium/windsurf/memories`
  - `~/.codeium/windsurf/global_rules.md`
  - any `./.windsurf/rules/`
  - any `SKILL.md` under global or project `skills/`
  - `~/Library/Application Support/Windsurf`
  - `~/Library/Logs/Windsurf`
  - `~/Library/Preferences/com.codeium.windsurf.plist`
  - `~/Library/Preferences/com.exafunction.windsurf.plist`
  - `/Applications/Windsurf.app`

## Observed macOS Roots

### `~/.codeium/windsurf/`

Observed entries:

- `mcp_config.json`
- `skills/`

Observed file content:

- `mcp_config.json`
  - shape: JSON object
  - content: `{"mcpServers":{}}`

Working interpretation:

- This is a real Windsurf-specific global config root on this machine.
- The only populated file is MCP configuration state, not transcript state.
- `skills/` exists as a documented container for reusable agent instructions, but no concrete skill payload was present.

### `<repo>/.windsurf/`

Observed example:

- `/Users/chenjing/dev/이력서/.windsurf/skills/`

Working interpretation:

- Windsurf keeps repo-scoped metadata outside the global config root.
- On this host, the only observed repo-level artifact class was `skills/`.
- No repo-level `rules/`, conversation export, or session index file was present.

### Standard macOS App Roots

Negative checks:

- `~/Library/Application Support/Windsurf`
- `~/Library/Application Support/Windsurf/User/globalStorage`
- `~/Library/Application Support/Windsurf/User/workspaceStorage`
- `~/Library/Logs/Windsurf`
- `~/Library/Saved Application State/com.codeium.windsurf.savedState`
- `~/Library/Saved Application State/com.exafunction.windsurf.savedState`
- `/Applications/Windsurf.app`

Working interpretation:

- This machine does not currently show evidence of an installed or recently used native Windsurf app bundle.
- That absence explains why no VS Code-family `globalStorage`, `workspaceStorage`, or Electron app-state database was available to inspect locally.

## Session And Message Structures

No transcript-bearing structure was confirmed on this host.

Observed session-adjacent structures:

- `~/.codeium/windsurf/mcp_config.json`
  - tool and MCP configuration only
- `~/.codeium/windsurf/skills/`
  - empty global skill container
- `<repo>/.windsurf/skills/`
  - empty project skill container

Important negative result:

- no file, directory, DB table, or key space with stable per-message fields such as `role`, `timestamp`, and `content` was observed
- no durable session index, chat export, or conversation DB was observed

## Account State

Negative checks under `~/.codeium` found:

- no auth file
- no token cache
- no email or account JSON
- no credential-like file beyond `mcp_config.json`

Working interpretation:

- account state is not exposed in the Windsurf-specific filesystem roots present on this host
- if account state exists locally, it may live in an unobserved app install, system keychain, or a host root that was not created on this machine because the app has not been run here

## Collector Notes

- Treat `~/.codeium/windsurf/mcp_config.json` as execution-noise or bridge config, not chat memory.
- Treat global or project `skills/` as operator-authored context, not transcript turns.
- Treat future `rules` files similarly:
  - useful for repo metadata and prompt-context reconstruction
  - not usable as user or assistant chat turns
- On this host there is no basis for message reconstruction because no message-bearing store was found.
- A future Windsurf collector should first probe, in order:
  - `~/.codeium/windsurf/memories`
  - `~/Library/Application Support/Windsurf/User/globalStorage`
  - `~/Library/Application Support/Windsurf/User/workspaceStorage`
- If none of those exist, the collector should emit a clear negative result instead of fabricating transcript support.

## Shared vs Independent Storage

Observed separation on this host:

- global product root:
  - `~/.codeium/windsurf/`
- repo-specific metadata root:
  - `<repo>/.windsurf/`

Working conclusion:

- Windsurf native-editor metadata is not currently evidenced as sharing a host IDE root such as `~/Library/Application Support/Code` or `~/Library/Application Support/Cursor` on this machine.
- The observed naming suggests Windsurf-specific storage rather than reuse of another editor's global key space.
- However, because no installed app bundle or populated session store was present, this remains a host-level negative conclusion, not a proof that other Windsurf execution contexts never share Codeium-family storage elsewhere.

## Negative Results

- No `memories` directory existed under `~/.codeium/windsurf/`
- No `global_rules.md` existed under `~/.codeium/windsurf/`
- No project `rules/` directory was found in inspected repos
- No `SKILL.md` file was found in any observed Windsurf `skills/` directory
- No macOS app-support, log, preferences, or saved-state roots were found for Windsurf
- No auth or account files were found under `~/.codeium`
- No conversation transcript, message index, SQLite DB, IndexedDB, LevelDB, or export artifact was found under any observed Windsurf root

## Cross-Platform Note

Only macOS was directly inspected.

Doc-backed non-macOS path clues, not locally verified:

- Windows:
  - `%APPDATA%\\Codeium\\windsurf\\memories`
  - `%APPDATA%\\Codeium\\windsurf\\global_rules.md`
- Linux:
  - `~/.codeium/windsurf/memories`
  - `~/.codeium/windsurf/global_rules.md`

Do not treat those non-macOS paths as confirmed until they are inspected on real hosts.

## Sources

- Official docs:
  - `https://docs.windsurf.com/context-awareness/memories`
  - `https://docs.windsurf.com/context-awareness/rules`
  - `https://docs.windsurf.com/windsurf/cascade/skills`
- Local inspection:
  - `~/.codeium/windsurf/`
  - `/Users/chenjing/dev/이력서/.windsurf/`
