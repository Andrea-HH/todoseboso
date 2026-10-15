"""K: bounded soil features and strictly nested, cross-fitted residual models.

All historical products are read-only. No full-sample OOF residual is used to fit
a corrector. Climate hyperparameter selection itself excludes each held-out label.
"""
from pathlib import Path
import json, hashlib, itertools, warnings, platform, os, uuid, importlib.metadata
import numpy as np
import pandas as pd
import joblib
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import GridSearchCV, KFold, GroupKFold, ParameterGrid
from sklearn.exceptions import ConvergenceWarning
from . import j_incremental_yield as j
from .climate_signal_reporting import summarize
from .rainfall_modeling import metrics

ROOT, ID, TARGET, RAIN, TOPO = j.ROOT, j.ID, j.TARGET, j.RAIN, j.TOPO
NAME = 'k_standalone_residual_geographic_edaphological'
ALPHA = [.001, .01, .1, 1.]
L1 = [.1, .5, .9]
ETA = [0., .25, .5, 1.]
GRID = {'model__alpha': ALPHA, 'model__l1_ratio': L1}

def locations(version='v1'):
    return ROOT/'outputs/modeling/family_1'/NAME/version, ROOT/'data/processed/family_1'/NAME/version

class StableFeatures(BaseEstimator, TransformerMixin):
    """Training-only imputations/constants; z-scale topo/rain, keep soil in [0,1].

    S2 learns support from positive coverage, pools rare AND unseen mass as Other.
    No variance-based soil amplification. Column order follows training schema.
    """
    def __init__(self, min_support=None): self.min_support = min_support
    def fit(self, X, y=None):
        self.columns_ = list(X.columns)
        self.unit_columns_ = [c for c in self.columns_ if c.startswith('soil_unit_share__')]
        self.kept_units_ = ([c for c in self.unit_columns_ if (X[c].fillna(0)>1e-12).sum() >= self.min_support]
                            if self.min_support is not None else self.unit_columns_)
        raw = self._raw(X)
        self.names_ = list(raw.columns)
        a = raw.to_numpy(float)
        self.median_ = np.array([np.median(v[np.isfinite(v)]) if np.isfinite(v).any() else 0. for v in a.T])
        a = np.where(np.isfinite(a), a, self.median_)
        self.center_ = np.zeros(a.shape[1]); self.scale_ = np.ones(a.shape[1])
        for n, c in enumerate(self.names_):
            if c in RAIN+TOPO:
                self.center_[n] = a[:, n].mean()
                self.scale_[n] = a[:, n].std() if a[:, n].std()>1e-10 else 1.
        self.support_ = a.var(axis=0)>1e-20
        self.all_constant_ = not self.support_.any()
        if self.all_constant_: self.support_[0] = True
        return self
    def _raw(self, X):
        raw = X[self.columns_].copy()
        if self.min_support is not None:
            # Fixed map schema is source metadata, not a vocabulary learned from validation.
            nonunits = [c for c in self.columns_ if c not in self.unit_columns_]
            other = [c for c in self.unit_columns_ if c not in self.kept_units_]
            raw = raw[nonunits+self.kept_units_]
            raw['soil_other_share'] = X[other].sum(axis=1, min_count=1) if other else 0.
        return raw
    def transform(self, X):
        a = self._raw(X).to_numpy(float)
        a = np.where(np.isfinite(a), a, self.median_)
        return ((a-self.center_)/self.scale_)[:, self.support_]
    def get_feature_names_out(self, input_features=None): return np.array(self.names_)[self.support_]

def pipeline(min_support=None):
    return Pipeline([('features', StableFeatures(min_support)),
                     ('model', ElasticNet(max_iter=20000, random_state=2026))])

class StableTop3(BaseEstimator, TransformerMixin):
    """Audit-only nominal composition: unknown includes missing nominal keys.

    Rank never enters as a numeric feature. Remaining coverage is separate, not
    duplicated with unknown unit coverage. No vocab learned from held-out data.
    """
    def fit(self,X,y=None):
        self.units_=sorted({str(u) for k in [1,2,3] for u,p in zip(X[f'soil_top{k}_unit'],X[f'soil_top{k}_share']) if pd.notna(u) and pd.notna(p) and p>1e-12})
        self.lookup_={u:i for i,u in enumerate(self.units_)}
        return self
    def transform(self,X):
        z=np.zeros((len(X),len(self.units_)+2))
        for k in [1,2,3]:
            for row,(u,p) in enumerate(zip(X[f'soil_top{k}_unit'],X[f'soil_top{k}_share'])):
                if pd.isna(p):
                    if pd.isna(u):continue # absent rank in audited I schema = structural zero
                    raise ValueError('Unknown coverage cannot be invented from a missing share')
                if p<0 or p>1+1e-8:raise ValueError('Invalid coverage')
                column=self.lookup_.get(str(u),len(self.units_)) if pd.notna(u) else len(self.units_)
                z[row,column]+=float(p)
        z[:,-1]=X.soil_remaining_share.to_numpy(float)
        if not np.isfinite(z).all():raise ValueError('Unknown remaining coverage')
        return z
    def get_feature_names_out(self,input_features=None):
        return np.array(['soil_top3_share__'+u for u in self.units_]+['soil_top3_unknown_share','soil_remaining_share'])

def strict_fit(estimator, X, y):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always', ConvergenceWarning)
        estimator.fit(X, y)
    if any(issubclass(a.category, ConvergenceWarning) for a in w):
        raise ValueError('Convergence warning: inspect before proceeding')
    return estimator

def atomic_dump(value,path):
    """Publish completed K cache/model files only; safe concurrent readers."""
    if not path.resolve().is_relative_to((ROOT/'outputs/modeling/family_1'/NAME).resolve()):
        raise ValueError('Atomic cache destination must remain in K output directory')
    if path.exists():
        joblib.load(path) # Existing atomic file is complete; same cache key/config.
        return
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    joblib.dump(value,temporary,compress=3)
    try:temporary.replace(path)
    except PermissionError:
        # Windows refuses replace while another worker reads an identical cache.
        if not path.exists():raise
        joblib.load(path)
        temporary.unlink()

def subcv(frame, protocol, groups):
    """Deeper folds needed only inside frozen inner training sets."""
    if protocol == 'random':
        return list(KFold(n_splits=min(4,len(frame)), shuffle=True, random_state=2026).split(frame))
    g = groups.loc[frame[ID], protocol].to_numpy()
    k = min(4,len(set(g)))
    if k<2: raise ValueError('Insufficient groups for honest nested cross-fitting')
    return list(GroupKFold(k).split(frame, groups=g))

def protection():
    # Extend J's protected inventory to include J itself and every old output.
    p={k:v for k,v in j.snapshot().items() if NAME not in k and 'k_geographic_edaphological' not in k and not Path(k).name.startswith(('k_','k1_'))}
    for base in [j.locations()[0],j.locations()[1]]:
        p.update({str(x.relative_to(ROOT)):j.sha(x) for x in base.rglob('*') if x.is_file()})
    for x in [ROOT/'src/family_1/j_incremental_yield.py',ROOT/'documentation/j_incremental_yield_modeling.md']:
        p[str(x.relative_to(ROOT))]=j.sha(x)
    return p

def load():
    d, t, old = j.load()
    groups = old['J3_RAIN_SOIL_GROUP'][7:]
    units = old['J5_RAIN_SOIL_FULL'][7:]
    specs = {'K0_MEAN':[], 'K1_SLOPE_ONLY':['slope_degrees'], 'K2_TOPO_ONLY':TOPO,
             'K3_SOIL_ONLY':groups, 'K4_TOPO_SOIL':TOPO+groups,
             'K3_SOIL_ONLY_ALT':units, 'KA_RAIN_SLOPE_MATCHED':RAIN+['slope_degrees'],
             'KA_RAIN_TOPO_MATCHED':RAIN+TOPO, 'KA_RAIN_SOIL_STABLE':RAIN+groups,
             'KA_RAIN_TOPO_SOIL_STABLE':RAIN+TOPO+groups,
             'K5_RAIN_RESID_SLOPE':['slope_degrees'], 'K6_RAIN_RESID_TOPO':TOPO,
             'K7_RAIN_RESID_SOIL':groups, 'K8_RAIN_RESID_TOPO_SOIL':TOPO+groups}
    return d,t,old,specs,groups,units

def synthetic_checks():
    x=pd.DataFrame({'slope_degrees':[1.,2.,3.,4.],
        'soil_unit_share__A':[1.-1e-6,1.,1.,1.], 'soil_unit_share__B':[1e-6,0.,0.,0.],
        'soil_unit_share__C':[0.,0.,0.,0.], 'soil_unit_share__D':[0.,0.,0.,0.]})
    v=x.iloc[[0]].copy();v.iloc[0,1:]=[.1,.3,.3,.3]
    rows=[]
    for support in [None,3,5]:
        m=pipeline(support).set_params(model__alpha=.01,model__l1_ratio=.5)
        strict_fit(m,x,np.array([3.,3.2,3.4,3.6]))
        z=m[:-1].transform(v)
        assert np.isfinite(z).all() and np.isfinite(m.predict(v)).all()
        soil=[i for i,c in enumerate(m['features'].get_feature_names_out()) if c.startswith('soil')]
        assert (np.abs(z[:,soil])<=1+1e-10).all()
        if support:
            raw=m['features']._raw(v)
            assert np.allclose(raw.filter(like='soil').sum(axis=1),1)
            assert 'soil_unit_share__C' not in m['features'].kept_units_
        missing=v.copy();missing.iloc[0,0]=np.nan
        assert np.isfinite(m.predict(missing)).all()
        rows.append(dict(test='rare,absent,unknown,shift,composition,multicomponent,missing',min_support=str(support),passed=True,max_abs_transform=float(abs(z).max())))
    constant=pd.DataFrame({'soil_a':[0.,0.,0.]})
    assert np.isfinite(strict_fit(pipeline(),constant,[1.,2.,3.]).predict(pd.DataFrame({'soil_a':[1.]}))).all()
    # Existing nominal Top3 encoder handles ties, changed edition keys and >3 units via remainder.
    top=pd.DataFrame({c:[1.,2.] for c in RAIN})
    for k,(u,p) in enumerate([(['A','B'],[.4,.5]),(['B','A'],[.3,.3]),(['C','C'],[.2,.1])],1):
        top[f'soil_top{k}_unit']=u;top[f'soil_top{k}_share']=p
    top['soil_remaining_share']=[.1,.1]
    enc=StableTop3().fit(top)
    test=top.iloc[[0]].copy();test['soil_top1_unit']='A_other_edition'
    z=enc.transform(test)
    assert abs(z.sum()-1)<1e-10 and abs(z[0,-2]-.4)<1e-10
    swapped=top.copy()
    for field in ['unit','share']:
        swapped[f'soil_top1_{field}']=top[f'soil_top2_{field}'];swapped[f'soil_top2_{field}']=top[f'soil_top1_{field}']
    assert np.allclose(enc.transform(top),enc.transform(swapped))
    missingkey=test.copy();missingkey['soil_top1_unit']=None
    assert np.allclose(enc.transform(missingkey),enc.transform(test))
    missing_share=test.copy();missing_share['soil_top1_share']=np.nan
    try:enc.transform(missing_share)
    except ValueError:pass
    else:raise AssertionError('Missing mass must fail explicitly, never invent soil coverage')
    rows.append(dict(test='ties,rank invariance,edition discrepancy,Top3 unknown+remainder mass',passed=True))
    return pd.DataFrame(rows)

