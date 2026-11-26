// Shared toon underwater look: three-tone storybook lighting, cartoon
// caustic ribbons and depth tinting. Included by every world shader so the reef
// reads as one painted scene. The globals are registered and driven by underwater_atmosphere.gd.

global uniform float uw_water_level;
global uniform vec4 uw_deep_color : source_color;
global uniform float uw_caustic_strength;
// World-space unit vector pointing toward the sun.
global uniform vec3 uw_sun_dir;

// Scatter draw-distance scale set by a quality module (1 = as authored).
global uniform float gc_range_scale;

const vec3 UW_CAUSTIC_COLOR = vec3(0.42, 0.98, 1.0);
// Shade color for occluded creases: deep plum-blue instead of black keeps the cartoon read.
const vec3 UW_SHADE_TINT = vec3(0.34, 0.36, 0.62);

float uw_hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float uw_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(
		mix(uw_hash(i), uw_hash(i + vec2(1.0, 0.0)), f.x),
		mix(uw_hash(i + vec2(0.0, 1.0)), uw_hash(i + vec2(1.0, 1.0)), f.x),
		f.y
	);
}

// Three-tone light band (lit / mid / shade) with a hair of softening
// so band edges do not crawl on curved surfaces.
float uw_toon_band(float ndl) {
	float mid = smoothstep(0.03, 0.07, ndl);
	float lit = smoothstep(0.53, 0.57, ndl);
	return mix(0.32, mix(0.65, 1.0, lit), mid);
}

// 0 at the surface, 1 at (and below) 48 m.
float uw_depth01(float world_y) {
	return clamp((uw_water_level - world_y) / 48.0, 0.0, 1.0);
}

vec3 uw_depth_tint(vec3 color, float world_y) {
	return mix(color, uw_deep_color.rgb, uw_depth01(world_y) * 0.30);
}

// Swimmers (fish, mantas) circle a center on a flattened lap. These three keep
// the path identical in every creature shader and in scripts that vet a route:
// radius scale 0.55..1.15 of the base, an ellipse 0.7 deep, heading along travel.
float uw_lap_radius(float base_radius, float pick) {
	return base_radius * mix(0.55, 1.15, pick);
}

vec3 uw_lap_offset(float lap, float radius) {
	return vec3(cos(lap) * radius, 0.0, sin(lap) * radius * 0.7);
}

// Rotation that points a +Z-facing mesh along the lap; `direction` is +1 or -1.
mat3 uw_lap_turn(float lap, float direction) {
	vec2 heading = normalize(vec2(-sin(lap), cos(lap) * 0.7)) * direction;
	return mat3(vec3(heading.y, 0.0, -heading.x), vec3(0.0, 1.0, 0.0), vec3(heading.x, 0.0, heading.y));
}

// One layer of drifting ribbons: bright where a warped wave field crosses zero.
float uw_caustic_layer(vec2 p, float t) {
	p += vec2(sin(p.y * 0.9 + t * 0.8), cos(p.x * 0.8 - t * 0.7)) * 0.6;
	float wave = sin(p.x * 1.3 + t) + sin(p.y * 1.7 - t * 1.2) + sin((p.x + p.y) * 0.9 + t * 0.6);
	return pow(clamp(1.0 - abs(wave) * 0.55, 0.0, 1.0), 5.0);
}

// Cartoon caustics in [0, 1], projected along the sun so they slide correctly
// over walls and props. Fades with depth and where ribbons get subpixel.
float uw_caustics(vec3 world_pos, vec3 world_normal) {
	vec3 sun = normalize(uw_sun_dir);
	vec2 p = world_pos.xz - sun.xz * (world_pos.y / max(sun.y, 0.2));
	float footprint = max(length(dFdx(p)), length(dFdy(p)));
	float t = TIME * 0.9;
	float ribbons = uw_caustic_layer(p * 0.95, t) + uw_caustic_layer(p * 1.6 + vec2(7.3, 2.1), -t * 0.8) * 0.7;
	float cel = smoothstep(0.32, 0.62, ribbons);
	float facing = smoothstep(-0.05, 0.45, dot(world_normal, sun));
	float fade = (1.0 - smoothstep(0.25, 0.9, footprint)) * (1.0 - uw_depth01(world_pos.y) * 0.55);
	return cel * facing * fade * uw_caustic_strength;
}

// Smooth draw-distance fade for instanced scatter: 1 near the camera, 0 beyond
// `range` (start, end in meters; end 0 = no fade). Scale an instance's vertices
// by it and each one shrinks away on its own, instead of a whole batch popping.
// Pass MAIN_CAM_INV_VIEW_MATRIX[3].xyz as `camera` so shadow passes agree.
float uw_distance_keep(vec3 origin, vec3 camera, vec2 range) {
	if (range.y <= 0.0) {
		return 1.0;
	}
	return 1.0 - smoothstep(range.x, range.y, distance(origin, camera) / max(gc_range_scale, 0.01));
}
