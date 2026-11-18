use crate::store::{Result, Store};
use rusqlite::{params, Connection, OpenFlags};
use serde_json::{json, Value};
use std::{
    fs,
    path::{Path, PathBuf},
};

const GAME_STATUSES: &[&str] = &[
    "unassigned",
    "recommended",
    "excluded",
    "planned",
    "in_progress",
    "approved",
];
const TRACK_STATUSES: &[&str] = &[
    "prompt_ready",
    "generated",
    "stems_split",
    "approved",
    "rejected",
];
const VOCALS: &[&str] = &["none", "wordless", "sung"];
const SUNO_INSTRUMENTS: &[&str] = &[
    // Standard options (22)
    "Lead Vocal",
    "Drums",
    "Bass",
    "Backing Vocals",
    "Piano",
    "Electric Guitar",
    "Percussion",
    "Strings",
    "Synth",
    "Acoustic Guitar",
    "Other",
    "Synth Pad",
    "Synth Bass",
    "Guitar",
    "Brass",
    "Organ",
    "Lead Guitar",
    "Synth Keys",
    "Rhythm Electric Guitar",
    "Electric Piano",
    "Upright Bass",
    "Keyboards",
    // Beta options (68)
    "Kick",
    "Snare",
    "Risers",
    "Synth Strings",
    "Synth Lead",
    "Woodwinds",
    "Rhythm Acoustic Guitar",
    "Flute",
    "Harp",
    "Tambourine",
    "Trumpet",
    "Arpeggiator",
    "Accordion",
    "Fiddle",
    "Slide Guitar",
    "Vocoder",
    "Violin",
    "Synth Brass",
    "Mandolin",
    "Choir",
    "Banjo",
    "Bells",
    "Clarinet",
    "Tenor Saxophone",
    "Trombone",
    "Shaker",
    "French Horn",
    "Glockenspiel",
    "Cello",
    "Timpani",
    "Harmonica",
    "Marimba",
    "Vibraphone",
    "Saxophone",
    "Orchestra",
    "Cymbals",
    "Clap",
    "Oboe",
    "Celesta",
    "Congas",
    "Drone",
    "Alto Saxophone",
    "Double Bass",
    "Ukulele",
    "Harpsichord",
    "Baritone Saxophone",
    "Xylophone",
    "Tuba",
    "Bass Guitar",
    "Whistle",
    "808",
    "Bongos",
    "Bassoon",
    "Cowbell",
    "Viola",
    "Sitar",
    "Steel Drums",
    "Piccolo",
    "Theremin",
    "Bagpipes",
    "Hi-Hat",
    "Music Box",
    "Melodica",
    "Tabla",
    "Koto",
    "Djembe",
    "Taiko",
    "Didgeridoo",
];

fn err(e: impl std::fmt::Display) -> String {
    e.to_string()
}

fn validate_music_record(rec: &Value) -> Result<()> {
    let gid = rec["game_id"]
        .as_str()
        .filter(|s| !s.is_empty())
        .ok_or("Music record requires game_id")?;
    let status = rec["status"]
        .as_str()
        .ok_or_else(|| format!("{gid}: missing status"))?;
    if !GAME_STATUSES.contains(&status) {
        return Err(format!("{gid}: invalid music design status '{status}'"));
    }
    let tracks = rec["tracks"]
        .as_array()
        .ok_or_else(|| format!("{gid}: tracks must be an array"))?;
    for t in tracks {
        let tid = t["track_id"]
            .as_str()
            .filter(|s| !s.is_empty())
            .ok_or_else(|| format!("{gid}: track missing track_id"))?;
        let ts = t["status"]
            .as_str()
            .ok_or_else(|| format!("{tid}: missing status"))?;
        if !TRACK_STATUSES.contains(&ts) {
            return Err(format!("{tid}: invalid track status '{ts}'"));
        }
        let voc = t["vocals"]
            .as_str()
            .ok_or_else(|| format!("{tid}: missing vocals"))?;
        if !VOCALS.contains(&voc) {
            return Err(format!("{tid}: invalid vocals '{voc}'"));
        }
        if t["style_prompt"].as_str().unwrap_or("").trim().is_empty() {
            return Err(format!("{tid}: missing style_prompt"));
        }
        if voc == "sung" && t["lyrics"].as_str().unwrap_or("").trim().is_empty() {
            return Err(format!("{tid}: sung track requires lyrics"));
        }
        if ["generated", "stems_split", "approved"].contains(&ts)
            && t["suno"]["url"].as_str().unwrap_or("").trim().is_empty()
        {
            return Err(format!("{tid}: generated track requires a Suno URL"));
        }
        let insts = t["instruments"]
            .as_array()
            .ok_or_else(|| format!("{tid}: instruments must be a list"))?;
        if insts.is_empty() {
            return Err(format!(
                "{tid}: specify instruments for Advanced Split stem mapping"
            ));
        }
        for inst in insts {
            let name = inst["name"].as_str().unwrap_or("");
            let stem = inst["stem"].as_str().unwrap_or("");
            if !SUNO_INSTRUMENTS.contains(&name) || !SUNO_INSTRUMENTS.contains(&stem) {
                return Err(format!(
                    "{tid}: '{name}' / '{stem}' is not one of Suno's 22 Standard or 68 Beta options"
                ));
            }
        }
    }
    Ok(())
}

