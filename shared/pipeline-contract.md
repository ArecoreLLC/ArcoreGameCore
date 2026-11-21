# Standardized Pipeline & Handoff Metadata Contract

All ArcoreGameCore pipelines and new pipeline proposals follow a single standardized schema so they can be listed in the GameCore **Pipelines** tab, exported as Markdown or JSON, and promoted into `workflows/<id>/` when implemented.

## Required Fields (`pipelines.json` / `workflows/proposals/<id>.json`)

- `id`: kebab-case identifier (e.g. `adaptive-music-stems`)
- `title`: human-readable pipeline name
- `status`: `active` | `scaffold` | `exploratory` | `proposal` | `draft`
- `kind`: `existing` | `proposal`
- `source_component`: originating tool, studio, or repo (e.g. `Suno MCP`, `ArcoreModelForge`)
- `target_component`: consuming engine or repo (e.g. `Unreal 5.8.4`, `Godot 4.x`)
- `summary`: concise 1–2 sentence scope
- `handoffs`: ordered list of `{ "from": string, "to": string, "artifact": string, "contract": string }`
- `stages`: ordered list of `{ "step": string, "owner": string, "tool_or_guide": string, "acceptance": string }`
- `guide_path`: repo-relative path to the Markdown guide (e.g. `workflows/adaptive-music-stems/README.md`)
- `updated_at`: UTC ISO-8601 timestamp
