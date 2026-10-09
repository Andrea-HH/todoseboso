"""F2.3 Round 2: prueba acotada Climate Current + Sentinel funcional.

Ocho pipelines en cuatro pares matched. Reutiliza los folds congelados; toda
imputacion, escala, FPCA y seleccion de hiperparametros ocurre dentro de train.
"""
from pathlib import Path
import sys,json,time,warnings,importlib.util
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('f2r1',Path(__file__).with_name('203_family2_round1.py'));r1=importlib.util.module_from_spec(spec);spec.loader.exec_module(r1)
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.linalg import solve
from scipy.stats import pearsonr,wilcoxon
from sklearn.model_selection import KFold
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge,ElasticNet
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,median_absolute_error
from xgboost import XGBRegressor
from family_1.stage4_modeling import load_xy,save_splits,representations,FEATURE_DIR,ID,SEED
warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid')

BASE=ROOT/'outputs/modeling/family_2/stage3_round2_hybrid'
D={x:BASE/x for x in ['metrics','predictions','models','sof','diagnostics','figures','report','checkpoints']}
for p in D.values():p.mkdir(parents=True,exist_ok=True)
PAIRS=[('CLIMATE_RIDGE','CLIMATE_FPCA_RIDGE'),('CLIMATE_ENET','CLIMATE_FPCA_ENET'),('CLIMATE_XGB','CLIMATE_FPCA_XGB'),('CLIMATE_FUNCTIONAL_LINEAR_BASELINE','CLIMATE_SOF_ALL4')]
PIPES=sum(([a,b] for a,b in PAIRS),[])
ARTIFACT_VERSION=2

def metric(y,p):return {'RMSE':mean_squared_error(y,p)**.5,'MAE':mean_absolute_error(y,p),'R2':r2_score(y,p),'MedAE':median_absolute_error(y,p)}

def climate_columns(X):
    core=representations(X.columns)['CORE'];dic=pd.read_csv(FEATURE_DIR/'family1_feature_dictionary.csv').set_index('feature_name')
    cols=[c for c in core if c in dic.index and dic.loc[c,'source']=='CLIMATE']
    if len(cols)!=48:raise ValueError(f'Climate Current debe tener 48 features, se encontraron {len(cols)}')
    return cols

def grids(kind):
    if kind=='RIDGE':return [{'alpha':a} for a in [.01,.1,1.,10.,100.]]
    if kind=='ENET':return [{'alpha':a,'l1_ratio':l} for a in [.01,.1,1.] for l in [.1,.7]]
    return [
      {'n_estimators':150,'max_depth':2,'learning_rate':.03,'min_child_weight':5,'subsample':.8,'colsample_bytree':.6,'reg_alpha':.5,'reg_lambda':5.},
      {'n_estimators':150,'max_depth':2,'learning_rate':.03,'min_child_weight':10,'subsample':.8,'colsample_bytree':.6,'reg_alpha':.5,'reg_lambda':5.},
      {'n_estimators':150,'max_depth':3,'learning_rate':.03,'min_child_weight':5,'subsample':.8,'colsample_bytree':.6,'reg_alpha':.5,'reg_lambda':5.},
      {'n_estimators':150,'max_depth':3,'learning_rate':.03,'min_child_weight':10,'subsample':.8,'colsample_bytree':.6,'reg_alpha':.5,'reg_lambda':5.},
      {'n_estimators':300,'max_depth':2,'learning_rate':.03,'min_child_weight':5,'subsample':.8,'colsample_bytree':.6,'reg_alpha':.5,'reg_lambda':5.},
      {'n_estimators':300,'max_depth':2,'learning_rate':.03,'min_child_weight':10,'subsample':.8,'colsample_bytree':.6,'reg_alpha':.5,'reg_lambda':5.},
      {'n_estimators':300,'max_depth':3,'learning_rate':.03,'min_child_weight':5,'subsample':.8,'colsample_bytree':.6,'reg_alpha':.5,'reg_lambda':5.},
      {'n_estimators':300,'max_depth':3,'learning_rate':.03,'min_child_weight':10,'subsample':.8,'colsample_bytree':.6,'reg_alpha':.5,'reg_lambda':5.}]

