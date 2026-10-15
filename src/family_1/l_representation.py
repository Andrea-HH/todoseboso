"""L: target-free multiblock PCA, matched EN architectures, Champion audit gate."""
import json,itertools
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from . import lm_multiblock as lm
from . import k_geographic_edaphological as k
ROOT,ID,TARGET=lm.ROOT,lm.ID,lm.TARGET

def protected_inventory():
    # Snapshot only paths present before L/M; checking this list avoids hashing new outputs.
    paths=[]
    for folder in ['data/original','data/processed','outputs/modeling','outputs/research','src','scripts','documentation']:
        paths += [p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p) and not any(x in str(p) for x in list(lm.NAMES.values())+['lm_multiblock','l_representation','m_satellite','l_m_','329_lm','330_l_','331_m_','332_lm']) and not p.name.startswith(('l_','m_'))]
    return {str(p.relative_to(ROOT)):k.j.sha(p) for p in paths}

def joint_audit(version='v1'):
    out,proc=lm.locations('L',version)
    for p in [out,proc,out/'tables',out/'report']:p.mkdir(parents=True,exist_ok=True)
    inv=out/'protected_inputs.json'
    if not inv.exists():inv.write_text(json.dumps(protected_inventory(),indent=2),encoding='utf-8')
    d,t,c,soil,units=lm.load_l();specs=lm.l_specs(c,soil,units)
    lm.setup('L',version,specs,d)
    correspondence=[
        ('E','315 / rainfall_pcr.py','monthly precipitation PCA/PCR, exact frozen folds','L reuses folds/base; no repeated rain-only PCA search'),
        ('G/H','316–322; climate_signal_modeling.py','temperature PCA, rain+Tmax and joint21 PCR','L adds geographic/edaphological blocks and base48 comparison'),
        ('I/K','323–328; soil parquet matrices','S1 mentions, S2 pooled support, S3 main group, S4 Top3','L primary S1, single S2 Hellinger sensitivity; no ordinal IDs'),
        ('Family1','135; feature_pipeline.build_history_anomaly','monthly 2022–24 means/std and 2025 anomalies already built','M reuses their definition; adds support checks, distribution deltas, controlled multisensor comparisons'),
        ('Family2','201–204 functional preprocessing/fPCA','functional curves and fPCA hybrids already evaluated','M monthly blocks/regularized PCA are a distinct controlled representation, not first functional analysis'),
        ('Family3','301–305 structural modeling','structured/multisource representations','M maps coverage and existing blocks before controlled comparisons'),
        ('Champion','210–212; TOP20 EN -> HISTORY15 XGB -> TOPO Ridge','48 climate features screened20;16 historical S2 effective;25 terrain features','L8 descriptive only unless full nested parameter-selection provenance can be reproduced')]
    pd.DataFrame(correspondence,columns=['previous','code','existing','new_question']).to_csv(out/'tables/00_previous_new_correspondence.csv',index=False)
    satellite=[];monthrows=[]
    for name in ['sentinel','planet','landsat']:
        p=ROOT/f'data/processed/family_1/timeseries/{name}_timeseries.parquet';x=pd.read_parquet(p)
        means=[v for v in x if v.endswith('_promedio')]
        satellite.append(dict(sensor=name,path=str(p.relative_to(ROOT)),sha256=k.j.sha(p),rows=len(x),parcels=x[ID].nunique(),min_observation=str(x.fecha_captura.min()),max_observation=str(x.fecha_captura.max()),years=json.dumps(sorted(x.fecha_captura.dt.year.unique().astype(int).tolist())),mean_index_columns=' | '.join(means),native_statistics='mean,std,min,max; no pixel arrays, per-scene spatial median/quantiles or count',cloud='provider cloud_raw; no local reconstruction of pixel mask',bands='band values not supplied in these parcel-index time tables',observation_date='fecha_captura',acquisition_processing_availability='separate dates not supplied; not assumed equivalent',resolution='catalog reference only: S2 indices commonly10/20m, Planet commonly3m, Landsat commonly30m; actual extraction grids/weights/count absent',spatial_extraction='preaggregated parcel statistics; exact original pixel-inclusion weights not available',quality='retain finite native values; missing counts explicit; no silent parcel removal',cutoff='2025-10-31; Nov/Dec2025 explicitly excluded'))
        q=x[x.fecha_captura.dt.month.between(4,10)&(x.fecha_captura.dt.year<=2025)]
        for (pid,year,month),g in q.groupby([ID,'year','month']):
            monthrows.append(dict(sensor=name,ID_POLIGONO=pid,year=int(year),month=int(month),n_dates=len(g),n_any_valid=int(g[means].notna().any(axis=1).sum()),valid_fraction=float(g[means].notna().any(axis=1).mean()),mean_cloud=g.cloud_raw.mean(),n_cloud_missing=int(g.cloud_raw.isna().sum())))
    pd.DataFrame(satellite).to_csv(out/'tables/01_joint_satellite_source_audit.csv',index=False)
    pd.DataFrame(monthrows).to_csv(out/'tables/02_sensor_month_support.csv',index=False)
    # Stronger full-Champion cross-fitting is not supplied by historical artifacts.
    gate=dict(status='descriptive_only',predictive_L8=False,reason='RS5 archived targets are residuals after climate+history, before final topographic stage. No fully nested cross-fitted predictions of ALL THREE Champion stages with hyperparameter selection restricted to each held-out subtraining are archived. RS4/RS5 reuse outer-fold hyperparameters inside cross-fitting. Retuning all stages and feature selectors would define a new Champion specification and cannot be certified as faithful reproduction of original frozen architecture in this experiment.',files_examined=['210_champion_reconstruction.py','211_second_residual_audit.py','212_residual_architecture_optimization.py'],policy='Do not use global OOF residuals as supervised targets. Report descriptive associations; no Champion models modified/retrained.')
    (out/'l8_validation_gate.json').write_text(json.dumps(gate,indent=2),encoding='utf-8')
    text='# L/M — Auditoría inicial y diseño congelado\n\n'+k.j.markdown_table(pd.DataFrame(correspondence,columns=['Antecedente','Código','Existente','Nueva pregunta']))+'\n\n197 parcelas,138etiquetas y59ocultas;53perfiles completos y43etiquetados. B1 reproduce J0; B2 reproduce las48columnas originales de Climate Current, no TOP20. Ambas bases usan exactamente la misma grilla original alpha .01,.1,1 / l1 .1,.5,.9 y folds. La grilla complementaria conserva K incluyendo .001.\n\nS1 es primaria, sin amplificar coberturas raras. S2 es una sola sensibilidad con soporte>=5 aprendido por fit y Other; Hellinger=sqrt(p), conserva ceros sin pseudoconteos. Los PCA predictivos no se blanquean y seleccionan1/2/4componentes internamente, con cap por dimensión disponible. Las estrategias se comparan con originales y transformaciones equivalentes; cambiar base también cambia representación térmica/temporal y no aísla temperatura.\n\nLa auditoría conjunta verifica antes de entrenar que Sentinel/Landsat poseen2022–2025 y Planet solo2025 en las tablas disponibles. Se reutilizarán NDVI/EVI/NDWI/MSI de Sentinel; Planet NDVI/EVI y estadísticas espaciales suministradas; Landsat VI6T independiente, sin asumir equivalencia espectral con NDVI. No se extraen bandas ni píxeles inexistentes. Historia2022–24 con al menos2años válidos por mes; M0–M5 y PCAsolo por bloque se predefinen; aditivo/residual soloM0,M1,M5 sobre cada base para evitar matriz exhaustiva. M usa28mensualidades actuales,44históricas/anomalías como máximo,20Planet y10Landsat. Sin selección por Y antes de folds.\n\nL8 se limita a auditoría descriptiva por la ausencia de procedencia de cross-fitting anidado de la arquitectura completa y la reutilización histórica de parámetros externos dentro de subfolds. Reajustar toda la selección produciría una variante distinta cuya fidelidad al Champion no se puede certificar. Se conserva este resultado negativo explícito.\n'
    (out/'report/initial_audit.md').write_text(text,encoding='utf-8');(ROOT/'documentation/l_m_initial_audit.md').write_text(text,encoding='utf-8')
    print('Joint audit complete; L design frozen, M feature plan prespecified',flush=True)

