"""Small extension of H: rain/Tmax structure and one nested PCR experiment."""
import json,shutil
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GridSearchCV
from .climate_signal_features import ROOT,ID,RAIN,MAX,MASTER,TARGET,paths,sha,original_snapshot,supervised_data
from .climate_signal_descriptive import geography
from .climate_signal_reporting import summarize,table_text
from .rainfall_pcr import load_frozen_splits
from .rainfall_pcr_reporting import save

COLS=RAIN+MAX
NAME='H_EXT_RAIN_TMAX_PCR'
E8=ROOT/'outputs/modeling/family_1/rainfall_yield/e8/v1'

def locations(run_id):
    return ROOT/'outputs/modeling/family_1/h_joint_climate_signal/extensions/rain_tmax'/run_id

def load():
    gout,gproc=paths('G','v1');hout,_=paths('H','v1')
    frame=pd.read_parquet(gproc/'climate_candidates_197.parquet')[[ID,'CONJUNTO']+COLS]
    membership=pd.read_csv(hout/'tables/06_profile_memberships.csv')[[ID,'rain']]
    frame=frame.merge(membership,on=ID,validate='one_to_one')
    groups=pd.factorize(pd.MultiIndex.from_frame(frame[COLS]))[0]
    if not all(frame.groupby('rain').apply(lambda z:len(set(groups[z.index])),include_groups=False).eq(1)) or len(set(groups))!=53:raise ValueError('Rain/Tmax profile partition differs')
    geo=geography()[[ID,'Estado','Municipio','longitude','latitude']]
    topo=pd.read_parquet(ROOT/'data/processed/family_1/features/topography_basic_features.parquet')[[ID,'TOPO_BASIC_elevation_mean']].rename(columns={'TOPO_BASIC_elevation_mean':'altitude_m'})
    q=frame.merge(geo,on=ID,validate='one_to_one').merge(topo,on=ID,validate='one_to_one')
    if len(q)!=197 or not np.isfinite(q[COLS+['altitude_m']]).all().all():raise ValueError('Incomplete extension data')
    return q,supervised_data(frame,pd.read_csv(MASTER))

def verify_protected(out):
    snapshot=json.loads((out/'protected_inputs.json').read_text(encoding='utf-8'))
    for name,digest in snapshot.items():
        if sha(ROOT/name)!=digest:raise ValueError(f'Protected input changed: {name}')

def initialize(run_id):
    out=locations(run_id)
    if (out/'manifest.json').exists():raise FileExistsError('Completed extension; choose another run-id')
    out.mkdir(parents=True,exist_ok=True)
    for d in ['tables','figures','report','models','splits','checkpoints']:(out/d).mkdir(exist_ok=True)
    if not (out/'protected_inputs.json').exists():
        snapshot=original_snapshot();snapshot.pop(str(Path(__file__).relative_to(ROOT)),None)
        for section in ['G','H']:
            for folder in paths(section,'v1'):
                snapshot.update({str(p.relative_to(ROOT)):sha(p) for p in folder.rglob('*') if p.is_file()})
        (out/'protected_inputs.json').write_text(json.dumps(snapshot,indent=2),encoding='utf-8')
    verify_protected(out)
    return out

def profile_frame(q):
    rows=[]
    for profile,z in q.groupby('rain',sort=True):
        row={ID:f'PROFILE_{profile:02d}','rain':profile,'n_parcels':len(z),**z[COLS].iloc[0].to_dict()}
        for field in ['Estado','Municipio']:row[field]=z[field].iloc[0] if z[field].nunique()==1 else 'Mixto'
        for field in ['longitude','latitude','altitude_m']:row[field]=z[field].mean()
        row['altitude_min_m']=z.altitude_m.min();row['altitude_max_m']=z.altitude_m.max()
        rows.append(row)
    return pd.DataFrame(rows)

