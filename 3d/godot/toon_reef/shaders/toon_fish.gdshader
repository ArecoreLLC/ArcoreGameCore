shader_type spatial;
render_mode cull_disabled, specular_disabled;

#include "underwater.gdshaderinc"

// Cartoon reef fish school animated entirely on the GPU. The fish mesh points
// along +Z; every instance sits at its school's center and circles it.
// INSTANCE_CUSTOM: x = lap phase, y = palette pick, z = orbit radius 0..1, w = swim height 0..1.
uniform vec3 color_a : source_color = vec3(1.0, 0.52, 0.16);
uniform vec3 color_b : source_color = vec3(1.0, 0.86, 0.22);
uniform vec3 color_c : source_color = vec3(0.30, 0.62, 1.0);
uniform vec3 stripe_color : source_color = vec3(1.0, 0.98, 0.94);
uniform float orbit_radius = 7.0;
uniform float orbit_height = 2.4;
uniform float lap_seconds = 26.0;

varying vec3 local_pos;
varying vec3 body_color;
varying vec3 world_pos;

void vertex() {
	local_pos = VERTEX;
	vec4 fish = INSTANCE_CUSTOM;
	body_color = fish.y < 0.34 ? color_a : (fish.y < 0.67 ? color_b : color_c);

	// Tail beat: sideways wiggle growing toward the tail.
	float tail = clamp(0.35 - VERTEX.z, 0.0, 1.4);
	VERTEX.x += sin(TIME * 9.0 + fish.x * 40.0 - VERTEX.z * 3.5) * 0.09 * tail * tail;

	float radius = uw_lap_radius(orbit_radius, fish.z);
	float lap = TIME * 6.2831 / (lap_seconds * mix(0.8, 1.25, fish.z)) + fish.x * 6.2831;
	vec3 offset = uw_lap_offset(lap, radius);
	offset.y = (fish.w - 0.5) * orbit_height + sin(lap * 2.0 + fish.x * 9.0) * 0.5;
	mat3 turn = uw_lap_turn(lap, 1.0);
	VERTEX = turn * VERTEX + offset / max(length(MODEL_MATRIX[0].xyz), 0.001);
	NORMAL = turn * NORMAL;
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	// Two soft stripes and a pale belly.
	float stripes = smoothstep(0.045, 0.03, abs(local_pos.z - 0.12)) + smoothstep(0.04, 0.025, abs(local_pos.z + 0.14));
	vec3 color = mix(body_color, stripe_color, clamp(stripes, 0.0, 1.0) * 0.9);
	color = mix(color, stripe_color, smoothstep(-0.02, -0.20, local_pos.y) * 0.45);
	// Eyes.
	float eye = length(vec2(local_pos.y - 0.05, local_pos.z - 0.30));
	color = mix(color, vec3(0.08, 0.07, 0.12), smoothstep(0.050, 0.038, eye) * step(0.05, abs(local_pos.x)));
	ALBEDO = uw_depth_tint(color, world_pos.y);
	EMISSION = ALBEDO * 0.10;
	ROUGHNESS = 0.8;
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
	}
}

void light() {
	DIFFUSE_LIGHT += ALBEDO * LIGHT_COLOR * uw_toon_band(dot(NORMAL, LIGHT)) * ATTENUATION / PI;
}
