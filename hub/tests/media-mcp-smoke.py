"""Exercise the shipped stdio endpoint against an isolated library and Git repo."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from contextlib import closing

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / "src-tauri/target/release/gamecore-library.exe"
with tempfile.TemporaryDirectory(prefix="gamecore-mcp-") as tmp:
    root = Path(tmp)
    repo = root / "game"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    image = root / "capture.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
    env = {**os.environ, "GAMECORE_DATA_DIR": str(root / "library")}

    def exchange(requests):
        result = subprocess.run([str(EXE), "--mcp"], env=env,
                                input="\n".join(json.dumps(r) for r in requests)+"\n",
                                text=True, capture_output=True, check=True, timeout=30)
        return [json.loads(line) for line in result.stdout.splitlines()]

    initial = exchange([
        {"jsonrpc":"2.0", "id":1, "method":"initialize", "params":{"protocolVersion":"2024-11-05", "capabilities":{}, "clientInfo":{"name":"smoke", "version":"1"}}},
        {"jsonrpc":"2.0", "method":"notifications/initialized"},
        {"jsonrpc":"2.0", "id":2, "method":"tools/list"},
    ])
    assert len(initial) == 2
    assert initial[0]["result"]["serverInfo"]["name"] == "gamecore-hub"
    assert {t["name"] for t in initial[1]["result"]["tools"]} == {"list_projects", "list_media", "import_media", "video_production", "animation_production", "animation_pipeline"}
    # Seed a generic project only in this isolated library.
    import sqlite3
    with closing(sqlite3.connect(root / "library/catalog.sqlite3")) as db:
        db.execute("INSERT INTO projects VALUES(?,?,?,?)", ("fixture", "Fixture", json.dumps({"id":"fixture", "name":"Fixture", "path":str(repo)}), "fixture"))
        db.commit()
    def call(i, name, args):
        return {"jsonrpc":"2.0", "id":i, "method":"tools/call", "params":{"name":name, "arguments":args}}
    results = exchange([
        call(3, "import_media", {"project_id":"fixture", "path":str(image), "kind":"screenshot"}),
        call(4, "list_media", {"project_id":"fixture"}),
        call(5, "import_media", {"project_id":"missing", "path":str(image), "kind":"screenshot"}),
    ])
    media = json.loads(results[0]["result"]["content"][0]["text"])
    assert media["iteration"]["status"] == "no-commit"
    assert media["iteration"]["basis"] == "import"
    assert media["status"] == "draft"
    assert Path(media["stored_path"]).read_bytes() == image.read_bytes()
    assert json.loads(results[1]["result"]["content"][0]["text"])[0]["iteration"] == media["iteration"]
    assert results[2]["result"]["isError"] is True
    print("PASS: stdio initialize/discovery, shared import/list tags, original bytes, draft status, error handling")
