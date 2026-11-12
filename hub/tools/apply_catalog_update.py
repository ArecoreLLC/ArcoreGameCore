"""Merge capability classifications and curated media into an existing SQLite library.

Requires an explicit --library. Originals and existing editorial/user fields are preserved.
An online SQLite backup and existing managed media copies precede any catalog mutation.
"""
import argparse, datetime, hashlib, json, shutil, sqlite3, uuid
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def apply(root, seed, taxonomy, selections):
    root=Path(root).resolve(); db=root/'catalog.sqlite3'
    if not db.is_file(): raise ValueError('Existing library database required')
    with closing(sqlite3.connect(db,timeout=30)) as conn:
        return _apply(root,seed,taxonomy,selections,conn)
def _apply(root,seed,taxonomy,selections,conn):
    conn.execute('PRAGMA foreign_keys=ON')
    if conn.execute('PRAGMA user_version').fetchone()[0]!=1: raise ValueError('Unsupported schema version')
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    backup=root/'backups'/('before-catalog-v2-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    backup.mkdir(parents=True)
    with closing(sqlite3.connect(backup/'catalog.sqlite3')) as dest: conn.backup(dest)
    for (raw,) in conn.execute('SELECT data FROM media'):
        m=json.loads(raw); src=Path(m['stored_path'])
        if not src.is_file() or digest(src)!=m['sha256']: raise ValueError('Existing media missing or corrupt: '+str(src))
        dest=backup/'media'/src.name; dest.parent.mkdir(exist_ok=True)
        if not dest.exists(): shutil.copy2(src,dest)
    # Validate everything before any database mutation.
    games={r[0] for r in conn.execute('SELECT id FROM projects')}
    for s in selections:
        if s['project_id'] not in games: raise ValueError('Unknown project '+s['project_id'])
        if digest(s['source_path'])!=s['sha256']: raise ValueError('Source hash changed: '+s['source_path'])
    media_root=root/'media'; media_root.mkdir(exist_ok=True)
    paths={}
    for s in selections:
        dest=media_root/(s['sha256']+Path(s['source_path']).suffix.lower())
        if dest.exists():
            if digest(dest)!=s['sha256']: raise ValueError('Managed media hash mismatch')
        else:
            temp=dest.with_name(dest.name+'.'+uuid.uuid4().hex+'.tmp')
            try:
                shutil.copy2(s['source_path'],temp)
                if digest(temp)!=s['sha256']: raise ValueError('Copy verification failed')
                temp.replace(dest)
            finally:
                if temp.exists(): temp.unlink()
        paths[s['sha256']]=str(dest)
    added_media=0; added_tags=0
    with conn:
        # Acquire write lock before reading fields to merge, preventing lost user edits.
        conn.execute('BEGIN IMMEDIATE')
        for t in taxonomy:
            row=conn.execute('SELECT data FROM taxonomy WHERE id=?',(t['id'],)).fetchone()
            if row:
                existing=json.loads(row[0])
                for key in ['level','group','parent_id','acceptance']:
                    if key in t and key not in existing: existing[key]=t[key]
                conn.execute('UPDATE taxonomy SET data=? WHERE id=?',(json.dumps(existing),t['id']))
            else: conn.execute('INSERT INTO taxonomy VALUES(?,?)',(t['id'],json.dumps(t)))
        for g in seed:
            row=conn.execute('SELECT data FROM projects WHERE id=?',(g['id'],)).fetchone()
            if not row: continue
            existing=json.loads(row[0]); ids={c['id'] for c in existing['capabilities']}
            for c in g['capabilities']:
                if c['id'].startswith('cap-') and c['id'] not in ids:
                    existing['capabilities'].append(c); ids.add(c['id']); added_tags+=1
            conn.execute('UPDATE projects SET data=?,updated_at=? WHERE id=?',(json.dumps(existing),now,g['id']))
        existing={(m['project_id'],m['sha256'],m['kind']) for (raw,) in conn.execute('SELECT data FROM media') for m in [json.loads(raw)]}
        for s in selections:
            key=(s['project_id'],s['sha256'],s['kind'])
            if key in existing: continue
            m={k:s[k] for k in ['project_id','kind','title','caption','alt_text','rights','credit','sort_order','width','height','duration_seconds','source_path','sha256','curation','content_role','review_notes']}
            m.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'gamecore:'+':'.join(key))),stored_path=paths[s['sha256']],status='draft',approved_at=None,created_at=now)
            conn.execute('INSERT INTO media VALUES(?,?,?)',(m['id'],m['project_id'],json.dumps(m)))
            existing.add(key); added_media+=1
        conn.execute("INSERT OR REPLACE INTO meta VALUES('catalog-v2-curation',?)",(now,))
    assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not conn.execute('PRAGMA foreign_key_check').fetchall()
    report=dict(backup=str(backup),added_media=added_media,added_capability_links=added_tags,media_total=conn.execute('SELECT COUNT(*) FROM media').fetchone()[0],taxonomy_total=conn.execute('SELECT COUNT(*) FROM taxonomy').fetchone()[0],integrity='ok',timestamp=now)
    conn.close(); return report
def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--library',required=True)
    parser.add_argument('--selections',type=Path,help='Project-specific media selection JSON; imports media only, without taxonomy/catalog reseeding')
    args=parser.parse_args(argv)
    read=lambda name:json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))
    if args.selections:
        selections=json.loads(args.selections.read_text(encoding='utf-8'))
        if not isinstance(selections,list): raise ValueError('Selections must be an array')
        result=apply(args.library,[],[],selections)
    else:
        result=apply(args.library,read('catalog.json'),read('taxonomy.json'),read('marketing-selection.json'))
    print(json.dumps(result,indent=2))
    return result
if __name__=='__main__': main()
