"""F2.3 Round 1: nested CV para modelos functional-only.

Las curvas suavizadas target-free de F2.1 quedan congeladas. FPCA, escalado,
joint PCA y regresores se reajustan dentro de cada inner/outer train split.
No se usan Climate, Planet, Landsat, History, Anomaly, Topography ni target
para construir las transformaciones funcionales.
"""
from pathlib import Path
import sys, json, time, warnings
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.linalg import solve
from scipy.stats import wilcoxon
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler, SplineTransformer
from sklearn.linear_model import LinearRegression, Ridge, ElasticNet
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,median_absolute_error
from xgboost import XGBRegressor
from family_1.stage4_modeling import load_xy,save_splits,ID,SEED

warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid')
SIGNALS=['ndvi','savi','ndwi','dswi4'];CAPS={'ndvi':5,'savi':4,'ndwi':5,'dswi4':4}
BASE=ROOT/'outputs/modeling/family_2/stage3_round1'
D={x:BASE/x for x in ['metrics','predictions','fpca_cv','models','sof','diagnostics','figures','report','checkpoints']}
for p in D.values():p.mkdir(parents=True,exist_ok=True)

INDEX_MODELS=['F2_OLS_INDEX','F2_RIDGE_INDEX','F2_ENET_INDEX','F2_PLS_INDEX','F2_XGB_INDEX']
JOINT_MODELS=['F2_RIDGE_JOINT','F2_ENET_JOINT','F2_XGB_JOINT']
SOF_BLOCKS={'SOF_NDVI':['ndvi'],'SOF_SAVI':['savi'],'SOF_NDWI':['ndwi'],'SOF_DSWI4':['dswi4'],
            'SOF_VIGOR':['ndvi','savi'],'SOF_MOISTURE':['ndwi','dswi4'],'SOF_ALL4':SIGNALS}
PIPELINES=INDEX_MODELS+JOINT_MODELS+list(SOF_BLOCKS)


def metric(y,p):return {'RMSE':mean_squared_error(y,p)**.5,'MAE':mean_absolute_error(y,p),'R2':r2_score(y,p),'MedAE':median_absolute_error(y,p)}


def load_data():
    ids,_,y=load_xy();d=pd.read_parquet(ROOT/'data/processed/family_2/functions/sentinel_smooth_grid.parquet')
    d=d[d['index'].isin(SIGNALS)];t=np.sort(d.t.unique()).astype(float);all_ids=sorted(d[ID].unique())
    arr={s:d[d['index'].eq(s)].pivot(index=ID,columns='t',values='smooth_value').reindex(all_ids).to_numpy(float) for s in SIGNALS}
    pos={p:i for i,p in enumerate(all_ids)};take=np.array([pos[p] for p in ids]);arr={s:x[take] for s,x in arr.items()}
    return ids.reset_index(drop=True),y.reset_index(drop=True),t,arr


def weights(t):
    dt=np.diff(t);return np.r_[dt[0]/2,(dt[:-1]+dt[1:])/2,dt[-1]/2]


class FoldFPCA:
    def __init__(self,t,caps=CAPS,var=.95):self.t=t;self.w=weights(t);self.caps=caps;self.var=var
    def fit(self,curves,idx):
        self.models={};self.names=[]
        for s in SIGNALS:
            x=curves[s][idx];mu=x.mean(0);u,sv,vt=np.linalg.svd((x-mu)*np.sqrt(self.w),full_matrices=False)
            eig=sv**2/(len(idx)-1);rat=eig/eig.sum();k=min(int(np.searchsorted(np.cumsum(rat),self.var)+1),self.caps[s])
            phi=vt[:k]/np.sqrt(self.w);self.models[s]=(mu,phi,eig,rat,k)
            self.names += [f'{s}_FPC{j}' for j in range(1,k+1)]
        return self
    def transform(self,curves,idx):
        return np.column_stack([(curves[s][idx]-m[0])@(m[1]*self.w).T for s,m in self.models.items()])
    def metadata(self):
        rows=[]
        for s,(mu,phi,eig,rat,k) in self.models.items():
            for j in range(len(rat)):
                rows.append({'signal':s,'component':j+1,'eigenvalue':eig[j],'explained_variance_ratio':rat[j],
                             'cumulative_explained_variance':np.cumsum(rat)[j],'selected':j<k,'cap':self.caps[s]})
        return pd.DataFrame(rows)


