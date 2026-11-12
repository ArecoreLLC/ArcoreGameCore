# Exposure meter

Header-only C++14 detection accumulation in [ExposureMeter.h](ExposureMeter.h). Step receives authoritative visibility, elapsed seconds, time to detect from zero, and time to recover from full. Values clamp to [0,1]. Invalid/nonfinite time or nonpositive durations leave state unchanged and return false. Zero elapsed time is accepted. Full detection is not latched; consumers own terminal loss, immunity, spatial volumes, sight traces and restart.

No frame cap is applied: equal elapsed visible/hidden intervals produce the same result regardless of partitioning (within floating-point tolerance). Consumers must sample visibility at an appropriate simulation cadence; this rule cannot reconstruct visibility changes during a long frame.

Initial consumer: Lumen-Weaver's Night-Mare. Unreal automation covers partition invariance, saturation, recovery, invalid input, sight occlusion and terminal-state reset. Other engines remain unvalidated.
