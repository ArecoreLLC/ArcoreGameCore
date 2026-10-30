# Arcore3dGameDesignFramework

A reusable game-development foundation distilled from ShammyVerse: preserve editable sources, build small playable increments, review real output, and turn each iteration's findings into a better process.

Status: initial process framework, 2026-10-30. This folder contains guidance and templates, not an executable game starter. ShammyVerse uses Godot and Blender; the requested framework name is retained. The first version is engine-independent. An Unreal Engine implementation and any Google ARCore integration are separate decisions, not existing capabilities.

## Start here

1. Read the [ShammyVerse process review](SHAMMYVERSE_REVIEW.md) for strengths, gaps, and supporting evidence.
2. Copy the [project brief](templates/PROJECT_BRIEF.md) into the next game's documentation and define its first playable experience.
3. Follow the [development process](DEVELOPMENT_PROCESS.md), using an [iteration record](templates/ITERATION_RECORD.md) for each meaningful change.
4. Use the [framework boundaries](FRAMEWORK_BOUNDARIES.md) to decide what to reuse, adapt, or implement separately.
5. Apply the [validation guide](VALIDATION.md) and choose the next item from the [improvement backlog](IMPROVEMENT_BACKLOG.md).

Additional templates: [asset record](templates/ASSET_RECORD.md) and [decision record](templates/DECISION_RECORD.md).

For children designing games, use the [printable grade-level Word workbooks](templates/kids/README.md), with separate documents for initial design, new features, new level design, and character design at each grade. Kindergarten through grade 4 emphasize drawing, storytelling, and simple rules; grades 5 through 10 progress through branching choices, gameplay loops, state changes, and playtesting.

## Principles to carry forward

- Preserve the last reviewed source and its evidence before changing it.
- Give each iteration one clear outcome and explicit behaviors to preserve.
- Review both the authored asset and its appearance and behavior in the game.
- Separate visual complexity from gameplay collision and control.
- Make important gameplay states easy to reach through isolated development fixtures.
- Distinguish functional checks, visual review, listening review, and performance measurements.
- Keep current instructions short; preserve historical decisions in dated records.
- Promote a technique into the framework when a real project demonstrates its value.

## Scope and evidence

The initial review covers repository workflows, selected iteration logs, maintenance code, save code, project configuration, and Git history through `0fb6bb40e0fa7b90be7bb5f0030d4b72d44a2889`. The working tree also contains in-progress Tsunami v019 changes; references to v019 are working-tree evidence, not a committed release baseline. Historical test results are attributed to their logs; this documentation pass did not rerun the game or benchmarks.

Case-study links point back to the ShammyVerse checkout at `X:/Projects/ShammyVerse`. If this folder is copied elsewhere, preserve a source-checkout reference or rewrite those links. The templates and process guidance can be used independently.

## Evolving the framework

Use this foundation on one new playable slice before extracting a general runtime library. After each milestone, record one strength worth retaining, one recurring source of rework, and one measurable process experiment. Update the relevant guide and backlog together. Keep project-specific characters, story, tuning, and art outside the shared foundation.

### Revision history

| Date | Revision | Change |
|---|---|---|
| 2026-10-30 | 0.1 | Initial ShammyVerse review, reusable process, extraction boundaries, validation guidance, backlog, and four templates. |
