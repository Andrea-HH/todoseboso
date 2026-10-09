"""Residual Signal Audit RS1: señal incremental respecto a Climate ENET OOF."""
from pathlib import Path
import sys,json,time,warnings,importlib.util
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('f2r1',Path(__file__).with_name('203_family2_round1.py'));f2=importlib.util.module_from_spec(spec);spec.loader.exec_module(f2)
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr,spearmanr
from scipy.spatial.distance import pdist,squareform
from sklearn.model_selection import KFold
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge,ElasticNet
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from xgboost import XGBRegressor
from family_1.stage4_modeling import load_xy,save_splits,representations,FEATURE_DIR,ID,SEED
warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid')

BASE=ROOT/'outputs/modeling/residual_signal_audit/stage1'
D={x:BASE/x for x in ['residuals','associations','block_models','augmentation','diagnostics','figures','report','checkpoints']}
for p in D.values():p.mkdir(parents=True,exist_ok=True)
BLOCK_FILES={'SENTINEL_CORE':'sentinel_features_core.parquet','PLANET':'planet_features.parquet','LANDSAT':'landsat_features.parquet','TOPO_BASIC':'topography_basic_features.parquet','TOPO_ADVANCED':'topography_advanced_features.parquet','HISTORY':'history_features.parquet','ANOMALY':'anomaly_features.parquet'}
MODELS=['RIDGE','ENET','XGB'];CLIMATE_ALPHAS=[.01,.1,1.];CLIMATE_L1=[.1,.7]

def metric(y,p):return {'RMSE':mean_squared_error(y,p)**.5,'MAE':mean_absolute_error(y,p),'R2':r2_score(y,p)}
def safe_corr(a,b,kind):
    # Correlations are positional: feature tables can carry parcel IDs as their
    # index while the OOF residual vector has a RangeIndex.  Building a frame
    # directly from both Series would align those unlike labels and yield NaN.
    z=pd.DataFrame({'a':np.asarray(a,dtype=float),'b':np.asarray(b,dtype=float)}).dropna()
    if len(z)<3 or z.a.nunique()<2 or z.b.nunique()<2:return np.nan
    return float((pearsonr if kind=='pearson' else spearmanr)(z.a,z.b).statistic)

def load_blocks(ids):
    blocks={}
    for name,file in BLOCK_FILES.items():
        d=pd.read_parquet(FEATURE_DIR/file).set_index(ID).reindex(ids);blocks[name]=d
    # Global scores only for descriptive association; fold-specific FPCA is used predictively.
    s=pd.read_parquet(ROOT/'data/processed/family_2/fpca/fpca_scores.parquet');wide=None
    for sig,g in s.groupby('signal'):
        q=g.drop(columns=['source','signal','CONJUNTO']).rename(columns={c:f'{sig}_{c}' for c in g if c.startswith('FPC')})
        wide=q if wide is None else wide.merge(q,on=ID)
    blocks['FUNCTIONAL_FPCA']=wide.set_index(ID).reindex(ids)
    return blocks

def climate_cols(X):
    core=representations(X.columns)['CORE'];dic=pd.read_csv(FEATURE_DIR/'family1_feature_dictionary.csv').set_index('feature_name');return [c for c in core if c in dic.index and dic.loc[c,'source']=='CLIMATE']

def configs(model):
    if model=='RIDGE':return [{'alpha':a} for a in [.01,.1,1.,10.,100.]]
    if model=='ENET':return [{'alpha':a,'l1_ratio':l} for a in [.01,.1,1.] for l in [.1,.7]]
    return [
      {'n_estimators':150,'max_depth':1,'learning_rate':.03,'min_child_weight':5,'subsample':.8,'colsample_bytree':.7,'reg_alpha':1.,'reg_lambda':10.},
      {'n_estimators':300,'max_depth':1,'learning_rate':.03,'min_child_weight':10,'subsample':.8,'colsample_bytree':.7,'reg_alpha':1.,'reg_lambda':10.},
      {'n_estimators':200,'max_depth':2,'learning_rate':.03,'min_child_weight':10,'subsample':.8,'colsample_bytree':.6,'reg_alpha':1.,'reg_lambda':10.},
      {'n_estimators':150,'max_depth':3,'learning_rate':.02,'min_child_weight':10,'subsample':.8,'colsample_bytree':.6,'reg_alpha':1.,'reg_lambda':15.}]

