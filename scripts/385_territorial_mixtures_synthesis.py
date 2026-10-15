"""Interpret frozen territorial mixture results without fits or model selection."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,joblib
from matplotlib import pyplot as plt
from src.territorial_mixtures import ROOT,OLD,OUT,PREVIOUS,ID,Y,metrics,sha

DEST=ROOT/'outputs/research/territorial_mixtures_synthesis/v1'
if DEST.exists():raise FileExistsError('Existing interpretation immutable')
DEST.mkdir(parents=True)
sources=[OUT/'manifest.json']+list((OUT/'tables').glob('*'))+[OLD/'cache/train138.parquet',PREVIOUS/'tables/parcel_gains.parquet',Path(__file__)]
hashes={p.relative_to(ROOT).as_posix():sha(p) for p in sources}
summary=pd.read_csv(OUT/'tables/metrics_summary.csv');ip=pd.read_csv(OUT/'tables/intraprofile_summary.csv');reg=pd.read_csv(OUT/'tables/registry.csv');rules=pd.read_csv(OUT/'tables/rules.csv');pred=pd.read_parquet(OUT/'tables/oof_predictions.parquet');regional=pd.read_csv(OUT/'tables/regional_repeat.csv');om=pd.read_csv(OUT/'tables/omissions.csv');paired=pd.read_csv(OUT/'tables/paired_repeat.csv');t=pd.read_parquet(OLD/'cache/train138.parquet')
experts=pd.read_csv(OUT/'tables/deep_expert_registry.csv');numeric=[]
for row in experts.itertuples():
    gp=json.loads(row.gp_parameters)
    numeric.append(dict(key=row.key,protocol=row.protocol,n_train=row.n_train,gp_converged=gp['selected_optimizer_converged'],gp_bound_hits=len(gp['bound_hits']),gp_warnings=len(gp['warnings']),condition=gp['covariance_condition'],minimum_eigenvalue=gp['min_covariance_eigenvalue'],cb_warnings=len(json.loads(row.cb_warnings)),seconds=row.seconds))
pd.DataFrame(numeric).to_csv(DEST/'numerical_diagnostics.csv',index=False)
paired.groupby(['experiment','reference','protocol'])[['delta_rmse','delta_mae','delta_bias']].mean().reset_index().to_csv(DEST/'paired_summary.csv',index=False)
reg.groupby(['experiment','protocol']).agg(mean_splits=('tree_splits','mean'),mean_municipal_rules=('municipal_rules','mean'),mean_fallback=('fraction_fallback','mean')).reset_index().to_csv(DEST/'rule_support_summary.csv',index=False)
rulefreq=rules[(rules.type=='tree')&rules.feature.notna()&rules.feature.ne('')].groupby(['protocol','feature']).size().reset_index(name='split_nodes');rulefreq.to_csv(DEST/'split_frequency.csv',index=False)
pd.DataFrame([dict(experiment=name,protocol=pro,params=params,n_folds=len(g)) for (name,pro,params),g in reg.groupby(['experiment','protocol','params'])]).to_csv(DEST/'configuration_frequency.csv',index=False)
reused=pd.read_parquet(PREVIOUS/'tables/parcel_gains.parquet');matched=[]
for r in reg.itertuples():
    if r.experiment not in ['R2','R3']:continue
    q=reused[(reused.protocol==r.protocol)&(reused['repeat']==r.repeat)&(reused.fold==r.fold)];weights=np.asarray(json.loads(r.global_weights));p=q[['C-T3','F5-01','F7-00']].to_numpy()@weights
    matched.extend(dict(experiment=r.experiment+'_GLOBAL',protocol=r.protocol,repeat=r.repeat,fold=r.fold,ID_POLIGONO=pid,y_true=float(y),y_pred=float(v)) for pid,y,v in zip(q[ID],q.y_true,p))
matched=pd.DataFrame(matched);matched.to_parquet(DEST/'matched_global_diagnostic.parquet',index=False);mr=[]
for (exp,pro,re),g in matched.groupby(['experiment','protocol','repeat']):mr.append(dict(experiment=exp,protocol=pro,repeat=re,**metrics(g.y_true,g.y_pred)))
pd.DataFrame(mr).groupby(['experiment','protocol'])[['rmse','mae','bias']].mean().reset_index().to_csv(DEST/'matched_global_summary.csv',index=False)
omissions=[]
for exp in ['R1','R2','R3']:
    for ref in ['C-T3','EQUAL3','R1']:
        if exp==ref:continue
        q=om[om.experiment==exp].merge(om[om.experiment==ref],on=['protocol','repeat','omitted_type','omitted'],suffixes=('_new','_ref'),validate='one_to_one');q['delta_rmse']=q.rmse_new-q.rmse_ref;q['experiment']=exp;q['reference']=ref;omissions.append(q[['experiment','reference','protocol','repeat','omitted_type','omitted','delta_rmse']])
omissions=pd.concat(omissions);omissions.to_csv(DEST/'paired_omissions.csv',index=False)
gains=pd.read_parquet(OUT/'tables/parcel_gains.parquet').merge(t[[ID,'Municipio','Estado']],on=ID,validate='many_to_one');gainrows=[]
for (name,ref,pro,re),g in gains.groupby(['experiment','reference','protocol','repeat']):
    net=float(g.sse_gain.sum());top=float(g.nlargest(5,'sse_gain').sse_gain.sum())
    for muni,h in g.groupby('Municipio'):gainrows.append(dict(experiment=name,reference=ref,protocol=pro,repeat=re,municipality=muni,n=len(h),sse_gain=float(h.sse_gain.sum()),total_net_gain=net,share_net_gain=float(h.sse_gain.sum()/net) if abs(net)>1e-12 else np.nan,top5_gain=top))
pd.DataFrame(gainrows).to_csv(DEST/'municipal_gain_concentration.csv',index=False)
dec=[]
for name in ['R1','R2','R3']:
    for ref in ['C-T3','EQUAL3']:
        a=summary[summary.experiment==name].set_index('protocol');b=summary[summary.experiment==ref].set_index('protocol');gain=b.rmse-a.rmse;harm=max((a.rmse-b.rmse).max(),(a.mae-b.mae).max());bh=(abs(a.bias)-abs(b.bias)).loc[['municipality','spatial']].max();o=omissions[(omissions.experiment==name)&(omissions.reference==ref)&(omissions.protocol=='spatial')&(omissions.omitted_type=='fold')];la=ip[ip.experiment==name].set_index('protocol');lb=ip[ip.experiment==ref].set_index('protocol');lh=(la[['equal_profile_RMSE','pair_weighted_RMSE']]-lb[['equal_profile_RMSE','pair_weighted_RMSE']]).max().max()
        dec.append(dict(experiment=name,reference=ref,grouped_gain_ge_01=bool((gain.loc[['climate_profile','municipality','spatial']]>=.01).any()),max_rmse_mae_harm=float(harm),max_geographic_abs_bias_harm=float(bh),max_spatial_omission_harm=float(o.delta_rmse.max()),max_intraprofile_harm=float(lh),passes_exploratory_guard=bool((gain.loc[['climate_profile','municipality','spatial']]>=.01).any() and harm<=.01 and bh<=.02 and o.delta_rmse.max()<=.01 and lh<=.01)))
pd.DataFrame(dec).to_csv(DEST/'decision_checks.csv',index=False)
order=['random','climate_profile','municipality','spatial'];fig,axes=plt.subplots(1,2,figsize=(13,4))
for name in ['C-T3','EQUAL3','R1','R2','R3']:
    a=summary[summary.experiment==name].set_index('protocol').reindex(order);axes[0].plot(range(4),a.rmse,marker='o',label=name)
axes[0].set_xticks(range(4),['Aleatoria','Perfil','Municipal','Espacial']);axes[0].set_ylabel('RMSE (t/ha)');axes[0].legend(fontsize=8)
for i,name in enumerate(['R1','R2','R3']):
    a=reg[reg.experiment==name].groupby('protocol').fraction_fallback.mean().reindex(order);axes[1].bar(np.arange(4)+(i-1)*.23,a,width=.23,label=name)
axes[1].set_xticks(range(4),['Aleatoria','Perfil','Municipal','Espacial']);axes[1].set_ylabel('Fracción de predicciones con mezcla global');axes[1].legend(fontsize=8);fig.tight_layout();fig.savefig(DEST/'performance_and_fallback.png',dpi=160);plt.close(fig)
lines=['# R1–R3: síntesis de mezclas territoriales','', 'Diseño congelado antes de ejecutar. R1 global regularizada hacia promedio; R2 municipal con contracción y fallback; R3 árbol que aprende mezclas directamente por SSE. Selección interna anidada de cada candidato completo, usando expertos profundos honestos. Sin correcciones aditivas o reglas retrospectivas por municipio.','', '## Resultados','', '```text',summary.to_string(index=False),'```','', '## Reglas y soporte','', '```text',reg.groupby(['experiment','protocol'])[['tree_splits','municipal_rules','fraction_fallback']].mean().to_string(),'```','', 'R2 en municipio completamente retenido solo puede usar su mezcla global. Fuera de rango marginal de entrenamiento R3 retorna a su mezcla global. La columna fraction_fallback cuenta global, raíz sin división y fuera de soporte. Las mezclas globales de R2/R3 pueden diferir de R1 porque su regularización se selecciona conjuntamente con la adaptación; matched_global_summary aísla descriptivamente el efecto de aplicar sus reglas con esos pesos ya congelados.','', '## Decisión exploratoria','', '```text',pd.DataFrame(dec).to_string(index=False),'```','', 'Criterios prácticos, no pruebas de significancia. Se reportan diferencias intraperfil con ambas ponderaciones, omisiones sin reajuste, concentración de ganancias y frecuencia de reglas. Las participaciones netas de SSE pueden exceder 100% si otras regiones empeoran. Ningún resultado externo se usa para modificar los modelos de esta ejecución.','', '## Límites','', 'Sin ajuste final de138, sin PRED, sin promoción, sin variables nuevas o corrección aditiva. Las OOF externas se han investigado repetidamente y no constituyen confirmación independiente. No hay intervalos de mezcla calibrados. Todos los modelos externos anteriores permanecen congelados y sus archivos consumidos se verifican por hash.']
(DEST/'informe.md').write_text('\n'.join(lines),encoding='utf-8')
for p,h in hashes.items():assert sha(ROOT/p)==h
(DEST/'manifest.json').write_text(json.dumps(dict(status='complete',new_fits=0,inputs=hashes,artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in DEST.rglob('*') if p.is_file() and p.name!='manifest.json'}),indent=2),encoding='utf-8')
print(summary.to_string(index=False));print(reg.groupby(['experiment','protocol'])[['tree_splits','municipal_rules','fraction_fallback']].mean().to_string());print(pd.DataFrame(dec).to_string(index=False))
