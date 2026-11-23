//! Stage 3 — XZ cell grid. Splits geometry and instances into square cells so
//! consumers can cull, stream or LOD per cell (Godot MultiMesh / Unreal HISM batches).

use super::field::GridSpec;
use super::surface::Mesh;
use crate::common::math::Vec3;
use serde::Serialize;
use std::collections::{BTreeMap, HashMap};

#[derive(Clone, Copy, Debug, PartialEq, Serialize)]
pub struct CellGrid {
    /// Minimum XZ corner in meters.
    pub origin: [f32; 2],
    pub size: f32,
    /// Cell counts along X and Z.
    pub counts: [u32; 2],
}

pub type CellId = [u32; 2];

impl CellGrid {
    pub fn new(grid: &GridSpec, cell_size: f32) -> Self {
        let max = grid.max_corner();
        let span_x = (max.x - grid.origin.x).max(cell_size);
        let span_z = (max.z - grid.origin.z).max(cell_size);
        Self {
            origin: [grid.origin.x, grid.origin.z],
            size: cell_size,
            counts: [(span_x / cell_size).ceil() as u32, (span_z / cell_size).ceil() as u32],
        }
    }

    pub fn cell_of(&self, p: Vec3) -> CellId {
        let f = |v: f32, o: f32, n: u32| (((v - o) / self.size).floor().max(0.0) as u32).min(n - 1);
        [f(p.x, self.origin[0], self.counts[0]), f(p.z, self.origin[1], self.counts[1])]
    }

    pub fn len(&self) -> usize {
        (self.counts[0] * self.counts[1]) as usize
    }

    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }
}

/// Split a mesh into per-cell meshes by triangle centroid. Cells are returned in
/// ascending (x, z) order; empty cells are omitted.
pub fn split_mesh(mesh: &Mesh, cells: &CellGrid) -> Vec<(CellId, Mesh)> {
    let mut buckets: BTreeMap<CellId, (Mesh, HashMap<u32, u32>)> = BTreeMap::new();
    for t in mesh.indices.chunks_exact(3) {
        let c = (mesh.position(t[0]) + mesh.position(t[1]) + mesh.position(t[2])) * (1.0 / 3.0);
        let (out, remap) = buckets.entry(cells.cell_of(c)).or_default();
        for &i in t {
            let slot = *remap.entry(i).or_insert_with(|| {
                out.positions.push(mesh.positions[i as usize]);
                out.normals.push(mesh.normals[i as usize]);
                (out.positions.len() - 1) as u32
            });
            out.indices.push(slot);
        }
    }
    buckets.into_iter().map(|(id, (m, _))| (id, m)).collect()
}
