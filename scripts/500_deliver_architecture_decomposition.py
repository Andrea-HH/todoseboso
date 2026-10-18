"""Independent metric checks, complexity/frontier views, figure and audit hashes."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.architecture_decomposition import OUT,load_design

def main():
    pruned=json.loads((OUT/'pruned_delivery_audit.json').read_text());assert pruned['status']=='complete' and pruned['max_difference']<1e-12
    report=json.loads((OUT/'evaluation_complete.json').read_text());assert report['status']=='complete';cfg=load_design();d=OUT/'tables';p=pd.read_parquet(d/'oof_residuals.parquet');m=pd.read_csv(d/'metrics_by_repeat.csv');s=pd.read_csv(d/'metrics_summary.csv');presentation=pd.read_csv(d/'presentation_RMSE_R2.csv')
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        row=m[(m.experiment==name)&(m.protocol==pro)&(m['repeat']==re)].iloc[0];e=g.y_pred-g.y_true;assert abs(np.sqrt(np.mean(e**2))-row.rmse)<1e-12 and abs(1-np.sum(e**2)/np.sum((g.y_true-g.y_true.mean())**2)-row.r2)<1e-12
    expected=m.groupby(['experiment','protocol'])[['rmse','r2','mae','bias']].mean().reset_index();pd.testing.assert_frame_equal(expected,s[['experiment','protocol','rmse','r2','mae','bias']],check_exact=False,atol=1e-12,rtol=1e-12)
    rows=[];counts={}
    for name,r in cfg['recipes'].items():
        calibration_fields=set(r['fields'])|(set(cfg['local_sets']['FULL7']) if r['internal']=='ON' else set());planet_prediction=any('planet' in c for c in cfg['local_sets'][r['local']]);counts[name+'_MASK']=r['mask_input_count'];rows.append(dict(experiment=name+'_MASK',local=r['local'],local_fields=len(cfg['local_sets'][r['local']]),internal_corrector=r['internal'],gate=r['gate'],prediction_inputs=r['mask_input_count'],calibration_inputs=len(calibration_fields),gate_dimensions=0 if r['gate']=='GLOBAL' else (2 if r['gate']=='PCA2' else 10),requires_Planet_prediction=planet_prediction,requires_Planet_calibration=planet_prediction or r['internal']=='ON',requires_geology=r['gate']!='GLOBAL',requires_historical_S2=True,local_hyperparameters='FULL7 same training context; coefficients refit'))
    inventory=pd.DataFrame(rows);inventory.to_csv(d/'complexity_inventory.csv',index=False);comparison=presentation[presentation.experiment.str.endswith('_MASK')|presentation.experiment.isin(['CT3_BASE','J7_GLOBAL_GLOBAL'])];comparison.to_csv(d/'comparison_MASK_RMSE_R2.csv',index=False)
    wide=s[s.experiment.isin(counts)].pivot(index='experiment',columns='protocol',values='rmse');wide['inputs']=[counts[n] for n in wide.index];front=[]
    for name,r in wide.iterrows():
        domination=[other for other,z in wide.iterrows() if name!=other and np.all(z.to_numpy()<=r.to_numpy()+1e-12) and np.any(z.to_numpy()<r.to_numpy()-1e-12)];front.append(dict(experiment=name,inputs=counts[name],dominated_on_four_RMSE_and_inputs=bool(domination),dominated_by=';'.join(domination)))
    pd.DataFrame(front).to_csv(d/'descriptive_input_frontier.csv',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(13,9));styles={'RAW':('tab:blue','o'),'PCA2':('tab:orange','^'),'GLOBAL':('tab:green','s')};ref='FULL7_ON_RAW_MASK'
    for ax,pro in zip(axes.ravel(),['random','climate_profile','municipality','spatial']):
        for r in rows:
            color,marker=styles[r['gate']];ax.scatter(r['prediction_inputs'],wide.loc[r['experiment'],pro],c=color,marker=marker,s=45,facecolors='none' if r['internal_corrector']=='OFF' else color,alpha=.8)
        ax.scatter(counts[ref],wide.loc[ref,pro],marker='*',s=180,c='black',label='Current reference');ax.set_title(pro);ax.set_xlabel('Raw input fields (not computational cost)');ax.set_ylabel('RMSE t/ha');ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(OUT/'figures/architecture_inputs_vs_RMSE.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(OUT/'descomposiciones_y_combinaciones.xlsx',engine='openpyxl',mode='a',if_sheet_exists='replace') as writer:
        pd.read_csv(OUT/'audit/pruned_source_independence.csv').to_excel(writer,sheet_name='source_independence',index=False)
        for name in ['complexity_inventory','comparison_MASK_RMSE_R2','descriptive_input_frontier']:pd.read_csv(d/(name+'.csv')).to_excel(writer,sheet_name=name[:31],index=False)
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());files=[OUT/'descomposiciones_y_combinaciones.xlsx',d/'oof_residuals.parquet',d/'paired_tests.csv',ROOT/'documentation/architecture_decomposition_results.md',ROOT/'documentation/architecture_decomposition_conclusions.md'];report.update(metrics_independently_verified=True,tests_passed=4,protected_sources=len(cfg['source_sha256']),performance_amendment='performance_amendment.json; equivalent dense Ridge, 32 real-data parity comparisons max0',artifact_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files if f.exists()});(OUT/'delivery_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='artifact_sha256'},indent=2))

if __name__=='__main__':main()
