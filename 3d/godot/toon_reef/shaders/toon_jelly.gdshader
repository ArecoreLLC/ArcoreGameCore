shader_type spatial;
render_mode unshaded, cull_disabled, blend_mix, depth_draw_never, shadows_disabled;

#include "underwater.gdshaderinc"

// toon jellyfish: glassy bell with a bright rim, rippling ribbon tentacles.
// Everything moves here: per-instance custom data picks color and phase.
uniform vec3 jelly_a : source_color = vec3(0.98, 0.56, 0.86);
uniform vec3 jelly_b : source_color = vec3(0.52, 0.86, 1.0);
uniform vec3 jelly_c : source_color = vec3(0.78, 0.66, 1.0);
uniform float pulse_speed = 1.7;
uniform float bob_height = 1.4;

varying vec3 tint;
varying float part;
varying float along;
varying vec3 world_pos;

void vertex() {
	vec4 pick = INSTANCE_CUSTOM;
	float phase = pick.x * 6.2831;
	tint = pick.y < 0.34 ? jelly_a : (pick.y < 0.67 ? jelly_b : jelly_c);
	part = COLOR.r;
	along = UV.y;

	float pulse = sin(TIME * pulse_speed + phase);
	if (part < 0.5) {
		// Bell squeezes in at the rim and stretches tall on each stroke.
		float rim = smoothstep(0.2, 1.0, along);
		VERTEX.xz *= 1.0 - 0.14 * pulse * rim;
		VERTEX.y *= 1.0 + 0.10 * pulse;
	} else {
		float t = along;
		float wave = TIME * 2.2 - t * 5.0 + phase;
		VERTEX.x += sin(wave) * 0.22 * t;
		VERTEX.z += cos(wave * 0.8) * 0.22 * t;
		VERTEX.y += max(pulse, 0.0) * 0.18 * t;
	}
	// Slow bob plus a lazy sideways drift.
	VERTEX.y += sin(TIME * 0.45 + phase) * bob_height;
	VERTEX.x += sin(TIME * 0.11 + phase * 2.0) * 1.2;
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float fresnel = pow(1.0 - clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0), 2.0);
	vec3 base = uw_depth_tint(tint, world_pos.y);
	if (part < 0.5) {
		// Banded glow: a bright cel rim and a soft inner ring.
		float ring = smoothstep(0.55, 0.6, along) * (1.0 - smoothstep(0.7, 0.75, along));
		ALBEDO = base * (0.75 + ring * 0.5) + vec3(1.0) * smoothstep(0.55, 0.7, fresnel) * 0.5;
		ALPHA = clamp(0.38 + fresnel * 0.5 + ring * 0.2, 0.0, 0.92);
	} else {
		ALBEDO = base * 1.15;
		ALPHA = 0.7 * (1.0 - along * 0.85);
	}
}
