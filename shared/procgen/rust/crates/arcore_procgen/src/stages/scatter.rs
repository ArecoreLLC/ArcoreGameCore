//! Stage 5 — scatter. Places instances on the extracted surface by triangle
//! area, gated by slope, height, zone weight and an optional clustering mask.
//! Each (layer, cell) pair has its own RNG stream, so results are independent of
//! thread count and of which other layers exist.

use super::cells::{CellGrid, CellId};
use super::field::DensityField;
use super::surface::Mesh;
use crate::common::math::{smoothstep, Quat, Vec3};
use crate::common::noise::fbm2;
use crate::common::rng::{hash_str, sub_seed, Rng};
use crate::recipe::{PropSpec, Recipe, ScatterLayer, Zone, ZoneMode};
use crate::runtime::collision::raycast;
use serde::Serialize;

/// Translation, rotation (glTF `[x, y, z, w]`) and uniform scale.
#[derive(Clone, Copy, Debug, PartialEq, Serialize)]
pub struct Instance {
    pub position: [f32; 3],
    pub rotation: [f32; 4],
    pub scale: f32,
}

#[derive(Clone, Debug, Serialize)]
pub struct CellInstances {
    pub cell: CellId,
    pub instances: Vec<Instance>,
}

#[derive(Clone, Debug, Serialize)]
pub struct LayerInstances {
    pub layer: String,
    pub mesh: String,
    pub external: bool,
    pub cells: Vec<CellInstances>,
}

impl LayerInstances {
    pub fn count(&self) -> usize {
        self.cells.iter().map(|c| c.instances.len()).sum()
    }
}

/// Zone weight in [0, 1] at an XZ position.
pub fn zone_weight(z: &Zone, x: f32, zz: f32) -> f32 {
    let d = ((x - z.center[0]).powi(2) + (zz - z.center[1]).powi(2)).sqrt();
    if z.falloff <= 0.0 {
        return if d <= z.radius { 1.0 } else { 0.0 };
    }
    smoothstep(z.radius + z.falloff, z.radius, d)
}

