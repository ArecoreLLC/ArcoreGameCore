use arcore_procgen::common::math::Vec3;
use arcore_procgen::export::bundle::encode_outputs;
use arcore_procgen::export::glb::read_glb_json;
use arcore_procgen::recipe::Recipe;
use arcore_procgen::runtime::collision::{glide, raycast};
use arcore_procgen::stages::field::build_field;
use arcore_procgen::stages::surface::surface_nets;
use arcore_procgen::{bake, randomize_recipe, randomize_stack, BakeOptions, RandomizeConfig, Theme};
use std::collections::HashMap;
use std::path::PathBuf;

fn recipe(json: serde_json::Value) -> Recipe {
    serde_json::from_value(json).expect("test recipe parses")
}

/// Flat ground at y = 0 inside a 32 m box, optional extra fields merged in.
fn flat(extra: serde_json::Value) -> Recipe {
    let mut base = serde_json::json!({
        "schema": "arcore.procgen.world-recipe.v1",
        "name": "flat",
        "seed": 1,
        "bounds": {"origin": [-16.0, -8.0, -16.0], "size": [32.0, 16.0, 32.0], "voxel": 0.5},
        "cells": {"size": 8.0},
        "terrain": {"base_height": 0.0, "height": {"amplitude": 0.0, "frequency": 0.0}}
    });
    if let (Some(b), Some(e)) = (base.as_object_mut(), extra.as_object()) {
        for (k, v) in e {
            b.insert(k.clone(), v.clone());
        }
    }
    recipe(base)
}

fn opts(threads: usize) -> BakeOptions {
    BakeOptions { threads, density_scale: 1.0 , mesh_detail: 0 }
}

#[test]
fn sphere_mesh_is_closed_accurate_and_outward() {
    // Ground far below the grid so only the sphere is solid.
    let r = recipe(serde_json::json!({
        "schema": "arcore.procgen.world-recipe.v1", "name": "sphere", "seed": 3,
        "bounds": {"origin": [-6.0, -6.0, -6.0], "size": [12.0, 12.0, 12.0], "voxel": 0.25},
        "cells": {"size": 12.0},
        "terrain": {"base_height": -100.0, "height": {"amplitude": 0.0, "frequency": 0.0},
            "primitives": [{"shape": "sphere", "center": [0.0, 0.0, 0.0], "radius": 4.0}]}
    }));
    let mesh = surface_nets(&build_field(&r, 2));
    assert!(mesh.triangle_count() > 1000);
    for p in &mesh.positions {
        let d = Vec3::from_array(*p).length();
        assert!((d - 4.0).abs() < 0.25 * 0.5, "vertex off sphere: {d}");
    }
    for t in mesh.indices.chunks_exact(3) {
        let (a, b, c) = (mesh.position(t[0]), mesh.position(t[1]), mesh.position(t[2]));
        let n = (b - a).cross(c - a);
        assert!(n.dot(a + b + c) > 0.0, "triangle faces inward");
    }
    // Watertight: every undirected edge is shared by exactly two triangles.
    let mut edges: HashMap<(u32, u32), u32> = HashMap::new();
    for t in mesh.indices.chunks_exact(3) {
        for (a, b) in [(t[0], t[1]), (t[1], t[2]), (t[2], t[0])] {
            *edges.entry((a.min(b), a.max(b))).or_default() += 1;
        }
    }
    assert!(edges.values().all(|c| *c == 2), "mesh has open or non-manifold edges");
}

#[test]
fn bake_is_identical_for_any_thread_count() {
    let path = recipes_dir().join("underwater-basin.json");
    let mut r = Recipe::from_json(&std::fs::read_to_string(path).unwrap()).unwrap();
    // Shrink the world so the test stays fast; keep every other input.
    r.bounds.origin = [-24.0, -40.0, -24.0];
    r.bounds.size = [48.0, 48.0, 48.0];
    r.bounds.voxel = 1.0;
    let a = encode_outputs(&bake(&r, opts(1)).unwrap());
    let b = encode_outputs(&bake(&r, opts(5)).unwrap());
    for (x, y) in a.iter().zip(&b) {
        assert_eq!(x.name, y.name);
        assert!(x.bytes == y.bytes, "{} differs between thread counts", x.name);
    }
}

