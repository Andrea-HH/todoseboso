"""E8 predictor provenance and repeated-OOF diagnosis, before any PCA fit."""
from pathlib import Path
import ast
import json
import joblib
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist
from .rainfall_features import ID, MONTHS
from .rainfall_modeling import experiments, supervised_data
from .rainfall_audit import ROOT, MASTER, sha

MONTHLY = [f'rain_{month}_2025' for month in MONTHS]
REFERENCE = ROOT/'outputs/modeling/family_1/rainfall_yield/v1'
FEATURES = ROOT/'data/processed/family_1/rainfall_yield/v1/rainfall_features.parquet'
DICTIONARY = FEATURES.with_name('rainfall_feature_dictionary.csv')

def bounded_groups(values, tolerance=.01):
    values=np.asarray(values,float)
    if not np.isfinite(values).all():raise ValueError('Finite profiles required')
    if len(values)==1:return np.ones(1,dtype=int)
    return fcluster(linkage(pdist(values,metric='chebyshev'),method='complete'),t=tolerance,criterion='distance')

def load_data():
    features=pd.read_parquet(FEATURES)
    matrix=features[[ID]+MONTHLY].sort_values(ID).reset_index(drop=True)
    if len(matrix)!=197 or not matrix[ID].is_unique or not np.isfinite(matrix[MONTHLY]).all().all():
        raise ValueError('E8 requires 197 complete, unique parcel vectors')
    train=supervised_data(matrix,pd.read_csv(MASTER))
    if len(train)!=138:raise ValueError('Expected 138 labeled parcels')
    return matrix,train

