"""Post-fit group/warning audit and readable figures; no fitting."""
from pathlib import Path
import sys,json,hashlib
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'outputs/modeling/physical_representation/v1'

if __name__=='__main__':
    manifest=json.loads((OUT/'manifest.json').read_text());cfg=json.loads((OUT/'frozen_design.json').read_text());warnings=[];groups=[]
    for fi in range(65):
        q=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');key={k:q['selection'][0][k] for k in ['protocol','repeat','fold']}
        warnings.extend(dict(index=fi,**key,**w) for w in q['warnings'])
        pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib')
        for name,info in pack['correctors'].items():
            m=info['model']
            if m is not None and m.kind=='groups':groups.append(dict(index=fi,**key,experiment=name,requested=m.params['n_clusters'],effective_requested=m.model_.n_clusters,nonempty=int((m.counts_>0).sum()),iterations=int(m.model_.n_iter_)))
    ww=pd.DataFrame(warnings);ww.to_csv(OUT/'audit/warnings_by_fold.csv',index=False);pd.DataFrame(groups).to_csv(OUT/'diagnostics/fitted_group_counts.csv',index=False)
    d=pd.read_csv(OUT/'diagnostics/metrics_summary.csv');protocols=['random','climate_profile','municipality','spatial'];table=d.pivot(index='experiment',columns='protocol',values='rmse')[protocols]
    fig,ax=plt.subplots(figsize=(9,5))
    for name,label in [('CT3','C-T3'),('LOCAL04D','Local04D'),('soil_texture_phase__neighbors','C-T3 + vecinos de textura/fase'),('soil_texture_phase__groups','C-T3 + grupos de textura/fase'),('GEOLOGY__groups','C-T3 + grupos geológicos')]:ax.plot(range(4),table.loc[name],marker='o',label=label)
    ax.set(xticks=range(4),xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],ylabel='RMSE (t/ha)',title='Candidatos físicos exploratorios: compromisos entre protocolos');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'diagnostics/physical_candidates.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(OUT/'resultados_representacion_fisica.xlsx',engine='openpyxl',mode='a',if_sheet_exists='replace') as writer:
        pd.DataFrame(groups).to_excel(writer,sheet_name='Grupos_efectivos',index=False)
        ww.to_excel(writer,sheet_name='Advertencias',index=False)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items())
    paths=[Path(__file__),ROOT/'documentation/physical_representation_results.md',OUT/'resultados_representacion_fisica.xlsx',OUT/'diagnostics/physical_candidates.png']
    manifest['delivery_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};manifest['fit_warnings_by_category']=ww.category.value_counts().to_dict();(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Delivery complete:',manifest['new_correction_oof'],'new OOF; max replay difference',manifest['exact_replay_max_difference']);print(ww.category.value_counts().to_string())