#[test]
fn glide_rests_on_floor_and_passes_through_tunnel() {
    let floor = flat(serde_json::json!({}));
    let field = build_field(&floor, 2);
    let p = glide(&field, Vec3::new(0.0, 3.0, 0.0), Vec3::new(2.0, -10.0, 0.0), 1.0);
    assert!((p.y - 1.0).abs() < 0.1, "sphere should rest one radius above ground, got {p:?}");
    assert!(p.x > 1.5, "horizontal motion should slide along the floor, got {p:?}");

    // A solid wall at x = 4 with a capsule tunnel through it at y = 2.
    let walled = flat(serde_json::json!({"terrain": {
        "base_height": 0.0, "height": {"amplitude": 0.0, "frequency": 0.0},
        "primitives": [
            {"shape": "box", "center": [4.0, 4.0, 0.0], "half_extents": [1.0, 4.0, 12.0]},
            {"shape": "capsule", "a": [0.0, 2.5, 0.0], "b": [8.0, 2.5, 0.0], "radius": 1.5, "op": "subtract"}
        ]}}));
    let field = build_field(&walled, 2);
    let blocked = glide(&field, Vec3::new(0.0, 2.5, 6.0), Vec3::new(8.0, 0.0, 0.0), 0.8);
    assert!(blocked.x < 3.2, "wall must stop the sphere, got {blocked:?}");
    let through = glide(&field, Vec3::new(0.0, 2.5, 0.0), Vec3::new(8.0, 0.0, 0.0), 0.8);
    assert!(through.x > 7.5, "tunnel must let the sphere pass, got {through:?}");
}

#[test]
fn raycast_hits_ground() {
    let field = build_field(&flat(serde_json::json!({})), 1);
    let hit = raycast(&field, Vec3::new(1.0, 5.0, 1.0), Vec3::new(0.0, -1.0, 0.0), 20.0).unwrap();
    assert!(hit.position.y.abs() < 0.01 && hit.normal.y > 0.99);
    assert!(raycast(&field, Vec3::new(1.0, 5.0, 1.0), Vec3::Y, 20.0).is_none());
}

#[test]
fn scatter_respects_density_slope_and_zones() {
    let r = flat(serde_json::json!({
        "zones": [{"id": "clearing", "center": [0.0, 0.0], "radius": 6.0, "falloff": 0.0}],
        "meshes": [{"id": "pebble", "kind": "rock", "radius": 0.2}],
        "scatter": [
            {"id": "all", "mesh": "pebble", "density": 0.5},
            {"id": "steep_only", "mesh": "pebble", "density": 0.5, "min_slope_deg": 30.0},
            {"id": "outside", "mesh": "pebble", "density": 0.5, "zone": "clearing", "zone_mode": "exclude"},
            {"id": "capped", "mesh": "pebble", "density": 5.0, "max_per_cell": 10}
        ]
    }));
    let w = bake(&r, opts(2)).unwrap();
    let layer = |id: &str| w.layers.iter().find(|l| l.layer == id).unwrap();
    let expected = 32.0 * 32.0 * 0.5;
    let all = layer("all").count() as f32;
    assert!((all - expected).abs() / expected < 0.1, "count {all} vs expected {expected}");
    assert_eq!(layer("steep_only").count(), 0, "flat ground has no steep faces");
    for c in &layer("outside").cells {
        for i in &c.instances {
            let d = (i.position[0].powi(2) + i.position[2].powi(2)).sqrt();
            assert!(d > 6.0 - 1e-3, "instance inside excluded zone at {d}");
        }
    }
    assert!(layer("capped").cells.iter().all(|c| c.instances.len() <= 10));
    // Half the density scale gives roughly half the instances.
    let half = bake(&r, BakeOptions { threads: 2, density_scale: 0.5 , mesh_detail: 0 }).unwrap();
    let h = half.layers[0].count() as f32;
    assert!((h / all - 0.5).abs() < 0.08, "density scale ratio {}", h / all);
}

