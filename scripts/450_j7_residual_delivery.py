"""Refresh plots using actual repeat IDs and validate the complete residual delivery."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import probplot
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('audit449',ROOT/'scripts/449_j7_both_residual_audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit);OUT=audit.OUT


def main():
    if (OUT/'delivery_audit.json').exists():raise FileExistsError('Preserve delivered residual audit')
    manifest=json.loads((OUT/'manifest.json').read_text());p=pd.read_parquet(OUT/'oof_residuals_components.parquet');colors={'Puebla':'tab:blue','Hidalgo':'tab:orange','Tlaxcala':'tab:green'};fig,axes=plt.subplots(2,4,figsize=(16,7));fig2,ax2=plt.subplots(2,4,figsize=(16,7));repeats={}
    for col,(pro,label) in enumerate(zip(audit.PROTOCOLS,audit.LABELS)):
        rep=int(p.loc[p.protocol==pro,'repeat'].min());repeats[pro]=rep;g=p[(p.protocol==pro)&(p['repeat']==rep)];assert len(g)==138 and g.ID_POLIGONO.is_unique;lo=min(g.y_true.min(),g.y_pred.min());hi=max(g.y_true.max(),g.y_pred.max());ax=axes[0,col]
        for state,h in g.groupby('Estado'):ax.scatter(h.y_pred,h.y_true,c=colors.get(state,'gray'),s=17,alpha=.65,label=state)
        ax.plot([lo,hi],[lo,hi],color='black',linestyle='--');cal=audit.calibration(g.y_true,g.y_pred);xx=np.array([lo,hi]);ax.plot(xx,cal['calibration_intercept']+cal['calibration_slope']*xx,color='red');ax.set(title=label,xlabel='Predicho t/ha',ylabel='Observado t/ha');ax.legend(fontsize=6);axes[1,col].scatter(g.y_pred,g.error,c=g.Estado.map(colors),s=17,alpha=.65);axes[1,col].axhline(0,color='black',linestyle='--');axes[1,col].set(xlabel='Predicho t/ha',ylabel='Predicho − observado t/ha');ax2[0,col].hist(g.error,bins=16,color='steelblue',alpha=.8);ax2[0,col].axvline(0,color='black',linestyle='--');ax2[0,col].set(title=label,xlabel='Error t/ha');probplot(g.error,dist='norm',plot=ax2[1,col]);ax2[1,col].set(title='QQ descriptivo')
    fig.suptitle('J7_BOTH OOF: calibración y residuos; aleatoria primera repetición');fig.tight_layout();fig.savefig(OUT/'figures/calibration_and_residuals.png',dpi=160);plt.close(fig);fig2.suptitle('Distribución de residuos; aleatoria primera repetición');fig2.tight_layout();fig2.savefig(OUT/'figures/residual_distribution_QQ.png',dpi=160);plt.close(fig2)
    # Verify metric aggregation, MSE decomposition and replay without refitting.
    raw=pd.read_csv(OUT/'tables/residual_by_repeat.csv');summary=pd.read_csv(OUT/'tables/residual_summary.csv').set_index('protocol');means=raw.groupby('protocol')[['rmse','r2','mae','bias']].mean();assert np.max(abs(means-summary[['rmse','r2','mae','bias']]).to_numpy())<1e-12
    for (pro,rep),g in p.groupby(['protocol','repeat']):
        row=raw[(raw.protocol==pro)&(raw['repeat']==rep)].iloc[0];e=g.y_pred.to_numpy()-g.y_true.to_numpy();assert len(g)==138 and abs(row.rmse-np.sqrt(np.mean(e**2)))<1e-12 and abs(row.bias-e.mean())<1e-12 and abs(row.rmse**2-row.error_variance-row.bias_squared)<1e-12
    assert len(p)==1794 and p.ID_POLIGONO.nunique()==138;assert manifest['replay_max_difference']==0
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in manifest['protected_source_sha256'].items());oldsha=manifest['code_sha256'];newsha=hashlib.sha256((ROOT/'scripts/449_j7_both_residual_audit.py').read_bytes()).hexdigest();manifest['original_analysis_code_sha256']=oldsha;manifest['code_sha256']=newsha;manifest['figure_repeat_correction']=dict(reason='Actual frozen repeat IDs start at 1; figures now use first chronological repetition, never best performance.',plotted_repeat_ids=repeats,no_numeric_metric_change=True,postprocess_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    report=ROOT/'documentation/j7_both_residual_audit.md';sources=[ROOT/'scripts/449_j7_both_residual_audit.py',Path(__file__),report];delivery=dict(status='complete',residual_rows=len(p),unique_parcels=138,complete_oof_metric_aggregation_verified=True,mse_decomposition_verified=True,figure_repeat_ids=repeats,protected_sources_unchanged=True,no_predictive_refit=True,no_new_PRED=True,source_sha256={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources});(OUT/'delivery_audit.json').write_text(json.dumps(delivery,indent=2),encoding='utf-8');print(json.dumps(delivery,indent=2))


if __name__=='__main__':main()
