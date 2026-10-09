"""Climate Regime Stage R2: caracterizacion y prediccion regime-aware.

La solucion global R1 se usa solo descriptivamente. En CV, scaler/PCA/GMM se
reajustan dentro de cada inner/outer train y se alinean contra perfiles R1 sin y.
"""
from pathlib import Path
import sys,json,time,warnings,importlib.util
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('hyb',Path(__file__).with_name('204_family2_round2_hybrid.py'));hyb=importlib.util.module_from_spec(spec);spec.loader.exec_module(hyb)
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import linear_sum_assignment
from scipy.stats import spearmanr,wilcoxon
from sklearn.model_selection import KFold
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,median_absolute_error
from xgboost import XGBRegressor
from family_1.stage4_modeling import load_xy,save_splits,ID,SEED,FEATURE_DIR
warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid')

BASE=ROOT/'outputs/modeling/family_1/climate_regimes/stage2_characterization_prediction'
D={x:BASE/x for x in ['characterization','cv','metrics','predictions','interactions','diagnostics','figures','report','checkpoints']}
for p in D.values():p.mkdir(parents=True,exist_ok=True)
PIPES=['CLIMATE_ENET_BASE','CLIMATE_XGB_BASE','ENET_CLIMATE_PLUS_MEMBERSHIP','XGB_CLIMATE_PLUS_MEMBERSHIP','ENET_SOFT_INTERACTIONS','ENET_HARD_INTERACTIONS']
COMPACT=['CLIMATE_precip_total','CLIMATE_precip_early_sum','CLIMATE_precip_mid_sum','CLIMATE_precip_late_sum','CLIMATE_precip_wettest_fraction','CLIMATE_tmin_mean_mean','CLIMATE_tmax_mean_mean','CLIMATE_tmean_mean_mean','CLIMATE_dtr_mean_mean','CLIMATE_tmean_mean_std']

def metric(y,p):return {'RMSE':mean_squared_error(y,p)**.5,'MAE':mean_absolute_error(y,p),'R2':r2_score(y,p),'MedAE':median_absolute_error(y,p)}
def weighted_median(x,w):
    o=np.argsort(x);x=np.asarray(x)[o];w=np.asarray(w)[o];return x[np.searchsorted(np.cumsum(w),w.sum()/2)]

def load_all():
    ids,X,y=load_xy();cols=hyb.climate_columns(X);C=X[cols].reset_index(drop=True);ids=ids.reset_index(drop=True);y=y.reset_index(drop=True)
    r1base=ROOT/'outputs/modeling/family_1/climate_regimes/stage1_discovery';mem=pd.read_parquet(r1base/'memberships/climate_regime_memberships.parquet');prof=pd.read_csv(r1base/'profiles/climate_regime_profiles.csv');scale=pd.read_csv(r1base/'diagnostics/scaler_parameters.csv').set_index('feature')
    ref=np.row_stack([prof[prof.regime.eq(j)].set_index('feature').reindex(cols).weighted_mean.to_numpy() for j in [1,2]])
    refz=(ref-scale.reindex(cols).scaler_mean.to_numpy())/scale.reindex(cols).scaler_scale.to_numpy()
    return ids,C,y,cols,mem,refz

class FoldRegime:
    def __init__(self,refz):self.refz=refz
    def fit(self,C,idx):
        self.imp=SimpleImputer(strategy='median').fit(C.iloc[idx]);x=self.imp.transform(C.iloc[idx]);self.sc=StandardScaler().fit(x);z=self.sc.transform(x);self.pca=PCA(n_components=.95,svd_solver='full').fit(z);q=self.pca.transform(z);self.gmm=GaussianMixture(n_components=2,covariance_type='full',reg_covar=1e-5,n_init=20,max_iter=1000,random_state=SEED).fit(q)
        rawp=self.gmm.predict_proba(q);profiles=rawp.T@x/rawp.sum(0)[:,None];profiles_z=(profiles-self.sc.mean_)/self.sc.scale_;cost=((profiles_z[:,None,:]-self.refz[None,:,:])**2).mean(2);row,col=linear_sum_assignment(cost);self.order=np.empty(2,dtype=int);self.order[col]=row;self.match_cost=float(cost[row,col].mean());return self
    def transform(self,C,idx):
        x=self.imp.transform(C.iloc[idx]);p=self.gmm.predict_proba(self.pca.transform(self.sc.transform(x)))[:,self.order];return p
    def meta(self):
        cv=self.gmm.covariances_;mineig=min(np.linalg.eigvalsh(q).min() for q in cv)
        return {'n_pcs':self.pca.n_components_,'explained_variance':self.pca.explained_variance_ratio_.sum(),'converged':self.gmm.converged_,'n_iter':self.gmm.n_iter_,'min_covariance_eigenvalue':mineig,'alignment_order':'|'.join(map(str,self.order)),'alignment_cost':self.match_cost}

