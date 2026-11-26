//! `arcore-procgen` — validate recipes and bake engine-neutral world bundles.

use arcore_procgen::export::bundle::write_bundle;
use arcore_procgen::{bake, randomize_recipe, randomize_stack, BakeOptions, RandomizeConfig, Recipe, Theme};
use std::path::PathBuf;
use std::process::ExitCode;

const USAGE: &str = "\
usage:
  arcore-procgen validate <recipe.json>...
  arcore-procgen bake <recipe.json> --out <dir> [--threads N] [--density-scale F] [--quality low|medium|high] [--mesh-detail 0|1|2]
  arcore-procgen randomize --seed <N> --out <recipe.json> [--name <name>] [--theme underwater-cartoon|underwater-basin|canyon-arch|overland-cartoon|sky-islands]
                           [--world-size F] [--voxel F] [--mesas N] [--arches N] [--tunnels N]
                           [--kelp-density F] [--shipwreck] [--vents N] [--no-ruins] [--crater] [--external-prop <mesh_key>]...
  arcore-procgen stack --seed <N> --out-dir <dir> [--names reef,overland,sky] [same knobs as randomize]
                           (writes <dir>/<name>/recipe.json for linked reef, overland and sky worlds, plus <dir>/stack.json)

Bundle: terrain.glb, meshes.glb, instances.json, manifest.json (glTF +Y up, meters).
Quality presets scale scatter density by 0.25 / 0.5 / 1.0; --density-scale overrides.";

fn load(path: &str) -> Result<(Recipe, Vec<u8>), String> {
    let bytes = std::fs::read(path).map_err(|e| format!("{path}: {e}"))?;
    let text = std::str::from_utf8(&bytes).map_err(|e| format!("{path}: {e}"))?;
    let recipe = Recipe::from_json(text).map_err(|e| format!("{path}: {e}"))?;
    Ok((recipe, bytes))
}

