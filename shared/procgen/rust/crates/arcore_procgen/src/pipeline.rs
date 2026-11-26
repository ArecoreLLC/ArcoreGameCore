//! Pipeline runner: executes the ordered stages and records a report per stage.

use crate::common::parallel::par_ranges;
use crate::recipe::Recipe;
use crate::stages::cells::{split_mesh, CellGrid, CellId};
use crate::stages::field::{build_field, DensityField};
use crate::stages::parametric::build_mesh;
use crate::stages::scatter::{place_props, scatter_layer, LayerInstances, PlacedProp};
use crate::stages::occlusion::bake_vertex_occlusion;
use crate::stages::surface::{surface_nets_threaded, Mesh};
use serde::Serialize;
use std::time::Instant;

pub const GENERATOR: &str = "arcore_procgen";
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
/// Suffix of the lower-detail twin of a library mesh (see `BakeOptions::mesh_detail`).
pub const LOD_SUFFIX: &str = "__lod";

#[derive(Clone, Debug, Serialize)]
pub struct BakeOptions {
    /// Worker threads for the field, surface and scatter stages (does not change results).
    pub threads: usize,
    /// Multiplier on every scatter density (quality tiers: e.g. 0.25 / 0.5 / 1.0).
    pub density_scale: f32,
    /// Extra tessellation for library meshes: 0 = as the recipe says, 1 or 2 = rounder
    /// rocks, smoother lathes, more blade segments, fuller tree canopies.
    pub mesh_detail: u32,
}

impl Default for BakeOptions {
    fn default() -> Self {
        Self {
            threads: std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1),
            density_scale: 1.0,
            mesh_detail: 0,
        }
    }
}

#[derive(Clone, Debug, Serialize)]
pub struct StageReport {
    pub stage: &'static str,
    pub millis: f64,
    pub detail: String,
}

pub struct WorldBake {
    pub options: BakeOptions,
    pub field: DensityField,
    pub cells: CellGrid,
    pub terrain_chunks: Vec<(CellId, Mesh)>,
    pub meshes: Vec<(String, Mesh)>,
    pub layers: Vec<LayerInstances>,
    pub props: Vec<PlacedProp>,
    pub stages: Vec<StageReport>,
}

impl WorldBake {
    pub fn counts(&self) -> serde_json::Value {
        let tris: usize = self.terrain_chunks.iter().map(|(_, m)| m.triangle_count()).sum();
        let verts: usize = self.terrain_chunks.iter().map(|(_, m)| m.positions.len()).sum();
        let layers: serde_json::Map<String, serde_json::Value> =
            self.layers.iter().map(|l| (l.layer.clone(), l.count().into())).collect();
        serde_json::json!({
            "density_samples": self.field.data.len(),
            "terrain_cells": self.terrain_chunks.len(),
            "terrain_vertices": verts,
            "terrain_triangles": tris,
            "library_meshes": self.meshes.len(),
            "instances": layers,
            "instances_total": self.layers.iter().map(|l| l.count()).sum::<usize>(),
            "props": self.props.len(),
            "props_ungrounded": self.props.iter().filter(|p| !p.grounded).count(),
        })
    }
}

#[derive(Debug)]
pub enum BakeError {
    Invalid(Vec<String>),
}

impl std::fmt::Display for BakeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            BakeError::Invalid(e) => write!(f, "invalid recipe:\n  - {}", e.join("\n  - ")),
        }
    }
}

impl std::error::Error for BakeError {}

/// Run stages 0–5 in order. Export (stage 6) is separate so callers can keep
/// results in memory (e.g. an engine plugin) or write the bundle to disk.
pub fn bake(recipe: &Recipe, options: BakeOptions) -> Result<WorldBake, BakeError> {
    let mut stages = Vec::new();
    let mut timed = |stage: &'static str, start: Instant, detail: String| {
        stages.push(StageReport { stage, millis: start.elapsed().as_secs_f64() * 1e3, detail });
    };

    let t = Instant::now();
    let errors = recipe.validate();
    if !errors.is_empty() {
        return Err(BakeError::Invalid(errors));
    }
    timed("recipe", t, format!("{} primitives, {} layers", recipe.terrain.primitives.len(), recipe.scatter.len()));

    let t = Instant::now();
    let field = build_field(recipe, options.threads);
    let d = field.spec.dims;
    timed("field", t, format!("{}x{}x{} samples, {:.1}% solid", d[0], d[1], d[2], field.solid_fraction() * 100.0));

    let t = Instant::now();
    let mut surface = surface_nets_threaded(&field, options.threads);
    bake_vertex_occlusion(&mut surface, &field, options.threads);
    timed(
        "surface",
        t,
        format!("{} vertices, {} triangles, vertex AO", surface.positions.len(), surface.triangle_count()),
    );

    let t = Instant::now();
    let cells = CellGrid::new(&field.spec, recipe.cells.size);
    let terrain_chunks = split_mesh(&surface, &cells);
    drop(surface);
    timed("cells", t, format!("{} of {} cells occupied", terrain_chunks.len(), cells.len()));

    let t = Instant::now();
    let mut meshes: Vec<(String, Mesh)> = Vec::new();
    for m in &recipe.meshes {
        let detailed = build_mesh(m, recipe.seed, options.mesh_detail);
        // With extra detail, the recipe-level mesh ships alongside as "<id>__lod" so
        // consumers can draw the heavy one nearby only.
        if options.mesh_detail > 0 {
            let plain = build_mesh(m, recipe.seed, 0);
            if plain.triangle_count() < detailed.triangle_count() {
                meshes.push((format!("{}{LOD_SUFFIX}", m.id), plain));
            }
        }
        meshes.push((m.id.clone(), detailed));
    }
    timed("parametric", t, format!("{} meshes", meshes.len()));

    let t = Instant::now();
    // Layers have independent RNG streams, so they can be placed concurrently.
    let layers: Vec<LayerInstances> = par_ranges(recipe.scatter.len(), options.threads, |range| {
        recipe.scatter[range]
            .iter()
            .map(|l| scatter_layer(recipe, l, &terrain_chunks, options.density_scale))
            .collect::<Vec<_>>()
    })
    .concat();
    let props = place_props(&recipe.props, &field, &cells);
    let total: usize = layers.iter().map(|l| l.count()).sum();
    timed("scatter", t, format!("{total} instances, {} props", props.len()));

    Ok(WorldBake { options, field, cells, terrain_chunks, meshes, layers, props, stages })
}
