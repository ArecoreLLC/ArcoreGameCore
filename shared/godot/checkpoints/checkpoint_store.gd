extends RefCounted
## Alternating checkpoints: never truncate the current valid slot while saving its successor.
## Incomplete writes fail JSON/checksum validation and the previous slot remains loadable.
## Call load_value before saving an existing prefix; one writer owns each prefix.
## encode(value) returns JSON-compatible data; validate(parsed) returns a value or null.
const VERSION := "0.1.0"
const MAX_BYTES := 262144
const MAX_SEQUENCE := 1000000000
var prefix: String
var sequence := 0
var active_slot := -1
var status := "new"

func _init(path_prefix: String) -> void:
	prefix = path_prefix

func path(slot: int) -> String:
	return prefix + (".a.json" if slot == 0 else ".b.json")

func load_value(validate: Callable) -> Variant:
	var best: Variant = null
	var existing := 0
	var invalid := 0
	sequence = 0
	active_slot = -1
	for slot in 2:
		if not FileAccess.file_exists(path(slot)):
			continue
		existing += 1
		var entry := read_entry(slot, validate)
		if entry.is_empty():
			invalid += 1
			continue
		if int(entry["sequence"]) > sequence:
			sequence = int(entry["sequence"])
			active_slot = slot
			best = entry["value"]
	status = "recovered" if best != null and invalid > 0 else ("restored" if best != null else ("unreadable" if existing > 0 else "new"))
	return best

func read_entry(slot: int, validate: Callable) -> Dictionary:
	var file := FileAccess.open(path(slot), FileAccess.READ)
	if file == null:
		return {}
	if file.get_length() > MAX_BYTES:
		file.close()
		return {}
	var text := file.get_as_text()
	file.close()
	var parser := JSON.new()
	if parser.parse(text) != OK:
		return {}
	var parsed: Variant = parser.data
	if not parsed is Dictionary or not _valid_sequence(parsed.get("sequence")):
		return {}
	if not parsed.get("payload") is String or not parsed.get("checksum") is String:
		return {}
	var payload: String = parsed["payload"]
	if payload.sha256_text() != parsed["checksum"]:
		return {}
	if parser.parse(payload) != OK:
		return {}
	if not validate.is_valid():
		return {}
	var value: Variant = validate.call(parser.data)
	return {"value": value, "sequence": int(parsed["sequence"])} if value != null else {}

func save_value(value: Variant, encode: Callable, validate: Callable) -> bool:
	if not encode.is_valid() or not validate.is_valid() or sequence >= MAX_SEQUENCE:
		return false
	var payload := JSON.stringify(encode.call(value))
	var target := 1 if active_slot == 0 else 0
	var next_sequence := sequence + 1
	var envelope := JSON.stringify({"sequence": next_sequence, "payload": payload, "checksum": payload.sha256_text()})
	if envelope.to_utf8_buffer().size() > MAX_BYTES:
		return false
	var file := FileAccess.open(path(target), FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(envelope)
	file.flush()
	var error := file.get_error()
	file.close()
	if error != OK:
		return false
	var verified := read_entry(target, validate)
	if verified.is_empty() or int(verified["sequence"]) != next_sequence:
		return false
	active_slot = target
	sequence = next_sequence
	return true

static func _valid_sequence(value: Variant) -> bool:
	if typeof(value) != TYPE_INT and typeof(value) != TYPE_FLOAT:
		return false
	var number := float(value)
	return is_finite(number) and number == floor(number) and number >= 1 and number <= MAX_SEQUENCE