def inner_data(C,outer,refz,seed):
    out=[]
    for a,b in KFold(4,shuffle=True,random_state=seed).split(outer):
        tr=outer[a];va=outer[b];reg=FoldRegime(refz).fit(C,tr);out.append({'tr':tr,'va':va,'ptr':reg.transform(C,tr)[:,1],'pva':reg.transform(C,va)[:,1]})
    return out

def design(Carr,p,cols,kind):
    if kind=='base':return Carr,cols
    if kind=='membership':return np.column_stack([Carr,p]),cols+['p_regime2']
    hard=(p>=.5).astype(float);gate=p if kind=='soft' else hard;names=cols+['p_regime2' if kind=='soft' else 'hard_regime2'];parts=[Carr,gate]
    for c in COMPACT:
        j=cols.index(c);parts.append(Carr[:,j]*gate);names.append(f'{c}__X__{kind}_regime2')
    return np.column_stack(parts),names

def configs(model):return hyb.grids('ENET' if model=='ENET' else 'XGB')
def fit_model(model,param,x,y):
    if model=='ENET':return ElasticNet(alpha=param['alpha'],l1_ratio=param['l1_ratio'],max_iter=30000,random_state=SEED).fit(x,y)
    return XGBRegressor(**param,objective='reg:squarederror',random_state=SEED,n_jobs=1,verbosity=0).fit(x,y)

def tune(model,kind,inner,C,y,cols):
    vals=[];scale=model=='ENET'
    for par in configs(model):
        pp=[];yy=[]
        for q in inner:
            imp=SimpleImputer(strategy='median').fit(C.iloc[q['tr']]);a=imp.transform(C.iloc[q['tr']]);b=imp.transform(C.iloc[q['va']]);xa,_=design(a,q['ptr'],cols,kind);xb,_=design(b,q['pva'],cols,kind)
            if scale:sc=StandardScaler().fit(xa);xa=sc.transform(xa);xb=sc.transform(xb)
            m=fit_model(model,par,xa,y.iloc[q['tr']]);pp.extend(m.predict(xb));yy.extend(y.iloc[q['va']])
        vals.append((mean_squared_error(yy,pp)**.5,par))
    return min(vals,key=lambda q:(q[0],json.dumps(q[1],sort_keys=True)))

def characterize(ids,y,global_mem):
    d=pd.DataFrame({ID:ids,'yield':y}).merge(global_mem,on=ID);q25=y.quantile(.25);q75=y.quantile(.75);rows=[]
    for r,g in d.groupby('regime_hard'):
        p=d[f'regime_probability_{int(r)}'];v=d['yield'];hard=g['yield'];rows.append({'regime':int(r),'hard_n':len(g),'effective_membership_size_train':p.sum(),'hard_mean_yield':hard.mean(),'hard_median_yield':hard.median(),'hard_std_yield':hard.std(),'hard_q10':hard.quantile(.1),'hard_q25':hard.quantile(.25),'hard_q75':hard.quantile(.75),'hard_q90':hard.quantile(.9),'hard_min':hard.min(),'hard_max':hard.max(),'weighted_mean_yield':np.average(v,weights=p),'weighted_median_yield':weighted_median(v,p),'proportion_low':(hard<=q25).mean(),'proportion_mid':((hard>q25)&(hard<q75)).mean(),'proportion_high':(hard>=q75).mean()})
    pd.DataFrame(rows).to_csv(D['characterization']/'yield_by_regime.csv',index=False)
    p=d.regime_probability_2;rho,pv=spearmanr(p,y);bins=pd.cut(p,[-1e-9,.1,.25,.5,.75,.9,1+1e-9],labels=['0-.1','.1-.25','.25-.5','.5-.75','.75-.9','.9-1'])
    z=d.assign(membership_bin=bins).groupby('membership_bin',observed=False).agg(n=('yield','size'),mean_yield=('yield','mean'),median_yield=('yield','median'),std_yield=('yield','std'),mean_p_regime2=('regime_probability_2','mean')).reset_index();z['spearman_rho']=rho;z['spearman_p_descriptive']=pv;z.to_csv(D['characterization']/'yield_vs_membership.csv',index=False)
    return d,rho

