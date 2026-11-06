# Wizard templates

A wizard template (`workflows/<id>/wizard.json`) is the **single source of truth** for a guided workflow. The GameCore hub renders its forms from it, the runner and CLI execute its stages, and ArcoreFlow nodes are generated from it. Do not hand-write a second definition of the same steps anywhere else.

- [wizard-template.schema.json](wizard-template.schema.json): structure (JSON Schema 2020-12).
- `tools/validate_wizards.py`: enforces the schema plus cross-references: known ids, stages ordered so every input artifact is produced earlier, each artifact produced once, every field shown in a step and consumed by a stage, defaults and presets within bounds, and honest status claims.

## Model

| Part | Purpose | Consumed by |
|---|---|---|
| `fields` | Typed user inputs with defaults, bounds, widgets and `visible_when`. `implemented: false` (the default) means the runner cannot honour the field yet and the hub must show it as unavailable. | Hub forms, runner, Flow node config |
| `presets` | Named field values. Never include approved branding text. | Hub |
| `capabilities` | Tools, hardware, providers and fonts, with registered probe ids (never shell strings). | Readiness checks |
| `artifacts` | Outputs passed between stages, each with a media type. | Runner, Flow ports and lineage |
| `stages` | Runnable units in dependency order: adapter id, inputs, outputs, checks, `flow_category` (`game`, `music`, `media`) and `implementation` (`not_started`, `script_only`, `parameterized`, `verified`). | Runner, Flow nodes |
| `wizard.steps` | How the hub groups fields and stages into screens, with previews and review gates. | Hub only |
| `acceptance` | `passed` / `failed` / `blocked` / `not_run`. A passed check needs evidence; a no-AI badge needs a passed `no_ai_run`. | Hub badges, reviewers |

## Downstream MCP calls

A stage's optional `calls` list names the downstream MCP tools the hub calls for it. Each call gives the server and tool from `shared/ecosystem.json` → `mcp.servers`, its purpose, its status (`proposed` until verified against the real server), `writes`, and arguments. A string argument of the form `field:<id>` or `artifact:<id>` refers to that stage's inputs, at any depth; anything else is a literal value. `results` maps output artifacts to what the tool returns. Agents never call these servers directly: they register only the hub MCP. See [the hub design](../../docs/GAMECORE_HUB_AND_WIZARD_DESIGN.md#mcp-one-registered-entry-point).

## ArcoreFlow nodes

ArcoreFlow's optional **gamedev** node pack (categories Game, Music and Media) is generated from these templates. Each stage becomes one node, `flow_category` sets its palette category, and artifact media types become typed ports. After changing a template, regenerate the pack from the ArcoreFlow checkout with `pnpm packs:gamedev`. `pnpm packs:gamedev:check` reports drift. Business deployments of Flow never show the pack: it appears only when the deployment offers it and a user turns it on.

## Rules

- Stage status must match reality. `script_only` means a production script exists but needs code edits; the template status cannot be `implemented` until every stage is `verified`.
- A template that claims `ai_required: false` cannot contain a stage whose assistance is `required`.
- Adapters receive typed values, never interpolated shell text.
