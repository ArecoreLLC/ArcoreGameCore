"""Unreal Editor Python script: import and verify Sonic-v001 adaptive music stems.

Run via:
  UnrealEditor-Cmd.exe <Project.uproject> -ExecutePythonScript=<path>/unreal_import_adaptive_music.py -unattended -nop4 -nosplash -NullRHI -nosound
"""
import hashlib
import json
from pathlib import Path
import unreal


def main() -> None:
    root = Path(unreal.Paths.project_dir()).resolve()
    manifest_path = root / "Media" / "Provenance" / "Sonic-v001" / "verified-copies.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"Missing verified-copies.json at {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["files"] + manifest["imports"]:
        actual = hashlib.sha256((root / entry["path"]).read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise RuntimeError(f"SHA-256 mismatch for {entry['path']}: {actual} != {entry['sha256']}")

    design_path = root / "Media" / "Audio" / "Sonic-v001" / "Export" / "design.json"
    design = json.loads(design_path.read_text(encoding="utf-8"))
    if design.get("schema") != "arcore-adaptive-v1" or design.get("transition", {}).get("boundary") != "bar":
        raise RuntimeError("Invalid design.json schema or boundary")

    expected_dur = design["bars"] * design["beatsPerBar"] * 60.0 / design["bpm"]
    music_dest = manifest.get("unreal_destination", "/Game/Audio/Music")
    tools = unreal.AssetToolsHelpers.get_asset_tools()

    for entry in manifest["imports"]:
        asset_path = f"{music_dest}/{entry['unreal_name']}"
        task = unreal.AssetImportTask()
        task.filename = str(root / entry["path"])
        task.destination_path = music_dest
        task.destination_name = entry["unreal_name"]
        task.automated = True
        task.replace_existing = True
        task.save = False
        tools.import_asset_tasks([task])
        if not task.imported_object_paths:
            raise RuntimeError(f"Music stem import failed: {entry['path']}")
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        asset.set_editor_property("looping", True)
        asset.set_editor_property("virtualization_mode", unreal.VirtualizationMode.PLAY_WHEN_SILENT)
        unreal.EditorAssetLibrary.save_loaded_asset(asset)
        if not asset.get_editor_property("looping"):
            raise RuntimeError(f"Looping not persisted on {asset_path}")
        if asset.get_editor_property("virtualization_mode") != unreal.VirtualizationMode.PLAY_WHEN_SILENT:
            raise RuntimeError(f"VirtualizationMode not persisted on {asset_path}")
        actual_dur = asset.get_editor_property("duration")
        if abs(actual_dur - expected_dur) >= 0.02:
            raise RuntimeError(f"Duration mismatch on {asset_path}: {actual_dur} vs {expected_dur}")

    unreal.EditorAssetLibrary.save_directory(music_dest)
    unreal.log(
        f"GAMECORE_MUSIC_IMPORT_PASS: {len(manifest['imports'])} stems imported to {music_dest} ({expected_dur:.2f}s loop)"
    )


if __name__ == "__main__":
    main()
