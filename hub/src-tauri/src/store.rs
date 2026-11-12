use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    fs,
    io::{Read, Write},
    path::{Path, PathBuf},
};

pub type Result<T> = std::result::Result<T, String>;
pub struct Store {
    pub conn: Connection,
    pub root: PathBuf,
}
fn err(e: impl std::fmt::Display) -> String {
    e.to_string()
}
fn now() -> String {
    chrono::Utc::now().to_rfc3339()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Media {
    pub id: String,
    pub project_id: String,
    pub kind: String,
    pub title: String,
    pub caption: String,
    pub alt_text: String,
    pub rights: String,
    pub credit: String,
    pub status: String,
    pub source_path: String,
    pub stored_path: String,
    pub sha256: String,
    pub created_at: String,
    pub approved_at: Option<String>,
    pub sort_order: i64,
    #[serde(default)]
    pub width: Option<u32>,
    #[serde(default)]
    pub height: Option<u32>,
    #[serde(default)]
    pub duration_seconds: Option<f64>,
    #[serde(default)]
    pub curation: String,
    #[serde(default)]
    pub content_role: String,
    #[serde(default)]
    pub review_notes: String,
}

impl Store {
    pub fn open(root: PathBuf) -> Result<Self> {
        fs::create_dir_all(root.join("media")).map_err(err)?;
        let conn = Connection::open(root.join("catalog.sqlite3")).map_err(err)?;
        conn.busy_timeout(std::time::Duration::from_secs(5))
            .map_err(err)?;
        conn.execute_batch("PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL;")
            .map_err(err)?;
        let version: i64 = conn
            .query_row("PRAGMA user_version", [], |r| r.get(0))
            .map_err(err)?;
        if version > 1 {
            return Err("This library was created by a newer GameCore version.".into());
        }
        conn.execute_batch("BEGIN;
    CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, name TEXT NOT NULL, data TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS taxonomy(id TEXT PRIMARY KEY, data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS files(project_id TEXT NOT NULL REFERENCES projects(id), kind TEXT NOT NULL, path TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY(project_id,kind,path));
    CREATE TABLE IF NOT EXISTS media(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), data TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS media_project ON media(project_id);
    CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    PRAGMA user_version=1; COMMIT;").map_err(err)?;
        Ok(Self { conn, root })
    }
    pub fn seed(&mut self, projects: &str, taxonomy: &str, files: &str) -> Result<()> {
        let seeded: i64 = self
            .conn
            .query_row("SELECT COUNT(*) FROM meta WHERE key='seed-v1'", [], |r| {
                r.get(0)
            })
            .map_err(err)?;
        if seeded > 0 {
            return Ok(());
        }
        let games: Vec<Value> = serde_json::from_str(projects).map_err(err)?;
        let tags: Vec<Value> = serde_json::from_str(taxonomy).map_err(err)?;
        let tx = self.conn.transaction().map_err(err)?;
        for game in games {
            tx.execute(
                "INSERT OR IGNORE INTO projects VALUES(?1,?2,?3,?4)",
                params![
                    game["id"].as_str(),
                    game["name"].as_str(),
                    game.to_string(),
                    now()
                ],
            )
            .map_err(err)?;
        }
        for tag in tags {
            tx.execute(
                "INSERT OR IGNORE INTO taxonomy VALUES(?1,?2)",
                params![tag["id"].as_str(), tag.to_string()],
            )
            .map_err(err)?;
        }
        {
            let mut stmt = tx
                .prepare("INSERT OR IGNORE INTO files VALUES(?1,?2,?3,?4)")
                .map_err(err)?;
            for line in files.lines().filter(|s| !s.trim().is_empty()) {
                let f: Value = serde_json::from_str(line).map_err(err)?;
                stmt.execute(params![
                    f["project_id"].as_str(),
                    f["kind"].as_str(),
                    f["path"].as_str(),
                    line
                ])
                .map_err(err)?;
            }
        }
        tx.execute("INSERT INTO meta VALUES('seed-v1',?1)", [now()])
            .map_err(err)?;
        tx.commit().map_err(err)
    }
    pub fn values(&self, sql: &str) -> Result<Vec<Value>> {
        let mut s = self.conn.prepare(sql).map_err(err)?;
        let strings = s
            .query_map([], |r| r.get::<_, String>(0))
            .map_err(err)?
            .collect::<std::result::Result<Vec<_>, _>>()
            .map_err(err)?;
        strings
            .into_iter()
            .map(|v| serde_json::from_str(&v).map_err(err))
            .collect()
    }
    pub fn project(&self, id: &str) -> Result<Value> {
        let data: String = self
            .conn
            .query_row("SELECT data FROM projects WHERE id=?1", [id], |r| r.get(0))
            .map_err(err)?;
        serde_json::from_str(&data).map_err(err)
    }
    pub fn save_project(&self, mut project: Value) -> Result<()> {
        let id = project["id"]
            .as_str()
            .ok_or("Project ID required")?
            .to_owned();
        if id.is_empty()
            || id.len() > 120
            || !id
                .bytes()
                .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'-')
        {
            return Err("Use a lowercase project ID with letters, numbers and hyphens.".into());
        }
        let name = project["name"].as_str().unwrap_or("").trim().to_owned();
        if name.is_empty() || name.len() > 200 {
            return Err("A project name of 1–200 characters is required.".into());
        }
        if project.to_string().len() > 2_000_000 {
            return Err("Project metadata exceeds 2 MB.".into());
        }
        for c in project["capabilities"]
            .as_array()
            .ok_or("Capabilities must be a list")?
        {
            let found: i64 = self
                .conn
                .query_row(
                    "SELECT COUNT(*) FROM taxonomy WHERE id=?1",
                    [c["id"].as_str().unwrap_or("")],
                    |r| r.get(0),
                )
                .map_err(err)?;
            if found == 0 {
                return Err("Unknown capability".into());
            }
            if !["planned", "prototype", "implemented", "verified", "reused"]
                .contains(&c["state"].as_str().unwrap_or(""))
            {
                return Err("Invalid capability maturity".into());
            }
            if ["verified", "reused"].contains(&c["state"].as_str().unwrap_or(""))
                && c["evidence"].as_str().unwrap_or("").trim().is_empty()
            {
                return Err("Verified/reused capabilities require evidence.".into());
            }
        }
        if let Some(mechanics) = project["mechanics"].as_array() {
            for m in mechanics {
                if m["name"].as_str().unwrap_or("").trim().is_empty() {
                    return Err("A mechanic needs a name.".into());
                }
                let found: i64 = self
                    .conn
                    .query_row(
                        "SELECT COUNT(*) FROM taxonomy WHERE id=?1",
                        [m["capability"].as_str().unwrap_or("")],
                        |r| r.get(0),
                    )
                    .map_err(err)?;
                if found == 0 {
                    return Err("Mechanic references an unknown capability.".into());
                }
                if !["planned", "prototype", "implemented", "verified", "reused"]
                    .contains(&m["state"].as_str().unwrap_or(""))
                {
                    return Err("Invalid mechanic maturity.".into());
                }
                if ["verified", "reused"].contains(&m["state"].as_str().unwrap_or(""))
                    && m["verification"].as_str().unwrap_or("").trim().is_empty()
                {
                    return Err("Verified mechanics need evidence.".into());
                }
            }
        }
        project["name"] = json!(name);
        self.conn.execute("INSERT INTO projects VALUES(?1,?2,?3,?4) ON CONFLICT(id) DO UPDATE SET name=excluded.name,data=excluded.data,updated_at=excluded.updated_at",params![id,name,project.to_string(),now()]).map_err(err)?;
        Ok(())
    }
    pub fn files(&self, id: &str, kind: &str, query: &str) -> Result<Vec<Value>> {
        let mut s=self.conn.prepare("SELECT data FROM files WHERE project_id=?1 AND kind=?2 AND instr(lower(path),lower(?3))>0 ORDER BY path LIMIT 100").map_err(err)?;
        let rows = s
            .query_map(params![id, kind, query], |r| r.get::<_, String>(0))
            .map_err(err)?
            .collect::<std::result::Result<Vec<_>, _>>()
            .map_err(err)?;
        rows.into_iter()
            .map(|r| serde_json::from_str(&r).map_err(err))
            .collect()
    }
    pub fn media(&self, project_id: &str) -> Result<Vec<Media>> {
        let mut s = self
            .conn
            .prepare("SELECT data FROM media WHERE project_id=?1")
            .map_err(err)?;
        let rows = s
            .query_map([project_id], |r| r.get::<_, String>(0))
            .map_err(err)?
            .collect::<std::result::Result<Vec<_>, _>>()
            .map_err(err)?;
        let mut result: Vec<Media> = rows
            .into_iter()
            .map(|r| serde_json::from_str(&r).map_err(err))
            .collect::<Result<_>>()?;
        result.sort_by_key(|m| (m.sort_order, m.created_at.clone()));
        Ok(result)
    }
    pub fn import_media(&self, project_id: &str, path: &str, kind: &str) -> Result<Media> {
        self.project(project_id)?;
        let src = Path::new(path).canonicalize().map_err(err)?;
        let ext = src
            .extension()
            .and_then(|x| x.to_str())
            .unwrap_or("")
            .to_lowercase();
        let allowed = match kind {
            "screenshot" => vec!["png", "jpg", "jpeg", "webp"],
            "video" | "trailer" => vec!["mp4", "webm", "mov"],
            _ => return Err("Unknown media type".into()),
        };
        if !allowed.contains(&ext.as_str()) {
            return Err("Choose a supported image or video format.".into());
        }
        let metadata = fs::metadata(&src).map_err(err)?;
        if !metadata.is_file() || metadata.len() == 0 || metadata.len() > 8 * 1024 * 1024 * 1024 {
            return Err("Media must be a nonempty file smaller than 8 GiB.".into());
        }
        let id = uuid::Uuid::new_v4().to_string();
        let staging = self.root.join("media").join(format!("{id}.part"));
        let copy_result = (|| -> Result<String> {
            let mut input = fs::File::open(&src).map_err(err)?;
            let mut output = fs::File::create(&staging).map_err(err)?;
            let mut hasher = Sha256::new();
            let mut buffer = vec![0u8; 1024 * 1024];
            loop {
                let n = input.read(&mut buffer).map_err(err)?;
                if n == 0 {
                    break;
                }
                output.write_all(&buffer[..n]).map_err(err)?;
                hasher.update(&buffer[..n]);
            }
            output.sync_all().map_err(err)?;
            Ok(format!("{:x}", hasher.finalize()))
        })();
        let hash = match copy_result {
            Ok(h) => h,
            Err(e) => {
                let _ = fs::remove_file(&staging);
                return Err(e);
            }
        };
        let dest = self.root.join("media").join(format!("{hash}.{ext}"));
        if dest.exists() {
            fs::remove_file(&staging).map_err(err)?;
        } else {
            fs::rename(&staging, &dest).map_err(err)?;
        }
        let media = Media {
            id,
            project_id: project_id.into(),
            kind: kind.into(),
            title: src.file_name().unwrap().to_string_lossy().into(),
            caption: String::new(),
            alt_text: String::new(),
            rights: String::new(),
            credit: String::new(),
            status: "draft".into(),
            source_path: src.to_string_lossy().into(),
            stored_path: dest.to_string_lossy().into(),
            sha256: hash,
            created_at: now(),
            approved_at: None,
            sort_order: 0,
            width: None,
            height: None,
            duration_seconds: None,
            curation: "unreviewed".into(),
            content_role: String::new(),
            review_notes: String::new(),
        };
        self.conn
            .execute(
                "INSERT INTO media VALUES(?1,?2,?3)",
                params![
                    media.id,
                    project_id,
                    serde_json::to_string(&media).map_err(err)?
                ],
            )
            .map_err(err)?;
        Ok(media)
    }
    pub fn update_media(&self, edited: Media) -> Result<Media> {
        let raw: String = self
            .conn
            .query_row("SELECT data FROM media WHERE id=?1", [&edited.id], |r| {
                r.get(0)
            })
            .map_err(err)?;
        let mut original: Media = serde_json::from_str(&raw).map_err(err)?;
        if !["draft", "approved", "retired"].contains(&edited.status.as_str()) {
            return Err("Unknown review status".into());
        }
        if !["screenshot", "video", "trailer"].contains(&edited.kind.as_str()) {
            return Err("Unknown media kind".into());
        }
        if (original.kind == "screenshot") != (edited.kind == "screenshot") {
            return Err("An image cannot be reclassified as video.".into());
        }
        if edited.status == "approved"
            && (edited.title.trim().is_empty()
                || edited.caption.trim().is_empty()
                || edited.rights.trim().is_empty()
                || (edited.kind == "screenshot" && edited.alt_text.trim().is_empty()))
        {
            return Err("Approval needs a title, caption, rights note, and image alt text.".into());
        }
        original.title = edited.title;
        original.caption = edited.caption;
        original.alt_text = edited.alt_text;
        original.rights = edited.rights;
        original.credit = edited.credit;
        original.kind = edited.kind;
        original.sort_order = edited.sort_order;
        if !["", "unreviewed", "selected", "reference"].contains(&edited.curation.as_str()) {
            return Err("Unknown editorial selection status".into());
        }
        original.curation = edited.curation;
        original.content_role = edited.content_role;
        original.review_notes = edited.review_notes;
        original.width = edited.width;
        original.height = edited.height;
        original.duration_seconds = edited
            .duration_seconds
            .filter(|d| d.is_finite() && *d >= 0.0);
        original.approved_at = if edited.status == "approved" {
            Some(now())
        } else {
            None
        };
        original.status = edited.status;
        self.conn
            .execute(
                "UPDATE media SET data=?1 WHERE id=?2",
                params![serde_json::to_string(&original).map_err(err)?, original.id],
            )
            .map_err(err)?;
        Ok(original)
    }
    pub fn export(&self, id: &str, parent: &str) -> Result<String> {
        let project = self.project(id)?;
        let media: Vec<Media> = self
            .media(id)?
            .into_iter()
            .filter(|m| m.status == "approved")
            .collect();
        if media.is_empty() {
            return Err("Approve at least one media item before exporting a press kit.".into());
        }
        let base = Path::new(parent).canonicalize().map_err(err)?;
        let dest = base.join(format!("{}-presskit-{}", id, uuid::Uuid::new_v4()));
        fs::create_dir(&dest).map_err(err)?;
        let export_result = (|| -> Result<()> {
            let mut manifest = Vec::new();
            for (i, m) in media.iter().enumerate() {
                let src = Path::new(&m.stored_path).canonicalize().map_err(err)?;
                if !src.starts_with(self.root.join("media").canonicalize().map_err(err)?) {
                    return Err("Media is outside managed storage".into());
                }
                let name = format!(
                    "{:02}-{}.{}",
                    i + 1,
                    m.kind,
                    src.extension().unwrap().to_string_lossy()
                );
                let target = dest.join(&name);
                fs::copy(&src, &target).map_err(err)?;
                let mut input = fs::File::open(&target).map_err(err)?;
                let mut hasher = Sha256::new();
                let mut buf = vec![0u8; 1024 * 1024];
                loop {
                    let n = input.read(&mut buf).map_err(err)?;
                    if n == 0 {
                        break;
                    }
                    hasher.update(&buf[..n]);
                }
                if format!("{:x}", hasher.finalize()) != m.sha256 {
                    return Err("Media hash mismatch; export stopped.".into());
                }
                manifest.push(json!({"file":name,"title":m.title,"caption":m.caption,"alt_text":m.alt_text,"rights":m.rights,"credit":m.credit,"sha256":m.sha256,"approved_at":m.approved_at,"width":m.width,"height":m.height,"duration_seconds":m.duration_seconds}));
            }
            // Deliberately exclude local source paths, private engineering notes and audit data.
            let mut marketing = project["marketing"].clone();
            if let Some(map) = marketing.as_object_mut() {
                map.remove("notes");
            }
            let public = json!({"name":project["name"],"marketing":marketing,"media":manifest,"exported_at":now(),"published":false});
            fs::write(
                dest.join("press-kit.json"),
                serde_json::to_string_pretty(&public).map_err(err)?,
            )
            .map_err(err)?;
            fs::write(
                dest.join("README.txt"),
                format!(
                    "{}\n\n{}\n\n{}\n\nCredits: {}\n",
                    project["name"].as_str().unwrap_or(""),
                    project["marketing"]["tagline"].as_str().unwrap_or(""),
                    project["marketing"]["pitch"].as_str().unwrap_or(""),
                    project["marketing"]["credits"].as_str().unwrap_or("")
                ),
            )
            .map_err(err)?;
            Ok(())
        })();
        if let Err(e) = export_result {
            fs::write(dest.join("EXPORT_INCOMPLETE.txt"), &e).map_err(err)?;
            return Err(format!(
                "{e}. Incomplete output retained at {}",
                dest.display()
            ));
        }
        Ok(dest.to_string_lossy().into())
    }
    pub fn backup(&self, parent: &str) -> Result<String> {
        let dest = Path::new(parent)
            .canonicalize()
            .map_err(err)?
            .join(format!("gamecore-backup-{}", uuid::Uuid::new_v4()));
        fs::create_dir(&dest).map_err(err)?;
        self.conn
            .backup(
                rusqlite::DatabaseName::Main,
                dest.join("catalog.sqlite3"),
                None,
            )
            .map_err(err)?;
        fs::create_dir(dest.join("media")).map_err(err)?;
        for entry in fs::read_dir(self.root.join("media")).map_err(err)? {
            let p = entry.map_err(err)?.path();
            if p.is_file() && p.extension().and_then(|s| s.to_str()) != Some("part") {
                fs::copy(&p, dest.join("media").join(p.file_name().unwrap())).map_err(err)?;
            }
        }
        fs::write(dest.join("RESTORE.txt"),"Close GameCore. Preserve the current app-data directory. Copy catalog.sqlite3 and media into the replacement directory. Media paths are rebased on startup. This backup contains private catalog metadata.").map_err(err)?;
        Ok(dest.to_string_lossy().into())
    }
    pub fn rebase_media(&self) -> Result<()> {
        for v in self.values("SELECT data FROM media")? {
            let mut m: Media = serde_json::from_value(v).map_err(err)?;
            if let Some(name) = Path::new(&m.stored_path).file_name() {
                m.stored_path = self.root.join("media").join(name).to_string_lossy().into();
                self.conn
                    .execute(
                        "UPDATE media SET data=?1 WHERE id=?2",
                        params![serde_json::to_string(&m).map_err(err)?, m.id],
                    )
                    .map_err(err)?;
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn fixture() -> (tempfile::TempDir, Store) {
        let d = tempfile::tempdir().unwrap();
        let mut s = Store::open(d.path().join("library")).unwrap();
        s.seed(r#"[{"id":"test","name":"Test","capabilities":[],"marketing":{"pitch":"Public copy"},"limitations":"PRIVATE"}]"#,"[]","").unwrap();
        (d, s)
    }
    #[test]
    fn seed_never_overwrites_edits_and_reopens() {
        let (d, mut s) = fixture();
        let mut p = s.project("test").unwrap();
        p["name"] = json!("Edited");
        s.save_project(p).unwrap();
        s.seed(r#"[{"id":"test","name":"Reset"}]"#, "[]", "")
            .unwrap();
        drop(s);
        let s = Store::open(d.path().join("library")).unwrap();
        assert_eq!(s.project("test").unwrap()["name"], "Edited");
    }
    #[test]
    fn media_copy_approval_export_and_backup() {
        let (d, s) = fixture();
        let src = d.path().join("image.png");
        fs::write(&src, b"sample image bytes").unwrap();
        let m = s
            .import_media("test", src.to_str().unwrap(), "screenshot")
            .unwrap();
        assert!(src.exists());
        assert_eq!(fs::read(&m.stored_path).unwrap(), b"sample image bytes");
        assert!(s.export("test", d.path().to_str().unwrap()).is_err());
        let mut approved = m;
        approved.status = "approved".into();
        assert!(s.update_media(approved.clone()).is_err());
        approved.title = "Scene".into();
        approved.caption = "Game view".into();
        approved.alt_text = "An arena".into();
        approved.rights = "Original".into();
        approved.stored_path = "C:/not-allowed".into();
        let saved = s.update_media(approved).unwrap();
        assert_ne!(saved.stored_path, "C:/not-allowed");
        let dest = s.export("test", d.path().to_str().unwrap()).unwrap();
        let manifest = fs::read_to_string(Path::new(&dest).join("press-kit.json")).unwrap();
        assert!(!manifest.contains("PRIVATE"));
        assert!(!manifest.contains("source_path"));
        let backup = s.backup(d.path().to_str().unwrap()).unwrap();
        let restored = Store::open(PathBuf::from(backup)).unwrap();
        restored.rebase_media().unwrap();
        assert!(Path::new(&restored.media("test").unwrap()[0].stored_path).exists());
    }
    #[test]
    fn foreign_project_and_bad_media_rejected() {
        let (d, s) = fixture();
        let src = d.path().join("payload.html");
        fs::write(&src, b"bad").unwrap();
        assert!(s
            .import_media("test", src.to_str().unwrap(), "screenshot")
            .is_err());
        assert!(s
            .import_media("missing", src.to_str().unwrap(), "video")
            .is_err());
    }
    #[test]
    fn corrupt_media_blocks_presskit() {
        let (d, s) = fixture();
        let src = d.path().join("video.mp4");
        fs::write(&src, b"clip").unwrap();
        let mut m = s
            .import_media("test", src.to_str().unwrap(), "video")
            .unwrap();
        m.status = "approved".into();
        m.title = "Clip".into();
        m.caption = "Gameplay".into();
        m.rights = "Original".into();
        let m = s.update_media(m).unwrap();
        fs::write(&m.stored_path, b"changed").unwrap();
        assert!(s.export("test", d.path().to_str().unwrap()).is_err());
    }
}