def fit_tab(model,param,x,y):
    if model=='RIDGE':return Ridge(alpha=param['alpha']).fit(x,y)
    if model=='ENET':return ElasticNet(alpha=param['alpha'],l1_ratio=param['l1_ratio'],max_iter=30000,random_state=SEED).fit(x,y)
    return XGBRegressor(**param,objective='reg:squarederror',random_state=SEED,n_jobs=1,verbosity=0).fit(x,y)

def prep(frame,tr,va,scale):
    imp=SimpleImputer(strategy='median').fit(frame.iloc[tr]);a=imp.transform(frame.iloc[tr]);b=imp.transform(frame.iloc[va]);sc=None
    if scale:sc=StandardScaler().fit(a);a=sc.transform(a);b=sc.transform(b)
    return a,b,imp,sc

def tune_climate(C,y,tr,inner):
    vals=[]
    for a in CLIMATE_ALPHAS:
      for l in CLIMATE_L1:
        pp=[];yy=[]
        for ia,ib in inner:
            x1,x2,_,_=prep(C,tr[ia],tr[ib],True);m=ElasticNet(alpha=a,l1_ratio=l,max_iter=30000,random_state=SEED).fit(x1,y.iloc[tr[ia]]);pp.extend(m.predict(x2));yy.extend(y.iloc[tr[ib]])
        vals.append((mean_squared_error(yy,pp)**.5,{'alpha':a,'l1_ratio':l}))
    return min(vals,key=lambda q:q[0])

def climate_crossfit(C,y,tr,va,inner,param):
    cf=np.empty(len(tr))
    for ia,ib in inner:
        x1,x2,_,_=prep(C,tr[ia],tr[ib],True);m=ElasticNet(**param,max_iter=30000,random_state=SEED).fit(x1,y.iloc[tr[ia]]);cf[ib]=m.predict(x2)
    a,b,_,_=prep(C,tr,va,True);m=ElasticNet(**param,max_iter=30000,random_state=SEED).fit(a,y.iloc[tr]);return cf,m.predict(b)

def block_repr(name,blocks,curves,t,tr,va):
    if name!='FUNCTIONAL_FPCA':return blocks[name].iloc[tr],blocks[name].iloc[va],list(blocks[name].columns)
    fp=f2.FoldFPCA(t).fit(curves,tr);return pd.DataFrame(fp.transform(curves,tr),columns=fp.names),pd.DataFrame(fp.transform(curves,va),columns=fp.names),fp.names

def tune_residual(name,model,blocks,curves,t,tr,inner,resid,y):
    vals=[]
    for par in configs(model):
        pp=[];rr=[]
        for ia,ib in inner:
            atr=tr[ia];ava=tr[ib];x1,x2,_=block_repr(name,blocks,curves,t,atr,ava);a,b,_,_=prep(pd.concat([x1,x2],ignore_index=True),np.arange(len(x1)),np.arange(len(x1),len(x1)+len(x2)),model!='XGB');m=fit_tab(model,par,a,resid[ia]);pp.extend(m.predict(b));rr.extend(resid[ib])
        vals.append((mean_squared_error(rr,pp)**.5,par))
    return min(vals,key=lambda q:q[0])

def frozen_residuals(ids):
    p=pd.read_parquet(ROOT/'outputs/modeling/family_2/stage3_round2_hybrid/predictions/oof_predictions.parquet');p=p[p.pipeline.eq('CLIMATE_ENET')][[ID,'repeat','fold','y_true','y_pred']].copy();p['residual_fold']=p.y_true-p.y_pred
    a=p.groupby(ID).agg(oof_prediction_mean=('y_pred','mean'),residual_parcel_mean=('residual_fold','mean')).reset_index();p=p.merge(a,on=ID);p.to_parquet(D['residuals']/'climate_enet_oof_residuals.parquet',index=False);return p,a

