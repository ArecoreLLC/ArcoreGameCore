# MCP-assisted modeling integration

## Referenced project

The initial plan called the model catalog **AssetForge** (formerly Model Vault). The reviewed Unreal consumer now calls its existing catalog/Blender integration **ModelForge**. It supplies editable source and versioned artifacts through the existing bridge; no hosted repository URL or package installation is assumed here.

**Status in GameCore:** integration guidance and an external implementation inventory. This scaffold does not ship an MCP client or invoke ModelForge or Blender.

**2026-11-02 inventory update:** the [Unreal integration guide](../../framework/UNREAL_INTEGRATION.md) catalogs the demonstrated external implementation: ArcoreOpenWorld's `Tools/modelforge_mcp.py`, `validate_modelforge_assets.py`, `model_review.py` and capture helpers, plus ArcoreWorldFramework's independent Blender validation and prepared-import adapters. Source hashes, native engine checks, retained failures and production-admission limits are recorded separately. GameCore links that implementation without installing a bridge or treating import results as blanket compatibility approval. The boundary below remains guidance for future generic integrations.

## Proposed tool boundary

1. Discover the connected server's actual capabilities and input/output schemas. Do not guess tool names, supported operations or permissions from this document.
2. Resolve a catalog asset or request a small modeling operation. Use the simpler tool where sufficient; use the Blender bridge only for operations requiring it.
3. Supply an explicit artifact/output destination, units, up axis, scale, format, material/texture requirements and budget (for example triangles and texture dimensions). Record the tool/version and input asset hash.
4. Return a compact summary and artifact references: operation, output IDs/paths, bounds, counts, warnings and validation results. Keep full tool logs as artifacts, not repeated prompt context.
5. Validate the actual exported artifact in the target engine: orientation, scale, normals, materials, rig/animations if present, collision needs, import errors and platform cost. A successful tool response is not proof of a usable model.

## Example work packet (not executed)

Create a generic low-poly switch housing for the [Godot → Unreal example](../../workflows/godot-to-unreal/example.md). First check whether an appropriately licensed catalog model already exists. Agree physical size, pivot and triangle budget, then choose the available simple-modeling capability or Blender bridge. Export to a mutually supported interchange format after discovery; do not assume a format or exporter is present.

Acceptance: correct measured dimensions, outward normals, expected pivot, no missing textures, and successful import into both pinned engine versions. Store source/export artifact hashes and the import report with the migration evidence. All checks are currently **not_run**.

## Permissions and portability

Respect server permissions and user approval for modifying assets, installing software, changing persistent access or publishing. Do not embed credentials, private filesystem paths, private asset data or signing keys in public workflow examples. Keep engine adapters and tool integration separate so changing the modeling tool does not rewrite gameplay modules.
