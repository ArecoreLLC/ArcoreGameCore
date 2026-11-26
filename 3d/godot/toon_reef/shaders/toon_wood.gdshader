shader_type spatial;
render_mode cull_disabled, specular_disabled;

#include "underwater.gdshaderinc"

// sunken-timber look for generated wrecks: painted plank lines,
// a part shade from vertex color (deck brightest, hull darker) and soft sea
// growth creeping over the upward-facing wood.
uniform vec3 wood_color : source_color = vec3(0.72, 0.46, 0.30);
uniform vec3 growth_color : source_color = vec3(0.30, 0.70, 0.56);
uniform float plank_width = 0.55;
uniform float growth : hint_range(0.0, 1.0) = 0.35;

varying vec3 local_pos;
varying vec3 local_nrm;
varying vec3 world_pos;
varying vec3 world_nrm;
varying float part_shade;

void vertex() {
	local_pos = VERTEX;
	local_nrm = NORMAL;
	part_shade = COLOR.r;
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	// Planks run fore-and-aft: stacked up the hull sides, side by side on the deck.
	float across = mix(local_pos.y, local_pos.x, smoothstep(0.6, 0.85, abs(local_nrm.y)));
	float plank = across / plank_width;
	float seam = smoothstep(0.42, 0.5, abs(fract(plank) - 0.5));
	float footprint = max(length(dFdx(local_pos)), length(dFdy(local_pos)));
	seam *= 1.0 - smoothstep(0.05, 0.25, footprint);
	// Each plank gets its own shade, with butt joints staggered along the length.
	float board = uw_hash(vec2(floor(plank), floor(local_pos.z / 3.2 + uw_hash(vec2(floor(plank), 3.0)))));
	vec3 color = wood_color * part_shade * (1.35 + board * 0.4) * (1.0 - seam * 0.45);

	float patch = uw_noise(world_pos.xz * 0.6 + world_pos.y * 0.4);
	float cover = smoothstep(0.75 - growth * 0.5, 0.95 - growth * 0.4, patch + world_nrm.y * 0.35);
	color = mix(color, growth_color, cover * 0.7);

	ALBEDO = uw_depth_tint(color, world_pos.y);
	EMISSION = UW_CAUSTIC_COLOR * uw_caustics(world_pos, world_nrm) * 0.3;
	ROUGHNESS = 0.9;
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
		ALBEDO *= 0.7;
	}
}

void light() {
	DIFFUSE_LIGHT += ALBEDO * LIGHT_COLOR * uw_toon_band(dot(NORMAL, LIGHT)) * ATTENUATION / PI;
}
