//! Minimal vector/quaternion math. Y-up, right-handed, meters (glTF convention).

use std::ops::{Add, AddAssign, Mul, Neg, Sub};

#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Vec3 {
    pub x: f32,
    pub y: f32,
    pub z: f32,
}

impl Vec3 {
    pub const ZERO: Vec3 = Vec3 { x: 0.0, y: 0.0, z: 0.0 };
    pub const Y: Vec3 = Vec3 { x: 0.0, y: 1.0, z: 0.0 };

    pub const fn new(x: f32, y: f32, z: f32) -> Self {
        Self { x, y, z }
    }
    pub fn from_array(a: [f32; 3]) -> Self {
        Self::new(a[0], a[1], a[2])
    }
    pub fn to_array(self) -> [f32; 3] {
        [self.x, self.y, self.z]
    }
    pub fn dot(self, o: Vec3) -> f32 {
        self.x * o.x + self.y * o.y + self.z * o.z
    }
    pub fn cross(self, o: Vec3) -> Vec3 {
        Vec3::new(
            self.y * o.z - self.z * o.y,
            self.z * o.x - self.x * o.z,
            self.x * o.y - self.y * o.x,
        )
    }
    pub fn length(self) -> f32 {
        self.dot(self).sqrt()
    }
    /// Unit vector, or `fallback` when the length is (near) zero or not finite.
    pub fn normalize_or(self, fallback: Vec3) -> Vec3 {
        let l = self.length();
        if l > 1e-12 && l.is_finite() {
            self * (1.0 / l)
        } else {
            fallback
        }
    }
    pub fn min(self, o: Vec3) -> Vec3 {
        Vec3::new(self.x.min(o.x), self.y.min(o.y), self.z.min(o.z))
    }
    pub fn max(self, o: Vec3) -> Vec3 {
        Vec3::new(self.x.max(o.x), self.y.max(o.y), self.z.max(o.z))
    }
    pub fn abs(self) -> Vec3 {
        Vec3::new(self.x.abs(), self.y.abs(), self.z.abs())
    }
    pub fn is_finite(self) -> bool {
        self.x.is_finite() && self.y.is_finite() && self.z.is_finite()
    }
}

impl Add for Vec3 {
    type Output = Vec3;
    fn add(self, o: Vec3) -> Vec3 {
        Vec3::new(self.x + o.x, self.y + o.y, self.z + o.z)
    }
}
impl AddAssign for Vec3 {
    fn add_assign(&mut self, o: Vec3) {
        *self = *self + o;
    }
}
impl Sub for Vec3 {
    type Output = Vec3;
    fn sub(self, o: Vec3) -> Vec3 {
        Vec3::new(self.x - o.x, self.y - o.y, self.z - o.z)
    }
}
impl Mul<f32> for Vec3 {
    type Output = Vec3;
    fn mul(self, s: f32) -> Vec3 {
        Vec3::new(self.x * s, self.y * s, self.z * s)
    }
}
impl Neg for Vec3 {
    type Output = Vec3;
    fn neg(self) -> Vec3 {
        Vec3::new(-self.x, -self.y, -self.z)
    }
}

/// Unit quaternion stored as `[x, y, z, w]` (glTF order).
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Quat(pub [f32; 4]);

impl Quat {
    pub const IDENTITY: Quat = Quat([0.0, 0.0, 0.0, 1.0]);

    pub fn from_axis_angle(axis: Vec3, radians: f32) -> Quat {
        let a = axis.normalize_or(Vec3::Y);
        let (s, c) = (radians * 0.5).sin_cos();
        Quat([a.x * s, a.y * s, a.z * s, c])
    }

    /// Hamilton product: applying the result equals applying `o` first, then `self`.
    pub fn mul(self, o: Quat) -> Quat {
        let [ax, ay, az, aw] = self.0;
        let [bx, by, bz, bw] = o.0;
        Quat([
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz,
        ])
    }

    /// Shortest rotation taking +Y onto `n`.
    pub fn from_y_to(n: Vec3) -> Quat {
        let n = n.normalize_or(Vec3::Y);
        let d = n.y; // dot(Y, n)
        if d < -0.999_999 {
            return Quat([1.0, 0.0, 0.0, 0.0]); // 180 degrees about X
        }
        // axis = Y x n = (n.z, 0, -n.x)
        let q = [n.z, 0.0, -n.x, 1.0 + d];
        let l = (q[0] * q[0] + q[2] * q[2] + q[3] * q[3]).sqrt();
        Quat([q[0] / l, 0.0, q[2] / l, q[3] / l])
    }

    pub fn rotate(self, v: Vec3) -> Vec3 {
        let [x, y, z, w] = self.0;
        let u = Vec3::new(x, y, z);
        let t = u.cross(v) * 2.0;
        v + t * w + u.cross(t)
    }
}

pub fn clamp(x: f32, lo: f32, hi: f32) -> f32 {
    x.max(lo).min(hi)
}

pub fn lerp(a: f32, b: f32, t: f32) -> f32 {
    a + (b - a) * t
}

/// Hermite smoothstep; `edge0 > edge1` yields a falling ramp.
pub fn smoothstep(edge0: f32, edge1: f32, x: f32) -> f32 {
    if edge0 == edge1 {
        return if x < edge0 { 0.0 } else { 1.0 };
    }
    let t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0);
    t * t * (3.0 - 2.0 * t)
}

/// Polynomial smooth minimum with blend radius `k` (k <= 0 is a hard min).
pub fn smin(a: f32, b: f32, k: f32) -> f32 {
    if k <= 0.0 {
        return a.min(b);
    }
    let h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    lerp(b, a, h) - k * h * (1.0 - h)
}

pub fn smax(a: f32, b: f32, k: f32) -> f32 {
    -smin(-a, -b, k)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn from_y_to_maps_up_onto_target() {
        for n in [
            Vec3::new(0.0, 1.0, 0.0),
            Vec3::new(1.0, 0.0, 0.0),
            Vec3::new(0.3, -0.2, 0.9),
            Vec3::new(0.0, -1.0, 0.0),
        ] {
            let r = Quat::from_y_to(n).rotate(Vec3::Y);
            let n = n.normalize_or(Vec3::Y);
            assert!((r - n).length() < 1e-5, "{r:?} vs {n:?}");
        }
    }

    #[test]
    fn smooth_ops_bound_hard_ops() {
        assert!(smin(1.0, 1.2, 0.5) <= 1.0);
        assert!(smax(1.0, 1.2, 0.5) >= 1.2);
        assert_eq!(smin(1.0, 3.0, 0.0), 1.0);
    }
}