def geography_plot(frame,scores,key,out):
    labelled=frame[[ID,'Estado','Municipio','altitude_m']].copy()
    labelled['PC1']=scores[:,0];labelled['PC2']=scores[:,1]
    fig,axes=plt.subplots(1,3,figsize=(17,5))
    sns.scatterplot(data=labelled,x='PC1',y='PC2',hue='Estado',s=35,ax=axes[0])
    sns.scatterplot(data=labelled,x='PC1',y='PC2',hue='Municipio',s=30,ax=axes[1]);axes[1].legend(fontsize=6,loc='lower left',ncol=2)
    sc=axes[2].scatter(scores[:,0],scores[:,1],c=frame.altitude_m,cmap='viridis',s=35)
    fig.colorbar(sc,ax=axes[2],label='Altitud media (m)');axes[2].set(xlabel='PC1',ylabel='PC2')
    fig.suptitle(key+' — distribución geográfica, no clusters confirmados')
    fig.tight_layout();save(fig,out,f'12_{key}_geography_altitude.png')
    if key.endswith('Rain_Tmax'):
        fig,axes=plt.subplots(1,2,figsize=(11,4))
        for i,ax in enumerate(axes):
            sc=ax.scatter(frame.longitude,frame.latitude,c=scores[:,i],cmap='coolwarm',s=30)
            fig.colorbar(sc,ax=ax,label=f'Score PC{i+1}')
            ax.set(xlabel='Longitud',ylabel='Latitud',title=f'PC{i+1}')
        fig.suptitle(key+' — gradientes en ubicación geográfica')
        fig.tight_layout();save(fig,out,f'13_{key}_PC_maps.png')

def biplot(frame,scores,loads,key,out):
    labelled=frame[[ID,'Estado']].copy();labelled['PC1']=scores[:,0];labelled['PC2']=scores[:,1]
    fig,axes=plt.subplots(1,2,figsize=(14,5))
    sns.scatterplot(data=labelled,x='PC1',y='PC2',hue='Estado',s=35,ax=axes[0])
    factor=.65*max(abs(scores[:,:2]).max(),1e-8)
    for feature,row in loads.iloc[:,:2].iterrows():
        color='royalblue' if feature in RAIN else 'firebrick';x,y=row*factor
        axes[0].annotate('',xy=(x,y),xytext=(0,0),arrowprops=dict(arrowstyle='->',color=color,alpha=.6))
        axes[0].text(x,y,feature.replace('_2025',''),fontsize=6,color=color)
    axes[0].set_title(f'Biplot: eigenvectores ×{factor:.2f}, solo visualización')
    sns.heatmap(loads.iloc[:,:min(4,len(loads.columns))],annot=True,fmt='.2f',cmap='coolwarm',center=0,yticklabels=[c.replace('_2025','') for c in loads.index],ax=axes[1])
    axes[1].tick_params(axis='y',labelsize=9);fig.suptitle(key);fig.subplots_adjust(wspace=.5)
    save(fig,out,f'11_{key}_biplot_loadings.png')

def fit_descriptive(X,name,weighting,balanced=False):
    """Reuse the existing single-block parcel PCA; refit only new descriptive cases."""
    weights=np.full(X.shape[1],1/np.sqrt(7)) if balanced else np.ones(X.shape[1])
    if weighting=='parcel' and name=='Rain':
        old=joblib.load(E8/'models/exploratory_PCA_197_target_free.joblib')
        scaler=old.named_steps['scaler'];pca=old.named_steps['pca'];origin='cached E8 exploratory PCA; no refit'
    elif weighting=='parcel' and name=='Tmax':
        old=joblib.load(paths('G','v1')[0]/'models/descriptive_Tmax.joblib')
        scaler=old['scaler'];pca=old['pca'];origin='cached G exploratory PCA; no refit'
    else:
        scaler=StandardScaler().fit(X);pca=PCA(svd_solver='full').fit(scaler.transform(X)*weights);origin='new target-free descriptive fit'
    return scaler,pca,weights,origin

