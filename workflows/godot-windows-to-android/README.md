# Godot Windows → Android

**Status:** assisted platform-adaptation scaffold. This ports a Godot project, not a Windows executable. It does not promise export parity by changing one preset.

## Inputs

Use the [shared contract](../../shared/migration-contract.md), the working source project and Windows baseline, pinned Godot/export-template versions, language and native-plugin inventory, Android toolchain and named test device. Choose [2D](../../2d/README.md) or [3D](../../3d/README.md). Check language/plugin compatibility before implementation.

## Mapping

| Windows assumption | Android adaptation | Acceptance focus |
|---|---|---|
| Keyboard/mouse | Named actions with touch/controller bindings | Simultaneous move/look/interact; release/cancel |
| Fixed window/UI size | Responsive layout, safe areas and orientation policy | Readability and no covered controls |
| Desktop file paths | Godot user storage and lifecycle-aware saves | Suspend/resume, relaunch, isolated save |
| Desktop shaders/quality | Device-tested renderer and quality profile | Visual correctness, frame time and heat |
| Desktop plugins/services | Android-compatible dependency or explicit fallback | No silent missing gameplay features |

## Checklist

- [ ] Record input actions, desktop-only assumptions, renderer and dependencies.
- [ ] Select device, supported orientation, performance budget and test duration.
- [ ] Implement touch/UI and lifecycle handling without changing desktop bindings.
- [ ] Configure Android SDK/JDK/export templates for the selected engine version.
- [ ] Build a debug APK and test on real hardware; retain logs and screenshots.
- [ ] Re-run the Windows baseline to catch shared-code regressions.

## Outputs and acceptance

Deliver adaptation changes, reproducible export instructions and device test evidence. The [worked example](example.md) covers controls and lifecycle. Distribution/signing and store submission are separate authorized steps; never commit keys or passwords. An Android preset or successful APK build alone is not a completed port.

Consult [Godot Android export](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_android.html) for the selected version. C# support and native extensions require explicit compatibility checks. The older [export setup notes](../../docs/EXPORT_SETUP.md) remain historical, not a current toolchain guarantee.
