//! Stage 3 — XZ cell grid. Splits geometry and instances into square cells so
//! consumers can cull, stream or LOD per cell (Godot MultiMesh / Unreal HISM batches).

use super::field::GridSpec;
use super::surface::Mesh;
use crate::common::math::Vec3;
use serde::Serialize;

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
/// ascending (x, z) order; empty cells are omitted. Vertex colors are carried over.
pub fn split_mesh(mesh: &Mesh, cells: &CellGrid) -> Vec<(CellId, Mesh)> {
    const UNSET: u32 = u32::MAX;
    let has_colors = mesh.has_colors();
    // Bucket triangles by cell, preserving triangle order within each cell.
    let mut buckets: Vec<Vec<u32>> = vec![Vec::new(); cells.len()];
    for (t, tri) in mesh.indices.chunks_exact(3).enumerate() {
        let c = (mesh.position(tri[0]) + mesh.position(tri[1]) + mesh.position(tri[2])) * (1.0 / 3.0);
        let [cx, cz] = cells.cell_of(c);
        buckets[(cx * cells.counts[1] + cz) as usize].push(t as u32);
    }
    // One shared remap table; each cell resets only the slots it touched.
    let mut remap = vec![UNSET; mesh.positions.len()];
    let mut touched: Vec<u32> = Vec::new();
    let mut chunks = Vec::new();
    for (slot, tris) in buckets.iter().enumerate() {
        if tris.is_empty() {
            continue;
        }
        let mut out = Mesh::default();
        out.indices.reserve_exact(tris.len() * 3);
        for &t in tris {
            let t = t as usize * 3;
            for &i in &mesh.indices[t..t + 3] {
                let entry = &mut remap[i as usize];
                if *entry == UNSET {
                    *entry = out.positions.len() as u32;
                    touched.push(i);
                    out.positions.push(mesh.positions[i as usize]);
                    out.normals.push(mesh.normals[i as usize]);
                    if has_colors {
                        out.colors.push(mesh.colors[i as usize]);
                    }
                }
                out.indices.push(*entry);
            }
        }
        for i in touched.drain(..) {
            remap[i as usize] = UNSET;
        }
        let slot = slot as u32;
        chunks.push(([slot / cells.counts[1], slot % cells.counts[1]], out));
    }
    chunks
}
