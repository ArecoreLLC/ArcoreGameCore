extends RefCounted
## Deterministic value-state evaluation and bounded simulation. Version 0.1.0.
## Reducer: (state: Dictionary, action: Dictionary) -> {next, resolution}, or {} to reject.
## State/action/result must contain value data (no Objects or Resources).

static func preview(state: Dictionary, action: Dictionary, reducer: Callable) -> Dictionary:
	var step: Dictionary = reducer.call(state.duplicate(true), action.duplicate(true))
	return step.duplicate(true)

## Pure commit: caller adopts returned `next`; rejection returns {}.
static func commit(state: Dictionary, action: Dictionary, reducer: Callable) -> Dictionary:
	return preview(state, action, reducer)

## Strict comparison preserves the first candidate on ties. -INF/NaN never win.
static func choose_best(candidates: Array, scorer: Callable, fallback: Variant = null) -> Variant:
	var best: Variant = fallback
	var best_score := -INF
	for candidate in candidates:
		var value := float(scorer.call(candidate))
		if value > best_score:
			best_score = value
			best = candidate
	return best

## chooser(state) -> action; terminal(state) -> bool. Stop on rejection, terminal,
## or attempt budget. Callbacks receive detached snapshots; no clock or RNG is used.
static func simulate(initial: Dictionary, chooser: Callable, reducer: Callable,
		terminal: Callable, max_steps: int = 100) -> Dictionary:
	var state := initial.duplicate(true)
	var trace: Array = []
	for index in maxi(0, max_steps):
		if bool(terminal.call(state.duplicate(true))):
			return {"state": state, "trace": trace, "reason": "terminal"}
		var action: Dictionary = chooser.call(state.duplicate(true))
		var step := commit(state, action, reducer)
		if step.is_empty():
			return {"state": state, "trace": trace, "reason": "rejected"}
		state = step["next"].duplicate(true)
		trace.append({"action": action.duplicate(true), "resolution": step["resolution"].duplicate(true)})
	return {"state": state, "trace": trace,
		"reason": "terminal" if bool(terminal.call(state.duplicate(true))) else "limit"}
