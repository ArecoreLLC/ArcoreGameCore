import importlib.util
import json
import math
import shutil
import subprocess
import struct
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
spec = importlib.util.spec_from_file_location("sap", ROOT / "tools" / "sonic_adaptive_pipeline.py")
sap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sap)


def write_float32_wav(path: Path, sr: int, seconds: float, freq: float, amp: float = 0.25):
    frames = int(round(sr * seconds))
    data = bytearray()
    for i in range(frames):
        v = amp * math.sin(2.0 * math.pi * freq * (i / sr))
        data.extend(struct.pack("<2f", v, v))
    pcm_size = len(data)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + pcm_size,
        b"WAVE",
        b"fmt ",
        16,
        3,
        2,
        sr,
        sr * 8,
        8,
        32,
        b"data",
        pcm_size,
    )
    path.write_bytes(header + data)


class SonicAdaptivePipelineTests(unittest.TestCase):
    def test_exact_wav_duration_and_session_builder(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "test.wav"
            write_float32_wav(p, 48000, 2.5, 220.0)
            self.assertAlmostEqual(sap.exact_wav_duration(p), 2.5, places=6)
            stems = [(1, "Strings", "stem-01.wav", 60.0, "strings")] * 4
            for idx in range(4):
                stems[idx] = (idx + 1, f"L{idx+1}", f"s{idx+1}.wav", 60.0, "role")
            sess, des = sap.build_session_and_design("Test", 115.0, "D minor", 4, 8, 2, -8.0, 2.0, stems)
            self.assertEqual(des["schema"], "arcore-adaptive-v1")
            self.assertEqual(len(sess["tracks"]), 4)
            self.assertEqual(len(des["states"]), 4)

    def test_auto_select_stems_and_cook_ini(self):
        with tempfile.TemporaryDirectory() as tmp:
            tdir = Path(tmp)
            write_float32_wav(tdir / "0 Mix.wav", 48000, 12.0, 110.0, 0.4)
            write_float32_wav(tdir / "1 Vocals.wav", 48000, 12.0, 440.0, 0.3)
            write_float32_wav(tdir / "2 Drums.wav", 48000, 12.0, 100.0, 0.35)
            write_float32_wav(tdir / "3 Bass.wav", 48000, 12.0, 65.0, 0.25)
            write_float32_wav(tdir / "4 Guitar.wav", 48000, 12.0, 220.0, 0.30)
            write_float32_wav(tdir / "5 Synth.wav", 48000, 12.0, 330.0, 0.20)
            stems, start_bar = sap.auto_select_stems(tdir, bpm=120.0, bars=2)
            self.assertEqual([s[1] for s in stems], ["Guitar", "Synth", "Bass", "Drums"])
            self.assertGreaterEqual(start_bar, 2)

            cfg = tdir / "Config"
            cfg.mkdir()
            (cfg / "DefaultGame.ini").write_text("[/Script/UnrealEd.ProjectPackagingSettings]\n", encoding="utf-8")
            sap.ensure_always_cook_music(tdir, "/Game/Audio/Music")
            self.assertIn('+DirectoriesToAlwaysCook=(Path="/Game/Audio/Music")', (cfg / "DefaultGame.ini").read_text(encoding="utf-8"))


class SonicAdaptiveIntegrationTests(unittest.TestCase):
    """Score codegen and the registered Sonic Alchemist MCP round trip."""

    def test_score_header_compiles_against_the_portable_module(self):
        design = {"schema": "arcore-adaptive-v1", "title": "Demo \"Loop\"", "bpm": 92.0, "key": "C", "beatsPerBar": 4,
                  "bars": 32, "start": 0.0, "masterDb": -8.0,
                  "layers": [{"id": 1, "name": "Keys", "duration": 90.0}, {"id": 2, "name": "Drums", "duration": 90.0}],
                  "states": [{"name": "Explore", "intensity": 0.2, "levels": [{"enabled": True, "gainDb": -5.0}, {"enabled": False, "gainDb": 0.0}]},
                             {"name": "Combat", "intensity": 0.9, "levels": [{"enabled": True, "gainDb": -2.0}, {"enabled": True, "gainDb": 1.5}]}],
                  "transition": {"boundary": "phrase", "fadeBeats": 2.0}}
        self.assertEqual(sap.score_function_name("3d-tower-assault"), "Game3dTowerAssaultScore")
        self.assertEqual(sap.score_function_name("acorn&anvil"), "AcornAnvilScore")
        text = sap.score_header(design, "DemoScore")
        self.assertIn("GameCore::MusicBoundary::Phrase", text)
        self.assertIn("{-5.0f, -60.0f}, // Explore", text)
        with self.assertRaises(ValueError):
            sap.score_header(design, "not a name")
        compiler = shutil.which("g++") or shutil.which("c++")
        if not compiler:
            self.skipTest("No host C++ compiler")
        with tempfile.TemporaryDirectory() as tmp:
            tdir = Path(tmp)
            (tdir / "DemoScore.h").write_text(text, encoding="utf-8")
            (tdir / "main.cpp").write_text(
                '#include "DemoScore.h"\n#include <cassert>\nint main(){const auto& s=DemoScore();'
                'assert(s.Valid() && s.Layers()==2 && s.TargetGain(0,1)==0 && s.stateGainDb[1][1]==1.5f);}\n', encoding="utf-8")
            exe = tdir / "demo.exe"
            subprocess.run([compiler, "-std=c++14", f"-I{ROOT / 'shared' / 'cpp'}", str(tdir / "main.cpp"), "-o", str(exe)], check=True)
            subprocess.run([str(exe)], check=True)

    def test_registered_mcp_validates_exports_and_verifies(self):
        command, _, server = sap.sonic_server()
        self.assertEqual(server["write_tools"], ["adaptive_export"])
        if not Path(command[0]).is_file():
            self.skipTest("Sonic Alchemist MCP server is not built")
        with self.assertRaises(ValueError):
            sap.sonic_mcp_call("delete_everything", {})
        with tempfile.TemporaryDirectory() as tmp:
            tdir = Path(tmp)
            stems = []
            for index, freq in enumerate([220.0, 330.0, 110.0, 440.0], start=1):
                write_float32_wav(tdir / f"s{index}.wav", 48000, 6.0, freq, 0.2)
                stems.append((index, f"L{index}", f"s{index}.wav", 6.0, "role"))
            session, design = sap.build_session_and_design("MCP round trip", 120.0, "A minor", 4, 2, 0, -8.0, 2.0, stems)
            sap.save_json(tdir / "game.arcore", session)
            sap.save_json(tdir / "Design.json", design)
            checked = sap.sonic_mcp_call("adaptive_validate", {"design": str(tdir / "Design.json"), "project": str(tdir / "game.arcore")})
            self.assertTrue(checked["project"]["matches"])
            self.assertAlmostEqual(checked["runtime"]["barSeconds"], 2.0)
            exported = sap.sonic_mcp_call("adaptive_export", {"project": str(tdir / "game.arcore"), "design": str(tdir / "Design.json"),
                                                               "output": str(tdir / "Export")})
            self.assertTrue(exported["verified"], exported["problems"])
            self.assertEqual(exported["runtimeSource"], "assets.json")
            self.assertEqual(len(exported["layers"]), 4)
            self.assertTrue(all(len(layer["sha256"]) == 64 for layer in exported["layers"]))
            self.assertEqual(sap.validate_export(tdir / "Export")["frames"], 192000)
            with self.assertRaisesRegex(RuntimeError, "new output folder"):
                sap.sonic_mcp_call("adaptive_export", {"project": str(tdir / "game.arcore"), "design": str(tdir / "Design.json"),
                                                        "output": str(tdir / "Export")})


if __name__ == "__main__":
    unittest.main()
