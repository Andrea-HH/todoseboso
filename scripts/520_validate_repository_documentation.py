"""Validate documentation, provenance and positional splits using stdlib only."""
from pathlib import Path
from collections import Counter
import argparse
import csv
import hashlib
import json
import re
import subprocess
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]
DOCS=['README.md','documentation/README.md','documentation/project_scope_and_guidelines.md',
      'documentation/model_registry.md','documentation/experiment_index.md','documentation/reproducibility.md',
      'documentation/repository_organization.md','documentation/ai_usage.md','documentation/ai/README.md',
      'documentation/git_data_policy.md','configs/README.md','environments/README.md']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(relative):
    return json.loads((ROOT/relative).read_text(encoding='utf-8'))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--local-sources',action='store_true',help='Also compare optional original design JSON hashes; no data loading.')
    args=parser.parse_args()
    checks=Counter()
    for name in DOCS:
        p=ROOT/name
        assert p.is_file(),name
        text=p.read_text(encoding='utf-8')
        assert '\ufffd' not in text,name
        for raw in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)',text):
            if raw.startswith(('http:','https:','mailto:','#')):continue
            destination=unquote(raw.split('#',1)[0].strip('<>'))
            assert (p.parent/destination).exists(),f'Broken link: {name} -> {raw}'
            checks['local_links']+=1
    manifest=read('configs/experiments/manifest.json')
    for record in manifest['snapshots']:
        p=ROOT/record['snapshot']
        assert sha(p)==record['snapshot_sha256'],str(p)
        assert record['source'].startswith('outputs/modeling/')
        json.loads(p.read_text(encoding='utf-8'))
        if args.local_sources:
            assert sha(ROOT/record['source'])==record['source_sha256'],record['source']
        checks['design_snapshots']+=1
    a=read('configs/validation/original65.json')
    b=read('configs/validation/original65_plus_fresh16.json')
    assert len(a['folds'])==65 and len(b['folds'])==81
    assert a['folds']==b['folds'][:65]
    assert a['ordered_ids_sha256']==b['ordered_ids_sha256']
    protocols=Counter(f['protocol'] for f in a['folds'])
    assert protocols==dict(random=50,climate_profile=5,municipality=5,spatial=5),protocols
    for item in [a,b]:
        for fold in item['folds']:
            assert set(fold)=={'execution_index','protocol','repeat','fold','train_positions','validation_positions','inner'}
            tr=fold['train_positions'];va=fold['validation_positions']
            assert not set(tr)&set(va)
            assert sorted(tr+va)==list(range(138))
            held=[]
            for inner in fold['inner']:
                x=inner['train_relative_positions'];y=inner['validation_relative_positions']
                assert not set(x)&set(y)
                assert sorted(x+y)==list(range(len(tr)))
                held.extend(y)
            assert sorted(held)==list(range(len(tr))),f'Inner folds fail OOF partition: {fold["execution_index"]}'
            checks['fold_records']+=1
        for (protocol,repeat),counts in _outer_coverage(item['folds']).items():
            if protocol!='fresh_97_41': assert counts==Counter(range(138)),(protocol,repeat)
    for fold in b['folds'][65:]:
        assert fold['protocol']=='fresh_97_41'
        assert len(fold['train_positions'])==97 and len(fold['validation_positions'])==41
    registry=read('configs/model_registry.json')['models']
    assert len(set(m['id'] for m in registry))==len(registry)
    model_ids={m['id'] for m in registry}
    for model in registry:
        assert set(model.get('components',[]))<=model_ids,model['id']
        for key in ['documentation','implementation']:
            if key in model:assert (ROOT/model[key]).exists(),model[key]
        checks['registered_models']+=1
    with (ROOT/'documentation/ai/prompt_inventory.csv').open(encoding='utf-8',newline='') as stream:
        rows=list(csv.DictReader(stream))
    assert len({row['prompt_id'] for row in rows})==len(rows)
    for row in rows:
        assert sha(ROOT/row['prompt_file'])==row['sha256'],row['prompt_id']
        assert (ROOT/row['related_document']).is_file(),row['related_document']
        checks['prompt_records']+=1
    with (ROOT/'documentation/inventories/repository_files.csv').open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream):
            assert (ROOT/row['path']).is_file(),row['path']
            checks['inventory_files']+=1
    if (ROOT/'.git').exists():
        files=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split(chr(0))
        assert not any(p.startswith(('data/','outputs/','docs/resources/')) for p in files),'Private artifacts tracked'
        assert not any('__pycache__' in p or p.endswith('.pyc') for p in files),'Compiled caches still tracked'
        checks['git_policy']=1
    print(json.dumps(dict(status='passed',checks=dict(checks),local_source_hashes_checked=args.local_sources,
                          training_performed=False,private_data_loaded=False),ensure_ascii=False,indent=2))


def _outer_coverage(folds):
    coverage={}
    for f in folds:
        key=(f['protocol'],f['repeat'])
        coverage.setdefault(key,Counter()).update(f['validation_positions'])
    return coverage


if __name__=='__main__':main()