fn run(args: Vec<String>) -> Result<(), String> {
    let mut it = args.into_iter();
    match it.next().as_deref() {
        Some("validate") => {
            let paths: Vec<String> = it.collect();
            if paths.is_empty() {
                return Err(USAGE.into());
            }
            let mut failed = false;
            for p in paths {
                match load(&p) {
                    Ok((r, _)) => {
                        let errors = r.validate();
                        if errors.is_empty() {
                            let d = r.bounds.sample_dims();
                            println!("ok      {p} ({}, {}x{}x{} samples)", r.name, d[0], d[1], d[2]);
                        } else {
                            failed = true;
                            println!("invalid {p}");
                            errors.iter().for_each(|e| println!("  - {e}"));
                        }
                    }
                    Err(e) => {
                        failed = true;
                        println!("invalid {e}");
                    }
                }
            }
            if failed {
                Err("validation failed".into())
            } else {
                Ok(())
            }
        }
        Some("bake") => {
            let mut recipe_path = None;
            let mut out = None;
            let mut options = BakeOptions::default();
            while let Some(a) = it.next() {
                let mut value = |name: &str| it.next().ok_or_else(|| format!("{name} needs a value"));
                match a.as_str() {
                    "--out" => out = Some(PathBuf::from(value("--out")?)),
                    "--threads" => {
                        options.threads = value("--threads")?.parse().map_err(|_| "--threads expects an integer")?
                    }
                    "--density-scale" => {
                        options.density_scale =
                            value("--density-scale")?.parse().map_err(|_| "--density-scale expects a number")?
                    }
                    "--mesh-detail" => {
                        options.mesh_detail = value("--mesh-detail")?.parse().map_err(|_| "--mesh-detail expects 0, 1 or 2")?
                    }
                    "--quality" => {
                        options.density_scale = match value("--quality")?.as_str() {
                            "low" => 0.25,
                            "medium" => 0.5,
                            "high" => 1.0,
                            q => return Err(format!("unknown quality {q:?}")),
                        }
                    }
                    s if s.starts_with("--") => return Err(format!("unknown option {s}\n{USAGE}")),
                    s => recipe_path = Some(s.to_string()),
                }
            }
            let (recipe_path, out) = recipe_path.zip(out).ok_or_else(|| USAGE.to_string())?;
            let (recipe, bytes) = load(&recipe_path)?;
            let world = bake(&recipe, options).map_err(|e| e.to_string())?;
            for s in &world.stages {
                println!("{:<11} {:>9.1} ms  {}", s.stage, s.millis, s.detail);
            }
            let manifest = write_bundle(&world, &recipe, &bytes, &out).map_err(|e| format!("{}: {e}", out.display()))?;
            for o in manifest["outputs"].as_array().into_iter().flatten() {
                println!("wrote   {} ({} bytes, sha256 {})", o["path"].as_str().unwrap_or("?"), o["bytes"], o["sha256"].as_str().unwrap_or("?"));
            }
            println!("wrote   manifest.json -> {}", out.display());
            Ok(())
        }
        Some(cmd @ ("randomize" | "stack")) => {
            let stack = cmd == "stack";
            let mut cfg = RandomizeConfig::default();
            let mut out: Option<PathBuf> = None;
            let mut out_dir: Option<PathBuf> = None;
            let mut names = vec!["coral_reef_01".to_string(), "overland_01".into(), "sky_islands_01".into()];
            let mut custom_props: Vec<String> = Vec::new();
            while let Some(a) = it.next() {
                let mut value = |name: &str| it.next().ok_or_else(|| format!("{name} needs a value"));
                match a.as_str() {
                    "--out" => out = Some(PathBuf::from(value("--out")?)),
                    "--out-dir" => out_dir = Some(PathBuf::from(value("--out-dir")?)),
                    "--names" => {
                        names = value("--names")?.split(',').map(|s| s.trim().to_string()).collect();
                        if names.len() != 3 {
                            return Err("--names expects three comma-separated names".into());
                        }
                    }
                    "--name" => cfg.name = value("--name")?,
                    "--seed" => cfg.seed = value("--seed")?.parse().map_err(|_| "--seed expects u64")?,
                    "--theme" => cfg.theme = Theme::parse(&value("--theme")?)?,
                    "--world-size" => {
                        cfg.world_size = value("--world-size")?.parse().map_err(|_| "--world-size expects f32")?
                    }
                    "--voxel" => cfg.voxel = value("--voxel")?.parse().map_err(|_| "--voxel expects f32")?,
                    "--mesas" => cfg.mesas = value("--mesas")?.parse().map_err(|_| "--mesas expects usize")?,
                    "--arches" => cfg.arches = value("--arches")?.parse().map_err(|_| "--arches expects usize")?,
                    "--tunnels" => cfg.tunnels = value("--tunnels")?.parse().map_err(|_| "--tunnels expects usize")?,
                    "--kelp-density" => {
                        cfg.kelp_density = value("--kelp-density")?.parse().map_err(|_| "--kelp-density expects f32")?
                    }
                    "--shipwreck" => cfg.shipwreck = true,
                    "--no-ruins" => cfg.ruins = false,
                    "--crater" => cfg.crater = true,
                    "--vents" => cfg.vents = value("--vents")?.parse().map_err(|_| "--vents expects usize")?,
                    "--external-prop" => custom_props.push(value("--external-prop")?),
                    s => return Err(format!("unknown option {s}\n{USAGE}")),
                }
            }
            if !custom_props.is_empty() {
                cfg.external_props = custom_props;
            } else if cfg.shipwreck {
                // A generated wreck replaces the default external shipwreck slot.
                cfg.external_props.clear();
            }
            if stack {
                let dir = out_dir.ok_or_else(|| USAGE.to_string())?;
                let (worlds, receipt) = randomize_stack(&cfg, [&names[0], &names[1], &names[2]]);
                for (name, recipe) in &worlds {
                    let errors = recipe.validate();
                    if !errors.is_empty() {
                        return Err(format!("{name}: stacked recipe failed validation: {}", errors.join("; ")));
                    }
                    let path = dir.join(name).join("recipe.json");
                    std::fs::create_dir_all(path.parent().unwrap()).map_err(|e| format!("{}: {e}", path.display()))?;
                    let pretty = serde_json::to_string_pretty(recipe).map_err(|e| e.to_string())?;
                    std::fs::write(&path, pretty).map_err(|e| format!("{}: {e}", path.display()))?;
                    println!("wrote   {} (seed={}, primitives={})", path.display(), recipe.seed, recipe.terrain.primitives.len());
                }
                let path = dir.join("stack.json");
                let pretty = serde_json::to_string_pretty(&receipt).map_err(|e| e.to_string())?;
                std::fs::write(&path, pretty).map_err(|e| format!("{}: {e}", path.display()))?;
                println!("wrote   {}", path.display());
                return Ok(());
            }
            let out = out.ok_or_else(|| USAGE.to_string())?;
            let recipe = randomize_recipe(&cfg);
            let errors = recipe.validate();
            if !errors.is_empty() {
                return Err(format!("randomized recipe failed validation: {}", errors.join("; ")));
            }
            if let Some(parent) = out.parent() {
                if !parent.as_os_str().is_empty() {
                    std::fs::create_dir_all(parent).map_err(|e| format!("{}: {e}", parent.display()))?;
                }
            }
            let pretty = serde_json::to_string_pretty(&recipe).map_err(|e| e.to_string())?;
            std::fs::write(&out, pretty).map_err(|e| format!("{}: {e}", out.display()))?;
            println!(
                "wrote   {} (theme={}, seed={}, primitives={}, props={})",
                out.display(),
                cfg.theme.as_str(),
                cfg.seed,
                recipe.terrain.primitives.len(),
                recipe.props.len()
            );
            Ok(())
        }
        _ => Err(USAGE.into()),
    }
}

fn main() -> ExitCode {
    match run(std::env::args().skip(1).collect()) {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("{e}");
            ExitCode::FAILURE
        }
    }
}
