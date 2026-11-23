"""Painted, animated companion pipeline: stage manifest, stepper math, vendoring and GLB checks."""
import importlib.util
import io
import json
import math
import struct
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / '3d/blender/companion_studio'))
import companion_pipeline as pipeline   # noqa: E402
import motion                           # noqa: E402


def run(argv):
    out = io.StringIO()
    with redirect_stdout(out): code = pipeline.main(argv)
    return code, out.getvalue()


def glb(path, clips, weights=(1.0, 0.0, 0.0, 0.0), textured=True):
    """A one-triangle skinned GLB. clips: {name: (times, rotations)} on the single joint."""
    chunks = []; views = []; accessors = []
    def add(rows, code, kind, component):
        data = b''.join(struct.pack('<' + code * len(row), *row) for row in rows); offset = sum(len(c) for c in chunks)
        chunks.append(data + b'\0' * (-len(data) % 4)); views.append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(data)})
        accessors.append({'bufferView': len(views) - 1, 'componentType': component, 'count': len(rows), 'type': kind}); return len(accessors) - 1
    position = add([(0, 0, 0), (1, 0, 0), (0, 1, 0)], 'f', 'VEC3', 5126); uv = add([(0, 0), (1, 0), (0, 1)], 'f', 'VEC2', 5126)
    joint = add([(0, 0, 0, 0)] * 3, 'B', 'VEC4', 5121); weight = add([weights] * 3, 'f', 'VEC4', 5126); index = add([(0,), (1,), (2,)], 'H', 'SCALAR', 5123)
    animations = []
    for name, (times, rotations) in clips.items():
        animations.append({'name': name, 'samplers': [{'input': add([(t,) for t in times], 'f', 'SCALAR', 5126), 'output': add(rotations, 'f', 'VEC4', 5126)}],
                           'channels': [{'sampler': 0, 'target': {'node': 0, 'path': 'rotation'}}]})
    material = {'name': 'paint', 'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}} if textured else {}}
    doc = {'asset': {'version': '2.0'}, 'nodes': [{'name': 'Body'}, {'name': 'Mesh', 'mesh': 0, 'skin': 0}], 'skins': [{'joints': [0]}],
           'meshes': [{'name': 'tri', 'primitives': [{'attributes': {'POSITION': position, 'TEXCOORD_0': uv, 'JOINTS_0': joint, 'WEIGHTS_0': weight}, 'indices': index, 'material': 0}]}],
           'materials': [material], 'images': [{'name': 'painted_albedo'}], 'animations': animations,
           'buffers': [{'byteLength': sum(len(c) for c in chunks)}], 'bufferViews': views, 'accessors': accessors}
    text = json.dumps(doc).encode(); text += b' ' * (-len(text) % 4); binary = b''.join(chunks)
    Path(path).write_bytes(b'glTF' + struct.pack('<II', 2, 28 + len(text) + len(binary)) + struct.pack('<I', len(text)) + b'JSON' + text
                           + struct.pack('<I', len(binary)) + b'BIN\0' + binary)


def turn(degrees):
    return (0.0, math.sin(math.radians(degrees) / 2), 0.0, math.cos(math.radians(degrees) / 2))


class StageTests(unittest.TestCase):
    def test_every_stage_names_a_known_automation_class_and_existing_tools(self):
        data = pipeline.load_stages(); classes = set(data['automation_classes']); ids = [s['id'] for s in data['stages']]
        self.assertEqual(len(ids), len(set(ids)))
        for stage in data['stages']:
            for key in ('automation', 'fallback', 'first_time'):
                if key in stage: self.assertIn(stage[key], classes, stage['id'])
            for field in ('title', 'inputs', 'outputs', 'check', 'why', 'tools'): self.assertIn(field, stage, stage['id'])
            for tool in stage['tools']:
                path = tool.split(' ')[0]
                if path.startswith(('tools/', '3d/')): self.assertTrue((ROOT / path).is_file(), f"{stage['id']}: {path}")
        # The judgement stages are named, not hidden: the workflow's point is to say which they are.
        frontier = {s['id'] for s in data['stages'] if s['automation'] == 'frontier-model'}
        self.assertTrue({'markings', 'clips-new-motion', 'visual-review'} <= frontier)

    def test_stages_command_filters_by_class(self):
        code, text = run(['stages', '--class', 'procedural', '--json']); self.assertEqual(code, 0)
        self.assertTrue(all(s['automation'] == 'procedural' for s in json.loads(text)))


class StepperTests(unittest.TestCase):
    def tip(self, head_height, length, angle_deg, lean, pitch, y, z):
        """Where the limb's ground contact ends up, for an upright body (pitch 0)."""
        a = math.radians(angle_deg - lean + pitch)
        return y + length * math.sin(a), head_height + z - length * math.cos(a)

    def test_stride_runs_back_at_constant_speed_then_lifts_forward(self):
        self.assertEqual(motion.stride(0.0), (-1, 0.0)); self.assertAlmostEqual(motion.stride(.3)[0], 0.0)
        self.assertAlmostEqual(motion.stride(.6 - 1e-9)[0], 1.0, places=6); self.assertEqual(motion.stride(1.0), motion.stride(0.0))
        position, lift = motion.stride(.8); self.assertAlmostEqual(position, 0.0); self.assertAlmostEqual(lift, 1.0)
        self.assertAlmostEqual(motion.stride_half(1.8, .6, .6), .324)

    def test_planted_contact_stays_on_the_floor_and_covers_the_stride(self):
        length, lean, base = motion.limb_geometry((0, 0, 1.0), (0, 0, .2), (0, 0, .25))
        self.assertAlmostEqual(length, 1.0); self.assertAlmostEqual(lean, 0.0); self.assertAlmostEqual(base, 0.0)
        for flat in (True, False):
            for position in (-1, -.4, 0, .5, 1):
                angle, y, z = motion.planted(length, lean, base, 0, position, 0.0, .3, max_swing=12, flat_feet=flat)
                tip_y, tip_z = self.tip(1.0, length, angle, lean, 0, y, z)
                self.assertAlmostEqual(tip_y, .3 * position, places=6); self.assertAlmostEqual(tip_z, 0.0, places=6)
                self.assertLessEqual(abs(angle), 12 + 1e-6)          # the rest of the stride is made up by translation

    def test_swing_lifts_by_step_height_and_roll_raises_a_tilted_foot(self):
        length, lean, base = motion.limb_geometry((0, 0, 1.0), (0, 0, .2), (0, 0, .25))
        _, y, z = motion.planted(length, lean, base, 0, 0.0, 1.0, .3, step_height=.07)
        self.assertAlmostEqual(self.tip(1.0, length, 0.0, lean, 0, y, z)[1], .07, places=6)
        angle, y, z = motion.planted(length, lean, base, 0, 1.0, 0.0, .3, foot_radius=.1)
        self.assertAlmostEqual(self.tip(1.0, length, angle, lean, 0, y, z)[1], .1 * abs(math.sin(math.radians(angle))), places=6)

    def test_pitched_and_lifted_body_still_plants_a_leaning_limb(self):
        head, tail, pivot = (.3, -.24, .8), (.28, -.38, .2), (0, 0, .25)
        length, lean, base = motion.limb_geometry(head, tail, pivot, pitch=30, lift=.12)
        posed = pivot[2] + .12 + (head[1] - pivot[1]) * math.sin(math.radians(30)) + (head[2] - pivot[2]) * math.cos(math.radians(30))
        angle, y, z = motion.planted(length, lean, base, 30, 0.0, 0.0, .324, flat_feet=False)
        th = math.radians(30); world_z = y * math.sin(th) + z * math.cos(th)     # offset back out of the pitched frame
        a = math.radians(angle - lean + 30)
        self.assertAlmostEqual(posed + world_z - length * math.cos(a), 0.0, places=6)


class VendorTests(unittest.TestCase):
    def test_vendor_writes_a_lock_and_check_detects_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'studio'; godot = Path(tmp) / 'addons'
            code, text = run(['vendor', '--target', str(target), '--godot', str(godot)]); self.assertEqual(code, 0)
            lock = json.loads((target / pipeline.LOCK).read_text()); self.assertEqual(lock['module'], pipeline.MODULE)
            self.assertEqual({f['name'] for f in lock['files']}, {'painterly.py', 'motion.py', 'painted_lighting.gdshaderinc'})
            self.assertEqual(run(['vendor', '--target', str(target), '--check'])[0], 0)
            (target / 'motion.py').write_text('changed')
            code, text = run(['vendor', '--target', str(target), '--check']); self.assertEqual(code, 1)
            self.assertEqual(json.loads(text)['problems'][0]['problem'], 'changed since vendoring')


class ValidateGlbTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.path = Path(self.tmp.name) / 'model.glb'

    def tearDown(self):
        self.tmp.cleanup()

    def test_good_model_is_ready_and_reports_clips(self):
        glb(self.path, {'Idle': ([0.0, .5, 1.0], [turn(0), turn(10), turn(0)])})
        result = pipeline.validate_glb(self.path, ['Idle'], ['Idle'])
        self.assertTrue(result['ready'], result['issues']); self.assertEqual(result['stats']['clips']['Idle']['seconds'], 1.0)
        self.assertEqual(result['stats']['images'], ['painted_albedo']); self.assertEqual(result['stats']['triangles'], 1)

    def test_open_loop_missing_clip_bad_weights_and_missing_texture_are_reported(self):
        glb(self.path, {'Walk': ([0.0, 1.0], [turn(0), turn(25)])}, weights=(.5, 0.0, 0.0, 0.0), textured=False)
        result = pipeline.validate_glb(self.path, ['Walk', 'Greet'], ['Walk'])
        codes = {i['code'] for i in result['issues']}; self.assertFalse(result['ready'])
        self.assertEqual(codes, {'loop_does_not_close', 'missing_clip', 'weights_not_normalised', 'material_without_texture'})

    def test_negated_quaternion_counts_as_the_same_pose(self):
        glb(self.path, {'Spin': ([0.0, 1.0], [turn(0), tuple(-v for v in turn(0))])})
        self.assertTrue(pipeline.validate_glb(self.path, loops=['Spin'])['ready'])


@unittest.skipUnless(importlib.util.find_spec('numpy') and importlib.util.find_spec('PIL'), 'numpy and Pillow are needed for the review tool')
class ReviewTests(unittest.TestCase):
    def test_compare_finds_the_painting_colours_in_a_render(self):
        import companion_review as review
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            painting = Image.new('RGB', (300, 330), 'white'); painting.paste((200, 90, 40), (20, 20, 280, 170)); painting.paste((250, 220, 170), (20, 170, 280, 310))
            render = Image.new('RGB', (200, 200), (120, 180, 230)); render.paste((206, 96, 44), (20, 20, 180, 100)); render.paste((244, 214, 176), (20, 100, 180, 180))
            a = Path(tmp) / 'painting.png'; b = Path(tmp) / 'render.png'; painting.save(a); render.save(b)
            result = review.compare(a, b, k=2)
            self.assertEqual(result['found'], 2); self.assertLessEqual(result['worst_channel_difference'], 8)
            sampled = review.sample_points(a, {'coat': (150, 90)})[0]; self.assertEqual(sampled['colour'], '#c85a28'); self.assertEqual(sampled['spread'], 0.0)
            sheet = review.sheet(Path(tmp) / 'sheet.png', [('row', [str(a), str(b)])]); self.assertTrue(Path(sheet['sheet']).is_file())


if __name__ == '__main__':
    unittest.main()
