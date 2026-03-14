# Agent + Execution Context Inventory

Updated: `2026-03-14`

Canonical machine-readable inventory:
`src/llm_chat_archive/inventory/agent_execution_inventory.json`

This ticket stops at market inventory and queue shaping. It does not finish full storage-path reverse engineering for each agent.

## Split Rules

- One row equals `product + execution context`.
- `execution_context` is the first split axis: `standalone_app`, `cli`, `ide_native`, `ide_extension`, `protocol_hosted`, `remote_cloud_agent`, `browser_workspace`, `manager_surface`.
- `state_gravity` is the second axis: `local_first`, `hybrid`, `cloud_first`, `dual_source`.
- `priority` is for the next path-research slice, not product quality.
- Detailed path work should start `macOS -> Windows -> Linux` because the current operator environment is macOS.
- Remote contexts stay in scope when they belong to a target product family or may leave useful local bridge artifacts.

## Queue Summary

- `P0` has `11` entries. These are the immediate detailed path-research queue.
- `P1` has `16` entries. These are strong secondary candidates after the first local collectors land.
- `P2` has `6` entries. These are mostly cloud-first and should be researched only for local bridge residue or after a concrete operator need appears.

## Immediate Queue (`P0`)

- `codex_cli`, `codex_ide_extension`, `codex_app`: same OpenAI family, but terminal, IDE bridge, and app surfaces are likely to persist different local artifacts.
- `claude_code_cli`, `claude_code_ide`: Anthropic's highest-yield local coding surfaces.
- `gemini_cli`, `gemini_code_assist_ide`: Google explicitly exposes both terminal and IDE agent contexts, and some cache locations are already documented.
- `cursor_desktop_agent`, `cursor_cli`: Cursor's native editor and terminal agent should be investigated separately.
- `windsurf_editor_cascade`: native editor remains the highest-yield Windsurf context, with official filesystem clues for memories.
- `antigravity_editor_view`: repo target source, but public documentation is sparse enough that it needs an early dedicated path investigation.

## Secondary Queue (`P1`)

- `claude_desktop`: likely separate storage patterns for ordinary desktop chat, desktop extensions, and Cowork preview.
- `github_copilot_ide_agent_mode`, `github_copilot_cli`: large market share and meaningful local state, but storage behavior likely differs by editor and mode.
- `augment_ide_agent`, `augment_auggie_cli`: high collector value, especially because checkpoints, memories, and task-manager artifacts are part of the product model.
- `amp_cli`, `amp_cli_ide_connected`: as of `2026-03-14`, Amp should be treated as CLI-first because the extension shutdown was announced for `2026-03-05`.
- `continue_ide_agent`, `continue_cli`: same product family, clearly split between IDE and terminal contexts.
- `cline_extension`, `cline_cli`: same reason as Continue; the product now spans editor and terminal contexts.
- `roo_code_extension`: strong local candidate, distinct from Roo Cloud.
- `aider_cli`: likely one of the simpler local-first collectors to implement once the first target sources are done.
- `zed_agent_panel_hosted`, `zed_external_agent_panel`: host-side traces may be useful even when Zed itself says it does not store prompts or code context by default.
- `antigravity_manager_view`: likely a different storage shape from Antigravity Editor View because it acts as an orchestration surface.

## Observe / Defer (`P2`)

- `codex_cloud`, `cursor_background_agents`: target families, but canonical history is likely remote; inspect only local handoff residue first.
- `github_copilot_coding_agent`, `augment_remote_agent`, `roo_code_cloud`, `replit_agent_workspace`: cloud-first contexts where local collection value is unclear without exports or explicit bridge artifacts.

## Official Clues Already Worth Carrying Forward

- Windsurf docs mention config and memories under `~/.codeium/windsurf`, including `~/.codeium/windsurf/memories`.
- Gemini Code Assist docs mention macOS cache roots under `~/Library/Application Support/cloud-code` and `~/Library/Application Support/google-vscode-extension`.
- Continue docs mention local config in `~/.continue/config.yaml`.
- GitHub Copilot docs mention personal skills under `~/.copilot/skills` or `~/.claude/skills`.
- Augment docs mention task-manager data under `~/.augment`.

## Notes For The Follow-up Ticket

- `CHE-49` should consume the JSON inventory directly and generate one detailed path ticket per `queue_key`, ordered by `priority` and then `support_track`.
- `protocol_hosted` rows need dual-source checks. The host product and the embedded agent may both store useful history.
- `manager_surface` rows should be treated as separate from `ide_native` rows even when they belong to the same product family.
- Public documentation for Antigravity is thinner than for the other target sources. The follow-up path ticket should start by verifying the product's local install layout before assuming a standard VS Code fork layout.
