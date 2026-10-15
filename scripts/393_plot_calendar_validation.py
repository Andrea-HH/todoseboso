"""Descriptive figure on TRAIN only, with matched four-year cohorts per feature."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'outputs/research/agronomic_calendar_validation/v1/annual_context.png'
if out.exists():raise FileExistsError('Preserve figure')
p=pd.read_parquet(ROOT/'data/processed/agronomic_calendar_set/v1/annual_features_2022_2025.parquet')
m=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet',columns=['ID_POLIGONO','Estado'])
p=p.merge(m,on='ID_POLIGONO',validate='many_to_one')
features=[('CAL_CLIM_precip_sowing_may_jun','Lluvia mayo-junio','mm'),('CAL_CLIM_tmax_sowing_may_jun','Tmax mayo-junio','°C'),('CAL_S2_ndvi_post_jul_aug','NDVI julio-agosto','NDVI'),('CAL_S2_ndvi_late_sep_oct','NDVI septiembre-octubre','NDVI')]
fig,axes=plt.subplots(2,2,figsize=(11,7))
for ax,(feature,title,unit) in zip(axes.ravel(),features):
    complete=p.pivot(index='ID_POLIGONO',columns='year',values=feature).dropna().index
    q=p[p.ID_POLIGONO.isin(complete)]
    for state,g in q.groupby('Estado'):
        line=g.groupby('year')[feature].median();ax.plot(line.index,line.values,marker='o',label=state)
    ax.set(title=title+f' (n={len(complete)})',ylabel=unit,xticks=[2022,2023,2024,2025]);ax.grid(alpha=.2)
axes[0,0].legend();fig.suptitle('Medianas por estado: mismas parcelas en los cuatro años\nDescriptivo; sin rendimientos ni inferencia causal',fontsize=12)
fig.tight_layout();fig.savefig(out,dpi=160);plt.close(fig)
print(out)
