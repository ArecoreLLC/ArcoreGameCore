//! Read-only discovery across canonical catalogs. Never a second installation registry.
use serde_json::{json, Value};
use std::collections::HashMap;
use std::sync::OnceLock;

pub fn reusable() -> &'static Value {
    static DATA: OnceLock<Value> = OnceLock::new();
    DATA.get_or_init(|| serde_json::from_str(include_str!("../../../shared/reusable-modules.json")).expect("validated reuse registry"))
}

struct Entry { key: String, summary: Value, source: Value, text: String }
struct Index { entries: Vec<Entry>, by_key: HashMap<String, usize> }
impl Index {
    fn new(procedures: &Value, portable: &Value) -> Self {
        let mut entries = Vec::new();
        for (catalog, rows) in [("procedures", &procedures["entries"]), ("portable", &portable["modules"])] {
            for row in rows.as_array().into_iter().flatten() {
                let id = row["id"].as_str().unwrap_or_default();
                let key = format!("{catalog}:{id}");
                let title = if catalog == "procedures" { &row["name"] } else { &row["description"] };
                let state = if catalog == "procedures" { &row["status"] } else { &row["maturity"] };
                let guide = if catalog == "procedures" { &row["guide"] } else { &row["documentation"] };
                let engine = if catalog == "procedures" { row["engine"].as_str().unwrap_or("") } else if row["source"].as_str().unwrap_or("").starts_with("3d/unreal/") {"Unreal C++"} else { "portable-cpp" };
                let dimension = if catalog == "procedures" { row["dimension"].as_str().unwrap_or("") } else { "any" };
                let languages = if catalog == "procedures" { row["languages"].clone() } else { json!([row["language"]]) };
                let capabilities = row.get("capability_ids").cloned().unwrap_or(json!([]));
                let reuse = if row["disposition"]=="legacy-source" {"legacy"} else if row["status"]=="candidate" {"game-specific"} else {"reusable"};
                let summary = json!({"key":key,"id":id,"catalog":catalog,"name":title,"state":state,
                    "engine":engine,"dimension":dimension,"guide":guide,"languages":languages,"reuse":reuse,
                    "capability_ids":capabilities,"source_project_ids":row.get("source_project_ids").cloned().unwrap_or(json!([]))});
                let mut text = format!("{id} {} {engine} {dimension}", title.as_str().unwrap_or(""));
                for field in ["tags", "aliases", "languages", "capability_ids"] {
                    for term in row[field].as_array().into_iter().flatten().filter_map(Value::as_str) {
                        text.push(' '); text.push_str(term);
                    }
                }
                if catalog=="portable" {text.push_str(" cpp c++");}
                entries.push(Entry { key, summary, source:row.clone(), text:text.to_lowercase() });
            }
        }
        entries.sort_by(|a,b|a.key.cmp(&b.key));
        let by_key = entries.iter().enumerate().map(|(i,e)|(e.key.clone(),i)).collect();
        Self {entries,by_key}
    }

    fn search(&self, args: &Value) -> Result<Value,String> {
        for field in ["query","key","catalog","state","engine","dimension","language","capability","reuse"] {
            if args.get(field).is_some_and(|v| !v.is_string()) {return Err(format!("{field} must be a string"));}
        }
        if args.get("details").is_some_and(|v| !v.is_boolean()) {return Err("details must be boolean".into());}
        let number = |name:&str,default:u64| -> Result<usize,String> {
            let n = match args.get(name) {None=>default,Some(v)=>v.as_u64().ok_or_else(||format!("{name} must be a nonnegative integer"))?};
            usize::try_from(n).map_err(|_|format!("{name} too large"))
        };
        let limit = number("limit",20)?;
        let offset = number("offset",0)?;
        if !(1..=100).contains(&limit) {return Err("limit must be 1..100".into());}
        if let Some(catalog) = args["catalog"].as_str() {
            if !["procedures","portable"].contains(&catalog) {return Err("catalog must be procedures or portable".into());}
        }
        let query = args["query"].as_str().unwrap_or("").to_lowercase();
        let terms:Vec<&str> = query.split_whitespace().collect();
        let candidates:Vec<usize> = match args["key"].as_str() {
            Some(key)=>self.by_key.get(key).copied().into_iter().collect(),
            None=>(0..self.entries.len()).collect()
        };
        let matched:Vec<&Entry> = candidates.into_iter().map(|i|&self.entries[i]).filter(|entry| {
            ["catalog","state","engine","dimension","reuse"].iter().all(|field| args[*field].as_str().map_or(true,|value|entry.summary[*field].as_str()==Some(value)))
                && [("language","languages"),("capability","capability_ids")].iter().all(|(arg,field)|args[*arg].as_str().map_or(true,|value|entry.summary[*field].as_array().is_some_and(|values|values.iter().any(|v|v.as_str()==Some(value)))))
                && terms.iter().all(|term|entry.text.contains(term))
        }).collect();
        let entries:Vec<Value> = matched.iter().skip(offset).take(limit).map(|entry| {
            let mut result=entry.summary.clone();
            if args["details"].as_bool().unwrap_or(false) {result["source_entry"]=entry.source.clone();}
            result
        }).collect();
        let next = offset.saturating_add(entries.len());
        Ok(json!({"total":matched.len(),"offset":offset,"limit":limit,"next_offset":if next<matched.len(){Some(next)}else{None},
            "entries":entries,"capabilities":self.entries.iter().flat_map(|e|e.summary["capability_ids"].as_array().into_iter().flatten().filter_map(Value::as_str)).collect::<std::collections::BTreeSet<_>>(),"specialization_policy":"shared/module-specialization.md",
            "guide":"shared/module-discovery.md","hub_version":env!("CARGO_PKG_VERSION"),
            "snapshot":"embedded at hub build; rebuild/restart after canonical catalog changes"}))
    }
}

