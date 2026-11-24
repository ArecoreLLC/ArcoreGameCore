extends SceneTree
const Counters = preload("../cooldowns.gd")
const Driver = preload("../turn_driver.gd")
var failures := 0
var checks := 0

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		printerr("FAIL: " + label)

## Synthetic warehouse: transfer crates, then rest a loading station for two turns.
func transfer(state: Dictionary, action: Dictionary) -> Dictionary:
	var station: int = action["station"]
	if Counters.remaining(state["rests"], station) > 0:
		return {}
	state["crates"][0] += 1
	state["rests"] = Counters.committed(state["rests"], {station: 2})
	return {"next": state, "resolution": {"loaded": state["crates"][0]}}

func choose_station(state: Dictionary) -> Dictionary:
	for station in [10, 20, 30]:
		if Counters.remaining(state["rests"], station) <= 0:
			return {"station": station}
	return {"station": 10}

func _init() -> void:
	var counters := {10: 2, 20: 1, 30: 0, 40: -2}
	check(Counters.committed(counters, {50: 3}) == {10: 1, 50: 3}, "tick before arming; expire zero/negative")
	check(counters == {10: 2, 20: 1, 30: 0, 40: -2}, "counter input unchanged")
	check(Counters.committed({10: 4}, {10: 2}) == {10: 2}, "rearm replaces after tick")
	check(Counters.committed({10: 4}, {10: 0, 20: -1}) == {10: 3}, "nonpositive arm ignored")
	check(Counters.remaining({}, 999) == 0, "missing key ready")
	var initial := {"crates": [0], "rests": {}}
	var action := {"station": 10}
	var preview := Driver.preview(initial, action, transfer)
	check(initial == {"crates": [0], "rests": {}} and action == {"station": 10}, "preview isolates nested values")
	check(preview == Driver.commit(initial, action, transfer), "preview commit parity")
	check(Driver.commit(preview["next"], action, transfer).is_empty(), "rejected action does not tick")
	var finished := func(s: Dictionary) -> bool: return s["crates"][0] == 6
	var run := Driver.simulate(initial, choose_station, transfer, finished, 6)
	check(run["reason"] == "terminal" and run["trace"].size() == 6, "terminal on budget boundary")
	check(run == Driver.simulate(initial, choose_station, transfer, finished, 6), "deterministic replay")
	check(run["trace"][0]["resolution"]["loaded"] == 1 and run["trace"][5]["resolution"]["loaded"] == 6, "trace snapshots independent")
	check(run["trace"][3]["action"]["station"] == 10, "station reusable after two other commits")
	check(Driver.simulate(initial, choose_station, transfer, finished, 2)["reason"] == "limit", "bounded simulation")
	check(Driver.simulate(initial, choose_station, transfer, finished, -1)["trace"].is_empty(), "negative budget runs no steps")
	var blocked := {"crates": [0], "rests": {10: 2, 20: 2, 30: 2}}
	check(Driver.simulate(blocked, choose_station, transfer, finished)["reason"] == "rejected", "rejection stops without retry loop")
	check(Driver.simulate({"crates": [6], "rests": {}}, choose_station, transfer, finished)["trace"].is_empty(), "initial terminal invokes no reducer")
	check(Driver.choose_best([20, 10], func(_x: int) -> float: return 3.0) == 20, "ties preserve input order")
	check(Driver.choose_best([20], func(_x: int) -> float: return -INF, -1) == -1, "ineligible fallback")
	check(Driver.choose_best([], func(_x: int) -> float: return 0.0, -1) == -1, "empty fallback")
	check(Driver.choose_best([20], func(_x: int) -> float: return NAN, -1) == -1, "NaN does not win")
	# A second use: a budget planner, without counters or any combat concepts.
	var spend := func(s: Dictionary, a: Dictionary) -> Dictionary:
		s["budget"] -= a["cost"]
		a["cost"] = 999
		return {"next": s, "resolution": {"left": s["budget"]}}
	var choose_cost := func(s: Dictionary) -> Dictionary:
		s["budget"] = 999 # callback mutations must not corrupt the simulation
		return {"cost": 2}
	var stop := func(s: Dictionary) -> bool:
		var done: bool = s["budget"] <= 0
		s["budget"] = 999
		return done
	var budget := Driver.simulate({"budget": 6}, choose_cost, spend, stop)
	check(budget["state"]["budget"] == 0 and budget["trace"].size() == 3, "planner callbacks isolated")
	check(budget["trace"][0]["action"]["cost"] == 2, "reducer cannot mutate recorded action")
	if failures == 0:
		print("PASS gamecore.turns 0.1.0 (%d checks)" % checks)
	quit(1 if failures else 0)
