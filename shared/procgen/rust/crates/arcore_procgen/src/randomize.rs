//! Procedural recipe randomizer: turns a seed + high-level knobs into a valid,
//! spatially separated `world-recipe.v1` JSON with optional external GLB slots.

use crate::common::rng::{hash_str, Rng};
use crate::recipe::{
    Bounds, CellsSpec, Clustering, CsgOp, MeshKind, MeshSpec, NoiseSpec, Primitive, PropSpec,
    Recipe, ScatterLayer, Shape, TerrainSpec, Zone, ZoneMode, RECIPE_SCHEMA,
};
use serde_json::json;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Theme {
    UnderwaterCartoon,
    UnderwaterBasin,
    CanyonArch,
}

impl Theme {
    pub fn parse(s: &str) -> Result<Self, String> {
        match s {
            "underwater-cartoon" => Ok(Theme::UnderwaterCartoon),
            "underwater-basin" => Ok(Theme::UnderwaterBasin),
            "canyon-arch" => Ok(Theme::CanyonArch),
            other => Err(format!(
                "unknown theme {other:?} (expected underwater-cartoon, underwater-basin, or canyon-arch)"
            )),
        }
    }

    pub fn as_str(self) -> &'static str {
        match self {
            Theme::UnderwaterCartoon => "underwater-cartoon",
            Theme::UnderwaterBasin => "underwater-basin",
            Theme::CanyonArch => "canyon-arch",
        }
    }
}

#[derive(Clone, Debug)]
pub struct RandomizeConfig {
    pub name: String,
    pub seed: u64,
    pub theme: Theme,
    pub world_size: f32,
    pub voxel: f32,
    pub mesas: usize,
    pub arches: usize,
    pub tunnels: usize,
    pub kelp_density: f32,
    /// Consumer-supplied external GLB mesh keys to place as grounded landmarks with clearings.
    pub external_props: Vec<String>,
}

impl Default for RandomizeConfig {
    fn default() -> Self {
        Self {
            name: "random-underwater".into(),
            seed: 20261123,
            theme: Theme::UnderwaterCartoon,
            world_size: 192.0,
            voxel: 1.0,
            mesas: 3,
            arches: 2,
            tunnels: 1,
            kelp_density: 0.14,
            external_props: vec!["hero_shipwreck".into()],
        }
    }
}