def audit_predictors(out):
    out=Path(out);dictionary=pd.read_csv(DICTIONARY).set_index('feature_name')
    config=json.loads((REFERENCE/'configuration.json').read_text(encoding='utf-8'))
    registry=pd.read_csv(REFERENCE/'tables/01_experiment_registry.csv')
    rows=[];lineage=[]
    for experiment,spec in experiments().items():
        if spec != config['experiments'][experiment]:raise ValueError(f'Configuration differs from source: {experiment}')
        part=registry[registry.experiment.eq(experiment)]
        actual=[]
        for row in part.itertuples():
            path=REFERENCE/'models'/f'{row.protocol}_{row.repeat:02d}_{row.fold:02d}_{experiment}.joblib'
            fitted=joblib.load(path);columns=[]
            if experiment!='E0_MEAN':
                for _,transform,cols in fitted.named_steps['features'].transformers_:
                    if transform!='drop':columns.extend(cols)
            if columns!=json.loads(row.columns):raise ValueError(f'Fitted model/registry disagree: {path}')
            actual.extend(columns)
        columns=sorted(set(actual))
        for c in columns:
            meta=dictionary.loc[c]
            if meta.source!='canonical CHIRPS precip_mean; exactextract':raise ValueError(f'Unknown origin: {c}')
            lineage.append(dict(experiment=experiment,column=c,source=meta.source,formula=meta.formula,
                period=meta.period,source_code='src/family_1/rainfall_features.py:build_features',rainfall_only=True))
        rows.append(dict(experiment=experiment,columns=json.dumps(columns),declared_candidates=json.dumps(spec['columns']),
            algorithm='DummyRegressor(mean Y_train)' if experiment=='E0_MEAN' else 'PolynomialFeatures + OLS' if spec['kind']=='quadratic' else 'OLS' if spec['kind']=='linear' else 'Ridge; nested families for E7',
            sources='none' if not columns else 'canonical CHIRPS precip_mean only',rainfall_only=True,
            fitted_folds_verified=len(part),scope='rainfall module'))
    rows.append(dict(experiment='E8_RAINFALL_PCA_PCR',columns=json.dumps(MONTHLY),declared_candidates=json.dumps(MONTHLY),
        algorithm='StandardScaler -> PCA -> OLS / Ridge',sources='same seven canonical CHIRPS monthly means',
        rainfall_only=True,fitted_folds_verified=0,scope='new experiment contract'))
    pd.DataFrame(rows).to_csv(out/'tables/00_predictor_audit.csv',index=False)
    pd.DataFrame(lineage).to_csv(out/'tables/01_column_provenance.csv',index=False)
    # Integral RS6 models: exact per-fold selected columns from saved metadata,
    # and all topo/Planet columns from the source frames used by script 212.
    base=ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization'
    hp=pd.read_csv(base/'models/selected_hyperparameters.csv')
    fd=ROOT/'data/processed/family_1/features'
    provenance=pd.read_csv(fd/'family1_feature_dictionary.csv').drop_duplicates('feature_name').set_index('feature_name')
    top=[c for c in pd.read_parquet(fd/'topography_basic_features.parquet') if c!=ID]
    planet=[c for c in pd.read_parquet(fd/'planet_features.parquet') if c!=ID]
    definitions={'A_CURRENT_CH_H_T':'ElasticNet climate -> XGBoost Sentinel history -> Ridge topography',
        'B_REVERSED_CT_H':'ElasticNet climate -> Ridge topography -> XGBoost history',
        'C1_JOINT_HT_RIDGE':'ElasticNet climate -> joint Ridge history/topography',
        'C2_JOINT_HT_XGB':'ElasticNet climate -> joint XGBoost history/topography',
        'D_CH_T_H2':'A plus conservative second XGBoost history correction',
        'E1_CH_JOINT_TP_RIDGE':'ElasticNet climate -> XGBoost history -> joint Ridge topography/Planet',
        'E2_CH_JOINT_TP_XGB':'ElasticNet climate -> XGBoost history -> joint XGBoost topography/Planet'}
    integrated=[];expanded=[]
    for name,algorithm in definitions.items():
        union=set()
        for row in hp.itertuples():
            cols=json.loads(row.climate_features)+json.loads(row.history_features)+top+(planet if name.startswith('E') else [])
            union.update(cols)
            integrated.append(dict(experiment=name,repeat=row.repeat,fold=row.fold,columns=json.dumps(cols),
                algorithm=algorithm,rainfall_only=False,scope='integral RS6; not an E8 input',
                source_code='scripts/data_uderstanding/tablas_agrocebada/212_residual_architecture_optimization.py:run'))
        for c in sorted(union):
            if c not in provenance.index:raise ValueError(f'Integral dictionary missing {c}')
            m=provenance.loc[c]
            expanded.append(dict(experiment=name,column=c,source=m.source,sensor=m.sensor,variable=m.variable,
                source_code='feature_pipeline.build_climate/build_history_anomaly/build_planet; terrain_features for topography',
                rainfall_only=False))
    pd.DataFrame(integrated).to_csv(out/'tables/02_integral_models_by_fold.csv',index=False)
    pd.DataFrame(expanded).to_csv(out/'tables/03_integral_column_provenance.csv',index=False)
    # Inventory the separate Phase C competition, with its source-declared blocks.
    source=ROOT/'scripts/modeling/312_phase_c_c4_c6_predictive_competition.py'
    tree=ast.parse(source.read_text(encoding='utf-8'))
    block_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='blocks')
    namespace={'pd':pd,'ROOT':ROOT}
    exec(compile(ast.Module(body=[block_node],type_ignores=[]),str(source),'exec'),namespace)
    f=pd.read_parquet(fd/'family1_features_all.parquet')
    rgb=pd.read_parquet(ROOT/'data/processed/phase_c/c1_2/rgb_compact_representations.parquet')
    blocks,s1,s3,s5=namespace['blocks'](pd.DataFrame(columns=list(f)+list(rgb)))
    phase=pd.read_csv(ROOT/'outputs/research/phase_c/c4_c6_predictive_competition/tables/01_experiment_registry.csv')
    catalog=[]
    for name,q in phase.groupby('model'):
        row=q.iloc[0];extras={'pca5':s5,'s1label':s1,'s3label':s3,'bothlabel':s1+s3,'soft':s1+s3,'interactions':s1+s3+['S2_ndwi_promedio_mean'],'partial':s1+s3}.get(row.environment,[])
        catalog.append(dict(experiment=name,algorithm=row.family,columns=json.dumps(blocks[row.feature_block]),
            derived_environment_inputs=json.dumps(list(dict.fromkeys(extras))),environment=row.environment,
            rainfall_only=False,source_code=str(source.relative_to(ROOT))+':blocks/run',scope='Phase C integral; excluded from E8'))
    pd.DataFrame(catalog).to_csv(out/'tables/04_phase_c_integral_catalog.csv',index=False)
    return {'rainfall_predictors_verified':True,'previous_fitted_models_verified':len(registry),
        'integral_RS6_architectures':len(definitions),'phase_c_integral_models':len(catalog)}

