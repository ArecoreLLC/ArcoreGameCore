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
    /// Rolling hills, lake and river, forests and meadows (see `biomes.rs`).
    OverlandCartoon,
    /// Floating islands in open air (see `biomes.rs`).
    SkyIslands,
}

impl Theme {
    pub fn parse(s: &str) -> Result<Self, String> {
        match s {
            "underwater-cartoon" => Ok(Theme::UnderwaterCartoon),
            "underwater-basin" => Ok(Theme::UnderwaterBasin),
            "canyon-arch" => Ok(Theme::CanyonArch),
            "overland-cartoon" => Ok(Theme::OverlandCartoon),
            "sky-islands" => Ok(Theme::SkyIslands),
            other => Err(format!(
                "unknown theme {other:?} (expected underwater-cartoon, underwater-basin, canyon-arch, overland-cartoon or sky-islands)"
            )),
        }
    }

    pub fn as_str(self) -> &'static str {
        match self {
            Theme::UnderwaterCartoon => "underwater-cartoon",
            Theme::UnderwaterBasin => "underwater-basin",
            Theme::CanyonArch => "canyon-arch",
            Theme::OverlandCartoon => "overland-cartoon",
            Theme::SkyIslands => "sky-islands",
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
    /// Add a generated, heeled-over shipwreck (library mesh and prop `shipwreck`).
    pub shipwreck: bool,
    /// Hydrothermal vent chimneys in one vent field (underwater-cartoon only; 0 = none).
    pub vents: usize,
    /// Add a landmark of weathered stone columns (sunken ruins on the reef, a
    /// standing-stone ring overland, a temple ring on the main sky island).
    pub ruins: bool,
    /// Add an impact crater with a skid trench and a cleared zone (overland-cartoon).
    pub crater: bool,
    /// Stack link (overland-cartoon): put the lake, the way down to the reef, here.
    pub link_center: Option<[f32; 2]>,
    /// Stack link (sky-islands): `[x, z, radius]` spots to float the first islands over.
    pub island_hints: Vec<[f32; 3]>,
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
            shipwreck: false,
            vents: 2,
            ruins: true,
            crater: false,
            link_center: None,
            island_hints: Vec::new(),
        }
    }
}

