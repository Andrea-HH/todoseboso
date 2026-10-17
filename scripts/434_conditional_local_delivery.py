"""Post-fit delivery provenance and physical cluster diagnostics; no training."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('runner432',ROOT/'scripts/432_run_conditional_local_phases.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner);OUT=runner.OUT

if __name__=='__main__':
    manifest=json.loads((OUT/'manifest.json').read_text());cfg=json.loads((OUT/'frozen_design.json').read_text());assets=runner.load_assets();t=assets['a']['train'];clusters=[];warnings=[]
    for fi in range(65):
        pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');checkpoint=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');q=checkpoint['selection'][0];key={k:q[k] for k in ['protocol','repeat','fold']};warnings.extend(dict(index=fi,**key,**w) for w in checkpoint['warnings'])
        for name in ['P1_TEXTURE_clusters','P1_GEOLOGY_clusters','P1_BOTH_clusters']:
            gate=pack['pipelines'][name]['gate'];tr=pack['train_positions'];labels=gate.model_.labels_
            for label in np.unique(labels):
                ix=tr[labels==label];states=t.iloc[ix].Estado.value_counts();municipal=t.iloc[ix].Municipio.value_counts();clusters.append(dict(index=fi,**key,experiment=name,cluster=int(label),n=len(ix),leader_weight=float(gate.weights_[label]),global_prior_weight=gate.global_,dominant_state=str(states.index[0]),dominant_state_fraction=float(states.iloc[0]/len(ix)),dominant_municipality=str(municipal.index[0]),dominant_municipality_fraction=float(municipal.iloc[0]/len(ix)),n_climate_profiles=int(t.iloc[ix].climate_profile.nunique())))
    pd.DataFrame(clusters).to_csv(OUT/'diagnostics/cluster_weights_and_support.csv',index=False);pd.DataFrame(warnings).to_csv(OUT/'audit/warnings_by_fold.csv',index=False)
    # Explicitly compare labels with the frozen reference OOF; physical-space schema remains inherited.
    new=pd.read_parquet(OUT/'tables/predictions.parquet');old=pd.read_parquet(runner.NC/'tables/new_oof_predictions.parquet');known=old.groupby('ID_POLIGONO').y_true.first();assert np.allclose(new.y_true,new.ID_POLIGONO.map(known),atol=0,rtol=0)
    s=pd.read_csv(OUT/'diagnostics/metrics_summary.csv');protocols=['random','climate_profile','municipality','spatial'];table=s.pivot(index='experiment',columns='protocol',values='rmse')[protocols];fig,ax=plt.subplots(figsize=(10,5))
    for name,label in [('CT3','C-T3'),('LEADER','Local sin clima + EN compacto'),('P1_GLOBAL_global','Mezcla global aprendida'),('P1_TEXTURE_clusters','Mezcla por textura/fase'),('P1_BOTH_clusters','Mezcla por textura/fase + geología')]:ax.plot(range(4),table.loc[name],marker='o',label=label)
    ax.set(xticks=range(4),xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],ylabel='RMSE (t/ha)',title='Mezcla de expertos: precisión y transferencia territorial');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'diagnostics/phase1_candidates.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(OUT/'resultados_tres_fases.xlsx',engine='openpyxl',mode='a',if_sheet_exists='replace') as writer:
        pd.DataFrame(clusters).to_excel(writer,sheet_name='Clusters_pesos_soporte',index=False)
        pd.DataFrame(warnings).to_excel(writer,sheet_name='Advertencias',index=False)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items())
    paths=[Path(__file__),ROOT/'documentation/conditional_local_phases_results.md',OUT/'resultados_tres_fases.xlsx',OUT/'diagnostics/phase1_candidates.png'];manifest['delivery_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};manifest['unchanged_y_against_reference_oof']=True;manifest['warnings_by_category']=pd.DataFrame(warnings).category.value_counts().to_dict();(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2))