pub fn scatter_layer(
    recipe: &Recipe,
    layer: &ScatterLayer,
    chunks: &[(CellId, Mesh)],
    density_scale: f32,
) -> LayerInstances {
    let zone = layer.zone.as_ref().and_then(|id| recipe.zones.iter().find(|z| &z.id == id));
    let cluster_seed = sub_seed(recipe.seed, &format!("scatter.{}.cluster", layer.id));
    let (cos_min, cos_max) = (layer.min_slope_deg.to_radians().cos(), layer.max_slope_deg.to_radians().cos());
    // Layers reserved for dense bakes contribute nothing below their threshold.
    let density = if density_scale < layer.min_density_scale { 0.0 } else { layer.density * density_scale.max(0.0) };
    let mut cells = Vec::new();
    for (cell, mesh) in chunks {
        let mut rng = Rng::derive(recipe.seed, &[hash_str(&layer.id), cell[0] as u64, cell[1] as u64]);
        let mut out = Vec::new();
        for t in mesh.indices.chunks_exact(3) {
            let (a, b, c) = (mesh.position(t[0]), mesh.position(t[1]), mesh.position(t[2]));
            let cr = (b - a).cross(c - a);
            let area = 0.5 * cr.length();
            if area <= 0.0 {
                continue;
            }
            let n = cr.normalize_or(Vec3::Y);
            // Slope = angle between the face normal and +Y.
            if n.y > cos_min + 1e-6 || n.y < cos_max - 1e-6 {
                continue;
            }
            let expected = area * density;
            let mut k = expected.floor() as u32;
            if rng.next_f32() < expected - expected.floor() {
                k += 1;
            }
            for _ in 0..k {
                let (mut u, mut v) = (rng.next_f32(), rng.next_f32());
                if u + v > 1.0 {
                    (u, v) = (1.0 - u, 1.0 - v);
                }
                let p = a + (b - a) * u + (c - a) * v;
                // Draw every random value up front so gating never shifts the stream.
                let (keep, yaw, s) = (rng.next_f32(), rng.next_f32(), rng.next_f32());
                if let Some([lo, hi]) = layer.height_range {
                    if p.y < lo || p.y > hi {
                        continue;
                    }
                }
                let mut w = 1.0;
                if let Some(z) = zone {
                    let zw = zone_weight(z, p.x, p.z);
                    w *= match layer.zone_mode {
                        ZoneMode::Include => zw,
                        ZoneMode::Exclude => 1.0 - zw,
                    };
                }
                for z in recipe.zones.iter().filter(|z| z.clear) {
                    w *= 1.0 - zone_weight(z, p.x, p.z);
                }
                if let Some(cl) = &layer.clustering {
                    let m = fbm2(cluster_seed, p.x * cl.frequency, p.z * cl.frequency, 3, 2.0, 0.5);
                    w *= smoothstep(cl.threshold - cl.softness, cl.threshold + cl.softness, m);
                }
                if keep >= w {
                    continue;
                }
                let spin = Quat::from_axis_angle(Vec3::Y, yaw * std::f32::consts::TAU);
                let rotation = if layer.align_to_normal { Quat::from_y_to(n).mul(spin) } else { spin };
                let scale = layer.scale_range[0] + (layer.scale_range[1] - layer.scale_range[0]) * s;
                out.push(Instance {
                    position: (p + n * layer.normal_offset).to_array(),
                    rotation: rotation.0,
                    scale,
                });
            }
        }
        // Shuffle (Fisher-Yates) so instances are in random spatial order: the per-cell
        // cap then thins evenly instead of emptying part of the cell, and consumers
        // can draw any prefix of a cell as a lower level of detail.
        for i in (1..out.len()).rev() {
            let j = (rng.next_u64() % (i as u64 + 1)) as usize;
            out.swap(i, j);
        }
        if let Some(cap) = layer.max_per_cell {
            // A density scale above 1 (denser bakes for high-end tiers) lifts the cap with it.
            out.truncate((cap as f32 * density_scale.max(1.0)).round() as usize);
        }
        if !out.is_empty() {
            cells.push(CellInstances { cell: *cell, instances: out });
        }
    }
    LayerInstances { layer: layer.id.clone(), mesh: layer.mesh.clone(), external: layer.external, cells }
}

#[derive(Clone, Debug, Serialize)]
pub struct PlacedProp {
    pub id: String,
    pub mesh: String,
    pub external: bool,
    pub cell: CellId,
    pub instance: Instance,
    /// False when `snap_to_ground` found no surface below the requested position.
    pub grounded: bool,
}

pub fn place_props(props: &[PropSpec], field: &DensityField, cells: &CellGrid) -> Vec<PlacedProp> {
    let top = field.spec.max_corner().y;
    props
        .iter()
        .map(|p| {
            let mut pos = Vec3::from_array(p.position);
            let mut grounded = !p.snap_to_ground;
            if p.snap_to_ground {
                let from = Vec3::new(pos.x, pos.y.min(top), pos.z);
                if let Some(hit) = raycast(field, from, -Vec3::Y, from.y - field.spec.origin.y) {
                    pos = hit.position;
                    grounded = true;
                }
            }
            PlacedProp {
                id: p.id.clone(),
                mesh: p.mesh.clone(),
                external: p.external,
                cell: cells.cell_of(pos),
                instance: Instance {
                    position: pos.to_array(),
                    rotation: Quat::from_axis_angle(Vec3::Y, p.yaw_deg.to_radians())
                        .mul(Quat::from_axis_angle(Vec3::new(0.0, 0.0, 1.0), p.roll_deg.to_radians()))
                        .0,
                    scale: p.scale,
                },
                grounded,
            }
        })
        .collect()
}
