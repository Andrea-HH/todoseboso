"""Post-fit diagnostics only: no model fitting, selection or new predictions PRED."""
from pathlib import Path
import sys,hashlib,json
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'outputs/modeling/physical_similarity/v2'

if __name__=='__main__':
    assert (OUT/'manifest.json').exists()
    x=pd.read_parquet(OUT/'cache/features138_target_free.parquet');b=joblib.load(OUT/'models/61.joblib');va=b['validation_positions'];info=b['correctors']['PHYSICAL_BALANCED__ridge'];m=info['model'];out=[];start=0
    with threadpool_limits(limits=1):
        for atom in info['atoms']:
            rep=b['representations'][atom];z=rep.transform(x.iloc[va])/np.sqrt(len(info['atoms']));width=z.shape[1];part=z@m.model_.coef_[start:start+width];start+=width
            out.append(dict(block=atom,external_max_score_norm=float(np.linalg.norm(z,axis=1).max()),mean_raw_contribution=float(part.mean()),max_abs_raw_contribution=float(abs(part).max())))
    pd.DataFrame(out).to_csv(OUT/'diagnostics/spatial_fold2_ridge_contributions.csv',index=False)
    d=pd.read_csv(OUT/'diagnostics/metrics_summary.csv');protocols=['random','climate_profile','municipality','spatial'];table=d.pivot(index='experiment',columns='protocol',values='rmse')[protocols]
    fig,ax=plt.subplots(figsize=(9,4.8))
    for name,label in [('CT3','C-T3'),('LOCAL04D','Local04D'),('geology_physiography__neighbors','C-T3 + vecinos geológicos'),('geology_physiography__groups','C-T3 + grupos geológicos'),('geology_physiography__ridge','C-T3 + Ridge geológico')]:
        ax.plot(range(4),table.loc[name],marker='o',label=label)
    ax.set(xticks=range(4),xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],ylabel='RMSE (t/ha)',title='Geología: señal complementaria con compromisos entre protocolos')
    ax.legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'diagnostics/geology_comparison.png',dpi=160);plt.close(fig)
    # Raw composition contrast at ten percentage points, not mere floating-point uniqueness.
    contrasts=[]
    train=joblib.load(ROOT/'outputs/modeling/geoc_bridge/v1/cache/prepared.joblib')['train'];profiles=train.climate_profile.to_numpy()
    for block,marker in [('soil_inegi','soil_unit_share__'),('geology_physiography','geo250_share__'),('erosion','erosion::')]:
        cols=[c for c in x if c.startswith(block+'::') and marker in c];a=x[cols].to_numpy(float);n=0;distinct=0
        for value in np.unique(profiles):
            ix=np.flatnonzero(profiles==value)
            for j,i in enumerate(ix):
                for k in ix[j+1:]:n+=1;distinct+=int(.5*np.sum(abs(a[i]-a[k]))>=.1-1e-10)
        contrasts.append(dict(block=block,pairs=n,composition_difference_at_least_10pp=distinct,fraction=distinct/n))
    contrast=pd.DataFrame(contrasts);contrast.to_csv(OUT/'audit/meaningful_composition_contrast.csv',index=False)
    descriptive=[]
    cfg=json.loads((OUT/'frozen_design.json').read_text())
    for block,cols in cfg['blocks'].items():
        for c in cols:
            s=x[c];row=dict(block=block,column=c,n=len(s),missing=int(s.isna().sum()),distinct=int(s.nunique()))
            if pd.api.types.is_numeric_dtype(s):
                a=pd.to_numeric(s,errors='coerce').replace([np.inf,-np.inf],np.nan)
                row.update(minimum=a.min(),q25=a.quantile(.25),median=a.median(),q75=a.quantile(.75),maximum=a.max())
            else:row['categories']=json.dumps(s.dropna().astype(str).unique().tolist(),ensure_ascii=False)
            descriptive.append(row)
    desc=pd.DataFrame(descriptive);desc.to_csv(OUT/'audit/feature_ranges138.csv',index=False)
    with pd.ExcelWriter(OUT/'resultados_semejanza_fisica.xlsx',engine='openpyxl',mode='a',if_sheet_exists='replace') as writer:
        contrast.to_excel(writer,sheet_name='Contraste_composiciones',index=False)
        desc.to_excel(writer,sheet_name='Rangos_138',index=False)
    mpath=OUT/'manifest.json';manifest=json.loads(mpath.read_text());paths=[Path(__file__),ROOT/'documentation/physical_similarity_design.md',ROOT/'documentation/physical_similarity_results.md',OUT/'resultados_semejanza_fisica.xlsx']
    manifest['delivery_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};mpath.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(contrast.to_string(index=False));print(pd.DataFrame(out).to_string(index=False))