def associations(ids,blocks,parcel_res,C_all):
    rows=[]
    for block,x in blocks.items():
      for c in x:
        rows.append({'feature':c,'block':block,'pearson_residual':safe_corr(x[c],parcel_res,'pearson'),'spearman_residual':safe_corr(x[c],parcel_res,'spearman'),'pearson_abs_residual':safe_corr(x[c],abs(parcel_res),'pearson'),'spearman_abs_residual':safe_corr(x[c],abs(parcel_res),'spearman'),'missing_fraction':x[c].isna().mean(),'n_unique':x[c].nunique(dropna=True)})
    a=pd.DataFrame(rows);a.to_csv(D['associations']/'feature_residual_association.csv',index=False);a[['feature','block','pearson_abs_residual','spearman_abs_residual','missing_fraction','n_unique']].to_csv(D['diagnostics']/'absolute_error_associations.csv',index=False)
    # Residualize top 10 per block against Climate on all 197 parcels, target-free.
    climate=pd.read_parquet(FEATURE_DIR/'climate_features.parquet').set_index(ID);allids=climate.index;cc=[c for c in C_all.columns];ci=SimpleImputer(strategy='median').fit_transform(climate[cc]);cz=StandardScaler().fit_transform(ci);out=[]
    for block,g in a.groupby('block'):
        top=g.assign(s=g.spearman_residual.abs()).nlargest(10,'s').feature
        source=blocks[block]
        # reload full block to include 197 where possible
        if block in BLOCK_FILES:full=pd.read_parquet(FEATURE_DIR/BLOCK_FILES[block]).set_index(ID).reindex(allids)
        else:full=source.reindex(allids)
        for c in top:
            yy=full[c];mask=yy.notna().to_numpy();ridge=Ridge(alpha=10.).fit(cz[mask],yy[mask]);e=yy-ridge.predict(cz);etrain=e.reindex(ids);out.append({'feature':c,'block':block,'ridge_alpha':10.,'pearson_residualized_X_vs_residual':safe_corr(etrain,parcel_res,'pearson'),'spearman_residualized_X_vs_residual':safe_corr(etrain,parcel_res,'spearman'),'original_spearman_residual':g.set_index('feature').loc[c,'spearman_residual']})
    pd.DataFrame(out).to_csv(D['associations']/'residualized_feature_association.csv',index=False)
    return a

