//! Stage 0 — world recipe: the data contract every later stage consumes.
//!
//! A recipe holds *only* generation inputs. Presentation (palettes, fog, audio,
//! material choices) is consumer policy: it is carried opaquely in `presentation`
//! and copied into the bake manifest without interpretation.

use serde::{Deserialize, Serialize};
use std::collections::HashSet;

pub const RECIPE_SCHEMA: &str = "arcore.procgen.world-recipe.v1";
/// Hard ceiling on density samples so a typo cannot exhaust memory (~1 GiB of f32).
pub const MAX_SAMPLES: u64 = 256 * 1024 * 1024;

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Recipe {
    pub schema: String,
    pub name: String,
    pub seed: u64,
    pub bounds: Bounds,
    pub cells: CellsSpec,
    /// Optional horizontal fluid/sea level for consumers (water plane, fog, buoyancy).
    #[serde(default)]
    pub water_level: Option<f32>,
    pub terrain: TerrainSpec,
    #[serde(default)]
    pub zones: Vec<Zone>,
    #[serde(default)]
    pub meshes: Vec<MeshSpec>,
    #[serde(default)]
    pub scatter: Vec<ScatterLayer>,
    #[serde(default)]
    pub props: Vec<PropSpec>,
    /// Consumer-owned look data; never read by the generator.
    #[serde(default)]
    pub presentation: serde_json::Value,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Bounds {
    /// Minimum corner in meters.
    pub origin: [f32; 3],
    /// Extent in meters.
    pub size: [f32; 3],
    /// Density sample spacing in meters.
    pub voxel: f32,
}

impl Bounds {
    /// Sample counts per axis (inclusive of both faces).
    pub fn sample_dims(&self) -> [usize; 3] {
        let d = |s: f32| ((s / self.voxel).round().max(1.0) as usize) + 1;
        [d(self.size[0]), d(self.size[1]), d(self.size[2])]
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CellsSpec {
    /// Edge length in meters of the square XZ culling/streaming cells.
    pub size: f32,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NoiseSpec {
    pub amplitude: f32,
    /// Cycles per meter of the first octave.
    pub frequency: f32,
    #[serde(default = "default_octaves")]
    pub octaves: u32,
    #[serde(default = "default_lacunarity")]
    pub lacunarity: f32,
    #[serde(default = "default_gain")]
    pub gain: f32,
}

fn default_octaves() -> u32 {
    4
}
fn default_lacunarity() -> f32 {
    2.0
}
fn default_gain() -> f32 {
    0.5
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TerrainSpec {
    /// Ground height (meters) before noise and primitives.
    pub base_height: f32,
    /// 2D height noise over XZ.
    pub height: NoiseSpec,
    /// 3D surface detail added to the density (overhangs, lumps).
    #[serde(default)]
    pub detail: Option<NoiseSpec>,
    /// Ordered CSG edits applied after the height field.
    #[serde(default)]
    pub primitives: Vec<Primitive>,
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CsgOp {
    /// Add solid material.
    #[default]
    Union,
    /// Carve water/air out of solid material.
    Subtract,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "shape", rename_all = "snake_case")]
pub enum Shape {
    Sphere { center: [f32; 3], radius: f32 },
    Box {
        center: [f32; 3],
        half_extents: [f32; 3],
        #[serde(default)]
        yaw_deg: f32,
    },
    /// Vertical capped cylinder (mesas, pillars, shafts).
    Cylinder { center: [f32; 3], radius: f32, height: f32 },
    /// Segment with radius (tunnels, ridges).
    Capsule { a: [f32; 3], b: [f32; 3], radius: f32 },
    /// Upright ring in the local XY plane after `yaw_deg` about +Y (arches when half-buried).
    Torus {
        center: [f32; 3],
        major_radius: f32,
        minor_radius: f32,
        #[serde(default)]
        yaw_deg: f32,
    },
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Primitive {
    #[serde(default)]
    pub id: Option<String>,
    #[serde(flatten)]
    pub shape: Shape,
    #[serde(default)]
    pub op: CsgOp,
    /// Smooth blend radius in meters (0 = hard edge).
    #[serde(default)]
    pub smooth: f32,
}

/// Circular XZ region with a soft edge. Weight is 1 inside `radius`, 0 beyond `radius + falloff`.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Zone {
    pub id: String,
    pub center: [f32; 2],
    pub radius: f32,
    #[serde(default)]
    pub falloff: f32,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum MeshKind {
    /// Noise-displaced icosphere (rocks, boulders, coral heads).
    Rock {
        radius: f32,
        #[serde(default = "default_subdiv")]
        subdivisions: u32,
        #[serde(default)]
        roughness: f32,
    },
    /// Surface of revolution from `[radius, y]` points, bottom to top (sponges, pots, trunks).
    Lathe {
        profile: Vec<[f32; 2]>,
        #[serde(default = "default_segments")]
        segments: u32,
    },
    /// Tapered strip along +Y, facing +Z (leaves, kelp, grass). Render double-sided.
    Blade {
        length: f32,
        width: f32,
        #[serde(default = "default_blade_segments")]
        segments: u32,
        #[serde(default)]
        bend: f32,
    },
}

fn default_subdiv() -> u32 {
    2
}
fn default_segments() -> u32 {
    16
}
fn default_blade_segments() -> u32 {
    6
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct MeshSpec {
    pub id: String,
    #[serde(flatten)]
    pub kind: MeshKind,
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ZoneMode {
    /// Weight instances by the zone weight.
    #[default]
    Include,
    /// Weight instances by `1 - zone weight`.
    Exclude,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Clustering {
    /// Cycles per meter of the XZ clustering mask.
    pub frequency: f32,
    /// Mask threshold in [-1, 1]; higher means sparser clumps.
    #[serde(default)]
    pub threshold: f32,
    /// Soft edge width of the mask.
    #[serde(default = "default_cluster_softness")]
    pub softness: f32,
}

fn default_cluster_softness() -> f32 {
    0.15
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ScatterLayer {
    pub id: String,
    /// `meshes[].id` the consumer instances (or any consumer key when `external` is true).
    pub mesh: String,
    /// Mesh is supplied by the consumer instead of generated from `meshes`.
    #[serde(default)]
    pub external: bool,
    /// Instances per square meter of eligible surface.
    pub density: f32,
    #[serde(default = "default_max_slope")]
    pub max_slope_deg: f32,
    #[serde(default)]
    pub min_slope_deg: f32,
    #[serde(default)]
    pub height_range: Option<[f32; 2]>,
    #[serde(default)]
    pub zone: Option<String>,
    #[serde(default)]
    pub zone_mode: ZoneMode,
    #[serde(default)]
    pub clustering: Option<Clustering>,
    #[serde(default = "default_scale")]
    pub scale_range: [f32; 2],
    #[serde(default)]
    pub align_to_normal: bool,
    /// Offset along the surface normal in meters (negative embeds the instance).
    #[serde(default)]
    pub normal_offset: f32,
    /// Cap per cell, after density.
    #[serde(default)]
    pub max_per_cell: Option<u32>,
}

fn default_max_slope() -> f32 {
    90.0
}
fn default_scale() -> [f32; 2] {
    [1.0, 1.0]
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PropSpec {
    pub id: String,
    pub mesh: String,
    #[serde(default)]
    pub external: bool,
    pub position: [f32; 3],
    #[serde(default)]
    pub yaw_deg: f32,
    #[serde(default = "default_one")]
    pub scale: f32,
    /// Drop the prop onto the first surface below `position` (within the bounds).
    #[serde(default)]
    pub snap_to_ground: bool,
}

fn default_one() -> f32 {
    1.0
}

impl Recipe {
    pub fn from_json(text: &str) -> Result<Recipe, String> {
        serde_json::from_str(text).map_err(|e| format!("recipe parse error: {e}"))
    }

    /// Semantic checks beyond the JSON shape. Returns every problem found.
    pub fn validate(&self) -> Vec<String> {
        let mut errors = Vec::new();
        let mut err = |m: String| errors.push(m);
        if self.schema != RECIPE_SCHEMA {
            err(format!("schema must be {RECIPE_SCHEMA:?}, got {:?}", self.schema));
        }
        if self.name.trim().is_empty() {
            err("name must be nonempty".into());
        }
        let b = &self.bounds;
        if !(b.voxel.is_finite() && b.voxel > 0.0) {
            err("bounds.voxel must be > 0".into());
        } else if b.size.iter().any(|s| !(s.is_finite() && *s >= b.voxel)) {
            err("bounds.size must be finite and at least one voxel per axis".into());
        } else {
            let d = b.sample_dims();
            let n = d.iter().map(|v| *v as u64).product::<u64>();
            if n > MAX_SAMPLES {
                err(format!("bounds produce {n} samples; limit is {MAX_SAMPLES}"));
            }
        }
        if !(self.cells.size.is_finite() && self.cells.size > 0.0) {
            err("cells.size must be > 0".into());
        }
        let noise_ok = |n: &NoiseSpec| {
            n.amplitude.is_finite()
                && n.frequency.is_finite()
                && n.frequency >= 0.0
                && (1..=12).contains(&n.octaves)
                && n.lacunarity > 0.0
                && n.gain > 0.0
        };
        if !noise_ok(&self.terrain.height) {
            err("terrain.height noise is invalid (octaves 1..12, positive lacunarity/gain)".into());
        }
        if let Some(d) = &self.terrain.detail {
            if !noise_ok(d) {
                err("terrain.detail noise is invalid".into());
            }
        }
        for (i, p) in self.terrain.primitives.iter().enumerate() {
            if p.smooth < 0.0 || !p.smooth.is_finite() {
                err(format!("terrain.primitives[{i}].smooth must be >= 0"));
            }
            let positive = match &p.shape {
                Shape::Sphere { radius, .. } => *radius > 0.0,
                Shape::Box { half_extents, .. } => half_extents.iter().all(|h| *h > 0.0),
                Shape::Cylinder { radius, height, .. } => *radius > 0.0 && *height > 0.0,
                Shape::Capsule { radius, .. } => *radius > 0.0,
                Shape::Torus { major_radius, minor_radius, .. } => {
                    *major_radius > 0.0 && *minor_radius > 0.0
                }
            };
            if !positive {
                err(format!("terrain.primitives[{i}] needs positive dimensions"));
            }
        }

        let mut zone_ids = HashSet::new();
        for z in &self.zones {
            if !zone_ids.insert(z.id.as_str()) {
                err(format!("duplicate zone id {:?}", z.id));
            }
            if z.radius < 0.0 || z.falloff < 0.0 {
                err(format!("zone {:?} radius/falloff must be >= 0", z.id));
            }
        }
        let mut mesh_ids = HashSet::new();
        for m in &self.meshes {
            if !mesh_ids.insert(m.id.as_str()) {
                err(format!("duplicate mesh id {:?}", m.id));
            }
            match &m.kind {
                MeshKind::Rock { radius, subdivisions, .. } => {
                    if *radius <= 0.0 || *subdivisions > 5 {
                        err(format!("mesh {:?}: radius > 0 and subdivisions <= 5", m.id));
                    }
                }
                MeshKind::Lathe { profile, segments } => {
                    if profile.len() < 2 || *segments < 3 || profile.iter().any(|p| p[0] < 0.0) {
                        err(format!("mesh {:?}: lathe needs >= 2 non-negative radii and >= 3 segments", m.id));
                    }
                }
                MeshKind::Blade { length, width, segments, .. } => {
                    if *length <= 0.0 || *width <= 0.0 || *segments < 1 {
                        err(format!("mesh {:?}: blade needs positive length/width", m.id));
                    }
                }
            }
        }
        let mut layer_ids = HashSet::new();
        for l in &self.scatter {
            if !layer_ids.insert(l.id.as_str()) {
                err(format!("duplicate scatter id {:?}", l.id));
            }
            if !l.external && !mesh_ids.contains(l.mesh.as_str()) {
                err(format!("scatter {:?} references unknown mesh {:?}", l.id, l.mesh));
            }
            if let Some(z) = &l.zone {
                if !zone_ids.contains(z.as_str()) {
                    err(format!("scatter {:?} references unknown zone {:?}", l.id, z));
                }
            }
            if !(l.density.is_finite() && l.density >= 0.0) {
                err(format!("scatter {:?}: density must be >= 0", l.id));
            }
            if !(0.0..=180.0).contains(&l.min_slope_deg)
                || !(0.0..=180.0).contains(&l.max_slope_deg)
                || l.min_slope_deg > l.max_slope_deg
            {
                err(format!("scatter {:?}: slopes must satisfy 0 <= min <= max <= 180", l.id));
            }
            if l.scale_range[0] <= 0.0 || l.scale_range[0] > l.scale_range[1] {
                err(format!("scatter {:?}: scale_range must be 0 < min <= max", l.id));
            }
            if let Some([lo, hi]) = l.height_range {
                if lo > hi {
                    err(format!("scatter {:?}: height_range min > max", l.id));
                }
            }
        }
        let mut prop_ids = HashSet::new();
        for p in &self.props {
            if !prop_ids.insert(p.id.as_str()) {
                err(format!("duplicate prop id {:?}", p.id));
            }
            if !p.external && !mesh_ids.contains(p.mesh.as_str()) {
                err(format!("prop {:?} references unknown mesh {:?}", p.id, p.mesh));
            }
            if p.scale <= 0.0 {
                err(format!("prop {:?}: scale must be > 0", p.id));
            }
        }
        errors
    }
}
