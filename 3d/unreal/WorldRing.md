# World ring 0.3.0

Unreal Canvas adapter for a bounded, projected XY ring. Call DrawWorldRing from
AHUD::DrawHUD with a world center and radius in centimeters. Segments clamp to
8–128; invalid position, radius or thickness draws nothing. Segments behind the
camera are omitted. This is a HUD overlay, not depth-tested world geometry.

`DrawWorldArc` accepts a start angle and signed sweep in radians (at most one
revolution). Zero or nonfinite sweeps draw nothing. Negative sweeps run clockwise.
`DrawWorldRing` delegates to a full arc, preserving the existing signature.
Lantern Heist uses arcs for a short guard-facing marker, not an occlusion or
detection boundary; rings show extraction range and timed decoy feedback.

The consumer owns event lifetime, color, accessibility, and ordering. No spawned actors,
dynamic materials or retained engine objects are required. Dungeon Dash Market uses it for
attack reach, hit feedback and the player's ground marker. Engine build and
rendered consumer smoke provide validation; packaged behavior is not yet verified.

## Normalized progress (0.3.0)

DrawWorldProgressRing composes the existing ring and arc, starting at -PI/2.
Finite progress clamps to [0,1]; nonfinite progress draws neither layer. Zero
keeps only the track. Size, segment bounds and camera clipping retain the arc
contract. Existing ring/arc callers are unchanged.

Reuse review: parameterize presentation only. No gameplay state, actors, clocks,
health rules or customer policy enter the adapter. Dungeon Dash Market supplies
health, patience and recovery ratios; a synthetic cooldown or capture meter uses
the identical contract. This is Unreal Canvas only, overlay rather than occluded
geometry. Second-consumer validation of this new helper remains not run.

Synthetic adapter boundaries: `python 3d/unreal/tests/TestWorldRing.py` uses a
minimal Canvas stub to test finite clamping, invalid inputs, segment bounds,
behind-camera omission and legacy ring/arc calls. This is not an Unreal renderer
or projection test. Dungeon Dash Market's rendered smoke supplies that evidence.

November 24, 2026: the synthetic contract check passed; Dungeon Dash Market's
Unreal 5.8.4 build, four automation tests, combat/demand/hazard scenarios and
rendered smoke passed. Dungeon/shop captures were inspected. Consumer evidence:
`Games/Dungeon-Dash-Market/Docs/REFINEMENT_VALIDATION.json` relative to the Projects
root. These checks do not establish packaged or second-consumer compatibility.
