shader_type spatial;
render_mode specular_schlick_ggx;

#include "underwater.gdshaderinc"

// storybook seabed: rippled golden sand on the flats, layered
// coral-slate cliffs with painted algae, baked crease shading from the
// generator (vertex COLOR.r), a glowing grotto and drifting caustic ribbons.
uniform vec3 sand_color : source_color = vec3(0.88, 0.73, 0.48);
uniform vec3 rock_color : source_color = vec3(0.28, 0.48, 0.62);
uniform vec3 algae_color : source_color = vec3(0.86, 0.42, 0.62);
uniform vec3 moss_color : source_color = vec3(0.30, 0.66, 0.52);
uniform vec3 grotto_color : source_color = vec3(0.76, 0.38, 0.96);
uniform vec2 grotto_center = vec2(8.0, 44.0);
uniform float grotto_radius = 24.0;
uniform float occlusion_strength : hint_range(0.0, 1.0) = 0.85;

varying vec3 world_pos;
varying vec3 world_nrm;
varying float baked_ao;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	baked_ao = COLOR.r;
}

void fragment() {
	vec2 p = world_pos.xz;
	float footprint = max(length(dFdx(p)), length(dFdy(p)));
	float detail = 1.0 - smoothstep(0.06, 0.35, footprint);
	float patches = uw_noise(p * 0.16) * 0.65 + uw_noise(p * 0.55) * 0.35;

	// Sand settles on the flats; a noisy threshold gives a hand-painted shoreline.
	float up = clamp(world_nrm.y, 0.0, 1.0);
	float edge = (uw_noise(p * 0.9) - 0.5) * 0.14;
	float sand_mask = smoothstep(0.58 + edge, 0.80 + edge, up);

	// Sand: broad patches, wind ripples (derivative-faded so they never shimmer) and grains.
	float phase = p.x * 2.6 + p.y * 0.9 + sin(p.y * 0.35) * 1.4 + uw_noise(p * 0.3) * 1.8;
	float ripple = sin(phase) * 0.04 * detail;
	float grain = (uw_hash(floor(p * 34.0)) - 0.5) * 0.06 * (1.0 - smoothstep(0.02, 0.09, footprint));
	vec3 sand = sand_color * (0.90 + patches * 0.16 + ripple + grain);

	// Rock: stepped strata bands warped by noise, mottling, and painted growth.
	float side = uw_noise(vec2(p.x + p.y, world_pos.y) * 0.45);
	float strata_pos = world_pos.y * 0.55 + (uw_noise(p * 0.12) + side) * 1.6;
	float strata = floor(fract(strata_pos) * 3.0) / 2.0;
	float strata_edge = smoothstep(0.42, 0.5, abs(fract(strata_pos * 3.0) - 0.5)) * detail;
	vec3 rock = rock_color * (1.05 + strata * 0.25 + side * 0.14 - strata_edge * 0.10);
	float algae = smoothstep(0.60, 0.68, uw_noise(p * 0.33 + world_pos.y * 0.21) + side * 0.25);
	rock = mix(rock, algae_color * (0.85 + side * 0.25), algae * 0.62);
	float moss = smoothstep(0.30, 0.55, up) * smoothstep(0.42, 0.60, uw_noise(p * 0.5 + 19.0));
	rock = mix(rock, moss_color, moss * 0.55);

	vec3 base = mix(rock, sand, sand_mask);

	// Glowing grotto zone.
	float gd = length(p - grotto_center);
	float grotto_mask = smoothstep(grotto_radius + 14.0, grotto_radius * 0.55, gd);
	base = mix(base, mix(base, grotto_color, 0.52), grotto_mask);

	// Baked crease shading from the generator, pushed toward plum-blue instead of black.
	float ao = mix(1.0, smoothstep(0.18, 0.92, baked_ao), occlusion_strength);
	base = mix(base * UW_SHADE_TINT, base, ao);
	base = uw_depth_tint(base, world_pos.y);

	float caustics = uw_caustics(world_pos, world_nrm) * ao;
	float pulse = 0.5 + 0.5 * sin(TIME * 0.9 + gd * 0.22);

	ALBEDO = base;
	EMISSION = UW_CAUSTIC_COLOR * caustics * mix(0.5, 0.8, sand_mask)
		+ grotto_color * grotto_mask * (0.05 + 0.05 * pulse) * ao;

	// Ripple relief on the sand.
	float slope = cos(phase) * 0.10 * detail * sand_mask;
	NORMAL = normalize(NORMAL + (VIEW_MATRIX * vec4(-slope, 0.0, -slope * 0.32, 0.0)).xyz);

	ROUGHNESS = mix(0.90, 0.74, sand_mask);
	SPECULAR = 0.06;
	METALLIC = 0.0;
}

void light() {
	DIFFUSE_LIGHT += ALBEDO * LIGHT_COLOR * uw_toon_band(dot(NORMAL, LIGHT)) * ATTENUATION / PI;
}
