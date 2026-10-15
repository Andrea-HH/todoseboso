"""Section J: small prespecified additive models using immutable H/I products."""
from pathlib import Path
import json,warnings,itertools,platform
import numpy as np
import pandas as pd
import joblib
from sklearn.base import BaseEstimator,TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import GridSearchCV
from sklearn.exceptions import ConvergenceWarning
from .climate_signal_features import ROOT,ID,MASTER,TARGET,RAIN,sha,supervised_data
from .climate_signal_modeling import ALPHAS,L1
from .climate_signal_reporting import summarize
from .rainfall_modeling import metrics
from .rainfall_pcr import load_frozen_splits
from .i_geographic_edaphological import DATA as IDATA,OUT as IOUT,protected as i_protected,markdown_table

NAME='j_incremental_geographic_edaphological_yield'
BASE='J0_RAIN'
TOPO=['altitude_m','slope_degrees']
H=ROOT/'outputs/modeling/family_1/h_joint_climate_signal/v1'

class FoldConstantDrop(BaseEstimator,TransformerMixin):
    """Remove negligible numerical variation only within fitted training data."""
    def fit(self,X,y=None):
        self.support_=np.var(np.asarray(X,float),axis=0)>1e-20
        self.all_constant_=not self.support_.any()
        if self.all_constant_:self.support_[0]=True  # intercept-only fit remains valid
        return self
    def transform(self,X):return np.asarray(X,float)[:,self.support_]
    def get_feature_names_out(self,input_features=None):return np.asarray(input_features)[self.support_]

class WeightedTop3(BaseEstimator,TransformerMixin):
    """Fold-learned nominal units, weighted by shares; no ordinal rank effects."""
    def fit(self,X,y=None):
        self.units_=sorted({str(v) for k in [1,2,3] for v in X[f'soil_top{k}_unit'].dropna()})
        self.lookup_={u:i for i,u in enumerate(self.units_)}
        return self
    def transform(self,X):
        out=np.zeros((len(X),len(self.units_)+2))
        for k in [1,2,3]:
            for row,(u,p) in enumerate(zip(X[f'soil_top{k}_unit'],X[f'soil_top{k}_share'].fillna(0))):
                if pd.notna(u):out[row,self.lookup_.get(str(u),len(self.units_))]+=float(p)
        out[:,-1]=X.soil_remaining_share.to_numpy(float)
        return np.c_[X[RAIN].to_numpy(float),out]
    def get_feature_names_out(self,input_features=None):return np.array(RAIN+['top3_map_share__'+u for u in self.units_]+['top3_unknown_unit_share','soil_remaining_share'])

def locations(run_id='v1'):
    return ROOT/'outputs/modeling/family_1'/NAME/run_id,ROOT/'data/processed/family_1'/NAME/run_id

def load():
    rain=pd.read_parquet(ROOT/'data/processed/family_1/g_temperature_signal/v1/climate_candidates_197.parquet')[[ID]+RAIN]
    diagnostic=pd.read_parquet(IDATA/'integrated_diagnostic_197.parquet')
    metadata=[ID,'CONJUNTO','climate_profile','Estado','Municipio','longitude','latitude','soil_assignment_reserve','soil_share_key_not_found_in_E1402_text','soil_boundary_buffer_50m_share','soil_boundary_buffer_125m_share','soil_boundary_buffer_250m_share']
    groups=[c for c in diagnostic if c.startswith('soil_map_share_mentions_group_')]
    units=[c for c in diagnostic if c.startswith('soil_unit_share__')]
    if len(groups)!=10 or len(units)!=22:raise ValueError('I soil schema changed')
    d=rain.merge(diagnostic[metadata+TOPO+groups+units],on=ID,validate='one_to_one')
    top=pd.read_parquet(IDATA/'soil_topn_per_parcel_3.parquet')
    d=d.merge(top,on=ID,validate='one_to_one').sort_values(ID).reset_index(drop=True)
    if len(d)!=197 or d.climate_profile.nunique()!=53 or not d[ID].is_unique or not np.isfinite(d[RAIN+TOPO+groups+units]).all().all():raise ValueError('Incomplete J inputs')
    train=supervised_data(d,pd.read_csv(MASTER))
    if len(train)!=138:raise ValueError('Expected 138 supervised parcels')
    specs={BASE:RAIN,'J1_RAIN_SLOPE':RAIN+['slope_degrees'],'J2_RAIN_TOPO':RAIN+TOPO,'J3_RAIN_SOIL_GROUP':RAIN+groups,'J4_RAIN_TOPO_SOIL':RAIN+TOPO+groups,'J5_RAIN_SOIL_FULL':RAIN+units,'J6_RAIN_SOIL_TOP3':RAIN+[f'soil_top{k}_{v}' for k in [1,2,3] for v in ['unit','share']]+['soil_remaining_share']}
    return d,train,specs

def pipeline(name):
    steps=[('encoding',WeightedTop3())] if name=='J6_RAIN_SOIL_TOP3' else []
    return Pipeline(steps+[('imputer',SimpleImputer(strategy='median',keep_empty_features=True)),('constants',FoldConstantDrop()),('scaler',StandardScaler()),('model',ElasticNet(max_iter=20000,random_state=2026))])

def snapshot():
    q=i_protected()
    q={p:v for p,v in q.items() if NAME not in p and 'j_incremental_yield' not in p and not Path(p).name.startswith('j_')}
    for folder in [IDATA,IOUT]:
        q.update({str(p.relative_to(ROOT)):sha(p) for p in folder.rglob('*') if p.is_file()})
    for file in ['src/family_1/i_geographic_edaphological.py','documentation/i_geographic_edaphological_exploration.md']:
        q[file]=sha(ROOT/file)
    return q

