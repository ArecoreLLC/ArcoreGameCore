"""Import the reviewed November 12 Games-folder selection into the local library."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
HUB = HERE.parents[1]
sys.path.insert(0, str(HUB / 'tools'))
from apply_catalog_update import apply

games_root = Path('X:/Projects/Games')
library = Path(os.environ['APPDATA']) / 'com.arcore.gamecore'
choices = json.loads((HERE / 'choices.json').read_text())
choices['Chroma-Turf'] = 'Docs/Media/Prototype-2026-11-12.png'
captions = [
    'Combat arena with the crab boss and mutation controls.',
    'Hero view of the cardboard fort and squad controls.',
    'Meadow puzzle with contraption pieces and progression HUD.',
    'Shop room with colored stalls and the inventory HUD.',
    'Crystal chamber with a glowing resonator and bridge.',
    'Raft construction grid with the salvage and build controls.',
    'Graybox structure with the glider challenge HUD.',
    'Museum prototype with disguise and treasure controls.',
    'Lantern-lit museum rooms with patrol and heist controls.',
    'Mirror chamber with a reflected beam and detection HUD.',
    'Planning view of the garden squad and objective.',
    'Patrol arena with enemies, coins and the tactical display.',
    'Combat arena showing the scrap mech, enemies and combat HUD.',
    'Three colored platforms in the sabotage prototype.',
    'Suspension vehicle facing a bowling lane and pins.',
    'Tugboat at the harbor dock with navigation controls.',
    'Current graybox terrain prototype with a single tile on a platform.',
]
selections = []
for (folder, relative), caption in zip(choices.items(), captions):
    source = games_root / folder / relative
    with Image.open(source) as im:
        im.load()
        width, height = im.size
    selections.append(dict(
        project_id=folder.lower(), source_path=str(source),
        sha256=hashlib.sha256(source.read_bytes()).hexdigest(), kind='screenshot',
        title=folder.replace('-', ' ') + ' — prototype', caption=caption,
        alt_text=caption, width=width, height=height, duration_seconds=None,
        sort_order=0, curation='selected', content_role='prototype-capture',
        review_notes='Visually inspected for catalog use; prototype state, not a new gameplay acceptance result.',
        rights='External publication rights unreviewed; retain as draft pending review.',
        credit='Source: ' + source.as_posix(), status='draft',
        review_evidence='contact-sheet.jpg; Chroma Turf inspected separately',
        reviewed_at='2026-11-12', selection_version=1))
(HERE / 'selection.json').write_text(json.dumps(selections, indent=2) + '\n', encoding='utf-8')

# Use the existing importer to back up the complete library before adding a missing game.
backup = apply(library, [], [], [])
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
with sqlite3.connect(library / 'catalog.sqlite3') as conn:
    original_projects = dict(conn.execute('SELECT id,data FROM projects'))
    if 'lantern-heist' not in original_projects:
        game = dict(id='lantern-heist', name='Lantern Heist', path=str(games_root / 'Lantern-Heist'),
            engine='Unreal 5.8.4 / C++', dimension='3d', kind='game', maturity='prototype',
            description='Steal the Vault relic and return to the Rotunda exit while a Custodian patrols and investigates decoys.',
            logic='Operate the lantern and prisms to change routes; vault gaps and evade the Custodian.',
            reuse='Standalone descendant of Haunt and Haul; retains donor module names.',
            assets='Engine primitive museum scene and lantern lighting.',
            limitations='Editor development prototype. No fresh gameplay acceptance performed during screenshot import.',
            capabilities=[], mechanics=[], provider_links=[],
            marketing=dict(tagline='',pitch='',audience='',release_status='Prototype',website='',credits='',notes=''),
            commands=['./Scripts/Play-Lantern.ps1'], review_date='2026-11-12',
            build_status='not_run',playtest_status='not_run',asset_counts={},asset_file_count=0,source_file_count=0,
            evidence_files=[],historical_checks=[],media_candidates=[],subgames=[],
            revision=dict(head=None,dirty=False,note='Revision not audited in this media import.'),
            audit=dict(timestamp_utc=now,errors=[],method='README and screenshot inspection; file index not audited.'))
        conn.execute('INSERT INTO projects VALUES(?,?,?,?)', (game['id'],game['name'],json.dumps(game),now))
        (HERE / 'lantern-heist-project.json').write_text(json.dumps(game,indent=2)+'\n',encoding='utf-8')
report = apply(library, [], [], selections)
with sqlite3.connect(library / 'catalog.sqlite3') as conn:
    assert all(conn.execute('SELECT data FROM projects WHERE id=?',(id,)).fetchone()[0] == raw for id,raw in original_projects.items())
    media = [json.loads(raw) for raw, in conn.execute('SELECT data FROM media')]
    coverage = {}
    for folder in choices:
        matches = [m for m in media if m['project_id']==folder.lower() and m['kind']=='screenshot']
        assert matches, folder
        for m in matches:
            assert hashlib.sha256(Path(m['stored_path']).read_bytes()).hexdigest() == m['sha256']
        coverage[folder] = len(matches)
report.update(pre_project_backup=backup['backup'],coverage=coverage,existing_projects_preserved=True)
(HERE / 'import-receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