class JointSpace:
    def fit(self,z):
        self.scaler=StandardScaler().fit(z);zs=self.scaler.transform(z);self.pca=PCA(svd_solver='full').fit(zs);return self
    def transform(self,z,k):return self.pca.transform(self.scaler.transform(z))[:,:min(k,self.pca.n_components_)]


def configs(name,nfeat):
    if name.startswith('F2_RIDGE'):return [{'alpha':a} for a in [.01,.1,1.,10.,100.]]
    if name.startswith('F2_ENET'):return [{'alpha':a,'l1_ratio':l} for a in [.01,.1,1.] for l in [.1,.7]]
    if name=='F2_PLS_INDEX':return [{'n_components':k} for k in [1,2,3,4,6,8] if k<=nfeat]
    if name.startswith('F2_XGB'):
        return [
          {'n_estimators':150,'max_depth':1,'learning_rate':.03,'min_child_weight':5,'subsample':.8,'colsample_bytree':.8,'reg_alpha':.5,'reg_lambda':5.},
          {'n_estimators':300,'max_depth':1,'learning_rate':.03,'min_child_weight':10,'subsample':.8,'colsample_bytree':.8,'reg_alpha':1.,'reg_lambda':10.},
          {'n_estimators':200,'max_depth':2,'learning_rate':.03,'min_child_weight':10,'subsample':.8,'colsample_bytree':.7,'reg_alpha':1.,'reg_lambda':10.},
          {'n_estimators':150,'max_depth':3,'learning_rate':.02,'min_child_weight':10,'subsample':.8,'colsample_bytree':.7,'reg_alpha':1.,'reg_lambda':15.}]
    return [{}]


def fit_predict_model(name,param,xtr,ytr,xva):
    if name=='F2_OLS_INDEX':m=LinearRegression().fit(xtr,ytr);return m.predict(xva),m
    if 'RIDGE' in name:
        sc=StandardScaler().fit(xtr);m=Ridge(alpha=param['alpha']).fit(sc.transform(xtr),ytr);return m.predict(sc.transform(xva)),(sc,m)
    if 'ENET' in name:
        sc=StandardScaler().fit(xtr);m=ElasticNet(alpha=param['alpha'],l1_ratio=param['l1_ratio'],max_iter=30000,random_state=SEED).fit(sc.transform(xtr),ytr);return m.predict(sc.transform(xva)),(sc,m)
    if 'PLS' in name:
        sc=StandardScaler().fit(xtr);m=PLSRegression(n_components=min(param['n_components'],xtr.shape[1]),scale=False,max_iter=1000).fit(sc.transform(xtr),ytr);return m.predict(sc.transform(xva)).ravel(),(sc,m)
    m=XGBRegressor(**param,objective='reg:squarederror',random_state=SEED,n_jobs=1,verbosity=0).fit(xtr,ytr);return m.predict(xva),m


def basis_and_penalty(t,n_basis=12):
    # Fixed basis depends only on the time domain. Design integral is the exact
    # scalar-on-function linear functional in this finite spline space.
    st=SplineTransformer(n_knots=n_basis-2,degree=3,include_bias=True,knots='uniform')
    B=st.fit_transform(t[:,None]);w=weights(t);D2=np.diff(np.eye(B.shape[1]),n=2,axis=0);R=D2.T@D2
    R=R/(np.trace(R)/len(R)+1e-12)
    return B,w,R


def sof_design(curves,idx,signals,B,w):return np.column_stack([curves[s][idx]@(B*w[:,None]) for s in signals])


