use crate::store::{Result, Store};
use rusqlite::{params, OptionalExtension};
use serde_json::{json, Value};
use std::collections::{HashMap, HashSet};

fn text<'a>(v: &'a Value, key: &str) -> Result<&'a str> {
    v[key].as_str().ok_or_else(|| format!("Missing {key}"))
}
fn ids(v: &Value) -> Result<Vec<String>> {
    v.as_array()
        .ok_or("Expected a list")?
        .iter()
        .map(|x| x.as_str().map(str::to_owned).ok_or("Expected an ID".into()))
        .collect()
}
fn accepted(v: &Value) -> bool {
    matches!(v["state"].as_str(), Some("verified" | "reused"))
}

impl Store {
    pub fn seed_roadmap(&mut self, source: &str) -> Result<()> {
        let plan: Value = serde_json::from_str(source).map_err(|e| e.to_string())?;
        let projects = plan["projects"]
            .as_array()
            .ok_or("Missing roadmap projects")?;
        let tx = self.conn.transaction().map_err(|e| e.to_string())?;
        tx.execute_batch("CREATE TABLE IF NOT EXISTS roadmap(id TEXT PRIMARY KEY, data TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS roadmap_history(id INTEGER PRIMARY KEY, project_id TEXT NOT NULL, data TEXT NOT NULL, saved_at TEXT NOT NULL);").map_err(|e| e.to_string())?;
        if let Some(tags) = plan["added_taxonomy"].as_array() {
            for tag in tags {
                tx.execute("INSERT OR IGNORE INTO taxonomy(id,data) VALUES(?1,?2)",
                    params![text(tag, "id")?, tag.to_string()]).map_err(|e| e.to_string())?;
            }
        }
        for project in projects {
            let mut p = project.clone();
            let mut requirements = json!({});
            for dep in ids(&p["depends_on"])? {
                let donor = projects
                    .iter()
                    .find(|x| x["id"] == dep)
                    .ok_or("Unknown dependency")?;
                let own = ids(&p["capability_ids"])?;
                let shared: Vec<_> = ids(&donor["capability_ids"])?
                    .into_iter()
                    .filter(|id| own.contains(id))
                    .collect();
                requirements[dep] = if shared.is_empty() {
                    donor["first_slice_capabilities"].clone()
                } else {
                    json!(shared)
                };
            }
            if !p["dependency_requirements"].is_object() {
                p["dependency_requirements"] = requirements;
            }
            p["target_progress"] = json!({});
            for id in ids(&p["capability_ids"])? {
                p["target_progress"][id] = json!({"state":"planned","notes":"","revision":"","platform":"","procedure":"","evidence":"","second_consumer":"","reuse_links":[]});
            }
            p["status"] = json!("planned");
            p["notes"] = json!("");
            p["owner"] = json!("");
            p["version"] = json!(0);
            let previous: Option<String> = tx.query_row("SELECT data FROM roadmap WHERE id=?1",
                [text(&p, "id")?], |r| r.get(0)).optional().map_err(|e| e.to_string())?;
            if let Some(previous) = previous {
                let old: Value = serde_json::from_str(&previous).map_err(|e| e.to_string())?;
                if p["feedback_revision"].is_string() && old["feedback_revision"] != p["feedback_revision"] {
                    // Keep a complete pre-update record, including removed targets/dependencies.
                    let timestamp = chrono::Utc::now().to_rfc3339();
                    tx.execute("INSERT INTO roadmap_history(project_id,data,saved_at) VALUES(?1,?2,?3)",
                        params![text(&p, "id")?, previous, timestamp]).map_err(|e| e.to_string())?;
                    for field in ["owner", "notes", "priority", "status"] {
                        if !old[field].is_null() { p[field] = old[field].clone(); }
                    }
                    for target in ids(&p["capability_ids"])? {
                        if old["target_progress"][&target].is_object() {
                            p["target_progress"][&target] = old["target_progress"][&target].clone();
                        }
                    }
                    p["archived_target_progress"] = old["archived_target_progress"].clone();
                    if !p["archived_target_progress"].is_object() { p["archived_target_progress"] = json!({}); }
                    for target in ids(&old["capability_ids"])? {
                        if p["target_progress"][&target].is_null() {
                            p["archived_target_progress"][&target] = old["target_progress"][&target].clone();
                        }
                    }
                    p["previous_dependency_requirements"] = old["dependency_requirements"].clone();
                    p["review_changes"].as_array_mut().ok_or("Missing review changes")?.push(json!(
                        "Prior dependency choices and removed target evidence are preserved in history; review the updated producer milestones before starting work."));
                    if p["status"] == "completed" && p["target_progress"].as_object().unwrap().values().any(|v| !accepted(v)) {
                        p["status"] = json!("active");
                    }
                    let version = old["version"].as_i64().unwrap_or(0) + 1;
                    p["version"] = json!(version);
                    p["updated_at"] = json!(timestamp);
                    tx.execute("UPDATE roadmap SET data=?1,version=?2 WHERE id=?3",
                        params![p.to_string(), version, text(&p, "id")?]).map_err(|e| e.to_string())?;
                }
                continue;
            }
            tx.execute(
                "INSERT OR IGNORE INTO roadmap(id,data,version) VALUES(?1,?2,0)",
                params![text(&p, "id")?, p.to_string()],
            )
            .map_err(|e| e.to_string())?;
        }
        tx.commit().map_err(|e| e.to_string())
    }

