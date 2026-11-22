import tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from svg_relief import build

class ReliefTests(unittest.TestCase):
 def test_solid_and_stroke_preserve_source(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'source.svg';out=Path(tmp)/'model.obj'
   text='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path d="M10 10L100 10L100 100Z" fill="#ff0000" stroke="#000000" stroke-width="4"/></svg>'
   source.write_text(text);result=build(source,out)
   self.assertGreater(result['triangles'],1);self.assertEqual(source.read_text(),text)
   self.assertIn('ink_ff0000',result['materials']);self.assertTrue(out.with_suffix('.json').exists())
   with self.assertRaises(FileExistsError):build(source,out)
 def test_transform_is_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'source.svg';source.write_text('<svg viewBox="0 0 512 512"><path transform="scale(2)" d="M0 0L1 0L1 1Z"/></svg>')
   with self.assertRaises(ValueError):build(source,Path(tmp)/'model.obj')
 def test_opacity_is_retained(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'source.svg';source.write_text('<svg viewBox="0 0 512 512"><circle cx="100" cy="100" r="20" fill="#ffffff" opacity="0.4"/></svg>')
   result=build(source,Path(tmp)/'model.obj');self.assertEqual(next(iter(result['materials'].values()))[3],0.4)

 def test_concave_ribbon_keeps_entire_area(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'ribbon.svg';out=Path(tmp)/'ribbon.obj'
   source.write_text('<svg viewBox="0 0 512 512"><path d="M214 166 L298 166 L216 244 L372 308 L206 392 L296 464 L212 464 L118 394 L276 318 L124 246 Z" fill="#1f4d54"/></svg>')
   result=build(source,out)
   vertices=[];area=0
   for line in out.read_text().splitlines():
    if line.startswith('v '):vertices.append(tuple(map(float,line.split()[1:])))
    if line.startswith('f '):
     a,b,c=[vertices[int(i)-1] for i in line.split()[1:]]
     area+=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2
   self.assertAlmostEqual(area,26768*16/(512*512),places=5)
   self.assertEqual(result['geometry_version'],2)
