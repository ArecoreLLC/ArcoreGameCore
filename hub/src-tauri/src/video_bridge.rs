//! Registry-routed ArcoreCut MCP calls. Provider state lives in its SQLite database.
use serde_json::{json, Value};
use std::{
    io::Write,
    path::PathBuf,
    process::{Command, Stdio},
    time::{Duration, Instant},
};

pub fn call(operation: &str, arguments: &Value) -> Result<Value, String> {
    call_provider("arcore-cut", operation, arguments)
}

pub fn call_provider(provider: &str, operation: &str, arguments: &Value) -> Result<Value, String> {
    if !["arcore-cut", "arcore-animate", "model-forge", "showcase", "sonic-alchemist"].contains(&provider) { return Err("Unsupported provider".into()); }
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
        .find(|s| s["id"] == provider)
        .ok_or("Provider is not registered")?;
    if operation != "tools/list"
        && !server["tools"]
            .as_array()
            .ok_or("Missing tool catalog")?
            .iter()
            .any(|t| t == operation)
    {
        return Err("Operation is not a registered provider tool".into());
    }
    if server["transport"]=="streamable-http" {
        let mut command=Command::new("python");
        #[cfg(windows)] {use std::os::windows::process::CommandExt;command.creation_flags(0x08000000);}
        let mut child=command.arg(root.join("tools/mcp_provider.py")).arg(provider).arg(operation).stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null()).spawn().map_err(|e|e.to_string())?;
        child.stdin.take().ok_or("Missing provider input")?.write_all(arguments.to_string().as_bytes()).map_err(|e|e.to_string())?;
        let output=child.wait_with_output().map_err(|e|e.to_string())?;
        if !output.status.success(){return Err("Local HTTP provider bridge failed".into());}
        return serde_json::from_slice(&output.stdout).map_err(|e|e.to_string());
    }
    let component = registry["components"]
        .as_array()
        .unwrap()
        .iter()
        .find(|c| c["id"] == server["component"])
        .ok_or("Missing provider component")?;
    let cwd = root
        .join(component["root"].as_str().ok_or("Missing component path")?)
        .canonicalize()
        .map_err(|e| e.to_string())?;
    let command = server["command"]
        .as_array()
        .ok_or("Missing provider command")?;
    let program = command[0].as_str().ok_or("Invalid provider executable")?;
    let exe = if std::path::Path::new(program).components().count() == 1 { PathBuf::from(program) } else { cwd.join(program) };
    let capture = std::env::temp_dir().join(format!("gamecore-provider-{}.jsonl", uuid::Uuid::new_v4()));
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
            .map_err(|e| format!("Provider executable unavailable: {e}"))?;
        let mut input = child.stdin.take().ok_or("Provider stdin unavailable")?;
        writeln!(input, "{}", json!({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"gamecore-hub","version":"0.1.0"}}})).map_err(|e|e.to_string())?;
        let start = Instant::now();
        let mut initialized = false;
        let outcome = loop {
            let text = std::fs::read_to_string(&capture).map_err(|e|e.to_string())?;
            let mut response = None;
            for line in text.lines() {
                // A provider can be midway through writing its last JSON line.
                let Ok(v) = serde_json::from_str::<Value>(line) else { continue };
                if v["id"] == 1 && !initialized {
                    if let Some(error) = v.get("error") { response = Some(Err(format!("Provider initialization failed: {error}"))); break; }
                    writeln!(input, "{}", json!({"jsonrpc":"2.0","method":"notifications/initialized"})).map_err(|e|e.to_string())?;
                    let request = if operation == "tools/list" {
                        json!({"jsonrpc":"2.0","id":2,"method":"tools/list"})
                    } else {
                        json!({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":operation,"arguments":arguments}})
                    };
                    writeln!(input, "{request}").map_err(|e|e.to_string())?;
                    initialized = true;
                }
                if v["id"] == 2 {
                    response = Some(if let Some(error) = v.get("error") {
                        Err(format!("Provider RPC error: {error}"))
                    } else if operation == "tools/list" {
                        Ok(json!({"content":[{"type":"text","text":v["result"].to_string()}],"isError":false}))
                    } else { Ok(v["result"].clone()) });
                    break;
                }
            }
            if let Some(response) = response { break response; }
            if let Some(status) = child.try_wait().map_err(|e|e.to_string())? {
                break Err(format!("Provider exited before responding: {status}"));
            }
            if start.elapsed() > Duration::from_secs(server["timeout_seconds"].as_u64().unwrap_or(30).clamp(1, 900)) {
                break Err("Provider MCP timeout; inspect jobs before retrying a write".into());
            }
            std::thread::sleep(Duration::from_millis(25));
        };
        drop(input);
        // Closing stdin permits SDK servers to exit after their response.
        for _ in 0..20 {
            if child.try_wait().map_err(|e|e.to_string())?.is_some() { break; }
            std::thread::sleep(Duration::from_millis(25));
        }
        let _ = child.kill();
        let _ = child.wait();
        outcome
    })();
    let _ = std::fs::remove_file(capture);
    result
}