def prep_climate(C,tr,va,scale):
    imp=SimpleImputer(strategy='median').fit(C.iloc[tr]);a=imp.transform(C.iloc[tr]);b=imp.transform(C.iloc[va]);sc=None
    if scale:sc=StandardScaler().fit(a);a=sc.transform(a);b=sc.transform(b)
    return a,b,imp,sc

def model_fit(kind,param,x,y):
    if kind=='RIDGE':return Ridge(alpha=param['alpha']).fit(x,y)
    if kind=='ENET':return ElasticNet(alpha=param['alpha'],l1_ratio=param['l1_ratio'],max_iter=30000,random_state=SEED).fit(x,y)
    return XGBRegressor(**param,objective='reg:squarederror',random_state=SEED,n_jobs=1,verbosity=0).fit(x,y)

def tune_ml(kind,hybrid,inner,C,y):
    vals=[];scale=kind in ['RIDGE','ENET']
    for par in grids(kind):
        pp=[];yy=[]
        for q in inner:
            ct,cv,_,_=prep_climate(C,q['tr'],q['va'],scale);xt=np.column_stack([ct,q['index_tr']]) if hybrid else ct;xv=np.column_stack([cv,q['index_va']]) if hybrid else cv
            m=model_fit(kind,par,xt,y.iloc[q['tr']]);pp.extend(m.predict(xv));yy.extend(y.iloc[q['va']])
        vals.append((mean_squared_error(yy,pp)**.5,par))
    return min(vals,key=lambda x:(x[0],json.dumps(x[1],sort_keys=True)))

def partial_fit(Cz,Z,y,alpha,lam,R,nblocks):
    X=np.column_stack([Cz,Z]) if Z is not None else Cz;xm=X.mean(0);ym=y.mean();xc=X-xm
    if Z is None:P=alpha*np.eye(Cz.shape[1])
    else:P=np.zeros((X.shape[1],X.shape[1]));P[:Cz.shape[1],:Cz.shape[1]]=alpha*np.eye(Cz.shape[1]);P[Cz.shape[1]:,Cz.shape[1]:]=lam*np.kron(np.eye(nblocks),R)
    coef=solve(xc.T@xc+P+1e-8*np.eye(X.shape[1]),xc.T@(y-ym),assume_a='pos');return ym-xm@coef,coef

def tune_partial(hybrid,inner,C,y,curves,B,w,R):
    cfg=[(a,l) for a in [1.,10.,100.] for l in ([.1,1.,10.] if hybrid else [np.nan])];vals=[]
    for alpha,lam in cfg:
        pp=[];yy=[]
        for q in inner:
            ct,cv,_,_=prep_climate(C,q['tr'],q['va'],True);zt=r1.sof_design(curves,q['tr'],r1.SIGNALS,B,w) if hybrid else None;zv=r1.sof_design(curves,q['va'],r1.SIGNALS,B,w) if hybrid else None
            inter,coef=partial_fit(ct,zt,y.iloc[q['tr']].to_numpy(),alpha,lam,R,4);xv=np.column_stack([cv,zv]) if hybrid else cv;pp.extend(inter+xv@coef);yy.extend(y.iloc[q['va']])
        vals.append((mean_squared_error(yy,pp)**.5,alpha,lam))
    return min(vals)