#[test]
fn glb_outputs_are_well_formed() {
    let r = flat(serde_json::json!({
        "meshes": [{"id": "sponge", "kind": "lathe", "profile": [[0.3, 0.0], [0.5, 1.0], [0.4, 1.5]]}],
        "props": [{"id": "landmark", "mesh": "sponge", "position": [2.0, 6.0, 2.0], "snap_to_ground": true}]
    }));
    let w = bake(&r, opts(2)).unwrap();
    assert!(w.props[0].grounded && w.props[0].instance.position[1].abs() < 0.05);
    let files = encode_outputs(&w);
    let terrain = read_glb_json(&files[0].bytes).unwrap();
    assert_eq!(terrain["nodes"].as_array().unwrap().len(), w.terrain_chunks.len());
    assert_eq!(w.terrain_chunks.len(), 16, "32 m / 8 m cells = 4x4");
    let meshes = read_glb_json(&files[1].bytes).unwrap();
    assert_eq!(meshes["nodes"][0]["name"], "sponge");
    let instances: serde_json::Value = serde_json::from_slice(&files[2].bytes).unwrap();
    assert_eq!(instances["schema"], "arcore.procgen.instances.v1");
    assert_eq!(instances["props"][0]["id"], "landmark");
}

#[test]
fn terrain_carries_baked_vertex_occlusion() {
    // Flat floor with a narrow trench: the trench floor must read darker than open ground.
    let r = flat(serde_json::json!({"terrain": {
        "base_height": 0.0, "height": {"amplitude": 0.0, "frequency": 0.0},
        "primitives": [{"shape": "box", "center": [0.0, -2.0, 0.0], "half_extents": [0.75, 2.0, 10.0], "op": "subtract"}]}}));
    let w = bake(&r, opts(3)).unwrap();
    let (mut open, mut trench) = (Vec::new(), Vec::new());
    for (_, m) in &w.terrain_chunks {
        assert!(m.has_colors(), "every terrain chunk carries vertex colors");
        for (p, c) in m.positions.iter().zip(&m.colors) {
            assert!((0.0..=1.0).contains(&c[0]) && c[3] == 1.0);
            if p[0].abs() > 6.0 && p[2].abs() < 10.0 {
                open.push(c[0]);
            } else if p[0].abs() < 0.3 && p[1] < -3.0 && p[2].abs() < 6.0 {
                trench.push(c[0]);
            }
        }
    }
    let mean = |v: &[f32]| v.iter().sum::<f32>() / v.len().max(1) as f32;
    assert!(!open.is_empty() && !trench.is_empty());
    assert!(mean(&open) > 0.9, "open ground should be unoccluded, got {}", mean(&open));
    assert!(mean(&trench) < mean(&open) - 0.2, "trench {} vs open {}", mean(&trench), mean(&open));

    let files = encode_outputs(&w);
    let doc = read_glb_json(&files[0].bytes).unwrap();
    assert!(doc["meshes"][0]["primitives"][0]["attributes"]["COLOR_0"].is_u64());
    let lib = read_glb_json(&files[1].bytes).unwrap();
    assert!(lib["meshes"].is_null(), "no library meshes in this recipe");
}

