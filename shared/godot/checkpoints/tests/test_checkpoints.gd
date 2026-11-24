extends SceneTree
## Run in a disposable project; all test files stay under res://.
const Store = preload("../checkpoint_store.gd")
var checks := 0
var failures := 0
var prefix := "res://checkpoint_fixture_%d" % Time.get_ticks_usec()

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		printerr("FAIL: " + label)

func encode(value: Variant) -> Variant:
	return value

func validate(value: Variant) -> Variant:
	if value is Dictionary and value.get("revision") is float and value.revision >= 0:
		return value
	return null

func write_text(path: String, text: String) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	check(file != null, "fixture opens")
	if file != null:
		file.store_string(text)
		file.close()

func envelope(sequence: Variant, payload: String) -> String:
	return JSON.stringify({"sequence": sequence, "payload": payload, "checksum": payload.sha256_text()})

func _init() -> void:
	_run.call_deferred()

func _run() -> void:
	var store := Store.new(prefix)
	check(store.load_value(validate) == null and store.status == "new", "empty startup")
	check(store.save_value({"revision": 1}, encode, validate), "first verified save")
	check(store.active_slot == 0 and store.sequence == 1 and store.status == "new", "save state and unchanged load status")
	var first := FileAccess.get_file_as_string(store.path(0))
	check(store.save_value({"revision": 2}, encode, validate), "second verified save")
	check(store.active_slot == 1 and store.sequence == 2, "alternation")
	check(FileAccess.get_file_as_string(store.path(0)) == first, "previous bytes untouched")
	var fresh := Store.new(prefix)
	var loaded: Variant = fresh.load_value(validate)
	check(loaded != null and loaded.revision == 2 and fresh.status == "restored", "restart selects newest")
	# Each damaged envelope must fall back, including structurally valid JSON.
	var bad: Array[String] = ['{"interrupted":', '[]', '{}',
		JSON.stringify({"sequence": 2, "payload": '{"revision":2}', "checksum": "wrong"}),
		envelope(2, "not json"), envelope(2, '{"wrong_schema":2}'),
		envelope(0, '{"revision":2}'), envelope(-1, '{"revision":2}'),
		envelope(1.5, '{"revision":2}'), envelope(true, '{"revision":2}'),
		envelope("2", '{"revision":2}'), envelope(Store.MAX_SEQUENCE + 1, '{"revision":2}'),
		JSON.stringify({"sequence": 2, "payload": {}, "checksum": "x"}),
		JSON.stringify({"sequence": 2, "payload": "{}", "checksum": 4}),
		"x".repeat(Store.MAX_BYTES + 1)]
	for damage in bad:
		write_text(store.path(1), damage)
		loaded = fresh.load_value(validate)
		check(loaded != null and loaded.revision == 1 and fresh.status == "recovered", "corrupt generation fallback")
		check(fresh.sequence == 1 and fresh.active_slot == 0, "recovery state")
	check(fresh.save_value({"revision": 3}, encode, validate), "save after recovery")
	check(fresh.sequence == 2 and fresh.active_slot == 1, "recovery continues sequence")
	var protected := FileAccess.get_file_as_string(fresh.path(1))
	check(not fresh.save_value({"wrong_schema": 4}, encode, validate), "validator rejects readback")
	check(fresh.sequence == 2 and fresh.active_slot == 1, "failed verification does not advance")
	check(FileAccess.get_file_as_string(fresh.path(1)) == protected, "failed write preserves active bytes")
	check(not fresh.save_value({"revision": 4, "large": "é".repeat(Store.MAX_BYTES)}, encode, validate), "UTF-8 size bounded")
	check(not fresh.save_value({}, Callable(), validate), "invalid encoder rejected")
	check(not fresh.save_value({}, encode, Callable()), "invalid validator rejected")
	check(Store.new(prefix).load_value(validate).revision == 3, "restart after failed write")
	# Equal generations select A deterministically; sequence ceiling is readable but not writable.
	write_text(store.path(0), envelope(Store.MAX_SEQUENCE, '{"revision":8}'))
	write_text(store.path(1), envelope(Store.MAX_SEQUENCE, '{"revision":9}'))
	loaded = fresh.load_value(validate)
	check(loaded != null and loaded.revision == 8 and fresh.active_slot == 0, "tie chooses A")
	check(not fresh.save_value({"revision": 10}, encode, validate), "sequence exhaustion rejected")
	check(fresh.sequence == Store.MAX_SEQUENCE and fresh.active_slot == 0, "exhaustion preserves state")
	write_text(store.path(0), "broken")
	write_text(store.path(1), "broken")
	check(fresh.load_value(validate) == null and fresh.status == "unreadable", "both invalid")
	check(fresh.sequence == 0 and fresh.active_slot == -1, "failed load resets state")
	check(fresh.save_value({"revision": 0}, encode, validate), "reset after unreadable")
	var missing := Store.new(prefix + "/absent/save")
	check(not missing.save_value({"revision": 1}, encode, validate), "open failure")
	check(missing.sequence == 0 and missing.active_slot == -1, "open failure preserves state")
	# Non-null falsy values are valid callback results.
	check(fresh.load_value(func(_v: Variant) -> Variant: return false) == false, "false accepted as restored value")
	for slot in 2:
		DirAccess.remove_absolute(store.path(slot))
	if failures == 0:
		print("CHECKPOINTS_STANDALONE_PASS (%d checks)" % checks)
	quit(1 if failures else 0)
