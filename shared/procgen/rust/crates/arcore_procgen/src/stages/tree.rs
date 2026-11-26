//! Stylized tree meshes (broadleaf, pine, palm) for overland and sky-island
//! recipes. Built from the same primitives as the rest of the mesh library:
//! tapered tubes, noise-displaced icospheres and lathed cones.
//!
//! Vertex colors: `r` = part (0 trunk, 1 foliage), `g` = seeded shade per
//! foliage piece in [0, 1], `b` = 0, `a` = 1.

use super::parametric::{lathe, push_tube, rock};
use super::surface::Mesh;
use crate::common::math::Vec3;
use crate::common::rng::Rng;
use crate::recipe::TreeStyle;
use std::f32::consts::TAU;

pub struct TreeParams {
    pub height: f32,
    pub trunk_radius: f32,
    pub canopy_radius: f32,
    pub style: TreeStyle,
    pub lobes: u32,
    /// Extra tessellation (0-2): rounder canopies and trunks, smoother pine tiers.
    pub detail: u32,
}

pub fn tree(p: &TreeParams, seed: u64) -> Mesh {
    let mut rng = Rng::new(seed);
    let mut out = Mesh::default();
    match p.style {
        TreeStyle::Round => round(&mut out, &mut rng, p),
        TreeStyle::Pine => pine(&mut out, &mut rng, p),
        TreeStyle::Palm => palm(&mut out, &mut rng, p),
    }
    out
}

/// Append `part` with every vertex colored `[part_id, shade, 0, 1]`.
fn add(out: &mut Mesh, mut part: Mesh, part_id: f32, shade: f32, offset: Vec3) {
    if part.normals.len() != part.positions.len() {
        part.recompute_normals();
    }
    part.colors = vec![[part_id, shade, 0.0, 1.0]; part.positions.len()];
    out.append_transformed(&part, |v| v + offset, |n| n);
}

fn trunk(out: &mut Mesh, base: Vec3, dir: Vec3, len: f32, r0: f32, r1: f32, detail: u32) {
    let mut m = Mesh::default();
    push_tube(&mut m, base, dir, len, r0, r1, 7 + 3 * detail, false);
    m.recompute_normals();
    add(out, m, 0.0, 0.5, Vec3::ZERO);
}

fn round(out: &mut Mesh, rng: &mut Rng, p: &TreeParams) {
    let cr = p.canopy_radius;
    let crown = (p.height - cr * 0.9).max(p.height * 0.45);
    trunk(out, Vec3::ZERO, Vec3::Y, crown, p.trunk_radius, p.trunk_radius * 0.6, p.detail);
    // A big central lobe, then smaller ones ringed around and slightly below it.
    let lobes = p.lobes.max(1);
    for i in 0..lobes {
        let (offset, radius) = if i == 0 {
            (Vec3::new(0.0, crown, 0.0), cr * 0.85)
        } else {
            let a = TAU * i as f32 / (lobes - 1) as f32 + rng.range(-0.4, 0.4);
            let reach = cr * rng.range(0.45, 0.7);
            (
                Vec3::new(a.cos() * reach, crown + rng.range(-0.35, 0.2) * cr, a.sin() * reach),
                cr * rng.range(0.5, 0.72),
            )
        };
        let blob = rock(radius, 2 + p.detail.min(1), 0.22, rng.next_u64());
        add(out, blob, 1.0, rng.next_f32(), offset);
    }
}

