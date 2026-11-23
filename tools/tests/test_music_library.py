import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
spec = importlib.util.spec_from_file_location("ml", ROOT / "tools" / "music_library.py")
ml = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ml)
ARCH = ml.load(ml.ARCH)


def track(tid, arch="cozy", **kw):
    t = {"id": tid, "title": f"Track {tid}", "file": f"{tid}.mp3", "archetype": arch,
         "secondary_archetypes": [], "game_states": ["explore"], "contexts": ["town"], "vocals": "none"}
    t.update(kw)
    return t


class MusicLibraryTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup); self.lib = Path(t.name)

    def folder(self, name, tracks, audio=True):
        d = self.lib / name; d.mkdir()
        if audio:
            for t in tracks:
                (d / t["file"]).write_bytes(b"ID3")
        (d / "metadata.json").write_text(json.dumps({"schema": ml.FOLDER_SCHEMA, "folder": name, "label": name.title(), "tracks": tracks}))
        return d

    def test_builds_index_with_parent_archetype_and_paths(self):
        self.folder("cozy", [track("A1", "nautical-folk", secondary_archetypes=["cozy"])])
        self.folder("horror", [track("B1", "horror", game_states=["tension", "combat"], contexts=["chase"])])
        index, errs = ml.build(self.lib, ARCH, generated_at="fixed")
        self.assertEqual(errs, [])
        self.assertEqual([t["id"] for t in index["tracks"]], ["A1", "B1"])
        a1 = index["tracks"][0]
        self.assertEqual((a1["parent_archetype"], a1["path"], a1["folder"]), ("cozy", "cozy/A1.mp3", "cozy"))
        fams = {f["archetype"]: f["sub_archetypes"] for f in index["families"]}
        self.assertIn("nautical-folk", fams["cozy"])
        self.assertEqual(len(fams), 6)

    def test_coverage_reports_missing_states_per_archetype(self):
        self.folder("cozy", [track("A1", "cozy", game_states=["explore", "resolve"]), track("A2", "lofi-workshop", secondary_archetypes=["cozy"])])
        cov = {c["archetype"]: c for c in ml.coverage(ml.scan(self.lib, ARCH)[0], ARCH)}
        self.assertEqual(cov["cozy"]["primary_tracks"], 1)
        self.assertEqual(cov["cozy"]["related_tracks"], 1)
        self.assertEqual(cov["cozy"]["missing_states"], ["tension", "combat", "boss"])
        self.assertEqual(cov["horror"]["primary_tracks"], 0)
        self.assertEqual(len(cov), len(ARCH["archetypes"]))

    def test_rejects_unknown_taxonomy_missing_files_and_duplicates(self):
        self.folder("a", [track("X1", "polka"), track("X2", game_states=["vibes"], contexts=["nowhere"])])
        d = self.folder("b", [track("X1")])
        (d / "stray.mp3").write_bytes(b"ID3")
        self.folder("c", [track("Y1")], audio=False)
        _, errs = ml.build(self.lib, ARCH)
        text = "\n".join(errs)
        for needle in ("unknown archetype 'polka'", "unknown game state 'vibes'", "unknown context 'nowhere'",
                       "duplicate id", "'stray.mp3' has no metadata entry", "file not found 'Y1.mp3'"):
            self.assertIn(needle, text)

    def test_invalid_tracks_are_left_out_of_the_index(self):
        self.folder("a", [track("OK"), track("BAD", "polka")])
        index, errs = ml.build(self.lib, ARCH)
        self.assertEqual([t["id"] for t in index["tracks"]], ["OK"])
        self.assertTrue(errs)

    def test_cli_build_refuses_to_write_when_invalid(self):
        self.folder("a", [track("BAD", "polka")])
        out = self.lib / "index.json"
        self.assertEqual(ml.main(["build", "--library", str(self.lib), "--out", str(out)]), 1)
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