pub fn search(args: &Value) -> Result<Value,String> {
    static INDEX: OnceLock<Index> = OnceLock::new();
    INDEX.get_or_init(|| Index::new(reusable(), &serde_json::from_str(include_str!("../../../shared/modules.json")).expect("validated portable registry"))).search(args)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn discovers_both_catalogs_and_details() {
        let result=search(&json!({"key":"procedures:reef-clearance","details":true})).unwrap();
        assert_eq!(result["total"],1);
        assert_eq!(result["entries"][0]["source_entry"]["status"],"extracted");
        assert_eq!(search(&json!({"key":"portable:buoyancy"})).unwrap()["total"],1);
        assert_eq!(search(&json!({"key":"missing"})).unwrap()["total"],0);
    }
    #[test]
    fn filtered_paging_and_invalid_inputs() {
        let a=search(&json!({"catalog":"procedures","state":"extracted","limit":1})).unwrap();
        let b=search(&json!({"catalog":"procedures","state":"extracted","limit":1,"offset":1})).unwrap();
        assert_ne!(a["entries"][0]["key"],b["entries"][0]["key"]);
        assert_eq!(a["next_offset"],1);
        assert!(a["entries"][0].get("source_entry").is_none());
        assert_eq!(search(&json!({"offset":999999})).unwrap()["entries"],json!([]));
        for args in [json!({"limit":0}),json!({"limit":101}),json!({"offset":-1}),json!({"query":1}),json!({"catalog":"wrong"}),json!({"details":"true"})] {
            assert!(search(&args).is_err());
        }
    }
    #[test]
    fn language_and_existing_capability_links() {
        for language in ["cpp","csharp","gdscript","python"] {
            let result=search(&json!({"language":language})).unwrap();
            assert!(result["total"].as_u64().unwrap()>0,"{language}");
            for row in result["entries"].as_array().unwrap() {assert!(row["languages"].as_array().unwrap().contains(&json!(language)));}
        }
        let result=search(&json!({"capability":"cap-terrain-height-sampling"})).unwrap();
        assert!(result["entries"].as_array().unwrap().iter().any(|v|v["key"]=="procedures:reef-clearance"));
    }
    #[test]
    fn alternate_catalog_scale_and_token_matching() {
        let rows:Vec<Value>=(0..10000).map(|i|json!({"id":format!("entry-{i:05}"),"name":"Terrain clearance","status":"extracted","tags":["underwater"],"engine":"Godot 4","dimension":"3d"})).collect();
        let start=std::time::Instant::now();
        let index=Index::new(&json!({"entries":rows}),&json!({"modules":[]}));
        let build=start.elapsed();let start=std::time::Instant::now();
        let result=index.search(&json!({"query":"UNDERWATER terrain","limit":20})).unwrap();
        assert_eq!(result["total"],10000);assert_eq!(result["entries"].as_array().unwrap().len(),20);
        assert_eq!(index.search(&json!({"key":"procedures:entry-09999"})).unwrap()["total"],1);
        eprintln!("MODULE_SEARCH_SCALE entries=10000 build_ms={} query_us={}",build.as_millis(),start.elapsed().as_micros());
    }
}
