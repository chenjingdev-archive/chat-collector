# Gemini CLI Local Artifacts

Updated: `2026-03-14`

Scope: local artifact reconnaissance for `Gemini CLI` in `cli` execution context on macOS. This note stops at storage-path and format identification. It does not implement a collector or parser.

## High-Signal Summary

- Primary observed per-user root: `~/.gemini/`
- Primary observed transcript candidate: `~/.gemini/tmp/<project-hash>/chats/session-YYYY-MM-DDTHH-MM-<session-prefix>.json`
- Primary observed companion stores:
  - `~/.gemini/tmp/<project-hash>/logs.json`
  - `~/.gemini/history/<project-hash>/`
- Strongest message-level fields observed in session JSON:
  - top-level: `sessionId`, `projectHash`, `startTime`, `lastUpdated`, `messages`
  - per-message: `type`, `timestamp`, `content`
  - Gemini-only companions: `model`, `thoughts`, `toolCalls`, `tokens`
- Shared-state candidates observed under the same global root:
  - `~/.gemini/settings.json`
  - `~/.gemini/google_accounts.json`
  - `~/.gemini/mcp-oauth-tokens-v2.json`
  - `~/.gemini/oauth_creds.json`
  - `~/.gemini/GEMINI.md`
- Negative result for the target repo:
  - no repo-local `.gemini/` directory
  - no repo-local `GEMINI.md`
  - no current-project hash directory yet for `/Users/chenjing/dev/chat-collector`
- Working conclusion:
  - clean CLI transcript extraction should start from `~/.gemini/tmp/<project-hash>/chats/session-*.json`
  - `logs.json`, `history/`, `thoughts`, `toolCalls`, token counters, hook output, and checkpoint residue should be treated as non-memory transcript noise by default

## Provenance And Local Install

Observed local CLI install:

- binary path: `/opt/homebrew/bin/gemini`
- resolved entrypoint: `/opt/homebrew/lib/node_modules/@google/gemini-cli/dist/index.js`
- observed version: `0.26.0`

A direct sandboxed launch attempt on `2026-03-14` failed because the environment blocked a localhost auth listener and blocked creation of a new current-project temp directory. That failure still yielded useful evidence:

- the attempted project temp dir for `/Users/chenjing/dev/chat-collector` was `~/.gemini/tmp/405eda4350775ff5078564a943938aa644a52df29bb6db3f5ef29353e3d79edb`
- the failure stack named `ChatRecordingService.initialize`
- the emitted error report embedded a startup context object shaped like Gemini model input, with `role` and `parts[].text`

This matched the installed source code and confirmed that transcript storage is initialized before normal chat turns continue.

## Observed macOS Roots

Primary roots with relevant state:

- `~/.gemini/`
- `~/Library/Application Support/cloud-code/`

Secondary support root checked:

- `/Library/Application Support/GeminiCli/settings.json`

Working split:

- `~/.gemini/` is the real user-state root for CLI config, memory, auth-adjacent files, encrypted MCP tokens, per-project temp state, checkpoint history, and extension sidecars
- `~/Library/Application Support/cloud-code/` existed on this host, but it did not hold transcript-bearing JSON or cache state for Gemini CLI
- `/Library/Application Support/GeminiCli/settings.json` is the source-defined macOS system settings path, but it was absent on this host

## ~/.gemini Findings

Observed top-level files and directories under `~/.gemini/` included:

- `GEMINI.md`
- `antigravity`
- `extensions`
- `google_accounts.json`
- `history`
- `installation_id`
- `mcp-oauth-tokens-v2.json`
- `oauth_creds.json`
- `settings.json`
- `skills`
- `state.json`
- `tmp`

This is a shared Gemini-family root rather than a transcript-only directory.

### tmp

Observed project-hash directories under `~/.gemini/tmp/` included several SHA-256-looking names such as:

- `2523ebac5c03f30000970b8f2c9e1ca5423c808a9ca963217d04ebc093aab492`
- `e9a13e9da3d0dcd08ee94ecd2a07993d0d506eb7c6115959959e4381d318a87b`
- `fe2a8f3f3db2171b5b99d47f16d91e125df8fb027be9ccd5a53a65147ce5ffa5`

Installed source confirmed the mapping:

- project temp dir = `~/.gemini/tmp/<sha256(projectRoot)>`
- project history dir = `~/.gemini/history/<sha256(projectRoot)>`

For the operator repo and this issue workspace:

- `/Users/chenjing/dev/chat-collector` -> `405eda4350775ff5078564a943938aa644a52df29bb6db3f5ef29353e3d79edb`
- `/Users/chenjing/code/workspaces/chat-collector/CHE-58` -> `3e3c96a6a57b1d6297e88adcde07d651a16e5a9b6a335a64502c0217710be669`

Neither hash directory existed at inspection time, which means Gemini CLI had not successfully persisted project-scoped state for either path on this machine.

### chats

Observed transcript files:

