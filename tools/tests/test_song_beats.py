import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("song_beats", ROOT / "tools" / "song_beats.py")
sb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sb)


def click_track(bpm, seconds=40.0, first=.3):
    """An onset envelope (100 Hz) with a click on every beat starting at `first` seconds."""
    frames = int(seconds * 100)
    onset = [0.0] * frames
    t = first
    while t * 100 < frames - 1:
        i = int(round(t * 100))
        onset[i] = 1.0
        if i + 1 < frames:onset[i + 1] = .4
        t += 60.0 / bpm
    return onset


class SongBeatsTests(unittest.TestCase):
    def test_tempo_recovers_click_track_bpm(self):
        for bpm in (96.0, 120.0, 135.0):
            self.assertAlmostEqual(sb.tempo(click_track(bpm)), bpm, delta=1.2)

    def test_phase_finds_first_click(self):
        onset = click_track(120.0, first=.25)
        self.assertEqual(sb.phase(onset, 50.0), 25)

    def test_estimate_offset_is_within_one_beat(self):
        result = sb.estimate(click_track(120.0, first=.25), start=0.0)
        self.assertAlmostEqual(result['bpm'], 120.0, delta=1.2)
        self.assertGreaterEqual(result['offset'], 0.0)
        self.assertLess(result['offset'], 60.0 / result['bpm'])

    def test_envelope_from_silence_and_burst(self):
        samples = [0] * 800 + [8000, -8000] * 400 + [0] * 800
        env = sb.envelope_from_samples(samples)
        self.assertEqual(max(env), 1.0)
        self.assertEqual(sb.envelope_from_samples([0] * 1000), [0.0] * 11)

    def test_render_json_and_gdscript(self):
        table = {'song': {'bpm': 120.0, 'offset': .25}}
        self.assertEqual(json.loads(sb.render(table, 'beats.json')), table)
        gd = sb.render(table, 'song_beats.gd')
        self.assertTrue(gd.startswith('extends RefCounted'))
        self.assertIn('const BEATS := {', gd)


if __name__ == "__main__":
    unittest.main()