def audit(run_id='v1'):
    out,proc=locations(run_id)
    for p in [out,proc]+[out/x for x in ['tables','splits','models','checkpoints','figures','report']]:p.mkdir(parents=True,exist_ok=True)
    if (out/'manifest.json').exists():raise FileExistsError('Completed run is immutable; use a new run-id')
    d,train,specs=load();splits,table,assignments=load_frozen_splits(train)
    for protocol,rep,fold,tr,va,inner in splits:
        if protocol=='climate_profile':
            values=train.climate_profile.to_numpy()
            if set(values[tr])&set(values[va]):raise ValueError('Exact I profile leaks across outer folds')
            for a,b in inner:
                if set(values[tr[a]])&set(values[tr[b]]):raise ValueError('Exact I profile leaks across inner folds')
    htable=pd.read_csv(H/'splits/outer_and_inner_splits.csv')
    if not table.equals(htable[table.columns]):raise ValueError('H frozen splits differ')
    table.to_csv(out/'splits/outer_and_inner_splits.csv',index=False);assignments.to_csv(out/'splits/group_memberships.csv')
    config=dict(seed=2026,alpha_grid=ALPHAS,l1_ratio_grid=L1,max_iter=20000,n_outer=65,specs=specs,n_train=138,n_prediction=59,hidden_y_used=False,
      primary_aggregation='metrics on complete 138-parcel OOF repetition, then mean across repetitions',
      preprocessing='median imputation, constant drop variance<=1e-20, StandardScaler and Top3 vocabulary fitted inside each inner/outer training fold',
      rare_policy='retain prespecified schema; no full-sample frequency filtering; absent/constant training columns dropped; unknown Top3 category shares go to explicit unknown-share field',
      composition='Full unit shares sum to 1 with intercept: structural collinearity; ElasticNet includes strictly positive L2 penalty, no causal coefficient interpretation. Group mention coverages are not a closed physical composition.',
      top3='N=3 fixed from I, weighted nominal encoding shared across ranks; fold-learned vocabulary; explicit remainder and unknown shares',
      decision=dict(noninferiority_rmse_margin=.01,rule='random improvement stable across repeats; no >0.01 deterioration in grouped RMSE; inspect extreme bias, same-model within-profile differentiation, uncertainty and category support; exploratory, no independent-fold confidence claim'),
      uncertainty='All validation observations retained; evaluate 50/125/250m boundary scenarios and source key discrepancy strata; no probabilistic precision claim',
      yield_bins='fixed descriptive bins low<3, mid 3-5, high>5 t/ha; no tuning',baseline_gate='J0 predicted values and complete-OOF metrics must match cached H1 at absolute 1e-8 tolerance before J1-J6')
    file=out/'configuration.json'
    if file.exists() and json.loads(file.read_text(encoding='utf-8'))!=config:raise ValueError('Checkpoint configuration changed')
    file.write_text(json.dumps(config,indent=2),encoding='utf-8')
    d.to_parquet(proc/'j_features_197_target_free.parquet',index=False)
    rows=[dict(experiment=k,n_raw_columns=len(v),columns=' | '.join(v)) for k,v in specs.items()]
    pd.DataFrame(rows).to_csv(out/'tables/00_feature_audit.csv',index=False)
    pd.DataFrame([dict(feature=c,units='mm/month' if c in RAIN else 'metres' if c=='altitude_m' else 'degrees' if c=='slope_degrees' else 'nominal cartographic key' if c.endswith('_unit') else 'cartographic coverage fraction',meaning='coverage of unit mentioning group, NOT physical fraction of group' if 'mentions_group' in c else 'prespecified existing H/I feature',fit_scope='deterministic parcel features; learned preprocessing inside training folds') for c in sorted(set(sum(specs.values(),[])))]).to_csv(out/'tables/01_variable_dictionary.csv',index=False)
    text='# Sección J — Auditoría previa y diseño congelado\n\n'+markdown_table(pd.DataFrame(rows))+ '\n\n138 TRAIN y 59 PRED; unión uno a uno por ID. Se reutilizan I y H sin extracción geográfica. Hay 50 folds aleatorios y cinco por cada protocolo agrupado; todos los inner folds se reutilizan por ID. J0 debe reproducir H1 antes de otros ajustes. Las categorías raras permanecen; sus columnas ausentes/constantes se eliminan dentro de entrenamiento. Top3 usa unidades nominales ponderadas por cobertura y conserva remanente/unknown.\n\nCriterio exploratorio fijado antes de entrenar: mejora aleatoria consistente, deterioro máximo agrupado de 0.01t/ha, diagnóstico de extremos, variación intraperfil de un mismo modelo, incertidumbre y soporte. No declarar ganador por RMSE aleatorio.\n'
    (out/'report/pretraining_audit.md').write_text(text,encoding='utf-8');(ROOT/'documentation/j_pretraining_audit.md').write_text(text,encoding='utf-8')
    protected_file=out/'protected_inputs.json'
    if not protected_file.exists():protected_file.write_text(json.dumps(snapshot(),indent=2),encoding='utf-8')
    print('J audit complete:',[(k,len(v)) for k,v in specs.items()],flush=True)
    return out,proc,d,train,specs,splits

