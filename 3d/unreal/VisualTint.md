# Unreal visual tint 0.1.0

Unreal-only initialization adapter. CreateTint creates and assigns one dynamic
material to slot zero, using a caller-supplied parent and vector parameter (Color
by default). Null parents and nonfinite colors are rejected without replacing the
existing material. HDR colors are allowed. Retain the instance for animation;
never call per frame. Does not change collision, visibility, geometry or shadows.
The caller must keep a cook-referenced parent exposing the chosen parameter.

Initial consumer Lumen-Weaver uses engine EmissiveMeshMaterial for mirror response,
receiver/bridge and patrol cues. Consumer Light.Chamber tests validate assignment,
invalid input and gameplay collision independence. See its Docs/VALIDATION.md for
executed evidence. No packaged or second-consumer validation is claimed.