def describe(q,out):
    profiles=profile_frame(q);profiles.to_csv(out/'tables/01_equal_profile_matrix.csv',index=False)
    q.to_csv(out/'tables/02_parcel_climate_geography.csv',index=False)
    dimensions=[];geographic=[];signal=[];comparisons=[]
    specs=[('Rain',RAIN,False),('Tmax',MAX,False),('Rain_Tmax',COLS,False),('Rain_Tmax_balanced',COLS,True)]
    for weighting,frame in [('parcel',q),('equal_profile',profiles)]:
        fitted={}
        for name,cols,balanced in specs:
            key=f'{weighting}_{name}';X=frame[cols]
            scaler,pca,weights,origin=fit_descriptive(X,name,weighting,balanced)
            scores=pca.transform(scaler.transform(X)*weights);pcs=[f'PC{k+1}' for k in range(len(cols))]
            fitted[name]=(pca,scores)
            cumulative=np.cumsum(pca.explained_variance_ratio_)
            dimensions.append(dict(weighting=weighting,representation=name,n=len(frame),columns=len(cols),K90=int(np.searchsorted(cumulative,.9)+1),K95=int(np.searchsorted(cumulative,.95)+1),PC1_variance=pca.explained_variance_ratio_[0],PC2_variance=pca.explained_variance_ratio_[1],origin=origin))
            pd.DataFrame(dict(component=pcs,eigenvalue=pca.explained_variance_,variance_fraction=pca.explained_variance_ratio_,cumulative=cumulative)).to_csv(out/'tables'/f'10_{key}_variance.csv',index=False)
            loads=pd.DataFrame(pca.components_.T,index=cols,columns=pcs);loads.to_csv(out/'tables'/f'11_{key}_loadings.csv')
            loads.pow(2).groupby(lambda c:'rain' if c in RAIN else 'tmax').sum().to_csv(out/'tables'/f'12_{key}_block_contributions.csv')
            s=pd.DataFrame(scores,columns=pcs);s.insert(0,ID,frame[ID].to_numpy());s.to_parquet(out/'tables'/f'13_{key}_scores_target_free.parquet',index=False)
            pd.DataFrame(dict(feature=cols,mean=scaler.mean_,scale=scaler.scale_,weight=weights)).to_csv(out/'tables'/f'14_{key}_scaling.csv',index=False)
            corr=pd.DataFrame(np.corrcoef(scores.T,X.to_numpy().T)[:len(cols),len(cols):],index=pcs,columns=cols);corr.to_csv(out/'tables'/f'15_{key}_pc_month_correlations.csv')
            labelled=s.merge(frame[[ID,'Estado','Municipio','altitude_m','longitude','latitude']],on=ID,validate='one_to_one')
            intensity=frame[RAIN].sum(axis=1).to_numpy();shares=frame[RAIN].to_numpy()/intensity[:,None]
            thermal_mean=frame[MAX].mean(axis=1).to_numpy()
            for i,pc in enumerate(pcs[:3]):
                y=scores[:,i];total=((y-y.mean())**2).sum()
                for field in ['Estado','Municipio']:
                    eta=sum(len(z)*(z[pc].mean()-labelled[pc].mean())**2 for _,z in labelled.groupby(field))/total
                    geographic.append(dict(weighting=weighting,representation=name,component=pc,analysis=field,statistic='between-group variance fraction',value=eta,n=len(frame),n_groups=labelled[field].nunique()))
                for field in ['altitude_m','longitude','latitude']:
                    geographic.append(dict(weighting=weighting,representation=name,component=pc,analysis=field,statistic='Pearson correlation',value=pd.Series(y).corr(frame[field].reset_index(drop=True)),n=len(frame),n_groups=np.nan))
                coords=frame[['longitude','latitude']].to_numpy();alt=frame[['altitude_m']].to_numpy()
                base=LinearRegression().fit(coords,y).score(coords,y);full=LinearRegression().fit(np.c_[coords,alt],y).score(np.c_[coords,alt],y)
                for analysis,value in [('coordinates_R2',base),('coordinates_altitude_R2',full),('altitude_incremental_R2_after_coordinates',full-base)]:
                    geographic.append(dict(weighting=weighting,representation=name,component=pc,analysis=analysis,statistic='descriptive in-sample R2; no Y, no inferential claim',value=value,n=len(frame),n_groups=np.nan))
                signal.append(dict(weighting=weighting,representation=name,component=pc,rain_total_pearson=np.corrcoef(y,intensity)[0,1],tmax_mean_pearson=np.corrcoef(y,thermal_mean)[0,1],**{f'rain_share_{m}_pearson':np.corrcoef(y,shares[:,j])[0,1] for j,m in enumerate(['apr','may','jun','jul','aug','sep','oct'])}))
            joblib.dump(dict(scaler=scaler,pca=pca,weights=weights,columns=cols,weighting=weighting,origin=origin,role='target-free descriptive only'),out/'models'/f'descriptive_{key}.joblib',compress=3)
            fig,axes=plt.subplots(1,2,figsize=(11,4));axes[0].plot(range(1,len(cols)+1),pca.explained_variance_ratio_,'o-');axes[1].plot(range(1,len(cols)+1),cumulative,'o-');axes[1].axhline(.95,c='grey',ls='--');axes[0].set(xlabel='PC',ylabel='Varianza explicada');axes[1].set(xlabel='K',ylabel='Varianza acumulada');fig.suptitle(key+' — exploratorio');save(fig,out,f'10_{key}_scree.png')
            biplot(frame,scores,loads,key,out)
            geography_plot(frame,scores,key,out)
        p,a=fitted['Rain_Tmax'];b,c=fitted['Rain_Tmax_balanced']
        alignment=abs(np.diag(p.components_@b.components_.T))
        if not np.allclose(alignment,1,atol=1e-6) or not np.allclose(p.explained_variance_ratio_,b.explained_variance_ratio_,atol=1e-12):raise ValueError('Equal-size block balancing should only multiply global scale')
        comparisons.append(dict(weighting=weighting,min_component_absolute_alignment=float(alignment.min()),variance_fraction_max_difference=float(abs(p.explained_variance_ratio_-b.explained_variance_ratio_).max()),balanced_eigenvalue_factor=1/7,conclusion='7 rain + 7 Tmax: standardized blocks already equal total variance; balancing changes only global scale'))
    pd.DataFrame(dimensions).to_csv(out/'tables/16_effective_dimensions.csv',index=False)
    pd.DataFrame(geographic).to_csv(out/'tables/17_pc_geographic_associations.csv',index=False)
    pd.DataFrame(signal).to_csv(out/'tables/18_intensity_timing_temperature.csv',index=False)
    pd.DataFrame(comparisons).to_csv(out/'tables/19_equal_block_balance_equivalence.csv',index=False)
    (out/'descriptive_complete.json').write_text(json.dumps(dict(profiles=53,n=197,hidden_y_used=False,balanced_role='descriptive sensitivity only'),indent=2),encoding='utf-8')

