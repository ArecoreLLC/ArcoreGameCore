//! `preview.json`: a coarse height grid of a baked world, small enough for a
//! neighboring level to load and draw as a distant stand-in (one low-poly mesh)
//! so transitions between generated worlds have something to look at.
//!
//! For each column of a `resolution` x `resolution` grid over the XZ bounds:
//! - `top`: height of the highest solid surface, or null if the column is open
//! - `bottom`: height of the lowest solid surface's underside, or null when the
//!   solid reaches the floor of the bounds (ordinary ground) or the column is open
//!
//! Rows run along +Z, values within a row along +X. Heights are meters.

use crate::stages::field::DensityField;
use serde_json::{json, Value};

pub const PREVIEW_SCHEMA: &str = "arcore.procgen.preview.v1";
pub const PREVIEW_RESOLUTION: usize = 96;

pub fn build_preview(field: &DensityField, water_level: Option<f32>, resolution: usize) -> Value {
    let s = field.spec;
    let [nx, ny, nz] = s.dims;
    let n = resolution.max(2);
    let round = |v: f32| (v * 100.0).round() / 100.0;
    let height = |y: usize, t: f32| s.origin.y + (y as f32 + t) * s.voxel;
    let mut top: Vec<Option<f32>> = Vec::with_capacity(n * n);
    let mut bottom: Vec<Option<f32>> = Vec::with_capacity(n * n);
    for gz in 0..n {
        let z = (gz * (nz - 1)) / (n - 1);
        for gx in 0..n {
            let x = (gx * (nx - 1)) / (n - 1);
            // Highest solid sample, interpolated toward the open sample above it.
            let mut t_val = None;
            for y in (0..ny).rev() {
                let d0 = field.at(x, y, z);
                if d0 > 0.0 {
                    t_val = Some(if y + 1 < ny {
                        let d1 = field.at(x, y + 1, z);
                        height(y, d0 / (d0 - d1).max(1e-6))
                    } else {
                        height(y, 0.0)
                    });
                    break;
                }
            }
            // Lowest solid sample, unless the column is solid at the floor.
            let mut b_val = None;
            if t_val.is_some() && field.at(x, 0, z) <= 0.0 {
                for y in 1..ny {
                    let d1 = field.at(x, y, z);
                    if d1 > 0.0 {
                        let d0 = field.at(x, y - 1, z);
                        b_val = Some(height(y - 1, d0 / (d0 - d1).min(-1e-6)));
                        break;
                    }
                }
            }
            top.push(t_val.map(round));
            bottom.push(b_val.map(round));
        }
    }
    let max = s.max_corner();
    json!({
        "schema": PREVIEW_SCHEMA,
        "resolution": n,
        "origin": [s.origin.x, s.origin.z],
        "size": [max.x - s.origin.x, max.z - s.origin.z],
        "water_level": water_level,
        "top": top,
        "bottom": bottom,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::recipe::Recipe;
    use crate::stages::field::build_field;

    fn recipe(primitives: serde_json::Value, base: f32) -> Recipe {
        Recipe::from_json(
            &json!({
                "schema": "arcore.procgen.world-recipe.v1", "name": "p", "seed": 1,
                "bounds": {"origin": [-8.0, 0.0, -8.0], "size": [16.0, 16.0, 16.0], "voxel": 1.0},
                "cells": {"size": 8.0},
                "terrain": {"base_height": base, "height": {"amplitude": 0.0, "frequency": 0.0}, "primitives": primitives}
            })
            .to_string(),
        )
        .unwrap()
    }

    #[test]
    fn flat_ground_has_tops_and_no_bottoms() {
        let f = build_field(&recipe(json!([]), 5.0), 1);
        let p = build_preview(&f, Some(1.0), 8);
        let tops = p["top"].as_array().unwrap();
        assert_eq!(tops.len(), 64);
        assert!(tops.iter().all(|t| (t.as_f64().unwrap() - 5.0).abs() < 0.1));
        assert!(p["bottom"].as_array().unwrap().iter().all(|b| b.is_null()));
    }

    #[test]
    fn floating_sphere_has_top_and_bottom() {
        let sphere = json!([{"shape": "sphere", "center": [0.0, 8.0, 0.0], "radius": 4.0}]);
        let f = build_field(&recipe(sphere, -100.0), 1);
        let p = build_preview(&f, None, 9);
        let mid = 4 * 9 + 4;
        let top = p["top"][mid].as_f64().unwrap();
        let bottom = p["bottom"][mid].as_f64().unwrap();
        assert!((top - 12.0).abs() < 0.3 && (bottom - 4.0).abs() < 0.3, "top {top} bottom {bottom}");
        assert!(p["top"][0].is_null(), "corner column is open air");
    }
}