- path pattern: `~/.gemini/tmp/<project-hash>/chats/session-YYYY-MM-DDTHH-MM-<session-prefix>.json`
- observed file count across inspected temp roots: `16`

Observed top-level JSON keys:

- `sessionId`
- `projectHash`
- `startTime`
- `lastUpdated`
- `messages`
- optional `summary`

Observed session filename behavior from installed source:

- filenames are generated with prefix `session-`
- the timestamp is truncated to minute precision
- the final suffix is the first `8` chars of the session UUID

Observed message type counts across the `16` session files:

- `gemini`: `46`
- `user`: `22`
- `info`: `11`
- `error`: `4`

Observed message-key shapes:

- `user`, `info`, `error`
  - `content`
  - `id`
  - `timestamp`
  - `type`
- `gemini`
  - `content`
  - `id`
  - `model`
  - `thoughts`
  - `timestamp`
  - `tokens`
  - `toolCalls`
  - `type`

Observed from a sampled `gemini` row:

- `content` type: `string`
- `thoughts[]` item keys:
  - `description`
  - `subject`
  - `timestamp`
- `toolCalls[]` item keys:
  - `args`
  - `description`
  - `displayName`
  - `id`
  - `name`
  - `renderOutputAsMarkdown`
  - `result`
  - `resultDisplay`
  - `status`
  - `timestamp`
- `tokens` keys:
  - `input`
  - `output`
  - `cached`
  - `thoughts`
  - `tool`
  - `total`

Observed summary result:

- `1` of the `16` inspected session files already had a top-level `summary`
- the observed `summary` field type was `string`

Collector implication:

- `role` is not stored as a dedicated field in the session JSON
- `type` is the primary discriminator for message rows
- `user` and `gemini.content` are the cleanest transcript candidates
- `gemini.thoughts`, `gemini.toolCalls`, and `gemini.tokens` are useful for forensics but should be excluded from memory-oriented output by default
- `info` and `error` are session event residue, not durable dialogue turns

### logs.json

Observed companion files:

- path pattern: `~/.gemini/tmp/<project-hash>/logs.json`
- observed file count: `4`

Observed structure:

- JSON array
- observed row type counts: `user = 26`
- observed row keys:
  - `sessionId`
  - `messageId`
  - `timestamp`
  - `type`
  - `message`

Installed source showed this file is used by the logger's `getPreviousUserMessages()` path and is filtered by `type === "user"`.

Collector implication:

- `logs.json` is prompt-history support state, not a full bidirectional transcript
- it should not be merged blindly into session JSON output

### history

Observed project-hash directories under `~/.gemini/history/` looked like miniature Git repositories with:

- `.git/`
- `.gitconfig`
- `.gitignore`
- `.git/logs/HEAD`
- `.git/objects/`

Installed source confirmed this is a shadow Git repository used for checkpointing:

- repo path: `~/.gemini/history/<project-hash>/`
- work tree: the actual project root
- commit author: `Gemini CLI <gemini-cli@google.com>`

Collector implication:

- `history/` is checkpoint infrastructure, not transcript storage
- `.git/logs`, refs, and commits under this root are execution residue and should be excluded from chat collection

### settings, account cache, memory, and extensions

Observed `~/.gemini/settings.json` top-level keys:

- `security`
- `general`
- `ide`
- `mcpServers`

Observed nested keys:

- `security.auth.selectedType`
- `general.previewFeatures`
- `ide.enabled`
- `mcpServers.<serverName>`

Observed `~/.gemini/google_accounts.json` shape:

- `active`
- `old`

Installed source confirmed:

- `google_accounts.json` is a cache of the active Google account plus prior accounts
- `GEMINI.md` under `~/.gemini/` is part of hierarchical memory discovery
- source also supports repo-local `.gemini/settings.json`, `.gemini/commands`, `.gemini/skills`, and `.gemini/agents`

Observed extension sidecars:

- `~/.gemini/extensions/extension-enablement.json`
- `~/.gemini/extensions/nanobanana/.gemini-extension-install.json`

These are shared product state and extension metadata, not transcript content.

### Auth And MCP Tokens

Observed auth-adjacent files:

- `~/.gemini/oauth_creds.json`
- `~/.gemini/google_accounts.json`

Observed MCP token file:

- `~/.gemini/mcp-oauth-tokens-v2.json`
- mode: `0600`
- size at inspection: `490` bytes
- file type: ASCII text with no line terminators
- not directly parseable as JSON

Installed source explained the distinction:

- `mcp-oauth-tokens-v2.json` is an AES-256-GCM encrypted token store derived from host and username specific material, then decrypted into JSON in memory
- `oauth_creds.json` is a legacy fallback path; current OAuth credential storage migrates file-based credentials into a hybrid token storage path and removes the old file after migration when possible

Collector implication:

- both files are auth material, not transcript material
- `mcp-oauth-tokens-v2.json` should be treated as sensitive encrypted state
- `oauth_creds.json` may still exist on disk, but it is not the preferred long-term storage path in current CLI code

