"""M: bounded prespecified temporal summaries, historical support and multisensor EN."""
import json
import numpy as np
import pandas as pd
from . import lm_multiblock as lm
from . import k_geographic_edaphological as k
ROOT,ID,TARGET=lm.ROOT,lm.ID,lm.TARGET
S2_INDICES=['ndvi','evi','ndwi','msi']
PLANET_INDICES=['ndvi','evi']
MONTHS=list(range(4,11))

def aligned_history(monthly,index,minimum_years=2):
    """Same calendar month, equal weight to pre2025 annual monthly means."""
    history=monthly[monthly.year.between(2022,2024)]
    means=history.groupby([ID,'month'])[index].mean()
    counts=history.groupby([ID,'month'])[index].count()
    baseline=means.where(counts>=minimum_years)
    return baseline,counts

def distribution(z):
    z=np.asarray(z,float);valid=np.isfinite(z);v=z[valid];m=np.array(MONTHS)[valid]
    if not len(v):return {n:np.nan for n in ['mean','median','std','min','max','range','q25','q75','slope','peak_month','min_month','early_mean','late_mean','integral_calendar']}
    return dict(mean=np.mean(v),median=np.median(v),std=np.std(v,ddof=1) if len(v)>1 else np.nan,min=np.min(v),max=np.max(v),range=np.ptp(v),q25=np.quantile(v,.25),q75=np.quantile(v,.75),slope=np.polyfit(m,v,1)[0] if len(v)>1 else np.nan,peak_month=m[np.argmax(v)],min_month=m[np.argmin(v)],early_mean=np.mean(v[m<=6]) if (m<=6).any() else np.nan,late_mean=np.mean(v[m>=9]) if (m>=9).any() else np.nan,integral_calendar=float(np.trapezoid(v,m)) if len(v)==7 else np.nan)

