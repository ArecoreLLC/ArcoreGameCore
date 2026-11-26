//! # arcore_procgen
//!
//! Engine-neutral procedural world generation for ArcoreGameCore, organized as an
//! ordered pipeline of stages. See `shared/procgen/README.md` for the contract.
//!
//! ```text
//! recipe ─► field ─► surface ─► cells ─► parametric ─► scatter ─► export
//!  (0)       (1)       (2)       (3)        (4)          (5)        (6)
//! ```
//!
//! The crate never touches an engine, window, GPU or audio device. Engine adapters
//! (Godot, Unreal) consume the exported bundle or link this crate behind their own
//! boundary. Presentation (materials, palettes, fog, audio) stays consumer-owned.

mod biomes;
pub mod common;
pub mod export;
pub mod pipeline;
pub mod randomize;
pub mod recipe;
pub mod runtime;
pub mod stages;

pub use pipeline::{bake, BakeOptions, WorldBake};
pub use randomize::{randomize_recipe, randomize_stack, RandomizeConfig, Theme};
pub use recipe::{Recipe, TreeStyle};
