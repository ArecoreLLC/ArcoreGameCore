"""Mixture math, region scheduling, clipping, and advanced CLI acceptance."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageDraw

from advanced import fit_recipe, mixed_color, schedule_count
from render_gif import ROOT, Renderer, run


class AdvancedTests(unittest.TestCase):
    def test_optical_density_mixture_and_recipe_percentages(self):
        self.assertEqual(mixed_color([(255,255,255),(64,64,64)],[.5,.5]),(128,128,128))
        bases=[(252,251,247),(8,12,9),(54,49,22),(55,125,126),(87,120,75),(31,62,45)]
        for index,base in enumerate(bases):
            recipe=fit_recipe(base,bases)
            self.assertEqual(sum(recipe['parts']),100)
            self.assertEqual(recipe['parts'][index],100)
            self.assertEqual(recipe['mixed_rgb'],list(base))
        target=mixed_color(bases,[.35,.1,.55,0,0,0])
        recipe=fit_recipe(target,bases)
        self.assertEqual(sum(recipe['parts']),100)
        self.assertLessEqual(recipe['rgb_rmse'],2)
        self.assertTrue(all(p>=0 for p in recipe['parts']))
        self.assertLessEqual(sum(p>0 for p in recipe['parts']),4)

    def test_equal_time_parts_finish_before_next_part(self):
        schedule=[{'id':'large','operations':[{}]*100},{'id':'small','operations':[{}]*10}]
        self.assertEqual(schedule_count(schedule,0)[0],0)
        self.assertEqual(schedule_count(schedule,.25)[0],50)
        self.assertEqual(schedule_count(schedule,.5)[0],100)
        self.assertEqual(schedule_count(schedule,.75)[0],105)
        self.assertEqual(schedule_count(schedule,1)[0],110)
        self.assertEqual(schedule_count(schedule,.25)[1]['id'],'large')
        self.assertEqual(schedule_count(schedule,.75)[1]['id'],'small')

    def test_brush_footprint_stays_inside_owned_region(self):
        region=Image.new('L',(640,349),0)
        ImageDraw.Draw(region).rectangle((0,0,319,348),fill=1)
        op={'x':620,'y':349,'dx':500,'dy':0,'width':100,'alpha':1,'color':'rgb(200,20,30)','part_id':'left'}
        data={'parts':[{'id':'background'},{'id':'left'}],'stages':[[],[],[],[],[op],[]]}
        renderer=Renderer(data,320,region);renderer.advance(4,1)
        self.assertGreater(renderer.layers[4].getpixel((250,174))[3],0)
        self.assertEqual(renderer.layers[4].getpixel((350,174))[3],0)

    def test_advanced_cli_and_separate_mixing_only_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            root=Path(temp);source=root/'reference.png'
            im=Image.new('RGB',(160,100),(250,248,241));d=ImageDraw.Draw(im)
            d.ellipse((30,15,130,85),fill=(92,105,55));d.ellipse((65,35,95,65),fill=(20,70,60));im.save(source)
            args=argparse.Namespace(input=source,lesson=None,output=root/'advanced.gif',sheet=None,width=320,fps=2,duration=6,hold=1,no_cursor=True,advanced=True,mixing_output=None,mixing_only=False,palette_output=None)
            report=run(args)
            self.assertTrue(report['advanced'])
            manifest=json.loads((root/'advanced-palette.json').read_text())
            self.assertEqual(len(manifest['base_colors']),6)
            self.assertTrue(all(sum(r['parts'])==100 for r in manifest['recipes']))
            self.assertEqual(sum(p['broad_strokes']+p['fine_strokes'] for p in manifest['parts']),sum(report['stroke_counts'][4:]))
            for part in manifest['parts']:
                for recipe_id in part['recipe_ids']:
                    self.assertIn(recipe_id,{r['id'] for r in manifest['recipes']})
            args.output=root/'not-rendered.gif';args.mixing_only=True;args.mixing_output=root/'mixing.gif'
            mixing=run(args)
            self.assertFalse(args.output.exists())
            self.assertTrue(args.mixing_output.exists())
            self.assertEqual(mixing['loop'],0)
            self.assertGreater(mixing['frames'],7)


if __name__=='__main__':
    unittest.main()
