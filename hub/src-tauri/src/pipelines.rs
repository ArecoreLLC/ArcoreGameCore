use crate::store::{Result, Store};
use rusqlite::params;
use serde_json::{json, Value};

fn text<'a>(v: &'a Value, key: &str) -> Result<&'a str> {
    v[key].as_str().ok_or_else(|| format!("Missing {key}"))
}

pub fn valid_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 80
        && id
            .chars()
            .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-')
}

impl Store {
    pub fn ensure_pipelines_table(&self) -> Result<()> {
        self.conn
            .execute_batch(
                "CREATE TABLE IF NOT EXISTS pipeline_proposals(id TEXT PRIMARY KEY, data TEXT NOT NULL, updated_at TEXT NOT NULL);",
            )
            .map_err(|e| e.to_string())
    }

    pub fn pipeline_proposals(&self) -> Result<Vec<Value>> {
        self.ensure_pipelines_table()?;
        self.values("SELECT data FROM pipeline_proposals ORDER BY updated_at DESC, id ASC")
    }

    pub fn save_pipeline_proposal(&mut self, mut proposal: Value) -> Result<Value> {
        self.ensure_pipelines_table()?;
        let id = text(&proposal, "id")?.trim().to_string();
        if !valid_id(&id) {
            return Err("Proposal id must be lowercase kebab-case (a-z, 0-9, -)".into());
        }
        let title = text(&proposal, "title")?.trim();
        if title.is_empty() {
            return Err("Proposal title is required".into());
        }
        let status = text(&proposal, "status")?;
        if !["proposal", "draft"].contains(&status) {
            return Err("Proposal status must be 'proposal' or 'draft'".into());
        }
        if text(&proposal, "source_component")?.trim().is_empty()
            || text(&proposal, "target_component")?.trim().is_empty()
        {
            return Err("Source and target components are required".into());
        }
        if !proposal["handoffs"].is_array() || !proposal["stages"].is_array() {
            return Err("Handoffs and stages must be lists".into());
        }
        let ts = chrono::Utc::now().to_rfc3339();
        proposal["kind"] = json!("proposal");
        proposal["updated_at"] = json!(ts);
        self.conn
            .execute(
                "INSERT OR REPLACE INTO pipeline_proposals(id, data, updated_at) VALUES(?1, ?2, ?3)",
                params![id, proposal.to_string(), ts],
            )
            .map_err(|e| e.to_string())?;
        Ok(proposal)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn save_and_list_pipeline_proposals() {
        let dir = tempdir().unwrap();
        let mut s = Store::open(dir.path().to_path_buf()).unwrap();
        let err = s
            .save_pipeline_proposal(json!({
                "id": "Bad ID!", "title": "X", "status": "proposal",
                "source_component": "A", "target_component": "B",
                "summary": "S", "handoffs": [], "stages": []
            }))
            .unwrap_err();
        assert!(err.contains("kebab-case"));

        let saved = s
            .save_pipeline_proposal(json!({
                "id": "sfx-batch-pipeline",
                "title": "SFX Batch Pipeline",
                "status": "draft",
                "source_component": "ArcoreSoundCore",
                "target_component": "Unreal 5.8.4",
                "summary": "Batch normalize and import SFX cues.",
                "handoffs": [{"from": "SoundCore", "to": "Unreal", "artifact": "WAV", "contract": "shared/ecosystem.json"}],
                "stages": [{"step": "1. Normalize", "owner": "SoundCore", "tool_or_guide": "tools/sfx.py", "acceptance": "48kHz"}]
            }))
            .unwrap();
        assert_eq!(saved["kind"], "proposal");
        let list = s.pipeline_proposals().unwrap();
        assert_eq!(list.len(), 1);
        assert_eq!(list[0]["id"], "sfx-batch-pipeline");
    }
}