def pca_tables(matrix,metadata,name,out,weight='parcel',balanced=False,blocks=None):
    X=np.asarray(matrix,float)
    if not np.isfinite(X).all():raise ValueError('Exploratory PCA requires complete finite matrix')
    if weight=='profile':
        frame=pd.DataFrame(X);frame['profile']=metadata.climate_profile.to_numpy()
        X=frame.groupby('profile').mean().to_numpy()
        numeric=[c for c in metadata if c in lm.TOPO+[TARGET]]
        categorical=[c for c in metadata if c not in numeric+['climate_profile']]
        aggregation={c:'mean' for c in numeric}
        aggregation.update({c:(lambda values:' | '.join(sorted(set(values.dropna().astype(str))))) if c in ['Estado','Municipio'] else 'first' for c in categorical})
        meta=metadata.groupby('climate_profile').agg(aggregation).reset_index()
    else:meta=metadata.reset_index(drop=True)
    if balanced:
        X=X.copy()
        for indices in blocks:
            energy=np.sum(np.var(X[:,indices],axis=0));X[:,indices]/=np.sqrt(energy) if energy>1e-15 else 1
    pca=PCA(svd_solver='full').fit(X);scores=pca.transform(X)
    prefix=name+'_'+weight+('_balanced' if balanced else '')
    variance=pd.DataFrame(dict(component=np.arange(1,len(pca.explained_variance_ratio_)+1),variance=pca.explained_variance_ratio_,cumulative=np.cumsum(pca.explained_variance_ratio_)))
    variance.to_csv(out/'tables'/f'pca_{prefix}_variance.csv',index=False)
    feature_names=list(matrix.columns) if isinstance(matrix,pd.DataFrame) else [f'x{i}' for i in range(X.shape[1])]
    pd.DataFrame(pca.components_.T,index=feature_names,columns=[f'PC{i+1}' for i in range(len(pca.components_))]).to_csv(out/'tables'/f'pca_{prefix}_loadings.csv')
    sc=pd.DataFrame(scores,columns=[f'PC{i+1}' for i in range(scores.shape[1])]);sc=pd.concat([meta.reset_index(drop=True),sc],axis=1)
    sc.to_parquet(out/'tables'/f'pca_{prefix}_scores.parquet',index=False)
    association=[]
    for c in sc.columns:
        if not c.startswith('PC'):continue
        for field in ['altitude_m','slope_degrees',TARGET]:
            if field in sc:
                z=sc[[c,field]].dropna()
                association.append(dict(component=c,field=field,pearson=z[c].corr(z[field]) if z[c].std()>1e-12 and z[field].std()>1e-12 else np.nan,n=len(z),role='descriptive only'))
        for field in ['Estado','Municipio','climate_profile']:
            total=((sc[c]-sc[c].mean())**2).sum();between=sum(len(g)*(g[c].mean()-sc[c].mean())**2 for _,g in sc.groupby(field))
            association.append(dict(component=c,field=field,eta_squared=between/total if total>1e-15 else np.nan,n=len(sc),role='descriptive geography, not generalization'))
    pd.DataFrame(association).to_csv(out/'tables'/f'pca_{prefix}_associations.csv',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,2,figsize=(11,4));axs[0].plot(variance.component,variance.cumulative,'o-');axs[0].set(title=prefix,ylabel='Cumulative explained variance',xlabel='Component')
    for state,g in sc.groupby('Estado'):axs[1].scatter(g.PC1,g.PC2,s=12,label=state,alpha=.6)
    if pca.components_.shape[0]>=2:
        lengths=np.linalg.norm(pca.components_[:2],axis=0);dominant=np.argsort(lengths)[-min(6,len(lengths)):]
        arrow_scale=max(np.ptp(scores[:,0]),np.ptp(scores[:,1]))*.35
        for col in dominant:
            a,b=pca.components_[:2,col]*arrow_scale
            axs[1].arrow(0,0,a,b,color='black',alpha=.55,width=.003,head_width=arrow_scale*.025,length_includes_head=True)
            axs[1].text(a,b,feature_names[col].replace('CLIMATE_','').replace('soil_map_share_mentions_group_','')[:28],fontsize=6)
    axs[1].legend(fontsize=8);axs[1].set(xlabel='PC1',ylabel='PC2');fig.tight_layout();fig.savefig(out/'figures'/f'pca_{prefix}.png',dpi=150);plt.close(fig)
    return sc