def audit(version='v1'):
    out,proc=locations(version)
    if (out/'manifest.json').exists():raise FileExistsError('Completed K version immutable')
    for p in [out,proc]+[out/x for x in ['tables','splits','models','checkpoints','climate_cache','figures','report']]:p.mkdir(parents=True,exist_ok=True)
    d,t,old,specs,groups,units=load();splits,table,assignment=j.load_frozen_splits(t)
    h=pd.read_csv(j.H/'splits/outer_and_inner_splits.csv')
    assert table.equals(h[table.columns])
    assert TARGET not in d and len(t)==138 and d[ID].is_unique and d.climate_profile.nunique()==53
    table.to_csv(out/'splits/outer_and_inner_splits.csv',index=False)
    assignment.to_csv(out/'splits/group_memberships.csv')
    if not (out/'protected_inputs.json').exists():
        (out/'protected_inputs.json').write_text(json.dumps(protection(),indent=2),encoding='utf-8')
    attrs=pd.read_parquet(j.IDATA/'soil_attributes.parquet')
    ac=[c for c in attrs if c.startswith('soil_map_share')]
    allsoil=d[[ID,'climate_profile','Municipio','CONJUNTO']+units].merge(attrs[[ID]+ac],on=ID,validate='one_to_one')
    labelled=allsoil[allsoil.CONJUNTO.eq('ENTRENAMIENTO')]
    support=[];foldsupport=[]
    for c in units+ac:
        pos=allsoil[c]>1e-12; lab=labelled[labelled[c]>1e-12];v=allsoil.loc[pos,c]
        support.append(dict(feature=c,n_all=int(pos.sum()),n_labelled=len(lab),n_profiles=lab.climate_profile.nunique(),n_municipalities=lab.Municipio.nunique(),min_share=v.min(),median_share=v.median(),max_share=v.max(),n_tiny_lt_1pct=int(((v>0)&(v<.01)).sum()),support_class='B_low_support' if len(lab)<5 else 'A_valid_supported'))
    # Align attrs to supervised ID order; no evaluation data informs transformations.
    sx=allsoil.set_index(ID).loc[t[ID]]
    for protocol,rep,fold,tr,va,inner in splits:
        for c in units+ac:
            a=sx.iloc[tr][c].to_numpy(float);b=sx.iloc[va][c].to_numpy(float)
            sd=a.std();z=(b-a.mean())/sd if sd>0 else np.full(len(b),np.nan)
            foldsupport.append(dict(protocol=protocol,repeat=rep,fold=fold,feature=c,n_train_positive=int((a>1e-12).sum()),n_validation_positive=int((b>1e-12).sum()),train_min=a.min(),train_max=a.max(),validation_min=b.min(),validation_max=b.max(),training_sd=sd,max_abs_conventional_z=float(np.nanmax(abs(z))) if sd>0 else np.nan,n_unseen_positive=int(((b>1e-12)&not_bool((a>1e-12).any())).sum()),n_outside_train_range=int(((b<a.min()-1e-10)|(b>a.max()+1e-10)).sum()),n_conventional_extreme_z=int((abs(z)>10).sum()),n_validation=len(b)))
    pd.DataFrame(support).to_csv(out/'tables/01_support_all.csv',index=False)
    fs=pd.DataFrame(foldsupport);fs.to_csv(out/'tables/02_support_by_outer_fold.csv',index=False)
    fs.groupby('protocol').agg(n_variable_predictions=('n_validation','sum'),n_outside_range=('n_outside_train_range','sum'),n_extreme_variable_predictions=('n_conventional_extreme_z','sum')).to_csv(out/'tables/03_support_protocol_summary.csv')
    # Audit J5/J6 model identity and predictions independently; no refitting J.
    jp=pd.read_parquet(j.locations()[0]/'tables/02_oof_predictions.parquet')
    a=jp[jp.experiment.eq('J5_RAIN_SOIL_FULL')];b=jp[jp.experiment.eq('J6_RAIN_SOIL_TOP3')]
    q=a.merge(b,on=[ID,'protocol','repeat','fold'],suffixes=('_full','_top3'),validate='one_to_one')
    q['prediction_difference']=q.y_pred_full-q.y_pred_top3
    q.to_csv(out/'tables/04_j5_j6_prediction_differences.csv',index=False)
    top=j.WeightedTop3().fit(d[old['J6_RAIN_SOIL_TOP3']]);encoded=top.transform(d[old['J6_RAIN_SOIL_TOP3']])[:,7:]
    reconstructed=pd.DataFrame(encoded[:,:len(top.units_)],columns=['soil_unit_share__'+u for u in top.units_])
    reconstruction=d[units].to_numpy()-reconstructed.reindex(columns=units,fill_value=0).to_numpy()
    modelaudit=[]
    reg=pd.read_csv(j.locations()[0]/'tables/03_registry.csv')
    for protocol,rep,fold,tr,va,inner in splits:
        paths=[j.locations()[0]/'models'/f'{name}_{protocol}_{rep}_{fold}.joblib' for name in ['J5_RAIN_SOIL_FULL','J6_RAIN_SOIL_TOP3']]
        models=[joblib.load(p) for p in paths]
        predictions=[m.predict(t.iloc[va][old[name]]) for m,name in zip(models,['J5_RAIN_SOIL_FULL','J6_RAIN_SOIL_TOP3'])]
        rr=reg[(reg.protocol==protocol)&(reg.repeat==rep)&(reg.fold==fold)].set_index('experiment')
        expected=q[(q.protocol==protocol)&(q['repeat']==rep)&(q.fold==fold)].set_index(ID)
        for name,pred in zip(['J5_RAIN_SOIL_FULL','J6_RAIN_SOIL_TOP3'],predictions):
            cached=jp[(jp.experiment==name)&(jp.protocol==protocol)&(jp['repeat']==rep)&(jp.fold==fold)].set_index(ID).loc[t.iloc[va][ID]].y_pred
            assert np.allclose(pred,cached,atol=1e-10,rtol=0)
        modelaudit.append(dict(protocol=protocol,repeat=rep,fold=fold,full_hash=j.sha(paths[0]),top3_hash=j.sha(paths[1]),same_artifact=j.sha(paths[0])==j.sha(paths[1]),same_params=rr.loc['J5_RAIN_SOIL_FULL','params']==rr.loc['J6_RAIN_SOIL_TOP3','params'],full_effective=rr.loc['J5_RAIN_SOIL_FULL','n_effective_columns'],top3_effective=rr.loc['J6_RAIN_SOIL_TOP3','n_effective_columns'],max_prediction_difference=float(abs(predictions[0]-predictions[1]).max())))
    pd.DataFrame(modelaudit).to_csv(out/'tables/05_j5_j6_model_audit.csv',index=False)
    # S3: actual Grupo1, not guessed key prefixes. This closed composition loses associates/qualifiers.
    long=pd.read_parquet(j.IDATA/'soil_intersections_long.parquet')
    s3=long.pivot_table(index=ID,columns='Grupo1',values='porcentaje_parcela',aggfunc='sum',fill_value=0).reindex(d[ID]).fillna(0)
    s3.columns=['soil_main_group_share__'+str(c) for c in s3.columns]
    s3=s3.reset_index();s3.to_parquet(proc/'s3_main_group_composition.parquet',index=False)
    d[[ID]+groups].to_parquet(proc/'s1_group_mentions.parquet',index=False)
    d[[ID]+units].to_parquet(proc/'s2_full_source_for_fold_pooling.parquet',index=False)
    d[[ID]+old['J6_RAIN_SOIL_TOP3'][7:]].to_parquet(proc/'s4_top3_source.parquet',index=False)
    d.to_parquet(proc/'k_features_197_target_free.parquet',index=False)
    comparisons=[]
    matrices={'S1':d[groups].to_numpy(),'S2_reference':d[units].to_numpy(),'S3':s3.drop(columns=ID).to_numpy(),'S4':encoded}
    for name,matrix in matrices.items():
        pairs=distinguished=0
        for _,indices in d.groupby('climate_profile').groups.items():
            for aa,bb in itertools.combinations(indices,2):
                pairs+=1;distinguished+=np.sum(abs(matrix[aa]-matrix[bb]))/2>.05
        comparisons.append(dict(representation=name,n_columns=matrix.shape[1],n_same_climate_pairs=pairs,n_pairs_L1_half_gt_5pp=distinguished,scale_policy='soil fractions kept in natural [0,1], no variance division',coverage_retained_mean=float(matrix.sum(axis=1).mean()),mass_mean_note='S1 sum may exceed one; S4 includes unknown/remainder; not physical soil proportions'))
    for threshold in [3,5]:
        pooled=StableFeatures(threshold).fit(t[units]);z=pooled._raw(d[units])
        z.insert(0,ID,d[ID]);z.to_parquet(proc/f's2_descriptive_labelled_support_{threshold}.parquet',index=False)
    pd.DataFrame(comparisons).to_csv(out/'tables/06_representation_comparison_target_free.csv',index=False)
    synth=synthetic_checks();synth.to_csv(out/'tables/07_synthetic_stability.csv',index=False)
    config=dict(section='K',primary='S1 group mention coverages',secondary='S2 prevalent units + Other, support threshold 3 or 5 chosen by inner CV only',not_predictively_searched=['S3 main-group composition','S4 weighted nominal Top3'],specs=specs,soil_scaling='raw [0,1], no variance amplification',continuous_scaling='median, training-only constant drop and StandardScaler-equivalent z for rain/topography',alpha_grid=ALPHA,l1_grid=L1,eta_grid=ETA,baseline_grid=dict(alpha=j.ALPHAS,l1=j.L1),support_thresholds=[3,5],seed=2026,n_outer=65,hidden_y_used=False,preprocessing='inside every training fit',residual_nesting='Frozen inner folds select complete residual pipeline; each inner-train climate residual is cross-fitted with deeper grouped folds; climate tuning excludes its held-out labels at every depth',deeper_cv='4-fold KFold seed2026 for random; GroupKFold min(4,n_groups) otherwise',decision=dict(rmse_geographic_margin=.01,mae_deterioration_margin=.01,random_repeat_improvement_fraction=.8,extreme_prediction_screen='unclipped negative predictions and max absolute errors; soil transformed values bounded by natural fractions',significance='descriptive correlated folds, not independent inferential evidence'),aggregation='complete 138-label OOF repetition metrics, then mean over repetitions',source_scope='read-only I official vector overlays, H frozen splits, J controls, cached Champion',primary_rationale='documented 10 groups; broad support, meaningful differentiation within climate profiles, no tiny-variance amplification; no Y used in representation choice',secondary_rationale='S2 conserves full coverage, explicit pooling of rare/unseen map units; tests specificity vs S1 only in standalone soil model')
    cfg=out/'configuration.json'
    if cfg.exists() and json.loads(cfg.read_text(encoding='utf-8'))!=config:raise ValueError('Frozen config changed')
    cfg.write_text(json.dumps(config,indent=2),encoding='utf-8')
    diagnosis=dict(n_j5_j6_predictions=len(q),max_abs_prediction_difference=float(q.prediction_difference.abs().max()),identical_model_files=sum(x['same_artifact'] for x in modelaudit),n_exactly_different_full_top3_rows=int((abs(reconstruction).max(axis=1)>1e-12).sum()),max_omitted_unit_share=float(abs(reconstruction).max()),mean_omitted_unit_share=float(reconstruction.sum(axis=1).mean()),all_synthetic_passed=True,primary='S1',secondary='S2',ready_for_modeling=True)
    (out/'k1_gate.json').write_text(json.dumps(diagnosis,indent=2),encoding='utf-8')
    text='# K.1 — Auditoría y rediseño edafológico\n\n'+j.markdown_table(pd.DataFrame(comparisons))+'\n\n'+json.dumps(diagnosis,indent=2)+'\n\nJ5 y J6 se reconstruyeron desde sus pipelines distintos y coinciden con sus propios OOF. Top3 suma codificaciones nominales ponderadas entre rangos: reconstruye casi toda la misma composición, no aporta un bloque independiente. Se conserva el remanente. No se sobrescribe J.\n\nEl z-score divide por desviaciones ínfimas: una cobertura razonable en validación puede crecer cientos de veces. K conserva TODAS las coberturas de suelo en [0,1]; no recorta rendimientos. Las columnas constantes se eliminan solo en entrenamiento. S2 aprende unidades con soporte >=3 o >=5 dentro del fit y acumula las demás, incluidas ausentes, en Other. Other constante no puede adquirir un efecto propio: queda eliminado por falta de variación.\n\nS1 es primaria por soporte, escala estable, interpretación y diferenciación climática; no por rendimiento. S2 es la única sensibilidad predictiva. S3 suma coberturas por Grupo1 oficial, perdiendo grupos asociados y calificadores; S4 conserva identificadores ponderados, remanente y masa desconocida, y es diagnóstico secundario sin otro ajuste predictivo. No se armonizan automáticamente claves discrepantes de ediciones.\n\nElastic Net utiliza el mismo conjunto de 12 penalizaciones en todos los modelos K: alpha .001,.01,.1,1 y l1 .1,.5,.9; el nuevo .001 permite menor penalización coherente con suelo sin z-score. El clima J0 mantiene exactamente su grilla anterior. Políticas congeladas antes de entrenar K.2/K.3.\n\nResiduos: nunca se usan los OOF globales para supervisar el corrector; las particiones más profundas respetan los grupos. La selección interna evalúa predicción climática + eta × corrección completa. ETA incluye cero. Margen geográfico/MAE exploratorio .01 t/ha; no prueba de significancia.\n'
    (out/'report/k1_audit.md').write_text(text,encoding='utf-8')
    (ROOT/'documentation/k1_edaphological_redesign.md').write_text(text,encoding='utf-8')
    complete_k1_diagnostics(version)
    print('K.1 READY',diagnosis,flush=True)
    return out,proc,d,t,old,specs,splits,assignment

