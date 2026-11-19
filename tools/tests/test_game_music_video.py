import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
spec = importlib.util.spec_from_file_location("gmv", ROOT / "tools" / "game_music_video.py")
gmv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gmv)

LOG = """Godot Engine v4.7.2
MUSIC_VIDEO_SONG_START frame=29 length=234.914 recorder=0.1.0
MUSIC_VIDEO_SHOT 0 18.6-34.6 blocked=0%
MUSIC_VIDEO_SHOT 1 34.6-53.0 blocked=24% CHECK
MUSIC_VIDEO_END t=235.93 frame=7107
"""


class GameMusicVideoTests(unittest.TestCase):
    def test_parse_log_reads_markers(self):
        r = gmv.parse_log(LOG)
        self.assertEqual(r["start_frame"], 29)
        self.assertAlmostEqual(r["song_length"], 234.914)
        self.assertTrue(r["finished"])
        self.assertEqual(len(r["shots"]), 2)
        self.assertEqual(r["checks"], [1])
        self.assertEqual(r["errors"], [])

    def test_parse_log_flags_unfinished_and_errors(self):
        r = gmv.parse_log("SCRIPT ERROR: Parse Error: x\n")
        self.assertIsNone(r["start_frame"])
        self.assertFalse(r["finished"])
        self.assertEqual(len(r["errors"]), 1)

    def test_override_shared_by_parallel_users_and_restored(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            (project / "override.cfg").write_text("mine\n", encoding="utf-8")
            first = gmv.acquire_override(project, 1920, 1200)
            second = gmv.acquire_override(project, 1920, 1200)
            self.assertIn("window_width_override=1920", (project / "override.cfg").read_text(encoding="utf-8"))
            gmv.release_override(first)
            self.assertIn("window_height_override=1200", (project / "override.cfg").read_text(encoding="utf-8"))
            gmv.release_override(second)
            self.assertEqual((project / "override.cfg").read_text(encoding="utf-8"), "mine\n")
            self.assertFalse((project / gmv.OVERRIDE_DIR).exists())

    def test_override_removed_when_none_existed(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            token = gmv.acquire_override(project, 1280, 720)
            gmv.release_override(token)
            self.assertFalse((project / "override.cfg").exists())

    def test_override_rejects_conflicting_size(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            token = gmv.acquire_override(project, 1920, 1200)
            with self.assertRaises(SystemExit):
                gmv.acquire_override(project, 1920, 1080)
            gmv.release_override(token)

    def test_mix_keeps_song_unnormalized_and_trims_setup(self):
        cmd = gmv.mix_command("a.avi", "song.mp3", "out.mp4", offset=0.967, length=235.9, sfx_db=-4)
        joined = " ".join(cmd)
        self.assertIn("-ss 0.967", joined)
        self.assertIn("normalize=0", joined)
        self.assertIn("volume=-4", joined)
        self.assertNotIn("loudnorm", joined)

    def test_preview_fits_sharing_limit(self):
        for length in (150.0, 235.0, 312.0):
            kbps = gmv.preview_bitrate(length, 28.0) + 96
            self.assertLessEqual(kbps * length / 8192, 28.0 + 1e-6)

    def test_headless_dry_run_and_movie_commands(self):
        dry = gmv.godot_command("godot.exe", "game", "rec.gd", "theme")
        self.assertIn("--headless", dry)
        self.assertEqual(dry[-1], "--song=theme")
        movie = gmv.godot_command("godot.exe", "game", "rec.gd", "theme", movie="x.avi")
        self.assertIn("--write-movie", movie)
        self.assertNotIn("--headless", movie)

    def test_motion_parses_signalstats_and_flags_dead_shots(self):
        text = 'frame:0\nlavfi.signalstats.YAVG=0.40\nframe:1\nlavfi.signalstats.YAVG=0.60\n'
        self.assertAlmostEqual(gmv.parse_motion(text), 0.5)
        self.assertEqual(gmv.parse_motion(''), 0.0)
        shots = [{'index': 0}, {'index': 1}, {'index': 2}]
        self.assertEqual(gmv.dead_shots(shots, [3.0, 0.5, 1.1], 1.2), [1, 2])
        cmd = gmv.motion_command('v.mp4', 10.0, 18.5)
        self.assertIn('10.00', cmd);self.assertIn('18.50', cmd)
        self.assertTrue(any('signalstats' in c for c in cmd))

    def test_vendor_world_life_module_locks_every_file(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            (project / "project.godot").write_text("", encoding="utf-8")
            lock = gmv.vendor(project, module="world-life")
            names = [f["name"] for f in lock["files"]]
            self.assertEqual(names[:2], ["world_life_kit.gd", "sea_breach.gd"])
            self.assertIn("beat_dance.gd", names);self.assertIn("celebration_burst.gd", names);self.assertEqual(len(names), 12)
            for f in lock["files"]:
                self.assertEqual(f["sha256"], gmv.sha256(project / "addons/gamecore_world_life" / f["name"]))
            self.assertEqual(lock["version"], "0.2.0")
            breach = project / "addons/gamecore_world_life/sea_breach.gd"
            breach.write_text(breach.read_text(encoding="utf-8") + "\n# local edit\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                gmv.vendor(project, module="world-life")

    def test_music_video_module_includes_showcase_base(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            (project / "project.godot").write_text("", encoding="utf-8")
            lock = gmv.vendor(project)
            self.assertEqual([f["name"] for f in lock["files"]], ["music_video_recorder.gd", "asset_showcase.gd"])
            self.assertEqual(lock["files"][1]["version"], "0.1.0")

    def test_showcase_tile_command_lays_out_two_rows(self):
        cmd = gmv.tile_command([f"{i}.png" for i in range(6)], "sheet.jpg")
        graph = cmd[cmd.index("-filter_complex") + 1]
        self.assertIn("xstack=inputs=6", graph)
        self.assertIn("w0+w0+w0_0", graph)
        self.assertIn("w0_h0", graph)
        self.assertEqual(gmv.SHOWCASE_RE.findall("SHOWCASE_SHOT G3b 13.0\nSHOWCASE_SHOT A1 0.0"), [("G3b", "13.0"), ("A1", "0.0")])

    def test_vendor_installs_lock_and_refuses_local_edits(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            (project / "project.godot").write_text("", encoding="utf-8")
            lock = gmv.vendor(project)
            installed = project / gmv.DEFAULT_DEST / gmv.RUNTIME.name
            self.assertEqual(lock["sha256"], gmv.sha256(installed))
            self.assertEqual(lock["version"], gmv.runtime_version())
            installed.write_text(installed.read_text(encoding="utf-8") + "\n# local edit\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                gmv.vendor(project)
            gmv.vendor(project, force=True)
            saved = json.loads((project / gmv.DEFAULT_DEST / gmv.LOCK_NAME).read_text(encoding="utf-8"))
            self.assertEqual(saved["sha256"], gmv.sha256(installed))


if __name__ == "__main__":
    unittest.main()