def existing_errors(global_desc):
    old2=pd.read_parquet(ROOT/'outputs/modeling/family_2/stage3_round2_hybrid/predictions/oof_predictions.parquet');old2=old2[old2.pipeline.isin(['CLIMATE_ENET','CLIMATE_XGB'])]
    old1=pd.read_parquet(ROOT/'outputs/modeling/family_1/source_contribution/predictions/source_oof_predictions.parquet');old1=old1[old1.pipeline.eq('XGB_CORE')][[ID,'repeat','fold','y_true','y_pred','pipeline']]
    z=pd.concat([old2[[ID,'repeat','fold','y_true','y_pred','pipeline']],old1]).groupby(['pipeline',ID]).agg(y_true=('y_true','first'),pred=('y_pred','mean')).reset_index().merge(global_desc[[ID,'regime_hard','regime_probability_2']],on=ID);z['residual']=z.pred-z.y_true
    rows=[]
    for (p,r),g in z.groupby(['pipeline','regime_hard']):
        slope=np.polyfit(g.y_true,g.pred,1)[0] if len(g)>=10 else np.nan;rows.append({'pipeline':p,'group_type':'hard_regime','group':f'R{r}','n':len(g),**metric(g.y_true,g.pred),'bias':g.residual.mean(),'calibration_slope':slope})
    z['p_bin']=pd.cut(z.regime_probability_2,[-1e-9,.1,.5,.9,1+1e-9],labels=['0-.1','.1-.5','.5-.9','.9-1'])
    for (p,r),g in z.groupby(['pipeline','p_bin'],observed=False):
        if len(g):rows.append({'pipeline':p,'group_type':'p_regime2_bin','group':str(r),'n':len(g),**metric(g.y_true,g.pred),'bias':g.residual.mean(),'calibration_slope':np.polyfit(g.y_true,g.pred,1)[0] if len(g)>=10 else np.nan})
    pd.DataFrame(rows).to_csv(D['characterization']/'existing_model_error_by_regime.csv',index=False)

