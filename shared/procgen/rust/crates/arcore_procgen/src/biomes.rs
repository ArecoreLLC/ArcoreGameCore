//! Above-water randomizer themes: `overland-cartoon` (rolling hills, lake and
//! river, forests and meadows) and `sky-islands` (floating rock islands with
//! hanging vines and crystal outcrops, open air below). Both produce plain
//! `world-recipe.v1` recipes, so the bake pipeline needs no biome-specific code.

use crate::common::rng::{hash_str, Rng};
use crate::randomize::{push_column_ring, RandomizeConfig};
use crate::recipe::{
    Bounds, CellsSpec, Clustering, CsgOp, MeshKind, MeshSpec, NoiseSpec, Primitive, PropSpec, Recipe,
    ScatterLayer, Shape, TerrainSpec, TreeStyle, Zone, ZoneMode, RECIPE_SCHEMA,
};
use serde_json::json;
use std::f32::consts::TAU;

/// XZ footprints already taken, so landmarks keep apart.
struct Spots {
    placed: Vec<[f32; 3]>,
    usable: f32,
}

impl Spots {
    fn new(world_size: f32) -> Self {
        let half = world_size * 0.5;
        let margin = (world_size * 0.16).max(14.0);
        Self { placed: Vec::new(), usable: (half - margin).max(8.0) }
    }

    fn pick(&mut self, rng: &mut Rng, r: f32, pad: f32) -> [f32; 2] {
        let u = self.usable;
        for _ in 0..64 {
            let (x, z) = (rng.range(-u, u), rng.range(-u, u));
            if self.placed.iter().all(|p| ((x - p[0]).powi(2) + (z - p[1]).powi(2)).sqrt() >= r + p[2] + pad) {
                self.placed.push([x, z, r]);
                return [x, z];
            }
        }
        let f = [rng.range(-u * 0.7, u * 0.7), rng.range(-u * 0.7, u * 0.7)];
        self.placed.push([f[0], f[1], r]);
        f
    }
}

fn prim(id: String, shape: Shape, op: CsgOp, smooth: f32) -> Primitive {
    Primitive { id: Some(id), shape, op, smooth }
}

fn mesh(id: &str, kind: MeshKind) -> MeshSpec {
    MeshSpec { id: id.into(), kind }
}

fn tree(height: f32, trunk_radius: f32, canopy_radius: f32, style: TreeStyle, lobes: u32) -> MeshKind {
    MeshKind::Tree { height, trunk_radius, canopy_radius, style, lobes }
}

/// Scatter layer with neutral defaults; override fields with struct update syntax.
fn layer(id: &str, mesh: &str, density: f32) -> ScatterLayer {
    ScatterLayer {
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
        scale_range: [1.0, 1.0],
        align_to_normal: false,
        normal_offset: 0.0,
        max_per_cell: None,
        min_density_scale: 0.0,
    }
}

fn clump(frequency: f32, threshold: f32) -> Option<Clustering> {
    Some(Clustering { frequency, threshold, softness: 0.25 })
}

fn external_props(
    cfg: &RandomizeConfig,
    rng: &mut Rng,
    spots: &mut Spots,
    drop_from: f32,
    zones: &mut Vec<Zone>,
) -> Vec<PropSpec> {
    let mut props = Vec::new();
    for (i, key) in cfg.external_props.iter().enumerate() {
        let [x, z] = spots.pick(rng, 9.0, 6.0);
        props.push(PropSpec {
            id: format!("custom_prop_{}_{}", i + 1, key),
            mesh: key.clone(),
            external: true,
            position: [x, drop_from, z],
            yaw_deg: rng.range(0.0, 360.0),
            roll_deg: 0.0,
            scale: 1.0,
            snap_to_ground: true,
        });
        zones.push(Zone { id: format!("prop_clearing_{}", i + 1), center: [x, z], radius: 7.0, falloff: 4.0, clear: false });
    }
    props
}

