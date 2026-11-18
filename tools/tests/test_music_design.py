import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
spec = importlib.util.spec_from_file_location("md", ROOT / "tools" / "music_design.py")
md = importlib.util.module_from_spec(spec)
spec.loader.exec_module(md)
CAT = [{"id": "a", "name": "A"}, {"id": "shammyverse", "name": "S"}]


class MusicDesignTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup); self.d = Path(t.name)

    def test_init_excludes_and_never_overwrites(self):
        md.init(CAT, self.d, {"shammyverse"})
        self.assertEqual(md.load(self.d / "shammyverse.json")["status"], "excluded")
        rec = md.load(self.d / "a.json"); rec["status"] = "approved"; md.save(self.d / "a.json", rec)
        self.assertEqual(md.init(CAT, self.d, set()), [])
        self.assertEqual(md.load(self.d / "a.json")["status"], "approved")

    def test_assign_preserves_recorded_tracks_and_renders_prompts(self):
        md.init(CAT, self.d, set())
        rec = md.assign(md.load(self.d / "a.json"), md.load(md.ARCH), "cozy", "village")
        self.assertEqual(len(rec["tracks"]), 3)
        rec["tracks"][0]["notes"] = "kept"
        rec = md.assign(rec, md.load(md.ARCH), "cozy", "village")
        self.assertEqual((len(rec["tracks"]), rec["tracks"][0]["notes"]), (3, "kept"))
        page = md.render(rec)
        self.assertIn(rec["tracks"][0]["style_prompt"], page)
        self.assertIn("| Acoustic Guitar | Acoustic Guitar | yes |", page)
        self.assertEqual(md.errors(rec), [])

    def test_validation_rules(self):
        md.init(CAT, self.d, set())
        rec = md.assign(md.load(self.d / "a.json"), md.load(md.ARCH), "cozy")
        t = rec["tracks"][0]
        t["vocals"] = "sung"; t["lyrics"] = ""; t["status"] = "generated"
        self.assertEqual(len(md.errors(rec)), 2)

    def test_recommend_covers_catalog_and_roadmap(self):
        cat = md.load(md.CATALOG)
        rm = md.load(md.ROADMAP)["projects"]
        updated = md.apply_recommendations(self.d, md.load(md.ARCH), cat, rm)
        self.assertEqual(len(updated), 81)
        bistro = md.load(self.d / "beast-bistro-express.json")
        self.assertEqual(bistro["recommended_archetype"], "action-rock")
        self.assertEqual(bistro["status"], "recommended")
        self.assertEqual(len(bistro["tracks"]), 3)
        shammy = md.load(self.d / "shammyverse.json")
        self.assertEqual(shammy["status"], "excluded")
        self.assertEqual(len(shammy["tracks"]), 0)



if __name__ == "__main__":
    unittest.main()