def run(run_id='v1'):
    out,proc,d,train,specs,splits=audit(run_id);predictions=[];registry=[];coeff=[];tuning=[]
    for name,cols in specs.items():
        rows=[];print('START',name,flush=True)
        for idx,(protocol,rep,fold,tr,va,inner) in enumerate(splits):
            key=dict(experiment=name,protocol=protocol,repeat=rep,fold=fold);checkpoint=out/'checkpoints'/f'{name}_{protocol}_{rep}_{fold}.joblib'
            if checkpoint.exists():pack=joblib.load(checkpoint)
            else:
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always',ConvergenceWarning)
                    search=GridSearchCV(pipeline(name),{'model__alpha':ALPHAS,'model__l1_ratio':L1},cv=inner,scoring='neg_root_mean_squared_error',n_jobs=1,error_score='raise').fit(train.iloc[tr][cols],train.iloc[tr][TARGET])
                count=sum(issubclass(x.category,ConvergenceWarning) for x in caught)
                if count:raise ValueError(f'{name}: convergence warning; review explicitly')
                model=search.best_estimator_;pred=model.predict(train.iloc[va][cols])
                raw_names=model.named_steps['encoding'].get_feature_names_out() if 'encoding' in model.named_steps else np.array(cols)
                support=model.named_steps['constants'].support_;names=raw_names[support];betas=model.named_steps['model'].coef_
                pack=dict(predictions=[{**key,ID:pid,'y_true':float(y),'y_pred':float(p),'outer_model_id':f'{name}_{protocol}_{rep}_{fold}'} for pid,y,p in zip(train.iloc[va][ID],train.iloc[va][TARGET],pred)],
                  registry={**key,'params':json.dumps(search.best_params_),'inner_rmse':-search.best_score_,'n_train':len(tr),'n_validation':len(va),'n_effective_columns':len(names),'dropped_columns':json.dumps(raw_names[~support].tolist()),'n_nonzero_coefficients':int((abs(betas)>1e-10).sum()),'convergence_warnings':count},
                  coefficients=[{**key,'feature':c,'standardized_coefficient':float(b),'coefficient_original_units':float(b/model.named_steps['scaler'].scale_[j])} for j,(c,b) in enumerate(zip(names,betas))],
                  tuning=[{**key,'params':json.dumps(p),'inner_rmse':float(-score),'rank':int(rank)} for p,score,rank in zip(search.cv_results_['params'],search.cv_results_['mean_test_score'],search.cv_results_['rank_test_score'])])
                joblib.dump(model,out/'models'/f'{name}_{protocol}_{rep}_{fold}.joblib',compress=3);joblib.dump(pack,checkpoint,compress=3)
            rows.extend(pack['predictions']);registry.append(pack['registry']);coeff.extend(pack['coefficients']);tuning.extend(pack['tuning'])
            if (idx+1)%10==0 or idx==64:print(name,idx+1,'/65',flush=True)
        p=pd.DataFrame(rows)
        if name==BASE:
            reference=pd.read_parquet(H/'tables/31_oof_individual.parquet');reference=reference[reference.experiment.eq('H1_RAIN')]
            q=p.merge(reference,on=[ID,'protocol','repeat','fold'],suffixes=('_J','_H'),validate='one_to_one')
            if len(q)!=len(p) or not np.allclose(q.y_true_J,q.y_true_H,atol=1e-12) or not np.allclose(q.y_pred_J,q.y_pred_H,rtol=0,atol=1e-8):raise ValueError('J0 does not reproduce H1; stop before remaining experiments')
            gate=dict(passed=True,n_predictions=len(q),max_abs_prediction_difference=float(abs(q.y_pred_J-q.y_pred_H).max()))
            (out/'baseline_reproduction_gate.json').write_text(json.dumps(gate,indent=2),encoding='utf-8');print('J0/H1 reproduction gate PASSED',gate,flush=True)
        predictions.append(p)
    p=pd.concat(predictions,ignore_index=True)
    p.to_parquet(out/'tables/02_oof_predictions.parquet',index=False);p.to_csv(out/'tables/02_oof_predictions.csv',index=False)
    pd.DataFrame(registry).to_csv(out/'tables/03_registry.csv',index=False);pd.DataFrame(coeff).to_csv(out/'tables/04_coefficients.csv',index=False);pd.DataFrame(tuning).to_csv(out/'tables/05_inner_search.csv',index=False)
    analyze(p,d,out)
    before=json.loads((out/'protected_inputs.json').read_text(encoding='utf-8'))
    if before!=snapshot():raise ValueError('Protected H/I/Champion inputs changed')
    files=[x for x in out.rglob('*') if x.is_file() and 'checkpoints' not in x.parts and x.name!='manifest.json']+[x for x in proc.rglob('*') if x.is_file()]
    manifest=dict(status='complete',section='J',n_train=138,hidden_y_used=False,previous_results_unchanged=True,final_59_predictions_generated=False,python=platform.python_version(),source_hashes={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},artifacts={str(x.relative_to(ROOT)):sha(x) for x in files})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print('J COMPLETE; protected inputs unchanged',flush=True)