def run_cv(ids,y,C,blocks,curves,t):
    splits=save_splits(ids);pos={p:i for i,p in enumerate(ids)};allhp=[]
    for k,s in splits.iterrows():
        pf=D['checkpoints']/f'pred_fold_{k:02d}.parquet';hf=D['checkpoints']/f'hp_fold_{k:02d}.csv';sf=D['checkpoints']/f'stability_fold_{k:02d}.csv'
        if pf.exists() and hf.exists() and sf.exists():allhp+=pd.read_csv(hf).to_dict('records');print(f'fold {k+1}/50 cached',flush=True);continue
        tr=np.array([pos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([pos[v] for v in json.loads(s.validation_ID_POLIGONO)]);inner=list(KFold(4,shuffle=True,random_state=SEED+k).split(tr));cscore,cpar=tune_climate(C,y,tr,inner);clim_cf,clim_va=climate_crossfit(C,y,tr,va,inner,cpar);resid=y.iloc[tr].to_numpy()-clim_cf;rows=[];hps=[];stab=[];start=time.time()
        for block in blocks:
          for model in MODELS:
            score,par=tune_residual(block,model,blocks,curves,t,tr,inner,resid,y);x1,x2,names=block_repr(block,blocks,curves,t,tr,va);frame=pd.concat([x1,x2],ignore_index=True);a,b,_,_=prep(frame,np.arange(len(x1)),np.arange(len(x1),len(frame)),model!='XGB');m=fit_tab(model,par,a,resid);rhat=m.predict(b);yp=clim_va+rhat;pipe=f'{model}_RESIDUAL_{block}'
            hps.append({'pipeline':pipe,'block':block,'model':model,'repeat':s['repeat'],'fold':s['fold'],'climate_inner_RMSE':cscore,'climate_params':json.dumps(cpar),'residual_inner_RMSE':score,'best_params':json.dumps(par,sort_keys=True),'n_features':len(names)})
            rows += [{ID:pid,'repeat':s['repeat'],'fold':s['fold'],'y_true':yt,'climate_pred':cp,'true_residual':yt-cp,'predicted_residual':rh,'corrected_pred':ypi,'pipeline':pipe,'block':block,'model':model} for pid,yt,cp,rh,ypi in zip(ids.iloc[va],y.iloc[va],clim_va,rhat,yp)]
            vals=np.abs(m.coef_) if model in ['RIDGE','ENET'] else m.feature_importances_
            stab += [{'pipeline':pipe,'block':block,'model':model,'repeat':s['repeat'],'fold':s['fold'],'feature':nm,'value':v,'selected':bool(v!=0)} for nm,v in zip(names,vals)]
        pd.DataFrame(rows).to_parquet(pf,index=False);pd.DataFrame(hps).to_csv(hf,index=False);pd.DataFrame(stab).to_csv(sf,index=False);allhp+=hps;print(f'fold {k+1}/50 complete in {time.time()-start:.1f}s',flush=True)
    pd.DataFrame(allhp).to_csv(D['block_models']/'selected_hyperparameters.csv',index=False)

def consolidate(ids,y,blocks,assoc):
    pred=pd.concat([pd.read_parquet(p) for p in sorted(D['checkpoints'].glob('pred_fold_*.parquet'))],ignore_index=True);fold=[]
    for (p,r,f),g in pred.groupby(['pipeline','repeat','fold']):
        base=metric(g.y_true,g.climate_pred);cor=metric(g.y_true,g.corrected_pred);fold.append({'pipeline':p,'block':g.block.iloc[0],'model':g.model.iloc[0],'repeat':r,'fold':f,'baseline_RMSE':base['RMSE'],'corrected_RMSE':cor['RMSE'],'delta_RMSE':cor['RMSE']-base['RMSE'],'corrected_MAE':cor['MAE'],'corrected_R2':cor['R2'],'residual_R2':r2_score(g.true_residual,g.predicted_residual),'residual_correlation':safe_corr(g.true_residual,g.predicted_residual,'pearson')})
    fm=pd.DataFrame(fold);fm.to_csv(D['block_models']/'fold_metrics.csv',index=False)
    sm=fm.groupby(['pipeline','block','model']).agg(corrected_RMSE=('corrected_RMSE','mean'),baseline_RMSE=('baseline_RMSE','mean'),mean_delta_RMSE=('delta_RMSE','mean'),median_delta_RMSE=('delta_RMSE','median'),std_delta_RMSE=('delta_RMSE','std'),fold_win_rate=('delta_RMSE',lambda x:(x<0).mean()),residual_R2_mean=('residual_R2','mean'),residual_correlation_mean=('residual_correlation','mean')).reset_index();sm.to_csv(D['block_models']/'block_residual_metrics.csv',index=False)
    pr=[]
    for p,g in fm.groupby('pipeline'):
        pr.append({'record_type':'overall','repeat':np.nan,'pipeline':p,'block':g.block.iloc[0],'model':g.model.iloc[0],'mean_delta_RMSE':g.delta_RMSE.mean(),'median_delta_RMSE':g.delta_RMSE.median(),'q25':g.delta_RMSE.quantile(.25),'q75':g.delta_RMSE.quantile(.75),'fold_win_rate':(g.delta_RMSE<0).mean()})
        for rep,h in g.groupby('repeat'):pr.append({'record_type':'repeat','repeat':rep,'pipeline':p,'block':g.block.iloc[0],'model':g.model.iloc[0],'mean_delta_RMSE':h.delta_RMSE.mean(),'median_delta_RMSE':h.delta_RMSE.median(),'q25':h.delta_RMSE.quantile(.25),'q75':h.delta_RMSE.quantile(.75),'fold_win_rate':(h.delta_RMSE<0).mean()})
    pd.DataFrame(pr).to_csv(D['block_models']/'paired_delta_rmse.csv',index=False)
    byp=pred.groupby(['pipeline',ID]).agg(y_true=('y_true','first'),climate_pred=('climate_pred','mean'),corrected_pred=('corrected_pred','mean'),predicted_residual=('predicted_residual','mean'),true_residual=('true_residual','mean'),block=('block','first'),model=('model','first')).reset_index();byp['climate_abs_error']=abs(byp.y_true-byp.climate_pred);byp['corrected_abs_error']=abs(byp.y_true-byp.corrected_pred);byp['improvement']=byp.climate_abs_error-byp.corrected_abs_error
    # Feature stability and top features.
    fs=pd.concat([pd.read_csv(p) for p in sorted(D['checkpoints'].glob('stability_fold_*.csv'))],ignore_index=True);fss=fs.groupby(['pipeline','block','model','feature']).agg(mean_importance=('value','mean'),selection_frequency=('selected','mean')).reset_index();tops=[]
    for block,g in assoc.groupby('block'):
        for met in ['spearman_residual','spearman_abs_residual']:
            for rank,(_,r) in enumerate(g.assign(v=g[met].abs()).nlargest(10,'v').iterrows(),1):tops.append({'block':block,'ranking_metric':met,'rank':rank,'feature':r.feature,'score':r[met]})
        for model in ['ENET','XGB']:
            q=fss[(fss.block==block)&(fss.model==model)].sort_values(['selection_frequency','mean_importance'],ascending=False).head(10)
            for rank,(_,r) in enumerate(q.iterrows(),1):tops.append({'block':block,'ranking_metric':f'{model}_stability_importance','rank':rank,'feature':r.feature,'score':r.selection_frequency,'mean_importance':r.mean_importance})
    pd.DataFrame(tops).to_csv(D['associations']/'top_features_by_block.csv',index=False)
    density=[]
    for block,g in assoc.groupby('block'):
        best=sm[sm.block.eq(block)].sort_values('corrected_RMSE').iloc[0];enet_fs=fs[(fs.block==block)&(fs.model=='ENET')];enet_selected_mean=enet_fs.groupby(['repeat','fold']).selected.sum().mean() if len(enet_fs) else np.nan;density.append({'block':block,'n_features':len(g),'best_abs_spearman_residual':g.spearman_residual.abs().max(),'median_top10_abs_spearman_residual':g.spearman_residual.abs().nlargest(10).median(),'best_abs_spearman_abs_residual':g.spearman_abs_residual.abs().max(),'best_pipeline':best.pipeline,'best_corrected_RMSE':best.corrected_RMSE,'best_delta_RMSE':best.mean_delta_RMSE,'best_fold_win_rate':best.fold_win_rate,'best_residual_correlation':best.residual_correlation_mean,'enet_selected_mean':enet_selected_mean})
    den=pd.DataFrame(density).sort_values('best_delta_RMSE');den.to_csv(D['diagnostics']/'block_signal_density.csv',index=False)
    # Difficult block geometry + correction from best pipeline per block.
    hard=pd.read_csv(ROOT/'outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv');hard=hard[hard.difficult_all_3][[ID,'support_class']];dr=[]
    for block,x in blocks.items():
        xi=SimpleImputer(strategy='median').fit_transform(x);z=StandardScaler().fit_transform(xi);dist=squareform(pdist(z));np.fill_diagonal(dist,np.inf);kn=np.sort(dist,axis=1)[:,:5].mean(1);ext=np.max(abs(z),axis=1);best=den[den.block.eq(block)].best_pipeline.iloc[0];q=byp[byp.pipeline.eq(best)].set_index(ID)
        for pid in hard[ID]:
            i=list(ids).index(pid);dr.append({ID:pid,'support_class':hard.set_index(ID).loc[pid,'support_class'],'block':block,'best_pipeline':best,'block_extremeness_percentile':(ext<=ext[i]).mean(),'block_5nn_distance_percentile':(kn<=kn[i]).mean(),'baseline_absolute_error':q.loc[pid,'climate_abs_error'],'corrected_absolute_error':q.loc[pid,'corrected_abs_error'],'improvement':q.loc[pid,'improvement']})
    pd.DataFrame(dr).to_csv(D['diagnostics']/'difficult_parcels_residual_signal.csv',index=False)
    return pred,fm,sm,den,byp

def augmentation(ids,y,C,blocks,curves,t,den):
    candidates=den[(den.best_delta_RMSE<0)|(den.best_fold_win_rate>.5)].block.tolist();rows=[]
    if not candidates:
        pd.DataFrame(columns=['block','matched_model','direct_RMSE_mean','residual_corrected_RMSE_mean','climate_RMSE_mean','direct_delta_RMSE','residual_delta_RMSE','note']).to_csv(D['augmentation']/'direct_augmentation_comparison.csv',index=False);return
    splits=save_splits(ids);pos={p:i for i,p in enumerate(ids)}
    for block in candidates:
      model=den[den.block.eq(block)].best_pipeline.iloc[0].split('_RESIDUAL_')[0]
      vals=[]
      for k,s in splits.iterrows():
        tr=np.array([pos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([pos[v] for v in json.loads(s.validation_ID_POLIGONO)]);inner=list(KFold(4,shuffle=True,random_state=SEED+k).split(tr));xtr,xva,_=block_repr(block,blocks,curves,t,tr,va)
        # Concatenate climate and block; tune same model family directly on yield.
        frame=pd.concat([pd.concat([C.iloc[tr].reset_index(drop=True),xtr.reset_index(drop=True)],axis=1),pd.concat([C.iloc[va].reset_index(drop=True),xva.reset_index(drop=True)],axis=1)],ignore_index=True);best=[]
        for par in configs(model):
            pp=[];yy=[]
            for ia,ib in inner:
                # Functional inner representation must be refit.
                bi,bv,_=block_repr(block,blocks,curves,t,tr[ia],tr[ib]);fa=pd.concat([C.iloc[tr[ia]].reset_index(drop=True),bi.reset_index(drop=True)],axis=1);fb=pd.concat([C.iloc[tr[ib]].reset_index(drop=True),bv.reset_index(drop=True)],axis=1);a,b,_,_=prep(pd.concat([fa,fb],ignore_index=True),np.arange(len(fa)),np.arange(len(fa),len(fa)+len(fb)),model!='XGB');m=fit_tab(model,par,a,y.iloc[tr[ia]]);pp.extend(m.predict(b));yy.extend(y.iloc[tr[ib]])
            best.append((mean_squared_error(yy,pp)**.5,par))
        _,par=min(best,key=lambda q:q[0]);a,b,_,_=prep(frame,np.arange(len(tr)),np.arange(len(tr),len(tr)+len(va)),model!='XGB');m=fit_tab(model,par,a,y.iloc[tr]);yp=m.predict(b);vals.append(mean_squared_error(y.iloc[va],yp)**.5)
      q=den[den.block.eq(block)].iloc[0];rows.append({'block':block,'matched_model':model,'direct_RMSE_mean':np.mean(vals),'residual_corrected_RMSE_mean':q.best_corrected_RMSE,'climate_RMSE_mean':q.best_corrected_RMSE-q.best_delta_RMSE,'direct_delta_RMSE':np.mean(vals)-(q.best_corrected_RMSE-q.best_delta_RMSE),'residual_delta_RMSE':q.best_delta_RMSE,'note':'direct augmentation executed because preliminary residual signal criterion met'})
    pd.DataFrame(rows).to_csv(D['augmentation']/'direct_augmentation_comparison.csv',index=False)

def plots(assoc,sm,den):
    q=assoc.groupby('block').spearman_residual.apply(lambda x:x.abs().max()).reset_index(name='max_abs_spearman');plt.figure(figsize=(9,4));sns.barplot(data=q,x='block',y='max_abs_spearman');plt.xticks(rotation=30);plt.tight_layout();plt.savefig(D['figures']/'residual_association_by_block.png',dpi=180);plt.close()
    best=sm.sort_values('mean_delta_RMSE').groupby('block').head(1);plt.figure(figsize=(9,4));sns.barplot(data=best,x='block',y='mean_delta_RMSE');plt.axhline(0,color='black');plt.xticks(rotation=30);plt.tight_layout();plt.savefig(D['figures']/'residual_model_delta_rmse.png',dpi=180);plt.close()
    plt.figure(figsize=(9,4));sns.barplot(data=best,x='block',y='residual_correlation_mean');plt.axhline(0,color='black');plt.xticks(rotation=30);plt.tight_layout();plt.savefig(D['figures']/'residual_prediction_correlation.png',dpi=180);plt.close()
    top=assoc.assign(v=assoc.spearman_residual.abs()).sort_values('v').groupby('block').tail(3);plt.figure(figsize=(9,7));sns.barplot(data=top,y='feature',x='spearman_residual',hue='block',dodge=False);plt.tight_layout();plt.savefig(D['figures']/'top_feature_residual_correlations.png',dpi=180);plt.close()

def report(assoc,sm,den):
    best=den.iloc[0];aug=pd.read_csv(D['augmentation']/'direct_augmentation_comparison.csv');resid=pd.read_csv(D['associations']/'residualized_feature_association.csv');hard=pd.read_csv(D['diagnostics']/'difficult_parcels_residual_signal.csv');desc=assoc.groupby('block').spearman_residual.apply(lambda x:x.abs().max()).sort_values(ascending=False);top=assoc.assign(v=assoc.spearman_residual.abs()).nlargest(20,'v')[['block','feature','spearman_residual','spearman_abs_residual']].round(3).to_dict('records')
    def blockline(b):
        q=den[den.block.eq(b)].iloc[0];return f"{q.best_pipeline}: Δ={q.best_delta_RMSE:+.4f}, wins={q.best_fold_win_rate:.0%}, residual corr={q.best_residual_correlation:+.3f}"
    strong=den[(den.best_delta_RMSE<0)&(den.best_fold_win_rate>.6)];weak=den[(den.best_delta_RMSE<0)|(den.best_fold_win_rate>.5)];promote=strong.head(2).block.tolist()
    hard_summary=hard.groupby('block').improvement.agg(mean_improvement='mean',proportion_improved=lambda x:(x>0).mean()).round(3).to_dict('index')
    atypical_summary=hard[hard.support_class.eq('y-outlier given similar X')].groupby('block').improvement.agg(mean_improvement='mean',proportion_improved=lambda x:(x>0).mean()).round(3).to_dict('index')
    direct_better=aug.loc[aug.direct_delta_RMSE<0,'block'].tolist() if len(aug) else []
    txt=f"""# Residual Signal Audit — Stage RS1

## Controles

Residual definido como `y - yhat_CLIMATE_ENET`. Exploración usa el promedio de 10 OOF; predicción usa 50 outer folds. En cada outer fold, Climate ENET genera residuales cross-fitted del outer-train y predicción de outer-validation; el modelo de bloque se ajusta sólo con residuales que excluyen esa observación del fit climático. No se usaron residuales in-sample, clustering, expertos ni predicción final.

## Respuestas

1. **Mayor asociación descriptiva:** `{desc.index[0]}` con máximo |Spearman|={desc.iloc[0]:.3f}.
2. **Mejor predicción residual OOF:** `{best.block}` mediante `{best.best_pipeline}`.
3. **¿Reduce RMSE Climate?** {'Sí' if best.best_delta_RMSE<0 else 'No'}.
4. **Mejor delta:** {best.best_delta_RMSE:+.4f}; corrected RMSE={best.best_corrected_RMSE:.4f}.
5. **Folds mejorados:** {best.best_fold_win_rate:.0%}.
6. **Estabilidad por repetición:** en `paired_delta_rmse.csv`; no se interpreta repeated CV como 50 observaciones independientes.
7. **Satellite incremental:** Sentinel {blockline('SENTINEL_CORE')}; Planet {blockline('PLANET')}; Landsat {blockline('LANDSAT')}.
8. **Mejor sensor:** `{den[den.block.isin(['SENTINEL_CORE','PLANET','LANDSAT'])].iloc[0].block}` por delta OOF.
9. **Topography Basic:** {blockline('TOPO_BASIC')}.
10. **Topography Advanced:** {blockline('TOPO_ADVANCED')}. Variables hidrológicas son proxies a ~120 m, no humedad observada.
11. **History:** {blockline('HISTORY')}.
12. **Anomaly:** {blockline('ANOMALY')}.
13. **Functional FPCA:** {blockline('FUNCTIONAL_FPCA')}; diagnóstico secundario sin retuning de smoothing.
14. **Features asociadas:** {top}.
15. **Tras residualizar X respecto a Climate:** top |Spearman|={resid.spearman_residualized_X_vs_residual.abs().max():.3f}; tabla completa en `residualized_feature_association.csv`.
16. **Error firmado:** ranking descriptivo {desc.round(3).to_dict()}.
17. **|error|:** {assoc.groupby('block').spearman_abs_residual.apply(lambda x:x.abs().max()).sort_values(ascending=False).round(3).to_dict()}.
18. **28 difíciles:** por mejor pipeline de bloque en `difficult_parcels_residual_signal.csv`; mejoras agregadas: {hard_summary}.
19. **9 y-atypical:** {atypical_summary}.
20. **Augmentación directa:** sólo mejora Climate para {direct_better}; la tabla completa es {aug.round(4).to_dict('records') if len(aug) else 'ningún bloque alcanzó el umbral preliminar para ejecutarla'}.
21. **Clustering posterior:** no se ejecutó. Si se abre una etapa posterior, limitarla a {promote}; History tiene la evidencia más estable y Planet queda como opción secundaria.
22. **Promoción máxima:** promover {promote}. Candidatos fuertes por regla RS1={strong.block.tolist()}; candidatos débiles={weak.block.tolist()}.

## Ranking separado

Valor predictivo incremental: {den[['block','best_delta_RMSE','best_fold_win_rate','best_residual_correlation']].round(4).to_dict('records')}.

Asociación descriptiva no equivale a valor incremental. Un bloque con correlaciones altas pero ΔRMSE no negativo queda sólo como explicación descriptiva del error.
"""
    (D['report']/'residual_signal_audit_report.md').write_text(txt,encoding='utf-8')

def main():
    ids,X,y=load_xy();ids=ids.reset_index(drop=True);y=y.reset_index(drop=True);cc=climate_cols(X);C=X[cc].reset_index(drop=True);blocks=load_blocks(ids);_,_,t,curves=f2.load_data();foldres,parcel=frozen_residuals(ids);pr=parcel.set_index(ID).reindex(ids).residual_parcel_mean.reset_index(drop=True);assoc=associations(ids,blocks,pr,C);run_cv(ids,y,C,blocks,curves,t);pred,fm,sm,den,byp=consolidate(ids,y,blocks,assoc);augmentation(ids,y,C,blocks,curves,t,den);plots(assoc,sm,den);report(assoc,sm,den);print(f"RS1 complete: best block={den.iloc[0].block}, delta={den.iloc[0].best_delta_RMSE:+.4f}",flush=True)

if __name__=='__main__':main()
