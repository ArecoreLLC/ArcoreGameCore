//! GameCore owns stage orchestration; Animate owns all detailed work and durable jobs.
use serde_json::{json, Value};
use std::path::PathBuf;

fn provider(tool: &str, args: Value) -> Result<Value, String> {
    let response = crate::video_bridge::call_provider("arcore-animate", tool, &args)?;
    let text = response["content"][0]["text"].as_str().ok_or("Missing Animate response")?;
    if response["isError"].as_bool().unwrap_or(false) { return Err(text.into()); }
    serde_json::from_str(text).map_err(|e| e.to_string())
}

fn save(path: &std::path::Path, value: &Value) -> Result<(), String> {
    let temp = path.with_extension("tmp");
    std::fs::write(&temp,serde_json::to_vec_pretty(value).map_err(|e|e.to_string())?).map_err(|e|e.to_string())?;
    std::fs::rename(temp,path).map_err(|e|e.to_string())
}

struct Lock(PathBuf);
impl Drop for Lock { fn drop(&mut self) { let _=std::fs::remove_file(&self.0); } }

pub fn call(args: &Value) -> Result<Value, String> {
    let action=args["action"].as_str().ok_or("action required")?;
    if !["start","status","cancel"].contains(&action) { return Err("Unknown pipeline action".into()); }
    let root=std::env::var_os("GAMECORE_DATA_DIR").map(PathBuf::from)
        .or_else(||std::env::var_os("APPDATA").map(|p|PathBuf::from(p).join("com.arcore.gamecore")))
        .ok_or("GameCore data directory unavailable")?.join("animation-runs");
    std::fs::create_dir_all(&root).map_err(|e|e.to_string())?;
    let id=if action=="start" { uuid::Uuid::new_v4().to_string() }
        else { args["run_id"].as_str().ok_or("run_id required")?.to_string() };
    uuid::Uuid::parse_str(&id).map_err(|_|"Invalid run_id")?;
    let lock=root.join(format!("{id}.lock"));
    let _file=std::fs::OpenOptions::new().write(true).create_new(true).open(&lock)
        .map_err(|_|"Pipeline is busy; retry. After a hub crash, inspect and remove its stale .lock file.")?;
    let _lock=Lock(lock);
    let path=root.join(format!("{id}.json"));
    let mut run=if action=="start" {
        let case=args["case_id"].as_str().ok_or("case_id required")?;
        let stages=args["stages"].as_array().ok_or("stages required")?;
        if stages.is_empty() || stages.len()>8 || stages.iter().any(|s|!matches!(s.as_str(),Some("track"|"refine"|"retarget"|"bake_moves"))) {
            return Err("Choose 1–8 track/refine/retarget/bake_moves stages".into());
        }
        if stages.iter().any(|s|s=="bake_moves") && !args["moves_revision"].is_string() { return Err("moves_revision required for bake_moves".into()); }
        provider("animate_app",json!({"action":"start","case_id":case}))?;
        json!({"run_id":id,"case_id":case,"stages":stages,"stage_index":0,"status":"running",
            "moves_revision":args["moves_revision"],"sequence":args["sequence"],"jobs":[],"active_job":null,
            "created_at":chrono::Utc::now().to_rfc3339(),"advance_policy":"poll status to advance stages"})
    } else { serde_json::from_slice(&std::fs::read(&path).map_err(|e|e.to_string())?).map_err(|e|e.to_string())? };
    save(&path,&run)?;
    if run["status"]!="running" { return Ok(run); }
    if action=="cancel" {
        if run["active_job"].is_string() {
            let job=provider("animate_cancel_job",json!({"case_id":run["case_id"],"job_id":run["active_job"]}))?;
            run["last_job"]=job;
        }
        run["status"]=json!("cancelled");save(&path,&run)?;return Ok(run);
    }
    if run["active_job"].is_string() {
        let job=provider("animate_jobs",json!({"case_id":run["case_id"],"job_id":run["active_job"]}))?;
        let status=job["status"].as_str().unwrap_or("unknown").to_string();run["last_job"]=job;
        match status.as_str() {
            "succeeded" => { run["stage_index"]=json!(run["stage_index"].as_u64().unwrap()+1);run["active_job"]=Value::Null; },
            "failed"|"cancelled"|"interrupted" => {run["status"]=json!(status);},
            _=>{},
        }
    }
    if run["status"]=="running" && run["active_job"].is_null() {
        let i=run["stage_index"].as_u64().unwrap() as usize;
        if i>=run["stages"].as_array().unwrap().len() { run["status"]=json!("succeeded"); }
        else {
            let operation=run["stages"][i].clone();
            let mut arguments=json!({});
            if operation=="bake_moves" {
                arguments["revision"]=run["moves_revision"].clone();
                if !run["sequence"].is_null() {arguments["sequence"]=run["sequence"].clone();}
            }
            // Deterministic request IDs recover a response lost before saving this receipt.
            save(&path,&run)?;
            let job=provider("animate_start_job",json!({"case_id":run["case_id"],"operation":operation,
                "arguments":arguments,"request_id":format!("gamecore:{id}:{i}")}))?;
            run["active_job"]=job["id"].clone();run["jobs"].as_array_mut().unwrap().push(job["id"].clone());
            run["last_job"]=job;
        }
    }
    run["updated_at"]=json!(chrono::Utc::now().to_rfc3339());
    save(&path,&run)?;
    Ok(run)
}
