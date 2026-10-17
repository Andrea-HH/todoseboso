"""Package descriptive top-ten audit; does not fit predictive models."""
from pathlib import Path
import pandas as pd
import numpy as np
P=Path('outputs/research/top10_difficult_parcels/v1');D=P/'tables'
def main():
 top=pd.read_csv(D/'top10_J7_random.csv');d=pd.read_csv(D/'outliers_all_numeric.csv');cat=pd.read_csv(D/'categorical_levels.csv')
 assert len(top)==10 and top.ID_POLIGONO.is_unique
 assert set(d['case'])==set(top.ID_POLIGONO)
 # A singleton profile cannot define a nearest-neighbor anomaly percentile.
 multi=pd.read_csv(D/'multivariate_case_ranks.csv')
 unsupported=(multi.n<2)|(multi.active_dimensions==0)|(~np.isfinite(multi.mean_5nn_distance))
 multi.loc[unsupported,['mean_5nn_distance','percentile_5nn_distance']]=np.nan
 multi['support_status']=np.where(unsupported,'insufficient_support','descriptive')
 multi.to_csv(D/'multivariate_case_ranks.csv',index=False)
 signals=['PLANET_evi_promedio_last_minus_first','TOPO_ADV_tpi_3x3_mean','S2_ndvi_derived_lower_gap_max_growth_rate']
 selected=d[(d.source=='MODEL')|((d.source=='OWN1867')&d.feature.isin(signals))].copy()
 selected.to_csv(D/'architecture_inputs_and_three_signals.csv',index=False)
 strong=d[(~d.quality_field)&(d.source!='TARGET')&(d.status=='continuous')].copy()
 strong['extremeness']=abs(strong.percentile_midrank-50)
 strong=strong.sort_values(['case','scope','extremeness'],ascending=[True,True,False]).drop_duplicates(['case','scope','feature'])
 strong.groupby(['case','scope'],sort=False).head(15).to_csv(D/'top15_differences_by_scope.csv',index=False)
 d[d.flag_iqr|d.flag_robust_z].to_csv(D/'all_flagged_variables.csv',index=False)
 rows=[]
 for _,r in top.iterrows():
  q=selected[(selected.case==r.ID_POLIGONO)&(selected.scope=='municipality')].copy();q['extremeness']=abs(q.percentile_midrank-50)
  q=q[q.status=='continuous'].sort_values('extremeness',ascending=False).head(4)
  rows.append(dict(ID_POLIGONO=r.ID_POLIGONO,Municipio=r.Municipio,observed=r.y_true,predicted=r.mean_prediction,bias=r.mean_error,RMSE_repeats=r.rms_error_across_repeats,municipal_differences='; '.join(f'{v.feature}: {v.value:.4g} (P{v.percentile_midrank:.0f}; mediana {v.median:.4g})' for v in q.itertuples())))
 summary=pd.DataFrame(rows);summary.to_csv(D/'top10_readable_summary.csv',index=False)
 with pd.ExcelWriter(P/'inventario_10_parcelas_dificiles.xlsx') as w:
  for name,frame in [('Resumen',summary),('Entradas_y_senales',selected),('Diferencias_por_grupo',pd.read_csv(D/'top15_differences_by_scope.csv')),('Categorias',cat),('Errores_otros_modelos',pd.read_csv(D/'top10_errors_all_models_protocols.csv'))]:frame.to_excel(w,sheet_name=name,index=False)
 print(summary.to_string(index=False))
 print('\nTHREE SIGNALS MUNICIPAL:');print(selected[(selected.feature.isin(signals))&(selected.scope=='municipality')][['case','feature','value','median','percentile_midrank','n_valid','flag_iqr']].to_string(index=False))
if __name__=='__main__':main()
