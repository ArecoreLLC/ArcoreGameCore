//! Stage 4 — parametric mesh library. Small, code-generated meshes referenced by
//! scatter layers and props (no external model files).

use super::ship::{ship, ShipParams};
use super::surface::Mesh;
use super::tree::{tree, TreeParams};
use crate::common::math::Vec3;
use crate::common::noise::fbm3;
use crate::common::rng::{sub_seed, Rng};
use crate::recipe::{MeshKind, MeshSpec};
use std::collections::HashMap;
use std::f32::consts::TAU;

/// Builds one library mesh. `detail` adds tessellation on top of what the recipe
/// asks for (see `BakeOptions::mesh_detail`); 0 reproduces the recipe exactly.
pub fn build_mesh(spec: &MeshSpec, seed: u64, detail: u32) -> Mesh {
    // Extra tessellation is wasted on small meshes (a pebble's silhouette is a few
    // pixels), so each kind only takes it above a size where it shows.
    let d = detail.min(2);
    let over = |size: f32, least: f32| if size >= least { d } else { 0 };
    match &spec.kind {
        MeshKind::Rock { radius, subdivisions, roughness } => {
            rock(*radius, (*subdivisions + over(*radius, 0.7)).min(4), *roughness, sub_seed(seed, &format!("mesh.{}", spec.id)))
        }
        MeshKind::Lathe { profile, segments } => {
            let widest = profile.iter().fold(0.0f32, |m, p| m.max(p[0]));
            lathe(profile, *segments + *segments * over(widest, 0.3) / 2)
        }
        MeshKind::Blade { length, width, segments, bend } => blade(*length, *width, *segments + 2 * over(*length, 2.0), *bend),
        MeshKind::Branch { height, radius, levels, branches, spread_deg, sides } => branch(
            *height,
            *radius,
            *levels,
            *branches,
            *spread_deg,
            (*sides + 2 * over(*radius, 0.1)).min(12),
            sub_seed(seed, &format!("mesh.{}", spec.id)),
        ),
        MeshKind::Ship { length, beam, depth, masts, mast_height, damage } => ship(
            &ShipParams {
                length: *length,
                beam: *beam,
                depth: *depth,
                masts: *masts,
                mast_height: *mast_height,
                damage: *damage,
            },
            sub_seed(seed, &format!("mesh.{}", spec.id)),
        ),
        MeshKind::Tuft { blades, radius, length, width } => {
            tuft(*blades, *radius, *length, *width, sub_seed(seed, &format!("mesh.{}", spec.id)))
        }
        MeshKind::Tree { height, trunk_radius, canopy_radius, style, lobes } => tree(
            &TreeParams {
                height: *height,
                trunk_radius: *trunk_radius,
                canopy_radius: *canopy_radius,
                style: *style,
                lobes: *lobes,
                detail: d,
            },
            sub_seed(seed, &format!("mesh.{}", spec.id)),
        ),
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
        ..Mesh::default()
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

/// A clump of two-segment blades rooted within `radius` of the origin, each with
/// its own heading, height and outward lean. Normals point up-and-out so the clump
/// shades as one soft mound instead of flickering blade by blade.
pub fn tuft(blades: u32, radius: f32, length: f32, width: f32, seed: u64) -> Mesh {
    let mut rng = Rng::new(seed);
    let mut m = Mesh::default();
    for i in 0..blades.max(1) {
        let around = TAU * i as f32 / blades.max(1) as f32 + rng.range(-0.5, 0.5);
        let out = Vec3::new(around.cos(), 0.0, around.sin());
        let root = out * (radius * rng.range(0.15, 1.0).sqrt());
        let yaw = rng.range(0.0, TAU);
        let side = Vec3::new(yaw.cos(), 0.0, yaw.sin()) * (width * 0.5);
        let (tall, lean) = (length * rng.range(0.6, 1.15), length * rng.range(0.1, 0.45));
        let base = m.positions.len() as u32;
        for (t, taper) in [(0.0f32, 1.0f32), (0.55, 0.7), (1.0, 0.08)] {
            let spine = root + Vec3::Y * (tall * t) + out * (lean * t * t);
            m.positions.push((spine - side * taper).to_array());
            m.positions.push((spine + side * taper).to_array());
            let n = (Vec3::Y + out * 0.5).normalize_or(Vec3::Y);
            m.normals.push(n.to_array());
            m.normals.push(n.to_array());
        }
        for s in 0..2u32 {
            let b = base + 2 * s;
            m.indices.extend_from_slice(&[b, b + 1, b + 3, b, b + 3, b + 2]);
        }
    }
    m
}

/// Child length and tip radius relative to the parent branch.
const LENGTH_FALLOFF: f32 = 0.68;
const TAPER: f32 = 0.62;

struct BranchShape {
    levels: u32,
    children: u32,
    spread: f32,
    sides: u32,
}

/// Seeded branching tubes growing along +Y from the origin. Each generation is
/// shorter and thinner than its parent and ends in a rounded tip.
pub fn branch(height: f32, radius: f32, levels: u32, branches: u32, spread_deg: f32, sides: u32, seed: u64) -> Mesh {
    let shape = BranchShape {
        levels: levels.clamp(1, 4),
        children: branches.clamp(1, 5),
        spread: spread_deg.to_radians(),
        sides: sides.clamp(3, 12),
    };
    // Trunk length such that the summed generations reach about `height`.
    let reach: f32 = (0..shape.levels).map(|l| LENGTH_FALLOFF.powi(l as i32)).sum();
    let mut m = Mesh::default();
    let mut rng = Rng::new(seed);
    grow_branch(&mut m, &mut rng, &shape, Vec3::ZERO, Vec3::Y, height / reach, radius, 0);
    m.recompute_normals();
    m
}

#[allow(clippy::too_many_arguments)]
fn grow_branch(m: &mut Mesh, rng: &mut Rng, shape: &BranchShape, base: Vec3, dir: Vec3, len: f32, r0: f32, level: u32) {
    let r1 = r0 * TAPER;
    let last = level + 1 >= shape.levels;
    let (u, v) = push_tube(m, base, dir, len, r0, r1, shape.sides, last);
    if last {
        return;
    }
    let tip = base + dir * len;
    let turn = rng.range(0.0, TAU);
    for c in 0..shape.children {
        let azimuth = turn + TAU * c as f32 / shape.children as f32 + rng.range(-0.35, 0.35);
        let tilt = shape.spread * rng.range(0.7, 1.3);
        let side = u * azimuth.cos() + v * azimuth.sin();
        let child_dir = (dir * tilt.cos() + side * tilt.sin()).normalize_or(dir);
        let child_len = len * LENGTH_FALLOFF * rng.range(0.85, 1.15);
        grow_branch(m, rng, shape, tip, child_dir, child_len, r1, level + 1);
    }
}

/// Append an outward-facing tapered tube from `base` along unit `dir`, optionally
/// closed with a rounded tip. Returns the cross-section frame `(u, v)`.
#[allow(clippy::too_many_arguments)]
pub(crate) fn push_tube(m: &mut Mesh, base: Vec3, dir: Vec3, len: f32, r0: f32, r1: f32, sides: u32, cap: bool) -> (Vec3, Vec3) {
    // Frame with v x u = dir, matching the lathe winding.
    let reference = if dir.x.abs() < 0.9 { Vec3::new(1.0, 0.0, 0.0) } else { Vec3::new(0.0, 0.0, 1.0) };
    let u = dir.cross(reference).normalize_or(Vec3::new(1.0, 0.0, 0.0));
    let v = u.cross(dir);
    let tip = base + dir * len;
    let ring0 = m.positions.len() as u32;
    for (center, r) in [(base, r0), (tip, r1)] {
        for s in 0..sides {
            let a = TAU * s as f32 / sides as f32;
            m.positions.push((center + (u * a.cos() + v * a.sin()) * r).to_array());
        }
    }
    for s in 0..sides {
        let (i0, i1) = (ring0 + s, ring0 + (s + 1) % sides);
        let (j0, j1) = (i0 + sides, i1 + sides);
        m.indices.extend_from_slice(&[i0, j0, i1, i1, j0, j1]);
    }
    if cap {
        let apex = m.positions.len() as u32;
        m.positions.push((tip + dir * r1).to_array());
        for s in 0..sides {
            let (j0, j1) = (ring0 + sides + s, ring0 + sides + (s + 1) % sides);
            m.indices.extend_from_slice(&[j0, apex, j1]);
        }
    }
    (u, v)
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

    #[test]
    fn branch_is_seeded_bounded_and_outward() {
        // A single generation is a tapered stem around +Y, so the outward test applies.
        let stem = branch(2.0, 0.2, 1, 3, 30.0, 6, 5);
        assert_eq!(stem.triangle_count(), 6 * 2 + 6);
        assert!(outward(&stem));
        let (lo, hi) = stem.bounds().unwrap();
        assert!(lo.y.abs() < 1e-6 && (hi.y - 2.0).abs() < 0.2, "stem spans its height: {lo:?} {hi:?}");

        let coral = branch(1.6, 0.12, 3, 3, 34.0, 5, 11);
        assert_eq!(coral, branch(1.6, 0.12, 3, 3, 34.0, 5, 11), "same seed, same mesh");
        assert_ne!(coral, branch(1.6, 0.12, 3, 3, 34.0, 5, 12), "seed changes the shape");
        // 1 + 3 + 9 tubes, 9 capped tips.
        assert_eq!(coral.triangle_count(), 13 * 10 + 9 * 5);
        let (lo, hi) = coral.bounds().unwrap();
        assert!(lo.y > -0.2 && hi.y > 0.8 && hi.y < 1.8, "coral height: {lo:?} {hi:?}");
        assert!(coral.normals.iter().all(|n| (Vec3::from_array(*n).length() - 1.0).abs() < 1e-3));
    }
}
