"""Exploratory paired OOF diagnostics; fixed blends, no fitting or selection."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/modeling/agronomic_calendar/expansion/v1/tables/oof_predictions.parquet'
META=ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet'
OUT=ROOT/'outputs/research/calendar_base_complementarity/v1'

def metrics(y,p):
    e=p-y
    return dict(rmse=float(np.sqrt(np.mean(e**2))),mae=float(np.mean(abs(e))),bias=float(np.mean(e)),r2=float(1-np.sum(e**2)/np.sum((y-y.mean())**2)))

def main():
    if OUT.exists():raise FileExistsError('Preserve previous results')
    OUT.mkdir(parents=True)
    design=dict(status='exploratory',bases=['C-T3','EN_CAL02'],calendar_weights=[0,.25,.5,.75,1],selection='none; all fixed weights reported, external OOF never used to fit weights',fits=0,warning='Repeated reuse of the same labels; blends are descriptive, not independently confirmed or internally selected.')
    (OUT/'design.json').write_text(json.dumps(design,indent=2),encoding='utf-8')
    p=pd.read_parquet(SOURCE);keys=['protocol','repeat','fold','ID_POLIGONO']
    a=p[p.experiment.eq('C-T3')][keys+['y_true','y_pred']]
    b=p[p.experiment.eq('EN_CAL02')][keys+['y_true','y_pred']]
    z=a.merge(b,on=keys,suffixes=('_ct3','_cal'),validate='one_to_one')
    assert len(z)==1794
    np.testing.assert_array_equal(z.y_true_ct3,z.y_true_cal)
    meta=pd.read_parquet(META,columns=['ID_POLIGONO','Estado','Municipio','climate_profile'])
    z=z.merge(meta,on='ID_POLIGONO',validate='many_to_one')
    z['error_ct3']=z.y_pred_ct3-z.y_true_ct3;z['error_cal']=z.y_pred_cal-z.y_true_ct3
    z['cal_sse_gain']=z.error_ct3**2-z.error_cal**2
    z.to_csv(OUT/'paired_oof.csv',index=False)
    rows=[];corr=[];regions=[];omissions=[]
    for (pro,rep),g in z.groupby(['protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique
        e=g.error_ct3;f=g.error_cal
        corr.append(dict(protocol=pro,repeat=rep,error_correlation=e.corr(f),prediction_correlation=g.y_pred_ct3.corr(g.y_pred_cal),calendar_better_fraction=float((abs(f)<abs(e)).mean()),opposite_error_fraction=float((e*f<0).mean()),prediction_disagreement_rmse=float(np.sqrt(np.mean((g.y_pred_cal-g.y_pred_ct3)**2)))))
        for weight in design['calendar_weights']:
            pred=(1-weight)*g.y_pred_ct3+weight*g.y_pred_cal
            rows.append(dict(protocol=pro,repeat=rep,calendar_weight=weight,**metrics(g.y_true_ct3,pred)))
            for kind in ['Estado','Municipio','fold','climate_profile']:
                for zone,h in g.groupby(kind):
                    hp=(1-weight)*h.y_pred_ct3+weight*h.y_pred_cal
                    regions.append(dict(protocol=pro,repeat=rep,calendar_weight=weight,kind=kind,zone=str(zone),n=len(h),**metrics(h.y_true_ct3,hp) if h.y_true_ct3.nunique()>1 else dict(rmse=float(np.sqrt(np.mean((hp-h.y_true_ct3)**2))),mae=float(np.mean(abs(hp-h.y_true_ct3))),bias=float(np.mean(hp-h.y_true_ct3)),r2=np.nan)))
                    if kind in ['Estado','Municipio','fold']:
                        h=g[g[kind]!=zone]
                        hp=(1-weight)*h.y_pred_ct3+weight*h.y_pred_cal
                        omissions.append(dict(protocol=pro,repeat=rep,calendar_weight=weight,kind=kind,omitted=str(zone),n=len(h),**metrics(h.y_true_ct3,hp)))
    for name,data,group in [('metrics',rows,['protocol','calendar_weight']),('complementarity',corr,['protocol']),('regional',regions,['protocol','calendar_weight','kind','zone']),('omissions_without_refit',omissions,['protocol','calendar_weight','kind','omitted'])]:
        frame=pd.DataFrame(data);frame.to_csv(OUT/f'{name}_by_repeat.csv',index=False)
        summary=frame.drop(columns='repeat').groupby(group).mean(numeric_only=True).reset_index()
        summary.to_csv(OUT/f'{name}_summary.csv',index=False)
        if name in ['metrics','complementarity']:print(summary.to_string(index=False))
    (OUT/'manifest.json').write_text(json.dumps(dict(design,paired_rows=len(z),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),no_model_changes=True,no_PRED=True),indent=2),encoding='utf-8')

if __name__=='__main__':main()
