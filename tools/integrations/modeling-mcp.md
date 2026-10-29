# MCP-assisted modeling integration

## Referenced project

**AssetForge** (formerly Model Vault) is the current working name of the user's local, unpublished project. It began as a 3D model catalog and now includes simpler modeling tools plus a Blender bridge for more complex modeling. Its repository has not been pushed, so no repository URL, package, local path or live connection is assumed here. The final repository name remains undecided.

**Status:** integration design only. This scaffold does not ship an MCP client, invoke AssetForge or Blender, or claim compatibility has been tested.

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
