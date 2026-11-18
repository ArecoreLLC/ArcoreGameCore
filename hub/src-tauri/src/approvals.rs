//! Approval decision history for the hub's Approvals inbox.
//!
//! Each source keeps owning its own state: music records stay in `music_design`, media
//! approval in `media`. This table only records who-decided-what-when so the inbox can
//! show "changes requested" and keep an audit trail. Entries are append-only.
use crate::store::{Result, Store};
use rusqlite::params;
use serde_json::{json, Value};

pub const KINDS: &[&str] = &["music_direction", "music_take", "media"];
/// `reopened` puts a decided item back in the queue (undo / reopen); history stays append-only.
pub const DECISIONS: &[&str] = &["approved", "changes_requested", "rejected", "reopened"];
const MAX_NOTE: usize = 2000;
const MAX_ID: usize = 200;

fn err(e: impl std::fmt::Display) -> String {
    e.to_string()
}

fn text<'a>(entry: &'a Value, key: &str) -> &'a str {
    entry[key].as_str().unwrap_or("").trim()
}

pub fn validate(entry: &Value) -> Result<()> {
    let kind = text(entry, "kind");
    if !KINDS.contains(&kind) {
        return Err(format!("Unknown approval kind '{kind}'"));
    }
    let decision = text(entry, "decision");
    if !DECISIONS.contains(&decision) {
        return Err(format!("Unknown approval decision '{decision}'"));
    }
    for key in ["subject_id", "item_id"] {
        let v = text(entry, key);
        if v.is_empty() || v.len() > MAX_ID {
            return Err(format!("Approval {key} is required (at most {MAX_ID} characters)"));
        }
    }
    let note = text(entry, "note");
    if note.chars().count() > MAX_NOTE {
        return Err(format!("Approval notes are limited to {MAX_NOTE} characters"));
    }
    if decision == "changes_requested" && note.is_empty() {
        return Err("Say what needs to change when requesting changes".into());
    }
    Ok(())
}

impl Store {
    fn ensure_approval_table(&self) -> Result<()> {
        self.conn
            .execute_batch(
                "CREATE TABLE IF NOT EXISTS approval_history(
                    id TEXT PRIMARY KEY, kind TEXT NOT NULL, subject_id TEXT NOT NULL,
                    item_id TEXT NOT NULL, decided_at TEXT NOT NULL, data TEXT NOT NULL);
                 CREATE INDEX IF NOT EXISTS approval_item ON approval_history(kind,item_id,decided_at);",
            )
            .map_err(err)
    }

    pub fn record_approval(&self, entry: Value) -> Result<Value> {
        validate(&entry)?;
        self.ensure_approval_table()?;
        let saved = json!({
            "id": uuid::Uuid::new_v4().to_string(),
            "kind": text(&entry, "kind"),
            "subject_id": text(&entry, "subject_id"),
            "item_id": text(&entry, "item_id"),
            "item_label": text(&entry, "item_label"),
            "decision": text(&entry, "decision"),
            "note": text(&entry, "note"),
            "decided_at": chrono::Utc::now().to_rfc3339(),
        });
        self.conn
            .execute(
                "INSERT INTO approval_history(id,kind,subject_id,item_id,decided_at,data) VALUES(?1,?2,?3,?4,?5,?6)",
                params![
                    saved["id"].as_str(),
                    saved["kind"].as_str(),
                    saved["subject_id"].as_str(),
                    saved["item_id"].as_str(),
                    saved["decided_at"].as_str(),
                    saved.to_string()
                ],
            )
            .map_err(err)?;
        Ok(saved)
    }

    /// Newest first.
    pub fn approval_history(&self, limit: usize) -> Result<Vec<Value>> {
        self.ensure_approval_table()?;
        let mut stmt = self
            .conn
            .prepare("SELECT data FROM approval_history ORDER BY decided_at DESC, rowid DESC LIMIT ?1")
            .map_err(err)?;
        let rows = stmt
            .query_map([limit.clamp(1, 5000) as i64], |r| r.get::<_, String>(0))
            .map_err(err)?;
        rows.map(|r| {
            r.map_err(err)
                .and_then(|s| serde_json::from_str(&s).map_err(err))
        })
        .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn store() -> (tempfile::TempDir, Store) {
        let dir = tempfile::tempdir().unwrap();
        let s = Store::open(dir.path().to_path_buf()).unwrap();
        (dir, s)
    }

    #[test]
    fn records_and_lists_newest_first_and_survives_reopen() {
        let (dir, s) = store();
        s.record_approval(json!({"kind":"media","subject_id":"g","item_id":"m1","decision":"approved"}))
            .unwrap();
        let second = s
            .record_approval(json!({"kind":"music_take","subject_id":"g","item_id":"g-A","decision":"changes_requested","note":"Loop seam clicks"}))
            .unwrap();
        assert!(second["id"].as_str().unwrap().len() > 10);
        drop(s);
        let s = Store::open(dir.path().to_path_buf()).unwrap();
        let rows = s.approval_history(10).unwrap();
        assert_eq!(rows.len(), 2);
        assert_eq!(rows[0]["item_id"], "g-A");
        assert_eq!(rows[0]["note"], "Loop seam clicks");
        assert_eq!(rows[1]["decision"], "approved");
    }

    #[test]
    fn rejects_invalid_entries() {
        let (_dir, s) = store();
        for bad in [
            json!({"kind":"nope","subject_id":"g","item_id":"i","decision":"approved"}),
            json!({"kind":"media","subject_id":"g","item_id":"i","decision":"maybe"}),
            json!({"kind":"media","subject_id":"","item_id":"i","decision":"approved"}),
            json!({"kind":"media","subject_id":"g","item_id":"i","decision":"changes_requested"}),
            json!({"kind":"media","subject_id":"g","item_id":"i","decision":"rejected","note":"x".repeat(2001)}),
        ] {
            assert!(s.record_approval(bad).is_err());
        }
        assert!(s.approval_history(10).unwrap().is_empty());
    }
}