def consolidate(y,global_desc):
    pred=pd.concat([pd.read_parquet(p) for p in sorted(D['checkpoints'].glob('pred_fold_*.parquet'))],ignore_index=True);pred.to_parquet(D['predictions']/'oof_predictions.parquet',index=False)
    memberships=pd.concat([pd.read_parquet(p) for p in sorted(D['checkpoints'].glob('membership_fold_*.parquet'))],ignore_index=True);memberships.to_parquet(D['cv']/'fold_regime_memberships.parquet',index=False)
    metas=pd.concat([pd.read_csv(p) for p in sorted(D['checkpoints'].glob('meta_fold_*.csv'))],ignore_index=True);metas.to_csv(D['cv']/'fold_gmm_metadata.csv',index=False)
    fold=[]
    for (p,r,f),g in pred.groupby(['pipeline','repeat','fold']):fold.append({'pipeline':p,'repeat':r,'fold':f,'n':len(g),**metric(g.y_true,g.y_pred)})
    fm=pd.DataFrame(fold);fm.to_csv(D['metrics']/'fold_metrics.csv',index=False);sm=fm.groupby('pipeline').agg(RMSE_mean=('RMSE','mean'),RMSE_median=('RMSE','median'),RMSE_std=('RMSE','std'),MAE_mean=('MAE','mean'),R2_mean=('R2','mean'),MedAE_mean=('MedAE','mean')).reset_index().sort_values('RMSE_mean');sm.to_csv(D['metrics']/'pipeline_metrics.csv',index=False)
    bp=pred.groupby(['pipeline',ID]).agg(y_true=('y_true','first'),oof_prediction_mean=('y_pred','mean'),oof_prediction_std=('y_pred','std')).reset_index();bp['residual']=bp.oof_prediction_mean-bp.y_true;bp['absolute_error']=abs(bp.residual);bp.to_csv(D['predictions']/'oof_by_parcel.csv',index=False)
    pairs=[('CLIMATE_ENET_BASE','ENET_CLIMATE_PLUS_MEMBERSHIP'),('CLIMATE_XGB_BASE','XGB_CLIMATE_PLUS_MEMBERSHIP'),('CLIMATE_ENET_BASE','ENET_SOFT_INTERACTIONS'),('CLIMATE_ENET_BASE','ENET_HARD_INTERACTIONS'),('ENET_HARD_INTERACTIONS','ENET_SOFT_INTERACTIONS')];wide=fm.pivot(index=['repeat','fold'],columns='pipeline',values='RMSE');pr=[]
    for base,new in pairs:
        delta=wide[new]-wide[base]
        try:pv=wilcoxon(delta).pvalue
        except:pv=np.nan
        pr.append({'record_type':'overall','repeat':np.nan,'baseline':base,'regime_model':new,'mean_delta_RMSE':delta.mean(),'median_delta_RMSE':delta.median(),'std_delta_RMSE':delta.std(),'q25_delta_RMSE':delta.quantile(.25),'q75_delta_RMSE':delta.quantile(.75),'regime_model_win_rate':(delta<0).mean(),'wilcoxon_p_descriptive':pv})
        for rep,g in delta.groupby(level=0):pr.append({'record_type':'repeat','repeat':rep,'baseline':base,'regime_model':new,'mean_delta_RMSE':g.mean(),'median_delta_RMSE':g.median(),'std_delta_RMSE':g.std(),'q25_delta_RMSE':g.quantile(.25),'q75_delta_RMSE':g.quantile(.75),'regime_model_win_rate':(g<0).mean(),'wilcoxon_p_descriptive':np.nan})
    pc=pd.DataFrame(pr);pc.to_csv(D['metrics']/'paired_comparisons.csv',index=False)
    # Fold-wise regime performance and membership/error bins.
    rp=[];mer=[]
    for (p,r,f),g in pred.groupby(['pipeline','repeat','fold']):
        for reg,h in g.groupby('regime_hard'):
            rp.append({'record_type':'fold','pipeline':p,'repeat':r,'fold':f,'regime':reg,'n':len(h),**metric(h.y_true,h.y_pred),'bias':(h.y_pred-h.y_true).mean()})
        bins=pd.cut(g.p_regime2,[-1e-9,.1,.5,.9,1+1e-9],labels=['0-.1','.1-.5','.5-.9','.9-1'])
        for bn,h in g.assign(p_bin=bins,abs_error=abs(g.y_pred-g.y_true)).groupby('p_bin',observed=False):
            if len(h):mer.append({'pipeline':p,'repeat':r,'fold':f,'p_regime2_bin':str(bn),'n':len(h),'MAE':h.abs_error.mean(),'bias':(h.y_pred-h.y_true).mean(),'mean_p':h.p_regime2.mean()})
    rdf=pd.DataFrame(rp);summ=rdf.groupby(['pipeline','regime']).agg(n_folds=('fold','size'),mean_n=('n','mean'),RMSE_mean=('RMSE','mean'),MAE_mean=('MAE','mean'),bias_mean=('bias','mean')).reset_index();pd.concat([rdf,summ.assign(record_type='summary')],ignore_index=True,sort=False).to_csv(D['metrics']/'regime_performance.csv',index=False);pd.DataFrame(mer).to_csv(D['diagnostics']/'membership_error_relationship.csv',index=False)
    q25=y.quantile(.25);q75=y.quantile(.75);seg=[]
    for p,g in bp.groupby('pipeline'):
        for lab,mask in [('LOW',g.y_true<=q25),('MID',(g.y_true>q25)&(g.y_true<q75)),('HIGH',g.y_true>=q75)]:
            h=g[mask];seg.append({'pipeline':p,'segment':lab,'n':len(h),'RMSE':mean_squared_error(h.y_true,h.oof_prediction_mean)**.5,'MAE':mean_absolute_error(h.y_true,h.oof_prediction_mean),'bias':h.residual.mean()})
    pd.DataFrame(seg).to_csv(D['metrics']/'yield_segment_performance.csv',index=False)
    # Coefficients and stability.
    co=pd.concat([pd.read_csv(p) for p in sorted(D['checkpoints'].glob('coef_fold_*.csv'))],ignore_index=True);co.to_csv(D['interactions']/'enet_interaction_coefficients.csv',index=False)
    st=co.groupby(['pipeline','feature_type','feature']).coefficient.agg(coefficient_mean='mean',coefficient_median='median',q25=lambda x:x.quantile(.25),q75=lambda x:x.quantile(.75),nonzero_frequency=lambda x:(x!=0).mean(),proportion_positive=lambda x:(x>0).mean(),n_folds='count').reset_index();st['sign_stability']=np.maximum(st.proportion_positive,1-st.proportion_positive);st.to_csv(D['interactions']/'interaction_stability.csv',index=False)
    # Difficult parcels (28) and nine y-atypical.
    hard=pd.read_csv(ROOT/'outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv');hard=hard[hard.difficult_all_3][[ID,'support_class']].merge(global_desc[[ID,'regime_hard','regime_probability_2']],on=ID)
    best=sm[~sm.pipeline.isin(['CLIMATE_ENET_BASE','CLIMATE_XGB_BASE'])].iloc[0].pipeline;base='CLIMATE_XGB_BASE' if best.startswith('XGB') else 'CLIMATE_ENET_BASE';a=bp[bp.pipeline.eq(base)].set_index(ID);h=bp[bp.pipeline.eq(best)].set_index(ID);hard['baseline_pipeline']=base;hard['regime_pipeline']=best;hard['baseline_absolute_error']=hard[ID].map(a.absolute_error);hard['regime_absolute_error']=hard[ID].map(h.absolute_error);hard['improvement']=hard.baseline_absolute_error-hard.regime_absolute_error;hard['y_atypical']=hard.support_class.eq('y-outlier given similar X');hard.to_csv(D['diagnostics']/'difficult_parcels_by_regime.csv',index=False)
    return pred,sm,pc,bp,st,hard

