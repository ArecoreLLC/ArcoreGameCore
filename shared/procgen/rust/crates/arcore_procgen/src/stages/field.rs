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
    sdf_with_yaw(shape, yaw_sin_cos(shape), p)
}

/// `(sin, cos)` of the negated yaw for shapes that rotate about +Y.
fn yaw_sin_cos(shape: &Shape) -> (f32, f32) {
    match shape {
        Shape::Box { yaw_deg, .. } | Shape::Torus { yaw_deg, .. } => (-yaw_deg.to_radians()).sin_cos(),
        _ => (0.0, 1.0),
    }
}

#[inline]
fn sdf_with_yaw(shape: &Shape, (s, co): (f32, f32), p: Vec3) -> f32 {
    let yaw_local = |c: Vec3| {
        let q = p - c;
        Vec3::new(q.x * co + q.z * s, q.y, -q.x * s + q.z * co)
    };
    match shape {
        Shape::Sphere { center, radius } => (p - Vec3::from_array(*center)).length() - radius,
        Shape::Box { center, half_extents, .. } => {
            let q = yaw_local(Vec3::from_array(*center)).abs() - Vec3::from_array(*half_extents);
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
        Shape::Torus { center, major_radius, minor_radius, .. } => {
            let q = yaw_local(Vec3::from_array(*center));
            let ring = (q.x * q.x + q.y * q.y).sqrt() - major_radius;
            (ring * ring + q.z * q.z).sqrt() - minor_radius
        }
    }
}

/// Center and radius of a sphere that contains the whole primitive.
pub fn bounding_sphere(shape: &Shape) -> (Vec3, f32) {
    match shape {
        Shape::Sphere { center, radius } => (Vec3::from_array(*center), radius.abs()),
        Shape::Box { center, half_extents, .. } => {
            (Vec3::from_array(*center), Vec3::from_array(*half_extents).length())
        }
        Shape::Cylinder { center, radius, height } => {
            (Vec3::from_array(*center), (radius * radius + 0.25 * height * height).sqrt())
        }
        Shape::Capsule { a, b, radius } => {
            let (a, b) = (Vec3::from_array(*a), Vec3::from_array(*b));
            ((a + b) * 0.5, 0.5 * (b - a).length() + radius.abs())
        }
        Shape::Torus { center, major_radius, minor_radius, .. } => {
            (Vec3::from_array(*center), major_radius.abs() + minor_radius.abs())
        }
    }
}

/// A CSG primitive with everything that does not depend on the sample point
/// hoisted out of the per-sample loop.
struct PreparedPrimitive<'a> {
    prim: &'a Primitive,
    yaw: (f32, f32),
    center: Vec3,
    /// Bounding radius plus the smooth-blend radius: beyond this distance (offset
    /// by the current density) the primitive leaves the density unchanged.
    reach: f32,
}

impl<'a> PreparedPrimitive<'a> {
    fn new(prim: &'a Primitive) -> Self {
        let (center, radius) = bounding_sphere(&prim.shape);
        Self { prim, yaw: yaw_sin_cos(&prim.shape), center, reach: radius + prim.smooth.max(0.0) }
    }

    /// Combine the primitive into density `d` at `p`.
    ///
    /// The smooth min/max return `d` unchanged once the primitive's solid value
    /// trails it by the blend radius, and a primitive's SDF is at least the
    /// distance to its bounding sphere, so far-away primitives are skipped with
    /// one squared-distance test instead of a full SDF evaluation.
    #[inline]
    fn apply(&self, d: f32, p: Vec3) -> f32 {
        let reach = self.reach + if self.prim.op == CsgOp::Union { -d } else { d };
        if reach <= 0.0 {
            return d;
        }
        let q = p - self.center;
        if q.dot(q) >= reach * reach {
            return d;
        }
        let solid = -sdf_with_yaw(&self.prim.shape, self.yaw, p);
        match self.prim.op {
            CsgOp::Union => smax(d, solid, self.prim.smooth),
            CsgOp::Subtract => smin(d, -solid, self.prim.smooth),
        }
    }
}

/// Precomputed seeds and parameters for evaluating density at any point.
pub struct DensityFn<'a> {
    terrain: &'a TerrainSpec,
    primitives: Vec<PreparedPrimitive<'a>>,
    height_seed: u64,
    detail_seed: u64,
}

impl<'a> DensityFn<'a> {
    pub fn new(recipe: &'a Recipe) -> Self {
        Self {
            terrain: &recipe.terrain,
            primitives: recipe.terrain.primitives.iter().map(PreparedPrimitive::new).collect(),
            height_seed: sub_seed(recipe.seed, "terrain.height"),
            detail_seed: sub_seed(recipe.seed, "terrain.detail"),
        }
    }

    pub fn height(&self, x: f32, z: f32) -> f32 {
        let h = &self.terrain.height;
        self.terrain.base_height
            + h.amplitude * fbm2(self.height_seed, x * h.frequency, z * h.frequency, h.octaves, h.lacunarity, h.gain)
    }

    /// Density at `p` before detail noise: column height plus CSG primitives.
    #[inline]
    fn eval_base(&self, p: Vec3, height: f32) -> f32 {
        let mut d = height - p.y;
        for prim in &self.primitives {
            d = prim.apply(d, p);
        }
        d
    }

    #[inline]
    fn detail(&self, p: Vec3) -> f32 {
        match &self.terrain.detail {
            Some(n) => n.amplitude * fbm3(self.detail_seed, p * n.frequency, n.octaves, n.lacunarity, n.gain),
            None => 0.0,
        }
    }

