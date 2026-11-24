# Pen input reliability

Version: **0.1.0**. Dependency-free Godot 4 GDScript contact tracking and reliability primitives. Copy this directory into another project; no autoload registration, native plugin, project settings, or global class names are required.

## API

Load `contact_tracker.gd` with a relative preload from your adapter. Create one tracker per independent input stream.

| API | Contract |
| --- | --- |
| `record_contact(position, time_seconds)` | Save the last accepted contact endpoint; caller supplies a monotonic timestamp in seconds. Read `last_position` and `last_time` for missed-release recovery. |
| `press_touch(index, position, time_seconds)` | Register or replace a contact, resetting its age and movement. |
| `move_touch(index, position)` | Track maximum distance from initial position, not accumulated path length. Unknown indices are ignored. |
| `release_touch(index)` / `clear_touches()` | Remove one/all touch records. Last accepted endpoint remains intact. |
| `is_resting(index, time_seconds, still_pixels, still_seconds)` | True for a known contact with maximum movement strictly below the supplied distance and age at least the supplied duration. |
| `rejects_emulated_mouse(is_mouse, device_id, emulated_device_id)` | Reject only mouse events from the injected emulation device. Does not deduplicate physical samples by timestamp or position. |
| `hover_ends_contact(eligible_contact, primary_button_down, pressure, release_threshold=0.001)` | Recover when eligible, button is up, and sanitized pressure is at/below threshold. Does not mutate state or emit events. |
| `mm_to_pixels(mm, pixels_per_inch, viewport_scale_x)` | Physical distance in viewport coordinates; scale denominator clamped to 0.001, preserving original behavior. |
| `sanitize_pressure(pressure)` | Nonfinite values become -1 (unknown); finite values remain unchanged. |

Preferences are arguments, not cached settings. Device IDs, PPI, viewport scale, pressure, button state, source eligibility, and clock readings all come from the caller. Positions and distance thresholds must share coordinates; timestamps for a contact must share a monotonic clock. The helper neither queries Time nor reads Input, OS, Engine, Profile, or Device.

## Standalone tests

Create an empty disposable Godot project containing `project.godot` with `config_version=5`, then copy the entire staged `shared/godot` directory to its `addons/gamecore`. From the repository root, run (replace `<fixture>` with that project's directory):

```powershell
& 'X:/Projects/ShammyVerse/tools/godot/Godot_v4.7.2-stable_win64_console.exe' --headless --path '<fixture>' --script res://addons/gamecore/pen_input/tests/test_contact_tracker.gd
```

Success: exit 0 and `PASS pen_input 0.1.0 (33 checks)`. No imports, application autoloads, external resources, or sleeps are required. Tests cover alternate PPI/scale, rest durations, pressure thresholds, synthetic device IDs, independent contacts, reset, boundary comparisons, maximum excursion, and recovery endpoint/time.

## InkFury integration and reuse review

InkFury's `input_router.gd` delegates touch bookkeeping, resting-contact detection, last-contact storage, hover-release checks, synthetic mouse filtering, pressure sanitization, and physical conversion to the vendored helper. Profile policy, pen detection/priority, pen-lock duration, source promotion, cancellation reasons, signals, probe telemetry, native singleton connection, platform mouse visibility and clock acquisition remain in the adapter.

Behavior is deliberately preserved: fresh physical down ends an existing non-finger stroke at its previous endpoint; hover recovery uses that same endpoint/time. Touch/native movement does not update the mouse recovery endpoint (the old router only updated it at stroke begin and mouse movement). Touch press replaces an existing index record before palm arbitration. Pen-like touch promotion, finite out-of-range pressure, and the existing eligibility of any active non-finger source are unchanged.

Reuse assessment: suitable for a drawing canvas, handwriting tool, or game that supplies its own device classification and preferences. The caller must arbitrate sources and decide when to call `record_contact`, cancel, end or start a stream. This is not a hardware backend, palm classifier, universal event deduplicator, or timeout-based release watchdog. Simulated tests cannot establish hardware driver behavior; native/Android/iOS paths still require device validation. No shared registry or external checkout is modified.
