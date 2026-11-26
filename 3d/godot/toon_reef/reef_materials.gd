extends RefCounted
## Toon look for arcore_procgen reef layers: maps each scatter layer to a
## material (three-tone light, ink outline, palette variation) and to its draw
## settings. Colors come from the bake manifest's `presentation` block when
## present, so a rerolled recipe can restyle the reef without code changes.

const Atmosphere := preload("underwater_atmosphere.gd")

const DEFAULT_CORAL_PALETTE: Array[Color] = [
	Color(1.0, 0.45, 0.42), Color(1.0, 0.72, 0.28), Color(0.72, 0.48, 0.98), Color(0.30, 0.86, 0.84),
]

## Per-layer style. `kind` picks the shader; `color_key` / `palette_key` name a
## `presentation` entry that overrides the default colors (`lighten` brightens it).
## `range` is the draw distance in meters (0 = unlimited) and should stay inside the fog.
const LAYER_STYLES := {
	"kelp_forest": {
		"kind": "blade", "color_key": "kelp_color", "colors": [Color(0.18, 0.84, 0.48)],
		"sway": 0.38, "sway_speed": 1.6, "shadow": false, "range": 125.0,
	},
	"sea_grass": {
		"kind": "blade", "color_key": "grass_color", "colors": [Color(0.36, 0.88, 0.42)],
		"sway": 0.14, "sway_speed": 2.3, "shadow": false, "range": 80.0,
	},
	"seabed_rocks": {
		"kind": "prop", "color_key": "rock_color", "colors": [Color(0.32, 0.48, 0.60)], "lighten": 0.3,
		"rim": 0.14, "emission": 0.0, "outline": 0.03, "range": 140.0,
	},
	"pebbles": {
		"kind": "prop", "colors": [Color(0.52, 0.62, 0.70), Color(0.78, 0.66, 0.50), Color(0.40, 0.50, 0.62)],
		"rim": 0.10, "emission": 0.0, "shadow": false, "range": 60.0,
	},
	"grotto_sponges": {
		"kind": "prop", "color_key": "sponge_color", "colors": [Color(0.98, 0.46, 0.68)],
		"emission": 0.16, "outline": 0.022, "range": 140.0,
	},
	"tube_sponges": {
		"kind": "prop", "colors": [Color(1.0, 0.80, 0.25), Color(1.0, 0.56, 0.24), Color(0.80, 0.56, 1.0)],
		"emission": 0.18, "outline": 0.018, "sway": 0.05, "range": 120.0,
	},
	"coral_garden": {
		"kind": "prop", "palette_key": "coral_palette", "colors": DEFAULT_CORAL_PALETTE,
		"emission": 0.12, "outline": 0.016, "sway": 0.03, "shadow": false, "range": 120.0,
	},
	"brain_corals": {
		"kind": "prop", "colors": [Color(0.98, 0.62, 0.46), Color(0.94, 0.52, 0.72), Color(0.58, 0.82, 0.62)],
		"emission": 0.06, "outline": 0.022, "range": 130.0,
	},
	"table_corals": {
		"kind": "prop", "colors": [Color(0.42, 0.78, 0.92), Color(0.98, 0.70, 0.40), Color(0.74, 0.60, 0.98)],
		"emission": 0.08, "outline": 0.018, "range": 130.0,
	},
	"sea_fans": {
		"kind": "prop", "palette_key": "fan_palette",
		"colors": [Color(0.96, 0.36, 0.62), Color(0.98, 0.62, 0.30), Color(0.60, 0.44, 0.96)],
		"emission": 0.14, "sway": 0.12, "shadow": false, "range": 120.0,
	},
	"anemones": {
		"kind": "prop", "palette_key": "anemone_palette",
		"colors": [Color(0.98, 0.52, 0.84), Color(0.46, 0.94, 0.80), Color(1.0, 0.80, 0.36)],
		"emission": 0.22, "rim": 0.45, "sway": 0.10, "shadow": false, "range": 90.0,
	},
	"sea_urchins": {
		"kind": "prop", "colors": [Color(0.30, 0.20, 0.44), Color(0.16, 0.18, 0.30), Color(0.74, 0.26, 0.40)],
		"emission": 0.05, "rim": 0.4, "shadow": false, "range": 70.0,
	},
	"giant_clams": {
		"kind": "prop", "colors": [Color(0.42, 0.62, 0.98), Color(0.62, 0.42, 0.96), Color(0.30, 0.86, 0.72)],
		"emission": 0.2, "rim": 0.4, "outline": 0.02, "range": 120.0,
	},
	"staghorn_thickets": {
		"kind": "prop", "palette_key": "coral_palette", "colors": DEFAULT_CORAL_PALETTE,
		"emission": 0.1, "outline": 0.02, "sway": 0.02, "range": 140.0,
	},
	"tube_worms": {
		"kind": "prop", "colors": [Color(1.0, 0.30, 0.26), Color(0.98, 0.94, 0.88), Color(1.0, 0.52, 0.30)],
		"emission": 0.30, "sway": 0.06, "shadow": false, "range": 80.0,
	},
	"starfish": {
		"kind": "prop", "colors": [Color(1.0, 0.52, 0.24), Color(0.96, 0.30, 0.34), Color(0.62, 0.42, 0.94), Color(0.30, 0.56, 0.98)],
		"emission": 0.12, "rim": 0.4, "shadow": false, "range": 70.0,
	},
	"vase_sponges": {
		"kind": "prop", "colors": [Color(0.96, 0.50, 0.30), Color(0.66, 0.40, 0.86), Color(0.98, 0.78, 0.34)],
		"emission": 0.14, "outline": 0.022, "range": 130.0,
	},
	"sea_whips": {
		"kind": "prop", "colors": [Color(1.0, 0.44, 0.30), Color(1.0, 0.84, 0.36), Color(0.96, 0.96, 0.90)],
		"emission": 0.18, "sway": 0.16, "shadow": false, "range": 120.0,
	},
	"cabbage_corals": {
		"kind": "prop", "palette_key": "coral_palette", "colors": DEFAULT_CORAL_PALETTE,
		"emission": 0.12, "rim": 0.4, "outline": 0.016, "range": 130.0,
	},
}
## Weathered stone for ruin columns (`stone_color` in the manifest overrides it).
const STONE_COLORS: Array[Color] = [Color(0.70, 0.74, 0.78)]
## Hydrothermal chimneys: dark basalt with an ember rim in the manifest's `vent_color`.
const VENT_COLORS: Array[Color] = [Color(0.24, 0.22, 0.30)]
## Style for layers this table does not know (other recipes still render sensibly).
## Extra batch draw distance beyond a layer's `range`: about a cell's width, so a
## batch is never culled while one of its instances is still fading.
const CULL_MARGIN := 40.0
const FALLBACK_STYLE := {"kind": "prop", "colors": [Color(0.86, 0.60, 0.74)], "outline": 0.02, "range": 130.0}