def consolidate(y,climcols):
    pred=pd.concat([pd.read_parquet(p) for p in sorted(D['checkpoints'].glob('pred_fold_*.parquet'))],ignore_index=True);pred.to_parquet(D['predictions']/'oof_predictions.parquet',index=False)
    fold=[]
    for (p,r,f),g in pred.groupby(['pipeline','repeat','fold']):fold.append({'pipeline':p,'repeat':r,'fold':f,'n':len(g),**metric(g.y_true,g.y_pred)})
    fm=pd.DataFrame(fold);fm.to_csv(D['metrics']/'fold_metrics.csv',index=False)
    sm=fm.groupby('pipeline').agg(RMSE_mean=('RMSE','mean'),RMSE_median=('RMSE','median'),RMSE_std=('RMSE','std'),MAE_mean=('MAE','mean'),R2_mean=('R2','mean'),MedAE_mean=('MedAE','mean')).reset_index().sort_values('RMSE_mean');sm.to_csv(D['metrics']/'pipeline_metrics.csv',index=False)
    bp=pred.groupby(['pipeline',ID]).agg(y_true=('y_true','first'),oof_prediction_mean=('y_pred','mean'),oof_prediction_std=('y_pred','std')).reset_index();bp['residual']=bp.oof_prediction_mean-bp.y_true;bp['absolute_error']=abs(bp.residual);bp.to_csv(D['predictions']/'oof_by_parcel.csv',index=False)
    wide=fm.pivot(index=['repeat','fold'],columns='pipeline',values='RMSE');rows=[]
    for base,hyb in PAIRS:
        d=wide[hyb]-wide[base]
        try:pv=wilcoxon(d).pvalue
        except Exception:pv=np.nan
        rows.append({'record_type':'overall','repeat':np.nan,'baseline':base,'hybrid':hyb,'n_folds':len(d),'mean_delta_RMSE':d.mean(),'median_delta_RMSE':d.median(),'std_delta_RMSE':d.std(),'q25_delta_RMSE':d.quantile(.25),'q75_delta_RMSE':d.quantile(.75),'hybrid_win_rate':(d<0).mean(),'wilcoxon_pvalue_descriptive':pv})
        for rep,g in d.groupby(level=0):rows.append({'record_type':'repeat','repeat':rep,'baseline':base,'hybrid':hyb,'n_folds':len(g),'mean_delta_RMSE':g.mean(),'median_delta_RMSE':g.median(),'std_delta_RMSE':g.std(),'q25_delta_RMSE':g.quantile(.25),'q75_delta_RMSE':g.quantile(.75),'hybrid_win_rate':(g<0).mean(),'wilcoxon_pvalue_descriptive':np.nan})
    pc=pd.DataFrame(rows);pc.to_csv(D['metrics']/'paired_incremental_comparisons.csv',index=False)
    # Diagnostics from parcel-aggregated OOF.
    q25=y.quantile(.25);q75=y.quantile(.75);seg=[];cal=[]
    for p,g in bp.groupby('pipeline'):
        for lab,mask in [('LOW',g.y_true<=q25),('MID',(g.y_true>q25)&(g.y_true<q75)),('HIGH',g.y_true>=q75)]:
            z=g[mask];seg.append({'pipeline':p,'segment':lab,'n':len(z),'RMSE':mean_squared_error(z.y_true,z.oof_prediction_mean)**.5,'MAE':mean_absolute_error(z.y_true,z.oof_prediction_mean),'bias':z.residual.mean()})
        beta,alpha=np.polyfit(g.y_true,g.oof_prediction_mean,1);cal.append({'pipeline':p,'n':len(g),'alpha':alpha,'beta':beta,'R2':r2_score(g.oof_prediction_mean,alpha+beta*g.y_true)})
    pd.DataFrame(seg).to_csv(D['diagnostics']/'yield_segment_performance.csv',index=False);pd.DataFrame(cal).to_csv(D['diagnostics']/'calibration_summary.csv',index=False)
    # Difficult parcels and functional-distance subgroup.
    hard=pd.read_csv(ROOT/'outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv');hard=hard[hard.support_class.eq('y-outlier given similar X')][[ID]]
    fd=pd.read_csv(ROOT/'outputs/modeling/family_2/stage2_fpca/diagnostics/difficult_parcels_functional_distance.csv')[[ID,'core_5nn_percentile','functional_5nn_percentile']]
    dw=hard.merge(fd,on=ID);dw['increased_functional_distance']=dw.functional_5nn_percentile>dw.core_5nn_percentile
    for base,hyb in PAIRS:
        a=bp[bp.pipeline.eq(base)].set_index(ID);h=bp[bp.pipeline.eq(hyb)].set_index(ID);dw[f'{base}_error']=dw[ID].map(a.absolute_error);dw[f'{hyb}_error']=dw[ID].map(h.absolute_error);dw[f'{hyb}_improvement']=dw[f'{base}_error']-dw[f'{hyb}_error']
    dw.to_csv(D['diagnostics']/'difficult_parcels_hybrid.csv',index=False)
    # Residual correlations: matched pair and corresponding functional-only model.
    old=pd.read_csv(ROOT/'outputs/modeling/family_2/stage3_round1/predictions/oof_by_parcel.csv');fmap={'CLIMATE_FPCA_RIDGE':'F2_RIDGE_INDEX','CLIMATE_FPCA_ENET':'F2_ENET_INDEX','CLIMATE_FPCA_XGB':'F2_XGB_INDEX','CLIMATE_SOF_ALL4':'SOF_ALL4'};corr=[]
    for base,hyb in PAIRS:
        a=bp[bp.pipeline.eq(base)].set_index(ID).residual;h=bp[bp.pipeline.eq(hyb)].set_index(ID).residual;f=old[old.pipeline.eq(fmap[hyb])].set_index(ID).residual
        corr.append({'baseline':base,'hybrid':hyb,'functional_only':fmap[hyb],'baseline_hybrid_residual_correlation':a.corr(h),'baseline_functional_residual_correlation':a.corr(f),'hybrid_functional_residual_correlation':h.corr(f)})
    pd.DataFrame(corr).to_csv(D['diagnostics']/'residual_correlations.csv',index=False)
    # ENET score selection and XGB feature importance summaries already saved per fold.
    fs=pd.concat([pd.read_csv(p) for p in sorted(D['checkpoints'].glob('importance_fold_*.csv'))],ignore_index=True);summ=[]
    for (pipe,ft,feat),g in fs.groupby(['pipeline','feature_type','feature']):summ.append({'pipeline':pipe,'feature_type':ft,'feature':feat,'index':feat.split('_FPC')[0] if '_FPC' in feat else np.nan,'n_folds_available':len(g),'mean_value':g.value.mean(),'median_value':g.value.median(),'mean_absolute_value':g.value.abs().mean(),'selection_frequency':(g.value!=0).mean()})
    pd.DataFrame(summ).to_csv(D['models']/'functional_score_selection.csv',index=False)
    # SOF beta stability and contiguous stable regions.
    cf=pd.concat([pd.read_parquet(p) for p in sorted(D['checkpoints'].glob('beta_fold_*.parquet'))],ignore_index=True);cf.to_parquet(D['sof']/'hybrid_beta_functions.parquet',index=False)
    st=cf.groupby(['signal','t']).beta.agg(beta_mean='mean',beta_median='median',beta_std='std',n_folds='count',proportion_positive=lambda x:(x>0).mean()).reset_index();st['proportion_folds_same_sign']=np.maximum(st.proportion_positive,1-st.proportion_positive);st.to_csv(D['sof']/'hybrid_beta_stability.csv',index=False)
    regions=[]
    for sig,g in st.groupby('signal'):
        g=g.sort_values('t');ok=g.proportion_folds_same_sign.ge(.8).to_numpy();tt=g.t.to_numpy();start=None
        for i,v in enumerate(np.r_[ok,False]):
            if v and start is None:start=i
            elif not v and start is not None:
                if i-start>=7:
                    z=g.iloc[start:i];regions.append({'signal':sig,'start_t':tt[start],'end_t':tt[i-1],'n_days':i-start,'dominant_sign':'positive' if z.proportion_positive.mean()>=.5 else 'negative','mean_sign_stability':z.proportion_folds_same_sign.mean(),'mean_beta':z.beta_mean.mean()})
                start=None
    pd.DataFrame(regions).to_csv(D['sof']/'hybrid_beta_stable_regions.csv',index=False)
    plt.figure(figsize=(9,5));sns.barplot(data=sm,x='RMSE_mean',y='pipeline',color='#4C78A8');plt.axvline(.5107,ls='--',color='black');plt.tight_layout();plt.savefig(D['figures']/'hybrid_pipeline_rmse.png',dpi=180);plt.close()
    return sm,bp,pc,dw,st

