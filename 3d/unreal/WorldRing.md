# World ring 0.2.0

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
