//! Registry-routed ArcoreCut MCP calls. Provider state lives in its SQLite database.
use serde_json::{json, Value};
use std::{
    io::Write,
    path::PathBuf,
    process::{Command, Stdio},
    time::{Duration, Instant},
};

pub fn call(operation: &str, arguments: &Value) -> Result<Value, String> {
    let root = std::env::var_os("GAMECORE_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../.."));
    let registry: Value = serde_json::from_slice(
        &std::fs::read(root.join("shared/ecosystem.json")).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    let server = registry["mcp"]["servers"]
        .as_array()
        .ok_or("Missing MCP registry")?
        .iter()
        .find(|s| s["id"] == "arcore-cut")
        .ok_or("ArcoreCut is not registered")?;
    if operation != "tools/list"
        && !server["tools"]
            .as_array()
            .ok_or("Missing tool catalog")?
            .iter()
            .any(|t| t == operation)
    {
        return Err("Operation is not an ArcoreCut registry tool".into());
    }
    let component = registry["components"]
        .as_array()
        .unwrap()
        .iter()
        .find(|c| c["id"] == server["component"])
        .ok_or("Missing ArcoreCut component")?;
    let cwd = root
        .join(component["root"].as_str().ok_or("Missing component path")?)
        .canonicalize()
        .map_err(|e| e.to_string())?;
    let command = server["command"]
        .as_array()
        .ok_or("Missing provider command")?;
    let exe = cwd.join(command[0].as_str().ok_or("Invalid provider executable")?);
    let capture = std::env::temp_dir().join(format!("gamecore-cut-{}.jsonl", uuid::Uuid::new_v4()));
    let output = std::fs::File::create(&capture).map_err(|e| e.to_string())?;
    let result = (|| {
        let mut cmd = Command::new(exe);
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            cmd.creation_flags(0x08000000);
        }
        cmd.current_dir(cwd)
            .env(
                "GAMECORE_ROOT",
                root.canonicalize().map_err(|e| e.to_string())?,
            )
            .stdin(Stdio::piped())
            .stdout(output)
            .stderr(Stdio::inherit());
        for arg in &command[1..] {
            cmd.arg(arg.as_str().ok_or("Invalid command argument")?);
        }
        let mut child = cmd
            .spawn()
            .map_err(|e| format!("Build ArcoreCut before using its MCP tools: {e}"))?;
        let input = format!(
            "{}\n{}\n{}\n",
            json!({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"gamecore-hub","version":"0.1.0"}}}),
            json!({"jsonrpc":"2.0","method":"notifications/initialized"}),
            if operation == "tools/list" {
                json!({"jsonrpc":"2.0","id":2,"method":"tools/list"})
            } else {
                json!({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":operation,"arguments":arguments}})
            }
        );
        child
            .stdin
            .take()
            .ok_or("Provider stdin unavailable")?
            .write_all(input.as_bytes())
            .map_err(|e| e.to_string())?;
        let start = Instant::now();
        loop {
            if let Some(status) = child.try_wait().map_err(|e| e.to_string())? {
                if !status.success() {
                    return Err(format!("ArcoreCut exited with {status}"));
                }
                break;
            }
            if start.elapsed() > Duration::from_secs(30) {
                let _ = child.kill();
                let _ = child.wait();
                return Err("ArcoreCut MCP timeout; inspect jobs before retrying a write".into());
            }
            std::thread::sleep(Duration::from_millis(25));
        }
        let text = std::fs::read_to_string(&capture).map_err(|e| e.to_string())?;
        for line in text.lines() {
            let v: Value = serde_json::from_str(line).map_err(|e| e.to_string())?;
            if v["id"] == 2 {
                return Ok(if operation == "tools/list" {
                    json!({"content":[{"type":"text","text":v["result"].to_string()}],"isError":false})
                } else {
                    v["result"].clone()
                });
            }
        }
        Err("ArcoreCut returned no tool response".into())
    })();
    let _ = std::fs::remove_file(capture);
    result
}
