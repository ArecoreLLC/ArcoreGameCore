#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
mod roadmap;
mod store;
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
        let links = p["provider_links"].as_array().ok_or("No provider links")?;
        links
            .iter()
            .find(|l| l["provider"].as_str() == Some(&provider))
            .and_then(|l| l["path"].as_str())
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
            export_roadmap_json,
            reveal_indexed_file,
            save_project,
            list_files,
            list_media,
            import_media,
            update_media,
            export_presskit,
            backup_library,
            open_project_folder
        ])
        .run(tauri::generate_context!())
        .expect("GameCore could not start");
}