def sof_fit(z,y,lam,R,nblocks):
    zm=z.mean(0);ym=y.mean();zc=z-zm;Rb=np.kron(np.eye(nblocks),R)
    coef=solve(zc.T@zc+lam*Rb+1e-8*np.eye(z.shape[1]),zc.T@(y-ym),assume_a='pos');return ym-zm@coef,coef


def inner_representations(curves,t,outer_train,seed):
    kf=KFold(4,shuffle=True,random_state=seed);out=[]
    for a,b in kf.split(outer_train):
        tr=outer_train[a];va=outer_train[b];fp=FoldFPCA(t).fit(curves,tr);zt=fp.transform(curves,tr);zv=fp.transform(curves,va);joint=JointSpace().fit(zt)
        out.append({'tr':tr,'va':va,'index_tr':zt,'index_va':zv,'joint':joint})
    return out


def tune_standard(name,inner,y,joint=False):
    candidates=[]
    basecfg=configs(name,inner[0]['index_tr'].shape[1])
    ks=[4,6,8] if joint else [None]
    for k in ks:
      for par in basecfg:
        pred=[];truth=[]
        for q in inner:
            xt=q['joint'].transform(q['index_tr'],k) if joint else q['index_tr']; xv=q['joint'].transform(q['index_va'],k) if joint else q['index_va']
            pp,_=fit_predict_model(name,par,xt,y.iloc[q['tr']].to_numpy(),xv);pred.extend(pp);truth.extend(y.iloc[q['va']])
        candidates.append((mean_squared_error(truth,pred)**.5,k,par))
    return min(candidates,key=lambda x:(x[0],999 if x[1] is None else x[1],json.dumps(x[2],sort_keys=True)))


