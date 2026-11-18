import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from tools.music_design import match_suno_library_clips


class MusicDesignMatchingTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            {"game_id": "3d-tower-assault", "name": "3D Tower Assault", "tracks": []},
            {"game_id": "tower-assault-web", "name": "Tower Assault Web", "tracks": []},
            {"game_id": "shammyverse", "name": "ShammyVerse", "tracks": []},
            {"game_id": "shammyverse-vr-beach", "name": "ShammyVerse VR Beach", "tracks": []},
        ]

    def test_3dtower_hits_3d_tower_assault_and_3d_alone_does_not_match(self):
        clips = [
            {"id": "c1", "title": "3DTower Assault - Adaptive track test2", "song_url": "https://suno.com/song/c1"},
            {"id": "c2", "title": "3Dtower - Siege Loop", "song_url": "https://suno.com/song/c2"},
            {"id": "c3", "title": "3D Space Jam", "song_url": "https://suno.com/song/c3"},
            {"id": "c4", "title": "Unrelated Midnight Jazz", "song_url": "https://suno.com/song/c4"},
        ]
        res = match_suno_library_clips(clips, self.records)
        ids_ta = [x["clip_id"] for x in res.get("3d-tower-assault", [])]
        self.assertEqual(ids_ta, ["c1", "c2"])
        self.assertEqual(res["3d-tower-assault"][0]["match_confidence"], "exact")
        self.assertEqual(res["3d-tower-assault"][1]["match_confidence"], "high")
        self.assertNotIn("tower-assault-web", res)

    def test_shammyverse_ambiguous_multi_match_and_stem_exclusion(self):
        clips = [
            {"id": "s1", "title": "ShammyVerse Island Cruise", "song_url": "https://suno.com/song/s1"},
            {"id": "s2", "title": "ShammyVerse Island Cruise - Drums", "song_url": "https://suno.com/song/s2"},
        ]
        res = match_suno_library_clips(clips, self.records)
        self.assertEqual([x["clip_id"] for x in res.get("shammyverse", [])], ["s1"])
        self.assertEqual(res["shammyverse"][0]["match_confidence"], "exact")
        self.assertIn("shammyverse-vr-beach", res["shammyverse"][0]["match_candidates"])
        self.assertEqual(res["shammyverse-vr-beach"][0]["match_confidence"], "ambiguous")


if __name__ == "__main__":
    unittest.main()
