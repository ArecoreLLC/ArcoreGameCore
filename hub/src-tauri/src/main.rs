#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
mod approvals;
mod roadmap;
mod store;
mod iteration;
mod mcp;
mod video_bridge;
mod animation_pipeline;
mod music;
mod pipelines;
use serde_json::{json, Value};
use std::sync::Mutex;
use store::{Media, Store};
use tauri::{Manager, State};
type AppState = Mutex<Store>;
type Result<T> = std::result::Result<T, String>;

#[tauri::command]
fn export_roadmap_json(directory: String, document: Value) -> Result<String> {
    if document["format"] != "gamecore.roadmap-review"
        || document["schema_version"] != 1
        || !document["games"].is_array()
    {
        return Err("Invalid roadmap review document".into());
    }
    let folder = std::path::Path::new(&directory)
        .canonicalize()
        .map_err(|e| e.to_string())?;
    if !folder.is_dir() {
        return Err("Choose an export folder".into());
    }
    let path = folder.join(format!(
        "gamecore-roadmap-{}-{}.json",
        chrono::Local::now().format("%Y-%m-%d"),
        uuid::Uuid::new_v4()
    ));
    use std::io::Write;
    let mut file = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&path)
        .map_err(|e| e.to_string())?;
    let bytes = serde_json::to_vec_pretty(&document).map_err(|e| e.to_string())?;
    file.write_all(&bytes)
        .and_then(|_| file.write_all(b"\n"))
        .and_then(|_| file.sync_all())
        .map_err(|e| e.to_string())?;
    Ok(path.to_string_lossy().into_owned())
}

