"""Reuse verified complete-OOF reporting without changing earlier source or artifacts."""
import pandas as pd,numpy as np
from src.family_6.expansion import reporting as shared,diagnostics as old_diag,interpretation as old_interpret
from src.family_4.stage_d_evidence import metrics
from . import execution as e,diagnostics,interpretation
metric_summary=shared.metric_summary
def architecture_comparison(p):
    key=[e.ID,'protocol','repeat','fold']
    z=p[p.experiment.eq('F7-01')].merge(p[p.experiment.eq('F7-00')],on=key,suffixes=('','_base'),validate='one_to_one')
    assert np.array_equal(z.y_true,z.y_true_base)
    rows=[];folds=[];omissions=[]
    for (protocol,repeat),g in z.groupby(['protocol','repeat']):
        a=metrics(g);b=metrics(g.rename(columns={'y_pred':'unused','y_pred_base':'y_pred'}))
        rows.append(dict(candidate='F7-01',baseline='F7-00',protocol=protocol,repeat=repeat,n=len(g),delta_RMSE=a['RMSE']-b['RMSE'],delta_MAE=a['MAE']-b['MAE'],delta_bias=a['bias']-b['bias'],SSE_gain=b['SSE']-a['SSE'],fraction_SE_improve=(((g.y_pred_base-g.y_true)**2)>((g.y_pred-g.y_true)**2)).mean()))
    for (protocol,repeat,fold),g in z.groupby(['protocol','repeat','fold']):
        a=metrics(g);b=metrics(g.rename(columns={'y_pred':'unused','y_pred_base':'y_pred'}));folds.append(dict(protocol=protocol,repeat=repeat,fold=fold,n=len(g),delta_RMSE=a['RMSE']-b['RMSE'],delta_MAE=a['MAE']-b['MAE'],SSE_gain=b['SSE']-a['SSE']))
    for protocol in ['municipality','spatial']:
        for fold in range(1,6):
            g=z[z.protocol.eq(protocol)&z.fold.ne(fold)];a=metrics(g);b=metrics(g.rename(columns={'y_pred':'unused','y_pred_base':'y_pred'}))
            omissions.append(dict(protocol=protocol,omitted_fold=fold,n=len(g),delta_RMSE=a['RMSE']-b['RMSE'],delta_MAE=a['MAE']-b['MAE'],analysis='OOF omission, no refit'))
    pd.DataFrame(rows).to_csv(e.OUT/'tables/architecture_paired_repeat.csv',index=False)
    pd.DataFrame(rows).groupby('protocol').mean(numeric_only=True).reset_index().to_csv(e.OUT/'tables/architecture_paired_summary.csv',index=False)
    pd.DataFrame(folds).to_csv(e.OUT/'tables/architecture_fold_comparison.csv',index=False)
    pd.DataFrame(omissions).to_csv(e.OUT/'tables/architecture_omission_sensitivity.csv',index=False)
    z.to_parquet(e.OUT/'tables/architecture_paired_parcels.parquet',index=False)
def build(p):
    architecture_comparison(p)
    original=shared.e,shared.PAIRS,old_diag.build,old_interpret.write
    try:
        shared.e=e;old_diag.build=diagnostics.build;old_interpret.write=interpretation.write
        shared.build(p)
    finally:shared.e,shared.PAIRS,old_diag.build,old_interpret.write=original
