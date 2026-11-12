import importlib.util, json, sqlite3, tempfile, unittest
from contextlib import closing
from pathlib import Path
spec=importlib.util.spec_from_file_location('update',Path(__file__).with_name('apply_catalog_update.py'))
update=importlib.util.module_from_spec(spec);spec.loader.exec_module(update)
class UpdateTests(unittest.TestCase):
    def test_project_selection_mode_does_not_reseed(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            selection=Path(tmp)/'selected.json'; selection.write_text('[{"project_id":"test"}]')
            with patch.object(update,'apply',return_value={'added_media':1}) as call:
                update.main(['--library',tmp,'--selections',str(selection)])
                call.assert_called_once_with(tmp,[],[],[{'project_id':'test'}])

    def test_idempotence_preserves_edits_and_backs_up_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); original=root/'original.png';original.write_bytes(b'preserved original fixture')
            db=root/'catalog.sqlite3';c=sqlite3.connect(db)
            c.executescript('PRAGMA user_version=1; CREATE TABLE projects(id TEXT PRIMARY KEY,name TEXT,data TEXT,updated_at TEXT); CREATE TABLE taxonomy(id TEXT PRIMARY KEY,data TEXT); CREATE TABLE media(id TEXT PRIMARY KEY,project_id TEXT REFERENCES projects(id),data TEXT); CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);')
            game=dict(id='test',name='User title',description='User prose',capabilities=[],marketing={'pitch':'User pitch'})
            c.execute('INSERT INTO projects VALUES(?,?,?,?)',('test','User title',json.dumps(game),'before'));c.commit()
            seed=[dict(id='test',capabilities=[dict(id='cap-a',state='prototype',evidence='source')])]
            taxa=[dict(id='cap-a',level='capability')]
            s=dict(project_id='test',kind='screenshot',title='Selected',caption='Caption',alt_text='Alt',rights='Pending',credit='Original',sort_order=0,width=10,height=10,duration_seconds=None,source_path=str(original),sha256=update.digest(original),curation='selected',content_role='prototype-capture',review_notes='Reviewed')
            first=update.apply(root,seed,taxa,[s]);self.assertEqual(first['added_media'],1)
            data=json.loads(c.execute('SELECT data FROM projects').fetchone()[0]);self.assertEqual(data['marketing'],game['marketing']);self.assertEqual(data['description'],'User prose')
            m=json.loads(c.execute('SELECT data FROM media').fetchone()[0]);m['title']='User edited title'
            c.execute('UPDATE media SET data=?',(json.dumps(m),));c.commit()
            second=update.apply(root,seed,taxa,[s]);self.assertEqual(second['added_media'],0);self.assertEqual(second['added_capability_links'],0)
            self.assertEqual(json.loads(c.execute('SELECT data FROM media').fetchone()[0])['title'],'User edited title')
            self.assertEqual(original.read_bytes(),Path(m['stored_path']).read_bytes())
            self.assertEqual((Path(second['backup'])/'media'/Path(m['stored_path']).name).read_bytes(),original.read_bytes())
            with closing(sqlite3.connect(Path(first['backup'])/'catalog.sqlite3')) as old: self.assertEqual(old.execute('SELECT COUNT(*) FROM media').fetchone()[0],0)
            s['sha256']='wrong'
            with self.assertRaisesRegex(ValueError,'Source hash changed'):update.apply(root,seed,taxa,[s])
            self.assertEqual(c.execute('SELECT COUNT(*) FROM media').fetchone()[0],1)
            c.close()
if __name__=='__main__':unittest.main()
