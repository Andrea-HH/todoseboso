"""Exploratory single-variable screening, using existing outer split assignments."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/research/family_1/variable_strength_screening/v1'
OUT.mkdir(parents=True,exist_ok=True)
ID='ID_POLIGONO'
files=['features/family1_features_all.parquet','m_historical_multisensor/v1/m_features_197_target_free.parquet','i_climate_conditioned_geographic_edaphological/v1/soil_attributes.parquet']
d=None
for f in files:
    z=pd.read_parquet(ROOT/'data/processed/family_1'/f)
    d=z if d is None else d.merge(z[[ID]+[c for c in z if c not in d]],on=ID,validate='one_to_one')
geo=pd.read_parquet(ROOT/'data/processed/family_1/i_climate_conditioned_geographic_edaphological/v1/integrated_diagnostic_197.parquet')
labels=pd.read_csv(ROOT/'outputs/research/family_1/soil_yield_quartile_analysis/v1/parcel_quartiles.csv')
d=labels.merge(d,on=ID,validate='one_to_one').set_index(ID)
profile=geo.set_index(ID).loc[d.index,'climate_profile']
cols=[c for c in d.select_dtypes(include='number') if c not in ['y_true','longitude','latitude','AREA_HA','soil_assignment_reserve'] and not c.startswith('soil_boundary') and not c.startswith('soil_share_key')]
X=d[cols].replace([np.inf,-np.inf],np.nan)
support=X.notna().sum(); unique=X.nunique()
cols=[c for c in cols if support[c]>=110 and unique[c]>=8]
X=X[cols]; y=d.y_true.to_numpy(); groups=profile.to_numpy()
within=X-X.groupby(groups).transform('mean')
wy=pd.Series(y,index=X.index)-pd.Series(y,index=X.index).groupby(groups).transform('mean')
corr=X.corrwith(pd.Series(y,index=X.index)); wcorr=within.corrwith(wy)
oof=pd.read_parquet(ROOT/'outputs/modeling/family_1/j_incremental_geographic_edaphological_yield/v1/tables/02_oof_predictions.parquet')
b=oof[oof.experiment.eq('J0_RAIN')]
records=[]
for (protocol,repeat),rep in b.groupby(['protocol','repeat']):
    pred=np.full((len(d),len(cols)),np.nan)
    baseline=np.full(len(d),np.nan)
    for fold,val in rep.groupby('fold'):
        va=d.index.isin(val[ID]);tr=~va
        a=X.to_numpy()[tr];v=X.to_numpy()[va]
        med=np.nanmedian(a,axis=0);med=np.where(np.isfinite(med),med,0)
        a=np.where(np.isfinite(a),a,med);v=np.where(np.isfinite(v),v,med)
        mean=a.mean(axis=0);sd=a.std(axis=0);sd=np.where(sd>1e-12,sd,1)
        a=(a-mean)/sd;v=(v-mean)/sd
        beta=a.T@(y[tr]-y[tr].mean())/(np.sum(a*a,axis=0)+1)
        pred[va]=y[tr].mean()+v*beta
        baseline[va]=val.set_index(ID).loc[d.index[va],'y_pred']
    assert np.isfinite(pred).all()
    for q in ['ALL','Q1','Q4']:
        mask=np.ones(len(d),bool) if q=='ALL' else d.quartile.eq(q).to_numpy()
        rmse=np.sqrt(((pred[mask]-y[mask,None])**2).mean(axis=0))
        ref=np.sqrt(((baseline[mask]-y[mask])**2).mean())
        for c,e in zip(cols,rmse):records.append(dict(variable=c,protocol=protocol,repeat=repeat,stratum=q,rmse=e,rain_rmse=ref,delta_vs_rain=e-ref))
r=pd.DataFrame(records);r.to_csv(OUT/'repeat_metrics.csv',index=False)
s=r.groupby(['variable','protocol','stratum'])[['rmse','rain_rmse','delta_vs_rain']].mean().reset_index()
s['correlation']=s.variable.map(corr);s['within_profile_correlation']=s.variable.map(wcorr)
s['support']=s.variable.map(support)
s.to_csv(OUT/'screening_summary.csv',index=False)
pd.DataFrame({'correlation':corr,'within_profile_correlation':wcorr,'support':support.reindex(cols)}).to_csv(OUT/'associations.csv')
print('VARIABLES',len(cols))
for q in ['Q1','Q4','ALL']:
    print(q,s[(s.protocol=='random')&(s.stratum==q)].sort_values('rmse').head(12)[['variable','rmse','delta_vs_rain','within_profile_correlation']].to_string(index=False))
print('WITHIN PROFILE',wcorr.abs().sort_values(ascending=False).head(15).to_string())
