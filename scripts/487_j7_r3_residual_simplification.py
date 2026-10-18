"""Frozen corrector ablations and descriptive residual research; no final/PRED fit."""
from pathlib import Path
import sys,json,hashlib,time,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.indicator_neighborhoods import OUT as SOURCE,ENGINEERING,CALIBRATION,REDUCTIONS,ReducedCorrection
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
OUT=ROOT/'outputs/research/j7_r3_residual_simplification/v1'
COLS=REDUCTIONS['R3']
RECIPES={'ONLY_NDVI':[COLS[0]],'ONLY_PERSISTENCE':[COLS[1]],'ONLY_SLOPE':[COLS[2]],'NDVI_PERSISTENCE':COLS[:2],'NDVI_SLOPE':[COLS[0],COLS[2]],'CONSTANT':[]}
KEY=['protocol','repeat','fold','ID_POLIGONO']

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def stats(g):
    y=g.y_true.to_numpy();p=g.y_pred.to_numpy();e=p-y;den=np.sum((y-y.mean())**2)
    slope=float(np.sum((p-p.mean())*(y-y.mean()))/np.sum((p-p.mean())**2)) if np.std(p)>1e-10 else np.nan
    return dict(n=len(g),rmse=float(np.sqrt(np.mean(e**2))),r2=float(1-np.sum(e**2)/den) if den>1e-12 else np.nan,mae=float(np.mean(abs(e))),bias=float(e.mean()),error_sd=float(e.std()),p95_absolute=float(np.quantile(abs(e),.95)),within_05=float(np.mean(abs(e)<=.5)),over_fraction=float(np.mean(e>0)),calibration_slope=slope,calibration_intercept=float(y.mean()-slope*p.mean()),target_min=float(y.min()),target_max=float(y.max()))

def table(rows,name,keys):
    d=pd.DataFrame(rows);d.to_csv(OUT/'tables'/f'{name}_by_repeat.csv',index=False);s=d.drop(columns='repeat',errors='ignore').groupby(keys,dropna=False).mean(numeric_only=True).reset_index();s.to_csv(OUT/'tables'/f'{name}_summary.csv',index=False);return s

