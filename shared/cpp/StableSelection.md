# StableSelection 0.1.0

Engine-neutral score selection with hysteresis. `Select(candidates, count, margin)` returns an eligible nonnegative ID or -1. Caller supplies eligibility and score units; higher scores win. Retain the previous candidate unless a challenger beats its score by more than margin. A missing candidate is discarded immediately. Reset clears history. Null input clears selection; negative IDs/nonfinite scores are ignored; invalid margin becomes zero. Duplicate IDs use their highest score. First-pass ties resolve to the smallest ID.

Reuse decision: split-module. Selection has no spatial, input, time or presentation dependencies. Synthetic aim and work-priority fixtures demonstrate different score scales; these are not second-game validation. No allocation, engine, visibility query or networking. Consumer owns per-frame query cadence and authoritative action revalidation. Tests: shared/cpp/tests/StableSelectionTests.cpp.
