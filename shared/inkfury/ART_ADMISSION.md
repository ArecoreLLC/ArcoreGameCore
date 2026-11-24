# Verified art admission 0.1.0

`tools/art_admission.py` validates rendered batches before admitting them to a
consumer-owned library. Requires Python 3 and Pillow; no renderer or game assets
are bundled. The caller owns licensing review and artistic approval.

## Contract

`admit(manifest_path, batch_path, library_path, *, layout=Layout(), replace=False,
receipt_name="receipt.json", receipt_root=None, source_key="svg",
rig_recipes=("articulated-v1", "articulated-volume-v2"))` returns the updated
library dictionary after publishing verified atlases and the library JSON.

The input manifest has `subjects`: records with unique ASCII `id` and a source
path under `source_key`, relative to the manifest. Optional `rig` points to JSON
with `source_sha256`. A completed receipt has `status: "complete"` and matching
`subjects` with `id`, `source_sha256`, atlas `sha256`, `frame_size`, `columns`,
and `rows`. Rigged records additionally carry `rig_sha256`. The existing library
has `assets` with `id`, `path`, and `sha256`; paths are relative to its parent.
An empty library is `{"assets": []}`. Other library fields are preserved.

`Layout` supplies frame size, columns, rows, clip names, margin, and atlas/model/
frame path templates. Defaults describe four rows of four 384-pixel frames;
callers can choose different geometry and names. `receipt_root` makes stored
receipt references relative to that root. Paths must stay inside their roots.

Admission checks source/rig hashes, source-to-rig binding, complete matching IDs,
PNG validity and layout, existing library bytes, and destination safety. Changed
assets require explicit `replace=True`; replacements record `supersedes_sha256`.
It stages all copies and backups before publication, publishes the catalog last,
and attempts rollback on publication errors. Errors are `ValidationError` or
`InstallationError`. Single writer only: this is not a crash-atomic transaction
across files, concurrent-writer lock, or a substitute for durable backups.

`validate_articulation(batch, *, layout=Layout(), receipt_name="receipt.json",
report_path=None)` checks GLB structure/accessor bounds and animation exports,
rendered frames, margins and clip variation. It does not certify animation quality.

## Reuse review

Decision: **extract-adapter**. Source identity, layout, clip names, paths and rig
recipes are parameters. The consumer scripts `tools/install-rendered-batch.py`
and `tools/validate-articulated-batch.py` retain project paths and art policy.
Default settings reflect the first consumer but are not mandatory restrictions.

Synthetic alternate-use tests use a robot drawing, a 3-by-2 atlas of 12-pixel
frames, walk/jump clips, custom paths and a different source key. Tests also cover
tampered sources, malformed GLBs, unsafe paths, copy failures and rollback.
Run `python -m unittest discover -s tools/tests -p test_art_admission.py -v`.
See [validation](VALIDATION.md) for actual results and limitations.