def features(version='v1'):
    lout,_=lm.locations('L',version)
    if not (lout/'manifest.json').exists():raise ValueError('Finish L before constructing M features')
    d,t,c,soil,units=lm.load_l();out,proc=lm.locations('M',version)
    for path in [out,proc,out/'tables',out/'figures',out/'report']:path.mkdir(parents=True,exist_ok=True)
    features=d.copy();quality=pd.DataFrame({ID:d[ID]});dictionary=[];temporal=[];references=[];paired_dates=[];source_audit=[]
    blocks={'S2':[],'HISTORY':[],'PLANET':[],'LANDSAT':[]}
    monthly_by_sensor={}
    for sensor,indices in [('S2',S2_INDICES),('PLANET',PLANET_INDICES),('LANDSAT',['vi6t'])]:
        filename={'S2':'sentinel','PLANET':'planet','LANDSAT':'landsat'}[sensor]
        source=pd.read_parquet(ROOT/f'data/processed/family_1/timeseries/{filename}_timeseries.parquet')
        source=source[source.fecha_captura.dt.month.between(4,10)&source.fecha_captura.le(pd.Timestamp('2025-10-31'))].copy()
        means=[idx+'_promedio' for idx in indices]
        if not set(means)<=set(source):raise ValueError('Prespecified spectral index absent')
        monthly=source.groupby([ID,'year','month'])[means].mean().reset_index()
        monthly_by_sensor[sensor]=monthly
        current=source[source.year.eq(2025)]
        curmonth=monthly[monthly.year.eq(2025)]
        nc=curmonth.set_index([ID,'month'])[means].notna().any(axis=1).groupby(ID).sum()
        quality[sensor+'_current_valid_months']=quality[ID].map(nc).fillna(0).astype(int)
        nc=current.groupby(ID)[means[0]].count();quality[sensor+'_current_valid_observations']=quality[ID].map(nc).fillna(0).astype(int)
        cloud=current.groupby(ID).cloud_raw.mean();quality[sensor+'_current_cloud_mean']=quality[ID].map(cloud)
        q=current.groupby(ID).apply(lambda g:g[means].notna().any(axis=1).mean(),include_groups=False)
        quality[sensor+'_current_valid_fraction']=quality[ID].map(q).fillna(0)
        srcstats=dict(sensor=sensor,indices=','.join(indices),years=','.join(str(int(x)) for x in sorted(source.year.unique())),period='Apr-Oct; cutoff2025-10-31',n_rows=len(source),cloud_missing=int(source.cloud_raw.isna().sum()),n_parcels_any_valid=int((quality[sensor+'_current_valid_months']>0).sum()),primary_mask='native finite values, no new cloud cutoff',spatial_quantiles='not supplied; q25/q75 below are TEMPORAL monthly-mean percentiles',availability_dates='not supplied separately from fecha_captura')
        source_audit.append(srcstats)
        for idx in indices:
            column=idx+'_promedio';wide=curmonth.pivot(index=ID,columns='month',values=column).reindex(index=d[ID],columns=MONTHS)
            for month in MONTHS:
                name=f'{sensor}_{idx}_month_{month:02d}'
                features[name]=wide[month].to_numpy();blocks[sensor].append(name)
                dictionary.append(dict(feature=name,sensor=sensor,index=idx,transformation='2025 arithmetic mean of valid native observations in calendar month',window=f'2025-{month:02d}',predictive=True))
            current_stats={pid:distribution(row) for pid,row in zip(d[ID],wide.to_numpy())}
            for pid,stats in current_stats.items():temporal.append({ID:pid,'sensor':sensor,'index':idx,**stats})
            if sensor=='PLANET':
                for statistic in ['std','derived_range']:
                    col=idx+'_'+statistic
                    if col not in current:raise ValueError('Planet heterogeneity source missing')
                    values=current.groupby(ID)[col].median();name=f'PLANET_{idx}_spatial_{statistic}_temporal_median'
                    features[name]=features[ID].map(values);blocks[sensor].append(name)
                    dictionary.append(dict(feature=name,sensor=sensor,index=idx,transformation='temporal median of supplied within-parcel spatial statistic; not raw-pixel percentile',window='Apr-Oct2025',predictive=True))
                name=f'PLANET_{idx}_temporal_q75_minus_q25'
                features[name]=[current_stats[pid]['q75']-current_stats[pid]['q25'] for pid in d[ID]];blocks[sensor].append(name)
                dictionary.append(dict(feature=name,sensor=sensor,index=idx,transformation='IQR of seven monthly means, temporal not spatial',window='Apr-Oct2025',predictive=True))
            if sensor=='LANDSAT':
                for statistic in ['mean','std','slope']:
                    name=f'LANDSAT_{idx}_{statistic}';features[name]=[current_stats[pid][statistic] for pid in d[ID]];blocks[sensor].append(name)
                    dictionary.append(dict(feature=name,sensor=sensor,index=idx,transformation='statistic of monthly means; VI6T not assumed equivalent to S2/Planet NDVI',window='Apr-Oct2025',predictive=True))
            if sensor in ['S2','LANDSAT']:
                baseline,years=aligned_history(monthly,column)
                h=baseline.unstack('month').reindex(index=d[ID],columns=MONTHS)
                n=years.unstack('month').reindex(index=d[ID],columns=MONTHS).fillna(0)
                n_hist_obs=source[source.year.between(2022,2024)].groupby([ID,'month'])[column].count().unstack('month').reindex(index=d[ID],columns=MONTHS).fillna(0)
                n_current_obs=current.groupby([ID,'month'])[column].count().unstack('month').reindex(index=d[ID],columns=MONTHS).fillna(0)
                anomaly=wide-h
                for pid,values,count,hcount,ccount in zip(d[ID],h.to_numpy(),n.to_numpy(),n_hist_obs.to_numpy(),n_current_obs.to_numpy()):
                    for month,v,support,hobs,cobs in zip(MONTHS,values,count,hcount,ccount):references.append({ID:pid,'sensor':sensor,'index':idx,'month':month,'reference_2022_2024':v,'n_years':int(support),'n_historical_valid_observations':int(hobs),'n_current_valid_observations':int(cobs),'reference_available':bool(support>=2),'sparse_observation_reserve':bool(hobs<4 or cobs<2)})
                if sensor=='S2':
                    for month in MONTHS:
                        name=f'HISTORY_{idx}_anomaly_month_{month:02d}';features[name]=anomaly[month].to_numpy();blocks['HISTORY'].append(name)
                        dictionary.append(dict(feature=name,sensor='S2',index=idx,transformation='2025 minus equal-year same-month mean2022-24, >=2validyears',window=f'Apr-Oct2025 vs prior same month {month}',predictive=True))
                    histstats={pid:distribution(row) for pid,row in zip(d[ID],h.to_numpy())}
                    # Four compact history/delta summaries per index:44 history predictors total.
                    for statistic in ['mean','std','range']:
                        name=f'HISTORY_{idx}_delta_{statistic}'
                        values=[]
                        for row,hrow in zip(wide.to_numpy(),h.to_numpy()):
                            mask=np.isfinite(row)&np.isfinite(hrow)
                            a=distribution(np.where(mask,row,np.nan));b=distribution(np.where(mask,hrow,np.nan))
                            values.append(a[statistic]-b[statistic] if mask.sum()>=4 else np.nan)
                        features[name]=values;blocks['HISTORY'].append(name)
                        dictionary.append(dict(feature=name,sensor='S2',index=idx,transformation=f'delta {statistic} on matched calendar months, at least4months; no2025 in history',window='2025 vs2022-24',predictive=True))
                    name=f'HISTORY_{idx}_historical_mean';features[name]=[histstats[pid]['mean'] for pid in d[ID]];blocks['HISTORY'].append(name)
                    dictionary.append(dict(feature=name,sensor='S2',index=idx,transformation='mean historical monthly reference, >=2years per month',window='2022-24',predictive=True))
                    for historical_year in [2022,2023,2024]:
                        hy=monthly[monthly.year.eq(historical_year)].pivot(index=ID,columns='month',values=column).reindex(index=d[ID],columns=MONTHS)
                        for pid,arr in zip(d[ID],(wide-hy).to_numpy()):
                            valid=np.isfinite(arr);temporal.append({ID:pid,'sensor':'S2_individual_year_difference','index':idx,'historical_year':historical_year,'mean':np.nanmean(arr) if valid.any() else np.nan,'valid_matched_months':int(valid.sum())})
        # Cloud sensitivity is descriptive; no additional model matrix selected by outcomes.
        for limit in [20,50]:
            clean=current[current.cloud_raw.le(limit)]
            count=clean.groupby(ID)[means[0]].count();quality[f'{sensor}_observations_cloud_le_{limit}']=quality[ID].map(count).fillna(0)
            avg=clean.groupby(ID)[means[0]].mean();original=current.groupby(ID)[means[0]].mean()
            quality[f'{sensor}_mean_shift_cloud_le_{limit}']=quality[ID].map(avg-original)
    features.to_parquet(proc/'m_features_draft_197_target_free.parquet',index=False)
    quality.to_parquet(proc/'m_quality_by_parcel.parquet',index=False)
    pd.DataFrame(dictionary).to_csv(out/'tables/00_feature_dictionary.csv',index=False)
    pd.DataFrame(source_audit).to_csv(out/'tables/01_sensor_audit.csv',index=False)
    pd.DataFrame(temporal).to_parquet(proc/'temporal_descriptive_statistics.parquet',index=False)
    refs=pd.DataFrame(references);refs.to_parquet(proc/'historical_reference_support.parquet',index=False)
    refs.groupby(['sensor','index']).agg(min_years=('n_years','min'),mean_years=('n_years','mean'),fraction_available=('reference_available','mean')).reset_index().to_csv(out/'tables/02_historical_support.csv',index=False)
    # Actual-band/formula compatibility is not established; names/paired calendars only.
    for idx in PLANET_INDICES:
        a=monthly_by_sensor['S2'][monthly_by_sensor['S2'].year.eq(2025)][[ID,'month',idx+'_promedio']]
        b=monthly_by_sensor['PLANET'][monthly_by_sensor['PLANET'].year.eq(2025)][[ID,'month',idx+'_promedio']]
        q=a.merge(b,on=[ID,'month'],suffixes=('_S2','_Planet'),validate='one_to_one')
        q['difference']=q[idx+'_promedio_Planet']-q[idx+'_promedio_S2'];q['index']=idx;paired_dates.append(q)
    pd.concat(paired_dates,ignore_index=True).to_csv(out/'tables/03_same_calendar_sensor_comparison.csv',index=False)
    pd.DataFrame([dict(feature=c,block=block,n_available=int(features[c].notna().sum()),n_labelled_available=int(features[features[ID].isin(t[ID])][c].notna().sum()),sd=features[c].std(),chosen_by='availability and prior spectral families, never Y') for block,cols in blocks.items() for c in cols]).to_csv(out/'tables/04_predictor_availability.csv',index=False)
    # Map old ANOM/HIST fields: equality means redescription, not new independent source.
    old=pd.read_parquet(ROOT/'data/processed/family_1/features/anomaly_features.parquet').set_index(ID)
    overlap=[]
    for idx in S2_INDICES:
        cols=[f'HISTORY_{idx}_anomaly_month_{m:02d}' for m in MONTHS]
        new=features.set_index(ID)[cols].mean(axis=1);name=f'ANOM_S2_{idx}_promedio_mean'
        if name in old:
            z=pd.concat([new.rename('new'),old[name].rename('old')],axis=1).dropna()
            overlap.append(dict(index=idx,old_feature=name,n=len(z),max_abs_difference=float(abs(z.new-z.old).max()),pearson=z.new.corr(z.old),interpretation='same information when matched support; differences due support guard, not independent spectral observation'))
    pd.DataFrame(overlap).to_csv(out/'tables/05_prior_anomaly_overlap.csv',index=False)
    combos={'M0':['S2'],'M1':['S2','HISTORY'],'M2':['S2','PLANET'],'M3':['S2','LANDSAT'],'M4':['S2','PLANET','LANDSAT'],'M5':['S2','HISTORY','PLANET','LANDSAT']}
    specs={'MB_RAIN':dict(kind='base',base='rain',blocks=[]),'MB_CURRENT':dict(kind='base',base='current',blocks=[])}
    for name,labels in combos.items():
        bs=[(label,blocks[label]) for label in labels]
        specs[name+'_RAW']=dict(kind='standalone',blocks=bs,mode='raw')
        specs[name+'_BLOCK_PCA']=dict(kind='standalone',blocks=bs,mode='block_pca')
        if name in ['M0','M1','M5']:
            for base in ['rain','current']:
                for kind,prefix in [('direct','MA'),('residual','MR')]:specs[f'{prefix}_{base}_{name}']=dict(kind=kind,base=base,blocks=bs,mode='raw')
    lm.setup('M',version,specs,features)
    (out/'representation_policy.json').write_text(json.dumps(dict(block_pca='fit PCA per block, divide by max(root training score energy,1), concatenate and fit final PCA with same total1/2/4component budget across M0-M5',important='selection internal; no whitening, block balancing never amplifies a near-constant block; individual spectral SD floor .05; raw models differ in feature count, hence source gains must be contrasted with common-budget PCA'),indent=2),encoding='utf-8')
    (out/'satellite_blocks.json').write_text(json.dumps(blocks,indent=2),encoding='utf-8')
    print('M FEATURES READY', {name:len(cols) for name,cols in blocks.items()},flush=True)
    return features,quality,blocks