def analyze(predictions,d,out):
    comparison,folds,reps=summarize(predictions,out)
    p=predictions.merge(d.drop(columns=RAIN+[c for c in d if c.startswith('soil_top')]),on=ID,validate='many_to_one');p['error']=p.y_pred-p.y_true;p['abs_error']=abs(p.error)
    base=p[p.experiment.eq(BASE)][[ID,'protocol','repeat','fold','abs_error','error']].rename(columns={'abs_error':'baseline_abs_error','error':'baseline_error'})
    p=p.merge(base,on=[ID,'protocol','repeat','fold'],validate='many_to_one');p['delta_absolute_error']=p.baseline_abs_error-p.abs_error
    p.to_parquet(out/'tables/10_errors_with_geography.parquet',index=False)
    contrasts=[('slope',BASE,'J1_RAIN_SLOPE'),('altitude_given_slope','J1_RAIN_SLOPE','J2_RAIN_TOPO'),('soil_groups',BASE,'J3_RAIN_SOIL_GROUP'),('soil_given_topography','J2_RAIN_TOPO','J4_RAIN_TOPO_SOIL'),('topography_given_soil','J3_RAIN_SOIL_GROUP','J4_RAIN_TOPO_SOIL'),('full_vs_groups','J3_RAIN_SOIL_GROUP','J5_RAIN_SOIL_FULL')]+[(name,BASE,name) for name in comparison.experiment.unique() if name!=BASE]
    paired=[];foldpaired=[]
    for label,b,c in contrasts:
        for table,keys,destination in [(reps,['protocol','repeat'],paired),(folds,['protocol','repeat','fold'],foldpaired)]:
            z=table[table.experiment.eq(b)].merge(table[table.experiment.eq(c)],on=keys,suffixes=('_base','_candidate'),validate='one_to_one')
            for _,r in z.iterrows():destination.append({**{k:r[k] for k in keys},'contrast':label,'base':b,'candidate':c,'delta_RMSE':r.RMSE_base-r.RMSE_candidate,'delta_MAE':r.MAE_base-r.MAE_candidate})
    pd.DataFrame(paired).to_csv(out/'tables/11_paired_repetitions.csv',index=False);fp=pd.DataFrame(foldpaired);fp.to_csv(out/'tables/12_paired_folds.csv',index=False)
    ps=pd.DataFrame(paired).groupby(['protocol','contrast','base','candidate']).agg(delta_RMSE_mean=('delta_RMSE','mean'),delta_RMSE_sd=('delta_RMSE','std'),delta_MAE_mean=('delta_MAE','mean'),fraction_repeats_improving=('delta_RMSE',lambda x:(x>1e-10).mean())).reset_index()
    wins=fp.groupby(['protocol','contrast']).delta_RMSE.apply(lambda x:(x>1e-10).mean()).rename('fraction_folds_improving').reset_index();ps=ps.merge(wins,on=['protocol','contrast']);ps.to_csv(out/'tables/13_incremental_summary.csv',index=False)
    subgroup=[];profile=[];same=[];pairrows=[]
    p['yield_bin']=np.where(p.y_true<3,'low_lt3',np.where(p.y_true>5,'high_gt5','middle_3_5'))
    for (protocol,name,rep),z in p.groupby(['protocol','experiment','repeat']):
        strata={'all':np.ones(len(z),bool),'Chignahuapan':z.Municipio.eq('Chignahuapan'),'other_municipalities':~z.Municipio.eq('Chignahuapan'),'near_boundary_125m':z.soil_assignment_reserve,'away_boundary_125m':~z.soil_assignment_reserve,'source_key_discrepancy':z.soil_share_key_not_found_in_E1402_text>0,'source_key_agrees':z.soil_share_key_not_found_in_E1402_text<=0}
        for radius in [50,250]:strata[f'near_boundary_{radius}m']=z[f'soil_boundary_buffer_{radius}m_share']>0;strata[f'away_boundary_{radius}m']=z[f'soil_boundary_buffer_{radius}m_share']<=0
        for k in ['low_lt3','middle_3_5','high_gt5']:strata[k]=z.yield_bin.eq(k);strata['Chignahuapan_'+k]=z.Municipio.eq('Chignahuapan')&z.yield_bin.eq(k)
        for stratum,mask in strata.items():
            q=z.loc[mask]
            if len(q):subgroup.append(dict(protocol=protocol,experiment=name,repeat=rep,stratum=stratum,n=len(q),**metrics(q.y_true,q.y_pred)))
        for group,q in z.groupby('climate_profile'):
            if len(q)<2:continue
            profile.append(dict(protocol=protocol,experiment=name,repeat=rep,profile=group,n=len(q),n_outer_models=q.outer_model_id.nunique(),y_sd=q.y_true.std(),prediction_sd=q.y_pred.std(),mean_paired_absolute_error_improvement=q.delta_absolute_error.mean(),**metrics(q.y_true,q.y_pred),interpretation='OOF dispersion may include differing fold models; see same-model diagnostics'))
            for model,qq in q.groupby('outer_model_id'):
                if len(qq)<2:continue
                varying=qq.y_true.std()>1e-12 and qq.y_pred.std()>1e-12
                same.append(dict(protocol=protocol,experiment=name,repeat=rep,profile=group,outer_model_id=model,n=len(qq),y_sd=qq.y_true.std(),prediction_sd=qq.y_pred.std(),prediction_range=qq.y_pred.max()-qq.y_pred.min(),within_model_correlation=qq.y_true.corr(qq.y_pred) if len(qq)>=5 and varying else np.nan,**metrics(qq.y_true,qq.y_pred)))
                for aa,bb in itertools.combinations(qq.itertuples(),2):
                    dy=aa.y_true-bb.y_true;dp=aa.y_pred-bb.y_pred
                    pairrows.append(dict(protocol=protocol,experiment=name,repeat=rep,profile=group,outer_model_id=model,ID_A=getattr(aa,ID),ID_B=getattr(bb,ID),observed_difference=dy,predicted_difference=dp,difference_error=dp-dy,same_outer_model=True))
    sg=pd.DataFrame(subgroup);sg.to_csv(out/'tables/14_subgroups_by_repeat.csv',index=False)
    pd.DataFrame(profile).to_csv(out/'tables/15_within_profile_oof.csv',index=False);sm=pd.DataFrame(same);sm.to_csv(out/'tables/16_same_model_within_profile.csv',index=False)
    pr=pd.DataFrame(pairrows);pr.to_parquet(out/'tables/17_same_model_pair_differences.parquet',index=False)
    pr.groupby(['protocol','experiment','repeat']).agg(n_pairs=('difference_error','size'),pair_difference_MAE=('difference_error',lambda x:abs(x).mean()),pair_difference_RMSE=('difference_error',lambda x:np.sqrt(np.mean(x*x))),prediction_difference_sd=('predicted_difference','std')).reset_index().to_csv(out/'tables/18_pair_difference_metrics.csv',index=False)
    co=pd.read_csv(out/'tables/04_coefficients.csv');rr=pd.read_csv(out/'tables/03_registry.csv')
    coef=[]
    for (protocol,name,feature),q in co.groupby(['protocol','experiment','feature']):
        n=len(rr[(rr.protocol==protocol)&(rr.experiment==name)]);v=np.r_[q.standardized_coefficient.to_numpy(),np.zeros(n-len(q))]
        coef.append(dict(protocol=protocol,experiment=name,feature=feature,n_folds=n,n_folds_nonconstant=len(q),mean_standardized_coefficient=v.mean(),sd_standardized_coefficient=v.std(),positive_fraction=float((v>1e-10).mean()),negative_fraction=float((v< -1e-10).mean()),nonzero_fraction=float((abs(v)>1e-10).mean()),warning='Conditional regularized coefficients; dependent shares and omitted variables prevent causal interpretation'))
    pd.DataFrame(coef).to_csv(out/'tables/19_coefficient_stability.csv',index=False)
    numeric=RAIN+TOPO+[c for c in d if c.startswith('soil_map_share_mentions_group_') or c.startswith('soil_unit_share__')]
    d[d.CONJUNTO.eq('ENTRENAMIENTO')][numeric].corr().to_csv(out/'tables/20_training_feature_correlations.csv')
    unknown=[]
    for protocol,rep,fold,tr,va,inner in load_frozen_splits(supervised_data(d,pd.read_csv(MASTER)))[0]:
        units=[c for c in d if c.startswith('soil_unit_share__')];train_ids=set(predictions[(predictions.protocol==protocol)&(predictions['repeat']==rep)&(predictions.fold==fold)&(predictions.experiment==BASE)][ID]);training=d[d.CONJUNTO.eq('ENTRENAMIENTO')&~d[ID].isin(train_ids)];validation=d[d[ID].isin(train_ids)]
        for c in units:
            if training[c].max()<=1e-10 and validation[c].max()>1e-10:unknown.append(dict(protocol=protocol,repeat=rep,fold=fold,unit=c,n_validation_present=int((validation[c]>1e-10).sum()),policy='absent training column dropped; no target-based category pooling'))
    pd.DataFrame(unknown,columns=['protocol','repeat','fold','unit','n_validation_present','policy']).to_csv(out/'tables/21_unseen_unit_support.csv',index=False)
    extended_diagnostics(out,p)
    benchmarks=predictions[predictions.protocol.eq('random')].copy()
    h=pd.read_parquet(H/'tables/31_oof_individual.parquet');h=h[h.experiment.eq('H8_CLIMATE_CURRENT_ORIGINAL')&h.protocol.eq('random')];benchmarks=pd.concat([benchmarks,h],ignore_index=True)
    ch=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet');ch=ch[ch.architecture.eq('A_CURRENT_CH_H_T')].rename(columns={'architecture':'experiment'});ch['protocol']='random'
    reference=predictions[predictions.experiment.eq(BASE)&predictions.protocol.eq('random')][[ID,'repeat','fold','y_true']]
    check=reference.merge(ch,on=[ID,'repeat','fold'],suffixes=('_J','_champion'),validate='one_to_one')
    if len(check)!=1380 or not np.allclose(check.y_true_J,check.y_true_champion):raise ValueError('Champion OOF folds not comparable')
    benchmarks=pd.concat([benchmarks,ch],ignore_index=True);benchrows=[]
    for (name,rep),z in benchmarks.groupby(['experiment','repeat']):
        if len(z)!=138 or not z[ID].is_unique:raise ValueError('Benchmark must have one complete, compatible OOF repetition')
        benchrows.append(dict(experiment=name,repeat=rep,**metrics(z.y_true,z.y_pred)))
    pd.DataFrame(benchrows).to_csv(out/'tables/22_contextual_benchmarks_repeat.csv',index=False)
    benchmark=pd.DataFrame(benchrows).groupby('experiment')[['RMSE','MAE','R2','bias_pred_minus_y']].mean().reset_index();benchmark.to_csv(out/'tables/23_contextual_benchmark_summary.csv',index=False)
    extrapolation_diagnostics(out)
    report(out,comparison,ps,sg,sm,benchmark)
    plots(out,p,comparison,ps,sg,sm)