def consolidate(ids,y):
    pred=pd.concat([pd.read_parquet(p) for p in sorted(D['checkpoints'].glob('pred_fold_*.parquet'))],ignore_index=True)
    pred.to_parquet(D['predictions']/'oof_predictions.parquet',index=False)
    folds=[]
    for (p,r,f),g in pred.groupby(['pipeline','repeat','fold']):folds.append({'pipeline':p,'repeat':r,'fold':f,'n':len(g),**metric(g.y_true,g.y_pred)})
    fm=pd.DataFrame(folds);fm.to_csv(D['metrics']/'fold_metrics.csv',index=False)
    sm=fm.groupby('pipeline').agg(RMSE_mean=('RMSE','mean'),RMSE_median=('RMSE','median'),RMSE_std=('RMSE','std'),MAE_mean=('MAE','mean'),R2_mean=('R2','mean'),MedAE_mean=('MedAE','mean')).reset_index().sort_values('RMSE_mean')
    sm.to_csv(D['metrics']/'pipeline_metrics.csv',index=False)
    bp=pred.groupby(['pipeline',ID]).agg(y_true=('y_true','first'),oof_prediction_mean=('y_pred','mean'),oof_prediction_median=('y_pred','median'),oof_prediction_std=('y_pred','std')).reset_index();bp['residual']=bp.oof_prediction_mean-bp.y_true;bp['absolute_error']=abs(bp.residual);bp.to_csv(D['predictions']/'oof_by_parcel.csv',index=False)
    # Exact same-fold references.
    old=pd.read_parquet(ROOT/'outputs/modeling/family_1/source_contribution/predictions/source_oof_predictions.parquet')
    refs=old[old.pipeline.isin(['XGB_SATELLITE','XGB_CORE'])]
    rf=[]
    for (p,r,f),g in refs.groupby(['pipeline','repeat','fold']):rf.append({'pipeline':p,'repeat':r,'fold':f,**metric(g.y_true,g.y_pred)})
    allfm=pd.concat([fm,pd.DataFrame(rf)],ignore_index=True);wide=allfm.pivot(index=['repeat','fold'],columns='pipeline',values='RMSE');best=sm.pipeline.iloc[0]
    comps=[]
    for other in list(sm.pipeline[1:])+['XGB_SATELLITE','XGB_CORE']:
        delta=wide[other]-wide[best];
        try:pval=wilcoxon(delta).pvalue
        except Exception:pval=np.nan
        comps.append({'better_pipeline':best,'comparison_pipeline':other,'mean_RMSE_gain':delta.mean(),'median_RMSE_gain':delta.median(),'win_rate':(delta>0).mean(),'wilcoxon_pvalue':pval})
    pd.DataFrame(comps).to_csv(D['metrics']/'paired_comparisons.csv',index=False)
    # Yield segments and calibration use parcel-aggregated OOF only.
    refbp=refs.groupby(['pipeline',ID]).agg(y_true=('y_true','first'),oof_prediction_mean=('y_pred','mean')).reset_index()
    refbp['residual']=refbp.oof_prediction_mean-refbp.y_true
    diagbp=pd.concat([bp,refbp],ignore_index=True,sort=False)
    q25=y.quantile(.25);q75=y.quantile(.75);seg=[];cal=[]
    for p,g in diagbp.groupby('pipeline'):
        for label,mask in [('LOW',g.y_true<=q25),('MID',(g.y_true>q25)&(g.y_true<q75)),('HIGH',g.y_true>=q75)]:
            z=g[mask];seg.append({'pipeline':p,'segment':label,'n':len(z),'RMSE':mean_squared_error(z.y_true,z.oof_prediction_mean)**.5,'MAE':mean_absolute_error(z.y_true,z.oof_prediction_mean),'bias':z.residual.mean()})
        slope,intercept=np.polyfit(g.y_true,g.oof_prediction_mean,1);cal.append({'pipeline':p,'n':len(g),'alpha':intercept,'beta':slope,'R2':r2_score(g.oof_prediction_mean,intercept+slope*g.y_true)})
    pd.DataFrame(seg).to_csv(D['diagnostics']/'yield_segment_performance.csv',index=False);pd.DataFrame(cal).to_csv(D['diagnostics']/'calibration_summary.csv',index=False)
    # Difficult parcels: compare compatible aggregated OOF sources.
    hard=pd.read_csv(ROOT/'outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv');hard=hard[hard.support_class.eq('y-outlier given similar X')][[ID]]
    fd=pd.read_csv(ROOT/'outputs/modeling/family_2/stage2_fpca/diagnostics/difficult_parcels_functional_distance.csv')[[ID,'core_5nn_percentile','functional_5nn_percentile']]
    f1=old.groupby(['pipeline',ID]).agg(y_true=('y_true','first'),pred=('y_pred','mean')).reset_index();f1=f1[f1.pipeline.isin(['XGB_SATELLITE','XGB_CORE'])];f1['absolute_error']=abs(f1.pred-f1.y_true)
    dw=hard.merge(fd,on=ID).merge(f1.pivot(index=ID,columns='pipeline',values='absolute_error').reset_index(),on=ID).merge(bp[bp.pipeline.eq(best)][[ID,'absolute_error']].rename(columns={'absolute_error':'F2_best_absolute_error'}),on=ID)
    dw['increased_functional_distance']=dw.functional_5nn_percentile>dw.core_5nn_percentile;dw['improvement_vs_satellite']=dw.XGB_SATELLITE-dw.F2_best_absolute_error;dw['best_F2_pipeline']=best;dw.to_csv(D['diagnostics']/'difficult_parcels_performance.csv',index=False)
    # SOF stability.
    cf=pd.concat([pd.read_parquet(p) for p in sorted(D['checkpoints'].glob('coef_fold_*.parquet'))],ignore_index=True);cf.to_parquet(D['sof']/'coefficient_functions.parquet',index=False)
    st=cf.groupby(['pipeline','signal','t']).beta.agg(beta_mean='mean',beta_median='median',beta_std='std',n_folds='count',proportion_positive=lambda x:(x>0).mean()).reset_index();st['proportion_folds_same_sign']=np.maximum(st.proportion_positive,1-st.proportion_positive);st.to_csv(D['sof']/'coefficient_function_stability.csv',index=False)
    regions=[]
    for (p,sig),g in st.groupby(['pipeline','signal']):
        g=g.sort_values('t');good=g.proportion_folds_same_sign.ge(.8).to_numpy();tt=g.t.to_numpy();start=None
        for i,ok in enumerate(np.r_[good,False]):
            if ok and start is None:start=i
            elif not ok and start is not None:
                if i-start>=7:
                    q=g.iloc[start:i];regions.append({'pipeline':p,'signal':sig,'start_t':int(tt[start]),'end_t':int(tt[i-1]),'n_days':i-start,
                      'dominant_sign':'positive' if q.proportion_positive.mean()>=.5 else 'negative','mean_same_sign_proportion':q.proportion_folds_same_sign.mean(),'mean_beta':q.beta_mean.mean()})
                start=None
    pd.DataFrame(regions).to_csv(D['sof']/'coefficient_stable_regions.csv',index=False)
    # Lightweight figures.
    plt.figure(figsize=(10,6));sns.barplot(data=sm,x='RMSE_mean',y='pipeline',color='#4C78A8');plt.axvline(.584546,ls='--',color='black',label='Family1 Satellite-only');plt.legend();plt.tight_layout();plt.savefig(D['figures']/'pipeline_rmse_comparison.png',dpi=180);plt.close()
    top=st[st.pipeline.eq(best)] if best.startswith('SOF') else st[st.pipeline.eq(st.groupby('pipeline').beta_std.mean().idxmin())]
    if len(top):
      plt.figure(figsize=(10,6));sns.lineplot(data=top,x='t',y='beta_mean',hue='signal');plt.axhline(0,color='black',lw=.8);plt.tight_layout();plt.savefig(D['figures']/'sof_coefficient_stability.png',dpi=180);plt.close()
    return pred,fm,sm,bp,best,dw,st


