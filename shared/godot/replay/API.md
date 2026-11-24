# API — 0.1.0

telemetry_codec.gd:

- encode_checked(strokes: Array) -> {ok: true, data: Array} or {ok: false, error: String}.
- decode_checked(data: Variant, factory: Callable = Callable()) -> {ok: true, strokes: Array} or failure envelope.
- encode_strokes / decode_strokes: legacy Array convenience APIs; return [] on failure. Use checked APIs to distinguish a valid empty batch from an error.
- sanitize(value): legacy JSON preparation for numeric telemetry dictionaries, arrays, Vector2 and supported packed arrays. Converts NaN/Inf to null; not a serializer for arbitrary Objects or cyclic containers.

Wire format is an array of dictionaries with equal-length numeric t/x/y/p arrays.
Optional tx/ty must both be absent (zero tilt) or both have the same length.
Times are milliseconds relative to the earliest first sample across the batch.
Encoding quantizes t/x/y to 0.01, pressure to 0.0001, tilt to 0.001.
Absolute clock origin is intentionally lost; gaps between strokes are preserved.
Empty batches/strokes and duplicate times are valid. Decreasing per-stroke times,
missing required arrays, wrong types, nonfinite values and overflow on conversion
to packed storage are errors. Decode is atomic: failures expose no partial batch.
No pressure-range policy is imposed. Decoder does not repair timestamps.

The optional factory must return a strokes/ink_stroke.gd instance or subclass.
The game adapter supplies InkStroke.new() to preserve existing typed consumers.

recorded_replay.gd:

- parse_line(text) -> {ok: true, record: Dictionary}, or failure with JSON diagnostic.
- evaluate(record, evaluator, factory=Callable()) validates record.strokes and calls evaluator(record, decoded_strokes).
- Evaluator returns {ok: true, value: any} or {ok: false, error: String}. Returned success dictionaries may carry additional caller-owned fields. Invalid callable/return envelope becomes a failure.

Metadata is opaque and belongs to the evaluator. There is no event filtering,
implicit sorting, history, glyph lookup, tier inference, I/O, or hidden state.
A caller can close over state to accumulate results across ordered records.
Callbacks must report failures through the envelope: GDScript has no exception
catching around arbitrary callback runtime errors. Caller metadata must be
validated by its evaluator. There are no size quotas; bound untrusted input at
an I/O boundary before allocating/parsing large records.