def plots(global_desc,bp,st,sm):
    fig,ax=plt.subplots(figsize=(7,4));sns.boxplot(data=global_desc,x='regime_hard',y='yield',ax=ax);sns.stripplot(data=global_desc,x='regime_hard',y='yield',color='black',alpha=.5,ax=ax);fig.tight_layout();fig.savefig(D['figures']/'yield_distribution_by_regime.png',dpi=180);plt.close(fig)
    plt.figure(figsize=(7,4));sns.regplot(data=global_desc,x='regime_probability_2',y='yield',lowess=True,scatter_kws={'alpha':.6});plt.tight_layout();plt.savefig(D['figures']/'yield_vs_membership.png',dpi=180);plt.close()
    old=pd.read_csv(D['characterization']/'existing_model_error_by_regime.csv');old=old[old.group_type.eq('hard_regime')];plt.figure(figsize=(8,4));sns.barplot(data=old,x='group',y='RMSE',hue='pipeline');plt.tight_layout();plt.savefig(D['figures']/'model_error_by_regime.png',dpi=180);plt.close()
    q=st[(st.pipeline=='ENET_SOFT_INTERACTIONS')&(st.feature_type=='interaction')].sort_values('nonzero_frequency');plt.figure(figsize=(9,5));plt.errorbar(q.coefficient_median,range(len(q)),xerr=[q.coefficient_median-q.q25,q.q75-q.coefficient_median],fmt='o');plt.yticks(range(len(q)),q.feature.str.replace('CLIMATE_','').str.replace('__X__soft_regime2',''));plt.axvline(0,color='black',lw=.8);plt.tight_layout();plt.savefig(D['figures']/'regime_interaction_coefficients.png',dpi=180);plt.close()
    z=sm[sm.pipeline.isin(['ENET_SOFT_INTERACTIONS','ENET_HARD_INTERACTIONS'])];plt.figure(figsize=(6,4));sns.barplot(data=z,x='pipeline',y='RMSE_mean');plt.xticks(rotation=15);plt.tight_layout();plt.savefig(D['figures']/'soft_vs_hard_performance.png',dpi=180);plt.close()

