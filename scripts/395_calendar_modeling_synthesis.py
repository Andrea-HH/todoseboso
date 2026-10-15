"""Paired diagnostics on sealed OOF; no model fitting or selection."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/modeling/agronomic_calendar/v1'
DEST=OUT/'diagnostics'
if DEST.exists():raise FileExistsError('Preserve diagnostics')
DEST.mkdir()
summary=pd.read_csv(OUT/'tables/metrics_summary.csv');reps=pd.read_csv(OUT/'tables/metrics_by_repeat.csv')
registry=pd.read_csv(OUT/'tables/registry.csv');p=pd.read_parquet(OUT/'tables/oof_predictions.parquet')
meta=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet',columns=['ID_POLIGONO','Estado','Municipio','climate_profile'])
gains=pd.read_parquet(OUT/'tables/parcel_gains.parquet').merge(meta,on='ID_POLIGONO',validate='many_to_one')
grouped=pd.read_csv(OUT/'tables/regional_by_repeat.csv')
grouped.groupby(['experiment','protocol','kind','zone'])[['n','rmse','mae','bias','r2']].mean().reset_index().to_csv(DEST/'regional_summary.csv',index=False)
reg=registry.groupby(['experiment','protocol']).agg(input_columns=('n_input','first'),design_columns=('n_design','first'),mean_effective_df=('effective_df','mean'),min_effective_df=('effective_df','min'),max_effective_df=('effective_df','max')).reset_index()
reg.to_csv(DEST/'complexity.csv',index=False)
registry.groupby(['experiment','protocol','alpha','gamma']).size().rename('outer_folds').reset_index().to_csv(DEST/'configuration_frequency.csv',index=False)
coef=pd.read_csv(OUT/'tables/coefficients.csv')
coef.groupby(['experiment','protocol','feature']).agg(median_standardized_effect=('unweighted_standardized_coefficient','median'),fraction_positive=('unweighted_standardized_coefficient',lambda a:(a>0).mean())).reset_index().to_csv(DEST/'coefficient_stability.csv',index=False)
pairs=[('CAL01','CAL00'),('CAL02','CAL01'),('CAL03','CAL00'),('CAL04','CAL02'),('CAL05','CAL04'),('CAL06','CAL04'),('CAL06','CAL05'),('CAL07','CAL05')]
contrasts=[]
for name,reference in pairs:
    j=reps[reps.experiment.eq(name)].merge(reps[reps.experiment.eq(reference)],on=['protocol','repeat'],suffixes=('','_ref'))
    for _,r in j.iterrows():contrasts.append(dict(experiment=name,reference=reference,protocol=r.protocol,repeat=r['repeat'],**{'delta_'+k:r[k]-r[k+'_ref'] for k in ['rmse','mae','bias','r2']}))
pd.DataFrame(contrasts).to_csv(DEST/'planned_ablations_by_repeat.csv',index=False)
pd.DataFrame(contrasts).groupby(['experiment','reference','protocol'])[['delta_rmse','delta_mae','delta_bias','delta_r2']].mean().reset_index().to_csv(DEST/'planned_ablations_summary.csv',index=False)
pd.read_csv(OUT/'tables/intraprofile_by_repeat.csv').groupby(['experiment','protocol']).mean(numeric_only=True).reset_index().to_csv(DEST/'intraprofile_summary.csv',index=False)
om=pd.read_csv(OUT/'tables/omission_without_refit.csv');paired=[]
for reference in ['C-T3','CAL04']:
    j=om[om.experiment.ne(reference)].merge(om[om.experiment.eq(reference)].drop(columns='experiment'),on=['protocol','repeat','kind','omitted'],suffixes=('','_ref'),validate='many_to_one')
    j['reference']=reference;j['delta_rmse']=j.rmse-j.rmse_ref
    paired.append(j[['experiment','reference','protocol','repeat','kind','omitted','delta_rmse']])
pd.concat(paired).to_csv(DEST/'paired_omissions.csv',index=False)
parcel=gains.groupby(['experiment','reference','protocol','ID_POLIGONO','Estado','Municipio'],as_index=False)[['sse_gain','absolute_error_gain']].mean()
parcel.to_csv(DEST/'parcel_gain_repeat_average.csv',index=False)
parcel.groupby(['experiment','reference','protocol','Estado','Municipio']).agg(n=('ID_POLIGONO','size'),sse_gain=('sse_gain','sum'),mean_absolute_error_gain=('absolute_error_gain','mean'),fraction_improved=('absolute_error_gain',lambda a:(a>0).mean())).reset_index().to_csv(DEST/'municipal_gain_contributions.csv',index=False)
extremes=[]
for key,g in parcel.groupby(['experiment','reference','protocol']):
    for direction,h in [('best',g.nlargest(5,'sse_gain')),('worst',g.nsmallest(5,'sse_gain'))]:
        h=h.copy();h['direction']=direction;extremes.append(h)
pd.concat(extremes).to_csv(DEST/'largest_improvements_deteriorations.csv',index=False)
decomp=[]
for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
    e=g.y_pred-g.y_true;decomp.append(dict(experiment=name,protocol=pro,repeat=re,bias_squared=e.mean()**2,error_variance=e.var(ddof=0),mse=np.mean(e**2)))
pd.DataFrame(decomp).to_csv(DEST/'bias_dispersion.csv',index=False)
# Relate gains to historical departure descriptively, never to select a rule.
features=pd.read_parquet(ROOT/'data/processed/agronomic_calendar_set/v1/current_history_delta_197_target_free.parquet')
q=parcel[(parcel.experiment.eq('CAL05'))&(parcel.reference.eq('CAL04'))].merge(features,on='ID_POLIGONO',validate='many_to_one')
associations=[]
for pro,g in q.groupby('protocol'):
    for feature in ['DELTA_CAL_S2_ndvi_post_jul_aug','DELTA_CAL_S2_ndvi_late_sep_oct','HIST_SD_CAL_S2_ndvi_post_jul_aug']:
        v=g[[feature,'sse_gain']].dropna();associations.append(dict(protocol=pro,feature=feature,n=len(v),spearman_gain=v[feature].corr(v.sse_gain,method='spearman')))
pd.DataFrame(associations).to_csv(DEST/'exploratory_history_gain_associations.csv',index=False)
protocols=['random','climate_profile','municipality','spatial'];models=[f'CAL{i:02d}' for i in range(8)]
mat=summary.pivot(index='experiment',columns='protocol',values='rmse');delta=mat.loc[models,protocols]-mat.loc['C-T3',protocols]
fig,ax=plt.subplots(figsize=(9,5));limit=np.max(abs(delta.to_numpy()));im=ax.imshow(delta,cmap='RdBu_r',vmin=-limit,vmax=limit,aspect='auto')
ax.set(xticks=range(4),xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],yticks=range(8),yticklabels=models,title='Cambio de RMSE frente a C-T3 (t/ha)\nNegativo: menor error; comparación exploratoria')
for i in range(8):
    for j in range(4):ax.text(j,i,f'{delta.iloc[i,j]:+.3f}',ha='center',va='center',color='black' if abs(delta.iloc[i,j])<.65*limit else 'white')
fig.colorbar(im,ax=ax);fig.tight_layout();fig.savefig(DEST/'rmse_vs_ct3.png',dpi=160);plt.close(fig)
print(mat[protocols].to_string())
print('\nPlanned ablations:\n',pd.read_csv(DEST/'planned_ablations_summary.csv').to_string(index=False))
