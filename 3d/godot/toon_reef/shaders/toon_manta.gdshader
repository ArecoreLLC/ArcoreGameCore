shader_type spatial;
render_mode cull_disabled, specular_disabled;

#include "underwater.gdshaderinc"

// Gentle cartoon manta rays gliding on wide laps, animated on the GPU. The mesh
// spans x in [-1, 1] (wingtip to wingtip) and faces +Z; vertex COLOR.r is 1 on
// the back and 0 on the belly.
// INSTANCE_CUSTOM: x = lap phase, y = flap phase, z = orbit radius 0..1, w = lap direction.
uniform vec3 back_color : source_color = vec3(0.26, 0.36, 0.62);
uniform vec3 belly_color : source_color = vec3(0.96, 0.97, 1.0);
uniform vec3 spot_color : source_color = vec3(0.62, 0.78, 0.98);
uniform float orbit_radius = 16.0;
uniform float lap_seconds = 70.0;
uniform float flap_amount = 0.34;

varying vec3 local_pos;
varying float back;
varying vec3 world_pos;

void vertex() {
	local_pos = VERTEX;
	back = COLOR.r;
	vec4 ray = INSTANCE_CUSTOM;

	// Wing beat travels from the body out to the tips; the tips also curl.
	float reach = abs(VERTEX.x);
	float beat = sin(TIME * 1.7 + ray.y * 6.2831 - reach * 1.4);
	VERTEX.y += beat * flap_amount * reach * reach;
	VERTEX.x *= 1.0 - 0.10 * (0.5 + 0.5 * beat) * reach;

	float direction = ray.w < 0.5 ? -1.0 : 1.0;
	float lap = direction * TIME * 6.2831 / lap_seconds + ray.x * 6.2831;
	float radius = uw_lap_radius(orbit_radius, ray.z);
	vec3 offset = uw_lap_offset(lap, radius);
	offset.y += sin(lap * 3.0 + ray.y * 6.2831) * 0.8;
	mat3 turn = uw_lap_turn(lap, direction);
	VERTEX = turn * VERTEX + offset / max(length(MODEL_MATRIX[0].xyz), 0.001);
	NORMAL = turn * NORMAL;
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	// Pale shoulder patches and a few freckles on the back; clean white belly.
	float shoulders = smoothstep(0.34, 0.20, length(vec2(abs(local_pos.x) - 0.42, local_pos.z - 0.12) * vec2(1.0, 1.6)));
	float freckles = smoothstep(0.72, 0.80, uw_noise(local_pos.xz * 9.0));
	vec3 top = mix(back_color, spot_color, clamp(shoulders * 0.7 + freckles * 0.35, 0.0, 1.0));
	vec3 color = mix(belly_color, top, smoothstep(0.35, 0.65, back));
	ALBEDO = uw_depth_tint(color, world_pos.y);
	EMISSION = ALBEDO * 0.08;
	ROUGHNESS = 0.8;
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
	}
}

void light() {
	DIFFUSE_LIGHT += ALBEDO * LIGHT_COLOR * uw_toon_band(dot(NORMAL, LIGHT)) * ATTENUATION / PI;
}