def extended_diagnostics(out,p=None):
    if p is None:p=pd.read_parquet(out/'tables/10_errors_with_geography.parquet')
    heterogeneous=pd.read_csv(IOUT/'tables/48_within_profile_soil_variation.csv').set_index('profile').n_pairs_tv_gt_5pp.gt(0)
    p=p.copy();p['soil_heterogeneous_profile']=p.climate_profile.map(heterogeneous).fillna(False)
    local=[];hetero=[]
    for (protocol,name,rep),z in p.groupby(['protocol','experiment','repeat']):
        for flag,qq in z.groupby('soil_heterogeneous_profile'):
            for scope,q in [('all',qq),('Chignahuapan',qq[qq.Municipio.eq('Chignahuapan')])]:
                if len(q):hetero.append(dict(protocol=protocol,experiment=name,repeat=rep,scope=scope,soil_heterogeneous_profile=bool(flag),n=len(q),**metrics(q.y_true,q.y_pred)))
        for profile,q in z[z.Municipio.eq('Chignahuapan')].groupby('climate_profile'):
            if len(q)>=2:local.append(dict(protocol=protocol,experiment=name,repeat=rep,profile=profile,n=len(q),n_outer_models=q.outer_model_id.nunique(),soil_heterogeneous_profile=bool(heterogeneous.loc[profile]),y_sd=q.y_true.std(),prediction_sd=q.y_pred.std(),mean_absolute_error_improvement=q.delta_absolute_error.mean(),**metrics(q.y_true,q.y_pred)))
    pd.DataFrame(local).to_csv(out/'tables/26_chignahuapan_profiles.csv',index=False)
    pd.DataFrame(hetero).to_csv(out/'tables/27_soil_heterogeneous_profile_subgroups.csv',index=False)
    sg=pd.read_csv(out/'tables/14_subgroups_by_repeat.csv')
    b=sg[sg.experiment.eq(BASE)]
    q=sg[~sg.experiment.eq(BASE)].merge(b,on=['protocol','repeat','stratum'],suffixes=('_candidate','_base'),validate='many_to_one')
    if not q.n_candidate.equals(q.n_base):raise ValueError('Unmatched uncertainty/local comparison observations')
    q['delta_RMSE']=q.RMSE_base-q.RMSE_candidate;q['delta_MAE']=q.MAE_base-q.MAE_candidate;q['absolute_bias_improvement']=abs(q.bias_pred_minus_y_base)-abs(q.bias_pred_minus_y_candidate)
    q.to_csv(out/'tables/28_paired_subgroup_diagnostics.csv',index=False)
    q.groupby(['protocol','experiment_candidate','stratum']).agg(n=('n_candidate','first'),delta_RMSE=('delta_RMSE','mean'),delta_MAE=('delta_MAE','mean'),absolute_bias_improvement=('absolute_bias_improvement','mean')).reset_index().to_csv(out/'tables/29_paired_subgroup_summary.csv',index=False)

