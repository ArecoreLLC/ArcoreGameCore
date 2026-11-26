//! Parametric sailing-ship hull for the mesh library (stage 4): a lofted hull,
//! a plank deck, masts with yards and a bowsprit, all from a handful of numbers.
//! `damage` turns it into a wreck by knocking seeded holes into the planking and
//! snapping the masts.
//!
//! Layout: keel on y = 0, bow toward +Z, centered on the origin in X and Z.
//! Surfaces are single-sided shells (render double-sided). Vertex colors hold a
//! grayscale part shade (deck brightest, hull darker) for the consumer's material.

use super::parametric::push_tube;
use super::surface::Mesh;
use crate::common::math::{smoothstep, Vec3};
use crate::common::noise::fbm3;
use crate::common::rng::Rng;

const STATIONS: usize = 16;
/// Segments across one hull cross-section (gunwale to gunwale); even, so the keel is a vertex row.
const SECTION: usize = 12;
const DECK_STRIPS: usize = 4;
/// Deck height as a fraction of the way from keel (0) to gunwale (1) along the section curve.
const DECK_LEVEL: f32 = 0.8;

const SHADE_HULL: f32 = 0.62;
const SHADE_DECK: f32 = 1.0;
const SHADE_SPAR: f32 = 0.8;

pub struct ShipParams {
    pub length: f32,
    pub beam: f32,
    pub depth: f32,
    pub masts: u32,
    pub mast_height: f32,
    /// 0 = seaworthy, 1 = heavily holed with snapped masts.
    pub damage: f32,
}

/// Hull outline at station `t` (0 = stern, 1 = bow).
struct Station {
    z: f32,
    half_beam: f32,
    keel: f32,
    gunwale: f32,
}

impl Station {
    fn at(p: &ShipParams, t: f32) -> Self {
        // Full amidships, slightly pinched stern, closing to a point at the bow.
        let width = if t < 0.45 {
            0.72 + 0.28 * smoothstep(0.0, 0.45, t)
        } else {
            1.0 - ((t - 0.45) / 0.55).powf(2.2)
        };
        let fore = ((t - 0.7) / 0.3).max(0.0);
        Self {
            z: (t - 0.5) * p.length,
            half_beam: 0.5 * p.beam * width.max(0.0),
            // The keel sweeps up toward the bow; the gunwale rises at both ends (sheer).
            keel: p.depth * 0.35 * fore * fore,
            gunwale: p.depth * (1.0 + 0.22 * (2.0 * t - 1.0).powi(2)),
        }
    }

    /// Point on the cross-section; `u` runs from -1 (port gunwale) through 0 (keel) to 1.
    fn point(&self, u: f32) -> Vec3 {
        let a = u.abs();
        Vec3::new(
            self.half_beam * u.signum() * a.powf(0.6),
            self.keel + (self.gunwale - self.keel) * a.powf(1.8),
            self.z,
        )
    }
}

pub fn ship(p: &ShipParams, seed: u64) -> Mesh {
    let mut m = Mesh::default();
    let mut rng = Rng::new(seed);
    let damage = p.damage.clamp(0.0, 1.0);
    // Planks whose noise value exceeds this are missing.
    let hole_threshold = 1.0 - damage * 0.9;
    let holed = |center: Vec3, salt: u64| damage > 0.0 && fbm3(seed ^ salt, center * 0.3, 3, 2.0, 0.5) > hole_threshold;
    let stations: Vec<Station> =
        (0..=STATIONS).map(|i| Station::at(p, i as f32 / STATIONS as f32)).collect();
    let inside = |z: f32| Vec3::new(0.0, p.depth * 0.6, z);

    // Hull shell.
    for st in &stations {
        for j in 0..=SECTION {
            m.positions.push(st.point(j as f32 / SECTION as f32 * 2.0 - 1.0).to_array());
        }
    }
    let row = (SECTION + 1) as u32;
    for i in 0..STATIONS as u32 {
        for j in 0..SECTION as u32 {
            let q = [i * row + j, i * row + j + 1, (i + 1) * row + j + 1, (i + 1) * row + j];
            let center = quad_center(&m, q);
            // The two plank rows along the keel always survive, so a wreck keeps its spine.
            let near_keel = j + 1 == SECTION as u32 / 2 || j == SECTION as u32 / 2;
            if near_keel || !holed(center, 0x48) {
                push_quad(&mut m, q, center - inside(center.z));
            }
        }
    }
    // Transom closing the stern.
    let hub = m.positions.len() as u32;
    m.positions.push(Vec3::new(0.0, stations[0].gunwale * 0.55, stations[0].z).to_array());
    for j in 0..SECTION as u32 {
        push_tri(&mut m, [hub, j, j + 1], Vec3::new(0.0, 0.0, -1.0));
    }
    fill_shade(&mut m, SHADE_HULL);

    // Deck.
    let deck0 = m.positions.len() as u32;
    for st in &stations {
        let (port, starboard) = (st.point(-DECK_LEVEL), st.point(DECK_LEVEL));
        for k in 0..=DECK_STRIPS {
            let f = k as f32 / DECK_STRIPS as f32;
            m.positions.push((port + (starboard - port) * f).to_array());
        }
    }
    let row = (DECK_STRIPS + 1) as u32;
    for i in 0..STATIONS as u32 {
        for k in 0..DECK_STRIPS as u32 {
            let q = [deck0 + i * row + k, deck0 + (i + 1) * row + k, deck0 + (i + 1) * row + k + 1, deck0 + i * row + k + 1];
            if !holed(quad_center(&m, q), 0xD3) {
                push_quad(&mut m, q, Vec3::Y);
            }
        }
    }
    fill_shade(&mut m, SHADE_DECK);

    // Masts with a yard each, then the bowsprit.
    let spar = p.beam * 0.035;
    for i in 0..p.masts.min(4) {
        let t = 0.26 + 0.5 * (i as f32 + 0.5) / p.masts.min(4) as f32;
        let st = Station::at(p, t);
        let foot = Vec3::new(0.0, st.point(DECK_LEVEL).y, st.z);
        // A damaged ship keeps anything from a stump to a full, leaning mast.
        let standing = if damage > 0.0 { rng.range(1.0 - 0.75 * damage, 1.0) } else { 1.0 };
        let lean = damage * 0.3;
        let dir = Vec3::new(rng.range(-lean, lean), 1.0, rng.range(-lean, lean)).normalize_or(Vec3::Y);
        let height = p.mast_height * standing;
        push_tube(&mut m, foot, dir, height, spar, spar * 0.6, 6, true);
        if standing > 0.7 {
            let yard = st.half_beam * 1.1;
            let at = foot + dir * (height * 0.72);
            push_tube(&mut m, at - Vec3::new(yard, 0.0, 0.0), Vec3::new(1.0, 0.0, 0.0), yard * 2.0, spar * 0.5, spar * 0.5, 5, true);
        }
    }
    let bow = &stations[STATIONS];
    push_tube(
        &mut m,
        Vec3::new(0.0, bow.gunwale * 0.95, bow.z - p.length * 0.04),
        Vec3::new(0.0, 0.35, 1.0).normalize_or(Vec3::Y),
        p.length * 0.2,
        spar * 0.8,
        spar * 0.4,
        5,
        true,
    );
    fill_shade(&mut m, SHADE_SPAR);

    m.recompute_normals();
    m
}

