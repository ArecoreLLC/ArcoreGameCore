# Example: touch exploration room

**Illustrative work packet, not a supplied Android build.** Target: one existing Godot 3D exploration room with movement, camera look, an interaction prompt and checkpoint saving. The same input/lifecycle method can be adapted to 2D.

## Scope and mapping

- Load only the controller, camera, interaction UI, save boundary and project input/export settings.
- Keep `move_left/right/forward/back`, `look`, `interact` and `pause` semantic actions. Map movement to a virtual stick, look to a separate drag region, and interaction to a button.
- Record the chosen orientation and safe-area policy. Test two simultaneous touches and ensure the UI does not consume the wrong touch.
- Save a checkpoint to an isolated test slot. Persist at a safe checkpoint/background transition rather than relying only on application exit.

## Acceptance procedure

1. On a named Android device, move and rotate the camera simultaneously, then interact while moving. Release/cancel all touches: motion stops.
2. Open/close pause repeatedly; background/resume the app. No stuck input, duplicate events or lost UI.
3. Reach checkpoint, background, relaunch and load the test slot. Expected checkpoint is restored; production saves remain untouched.
4. Verify UI on the selected aspect ratios/safe areas. If rotation is unsupported, confirm orientation stays locked.
5. Run a repeatable traversal for an agreed duration and frame-time budget. Record device, OS, renderer, settings, sustained performance and visual defects.
6. Re-run keyboard/mouse controls on Windows.

Expected artifacts: APK checksum, revision, export command/preset, device logs, input/lifecycle results and screenshots. **Current evidence status: all checks not_run.**

See the [guide](README.md) and [shared contract](../../shared/migration-contract.md). Signing for distribution and publishing are outside this example.