def exploratory(version='v1'):
    out,proc=lm.locations('L',version);d,t,c,soil,units=lm.load_l()
    metadata=d[[ID,'climate_profile','Estado','Municipio']+lm.TOPO].merge(t[[ID,TARGET]],on=ID,how='left',validate='one_to_one')
    matrices={'S1':d[soil],'composition_raw':d[units],'composition_hellinger':np.sqrt(d[units])}
    for name,x in matrices.items():
        for weight in ['parcel','profile']:pca_tables(x,metadata,name,out,weight)
    climate=pd.DataFrame(StandardScaler().fit_transform(d[c]),columns=c);top=pd.DataFrame(StandardScaler().fit_transform(d[lm.TOPO]),columns=lm.TOPO)
    for name,parts in [('climate_topo',[climate,top]),('climate_soil',[climate,d[soil]]),('climate_topo_soil',[climate,top,d[soil]])]:
        x=pd.concat(parts,axis=1);bounds=[];start=0
        for p in parts:bounds.append(list(range(start,start+p.shape[1])));start+=p.shape[1]
        for weight in ['parcel','profile']:
            for balanced in [False,True]:pca_tables(x,metadata,name,out,weight,balanced,bounds)
    # Separate block PCA, explanatory only, retain enough PCs to explain95% per block.
    pieces=[]
    for label,x in [('climate',climate),('topography',top),('soil',d[soil])]:
        p=PCA(n_components=.95,svd_solver='full').fit(x);pieces.append(pd.DataFrame(p.transform(x),columns=[label+f'_PC{i+1}' for i in range(p.n_components_)]))
    concatenated=pd.concat(pieces,axis=1);concatenated.insert(0,ID,d[ID]);concatenated.to_parquet(proc/'separate_block_pca_197_descriptive.parquet',index=False)
    champion_audit(version,d,t,soil)
    print('L exploratory PCA and Champion descriptive audit complete',flush=True)

