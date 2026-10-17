"""Inventory all error groups, then fit two fixed train-only diagnostic classifiers."""
from pathlib import Path
import sys,json,hashlib,warnings,time
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.difficult_quartile import OUT,CALIBRATION,effect,conditional_effect,bh,labels_for_errors,DiagnosticClassifier


def associations(t,x,meta,categories):
    contrasts={
        'hard_vs_remaining':(t.hard_quartile.to_numpy(),~t.hard_quartile.to_numpy()),
        'hard_over_vs_hard_under':(t.error_group.eq('hard_over').to_numpy(),t.error_group.eq('hard_under').to_numpy()),
        'hard_over_vs_remaining':(t.error_group.eq('hard_over').to_numpy(),t.error_group.eq('remaining').to_numpy()),
        'hard_under_vs_remaining':(t.error_group.eq('hard_under').to_numpy(),t.error_group.eq('remaining').to_numpy()),
        'all_over_vs_under':(t.direction.eq('over').to_numpy(),t.direction.eq('under').to_numpy()),
        'low_yield_vs_other':(t.low_yield_quartile.to_numpy(),~t.low_yield_quartile.to_numpy())}
    records=[];catrows=[];values=x.to_numpy(float)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for name,(a,b) in contrasts.items():
            delta,p,na,nb=effect(values[a],values[b]);dm,em,nm=conditional_effect(values,a,b,t.Municipio.to_numpy());dp,ep,npf=conditional_effect(values,a,b,t.climate_profile.to_numpy())
            f=pd.DataFrame(dict(feature=x.columns,contrast=name,n_a=na,n_b=nb,median_a=np.nanmedian(values[a],axis=0),median_b=np.nanmedian(values[b],axis=0),cliffs_delta=delta,p_nominal=p,q_BH=bh(p),municipal_pair_weighted_delta=dm,municipal_equal_weight_delta=em,n_supported_municipalities=nm,profile_pair_weighted_delta=dp,profile_equal_weight_delta=ep,n_supported_profiles=npf))
            f['municipal_sign_consistent']=np.sign(f.cliffs_delta)==np.sign(f.municipal_equal_weight_delta);records.append(f)
            for column in categories:
                s=categories[column].fillna('<missing>').astype(str)
                for level in s.unique():
                    use=s.eq(level).to_numpy();catrows.append(dict(feature=column,contrast=name,level=level,n_a=int(a.sum()),n_b=int(b.sum()),count_a=int((a&use).sum()),count_b=int((b&use).sum()),fraction_a=float(use[a].mean()),fraction_b=float(use[b].mean()),fraction_difference=float(use[a].mean()-use[b].mean())))
    f=pd.concat(records,ignore_index=True).merge(meta,on='feature',validate='many_to_one');f.to_csv(OUT/'tables/numeric_group_differences.csv',index=False);pd.DataFrame(catrows).merge(meta,on='feature',validate='many_to_one').to_csv(OUT/'tables/categorical_group_differences.csv',index=False)
    # Two rankings: pooled and within municipality. Correlated variants remain marked, never counted as independent discoveries.
    rank=f[(~f.quality)&(~f.geographic_identifier)&(f.n_a>=8)&(f.n_b>=8)].copy();rank['abs_delta']=abs(rank.cliffs_delta);rank['abs_conditional_delta']=abs(rank.municipal_equal_weight_delta)
    rank.sort_values('abs_delta',ascending=False).groupby('contrast',sort=False).head(40).to_csv(OUT/'tables/top_pooled_differences.csv',index=False)
    conditional=rank[(rank.n_supported_municipalities>=2)&rank.municipal_sign_consistent]
    conditional.sort_values('abs_conditional_delta',ascending=False).groupby('contrast',sort=False).head(40).to_csv(OUT/'tables/top_conditional_differences.csv',index=False)
    diverse=[]
    for (contrast,family),g in conditional.groupby(['contrast','family']):
        h=g.sort_values('abs_conditional_delta',ascending=False).head(3);diverse.append(h)
    pd.concat(diverse,ignore_index=True).to_csv(OUT/'tables/representative_differences_by_family.csv',index=False)


