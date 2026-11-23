//! First-party Drawing Atelier; Python owns validation/render jobs, hub owns discovery.
use serde_json::Value;
use std::{io::Write,path::PathBuf,process::{Command,Stdio}};

pub fn call(operation: &str, arguments: &Value) -> Result<Value,String> {
    if !["tools/list","drawing_guide","drawing_import_reference","drawing_validate","drawing_render","drawing_job",
        "animal_guide","animal_validate","animal_status","animal_resume","animal_review"].contains(&operation) {
        return Err("Unknown drawing operation; use tools/list first".into());
    }
    let root=std::env::var_os("GAMECORE_ROOT").map(PathBuf::from)
        .unwrap_or_else(||PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../.."));
    let mut command=Command::new(std::env::var_os("GAMECORE_PYTHON").unwrap_or_else(||"python".into()));
    #[cfg(windows)] {use std::os::windows::process::CommandExt;command.creation_flags(0x08000000);}
    let mut child=command.arg(root.join("tools/drawing-studio/production.py"))
        .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped()).spawn()
        .map_err(|e|format!("Drawing Atelier needs Python with Pillow and Node: {e}"))?;
    let request=serde_json::json!({"operation":operation,"arguments":arguments});
    child.stdin.take().ok_or("Missing drawing input")?.write_all(request.to_string().as_bytes()).map_err(|e|e.to_string())?;
    let output=child.wait_with_output().map_err(|e|e.to_string())?;
    if !output.status.success(){return Err(format!("Drawing bridge failed: {}",String::from_utf8_lossy(&output.stderr)));}
    let result:Value=serde_json::from_slice(&output.stdout).map_err(|e|format!("Invalid drawing response: {e}"))?;
    if result["ok"]==true {Ok(result["result"].clone())}
    else {Err(result["error"].as_str().unwrap_or("Drawing operation failed").to_string())}
}
