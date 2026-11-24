# Reuse review — 0.1.0

Boundary: compact sample format, JSON parsing and explicit evaluator orchestration.
The only dependency is stroke data in ../strokes. All imports are relative, with
no global declarations. Two synthetic evaluators (length scaled by record metadata
and sample count) demonstrate reuse without Ink Fury glyphs, tiers, or tuning.

The original TelemetryCodec class stays at its existing path and constructs
InkStroke subclasses on decode. The CLI delegates parsing, validated decoding and
callback evaluation, while retaining file discovery, cast selection, game history,
tuning, glyph evaluation and CSV/report policy. It warns and skips invalid sample
records. Metadata validation is a domain-adapter responsibility; the CLI is not a
fully hardened parser for arbitrary malicious game-context dictionaries.

Valid sample wire precision and game evaluation are preserved. Malformed strokes
now fail atomically instead of indexing mismatched arrays or silently coercing bad
values. Partial/mismatched tilt arrays are rejected; fully omitted legacy tilt is
supported. Empty convenience results remain ambiguous; checked APIs are preferred.

Limitations: synchronous replay only, no scheduling or event playback into an OS,
no streaming quota, no exception interception inside evaluator callbacks. Existing
game telemetry/recognition/pressure/motion tests remain unchanged for the parent
full-suite run. Isolated tests and copied-wrapper compatibility checks passed;
real telemetry CLI end-to-end execution is deferred to the parent integration run.