#[test]
fn randomized_reef_has_varied_dressing() {
    let r = randomize_recipe(&RandomizeConfig { name: "reef".into(), world_size: 96.0, ..Default::default() });
    assert!(r.validate().is_empty(), "errors: {:?}", r.validate());
    let w = bake(&r, opts(4)).unwrap();
    for layer in ["kelp_forest", "coral_garden", "brain_corals", "table_corals", "sea_grass", "pebbles"] {
        let n = w.layers.iter().find(|l| l.layer == layer).map(|l| l.count());
        assert!(n.is_some_and(|n| n > 0), "layer {layer} should place instances, got {n:?}");
    }
    assert!(w.meshes.iter().any(|(id, m)| id == "branch_coral" && m.triangle_count() > 100));
}

#[test]
fn randomized_shipwreck_is_a_grounded_heeled_library_prop() {
    let cfg = RandomizeConfig { name: "wreck".into(), world_size: 96.0, shipwreck: true, external_props: vec![], ..Default::default() };
    let r = randomize_recipe(&cfg);
    assert!(r.validate().is_empty(), "errors: {:?}", r.validate());
    let w = bake(&r, opts(4)).unwrap();
    let wreck = w.props.iter().find(|p| p.id == "shipwreck").expect("shipwreck prop");
    assert!(!wreck.external && wreck.grounded);
    // Heeled over: the prop's up axis is tilted but still mostly upright.
    let [x, y, z, s] = wreck.instance.rotation;
    let up_y = 1.0 - 2.0 * (x * x + z * z);
    assert!(up_y < 0.98 && up_y > 0.85, "up.y = {up_y} (w = {s}, y = {y})");
    assert!(w.meshes.iter().any(|(id, m)| id == "shipwreck" && m.has_colors() && m.triangle_count() > 300));
    let lib = read_glb_json(&encode_outputs(&w)[1].bytes).unwrap();
    let ship = lib["meshes"].as_array().unwrap().iter().find(|m| m["name"] == "shipwreck").unwrap();
    assert!(ship["primitives"][0]["attributes"]["COLOR_0"].is_u64());
}

#[test]
fn validation_reports_bad_references() {
    let r = flat(serde_json::json!({
        "scatter": [{"id": "x", "mesh": "missing", "density": 1.0, "zone": "nowhere"}]
    }));
    let errors = r.validate();
    assert!(errors.iter().any(|e| e.contains("unknown mesh")));
    assert!(errors.iter().any(|e| e.contains("unknown zone")));
    assert!(bake(&r, opts(1)).is_err());
}

fn recipes_dir() -> PathBuf {
    // crates/arcore_procgen -> repository root -> 3d/procgen/recipes
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../../../3d/procgen/recipes")
}

#[test]
fn shipped_recipes_validate() {
    let mut n = 0;
    for entry in std::fs::read_dir(recipes_dir()).expect("recipes directory") {
        let path = entry.unwrap().path();
        if path.extension().is_some_and(|e| e == "json") {
            let r = Recipe::from_json(&std::fs::read_to_string(&path).unwrap())
                .unwrap_or_else(|e| panic!("{}: {e}", path.display()));
            assert!(r.validate().is_empty(), "{}: {:?}", path.display(), r.validate());
            n += 1;
        }
    }
    assert!(n >= 2, "expected at least two shipped recipes");
}

#[test]
fn randomize_produces_valid_deterministic_bakeable_recipes() {
    for theme in [Theme::UnderwaterCartoon, Theme::UnderwaterBasin, Theme::CanyonArch, Theme::OverlandCartoon, Theme::SkyIslands] {
        let cfg = RandomizeConfig {
            name: format!("test-{}", theme.as_str()),
            seed: 4242,
            theme,
            world_size: 48.0,
            voxel: 1.0,
            mesas: 2,
            arches: 1,
            tunnels: 1,
            kelp_density: 0.1,
            external_props: vec!["custom_ship".into()],
            shipwreck: false,
            vents: 0,
            ruins: false,
            crater: false,
            link_center: None,
            island_hints: vec![],
        };
        let r1 = randomize_recipe(&cfg);
        let r2 = randomize_recipe(&cfg);
        assert!(r1.validate().is_empty(), "errors: {:?}", r1.validate());
        assert_eq!(serde_json::to_string(&r1).unwrap(), serde_json::to_string(&r2).unwrap());
        let w = bake(&r1, opts(2)).unwrap();
        assert!(!w.terrain_chunks.is_empty());
        assert_eq!(w.props.len(), 1);
        assert!(w.props[0].external && w.props[0].grounded);
    }
}

