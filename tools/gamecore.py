"""Common Unreal build/automation/smoke runner. No arbitrary manifest commands."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

from check_unreal_automation import validate
from gamecore_modules import ROOT, check_lock, contained, digest, read_json, registry, sync, write_json


def project_config(project):
    manifest = read_json(contained(project, "Config/GameCore.project.json"))
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported project manifest")
    if not re.fullmatch(r"[a-z][a-z0-9-]*", manifest["project_id"]):
        raise ValueError("Invalid project id")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*Editor", manifest["editor_target"]):
        raise ValueError("Invalid Editor target")
    if manifest["platform"] != "Win64":
        raise ValueError("This runner currently supports Win64 only")
    project_file = contained(project, manifest["project_file"])
    if project_file.suffix != ".uproject" or not project_file.is_file():
        raise ValueError("Missing Unreal project")
    automation = manifest["automation"]
    if not re.fullmatch(r"[A-Za-z0-9_.]+", automation["prefix"]) or not automation["required_tests"]:
        raise ValueError("Automation requires a prefix and named tests")
    if any(not name.startswith(automation["prefix"]) for name in automation["required_tests"]):
        raise ValueError("Required tests must match suite prefix")
    smoke = manifest["smoke"]
    if not re.fullmatch(r"/Game/[A-Za-z0-9_/]+", smoke["map"]) or not re.fullmatch(r"[A-Za-z0-9]+", smoke["flag"]):
        raise ValueError("Invalid smoke map/flag")
    if not smoke["pass_marker"] or not smoke["fail_marker"]:
        raise ValueError("Smoke markers are required")
    if "game_mode" in smoke and not re.fullmatch(r"/Script/[A-Za-z][A-Za-z0-9]*\.[A-Za-z][A-Za-z0-9]*", smoke["game_mode"]):
        raise ValueError("Invalid smoke game_mode; expected a native /Script/Module.Class")
    return manifest


def engine_tools(engine, version):
    actual = read_json(engine / "Engine/Build/Build.version")
    actual_version = '.'.join(str(actual[k]) for k in ("MajorVersion", "MinorVersion", "PatchVersion"))
    if actual_version != version:
        raise ValueError(f"Engine mismatch: requested {version}, found {actual_version}")
    tools = {
        "dotnet": engine / "Engine/Binaries/ThirdParty/DotNet/10.0/win-x64/dotnet.exe",
        "ubt": engine / "Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll",
        "editor": engine / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe",
    }
    for path in tools.values():
        if not path.is_file():
            raise ValueError(f"Missing engine tool: {path}")
    return tools, actual


def commands(project, manifest, tools, output, action, rendered=False):
    uproject = str(contained(project, manifest["project_file"]))
    if action == "build":
        return [str(tools["dotnet"]), str(tools["ubt"]), manifest["editor_target"], "Win64", "Development",
                f"-Project={uproject}", "-WaitMutex", "-NoHotReloadFromIDE", f"-Log={output / 'engine.log'}"]
    base = [str(tools["editor"]), uproject]
    common = ["-unattended", "-nosound", "-Multiprocess", f"-abslog={output / 'engine.log'}"]
    if action == "automation":
        return base + common + ["-NullRHI", f"-ExecCmds=Automation RunTests {manifest['automation']['prefix']}",
                                "-TestExit=Automation Test Queue Empty", f"-ReportExportPath={output / 'report'}"]
    smoke = manifest["smoke"]
    display = ["-RenderOffscreen", "-windowed", "-ResX=1280", "-ResY=800"] if rendered else ["-NullRHI"]
    map_url = smoke["map"]
    if smoke.get("game_mode"):
        map_url += "?game=" + smoke["game_mode"]
    return base + [map_url, "-game", f"-{smoke['flag']}"] + common + display


def verify_result(manifest, output, action):
    if action == "automation":
        result = validate(read_json(output / "report/index.json"), manifest["automation"]["prefix"])
        missing = set(manifest["automation"]["required_tests"]) - set(result["tests"])
        if missing:
            raise ValueError(f"Required automation tests missing: {sorted(missing)}")
        return result
    if action == "smoke":
        log = (output / "engine.log").read_text(encoding="utf-8-sig", errors="replace")
        smoke = manifest["smoke"]
        if smoke["pass_marker"] not in log or smoke["fail_marker"] in log:
            raise ValueError("Smoke log lacks a pass marker or contains a failure marker")
    return {"status": "passed"}


def snapshot(project):
    files = {}
    for folder in ("Source", "Config", "Scripts", "Content"):
        base = project / folder
        if base.exists():
            for path in sorted(base.rglob("*")):
                if path.is_file():
                    checked = contained(project, path.relative_to(project).as_posix())
                    files[path.relative_to(project).as_posix()] = digest(checked)
    for path in sorted(project.glob("*.uproject")):
        files[path.name] = digest(path)
    return files


def execute(command, project, output, timeout):
    with (output / "console.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=project, stdout=log, stderr=subprocess.STDOUT)
        try:
            return process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            # Kill only this invocation's process tree, never other Editor/build sessions.
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
            else:
                process.kill()
            process.wait()
            raise


def run(project, manifest, engine, action, timeout, rendered=False):
    check_lock(project, manifest)
    tools, engine_version = engine_tools(engine, manifest["engine_version"])
    if action == "smoke":
        map_path = "Content/" + manifest["smoke"]["map"][len("/Game/"):] + ".umap"
        if not contained(project, map_path).is_file():
            raise ValueError(f"Missing smoke map: {map_path}")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    output = contained(project, f"Saved/GameCore/{run_id}-{action}")
    output.mkdir(parents=True, exist_ok=False)
    command = commands(project, manifest, tools, output, action, rendered)
    receipt = {"schema_version": 1, "project_id": manifest["project_id"], "action": action,
               "status": "running", "command": command, "engine": engine_version,
               "platform": "Win64", "rendered": rendered, "source_hashes": snapshot(project),
               "runner_sha256": digest(Path(__file__)), "module_tool_sha256": digest(ROOT / "tools/gamecore_modules.py"),
               "started_utc": datetime.now(timezone.utc).isoformat()}
    write_json(output / "receipt.json", receipt)
    print(f"Running {action}: {output}", flush=True)
    started = time.monotonic()
    try:
        receipt["exit_code"] = execute(command, project, output, timeout)
        if receipt["exit_code"] != 0:
            raise ValueError(f"Process failed with exit code {receipt['exit_code']}")
        receipt["result"] = verify_result(manifest, output, action)
        if snapshot(project) != receipt["source_hashes"]:
            raise ValueError("Project inputs changed during run; rerun against a stable baseline")
        receipt["status"] = "passed"
    except (Exception, KeyboardInterrupt) as error:
        receipt["status"] = "failed"
        receipt["error"] = str(error) or type(error).__name__
        raise
    finally:
        receipt["elapsed_seconds"] = round(time.monotonic() - started, 3)
        receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
        receipt["artifacts"] = {p.relative_to(output).as_posix(): digest(p) for p in output.rglob("*")
                                if p.is_file() and p.name != "receipt.json"}
        write_json(output / "receipt.json", receipt)
        print(f"{receipt['status']}: {output / 'receipt.json'}", flush=True)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["modules", "check", "sync", "doctor", "build", "test", "automation", "smoke"])
    parser.add_argument("--project", type=Path)
    parser.add_argument("--engine-root", type=Path, default=Path(os.environ.get("ARCORE_UNREAL_ROOT", "C:/Program Files/Epic Games/UE_5.8")))
    parser.add_argument("--update", action="store_true", help="Explicitly accept changed dependency selections during sync")
    parser.add_argument("--rendered", action="store_true", help="Rendered smoke only; does not certify visual quality")
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    try:
        if args.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if args.update and args.action != "sync":
            raise ValueError("--update is only valid for sync")
        if args.rendered and args.action not in ("smoke", "test"):
            raise ValueError("--rendered is only valid for smoke/test")
        if args.action == "modules":
            print(json.dumps(list(registry().values()), indent=2))
            return
        if not args.project:
            raise ValueError("--project is required")
        project = args.project.resolve()
        manifest = project_config(project)
        if args.action == "sync":
            print(json.dumps(sync(project, manifest, args.update), indent=2))
        elif args.action in ("check", "doctor"):
            check_lock(project, manifest)
            if args.action == "doctor":
                engine_tools(args.engine_root, manifest["engine_version"])
            print(f"passed: {args.action} {manifest['project_id']} (not a gameplay check)")
        else:
            for action in (["automation", "smoke"] if args.action == "test" else [args.action]):
                run(project, manifest, args.engine_root, action, args.timeout, args.rendered if action == "smoke" else False)
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"GameCore failed: {error}\n")


if __name__ == "__main__":
    main()
