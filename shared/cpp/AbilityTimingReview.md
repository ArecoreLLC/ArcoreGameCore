# Ability timing reuse review — 2026-11-24

Workflow: game-project-integration / 3d. Target: Unreal 5.8.4 Win64, C++.
Baseline: existing dirty consumer and framework worktrees preserved; existing scan,
disguise, extraction and presentation behavior covered by twelve consumer tests.

Decision: parameterize CombatWindow, retain WorldRing. CombatWindow owns finite
active/recovery timing only. Add read-only deadline accessors for replication;
authority, clock synchronization, movement, teams and reveal policy stay in the
consumer. No engine imports or assets enter the portable helper. WorldRing is an
Unreal Canvas adapter, intentionally not an occlusion-aware world material.
Alternate synthetic case: zero-duration action and long recovery, plus rejected
restart preserving deadlines. Existing melee-window tests remain applicable.
Version: combat-window 0.3.0 -> 0.4.0, additive accessors; world-ring 0.2.0 unchanged.
Acceptance: portable boundary tests, native burst lifecycle tests, dedicated-server
RPC/replication probe, rendered HUD review. No cross-engine or latency claim.

Final admission: concurrent compatible recovery-progress work consolidated the
header at 0.5.0; Haunt and Haul selects that version. PresentationMotion 0.5.0
preserves default pulse behavior, and WorldRing 0.3.0 adds normalized progress
rendering used by the exit overlay. Canonical portable tests were rerun after
consolidation. Consumer validation is recorded in its Docs/Validation/Refinement20261124.