impl Store {
    pub fn seed_music_design(&mut self, source: &str) -> Result<()> {
        let records: Vec<Value> = serde_json::from_str(source).map_err(err)?;
        let tx = self.conn.transaction().map_err(err)?;
        tx.execute_batch(
            "CREATE TABLE IF NOT EXISTS music_design(game_id TEXT PRIMARY KEY, data TEXT NOT NULL, updated_at TEXT NOT NULL);",
        )
        .map_err(err)?;
        for rec in records {
            let gid = rec["game_id"]
                .as_str()
                .ok_or("Missing game_id in music design seed")?;
            let ts = rec["updated_at"].as_str().unwrap_or("");
            let existing: Option<String> = tx
                .query_row(
                    "SELECT data FROM music_design WHERE game_id=?1",
                    [gid],
                    |r| r.get(0),
                )
                .ok();
            if let Some(raw) = existing {
                if let Ok(old) = serde_json::from_str::<Value>(&raw) {
                    let is_untouched = old["status"].as_str() == Some("recommended");
                    let has_legacy_inst = old["tracks"]
                        .as_array()
                        .map(|arr| {
                            arr.iter().any(|t| {
                                t["instruments"]
                                    .as_array()
                                    .map(|insts| {
                                        insts.iter().any(|i| {
                                            !SUNO_INSTRUMENTS
                                                .contains(&i["stem"].as_str().unwrap_or(""))
                                        })
                                    })
                                    .unwrap_or(false)
                            })
                        })
                        .unwrap_or(false);
                    let seed_upgraded =
                        is_untouched && rec["status"].as_str() == Some("in_progress");
                    let old_has_candidates = old["tracks"][0]["suno"]["candidates"]
                        .as_array()
                        .map(|a| !a.is_empty())
                        .unwrap_or(false);
                    let rec_has_candidates = rec["tracks"][0]["suno"]["candidates"]
                        .as_array()
                        .map(|a| !a.is_empty())
                        .unwrap_or(false);
                    let old_has_ingame = old["tracks"][0]["suno"]["in_game_status"].is_string();
                    let rec_has_ingame = rec["tracks"][0]["suno"]["in_game_status"].is_string();
                    let seed_enriched = (!old_has_candidates && rec_has_candidates)
                        || (!old_has_ingame && rec_has_ingame);
                    if (is_untouched && has_legacy_inst) || seed_upgraded || seed_enriched {
                        tx.execute(
                            "UPDATE music_design SET data=?1, updated_at=?2 WHERE game_id=?3",
                            params![rec.to_string(), ts, gid],
                        )
                        .map_err(err)?;
                    }
                }
                continue;
            }
            tx.execute(
                "INSERT INTO music_design(game_id,data,updated_at) VALUES(?1,?2,?3)",
                params![gid, rec.to_string(), ts],
            )
            .map_err(err)?;
        }
        tx.commit().map_err(err)
    }

    pub fn music_designs(&self) -> Result<Vec<Value>> {
        self.conn
            .execute_batch(
                "CREATE TABLE IF NOT EXISTS music_design(game_id TEXT PRIMARY KEY, data TEXT NOT NULL, updated_at TEXT NOT NULL);",
            )
            .map_err(err)?;
        self.values(
            "SELECT data FROM music_design ORDER BY json_extract(data,'$.name'), game_id",
        )
    }

