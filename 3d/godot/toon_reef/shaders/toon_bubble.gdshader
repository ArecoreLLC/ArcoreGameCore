shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_back, unshaded;

// iridescent thin-film soap/sea bubble (self-contained, no HDRI required).
uniform float film_thickness_nm = 430.0;
varying vec3 film_point;

void vertex() {
	film_point = normalize(VERTEX);
	// Subtle surface-tension wobble
	VERTEX *= 1.0 + sin(VERTEX.x * 7.0 + TIME * 2.2) * sin(VERTEX.y * 5.0 - TIME * 1.4) * sin(VERTEX.z * 7.0) * 0.025;
}

void fragment() {
	float facing = clamp(dot(normalize(NORMAL), normalize(VIEW)), 0.0, 1.0);
	float fresnel = 0.04 + 0.96 * pow(1.0 - facing, 3.2);
	float cos_t = sqrt(max(0.0, 1.0 - (1.0 - facing * facing) / (1.333 * 1.333)));
	float swirl = 0.5 + 0.5 * sin(film_point.x * 6.0 + film_point.y * 8.0 - TIME * 1.4);
	float thickness = clamp(film_thickness_nm + swirl * 160.0, 220.0, 720.0);
	vec3 wavelengths = vec3(650.0, 510.0, 475.0);
	vec3 interference = 0.5 + 0.5 * cos(vec3(12.5663706 * 1.333 * thickness * cos_t) / wavelengths);
	vec3 tint = mix(vec3(0.84, 0.96, 1.0), interference, 0.72);
	ALBEDO = tint * (0.65 + fresnel * 0.9);
	ALPHA = clamp(0.18 + fresnel * 0.72, 0.0, 0.88);
}
