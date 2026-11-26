//! Stage 2 — surface extraction with Surface Nets (one vertex per sign-changing
//! cell, one quad per sign-changing grid edge). Produces a closed, indexed,
//! smooth-normal mesh wherever the surface lies inside the grid.
//!
//! Both passes split the grid into z-ranges across worker threads and merge the
//! per-range results in z order, so output is identical for any thread count.

use super::field::DensityField;
use crate::common::math::Vec3;
use crate::common::parallel::par_ranges;

#[derive(Clone, Debug, Default, PartialEq)]
pub struct Mesh {
    pub positions: Vec<[f32; 3]>,
    pub normals: Vec<[f32; 3]>,
    /// Optional linear RGBA vertex colors (empty, or one per position). Terrain
    /// stores baked ambient occlusion here; see `stages::occlusion`.
    pub colors: Vec<[f32; 4]>,
    pub indices: Vec<u32>,
}

impl Mesh {
    pub fn triangle_count(&self) -> usize {
        self.indices.len() / 3
    }
    pub fn is_empty(&self) -> bool {
        self.indices.is_empty()
    }
    pub fn position(&self, i: u32) -> Vec3 {
        Vec3::from_array(self.positions[i as usize])
    }
    pub fn has_colors(&self) -> bool {
        !self.colors.is_empty() && self.colors.len() == self.positions.len()
    }
    pub fn bounds(&self) -> Option<(Vec3, Vec3)> {
        let mut it = self.positions.iter().map(|p| Vec3::from_array(*p));
        let first = it.next()?;
        Some(it.fold((first, first), |(lo, hi), p| (lo.min(p), hi.max(p))))
    }
    /// Append `other`, transforming positions with `f` and normals with `rot`.
    /// Colors are kept only while every appended mesh carries them.
    pub fn append_transformed(&mut self, other: &Mesh, f: impl Fn(Vec3) -> Vec3, rot: impl Fn(Vec3) -> Vec3) {
        let base = self.positions.len() as u32;
        if (base == 0 || self.has_colors()) && other.has_colors() {
            self.colors.extend_from_slice(&other.colors);
        } else {
            self.colors.clear();
        }
        self.positions.extend(other.positions.iter().map(|p| f(Vec3::from_array(*p)).to_array()));
        self.normals.extend(
            other.normals.iter().map(|n| rot(Vec3::from_array(*n)).normalize_or(Vec3::Y).to_array()),
        );
        self.indices.extend(other.indices.iter().map(|i| i + base));
    }
    /// Recompute area-weighted smooth normals from the triangles.
    pub fn recompute_normals(&mut self) {
        let mut acc = vec![Vec3::ZERO; self.positions.len()];
        for t in self.indices.chunks_exact(3) {
            let (a, b, c) = (self.position(t[0]), self.position(t[1]), self.position(t[2]));
            let n = (b - a).cross(c - a);
            for &i in t {
                acc[i as usize] += n;
            }
        }
        self.normals = acc.into_iter().map(|n| n.normalize_or(Vec3::Y).to_array()).collect();
    }
}

const CORNERS: [[usize; 3]; 8] = [
    [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0],
    [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1],
];
const EDGES: [[usize; 2]; 12] = [
    [0, 1], [2, 3], [4, 5], [6, 7], // x
    [0, 2], [1, 3], [4, 6], [5, 7], // y
    [0, 4], [1, 5], [2, 6], [3, 7], // z
];

/// Single-threaded Surface Nets; see [`surface_nets_threaded`].
pub fn surface_nets(field: &DensityField) -> Mesh {
    surface_nets_threaded(field, 1)
}