## Memory Commands And Repo Breadcrumbs

Installed source showed the `/memory` command family:

- `/memory show`
- `/memory add`
- `/memory refresh`
- `/memory list`

Memory discovery behavior is hierarchical:

- always consider the global `~/.gemini/GEMINI.md`
- search upward from the current directory toward the project root for `GEMINI.md`
- search downward from the current directory as well

Observed on this host:

- `~/.gemini/GEMINI.md` existed but was empty
- no repo-local `GEMINI.md` existed in `/Users/chenjing/dev/chat-collector`
- no repo-local `GEMINI.md` existed in `/Users/chenjing/code/workspaces/chat-collector/CHE-58`
- no repo-local `.gemini/` directory existed in either path
- no `commands/` or `agents/` directory was observed under `~/.gemini/`

Working conclusion:

- repo-local Gemini breadcrumbs are supported by the product design
- none were present for the target repo on this machine

## Hooks, MCP, And Execution Noise

Installed source showed hook event payloads always include:

- `session_id`
- `transcript_path`
- `cwd`
- `hook_event_name`
- `timestamp`

Additional hook payloads can also include:

- `tool_name`
- `tool_input`
- `tool_response`
- `mcp_context`
- `llm_request`
- `llm_response`
- `prompt`
- `prompt_response`

Collector implication:

- hooks can point back to the session JSON through `transcript_path`
- hook payloads, MCP context, tool responses, prompt-response wrappers, and execution output should not be treated as user-assistant transcript turns by default
- the cleanest source remains the session JSON itself, with selective filtering inside `gemini` messages

## cloud-code Findings

Observed under `~/Library/Application Support/cloud-code/`:

- `install_id.txt`
- `cloudcode_cli/cloudcode_cli/<build-id>/cloudcode_cli`

Observed local result:

- the nested `cloudcode_cli` file was a macOS arm64 executable
- no transcript-bearing `json`, `jsonl`, `sqlite`, or similar cache file was found under the inspected `cloud-code` subtree on this host

Collector implication:

- `cloud-code` is a real local root worth checking for Gemini Code Assist related artifacts
- on this macOS host it did not contain the primary Gemini CLI transcript store

## Shared vs Independent Storage

This machine supports a split conclusion rather than a purely isolated or purely shared one.

Evidence for shared storage:

- `~/.gemini/` holds CLI config, auth-adjacent files, memory, extensions, and non-CLI sibling state such as `antigravity`
- installed source supports repo-local `.gemini/` settings and global `GEMINI.md`
- Google documentation describes Gemini Code Assist agent mode as powered by Gemini CLI

Evidence for CLI-specific transcript storage:

- actual session files live under `~/.gemini/tmp/<project-hash>/chats/`
- companion `logs.json` and checkpoint `history/<project-hash>/` are also keyed by the same project hash
- no transcript-bearing data was found under `~/Library/Application Support/cloud-code/` on this machine

Working conclusion:

- Gemini CLI transcript storage is not isolated at the top-level root; it lives inside the shared `~/.gemini/` namespace
- however, the actual conversation files are in a CLI-specific per-project temp subtree under `tmp/<project-hash>/chats`
- config, memory, account cache, and token state are more clearly shared than transcript files
- direct transcript sharing between terminal Gemini CLI and Gemini Code Assist IDE or Cloud Shell remains unconfirmed on this host

## Negative Results

- No repo-local `.gemini/` directory was found in `/Users/chenjing/dev/chat-collector`
- No repo-local `.gemini/` directory was found in `/Users/chenjing/code/workspaces/chat-collector/CHE-58`
- No repo-local `GEMINI.md` was found in either path
- No `~/.gemini/tmp/<hash>/` directory existed yet for the operator repo path or this issue workspace path
- No transcript-bearing files were found under `~/Library/Application Support/cloud-code/`
- No system settings file was found at `/Library/Application Support/GeminiCli/settings.json`
- No `shell_history`, `checkpoints/`, or `checkpoint-*.json` artifact was observed under the inspected `~/.gemini/tmp/*` trees
- No `commands/` or `agents/` directory was observed under `~/.gemini/`

## Cross-Platform Note

Installed source defines path behavior as follows:

- user root defaults to `homedir()/.gemini`
- `GEMINI_CLI_HOME` can override that root entirely
- system settings path is platform-specific:
  - macOS: `/Library/Application Support/GeminiCli/settings.json`
  - Windows: `C:\\ProgramData\\gemini-cli\\settings.json`
  - Linux: `/etc/gemini-cli/settings.json`

Practical translation from the source and the observed macOS layout:

- Windows home-root guess, source-derived but unverified on a real host: `%USERPROFILE%\\.gemini\\`
- Linux home-root guess, source-derived but unverified on a real host: `$HOME/.gemini/`

Do not treat those non-macOS home paths as confirmed until they are inspected on real machines.
