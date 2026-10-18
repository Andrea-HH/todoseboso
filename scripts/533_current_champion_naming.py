"""Reserve current champion status for26/14; retain frozen and executable legacy IDs."""
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ACTIVE={'README.md','model_registry.md','current_champions_reproduction.md','project_scope_and_guidelines.md',
        'reproducibility.md','experiment_index.md','model_status_history.md','repository_organization.md'}


def clean(text,historical=False):
    # Do not change executable snippets, raw column names, or link destinations.
    pieces=re.split(r'(```[\s\S]*?```|`[^`\n]*`|\]\([^\n)]*\))',text)
    for i in range(0,len(pieces),2):
        s=pieces[i]
        s=re.sub(r'\bchampion hist[oó]rico\b','modelo histórico TOP20/TOP15',s,flags=re.I)
        s=s.replace('C-T3/Champion/EQUAL3','C-T3/modelo TOP20/TOP15/EQUAL3')
        if historical:
            s=re.sub(r'nuevo\s*Champion\b','nuevo líder',s)
            s=re.sub(r'como\s*Champion\b','como líder',s)
            s=re.sub(r'\bChampion\b','modelo TOP20/TOP15',s)
        pieces[i]=s
    return ''.join(pieces)


def main():
    changes=[];protected=[]
    for folder in ['documentation','results']:
        for path in sorted((ROOT/folder).rglob('*.md')):
            if '/ai/prompts/' in path.as_posix():continue
            relative=path.relative_to(ROOT).as_posix()
            frozen=any(token in path.stem.lower() for token in ['design','proposal','plan'])
            if frozen:
                protected.append(relative);continue
            old=path.read_text(encoding='utf-8')
            historical=folder=='documentation' and path.parent==ROOT/'documentation' and path.name not in ACTIVE
            new=clean(old,historical)
            if new!=old:
                changes.append(dict(path=relative,before_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
                path.write_text(new,encoding='utf-8',newline='\n')
    path=ROOT/'README.md';old=path.read_text(encoding='utf-8');new=clean(old)
    if new!=old:path.write_text(new,encoding='utf-8',newline='\n');changes.append(dict(path='README.md'))
    path=ROOT/'configs/model_registry.json';registry=json.loads(path.read_text(encoding='utf-8'))
    for m in registry['models']:
        if m['id']=='A_CURRENT_CH_H_T':
            m['status']='historical_model_final59'
            m['aliases']=['Modelo histórico TOP20/TOP15']
            m['legacy_aliases']=['Champion','CHAMPION','historical_champion']
    actual={m['id'] for m in registry['models'] if m['status'].startswith('current_champion')}
    assert actual=={'Reference26','Compact14'}
    path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    path=ROOT/'configs/current_stage.json';stage=json.loads(path.read_text(encoding='utf-8'))
    if 'historical_champion' in stage:stage['historical_model']=stage.pop('historical_champion')
    assert stage['champions']==['Reference26','Compact14']
    path.write_text(json.dumps(stage,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    # Refresh contextual hashes after presentation-only wording edits.
    audit_path=ROOT/'documentation/inventories/model_status_audit.csv'
    with audit_path.open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
    for row in rows:row['sha256_after']=hashlib.sha256((ROOT/row['document']).read_bytes()).hexdigest()
    with audit_path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result=dict(current_champions=sorted(actual),modified_document_count=len(changes),modified_documents=changes,
        preserved_frozen_documents=protected,
        legacy_policy='Old raw IDs such as Champion_t_ha, CHAMPION, A_CURRENT_CH_H_T and source identifiers remain for reproducibility; they are not current champion declarations. Literal user prompts and frozen designs preserve their original wording.',
        model_code_changed=False,predictions_changed=False)
    candidates=set(subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode('utf-8').split('\0'))
    references=[]
    for name in sorted(candidates):
        path=ROOT/name
        if not name or not path.is_file() or path.suffix not in ['.md','.py','.json','.csv','.txt']:continue
        text=path.read_text(encoding='utf-8-sig',errors='replace')
        count=len(re.findall('champion',text,re.I))
        if not count:continue
        kind=('literal_user_prompt' if name.startswith('documentation/ai/prompts/') else
              'frozen_historical_design' if name.startswith('configs/experiments/') or any(t in path.stem.lower() for t in ['design','proposal','plan']) else
              'code_or_legacy_identifier' if name.startswith(('src/','scripts/','tests/')) else
              'structured_registry_current_or_legacy_alias' if name.startswith('configs/') else
              'historical_metric_or_audit_identifier' if path.suffix in ['.csv','.json'] else
              'current_documentation_with_legacy_names_explicitly_qualified')
        references.append(dict(path=name,occurrences=count,classification=kind))
    target=ROOT/'documentation/inventories/champion_references.csv'
    with target.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['path','occurrences','classification']);writer.writeheader();writer.writerows(references)
    result['repository_files_with_current_or_legacy_references']=len(references)
    (ROOT/'documentation/inventories/current_champion_naming.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'Only current champions:26/14; refreshed {len(changes)} documents; raw legacy identifiers and frozen originals preserved.')


if __name__=='__main__':main()
