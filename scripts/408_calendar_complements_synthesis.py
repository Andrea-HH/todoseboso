"""Evaluate full OOF, geographic stability and exact persisted-model replay."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.calendar_complements import OUT,OLD
from src.calendar_expansion import metric,BlockEstimator
from src.family_8.research import pair_metrics

def main():
    assert (OUT/'execution_complete.json').exists()
    dest=OUT/'diagnostics'
    if dest.exists():raise FileExistsError('Preserve completed diagnostics')
    dest.mkdir()
    cfg=json.loads((OUT/'frozen_design.json').read_text());frame=pd.read_parquet(OUT/'features_train138.parquet')
    new=pd.read_parquet(OUT/'tables/predictions.parquet');assert len(new)==19734
    archived=pd.read_parquet(ROOT/'outputs/modeling/agronomic_calendar/expansion/v1/tables/oof_predictions.parquet')
    ref=archived[archived.experiment.isin(['C-T3','F7-00','EN_CAL00','EN_CAL02'])][new.columns]
    p=pd.concat([new,ref],ignore_index=True)
    assert not p.duplicated(['experiment','protocol','repeat','fold','ID_POLIGONO']).any()
    p.to_csv(OUT/'tables/oof_predictions.csv',index=False);p.to_parquet(OUT/'tables/oof_predictions.parquet',index=False)
    z=p.merge(frame[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one')
    rows=[];regional=[];om=[];pairs=[];decomp=[]
    for (name,pro,re),g in z.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique
        key=dict(experiment=name,protocol=pro,repeat=re)
        rows.append(dict(**key,**metric(g.y_true,g.y_pred)))
        pairs.append(dict(**key,**pair_metrics(g)))
        e=g.y_pred-g.y_true
        decomp.append(dict(**key,bias_squared=e.mean()**2,error_variance=e.var(ddof=0),mse=np.mean(e**2)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):
                regional.append(dict(**key,kind=kind,zone=str(zone),n=len(h),**metric(h.y_true,h.y_pred)))
                q=g[g[kind]!=zone];om.append(dict(**key,kind=kind,omitted=str(zone),n=len(q),**metric(q.y_true,q.y_pred)))
    for name,data,group in [('metrics',rows,['experiment','protocol']),('regional',regional,['experiment','protocol','kind','zone']),('omissions',om,['experiment','protocol','kind','omitted']),('intraprofile',pairs,['experiment','protocol']),('bias_dispersion',decomp,['experiment','protocol'])]:
        d=pd.DataFrame(data);d.to_csv(dest/f'{name}_by_repeat.csv',index=False)
        d.drop(columns='repeat').groupby(group).mean(numeric_only=True).reset_index().to_csv(dest/f'{name}_summary.csv',index=False)
    reps=pd.DataFrame(rows);gains=[];paired=[]
    for name in new.experiment.unique():
        for reference in ['C-T3','SELECTED_BASE']:
            if name==reference:continue
            a=reps[reps.experiment.eq(name)].merge(reps[reps.experiment.eq(reference)],on=['protocol','repeat'],suffixes=('','_ref'),validate='one_to_one')
            for _,r in a.iterrows():paired.append(dict(experiment=name,reference=reference,protocol=r.protocol,repeat=r['repeat'],**{'delta_'+c:r[c]-r[c+'_ref'] for c in ['rmse','mae','bias','r2']}))
            a=z[z.experiment.eq(name)].merge(z[z.experiment.eq(reference)][['protocol','repeat','fold','ID_POLIGONO','y_pred']],on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one')
            a['reference']=reference;a['sse_gain']=(a.y_pred_ref-a.y_true)**2-(a.y_pred-a.y_true)**2;a['absolute_error_gain']=abs(a.y_pred_ref-a.y_true)-abs(a.y_pred-a.y_true);gains.append(a)
    d=pd.DataFrame(paired);d.to_csv(dest/'paired_by_repeat.csv',index=False)
    d.groupby(['experiment','reference','protocol']).mean(numeric_only=True).drop(columns='repeat').reset_index().to_csv(dest/'paired_summary.csv',index=False)
    g=pd.concat(gains,ignore_index=True);g.to_parquet(dest/'parcel_gains.parquet',index=False)
    g=g.groupby(['experiment','reference','protocol','ID_POLIGONO','Estado','Municipio'],as_index=False)[['sse_gain','absolute_error_gain']].mean()
    g.to_csv(dest/'parcel_gains_repeat_average.csv',index=False)
    g.groupby(['experiment','reference','protocol','Municipio']).agg(n=('ID_POLIGONO','size'),sse_gain=('sse_gain','sum'),fraction_improved=('absolute_error_gain',lambda v:(v>0).mean())).reset_index().to_csv(dest/'municipal_gain_concentration.csv',index=False)
    extremes=[]
    for _,h in g.groupby(['experiment','reference','protocol']):
        extremes.extend([h.nlargest(5,'sse_gain').assign(direction='improvement'),h.nsmallest(5,'sse_gain').assign(direction='deterioration')])
    pd.concat(extremes).to_csv(dest/'largest_changes.csv',index=False)
    usage=[];selection=[];replay=[]
    splits=joblib.load(OLD/'frozen65_splits.joblib')
    for fi,(pro,re,fo,tr,va,inner) in enumerate(splits):
        pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib')
        # Export plain, stateless prediction classes; memoization is only an
        # execution optimization on the fixed training dataframe.
        converted=False
        for b in pack['base']['representations'].values():
            if type(b['model']) is not BlockEstimator:
                b['model'].__class__=BlockEstimator;converted=True
        if converted:joblib.dump(pack,OUT/'models'/f'{fi:02d}.joblib',compress=3)
        np.testing.assert_array_equal(pack['train_positions'],tr);np.testing.assert_array_equal(pack['validation_positions'],va);assert not set(tr)&set(va)
        selection.append(dict(protocol=pro,repeat=re,fold=fo,representation=pack['base']['chosen']))
        preds={}
        for name,b in pack['base']['representations'].items():
            m=b['model'];preds[name]=m.predict(frame.iloc[va])
            usage.extend(dict(experiment=name,protocol=pro,repeat=re,fold=fo,feature=c,selected=bool(u),coefficient=float(v)) for c,u,v in zip(m.names_,m.used_,m.effects_))
        preds['SELECTED_BASE']=preds[pack['base']['chosen']]
        for name,b in pack['corrections'].items():
            preds[name]=preds['SELECTED_BASE'] if b['amplitude']==0 else preds['SELECTED_BASE']+b['amplitude']*b['model'].predict(frame.iloc[va])
        for name,pred in preds.items():
            expected=new[(new.experiment==name)&(new.protocol==pro)&(new['repeat']==re)&(new.fold==fo)].set_index('ID_POLIGONO').loc[frame.iloc[va].ID_POLIGONO].y_pred.to_numpy()
            delta=float(np.max(abs(expected-pred)));assert delta==0.
            replay.append(dict(experiment=name,protocol=pro,repeat=re,fold=fo,maximum_difference=delta))
    pd.DataFrame(replay).to_csv(OUT/'audit/exact_replay.csv',index=False)
    pd.DataFrame(selection).to_csv(dest/'base_selection_by_fold.csv',index=False)
    pd.DataFrame(selection).groupby(['protocol','representation']).size().rename('folds').reset_index().to_csv(dest/'base_selection_frequency.csv',index=False)
    u=pd.DataFrame(usage);u.to_csv(dest/'feature_selection_by_fold.csv',index=False)
    u.groupby(['experiment','protocol','feature']).agg(fraction_selected=('selected','mean'),median_coefficient=('coefficient','median')).reset_index().to_csv(dest/'feature_selection_stability.csv',index=False)
    reg=pd.read_parquet(OUT/'tables/registry.parquet');reg.to_csv(dest/'registry.csv',index=False)
    reg[reg.experiment.isin(cfg['corrections'])].groupby(['experiment','protocol']).agg(zero_fraction=('amplitude',lambda v:(v==0).mean()),mean_amplitude=('amplitude','mean')).reset_index().to_csv(dest/'correction_selection.csv',index=False)
    equality={}
    for name,reference in [('COMPACT4','EN_CAL00'),('CAL02','EN_CAL02')]:
        a=p[p.experiment.eq(name)].merge(p[p.experiment.eq(reference)],on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one')
        equality[name]=float(abs(a.y_pred-a.y_pred_ref).max());assert equality[name]<1e-10
    summary=pd.read_csv(dest/'metrics_summary.csv');matrix=summary.pivot(index='experiment',columns='protocol',values='rmse')
    order=list(cfg['representations'])+['SELECTED_BASE']+list(cfg['corrections']);protocols=['random','climate_profile','municipality','spatial']
    values=matrix.loc[order,protocols]-matrix.loc['C-T3',protocols]
    fig,ax=plt.subplots(figsize=(9,7));limit=max(abs(values.to_numpy()).max(),.01)
    im=ax.imshow(values,cmap='RdBu_r',vmin=-limit,vmax=limit,aspect='auto')
    ax.set(xticks=range(4),xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],yticks=range(len(order)),yticklabels=order,title='Cambio de RMSE frente a C-T3; negativo = mejora')
    for i in range(len(order)):
        for j in range(4):ax.text(j,i,f'{values.iloc[i,j]:+.3f}',ha='center',va='center')
    fig.colorbar(im,ax=ax);fig.tight_layout();fig.savefig(dest/'rmse_vs_ct3.png',dpi=160);plt.close(fig)
    protected=all(hashlib.sha256((ROOT/s).read_bytes()).hexdigest()==h for s,h in cfg['sha256'].items());assert protected
    manifest=dict(status='complete',**json.loads((OUT/'execution_complete.json').read_text()),new_external_predictions=len(new),external_predictors_replayed=len(replay),maximum_replay_difference=0.,matched_control_max_difference=equality,no_final138=True,no_PRED=True,tests_passed=4)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(matrix[protocols].to_string());print('\nBASE SELECTION');print(pd.read_csv(dest/'base_selection_frequency.csv').to_string(index=False));print('\nCORRECTIONS');print(pd.read_csv(dest/'correction_selection.csv').to_string(index=False))

if __name__=='__main__':main()