def tune_pcr(X,y,inner):
    pipeline=Pipeline([('imputer',SimpleImputer(strategy='median')),('scaler',StandardScaler()),('pca',PCA(svd_solver='full')),('model',LinearRegression())])
    return GridSearchCV(pipeline,{'pca__n_components':list(range(1,15))},cv=inner,scoring='neg_root_mean_squared_error',n_jobs=1,error_score='raise').fit(X[COLS],y)

def model(train,out):
    splits,table,_=load_frozen_splits(train)
    saved=pd.read_csv(paths('H','v1')[0]/'splits/outer_and_inner_splits.csv')
    pd.testing.assert_frame_equal(table,saved[table.columns],check_dtype=False)
    for name in ['outer_and_inner_splits.csv','group_memberships.csv','profile_protocol_definition.json']:shutil.copy2(paths('H','v1')[0]/'splits'/name,out/'splits'/name)
    config=dict(section='H extension: precipitation + Tmax',columns=COLS,K_grid=list(range(1,15)),seed=2026,algorithm='OLS PCR',selection='mean inner-fold RMSE',n_outer=len(splits),weighting='ordinary parcel training; 53-profile fits descriptive only',scaling='within inner and outer training',balanced_predictive_model=False,reason_no_balanced_PCR='equal-sized standardized blocks differ by one global factor only',matrix_hash=sha(paths('G','v1')[1]/'climate_candidates_197.parquet'))
    if (out/'configuration.json').exists() and json.loads((out/'configuration.json').read_text())!=config:raise ValueError('Checkpoint configuration changed')
    (out/'configuration.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    predictions=[];registry=[];tuning=[]
    for index,(protocol,rep,fold,tr,va,inner) in enumerate(splits):
        key=dict(protocol=protocol,repeat=rep,fold=fold,experiment=NAME)
        stem=f'{protocol}_{rep:02d}_{fold:02d}'
        checkpoint=out/'checkpoints'/f'{stem}.joblib'
        if checkpoint.exists():pack=joblib.load(checkpoint)
        else:
            search=tune_pcr(train.iloc[tr],train.iloc[tr][TARGET],inner);est=search.best_estimator_;pred=est.predict(train.iloc[va][COLS])
            pack=dict(predictions=[{**key,ID:pid,'y_true':float(y),'y_pred':float(p)} for pid,y,p in zip(train.iloc[va][ID],train.iloc[va][TARGET],pred)],registry={**key,'selected_K':int(search.best_params_['pca__n_components']),'inner_RMSE':float(-search.best_score_),'n_train':len(tr),'n_validation':len(va)},tuning=[{**key,'K':p['pca__n_components'],'inner_RMSE':float(-score)} for p,score in zip(search.cv_results_['params'],search.cv_results_['mean_test_score'])])
            joblib.dump(est,out/'models'/f'{stem}_{NAME}.joblib',compress=3);joblib.dump(pack,checkpoint,compress=3)
        predictions.extend(pack['predictions']);registry.append(pack['registry']);tuning.extend(pack['tuning'])
        if (index+1)%10==0 or index==len(splits)-1:print(f'H extension PCR {index+1}/{len(splits)}',flush=True)
    p=pd.DataFrame(predictions);p.to_parquet(out/'tables/30_new_pcr_oof.parquet',index=False)
    pd.DataFrame(registry).to_csv(out/'tables/31_pcr_registry.csv',index=False);pd.DataFrame(tuning).to_csv(out/'tables/32_inner_K_selection.csv',index=False)
    old=pd.read_parquet(paths('H','v1')[0]/'tables/31_oof_individual.parquet');old=old[old.experiment.isin(['H0_MEAN','H1_RAIN','H3_TMAX','H6_RAIN_TMAX'])]
    previous=pd.read_parquet(E8/'tables/30_e8_oof_predictions.parquet');previous=previous[previous.experiment.eq('E8_PCR')].copy();previous['experiment']='H_EXT_CACHED_RAIN_PCR'
    combined=pd.concat([p,old,previous[p.columns]],ignore_index=True)
    ref=p[['protocol','repeat','fold',ID,'y_true']]
    for name,z in combined.groupby('experiment'):
        paired=z.merge(ref,on=['protocol','repeat','fold',ID],suffixes=('','_ref'),validate='one_to_one')
        if len(z)!=len(ref) or len(paired)!=len(ref) or not np.array_equal(paired.y_true,paired.y_true_ref):raise ValueError('Comparisons have different OOF rows')
    combined.to_parquet(out/'tables/39_comparison_oof.parquet',index=False)
    return combined

def finish(q,p,out):
    c,f,r=summarize(p,out)
    folds=[];repeats=[];summaries=[]
    for base in ['H6_RAIN_TMAX','H1_RAIN','H_EXT_CACHED_RAIN_PCR']:
        for protocol,z in f.groupby('protocol'):
            a=z[z.experiment.eq(base)].merge(z[z.experiment.eq(NAME)],on=['repeat','fold'],suffixes=('_base','_PCR'),validate='one_to_one');delta=a.RMSE_base-a.RMSE_PCR
            rr=r[r.protocol.eq(protocol)];b=rr[rr.experiment.eq(base)].merge(rr[rr.experiment.eq(NAME)],on='repeat',suffixes=('_base','_PCR'),validate='one_to_one');dr=b.RMSE_base-b.RMSE_PCR
            for row in a.itertuples():folds.append(dict(protocol=protocol,base=base,repeat=row.repeat,fold=row.fold,delta_RMSE=row.RMSE_base-row.RMSE_PCR))
            for row in b.itertuples():repeats.append(dict(protocol=protocol,base=base,repeat=row.repeat,delta_RMSE=row.RMSE_base-row.RMSE_PCR))
            summaries.append(dict(protocol=protocol,base=base,mean_repeat_delta_RMSE=dr.mean(),mean_fold_delta_RMSE=delta.mean(),positive_fold_fraction=float((delta>1e-10).mean()),fold_delta_sd=delta.std(),fold_delta_q25=delta.quantile(.25),fold_delta_q75=delta.quantile(.75),repeat_delta_sd=dr.std() if len(dr)>1 else np.nan))
    deltas=pd.DataFrame(summaries);deltas.to_csv(out/'tables/43_paired_improvement_summary.csv',index=False);pd.DataFrame(folds).to_csv(out/'tables/44_paired_fold_deltas.csv',index=False);pd.DataFrame(repeats).to_csv(out/'tables/45_paired_repeat_deltas.csv',index=False)
    registry=pd.read_csv(out/'tables/31_pcr_registry.csv');registry.groupby(['protocol','selected_K']).size().rename('count').to_csv(out/'tables/46_selected_K_counts.csv')
    fig,ax=plt.subplots(figsize=(12,5));sns.barplot(data=c,x='RMSE_mean',y='experiment',hue='protocol',ax=ax);ax.set_xlabel('RMSE media de repeticiones OOF completas (t/ha)');save(fig,out,'40_predictive_comparison.png')
    fig,ax=plt.subplots(figsize=(9,4));sns.heatmap(deltas.pivot(index='base',columns='protocol',values='mean_repeat_delta_RMSE'),annot=True,fmt='.4f',center=0,cmap='coolwarm',ax=ax);ax.set_title('RMSE referencia − PCR nueva; positivo = mejora');save(fig,out,'41_paired_improvements.png')
    dimensions=pd.read_csv(out/'tables/16_effective_dimensions.csv');geo=pd.read_csv(out/'tables/17_pc_geographic_associations.csv');signal=pd.read_csv(out/'tables/18_intensity_timing_temperature.csv')
    reading=[]
    for weighting in ['parcel','equal_profile']:
        b=pd.read_csv(out/'tables'/f'12_{weighting}_Rain_Tmax_block_contributions.csv',index_col=0)
        v=pd.read_csv(out/'tables'/f'10_{weighting}_Rain_Tmax_variance.csv')
        for pc in ['PC1','PC2','PC3']:
            a=signal[(signal.weighting==weighting)&(signal.representation=='Rain_Tmax')&(signal.component==pc)].iloc[0]
            reading.append(dict(weighting=weighting,component=pc,variance_fraction=v.set_index('component').loc[pc,'variance_fraction'],rain_squared_loading_share=b.loc['rain',pc],tmax_squared_loading_share=b.loc['tmax',pc],rain_total_correlation=a.rain_total_pearson,tmax_mean_correlation=a.tmax_mean_pearson))
    reading=pd.DataFrame(reading);reading.to_csv(out/'tables/20_joint_PC_interpretation.csv',index=False)
    narrative=interpretation(q,reading,geo,signal,c,deltas,out)
    decisions=[]
    for base in deltas.base.unique():
        z=deltas[deltas.base.eq(base)];decisions.append(dict(base=base,consistent_descriptive_improvement=bool((z.mean_repeat_delta_RMSE>.005).all() and (z.positive_fold_fraction>=.6).all()),independent_validation=False))
    (out/'report/predictive_decision.json').write_text(json.dumps(decisions,indent=2),encoding='utf-8')
    report=f'''# H — Extensión de estructura climática: precipitación + Tmax

## Alcance y conservación

Extensión de H, sin sección I: 14 valores mensuales originales, abril–octubre de 2025. Las mismas 197 parcelas para descripción, 138 etiquetas para evaluación y 59 sin Y. No entran Tmin, suelo, satélite, estado, municipio, coordenadas o altitud como predictores de rendimiento. Se conservan las matrices y modelos previos, G/H v1 y Champion por hashes. Se añade una sola especificación predictiva: PCR conjunta OLS, 65 folds externos; H6, lluvia sola, Tmax sola y PCR de lluvia se reutilizan desde cache.

## PCA por parcela y por perfil

Se comparan lluvia, Tmax y lluvia+Tmax, con StandardScaler y PCA SVD. Para 197 parcelas se reutilizan exactamente las PCA descriptivas de lluvia y Tmax ya existentes. Como sensibilidad, se ajusta cada PCA dando el mismo peso a los 53 vectores exactos: una fila por perfil. Los scores descriptivos nunca alimentan la regresión PCR validada.

{table_text(dimensions)}
**El balance por bloques no cambia la estructura de esta PCA:** hay siete columnas de lluvia y siete Tmax, todas estandarizadas. Dividir cada bloque por sqrt(7) multiplica toda la matriz por la misma constante. Las direcciones, porcentajes de varianza y separación relativa son iguales; scores se dividen por sqrt(7) y autovalores por 7. Tabla 19 verifica equivalencia. Se conserva esta variante descriptiva solicitada y no se duplica una regresión equivalente.

Los biplots muestran eigenvectores multiplicados por un factor explícito solo para legibilidad, colores azul=lluvia y rojo=Tmax. El signo de los PC es arbitrario. Estado/municipio colorean los scores y altitud tiene escala continua. En la sensibilidad de perfiles, coordenadas y altitud son medias de sus parcelas; perfiles que cruzan límites administrativos se etiquetan Mixto. Tabla 01 conserva rangos altitudinales y tamaño original. Municipios numerosos y pocos perfiles pueden producir separación descriptiva mecánica; no se confirman clusters.

## Intensidad, distribución temporal y temperatura

{table_text(reading)}
Las contribuciones por bloque son sumas de cargas cuadradas. La correlación con lluvia total distingue intensidad; tabla 18 añade correlaciones con las siete proporciones mensuales para describir distribución temporal, y con Tmax media para distinguir temperatura. Las proporciones suman uno y sus correlaciones no son efectos independientes. Las cargas y correlaciones mes–PC (11, 15) identifican contrastes concretos, sin nombres agronómicos impuestos.

## Geografía y altitud

{table_text(geo[(geo.representation=='Rain_Tmax')&geo.analysis.isin(['Estado','altitude_m','longitude','latitude','coordinates_R2','coordinates_altitude_R2','altitude_incremental_R2_after_coordinates'])])}
Las correlaciones y fracciones de variación entre estados/municipios son descriptivas. Se informa R² del score PC usando coordenadas y luego coordenadas+altitud, y el incremento de R² de altitud. Son ajustes exploratorios del score climático, sin Y y dentro de la muestra; no constituyen evaluación de generalización ni atribución causal. Coordenadas y altitud se correlacionan entre sí. La sensibilidad con 53 perfiles reduce el peso de las concentraciones de parcelas; no elimina dependencia espacial.

La combinación conserva 53 perfiles y la misma partición de ID que lluvia: PCA no distingue parcelas con vectores idénticos, y que los estados se separen visualmente no asegura transferencia geográfica.

## PCR con validación anidada

Mediana, StandardScaler, PCA y OLS se ajustan dentro de cada inner-train; K se elige entre 1–14 por media de RMSE interna, y se reajusta solo con outer-train. Se reutilizan exactamente los 50 folds aleatorios externos e internos y 15 agrupados de H. El protocolo climate_profile conserva la definición de lluvia enero2022–octubre2025; coincide con la partición conjunta exacta en estas parcelas, sin redefinición silenciosa.

{table_text(c)}
H6 y H1 mantienen Elastic Net original. Compararlos con PCR cambia reducción y algoritmo; una diferencia no se atribuye exclusivamente a PCA. La PCR previa de lluvia, seleccionada internamente entre 1–7, permite comparar añadir Tmax bajo el mismo OLS PCR y los mismos folds sin reentrenar antecedentes. Ambos grids consideran todos los K posibles en cada espacio. No se elige escalamiento ni ponderación por perfiles usando resultados externos.

## Comparaciones pareadas y conclusión

{narrative}

{table_text(deltas)}
Positivo=menor RMSE con PCR nueva. Tablas 44–45 conservan cada fold y repetición; tabla 46 la selección K. RMSE principal es media de repeticiones OOF completas de 138 parcelas, no promedio de predicciones ni media de folds. SD y cuartiles son descriptivos: folds/repeticiones superpuestos no son observaciones independientes. En agrupados hay una sola repetición y no se inventa SD entre repeticiones.

Regla descriptiva de mejora consistente (>0.005 t/ha y ≥60% de folds mejorados en cada protocolo): {json.dumps(decisions,ensure_ascii=False)}. Una mejora limitada a random no confirma generalización. La PCA sí aporta una descomposición interpretable de intensidad, distribución y gradientes térmicos; su utilidad predictiva depende de las comparaciones anteriores. Ningún resultado autoriza modificar Champion, seleccionar una arquitectura definitiva ni introducir nuevas variables o experimentos.

## Figuras

'''
    report+='\n'.join(f'![{x.stem}](../figures/{x.name})\n' for x in sorted((out/'figures').glob('*.png')))
    (out/'report/h_rain_tmax_extension.md').write_text(report,encoding='utf-8')
    print(c[['protocol','experiment','RMSE_mean']].round(5).to_string(index=False),flush=True)
    print(deltas.round(5).to_string(index=False),flush=True)

def interpretation(q,reading,geo,signal,comparison,deltas,out):
    """Describe actual axes and observed geographic contrasts without causal claims."""
    summary=[]
    for weighting,frame in [('parcel',q),('equal_profile',profile_frame(q))]:
        model=joblib.load(out/'models'/f'descriptive_{weighting}_Rain_Tmax.joblib')
        scores=model['pca'].transform(model['scaler'].transform(frame[COLS])*model['weights'])
        z=frame.copy();z['rain_total']=z[RAIN].sum(axis=1);z['tmax_cycle_mean']=z[MAX].mean(axis=1)
        for i in range(3):z[f'PC{i+1}']=scores[:,i]
        for state,g in z.groupby('Estado'):
            summary.append(dict(weighting=weighting,state=state,n=len(g),rain_total_mean=g.rain_total.mean(),tmax_cycle_mean=g.tmax_cycle_mean.mean(),altitude_mean_m=g.altitude_m.mean(),PC1_mean=g.PC1.mean(),PC2_mean=g.PC2.mean(),PC3_mean=g.PC3.mean()))
    pd.DataFrame(summary).to_csv(out/'tables/21_state_centroids_climate.csv',index=False)
    a=reading[reading.weighting.eq('parcel')].set_index('component');b=reading[reading.weighting.eq('equal_profile')].set_index('component')
    s=signal[signal.weighting.eq('equal_profile')&signal.representation.eq('Rain_Tmax')].set_index('component')
    geographic=geo[geo.weighting.eq('equal_profile')&geo.representation.eq('Rain_Tmax')].set_index(['component','analysis'])
    t=f"Con peso por parcela, los primeros tres PC acumulan {a.variance_fraction.sum():.2%} de varianza. PC1 tiene {a.loc['PC1','tmax_squared_loading_share']:.1%} de cargas cuadradas en Tmax; PC2 se relaciona con intensidad de lluvia (r={a.loc['PC2','rain_total_correlation']:.2f}) y temperatura en sentido opuesto (r={a.loc['PC2','tmax_mean_correlation']:.2f}).\n\n"
    t+=f"Con peso igual por perfil, los tres PC acumulan {b.variance_fraction.sum():.2%}. PC1 representa un contraste más claro: lluvia total r={b.loc['PC1','rain_total_correlation']:.2f} y Tmax media r={b.loc['PC1','tmax_mean_correlation']:.2f}, es decir, perfiles más lluviosos y frescos frente a menos lluviosos y cálidos. No es la misma orientación del PC1 ponderado por parcelas; los puntos repetidos influyen en la covarianza y en su orden.\n\n"
    t+=f"PC2 de perfiles distingue distribución temporal: proporción de lluvia en mayo r={s.loc['PC2','rain_share_may_pearson']:.2f} y octubre r={s.loc['PC2','rain_share_oct_pearson']:.2f}. También combina temperatura; no es un eje exclusivamente de lluvia. PC3 contrasta especialmente agosto (r={s.loc['PC3','rain_share_aug_pearson']:.2f}) con mayo (r={s.loc['PC3','rain_share_may_pearson']:.2f}).\n\n"
    t+='Los centroides por estado muestran separación de Tlaxcala sobre PC2 y solapamiento parcial entre Puebla e Hidalgo; dentro de cada estado hay dispersión. La tabla conserva la versión por parcela y por perfil, y Mixto identifica perfiles compartidos entre estados:\n'+table_text(pd.DataFrame(summary))
    t+=f"El PC2 con peso por perfil tiene correlación con longitud {geographic.loc[('PC2','longitude'),'value']:.2f} y altitud {geographic.loc[('PC2','altitude_m'),'value']:.2f}. Coordenadas explican {geographic.loc[('PC2','coordinates_R2'),'value']:.1%} de su variación dentro de la muestra; añadir altitud eleva ese R² a {geographic.loc[('PC2','coordinates_altitude_R2'),'value']:.1%}. PC1 añade un contraste altitudinal: el incremento de R² de altitud tras coordenadas es {geographic.loc[('PC1','altitude_incremental_R2_after_coordinates'),'value']:.1%}. Estas cifras explican scores climáticos, no rendimientos ni transferencia.\n\n"
    rain=deltas[deltas.base.eq('H_EXT_CACHED_RAIN_PCR')].set_index('protocol')
    h6=deltas[deltas.base.eq('H6_RAIN_TMAX')].set_index('protocol')
    t+=f"La PCR conjunta mejora frente a H6 en random en {h6.loc['random','mean_repeat_delta_RMSE']:.5f} t/ha y por perfil en {h6.loc['climate_profile','mean_repeat_delta_RMSE']:.5f}, pero empeora en municipal en {abs(h6.loc['municipality','mean_repeat_delta_RMSE']):.5f}. Frente a la PCR de lluvia, con el mismo algoritmo, mejora random en {rain.loc['random','mean_repeat_delta_RMSE']:.5f} y por perfil apenas {rain.loc['climate_profile','mean_repeat_delta_RMSE']:.5f}; empeora municipal en {abs(rain.loc['municipality','mean_repeat_delta_RMSE']):.5f} y espacial en {abs(rain.loc['spatial','mean_repeat_delta_RMSE']):.5f}.\n\n"
    t+='**Conclusión:** la PCA aporta interpretación de intensidad, distribución temporal y contrastes térmicos y geográficos. La PCR conjunta no aporta una mejora predictiva consistente sobre las referencias: la separación geográfica visible no se traduce en transferencia robusta. Se conserva como investigación de H y no justifica cambios al Champion.\n'
    return t

def run(run_id):
    out=initialize(run_id);q,train=load()
    if not (out/'descriptive_complete.json').exists():describe(q,out)
    p=model(train,out);finish(q,p,out);verify_protected(out)
    write_manifest(out)
    print('H rain+Tmax extension complete; original artifacts unchanged',flush=True)

def write_manifest(out):
    import platform,importlib.metadata
    source=Path(__file__)
    sources=[source,ROOT/'scripts/modeling/322_h_rain_tmax_extension.py',ROOT/'tests/test_h_rain_tmax_extension.py',ROOT/'documentation/h_rain_tmax_extension.md']
    manifest=dict(status='complete',section='H extension precipitation + Tmax',n=197,n_profiles=53,n_labeled=138,predictive_specs_added=1,outer_fits=65,hidden_y_used=False,previous_results_unchanged=True,source_hash=sha(source),python=platform.python_version(),packages={p:importlib.metadata.version(p) for p in ['numpy','pandas','scikit-learn','geopandas']},source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sources if p.exists()},artifacts={str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file() and 'checkpoints' not in f.parts and f.name!='manifest.json'})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
