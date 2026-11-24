"""Portable regression fixtures: no InkFury assets or runtime required."""
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

MODULE = Path(os.environ.get("ART_ADMISSION_MODULE", str(Path(__file__).resolve().parents[1] / "art_admission.py")))
spec = importlib.util.spec_from_file_location("admission_under_test", MODULE)
art = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = art
spec.loader.exec_module(art)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.batch = self.root / "export"
        self.library = self.root / "runtime/catalog.json"
        self.manifest = self.root / "inputs/source.json"
        self.layout = art.Layout(frame_size=12, columns=3, rows=2, clips=("walk", "jump"), margin=1,
                                 atlas="sheets/{id}/atlas.png", model="models/{id}.glb",
                                 frame="renders/{id}/{frame:03d}.png")
        self.source = self.manifest.parent / "drawing.txt"
        self.source.parent.mkdir()
        self.source.write_text("test drawing")
        write_json(self.manifest, {"subjects": [{"id": "robot", "drawing": "drawing.txt"}]})
        write_json(self.library, {"assets": [], "version": 7})
        png = self.batch / "sheets/robot/atlas.png"
        png.parent.mkdir(parents=True)
        Image.new("RGBA", (36, 24), "red").save(png)
        self.record = dict(id="robot", source_sha256=art.digest(self.source), sha256=art.digest(png),
                           frame_size=12, columns=3, rows=2)
        self.receipt = self.batch / "audit.json"
        self.save_receipt()

    def save_receipt(self):
        write_json(self.receipt, {"status": "complete", "subjects": [self.record]})

    def admit(self, **kwargs):
        return art.admit(self.manifest, self.batch, self.library, layout=self.layout,
                         receipt_name="audit.json", source_key="drawing", **kwargs)

    def test_alternate_layout_paths_and_idempotence(self):
        result = self.admit(receipt_root=self.root)
        self.assertEqual(result["version"], 7)
        self.assertEqual(result["assets"][0]["receipt"], "export/audit.json")
        self.assertEqual(art.digest(self.library.parent / "robot.png"), self.record["sha256"])
        self.assertEqual(result, self.admit(receipt_root=self.root))

    def test_sources_rigs_and_rig_binding(self):
        self.source.write_text("changed")
        with self.assertRaisesRegex(art.ValidationError, "Source changed"):
            self.admit()
        self.source.write_text("test drawing")
        rig = self.manifest.parent / "rig.json"
        write_json(rig, {"source_sha256": "wrong"})
        write_json(self.manifest, {"subjects": [{"id": "robot", "drawing": "drawing.txt", "rig": "rig.json"}]})
        self.record["rig_sha256"] = art.digest(rig)
        self.save_receipt()
        with self.assertRaisesRegex(art.ValidationError, "different source"):
            self.admit()
        write_json(rig, {"source_sha256": self.record["source_sha256"]})
        with self.assertRaisesRegex(art.ValidationError, "Rig changed"):
            self.admit()
        self.record["rig_sha256"] = art.digest(rig)
        self.save_receipt()
        self.admit()

    def test_invalid_paths(self):
        for value in ("../outside", "/absolute", "C:/outside", "C:relative", "..\\outside", "//server/share", "x:stream"):
            with self.subTest(value=value), self.assertRaises(art.ValidationError):
                art.safe_path(self.root, value)

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            try:
                (self.root / "escape").symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"Symlinks unavailable: {exc}")
            with self.assertRaises(art.ValidationError):
                art.safe_path(self.root, "escape/file.png")

    def test_duplicate_and_traversing_ids(self):
        for records in ([self.record, self.record], [dict(self.record, id="../robot")], [self.record, dict(self.record, id="ROBOT")]):
            write_json(self.receipt, {"status": "complete", "subjects": records})
            with self.assertRaises(art.ValidationError):
                self.admit()
        self.assertFalse((self.library.parent / "robot.png").exists())

    def test_unsafe_existing_library_path(self):
        write_json(self.library, {"assets": [dict(self.record, path="../outside.png")]})
        with self.assertRaises(art.ValidationError):
            self.admit(replace=True)

    def test_corruption_and_layout_mismatch(self):
        self.record["rows"] = 4
        self.save_receipt()
        with self.assertRaisesRegex(art.ValidationError, "layout"):
            self.admit()
        png = self.batch / "sheets/robot/atlas.png"
        png.write_bytes(b"broken")
        self.record["sha256"] = art.digest(png)
        self.save_receipt()
        with self.assertRaises(art.ValidationError):
            self.admit()

    def test_replacement_requires_verified_old_bytes(self):
        self.admit()
        old = self.record["sha256"]
        png = self.batch / "sheets/robot/atlas.png"
        Image.new("RGBA", (36, 24), "blue").save(png)
        self.record["sha256"] = art.digest(png)
        self.save_receipt()
        with self.assertRaisesRegex(art.ValidationError, "overwrite"):
            self.admit()
        self.assertEqual(self.admit(replace=True)["assets"][0]["supersedes_sha256"], old)
        (self.library.parent / "robot.png").write_bytes(b"corrupt runtime")
        with self.assertRaisesRegex(art.ValidationError, "Runtime file"):
            self.admit(replace=True)

    def test_copy_failure_leaves_library_untouched(self):
        before = self.library.read_bytes()
        with patch.object(art.shutil, "copy2", side_effect=OSError("disk full")):
            with self.assertRaises(art.ValidationError):
                self.admit()
        self.assertEqual(before, self.library.read_bytes())
        self.assertEqual([self.library], list(self.library.parent.iterdir()))

    def test_manifest_publish_failure_rolls_back_new_and_existing_files(self):
        for existing in (False, True):
            with self.subTest(existing=existing):
                if existing:
                    self.admit()
                before = {p.name: p.read_bytes() for p in self.library.parent.iterdir()}
                original = art.os.replace
                def fail_manifest(source, destination):
                    if Path(source).name == "manifest":
                        raise OSError("injected publish failure")
                    return original(source, destination)
                with patch.object(art.os, "replace", side_effect=fail_manifest):
                    with self.assertRaisesRegex(art.InstallationError, "rollback completed"):
                        self.admit(replace=True)
                self.assertEqual(before, {p.name: p.read_bytes() for p in self.library.parent.iterdir()})

    def test_late_invalid_subject_does_not_publish_earlier_subject(self):
        manifest = json.loads(self.manifest.read_text())
        manifest["subjects"].append(dict(manifest["subjects"][0], id="second"))
        write_json(self.manifest, manifest)
        write_json(self.receipt, {"status": "complete", "subjects": [self.record, dict(self.record, id="second", source_sha256="bad")]})
        before = self.library.read_bytes()
        with self.assertRaises(art.ValidationError):
            self.admit()
        self.assertEqual(before, self.library.read_bytes())
        self.assertFalse((self.library.parent / "robot.png").exists())

    def model(self):
        binary = bytearray()
        views, accessors = [], []
        def accessor(fmt, rows, component, shape):
            start = len(binary)
            for row in rows:
                binary.extend(struct.pack(fmt, *row))
            views.append(dict(buffer=0, byteOffset=start, byteLength=len(binary)-start))
            accessors.append(dict(bufferView=len(views)-1, componentType=component, count=len(rows), type=shape))
            return len(accessors)-1
        weights = accessor("<4f", [(1, 0, 0, 0)], 5126, "VEC4")
        joints = accessor("<4H", [(0, 0, 0, 0)], 5123, "VEC4")
        times = accessor("<f", [(0,), (1,)], 5126, "SCALAR")
        values = accessor("<3f", [(0, 0, 0), (1, 0, 0)], 5126, "VEC3")
        model = dict(nodes=[{}], skins=[dict(joints=[0])], accessors=accessors, bufferViews=views,
                     meshes=[dict(primitives=[dict(attributes=dict(WEIGHTS_0=weights, JOINTS_0=joints))])],
                     animations=[dict(name=name, samplers=[dict(input=times, output=values)],
                                      channels=[dict(sampler=0, target=dict(node=0, path="translation"))]) for name in self.layout.clips])
        return model, binary

    def write_model(self, model, binary):
        encoded = json.dumps(model).encode()
        encoded += b" " * (-len(encoded) % 4)
        binary += b"\x00" * (-len(binary) % 4)
        raw = struct.pack("<4sII", b"glTF", 2, 28 + len(encoded) + len(binary))
        raw += struct.pack("<II", len(encoded), 0x4E4F534A) + encoded
        raw += struct.pack("<II", len(binary), 0x004E4942) + binary
        path = self.batch / "models/robot.glb"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(raw)

    def frames(self, static=False, border=False):
        folder = self.batch / "renders/robot"
        folder.mkdir(parents=True, exist_ok=True)
        for i in range(6):
            im = Image.new("RGBA", (12, 12))
            im.putpixel((0 if border else 2, 2), (255, 0 if static else i * 30, 0, 255))
            im.save(folder / f"{i:03d}.png")

    def validate(self):
        return art.validate_articulation(self.batch, layout=self.layout, receipt_name="audit.json")

    def test_alternate_articulation_and_no_implicit_report(self):
        self.write_model(*self.model())
        self.frames()
        records = self.validate()
        self.assertEqual(records[0]["clips"], 2)
        self.assertEqual(records[0]["bones"], 1)
        self.assertFalse((self.batch / "rig-validation.json").exists())

    def test_frame_margins_and_static_clips(self):
        self.write_model(*self.model())
        for kwargs in (dict(static=True), dict(border=True)):
            self.frames(**kwargs)
            with self.assertRaises(art.ValidationError):
                self.validate()

    def test_malformed_glb_and_accessor_bounds(self):
        self.frames()
        model, binary = self.model()
        model["bufferViews"][0]["byteLength"] = 1
        self.write_model(model, binary)
        with self.assertRaisesRegex(art.ValidationError, "buffer view"):
            self.validate()
        (self.batch / "models/robot.glb").write_bytes(b"glTF")
        with self.assertRaises(art.ValidationError):
            self.validate()

    def test_bad_weights_times_and_clip_names(self):
        self.frames()
        for mutation in ("weights", "times", "clips", "sparse"):
            model, binary = self.model()
            if mutation == "weights":
                struct.pack_into("<f", binary, 0, 0.5)
            elif mutation == "times":
                struct.pack_into("<f", binary, model["bufferViews"][2]["byteOffset"], float("nan"))
            elif mutation == "clips":
                model["animations"][0]["name"] = "unknown"
            else:
                model["accessors"][0]["sparse"] = {}
            self.write_model(model, binary)
            with self.subTest(mutation=mutation), self.assertRaises(art.ValidationError):
                self.validate()


if __name__ == "__main__":
    unittest.main()
