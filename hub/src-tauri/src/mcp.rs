//! Local media tools and registry-routed video production tools.
use crate::store::Store;
use serde_json::{json, Value};
use std::io::{BufRead, Write};

fn definitions() -> Value {
    json!([
        {"name":"showcase_production","description":"Showcase on Fleet: discover typed tools with operation=tools/list. Import exact approved masters with finished_video_import (no extra splash), then youtube_prepare for the Games channel. youtube_queue uploads privately only when requested. Existing protected credentials stay in the provider.","inputSchema":{"type":"object","properties":{"operation":{"type":"string"},"arguments":{"type":"object"}},"required":["operation","arguments"],"additionalProperties":false}},
        {"name":"model_production","description":"ModelForge operations through the GameCore registry. Discover typed schemas with operation=tools/list. Local app credentials are discovered privately; no direct downstream agent registration.","inputSchema":{"type":"object","properties":{"operation":{"type":"string"},"arguments":{"type":"object"}},"required":["operation","arguments"],"additionalProperties":false}},
        {"name":"animation_production","description":"Detailed Animate work routed through the GameCore registry. First operation=tools/list, arguments={}. Animate owns cases, anchors, provenance, ROM, versioned moves, composition, job workers and previews. Jobs persist after this call. Use animate_app to start/inspect the service. Use animation_pipeline for tracked multi-stage orchestration.","inputSchema":{"type":"object","properties":{"operation":{"type":"string"},"arguments":{"type":"object"}},"required":["operation","arguments"],"additionalProperties":false}},
        {"name":"animation_pipeline","description":"GameCore-owned persistent animation pipeline. action=start requires case_id and stages (track/refine/retarget/bake_moves). For bake_moves provide moves_revision and optional sequence. action=status polls and advances completed stages; action=cancel stops its active worker. The returned run_id is durable.","inputSchema":{"type":"object","properties":{"action":{"type":"string","enum":["start","status","cancel"]},"run_id":{"type":"string"},"case_id":{"type":"string"},"stages":{"type":"array","items":{"type":"string","enum":["track","refine","retarget","bake_moves"]}},"moves_revision":{"type":"string"},"sequence":{"type":"array","items":{"type":"string"}}},"required":["action"],"additionalProperties":false}},
        {"name":"video_production","description":"Call ArcoreCut through the GameCore registry. First use operation=tools/list with arguments={} to discover full typed schemas. Operations: video_projects, video_project, video_import, video_timing, video_mix, video_validate, video_render, video_replace, video_jobs, video_cancel, video_workflows. Long media operations return persistent jobs. Edits require project_id and expected_revision; read video_project first. Media remains in GameVideo.","inputSchema":{"type":"object","properties":{"operation":{"type":"string"},"arguments":{"type":"object"}},"required":["operation","arguments"],"additionalProperties":false}},
        {"name":"music_production","description":"Sonic Alchemist adaptive music through the GameCore registry. First operation=tools/list, arguments={}. Operations: adaptive_compositions (saved game designs), adaptive_validate (design path or object, optional .arcore project; returns the runtime contract: bar/fade seconds, boundary, equal-power curve, linear gains), adaptive_export (writes layer WAVs, design.json, assets.json with runtime manifest into a NEW folder), adaptive_manifest (verify an export's frames and SHA-256). Paths are absolute. Games play exports with GameCore adaptive-music modules.","inputSchema":{"type":"object","properties":{"operation":{"type":"string"},"arguments":{"type":"object"}},"required":["operation","arguments"],"additionalProperties":false}},
        {"name":"list_projects","description":"List GameCore project IDs, names and source folders.","inputSchema":{"type":"object","properties":{},"additionalProperties":false}},
        {"name":"list_media","description":"List a game's media including immutable iteration observations. basis=import records the checkout at import, not the image's capture/build revision. Null iteration means legacy/unknown.","inputSchema":{"type":"object","properties":{"project_id":{"type":"string"}},"required":["project_id"],"additionalProperties":false}},
        {"name":"import_media","description":"Copy local media into GameCore as a draft. Screenshots automatically record UTC date, full Git HEAD and modified state from the selected game's folder at import. Does not capture a game, commit changes or prove the pictured build. Originals are preserved.","inputSchema":{"type":"object","properties":{"project_id":{"type":"string"},"path":{"type":"string"},"kind":{"type":"string","enum":["screenshot","video","trailer"]}},"required":["project_id","path","kind"],"additionalProperties":false}}
    ])
}