def extrapolation_diagnostics(out):
    """Inspect stored fitted pipelines; diagnostic only, no refitting or clipping."""
    d,train,specs=load();rows=[]
    for protocol,rep,fold,tr,va,inner in load_frozen_splits(train)[0]:
        for name in ['J3_RAIN_SOIL_GROUP','J4_RAIN_TOPO_SOIL','J5_RAIN_SOIL_FULL','J6_RAIN_SOIL_TOP3']:
            model=joblib.load(out/'models'/f'{name}_{protocol}_{rep}_{fold}.joblib')
            cols=specs[name];a=model[:-1].transform(train.iloc[tr][cols]);b=model[:-1].transform(train.iloc[va][cols])
            names=model.named_steps['encoding'].get_feature_names_out() if 'encoding' in model.named_steps else np.array(cols)
            names=names[model.named_steps['constants'].support_]
            for j,feature in enumerate(names):
                if not ('soil' in feature or 'top3' in feature):continue
                maximum=float(abs(b[:,j]).max())
                if maximum>10:
                    k=int(np.argmax(abs(b[:,j])));beta=model.named_steps['model'].coef_[j]
                    rows.append(dict(experiment=name,protocol=protocol,repeat=rep,fold=fold,feature=feature,max_abs_validation_z=maximum,worst_validation_ID=train.iloc[va[k]][ID],train_z_min=float(a[:,j].min()),train_z_max=float(a[:,j].max()),validation_z=float(b[k,j]),standardized_coefficient=float(beta),contribution_t_ha=float(b[k,j]*beta),training_scale=float(model.named_steps['scaler'].scale_[j]),screen='postfit descriptive |z|>10; no removal, clipping or retuning'))
    pd.DataFrame(rows).to_csv(out/'tables/30_extrapolation_screen.csv',index=False)