    pub fn save_music_design(&mut self, mut rec: Value) -> Result<Value> {
        validate_music_record(&rec)?;
        let gid = rec["game_id"].as_str().unwrap().to_owned();
        let now = chrono::Utc::now().to_rfc3339();
        rec["updated_at"] = json!(now);
        self.conn
            .execute_batch(
                "CREATE TABLE IF NOT EXISTS music_design(game_id TEXT PRIMARY KEY, data TEXT NOT NULL, updated_at TEXT NOT NULL);",
            )
            .map_err(err)?;
        self.conn
            .execute(
                "INSERT INTO music_design(game_id,data,updated_at) VALUES(?1,?2,?3) ON CONFLICT(game_id) DO UPDATE SET data=excluded.data,updated_at=excluded.updated_at",
                params![gid, rec.to_string(), now],
            )
            .map_err(err)?;
        Ok(rec)
    }
}

pub fn discover_provider_catalogs() -> Value {
    let mut modelforge = Vec::new();
    let mut soundcore = Vec::new();
    let mut sonicalchemist = Vec::new();

    // 1. ArcoreModelForge
    let mf_root = Path::new("X:/Projects/ArcoreModelForge");
    let mut mf_lib_dir = PathBuf::from("X:/Projects/ModelVaultLibrary");
    if let Some(home) = std::env::var_os("USERPROFILE") {
        let settings_path = PathBuf::from(home).join(".modelvault/settings.json");
        if let Ok(raw) = fs::read_to_string(&settings_path) {
            if let Ok(v) = serde_json::from_str::<Value>(&raw) {
                if let Some(dir) = v["libraryDir"].as_str().filter(|s| !s.is_empty()) {
                    mf_lib_dir = PathBuf::from(dir);
                }
            }
        }
    }
    let mf_db = mf_lib_dir.join("modelvault.db");
    if mf_db.is_file() {
        if let Ok(conn) = Connection::open_with_flags(&mf_db, OpenFlags::SQLITE_OPEN_READ_ONLY) {
            if let Ok(mut stmt) = conn.prepare(
                "SELECT project, COUNT(*) FROM assets WHERE project IS NOT NULL AND trim(project) != '' GROUP BY project ORDER BY COUNT(*) DESC, project",
            ) {
                if let Ok(rows) = stmt.query_map([], |r| Ok((r.get::<_, String>(0)?, r.get::<_, i64>(1)?))) {
                    for row in rows.flatten() {
                        modelforge.push(json!({
                            "id": row.0,
                            "label": format!("{} ({} models)", row.0, row.1),
                            "kind": "project",
                            "count": row.1,
                            "path": mf_lib_dir.to_string_lossy()
                        }));
                    }
                }
            }
        }
    }

    // 2. ArcoreSoundCore
    if let Some(appdata) = std::env::var_os("APPDATA") {
        let sc_dir = PathBuf::from(appdata).join("com.arcore.soundcore");
        let sc_db = sc_dir.join("library.sqlite3");
        if sc_db.is_file() {
            if let Ok(conn) = Connection::open_with_flags(&sc_db, OpenFlags::SQLITE_OPEN_READ_ONLY)
            {
                if let Ok(mut stmt) =
                    conn.prepare("SELECT id FROM records WHERE kind='project' ORDER BY id")
                {
                    if let Ok(rows) = stmt.query_map([], |r| r.get::<_, String>(0)) {
                        for id in rows.flatten() {
                            soundcore.push(json!({
                                "id": id,
                                "label": format!("Project: {}", id),
                                "kind": "project",
                                "path": sc_dir.to_string_lossy()
                            }));
                        }
                    }
                }
                if let Ok(mut stmt) = conn.prepare(
                    "SELECT c.name, COUNT(i.id) FROM collections c LEFT JOIN collection_items i ON c.name = i.name GROUP BY c.name ORDER BY c.name",
                ) {
                    if let Ok(rows) = stmt.query_map([], |r| Ok((r.get::<_, String>(0)?, r.get::<_, i64>(1)?))) {
                        for (name, count) in rows.flatten() {
                            soundcore.push(json!({
                                "id": format!("collection:{name}"),
                                "label": format!("Collection: {} ({} sounds)", name, count),
                                "kind": "collection",
                                "count": count,
                                "path": sc_dir.to_string_lossy()
                            }));
                        }
                    }
                }
            }
        }
    }
    let sc_repo_cat = Path::new("X:/Projects/ArcoreSoundCore/catalog/sounds.json");
    if sc_repo_cat.is_file() {
        for cat in [
            "arcade", "combat", "impacts", "movement", "music", "objects", "sci-fi", "ui",
        ] {
            let p = Path::new("X:/Projects/ArcoreSoundCore/sounds").join(cat);
            soundcore.push(json!({
                "id": format!("category:{cat}"),
                "label": format!("SoundCore category: {cat}"),
                "kind": "category",
                "path": p.to_string_lossy()
            }));
        }
    }

    // 3. ArcoreSonicAlchemist
    let sa_repo = Path::new("X:/Projects/ArcoreSonicAlchemist");
    let comp_dir = sa_repo.join("compositions");
    if let Ok(entries) = fs::read_dir(&comp_dir) {
        for e in entries.flatten() {
            let p = e.path();
            if p.extension().and_then(|s| s.to_str()) == Some("json") {
                if let Some(stem) = p.file_stem().and_then(|s| s.to_str()) {
                    sonicalchemist.push(json!({
                        "id": stem,
                        "label": format!("Composition: {stem}"),
                        "kind": "composition",
                        "path": p.to_string_lossy()
                    }));
                }
            }
        }
    }
    let songs_dir = sa_repo.join(".runtime/songs");
    if let Ok(entries) = fs::read_dir(&songs_dir) {
        for e in entries.flatten() {
            let p = e.path();
            if p.is_dir() {
                if let Some(name) = p.file_name().and_then(|s| s.to_str()) {
                    sonicalchemist.push(json!({
                        "id": format!("song:{name}"),
                        "label": format!("Song session: {name}"),
                        "kind": "song",
                        "path": p.to_string_lossy()
                    }));
                }
            }
        }
    }
    if let Some(local) = std::env::var_os("LOCALAPPDATA") {
        let jobs_file = PathBuf::from(local).join("com.arcore.sonicalchemist/processing/jobs.json");
        if let Ok(raw) = fs::read_to_string(&jobs_file) {
            if let Ok(v) = serde_json::from_str::<Value>(&raw) {
                if let Some(jobs) = v["jobs"].as_array() {
                    for j in jobs.iter().take(20) {
                        let id = j["id"].as_str().unwrap_or("");
                        let title = j["title"]
                            .as_str()
                            .or_else(|| j["name"].as_str())
                            .or_else(|| j["source_path"].as_str())
                            .unwrap_or(id);
                        if !id.is_empty() {
                            sonicalchemist.push(json!({
                                "id": format!("job:{id}"),
                                "label": format!("Stem job: {title}"),
                                "kind": "job",
                                "path": jobs_file.parent().unwrap_or(sa_repo).to_string_lossy()
                            }));
                        }
                    }
                }
            }
        }
    }

    json!({
        "ArcoreModelForge": {
            "root": mf_root.to_string_lossy(),
            "library": mf_lib_dir.to_string_lossy(),
            "projects": modelforge
        },
        "ArcoreSoundCore": {
            "root": "X:/Projects/ArcoreSoundCore",
            "projects": soundcore
        },
        "ArcoreSonicAlchemist": {
            "root": sa_repo.to_string_lossy(),
            "projects": sonicalchemist
        }
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::store::Store;

    #[test]
    fn seed_save_and_validate_music_design() {
        let d = tempfile::tempdir().unwrap();
        let mut s = Store::open(d.path().join("library")).unwrap();
        s.seed_music_design(include_str!("../../data/music-design/index.json"))
            .unwrap();
        let list = s.music_designs().unwrap();
        assert_eq!(list.len(), 81);
        let mut bistro = list
            .into_iter()
            .find(|r| r["game_id"] == "beast-bistro-express")
            .unwrap();
        assert_eq!(bistro["status"], "in_progress");
        assert_eq!(bistro["recommended_archetype"], "action-rock");
        assert_eq!(bistro["tracks"].as_array().unwrap().len(), 3);

        // Approve archetype -> status approved
        bistro["archetype"] = json!("action-rock");
        bistro["status"] = json!("approved");
        let saved = s.save_music_design(bistro.clone()).unwrap();
        assert_eq!(saved["status"], "approved");

        // Re-seeding never overwrites saved edits
        s.seed_music_design(include_str!("../../data/music-design/index.json"))
            .unwrap();
        let reloaded = s
            .music_designs()
            .unwrap()
            .into_iter()
            .find(|r| r["game_id"] == "beast-bistro-express")
            .unwrap();
        assert_eq!(reloaded["status"], "approved");

        // Validation rejects sung track without lyrics or generated track without URL
        let mut bad = reloaded.clone();
        bad["tracks"][1]["status"] = json!("generated");
        assert!(s.save_music_design(bad).is_err());
    }
}
