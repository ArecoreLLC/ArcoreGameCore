//! Stage 1 — density field.
//!
//! Convention: density > 0 is solid, < 0 is open (water/air), 0 is the surface.
//! Values approximate signed distance in meters (exact for lone primitives; the
//! height field and noise make it a bounded approximation).

use crate::common::math::{smax, smin, Vec3};
use crate::common::noise::{fbm2, fbm3};
use crate::common::rng::sub_seed;
use crate::recipe::{CsgOp, Primitive, Recipe, Shape, TerrainSpec};

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct GridSpec {
    pub origin: Vec3,
    pub voxel: f32,
    /// Sample counts along x, y, z.
    pub dims: [usize; 3],
}

impl GridSpec {
    pub fn from_recipe(r: &Recipe) -> Self {
        Self {
            origin: Vec3::from_array(r.bounds.origin),
            voxel: r.bounds.voxel,
            dims: r.bounds.sample_dims(),
        }
    }
    #[inline]
    pub fn index(&self, x: usize, y: usize, z: usize) -> usize {
        x + self.dims[0] * (y + self.dims[1] * z)
    }
    #[inline]
    pub fn position(&self, x: usize, y: usize, z: usize) -> Vec3 {
        self.origin + Vec3::new(x as f32, y as f32, z as f32) * self.voxel
    }
    pub fn len(&self) -> usize {
        self.dims[0] * self.dims[1] * self.dims[2]
    }
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }
    pub fn max_corner(&self) -> Vec3 {
        self.position(self.dims[0] - 1, self.dims[1] - 1, self.dims[2] - 1)
    }
}

/// Sampled density grid. Index order: x fastest, then y, then z.
#[derive(Clone, Debug)]
pub struct DensityField {
    pub spec: GridSpec,
    pub data: Vec<f32>,
}

impl DensityField {
    #[inline]
    pub fn at(&self, x: usize, y: usize, z: usize) -> f32 {
        self.data[self.spec.index(x, y, z)]
    }

    /// Trilinear sample; positions outside the grid clamp to the boundary.
    pub fn sample(&self, p: Vec3) -> f32 {
        let s = &self.spec;
        let g = (p - s.origin) * (1.0 / s.voxel);
        let axis = |v: f32, n: usize| -> (usize, f32) {
            let max = (n - 1) as f32;
            let v = v.max(0.0).min(max);
            let i = (v.floor() as usize).min(n.saturating_sub(2));
            (i, v - i as f32)
        };
        let (x0, fx) = axis(g.x, s.dims[0]);
        let (y0, fy) = axis(g.y, s.dims[1]);
        let (z0, fz) = axis(g.z, s.dims[2]);
        let (x1, y1, z1) = (
            (x0 + 1).min(s.dims[0] - 1),
            (y0 + 1).min(s.dims[1] - 1),
            (z0 + 1).min(s.dims[2] - 1),
        );
        let l = |a: f32, b: f32, t: f32| a + (b - a) * t;
        let c00 = l(self.at(x0, y0, z0), self.at(x1, y0, z0), fx);
        let c10 = l(self.at(x0, y1, z0), self.at(x1, y1, z0), fx);
        let c01 = l(self.at(x0, y0, z1), self.at(x1, y0, z1), fx);
        let c11 = l(self.at(x0, y1, z1), self.at(x1, y1, z1), fx);
        l(l(c00, c10, fy), l(c01, c11, fy), fz)
    }

    /// Central-difference gradient (points into solid material).
    pub fn gradient(&self, p: Vec3) -> Vec3 {
        let h = self.spec.voxel * 0.5;
        let d = |o: Vec3| self.sample(p + o) - self.sample(p - o);
        Vec3::new(
            d(Vec3::new(h, 0.0, 0.0)),
            d(Vec3::new(0.0, h, 0.0)),
            d(Vec3::new(0.0, 0.0, h)),
        ) * (0.5 / h)
    }

    /// Outward surface normal (points from solid into open space).
    pub fn normal(&self, p: Vec3) -> Vec3 {
        (-self.gradient(p)).normalize_or(Vec3::Y)
    }

    pub fn solid_fraction(&self) -> f32 {
        let n = self.data.iter().filter(|d| **d > 0.0).count();
        n as f32 / self.data.len().max(1) as f32
    }
}

/// Signed distance of a primitive (negative inside).
pub fn primitive_sdf(shape: &Shape, p: Vec3) -> f32 {
    fn yaw_local(p: Vec3, c: Vec3, yaw_deg: f32) -> Vec3 {
        let q = p - c;
        let (s, co) = (-yaw_deg.to_radians()).sin_cos();
        Vec3::new(q.x * co + q.z * s, q.y, -q.x * s + q.z * co)
    }
    match shape {
        Shape::Sphere { center, radius } => (p - Vec3::from_array(*center)).length() - radius,
        Shape::Box { center, half_extents, yaw_deg } => {
            let q = yaw_local(p, Vec3::from_array(*center), *yaw_deg).abs() - Vec3::from_array(*half_extents);
            q.max(Vec3::ZERO).length() + q.x.max(q.y.max(q.z)).min(0.0)
        }
        Shape::Cylinder { center, radius, height } => {
            let q = p - Vec3::from_array(*center);
            let dx = (q.x * q.x + q.z * q.z).sqrt() - radius;
            let dy = q.y.abs() - height * 0.5;
            dx.max(dy).min(0.0) + (dx.max(0.0).powi(2) + dy.max(0.0).powi(2)).sqrt()
        }
        Shape::Capsule { a, b, radius } => {
            let (a, b) = (Vec3::from_array(*a), Vec3::from_array(*b));
            let (pa, ba) = (p - a, b - a);
            let denom = ba.dot(ba);
            let h = if denom > 0.0 { (pa.dot(ba) / denom).clamp(0.0, 1.0) } else { 0.0 };
            (pa - ba * h).length() - radius
        }
        Shape::Torus { center, major_radius, minor_radius, yaw_deg } => {
            let q = yaw_local(p, Vec3::from_array(*center), *yaw_deg);
            let ring = (q.x * q.x + q.y * q.y).sqrt() - major_radius;
            (ring * ring + q.z * q.z).sqrt() - minor_radius
        }
    }
}

