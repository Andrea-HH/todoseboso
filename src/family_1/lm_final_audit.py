"""Read-only checks and supplementary quality interpretation; no predictive fits."""
import json
import numpy as np
import pandas as pd
from . import lm_multiblock as lm
ROOT,ID=lm.ROOT,lm.ID

def satellite_quality(version='v1'):
    out,proc=lm.locations('M',version);quality=pd.read_parquet(proc/'m_quality_by_parcel.parquet');rows=[];annual=[]
    from .m_satellite import S2_INDICES,MONTHS,distribution
    for label,sensor,indices in [('S2','sentinel',S2_INDICES),('PLANET','planet',['ndvi','evi']),('LANDSAT','landsat',['vi6t'])]:
        source=pd.read_parquet(ROOT/f'data/processed/family_1/timeseries/{sensor}_timeseries.parquet')
        current=source[source.fecha_captura.between('2025-04-01','2025-10-31')]
        for pid,g in current.groupby(ID):
            valid=g.loc[g[indices[0]+'_promedio'].notna(),'fecha_captura'].sort_values();gaps=valid.diff().dt.days.dropna()
            rows.append(dict(sensor=label,ID_POLIGONO=pid,n_observation_dates=len(g),n_valid_dates=len(valid),median_valid_gap_days=gaps.median(),max_valid_gap_days=gaps.max(),fraction_cloud_missing=g.cloud_raw.isna().mean(),provider_cloud_mean=g.cloud_raw.mean(),method='date count, not verified scene/image count; native parcel aggregate'))
        if sensor=='sentinel':
            src=source[source.fecha_captura.dt.month.between(4,10)&source.fecha_captura.le(pd.Timestamp('2025-10-31'))]
            monthly=src.groupby([ID,'year','month'])[[i+'_promedio' for i in indices]].mean().reset_index()
            for idx in indices:
                tables={int(year):g.pivot(index=ID,columns='month',values=idx+'_promedio').reindex(columns=MONTHS) for year,g in monthly.groupby('year')}
                for pid in tables[2025].index:
                    cur=tables[2025].loc[pid].to_numpy(float);past=[]
                    for year in [2022,2023,2024]:
                        hist=tables[year].loc[pid].to_numpy(float);mask=np.isfinite(cur)&np.isfinite(hist)
                        a=distribution(np.where(mask,cur,np.nan));b=distribution(np.where(mask,hist,np.nan));past.append(b)
                        annual.append({ID:pid,'index':idx,'comparison':str(year),'matched_months':int(mask.sum()),**{'delta_'+s:a[s]-b[s] if mask.sum()>=4 else np.nan for s in ['mean','std','range','min','max','q25','q75']}})
                    full=distribution(cur)
                    annual.append({ID:pid,'index':idx,'comparison':'mean_annual_statistic_2022_2024','matched_months':np.nan,**{'delta_'+s:full[s]-np.nanmean([p[s] for p in past]) for s in ['mean','std','range','min','max','q25','q75']}})
    pd.DataFrame(rows).to_csv(out/'tables/36_current_temporal_support.csv',index=False)
    pd.DataFrame(annual).to_parquet(proc/'annual_distribution_delta_sensitivity_descriptive.parquet',index=False)
    refs=pd.read_parquet(proc/'historical_reference_support.parquet')
    refs.groupby(['sensor','index']).agg(mean_years=('n_years','mean'),mean_historical_observations=('n_historical_valid_observations','mean'),min_historical_observations=('n_historical_valid_observations','min'),min_current_observations=('n_current_valid_observations','min'),fraction_sparse_reserve=('sparse_observation_reserve','mean'),fraction_available=('reference_available','mean')).reset_index().to_csv(out/'tables/37_reference_observation_support.csv',index=False)
    # Additional strata quantify error vs native source quality, without another model.
    p=pd.read_parquet(out/'tables/10_oof_predictions.parquet');q=quality.set_index(ID);errors=[]
    for (protocol,experiment,repeat),g in p.groupby(['protocol','experiment','repeat']):
        for label in ['S2','PLANET','LANDSAT']:
            v=g[ID].map(q[label+'_current_valid_fraction']);cloud=g[ID].map(q[label+'_current_cloud_mean'])
            for name,mask in [('valid_fraction_lt_half',v<.5),('valid_fraction_ge_half',v>=.5),('cloud_mean_gt50',cloud>50),('cloud_mean_le50',cloud<=50)]:
                z=g[mask]
                if len(z):errors.append(dict(protocol=protocol,experiment=experiment,repeat=repeat,sensor=label,stratum=name,n=len(z),**lm.k.metrics(z.y_true,z.y_pred)))
    pd.DataFrame(errors).to_csv(out/'tables/38_native_quality_error_sensitivity.csv',index=False)
    print('M quality support and annual-distribution sensitivities complete; no refits',flush=True)

def validate(section,version='v1'):
    out,proc=lm.locations(section,version);config=json.loads((out/'configuration.json').read_text());d=pd.read_parquet(proc/f'{section.lower()}_features_197_target_free.parquet')
    t=lm.k.j.supervised_data(d,pd.read_csv(lm.k.j.MASTER));splits,table,groups=lm.k.j.load_frozen_splits(t)
    p=pd.read_parquet(out/'tables/10_oof_predictions.parquet');train_ids=set(t[ID]);hidden_ids=set(d[ID])-train_ids
    assert len(p)==1794*len(config['specs']) and not set(p[ID])&hidden_ids and lm.TARGET not in d
    for _,z in p.groupby(['protocol','experiment','repeat']):assert len(z)==138 and z[ID].is_unique and np.isfinite(z.y_pred).all()
    residual_names=[name for name,s in config['specs'].items() if s['kind']=='residual'];r=p[p.experiment.isin(residual_names)]
    assert np.allclose(r.y_pred,r.y_base+r.correction) and np.allclose(r.correction,r.eta*r.proposed_correction)
    group_values={protocol:groups[protocol].to_dict() for protocol in ['climate_profile','municipality','spatial']}
    provenance=pd.read_csv(out/'tables/14_crossfit_provenance.csv')
    for row in provenance.itertuples():
        a=set(json.loads(row.fit_ids));b=set(json.loads(row.heldout_ids));assert not a&b and a|b<=train_ids
        if row.protocol!='random':assert not {group_values[row.protocol][x] for x in a}&{group_values[row.protocol][x] for x in b}
        for aa,bb in json.loads(row.tuning_folds):
            assert not set(aa)&set(bb) and set(aa)|set(bb)==a and not b&(set(aa)|set(bb))
            if row.protocol!='random':assert not {group_values[row.protocol][x] for x in aa}&{group_values[row.protocol][x] for x in bb}
    # Per-fold ID/label alignment and base-cache reproduction were also strict gates during training.
    for protocol,rep,fold,tr,va,inner in splits:
        z=p[(p.protocol==protocol)&(p['repeat']==rep)&(p.fold==fold)]
        for name,q in z.groupby('experiment'):
            assert set(q[ID])==set(t.iloc[va][ID]);truth=t.set_index(ID).loc[q[ID],lm.TARGET].to_numpy();assert np.allclose(q.y_true,truth)
    result=dict(status='passed',n_experiments=len(config['specs']),n_predictions=len(p),n_models=len(list((out/'models').glob('*.joblib'))),n_crossfit_provenance_rows=len(provenance),label_and_group_exclusion=True,hidden_y_used=False,baseline_reproduction_tolerance=1e-8,all_197_features_target_free=True)
    (out/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(section,'PROVENANCE PASSED',result,flush=True)
    return result
