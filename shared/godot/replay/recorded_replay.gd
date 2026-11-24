extends RefCounted
const Codec = preload("telemetry_codec.gd")

## Evaluator(record, strokes) returns {ok: true, value: Variant} or {ok: false, error: String}.
## No implicit filtering, session state, or domain-specific evaluation.
static func evaluate(record: Variant, evaluator: Callable, factory: Callable = Callable()) -> Dictionary:
	if not record is Dictionary:
		return {"ok": false, "error": "record must be a dictionary"}
	if not evaluator.is_valid():
		return {"ok": false, "error": "invalid evaluator"}
	var decoded := Codec.decode_checked(record.get("strokes", null), factory)
	if not decoded.ok:
		return decoded
	var result: Variant = evaluator.call(record, decoded.strokes)
	if not result is Dictionary or not result.get("ok", null) is bool:
		return {"ok": false, "error": "evaluator must return an ok envelope"}
	if not result.ok and not result.get("error", null) is String:
		return {"ok": false, "error": "evaluator failure must contain an error string"}
	return result

static func parse_line(line: String) -> Dictionary:
	var parser := JSON.new()
	var err := parser.parse(line)
	if err != OK:
		return {"ok": false, "error": "JSON line %d: %s" % [parser.get_error_line(), parser.get_error_message()]}
	if not parser.data is Dictionary:
		return {"ok": false, "error": "record must be a dictionary"}
	return {"ok": true, "record": parser.data}