def make_report(sm,bp,pc,dw,st):
    x=sm.set_index('pipeline');bestbase=min([a for a,b in PAIRS],key=lambda p:x.loc[p,'RMSE_mean']);besthyb=min([b for a,b in PAIRS],key=lambda p:x.loc[p,'RMSE_mean']);delta=.5107-x.loc[besthyb,'RMSE_mean'];overall=pc[pc.record_type.eq('overall')].set_index('hybrid');cal=pd.read_csv(D['diagnostics']/'calibration_summary.csv').set_index('pipeline');seg=pd.read_csv(D['diagnostics']/'yield_segment_performance.csv');sel=pd.read_csv(D['models']/'functional_score_selection.csv');reg=pd.read_csv(D['sof']/'hybrid_beta_stable_regions.csv')
    def pairtext(h):
        q=overall.loc[h];return f"mean Δ={q.mean_delta_RMSE:+.4f}, median Δ={q.median_delta_RMSE:+.4f}, wins={q.hybrid_win_rate:.0%}"
    en=sel[(sel.pipeline=='CLIMATE_FPCA_ENET')&(sel.feature_type=='functional')].groupby('index').agg(mean_selection_frequency=('selection_frequency','mean'),scores=('feature','count')).reset_index().round(3).to_dict('records')
    xi=sel[(sel.pipeline=='CLIMATE_FPCA_XGB')].groupby('feature_type').mean_absolute_value.sum();xi=(xi/xi.sum()).round(3).to_dict()
    drow=dw[f'{besthyb}_improvement'];six=dw[dw.increased_functional_distance][f'{besthyb}_improvement']
    low=seg[(seg.pipeline==besthyb)&(seg.segment=='LOW')].iloc[0];high=seg[(seg.pipeline==besthyb)&(seg.segment=='HIGH')].iloc[0]
    txt=f"""# Familia 2 — F2.3 Round 2 Hybrid

## Controles

Se ejecutaron exclusivamente ocho pipelines en cuatro pares matched, con los 50 outer folds congelados y 4 inner folds. Climate Current contiene exactamente 48 features de Familia 1. Imputación, escala, FPCA, penalizaciones y regresores se ajustaron dentro del train correspondiente. No se añadieron otras fuentes, no se inició Familia 3 y no se predijeron las 59 parcelas.

## Respuestas

1. **Mejor Climate-only:** `{bestbase}`, RMSE={x.loc[bestbase,'RMSE_mean']:.4f}.
2. **Mejor híbrido:** `{besthyb}`, RMSE={x.loc[besthyb,'RMSE_mean']:.4f}.
3. **¿Supera XGB Climate 0.5107?** {'Sí' if delta>0 else 'No'}.
4. **Diferencia:** {abs(delta):.4f} RMSE {'mejor' if delta>0 else 'peor'}.
5. **Consistencia:** {pairtext(besthyb)}. Los resultados por repetición están en `paired_incremental_comparisons.csv`; Wilcoxon es sólo descriptivo porque repeated-CV induce dependencia.
6. **FPCA + Ridge:** {pairtext('CLIMATE_FPCA_RIDGE')}.
7. **FPCA + Elastic Net:** {pairtext('CLIMATE_FPCA_ENET')}.
8. **FPCA + XGBoost:** {pairtext('CLIMATE_FPCA_XGB')}.
9. **SOF_ALL4 controlando Climate:** {pairtext('CLIMATE_SOF_ALL4')}.
10. **Mejor complemento funcional:** `{min([b for a,b in PAIRS],key=lambda h:overall.loc[h,'mean_delta_RMSE'])}` por delta medio.
11. **Scores que sobreviven ENET:** {en}.
12. **Importancia XGBoost agregada:** {xi}. Importancia gain normalizada por fold; no se calculó SHAP.
13. **Beta(t) estable:** {reg.sort_values('n_days',ascending=False).head(10).round(3).to_dict('records')}. Son asociaciones condicionales descriptivas, no eventos causales.
14. **Bajos rendimientos, mejor híbrido:** RMSE={low.RMSE:.4f}, bias={low.bias:+.4f}; compárese por par en `yield_segment_performance.csv`.
15. **Altos rendimientos:** RMSE={high.RMSE:.4f}, bias={high.bias:+.4f}.
16. **Regresión a la media:** beta híbrido={cal.loc[besthyb,'beta']:.3f}, baseline matched={cal.loc[overall.loc[besthyb,'baseline'],'beta']:.3f}. Sólo es favorable si mejora hacia 1 sin sacrificar RMSE.
17. **Nueve parcelas difíciles:** mejoran {(drow>0).sum()}/9; mejora media={drow.mean():+.4f} t/ha en error absoluto. De las seis separadas funcionalmente mejoran {(six>0).sum()}/{len(six)}.
18. **Contribución predictiva:** {'la evidencia cumple inicialmente dirección media, pero debe además cumplir mediana, mayoría y estabilidad por repetición' if overall.loc[besthyb,'mean_delta_RMSE']<0 else 'no hay evidencia útil de valor incremental bajo el criterio predefinido'}.
19. **Papel de Familia 2:** {'puede conservarse como bloque predictivo candidato acotado' if overall.loc[besthyb,'mean_delta_RMSE']<0 and overall.loc[besthyb,'median_delta_RMSE']<0 and overall.loc[besthyb,'hybrid_win_rate']>.5 else 'debe conservarse principalmente como análisis temporal e interpretativo'}.
20. **Cierre:** Round 2 es la prueba decisiva. {'Conviene congelar el híbrido ganador y comenzar el diseño de Familia 3, sin ejecutarla automáticamente' if overall.loc[besthyb,'mean_delta_RMSE']<0 and overall.loc[besthyb,'median_delta_RMSE']<0 and overall.loc[besthyb,'hybrid_win_rate']>.5 else 'conviene cerrar Familia 2 sin promover un híbrido y comenzar después Familia 3' }.
"""
    (D['report']/'family2_stage3_round2_hybrid_report.md').write_text(txt,encoding='utf-8')

