//! Stage 4 — parametric mesh library. Small, code-generated meshes referenced by
//! scatter layers and props (no external model files).

use super::surface::Mesh;
use crate::common::math::Vec3;
use crate::common::noise::fbm3;
use crate::common::rng::sub_seed;
use crate::recipe::{MeshKind, MeshSpec};
use std::collections::HashMap;
use std::f32::consts::TAU;

pub fn build_mesh(spec: &MeshSpec, seed: u64) -> Mesh {
    match &spec.kind {
        MeshKind::Rock { radius, subdivisions, roughness } => {
            rock(*radius, *subdivisions, *roughness, sub_seed(seed, &format!("mesh.{}", spec.id)))
        }
        MeshKind::Lathe { profile, segments } => lathe(profile, *segments),
        MeshKind::Blade { length, width, segments, bend } => blade(*length, *width, *segments, *bend),
    }
}

/// Unit icosphere with `sub` midpoint subdivisions.
pub fn icosphere(sub: u32) -> Mesh {
    let t = (1.0 + 5f32.sqrt()) * 0.5;
    let mut pos: Vec<Vec3> = [
        [-1.0, t, 0.0], [1.0, t, 0.0], [-1.0, -t, 0.0], [1.0, -t, 0.0],
        [0.0, -1.0, t], [0.0, 1.0, t], [0.0, -1.0, -t], [0.0, 1.0, -t],
        [t, 0.0, -1.0], [t, 0.0, 1.0], [-t, 0.0, -1.0], [-t, 0.0, 1.0],
    ]
    .iter()
    .map(|p| Vec3::from_array(*p).normalize_or(Vec3::Y))
    .collect();
    let mut faces: Vec<[u32; 3]> = vec![
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
    ];
    for _ in 0..sub {
        let mut cache: HashMap<(u32, u32), u32> = HashMap::new();
        let mut mid = |a: u32, b: u32, pos: &mut Vec<Vec3>| -> u32 {
            let key = (a.min(b), a.max(b));
            *cache.entry(key).or_insert_with(|| {
                pos.push(((pos[a as usize] + pos[b as usize]) * 0.5).normalize_or(Vec3::Y));
                (pos.len() - 1) as u32
            })
        };
        let mut next = Vec::with_capacity(faces.len() * 4);
        for [a, b, c] in faces {
            let (ab, bc, ca) = (mid(a, b, &mut pos), mid(b, c, &mut pos), mid(c, a, &mut pos));
            next.extend_from_slice(&[[a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]]);
        }
        faces = next;
    }
    Mesh {
        normals: pos.iter().map(|p| p.to_array()).collect(),
        positions: pos.iter().map(|p| p.to_array()).collect(),
        indices: faces.into_iter().flatten().collect(),
    }
}

pub fn rock(radius: f32, sub: u32, roughness: f32, seed: u64) -> Mesh {
    let mut m = icosphere(sub);
    for p in &mut m.positions {
        let v = Vec3::from_array(*p);
        let n = fbm3(seed, v * 1.7, 3, 2.0, 0.5);
        // Flatten the underside a little so rocks sit on the ground.
        let squash = if v.y < 0.0 { 0.75 } else { 1.0 };
        let r = radius * (1.0 + roughness * n);
        *p = Vec3::new(v.x * r, v.y * r * squash, v.z * r).to_array();
    }
    m.recompute_normals();
    m
}

/// Surface of revolution around +Y from `[radius, y]` points.
pub fn lathe(profile: &[[f32; 2]], segments: u32) -> Mesh {
    let seg = segments.max(3) as usize;
    let rings = profile.len();
    let mut m = Mesh::default();
    for p in profile {
        for s in 0..seg {
            let a = TAU * s as f32 / seg as f32;
            m.positions.push([p[0] * a.cos(), p[1], p[0] * a.sin()]);
        }
    }
    for r in 0..rings.saturating_sub(1) {
        for s in 0..seg {
            let (i0, i1) = ((r * seg + s) as u32, (r * seg + (s + 1) % seg) as u32);
            let (j0, j1) = (i0 + seg as u32, i1 + seg as u32);
            // Outward-facing (CCW seen from outside).
            m.indices.extend_from_slice(&[i0, j0, i1, i1, j0, j1]);
        }
    }
    m.recompute_normals();
    m
}

/// Tapered strip from y = 0 to `length`, facing +Z, curving toward +Z by `bend` meters at the tip.
pub fn blade(length: f32, width: f32, segments: u32, bend: f32) -> Mesh {
    let n = segments.max(1);
    let mut m = Mesh::default();
    for i in 0..=n {
        let t = i as f32 / n as f32;
        let half = 0.5 * width * (1.0 - 0.85 * t);
        let (y, z) = (length * t, bend * t * t);
        m.positions.push([-half, y, z]);
        m.positions.push([half, y, z]);
    }
    for i in 0..n {
        let b = 2 * i;
        m.indices.extend_from_slice(&[b, b + 1, b + 3, b, b + 3, b + 2]);
    }
    m.recompute_normals();
    m
}

#[cfg(test)]
mod tests {
    use super::*;

    fn outward(m: &Mesh) -> bool {
        m.indices.chunks_exact(3).all(|t| {
            let (a, b, c) = (m.position(t[0]), m.position(t[1]), m.position(t[2]));
            let center = (a + b + c) * (1.0 / 3.0);
            let n = (b - a).cross(c - a);
            n.dot(Vec3::new(center.x, 0.0, center.z)) >= -1e-6 || n.dot(center) >= -1e-6
        })
    }

    #[test]
    fn generated_meshes_are_valid_and_outward() {
        let ico = icosphere(2);
        assert_eq!(ico.triangle_count(), 20 * 16);
        assert!(outward(&ico));
        let lathe = lathe(&[[0.5, 0.0], [0.6, 1.0], [0.3, 2.0]], 12);
        assert_eq!(lathe.triangle_count(), 2 * 12 * 2);
        assert!(outward(&lathe));
        let r = rock(1.0, 2, 0.3, 9);
        assert!(r.normals.iter().all(|n| (Vec3::from_array(*n).length() - 1.0).abs() < 1e-3));
        let b = blade(2.0, 0.3, 4, 0.2);
        assert_eq!(b.triangle_count(), 8);
        assert!(b.normals.iter().all(|n| n[2] > 0.5), "blade faces +Z");
    }
}
