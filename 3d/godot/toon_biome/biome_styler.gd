extends RefCounted
## Toon materials for open-air arcore_procgen bundles (rolling land, floating
## islands, anything above water). Reuses the toon_reef prop/blade shaders and
## their shared three-tone light, adds a ground shader and a two-part tree
## shader for the generator's `tree` meshes, and maps scatter layers and props
## to materials from a style table the game supplies. Colors come from the
## bundle's `presentation` block, so a reroll can restyle without code changes.
##
##   const BiomeStyler := preload("res://addons/gamecore_toon_biome/biome_styler.gd")
##   var styler := BiomeStyler.new(presentation, STYLES, FALLBACK)
##   BiomeStyler.set_open_air_globals(water_level, deep_color, sun_direction)
##   var world := ProcgenWorldLoader.load_bundle(self, dir, {
##       "terrain_material": styler.ground(), "layer_settings": styler.layer_settings(),
##       "instance_custom_data": true})
##   styler.style_scatter(world.root)
##   styler.style_props(world.root, PROP_STYLES)
##
## Vendor this folder next to toon_reef (`addons/gamecore_toon_biome` beside
## `addons/gamecore_toon_reef`): scripts and shaders reach it by relative path.
##
## Style entry keys:
##   kind: "prop" | "blade" | "tree"
##   colors / color_key / palette_key: as in toon_reef's ReefMaterials
##   leaf_key / leaf_palette_key, trunk_key: tree foliage and trunk colors
##   emission, rim, outline, sway, sway_speed, shadow, range: as in ReefMaterials

const ReefMaterials := preload("../gamecore_toon_reef/reef_materials.gd")
const Atmosphere := preload("../gamecore_toon_reef/underwater_atmosphere.gd")
const GROUND_SHADER := preload("shaders/toon_ground.gdshader")
const TREE_SHADER := preload("shaders/toon_tree.gdshader")
const BLADE_SHADER := preload("../gamecore_toon_reef/shaders/toon_blade.gdshader")

var presentation: Dictionary
var reef: ReefMaterials
var _styles: Dictionary
var _fallback: Dictionary


func _init(manifest_presentation: Dictionary, styles: Dictionary, fallback: Dictionary) -> void:
	presentation = manifest_presentation
	reef = ReefMaterials.new(presentation)
	_styles = styles
	_fallback = fallback


## Points the toon shaders' shared globals at an above-water scene: no
## caustics, and `water_level` only tints what lies below it.
static func set_open_air_globals(water_level: float, deep_color: Color, sun_dir: Vector3) -> void:
	Atmosphere.ensure_globals()
	RenderingServer.global_shader_parameter_set(&"uw_water_level", water_level)
	RenderingServer.global_shader_parameter_set(&"uw_deep_color", deep_color)
	RenderingServer.global_shader_parameter_set(&"uw_caustic_strength", 0.0)
	RenderingServer.global_shader_parameter_set(&"uw_sun_dir", sun_dir)


func color(key: String, fallback: Color) -> Color:
	return Atmosphere.color_from(presentation.get(key), fallback)


func palette(key: String, fallback: Array[Color]) -> Array[Color]:
	var value: Variant = presentation.get(key)
	if not (value is Array) or value.is_empty():
		return fallback
	var out: Array[Color] = []
	for entry in value:
		out.append(Atmosphere.color_from(entry, Color.WHITE))
	return out


## Loader `layer_settings` for every styled layer plus the "*" fallback.
func layer_settings() -> Dictionary:
	var settings := {"*": _settings_from(_fallback)}
	for id in _styles:
		settings[id] = _settings_from(_styles[id])
	return settings


static func _settings_from(style: Dictionary) -> Dictionary:
	return {
		"cast_shadow": bool(style.get("shadow", true)),
		# Instances shrink away by themselves at `range`; the batch is culled a cell further out.
		"visibility_range_end": float(style.get("range", 0.0)) + (ReefMaterials.CULL_MARGIN if float(style.get("range", 0.0)) > 0.0 else 0.0),
		"extra_cull_margin": 1.5 if float(style.get("sway", 0.0)) > 0.0 or style.get("kind") == "tree" else 0.0,
	}


