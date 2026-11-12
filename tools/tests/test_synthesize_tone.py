import math, struct, sys, tempfile, unittest, wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from synthesize_tone import write_tone
class ToneTests(unittest.TestCase):
    def test_bounded_stereo_and_repeatability(self):
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/'a.wav'; b=Path(folder)/'b.wav'
            write_tone(a,[130.81,196],gain=0.6)
            write_tone(b,[130.81,196],gain=0.6)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with wave.open(str(a)) as w:
                self.assertEqual((w.getnchannels(),w.getnframes(),w.getframerate()),(2,24000,24000))
                raw=w.readframes(w.getnframes())
            values=struct.unpack('<'+'h'*(len(raw)//2),raw)
            self.assertLessEqual(max(abs(x) for x in values),round(0.6*32767))
            self.assertEqual(values[:2],(0,0));self.assertEqual(values[-2:],(0,0))
            self.assertNotEqual(values[::2],values[1::2])
    def test_invalid_inputs_do_not_write(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'bad.wav'
            for args in [dict(frequencies=[]),dict(frequencies=[math.nan]),dict(frequencies=[13000]),dict(frequencies=[100],duration=100),dict(frequencies=[100],gain=1),dict(frequencies=[100],echo=-1)]:
                with self.assertRaises(ValueError):write_tone(p,**args)
                self.assertFalse(p.exists())