def exploratory(version,d,blocks):
    from .l_representation import pca_tables
    out,proc=lm.locations('M',version);t=k.j.supervised_data(d,pd.read_csv(k.j.MASTER))
    metadata=d[[ID,'Estado','Municipio','climate_profile']+lm.TOPO].merge(t[[ID,TARGET]],on=ID,how='left')
    matrices={}
    for label,cols in blocks.items():
        spec=dict(blocks=[(label,cols)],mode='raw');r=lm.model(spec)['repr'].fit(d);matrices[label]=pd.DataFrame(r.transform(d),columns=r.get_feature_names_out())
        pca_tables(matrices[label],metadata,label,out)
    concat=pd.concat([matrices['S2'],matrices['HISTORY']],axis=1);pca_tables(concat,metadata,'current_history',out)
    both=pd.concat(list(matrices.values()),axis=1);bounds=[];start=0
    for x in matrices.values():bounds.append(list(range(start,start+x.shape[1])));start+=x.shape[1]
    for balanced in [False,True]:pca_tables(both,metadata,'multisensor',out,balanced=balanced,blocks=bounds)
    # New historical dimensions conditional on current spectral levels; target-free.
    x=np.c_[np.ones(len(d)),matrices['S2'].to_numpy()];history=matrices['HISTORY'].to_numpy()
    residual=history-x@np.linalg.lstsq(x,history,rcond=None)[0]
    pd.DataFrame([dict(feature=c,variance_original=np.var(history[:,i]),variance_after_linear_current_projection=np.var(residual[:,i]),fraction_remaining=np.var(residual[:,i])/np.var(history[:,i]) if np.var(history[:,i])>1e-15 else np.nan,role='target-free descriptive, not predictive preprocessing') for i,c in enumerate(matrices['HISTORY'])]).to_csv(out/'tables/06_history_dimensions_beyond_current.csv',index=False)
    # By-index PCA descriptor, never used for prediction or Y-based choice.
    for idx in S2_INDICES:
        cols=[c for c in blocks['S2']+blocks['HISTORY'] if '_'+idx+'_' in c];r=lm.model(dict(blocks=[(idx,cols)],mode='raw'))['repr'].fit(d)
        pca_tables(pd.DataFrame(r.transform(d),columns=cols),metadata,'index_'+idx,out)

