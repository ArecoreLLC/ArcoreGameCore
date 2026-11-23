use arcore_procgen::common::math::Vec3;
use arcore_procgen::export::bundle::encode_outputs;
use arcore_procgen::export::glb::read_glb_json;
use arcore_procgen::recipe::Recipe;
use arcore_procgen::runtime::collision::{glide, raycast};
use arcore_procgen::stages::field::build_field;
use arcore_procgen::stages::surface::surface_nets;
use arcore_procgen::{bake, randomize_recipe, BakeOptions, RandomizeConfig, Theme};
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
    BakeOptions { threads, density_scale: 1.0 }
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
    let half = bake(&r, BakeOptions { threads: 2, density_scale: 0.5 }).unwrap();
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
    for theme in [Theme::UnderwaterCartoon, Theme::UnderwaterBasin, Theme::CanyonArch] {
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
