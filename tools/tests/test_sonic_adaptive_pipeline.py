import importlib.util
import json
import math
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


if __name__ == "__main__":
    unittest.main()
