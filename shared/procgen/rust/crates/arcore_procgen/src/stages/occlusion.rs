//! Stage 2b — baked vertex ambient occlusion from the density field.
//!
//! Density approximates signed distance, so a point `r` meters out along the
//! normal reads about `-r` on open ground and closer to zero inside creases,
//! tunnels and under overhangs. The result is stored as a grayscale linear
//! vertex color (`1.0` = fully open) and exported as glTF `COLOR_0`. Consumers
//! decide whether and how strongly to use it.

use super::field::DensityField;
use super::surface::Mesh;
use crate::common::math::Vec3;
use crate::common::parallel::par_ranges;

/// Probe distances in voxels and their weights (weights sum to 1).
const PROBES: [(f32, f32); 3] = [(1.0, 0.45), (2.5, 0.35), (5.0, 0.20)];

/// Occlusion in `[0, 1]` (1 = open) at `p` with outward normal `n`.
pub fn occlusion_at(field: &DensityField, p: Vec3, n: Vec3) -> f32 {
    let mut blocked = 0.0;
    for (voxels, weight) in PROBES {
        let r = voxels * field.spec.voxel;
        blocked += weight * (1.0 + field.sample(p + n * r) / r).clamp(0.0, 1.0);
    }
    1.0 - blocked
}

/// Fill `mesh.colors` with grayscale occlusion. Output does not depend on `threads`.
pub fn bake_vertex_occlusion(mesh: &mut Mesh, field: &DensityField, threads: usize) {
    let (positions, normals) = (&mesh.positions, &mesh.normals);
    let parts = par_ranges(positions.len(), threads, |range| {
        range
            .map(|i| {
                let ao = occlusion_at(field, Vec3::from_array(positions[i]), Vec3::from_array(normals[i]));
                [ao, ao, ao, 1.0]
            })
            .collect::<Vec<[f32; 4]>>()
    });
    mesh.colors = parts.concat();
}