fn call(store: &Store, params: &Value) -> Result<Value, String> {
    let args = &params["arguments"];
    let string = |key: &str| args[key].as_str().filter(|s| !s.is_empty())
        .ok_or_else(|| format!("{key} is required"));
    match params["name"].as_str() {
        Some("list_projects") => Ok(json!(store.values("SELECT json_object('id',id,'name',name,'path',json_extract(data,'$.path')) FROM projects ORDER BY name")?)),
        Some("list_media") => {
            let id = string("project_id")?;
            store.project(id)?;
            Ok(json!(store.media(id)?))
        },
        Some("import_media") => Ok(json!(store.import_media(string("project_id")?, string("path")?, string("kind")?)?)),
        _ => Err("Unknown GameCore media tool".into()),
    }
}

pub fn respond(store: &Store, request: Value) -> Option<Value> {
    let id = request.get("id")?.clone();
    let result = match request["method"].as_str() {
        Some("initialize") => json!({"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"gamecore-hub","version":env!("CARGO_PKG_VERSION")}}),
        Some("ping") => json!({}),
        Some("tools/list") => json!({"tools":definitions()}),
        Some("tools/call") if request["params"]["name"]=="animation_pipeline" => {
            match crate::animation_pipeline::call(&request["params"]["arguments"]) {
                Ok(value)=>json!({"content":[{"type":"text","text":value.to_string()}],"isError":false}),
                Err(error)=>json!({"content":[{"type":"text","text":error}],"isError":true}),
            }
        },
        Some("tools/call") if request["params"]["name"]=="showcase_production" => {
            let args=&request["params"]["arguments"];
            match crate::video_bridge::call_provider("showcase",args["operation"].as_str().unwrap_or(""),&args["arguments"]) {Ok(result)=>result,Err(error)=>json!({"content":[{"type":"text","text":error}],"isError":true})}
        },
        Some("tools/call") if request["params"]["name"]=="model_production" => {
            let args=&request["params"]["arguments"];
            match crate::video_bridge::call_provider("model-forge",args["operation"].as_str().unwrap_or(""),&args["arguments"]) {Ok(result)=>result,Err(error)=>json!({"content":[{"type":"text","text":error}],"isError":true})}
        },
        Some("tools/call") if request["params"]["name"]=="animation_production" => {
            let args=&request["params"]["arguments"];
            match crate::video_bridge::call_provider("arcore-animate",args["operation"].as_str().unwrap_or(""),&args["arguments"]) {
                Ok(result)=>result,
                Err(error)=>json!({"content":[{"type":"text","text":error}],"isError":true}),
            }
        },
        Some("tools/call") if request["params"]["name"]=="music_production" => {
            let args=&request["params"]["arguments"];
            match crate::video_bridge::call_provider("sonic-alchemist",args["operation"].as_str().unwrap_or(""),&args["arguments"]) {Ok(result)=>result,Err(error)=>json!({"content":[{"type":"text","text":error}],"isError":true})}
        },
        Some("tools/call") if request["params"]["name"]=="video_production" => {
            let args=&request["params"]["arguments"];
            match crate::video_bridge::call(args["operation"].as_str().unwrap_or(""),&args["arguments"]) {
                Ok(result)=>result,
                Err(error)=>json!({"content":[{"type":"text","text":error}],"isError":true})
            }
        },
        Some("tools/call") => match call(store, &request["params"]) {
            Ok(value) => json!({"content":[{"type":"text","text":value.to_string()}],"isError":false}),
            Err(error) => json!({"content":[{"type":"text","text":error}],"isError":true}),
        },
        _ => return Some(json!({"jsonrpc":"2.0","id":id,"error":{"code":-32601,"message":"Method not found"}})),
    };
    Some(json!({"jsonrpc":"2.0","id":id,"result":result}))
}

pub fn run() -> Result<(), String> {
    let root = std::env::var_os("GAMECORE_DATA_DIR").map(std::path::PathBuf::from)
        .or_else(|| std::env::var_os("APPDATA").map(|p| std::path::PathBuf::from(p).join("com.arcore.gamecore")))
        .ok_or("Set GAMECORE_DATA_DIR to the GameCore library folder")?;
    let mut store = Store::open(root)?;
    store.seed(include_str!("../../data/catalog.json"), include_str!("../../data/taxonomy.json"), include_str!("../../data/files.jsonl"))?;
    store.rebase_media()?;
    let mut out = std::io::stdout().lock();
    for line in std::io::stdin().lock().lines() {
        let line = line.map_err(|e| e.to_string())?;
        let response = match serde_json::from_str(&line) {
            Ok(request) => respond(&store, request),
            Err(_) => Some(json!({"jsonrpc":"2.0","id":null,"error":{"code":-32700,"message":"Parse error"}})),
        };
        if let Some(response) = response {
            writeln!(out, "{response}").and_then(|_| out.flush()).map_err(|e| e.to_string())?;
        }
    }
    Ok(())
}
