//! Runtime queries against a density field: sphere glide (swim/fly controllers
//! that slide along rock instead of stopping) and ray casts (snapping, sonar,
//! line of sight). Engines may instead use trimesh collision from the baked mesh.

use crate::common::math::Vec3;
use crate::stages::field::DensityField;

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct RayHit {
    pub position: Vec3,
    pub normal: Vec3,
    pub distance: f32,
}

/// First surface crossing along `dir` within `max_dist`. Starting inside solid
/// material reports a hit at the origin.
pub fn raycast(field: &DensityField, origin: Vec3, dir: Vec3, max_dist: f32) -> Option<RayHit> {
    let dir = dir.normalize_or(Vec3::Y);
    let min_step = field.spec.voxel * 0.25;
    let mut t = 0.0f32;
    let mut prev_t = 0.0f32;
    let mut prev_d = field.sample(origin);
    if prev_d > 0.0 {
        return Some(RayHit { position: origin, normal: field.normal(origin), distance: 0.0 });
    }
    while t < max_dist {
        // Density approximates distance; never step further than one voxel.
        t = (t + (-prev_d * 0.8).clamp(min_step, field.spec.voxel)).min(max_dist);
        let d = field.sample(origin + dir * t);
        if d > 0.0 {
            // Bisect the bracket [prev_t, t].
            let (mut lo, mut hi) = (prev_t, t);
            for _ in 0..12 {
                let mid = 0.5 * (lo + hi);
                if field.sample(origin + dir * mid) > 0.0 {
                    hi = mid;
                } else {
                    lo = mid;
                }
            }
            let p = origin + dir * hi;
            return Some(RayHit { position: p, normal: field.normal(p), distance: hi });
        }
        if t >= max_dist {
            break;
        }
        prev_t = t;
        prev_d = d;
    }
    None
}

/// Move a sphere of `radius` from `pos` by `delta`, sliding along surfaces.
/// Steps are shorter than the radius so thin walls cannot be tunnelled through.
pub fn glide(field: &DensityField, pos: Vec3, delta: Vec3, radius: f32) -> Vec3 {
    let len = delta.length();
    if !(len.is_finite() && radius > 0.0) {
        return pos;
    }
    let steps = ((len / (radius * 0.5)).ceil() as usize).clamp(1, 1024);
    let step = delta * (1.0 / steps as f32);
    let mut p = pos;
    for _ in 0..steps {
        p += step;
        p = depenetrate(field, p, radius);
    }
    p
}

/// Push a sphere out of solid material along the outward normal.
pub fn depenetrate(field: &DensityField, mut p: Vec3, radius: f32) -> Vec3 {
    for _ in 0..4 {
        // Open-side distance to the surface is approximately -density.
        let penetration = radius + field.sample(p);
        if penetration <= 1e-4 {
            break;
        }
        p += field.normal(p) * penetration;
    }
    p
}
