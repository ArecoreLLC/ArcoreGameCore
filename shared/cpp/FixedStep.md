# Fixed step 0.1.1

`AdvanceFixedSteps(seconds, quantum, maxSteps, remainder, callback)` advances a
caller-owned simulation in constant quanta. It returns the callback count and
retains a serializable fractional remainder. Pass finite positive time and quantum,
1–1024 maximum steps, and a remainder in [0, quantum). Invalid input is a no-op.
Stalls admit at most `quantum * maxSteps` seconds; excess time is discarded.
Rounding within 1e-10 of a step boundary is treated as that boundary.
Version 0.1.1 preserves the strict remainder bound when cap addition rounds up.

Callbacks must not mutate the remainder or reenter this function. Exceptions are
not transactional. Pause, completion, inventory, energy and saves belong to the
consumer. This is a bounded local simulation driver, not an offline or network
clock. No engine dependencies. Synthetic 60 Hz movement and 20 Hz production are
tested; second-game adoption and other compiler/platform validation remain open.
