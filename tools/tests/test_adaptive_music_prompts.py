import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
spec = importlib.util.spec_from_file_location("amp", ROOT / "tools" / "adaptive_music_prompts.py")
amp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(amp)
WF = ROOT / "workflows" / "adaptive-music-stems"


class AdaptiveMusicPromptTests(unittest.TestCase):
    def setUp(self):
        self.arch = json.loads((WF / "archetypes.json").read_text(encoding="utf-8"))
        self.games = json.loads((WF / "games.example.json").read_text(encoding="utf-8"))

    def test_excludes_scored_games_and_counts_tracks(self):
        tracks = amp.generate(self.arch, self.games)
        self.assertEqual(len(tracks), 9)
        self.assertFalse(any("existing" in t["game"] for t in tracks))

    def test_stems_are_valid_suno_categories_and_style_fits(self):
        valid = set(self.arch["suno_stem_categories"])
        for a in self.arch["archetypes"].values():
            for i in a["instruments"]:
                self.assertIn(i["stem"], valid)
        self.assertEqual(amp.check_style_length(amp.generate(self.arch, self.games)), [])

    def test_unknown_archetype_rejected(self):
        self.games["games"][0]["archetype"] = "nope"
        with self.assertRaises(ValueError):
            amp.generate(self.arch, self.games)


if __name__ == "__main__":
    unittest.main()
