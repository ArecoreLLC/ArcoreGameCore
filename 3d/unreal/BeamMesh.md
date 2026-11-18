# Unreal beam mesh adapter 0.1.0

Engine-specific header for Unreal 5.8.4, Win64, 3D. This is not a portable C++
rule or a cross-engine implementation. Requires Core, CoreUObject and Engine.

ConfigureBeam makes an existing static mesh movable, noncolliding, nonoverlapping,
non-shadow-casting and irrelevant to navigation. UpdateBeam aligns its local Z
axis between finite endpoints, positions its center and sets diameter/length.
The mesh must be a centered 100-unit cylinder with a 100-unit diameter. Radius
and endpoints use Unreal world units. Invalid radius, nonfinite or degenerate
segments hide the old visual and return false. Valid segments return true.

Consumers own component lifetime, a bounded pool, material references and trace
authority. Hide unused segments every evaluation and on reset. Never use visual
meshes as ray blockers. Supply constructor-held asset references for cooking;
avoid development-only DrawDebug helpers for required gameplay presentation.

Install module unreal-beam-mesh at version 0.1.0 through GameCore sync. Include
BeamMesh.h only in an Unreal module. This adapter does not need a generated header.

Initial consumer: Lumen-Weaver. LumenWeaver.Light.Chamber exercises endpoint
alignment, invalid geometry, amber material, pool visibility, obstruction,
noncollision and reset using real Unreal components. Reproduce with the consumer's
Scripts/Build.ps1 and Scripts/Test.ps1. See consumer Docs/VALIDATION.md for actual
results and receipts. Listed coverage is not a new framework-side test execution.
No packaged build, second consumer or cross-engine parity is claimed.
