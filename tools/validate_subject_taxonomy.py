"""Validate the shared subject taxonomy and example instances."""
import argparse,json,sys
from pathlib import Path
from subject_taxonomy import load_catalog,validate_catalog


def validate(root):
    catalog_path=root/'shared'/'subject-taxonomy'/'catalog.v1.json'
    try:catalog=load_catalog(catalog_path)
    except (OSError,json.JSONDecodeError) as error:return [f'{catalog_path}: {error}']
    errors=validate_catalog(catalog)
    example_path=root/'shared'/'subject-taxonomy'/'spider.example.json'
    try:example=json.loads(example_path.read_text(encoding='utf-8'))
    except (OSError,json.JSONDecodeError) as error:return errors+[f'{example_path}: {error}']
    if example.get('schema_version')!=catalog['schema_version']:errors.append('spider example schema version mismatch')
    if example.get('taxonomy_version')!=catalog['taxonomy_version']:errors.append('spider example taxonomy version mismatch')
    if example.get('profile') not in catalog['profiles']:errors.append('spider example references unknown profile')
    for part in example.get('observed_parts',[]):
        if part.get('part') not in catalog['parts']:errors.append(f'spider example references unknown part {part.get("part")}')
        if part.get('state') not in {'visible','partially_visible','occluded','absent','ambiguous','unknown'}:errors.append(f'spider example has invalid state {part.get("state")}')
    return errors


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);args=parser.parse_args()
    errors=validate(args.root)
    print(json.dumps({'status':'failed' if errors else 'passed','errors':errors},indent=2))
    sys.exit(bool(errors))
