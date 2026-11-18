"""Add visually reviewed improvement captures, preserving existing editorial records."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'tools'))
from apply_catalog_update import apply

library = Path(os.environ['APPDATA']) / 'com.arcore.gamecore'
selection = json.loads((HERE / 'selection.json').read_text(encoding='utf-8'))
for item in selection:
    assert hashlib.sha256(Path(item['source_path']).read_bytes()).hexdigest() == item['sha256']
backup = apply(library, [], [], [])
with sqlite3.connect(library / 'catalog.sqlite3') as conn:
    projects_before = dict(conn.execute('SELECT id,data FROM projects'))
    media_before = dict(conn.execute('SELECT id,data FROM media'))
    if 'clockwork-courier' not in projects_before:
        game = json.loads((HERE.parent / 'screenshots-2026-11-12/lantern-heist-project.json').read_text(encoding='utf-8'))
        game.update(id='clockwork-courier', name='Clockwork Courier', path='X:/Projects/Games/Clockwork-Courier',
            description='Carry a fragile clockwork parcel over a terracotta ridge and stop at the depot.',
            logic='Drive the fixed buggy, protect cargo from sudden velocity changes, and stop in the depot for 1.5 seconds to deliver.',
            reuse='Standalone Snap Rally descendant retaining donor module names; locally pinned portable GameCore headers.',
            assets='Starter buggy, attached parcel and short terracotta ridge route.',
            limitations='Development prototype; cargo uses an attached impact-damage model. Packaging, controller hardware and replay not validated in this media refresh.',
            commands=['./Scripts/Play.ps1'], review_date='2026-11-13',
            audit=dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),errors=[],method='README and screenshot inspection; no fresh build or playtest.'))
        game['media_candidates'] = [dict(path=selection_item['source_path'], name='First playable', kind='screenshot') for selection_item in selection if selection_item['project_id']=='clockwork-courier']
        conn.execute('INSERT INTO projects VALUES(?,?,?,?)',(game['id'],game['name'],json.dumps(game),datetime.datetime.now(datetime.timezone.utc).isoformat()))
        (HERE / 'clockwork-courier-project.json').write_text(json.dumps(game,indent=2)+'\n',encoding='utf-8')
report = apply(library, [], [], selection)
with sqlite3.connect(library / 'catalog.sqlite3') as conn:
    for table, before in [('projects',projects_before),('media',media_before)]:
        after = dict(conn.execute(f'SELECT id,data FROM {table}'))
        assert all(after[id] == value for id,value in before.items()), f'{table} changed concurrently; inspect before reporting preservation'
    stored = [json.loads(raw) for raw, in conn.execute('SELECT data FROM media')]
    for item in selection:
        matches = [m for m in stored if m['project_id']==item['project_id'] and m['sha256']==item['sha256']]
        assert matches
        for m in matches:
            assert hashlib.sha256(Path(m['stored_path']).read_bytes()).hexdigest()==item['sha256']
    report.update(pre_project_backup=backup['backup'],existing_records_preserved=True,
        selected_count=len(selection),games_updated=len({s['project_id'] for s in selection}),
        no_new_capture=['Chroma-Turf'],excluded={'candidate_20':'Partial start framing; retained full museum view instead.'})
(HERE / 'import-receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