def not_bool(value): return not bool(value)

def complete_k1_diagnostics(version='v1'):
    """Additional target-free technical comparisons; no predictive grid changes."""
    out,proc=locations(version);d,t,old,specs,groups,units=load()
    splits,_,assignment=j.load_frozen_splits(t)
    scaling=[];representation=[];prediction_flags=[];dictrows=[]
    attrs=pd.read_parquet(j.IDATA/'soil_attributes.parquet')
    support=pd.read_csv(out/'tables/01_support_all.csv')
    allsupport=d[[ID,'climate_profile','Municipio']+units].merge(attrs,on=ID,validate='one_to_one')
    profiles_all={c:allsupport.loc[allsupport[c]>1e-12,'climate_profile'].nunique() for c in support.feature}
    municipalities_all={c:allsupport.loc[allsupport[c]>1e-12,'Municipio'].nunique() for c in support.feature}
    support['n_profiles_labelled']=support.n_profiles
    support['n_municipalities_labelled']=support.n_municipalities
    support['n_profiles_all']=support.feature.map(profiles_all)
    support['n_municipalities_all']=support.feature.map(municipalities_all)
    support.to_csv(out/'tables/01_support_all.csv',index=False)
    attrs=attrs.set_index(ID).loc[t[ID]].reset_index()
    ac=[c for c in attrs if c.startswith('soil_map_share')]
    s3=pd.read_parquet(proc/'s3_main_group_composition.parquet').set_index(ID).loc[d[ID]].reset_index()
    s3cols=[c for c in s3 if c!=ID]
    for protocol,rep,fold,tr,va,inner in splits:
        for family,frame,cols in [('units',t,units),('attributes',attrs,ac)]:
            flag=np.zeros(len(va),bool)
            for c in cols:
                a=frame.iloc[tr][c].to_numpy(float);b=frame.iloc[va][c].to_numpy(float);sd=a.std();mu=a.mean()
                # Policies are technical diagnostics, not alternative predictive experiments.
                strategies={'natural_fraction':b,'fixed_factor_2':2*b,'protected_z_sd_floor_0.1':(b-mu)/max(sd,.1)}
                strategies['conventional_z']=((b-mu)/sd if sd>1e-20 else np.full(len(b),np.nan))
                for policy,value in strategies.items():
                    scaling.append(dict(protocol=protocol,repeat=rep,fold=fold,family=family,feature=c,policy=policy,training_sd=sd,max_abs_validation=float(np.nanmax(abs(value))) if np.isfinite(value).any() else np.nan,n_abs_gt10=int((abs(value)>10).sum()),numerically_defined=bool(np.isfinite(value).all()),selected_for_prediction=policy=='natural_fraction'))
                flag|=abs(strategies['conventional_z'])>10
            for pid,extreme in zip(t.iloc[va][ID],flag):prediction_flags.append(dict(protocol=protocol,repeat=rep,fold=fold,family=family,ID_POLIGONO=pid,conventional_extreme_any_feature=bool(extreme)))
        allmatrices={'S1':d[groups].to_numpy(),'S3':s3[s3cols].to_numpy()}
        for threshold in [3,5]:
            encoder=StableFeatures(threshold).fit(t.iloc[tr][units])
            raw=encoder._raw(d[units]);allmatrices[f'S2_support_{threshold}']=raw.to_numpy()
        top=StableTop3().fit(t.iloc[tr][old['J6_RAIN_SOIL_TOP3'][7:]])
        allmatrices['S4']=top.transform(d[old['J6_RAIN_SOIL_TOP3'][7:]])
        for name,matrix in allmatrices.items():
            pairs=distinguished=0
            for _,positions in d.groupby('climate_profile').groups.items():
                for a,b in itertools.combinations(positions,2):
                    pairs+=1;distinguished+=np.sum(abs(matrix[a]-matrix[b]))/2>.05
            source='S1 group mentions, overlapping units' if name=='S1' else 'closed cartographic composition including Other/unknown/remainder'
            parcel_positions=pd.Series(np.arange(len(d)),index=d[ID])
            tr_global=parcel_positions.loc[t.iloc[tr][ID]].to_numpy()
            va_global=parcel_positions.loc[t.iloc[va][ID]].to_numpy()
            representation.append(dict(protocol=protocol,repeat=rep,fold=fold,representation=name,n_encoded_columns=matrix.shape[1],n_variable_training_columns=int((matrix[tr_global].var(axis=0)>1e-20).sum()),coverage_sum_min=float(matrix.sum(axis=1).min()),coverage_sum_max=float(matrix.sum(axis=1).max()),interpretation=source,n_pairs_same_climate=pairs,n_pairs_differentiated=distinguished,unknown_mass_validation_max=float(matrix[va_global,-2].max()) if name=='S4' else np.nan,remaining_mass_validation_max=float(matrix[va_global,-1].max()) if name=='S4' else np.nan))
    pd.DataFrame(scaling).to_csv(out/'tables/08_scaling_technical_comparison.csv',index=False)
    flags=pd.DataFrame(prediction_flags);flags.to_csv(out/'tables/08b_conventional_extrapolation_parcels.csv',index=False)
    flags.groupby(['protocol','family']).agg(n_heldout_predictions=('ID_POLIGONO','size'),fraction_affected=('conventional_extreme_any_feature','mean')).reset_index().to_csv(out/'tables/08c_conventional_extrapolation_rate.csv',index=False)
    pd.DataFrame(representation).to_csv(out/'tables/09_representations_by_training_fold.csv',index=False)
    # Effect of 125m map-boundary reserve on apparent differentiation (descriptive).
    reserve=[]
    for name,matrix in [('S1',d[groups].to_numpy()),('full_reference',d[units].to_numpy()),('S3',s3[s3cols].to_numpy())]:
        for _,positions in d.groupby('climate_profile').groups.items():
            for a,b in itertools.combinations(positions,2):
                reserve.append(dict(representation=name,at_least_one_boundary_reserve=bool(d.iloc[a].soil_assignment_reserve or d.iloc[b].soil_assignment_reserve),differentiated=bool(np.sum(abs(matrix[a]-matrix[b]))/2>.05)))
    pd.DataFrame(reserve).groupby(['representation','at_least_one_boundary_reserve']).agg(n_pairs=('differentiated','size'),n_differentiated=('differentiated','sum')).reset_index().to_csv(out/'tables/09b_boundary_differentiation.csv',index=False)
    for repname,cols,meaning in [('S1',groups,'coverage of units mentioning group; not physical group composition'),('S2',units+['soil_other_share'],'fold-supported unit coverage + pooled rare/absent/unknown unit mass'),('S3',s3cols,'unit coverage aggregated by official Grupo1; loses associates and qualifiers'),('S4',[f'soil_top{k}_{v}' for k in [1,2,3] for v in ['unit','share']]+['soil_remaining_share','soil_top3_unknown_share'],'weighted nominal units across ranks; missing nominal key routes to unknown; missing share fails explicitly')]:
        for c in cols:dictrows.append(dict(representation=repname,feature=c,meaning=meaning,units='nominal key' if c.endswith('_unit') else 'fraction of cartographic parcel coverage',role='primary predictive' if repname=='S1' else 'single standalone sensitivity' if repname=='S2' else 'descriptive only',fitted_scope='training fold only for support/vocabulary, source mapping fixed'))
    pd.DataFrame(dictrows).to_csv(out/'tables/00_representation_dictionary.csv',index=False)
    pd.DataFrame([dict(experiment=name,stage='residual correction' if name.startswith(('K5_','K6_','K7_','K8_')) else 'matched additive control' if name.startswith('KA_') else 'standalone',n_raw_columns=len(cols),columns=' | '.join(cols),estimator='training mean' if name=='K0_MEAN' else 'ElasticNet',soil_representation='S2 sensitivity' if name=='K3_SOIL_ONLY_ALT' else 'S1' if any(c in groups for c in cols) else 'none',preprocessing_fit_scope='each training fit',n_outer_folds=65) for name,cols in specs.items()]).to_csv(out/'tables/00_experimental_design.csv',index=False)
    pd.DataFrame([dict(ID_POLIGONO=pid,CONJUNTO=label,eligible_for_supervised_fit=pid in set(t[ID]),climate_profile=profile) for pid,label,profile in zip(d[ID],d.CONJUNTO,d.climate_profile)]).to_csv(out/'tables/00_id_label_gate.csv',index=False)
    sources=[j.IDATA/'soil_full_composition.parquet',j.IDATA/'soil_attributes.parquet',j.IDATA/'soil_intersections_long.parquet',j.IDATA/'soil_topn_per_parcel_3.parquet',j.IDATA/'integrated_diagnostic_197.parquet',ROOT/'data/processed/family_1/features/topography_basic_features.parquet',j.H/'splits/outer_and_inner_splits.csv',j.locations()[0]/'tables/02_oof_predictions.parquet',j.locations()[0]/'tables/03_registry.csv',ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet']
    sources += [ROOT/'scripts/data_uderstanding/tablas_agrocebada'/name for name in ['212_residual_architecture_optimization.py','211_second_residual_audit.py','210_champion_reconstruction.py']]
    pd.DataFrame([dict(path=str(p.relative_to(ROOT)),sha256=j.sha(p),use='read only; no extraction or historical refit') for p in sources]).to_csv(out/'tables/00_source_inventory.csv',index=False)
    qa=json.loads((out/'k1_gate.json').read_text())
    text='# K.1 — Comparaciones técnicas complementarias\n\n'+j.markdown_table(pd.DataFrame(representation).groupby('representation').agg(n_columns_min=('n_encoded_columns','min'),n_columns_max=('n_encoded_columns','max'),n_variable_min=('n_variable_training_columns','min'),n_variable_max=('n_variable_training_columns','max'),mean_pairs_distinguished=('n_pairs_differentiated','mean')).reset_index())+'\n\nLas matrices S2 de soporte global etiquetado son exclusivamente descriptivas. Cada pipeline reaprende soporte dentro de cada ajuste interno y externo. Las matrices dependientes del fold se describen en tabla09; el vocabulario S4 se aprende solo en entrenamiento y conserva masa desconocida/remanente. Clave nominal faltante con cuota conocida se asigna a desconocido; cuota faltante no se inventa, produce error explícito. Todas las cuotas reales de I están completas. S4 no agrega modelos predictivos.\n\nEscalamiento comparado sin Y: natural[0,1], factor fijo2[0,2], z convencional y z protegido con pisoSD=.1. Solo natural se usa predictivamente. Una política acotada no amplifica categorías poco frecuentes; un pisoSD evita división ínfima pero cambia penalización/interpretación. No se recortan las predicciones. Tabla08 compara los65folds y tabla08c reporta fracción de observaciones con alguna variable |z|>10, evitando sumar variables como si fueran parcelas independientes.\n\nJ5/J6: diferencia máxima real '+str(qa['max_abs_prediction_difference'])+'t/ha, cero artefactos reutilizados. Un único vector completo difiere de Top3 (cuarta unidad). Sus métricas coinciden por redondeo, no por identidad exacta.\n\nFuentes y hashes en tabla00_source_inventory; correspondencia ID uno a uno,138TRAIN/59PRED,53perfiles completos,43perfiles etiquetados. Arquitectura Champion consultada en sus artefactos: clima EN→residuo Sentinel histórico XGB→residuo topográfico Ridge; K conserva su convención de suma por etapas pero exige cross-fitting anidado explícito y no modifica Champion.\n'
    text+='\n\nS1 mantiene ocho grupos con12–101etiquetas y dos, RG/UM, con solo una. No se les atribuye transferencia independiente; columnas ausentes/constantes se eliminan dentro de entrenamiento. El umbral de diferencias L1/2>.05 es descriptivo y no representa distancia de variación total para los grupos S1 solapados.\n\nLos rangos Top3 sin clave ni cuota en I son ceros estructurales. Una clave presente con cuota faltante produce error, y una cuota positiva con clave faltante se conserva como masa desconocida. El cross-fitting no utiliza estas variables S4 como otro experimento predictivo.\n'
    (out/'report/k1_technical_comparison.md').write_text(text,encoding='utf-8')
    print('K.1 supplemental target-free diagnostics complete',flush=True)

class ClimateContexts:
    """Cache by ordered train IDs + exact CV; shared across corrector feature blocks."""
    def __init__(self,out,groups): self.out=out;self.groups=groups;self.audit=[]
    def tune(self,frame,protocol,cv):
        key=hashlib.sha256(json.dumps([protocol,frame[ID].tolist(),[[a.tolist(),b.tolist()] for a,b in cv]]).encode()).hexdigest()
        path=self.out/'climate_cache'/f'tune_{key}.joblib'
        if path.exists():return joblib.load(path)
        model=strict_fit(GridSearchCV(j.pipeline('J0_RAIN'),{'model__alpha':j.ALPHAS,'model__l1_ratio':j.L1},cv=cv,scoring='neg_root_mean_squared_error',n_jobs=1,error_score='raise'),frame[RAIN],frame[TARGET])
        pack=dict(model=model.best_estimator_,params=model.best_params_,inner_rmse=-model.best_score_,train_ids=frame[ID].tolist())
        atomic_dump(pack,path);return pack
    def context(self,frame,validation,protocol,cv,label):
        # Cross-fit climate; each held-out label is excluded even from parameter selection.
        pred=np.full(len(frame),np.nan);logs=[]
        for fold,(a,b) in enumerate(cv):
            fitting=frame.iloc[a]; held=frame.iloc[b]
            deeper=subcv(fitting,protocol,self.groups)
            pack=self.tune(fitting,protocol,deeper)
            assert not set(pack['train_ids'])&set(held[ID])
            pred[b]=pack['model'].predict(held[RAIN])
            logs.append(dict(context=label,protocol=protocol,fold=fold,fit_ids=json.dumps(fitting[ID].tolist()),heldout_ids=json.dumps(held[ID].tolist()),params=json.dumps(pack['params']),inner_folds=json.dumps([[fitting.iloc[x][ID].tolist(),fitting.iloc[y][ID].tolist()] for x,y in deeper])))
        if not np.isfinite(pred).all():raise ValueError('Incomplete cross-fitting')
        pack=self.tune(frame,protocol,cv)
        self.audit.extend(logs)
        return dict(residual=frame[TARGET].to_numpy()-pred,crossfit=pred,base=pack['model'].predict(validation[RAIN]),model=pack['model'],params=pack['params'])

def record_model(model,cols,key):
    f=model['features'];names=f.get_feature_names_out();beta=model['model'].coef_
    reg={**key,'n_effective_columns':len(names),'dropped_columns':json.dumps(np.array(f.names_)[~f.support_].tolist()),'n_nonzero_coefficients':int((abs(beta)>1e-10).sum())}
    coef=[{**key,'feature':c,'coefficient_model_scale':float(b),'coefficient_original_units':float(b/f.scale_[f.support_][k])} for k,(c,b) in enumerate(zip(names,beta))]
    return reg,coef

def precompute_residual_fold(version,index):
    """Independent numerical worker; fixed decisions, no model/feature search expansion."""
    out,_=locations(version);d,t,old,specs,groups,units=load()
    splits,_,assignments=j.load_frozen_splits(t)
    protocol,rep,fold,tr,va,inner=splits[index];label=f'{protocol}_{rep}_{fold}'
    r_specs=[(k,v) for k,v in specs.items() if k.startswith(('K5_','K6_','K7_','K8_'))]
    if all((out/'checkpoints'/f'{name}_{label}.joblib').exists() for name,cols in r_specs):return label
    a,b=t.iloc[tr],t.iloc[va];contextfile=out/'climate_cache'/f'contexts_{label}.joblib'
    if contextfile.exists():full,internal,logs=joblib.load(contextfile)
    else:
        contexts=ClimateContexts(out,assignments)
        full=contexts.context(a,b,protocol,inner,label+'_outer');internal=[]
        for k,(itr,iva) in enumerate(inner):
            aa,bb=a.iloc[itr],a.iloc[iva]
            internal.append(contexts.context(aa,bb,protocol,subcv(aa,protocol,assignments),label+f'_inner{k}'))
        logs=contexts.audit
        atomic_dump((full,internal,logs),contextfile)
    jp=pd.read_parquet(j.locations()[0]/'tables/02_oof_predictions.parquet')
    baseline=jp[(jp.experiment=='J0_RAIN')&(jp.protocol==protocol)&(jp['repeat']==rep)&(jp.fold==fold)].set_index(ID).loc[b[ID]]
    if not np.allclose(full['base'],baseline.y_pred,rtol=0,atol=1e-8):raise ValueError('Residual climate must reproduce J0')
    for name,cols in r_specs:
        checkpoint=out/'checkpoints'/f'{name}_{label}.joblib'
        if checkpoint.exists():continue
        key=dict(experiment=name,protocol=protocol,repeat=rep,fold=fold);candidates=[]
        for params in ParameterGrid(GRID):
            scores={eta:[] for eta in ETA}
            for (itr,iva),ctx in zip(inner,internal):
                model=strict_fit(pipeline().set_params(**params),a.iloc[itr][cols],ctx['residual'])
                correction=model.predict(a.iloc[iva][cols])
                for eta in ETA:scores[eta].append(metrics(a.iloc[iva][TARGET],ctx['base']+eta*correction)['RMSE'])
            for eta in ETA:candidates.append({**key,'params':json.dumps(params),'eta':eta,'inner_rmse':float(np.mean(scores[eta]))})
        best=min(candidates,key=lambda x:(x['inner_rmse'],x['eta'],-json.loads(x['params'])['model__alpha']))
        model=strict_fit(pipeline().set_params(**json.loads(best['params'])),a[cols],full['residual'])
        proposed=model.predict(b[cols]);correction=best['eta']*proposed;prediction=full['base']+correction
        reg,coef=record_model(model,cols,key)
        reg.update(params=best['params'],eta=best['eta'],inner_rmse=best['inner_rmse'],climate_params=json.dumps(full['params']),max_abs_proposed_correction=float(abs(proposed).max()),max_abs_applied_correction=float(abs(correction).max()))
        rows=[{**key,ID:pid,'y_true':float(y),'y_pred':float(p),'y_climate':float(base),'proposed_correction':float(raw),'correction':float(delta),'eta':best['eta'],'outer_model_id':f'{name}_{label}'} for pid,y,p,base,raw,delta in zip(b[ID],b[TARGET],prediction,full['base'],proposed,correction)]
        pack=dict(predictions=rows,registry=reg,coefficients=coef,tuning=candidates)
        atomic_dump(dict(climate=full['model'],corrector=model,eta=best['eta'],columns=cols,train_ids=a[ID].tolist()),out/'models'/f'{name}_{label}.joblib')
        atomic_dump(pack,checkpoint)
    print('RESIDUAL WORKER',index+1,'/65',label,flush=True)
    return label

def run(version='v1'):
    out,proc,d,t,old,specs,splits,assignment=audit(version)
    if not json.loads((out/'k1_gate.json').read_text())['ready_for_modeling']:raise ValueError('K.1 gate failed')
    predictions=[];registry=[];coefficients=[];searchrows=[];crossrows=[]
    jp=pd.read_parquet(j.locations()[0]/'tables/02_oof_predictions.parquet')
    # K.2 standalone first, followed by exact-variable additive controls.
    for name,cols in [(k,v) for k,v in specs.items() if not k.startswith(('K5_','K6_','K7_','K8_'))]:
        print('START',name,flush=True)
        for idx,(protocol,rep,fold,tr,va,inner) in enumerate(splits):
            key=dict(experiment=name,protocol=protocol,repeat=rep,fold=fold)
            checkpoint=out/'checkpoints'/f'{name}_{protocol}_{rep}_{fold}.joblib'
            if checkpoint.exists():pack=joblib.load(checkpoint)
            else:
                a,b=t.iloc[tr],t.iloc[va]
                if name=='K0_MEAN':
                    prediction=np.repeat(a[TARGET].mean(),len(b));model=dict(mean=float(a[TARGET].mean()),train_ids=a[ID].tolist())
                    reg={**key,'params':'training_mean','n_effective_columns':0};coef=[];tuning=[]
                else:
                    grid=dict(GRID)
                    if name=='K3_SOIL_ONLY_ALT':grid['features__min_support']=[3,5]
                    search=strict_fit(GridSearchCV(pipeline(),grid,cv=inner,scoring='neg_root_mean_squared_error',n_jobs=1,error_score='raise'),a[cols],a[TARGET])
                    model=search.best_estimator_;prediction=model.predict(b[cols]);reg,coef=record_model(model,cols,key)
                    reg.update(params=json.dumps(search.best_params_),inner_rmse=-search.best_score_)
                    tuning=[{**key,'params':json.dumps(p),'inner_rmse':float(-s)} for p,s in zip(search.cv_results_['params'],search.cv_results_['mean_test_score'])]
                rows=[{**key,ID:pid,'y_true':float(y),'y_pred':float(p),'outer_model_id':f'{name}_{protocol}_{rep}_{fold}'} for pid,y,p in zip(b[ID],b[TARGET],prediction)]
                pack=dict(predictions=rows,registry=reg,coefficients=coef,tuning=tuning)
                joblib.dump(model,out/'models'/f'{name}_{protocol}_{rep}_{fold}.joblib',compress=3);joblib.dump(pack,checkpoint,compress=3)
            predictions.extend(pack['predictions']);registry.append(pack['registry']);coefficients.extend(pack['coefficients']);searchrows.extend(pack['tuning'])
            if (idx+1)%10==0 or idx==64:print(name,idx+1,'/65',flush=True)
    pd.DataFrame(predictions).to_parquet(out/'tables/10_k2_oof_predictions.parquet',index=False)
    print('K.2 complete; starting nested residual contexts',flush=True)
    workers=int(os.environ.get('K_FOLD_WORKERS','3'))
    joblib.Parallel(n_jobs=workers,backend='loky',inner_max_num_threads=1)(joblib.delayed(precompute_residual_fold)(version,index) for index in range(len(splits)))
    residual_specs=[(k,v) for k,v in specs.items() if k.startswith(('K5_','K6_','K7_','K8_'))]
    for idx,(protocol,rep,fold,tr,va,inner) in enumerate(splits):
        a,b=t.iloc[tr],t.iloc[va];foldlabel=f'{protocol}_{rep}_{fold}'
        contextfile=out/'climate_cache'/f'contexts_{foldlabel}.joblib'
        full,internal,logs=joblib.load(contextfile)
        baseline=jp[(jp.experiment=='J0_RAIN')&(jp.protocol==protocol)&(jp['repeat']==rep)&(jp.fold==fold)].set_index(ID).loc[b[ID]]
        if not np.allclose(full['base'],baseline.y_pred,rtol=0,atol=1e-8):raise ValueError('Residual first stage does not exactly reproduce J0')
        for pid,y,p in zip(a[ID],a[TARGET],full['crossfit']):crossrows.append(dict(protocol=protocol,repeat=rep,fold=fold,ID_POLIGONO=pid,y_true=y,y_crossfit=p,residual=y-p,role='outer-train cross-fitted target; never full-dataset OOF'))
        for name,cols in residual_specs:
            key=dict(experiment=name,protocol=protocol,repeat=rep,fold=fold);checkpoint=out/'checkpoints'/f'{name}_{foldlabel}.joblib'
            pack=joblib.load(checkpoint)
            predictions.extend(pack['predictions']);registry.append(pack['registry']);coefficients.extend(pack['coefficients']);searchrows.extend(pack['tuning'])
        print('RESIDUAL',idx+1,'/65',foldlabel,flush=True)
    p=pd.DataFrame(predictions)
    p.to_parquet(out/'tables/11_k_oof_predictions.parquet',index=False)
    p.to_csv(out/'tables/11_k_oof_predictions.csv',index=False)
    pd.DataFrame(registry).to_csv(out/'tables/12_registry.csv',index=False)
    pd.DataFrame(coefficients).to_csv(out/'tables/13_coefficients.csv',index=False)
    pd.DataFrame(searchrows).to_csv(out/'tables/14_inner_search.csv',index=False)
    pd.DataFrame(crossrows).to_parquet(out/'tables/15_outer_train_crossfit_residuals.parquet',index=False)
    logs=[]
    for protocol,rep,fold,tr,va,inner in splits:
        logs.extend(joblib.load(out/'climate_cache'/f'contexts_{protocol}_{rep}_{fold}.joblib')[2])
    pd.DataFrame(logs).to_csv(out/'tables/16_crossfit_provenance.csv',index=False)
    analyze(out,d,p)
    previous=json.loads((out/'protected_inputs.json').read_text(encoding='utf-8'))
    if previous!=protection():raise ValueError('Historical protected files changed')
    artifacts=[x for x in out.rglob('*') if x.is_file() and not any(z in x.parts for z in ['checkpoints','climate_cache']) and x.name!='manifest.json']+list(proc.glob('*.parquet'))
    sources=[Path(__file__),ROOT/'scripts/modeling/327_k_edaphological_stability.py',ROOT/'scripts/modeling/328_k_standalone_residual_modeling.py',ROOT/'tests/test_k_geographic_edaphological.py']
    (out/'manifest.json').write_text(json.dumps(dict(status='complete',section='K',previous_results_unchanged=True,hidden_y_used=False,final_59_predictions_generated=False,n_labelled=138,n_unlabelled=59,n_outer=65,n_experiments=len(specs),saved_outer_models=65*len(specs),n_oof_predictions=len(p),protected_file_count=len(previous),fold_workers=workers,python=platform.python_version(),packages={name:importlib.metadata.version(name) for name in ['numpy','pandas','scikit-learn','joblib','scipy']},source_hashes={str(x.relative_to(ROOT)):j.sha(x) for x in sources},artifacts={str(x.relative_to(ROOT)):j.sha(x) for x in artifacts}),indent=2),encoding='utf-8')
    print('K COMPLETE; historical files unchanged',flush=True)

def analyze(out,d,p=None):
    if p is None:p=pd.read_parquet(out/'tables/11_k_oof_predictions.parquet')
    controls=pd.read_parquet(j.locations()[0]/'tables/02_oof_predictions.parquet')
    controls=controls[controls.experiment.isin(['J0_RAIN','J1_RAIN_SLOPE','J2_RAIN_TOPO','J3_RAIN_SOIL_GROUP','J4_RAIN_TOPO_SOIL'])]
    p=pd.concat([p,controls],ignore_index=True)
    comparison,folds,reps=summarize(p,out)
    p=p.merge(d,on=ID,validate='many_to_one');p['error']=p.y_pred-p.y_true;p['abs_error']=abs(p.error)
    base=p[p.experiment.eq('J0_RAIN')][[ID,'protocol','repeat','fold','error','abs_error']].rename(columns={'error':'baseline_error','abs_error':'baseline_abs_error'})
    p=p.merge(base,on=[ID,'protocol','repeat','fold'],validate='many_to_one');p['absolute_error_improvement']=p.baseline_abs_error-p.abs_error
    p.to_parquet(out/'tables/20_errors_with_geography.parquet',index=False)
    contrasts=[('K0_MEAN',x) for x in ['K1_SLOPE_ONLY','K2_TOPO_ONLY','K3_SOIL_ONLY','K4_TOPO_SOIL','K3_SOIL_ONLY_ALT']]
    contrasts += [('J0_RAIN',x) for x in comparison.experiment.unique() if x!='J0_RAIN']
    contrasts += [('KA_RAIN_SLOPE_MATCHED','K5_RAIN_RESID_SLOPE'),('KA_RAIN_TOPO_MATCHED','K6_RAIN_RESID_TOPO'),('J1_RAIN_SLOPE','K5_RAIN_RESID_SLOPE'),('J2_RAIN_TOPO','K6_RAIN_RESID_TOPO'),('KA_RAIN_SOIL_STABLE','K7_RAIN_RESID_SOIL'),('KA_RAIN_TOPO_SOIL_STABLE','K8_RAIN_RESID_TOPO_SOIL'),('J3_RAIN_SOIL_GROUP','KA_RAIN_SOIL_STABLE'),('J4_RAIN_TOPO_SOIL','KA_RAIN_TOPO_SOIL_STABLE'),('K1_SLOPE_ONLY','K2_TOPO_ONLY'),('K3_SOIL_ONLY','K4_TOPO_SOIL'),('K2_TOPO_ONLY','K4_TOPO_SOIL'),('K3_SOIL_ONLY','K3_SOIL_ONLY_ALT')]
    paired=[]
    for baseline,candidate in contrasts:
        for scope,table,keys in [('repetition',reps,['protocol','repeat']),('fold',folds,['protocol','repeat','fold'])]:
            z=table[table.experiment.eq(baseline)].merge(table[table.experiment.eq(candidate)],on=keys,suffixes=('_base','_candidate'),validate='one_to_one')
            for _,r in z.iterrows():paired.append(dict(scope=scope,baseline=baseline,candidate=candidate,**{k:r[k] for k in keys},delta_RMSE=r.RMSE_base-r.RMSE_candidate,delta_MAE=r.MAE_base-r.MAE_candidate))
    paired=pd.DataFrame(paired);paired.to_csv(out/'tables/21_paired_comparisons.csv',index=False)
    paired.groupby(['scope','protocol','baseline','candidate']).agg(delta_RMSE=('delta_RMSE','mean'),sd_delta_RMSE=('delta_RMSE','std'),delta_MAE=('delta_MAE','mean'),fraction_improving=('delta_RMSE',lambda x:(x>1e-10).mean())).reset_index().to_csv(out/'tables/22_paired_summary.csv',index=False)
    subgroups=[];profiles=[];same=[];pairs=[];residual=[]
    for (protocol,name,rep),z in p.groupby(['protocol','experiment','repeat']):
        masks={'all':np.ones(len(z),bool),'Chignahuapan':z.Municipio.eq('Chignahuapan'),'other_municipalities':~z.Municipio.eq('Chignahuapan'),'low_lt3':z.y_true<3,'high_gt5':z.y_true>5,'middle_3_5':z.y_true.between(3,5),'source_key_discrepancy':z.soil_share_key_not_found_in_E1402_text>0,'source_key_agrees':z.soil_share_key_not_found_in_E1402_text==0}
        for radius in [50,125,250]:
            masks[f'near_boundary_{radius}m']=z[f'soil_boundary_buffer_{radius}m_share']>0
            masks[f'away_boundary_{radius}m']=~masks[f'near_boundary_{radius}m']
        for value in z.Estado.unique():masks['state_'+str(value)]=z.Estado.eq(value)
        for value in z.Municipio.unique():masks['municipality_'+str(value)]=z.Municipio.eq(value)
        for k in ['low_lt3','high_gt5','middle_3_5']:masks['Chignahuapan_'+k]=masks['Chignahuapan']&masks[k]
        # Rare support stratification defined separately for each training model below.
        for label,mask in masks.items():
            q=z[mask]
            if len(q):subgroups.append(dict(protocol=protocol,experiment=name,repeat=rep,stratum=label,n=len(q),absolute_error_improvement=q.absolute_error_improvement.mean(),**metrics(q.y_true,q.y_pred)))
        if name.startswith(('K5_','K6_','K7_','K8_')):
            for label,mask in masks.items():
                q=z[mask]
                if len(q):residual.append(dict(protocol=protocol,experiment=name,repeat=rep,stratum=label,n=len(q),mean_correction=q.correction.mean(),mean_abs_correction=q.correction.abs().mean(),sd_correction=q.correction.std(),max_abs_correction=q.correction.abs().max(),max_abs_proposed=q.proposed_correction.abs().max(),n_negative_predictions=int((q.y_pred<0).sum()),correlation_residual_applied=q.baseline_error.mul(-1).corr(q.correction) if q.correction.std()>1e-12 else np.nan,correlation_residual_proposed=q.baseline_error.mul(-1).corr(q.proposed_correction) if q.proposed_correction.std()>1e-12 else np.nan,absolute_bias_improvement=abs(q.baseline_error.mean())-abs(q.error.mean()),absolute_error_improvement=q.absolute_error_improvement.mean()))
        for profile,q in z.groupby('climate_profile'):
            if len(q)<2:continue
            profiles.append(dict(protocol=protocol,experiment=name,repeat=rep,profile=profile,n=len(q),n_models=q.outer_model_id.nunique(),y_sd=q.y_true.std(),prediction_sd=q.y_pred.std(),absolute_error_improvement=q.absolute_error_improvement.mean(),Municipio=' | '.join(sorted(q.Municipio.unique())),**metrics(q.y_true,q.y_pred)))
            for model,qq in q.groupby('outer_model_id'):
                if len(qq)<2:continue
                corr=qq.correction.std() if name.startswith(('K5_','K6_','K7_','K8_')) else np.nan
                same.append(dict(protocol=protocol,experiment=name,repeat=rep,profile=profile,outer_model_id=model,n=len(qq),y_sd=qq.y_true.std(),prediction_sd=qq.y_pred.std(),climate_sd=qq.y_climate.std() if 'y_climate' in qq and qq.y_climate.notna().all() else np.nan,correction_sd=corr,absolute_error_improvement=qq.absolute_error_improvement.mean(),artificial_differentiation=bool(qq.y_pred.std()>1e-8 and qq.absolute_error_improvement.mean()<=0),**metrics(qq.y_true,qq.y_pred)))
                for aa,bb in itertools.combinations(qq.itertuples(),2):
                    pairs.append(dict(protocol=protocol,experiment=name,repeat=rep,profile=profile,outer_model_id=model,ID_a=getattr(aa,ID),ID_b=getattr(bb,ID),y_difference=aa.y_true-bb.y_true,prediction_difference=aa.y_pred-bb.y_pred,pair_error=(aa.y_pred-bb.y_pred)-(aa.y_true-bb.y_true),slope_difference=aa.slope_degrees-bb.slope_degrees,altitude_difference=aa.altitude_m-bb.altitude_m,soil_group_L1_half=float(sum(abs(getattr(aa,c)-getattr(bb,c)) for c in d if c.startswith('soil_map_share_mentions_group_'))/2),Municipio_a=aa.Municipio,Municipio_b=bb.Municipio))
    pd.DataFrame(subgroups).to_csv(out/'tables/23_subgroups_repeat.csv',index=False)
    sg=pd.DataFrame(subgroups).groupby(['protocol','experiment','stratum']).agg(n=('n','first'),RMSE=('RMSE','mean'),MAE=('MAE','mean'),R2=('R2','mean'),bias=('bias_pred_minus_y','mean'),absolute_error_improvement=('absolute_error_improvement','mean')).reset_index();sg.to_csv(out/'tables/24_subgroup_summary.csv',index=False)
    pd.DataFrame(residual).to_csv(out/'tables/25_residual_diagnostics_oof.csv',index=False)
    pd.DataFrame(profiles).to_csv(out/'tables/26_profile_diagnostics.csv',index=False)
    pd.DataFrame(same).to_csv(out/'tables/27_same_model_profile_diagnostics.csv',index=False)
    pair=pd.DataFrame(pairs);pair.to_parquet(out/'tables/28_same_model_pair_differences.parquet',index=False)
    pm=pair.groupby(['protocol','experiment','repeat']).pair_error.agg(pair_RMSE=lambda x:np.sqrt(np.mean(x*x)),pair_MAE=lambda x:abs(x).mean(),n_pairs='size').reset_index();pm.to_csv(out/'tables/29_same_model_pair_metrics.csv',index=False)
    coef=pd.read_csv(out/'tables/13_coefficients.csv')
    coef.groupby(['experiment','protocol','feature']).agg(n_fits_present=('fold','size'),mean_beta=('coefficient_original_units','mean'),sd_beta=('coefficient_original_units','std'),positive_fraction=('coefficient_original_units',lambda x:(x>1e-10).mean()),negative_fraction=('coefficient_original_units',lambda x:(x<-1e-10).mean())).reset_index().to_csv(out/'tables/30_coefficient_stability_present_fits.csv',index=False)
    # Stored benchmark already audited for ID/fold compatibility in J; recover read-only.
    benchmark=pd.read_csv(j.locations()[0]/'tables/23_contextual_benchmark_summary.csv')
    benchmark.to_csv(out/'tables/31_contextual_benchmarks.csv',index=False)
    support_diagnostics(out,d,p)
    report(out,comparison,sg,pm,benchmark)
    plots(out,p,comparison,sg)
    final_diagnostics(out)

def support_diagnostics(out,d,p):
    _,t,_,_,groups,units=load();rows=[];ext=[]
    for protocol,rep,fold,tr,va,inner in j.load_frozen_splits(t)[0]:
        rare=[c for c in units if (t.iloc[tr][c]>1e-12).sum()<5]
        q=p[(p.protocol==protocol)&(p['repeat']==rep)&(p.fold==fold)].copy()
        q['rare_unit_share']=q[rare].sum(axis=1)
        for name,z in q.groupby('experiment'):
            for label,mask in [('rare_mass_gt_5pct',z.rare_unit_share>.05),('rare_mass_le_5pct',z.rare_unit_share<=.05)]:
                zz=z[mask]
                if len(zz):rows.append(dict(protocol=protocol,repeat=rep,fold=fold,experiment=name,stratum=label,n=len(zz),**metrics(zz.y_true,zz.y_pred)))
            if name.startswith('J'):continue
            stored=joblib.load(out/'models'/f'{name}_{protocol}_{rep}_{fold}.joblib')
            if name=='K0_MEAN':continue
            model=stored['corrector'] if name.startswith(('K5_','K6_','K7_','K8_')) else stored
            cols=stored['columns'] if isinstance(stored,dict) else load()[3][name]
            transformed=model[:-1].transform(t.iloc[va][cols]);names=model['features'].get_feature_names_out()
            for k,c in enumerate(names):
                if c.startswith('soil'):
                    assert abs(transformed[:,k]).max()<=1+1e-8
                    ext.append(dict(protocol=protocol,repeat=rep,fold=fold,experiment=name,feature=c,max_abs_transformed=float(abs(transformed[:,k]).max()),max_abs_contribution=float(abs(transformed[:,k]*model['model'].coef_[k]).max())))
    pd.DataFrame(rows).to_csv(out/'tables/32_errors_by_training_support.csv',index=False)
    pd.DataFrame(ext).to_csv(out/'tables/33_stable_soil_transformation_screen.csv',index=False)

def final_diagnostics(out=None):
    """Complete interpretation and decisions from frozen out-of-sample results."""
    if out is None:out=locations()[0]
    d,t,old,specs,groups,units=load()
    c=pd.read_csv(out/'tables/40_model_comparison.csv')
    reps=pd.read_csv(out/'tables/42_repetition_metrics.csv')
    p=pd.read_parquet(out/'tables/20_errors_with_geography.parquet')
    # Independently verify cached benchmarks against K baseline IDs, folds and Y.
    anchor=p[(p.experiment=='J0_RAIN')&(p.protocol=='random')][[ID,'protocol','repeat','fold','y_true']]
    champion=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet')
    champion=champion[champion.architecture.eq('A_CURRENT_CH_H_T')].rename(columns={'architecture':'experiment'});champion['protocol']='random'
    current=pd.read_parquet(j.H/'tables/31_oof_individual.parquet')
    current=current[(current.experiment=='H8_CLIMATE_CURRENT_ORIGINAL')&(current.protocol=='random')]
    benchmarks=[]
    for name,z in [('Champion',champion),('Climate Current',current)]:
        check=z.merge(anchor,on=[ID,'protocol','repeat','fold'],suffixes=('_cached','_K'),validate='one_to_one')
        if len(check)!=1380 or len(z)!=1380 or not np.allclose(check.y_true_cached,check.y_true_K,atol=1e-12,rtol=0):raise ValueError('Incompatible contextual benchmark')
        for repeat,q in check.groupby('repeat'):
            benchmarks.append(dict(experiment=name,protocol='random',repeat=repeat,n=len(q),**metrics(q.y_true_K,q.y_pred)))
    bb=pd.DataFrame(benchmarks);bb.to_csv(out/'tables/45_verified_contextual_benchmark_repeat.csv',index=False)
    bb.groupby('experiment')[['RMSE','MAE','R2','bias_pred_minus_y']].mean().to_csv(out/'tables/46_verified_contextual_benchmark_summary.csv')
    pair=pd.read_parquet(out/'tables/28_same_model_pair_differences.parquet')
    # Correlation of pair DIFFERENCES, not full-sample training fits.
    pairsummary=[]
    for (protocol,name,rep),z in pair.groupby(['protocol','experiment','repeat']):
        for scope,q in [('all',z),('Chignahuapan',z[(z.Municipio_a=='Chignahuapan')&(z.Municipio_b=='Chignahuapan')]),('soil_L1_gt_5pp',z[z.soil_group_L1_half>.05]),('soil_L1_le_5pp',z[z.soil_group_L1_half<=.05])]:
            if not len(q):continue
            pairsummary.append(dict(protocol=protocol,experiment=name,repeat=rep,scope=scope,n_pairs=len(q),pair_RMSE=float(np.sqrt(np.mean(q.pair_error**2))),pair_MAE=float(q.pair_error.abs().mean()),correlation_difference_y=q.y_difference.corr(q.prediction_difference) if q.y_difference.std()>1e-12 and q.prediction_difference.std()>1e-12 else np.nan,correlation_difference_slope=q.slope_difference.corr(q.prediction_difference) if q.slope_difference.std()>1e-12 and q.prediction_difference.std()>1e-12 else np.nan))
    pd.DataFrame(pairsummary).to_csv(out/'tables/35_pair_diagnostics_local_soil.csv',index=False)
    # Coefficient drop = zero in predictive model, while pooled units retain Other effects.
    co=pd.read_csv(out/'tables/13_coefficients.csv');reg=pd.read_csv(out/'tables/12_registry.csv')
    complete=[]
    for name,z in reg.groupby('experiment'):
        if name=='K0_MEAN':continue
        names=sorted(set(co[co.experiment==name].feature))
        for row in z.itertuples():
            values=co[(co.experiment==name)&(co.protocol==row.protocol)&(co['repeat']==row.repeat)&(co.fold==row.fold)].set_index('feature').coefficient_original_units
            eta=float(row.eta) if name.startswith(('K5_','K6_','K7_','K8_')) else 1.
            for feature in names:complete.append(dict(experiment=name,protocol=row.protocol,repeat=row.repeat,fold=row.fold,feature=feature,coefficient=float(values.get(feature,0)),applied_coefficient=float(values.get(feature,0))*eta,eta=eta,column_available=feature in values.index))
    cc=pd.DataFrame(complete);cc.to_csv(out/'tables/36_coefficients_including_dropped_zero.csv',index=False)
    cc.groupby(['experiment','protocol','feature']).agg(n_outer_fits=('coefficient','size'),fraction_available=('column_available','mean'),mean_beta=('coefficient','mean'),sd_beta=('coefficient','std'),positive_fraction=('coefficient',lambda x:(x>1e-10).mean()),negative_fraction=('coefficient',lambda x:(x<-1e-10).mean())).reset_index().to_csv(out/'tables/37_coefficient_stability_all_fits.csv',index=False)
    eta=reg[reg.experiment.str.startswith(('K5_','K6_','K7_','K8_'))]
    eta.groupby(['experiment','protocol','eta']).size().rename('n_outer_folds').reset_index().to_csv(out/'tables/38_eta_selections.csv',index=False)
    outliers=p.groupby(['experiment','protocol']).agg(n_predictions=('y_pred','size'),n_negative=('y_pred',lambda x:(x<0).sum()),min_prediction=('y_pred','min'),max_prediction=('y_pred','max'),max_abs_error=('error',lambda x:abs(x).max()),min_error=('error','min'),max_error=('error','max')).reset_index()
    outliers.to_csv(out/'tables/39_unclipped_prediction_extremes.csv',index=False)
    # Target-free correlations show redundancy descriptively, not conditional causality.
    t[RAIN+TOPO+groups].corr().to_csv(out/'tables/43_predictor_correlations_train_descriptive.csv')
    metrics_by_name=c.set_index(['experiment','protocol'])
    def rmse(name,protocol):return metrics_by_name.loc[(name,protocol),'RMSE_mean']
    def mae(name,protocol):return metrics_by_name.loc[(name,protocol),'MAE_mean']
    def row(name):return '| '+name+' | '+' | '.join(f'{rmse(name,pr):.4f}' for pr in ['random','climate_profile','municipality','spatial'])+' |'
    lines=['# K — Resumen para decisiones','', 'RMSE (t/ha), OOF completos por repetición; menor es mejor.','', '| Modelo | Aleatorio | Perfil | Municipal | Espacial |','| --- | --- | --- | --- | --- |']
    ordered=['K0_MEAN','K1_SLOPE_ONLY','K2_TOPO_ONLY','K3_SOIL_ONLY','K3_SOIL_ONLY_ALT','K4_TOPO_SOIL','J0_RAIN','J1_RAIN_SLOPE','KA_RAIN_SLOPE_MATCHED','KA_RAIN_TOPO_MATCHED','KA_RAIN_SOIL_STABLE','KA_RAIN_TOPO_SOIL_STABLE','K5_RAIN_RESID_SLOPE','K6_RAIN_RESID_TOPO','K7_RAIN_RESID_SOIL','K8_RAIN_RESID_TOPO_SOIL']
    lines += [row(name) for name in ordered]
    lines += ['', 'La pendiente/topografía y el suelo como modelos independientes se valoran frente a la media K0. La comparación contra lluvia mide otra pregunta; un buen modelo independiente no garantiza señal incremental.', '']
    for name in ['K1_SLOPE_ONLY','K2_TOPO_ONLY','K3_SOIL_ONLY','K4_TOPO_SOIL','K3_SOIL_ONLY_ALT']:
        gains=[rmse('K0_MEAN',pr)-rmse(name,pr) for pr in ['random','climate_profile','municipality','spatial']]
        lines.append(f'{name}: mejora RMSE frente a K0 aleatoria/perfil/municipal/espacial = '+', '.join(f'{v:+.4f}' for v in gains)+' t/ha. Esto describe capacidad predictiva propia en estos protocolos, no causalidad.')
    lines += ['', 'La comparación de arquitectura usa controles KA con idénticas variables, escalas, penalizaciones y folds. J permanece como referencia histórica.','']
    matched={'K5_RAIN_RESID_SLOPE':'KA_RAIN_SLOPE_MATCHED','K6_RAIN_RESID_TOPO':'KA_RAIN_TOPO_MATCHED','K7_RAIN_RESID_SOIL':'KA_RAIN_SOIL_STABLE','K8_RAIN_RESID_TOPO_SOIL':'KA_RAIN_TOPO_SOIL_STABLE'}
    decisions=[]
    for name,additive in matched.items():
        gains=[rmse('J0_RAIN',pr)-rmse(name,pr) for pr in ['random','climate_profile','municipality','spatial']]
        arch=[rmse(additive,pr)-rmse(name,pr) for pr in ['random','climate_profile','municipality','spatial']]
        r=reps[(reps.experiment==name)&(reps.protocol=='random')].merge(reps[(reps.experiment=='J0_RAIN')&(reps.protocol=='random')],on=['protocol','repeat'],suffixes=('_candidate','_base'))
        fraction=float((r.RMSE_candidate<r.RMSE_base-1e-10).mean());magain=mae('J0_RAIN','random')-mae(name,'random')
        geographic=min(gains[1:])>=-.01
        mae_gains=[mae('J0_RAIN',pr)-mae(name,pr) for pr in ['random','climate_profile','municipality','spatial']]
        rmse_and_random_mae=bool(gains[0]>0 and magain>=-.01 and fraction>=.8 and geographic)
        decisions.append(dict(experiment=name,random_gain=gains[0],random_mae_gain=magain,random_fraction_repeats_improving=fraction,geographic_RMSE_noninferiority=geographic,random_consistency=fraction>=.8,passes_RMSE_and_random_MAE_screen=rmse_and_random_mae,worst_protocol_MAE_improvement=min(mae_gains),passes_all_protocol_MAE_margin=bool(min(mae_gains)>=-.01),passes_all_protocol_metric_screen=bool(rmse_and_random_mae and min(mae_gains)>=-.01),note='all protocol MAE margin .01 from frozen policy; support/extreme/intraprofile diagnostics also mandatory; not Champion replacement'))
        lines.append(f'{name}: mejora sobre lluvia (aleatorio/perfil/municipal/espacial) '+', '.join(f'{v:+.4f}' for v in gains)+f' t/ha; mejora MAE aleatoria {magain:+.4f}; {fraction:.0%} de repeticiones mejora RMSE. Frente al control aditivo comparable: '+', '.join(f'{v:+.4f}' for v in arch)+'.')
    pd.DataFrame(decisions).to_csv(out/'tables/44_residual_decision_metrics.csv',index=False)
    lines += ['', 'El control eta=0 reproduce lluvia en cada fold. Una menor degradación que J no equivale a mejora sobre lluvia; el ajuste interno puede rechazar una corrección, pero no garantiza transferencia externa.', '', 'La inestabilidad numérica de coberturas estandarizadas se eliminó por construcción: todas las cuotas de suelo utilizadas quedan entre0y1. Permanecen falta de soporte y cambios geográficos: RG/UM tienen una etiqueta cada uno; las unidades raras se agrupan solo en S2 y la cartografía mantiene reservas1:250000. No se recortan rendimientos ni se eliminan parcelas.', '', 'Intraperfil y Chignahuapan: tablas27–29/35 usan parejas evaluadas por un mismo modelo externo; Chignahuapan es un subconjunto de71 etiquetas y no constituye validación independiente. Tabla25 mide correlaciones de correcciones fuera de muestra. Aumentar dispersión sin disminuir errores no justifica integración.', '', 'Las comparaciones entre10 repeticiones y65 folds son descriptivas y correlacionadas. El margen .01t/ha de deterioro geográfico/MAE es exploratorio; no significancia estadística. No se modifica Champion ni se entrenan las59 parcelas sin etiqueta.', '', 'Próximo paso justificable si queda señal local pero falla transferencia: evaluar en etiquetas de regiones externas y estudiar soporte temático de clases. No se abren nuevas arquitecturas ni ensayos retrospectivos dentro de K.']
    lines += ['', 'Lectura de los resultados de esta versión:', '',
        f'Pendiente sola aporta una señal modesta frente a la media: RMSE aleatorio {rmse("K1_SLOPE_ONLY","random"):.4f} frente a {rmse("K0_MEAN","random"):.4f}. La altitud mejora ligeramente ese resultado aleatorio, pero empeora la transferencia espacial; no fortalece de manera consistente el bloque topográfico.', '',
        f'El suelo tiene asociación predictiva propia: S1 logra {rmse("K3_SOIL_ONLY","random"):.4f} y S2 {rmse("K3_SOIL_ONLY_ALT","random"):.4f} en aleatorio. S2 conserva unidades más específicas y predice mejor dentro de los datos disponibles, pero su RMSE espacial es {rmse("K3_SOIL_ONLY_ALT","spatial"):.4f}, peor que la media {rmse("K0_MEAN","spatial"):.4f}. No se cambia retrospectivamente la representación primaria para favorecer ese resultado.', '',
        'Combinar topografía y S1 mejora a cada bloque independiente en aleatorio y espacio; aun así, lluvia sola supera a estos modelos. Los controles aditivos y residuales de suelo no confirman una mejora incremental estable. Esto es compatible con redundancia regional con clima y con soporte insuficiente; no prueba irrelevancia agronómica del suelo.', '',
        'K5, pendiente residual, es la candidata más equilibrada entre los correctores: mejora RMSE aleatorio, por perfil y espacial, y queda casi igual en municipal. Su MAE aleatorio empeora ligeramente. El control aditivo de pendiente conserva mejores resultados por perfil y municipio; la corrección residual ofrece una transferencia espacial mucho menos deteriorada. No hay una arquitectura que gane todos los objetivos.', '',
        'Los dos estimadores Elastic Net siguen siendo lineales: sumar clima y corrector lineal no crea por sí mismo capacidad no lineal. Las diferencias provienen del ajuste por etapas, los objetivos cruzados, la regularización y eta; no de variables adicionales.', '',
        'La señal favorable de K5 es pequeña y exploratoria. Justifica conservarla como candidata de RMSE para validación externa, sin declarar una mejora confirmada ni reemplazar Champion. No cumple todos los criterios: el MAE por perfil aumenta .0114t/ha y el municipal .0122t/ha, por encima del margen exploratorio .01. K6 excede ligeramente el margen municipal de RMSE; K7/K8 no aportan una mejora geográficamente consistente. Ningún corrector cumple la pantalla completa de RMSE y MAE en todos los protocolos.', '',
        'En Chignahuapan K5 reduce RMSE aleatorio .5764→.5685, pero eleva MAE .3896→.3969; por perfil, MAE .3863→.4092 y en espacial .3809→.4007. El beneficio en errores grandes no es una mejora uniforme por parcela. Las71 etiquetas locales pertenecen a los mismos OOF, no a una prueba independiente.', '',
        'La reserva por discrepancia de clave de edición solo tiene una etiqueta: no permite inferencias firmes. Los buffers cartográficos son sensibilidades descriptivas, no errores probabilísticos de localización. Coeficientes residuales propuestos y aplicados (multiplicados por eta) se distinguen en tabla36.']
    text='\n'.join(lines)+'\n'
    (out/'report/decision_summary.md').write_text(text,encoding='utf-8')
    (ROOT/'documentation/k_decision_summary.md').write_text(text,encoding='utf-8')
    main=out/'report/k_modeling.md'
    textmain=main.read_text(encoding='utf-8').split('\n## Conclusiones de los resultados congelados')[0]
    # Replace outdated caveat now that all continuous-block controls share K's grid.
    textmain=textmain.replace('J1/J2 usan la misma estandarización continua; K agrega alpha .001 por coherencia con suelo sin z-score, por lo que diferencias minúsculas contra J no aíslan exclusivamente arquitectura.', 'KA_RAIN_SLOPE_MATCHED y KA_RAIN_TOPO_MATCHED aíslan arquitectura con la misma grilla K; J1/J2 siguen como referencia histórica. K agrega alpha .001 por coherencia con suelo sin z-score.')
    textmain += '\n## Conclusiones de los resultados congelados\n\n'+text.split('\n',2)[2]
    textmain += '\n## Figuras\n\n'
    for filename,caption in [('01_RMSE_protocol.png','RMSE por protocolo'),('01_MAE_protocol.png','MAE por protocolo'),('02_delta_against_rain.png','Mejoras y deterioros frente a lluvia'),('03_additive_vs_residual.png','Arquitectura aditiva y residual con variables y grillas idénticas'),('04_observed_estimated.png','Predicciones OOF aleatorias promediadas solo para descripción'),('05_corrections_parcel.png','Correcciones aplicadas por parcela'),('06_chignahuapan.png','Chignahuapan, subconjunto de los mismos OOF'),('07_boundary_near125m.png','Reserva por proximidad a límites125m'),('08_intraprofile.png','Mejora intraperfil con un mismo modelo externo'),('09_soil_support.png','Errores según soporte aprendido en entrenamiento')]:
        textmain+=f'{caption}\n\n![{caption}](../figures/{filename})\n\n'
    main.write_text(textmain,encoding='utf-8')
    document=textmain.replace('../figures/',f'../outputs/modeling/family_1/{NAME}/{out.name}/figures/')
    document=document.replace('(k1_audit.md)','(k1_edaphological_redesign.md)')
    (ROOT/'documentation/k_standalone_residual_modeling.md').write_text(document,encoding='utf-8')

def report(out,c,sg,pm,benchmark):
    table=c.pivot(index='experiment',columns='protocol',values='RMSE_mean').reset_index()
    baseline=c[c.experiment.eq('J0_RAIN')].set_index('protocol');decision=[]
    for name,z in c.groupby('experiment'):
        if name=='J0_RAIN':continue
        z=z.set_index('protocol');delta=baseline.RMSE_mean-z.RMSE_mean
        decision.append(dict(experiment=name,random_RMSE_improvement=delta['random'],random_MAE_improvement=baseline.loc['random','MAE_mean']-z.loc['random','MAE_mean'],worst_grouped_RMSE_improvement=delta.drop('random').min(),passes_geographic_margin=bool(delta.drop('random').min()>=-.01),interpretation='standalone vs mean is primary' if name.startswith(('K1_','K2_','K3_','K4_')) else 'incremental vs rain; contextual J controls'))
    pd.DataFrame(decision).to_csv(out/'tables/34_operational_decisions.csv',index=False)
    text='# K — Standalone and Residual Geographic–Edaphological Modeling\n\n## K.1 — Representación congelada\n\nS1 primaria: diez coberturas de unidades que mencionan grupos oficiales, conservadas en [0,1]; no son proporciones físicas de grupos asociados. S2 única sensibilidad: unidades con soporte de tres/cinco parcelas aprendido dentro de cada entrenamiento, más Other. S3 y S4 se describen sin buscar rendimiento. Auditoría y pruebas en [K.1](k1_audit.md). Sin modificación de E–J ni Champion.\n\n## K.2/K.3 — Comparación controlada\n\nRMSE t/ha, primero métricas en los 138 OOF completos de cada repetición, después promedio; no promedio de RMSE por fold.\n\n'+j.markdown_table(table)+'\n\nModelos independientes se comparan primariamente con K0, media aprendida en entrenamiento. Controles KA usan exactamente las mismas variables y escalas de suelo que los correctores K7/K8. J1/J2 usan la misma estandarización continua; K agrega alpha .001 por coherencia con suelo sin z-score, por lo que diferencias minúsculas contra J no aíslan exclusivamente arquitectura. Comparaciones pareadas y todos los parámetros en tablas 21/22 y 12/14.\n\nCada predicción climática externa reproduce J0 (tolerancia 1e-8). Los objetivos residuales son predicciones cruzadas únicamente dentro de outer-train; la selección climática de cada submodelo también excluye la etiqueta retenida. La validación interna evalúa el sistema completo con su propio cross-fitting más profundo. ETA=0,.25,.5,1 se elige internamente. Las divisiones profundas conservan perfiles/municipios/grupos espaciales; solo aleatorio usa KFold. Proveniencia de IDs en tabla16 y residuos cruzados en tabla15.\n\n## Geografía, intraperfil y Chignahuapan\n\n'+j.markdown_table(sg[sg.stratum.eq('Chignahuapan')][['experiment','protocol','n','RMSE','MAE','bias']])+'\n\nChignahuapan: 71 etiquetas, subconjunto de los mismos OOF, sin modelo local ni evaluación independiente. Las diferencias entre parejas se atribuyen a variables solo cuando fueron evaluadas por el mismo modelo externo. Tabla27 identifica dispersión artificial sin mejora de error; tabla28 conserva pendiente, altitud y distancia composicional de cada pareja. La correlación residual/corrección en tabla25 procede exclusivamente de predicciones externas. Más dispersión no demuestra mejor predicción.\n\n## Reservas edafológicas y soporte\n\nSe conservan todas las predicciones, incluso negativas o extremas. Tabla33 verifica que las coberturas transformadas no excedan su rango natural, evitando el mecanismo z≈353 de J. Tabla32 define reservas por soporte EXCLUSIVAMENTE en entrenamiento. Tablas23/24 incluyen buffers cartográficos de50/125/250m, claves discrepantes, estados/municipios y rendimientos<3/>5; estos son diagnósticos y nunca predictores. Cartografía1:250000, sin interpretar como medición física parcelaria ni precisión probabilística.\n\n## Criterios y benchmark\n\n'+j.markdown_table(pd.DataFrame(decision))+'\n\nMargen exploratorio .01t/ha para deterioro geográfico/MAE, sin prueba de significancia. Repeticiones y folds comparten observaciones: mejoras pequeñas no son confirmación independiente. Distinguir regiones conocidas, transferencia a nuevas regiones e intraperfil; no hay reemplazo automático del Champion.\n\nBenchmark aleatorio compatible, sin reentrenar:\n\n'+j.markdown_table(benchmark)+'\n\nChampion y Climate Current son contextuales, con otros bloques y arquitecturas. No hay OOF Champion municipal/espacial comparable en esta auditoría; no se extrapola su superioridad a esos protocolos.\n\nTodos los modelos K solo usan lluvia, pendiente, altitud o suelo según especificación; nunca temperatura, satélite, estado/municipio/localidad ni las59 etiquetas ocultas.\n'
    (out/'report/k_modeling.md').write_text(text,encoding='utf-8');(ROOT/'documentation/k_standalone_residual_modeling.md').write_text(text,encoding='utf-8')

def plots(out,p,c,sg):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    def save(fig,name):fig.tight_layout();fig.savefig(out/'figures'/name,dpi=170);plt.close(fig)
    for metric in ['RMSE','MAE']:
        table=c.pivot(index='experiment',columns='protocol',values=metric+'_mean')
        ax=table.plot.barh(figsize=(11,9));ax.set_xlabel(metric+' t/ha (complete OOF)');save(ax.figure,f'01_{metric}_protocol.png')
    z=c.copy();base=c[c.experiment.eq('J0_RAIN')].set_index('protocol').RMSE_mean
    z['delta']=z.protocol.map(base)-z.RMSE_mean
    ax=z.pivot(index='experiment',columns='protocol',values='delta').plot.barh(figsize=(11,9));ax.axvline(0,color='k');ax.set_xlabel('RMSE rain − candidate; positive improves');save(ax.figure,'02_delta_against_rain.png')
    contrasts=[('KA_RAIN_SLOPE_MATCHED','K5_RAIN_RESID_SLOPE'),('KA_RAIN_TOPO_MATCHED','K6_RAIN_RESID_TOPO'),('KA_RAIN_SOIL_STABLE','K7_RAIN_RESID_SOIL'),('KA_RAIN_TOPO_SOIL_STABLE','K8_RAIN_RESID_TOPO_SOIL')]
    fig,axs=plt.subplots(2,2,figsize=(12,8))
    for ax,(a,b),title in zip(axs.flat,contrasts,['Pendiente','Topografía','Suelo','Topografía + suelo']):
        order=['random','climate_profile','municipality','spatial']
        q=c[c.experiment.isin([a,b])].pivot(index='protocol',columns='experiment',values='RMSE_mean').reindex(order)
        q=q.rename(columns={a:'Aditivo',b:'Residual'})[['Residual','Aditivo']]
        q.index=['Aleatorio','Perfil','Municipal','Espacial']
        q.plot.bar(ax=ax,rot=0)
        base=c[c.experiment.eq('J0_RAIN')].set_index('protocol').RMSE_mean.reindex(order)
        ax.plot(np.arange(4),base.to_numpy(),'k--o',label='Lluvia sola',markersize=3)
        ax.set_title(title);ax.set_ylabel('RMSE t/ha');ax.set_xlabel('');ax.legend(fontsize=10)
    save(fig,'03_additive_vs_residual.png')
    q=p[p.protocol.eq('random')&p.experiment.str.startswith(('K5_','K6_','K7_','K8_'))].groupby(['experiment',ID]).agg(y_true=('y_true','first'),y_pred=('y_pred','mean'),correction=('correction','mean'),improvement=('absolute_error_improvement','mean')).reset_index()
    fig,axs=plt.subplots(2,2,figsize=(10,9))
    for ax,(name,z) in zip(axs.flat,q.groupby('experiment')):
        ax.scatter(z.y_true,z.y_pred,s=14,alpha=.7);ax.plot([2,6],[2,6],color='k');ax.set_title(name);ax.set_xlabel('Observed');ax.set_ylabel('Mean random OOF prediction')
    save(fig,'04_observed_estimated.png')
    fig,ax=plt.subplots(figsize=(12,5))
    for name,z in q.groupby('experiment'):ax.plot(np.arange(len(z)),z.correction,label=name,alpha=.7)
    ax.axhline(0,color='k');ax.legend();ax.set_ylabel('Mean random OOF correction t/ha');ax.set_xlabel('Parcel ID order');save(fig,'05_corrections_parcel.png')
    local=sg[sg.stratum.eq('Chignahuapan')].pivot(index='experiment',columns='protocol',values='RMSE');ax=local.plot.barh(figsize=(11,9));ax.set_xlabel('Chignahuapan OOF subset RMSE');save(ax.figure,'06_chignahuapan.png')
    for label,title in [('near_boundary_125m','near125m'),('away_boundary_125m','away125m')]:
        table=sg[sg.stratum.eq(label)].pivot(index='experiment',columns='protocol',values='MAE');ax=table.plot.barh(figsize=(11,9));ax.set_xlabel('MAE '+title);save(ax.figure,'07_boundary_'+title+'.png')
    ss=pd.read_csv(out/'tables/27_same_model_profile_diagnostics.csv');qq=ss.groupby(['experiment','protocol']).absolute_error_improvement.mean().unstack();ax=qq.plot.barh(figsize=(11,9));ax.set_xlabel('Mean within-profile MAE improvement, same outer model');save(ax.figure,'08_intraprofile.png')
    support=pd.read_csv(out/'tables/32_errors_by_training_support.csv');qq=support.groupby(['experiment','stratum']).MAE.mean().unstack();ax=qq.plot.barh(figsize=(11,9));ax.set_xlabel('Descriptive mean fold/subgroup MAE, training support');save(ax.figure,'09_soil_support.png')
