import importlib.util,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('reuse_inventory',ROOT/'tools/reuse_inventory.py')
inventory=importlib.util.module_from_spec(spec);spec.loader.exec_module(inventory)

class ReuseRegistryTests(unittest.TestCase):
    def test_registry_links_and_status(self):
        data=json.loads((ROOT/'shared/reusable-modules.json').read_text());ids=set()
        for row in data['entries']:
            self.assertNotIn(row['id'],ids);ids.add(row['id'])
            self.assertIn(row['status'],['extracted','existing','candidate'])
            self.assertTrue((ROOT/row['guide']).is_file(),row['guide'])
            for file in row['files']:self.assertTrue((ROOT/file).is_file(),file)
            if row['status']=='candidate':self.assertEqual(row['files'],[]);self.assertTrue(row['limitations'])
            else:self.assertTrue(row['files'])
        self.assertIn('wing-patterns',ids);self.assertIn('timed-stroke-track',ids)
    def test_discovery_catalog_sources(self):
        capabilities={r['id'] for r in json.loads((ROOT/'hub/data/taxonomy.json').read_text(encoding='utf-8'))}
        projects={r['id']:r for r in json.loads((ROOT/'hub/data/catalog.json').read_text(encoding='utf-8'))}
        for filename,field,guide in [('shared/reusable-modules.json','entries','guide'),('shared/modules.json','modules','documentation')]:
            rows=json.loads((ROOT/filename).read_text())[field]
            self.assertEqual(len(rows),len({row['id'] for row in rows}))
            for row in rows:
                self.assertTrue((ROOT/row[guide]).is_file())
                for name in ['tags','aliases']:
                    self.assertTrue(all(isinstance(term,str) and term.strip() for term in row.get(name,[])))
                for capability in row.get('capability_ids',[]):self.assertIn(capability,capabilities)
                for project in row.get('source_project_ids',[]):self.assertIn(project,projects)
                for ref in row.get('catalog_mechanic_refs',[]):
                    self.assertIn(ref['mechanic_id'],{m['id'] for m in projects[ref['project_id']]['mechanics']})
                if field=='entries':self.assertTrue(set(row['languages']) <= {'cpp','csharp','gdscript','python'})
        hub=json.loads((ROOT/'shared/ecosystem.json').read_text())['mcp']['hub']
        self.assertIn('module_search',hub['implemented_tools'])
        self.assertIn('reusable_modules',hub['implemented_tools'])
    def test_source_inventory_never_runs_game(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'scripts').mkdir()
            (p/'scripts/example.gd').write_text('extends Node\nfunc _ready():\n    OS.execute("bad",[])\nconst X=preload("res://test.tres")\n')
            report=inventory.scan(p)
            self.assertEqual(report['file_count'],1);self.assertEqual(report['function_count'],1)
            self.assertEqual(report['files'][0]['resource_dependencies'],['res://test.tres'])
if __name__=='__main__':unittest.main()
