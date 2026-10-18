"""Independent metric aggregation, contrast tables, figure and delivery hashes."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.learned_r3_weight import OUT
from src.learned_r3_protocol import load_design

def main():
    result=json.loads((OUT/'evaluation_complete.json').read_text());assert result['status']=='complete';d=OUT/'tables';p=pd.read_parquet(d/'oof_residuals.parquet');m=pd.read_csv(d/'metrics_by_repeat.csv');summary=pd.read_csv(d/'metrics_summary.csv')
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        row=m[(m.experiment==name)&(m.protocol==pro)&(m['repeat']==re)].iloc[0];e=g.y_pred-g.y_true;assert abs(np.sqrt(np.mean(e**2))-row.rmse)<1e-12 and abs(1-np.sum(e**2)/np.sum((g.y_true-g.y_true.mean())**2)-row.r2)<1e-12
    expected=m.groupby(['experiment','protocol'])[['rmse','r2','mae','bias']].mean().reset_index();pd.testing.assert_frame_equal(expected,summary[['experiment','protocol','rmse','r2','mae','bias']],check_exact=False,atol=1e-12,rtol=1e-12)
    cfg=load_design();changes=[]
    for b in cfg['bases']:
        for variant in cfg['recipes']:
            name=b+'_'+variant
            for reference in [b+'_GLOBAL_GLOBAL',b+'_MASK']:
                z=summary[summary.experiment==name].merge(summary[summary.experiment==reference],on='protocol',suffixes=('','_reference'),validate='one_to_one')
                for col in ['rmse','r2','mae','bias']:z['delta_'+col]=z[col]-z[col+'_reference']
                changes.append(z)
    changes=pd.concat(changes);changes.to_csv(d/'changes_vs_global_and_mask.csv',index=False)
    # Stable predefined sensitivities shown together, without selecting one by external scores.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(14,9));variants=list(cfg['recipes'])
    for ax,pro in zip(axes.ravel(),['random','climate_profile','municipality','spatial']):
        for b in cfg['bases']:
            z=changes[(changes.protocol==pro)&(changes.experiment_reference==b+'_GLOBAL_GLOBAL')].set_index('experiment');ax.plot(range(len(variants)),[z.loc[b+'_'+v,'delta_rmse'] for v in variants],marker='o',label=b)
        ax.axhline(0,color='black',lw=.7);ax.set_title(pro);ax.set_xticks(range(len(variants)),variants,rotation=45,ha='right');ax.set_ylabel('Delta RMSE versus own global R3');ax.grid(alpha=.2)
    axes[0,0].legend();fig.tight_layout();fig.savefig(OUT/'figures/changes_vs_global_R3.png',dpi=150);plt.close(fig)
    with pd.ExcelWriter(OUT/'pesos_aprendidos_y_asimetria.xlsx',engine='openpyxl',mode='a',if_sheet_exists='replace') as writer:
        changes.to_excel(writer,sheet_name='cambios_global_y_mask',index=False)
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());files=[OUT/'pesos_aprendidos_y_asimetria.xlsx',d/'oof_residuals.parquet',d/'paired_tests.csv',ROOT/'documentation/learned_r3_weight_results.md',ROOT/'documentation/learned_r3_weight_conclusions.md',ROOT/'documentation/learned_r3_weight_amendment.md'];result.update(metrics_independently_verified=True,tests_passed=4,meta_penalties='fixed sensitivities; not internally or externally selected',amendment='amendment_01.json',protected_sources=len(cfg['source_sha256']),artifact_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files});(OUT/'delivery_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='artifact_sha256'},indent=2))

if __name__=='__main__':main()