fn layer_count(w: &arcore_procgen::WorldBake, layer: &str) -> usize {
    w.layers.iter().find(|l| l.layer == layer).map_or(0, |l| l.count())
}

#[test]
fn reef_extras_add_fans_anemones_and_a_vent_field() {
    let cfg = RandomizeConfig { name: "vents".into(), world_size: 128.0, vents: 3, external_props: vec![], ..Default::default() };
    let r = randomize_recipe(&cfg);
    assert!(r.validate().is_empty(), "errors: {:?}", r.validate());
    let w = bake(&r, opts(4)).unwrap();
    let vents: Vec<_> = w.props.iter().filter(|p| p.id.starts_with("vent_chimney")).collect();
    assert_eq!(vents.len(), 3);
    assert!(vents.iter().all(|p| p.grounded));
    for layer in ["sea_fans", "anemones", "tube_worms"] {
        assert!(layer_count(&w, layer) > 0, "layer {layer} should place instances");
    }
}

#[test]
fn overland_theme_grows_forests_meadows_and_a_lake() {
    let cfg = RandomizeConfig { name: "land".into(), theme: Theme::OverlandCartoon, world_size: 160.0, external_props: vec![], ..Default::default() };
    let r = randomize_recipe(&cfg);
    assert!(r.validate().is_empty(), "errors: {:?}", r.validate());
    assert_eq!(r.water_level, Some(0.0));
    let w = bake(&r, opts(4)).unwrap();
    for layer in ["pine_forest", "meadow_grass", "wildflowers", "bushes"] {
        assert!(layer_count(&w, layer) > 0, "layer {layer} should place instances");
    }
    let pine = w.meshes.iter().find(|(id, _)| id == "pine_tree").expect("pine mesh");
    assert!(pine.1.has_colors());
}