def diagnose_profiles(matrix,train,geography,out):
    out=Path(out)
    exact=pd.factorize(pd.MultiIndex.from_frame(matrix[MONTHLY]),sort=True)[0]+1
    near=bounded_groups(matrix[MONTHLY],.01)
    profiles=matrix[[ID]].assign(exact_profile=exact,near_profile=near)
    profiles.to_csv(out/'tables/05_seven_month_profile_groups.csv',index=False)
    geo=geography[[ID,'Estado','Municipio']]
    all_data=profiles.merge(geo,on=ID,validate='one_to_one').merge(train[[ID,'RENDIMIENTO_T_HA']],on=ID,how='left',validate='one_to_one')
    prior=pd.read_parquet(REFERENCE/'tables/02_oof_predictions.parquet')
    prior=prior[prior.experiment.isin(['E0_MEAN','E3_MONTHLY_LINEAR','E3_MONTHLY_RIDGE'])].copy()
    prior=prior.merge(profiles,on=ID,validate='many_to_one')
    avg=prior.groupby(['protocol','experiment',ID,'exact_profile','near_profile']).agg(y_true=('y_true','first'),y_pred=('y_pred','mean')).reset_index()
    prior['absolute_error']=abs(prior.y_pred-prior.y_true)
    avg['absolute_error']=abs(avg.y_pred-avg.y_true)
    summaries=[]
    for definition in ['exact_profile','near_profile']:
        for group,g in all_data.groupby(definition):
            for (protocol,experiment),pred in prior[prior[definition].eq(group)].groupby(['protocol','experiment']):
                averaged=avg[(avg[definition]==group)&(avg.protocol==protocol)&(avg.experiment==experiment)]
                y=g.RENDIMIENTO_T_HA.dropna()
                summaries.append(dict(definition=definition,group=group,protocol=protocol,experiment=experiment,
                    n_parcels=len(g),n_labeled=len(y),n_states=g.Estado.nunique(),n_municipalities=g[['Estado','Municipio']].drop_duplicates().shape[0],
                    y_std=y.std(),y_min=y.min(),y_max=y.max(),y_range=y.max()-y.min(),
                    individual_oof_prediction_std=pred.y_pred.std(),individual_oof_prediction_range=pred.y_pred.max()-pred.y_pred.min(),
                    averaged_oof_prediction_std=averaged.y_pred.std(),averaged_oof_prediction_range=averaged.y_pred.max()-averaged.y_pred.min(),
                    individual_oof_MAE=pred.absolute_error.mean(),averaged_oof_MAE=averaged.absolute_error.mean()))
    # Preserve also climate groups with no labeled observations.
    all_data.groupby('exact_profile').agg(n_parcels=(ID,'size'),n_labeled=('RENDIMIENTO_T_HA','count'),n_states=('Estado','nunique')).to_csv(out/'tables/06_all_profile_counts.csv')
    pd.DataFrame(summaries).to_csv(out/'tables/07_profile_y_and_prediction_dispersion.csv',index=False)
    freq=train.RENDIMIENTO_T_HA.value_counts().rename_axis('yield').reset_index(name='n_parcels')
    freq.to_csv(out/'tables/08_repeated_observed_y.csv',index=False)
    bands=[];pairs=[]
    positions=matrix.set_index(ID)[MONTHLY]
    for (protocol,experiment),p in prior.groupby(['protocol','experiment']):
        a=avg[(avg.protocol==protocol)&(avg.experiment==experiment)]
        band_ids=bounded_groups(a[['y_pred']],.01)
        for group in np.unique(band_ids):
            q=a[band_ids==group]
            bands.append(dict(protocol=protocol,experiment=experiment,prediction_band=int(group),n=len(q),
                n_exact_profiles=q.exact_profile.nunique(),n_near_profiles=q.near_profile.nunique(),
                prediction_min=q.y_pred.min(),prediction_max=q.y_pred.max(),y_range=q.y_true.max()-q.y_true.min()))
        x=positions.loc[a[ID]].to_numpy();distance=pdist(x,metric='chebyshev')
        ii,jj=np.triu_indices(len(a),1);pred_diff=abs(a.y_pred.to_numpy()[ii]-a.y_pred.to_numpy()[jj])
        for z in np.flatnonzero((pred_diff<=.01)&(distance>.01)):
            pairs.append(dict(protocol=protocol,experiment=experiment,ID_a=a.iloc[ii[z]][ID],ID_b=a.iloc[jj[z]][ID],
                max_month_difference_mm=distance[z],prediction_difference_t_ha=pred_diff[z]))
    pd.DataFrame(bands).to_csv(out/'tables/09_prediction_bands_001tha.csv',index=False)
    pd.DataFrame(pairs).to_csv(out/'tables/10_distinct_profiles_similar_predictions.csv',index=False)
    # A fixed fitted function must give identical predictions to identical vectors;
    # this check includes all 197 parcels without interpreting fitted predictions as OOF.
    fixed=joblib.load(REFERENCE/'models/random_01_01_E3_MONTHLY_RIDGE.joblib')
    fixed_predictions=profiles.assign(fixed_prediction=fixed.predict(matrix[MONTHLY]))
    group_ranges=fixed_predictions.groupby('exact_profile').fixed_prediction.agg(lambda s:s.max()-s.min())
    labeled=train[[ID,'RENDIMIENTO_T_HA']].merge(profiles,on=ID)
    mean_y=labeled.groupby('exact_profile').RENDIMIENTO_T_HA.transform('mean')
    empirical_floor=float(np.sqrt(np.mean((labeled.RENDIMIENTO_T_HA-mean_y)**2)))
    summary=dict(exact_seven_month_profiles=int(len(np.unique(exact))),near_seven_month_profiles_001mm=int(len(np.unique(near))),
        distinct_observed_y=int(train.RENDIMIENTO_T_HA.nunique()),max_observed_y_multiplicity=int(freq.n_parcels.max()),
        fixed_model_max_within_exact_profile_prediction_range=float(group_ranges.max()),
        empirical_exact_profile_constant_prediction_RMSE_floor=empirical_floor,
        note='Empirical best constant per exact profile uses same Y, NOT validated RMSE or population irreducible error.',
        predicted_band_tolerance_t_ha=.01,near_profile_tolerance_mm=.01,
        axis_caveat='Prior charts put observed Y on x. Vertical bands can also reflect repeated observed yield values, not predictions.')
    (out/'report/profile_diagnostic.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    prior.to_parquet(out/'tables/11_reference_oof_individual.parquet',index=False)
    avg.to_parquet(out/'tables/12_reference_oof_averaged.parquet',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for data,ax,title in [(prior,axes[0],'OOF individuales: 1,380 predicciones'),(avg,axes[1],'OOF media: 138 parcelas')]:
        q=data[data.protocol.eq('random')&data.experiment.eq('E3_MONTHLY_RIDGE')]
        sc=ax.scatter(q.y_true,q.y_pred,c=q.exact_profile,cmap='turbo',vmin=1,vmax=max(exact),s=18,alpha=.45)
        ax.plot([1,6],[1,6],'k--');ax.set(xlabel='Observado (t/ha)',ylabel='Predicción (t/ha)',title=title,xlim=(1,6),ylim=(1,6))
    fig.colorbar(sc,ax=axes.tolist(),label='Grupo de siete meses (ID en tabla 05)')
    fig.savefig(out/'figures/01_profile_colored_individual_vs_average.png',dpi=160,bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(13,4))
    ax.scatter(labeled.exact_profile,labeled.RENDIMIENTO_T_HA,c=labeled.exact_profile,cmap='turbo',s=25)
    ax.set(xlabel='Perfil climático exacto',ylabel='Rendimiento observado (t/ha)',title='Dispersión del rendimiento dentro del mismo vector de lluvia')
    fig.tight_layout();fig.savefig(out/'figures/02_within_profile_observed_y.png',dpi=160);plt.close(fig)
    (out/'report/predictor_and_bands_audit.md').write_text(f'''# E8 — auditoría previa a PCA

Se cotejaron código, diccionario, configuración, registro y columnas efectivas de los 845 modelos E0–E7/F. Todos son exclusivamente de precipitación; E0 no tiene predictores. E7 elige subconjuntos internos, por eso su catálogo muestra la unión de candidatos y el registro previo conserva las columnas de cada fold. Tablas 00–01: algoritmos, columnas y procedencia verificada desde precip_mean/CHIRPS. Tablas 02–04: siete arquitecturas integrales RS6 y 16 modelos Fase C, separados y excluidos de E8; incluyen temperatura, historia satelital, topografía y otras fuentes.

Hay {summary['exact_seven_month_profiles']} perfiles exactos y {summary['near_seven_month_profiles_001mm']} casi equivalentes a 0.01 mm por mes (enlace completo, sin redondear ni encadenar distancias). El modelo fijo comprobado devuelve diferencia cero para iguales vectores. Cerca no significa matemáticamente indistinguible: un modelo puede amplificar diferencias pequeñas. La tabla 10 identifica perfiles distintos con predicciones promedio a ≤0.01 t/ha, lo cual también puede ocurrir al proyectar siete variables en una salida escalar.

En las gráficas anteriores x=Y observado; hay {summary['distinct_observed_y']} valores diferentes de Y entre 138 parcelas y hasta {summary['max_observed_y_multiplicity']} parcelas con el mismo valor. Esto explica bandas verticales del eje x y no demuestra sobreajuste. Con ejes invertidos las bandas de predicción pueden reflejar los perfiles compartidos. No se atribuye un mecanismo a la banda sin distinguir estos casos.

Las OOF individuales proceden de modelos diferentes; hasta parcelas idénticas pueden recibir predicciones ligeramente diferentes por composición del train, escala y alpha. La media de diez repeticiones vuelve a cambiar dispersión y errores. Tablas 07, 11–12 y figura 01 distinguen ambos; no se cuentan las 1,380 OOF como 1,380 rendimientos independientes.

Toda función determinista fija de siete valores asigna una única salida a vectores exactamente iguales. La mínima RMSE empírica entre funciones constantes por perfil, calculada con las mismas etiquetas, es {empirical_floor:.4f} t/ha. Es una identidad descriptiva del conjunto observado, no un error irreducible poblacional ni un resultado validado. La variación intraperfil de Y requiere información que estos siete valores no distinguen. El PCA no puede crear esa información.

![OOF individuales y media](../figures/01_profile_colored_individual_vs_average.png)
![Y dentro de perfiles](../figures/02_within_profile_observed_y.png)
''',encoding='utf-8')
    return summary