def report(version='v1'):
    out,proc=lm.locations('M',version);c=pd.read_csv(out/'tables/40_model_comparison.csv');q=pd.read_csv(out/'tables/01_sensor_audit.csv')
    table=c.pivot(index='experiment',columns='protocol',values='RMSE_mean').reset_index()
    text='# M — Historical and Multisensor Satellite Signal Exploration\n\n'+k.j.markdown_table(q)+'\n\n'+k.j.markdown_table(table)+'\n\nM0=Sentinel2025; M1=actual+historia/anomalías; M2=actual+Planet; M3=actual+Landsat; M4=actual+Planet+Landsat; M5=todos. Cada combinación tiene control raw y PCAporbloque, mismos197/138IDs/folds sin borrar parcelas incompletas. MA/MR soloM0,M1,M5 sobre B1/B2, mismos bloques/escalas/grillas para separar arquitectura. PCApredictivo1/2/4componentes por bloque seleccionado internamente. No se seleccionan combinaciones por RMSEexterno.\n\nSentinelNDVI/EVI/NDWI/MSI:28promedios mensuales. Historia44variables:28anomalías,12diferencias de media/dispersión/rango y4medias históricas. La referencia utiliza solo2022–24 y>=2años válidos por mes, igual peso anual. Diferencias de distribución usan>=4meses emparejados. Cada referencia conserva soporte de años; las no defendibles permanecenNaN y se imputan solo dentro de cada fit. No se utiliza2025 para su propia referencia. Tres años no son normal climatológica. Tabla05 identifica cuánto de anomalías ya estaba en Familia1; son nuevos controles/representaciones, no nuevos datos.\n\nPlanet:14promedios mensualesNDVI/EVI y6estadísticas de heterogeneidad suministrada/dispersión temporal. Mediana y percentiles calculados aquí son TEMPORALES; no se inventan cuantiles de píxeles. Landsat:7mensualidadesVI6T y3resúmenes propios. VI6T no es asumidoNDVI, ni se mezcla como observación intercambiable de Sentinel. Comparación por mes calendario no garantiza misma fecha, bandas, ecuación o calibración; no se atribuye mejora solo a resolución. Tablasfuente no suministran rasters/bandas originales, pesos exactos de intersección, conteo de píxeles, máscaras de píxeles ni fecha separada de procesamiento/disponibilidad; límites explícitos para parcelas pequeñas y pronóstico.\n\nLa calidad retiene valores nativos finitos sin nuevo cutoffde nube. Sensibilidades<=20/50% se describen sin retunear resultados; falta de observaciones, nubes, años y meses se conservan como diagnósticos. No hay interpolación entre sensores ni fechas. Noviembre/diciembre2025 se excluyeron; estudio retrospectivo al31octubre, no pronóstico temprano. Máximos espectrales no son fechas de siembra/emergencia/cosecha.\n\nCross-fitting y selección interna de toda la base climática, sin OOFglobal usado para supervisar correctores. Residuos por etapa en tabla15 y14proveniencia; propuesta,eta,aplicación,final en tabla10. Coeficientes y estabilidad de signos/magnitudes, errores extremos, nubes/faltantes, perfiles, regiones, Chignahuapan y buffers en tablas20–31. Las parejas intraperfil solo usan un mismo modelo externo; distinguir parcelas no garantiza acertar diferencias de rendimiento.\n\nAsociaciones de suelo después de clima+satélite se reportan descriptivamente, no como validación de una tercera etapa. No se añade ninguna etapa al Champion; su historiaSentinel ya contenía resúmenes2022–24. M propone integración solo si la señal geográfica complementaria resulta consistente; folds/repeticiones superpuestos no son evidencia independiente.\n\n![RMSE](../figures/RMSE_protocol.png)\n\n![MAE](../figures/MAE_protocol.png)\n'
    (out/'report/m_report.md').write_text(text,encoding='utf-8');(ROOT/'documentation/m_historical_multisensor.md').write_text(text.replace('../figures/',f'../outputs/modeling/family_1/{lm.NAMES["M"]}/{version}/figures/'),encoding='utf-8')

