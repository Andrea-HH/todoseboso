"""Interpret sealed compact ensemble results, without training."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd
from matplotlib import pyplot as plt
from src.compact_ensemble import ROOT,OUT,sha

DEST=ROOT/'outputs/research/compact_ensemble_synthesis/v1'
if DEST.exists():raise FileExistsError('Preserve previous versions')
DEST.mkdir(parents=True)
sources=[OUT/'manifest.json']+list((OUT/'tables').glob('*'))+[Path(__file__)]
protected={p.relative_to(ROOT).as_posix():sha(p) for p in sources}
m=pd.read_csv(OUT/'tables/metrics_summary.csv');w=pd.read_csv(OUT/'tables/weights.csv');c=pd.read_csv(OUT/'tables/error_complementarity.csv');r=pd.read_csv(OUT/'tables/regional_repeat.csv');om=pd.read_csv(OUT/'tables/omissions.csv');ip=pd.read_csv(OUT/'tables/intraprofile_summary.csv');pr=pd.read_csv(OUT/'tables/paired_repeat.csv');g=pd.read_parquet(OUT/'tables/parcel_gains.parquet')
com=c[c.group_type=='all'].groupby(['protocol','model_a','model_b'])[['error_correlation','opposite_error_fraction','fraction_b_lower_absolute_error','equal_pair_rmse']].mean().reset_index();com.to_csv(DEST/'complementarity_summary.csv',index=False)
weights=w.groupby('protocol').agg(mean_ct3=('w_ct3','mean'),mean_gpr=('w_gpr','mean'),mean_catboost=('w_catboost','mean'),sd_ct3=('w_ct3','std'),sd_gpr=('w_gpr','std'),sd_catboost=('w_catboost','std'),fraction_single_model=('w_ct3',lambda a:float(np.mean(np.max(w.loc[a.index,['w_ct3','w_gpr','w_catboost']].to_numpy(),axis=1)==1)))).reset_index();weights.to_csv(DEST/'weights_summary.csv',index=False)
pair=pr.groupby(['experiment','reference','protocol'])[['delta_rmse','delta_mae','delta_bias']].mean().reset_index();pair.to_csv(DEST/'paired_summary.csv',index=False)
omrows=[]
for exp in ['BLEND3','EQUAL3']:
    for ref in ['C-T3','F5-01','F7-00']:
        z=om[om.experiment==exp].merge(om[om.experiment==ref],on=['protocol','repeat','omitted_type','omitted'],suffixes=('_new','_ref'),validate='one_to_one');z['delta_rmse']=z.rmse_new-z.rmse_ref;z['experiment']=exp;z['reference']=ref;omrows.append(z[['experiment','reference','protocol','repeat','omitted_type','omitted','delta_rmse']])
omissions=pd.concat(omrows);omissions.to_csv(DEST/'paired_omissions.csv',index=False)
regional=[]
for (protocol,repeat),z in g.groupby(['protocol','repeat']):
    for ref in ['C-T3','F5-01','F7-00']:
        col=f'sse_gain_vs_{ref}';total=z[col].sum();top=z.sort_values(col,ascending=False).head(5)[col].sum()
        for muni,h in z.groupby('Municipio'):
            gain=h[col].sum();regional.append(dict(protocol=protocol,repeat=repeat,reference=ref,municipality=muni,n=len(h),sse_gain=float(gain),share_net_gain=float(gain/total) if abs(total)>1e-12 else np.nan,net_total_gain=float(total),top5_gain=float(top)))
pd.DataFrame(regional).to_csv(DEST/'regional_gain_concentration.csv',index=False)
dec=[]
for exp in ['BLEND3','EQUAL3']:
    a=m[m.experiment==exp].set_index('protocol');b=m[m.experiment=='C-T3'].set_index('protocol');gain=b.rmse-a.rmse;harm=max((a.rmse-b.rmse).max(),(a.mae-b.mae).max());bh=(abs(a.bias)-abs(b.bias)).loc[['municipality','spatial']].max()
    qo=omissions[(omissions.experiment==exp)&(omissions.reference=='C-T3')&(omissions.protocol=='spatial')&(omissions.omitted_type=='fold')]
    eligible=bool((gain.loc[['climate_profile','municipality','spatial']]>=.01).any() and harm<=.01 and bh<=.02 and qo.delta_rmse.max()<=.01)
    dec.append(dict(experiment=exp,max_rmse_mae_harm=float(harm),max_geographic_abs_bias_harm=float(bh),max_spatial_block_omission_harm=float(qo.delta_rmse.max()),passes_exploratory_guard=eligible))
pd.DataFrame(dec).to_csv(DEST/'decision_checks.csv',index=False)
order=['random','climate_profile','municipality','spatial'];fig,axes=plt.subplots(1,2,figsize=(12,4))
for name in ['C-T3','F5-01','F7-00','EQUAL3','BLEND3']:
    a=m[m.experiment==name].set_index('protocol').reindex(order);axes[0].plot(range(4),a.rmse,marker='o',label=name)
axes[0].set_xticks(range(4),['Aleatoria','Perfil','Municipal','Espacial']);axes[0].set_ylabel('RMSE (t/ha)');axes[0].legend(fontsize=8)
bottom=np.zeros(4)
for col,label in [('mean_ct3','C-T3'),('mean_gpr','GPR'),('mean_catboost','CatBoost')]:
    v=weights.set_index('protocol').reindex(order)[col].to_numpy();axes[1].bar(range(4),v,bottom=bottom,label=label);bottom+=v
axes[1].set_xticks(range(4),['Aleatoria','Perfil','Municipal','Espacial']);axes[1].set_ylabel('Peso medio seleccionado internamente');axes[1].legend(fontsize=8);fig.tight_layout();fig.savefig(DEST/'results_and_weights.png',dpi=160);plt.close(fig)
lines=['# Complementariedad y combinación del núcleo compacto','', 'Pesos no negativos, suma uno, rejilla .1; selección por OOF internas completas. Sin intercepto, corrección residual ni reglas regionales. Modelos externos anteriores congelados y reproducidos. Retuneo interno de CatBoost con su rejilla original para evitar reutilizar configuraciones elegidas con etiquetas de validación de pesos.','', '## Métricas completas','', '```text',m.to_string(index=False),'```','', '## Complementariedad descriptiva','', '```text',com.to_string(index=False),'```','', 'Correlación de errores, signos opuestos y comparaciones por parcela son descriptivos de OOF externas: no eligieron pesos. La fracción de signos opuestos no mide por sí sola magnitud útil de compensación. Las parejas al 50% son cálculos descriptivos, no nuevas búsquedas de modelos. Promedios aleatorios son por repetición.','', '## Pesos internos','', '```text',weights.to_string(index=False),'```','', '## Diagnósticos de decisión','', '```text',pd.DataFrame(dec).to_string(index=False),'```','', 'Los márgenes son exploratorios prácticos, no pruebas de significancia. Revisar paired_omissions, regional_gain_concentration y la tabla intraperfil antes de interpretar una ventaja agregada. Participaciones mayores que 100% o negativas pueden aparecer porque unas regiones compensan pérdidas en otras.','', '## Alcance','', 'Se mantuvieron 138 rendimientos, 65 folds externos y sus particiones internas. No se ajustó un modelo final ni se generaron 59 PRED, no se modificó Champion. Los resultados proceden de etiquetas repetidamente estudiadas y no son confirmación independiente. Los pesos son globales por entrenamiento externo, aunque pueden variar entre folds; no hay selección específica por municipio o bloque. No se presentan intervalos de mezcla: requieren calibración adicional.']
(DEST/'informe.md').write_text('\n'.join(lines),encoding='utf-8')
for path,h in protected.items():assert sha(ROOT/path)==h
(DEST/'manifest.json').write_text(json.dumps(dict(status='complete',new_fits=0,inputs=protected,artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in DEST.rglob('*') if p.is_file() and p.name!='manifest.json'}),indent=2),encoding='utf-8')
print(m.to_string(index=False));print(com.to_string(index=False));print(weights.to_string(index=False));print(pd.DataFrame(dec).to_string(index=False))