/// Rolling green hills with a lake fed by a meandering river, rocky outcrops,
/// natural arches, a pine forest, oak groves and a wildflower meadow.
pub fn overland_recipe(cfg: &RandomizeConfig) -> Recipe {
    let mut rng = Rng::derive(cfg.seed, &[hash_str("randomize"), hash_str("overland-cartoon")]);
    let half = cfg.world_size * 0.5;
    let (origin_y, height_y, base_y, water) = (-20.0, 76.0, 2.5, 0.0);
    let mut spots = Spots::new(cfg.world_size);
    let mut primitives = Vec::new();
    let mut zones = Vec::new();

    // Lake first, so it gets the most room; the river runs from it to the map edge.
    let lake_r = rng.range(18.0, 26.0).min(cfg.world_size * 0.2);
    let [lx, lz] = match cfg.link_center {
        Some(c) => {
            spots.placed.push([c[0], c[1], lake_r]);
            c
        }
        None => spots.pick(&mut rng, lake_r, 10.0),
    };
    primitives.push(prim(
        "lake".into(),
        Shape::Sphere { center: [lx, base_y + lake_r * 0.6, lz], radius: lake_r },
        CsgOp::Subtract,
        5.0,
    ));
    zones.push(Zone { id: "lake".into(), center: [lx, lz], radius: lake_r * 0.6, falloff: 8.0, clear: false });
    let mut heading = rng.range(0.0, TAU);
    let mut at = [lx, lz];
    let step = (cfg.world_size * 0.12).max(8.0);
    for i in 0..7 {
        heading += rng.range(-0.6, 0.6);
        let next = [at[0] + heading.cos() * step, at[1] + heading.sin() * step];
        primitives.push(prim(
            format!("river-{}", i + 1),
            Shape::Capsule {
                a: [at[0], base_y - 1.2, at[1]],
                b: [next[0], base_y - 1.2, next[1]],
                radius: rng.range(4.0, 5.2),
            },
            CsgOp::Subtract,
            3.0,
        ));
        at = next;
        if at[0].abs() > half + step || at[1].abs() > half + step {
            break;
        }
    }

    // Broad hills: buried spheres blended softly into the ground.
    for i in 0..(cfg.mesas + 3) {
        let r = rng.range(16.0, 30.0).min(cfg.world_size * 0.3);
        let [x, z] = spots.pick(&mut rng, r * 0.55, 2.0);
        primitives.push(prim(
            format!("hill-{}", i + 1),
            Shape::Sphere { center: [x, base_y - r * rng.range(0.5, 0.7), z], radius: r },
            CsgOp::Union,
            10.0,
        ));
    }
    // Rocky outcrops.
    for i in 0..cfg.mesas {
        let r = rng.range(5.0, 9.0);
        let [x, z] = spots.pick(&mut rng, r, 6.0);
        let h = rng.range(10.0, 20.0);
        primitives.push(prim(
            format!("outcrop-{}", i + 1),
            Shape::Cylinder { center: [x, base_y + h * 0.3, z], radius: r, height: h },
            CsgOp::Union,
            3.0,
        ));
    }
    // Natural stone arches.
    for i in 0..cfg.arches {
        let major = rng.range(9.0, 14.0);
        let [x, z] = spots.pick(&mut rng, major, 6.0);
        primitives.push(prim(
            format!("arch-{}", i + 1),
            Shape::Torus { center: [x, base_y, z], major_radius: major, minor_radius: rng.range(2.4, 3.4), yaw_deg: rng.range(0.0, 180.0) },
            CsgOp::Union,
            2.0,
        ));
        zones.push(Zone { id: format!("arch-clearing-{}", i + 1), center: [x, z], radius: major * 0.5, falloff: 3.0, clear: false });
    }
    // Hillside caves through the first outcrops.
    for i in 0..cfg.tunnels.min(cfg.mesas) {
        let p = &primitives[primitives.len() - cfg.arches - cfg.mesas + i];
        if let Shape::Cylinder { center, radius, .. } = p.shape {
            let a = rng.range(0.0, TAU);
            let span = radius + 4.0;
            primitives.push(prim(
                format!("cave-{}", i + 1),
                Shape::Capsule {
                    a: [center[0] - a.cos() * span, base_y + 3.5, center[2] - a.sin() * span],
                    b: [center[0] + a.cos() * span, base_y + 3.5, center[2] + a.sin() * span],
                    radius: 3.2,
                },
                CsgOp::Subtract,
                1.5,
            ));
        }
    }

    let meadow_r = rng.range(16.0, 24.0);
    let [mx, mz] = spots.pick(&mut rng, meadow_r * 0.8, 4.0);
    zones.push(Zone { id: "feature_zone".into(), center: [mx, mz], radius: meadow_r, falloff: 10.0, clear: false });
    let forest_r = rng.range(30.0, 44.0).min(cfg.world_size * 0.3);
    let [fx, fz] = spots.pick(&mut rng, forest_r * 0.5, 0.0);
    zones.push(Zone { id: "forest".into(), center: [fx, fz], radius: forest_r, falloff: 16.0, clear: false });

    let mut meshes = vec![
        mesh("palm_tree", tree(6.5, 0.22, 2.7, TreeStyle::Palm, 6)),
        mesh("fern", MeshKind::Branch { height: 0.7, radius: 0.03, levels: 2, branches: 5, spread_deg: 62.0, sides: 3 }),
        mesh(
            "sunflower",
            MeshKind::Lathe { profile: vec![[0.03, 0.0], [0.03, 1.3], [0.22, 1.34], [0.27, 1.42], [0.0, 1.46]], segments: 8 },
        ),
        mesh(
            "tree_stump",
            MeshKind::Lathe { profile: vec![[0.5, 0.0], [0.36, 0.25], [0.33, 0.6], [0.0, 0.62]], segments: 8 },
        ),
        mesh("pebble", MeshKind::Rock { radius: 0.28, subdivisions: 1, roughness: 0.3 }),
        mesh("grass_clump", MeshKind::Tuft { blades: 9, radius: 0.45, length: 0.5, width: 0.09 }),
        mesh("oak_tree", tree(7.0, 0.34, 2.5, TreeStyle::Round, 5)),
        mesh("birch_tree", tree(5.2, 0.2, 1.6, TreeStyle::Round, 3)),
        mesh("pine_tree", tree(9.5, 0.3, 2.4, TreeStyle::Pine, 4)),
        mesh("bush", MeshKind::Rock { radius: 0.9, subdivisions: 2, roughness: 0.25 }),
        mesh("boulder", MeshKind::Rock { radius: 1.3, subdivisions: 2, roughness: 0.3 }),
        mesh("grass_tuft", MeshKind::Blade { length: 0.9, width: 0.16, segments: 3, bend: 0.22 }),
        mesh("reed", MeshKind::Blade { length: 1.7, width: 0.08, segments: 3, bend: 0.3 }),
        mesh(
            "flower",
            MeshKind::Lathe { profile: vec![[0.02, 0.0], [0.02, 0.5], [0.13, 0.55], [0.17, 0.62], [0.0, 0.66]], segments: 6 },
        ),
        mesh(
            "mushroom",
            MeshKind::Lathe { profile: vec![[0.07, 0.0], [0.08, 0.28], [0.34, 0.3], [0.3, 0.44], [0.0, 0.5]], segments: 10 },
        ),
    ];
    let dry = Some([water + 0.8, origin_y + height_y]);
    let forest = Some("forest".to_string());
    let scatter = vec![
        // Palms lean over the water's edge; pebbles line the shore.
        ScatterLayer {
            max_slope_deg: 24.0,
            height_range: Some([water + 0.4, water + 1.7]),
            clustering: clump(0.05, 0.1),
            scale_range: [0.8, 1.3],
            normal_offset: -0.2,
            max_per_cell: Some(8),
            ..layer("shore_palms", "palm_tree", 0.012)
        },
        ScatterLayer {
            max_slope_deg: 30.0,
            height_range: Some([water - 1.5, water + 0.9]),
            scale_range: [0.5, 1.8],
            align_to_normal: true,
            normal_offset: -0.05,
            max_per_cell: Some(120),
            ..layer("shore_pebbles", "pebble", 0.3)
        },
        ScatterLayer {
            max_slope_deg: 34.0,
            zone: forest.clone(),
            clustering: clump(0.09, 0.0),
            scale_range: [0.7, 1.6],
            max_per_cell: Some(90),
            ..layer("forest_ferns", "fern", 0.3)
        },
        ScatterLayer {
            max_slope_deg: 24.0,
            zone: forest.clone(),
            scale_range: [0.7, 1.4],
            normal_offset: -0.05,
            max_per_cell: Some(4),
            ..layer("stumps", "tree_stump", 0.006)
        },
        ScatterLayer {
            max_slope_deg: 22.0,
            height_range: dry,
            zone: Some("feature_zone".into()),
            clustering: clump(0.07, 0.15),
            scale_range: [0.8, 1.3],
            max_per_cell: Some(90),
            ..layer("sunflowers", "sunflower", 0.3)
        },
        ScatterLayer {
            max_slope_deg: 32.0,
            height_range: Some([water + 2.5, origin_y + height_y]),
            zone: forest.clone(),
            clustering: clump(0.04, -0.1),
            scale_range: [0.7, 1.4],
            normal_offset: -0.2,
            max_per_cell: Some(40),
            ..layer("pine_forest", "pine_tree", 0.03)
        },
        ScatterLayer {
            max_slope_deg: 26.0,
            height_range: Some([water + 1.5, origin_y + height_y]),
            zone: forest.clone(),
            zone_mode: ZoneMode::Exclude,
            clustering: clump(0.03, 0.15),
            scale_range: [0.8, 1.3],
            normal_offset: -0.2,
            max_per_cell: Some(14),
            ..layer("oak_groves", "oak_tree", 0.012)
        },
        ScatterLayer {
            max_slope_deg: 28.0,
            height_range: Some([water + 1.5, origin_y + height_y]),
            zone: Some("feature_zone".into()),
            zone_mode: ZoneMode::Exclude,
            clustering: clump(0.05, 0.3),
            scale_range: [0.8, 1.25],
            normal_offset: -0.15,
            max_per_cell: Some(10),
            ..layer("birch_stands", "birch_tree", 0.01)
        },
        ScatterLayer {
            max_slope_deg: 36.0,
            height_range: dry,
            clustering: clump(0.06, 0.05),
            scale_range: [0.6, 1.5],
            align_to_normal: true,
            normal_offset: -0.25,
            max_per_cell: Some(40),
            ..layer("bushes", "bush", 0.025)
        },
        ScatterLayer {
            scale_range: [0.5, 1.8],
            align_to_normal: true,
            normal_offset: -0.35,
            max_per_cell: Some(24),
            ..layer("boulders", "boulder", 0.012)
        },
        ScatterLayer {
            max_slope_deg: 32.0,
            height_range: dry,
            clustering: clump(0.035, -0.35),
            scale_range: [0.6, 1.5],
            normal_offset: -0.05,
            max_per_cell: Some(420),
            ..layer("meadow_grass", "grass_tuft", 0.9)
        },
        ScatterLayer {
            max_slope_deg: 25.0,
            height_range: dry,
            zone: Some("feature_zone".into()),
            scale_range: [0.7, 1.4],
            max_per_cell: Some(220),
            ..layer("wildflowers", "flower", 0.45)
        },
        ScatterLayer {
            max_slope_deg: 30.0,
            zone: forest,
            clustering: clump(0.1, 0.25),
            scale_range: [0.6, 1.6],
            normal_offset: -0.03,
            max_per_cell: Some(30),
            ..layer("mushrooms", "mushroom", 0.04)
        },
        ScatterLayer {
            max_slope_deg: 35.0,
            height_range: Some([water - 0.7, water + 1.0]),
            clustering: clump(0.08, -0.1),
            scale_range: [0.7, 1.4],
            max_per_cell: Some(140),
            ..layer("shore_reeds", "reed", 0.35)
        },
        // Grass carpet: clumps of blades that only dense (high-end) bakes place.
        ScatterLayer {
            max_slope_deg: 34.0,
            height_range: dry,
            scale_range: [0.7, 1.5],
            normal_offset: -0.04,
            max_per_cell: Some(900),
            min_density_scale: 2.0,
            ..layer("grass_carpet", "grass_clump", 0.6)
        },
    ];

    let mut props = external_props(cfg, &mut rng, &mut spots, origin_y + height_y - 2.0, &mut zones);
    if cfg.ruins {
        // A ring of standing stones on open ground.
        let [sx, sz] = spots.pick(&mut rng, 11.0, 6.0);
        zones.push(Zone { id: "stone_circle".into(), center: [sx, sz], radius: 10.0, falloff: 3.0, clear: false });
        push_column_ring(&mut rng, &mut meshes, &mut props, [sx, sz], origin_y + height_y - 2.0, 7.5, 8, false);
    }
    if cfg.crater {
        // Something came down hard: a bowl, the trench it ploughed on the way in, bare ground around it.
        let [cx, cz] = spots.pick(&mut rng, 14.0, 8.0);
        let a = rng.range(0.0, TAU);
        primitives.push(prim(
            "crater".into(),
            Shape::Sphere { center: [cx, base_y + 5.5, cz], radius: 9.0 },
            CsgOp::Subtract,
            2.5,
        ));
        primitives.push(prim(
            "crater-trench".into(),
            Shape::Capsule {
                a: [cx, base_y - 0.5, cz],
                b: [cx + a.cos() * 34.0, base_y + 5.0, cz + a.sin() * 34.0],
                radius: 3.2,
            },
            CsgOp::Subtract,
            1.5,
        ));
        zones.push(Zone { id: "crater".into(), center: [cx, cz], radius: 11.0, falloff: 5.0, clear: true });
    }
    Recipe {
        schema: RECIPE_SCHEMA.into(),
        name: cfg.name.clone(),
        seed: cfg.seed,
        bounds: Bounds { origin: [-half, origin_y, -half], size: [cfg.world_size, height_y, cfg.world_size], voxel: cfg.voxel },
        cells: CellsSpec { size: 32.0 },
        water_level: Some(water),
        terrain: TerrainSpec {
            base_height: base_y,
            height: NoiseSpec { amplitude: 6.0, frequency: 0.012, octaves: 4, lacunarity: 2.0, gain: 0.5 },
            detail: Some(NoiseSpec { amplitude: 0.7, frequency: 0.07, octaves: 3, lacunarity: 2.1, gain: 0.48 }),
            primitives,
        },
        zones,
        meshes,
        scatter,
        props,
        presentation: json!({
            "theme": "overland-cartoon",
            "style": "cel-shaded",
            "grass_color": [0.42, 0.80, 0.34],
            "meadow_color": [0.62, 0.86, 0.36],
            "rock_color": [0.62, 0.58, 0.54],
            "sand_color": [0.94, 0.86, 0.62],
            "water_color": [0.22, 0.70, 0.90],
            "deep_color": [0.08, 0.34, 0.56],
            "trunk_color": [0.50, 0.33, 0.22],
            "leaf_palette": [[0.30, 0.72, 0.30], [0.46, 0.80, 0.28], [0.22, 0.60, 0.36], [0.70, 0.82, 0.26]],
            "pine_color": [0.16, 0.52, 0.36],
            "palm_color": [0.34, 0.74, 0.30],
            "stone_color": [0.74, 0.72, 0.68],
            "flower_palette": [[1.0, 0.42, 0.48], [1.0, 0.86, 0.30], [0.66, 0.52, 1.0], [1.0, 0.98, 0.96]],
            "sky_top": [0.30, 0.62, 0.96],
            "sky_horizon": [0.76, 0.90, 0.98],
            "sun_color": [1.0, 0.95, 0.84],
            "cel_bands": 3
        }),
    }
}

