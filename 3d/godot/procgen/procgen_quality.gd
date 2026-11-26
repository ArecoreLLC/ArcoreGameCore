extends Node
## Quality presets for scenes built from arcore_procgen bundles: one setting
## that scales a whole game from an integrated GPU to a desktop card without
## touching level code. Add it as an autoload (any name; the examples use
## `Quality`). It tunes nodes as they enter the tree and re-tunes the scene
## after every scene change:
##
##   - loader scatter batches (`<world>/Scatter/<layer>/<cell>`): share of
##     instances drawn and draw distance
##   - GPUParticles3D: share of particles
##   - DirectionalLight3D: shadows on/off and shadow distance
##   - WorldEnvironment: SSAO and glow (only ever switched off, never on)
##   - the viewport: 3D render scale and MSAA
##
## Bake worlds at full scatter density. arcore_procgen stores each cell's
## instances in random order, so drawing a prefix (`visible_instance_count`)
## thins evenly and no rebake is needed per preset.
##
## Level code that spawns things (creatures, clouds, asteroids) can ask for
## `scaled(count)` or `value("detail")` when it builds them.
##
## The choice is saved to `save_path`. With no saved choice, integrated and
## software GPUs start on the first preset in `order` and discrete GPUs on
## `default_level`. `-- --quality=<name>` on the command line overrides both.

signal changed(level: String)

## Global shader uniform (float) carrying the preset's `range` multiplier.
const RANGE_GLOBAL := &"gc_range_scale"

## Preset names from lightest to heaviest; `toggle_key` cycles through them.
@export var order: Array[String] = ["low", "medium", "high"]
## Starting preset for discrete GPUs when nothing is saved.
@export var default_level: String = "high"
## Key that cycles presets (KEY_NONE disables it).
@export var toggle_key: Key = KEY_F6
@export var save_path: String = "user://quality.cfg"

## Per preset:
##   scale         3D render scale (FSR upscaling under Forward+, bilinear otherwise)
##   msaa          Viewport.MSAA_*
##   shadow_size   sun shadow atlas size; 0 switches sun shadows off
##   shadow_reach  multiplier on each sun's shadow distance
##   ssao, glow    false switches the effect off where a scene has it on
##   density       share of each scatter batch's instances drawn
##   range         multiplier on scatter draw distance
##   effects       share of particles; also what `scaled()` multiplies by
##   detail        free multiplier for consumer tessellation (`value("detail")`)
## Assign a new dictionary (and `order`) before `_ready` to change or add tiers.
var presets: Dictionary = {
	"low": {
		"scale": 0.67, "msaa": Viewport.MSAA_DISABLED, "shadow_size": 0, "shadow_reach": 0.0,
		"ssao": false, "glow": false, "density": 0.3, "range": 0.6, "effects": 0.4, "detail": 0.5,
	},
	"medium": {
		"scale": 0.85, "msaa": Viewport.MSAA_DISABLED, "shadow_size": 2048, "shadow_reach": 0.6,
		"ssao": false, "glow": true, "density": 0.6, "range": 0.8, "effects": 0.7, "detail": 0.75,
	},
	"high": {
		"scale": 1.0, "msaa": Viewport.MSAA_2X, "shadow_size": 4096, "shadow_reach": 1.0,
		"ssao": true, "glow": true, "density": 1.0, "range": 1.0, "effects": 1.0, "detail": 1.0,
	},
}

var level: String = ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	level = _initial_level()
	get_tree().node_added.connect(_on_node_added)
	get_tree().scene_changed.connect(func() -> void: apply.call_deferred())
	apply.call_deferred()


## Value of a preset field for the current level, e.g. `value("effects")`.
func value(key: String) -> Variant:
	return presets[level][key]


## A count scaled by the `effects` share (at least `minimum`).
func scaled(count: int, minimum: int = 1) -> int:
	return maxi(int(round(count * float(value("effects")))), minimum)


func set_level(new_level: String, save: bool = true) -> void:
	if not presets.has(new_level):
		return
	level = new_level
	if save and save_path != "":
		var cfg := ConfigFile.new()
		cfg.set_value("quality", "level", level)
		cfg.save(save_path)
	apply()
	changed.emit(level)


## Moves to the next preset in `order`, wrapping around.
func cycle() -> void:
	set_level(order[(order.find(level) + 1) % order.size()])


