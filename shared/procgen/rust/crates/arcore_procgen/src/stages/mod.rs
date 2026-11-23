//! Ordered generation stages. Each stage is a pure function of the recipe and
//! the outputs of earlier stages; see `pipeline.rs` for the runner.
//!
//! 0. `recipe`      (crate::recipe) load + validate
//! 1. `field`       density grid
//! 2. `surface`     Surface Nets mesh
//! 3. `cells`       XZ cell grid + per-cell chunks
//! 4. `parametric`  generated mesh library
//! 5. `scatter`     instances per layer/cell, placed props

pub mod cells;
pub mod field;
pub mod parametric;
pub mod scatter;
pub mod surface;