fn quad_center(m: &Mesh, q: [u32; 4]) -> Vec3 {
    (m.position(q[0]) + m.position(q[1]) + m.position(q[2]) + m.position(q[3])) * 0.25
}

/// Two triangles for quad `q`, wound so their normals face along `outward`.
fn push_quad(m: &mut Mesh, q: [u32; 4], outward: Vec3) {
    push_tri(m, [q[0], q[1], q[2]], outward);
    push_tri(m, [q[0], q[2], q[3]], outward);
}

fn push_tri(m: &mut Mesh, t: [u32; 3], outward: Vec3) {
    let (a, b, c) = (m.position(t[0]), m.position(t[1]), m.position(t[2]));
    if (b - a).cross(c - a).dot(outward) >= 0.0 {
        m.indices.extend_from_slice(&t);
    } else {
        m.indices.extend_from_slice(&[t[0], t[2], t[1]]);
    }
}

/// Give every vertex added since the last call the same part shade.
fn fill_shade(m: &mut Mesh, shade: f32) {
    m.colors.resize(m.positions.len(), [shade, shade, shade, 1.0]);
}

#[cfg(test)]
mod tests {
    use super::*;

    fn params(damage: f32) -> ShipParams {
        ShipParams { length: 24.0, beam: 7.0, depth: 4.5, masts: 2, mast_height: 11.0, damage }
    }

    #[test]
    fn ship_has_expected_proportions_and_part_shades() {
        let s = ship(&params(0.0), 1);
        let (lo, hi) = s.bounds().unwrap();
        assert!(lo.y.abs() < 1e-4, "keel sits on y = 0, got {}", lo.y);
        assert!((hi.x - lo.x - 7.0).abs() < 0.8, "beam: {}", hi.x - lo.x);
        assert!(hi.z - lo.z >= 24.0 && hi.z - lo.z < 31.0, "length incl. bowsprit: {}", hi.z - lo.z);
        assert!(hi.y > 4.5 + 9.0, "masts rise above the deck: {}", hi.y);
        assert!(s.has_colors());
        assert!(s.normals.iter().all(|n| (Vec3::from_array(*n).length() - 1.0).abs() < 1e-3));
        // Hull planking faces away from the centerline.
        let hull_tris = STATIONS * SECTION * 2;
        for t in s.indices.chunks_exact(3).take(hull_tris) {
            let (a, b, c) = (s.position(t[0]), s.position(t[1]), s.position(t[2]));
            let center = (a + b + c) * (1.0 / 3.0);
            let n = (b - a).cross(c - a);
            assert!(n.dot(center - Vec3::new(0.0, 4.5 * 0.6, center.z)) >= -1e-5, "hull triangle faces inward");
        }
    }

    #[test]
    fn damage_is_seeded_and_removes_planking() {
        let intact = ship(&params(0.0), 3);
        let wreck = ship(&params(0.7), 3);
        assert_eq!(wreck, ship(&params(0.7), 3), "same seed, same wreck");
        assert_ne!(wreck, ship(&params(0.7), 4), "seed changes the wreck");
        assert!(wreck.triangle_count() < intact.triangle_count(), "holes remove triangles");
        assert!(wreck.triangle_count() > intact.triangle_count() / 2, "most of the ship survives");
    }
}