var _presentation: Dictionary
var _shader_dir: String
var _outlines: Dictionary = {}


func _init(presentation: Dictionary = {}) -> void:
	_presentation = presentation
	_shader_dir = (get_script() as Script).resource_path.get_base_dir().path_join("shaders")
	# The shaders read global uniforms; make sure they exist before any shader loads.
	Atmosphere.ensure_globals()


static func style_for(layer_id: String) -> Dictionary:
	return LAYER_STYLES.get(layer_id, FALLBACK_STYLE)


## Loader `layer_settings` for every styled layer plus the "*" fallback.
static func layer_settings() -> Dictionary:
	var settings := {"*": _settings_from(FALLBACK_STYLE)}
	for layer_id in LAYER_STYLES:
		settings[layer_id] = _settings_from(LAYER_STYLES[layer_id])
	return settings


static func _settings_from(style: Dictionary) -> Dictionary:
	return {
		"cast_shadow": bool(style.get("shadow", true)),
		# Instances fade out by themselves at `range` (see `fade_for`); the batch is only
		# culled once every instance in its cell is past that.
		"visibility_range_end": float(style.get("range", 0.0)) + (CULL_MARGIN if float(style.get("range", 0.0)) > 0.0 else 0.0),
		# Blades and soft corals sway outside their rest bounds.
		"extra_cull_margin": 1.0 if float(style.get("sway", 0.0)) > 0.0 else 0.0,
	}


func seabed() -> ShaderMaterial:
	var mat := _material("toon_seabed.gdshader")
	for key in ["sand_color", "rock_color", "grotto_color"]:
		if _presentation.has(key):
			mat.set_shader_parameter(key, Atmosphere.color_from(_presentation[key], Color.WHITE))
	return mat


## Sunken timber for generated wrecks (reads the ship mesh's part shade from vertex color).
func wood() -> ShaderMaterial:
	var mat := _material("toon_wood.gdshader")
	if _presentation.has("wood_color"):
		mat.set_shader_parameter("wood_color", Atmosphere.color_from(_presentation["wood_color"], Color.WHITE))
	return mat