func _initial_level() -> String:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--quality=") and presets.has(arg.trim_prefix("--quality=")):
			return arg.trim_prefix("--quality=")
	var cfg := ConfigFile.new()
	if save_path != "" and cfg.load(save_path) == OK and presets.has(str(cfg.get_value("quality", "level", ""))):
		return str(cfg.get_value("quality", "level"))
	var discrete := RenderingServer.get_video_adapter_type() == RenderingDevice.DEVICE_TYPE_DISCRETE_GPU
	return default_level if discrete and presets.has(default_level) else order[0]


func _unhandled_input(event: InputEvent) -> void:
	if toggle_key != KEY_NONE and event is InputEventKey and event.pressed and not event.echo and event.keycode == toggle_key:
		cycle()


## Tunes the viewport and every node of the current scene to the preset.
func apply() -> void:
	var preset: Dictionary = presets[level]
	var viewport := get_viewport()
	viewport.scaling_3d_scale = preset.scale
	# FSR upscaling exists only in the Forward+ renderer; others fall back to bilinear.
	var fsr: bool = preset.scale < 1.0 and RenderingServer.get_current_rendering_method() == "forward_plus"
	viewport.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR if fsr else Viewport.SCALING_3D_MODE_BILINEAR
	viewport.msaa_3d = preset.msaa
	if int(preset.shadow_size) > 0:
		RenderingServer.directional_shadow_atlas_set_size(int(preset.shadow_size), true)
	# Shaders that fade scatter per instance (GameCore's toon modules) follow the same scale.
	# (Modules leave a note on Engine when they register a shared global, so it is added once.)
	if not ProjectSettings.has_setting("shader_globals/%s" % RANGE_GLOBAL) and not Engine.has_meta("shader_global_%s" % RANGE_GLOBAL):
		RenderingServer.global_shader_parameter_add(RANGE_GLOBAL, RenderingServer.GLOBAL_VAR_TYPE_FLOAT, 1.0)
		Engine.set_meta("shader_global_%s" % RANGE_GLOBAL, true)
	RenderingServer.global_shader_parameter_set(RANGE_GLOBAL, float(preset.range))
	if get_tree().current_scene != null:
		_tune_tree(get_tree().current_scene, preset)


## Content that arrives after a scene loads (scatter, creatures, particles) is
## tuned as it enters the tree.
func _on_node_added(node: Node) -> void:
	if level != "" and (node is MultiMeshInstance3D or node is GPUParticles3D):
		_tune(node, presets[level])


func _tune_tree(node: Node, preset: Dictionary) -> void:
	_tune(node, preset)
	for child in node.get_children():
		_tune_tree(child, preset)


func _tune(node: Node, preset: Dictionary) -> void:
	if node is MultiMeshInstance3D:
		var batch := node as MultiMeshInstance3D
		var layer := batch.get_parent()
		# Loader scatter lives under <world>/Scatter/<layer>/<cell>.
		if batch.multimesh == null or layer == null or layer.get_parent() == null or layer.get_parent().name != &"Scatter":
			return
		var total := batch.multimesh.instance_count
		batch.multimesh.visible_instance_count = -1 if preset.density >= 1.0 else maxi(int(ceil(total * float(preset.density))), 1)
		if not batch.has_meta("base_range"):
			batch.set_meta("base_range", Vector2(batch.visibility_range_begin, batch.visibility_range_end))
		var base_range: Vector2 = batch.get_meta("base_range")
		batch.visibility_range_begin = base_range.x * float(preset.range)
		batch.visibility_range_end = base_range.y * float(preset.range)
	elif node is GPUParticles3D:
		(node as GPUParticles3D).amount_ratio = preset.effects
	elif node is DirectionalLight3D:
		var sun := node as DirectionalLight3D
		if not sun.has_meta("base_shadow"):
			sun.set_meta("base_shadow", [sun.shadow_enabled, sun.directional_shadow_max_distance])
		var base: Array = sun.get_meta("base_shadow")
		sun.shadow_enabled = base[0] and int(preset.shadow_size) > 0
		sun.directional_shadow_max_distance = maxf(float(base[1]) * float(preset.shadow_reach), 10.0)
	elif node is WorldEnvironment and (node as WorldEnvironment).environment != null:
		var env := (node as WorldEnvironment).environment
		if not node.has_meta("base_fx"):
			node.set_meta("base_fx", [env.ssao_enabled, env.glow_enabled])
		var fx: Array = node.get_meta("base_fx")
		env.ssao_enabled = fx[0] and preset.ssao
		env.glow_enabled = fx[1] and preset.glow