def champion_audit(version,d,t,soil):
    out,proc=lm.locations('L',version)
    ch=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet')
    ch=ch[ch.architecture.eq('A_CURRENT_CH_H_T')].copy();ch['residual']=ch.y_true-ch.y_pred
    per=ch.groupby(ID).agg(y_true=('y_true','first'),residual=('residual','mean'),prediction=('y_pred','mean'),error_sd=('residual','std')).reset_index().merge(d,on=ID,validate='one_to_one')
    pc=pd.read_parquet(out/'tables/pca_S1_parcel_scores.parquet')[[ID]+['PC1','PC2','PC3','PC4']]
    per=per.merge(pc,on=ID);per.to_parquet(out/'tables/05_champion_oof_residuals_descriptive.parquet',index=False)
    rows=[]
    for scope,z in [('all',per),('Chignahuapan',per[per.Municipio.eq('Chignahuapan')])]:
        rwithin=z.residual-z.groupby('climate_profile').residual.transform('mean')
        between=z.groupby('climate_profile').mean(numeric_only=True)
        for col in soil+lm.TOPO+['PC1','PC2','PC3','PC4']:
            within=z[col]-z.groupby('climate_profile')[col].transform('mean')
            rows.append(dict(scope=scope,feature=col,n=len(z),pearson_total=z[col].corr(z.residual) if z[col].std()>1e-12 else np.nan,pearson_within=within.corr(rwithin) if within.std()>1e-12 and rwithin.std()>1e-12 else np.nan,pearson_between=between[col].corr(between.residual) if between[col].std()>1e-12 else np.nan,role='OOF descriptive association; NEVER used as corrector targets'))
    pd.DataFrame(rows).to_csv(out/'tables/06_champion_residual_associations.csv',index=False)
    per.groupby(['Estado','Municipio']).agg(n=(ID,'size'),mean_residual=('residual','mean'),MAE=('residual',lambda x:abs(x).mean()),RMSE=('residual',lambda x:np.sqrt(np.mean(x*x)))).reset_index().to_csv(out/'tables/07_champion_regional_residuals.csv',index=False)