def classify(cfg,t,x):
    folds=joblib.load(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/frozen65_splits.joblib');source=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');source_ids=source.ID_POLIGONO.tolist();y=source.RENDIMIENTO_T_HA.to_numpy();x=x.loc[source_ids]
    refs=pd.read_parquet(CALIBRATION/'tables/predictions.parquet');refs=refs[refs.experiment=='J7_BOTH'];rows=[];selected=[];checks=[];logs=[]
    with threadpool_limits(limits=1):
        for fi,(protocol,repeat,fold,tr,va,inner) in enumerate(folds):
            tr=np.asarray(tr);va=np.asarray(va);assert not set(tr)&set(va)
            ck=joblib.load(CALIBRATION/'checkpoints'/f'{fi:02d}.joblib');np.testing.assert_array_equal(ck['calibration']['train_positions'],tr)
            assert all(not set(rec['train'])&(set(rec['held'])|set(va)) for rec in ck['ledger'])
            train_error=ck['calibration']['base_oof']-y[tr];threshold=float(np.quantile(abs(train_error),.75));train_labels=labels_for_errors(train_error,threshold)
            ref=refs[(refs.protocol==protocol)&(refs['repeat']==repeat)&(refs.fold==fold)].set_index('ID_POLIGONO').loc[source.iloc[va].ID_POLIGONO];test_error=ref.y_pred.to_numpy()-y[va];test_labels=labels_for_errors(test_error,threshold);prior=np.bincount(train_labels,minlength=3)/len(train_labels);models={}
            for name,columns in cfg['classifiers'].items():
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always');model=DiagnosticClassifier(6).fit(x.iloc[tr][columns].to_numpy(float),train_labels);p=model.predict_proba(x.iloc[va][columns].to_numpy(float))
                logs.extend(dict(execution_index=fi,classifier=name,category=w.category.__name__,message=str(w.message)) for w in caught);models[name]=dict(model=model,columns=columns)
                for j in model.selected:
                    coefficients=np.zeros(3)
                    if model.model is not None:coefficients[model.model.classes_]=model.model.coef_[:,list(model.selected).index(j)] if len(model.model.classes_)==3 else np.nan
                    selected.append(dict(execution_index=fi,protocol=protocol,repeat=repeat,fold=fold,classifier=name,feature=columns[j],coef_remaining=coefficients[0],coef_hard_over=coefficients[1],coef_hard_under=coefficients[2]))
                for i,pos in enumerate(va):rows.append(dict(execution_index=fi,protocol=protocol,repeat=repeat,fold=fold,classifier=name,ID_POLIGONO=source.iloc[pos].ID_POLIGONO,actual=int(test_labels[i]),p_remaining=p[i,0],p_over=p[i,1],p_under=p[i,2],training_cutoff=threshold,outer_error=test_error[i]))
            for i,pos in enumerate(va):rows.append(dict(execution_index=fi,protocol=protocol,repeat=repeat,fold=fold,classifier='PRIOR',ID_POLIGONO=source.iloc[pos].ID_POLIGONO,actual=int(test_labels[i]),p_remaining=prior[0],p_over=prior[1],p_under=prior[2],training_cutoff=threshold,outer_error=test_error[i]))
            joblib.dump(dict(models=models,train_positions=tr,validation_positions=va,train_labels=train_labels,training_cutoff=threshold),OUT/'models'/f'{fi:02d}.joblib',compress=3)
            checks.append(dict(execution_index=fi,protocol=protocol,repeat=repeat,fold=fold,n_train=len(tr),n_validation=len(va),training_cutoff=threshold,n_train_hard=int((train_labels!=0).sum()),n_test_hard=int((test_labels!=0).sum()),train_ids=source.iloc[tr].ID_POLIGONO.tolist(),validation_ids=source.iloc[va].ID_POLIGONO.tolist()))
            if fi%10==0:print(f'Classifiers {fi+1}/65 {protocol}',flush=True)
    pd.DataFrame(rows).to_parquet(OUT/'tables/classification_OOF.parquet',index=False);pd.DataFrame(selected).to_csv(OUT/'tables/classifier_selected_features.csv',index=False);pd.DataFrame(logs,columns=['execution_index','classifier','category','message']).to_csv(OUT/'audit/classifier_warnings.csv',index=False);(OUT/'audit/classification_membership.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')


def main():
    if (OUT/'analysis_complete.json').exists():raise FileExistsError('Preserve completed quartile analysis')
    start=time.perf_counter();cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());t=pd.read_csv(OUT/'tables/parcel_groups.csv');x=pd.read_parquet(OUT/'cache/numeric_X138.parquet');c=pd.read_parquet(OUT/'cache/categorical_X138.parquet');meta=pd.read_csv(OUT/'tables/feature_catalog.csv')
    assert x.index.tolist()==t.ID_POLIGONO.tolist();associations(t,x,meta,c);print('Descriptive associations complete.',flush=True);classify(cfg,t,x)
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'analysis_complete.json').write_text(json.dumps(dict(status='complete',seconds=time.perf_counter()-start,numeric_vectors=len(x.columns),new_diagnostic_classifiers=130,no_PRED=True,no_final138_fit=True,protected_sources_unchanged=True),indent=2),encoding='utf-8')


if __name__=='__main__':main()