def main():
    start=time.perf_counter();assert not (OUT/'complete.json').exists()
    for sub in ['tables','models','figures']: (OUT/sub).mkdir(parents=True,exist_ok=True)
    files=[ROOT/'scripts/487_j7_r3_residual_simplification.py',SOURCE/'frozen_design.json',SOURCE/'delivery_audit.json',SOURCE/'tables/oof_residuals.parquet',SOURCE/'cache/features_train138_target_free.parquet']
    design=dict(recipes=RECIPES,amplitudes=[0,.25,.5],base='J7_BOTH unchanged',external_folds=65,selection='complete internal OOF RMSE; tie smaller amplitude',alpha=.01,l1_ratio=.5,cap_t_ha=.25,exploratory=True,no_PRED=True,source_hashes={str(p):digest(p) for p in files})
    (OUT/'frozen_design.json').write_text(json.dumps(design,indent=2),encoding='utf-8')
    t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');x=pd.read_parquet(SOURCE/'cache/features_train138_target_free.parquet');y=t.RENDIMIENTO_T_HA.to_numpy();ids=t.ID_POLIGONO.tolist();assert x.ID_POLIGONO.tolist()==ids
    source=pd.read_parquet(SOURCE/'tables/oof_residuals.parquet');p=source[source.experiment.isin(['CT3','J7_BOTH','J7_GLOBAL_R3','J7_GLOBAL_R2'])].copy();rows=[];selections=[];coefficients=[]
    folds=joblib.load(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/frozen65_splits.joblib');REDUCTIONS.update(RECIPES)
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for fi,(pro,re,fold,tr,va,inner) in enumerate(folds):
            tr=np.asarray(tr);va=np.asarray(va);old=joblib.load(CALIBRATION/'checkpoints'/f'{fi:02d}.joblib');ctxs=joblib.load(ENGINEERING/'checkpoints'/f'{fi:02d}.joblib');np.testing.assert_array_equal(old['calibration']['train_positions'],tr);bp=old['calibration']['base_oof'];base=p[(p.experiment=='J7_BOTH')&(p.protocol==pro)&(p['repeat']==re)&(p.fold==fold)].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();pack={}
            for name,columns in RECIPES.items():
                delta=np.full(len(tr),np.nan)
                for ctx,(a,b) in zip(ctxs['contexts'],inner):
                    aa=np.asarray(ctx['aa']);d=np.asarray(ctx['where']);np.testing.assert_array_equal(aa,tr[a]);np.testing.assert_array_equal(d,b);assert not set(aa)&(set(tr[d])|set(va));m=ReducedCorrection(name).fit(x.iloc[aa],y[aa]-ctx['bases']['J7']);delta[d]=m.delta(x.iloc[tr[d]])
                assert np.isfinite(delta).all();scores=[dict(amplitude=a,inner_rmse=float(np.sqrt(np.mean((bp+(a/.5)*delta-y[tr])**2)))) for a in design['amplitudes']];best=min(scores,key=lambda z:(round(z['inner_rmse'],12),z['amplitude']));m=ReducedCorrection(name).fit(x.iloc[tr],y[tr]-bp);correction=best['amplitude']/.5*m.delta(x.iloc[va]);assert max(abs(correction))<=.25+1e-12
                experiment='J7_ABL_'+name;selections.append(dict(experiment=experiment,execution_index=fi,protocol=pro,repeat=re,fold=fold,**best));rows.extend(dict(experiment=experiment,protocol=pro,repeat=re,fold=fold,ID_POLIGONO=ids[i],y_true=y[i],y_pred=float(pred)) for i,pred in zip(va,base+correction));pack[experiment]=dict(model=m,amplitude=best['amplitude'],train_positions=tr,validation_positions=va)
            joblib.dump(pack,OUT/'models'/f'{fi:02d}.joblib',compress=3)
            if fi%10==0:print(f'Ablations {fi+1}/65',flush=True)
        (OUT/'warnings.json').write_text(json.dumps([dict(category=w.category.__name__,message=str(w.message)) for w in caught],indent=2),encoding='utf-8')
    new=pd.DataFrame(rows).merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');p=pd.concat([p[new.columns],new],ignore_index=True);p['error']=p.y_pred-p.y_true;p['absolute_error']=abs(p.error);p['squared_error']=p.error**2
    p.to_parquet(OUT/'tables/oof.parquet',index=False);pd.DataFrame(selections).to_csv(OUT/'tables/selection.csv',index=False)
    metrics=[];regional=[];quartiles=[];omissions=[]
    q=dict(zip(ids,pd.qcut(y,4,duplicates='drop').astype(str)))
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;k=dict(experiment=name,protocol=pro,repeat=re);metrics.append(dict(**k,**stats(g)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):regional.append(dict(**k,kind=kind,zone=str(zone),**stats(h)));omissions.append(dict(**k,kind=kind,omitted=str(zone),**stats(g[g[kind]!=zone])))
        for zone,h in g.groupby(g.ID_POLIGONO.map(q)):quartiles.append(dict(**k,zone=zone,**stats(h)))
    summary=table(metrics,'metrics',['experiment','protocol']);table(regional,'regions',['experiment','protocol','kind','zone']);table(quartiles,'quartiles',['experiment','protocol','zone']);table(omissions,'omissions',['experiment','protocol','kind','omitted'])
    # Corrector effect on exactly matched OOF cases, not independent repeats.
    a=p[p.experiment=='J7_GLOBAL_R3'].merge(p[p.experiment=='J7_BOTH'],on=KEY,suffixes=('','_base'),validate='one_to_one');a['correction']=a.y_pred-a.y_pred_base;a['sse_gain']=a.error_base**2-a.error**2;a['absolute_gain']=abs(a.error_base)-abs(a.error);a['helped']=a.absolute_gain>1e-12;a['harm']=a.absolute_gain< -1e-12;a['overshot']=a.error*a.error_base<0
    a.to_csv(OUT/'tables/correction_effect_by_oof.csv',index=False);parcel=a.groupby(['protocol','ID_POLIGONO','Estado','Municipio']).agg(y_true=('y_true','first'),base_error=('error_base','mean'),corrected_error=('error','mean'),base_mse=('squared_error_base','mean'),corrected_mse=('squared_error','mean'),correction=('correction','mean'),sse_gain=('sse_gain','mean'),absolute_gain=('absolute_gain','mean'),help_fraction=('helped','mean'),overshot_fraction=('overshot','mean')).reset_index();parcel.to_csv(OUT/'tables/parcel_changes.csv',index=False)
    effects=[]
    for (pro,re),g in a.groupby(['protocol','repeat']):effects.append(dict(protocol=pro,repeat=re,mean_correction=g.correction.mean(),mean_absolute_correction=abs(g.correction).mean(),fraction_helped=g.helped.mean(),fraction_harmed=g.harm.mean(),fraction_zero=(abs(g.correction)<1e-12).mean(),fraction_cap=(abs(g.correction)>=.25-1e-10).mean(),base_bias=g.error_base.mean(),corrected_bias=g.error.mean(),bias_squared_gain=g.error_base.mean()**2-g.error.mean()**2,error_variance_gain=g.error_base.var(ddof=0)-g.error.var(ddof=0)))
    table(effects,'correction_effect',['protocol'])
    # Descriptive Spearman associations: not a variable selector or causal evidence.
    assoc=[]
    for pro,g in parcel.groupby('protocol'):
        z=g.merge(x,on='ID_POLIGONO',validate='one_to_one')
        for col in x.select_dtypes('number').columns:
            for target in ['base_error','corrected_error','sse_gain']:
                h=z[[col,target]].dropna();assoc.append(dict(protocol=pro,feature=col,target=target,n=len(h),spearman=h[col].corr(h[target],method='spearman') if len(h)>=10 and h[col].nunique()>1 else np.nan))
    pd.DataFrame(assoc).to_csv(OUT/'tables/descriptive_associations.csv',index=False)
    # Reuse existing lower-complexity architectures without pretending they include R3.
    arch=pd.read_parquet(ROOT/'outputs/modeling/joint_simplification/v1/tables/predictions.parquet');ar=[]
    for (name,pro,re),g in arch.groupby(['experiment','protocol','repeat']):ar.append(dict(experiment=name,protocol=pro,repeat=re,**stats(g)))
    table(ar,'existing_architectures',['experiment','protocol'])
    # Paired inference for 6 new ablations versus R3 and R3 versus original J7.
    groups=pd.read_csv(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/groups.csv').set_index('ID_POLIGONO').loc[ids];tests=[]
    for pro,g in p.groupby('protocol'):
        group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();w,_=cluster_weights(group,5000,2026);arrays={n:h.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy() for n,h in g.groupby('experiment')};samples={n:sampled_metrics(y,v,w) for n,v in arrays.items()}
        for name,ref in [('J7_GLOBAL_R3','J7_BOTH')]+[('J7_ABL_'+n,'J7_GLOBAL_R3') for n in RECIPES]:
            delta=samples[name]['rmse']-samples[ref]['rmse'];loss=np.sum((arrays[name]-y)**2-(arrays[ref]-y)**2,axis=0);tests.append(dict(experiment=name,reference=ref,protocol=pro,delta_rmse=summary[(summary.experiment==name)&(summary.protocol==pro)].rmse.iloc[0]-summary[(summary.experiment==ref)&(summary.protocol==pro)].rmse.iloc[0],low95=np.quantile(delta,.025),high95=np.quantile(delta,.975),**paired_signflip(loss,group)))
    tests=pd.DataFrame(tests);tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(OUT/'tables/paired_tests.csv',index=False)
    # Plot parcel-average residuals only for illustration; metrics above remain by repetition.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,4,figsize=(16,7))
    for j,pro in enumerate(['random','climate_profile','municipality','spatial']):
        g=parcel[parcel.protocol==pro];axes[0,j].scatter(g.y_true,g.base_error,s=15,label='J7',alpha=.6);axes[0,j].scatter(g.y_true,g.corrected_error,s=15,label='J7 + R3',alpha=.6);axes[0,j].axhline(0,color='black',lw=.6);axes[0,j].set_title(pro);axes[0,j].set_xlabel('Observed t/ha');axes[1,j].scatter(g.base_error,g.corrected_error,s=15);axes[1,j].plot([-2,2],[-2,2],color='black',lw=.7);axes[1,j].set_xlabel('J7 error');axes[1,j].set_ylabel('J7 + R3 error')
    axes[0,0].legend();fig.tight_layout();fig.savefig(OUT/'figures/residual_comparison.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(OUT/'residuos_y_simplificacion.xlsx',engine='openpyxl') as writer:
        for f in sorted((OUT/'tables').glob('*.csv')):
            if f.stem.endswith('_by_repeat') or f.stem=='correction_effect_by_oof':continue
            pd.read_csv(f).to_excel(writer,sheet_name=f.stem[:31],index=False)
        for sheet in writer.book.worksheets:sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    assert all(digest(Path(f))==h for f,h in design['source_hashes'].items());(OUT/'complete.json').write_text(json.dumps(dict(status='complete',new_outer_systems=390,OOF_rows=len(p),old_sources_unchanged=True,no_PRED=True,no_final138_fit=True,seconds=time.perf_counter()-start),indent=2));print(summary[['experiment','protocol','rmse','r2','mae','bias']].to_string(index=False))

if __name__=='__main__':main()