def report(version='v1'):
    out,proc=lm.locations('L',version);c=pd.read_csv(out/'tables/40_model_comparison.csv')
    table=c.pivot(index='experiment',columns='protocol',values='RMSE_mean').reset_index()
    base=c[c.experiment.isin(['L0_BASE','L1_BASE'])][['experiment','protocol','RMSE_mean','MAE_mean','R2_mean','bias_pred_minus_y_mean']]
    text='# L — Multiblock Representation and Residual Complementarity\n\n'+k.j.markdown_table(base)+'\n\nLas dos bases reproducen J0/H8 a tolerancia1e-8, mismos65folds. Climate Current48 no es TOP20 ni Champion. Es una comparación de representación completa, no un efecto exclusivo de temperatura.\n\n'+k.j.markdown_table(table)+'\n\nS1 primaria:10coberturas solapadas que mencionan grupos, sin z-score. S2 sensibilidad:22unidades agrupadas con soporte>=5 por fit y Other. Hellinger h_j=sqrt(p_j): distancia Euclídea en raíces, ceros válidos sin CLR/pseudoconteos. Los PCA se centran sin whitening; PCs1/2/4 se seleccionan en CV interna. L2/L3 sueloPCAresidual; L4/L5 topografía+sueloPCAresidual; LC controles originales y PCAs directos con mismas variables y escalas. L6/L7 mezcla Hellinger, PCAconjunto y control S2natural. Los cambios por rotación también cambian penalización L1; no toda diferencia PCA procede de reducción dimensional.\n\nEl PCA descriptivo usa197parcelas o53perfiles de igual peso, sin usarse para preprocesar predicción. La ponderación equilibrada divide cada bloque por raíz de su varianza total; sensibilidad target-free. Cargas, scores, biplots/scree y eta² estatal/municipal se guardan separados. Clima48 estandarizado puede dominar suelo natural por dimensión/energía; la sensibilidad equilibrada permite distinguir eso de nueva información. PCA no modela interacciones no lineales.\n\nCada corrector utiliza residuos cruzados SOLO de outer-train. La selección interna evalúa base+eta×corrección y regenera/tunea sus propias predicciones climáticas sin sus etiquetas. Se reutiliza el cross-fitting legítimo de K para lluvia, en lectura. BasesCurrent se cruzan con las mismas restricciones geográficas. Proveniencia en tabla14, residuos en15, coeficientes en13/30, decisiones en31.\n\nL8 es exclusivamente descriptivo: no hay cross-fitting anidado y selección de hiperparámetros de TODAS las tres etapas originales archivados; los residuosRS5 preceden topografía. Retunear todo definiría una variante nueva y no garantiza reproducción fiel. Asociaciones del residuo finalChampion con suelo/PCs/topografía e intraperfil no demuestran mejora predictiva. No se entrenó una nueva etapaChampion ni se reutilizaron sus OOF como objetivos.\n\nDiagnósticos: regiones, Chignahuapan(71etiquetas, mismoOOF), bajos<3/altos>5, buffers50/125/250m, claves discrepantes, negativos/extremos conservados y diferencias de parejas evaluadas por el mismo modelo. Más dispersión intraperfil no prueba mejor precisión. Folds/repeticiones correlacionados; margen .01t/ha exploratorio para RMSEgeográfico/MAEen TODOS los protocolos, sin significancia formal.\n\n![RMSE](../figures/RMSE_protocol.png)\n\n![MAE](../figures/MAE_protocol.png)\n'
    (out/'report/l_report.md').write_text(text,encoding='utf-8');(ROOT/'documentation/l_multiblock_representation.md').write_text(text.replace('../figures/',f'../outputs/modeling/family_1/{lm.NAMES["L"]}/{version}/figures/'),encoding='utf-8')

def run(version='v1',workers=3):
    joint_audit(version);exploratory(version);lm.run_models('L',version,workers);report(version)
    out,_=lm.locations('L',version)
    inv=json.loads((out/'protected_inputs.json').read_text())
    changed=[p for p,old in inv.items() if k.j.sha(ROOT/p)!=old]
    if changed:raise ValueError('Historical files changed: '+str(changed[:4]))
    lm.finish('L',version,dict(previous_results_unchanged=True,L8='descriptive_only'));print('L COMPLETE',flush=True)