## Material for a scatter layer. `mesh_height` is the layer mesh's model-space
## height, which scales the base-to-tip gradient and the sway.
func layer(layer_id: String, mesh_height: float) -> ShaderMaterial:
	var style := style_for(layer_id)
	var colors := _colors(style)
	if str(style.get("kind", "prop")) == "blade":
		return _blade(style, colors[0], mesh_height)
	return prop(colors, mesh_height, style)


func prop(colors: Array[Color], mesh_height: float, style: Dictionary = {}) -> ShaderMaterial:
	var mat := _material("toon_prop.gdshader")
	var names := ["color_a", "color_b", "color_c", "color_d"]
	for i in names.size():
		mat.set_shader_parameter(names[i], colors[mini(i, colors.size() - 1)])
	mat.set_shader_parameter("palette_size", clampi(colors.size(), 1, 4))
	mat.set_shader_parameter("gradient_height", maxf(mesh_height, 0.1))
	mat.set_shader_parameter("rim_strength", float(style.get("rim", 0.30)))
	mat.set_shader_parameter("emission_strength", float(style.get("emission", 0.08)))
	mat.set_shader_parameter("sway_amount", float(style.get("sway", 0.0)))
	mat.set_shader_parameter("fade_range", fade_for(style))
	var outline_width := float(style.get("outline", 0.0))
	if outline_width > 0.0:
		mat.next_pass = _outline(outline_width, fade_for(style))
	return mat


func _blade(style: Dictionary, tip: Color, mesh_height: float) -> ShaderMaterial:
	var mat := _material("toon_blade.gdshader")
	mat.set_shader_parameter("tip_color", tip)
	mat.set_shader_parameter("base_color", tip.darkened(0.45).lerp(Color(0.04, 0.36, 0.34), 0.35))
	mat.set_shader_parameter("blade_height", maxf(mesh_height, 0.1))
	mat.set_shader_parameter("sway_amount", float(style.get("sway", 0.3)))
	mat.set_shader_parameter("sway_speed", float(style.get("sway_speed", 1.6)))
	mat.set_shader_parameter("fade_range", fade_for(style))
	return mat


## Pale carved stone for sunken ruins.
func stone() -> ShaderMaterial:
	var colors: Array[Color] = [Atmosphere.color_from(_presentation.get("stone_color"), STONE_COLORS[0])]
	return prop(colors, 5.0, {"emission": 0.0, "rim": 0.2, "outline": 0.03})


## Basalt vent chimney with an ember-colored rim light.
func vent() -> ShaderMaterial:
	var mat := prop(VENT_COLORS, 6.2, {"emission": 0.02, "rim": 0.55, "outline": 0.03})
	mat.set_shader_parameter("rim_color", Atmosphere.color_from(_presentation.get("vent_color"), Color(1.0, 0.46, 0.2)))
	return mat


## The (start, end) distance over which a style's instances shrink away: the last
## 30% of its `range`. Zero when the style has no range.
static func fade_for(style: Dictionary) -> Vector2:
	var reach := float(style.get("range", 0.0))
	return Vector2(reach * 0.7, reach)


## Ink outlines are shared per width and fade so matching batches reuse one material.
func _outline(width: float, fade: Vector2 = Vector2.ZERO) -> ShaderMaterial:
	var key := [width, fade]
	if not _outlines.has(key):
		var mat := _material("toon_outline.gdshader")
		mat.set_shader_parameter("width", width)
		mat.set_shader_parameter("fade_range", fade)
		_outlines[key] = mat
	return _outlines[key]


func _material(shader_file: String) -> ShaderMaterial:
	var mat := ShaderMaterial.new()
	mat.shader = load(_shader_dir.path_join(shader_file))
	return mat


func _colors(style: Dictionary) -> Array[Color]:
	var colors: Array[Color] = []
	var palette: Variant = _presentation.get(str(style.get("palette_key", "")))
	if palette is Array:
		for entry in palette:
			colors.append(Atmosphere.color_from(entry, Color.WHITE))
	var single: Variant = _presentation.get(str(style.get("color_key", "")))
	if colors.is_empty() and single is Array:
		colors.append(Atmosphere.color_from(single, Color.WHITE))
	if colors.is_empty():
		colors.assign(style.get("colors", [Color.WHITE]))
	var lighten := float(style.get("lighten", 0.0))
	if lighten > 0.0:
		for i in colors.size():
			colors[i] = colors[i].lightened(lighten)
	return colors