    /// Largest magnitude the detail noise can add (fBm is normalized to `[-1, 1]`).
    pub fn detail_bound(&self) -> f32 {
        self.terrain.detail.as_ref().map_or(0.0, |n| n.amplitude.abs())
    }

    /// Density at `p` given a precomputed column height.
    pub fn eval_with_height(&self, p: Vec3, height: f32) -> f32 {
        self.eval_base(p, height) + self.detail(p)
    }

    /// Grid variant of [`eval_with_height`](Self::eval_with_height): detail noise is
    /// only evaluated within `band` meters of the surface. Outside the band the
    /// noise cannot flip the sign (`band >= detail_bound()`), so solid/open
    /// classification is exact everywhere and values are exact inside the band;
    /// beyond it they are off by at most `detail_bound()`.
    #[inline]
    pub fn eval_banded(&self, p: Vec3, height: f32, band: f32) -> f32 {
        let d = self.eval_base(p, height);
        if d.abs() <= band {
            d + self.detail(p)
        } else {
            d
        }
    }

    pub fn eval(&self, p: Vec3) -> f32 {
        self.eval_with_height(p, self.height(p.x, p.z))
    }
}

/// Voxels of exact density kept on each side of the surface (beyond the detail
/// noise bound). Covers every sample read by surface extraction, normals, prop
/// snapping and the near occlusion probes; the farthest occlusion probe may read
/// a noise-free value, which shifts it by a few percent at most.
pub const DETAIL_BAND_VOXELS: f32 = 4.0;

/// Evaluate the whole grid, splitting z-slabs across `threads` workers.
/// Output is identical for any thread count.
///
/// Detail noise (the dominant cost) is only evaluated in a narrow band around
/// the surface; see [`DensityFn::eval_banded`].
pub fn build_field(recipe: &Recipe, threads: usize) -> DensityField {
    let spec = GridSpec::from_recipe(recipe);
    let f = DensityFn::new(recipe);
    let [nx, ny, nz] = spec.dims;
    let band = f.detail_bound() + DETAIL_BAND_VOXELS * spec.voxel;

    let mut heights = vec![0.0f32; nx * nz];
    let mut data = vec![0.0f32; spec.len()];
    let slab = nx * ny;
    let threads = threads.clamp(1, nz.max(1));
    let slabs_per_worker = nz.div_ceil(threads);
    std::thread::scope(|scope| {
        // Column heights (x fastest, then z).
        for (w, rows) in heights.chunks_mut(nx * slabs_per_worker).enumerate() {
            let (f, spec) = (&f, &spec);
            scope.spawn(move || {
                for (dz, row) in rows.chunks_mut(nx).enumerate() {
                    for (x, h) in row.iter_mut().enumerate() {
                        let p = spec.position(x, 0, w * slabs_per_worker + dz);
                        *h = f.height(p.x, p.z);
                    }
                }
            });
        }
    });
    std::thread::scope(|scope| {
        for (w, chunk) in data.chunks_mut(slab * slabs_per_worker).enumerate() {
            let (f, heights, spec) = (&f, &heights, &spec);
            scope.spawn(move || {
                let z0 = w * slabs_per_worker;
                for (dz, plane) in chunk.chunks_mut(slab).enumerate() {
                    let z = z0 + dz;
                    let row_heights = &heights[nx * z..nx * (z + 1)];
                    for (y, row) in plane.chunks_mut(nx).enumerate() {
                        for (x, d) in row.iter_mut().enumerate() {
                            *d = f.eval_banded(spec.position(x, y, z), row_heights[x], band);
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
    fn culled_primitives_match_direct_evaluation() {
        use crate::common::rng::Rng;
        let shapes = [
            Shape::Sphere { center: [3.0, -2.0, 1.0], radius: 2.5 },
            Shape::Box { center: [-4.0, 0.0, 2.0], half_extents: [3.0, 1.0, 0.5], yaw_deg: 37.0 },
            Shape::Cylinder { center: [0.0, 1.0, -5.0], radius: 1.5, height: 6.0 },
            Shape::Capsule { a: [-6.0, 0.0, -6.0], b: [5.0, 2.0, 4.0], radius: 1.2 },
            Shape::Torus { center: [2.0, 0.0, 6.0], major_radius: 4.0, minor_radius: 1.0, yaw_deg: 110.0 },
        ];
        let mut rng = Rng::new(17);
        for shape in &shapes {
            let (c, r) = bounding_sphere(shape);
            for op in [CsgOp::Union, CsgOp::Subtract] {
                for smooth in [0.0, 2.5] {
                    let prim = Primitive { id: None, shape: shape.clone(), op, smooth };
                    let prepared = PreparedPrimitive::new(&prim);
                    for _ in 0..400 {
                        let p = Vec3::new(rng.range(-14.0, 14.0), rng.range(-14.0, 14.0), rng.range(-14.0, 14.0));
                        let sdf = primitive_sdf(shape, p);
                        assert!(sdf >= (p - c).length() - r - 1e-4, "bounding sphere must contain {shape:?}");
                        let d = rng.range(-12.0, 12.0);
                        let direct = match op {
                            CsgOp::Union => smax(d, -sdf, smooth),
                            CsgOp::Subtract => smin(d, sdf, smooth),
                        };
                        let culled = prepared.apply(d, p);
                        assert!((culled - direct).abs() < 1e-4, "{shape:?} {op:?} k={smooth}: {culled} vs {direct}");
                    }
                }
            }
        }
    }

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
