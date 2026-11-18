# Viewport layout 0.1.0

Engine-neutral C++17 header. `ViewportLayout::Fit` fits a logical reference canvas
inside both pixel dimensions, with an optional maximum scale. It preserves at
least the reference logical area without cropping to a minimum scale. Invalid,
nonfinite or minimized dimensions return `Valid=false`, scale 1 and zero area.

Draw logical rectangles multiplied by `Scale`; divide pointer coordinates by
the same scale before `ViewportRect::Contains`. Rectangles include their top/left
edges and exclude bottom/right edges. `Centered` expects finite positive sizes;
consumers own panel sizing, wrapping, accessible font sizes and viewport policy.
No engine dependency, input handling, DPI discovery or font measurement is included.

First consumer: Critter Contraptions HUD and mouse exclusion. Its Unreal test
`Critter.UI.ViewportLayout` covers landscape, ultrawide, short and portrait windows,
panel separation, hit boundaries and invalid input. This is pilot reuse, not
second-consumer or device accessibility evidence.

Gully Giants also uses Fit for its HUD, including portrait-safe logical dimensions
and world-label screen exclusions. Its consumer Docs/POLISH_VALIDATION.md records
Win64 editor build, automation and limited rendered inspection. Packaged deployment
and a full resolution/accessibility matrix remain unverified.