/// Precomputed seeds and parameters for evaluating density at any point.
pub struct DensityFn<'a> {
    terrain: &'a TerrainSpec,
    height_seed: u64,
    detail_seed: u64,
}

impl<'a> DensityFn<'a> {
    pub fn new(recipe: &'a Recipe) -> Self {
        Self {
            terrain: &recipe.terrain,
            height_seed: sub_seed(recipe.seed, "terrain.height"),
            detail_seed: sub_seed(recipe.seed, "terrain.detail"),
        }
    }

    pub fn height(&self, x: f32, z: f32) -> f32 {
        let h = &self.terrain.height;
        self.terrain.base_height
            + h.amplitude * fbm2(self.height_seed, x * h.frequency, z * h.frequency, h.octaves, h.lacunarity, h.gain)
    }

    /// Density at `p` given a precomputed column height.
    pub fn eval_with_height(&self, p: Vec3, height: f32) -> f32 {
        let mut d = height - p.y;
        for prim in &self.terrain.primitives {
            d = apply(d, prim, p);
        }
        if let Some(n) = &self.terrain.detail {
            d += n.amplitude * fbm3(self.detail_seed, p * n.frequency, n.octaves, n.lacunarity, n.gain);
        }
        d
    }

    pub fn eval(&self, p: Vec3) -> f32 {
        self.eval_with_height(p, self.height(p.x, p.z))
    }
}

fn apply(d: f32, prim: &Primitive, p: Vec3) -> f32 {
    let solid = -primitive_sdf(&prim.shape, p);
    match prim.op {
        CsgOp::Union => smax(d, solid, prim.smooth),
        CsgOp::Subtract => smin(d, -solid, prim.smooth),
    }
}

/// Evaluate the whole grid, splitting z-slabs across `threads` workers.
/// Output is identical for any thread count.
pub fn build_field(recipe: &Recipe, threads: usize) -> DensityField {
    let spec = GridSpec::from_recipe(recipe);
    let f = DensityFn::new(recipe);
    let [nx, ny, nz] = spec.dims;

    // Column heights (x fastest, then z).
    let mut heights = vec![0.0f32; nx * nz];
    for z in 0..nz {
        for x in 0..nx {
            let p = spec.position(x, 0, z);
            heights[x + nx * z] = f.height(p.x, p.z);
        }
    }

    let mut data = vec![0.0f32; spec.len()];
    let slab = nx * ny;
    let threads = threads.clamp(1, nz.max(1));
    let slabs_per_worker = nz.div_ceil(threads);
    std::thread::scope(|scope| {
        for (w, chunk) in data.chunks_mut(slab * slabs_per_worker).enumerate() {
            let (f, heights, spec) = (&f, &heights, &spec);
            scope.spawn(move || {
                let z0 = w * slabs_per_worker;
                for (dz, plane) in chunk.chunks_mut(slab).enumerate() {
                    let z = z0 + dz;
                    for y in 0..ny {
                        for x in 0..nx {
                            let p = spec.position(x, y, z);
                            plane[x + nx * y] = f.eval_with_height(p, heights[x + nx * z]);
                        }
                    }
                }
            });
        }
    });
    DensityField { spec, data }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn primitive_signs() {
        let s = Shape::Sphere { center: [0.0; 3], radius: 2.0 };
        assert!((primitive_sdf(&s, Vec3::new(3.0, 0.0, 0.0)) - 1.0).abs() < 1e-6);
        let t = Shape::Torus { center: [0.0; 3], major_radius: 5.0, minor_radius: 1.0, yaw_deg: 0.0 };
        assert!(primitive_sdf(&t, Vec3::new(0.0, 5.0, 0.0)) < 0.0, "top of upright ring is solid");
        assert!(primitive_sdf(&t, Vec3::new(0.0, 0.0, 0.0)) > 0.0, "ring hole is open");
        let b = Shape::Box { center: [0.0; 3], half_extents: [4.0, 1.0, 1.0], yaw_deg: 90.0 };
        assert!(primitive_sdf(&b, Vec3::new(0.0, 0.0, 3.5)) < 0.0, "yaw rotates the long axis onto Z");
        let c = Shape::Cylinder { center: [0.0; 3], radius: 1.0, height: 4.0 };
        assert!((primitive_sdf(&c, Vec3::new(0.0, 3.0, 0.0)) - 1.0).abs() < 1e-6);
        let k = Shape::Capsule { a: [0.0; 3], b: [10.0, 0.0, 0.0], radius: 1.0 };
        assert!((primitive_sdf(&k, Vec3::new(5.0, 3.0, 0.0)) - 2.0).abs() < 1e-6);
    }
}