/// Floating islands high in open air: flat grassy tops on hanging rock roots,
/// small rock satellites, and stone rings to fly through. Nothing below.
pub fn sky_recipe(cfg: &RandomizeConfig) -> Recipe {
    let mut rng = Rng::derive(cfg.seed, &[hash_str("randomize"), hash_str("sky-islands")]);
    let half = cfg.world_size * 0.5;
    let (origin_y, height_y) = (0.0, 150.0);
    let mut spots = Spots::new(cfg.world_size);
    let mut primitives = Vec::new();
    let mut zones = Vec::new();
    let mut islands: Vec<[f32; 4]> = Vec::new(); // x, top, z, radius

    let count = (cfg.mesas + 4).max(3);
    for i in 0..count {
        // The first island is the biggest; it holds the feature zone.
        let mut r = if i == 0 { rng.range(18.0, 24.0) } else { rng.range(8.0, 17.0) }.min(cfg.world_size * 0.22);
        // Stacked worlds: the first islands float over the land below.
        let hint = cfg.island_hints.get(i).filter(|h| {
            spots.placed.iter().all(|p| ((h[0] - p[0]).powi(2) + (h[1] - p[1]).powi(2)).sqrt() >= h[2] + p[2] + 6.0)
        });
        let [x, z] = match hint {
            Some(h) => {
                r = if i == 0 { h[2].max(16.0) } else { h[2] };
                spots.placed.push([h[0], h[1], r]);
                [h[0], h[1]]
            }
            None => spots.pick(&mut rng, r, 10.0),
        };
        let top = rng.range(55.0, 115.0);
        let id = i + 1;
        primitives.push(prim(
            format!("island-{id}-top"),
            Shape::Cylinder { center: [x, top - 2.5, z], radius: r, height: 5.0 },
            CsgOp::Union,
            1.5,
        ));
        let (jx, jz) = (rng.range(-0.25, 0.25) * r, rng.range(-0.25, 0.25) * r);
        primitives.push(prim(
            format!("island-{id}-root"),
            Shape::Capsule { a: [x, top - 4.0, z], b: [x + jx, top - r * rng.range(1.3, 1.9), z + jz], radius: r * 0.55 },
            CsgOp::Union,
            r * 0.45,
        ));
        for k in 0..2 {
            let a = rng.range(0.0, TAU);
            primitives.push(prim(
                format!("island-{id}-lump-{}", k + 1),
                Shape::Sphere { center: [x + a.cos() * r * 0.55, top - r * 0.5, z + a.sin() * r * 0.55], radius: r * 0.4 },
                CsgOp::Union,
                r * 0.3,
            ));
        }
        // A grassy knoll on top.
        primitives.push(prim(
            format!("island-{id}-knoll"),
            Shape::Sphere { center: [x + jx * 0.6, top - r * 0.55, z + jz * 0.6], radius: r * 0.75 },
            CsgOp::Union,
            3.0,
        ));
        zones.push(Zone { id: format!("island-{id}"), center: [x, z], radius: r, falloff: 2.0, clear: false });
        islands.push([x, top, z, r]);
    }
    // Satellite boulders drifting near the islands.
    for (i, isl) in islands.clone().iter().enumerate() {
        for k in 0..3 {
            let a = rng.range(0.0, TAU);
            let d = isl[3] * rng.range(1.4, 2.2);
            primitives.push(prim(
                format!("satellite-{}-{}", i + 1, k + 1),
                Shape::Sphere {
                    center: [isl[0] + a.cos() * d, isl[1] - rng.range(4.0, 18.0), isl[2] + a.sin() * d],
                    radius: rng.range(1.6, 3.4),
                },
                CsgOp::Union,
                0.0,
            ));
        }
    }
    // Stone rings hanging in the gaps, to fly through.
    for i in 0..cfg.arches {
        let major = rng.range(7.0, 11.0);
        let [x, z] = spots.pick(&mut rng, major, 4.0);
        primitives.push(prim(
            format!("sky-ring-{}", i + 1),
            Shape::Torus { center: [x, rng.range(50.0, 105.0), z], major_radius: major, minor_radius: 1.4, yaw_deg: rng.range(0.0, 180.0) },
            CsgOp::Union,
            0.0,
        ));
    }
    let main = islands[0];
    zones.push(Zone { id: "feature_zone".into(), center: [main[0], main[2]], radius: main[3] * 0.8, falloff: 4.0, clear: false });

    let mut meshes = vec![
        mesh(
            "glow_cap",
            MeshKind::Lathe { profile: vec![[0.07, 0.0], [0.08, 0.5], [0.42, 0.52], [0.36, 0.72], [0.0, 0.8]], segments: 10 },
        ),
        mesh("fern", MeshKind::Branch { height: 0.7, radius: 0.03, levels: 2, branches: 5, spread_deg: 62.0, sides: 3 }),
        mesh("grass_clump", MeshKind::Tuft { blades: 9, radius: 0.45, length: 0.5, width: 0.09 }),
        mesh("sky_oak", tree(5.5, 0.28, 2.0, TreeStyle::Round, 4)),
        mesh("sky_pine", tree(7.0, 0.24, 1.8, TreeStyle::Pine, 3)),
        mesh("grass_tuft", MeshKind::Blade { length: 0.8, width: 0.15, segments: 3, bend: 0.2 }),
        mesh("hanging_vine", MeshKind::Blade { length: 3.6, width: 0.28, segments: 5, bend: 0.4 }),
        mesh("boulder", MeshKind::Rock { radius: 1.0, subdivisions: 2, roughness: 0.3 }),
        mesh(
            "sky_crystal",
            MeshKind::Lathe { profile: vec![[0.0, -0.2], [0.26, 0.0], [0.32, 1.3], [0.0, 1.9]], segments: 6 },
        ),
        mesh(
            "flower",
            MeshKind::Lathe { profile: vec![[0.02, 0.0], [0.02, 0.45], [0.12, 0.5], [0.16, 0.57], [0.0, 0.61]], segments: 6 },
        ),
    ];
    let scatter = vec![
        // Glowing mushrooms cluster in the shade; ferns fringe the island rims.
        ScatterLayer {
            max_slope_deg: 40.0,
            clustering: clump(0.12, 0.3),
            scale_range: [0.5, 1.8],
            normal_offset: -0.03,
            max_per_cell: Some(40),
            ..layer("glow_caps", "glow_cap", 0.08)
        },
        ScatterLayer {
            min_slope_deg: 18.0,
            max_slope_deg: 60.0,
            scale_range: [0.8, 1.9],
            max_per_cell: Some(80),
            ..layer("rim_ferns", "fern", 0.25)
        },
        ScatterLayer {
            max_slope_deg: 30.0,
            clustering: clump(0.05, 0.0),
            scale_range: [0.7, 1.3],
            normal_offset: -0.2,
            max_per_cell: Some(12),
            ..layer("island_oaks", "sky_oak", 0.02)
        },
        ScatterLayer {
            max_slope_deg: 30.0,
            zone: Some("feature_zone".into()),
            zone_mode: ZoneMode::Exclude,
            clustering: clump(0.06, 0.2),
            scale_range: [0.7, 1.3],
            normal_offset: -0.2,
            max_per_cell: Some(12),
            ..layer("island_pines", "sky_pine", 0.015)
        },
        ScatterLayer {
            max_slope_deg: 35.0,
            scale_range: [0.6, 1.5],
            normal_offset: -0.05,
            max_per_cell: Some(420),
            ..layer("island_grass", "grass_tuft", 1.1)
        },
        ScatterLayer {
            max_slope_deg: 25.0,
            zone: Some("feature_zone".into()),
            scale_range: [0.7, 1.3],
            max_per_cell: Some(160),
            ..layer("island_flowers", "flower", 0.5)
        },
        ScatterLayer {
            min_slope_deg: 120.0,
            max_slope_deg: 180.0,
            clustering: clump(0.08, -0.2),
            scale_range: [0.6, 1.6],
            normal_offset: -0.1,
            max_per_cell: Some(160),
            ..layer("hanging_vines", "hanging_vine", 0.3)
        },
        ScatterLayer {
            min_slope_deg: 40.0,
            max_slope_deg: 140.0,
            clustering: clump(0.09, 0.25),
            scale_range: [0.6, 2.0],
            align_to_normal: true,
            normal_offset: -0.15,
            max_per_cell: Some(40),
            ..layer("sky_crystals", "sky_crystal", 0.04)
        },
        ScatterLayer {
            max_slope_deg: 50.0,
            scale_range: [0.5, 1.5],
            align_to_normal: true,
            normal_offset: -0.25,
            max_per_cell: Some(16),
            ..layer("boulders", "boulder", 0.012)
        },
        // Grass carpet: clumps of blades that only dense (high-end) bakes place.
        ScatterLayer {
            max_slope_deg: 34.0,
            scale_range: [0.7, 1.5],
            normal_offset: -0.04,
            max_per_cell: Some(900),
            min_density_scale: 2.0,
            ..layer("grass_carpet", "grass_clump", 0.6)
        },
    ];

    // External props land on island tops, so they always find ground.
    let mut props = Vec::new();
    if cfg.ruins {
        // A ruined temple ring crowns the main island.
        push_column_ring(&mut rng, &mut meshes, &mut props, [main[0], main[2]], (main[1] + 14.0).min(origin_y + height_y - 1.0), main[3] * 0.5, 6, true);
    }
    for (i, key) in cfg.external_props.iter().enumerate() {
        let isl = islands[(i + 1) % islands.len()];
        props.push(PropSpec {
            id: format!("custom_prop_{}_{}", i + 1, key),
            mesh: key.clone(),
            external: true,
            position: [isl[0], (isl[1] + 12.0).min(origin_y + height_y - 1.0), isl[2]],
            yaw_deg: rng.range(0.0, 360.0),
            roll_deg: 0.0,
            scale: 1.0,
            snap_to_ground: true,
        });
    }

    Recipe {
        schema: RECIPE_SCHEMA.into(),
        name: cfg.name.clone(),
        seed: cfg.seed,
        bounds: Bounds { origin: [-half, origin_y, -half], size: [cfg.world_size, height_y, cfg.world_size], voxel: cfg.voxel },
        cells: CellsSpec { size: 32.0 },
        water_level: None,
        terrain: TerrainSpec {
            // Far below the bounds: open air everywhere except the primitives.
            base_height: origin_y - 1000.0,
            height: NoiseSpec { amplitude: 0.0, frequency: 0.0, octaves: 1, lacunarity: 2.0, gain: 0.5 },
            detail: Some(NoiseSpec { amplitude: 1.4, frequency: 0.08, octaves: 3, lacunarity: 2.1, gain: 0.5 }),
            primitives,
        },
        zones,
        meshes,
        scatter,
        props,
        presentation: json!({
            "theme": "sky-islands",
            "style": "cel-shaded",
            "grass_color": [0.50, 0.86, 0.42],
            "rock_color": [0.66, 0.56, 0.62],
            "root_color": [0.46, 0.38, 0.50],
            "trunk_color": [0.52, 0.36, 0.28],
            "leaf_palette": [[0.42, 0.82, 0.40], [0.98, 0.70, 0.78], [0.56, 0.86, 0.34]],
            "pine_color": [0.22, 0.60, 0.48],
            "stone_color": [0.86, 0.80, 0.84],
            "glow_palette": [[0.40, 1.0, 0.86], [0.76, 0.56, 1.0], [1.0, 0.62, 0.86]],
            "vine_color": [0.32, 0.78, 0.46],
            "crystal_palette": [[0.56, 0.86, 1.0], [0.82, 0.62, 1.0], [1.0, 0.72, 0.92]],
            "flower_palette": [[1.0, 0.60, 0.76], [1.0, 0.92, 0.42], [0.72, 0.66, 1.0]],
            "cloud_color": [1.0, 0.98, 0.98],
            "cloud_shade": [0.72, 0.78, 0.96],
            "sky_top": [0.10, 0.30, 0.78],
            "sky_horizon": [0.66, 0.84, 1.0],
            "sun_color": [1.0, 0.94, 0.86],
            "cel_bands": 3
        }),
    }
}
