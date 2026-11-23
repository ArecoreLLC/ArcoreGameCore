//! Hash-based value noise and fractal sums. Pure functions of (seed, position).

use super::math::{lerp, Vec3};
use super::rng::hash3;

#[inline]
fn fade(t: f32) -> f32 {
    t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
}

#[inline]
fn corner(seed: u64, x: i32, y: i32, z: i32) -> f32 {
    (hash3(seed, x, y, z) >> 40) as f32 * (2.0 / (1u64 << 24) as f32) - 1.0
}

/// 3D value noise in `[-1, 1]`.
pub fn value3(seed: u64, p: Vec3) -> f32 {
    let (fx, fy, fz) = (p.x.floor(), p.y.floor(), p.z.floor());
    let (xi, yi, zi) = (fx as i32, fy as i32, fz as i32);
    let (u, v, w) = (fade(p.x - fx), fade(p.y - fy), fade(p.z - fz));
    let c = |dx, dy, dz| corner(seed, xi + dx, yi + dy, zi + dz);
    let x00 = lerp(c(0, 0, 0), c(1, 0, 0), u);
    let x10 = lerp(c(0, 1, 0), c(1, 1, 0), u);
    let x01 = lerp(c(0, 0, 1), c(1, 0, 1), u);
    let x11 = lerp(c(0, 1, 1), c(1, 1, 1), u);
    lerp(lerp(x00, x10, v), lerp(x01, x11, v), w)
}

/// Normalized fractal Brownian motion in `[-1, 1]`.
pub fn fbm3(seed: u64, p: Vec3, octaves: u32, lacunarity: f32, gain: f32) -> f32 {
    let (mut sum, mut amp, mut norm, mut freq) = (0.0, 1.0, 0.0, 1.0);
    for o in 0..octaves.max(1) {
        sum += amp * value3(seed.wrapping_add((o as u64).wrapping_mul(0x632B_E59B_D9B4_E019)), p * freq);
        norm += amp;
        amp *= gain;
        freq *= lacunarity;
    }
    sum / norm
}

/// 2D fBm over the XZ plane.
pub fn fbm2(seed: u64, x: f32, z: f32, octaves: u32, lacunarity: f32, gain: f32) -> f32 {
    fbm3(seed, Vec3::new(x, 0.5, z), octaves, lacunarity, gain)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bounded_continuous_and_seeded() {
        let mut prev = value3(3, Vec3::new(0.0, 0.25, 0.5));
        for i in 1..2000 {
            let p = Vec3::new(i as f32 * 0.01, 0.25, 0.5);
            let v = value3(3, p);
            assert!((-1.0..=1.0).contains(&v));
            assert!((v - prev).abs() < 0.1, "noise should be continuous");
            prev = v;
            let f = fbm3(3, p, 4, 2.0, 0.5);
            assert!((-1.0..=1.0).contains(&f));
        }
        assert_ne!(value3(1, Vec3::new(0.3, 0.3, 0.3)), value3(2, Vec3::new(0.3, 0.3, 0.3)));
    }
}