def report(global_desc,sm,pc,st,hard,rho):
    x=sm.set_index('pipeline');ov=pc[pc.record_type.eq('overall')];get=lambda base,new:ov[(ov.baseline==base)&(ov.regime_model==new)].iloc[0];yb=pd.read_csv(D['characterization']/'yield_by_regime.csv');er=pd.read_csv(D['characterization']/'existing_model_error_by_regime.csv');er=er[er.group_type.eq('hard_regime')];rp=pd.read_csv(D['metrics']/'regime_performance.csv');rp=rp[rp.record_type.eq('summary')];seg=pd.read_csv(D['metrics']/'yield_segment_performance.csv');stable=st[(st.pipeline=='ENET_SOFT_INTERACTIONS')&(st.feature_type=='interaction')&(st.nonzero_frequency>=.5)&(st.sign_stability>=.7)].sort_values('nonzero_frequency',ascending=False);gm=pd.read_csv(D['cv']/'fold_gmm_metadata.csv');fold_floor=int((gm.min_covariance_eigenvalue<=1.1e-5).sum());fold_r2_range=(gm.train_regime2_effective.min(),gm.train_regime2_effective.max());memb=pd.read_parquet(D['cv']/'fold_regime_memberships.parquet');conf=float((memb[['p_regime1','p_regime2']].max(axis=1)>.9).mean())
    bestreg=min(['ENET_CLIMATE_PLUS_MEMBERSHIP','XGB_CLIMATE_PLUS_MEMBERSHIP','ENET_SOFT_INTERACTIONS','ENET_HARD_INTERACTIONS'],key=lambda p:x.loc[p,'RMSE_mean']);bb='CLIMATE_XGB_BASE' if bestreg.startswith('XGB') else 'CLIMATE_ENET_BASE';q=get(bb,bestreg);minor=int(yb.sort_values('hard_n').iloc[0].regime);br=rp[(rp.pipeline==bestreg)&(rp.regime==minor)].iloc[0];bbr=rp[(rp.pipeline==bb)&(rp.regime==minor)].iloc[0]
    txt=f"""# Climate Regime Stage R2 — Characterization and Prediction

## Controles

La caracterización usa memberships globales R1; toda evaluación predictiva reajusta StandardScaler, PCA 95% y GMM K=2 full dentro de cada inner/outer train. Los componentes se alinean contra perfiles climáticos R1 mediante distancia de centroides estandarizados, nunca usando yield. Se reutilizan 50 outer folds y 4 inner folds. No se entrenaron expertos separados ni se inició R3/Familia 3. Diagnóstico de transportabilidad: {fold_floor}/50 outer GMM alcanzan el piso de covarianza y el tamaño efectivo train de R2 varía entre {fold_r2_range[0]:.1f} y {fold_r2_range[1]:.1f}; {conf:.1%} de memberships validation tienen probabilidad dominante >0.90.

## Respuestas

1. **Distribuciones distintas:** {yb[['regime','hard_n','hard_mean_yield','hard_median_yield','hard_std_yield']].round(3).to_dict('records')}; Spearman yield–P(R2)={rho:.3f}. Es asociación descriptiva, no causal.
2. **Mayor rendimiento:** régimen {int(yb.sort_values('hard_mean_yield',ascending=False).iloc[0].regime)} en media y régimen {int(yb.sort_values('hard_median_yield',ascending=False).iloc[0].regime)} en mediana.
3. **Nivel/dispersión/extremos:** cuantiles y proporciones LOW/MID/HIGH están en `yield_by_regime.csv`; las diferencias no redefinen los regímenes.
4. **Régimen más difícil:** {er[['pipeline','group','RMSE','MAE','R2','bias']].round(3).to_dict('records')}. R1 tiene mayor RMSE absoluto por su mayor dispersión; R2 tiene R² negativo y slope≈0, por lo que es más difícil explicar internamente.
5. **Bias CLIMATE_ENET:** {er[er.pipeline.eq('CLIMATE_ENET')][['group','bias','calibration_slope']].round(3).to_dict('records')}.
6. **Bias XGB:** {er[er.pipeline.eq('CLIMATE_XGB')][['group','bias','calibration_slope']].round(3).to_dict('records')}.
7. **Membership en ENET:** Δ medio={get('CLIMATE_ENET_BASE','ENET_CLIMATE_PLUS_MEMBERSHIP').mean_delta_RMSE:+.4f}, mediano={get('CLIMATE_ENET_BASE','ENET_CLIMATE_PLUS_MEMBERSHIP').median_delta_RMSE:+.4f}, wins={get('CLIMATE_ENET_BASE','ENET_CLIMATE_PLUS_MEMBERSHIP').regime_model_win_rate:.0%}.
8. **Membership en XGB:** Δ medio={get('CLIMATE_XGB_BASE','XGB_CLIMATE_PLUS_MEMBERSHIP').mean_delta_RMSE:+.4f}, wins={get('CLIMATE_XGB_BASE','XGB_CLIMATE_PLUS_MEMBERSHIP').regime_model_win_rate:.0%}.
9. **Soft interactions:** RMSE={x.loc['ENET_SOFT_INTERACTIONS','RMSE_mean']:.4f}; Δ={get('CLIMATE_ENET_BASE','ENET_SOFT_INTERACTIONS').mean_delta_RMSE:+.4f}, mediana={get('CLIMATE_ENET_BASE','ENET_SOFT_INTERACTIONS').median_delta_RMSE:+.4f}.
10. **Magnitud:** el signo anterior es regime-aware menos baseline; negativo representa mejora.
11. **Proporción de folds:** {get('CLIMATE_ENET_BASE','ENET_SOFT_INTERACTIONS').regime_model_win_rate:.0%}; resultados por repetición en `paired_comparisons.csv`.
12. **Hard vs soft:** hard RMSE={x.loc['ENET_HARD_INTERACTIONS','RMSE_mean']:.4f}, soft={x.loc['ENET_SOFT_INTERACTIONS','RMSE_mean']:.4f}; Δ soft−hard={get('ENET_HARD_INTERACTIONS','ENET_SOFT_INTERACTIONS').mean_delta_RMSE:+.4f}. Son prácticamente idénticos porque las memberships fold-wise también son casi discretas.
13. **Interacciones estables:** {stable[['feature','coefficient_median','q25','q75','nonzero_frequency','sign_stability']].round(3).to_dict('records')}.
14. **Temperatura/DTR:** revisar las filas `tmin/tmax/tmean/dtr` anteriores; sólo se consideran relativamente estables si frecuencia≥50% y estabilidad de signo≥70%.
15. **Precipitación:** mismo criterio para total, early, mid, late y concentración; no son efectos causales.
16. **Régimen minoritario R{minor}:** RMSE baseline={bbr.RMSE_mean:.4f}, regime-aware={br.RMSE_mean:.4f}; {'mejora' if br.RMSE_mean<bbr.RMSE_mean else 'empeora'}.
17. **Extremos:** {seg[seg.pipeline.isin([bb,bestreg])][['pipeline','segment','RMSE','bias']].round(3).to_dict('records')}.
18. **Parcelas difíciles:** mejoran {(hard.improvement>0).sum()}/28; entre las 9 y-atypical mejoran {(hard[hard.y_atypical].improvement>0).sum()}/9.
19. **Heterogeneidad climate→yield:** {'hay evidencia predictiva inicial' if q.mean_delta_RMSE<0 and q.median_delta_RMSE<0 and q.regime_model_win_rate>.5 else 'no hay evidencia predictiva consistente bajo los criterios predefinidos'}. Además, la inestabilidad/singularidad fold-wise indica que la partición global climática no se transporta limpiamente a muestras de ~110 parcelas.
20. **Stage R3:** {'se justifica sólo como siguiente prueba controlada' if q.mean_delta_RMSE<0 and q.median_delta_RMSE<0 and q.regime_model_win_rate>.5 and br.RMSE_mean<=bbr.RMSE_mean else 'no existe soporte suficiente para mixture-of-experts'}.
21. **Papel de regímenes:** {'pueden conservarse como candidatos predictivos además de descriptivos' if q.mean_delta_RMSE<0 and q.median_delta_RMSE<0 and q.regime_model_win_rate>.5 else 'deben conservarse principalmente como descripción climática'}.
"""
    (D['report']/'climate_regime_stage2_report.md').write_text(txt,encoding='utf-8')