def soil_after_satellite(version):
    out,proc=lm.locations('M',version);d,t,c,soil,units=lm.load_l()
    p=pd.read_parquet(out/'tables/10_oof_predictions.parquet');rows=[]
    for name in ['MR_rain_M5','MR_current_M5']:
        for protocol,z in p[p.experiment.eq(name)].groupby('protocol'):
            q=z.groupby(ID).agg(y_true=('y_true','first'),y_pred=('y_pred','mean')).reset_index().merge(d,on=ID,validate='one_to_one');q['residual']=q.y_true-q.y_pred
            for col in soil:
                a=q[col]-q.groupby('climate_profile')[col].transform('mean');b=q.residual-q.groupby('climate_profile').residual.transform('mean')
                rows.append(dict(experiment=name,protocol=protocol,feature=col,n=len(q),pearson=q[col].corr(q.residual) if q[col].std()>1e-12 else np.nan,pearson_within=a.corr(b) if a.std()>1e-12 and b.std()>1e-12 else np.nan,role='descriptive OOF association per protocol, not predictive third-stage evidence'))
    pd.DataFrame(rows).to_csv(out/'tables/32_soil_after_satellite_descriptive.csv',index=False)

def run(version='v1',workers=3):
    d,quality,blocks=features(version);exploratory(version,d,blocks);lm.run_models('M',version,workers);soil_after_satellite(version);report(version)
    lout,_=lm.locations('L',version);inv=json.loads((lout/'protected_inputs.json').read_text())
    changed=[p for p,value in inv.items() if k.j.sha(ROOT/p)!=value]
    if changed:raise ValueError('Historical files changed '+str(changed[:4]))
    lm.finish('M',version,dict(previous_results_unchanged=True,Champion_retrained=False));print('M COMPLETE',flush=True)
