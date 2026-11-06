# Subject profile taxonomy

`catalog.v1.json` is an engine-neutral draft vocabulary for AI-assisted interpretation of images, drawings, meshes, and game assets. It separates model-generated text from stable canonical IDs. Florence, another model, a manual trace, or mesh analysis may supply evidence; none of those sources defines the taxonomy.

The catalog contains 19 shared construction primitives, 12 application tags, 99 canonical parts, 16 composable traits, 13 topology templates, and 40 subject-family profiles. Coverage includes articulated characters and creatures, vegetation, vehicles, robots, buildings and infrastructure, terrain, clothing, appliances, containers, equipment, and furniture. Profiles describe expected ranges rather than asserting that every part is visible or present.

Traits add optional capabilities or parts without requiring a profile for every imaginable combination. For example, a fantasy creature may compose `profile.quadruped`, `trait.winged`, and `trait.horned`. Topology templates describe attachment relationships independently of any particular engine hierarchy.

## Mapping contract

1. Preserve the model's raw label and source evidence.
2. Normalize case, articles, singular/plural spelling, and known aliases.
3. Select zero or more candidate profiles from subject aliases.
4. Compose optional traits supported by visible evidence; do not infer them solely from a class stereotype.
5. Resolve ambiguous parts using location, geometry, topology, and cross-prompt agreement.
6. Use `part.unknown` or `part.ambiguous` when evidence is insufficient.
7. Record visibility separately from expected profile counts.
8. Require review before generating rig chains, colliders, damage zones, or destructive asset edits.

Aliases are search and mapping hints, not globally unique synonyms. For example, `body`, `trunk`, `arm`, and `cabin` can mean different things under different profiles. A mapper must use the selected profile and retain alternatives when context does not resolve them.

## Adapter boundary

The catalog does not prescribe engine nodes, skeleton names, physics behavior, or material graphs. Adapters translate canonical parts into a consumer:

- 2D drawing: circles, ellipses, capsules, axes, and visible contour completion.
- 3D blockout: spheres, ellipsoids, boxes, tapered cylinders, and freeform placeholders.
- Rigging and animation: reviewed joint chains, symmetry, gait families, and control groups.
- Gameplay: candidate collision, damage, attachment, interaction, or navigation regions.
- Asset management: tags, completeness checks, search aliases, and LOD group suggestions.

`spider.example.json` shows an evidence-backed instance. It deliberately leaves walking-leg and palp counts unresolved because the current image analysis does not establish their identities.

The `samples/` directory also contains generated expansion sheets for taxonomy testing. Each sheet is a four-panel reference with one subject per panel: `biology-expansion-sheet.png`, `soft-bodied-expansion-sheet.png`, `mechanical-expansion-sheet.png`, `infrastructure-expansion-sheet.png`, and `props-expansion-sheet.png`. The sheets are visual test fixtures; panel crops can be added later if a classifier requires one file per profile.

## Versioning

Canonical IDs are intended to remain stable within schema version 1. Add aliases freely when their meaning is profile-scoped. Renaming or splitting an ID requires a migration table and a taxonomy-version increment. A schema-version change is required for incompatible structural changes.

Validate with:

```powershell
python tools/validate_subject_taxonomy.py
python -m unittest discover -s tools/tests -p test_subject_taxonomy.py -v
```

This is a broad first pass. It has not been evaluated against a labeled multi-subject dataset, so coverage, topology, and count ranges are draft authoring guidance rather than anatomical or engineering certification.