    pub fn save_roadmap(&mut self, edit: Value) -> Result<Value> {
        let tx = rusqlite::Transaction::new_unchecked(
            &self.conn,
            rusqlite::TransactionBehavior::Immediate,
        )
        .map_err(|e| e.to_string())?;
        let all = self.values("SELECT data FROM roadmap")?;
        let id = text(&edit, "id")?;
        let original = all
            .iter()
            .find(|p| p["id"] == id)
            .ok_or("Unknown roadmap game")?;
        let version = edit["version"].as_i64().ok_or("Missing edit version")?;
        let priority = edit["priority"]
            .as_u64()
            .filter(|n| *n > 0 && *n <= 999)
            .ok_or("Priority must be 1–999")?;
        let status = text(&edit, "status")?;
        if !["planned", "active", "blocked", "completed", "paused"].contains(&status) {
            return Err("Invalid roadmap status".into());
        }
        let targets = ids(&original["capability_ids"])?;
        let progress = edit["target_progress"]
            .as_object()
            .ok_or("Missing capability progress")?;
        if progress.len() != targets.len() || targets.iter().any(|id| !progress.contains_key(id)) {
            return Err("Capability targets cannot be removed or replaced".into());
        }
        for target in progress.values() {
            let state = text(target, "state")?;
            if ![
                "planned",
                "in_progress",
                "blocked",
                "implemented",
                "verified",
                "reused",
            ]
            .contains(&state)
            {
                return Err("Invalid capability state".into());
            }
            for field in [
                "notes",
                "revision",
                "platform",
                "procedure",
                "evidence",
                "second_consumer",
            ] {
                text(target, field)?;
            }
            if accepted(target) {
                for field in ["revision", "platform", "procedure", "evidence"] {
                    if text(target, field)?.trim().is_empty() {
                        return Err(format!("Verified targets require {field}"));
                    }
                }
            }
            if state == "reused" && text(target, "second_consumer")?.trim().is_empty() {
                return Err("Reused targets require a second consumer".into());
            }
            for link in target["reuse_links"]
                .as_array()
                .ok_or("Missing reuse links")?
            {
                let count: i64 = self
                    .conn
                    .query_row(
                        "SELECT COUNT(*) FROM files WHERE project_id=?1 AND kind=?2 AND path=?3",
                        params![
                            text(link, "project_id")?,
                            text(link, "kind")?,
                            text(link, "path")?
                        ],
                        |r| r.get(0),
                    )
                    .map_err(|e| e.to_string())?;
                if count != 1 {
                    return Err("Reuse reference is not an indexed source or asset".into());
                }
            }
        }
        if status == "completed" && progress.values().any(|p| !accepted(p)) {
            return Err(
                "Complete all capability acceptance records before completing this game".into(),
            );
        }
        let req = edit["dependency_requirements"]
            .as_object()
            .ok_or("Missing dependency requirements")?;
        for (dep, selected) in req {
            if dep == id {
                return Err("A game cannot depend on itself".into());
            }
            let donor = all
                .iter()
                .find(|p| p["id"] == *dep)
                .ok_or("Unknown dependency game")?;
            let selected = ids(selected)?;
            let available = ids(&donor["capability_ids"])?;
            if selected.is_empty()
                || selected.iter().any(|s| !available.contains(s))
                || selected.iter().collect::<HashSet<_>>().len() != selected.len()
            {
                return Err("Choose valid prerequisite capability targets".into());
            }
        }
        let mut graph: HashMap<String, Vec<String>> = HashMap::new();
        for p in &all {
            graph.insert(
                text(p, "id")?.to_string(),
                p["dependency_requirements"]
                    .as_object()
                    .ok_or("Invalid stored dependencies")?
                    .keys()
                    .cloned()
                    .collect(),
            );
        }
        graph.insert(id.to_owned(), req.keys().cloned().collect());
        fn visit(
            id: &str,
            graph: &HashMap<String, Vec<String>>,
            stack: &mut HashSet<String>,
            done: &mut HashSet<String>,
        ) -> Result<()> {
            if done.contains(id) {
                return Ok(());
            }
            if !stack.insert(id.to_owned()) {
                return Err("Dependency cycle detected".into());
            }
            for dep in &graph[id] {
                visit(dep, graph, stack, done)?;
            }
            stack.remove(id);
            done.insert(id.to_owned());
            Ok(())
        }
        visit(id, &graph, &mut HashSet::new(), &mut HashSet::new())?;
        let mut saved = original.clone();
        for field in ["owner", "notes"] {
            text(&edit, field)?;
            saved[field] = edit[field].clone();
        }
        saved["priority"] = json!(priority);
        saved["status"] = json!(status);
        saved["target_progress"] = edit["target_progress"].clone();
        saved["dependency_requirements"] = edit["dependency_requirements"].clone();
        let mut stages = json!({});
        for (dep, targets) in req {
            for target in ids(targets)? {
                let stage = edit["dependency_stages"][dep][&target].as_str().unwrap_or("first_slice");
                if !["first_slice", "later"].contains(&stage) { return Err("Invalid dependency stage".into()); }
                if stages[dep].is_null() { stages[dep] = json!({}); }
                stages[dep][target] = json!(stage);
            }
        }
        saved["dependency_stages"] = stages;
        saved["depends_on"] = json!(req.keys().collect::<Vec<_>>());
        saved["version"] = json!(version + 1);
        saved["updated_at"] = json!(chrono::Utc::now().to_rfc3339());
        let changed = tx
            .execute(
                "UPDATE roadmap SET data=?1,version=version+1 WHERE id=?2 AND version=?3",
                params![saved.to_string(), id, version],
            )
            .map_err(|e| e.to_string())?;
        if changed != 1 {
            return Err("This roadmap changed in another window. Reload before saving.".into());
        }
        tx.execute(
            "INSERT INTO roadmap_history(project_id,data,saved_at) VALUES(?1,?2,?3)",
            params![id, saved.to_string(), text(&saved, "updated_at")?],
        )
        .map_err(|e| e.to_string())?;
        tx.commit().map_err(|e| e.to_string())?;
        Ok(saved)
    }