func ground(options: Dictionary = {}) -> ShaderMaterial:
	var mat := ShaderMaterial.new()
	mat.shader = GROUND_SHADER
	mat.set_shader_parameter("grass_color", color("grass_color", Color(0.42, 0.80, 0.34)))
	mat.set_shader_parameter("meadow_color", color("meadow_color", color("grass_color", Color(0.62, 0.86, 0.36))))
	mat.set_shader_parameter("rock_color", color("rock_color", Color(0.62, 0.58, 0.54)))
	mat.set_shader_parameter("under_color", color("root_color", color("rock_color", Color(0.5, 0.46, 0.44)).darkened(0.25)))
	mat.set_shader_parameter("sand_color", color("sand_color", Color(0.94, 0.86, 0.62)))
	for key in options:
		mat.set_shader_parameter(key, options[key])
	return mat


func layer(layer_id: String, mesh_height: float) -> ShaderMaterial:
	var style: Dictionary = _styles.get(layer_id, _fallback)
	match str(style.get("kind", "prop")):
		"tree":
			return tree(style, mesh_height)
		"blade":
			return blade(style, mesh_height)
	return reef.prop(colors_for(style), mesh_height, style)


func tree(style: Dictionary, mesh_height: float) -> ShaderMaterial:
	var mat := ShaderMaterial.new()
	mat.shader = TREE_SHADER
	var leaves: Array[Color] = palette(str(style.get("leaf_palette_key", "")), [])
	if leaves.is_empty():
		leaves = [color(str(style.get("leaf_key", "")), style.get("leaf", Color(0.3, 0.72, 0.3)))]
	var names := ["leaf_a", "leaf_b", "leaf_c", "leaf_d"]
	for i in names.size():
		mat.set_shader_parameter(names[i], leaves[mini(i, leaves.size() - 1)])
	mat.set_shader_parameter("leaf_count", clampi(leaves.size(), 1, 4))
	mat.set_shader_parameter("trunk_color", color(str(style.get("trunk_key", "trunk_color")), style.get("trunk", Color(0.5, 0.33, 0.22))))
	mat.set_shader_parameter("tree_height", maxf(mesh_height, 0.5))
	mat.set_shader_parameter("sway_amount", float(style.get("sway", 0.12)))
	mat.set_shader_parameter("fade_range", ReefMaterials.fade_for(style))
	return mat


func blade(style: Dictionary, mesh_height: float) -> ShaderMaterial:
	var tip: Color = colors_for(style)[0]
	var mat := ShaderMaterial.new()
	mat.shader = BLADE_SHADER
	mat.set_shader_parameter("tip_color", tip)
	mat.set_shader_parameter("base_color", tip.darkened(0.42))
	mat.set_shader_parameter("blade_height", maxf(mesh_height, 0.1))
	mat.set_shader_parameter("sway_amount", float(style.get("sway", 0.15)))
	mat.set_shader_parameter("sway_speed", float(style.get("sway_speed", 1.8)))
	mat.set_shader_parameter("fade_range", ReefMaterials.fade_for(style))
	return mat


## Props built from the bundle's mesh library get a prop material by mesh id;
## `prop_styles` maps mesh ids to style entries. Others are left untouched.
func style_props(root: Node3D, prop_styles: Dictionary) -> void:
	var props := root.get_node_or_null("Props")
	if props == null:
		return
	for child in props.get_children():
		var prop := child as MeshInstance3D
		var style: Variant = prop_styles.get(str(child.get_meta("procgen_mesh_id", "")))
		if prop != null and style != null:
			prop.material_override = reef.prop(colors_for(style), prop.mesh.get_aabb().end.y, style)


## Gives every scatter layer of a loaded bundle its material.
func style_scatter(root: Node3D) -> void:
	var scatter := root.get_node_or_null("Scatter")
	if scatter == null:
		return
	for layer_node in scatter.get_children():
		var batches := layer_node.get_children()
		if batches.is_empty():
			continue
		var first := batches[0] as MultiMeshInstance3D
		if first == null or first.multimesh == null:
			continue
		var mesh := first.multimesh.mesh
		var mat := layer(str(layer_node.name), mesh.get_aabb().end.y if mesh != null else 1.0)
		for batch in batches:
			(batch as GeometryInstance3D).material_override = mat


## Colors of a style entry: `palette_key`, else `color_key`, else its `colors`.
func colors_for(style: Dictionary) -> Array[Color]:
	var out := palette(str(style.get("palette_key", "")), [])
	if out.is_empty() and presentation.get(str(style.get("color_key", ""))) is Array:
		out.append(color(str(style.get("color_key", "")), Color.WHITE))
	if out.is_empty():
		out.assign(style.get("colors", [Color.WHITE]))
	return out