/// Generate a valid, deterministic `Recipe` from high-level knobs with minimum
/// spacing between landmarks so arches, mesas, grottos, and external props do not collide.
pub fn randomize_recipe(cfg: &RandomizeConfig) -> Recipe {
    let mut rng = Rng::derive(cfg.seed, &[hash_str("randomize"), hash_str(cfg.theme.as_str())]);
    let half = cfg.world_size * 0.5;
    let margin = (cfg.world_size * 0.16).max(20.0);
    let usable = (half - margin).max(12.0);
    let underwater = cfg.theme != Theme::CanyonArch;
    let (origin_y, height_y, base_y, water_level) = if underwater {
        (-48.0, 56.0, -28.0, Some(0.0))
    } else {
        (-16.0, 48.0, 0.0, None)
    };

    // Track placed XZ footprints (x, z, radius) so landmarks stay separated.
    let mut placed: Vec<[f32; 3]> = Vec::new();
    let pick_spot = |rng: &mut Rng, placed: &mut Vec<[f32; 3]>, r: f32, pad: f32| -> [f32; 2] {
        for _ in 0..48 {
            let x = rng.range(-usable, usable);
            let z = rng.range(-usable, usable);
            let clear = placed.iter().all(|p| {
                let d = ((x - p[0]).powi(2) + (z - p[1]).powi(2)).sqrt();
                d >= r + p[2] + pad
            });
            if clear {
                placed.push([x, z, r]);
                return [x, z];
            }
        }
        let fallback = [rng.range(-usable * 0.7, usable * 0.7), rng.range(-usable * 0.7, usable * 0.7)];
        placed.push([fallback[0], fallback[1], r]);
        fallback
    };

    let mut primitives = Vec::new();
    let mut zones = Vec::new();

    // Mesas / spires
    let mut mesa_centers = Vec::new();
    for i in 0..cfg.mesas {
        let radius = rng.range(12.0, 20.0);
        let height = rng.range(16.0, 26.0);
        let [x, z] = pick_spot(&mut rng, &mut placed, radius, 8.0);
        mesa_centers.push([x, z, radius]);
        primitives.push(Primitive {
            id: Some(format!("mesa-{}", i + 1)),
            shape: Shape::Cylinder { center: [x, base_y + height * 0.35, z], radius, height },
            op: CsgOp::Union,
            smooth: 3.5,
        });
    }

    // Rock arches
    for i in 0..cfg.arches {
        let major = rng.range(13.0, 19.0);
        let minor = rng.range(3.2, 4.8);
        let [x, z] = pick_spot(&mut rng, &mut placed, major, 8.0);
        let yaw_deg = rng.range(0.0, 180.0);
        primitives.push(Primitive {
            id: Some(format!("arch-{}", i + 1)),
            shape: Shape::Torus {
                center: [x, base_y + 2.0, z],
                major_radius: major,
                minor_radius: minor,
                yaw_deg,
            },
            op: CsgOp::Union,
            smooth: 2.5,
        });
        zones.push(Zone {
            id: format!("arch-clearing-{}", i + 1),
            center: [x, z],
            radius: major * 0.55,
            falloff: 4.0,
        });
    }

    // Swim / walk tunnels carved through the first mesas (or terrain if no mesas)
    for i in 0..cfg.tunnels {
        let (cx, cz, span) = if let Some(m) = mesa_centers.get(i) {
            (m[0], m[1], m[2] + 6.0)
        } else {
            let [x, z] = pick_spot(&mut rng, &mut placed, 14.0, 6.0);
            (x, z, 18.0)
        };
        let ang = rng.range(0.0, std::f32::consts::TAU);
        let (dx, dz) = (ang.cos() * span, ang.sin() * span);
        let ty = base_y + 5.5;
        primitives.push(Primitive {
            id: Some(format!("tunnel-{}", i + 1)),
            shape: Shape::Capsule {
                a: [cx - dx, ty, cz - dz],
                b: [cx + dx, ty, cz + dz],
                radius: rng.range(4.0, 5.2),
            },
            op: CsgOp::Subtract,
            smooth: 2.0,
        });
    }

    // Feature zone (glowing grotto underwater, or oasis/floor in canyon)
    let grotto_r = rng.range(20.0, 28.0);
    let [gx, gz] = pick_spot(&mut rng, &mut placed, grotto_r * 0.85, 6.0);
    if underwater {
        primitives.push(Primitive {
            id: Some("grotto-basin".into()),
            shape: Shape::Sphere { center: [gx, base_y + 6.0, gz], radius: grotto_r * 0.68 },
            op: CsgOp::Subtract,
            smooth: 3.0,
        });
    }
    zones.push(Zone {
        id: "feature_zone".into(),
        center: [gx, gz],
        radius: grotto_r,
        falloff: 12.0,
    });

    // Parametric meshes
    let meshes = if underwater {
        vec![
            MeshSpec {
                id: "kelp_blade".into(),
                kind: MeshKind::Blade { length: 5.5, width: 0.48, segments: 6, bend: 0.45 },
            },
            MeshSpec {
                id: "boulder".into(),
                kind: MeshKind::Rock { radius: 1.4, subdivisions: 2, roughness: 0.28 },
            },
            MeshSpec {
                id: "barrel_sponge".into(),
                kind: MeshKind::Lathe {
                    profile: vec![
                        [0.35, 0.0],
                        [0.60, 0.45],
                        [0.66, 1.05],
                        [0.52, 1.55],
                        [0.40, 1.60],
                        [0.36, 0.90],
                    ],
                    segments: 14,
                },
            },
        ]
    } else {
        vec![
            MeshSpec {
                id: "desert_rock".into(),
                kind: MeshKind::Rock { radius: 1.1, subdivisions: 2, roughness: 0.34 },
            },
            MeshSpec {
                id: "scrub_blade".into(),
                kind: MeshKind::Blade { length: 1.2, width: 0.18, segments: 4, bend: 0.2 },
            },
        ]
    };

    // Scatter layers
    let scatter = if underwater {
        vec![
            ScatterLayer {
                id: "kelp_forest".into(),
                mesh: "kelp_blade".into(),
                external: false,
                density: cfg.kelp_density.max(0.0),
                max_slope_deg: 36.0,
                min_slope_deg: 0.0,
                height_range: Some([base_y - 10.0, base_y + 18.0]),
                zone: Some("feature_zone".into()),
                zone_mode: ZoneMode::Exclude,
                clustering: Some(Clustering { frequency: 0.045, threshold: -0.05, softness: 0.2 }),
                scale_range: [0.7, 1.45],
                align_to_normal: false,
                normal_offset: -0.15,
                max_per_cell: Some(180),
            },
            ScatterLayer {
                id: "grotto_sponges".into(),
                mesh: "barrel_sponge".into(),
                external: false,
                density: 0.055,
                max_slope_deg: 42.0,
                min_slope_deg: 0.0,
                height_range: None,
                zone: Some("feature_zone".into()),
                zone_mode: ZoneMode::Include,
                clustering: None,
                scale_range: [0.65, 1.35],
                align_to_normal: true,
                normal_offset: -0.1,
                max_per_cell: Some(48),
            },
            ScatterLayer {
                id: "seabed_rocks".into(),
                mesh: "boulder".into(),
                external: false,
                density: 0.025,
                max_slope_deg: 55.0,
                min_slope_deg: 0.0,
                height_range: None,
                zone: None,
                zone_mode: ZoneMode::Include,
                clustering: None,
                scale_range: [0.45, 1.55],
                align_to_normal: true,
                normal_offset: -0.25,
                max_per_cell: Some(32),
            },
        ]
    } else {
        vec![
            ScatterLayer {
                id: "talus_rocks".into(),
                mesh: "desert_rock".into(),
                external: false,
                density: 0.04,
                max_slope_deg: 55.0,
                min_slope_deg: 10.0,
                height_range: None,
                zone: None,
                zone_mode: ZoneMode::Include,
                clustering: None,
                scale_range: [0.45, 1.5],
                align_to_normal: true,
                normal_offset: -0.15,
                max_per_cell: Some(40),
            },
            ScatterLayer {
                id: "floor_scrub".into(),
                mesh: "scrub_blade".into(),
                external: false,
                density: 0.08,
                max_slope_deg: 28.0,
                min_slope_deg: 0.0,
                height_range: None,
                zone: Some("feature_zone".into()),
                zone_mode: ZoneMode::Include,
                clustering: None,
                scale_range: [0.7, 1.3],
                align_to_normal: false,
                normal_offset: -0.05,
                max_per_cell: Some(64),
            },
        ]
    };

    // Grounded external props + clearing zones
    let mut props = Vec::new();
    for (i, mesh_key) in cfg.external_props.iter().enumerate() {
        let [px, pz] = pick_spot(&mut rng, &mut placed, 10.0, 6.0);
        props.push(PropSpec {
            id: format!("custom_prop_{}_{}", i + 1, mesh_key),
            mesh: mesh_key.clone(),
            external: true,
            position: [px, origin_y + height_y - 2.0, pz],
            yaw_deg: rng.range(0.0, 360.0),
            scale: 1.0,
            snap_to_ground: true,
        });
        zones.push(Zone {
            id: format!("prop_clearing_{}", i + 1),
            center: [px, pz],
            radius: 8.0,
            falloff: 4.0,
        });
    }

    let presentation = match cfg.theme {
        Theme::UnderwaterCartoon => json!({
            "theme": "underwater-cartoon",
            "style": "cel-shaded",
            "water_color": [0.10, 0.72, 0.86],
            "deep_color": [0.05, 0.24, 0.48],
            "grotto_color": [0.76, 0.36, 0.96],
            "sand_color": [0.95, 0.84, 0.56],
            "rock_color": [0.28, 0.44, 0.56],
            "kelp_color": [0.18, 0.84, 0.48],
            "sponge_color": [0.98, 0.46, 0.68],
            "sun_color": [1.0, 0.96, 0.82],
            "cel_bands": 4
        }),
        Theme::UnderwaterBasin => json!({
            "theme": "underwater-basin",
            "style": "atmospheric",
            "water_color": [0.16, 0.58, 0.90],
            "grotto_color": [0.58, 0.66, 0.98],
            "sun_color": [1.7, 1.6, 1.45]
        }),
        Theme::CanyonArch => json!({
            "theme": "canyon-arch",
            "style": "stylized-desert",
            "rock_color": [0.82, 0.45, 0.26],
            "sun_color": [1.0, 0.92, 0.78]
        }),
    };

    Recipe {
        schema: RECIPE_SCHEMA.into(),
        name: cfg.name.clone(),
        seed: cfg.seed,
        bounds: Bounds {
            origin: [-half, origin_y, -half],
            size: [cfg.world_size, height_y, cfg.world_size],
            voxel: cfg.voxel,
        },
        cells: CellsSpec { size: 24.0 },
        water_level,
        terrain: TerrainSpec {
            base_height: base_y,
            height: NoiseSpec {
                amplitude: if underwater { 7.0 } else { 5.0 },
                frequency: 0.015,
                octaves: 4,
                lacunarity: 2.0,
                gain: 0.5,
            },
            detail: Some(NoiseSpec {
                amplitude: if underwater { 1.5 } else { 0.9 },
                frequency: 0.06,
                octaves: 3,
                lacunarity: 2.1,
                gain: 0.48,
            }),
            primitives,
        },
        zones,
        meshes,
        scatter,
        props,
        presentation,
    }
}