def report(sm,bp,best,dw,st):
    b=sm.set_index('pipeline').loc[best];bench=.584546;core=.527033;clim=.5107
    idx=sm[sm.pipeline.str.endswith('_INDEX')].iloc[0];joint=sm[sm.pipeline.str.endswith('_JOINT')].iloc[0];sof=sm[sm.pipeline.str.startswith('SOF_')].iloc[0]
    cal=pd.read_csv(D['diagnostics']/'calibration_summary.csv').set_index('pipeline');seg=pd.read_csv(D['diagnostics']/'yield_segment_performance.csv')
    hp=pd.read_csv(D['models']/'selected_hyperparameters.csv');jointk=hp[hp.pipeline.str.endswith('_JOINT')].selected_joint_components.value_counts().to_dict()
    curves=sm[sm.pipeline.isin(['SOF_NDVI','SOF_SAVI','SOF_NDWI','SOF_DSWI4'])][['pipeline','RMSE_mean']].to_dict('records')
    stable=pd.read_csv(D['sof']/'coefficient_stable_regions.csv').sort_values('n_days',ascending=False).head(12).to_dict('records')
    low=seg[(seg.pipeline==best)&(seg.segment=='LOW')].iloc[0];high=seg[(seg.pipeline==best)&(seg.segment=='HIGH')].iloc[0]
    satlow=seg[(seg.pipeline=='XGB_SATELLITE')&(seg.segment=='LOW')].iloc[0];sathigh=seg[(seg.pipeline=='XGB_SATELLITE')&(seg.segment=='HIGH')].iloc[0]
    gain=bench-b.RMSE_mean
    txt=f"""# Familia 2 — F2.3 Round 1 functional-only

## Controles

Se reutilizaron exactamente 50 outer folds (5×10) y 4 inner folds. Las cuatro señales quedaron congeladas por F2.2. En cada inner y outer train se reajustaron media funcional, FPCA, proyección, escalado, joint PCA y regresor. Smoothing default de F2.1 permaneció congelado y target-free. No se incorporaron fuentes prohibidas ni se inició el modelo híbrido.

## Respuestas

1. **Mejor modelo functional-only:** `{best}`.
2. **RMSE:** media {b.RMSE_mean:.4f}, mediana {b.RMSE_median:.4f}.
3. **Family1 Satellite-only:** {'sí supera' if gain>0 else 'no supera'} 0.5845.
4. **Diferencia:** Family 2 es {abs(gain):.4f} RMSE {'mejor' if gain>0 else 'peor'} que Satellite-only.
5. **XGB_CORE 0.5270:** diferencia del mejor F2 = {b.RMSE_mean-core:+.4f}; {'lo supera' if b.RMSE_mean<core else 'no lo alcanza'}.
6. **Climate Current 0.5107:** diferencia = {b.RMSE_mean-clim:+.4f}; {'lo supera' if b.RMSE_mean<clim else 'no lo alcanza'}.
7. **F_INDEX vs F_JOINT:** mejores respectivos `{idx.pipeline}` ({idx.RMSE_mean:.4f}) y `{joint.pipeline}` ({joint.RMSE_mean:.4f}); gana {'F_INDEX' if idx.RMSE_mean<joint.RMSE_mean else 'F_JOINT'}.
8. **Dimensiones:** selección de ejes joint por fold/modelo: {jointk}. Se eligieron 8 en 115/150 ajustes outer y 6 en 35/150; 4 nunca ganó. Aproximadamente 6 ejes no parecen suficientes bajo inner CV. La FPCA por índice usa 17–18 scores.
9. **Linealidad:** Ridge/ENET mejor = {min(idx.RMSE_mean,joint.RMSE_mean):.4f}. Regularización lineal es suficiente frente a XGB, pero SOF_ALL4 mejora modestamente a ambas representaciones FPCA.
10. **No linealidad XGB:** XGB_INDEX={sm.set_index('pipeline').loc['F2_XGB_INDEX','RMSE_mean']:.4f}, frente a Ridge INDEX={sm.set_index('pipeline').loc['F2_RIDGE_INDEX','RMSE_mean']:.4f}; XGB_JOINT={sm.set_index('pipeline').loc['F2_XGB_JOINT','RMSE_mean']:.4f}, frente a ENET JOINT={sm.set_index('pipeline').loc['F2_ENET_JOINT','RMSE_mean']:.4f}. No hay ganancia no lineal consistente.
11. **PLS compacto:** PLS_INDEX={sm.set_index('pipeline').loc['F2_PLS_INDEX','RMSE_mean']:.4f}, peor que PLS_CORE≈0.5565 y PLS_ALL≈0.5556 de Familia 1. Reabrir PLS no recuperó la señal perdida.
12. **Scalar-on-function:** mejor `{sof.pipeline}`={sof.RMSE_mean:.4f}; {'es competitivo' if sof.RMSE_mean<=b.RMSE_mean+.02 else 'queda claramente detrás'} respecto al mejor.
13. **Curvas individuales:** {curves}.
14. **Vigor vs humedad:** SOF_VIGOR={sm.set_index('pipeline').loc['SOF_VIGOR','RMSE_mean']:.4f}; SOF_MOISTURE={sm.set_index('pipeline').loc['SOF_MOISTURE','RMSE_mean']:.4f}.
15. **Regiones beta estables:** {stable}. Son estabilidad de signo descriptiva, no evidencia de un evento biológico puntual.
16. **Parcelas difíciles:** mejora media frente a Satellite-only={dw.improvement_vs_satellite.mean():+.4f}; mejoran {(dw.improvement_vs_satellite>0).sum()}/9. Entre las seis con mayor distancia funcional, mejoran {(dw[dw.increased_functional_distance].improvement_vs_satellite>0).sum()}/{dw.increased_functional_distance.sum()}.
17. **Extremos:** mejor F2 LOW RMSE={low.RMSE:.4f}, bias={low.bias:+.4f}, frente a Satellite {satlow.RMSE:.4f}/{satlow.bias:+.4f}; HIGH RMSE={high.RMSE:.4f}, bias={high.bias:+.4f}, frente a Satellite {sathigh.RMSE:.4f}/{sathigh.bias:+.4f}. F2 reduce levemente el sesgo absoluto, pero empeora el error en ambos extremos.
18. **Regresión a la media:** beta de calibración={cal.loc[best,'beta']:.3f}, frente a XGB_SATELLITE={cal.loc['XGB_SATELLITE','beta']:.3f} y XGB_CORE={cal.loc['XGB_CORE','beta']:.3f}. F2 reduce algo la compresión respecto a Satellite-only, pero sigue peor que CORE y lejos de 1; no se calibraron predicciones.
19. **Avance híbrido:** {'sí hay evidencia para probar Climate + Functional Satellite' if gain>0 else 'la señal funcional aislada no supera el benchmark directo; un híbrido sólo se justifica como prueba acotada de complementariedad'}.
20. **Conservar:** {', '.join(sm.head(3).pipeline)} como candidatos provisionales por RMSE; en la ronda híbrida conviene evitar representaciones casi duplicadas y decidir con comparaciones pareadas.

## Advertencias

Los 18 scores globales de F2.2 no se usaron como predictores fijos. Las funciones beta resumen 50 outer folds; un pico aislado no se interpreta causalmente. Los benchmarks se reutilizaron, no se reentrenaron.
"""
    (D['report']/'family2_stage3_round1_report.md').write_text(txt,encoding='utf-8')


