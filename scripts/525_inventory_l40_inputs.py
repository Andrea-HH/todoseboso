"""Read-only reconstruction of GeoC C4 input names; no PCA fit or yields loaded."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import ast

ROOT=Path(__file__).resolve().parents[1]
GEO=ROOT.parent/'fira/GeoC'


def main():
    import pandas as pd
    # Execute only this pure selection function; avoid importing GeoC's runtime
    # and optional configuration/training dependencies. Its source is hashed below.
    selection_path=GEO/'src/geocebada/evaluation/checkpoint04a.py'
    tree=ast.parse(selection_path.read_text(encoding='utf-8'))
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='resolve_numeric_representation_features')
    module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),function],type_ignores=[])
    namespace={'pd':pd}
    exec(compile(ast.fix_missing_locations(module),str(selection_path),'exec'),namespace)
    resolve_numeric_representation_features=namespace['resolve_numeric_representation_features']
    config_path=GEO/'configs/checkpoint04a.yaml'
    # Read only the plain scalar input paths; this is not a general YAML parser.
    raw=config_path.read_text(encoding='utf-8')
    input_text=raw.split('\ninputs:\n',1)[1].split('\nidentity:',1)[0]
    inputs=dict(line.strip().split(': ',1) for line in input_text.splitlines() if ': ' in line)
    assert 'allowed_modes: [clean, competition]' in raw
    assert '    - external_chirps_daily' in raw and 'exclude_columns: []' in raw
    assert 'layers: [base, agronomic, empirical]' in raw
    sources=[config_path,GEO/'src/geocebada/evaluation/checkpoint04a.py']
    tables=[];manifests={};records={}
    for layer in ['base','agronomic','empirical']:
        directory=GEO/inputs[layer+'_directory']
        table_path=directory/inputs[layer+'_table']
        manifest_path=directory/inputs[layer+'_manifest']
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        manifests[layer]=manifest
        # Do not load target, ID or per-parcel metadata into this inventory.
        wanted={r['column'] for r in manifest['features']} - {'RENDIMIENTO_T_HA','ID_POLIGONO','CONJUNTO'}
        table=pd.read_csv(table_path,usecols=lambda c:c in wanted,low_memory=False)
        tables.append(table)
        for record in manifest['features']:records.setdefault(record['column'],dict(layer=layer,**record))
        sources.extend([table_path,manifest_path])
    joined=pd.concat(tables,axis=1)
    assert not joined.columns.duplicated().any()
    candidates=resolve_numeric_representation_features(joined=joined,manifests=manifests,
        layers=['base','agronomic','empirical'],allowed_modes=['clean','competition'],
        exclude_sources=['external_chirps_daily'],exclude_columns=[])
    # Same pre-PCA nonempty/nonconstant criterion, without fitting any transform.
    names=[c for c in candidates if joined[c].notna().any() and joined[c].nunique(dropna=True)>1]
    assert len(names)==len(set(names))==2082,len(names)
    directory=ROOT/'documentation/models/L40'
    with (directory/'variables_C4_2082.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['position','variable','layer','source','mode','description','formula','inputs','caveats'])
        writer.writeheader()
        for i,name in enumerate(names,1):
            r=records[name]
            writer.writerow(dict(position=i,variable=name,layer=r['layer'],source=r.get('source',''),
                                 mode=r.get('mode',''),description=r.get('description',r.get('meaning','No description in source manifest')),
                                 formula=r.get('formula','Not specified in source manifest'),
                                 inputs=json.dumps(r.get('inputs',[]),ensure_ascii=False),
                                 caveats=json.dumps(r.get('caveats',[]),ensure_ascii=False)))
    provenance=dict(date='2026-10-18',n_features=len(names),counts_by_layer=dict(Counter(records[n]['layer'] for n in names)),
        method='Original resolve_numeric_representation_features, original C4 policy, original nonempty/nonconstant filter; no PCA refit.',
        target_loaded=False,models_trained=0,external_repository_modified=False,
        limitation='Reconstructs original input names from current local source tables; not an independent re-audit of every upstream formula or the historical PCA loading matrix.',
        source_sha256={p.relative_to(GEO).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    (directory/'inventory_provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:provenance[k] for k in ['n_features','counts_by_layer','target_loaded','models_trained']},indent=2))


if __name__=='__main__':main()