def main():
    ids,X,y=load_xy();cols=climate_columns(X);C=X[cols].reset_index(drop=True);ids=ids.reset_index(drop=True);y=y.reset_index(drop=True);_,_,t,curves=r1.load_data();splits=save_splits(ids);pos={p:i for i,p in enumerate(ids)};B,w,R=r1.basis_and_penalty(t)
    hpall=[]
    for k,s in splits.iterrows():
        pf=D['checkpoints']/f'pred_fold_{k:02d}.parquet';hf=D['checkpoints']/f'hp_fold_{k:02d}.csv';iff=D['checkpoints']/f'importance_fold_{k:02d}.csv';bf=D['checkpoints']/f'beta_fold_{k:02d}.parquet'
        valid_cache=all(p.exists() for p in [pf,hf,iff,bf])
        if valid_cache:
            oldhp=pd.read_csv(hf);valid_cache='artifact_version' in oldhp and oldhp.artifact_version.eq(ARTIFACT_VERSION).all()
        if valid_cache:hpall+=oldhp.to_dict('records');print(f'fold {k+1}/50 cached',flush=True);continue
        tr=np.array([pos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([pos[v] for v in json.loads(s.validation_ID_POLIGONO)]);inner=r1.inner_representations(curves,t,tr,SEED+k);fp=r1.FoldFPCA(t).fit(curves,tr);zt=fp.transform(curves,tr);zv=fp.transform(curves,va);rows=[];hps=[];imps=[];betas=[];start=time.time()
        for kind in ['RIDGE','ENET','XGB']:
            for hybrid in [False,True]:
                name=f"CLIMATE_FPCA_{kind}" if hybrid else f"CLIMATE_{kind}";score,par=tune_ml(kind,hybrid,inner,C,y);ct,cv,imp,sc=prep_climate(C,tr,va,kind in ['RIDGE','ENET']);xt=np.column_stack([ct,zt]) if hybrid else ct;xv=np.column_stack([cv,zv]) if hybrid else cv;m=model_fit(kind,par,xt,y.iloc[tr]);pred=m.predict(xv)
                nfnz=int(np.count_nonzero(m.coef_[-zt.shape[1]:])) if hybrid and kind=='ENET' else np.nan
                hps.append({'artifact_version':ARTIFACT_VERSION,'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'inner_RMSE':score,'best_params':json.dumps(par,sort_keys=True),'n_features':xt.shape[1],'n_functional_nonzero':nfnz})
                rows += [{ID:p,'repeat':s['repeat'],'fold':s['fold'],'y_true':yt,'y_pred':yp,'pipeline':name,'pair_model':kind,'hybrid':hybrid} for p,yt,yp in zip(ids.iloc[va],y.iloc[va],pred)]
                if hybrid and kind in ['ENET','XGB']:
                    values=m.coef_ if kind=='ENET' else m.feature_importances_;names=cols+fp.names
                    imps += [{'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'feature':f,'feature_type':'functional' if '_FPC' in f else 'climate','value':v} for f,v in zip(names,values)]
        for hybrid in [False,True]:
            name='CLIMATE_SOF_ALL4' if hybrid else 'CLIMATE_FUNCTIONAL_LINEAR_BASELINE';score,alpha,lam=tune_partial(hybrid,inner,C,y,curves,B,w,R);ct,cv,imp,sc=prep_climate(C,tr,va,True);ztr=r1.sof_design(curves,tr,r1.SIGNALS,B,w) if hybrid else None;zva=r1.sof_design(curves,va,r1.SIGNALS,B,w) if hybrid else None;inter,coef=partial_fit(ct,ztr,y.iloc[tr].to_numpy(),alpha,lam,R,4);xv=np.column_stack([cv,zva]) if hybrid else cv;pred=inter+xv@coef
            hps.append({'artifact_version':ARTIFACT_VERSION,'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'inner_RMSE':score,'best_params':json.dumps({'alpha_scalar':alpha,'lambda_functional':None if not hybrid else lam}),'n_features':len(coef),'n_functional_nonzero':np.nan})
            rows += [{ID:p,'repeat':s['repeat'],'fold':s['fold'],'y_true':yt,'y_pred':yp,'pipeline':name,'pair_model':'PARTIAL_SOF','hybrid':hybrid} for p,yt,yp in zip(ids.iloc[va],y.iloc[va],pred)]
            if hybrid:
                nb=B.shape[1];fc=coef[len(cols):]
                for j,sig in enumerate(r1.SIGNALS):
                    beta=B@fc[j*nb:(j+1)*nb];betas += [{'signal':sig,'repeat':s['repeat'],'fold':s['fold'],'t':int(tt),'date':pd.Timestamp('2025-04-01')+pd.Timedelta(days=int(tt)),'beta':bb,'alpha_scalar':alpha,'lambda_functional':lam} for tt,bb in zip(t,beta)]
        pd.DataFrame(rows).to_parquet(pf,index=False);pd.DataFrame(hps).to_csv(hf,index=False);pd.DataFrame(imps).to_csv(iff,index=False);pd.DataFrame(betas).to_parquet(bf,index=False);hpall+=hps;print(f'fold {k+1}/50 complete in {time.time()-start:.1f}s',flush=True)
    pd.DataFrame(hpall).to_csv(D['models']/'selected_hyperparameters.csv',index=False);sm,bp,pc,dw,st=consolidate(y,cols);make_report(sm,bp,pc,dw,st);print(f"Round2 complete: best={sm.iloc[0].pipeline}, RMSE={sm.iloc[0].RMSE_mean:.4f}",flush=True)

if __name__=='__main__':main()