/// Generate a valid, deterministic `Recipe` from high-level knobs with minimum
/// spacing between landmarks so arches, mesas, grottos, and external props do not collide.
pub fn randomize_recipe(cfg: &RandomizeConfig) -> Recipe {
    match cfg.theme {
        Theme::OverlandCartoon => return crate::biomes::overland_recipe(cfg),
        Theme::SkyIslands => return crate::biomes::sky_recipe(cfg),
        _ => {}
    }
    let mut rng = Rng::derive(cfg.seed, &[hash_str("randomize"), hash_str(cfg.theme.as_str())]);
    let half = cfg.world_size * 0.5;
    let margin = (cfg.world_size * 0.16).max(20.0);
    let usable = (half - margin).max(12.0);
    let underwater = matches!(cfg.theme, Theme::UnderwaterCartoon | Theme::UnderwaterBasin);
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
            clear: false,
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
        falloff: 12.0, clear: false });

    // Parametric meshes
    let mut meshes = if underwater {
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
            MeshSpec {
                id: "branch_coral".into(),
                kind: MeshKind::Branch { height: 1.7, radius: 0.13, levels: 3, branches: 3, spread_deg: 34.0, sides: 5 },
            },
            MeshSpec {
                id: "brain_coral".into(),
                kind: MeshKind::Rock { radius: 0.8, subdivisions: 2, roughness: 0.09 },
            },
            MeshSpec {
                id: "table_coral".into(),
                kind: MeshKind::Lathe {
                    profile: vec![[0.10, 0.0], [0.13, 0.34], [0.78, 0.50], [0.84, 0.57], [0.0, 0.60]],
                    segments: 12,
                },
            },
            MeshSpec {
                id: "tube_sponge".into(),
                kind: MeshKind::Lathe {
                    profile: vec![[0.15, 0.0], [0.20, 0.60], [0.25, 1.30], [0.21, 1.46], [0.13, 1.40], [0.10, 0.60]],
                    segments: 10,
                },
            },
            MeshSpec {
                id: "sea_grass".into(),
                kind: MeshKind::Blade { length: 1.3, width: 0.18, segments: 3, bend: 0.28 },
            },
            MeshSpec {
                id: "pebble".into(),
                kind: MeshKind::Rock { radius: 0.3, subdivisions: 1, roughness: 0.3 },
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
                min_density_scale: 0.0,
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
                min_density_scale: 0.0,
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
                min_density_scale: 0.0,
            },
            // Reef dressing: corals favor the raised rock, grass and pebbles the sandy flats.
            ScatterLayer {
                id: "coral_garden".into(),
                mesh: "branch_coral".into(),
                external: false,
                density: 0.07,
                max_slope_deg: 50.0,
                min_slope_deg: 0.0,
                height_range: Some([base_y - 4.0, base_y + 26.0]),
                zone: None,
                zone_mode: ZoneMode::Include,
                clustering: Some(Clustering { frequency: 0.06, threshold: 0.05, softness: 0.22 }),
                scale_range: [0.6, 1.5],
                align_to_normal: false,
                normal_offset: -0.1,
                max_per_cell: Some(110),
                min_density_scale: 0.0,
            },
            ScatterLayer {
                id: "brain_corals".into(),
                mesh: "brain_coral".into(),
                external: false,
                density: 0.022,
                max_slope_deg: 45.0,
                min_slope_deg: 0.0,
                height_range: None,
                zone: None,
                zone_mode: ZoneMode::Include,
                clustering: Some(Clustering { frequency: 0.05, threshold: 0.1, softness: 0.25 }),
                scale_range: [0.5, 1.4],
                align_to_normal: true,
                normal_offset: -0.3,
                max_per_cell: Some(40),
                min_density_scale: 0.0,
            },
            ScatterLayer {
                id: "table_corals".into(),
                mesh: "table_coral".into(),
                external: false,
                density: 0.035,
                max_slope_deg: 68.0,
                min_slope_deg: 18.0,
                height_range: None,
                zone: None,
                zone_mode: ZoneMode::Include,
                clustering: None,
                scale_range: [0.7, 1.7],
                align_to_normal: true,
                normal_offset: -0.06,
                max_per_cell: Some(48),
                min_density_scale: 0.0,
            },
            ScatterLayer {
                id: "tube_sponges".into(),
                mesh: "tube_sponge".into(),
                external: false,
                density: 0.07,
                max_slope_deg: 55.0,
                min_slope_deg: 0.0,
                height_range: None,
                zone: Some("feature_zone".into()),
                zone_mode: ZoneMode::Include,
                clustering: None,
                scale_range: [0.6, 1.5],
                align_to_normal: true,
                normal_offset: -0.08,
                max_per_cell: Some(64),
                min_density_scale: 0.0,
            },
            ScatterLayer {
                id: "sea_grass".into(),
                mesh: "sea_grass".into(),
                external: false,
                density: cfg.kelp_density.max(0.0) * 4.0,
                max_slope_deg: 30.0,
                min_slope_deg: 0.0,
                height_range: Some([base_y - 12.0, base_y + 10.0]),
                zone: Some("feature_zone".into()),
                zone_mode: ZoneMode::Exclude,
                clustering: Some(Clustering { frequency: 0.03, threshold: 0.0, softness: 0.3 }),
                scale_range: [0.6, 1.5],
                align_to_normal: false,
                normal_offset: -0.05,
                max_per_cell: Some(360),
                min_density_scale: 0.0,
            },
            ScatterLayer {
                id: "pebbles".into(),
                mesh: "pebble".into(),
                external: false,
                density: 0.12,
                max_slope_deg: 40.0,
                min_slope_deg: 0.0,
                height_range: None,
                zone: None,
                zone_mode: ZoneMode::Include,
                clustering: Some(Clustering { frequency: 0.09, threshold: 0.0, softness: 0.3 }),
                scale_range: [0.5, 1.7],
                align_to_normal: true,
                normal_offset: -0.06,
                max_per_cell: Some(160),
                min_density_scale: 0.0,
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
                min_density_scale: 0.0,
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
                min_density_scale: 0.0,
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
            roll_deg: 0.0,
            scale: 1.0,
            snap_to_ground: true,
        });
        zones.push(Zone {
            id: format!("prop_clearing_{}", i + 1),
            center: [px, pz],
            radius: 8.0,
            falloff: 4.0,
            clear: false,
        });
    }

    if cfg.shipwreck {
        let (length, beam) = (rng.range(20.0, 26.0), rng.range(6.0, 7.5));
        let [px, pz] = pick_spot(&mut rng, &mut placed, length * 0.55, 6.0);
        meshes.push(MeshSpec {
            id: "shipwreck".into(),
            kind: MeshKind::Ship {
                length,
                beam,
                depth: beam * 0.62,
                masts: 2,
                mast_height: length * 0.5,
                damage: rng.range(0.45, 0.7),
            },
        });
        let side = if rng.next_f32() < 0.5 { -1.0 } else { 1.0 };
        props.push(PropSpec {
            id: "shipwreck".into(),
            mesh: "shipwreck".into(),
            external: false,
            position: [px, origin_y + height_y - 2.0, pz],
            yaw_deg: rng.range(0.0, 360.0),
            roll_deg: side * rng.range(14.0, 24.0),
            scale: 1.0,
            snap_to_ground: true,
        });
        zones.push(Zone { id: "shipwreck_site".into(), center: [px, pz], radius: length * 0.5, falloff: 6.0, clear: false });
    }

    let mut scatter = scatter;
    if cfg.theme == Theme::UnderwaterCartoon {
        add_reef_extras(cfg, &mut rng, base_y, origin_y + height_y - 2.0, &mut meshes, &mut scatter, &mut props, &mut zones, |rng, r| {
            pick_spot(rng, &mut placed, r, 6.0)
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
            "grass_color": [0.36, 0.88, 0.42],
            "wood_color": [0.72, 0.46, 0.30],
            "coral_palette": [[1.0, 0.45, 0.42], [1.0, 0.72, 0.28], [0.72, 0.48, 0.98], [0.30, 0.86, 0.84]],
            "fan_palette": [[0.96, 0.36, 0.62], [0.98, 0.62, 0.30], [0.60, 0.44, 0.96]],
            "anemone_palette": [[0.98, 0.52, 0.84], [0.46, 0.94, 0.80], [1.0, 0.80, 0.36]],
            "vent_color": [1.0, 0.46, 0.20],
            "stone_color": [0.70, 0.74, 0.78],
            "sun_color": [1.0, 0.96, 0.82],
            "cel_bands": 3
        }),
        Theme::UnderwaterBasin => json!({
            "theme": "underwater-basin",
            "style": "atmospheric",
            "water_color": [0.16, 0.58, 0.90],
            "grotto_color": [0.58, 0.66, 0.98],
            "sun_color": [1.7, 1.6, 1.45]
        }),
        Theme::CanyonArch | Theme::OverlandCartoon | Theme::SkyIslands => json!({
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


/// underwater-cartoon dressing beyond the core reef: sea fans on the slopes,
/// anemone clumps on the flats, and a hydrothermal vent field with chimneys
/// ringed by tube worms. `pick` reserves a clear XZ spot of the given radius.
#[allow(clippy::too_many_arguments)]
fn add_reef_extras(
    cfg: &RandomizeConfig,
    rng: &mut Rng,
    base_y: f32,
    drop_from: f32,
    meshes: &mut Vec<MeshSpec>,
    scatter: &mut Vec<ScatterLayer>,
    props: &mut Vec<PropSpec>,
    zones: &mut Vec<Zone>,
    mut pick: impl FnMut(&mut Rng, f32) -> [f32; 2],
) {
    meshes.push(MeshSpec {
        id: "sea_fan".into(),
        kind: MeshKind::Branch { height: 2.2, radius: 0.07, levels: 4, branches: 2, spread_deg: 30.0, sides: 3 },
    });
    meshes.push(MeshSpec {
        id: "anemone".into(),
        kind: MeshKind::Branch { height: 0.7, radius: 0.1, levels: 2, branches: 5, spread_deg: 38.0, sides: 4 },
    });
    let reef_layer = |id: &str, mesh: &str, density: f32| ScatterLayer {
        id: id.into(),
        mesh: mesh.into(),
        external: false,
        density,
        max_slope_deg: 90.0,
        min_slope_deg: 0.0,
        height_range: None,
        zone: None,
        zone_mode: ZoneMode::Include,
        clustering: None,
        scale_range: [0.7, 1.4],
        align_to_normal: false,
        normal_offset: -0.05,
        max_per_cell: None,
        min_density_scale: 0.0,
    };
    scatter.push(ScatterLayer {
        min_slope_deg: 22.0,
        max_slope_deg: 75.0,
        clustering: Some(Clustering { frequency: 0.07, threshold: 0.0, softness: 0.2 }),
        scale_range: [0.6, 1.5],
        max_per_cell: Some(40),
        ..reef_layer("sea_fans", "sea_fan", 0.03)
    });
    scatter.push(ScatterLayer {
        max_slope_deg: 30.0,
        height_range: Some([base_y - 12.0, base_y + 14.0]),
        clustering: Some(Clustering { frequency: 0.08, threshold: 0.25, softness: 0.2 }),
        align_to_normal: true,
        max_per_cell: Some(60),
        ..reef_layer("anemones", "anemone", 0.05)
    });
    // Spiky urchins and giant clams on the flats, staghorn thickets on the rock.
    meshes.push(MeshSpec {
        id: "sea_urchin".into(),
        kind: MeshKind::Branch { height: 0.5, radius: 0.05, levels: 2, branches: 5, spread_deg: 78.0, sides: 3 },
    });
    meshes.push(MeshSpec {
        id: "giant_clam".into(),
        kind: MeshKind::Lathe {
            profile: vec![[0.15, 0.0], [0.55, 0.18], [0.72, 0.5], [0.64, 0.62], [0.45, 0.4], [0.1, 0.22]],
            segments: 12,
        },
    });
    meshes.push(MeshSpec {
        id: "staghorn_coral".into(),
        kind: MeshKind::Branch { height: 2.6, radius: 0.16, levels: 4, branches: 2, spread_deg: 42.0, sides: 5 },
    });
    scatter.push(ScatterLayer {
        max_slope_deg: 40.0,
        clustering: Some(Clustering { frequency: 0.12, threshold: 0.3, softness: 0.2 }),
        scale_range: [0.6, 1.5],
        align_to_normal: true,
        normal_offset: 0.05,
        max_per_cell: Some(50),
        ..reef_layer("sea_urchins", "sea_urchin", 0.06)
    });
    scatter.push(ScatterLayer {
        max_slope_deg: 22.0,
        scale_range: [0.8, 1.9],
        align_to_normal: true,
        normal_offset: -0.1,
        max_per_cell: Some(6),
        ..reef_layer("giant_clams", "giant_clam", 0.006)
    });
    scatter.push(ScatterLayer {
        min_slope_deg: 8.0,
        max_slope_deg: 55.0,
        height_range: Some([base_y, base_y + 30.0]),
        clustering: Some(Clustering { frequency: 0.05, threshold: 0.2, softness: 0.2 }),
        scale_range: [0.6, 1.4],
        normal_offset: -0.15,
        max_per_cell: Some(24),
        ..reef_layer("staghorn_thickets", "staghorn_coral", 0.02)
    });
    if cfg.ruins {
        let [rx, rz] = pick(rng, 11.0);
        zones.push(Zone { id: "ruins".into(), center: [rx, rz], radius: 11.0, falloff: 4.0, clear: false });
        push_column_ring(rng, meshes, props, [rx, rz], drop_from, 7.5, 7, true);
    }
    if cfg.vents == 0 {
        return;
    }
    meshes.push(MeshSpec {
        id: "vent_chimney".into(),
        kind: MeshKind::Lathe {
            profile: vec![[1.5, 0.0], [1.15, 1.4], [0.85, 3.2], [1.05, 3.9], [0.7, 5.6], [0.52, 6.2], [0.36, 6.1]],
            segments: 10,
        },
    });
    meshes.push(MeshSpec {
        id: "tube_worm".into(),
        kind: MeshKind::Lathe {
            profile: vec![[0.05, 0.0], [0.05, 0.85], [0.11, 0.9], [0.09, 1.0], [0.0, 1.02]],
            segments: 6,
        },
    });
    let field_r = 10.0 + cfg.vents as f32 * 1.5;
    let [vx, vz] = pick(rng, field_r);
    zones.push(Zone { id: "vent_field".into(), center: [vx, vz], radius: field_r, falloff: 5.0, clear: false });
    for i in 0..cfg.vents {
        let a = std::f32::consts::TAU * i as f32 / cfg.vents as f32 + rng.range(-0.4, 0.4);
        let d = if i == 0 { 0.0 } else { field_r * rng.range(0.35, 0.6) };
        props.push(PropSpec {
            id: format!("vent_chimney_{}", i + 1),
            mesh: "vent_chimney".into(),
            external: false,
            position: [vx + a.cos() * d, drop_from, vz + a.sin() * d],
            yaw_deg: rng.range(0.0, 360.0),
            roll_deg: rng.range(-6.0, 6.0),
            scale: if i == 0 { 1.25 } else { rng.range(0.6, 1.0) },
            snap_to_ground: true,
        });
    }
    scatter.push(ScatterLayer {
        max_slope_deg: 45.0,
        zone: Some("vent_field".into()),
        clustering: Some(Clustering { frequency: 0.2, threshold: -0.2, softness: 0.2 }),
        scale_range: [0.6, 1.6],
        max_per_cell: Some(260),
        ..reef_layer("tube_worms", "tube_worm", 0.9)
    });
}

/// One world per level of the sandbox climb, generated together so they line
/// up: the overland lake (the way down to the reef) sits at the shared XZ
/// anchor, and the first sky islands float above the overland's hills. All
/// three share one XZ frame centered on the origin. Returns
/// `[(name, recipe); 3]` for reef, overland and sky plus a link receipt.
pub fn randomize_stack(base: &RandomizeConfig, names: [&str; 3]) -> (Vec<(String, Recipe)>, serde_json::Value) {
    let reef = randomize_recipe(&RandomizeConfig {
        name: names[0].into(),
        theme: Theme::UnderwaterCartoon,
        world_size: 192.0,
        ..base.clone()
    });
    let anchor = [0.0, 0.0];
    let overland = randomize_recipe(&RandomizeConfig {
        name: names[1].into(),
        theme: Theme::OverlandCartoon,
        world_size: 256.0,
        vents: 0,
        shipwreck: false,
        link_center: Some(anchor),
        ..base.clone()
    });
    let hints: Vec<[f32; 3]> = overland
        .terrain
        .primitives
        .iter()
        .filter(|p| p.id.as_deref().is_some_and(|id| id.starts_with("hill-") || id.starts_with("outcrop-")))
        .filter_map(|p| match p.shape {
            Shape::Sphere { center, radius } => Some([center[0], center[2], (radius * 0.6).clamp(9.0, 20.0)]),
            Shape::Cylinder { center, radius, .. } => Some([center[0], center[2], (radius * 1.5).clamp(9.0, 16.0)]),
            _ => None,
        })
        .collect();
    let sky = randomize_recipe(&RandomizeConfig {
        name: names[2].into(),
        theme: Theme::SkyIslands,
        world_size: 288.0,
        vents: 0,
        shipwreck: false,
        island_hints: hints.clone(),
        ..base.clone()
    });
    let lake = overland.zones.iter().find(|z| z.id == "lake").map(|z| json!([z.center[0], z.center[1], z.radius]));
    let receipt = json!({
        "schema": "arcore.procgen.stack.v1",
        "seed": base.seed,
        "frame": "all layers share one XZ frame centered on the origin",
        "layers": [
            {"name": names[0], "theme": "underwater-cartoon", "up": names[1]},
            {"name": names[1], "theme": "overland-cartoon", "down": names[0], "up": names[2]},
            {"name": names[2], "theme": "sky-islands", "down": names[1]},
        ],
        "anchors": {"lake": lake, "island_hints": hints},
    });
    (
        vec![(names[0].into(), reef), (names[1].into(), overland), (names[2].into(), sky)],
        receipt,
    )
}

/// A ring of weathered stone columns (mesh `ruin_column`, props `ruin_column_N`),
/// dropped onto the ground around `center`. With `toppled`, some lie on their
/// side and some are broken short, as in a ruin; otherwise they all stand.
#[allow(clippy::too_many_arguments)]
pub(crate) fn push_column_ring(
    rng: &mut Rng,
    meshes: &mut Vec<MeshSpec>,
    props: &mut Vec<PropSpec>,
    center: [f32; 2],
    drop_from: f32,
    radius: f32,
    count: usize,
    toppled: bool,
) {
    meshes.push(MeshSpec {
        id: "ruin_column".into(),
        kind: MeshKind::Lathe {
            profile: vec![[0.7, 0.0], [0.7, 0.3], [0.48, 0.42], [0.44, 4.5], [0.58, 4.65], [0.62, 4.95], [0.0, 5.0]],
            segments: 10,
        },
    });
    let turn = rng.range(0.0, std::f32::consts::TAU);
    for i in 0..count {
        let a = turn + std::f32::consts::TAU * i as f32 / count as f32;
        let fallen = toppled && rng.next_f32() < 0.3;
        let broken = toppled && !fallen && rng.next_f32() < 0.35;
        props.push(PropSpec {
            id: format!("ruin_column_{}", i + 1),
            mesh: "ruin_column".into(),
            external: false,
            position: [center[0] + a.cos() * radius, drop_from, center[1] + a.sin() * radius],
            yaw_deg: rng.range(0.0, 360.0),
            roll_deg: if fallen { rng.range(80.0, 96.0) } else { rng.range(-5.0, 5.0) },
            scale: if broken { rng.range(0.35, 0.6) } else { rng.range(0.9, 1.15) },
            snap_to_ground: true,
        });
    }
}