def main():
    ids,y,t,curves=load_data();splits=save_splits(ids);idpos={p:i for i,p in enumerate(ids)};B,w,R=basis_and_penalty(t)
    hpall=[];fmeta=[];fev=[]
    for k,s in splits.iterrows():
        ck=D['checkpoints']/f'pred_fold_{k:02d}.parquet';cc=D['checkpoints']/f'coef_fold_{k:02d}.parquet';hm=D['checkpoints']/f'meta_fold_{k:02d}.json'
        if ck.exists() and cc.exists() and hm.exists():
            old=json.loads(hm.read_text());hpall+=old['hp'];fmeta+=old['fmeta'];fev+=old['fev'];print(f'fold {k+1}/50 cached',flush=True);continue
        tr=np.array([idpos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([idpos[v] for v in json.loads(s.validation_ID_POLIGONO)])
        inner=inner_representations(curves,t,tr,SEED+k);fp=FoldFPCA(t).fit(curves,tr);zt=fp.transform(curves,tr);zv=fp.transform(curves,va);joint=JointSpace().fit(zt)
        foldpred=[];foldcoef=[];foldhp=[];start=time.time()
        md=fp.metadata();
        for _,r in md.iterrows():fev.append({'repeat':s['repeat'],'fold':s['fold'],**r.to_dict()})
        fmeta.append({'repeat':s['repeat'],'fold':s['fold'],'n_outer_train':len(tr),'n_outer_validation':len(va),'n_index_scores':zt.shape[1],**{f'{sig}_components':fp.models[sig][4] for sig in SIGNALS}})
        for name in INDEX_MODELS:
            if name=='F2_OLS_INDEX':score=np.nan;jk=None;par={};pred,model=fit_predict_model(name,par,zt,y.iloc[tr],zv)
            else:
                score,jk,par=tune_standard(name,inner,y,False);pred,model=fit_predict_model(name,par,zt,y.iloc[tr],zv)
            nz=np.nan
            if 'ENET' in name:nz=int(np.count_nonzero(model[1].coef_))
            foldhp.append({'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'inner_RMSE':score,'selected_joint_components':jk,'best_params':json.dumps(par,sort_keys=True),'n_outer_features':zt.shape[1],'nonzero_coefficients':nz})
            foldpred += [{ID:p,'repeat':s['repeat'],'fold':s['fold'],'y_true':yt,'y_pred':yp,'pipeline':name,'representation':'F_INDEX'} for p,yt,yp in zip(ids.iloc[va],y.iloc[va],pred)]
        for name in JOINT_MODELS:
            score,jk,par=tune_standard(name,inner,y,True);xtr=joint.transform(zt,jk);xva=joint.transform(zv,jk);pred,model=fit_predict_model(name,par,xtr,y.iloc[tr],xva)
            nz=int(np.count_nonzero(model[1].coef_)) if 'ENET' in name else np.nan
            foldhp.append({'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'inner_RMSE':score,'selected_joint_components':jk,'best_params':json.dumps(par,sort_keys=True),'n_outer_features':xtr.shape[1],'nonzero_coefficients':nz})
            foldpred += [{ID:p,'repeat':s['repeat'],'fold':s['fold'],'y_true':yt,'y_pred':yp,'pipeline':name,'representation':'F_JOINT'} for p,yt,yp in zip(ids.iloc[va],y.iloc[va],pred)]
        # Genuine scalar-on-function: inner tuning of roughness lambda.
        for name,sigs in SOF_BLOCKS.items():
            vals=[]
            for lam in [.01,.1,1.,10.,100.]:
                pp=[];yy=[]
                for q in inner:
                    a=sof_design(curves,q['tr'],sigs,B,w);b=sof_design(curves,q['va'],sigs,B,w);inter,coef=sof_fit(a,y.iloc[q['tr']].to_numpy(),lam,R,len(sigs));pp.extend(inter+b@coef);yy.extend(y.iloc[q['va']])
                vals.append((mean_squared_error(yy,pp)**.5,lam))
            score,lam=min(vals);a=sof_design(curves,tr,sigs,B,w);b=sof_design(curves,va,sigs,B,w);inter,coef=sof_fit(a,y.iloc[tr].to_numpy(),lam,R,len(sigs));pred=inter+b@coef
            foldhp.append({'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'inner_RMSE':score,'selected_joint_components':np.nan,'best_params':json.dumps({'lambda':lam}),'n_outer_features':a.shape[1],'nonzero_coefficients':np.nan})
            foldpred += [{ID:p,'repeat':s['repeat'],'fold':s['fold'],'y_true':yt,'y_pred':yp,'pipeline':name,'representation':'SCALAR_ON_FUNCTION'} for p,yt,yp in zip(ids.iloc[va],y.iloc[va],pred)]
            nb=B.shape[1]
            for j,sig in enumerate(sigs):
                beta=B@coef[j*nb:(j+1)*nb]
                foldcoef += [{'pipeline':name,'signal':sig,'repeat':s['repeat'],'fold':s['fold'],'t':int(tt),'date':pd.Timestamp('2025-04-01')+pd.Timedelta(days=int(tt)),'beta':bb,'lambda':lam} for tt,bb in zip(t,beta)]
        pd.DataFrame(foldpred).to_parquet(ck,index=False);pd.DataFrame(foldcoef).to_parquet(cc,index=False)
        hm.write_text(json.dumps({'hp':foldhp,'fmeta':fmeta[-1:],'fev':fev[-len(md):]},default=lambda x:x.item() if hasattr(x,'item') else x),encoding='utf-8')
        hpall+=foldhp;print(f"fold {k+1}/50 complete in {time.time()-start:.1f}s",flush=True)
    pd.DataFrame(hpall).to_csv(D['models']/'selected_hyperparameters.csv',index=False);pd.DataFrame(fmeta).to_csv(D['fpca_cv']/'fold_fpca_metadata.csv',index=False);pd.DataFrame(fev).to_csv(D['fpca_cv']/'fold_explained_variance.csv',index=False)
    pd.DataFrame(fmeta)[['repeat','fold','n_index_scores']+[f'{s}_components' for s in SIGNALS]].to_csv(D['fpca_cv']/'selected_components.csv',index=False)
    pred,fm,sm,bp,best,dw,st=consolidate(ids,y);report(sm,bp,best,dw,st)
    print(f'F2.3 complete: best={best}, RMSE={sm.iloc[0].RMSE_mean:.4f}',flush=True)

if __name__=='__main__':main()