def main():
    ids,C,y,cols,gmem,refz=load_all();global_desc,rho=characterize(ids,y,gmem);existing_errors(global_desc);pd.DataFrame({'feature':COMPACT,'selection_basis':['R1/dictionary target-free representative']*len(COMPACT),'role':['precipitation total','early precipitation','mid precipitation','late precipitation','precipitation concentration','Tmin level','Tmax level','Tmean level','DTR level','thermal variability']}).to_csv(D['interactions']/'regime_interaction_feature_set.csv',index=False)
    splits=save_splits(ids);pos={p:i for i,p in enumerate(ids)};hp=[]
    for k,s in splits.iterrows():
        files=[D['checkpoints']/f'{kind}_fold_{k:02d}.{ext}' for kind,ext in [('pred','parquet'),('membership','parquet'),('meta','csv'),('coef','csv'),('hp','csv')]]
        if all(p.exists() for p in files):hp+=pd.read_csv(files[-1]).to_dict('records');print(f'fold {k+1}/50 cached',flush=True);continue
        tr=np.array([pos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([pos[v] for v in json.loads(s.validation_ID_POLIGONO)]);inner=inner_data(C,tr,refz,SEED+k);reg=FoldRegime(refz).fit(C,tr);ptr=reg.transform(C,tr)[:,1];pva=reg.transform(C,va)[:,1];imp=SimpleImputer(strategy='median').fit(C.iloc[tr]);ct=imp.transform(C.iloc[tr]);cv=imp.transform(C.iloc[va]);predrows=[];coefrows=[];hprows=[];start=time.time()
        specs=[('CLIMATE_ENET_BASE','ENET','base'),('CLIMATE_XGB_BASE','XGB','base'),('ENET_CLIMATE_PLUS_MEMBERSHIP','ENET','membership'),('XGB_CLIMATE_PLUS_MEMBERSHIP','XGB','membership'),('ENET_SOFT_INTERACTIONS','ENET','soft'),('ENET_HARD_INTERACTIONS','ENET','hard')]
        for name,model,kind in specs:
            score,par=tune(model,kind,inner,C,y,cols);a,names=design(ct,ptr,cols,kind);b,_=design(cv,pva,cols,kind);sc=None
            if model=='ENET':sc=StandardScaler().fit(a);a=sc.transform(a);b=sc.transform(b)
            m=fit_model(model,par,a,y.iloc[tr]);yp=m.predict(b);hprows.append({'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'inner_RMSE':score,'best_params':json.dumps(par,sort_keys=True),'n_features':len(names)})
            predrows += [{ID:pid,'repeat':s['repeat'],'fold':s['fold'],'y_true':yt,'y_pred':pp,'pipeline':name,'p_regime2':pr,'regime_hard':int(pr>=.5)+1} for pid,yt,pp,pr in zip(ids.iloc[va],y.iloc[va],yp,pva)]
            if model=='ENET':
                for nm,co in zip(names,m.coef_):coefrows.append({'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'feature':nm,'feature_type':'interaction' if '__X__' in nm else 'membership' if nm in ['p_regime2','hard_regime2'] else 'base_climate','coefficient':co})
        meta={'repeat':s['repeat'],'fold':s['fold'],'n_train':len(tr),'n_validation':len(va),**reg.meta(),'train_regime1_effective':(1-ptr).sum(),'train_regime2_effective':ptr.sum(),'validation_regime1_effective':(1-pva).sum(),'validation_regime2_effective':pva.sum()}
        pd.DataFrame(predrows).to_parquet(files[0],index=False);pd.DataFrame({ID:ids.iloc[va],'repeat':s['repeat'],'fold':s['fold'],'p_regime1':1-pva,'p_regime2':pva,'regime_hard':(pva>=.5).astype(int)+1}).to_parquet(files[1],index=False);pd.DataFrame([meta]).to_csv(files[2],index=False);pd.DataFrame(coefrows).to_csv(files[3],index=False);pd.DataFrame(hprows).to_csv(files[4],index=False);hp+=hprows;print(f'fold {k+1}/50 complete in {time.time()-start:.1f}s',flush=True)
    pd.DataFrame(hp).to_csv(D['cv']/'selected_hyperparameters.csv',index=False);pred,sm,pc,bp,st,hard=consolidate(y,global_desc);plots(global_desc,bp,st,sm);report(global_desc,sm,pc,st,hard,rho);print(f'R2 complete: best={sm.iloc[0].pipeline}, RMSE={sm.iloc[0].RMSE_mean:.4f}',flush=True)

if __name__=='__main__':main()
