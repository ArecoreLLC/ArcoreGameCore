"""Headless exporter acceptance tests; run with unittest discovery in this directory."""
import argparse
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageChops, ImageDraw

from render_gif import ROOT, normalized_reference, run


class GifExportTests(unittest.TestCase):
    def test_reference_fit_preserves_aspect_ratio(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            path=Path(temp)/'portrait.png'
            Image.new('RGB',(100,200),(200,10,20)).save(path)
            args=argparse.Namespace(input=path,lesson=None)
            image,name,study=normalized_reference(args)
            self.assertEqual(image.size,(1280,698))
            self.assertEqual(image.getpixel((0,0)),(250,248,241,255))
            self.assertEqual(image.getpixel((640,349)),(200,10,20,255))
            self.assertEqual(image.getpixel((640,10)),(200,10,20,255))
            self.assertEqual(study,'custom')

    def test_cli_exports_decodable_loop_with_exact_timing_and_teaching_sheet(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            root=Path(temp);source=root/'reference.png'
            image=Image.new('RGB',(200,100),(250,248,241))
            ImageDraw.Draw(image).ellipse((50,15,150,85),fill=(45,80,55))
            image.save(source)
            args=argparse.Namespace(input=source,lesson=None,output=root/'study.gif',sheet=root/'sheet.png',width=320,fps=2,duration=6,hold=1,no_cursor=True)
            report=run(args)
            self.assertEqual(report['duration_ms'],7000)
            self.assertEqual(report['loop'],0)
            self.assertGreaterEqual(report['frames'],7)
            with Image.open(args.output) as gif:
                first=gif.convert('RGB');gif.seek(gif.n_frames-1)
                self.assertIsNotNone(ImageChops.difference(first,gif.convert('RGB')).getbbox())
            with Image.open(args.sheet) as sheet:
                self.assertEqual(sheet.size,(1800,2240))
            self.assertTrue(args.output.with_suffix('.evidence.json').is_file())

    def test_invalid_export_settings_fail_before_render(self):
        args=argparse.Namespace(width=960,fps=0,duration=24,hold=2)
        with self.assertRaises(ValueError):
            run(args)


if __name__=='__main__':
    unittest.main()