#[test]
fn sky_islands_float_with_vines_underneath() {
    let cfg = RandomizeConfig { name: "sky".into(), theme: Theme::SkyIslands, world_size: 192.0, external_props: vec![], ..Default::default() };
    let r = randomize_recipe(&cfg);
    assert!(r.validate().is_empty(), "errors: {:?}", r.validate());
    assert_eq!(r.water_level, None);
    let w = bake(&r, opts(4)).unwrap();
    // Open air under the islands: the bottom layer of the field is empty.
    let [nx, _, nz] = w.field.spec.dims;
    assert!((0..nz).all(|z| (0..nx).all(|x| w.field.at(x, 0, z) < 0.0)));
    for layer in ["island_grass", "hanging_vines", "island_oaks"] {
        assert!(layer_count(&w, layer) > 0, "layer {layer} should place instances");
    }
}
#[test]
fn stack_links_lake_to_anchor_and_islands_to_hills() {
    let (worlds, receipt) = randomize_stack(&RandomizeConfig { seed: 77, external_props: vec![], ..Default::default() }, ["r", "o", "s"]);
    assert_eq!(worlds.len(), 3);
    for (_, r) in &worlds {
        assert!(r.validate().is_empty(), "{}: {:?}", r.name, r.validate());
    }
    let lake = worlds[1].1.zones.iter().find(|z| z.id == "lake").unwrap();
    assert_eq!(lake.center, [0.0, 0.0]);
    let hints = receipt["anchors"]["island_hints"].as_array().unwrap();
    assert!(!hints.is_empty());
    // At least one island sits exactly over a hint.
    let islands: Vec<_> = worlds[2].1.zones.iter().filter(|z| z.id.starts_with("island-")).collect();
    assert!(hints.iter().any(|h| islands.iter().any(|z| (z.center[0] as f64 - h[0].as_f64().unwrap()).abs() < 1e-3)));
    let w = bake(&worlds[2].1, opts(4)).unwrap();
    let preview = arcore_procgen::export::preview::build_preview(&w.field, None, 32);
    assert!(preview["bottom"].as_array().unwrap().iter().any(|b| !b.is_null()), "islands have undersides");
}
#[test]
fn crater_zone_is_carved_and_kept_clear_of_scatter() {
    let cfg = RandomizeConfig { name: "crash".into(), theme: Theme::OverlandCartoon, world_size: 192.0, crater: true, external_props: vec![], ..Default::default() };
    let r = randomize_recipe(&cfg);
    assert!(r.validate().is_empty(), "errors: {:?}", r.validate());
    let zone = r.zones.iter().find(|z| z.id == "crater").expect("crater zone");
    assert!(zone.clear);
    let w = bake(&r, opts(4)).unwrap();
    let inside = w.layers.iter().flat_map(|l| l.cells.iter()).flat_map(|c| c.instances.iter()).filter(|i| {
        ((i.position[0] - zone.center[0]).powi(2) + (i.position[2] - zone.center[1]).powi(2)).sqrt() < zone.radius
    });
    assert_eq!(inside.count(), 0, "nothing is scattered inside a clear zone");
}
#[test]
fn mesh_detail_refines_large_meshes_and_ships_lod_twins() {
    let cfg = RandomizeConfig { name: "detail".into(), world_size: 96.0, external_props: vec![], ..Default::default() };
    let r = randomize_recipe(&cfg);
    let plain = bake(&r, opts(4)).unwrap();
    let fine = bake(&r, BakeOptions { threads: 4, density_scale: 1.0, mesh_detail: 1 }).unwrap();
    let tris = |w: &arcore_procgen::WorldBake, id: &str| w.meshes.iter().find(|(m, _)| m == id).map(|(_, m)| m.triangle_count());
    assert!(plain.meshes.iter().all(|(id, _)| !id.ends_with("__lod")), "no twins without extra detail");
    // A boulder is big enough to refine; its twin is the recipe-level mesh.
    assert!(tris(&fine, "boulder").unwrap() > tris(&plain, "boulder").unwrap());
    assert_eq!(tris(&fine, "boulder__lod"), tris(&plain, "boulder"));
    // A pebble is too small for the extra triangles to show: unchanged, and no twin.
    assert_eq!(tris(&fine, "pebble"), tris(&plain, "pebble"));
    assert_eq!(tris(&fine, "pebble__lod"), None);
    // Placement does not depend on mesh detail.
    assert_eq!(layer_count(&fine, "seabed_rocks"), layer_count(&plain, "seabed_rocks"));
}

#[test]
fn density_scale_above_one_lifts_the_per_cell_cap() {
    let cfg = RandomizeConfig { name: "dense".into(), world_size: 96.0, external_props: vec![], ..Default::default() };
    let r = randomize_recipe(&cfg);
    let cap = r.scatter.iter().find(|l| l.id == "sea_grass").unwrap().max_per_cell.unwrap() as usize;
    let most = |w: &arcore_procgen::WorldBake| {
        w.layers.iter().find(|l| l.layer == "sea_grass").unwrap().cells.iter().map(|c| c.instances.len()).max().unwrap()
    };
    let base = bake(&r, opts(4)).unwrap();
    let dense = bake(&r, BakeOptions { threads: 4, density_scale: 3.0, mesh_detail: 0 }).unwrap();
    assert!(most(&base) <= cap);
    assert!(most(&dense) > cap && most(&dense) <= cap * 3, "cap scales with density: {} vs {cap}", most(&dense));
}