#[tauri::command]
fn roadmap(state: State<AppState>) -> Result<Vec<Value>> {
    state
        .lock()
        .map_err(|e| e.to_string())?
        .values("SELECT data FROM roadmap ORDER BY json_extract(data,'$.priority'),id")
}
#[tauri::command]
fn save_roadmap(project: Value, state: State<AppState>) -> Result<Value> {
    state
        .lock()
        .map_err(|e| e.to_string())?
        .save_roadmap(project)
}
#[tauri::command]
fn music_designs(state: State<AppState>) -> Result<Vec<Value>> {
    state.lock().map_err(|e| e.to_string())?.music_designs()
}
#[tauri::command]
fn save_music_design(record: Value, state: State<AppState>) -> Result<Value> {
    state
        .lock()
        .map_err(|e| e.to_string())?
        .save_music_design(record)
}
#[tauri::command]
fn provider_catalogs() -> Result<Value> {
    Ok(music::discover_provider_catalogs())
}
#[tauri::command]
fn pipeline_proposals(state: State<AppState>) -> Result<Vec<Value>> {
    state.lock().map_err(|e| e.to_string())?.pipeline_proposals()
}
#[tauri::command]
fn save_pipeline_proposal(proposal: Value, state: State<AppState>) -> Result<Value> {
    state
        .lock()
        .map_err(|e| e.to_string())?
        .save_pipeline_proposal(proposal)
}
#[tauri::command]
fn export_pipeline_proposal(directory: String, proposal: Value, markdown: String) -> Result<String> {
    let id = proposal["id"].as_str().ok_or("Missing proposal id")?.trim();
    if !pipelines::valid_id(id) {
        return Err("Invalid proposal id".into());
    }
    let folder = std::path::Path::new(&directory).canonicalize().map_err(|e| e.to_string())?;
    if !folder.is_dir() {
        return Err("Choose an export folder".into());
    }
    let json_path = folder.join(format!("{id}.json"));
    let md_path = folder.join(format!("{id}.md"));
    std::fs::write(&json_path, serde_json::to_string_pretty(&proposal).map_err(|e| e.to_string())? + "\n")
        .map_err(|e| e.to_string())?;
    std::fs::write(&md_path, markdown).map_err(|e| e.to_string())?;
    Ok(format!("{} (+ .md)", json_path.display()))
}
#[tauri::command]
fn open_folder_for_path(path: String) -> Result<()> {
    let raw = std::path::Path::new(&path);
    let folder = if raw.is_dir() {
        raw
    } else {
        raw.parent().ok_or("No parent folder")?
    };
    let canonical = folder.canonicalize().map_err(|e| e.to_string())?;
    if !canonical.is_dir() {
        return Err("Folder does not exist".into());
    }
    std::process::Command::new("explorer.exe")
        .arg(canonical)
        .spawn()
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn reveal_indexed_file(
    project_id: String,
    kind: String,
    path: String,
    state: State<AppState>,
) -> Result<()> {
    let path = state
        .lock()
        .map_err(|e| e.to_string())?
        .indexed_path(&project_id, &kind, &path)?;
    std::process::Command::new("explorer.exe")
        .arg(format!("/select,{}", path.display()))
        .spawn()
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn library(state: State<AppState>) -> Result<Value> {
    let s = state.lock().map_err(|e| e.to_string())?;
    Ok(
        json!({"projects":s.values("SELECT data FROM projects ORDER BY name")?,"taxonomy":s.values("SELECT data FROM taxonomy ORDER BY id")?,"media":s.values("SELECT data FROM media")?,"storage":s.root,"schema_version":1}),
    )
}
#[tauri::command]
fn save_project(project: Value, state: State<AppState>) -> Result<()> {
    state
        .lock()
        .map_err(|e| e.to_string())?
        .save_project(project)
}
#[tauri::command]
fn list_files(
    project_id: String,
    kind: String,
    query: String,
    state: State<AppState>,
) -> Result<Vec<Value>> {
    state
        .lock()
        .map_err(|e| e.to_string())?
        .files(&project_id, &kind, &query)
}
#[tauri::command]
fn approval_history(limit: Option<usize>, state: State<AppState>) -> Result<Vec<Value>> {
    state
        .lock()
        .map_err(|e| e.to_string())?
        .approval_history(limit.unwrap_or(500))
}
#[tauri::command]
fn record_approval(entry: Value, state: State<AppState>) -> Result<Value> {
    state.lock().map_err(|e| e.to_string())?.record_approval(entry)
}
#[tauri::command]
fn list_media(project_id: String, state: State<AppState>) -> Result<Vec<Media>> {
    state.lock().map_err(|e| e.to_string())?.media(&project_id)
}
#[tauri::command]
async fn import_media(
    project_id: String,
    path: String,
    kind: String,
    state: State<'_, AppState>,
) -> Result<Media> {
    state
        .lock()
        .map_err(|e| e.to_string())?
        .import_media(&project_id, &path, &kind)
}
#[tauri::command]
fn import_clipboard_image(
    project_id: String,
    bytes: Vec<u8>,
    state: State<AppState>,
) -> Result<Media> {
    state
        .lock()
        .map_err(|e| e.to_string())?
        .import_clipboard_image(&project_id, &bytes)
}
#[tauri::command]
fn set_thumbnail(project_id: String, media_id: String, state: State<AppState>) -> Result<()> {
    state.lock().map_err(|e| e.to_string())?.set_thumbnail(&project_id, &media_id)
}
#[tauri::command]
fn update_media(media: Media, state: State<AppState>) -> Result<Media> {
    state.lock().map_err(|e| e.to_string())?.update_media(media)
}
#[tauri::command]
async fn export_presskit(
    project_id: String,
    directory: String,
    state: State<'_, AppState>,
) -> Result<String> {
    state
        .lock()
        .map_err(|e| e.to_string())?
        .export(&project_id, &directory)
}
#[tauri::command]
async fn backup_library(directory: String, state: State<'_, AppState>) -> Result<String> {
    state.lock().map_err(|e| e.to_string())?.backup(&directory)
}
#[tauri::command]
fn open_project_folder(
    project_id: String,
    provider: Option<String>,
    state: State<AppState>,
) -> Result<()> {
    let s = state.lock().map_err(|e| e.to_string())?;
    let p = s.project(&project_id)?;
    let path = if let Some(provider) = provider {
        let links = p["provider_links"].as_array();
        links
            .and_then(|l| {
                l.iter()
                    .find(|x| x["provider"].as_str() == Some(&provider))
                    .and_then(|x| x["path"].as_str())
                    .filter(|s| !s.is_empty())
            })
            .or(match provider.as_str() {
                "ArcoreModelForge" => Some("X:/Projects/ArcoreModelForge"),
                "ArcoreSoundCore" => Some("X:/Projects/ArcoreSoundCore"),
                "ArcoreSonicAlchemist" => Some("X:/Projects/ArcoreSonicAlchemist"),
                _ => None,
            })
            .ok_or("Unknown provider")?
    } else {
        p["path"].as_str().ok_or("No source path")?
    };
    let path = std::path::Path::new(path)
        .canonicalize()
        .map_err(|e| e.to_string())?;
    if !path.is_dir() {
        return Err("Folder does not exist".into());
    }
    std::process::Command::new("explorer.exe")
        .arg(path)
        .spawn()
        .map_err(|e| e.to_string())?;
    Ok(())
}
fn main() {
    if std::env::args().any(|arg| arg == "--mcp") {
        if let Err(error) = mcp::run() { eprintln!("{error}"); std::process::exit(1); }
        return;
    }
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let root = std::env::var_os("GAMECORE_DATA_DIR")
                .map(std::path::PathBuf::from)
                .unwrap_or(app.path().app_data_dir()?);
            let mut s = Store::open(root).map_err(std::io::Error::other)?;
            s.seed(
                include_str!("../../data/catalog.json"),
                include_str!("../../data/taxonomy.json"),
                include_str!("../../data/files.jsonl"),
            )
            .map_err(std::io::Error::other)?;
            s.seed_roadmap(include_str!("../../data/capability-roadmap.json"))
                .map_err(std::io::Error::other)?;
            s.seed_music_design(include_str!("../../data/music-design/index.json"))
                .map_err(std::io::Error::other)?;
            s.rebase_media().map_err(std::io::Error::other)?;
            // Permit only the managed media directory, including an explicit isolated test library.
            app.asset_protocol_scope()
                .allow_directory(s.root.join("media"), true)?;
            app.manage(Mutex::new(s));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            library,
            roadmap,
            save_roadmap,
            music_designs,
            save_music_design,
            approval_history,
            record_approval,
            provider_catalogs,
            pipeline_proposals,
            save_pipeline_proposal,
            export_pipeline_proposal,
            export_roadmap_json,
            open_folder_for_path,
            reveal_indexed_file,
            save_project,
            list_files,
            list_media,
            import_media,
            import_clipboard_image,
            update_media,
            set_thumbnail,
            export_presskit,
            backup_library,
            open_project_folder
        ])
        .run(tauri::generate_context!())
        .expect("GameCore could not start");
}