def report(out,c,paired,sg,same,benchmark):
    table=c.pivot(index='experiment',columns='protocol',values='RMSE_mean').reset_index()
    baseline=c[c.experiment.eq(BASE)].set_index('protocol').RMSE_mean;decisions=[]
    for name in table.experiment:
        if name==BASE:continue
        q=c[c.experiment.eq(name)].set_index('protocol').RMSE_mean;delta=baseline-q;geo_ok=bool((delta.drop('random')>=-.01).all())
        repeatwin=paired[(paired.protocol=='random')&(paired.base==BASE)&(paired.candidate==name)].fraction_repeats_improving.iloc[0]
        status='candidate for controlled follow-up; not a Champion replacement' if delta['random']>0 and repeatwin>=.8 and geo_ok else 'potential known-region use only; geographic transfer not demonstrated' if delta['random']>0 and not geo_ok else 'no consistent incremental support under prespecified criteria'
        decisions.append(dict(experiment=name,random_RMSE_improvement=delta['random'],random_repeat_win_fraction=repeatwin,worst_grouped_RMSE_improvement=delta.drop('random').min(),geographic_margin_pass=geo_ok,classification=status))
    decisions=pd.DataFrame(decisions);decisions.to_csv(out/'tables/24_operational_decisions.csv',index=False)
    sub=sg.groupby(['protocol','experiment','stratum']).agg(n=('n','first'),RMSE=('RMSE','mean'),MAE=('MAE','mean'),bias=('bias_pred_minus_y','mean')).reset_index();sub.to_csv(out/'tables/25_subgroup_summary.csv',index=False)
    ch=sub[sub.stratum.eq('Chignahuapan')].pivot(index='experiment',columns='protocol',values='RMSE').reset_index()
    gate=json.loads((out/'baseline_reproduction_gate.json').read_text());pairs=pd.read_csv(out/'tables/18_pair_difference_metrics.csv').groupby(['protocol','experiment'])[['pair_difference_MAE','pair_difference_RMSE']].mean().reset_index()
    slope=c[c.experiment.eq('J1_RAIN_SLOPE')].set_index('protocol').RMSE_mean
    evidence=f"Pendiente reduce RMSE aleatorio {baseline['random']:.5f}→{slope['random']:.5f}, por perfil {baseline['climate_profile']:.5f}→{slope['climate_profile']:.5f} y municipal {baseline['municipality']:.5f}→{slope['municipality']:.5f}, pero espacial empeora {baseline['spatial']:.5f}→{slope['spatial']:.5f}. Por tanto, pendiente merece conservarse como señal local, sin transferencia espacial demostrada. Altitud adicional no resuelve este deterioro; las representaciones de suelo no mejoran el RMSE aleatorio de lluvia sola."
    strata=pd.read_csv(out/'tables/29_paired_subgroup_summary.csv')
    selected=strata[(strata.protocol=='random')&strata.experiment_candidate.isin(['J1_RAIN_SLOPE','J3_RAIN_SOIL_GROUP','J4_RAIN_TOPO_SOIL'])&strata.stratum.isin(['near_boundary_125m','away_boundary_125m','low_lt3','high_gt5'])]
    text=f'''# Sección J — Modelado incremental con topografía y edafología

Se ejecutaron J0–J5 y una sensibilidad J6 Top-3 con Elastic Net, 138 etiquetas y los 65 folds congelados de H. No se reemplazó el Champion ni se generaron predicciones finales para los 59 casos sin etiqueta. Las columnas efectivas y reglas se fijaron antes de entrenar en `configuration.json` y `report/pretraining_audit.md`.

## Reproducción y comparabilidad

J0 reproduce las {gate['n_predictions']} predicciones OOF de H1: diferencia máxima {gate['max_abs_prediction_difference']:.3g}, tolerancia 1e-8. La comparación se aprobó antes de ejecutar J1–J6. Algoritmo, α=[0.01,0.1,1], L1=[0.1,0.5,0.9], semilla2026 y particiones internas/externas son comunes. Imputación, columnas constantes, escalamiento y vocabulario Top3 se aprenden dentro de cada entrenamiento. Se mantienen las categorías raras; no se seleccionan usando frecuencia del universo completo.

**RMSE t/ha: métricas calculadas sobre cada repetición OOF completa y después promediadas**, no promedio de RMSE de folds:

{markdown_table(table)}

`40_model_comparison.csv` incluye MAE, R², sesgo, desviación entre folds y repeticiones; 41/42 conservan ambos niveles. Los contrastes pareados de RMSE y MAE están en tablas 11–13: positivo=mejora. Los folds/repeticiones se solapan; proporciones de mejoras y dispersiones son diagnósticos, no pruebas independientes ni intervalos de confianza.

## Contribución incremental y decisión

{evidence}

En aleatorio, el MAE de pendiente es mayor que el de lluvia sola aunque su RMSE sea menor; por eso la mejora no es uniforme entre métricas. La tabla de contrastes incluye ambas. No hay una variante que justifique integración general al Champion bajo los criterios predefinidos. La recomendación es conservar pendiente para investigación local/controlada y reservar suelo como contexto mientras no se resuelvan soporte y transferencia.

{markdown_table(decisions)}

El margen 0.01t/ha es operativo exploratorio. La clasificación de transferencia exige ausencia de deterioros superiores al margen en perfil, municipio y espacio; mejora aleatoria por sí sola no basta. J3/J4 son las pruebas compactas principales; J5 prueba detalle y dimensionalidad. Antes de integración debe considerarse también soporte de categorías, sesgos extremos, diferenciación intraperfil y reservas cartográficas, sin declarar automáticamente ganador.

## Diferenciación dentro de clima idéntico

Las tablas 15–18 separan dispersión de todas las predicciones OOF de la dispersión de parcelas evaluadas por **el mismo modelo externo**. En aleatorio, parcelas del mismo perfil pueden caer en folds distintos: esa dispersión no acredita valor de nuevas variables. Bajo el protocolo por perfil, todas las parcelas del perfil se evalúan con el mismo ajuste. Correlación observada/predicha se informa solo con al menos cinco etiquetas y variación no nula. Se comparan diferencias de Y entre pares evaluados por el mismo modelo; estas observaciones pareadas tampoco son independientes.

{markdown_table(pairs)}

`10_errors_with_geography.parquet` conserva error por parcela, fold, repetición, protocolo, perfil, municipio e incertidumbre, más cambio pareado de error absoluto frente a J0. Los extremos son categorías descriptivas fijadas antes de entrenar: Y<3, 3<=Y<=5 y Y>5t/ha; no se usaron para seleccionar modelos.

## Chignahuapan y reservas cartográficas

Hay 71 etiquetas locales; sus errores se extraen de las mismas predicciones OOF, sin ajuste local independiente. I encontró aproximadamente 85.8% de SS local dentro de sus perfiles; ello no implicaba que esa variación pudiera predecirse con suelo/topografía. RMSE local comparable:

{markdown_table(ch)}

La tabla 25 informa número de etiquetas, RMSE, MAE y sesgo para Chignahuapan, otras regiones, extremos y reservas. Se mantienen **todas** las parcelas en evaluación. Los estratos 50/125/250m son escenarios cartográficos, no probabilidades de exactitud. Las dos claves UM con diferencia lo/hu entre vector y E1402 permanecen identificadas; no se sustituyen calificadores. Un estrato pequeño no ofrece evidencia robusta. No se perturbaron límites ni se fabricaron fracciones: Top3 frente a grupos/composición completa es la sensibilidad de representación justificada.

Las tablas 26/27 detallan específicamente perfiles de Chignahuapan y perfiles con variación cartográfica >5pp, con soporte de cada comparación. Las tablas 28/29 conservan diferencias pareadas de RMSE, MAE y sesgo absoluto por estrato: permite comprobar si una mejora ocurre cerca de límites o también lejos de ellos, sin usar esos estratos para escoger parámetros.

Diagnóstico aleatorio: diferencias positivas favorecen el candidato; N cuenta etiquetas únicas, no repeticiones independientes.

{markdown_table(selected[['experiment_candidate','stratum','n','delta_RMSE','delta_MAE','absolute_bias_improvement']])}

Los grupos de suelo deterioran RMSE tanto lejos como cerca de límites, con mayor deterioro cerca; no hay una mejora general escondida al excluir parcelas inciertas. La pendiente mejora el sesgo de los rendimientos altos (10 etiquetas), pero no el de los bajos (14), y su mejora local en Chignahuapan no se extiende al conjunto espacial completo. El estrato de discrepancia entre claves tiene solo una etiqueta: no permite conclusiones robustas.

Las fracciones describen unidades oficiales 1:250000 y las coberturas de grupos describen unidades que mencionan el grupo; no porcentajes físicos del suelo asociado. Se preservan 13 unidades con menos de cinco etiquetas y dos exclusivas de predicción como información auditada, sin utilizarlas para filtrar globalmente. La tabla 21 registra unidades ausentes en entrenamiento externo que aparecen en evaluación. Top3 aprende etiquetas nominales dentro del fold, pondera por cobertura y conserva resto y masa desconocida; no convierte claves o puestos en números continuos.

## Coeficientes y redundancia

Tablas 19/20: estabilidad de coeficientes, frecuencias de signo/no-cero y correlaciones de características en TRAIN. La composición completa suma uno y sus columnas dependen del intercepto; Elastic Net tiene penalización L2 estrictamente positiva, que estabiliza esa colinealidad. Los grupos pueden sumar más de uno. El signo depende de regularización y variables incluidas; no mide un efecto causal ni una propiedad de infiltración, pH o laboratorio.

J5 y Top3 presentan un fracaso de estabilidad por perfil: RMSE cercano a 3.25t/ha. En un ajuste externo, `PHpdn-ph+VRpe/2` aparece con pequeñas fracciones en entrenamiento y cobertura alta en evaluación; su valor estandarizado llega a aproximadamente 353 y su contribución a una predicción es cercana a −14.66t/ha. Se conservan las predicciones negativas y todos los errores, sin recortarlos ni cambiar la búsqueda después de observar el resultado. `30_extrapolation_screen.csv` inspecciona los modelos guardados para identificar este tipo de falta de soporte. Un esquema Top3 ponderado no resuelve el problema porque preserva casi las mismas coberturas.

Esto limita **esta representación y pipeline**, no demuestra que el suelo carezca de influencia agronómica. La regularización y la eliminación de columnas constantes no garantizan estabilidad frente a una columna casi ausente en entrenamiento y abundante fuera. Si se reconsidera el suelo completo, primero habría que predefinir otra sensibilidad con soporte mínimo/agrupación aprendida dentro de cada entrenamiento, conservar masa desconocida y volver a evaluar exactamente los mismos protocolos. Esa sensibilidad no se ejecutó ni se utilizó para rescatar resultados de J.

## Contexto de Familia 1 y Champion

Las predicciones del Champion fueron compatibles por ID, repetición y fold con J0 aleatorio. Se recalculan RMSE/MAE/R²/sesgo sobre las mismas OOF completas:

{markdown_table(benchmark)}

Climate Current usa el bloque climático original completo; Champion incorpora selección climática y correcciones residuales satelitales/topográficas. Cambian características y arquitectura: sus diferencias no se atribuyen exclusivamente a suelo o topografía. Se reutilizan resultados existentes y no se refitan esos benchmarks. No se extrapola este contraste contextual aleatorio a protocolos geográficos que no tienen predicciones comparables del Champion.

## Productos y siguiente decisión

Matrices objetivo-libres en `data/processed/family_1/{NAME}/{out.name}`, modelos por fold, búsqueda interna, OOF, métricas, errores, diagnósticos locales/intraperfil, incertidumbre y coeficientes en esta carpeta. Figuras muestran RMSE por protocolo, diferencias respecto de J0, observado/predicho, errores espaciales, perfiles, Chignahuapan y límites. Scripts 325 (auditoría) y 326 (ejecución) continúan la numeración existente.

Las clasificaciones operativas son evidencia para una investigación posterior, no un nuevo ganador. Si las mejoras no sobreviven retención municipal/espacial o se concentran en categorías/parcelas inciertas, conservar la variable como señal local/contexto. Una integración residual al Champion y las interacciones lluvia–suelo requieren un experimento separado, pequeño y validado, no se ejecutan en J.
'''
    (out/'report/section_j_report.md').write_text(text,encoding='utf-8');(ROOT/'documentation/j_incremental_yield_modeling.md').write_text(text,encoding='utf-8')

