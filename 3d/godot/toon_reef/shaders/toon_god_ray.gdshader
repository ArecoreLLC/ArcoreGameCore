shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled, world_vertex_coords;

#include "underwater.gdshaderinc"

// Storybook sun shafts. Each MultiMesh instance is a unit quad anchored at the
// water surface; the vertex stage stretches it down along the sun direction and
// turns it to face the camera around that axis, so one draw call covers the sea.
// INSTANCE_CUSTOM: x = width scale, y = length scale, z = phase, w = brightness.
uniform vec3 ray_color : source_color = vec3(1.0, 0.96, 0.82);
uniform float intensity = 0.16;
uniform float base_width = 5.0;
uniform float base_length = 34.0;

varying vec2 ray_uv;
varying vec4 ray_params;

void vertex() {
	ray_uv = UV;
	ray_params = INSTANCE_CUSTOM;
	vec3 anchor = MODEL_MATRIX[3].xyz;
	vec3 axis = -normalize(uw_sun_dir);
	vec3 to_camera = CAMERA_POSITION_WORLD - anchor;
	vec3 right = normalize(cross(axis, to_camera - axis * dot(to_camera, axis)) + vec3(1e-5, 0.0, 0.0));
	float width = base_width * mix(0.5, 1.6, INSTANCE_CUSTOM.x);
	float reach = base_length * mix(0.7, 1.25, INSTANCE_CUSTOM.y);
	VERTEX = anchor + right * (UV.x - 0.5) * width + axis * UV.y * reach;
	NORMAL = normalize(to_camera);
}

void fragment() {
	// MSAA can extrapolate UVs slightly past the quad; clamp before any pow().
	vec2 uv = clamp(ray_uv, 0.0, 1.0);
	float across = sin(uv.x * 3.14159);
	across *= across;
	// Bright just under the surface, dissolving toward the seabed.
	float along = smoothstep(0.0, 0.22, uv.y) * pow(1.0 - uv.y, 1.6);
	float streaks = 0.55 + 0.45 * uw_noise(vec2(uv.x * 5.0 + ray_params.z * 37.0, TIME * 0.22 + ray_params.z * 11.0));
	float shimmer = 0.75 + 0.25 * sin(TIME * 0.6 + ray_params.z * 6.2831);
	// Scene fog would paint the whole quad, so shafts fade with distance themselves,
	// and they thin out up close so swimming through one never flashes.
	float dist = length(VERTEX);
	float near_fade = smoothstep(1.5, 9.0, dist) * (1.0 - smoothstep(55.0, 120.0, dist));
	ALBEDO = ray_color * intensity * across * along * streaks * shimmer * near_fade * mix(0.5, 1.0, ray_params.w);
}
