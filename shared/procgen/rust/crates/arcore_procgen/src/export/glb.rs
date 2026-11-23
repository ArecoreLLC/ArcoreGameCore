//! Minimal glTF 2.0 binary (.glb) writer: one node per named mesh, POSITION +
//! NORMAL + u32 indices. Imports in Godot 4 and Unreal (Interchange glTF).

use crate::stages::surface::Mesh;
use serde_json::{json, Value};

const ARRAY_BUFFER: u32 = 34962;
const ELEMENT_ARRAY_BUFFER: u32 = 34963;
const FLOAT: u32 = 5126;
const UNSIGNED_INT: u32 = 5125;

fn pad4(buf: &mut Vec<u8>, byte: u8) {
    while buf.len() % 4 != 0 {
        buf.push(byte);
    }
}

/// Encode named meshes into GLB bytes. Empty meshes are skipped. Output is a
/// pure function of the input (deterministic bytes).
pub fn write_glb(meshes: &[(String, &Mesh)], generator: &str) -> Vec<u8> {
    let mut bin: Vec<u8> = Vec::new();
    let (mut views, mut accessors, mut gl_meshes, mut nodes) = (vec![], vec![], vec![], vec![]);

    for (name, mesh) in meshes.iter().filter(|(_, m)| !m.is_empty()) {
        let mut view = |bytes: &[u8], target: u32, bin: &mut Vec<u8>| -> usize {
            pad4(bin, 0);
            views.push(json!({"buffer": 0, "byteOffset": bin.len(), "byteLength": bytes.len(), "target": target}));
            bin.extend_from_slice(bytes);
            views.len() - 1
        };
        let flat = |v: &[[f32; 3]]| -> Vec<u8> { v.iter().flatten().flat_map(|f| f.to_le_bytes()).collect() };

        let (lo, hi) = mesh.bounds().expect("non-empty mesh has bounds");
        let pv = view(&flat(&mesh.positions), ARRAY_BUFFER, &mut bin);
        accessors.push(json!({"bufferView": pv, "componentType": FLOAT, "count": mesh.positions.len(),
            "type": "VEC3", "min": lo.to_array(), "max": hi.to_array()}));
        let pos_acc = accessors.len() - 1;

        let normals: Vec<[f32; 3]> = mesh
            .normals
            .iter()
            .map(|n| crate::common::math::Vec3::from_array(*n).normalize_or(crate::common::math::Vec3::Y).to_array())
            .collect();
        let nv = view(&flat(&normals), ARRAY_BUFFER, &mut bin);
        accessors.push(json!({"bufferView": nv, "componentType": FLOAT, "count": normals.len(), "type": "VEC3"}));
        let nrm_acc = accessors.len() - 1;

        let idx: Vec<u8> = mesh.indices.iter().flat_map(|i| i.to_le_bytes()).collect();
        let iv = view(&idx, ELEMENT_ARRAY_BUFFER, &mut bin);
        accessors.push(json!({"bufferView": iv, "componentType": UNSIGNED_INT, "count": mesh.indices.len(), "type": "SCALAR"}));
        let idx_acc = accessors.len() - 1;

        gl_meshes.push(json!({"name": name, "primitives": [{
            "attributes": {"POSITION": pos_acc, "NORMAL": nrm_acc}, "indices": idx_acc, "mode": 4}]}));
        nodes.push(json!({"name": name, "mesh": gl_meshes.len() - 1}));
    }
    pad4(&mut bin, 0);

    let node_ids: Vec<usize> = (0..nodes.len()).collect();
    let mut doc: Value = json!({
        "asset": {"version": "2.0", "generator": generator},
        "scene": 0,
        "scenes": [{"nodes": node_ids}],
        "nodes": nodes,
    });
    if !gl_meshes.is_empty() {
        doc["meshes"] = Value::Array(gl_meshes);
        doc["accessors"] = Value::Array(accessors);
        doc["bufferViews"] = Value::Array(views);
        doc["buffers"] = json!([{"byteLength": bin.len()}]);
    }
    let mut json_bytes = serde_json::to_vec(&doc).expect("glTF JSON serializes");
    pad4(&mut json_bytes, b' ');

    let has_bin = !bin.is_empty();
    let total = 12 + 8 + json_bytes.len() + if has_bin { 8 + bin.len() } else { 0 };
    let mut out = Vec::with_capacity(total);
    out.extend_from_slice(&0x4654_6C67u32.to_le_bytes()); // "glTF"
    out.extend_from_slice(&2u32.to_le_bytes());
    out.extend_from_slice(&(total as u32).to_le_bytes());
    out.extend_from_slice(&(json_bytes.len() as u32).to_le_bytes());
    out.extend_from_slice(&0x4E4F_534Au32.to_le_bytes()); // "JSON"
    out.extend_from_slice(&json_bytes);
    if has_bin {
        out.extend_from_slice(&(bin.len() as u32).to_le_bytes());
        out.extend_from_slice(&0x004E_4942u32.to_le_bytes()); // "BIN\0"
        out.extend_from_slice(&bin);
    }
    out
}

/// Parse a GLB header and JSON chunk (used by tests and the CLI self-check).
pub fn read_glb_json(bytes: &[u8]) -> Result<Value, String> {
    let u32_at = |o: usize| -> Result<u32, String> {
        bytes
            .get(o..o + 4)
            .map(|b| u32::from_le_bytes([b[0], b[1], b[2], b[3]]))
            .ok_or_else(|| "truncated glb".to_string())
    };
    if u32_at(0)? != 0x4654_6C67 || u32_at(4)? != 2 {
        return Err("not a glTF 2.0 binary".into());
    }
    if u32_at(8)? as usize != bytes.len() {
        return Err("glb length header mismatch".into());
    }
    let json_len = u32_at(12)? as usize;
    if u32_at(16)? != 0x4E4F_534A {
        return Err("first chunk is not JSON".into());
    }
    let chunk = bytes.get(20..20 + json_len).ok_or("truncated JSON chunk")?;
    serde_json::from_slice(chunk).map_err(|e| e.to_string())
}