/// Surface Nets over `threads` workers. Output does not depend on `threads`.
pub fn surface_nets_threaded(field: &DensityField, threads: usize) -> Mesh {
    let s = field.spec;
    let [nx, ny, nz] = s.dims;
    let mut mesh = Mesh::default();
    if nx < 2 || ny < 2 || nz < 2 {
        return mesh;
    }
    let (cx, cy, cz) = (nx - 1, ny - 1, nz - 1);
    let cell_index = |x: usize, y: usize, z: usize| x + cx * (y + cy * z);
    // Sample offsets of the eight cell corners, in `CORNERS` order.
    let corner_offsets = CORNERS.map(|c| c[0] + nx * (c[1] + ny * c[2]));

    // Pass 1: one vertex per sign-changing cell.
    let parts = par_ranges(cz, threads, |zs| {
        let mut out: Vec<(usize, [f32; 3], [f32; 3])> = Vec::new();
        for z in zs {
            for y in 0..cy {
                let row = s.index(0, y, z);
                for x in 0..cx {
                    let base = row + x;
                    let mut v = [0.0f32; 8];
                    let mut mask = 0u8;
                    for (i, off) in corner_offsets.iter().enumerate() {
                        v[i] = field.data[base + off];
                        if v[i] > 0.0 {
                            mask |= 1 << i;
                        }
                    }
                    if mask == 0 || mask == 0xFF {
                        continue;
                    }
                    let (mut sum, mut count) = (Vec3::ZERO, 0.0f32);
                    for e in EDGES {
                        let (a, b) = (v[e[0]], v[e[1]]);
                        if (a > 0.0) == (b > 0.0) {
                            continue;
                        }
                        let t = (a / (a - b)).clamp(0.0, 1.0);
                        let (ca, cb) = (CORNERS[e[0]], CORNERS[e[1]]);
                        let pa = Vec3::new(ca[0] as f32, ca[1] as f32, ca[2] as f32);
                        let pb = Vec3::new(cb[0] as f32, cb[1] as f32, cb[2] as f32);
                        sum += pa + (pb - pa) * t;
                        count += 1.0;
                    }
                    let local = sum * (1.0 / count);
                    let p = s.position(x, y, z) + local * s.voxel;
                    out.push((cell_index(x, y, z), p.to_array(), field.normal(p).to_array()));
                }
            }
        }
        out
    });
    let mut cell_vertex = vec![u32::MAX; cx * cy * cz];
    let total: usize = parts.iter().map(Vec::len).sum();
    mesh.positions.reserve_exact(total);
    mesh.normals.reserve_exact(total);
    for (cell, p, n) in parts.into_iter().flatten() {
        cell_vertex[cell] = mesh.positions.len() as u32;
        mesh.positions.push(p);
        mesh.normals.push(n);
    }

    // Pass 2: for each grid edge with a sign change, connect the four cells around it.
    let (positions, cell_vertex) = (&mesh.positions, &cell_vertex);
    let position = |i: u32| Vec3::from_array(positions[i as usize]);
    let parts = par_ranges(nz, threads, |zs| {
        let mut out: Vec<u32> = Vec::new();
        for z in zs {
            for y in 0..ny {
                for x in 0..nx {
                    let d0 = field.at(x, y, z);
                    for axis in 0..3 {
                        let (u, w) = ((axis + 1) % 3, (axis + 2) % 3);
                        let mut p = [x, y, z];
                        p[axis] += 1;
                        if p[axis] >= s.dims[axis]
                            || [x, y, z][u] == 0
                            || [x, y, z][u] + 1 >= s.dims[u]
                            || [x, y, z][w] == 0
                            || [x, y, z][w] + 1 >= s.dims[w]
                        {
                            continue;
                        }
                        let d1 = field.at(p[0], p[1], p[2]);
                        if (d0 > 0.0) == (d1 > 0.0) {
                            continue;
                        }
                        let quad = [[0, 0], [1, 0], [1, 1], [0, 1]].map(|[du, dw]: [usize; 2]| {
                            let mut c = [x, y, z];
                            c[u] -= 1 - du;
                            c[w] -= 1 - dw;
                            cell_vertex[cell_index(c[0], c[1], c[2])]
                        });
                        if quad.contains(&u32::MAX) {
                            continue;
                        }
                        // Solid -> open along +axis means the surface faces +axis.
                        let facing_positive = d0 > 0.0;
                        let order = if facing_positive { [0, 1, 2, 3] } else { [0, 3, 2, 1] };
                        let q = order.map(|i| quad[i]);
                        // Split along the shorter diagonal for nicer triangles.
                        let (a, b, c, d) = (position(q[0]), position(q[1]), position(q[2]), position(q[3]));
                        if (a - c).length() <= (b - d).length() {
                            out.extend_from_slice(&[q[0], q[1], q[2], q[0], q[2], q[3]]);
                        } else {
                            out.extend_from_slice(&[q[0], q[1], q[3], q[1], q[2], q[3]]);
                        }
                    }
                }
            }
        }
        out
    });
    mesh.indices = parts.concat();
    mesh
}
