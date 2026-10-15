"""Post-fit soil diagnosis by observed yield quartile; no model fitting."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/research/family_1/soil_yield_quartile_analysis/v1'
OUT.mkdir(parents=True, exist_ok=True)
base = ROOT / 'outputs/modeling/family_1'
k = pd.read_parquet(base / 'k_standalone_residual_geographic_edaphological/v1/tables/11_k_oof_predictions.parquet')
j = pd.read_parquet(base / 'j_incremental_geographic_edaphological_yield/v1/tables/02_oof_predictions.parquet')
l = pd.read_parquet(base / 'l_multiblock_representation/v1/tables/10_oof_predictions.parquet')
names = {'K0_MEAN':'Media', 'K3_SOIL_ONLY':'Suelo S1 solo', 'K3_SOIL_ONLY_ALT':'Suelo S2 solo', 'KA_RAIN_SOIL_STABLE':'Lluvia + suelo S1', 'K7_RAIN_RESID_SOIL':'Lluvia + corrección suelo S1', 'J0_RAIN':'Lluvia', 'L2':'Lluvia + corrección PCA suelo'}
print('J experiments:', j.experiment.unique().tolist())
print('L experiments:', l.experiment.unique().tolist())
# Resolve the stored baseline and PCA experiment names explicitly by prefix.
jn = next(x for x in j.experiment.unique() if x.startswith('J0'))
ln = next(x for x in l.experiment.unique() if x.startswith('L2'))
names[jn] = names.pop('J0_RAIN')
names[ln] = names.pop('L2')
d = pd.concat([k[k.experiment.isin(names)], j[j.experiment.eq(jn)], l[l.experiment.eq(ln)]], ignore_index=True)
y = d[['ID_POLIGONO','y_true']].drop_duplicates()
assert len(y) == 138 and y.ID_POLIGONO.is_unique
y['quartile'], edges = pd.qcut(y.y_true, 4, labels=['Q1','Q2','Q3','Q4'], retbins=True)
y.to_csv(OUT / 'parcel_quartiles.csv', index=False)
keys = ['protocol','repeat','fold','ID_POLIGONO']
b = d[d.experiment.eq(jn)][keys + ['y_true','y_pred']].rename(columns={'y_pred':'baseline_pred','y_true':'baseline_y'})
d = d.merge(b, on=keys, validate='many_to_one').merge(y[['ID_POLIGONO','quartile']], on='ID_POLIGONO', validate='many_to_one')
assert np.allclose(d.y_true, d.baseline_y)
assert not d.duplicated(['experiment'] + keys).any()
rows=[]
for (exp, protocol, repeat, q), g in d.groupby(['experiment','protocol','repeat','quartile'], observed=True):
    assert len(g) == int((y.quartile == q).sum())
    err = g.y_pred - g.y_true
    be = g.baseline_pred - g.y_true
    rows.append(dict(experiment=exp, model=names[exp], protocol=protocol, repeat=repeat, quartile=q, n=len(g), rmse=np.sqrt(np.mean(err**2)), mae=np.mean(abs(err)), bias=err.mean(), delta_rmse=np.sqrt(np.mean(err**2))-np.sqrt(np.mean(be**2)), delta_mae=np.mean(abs(err))-np.mean(abs(be))))
r=pd.DataFrame(rows)
r.to_csv(OUT / 'metrics_by_repeat.csv', index=False)
s=r.groupby(['experiment','model','protocol','quartile'], observed=True)[['n','rmse','mae','bias','delta_rmse','delta_mae']].mean().reset_index()
s.to_csv(OUT / 'metrics_summary.csv', index=False)
geo=pd.read_parquet(ROOT / 'data/processed/family_1/i_climate_conditioned_geographic_edaphological/v1/integrated_diagnostic_197.parquet')
z=y.merge(geo.drop(columns=['y_true'], errors='ignore'), on='ID_POLIGONO', validate='one_to_one')
cols=[c for c in z if c.startswith('soil_map_share_mentions_group_')]
soil=z.groupby('quartile', observed=True)[cols].mean()
soil.to_csv(OUT / 'soil_group_coverage_by_quartile.csv')
for c in ['Estado','Municipio']:
    if c in z:
        pd.crosstab(z.quartile,z[c]).to_csv(OUT / f'{c}_counts.csv')
fig, axes=plt.subplots(1,2,figsize=(13,5))
for exp in [jn,'K3_SOIL_ONLY','K3_SOIL_ONLY_ALT','KA_RAIN_SOIL_STABLE','K7_RAIN_RESID_SOIL',ln]:
    g=s[(s.experiment==exp)&(s.protocol=='random')].sort_values('quartile')
    axes[0].plot(g.quartile,g.rmse,marker='o',label=names[exp])
axes[0].set(ylabel='RMSE (t/ha)',title='Predicciones fuera de muestra: validación aleatoria')
axes[0].legend(fontsize=8)
im=axes[1].imshow(soil.T.to_numpy(),vmin=0,vmax=1,aspect='auto',cmap='YlGn')
axes[1].set_xticks(range(4),soil.index.astype(str))
axes[1].set_yticks(range(len(cols)),[c.rsplit('_',1)[-1] for c in cols])
axes[1].set_title('Cobertura media de unidades que mencionan cada grupo')
fig.colorbar(im,ax=axes[1],label='Fracción cartográfica (grupos pueden coexistir)')
fig.tight_layout()
fig.savefig(OUT / 'soil_quartiles.png',dpi=180)
print('EDGES',edges)
print(s[s.protocol=='random'][['model','quartile','rmse','bias','delta_rmse']].to_string(index=False))
print('SOIL',soil.round(3).to_string())
print('GEOGRAPHY',pd.crosstab(z.quartile,z.Estado).to_string())
