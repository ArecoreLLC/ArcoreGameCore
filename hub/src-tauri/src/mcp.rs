//! Local stdio media tools for the GameCore hub; no downstream connections.
use crate::store::Store;
use serde_json::{json, Value};
use std::io::{BufRead, Write};

fn definitions() -> Value {
    json!([
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