fn pine(out: &mut Mesh, rng: &mut Rng, p: &TreeParams) {
    let base = p.height * 0.22;
    trunk(out, Vec3::ZERO, Vec3::Y, base + p.height * 0.1, p.trunk_radius, p.trunk_radius * 0.7, p.detail);
    let tiers = p.lobes.clamp(1, 6);
    let span = p.height - base;
    // Overlapping cones that shrink toward the top.
    let tier_h = span / (tiers as f32 * 0.72 + 0.28);
    for t in 0..tiers {
        let f = t as f32 / tiers as f32;
        let y0 = base + t as f32 * tier_h * 0.72;
        let r = p.canopy_radius * (1.0 - f * 0.62) * rng.range(0.92, 1.06);
        let cone = lathe(&[[0.0, y0], [r, y0], [r * 0.55, y0 + tier_h * 0.45], [0.0, y0 + tier_h]], 9 + 4 * p.detail);
        add(out, cone, 1.0, (f + rng.range(0.0, 0.3)).min(1.0), Vec3::ZERO);
    }
}

fn palm(out: &mut Mesh, rng: &mut Rng, p: &TreeParams) {
    // Segmented trunk leaning along a seeded heading, curving back up near the top.
    let heading = rng.range(0.0, TAU);
    let lean = Vec3::new(heading.cos(), 0.0, heading.sin());
    let segments = 5;
    let seg_len = p.height / segments as f32;
    let mut at = Vec3::ZERO;
    let mut r = p.trunk_radius;
    for s in 0..segments {
        let bend = 0.28 * (1.0 - s as f32 / segments as f32);
        let dir = (Vec3::Y + lean * bend).normalize_or(Vec3::Y);
        trunk(out, at, dir, seg_len * 1.04, r, r * 0.9, p.detail);
        at = at + dir * seg_len;
        r *= 0.9;
    }
    // Fronds: arched strips radiating from the crown, drooping toward the tip.
    let fronds = p.lobes.clamp(3, 8);
    let len = p.canopy_radius;
    for f in 0..fronds {
        let a = TAU * f as f32 / fronds as f32 + rng.range(-0.25, 0.25);
        let out_dir = Vec3::new(a.cos(), 0.0, a.sin());
        let side = Vec3::Y.cross(out_dir).normalize_or(Vec3::new(1.0, 0.0, 0.0));
        let droop = rng.range(0.7, 1.1);
        let mut m = Mesh::default();
        let n = 6;
        for i in 0..=n {
            let t = i as f32 / n as f32;
            let width = len * 0.22 * (1.0 - t * 0.8) * (t * 4.0).min(1.0).max(0.25);
            let spine = out_dir * (len * t) + Vec3::Y * (len * (0.35 * t - droop * t * t * 0.75));
            m.positions.push((spine - side * width).to_array());
            m.positions.push((spine + side * width).to_array());
        }
        for i in 0..n {
            let b = 2 * i as u32;
            m.indices.extend_from_slice(&[b, b + 3, b + 1, b, b + 2, b + 3]);
        }
        m.recompute_normals();
        add(out, m, 1.0, rng.next_f32(), at);
    }
    // A few coconuts under the crown.
    for c in 0..3 {
        let a = TAU * c as f32 / 3.0 + heading;
        let nut = rock(p.trunk_radius * 0.75, 1, 0.1, rng.next_u64());
        add(out, nut, 0.0, 0.2, at + Vec3::new(a.cos(), -0.6, a.sin()) * (p.trunk_radius * 1.2));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_style_is_seeded_colored_and_sized() {
        for style in [TreeStyle::Round, TreeStyle::Pine, TreeStyle::Palm] {
            let p = TreeParams { height: 6.0, trunk_radius: 0.3, canopy_radius: 2.0, style, lobes: 5, detail: 0 };
            let a = tree(&p, 3);
            assert_eq!(a, tree(&p, 3), "{style:?}: same seed, same mesh");
            assert!(a.has_colors() && a.normals.len() == a.positions.len());
            assert!(a.colors.iter().any(|c| c[0] == 0.0) && a.colors.iter().any(|c| c[0] == 1.0));
            let (lo, hi) = a.bounds().unwrap();
            assert!(lo.y > -1.0 && hi.y > 4.0 && hi.y < 8.5, "{style:?} height: {lo:?} {hi:?}");
        }
    }
}