def plots(out,p,c,paired,sg,same):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    def save(fig,name):fig.tight_layout();fig.savefig(out/'figures'/f'{name}.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(13,6));sns.barplot(data=c,x='experiment',y='RMSE_mean',hue='protocol',ax=ax);ax.tick_params(axis='x',rotation=25);ax.set_ylabel('RMSE de repeticiones OOF completas t/ha');save(fig,'01_rmse_protocol')
    q=paired[paired.base.eq(BASE)];fig,ax=plt.subplots(figsize=(12,6));sns.barplot(data=q,x='candidate',y='delta_RMSE_mean',hue='protocol',ax=ax);ax.axhline(0,c='black');ax.axhline(-.01,ls='--',c='gray');ax.tick_params(axis='x',rotation=25);save(fig,'02_delta_rmse_baseline')
    avg=p[p.protocol.eq('random')].groupby(['experiment',ID]).agg(y_true=('y_true','first'),y_pred=('y_pred','mean'),error=('error','mean'),longitude=('longitude','first'),latitude=('latitude','first'),climate_profile=('climate_profile','first')).reset_index()
    fig,axes=plt.subplots(2,3,figsize=(14,9))
    for (name,z),ax in zip(avg[~avg.experiment.eq('J6_RAIN_SOIL_TOP3')].groupby('experiment'),axes.flat):ax.scatter(z.y_true,z.y_pred,s=14);ax.plot([1,6],[1,6],'k--');ax.set(title=name,xlabel='Y real',ylabel='OOF promedio; descriptivo')
    save(fig,'03_observed_predicted')
    fig,axes=plt.subplots(2,3,figsize=(15,9))
    limit=max(2,float(abs(p.loc[p.protocol.eq('spatial'),'error']).max()))
    for (name,z),ax in zip(p[p.protocol.eq('spatial')&~p.experiment.eq('J6_RAIN_SOIL_TOP3')].groupby('experiment'),axes.flat):sc=ax.scatter(z.longitude,z.latitude,c=z.error,cmap='coolwarm',vmin=-limit,vmax=limit,s=22);fig.colorbar(sc,ax=ax);ax.set(title=name,xlabel='Longitud',ylabel='Latitud')
    save(fig,'04_spatial_errors')
    fig,ax=plt.subplots(figsize=(12,5));sns.boxplot(data=p[p.protocol.eq('climate_profile')],x='experiment',y='delta_absolute_error',ax=ax,fliersize=2);ax.axhline(0,c='black');ax.tick_params(axis='x',rotation=25);save(fig,'05_profile_protocol_paired_errors')
    ch=sg[sg.stratum.eq('Chignahuapan')].groupby(['protocol','experiment']).RMSE.mean().reset_index();fig,ax=plt.subplots(figsize=(12,5));sns.barplot(data=ch,x='experiment',y='RMSE',hue='protocol',ax=ax);ax.tick_params(axis='x',rotation=25);save(fig,'06_chignahuapan')
    u=sg[sg.stratum.isin(['near_boundary_125m','away_boundary_125m'])].groupby(['protocol','experiment','stratum']).RMSE.mean().reset_index();fig,axes=plt.subplots(1,2,figsize=(14,5))
    for protocol,ax in zip(['random','spatial'],axes):sns.barplot(data=u[u.protocol.eq(protocol)],x='experiment',y='RMSE',hue='stratum',ax=ax);ax.tick_params(axis='x',rotation=35);ax.set_title(protocol)
    save(fig,'07_boundary_uncertainty')
    s=same[same.protocol.eq('climate_profile')];fig,ax=plt.subplots(figsize=(12,5));sns.boxplot(data=s,x='experiment',y='prediction_sd',ax=ax,fliersize=2);ax.tick_params(axis='x',rotation=25);ax.set_ylabel('SD predicha dentro de perfil, mismo modelo');save(fig,'08_same_model_profile_dispersion')
    profiles=pd.read_csv(out/'tables/15_within_profile_oof.csv');matrix=profiles[profiles.protocol.eq('climate_profile')].pivot(index='profile',columns='experiment',values='mean_paired_absolute_error_improvement')
    fig,ax=plt.subplots(figsize=(12,6));sns.heatmap(matrix,cmap='coolwarm',center=0,annot=True,fmt='.2f',ax=ax);ax.set_title('Mejora MAE por perfil, mismo modelo; positivo favorece candidato');save(fig,'09_profile_mae_improvement')
