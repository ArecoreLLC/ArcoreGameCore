//! Stage 6 — export. Writes the engine-neutral bake bundle:
//!
//! - `terrain.glb`    one mesh node per non-empty cell (`cell_<x>_<z>`)
//! - `meshes.glb`     generated mesh library (node name = recipe mesh id)
//! - `instances.json` scatter layers and props, grouped by cell
//! - `preview.json`   coarse height grid for neighboring levels (see `preview.rs`)
//! - `manifest.json`  provenance receipt (recipe hash, counts, timings, output SHA-256)

use super::glb::write_glb;
use super::preview::{build_preview, PREVIEW_RESOLUTION};
use crate::common::sha256::sha256_hex;
use crate::pipeline::{WorldBake, GENERATOR, VERSION};
use crate::recipe::Recipe;
use serde_json::json;
use std::fs;
use std::path::Path;

pub const MANIFEST_SCHEMA: &str = "arcore.procgen.bake-manifest.v1";
pub const INSTANCES_SCHEMA: &str = "arcore.procgen.instances.v1";

pub struct BundleFile {
    pub name: &'static str,
    pub bytes: Vec<u8>,
}

/// Encode the deterministic outputs (everything except the manifest).
pub fn encode_outputs(bake: &WorldBake) -> Vec<BundleFile> {
    encode_outputs_with_water(bake, None)
}

/// As [`encode_outputs`], recording `water_level` in the preview.
pub fn encode_outputs_with_water(bake: &WorldBake, water_level: Option<f32>) -> Vec<BundleFile> {
    let generator = format!("{GENERATOR} {VERSION}");
    let terrain: Vec<(String, &_)> = bake
        .terrain_chunks
        .iter()
        .map(|(c, m)| (format!("cell_{}_{}", c[0], c[1]), m))
        .collect();
    let meshes: Vec<(String, &_)> = bake.meshes.iter().map(|(id, m)| (id.clone(), m)).collect();
    let instances = json!({
        "schema": INSTANCES_SCHEMA,
        "transform": "position [x,y,z] meters, rotation [x,y,z,w] quaternion, uniform scale",
        "cells": bake.cells,
        "layers": bake.layers,
        "props": bake.props,
    });
    vec![
        BundleFile { name: "terrain.glb", bytes: write_glb(&terrain, &generator) },
        BundleFile { name: "meshes.glb", bytes: write_glb(&meshes, &generator) },
        BundleFile {
            name: "instances.json",
            bytes: serde_json::to_vec(&instances).expect("instances serialize"),
        },
        BundleFile {
            name: "preview.json",
            bytes: serde_json::to_vec(&build_preview(&bake.field, water_level, PREVIEW_RESOLUTION))
                .expect("preview serializes"),
        },
    ]
}

/// Write the bundle into `dir` and return the manifest JSON.
pub fn write_bundle(
    bake: &WorldBake,
    recipe: &Recipe,
    recipe_bytes: &[u8],
    dir: &Path,
) -> std::io::Result<serde_json::Value> {
    fs::create_dir_all(dir)?;
    let files = encode_outputs_with_water(bake, recipe.water_level);
    let mut outputs = Vec::new();
    for f in &files {
        fs::write(dir.join(f.name), &f.bytes)?;
        outputs.push(json!({"path": f.name, "bytes": f.bytes.len(), "sha256": sha256_hex(&f.bytes)}));
    }
    let manifest = json!({
        "schema": MANIFEST_SCHEMA,
        "generator": {"name": GENERATOR, "version": VERSION},
        "recipe": {"name": recipe.name, "seed": recipe.seed, "sha256": sha256_hex(recipe_bytes)},
        "options": bake.options,
        "coordinate_system": "glTF: +Y up, right-handed, meters; density > 0 is solid",
        "bounds": recipe.bounds,
        "water_level": recipe.water_level,
        "cells": bake.cells,
        "zones": recipe.zones,
        "presentation": recipe.presentation,
        "counts": bake.counts(),
        "stages": bake.stages,
        "outputs": outputs,
        "note": "Stage timings vary per run; output hashes are deterministic for a recipe, options and generator version."
    });
    fs::write(dir.join("manifest.json"), serde_json::to_vec_pretty(&manifest).expect("manifest serializes"))?;
    Ok(manifest)
}
