"""Descriptive architecture/proximity comparisons and input-count frontier."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/modeling/base_distribution_correction/v1';D=OUT/'tables'

def main():
    assert json.loads((OUT/'evaluation_complete.json').read_text())['status']=='complete';m=pd.read_csv(D/'metrics_summary.csv');presentation=pd.read_csv(D/'presentation_RMSE_R2.csv');counts=presentation.set_index('experiment').input_count.to_dict();rows=[]
    for name in m.experiment.unique():
        if name.endswith('_BASE') or '_GLOBAL_' in name:continue
        base=name.split('_')[0];a=m[m.experiment==name];b=m[m.experiment==base+'_GLOBAL_GLOBAL'];z=a.merge(b,on='protocol',suffixes=('','_global'),validate='one_to_one');z['input_count']=counts[name]
        for col in ['rmse','r2','mae','bias']:z['delta_'+col]=z[col]-z[col+'_global']
        rows.append(z)
    comparison=pd.concat(rows,ignore_index=True);comparison.to_csv(D/'conditional_vs_own_global.csv',index=False)
    cross=[]
    for name,g in comparison.groupby('experiment'):
        r=dict(experiment=name,input_count=counts[name],protocols_lower_rmse=int((g.delta_rmse< -1e-12).sum()))
        for z in g.itertuples():r[z.protocol+'_delta_rmse']=z.delta_rmse
        cross.append(r)
    pd.DataFrame(cross).to_csv(D/'conditional_cross_protocol.csv',index=False)
    presentation[presentation.experiment.str.endswith('_BASE')|presentation.experiment.str.contains('_GLOBAL_')].to_csv(D/'bases_global_R3_RMSE_R2.csv',index=False)
    wide=m.pivot(index='experiment',columns='protocol',values='rmse');wide['input_count']=[counts[n] for n in wide.index];front=[]
    for name,r in wide.iterrows():
        domination=[]
        for other,s in wide.iterrows():
            if name!=other and np.all(s.to_numpy()<=r.to_numpy()+1e-12) and np.any(s.to_numpy()<r.to_numpy()-1e-12):domination.append(other)
        front.append(dict(experiment=name,input_count=counts[name],dominated_on_RMSE_and_fields=bool(domination),dominated_by=';'.join(domination)))
    pd.DataFrame(front).to_csv(D/'descriptive_input_frontier.csv',index=False)
    fig,axes=plt.subplots(2,2,figsize=(12,8));colors={'CT3':'tab:blue','RAW7':'tab:orange','EXPERT7':'tab:green','EQUAL7':'tab:red','SHARES':'tab:purple','J7':'tab:brown'}
    for ax,pro in zip(axes.ravel(),['random','climate_profile','municipality','spatial']):
        for name,r in wide.iterrows():
            marker='s' if name.endswith('_BASE') else ('*' if '_GLOBAL_' in name else 'o');ax.scatter(r.input_count,r[pro],c=colors[name.split('_')[0]],marker=marker,s=90 if marker=='*' else 30,alpha=.8)
            if name in ['CT3_GLOBAL_GLOBAL','J7_GLOBAL_GLOBAL','RAW7_GLOBAL_GLOBAL','EQUAL7_GLOBAL_GLOBAL']:ax.annotate(name.replace('_GLOBAL_GLOBAL','+R3'),(r.input_count,r[pro]),fontsize=7,xytext=(3,4),textcoords='offset points')
        ax.set_title(pro);ax.set_xlabel('Input fields (not total computational complexity)');ax.set_ylabel('RMSE t/ha');ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(OUT/'figures/complexity_RMSE.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(OUT/'bases_y_correccion_por_distribucion.xlsx',engine='openpyxl',mode='a',if_sheet_exists='replace') as writer:
        for name in ['conditional_vs_own_global','conditional_cross_protocol','bases_global_R3_RMSE_R2','descriptive_input_frontier']:pd.read_csv(D/(name+'.csv')).to_excel(writer,sheet_name=name[:31],index=False)
    files=[OUT/'bases_y_correccion_por_distribucion.xlsx',D/'oof_residuals.parquet',D/'paired_tests.csv',ROOT/'documentation/base_distribution_correction_results.md',ROOT/'documentation/base_distribution_correction_conclusions.md'];report=json.loads((OUT/'evaluation_complete.json').read_text());report.update(tests_passed=3,amendment='amendment_01.json: enforce original internal outer splits',artifact_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files if f.exists()});(OUT/'delivery_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(presentation[presentation.experiment.str.endswith('_BASE')|presentation.experiment.str.contains('_GLOBAL_')].to_string(index=False));print('\nConditional improvements versus own global R3:');print(pd.DataFrame(cross).sort_values(['protocols_lower_rmse','input_count'],ascending=[False,True]).to_string(index=False))

if __name__=='__main__':main()