    pub fn indexed_path(
        &self,
        project_id: &str,
        kind: &str,
        path: &str,
    ) -> Result<std::path::PathBuf> {
        let count: i64 = self
            .conn
            .query_row(
                "SELECT COUNT(*) FROM files WHERE project_id=?1 AND kind=?2 AND path=?3",
                params![project_id, kind, path],
                |r| r.get(0),
            )
            .map_err(|e| e.to_string())?;
        if count != 1 {
            return Err("Unknown indexed file".into());
        }
        let project = self.project(project_id)?;
        let root = std::path::Path::new(text(&project, "path")?)
            .canonicalize()
            .map_err(|e| e.to_string())?;
        let file = root.join(path).canonicalize().map_err(|e| e.to_string())?;
        if !file.starts_with(root) || !file.is_file() {
            return Err("Indexed file is outside its project or unavailable".into());
        }
        Ok(file)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn feedback_upgrade_preserves_work_archives_retired_targets_and_is_idempotent() {
        let d = tempfile::tempdir().unwrap();
        let mut s = Store::open(d.path().join("library")).unwrap();
        s.seed_roadmap(include_str!("../../evidence/roadmap-feedback-2026-11-11/before-capability-roadmap.json")).unwrap();
        let mut old = s.values("SELECT data FROM roadmap WHERE id='clockwork-courier'").unwrap().remove(0);
        old["owner"] = json!("Existing owner");
        old["notes"] = json!("Keep user notes");
        old["priority"] = json!(77);
        old["target_progress"]["cap-suspension-solver"]["state"] = json!("in_progress");
        old["target_progress"]["cap-deterministic-replay-verification"]["notes"] = json!("Retired experiment evidence");
        let stale = s.save_roadmap(old).unwrap();
        let source = include_str!("../../data/capability-roadmap.json");
        s.seed_roadmap(source).unwrap();
        let upgraded = s.values("SELECT data FROM roadmap WHERE id='clockwork-courier'").unwrap().remove(0);
        assert_eq!(upgraded["owner"], "Existing owner");
        assert_eq!(upgraded["notes"], "Keep user notes");
        assert_eq!(upgraded["priority"], 77);
        assert_eq!(upgraded["target_progress"]["cap-suspension-solver"]["state"], "in_progress");
        assert_eq!(upgraded["target_progress"]["cap-frame-rate-resilience"]["state"], "planned");
        assert_eq!(upgraded["archived_target_progress"]["cap-deterministic-replay-verification"]["notes"], "Retired experiment evidence");
        assert!(s.save_roadmap(stale).is_err());
        let count = s.values("SELECT data FROM roadmap_history").unwrap().len();
        s.seed_roadmap(source).unwrap();
        assert_eq!(s.values("SELECT data FROM roadmap_history").unwrap().len(), count);
        assert_eq!(s.values("SELECT data FROM taxonomy").unwrap().len(), 3);
        assert_eq!(s.values("SELECT data FROM roadmap WHERE id='clockwork-courier'").unwrap()[0], upgraded);
        let mut edit = upgraded;
        edit["dependency_requirements"] = json!({"lantern-heist":["cap-spatial-audio"]});
        edit["dependency_stages"] = json!({"lantern-heist":{"cap-spatial-audio":"later"}});
        let saved = s.save_roadmap(edit.clone()).unwrap();
        assert_eq!(saved["dependency_stages"]["lantern-heist"]["cap-spatial-audio"], "later");
        edit["version"] = saved["version"].clone();
        edit["dependency_stages"]["lantern-heist"]["cap-spatial-audio"] = json!("bad-stage");
        assert!(s.save_roadmap(edit).unwrap_err().contains("stage"));
    }
    fn fixture() -> (tempfile::TempDir, Store) {
        let d = tempfile::tempdir().unwrap();
        let mut s = Store::open(d.path().join("library")).unwrap();
        s.seed_roadmap(include_str!("../../data/capability-roadmap.json"))
            .unwrap();
        (d, s)
    }
    #[test]
    fn seed_save_reopen_and_conflict() {
        let (d, mut s) = fixture();
        let mut p = s
            .values("SELECT data FROM roadmap WHERE id='lantern-heist'")
            .unwrap()
            .remove(0);
        let stale = p.clone();
        p["priority"] = json!(42);
        p["notes"] = json!("Keep this");
        s.save_roadmap(p).unwrap();
        assert!(s
            .save_roadmap(stale)
            .unwrap_err()
            .contains("another window"));
        s.seed_roadmap(include_str!("../../data/capability-roadmap.json"))
            .unwrap();
        drop(s);
        let s = Store::open(d.path().join("library")).unwrap();
        assert_eq!(
            s.values("SELECT data FROM roadmap WHERE id='lantern-heist'")
                .unwrap()[0]["notes"],
            "Keep this"
        );
        assert_eq!(
            s.values("SELECT data FROM roadmap_history").unwrap().len(),
            1
        );
    }
    #[test]
    fn expands_seed_without_resetting_existing_progress() {
        let d = tempfile::tempdir().unwrap();
        let mut s = Store::open(d.path().join("library")).unwrap();
        let mut seed: Value =
            serde_json::from_str(include_str!("../../data/capability-roadmap.json")).unwrap();
        seed["projects"].as_array_mut().unwrap().truncate(22);
        s.seed_roadmap(&seed.to_string()).unwrap();
        let mut p = s
            .values("SELECT data FROM roadmap WHERE id='lantern-heist'")
            .unwrap()
            .remove(0);
        p["owner"] = json!("Keep owner");
        s.save_roadmap(p).unwrap();
        s.seed_roadmap(include_str!("../../data/capability-roadmap.json"))
            .unwrap();
        assert_eq!(s.values("SELECT data FROM roadmap").unwrap().len(), 50);
        assert_eq!(
            s.values("SELECT data FROM roadmap WHERE id='lantern-heist'")
                .unwrap()[0]["owner"],
            "Keep owner"
        );
    }
    #[test]
    fn indexed_file_resolution_stays_within_owning_project() {
        let (d, s) = fixture();
        let root = d.path().join("project");
        std::fs::create_dir(&root).unwrap();
        std::fs::write(root.join("code.cpp"), "fixture").unwrap();
        std::fs::write(d.path().join("outside.cpp"), "outside").unwrap();
        s.conn
            .execute(
                "INSERT INTO projects VALUES('donor','Donor',?1,'now')",
                [json!({"id":"donor","path":root}).to_string()],
            )
            .unwrap();
        for path in ["code.cpp", "../outside.cpp"] {
            s.conn
                .execute("INSERT INTO files VALUES('donor','source',?1,'{}')", [path])
                .unwrap();
        }
        assert!(s
            .indexed_path("donor", "source", "code.cpp")
            .unwrap()
            .is_file());
        assert!(s.indexed_path("donor", "source", "missing.cpp").is_err());
        assert!(s.indexed_path("donor", "source", "../outside.cpp").is_err());
    }
    #[test]
    fn evidence_cycles_and_unknown_links_rejected() {
        let (_d, mut s) = fixture();
        let p = s
            .values("SELECT data FROM roadmap WHERE id='lantern-heist'")
            .unwrap()
            .remove(0);
        let cap = p["capability_ids"][0].as_str().unwrap().to_owned();
        let mut edit = p.clone();
        edit["target_progress"][&cap]["state"] = json!("verified");
        assert!(s.save_roadmap(edit.clone()).is_err());
        for f in ["revision", "platform", "procedure", "evidence"] {
            edit["target_progress"][&cap][f] = json!("test evidence");
        }
        edit["target_progress"][&cap]["state"] = json!("reused");
        assert!(s.save_roadmap(edit).is_err());
        let mut edit = p.clone();
        edit["status"] = json!("completed");
        assert!(s.save_roadmap(edit).is_err());
        let mut edit = p.clone();
        edit["dependency_requirements"] = json!({"prism-patrol":["cap-dynamic-path-replanning"]});
        assert!(s.save_roadmap(edit).unwrap_err().contains("cycle"));
        let mut edit = p;
        edit["target_progress"][&cap]["reuse_links"] =
            json!([{"project_id":"missing","kind":"source","path":"no"}]);
        assert!(s.save_roadmap(edit).is_err());
    }
}
