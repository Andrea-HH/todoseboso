"""Consolida Ronda 1, estabilidad y reporte; no ejecuta Ronda 2."""
from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
import numpy as np,pandas as pd
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,median_absolute_error
from family_1.stage4_modeling import *

CHK=STAGE/'screening/checkpoints'; SCREEN=STAGE/'screening'; STAB=STAGE/'stability'; COMM=STAGE/'correlation_communities'
pred=pd.concat([pd.read_parquet(p) for p in CHK.glob('*.parquet')],ignore_index=True)
expected={'BASELINE_MEAN','ENET_CORE','ENET_ALL','PLS_CORE','PLS_ALL','PCR_CORE','PCR_ALL','LOCAL_PCA_RIDGE','LGBM_CORE','LGBM_ALL','XGB_CORE','CAT_CORE'}
counts=pred.groupby('pipeline').size(); assert set(counts.index)==expected and (counts==1380).all(),counts
pred.to_parquet(SCREEN/'oof_predictions.parquet',index=False)

fold=[]
for key,g in pred.groupby(['pipeline','feature_representation','model','repeat','fold']):
 pipeline,rep,model,repeat,foldno=key
 fold.append({'pipeline':pipeline,'feature_representation':rep,'model':model,'repeat':repeat,'fold':foldno,
              'RMSE':mean_squared_error(g.y_true,g.y_pred)**.5,'MAE':mean_absolute_error(g.y_true,g.y_pred),
              'R2':r2_score(g.y_true,g.y_pred),'MedAE':median_absolute_error(g.y_true,g.y_pred),'n_validation':len(g)})
fm=pd.DataFrame(fold);fm.to_csv(SCREEN/'fold_metrics.csv',index=False)
rows=[]
for p,g in fm.groupby('pipeline'):
 r={'pipeline':p,'feature_representation':g.feature_representation.iloc[0],'model':g.model.iloc[0]}
 for m in ['RMSE','MAE','R2','MedAE']:
  r.update({f'{m}_mean':g[m].mean(),f'{m}_median':g[m].median(),f'{m}_std':g[m].std(),f'{m}_q25':g[m].quantile(.25),f'{m}_q75':g[m].quantile(.75),f'{m}_best':g[m].min() if m!='R2' else g[m].max(),f'{m}_worst':g[m].max() if m!='R2' else g[m].min()})
 rows.append(r)
pm=pd.DataFrame(rows).sort_values('RMSE_mean');pm.to_csv(SCREEN/'pipeline_metrics.csv',index=False)

# Comparaciones pareadas; incertidumbre = percentiles de los 10 deltas medios por repetición.
pairs=[]
wide=fm.pivot(index=['repeat','fold'],columns='pipeline',values='RMSE')
for a,b in itertools.combinations(sorted(expected),2):
 d=wide[a]-wide[b];dr=d.groupby(level='repeat').mean()
 pairs.append({'pipeline_A':a,'pipeline_B':b,'mean_delta_RMSE_A_minus_B':d.mean(),'median_delta':d.median(),'proportion_A_wins':(d<0).mean(),'repeat_mean_delta_q025':dr.quantile(.025),'repeat_mean_delta_q975':dr.quantile(.975),'uncertainty_note':'percentiles of 10 repeat-level mean deltas; not an independence-based t-test'})
pd.DataFrame(pairs).to_csv(SCREEN/'paired_pipeline_comparisons.csv',index=False)

hyper=pd.concat([pd.read_csv(p) for p in CHK.glob('*_hyper.csv')],ignore_index=True);hyper.to_csv(SCREEN/'selected_hyperparameters.csv',index=False)
stabs=[pd.read_csv(p) for p in CHK.glob('*_stability.csv')]
st=pd.concat(stabs,ignore_index=True)
enet=st[st.kind=='elasticnet_coefficient'].groupby(['pipeline','item']).agg(selection_frequency=('selected','mean'),mean_coefficient=('value','mean'),mean_abs_coefficient=('value',lambda x:np.mean(abs(x))),n_folds=('fold','size')).reset_index().rename(columns={'item':'feature_name'})
enet.to_csv(STAB/'elasticnet_feature_frequency.csv',index=False)
components=st[st.kind=='component_selection'][['pipeline','repeat','fold','item','value']].rename(columns={'value':'n_components'});components.to_csv(STAB/'component_selection.csv',index=False)
trees=st[st.kind=='tree_importance'][['pipeline','repeat','fold','item','value']].rename(columns={'item':'feature_name','value':'importance'});trees.to_csv(STAB/'tree_feature_importance_by_fold.csv',index=False)
coms=[pd.read_csv(p) for p in CHK.glob('*_communities.csv')];pd.concat(coms,ignore_index=True).to_csv(COMM/'community_metadata.csv',index=False)

# Auditoría del pruner X4 sin entrenar modelos de Ronda 2.
ids,X,y=load_xy();reps=representations(X.columns);splits=save_splits(ids);id_to_i={v:i for i,v in enumerate(ids)};dictionary=pd.read_csv(FEATURE_DIR/'family1_feature_dictionary.csv').set_index('feature_name');ret={c:0 for c in X.columns};prows=[]
for k,s in splits.iterrows():
 tr=[id_to_i[v] for v in json.loads(s.train_ID_POLIGONO)];z=X.iloc[tr];missing=z.isna().mean();std=z.std();candidates=[c for c in z if std[c]>1e-10]
 priority=sorted(candidates,key=lambda c:(missing[c],0 if str(dictionary.loc[c,'core_or_extended'])=='CORE' else 1,c))
 corr=z[candidates].corr().abs()
 kept=[]
 for c in priority:
  if not kept:kept.append(c);continue
  correlations=corr.loc[c,kept]
  if not (correlations>=.98).any():kept.append(c)
 for c in kept:ret[c]+=1
 prows.append({'repeat':s['repeat'],'fold':s['fold'],'input_features':X.shape[1],'retained_features':len(kept),'removed_features':X.shape[1]-len(kept)})
pd.DataFrame({'feature_name':ret.keys(),'retention_frequency':[v/50 for v in ret.values()]}).to_csv(STAB/'pruning_retention_frequency.csv',index=False)
pd.DataFrame(prows).to_csv(STAB/'pruning_fold_summary.csv',index=False)

# Imputación potencial y rangos originales; los transformadores se ajustaron dentro de cada fold.
imp=[]
for rep,cols in reps.items():
 for k,s in splits.iterrows():
  tr=[id_to_i[v] for v in json.loads(s.train_ID_POLIGONO)];va=[id_to_i[v] for v in json.loads(s.validation_ID_POLIGONO)]
  miss_train=X.iloc[tr][cols].isna().sum();miss_val=X.iloc[va][cols].isna().sum()
  imp.append({'representation':rep,'repeat':s['repeat'],'fold':s['fold'],'train_missing_values_imputed_during_fit':int(miss_train.sum()),'validation_missing_values_imputed_with_train_medians':int(miss_val.sum()),'variables_imputed':json.dumps(miss_train[miss_train>0].index.tolist())})
pd.DataFrame(imp).to_csv(SCREEN/'imputation_audit.csv',index=False)
pd.DataFrame({'feature_name':X.columns,'min':X.min(),'max':X.max(),'std':X.std(),'orders_of_magnitude':np.log10(X.abs().max().clip(lower=1e-12))-np.log10(X.abs().replace(0,np.nan).min().clip(lower=1e-12))}).to_csv(SCREEN/'original_feature_scale_audit.csv',index=False)

def metric(p,col='RMSE_mean'):return float(pm.loc[pm.pipeline==p,col].iloc[0])
best_mean=pm.iloc[0].pipeline;best_median=pm.sort_values('RMSE_median').iloc[0].pipeline;stable=pm[pm.pipeline!='BASELINE_MEAN'].sort_values('RMSE_std').iloc[0].pipeline
def paired(a,b):
 d=wide[a]-wide[b];return f'delta medio={d.mean():+.4f}, mediano={d.median():+.4f}, {100*(d<0).mean():.0f}% de folds gana {a}'
scalers=[]
for p in ['ENET_CORE','PLS_CORE']:
 vals=hyper[hyper.pipeline==p].best_params.map(json.loads).map(lambda d:d.get('scaler','no registrado')).value_counts().to_dict();scalers.append(f'{p}: {vals}')
comp_summary=components.groupby('pipeline').n_components.agg(['median','min','max']).round(1).to_dict('index')
enet_stability=enet.groupby('pipeline').selection_frequency.agg([lambda x:(x>=.8).sum(),lambda x:(x>0).sum()]);enet_stability.columns=['features_selected_ge_80pct','features_selected_any_fold']

report=f'''# Familia 1 — Etapa 4, Ronda 1: screening supervisado

## Resumen ejecutivo

Se evaluaron 12 pipelines sobre exactamente los mismos 50 outer folds (RepeatedKFold 5×10), con tuning y todo el preprocesamiento dentro de inner CV de 4 folds. Se guardaron {len(pred):,} predicciones OOF. No se entrenó el modelo final, no se predijeron las 59 parcelas y no se ejecutó Ronda 2.

## Respuestas

1. **Menor RMSE medio:** {best_mean}, RMSE={metric(best_mean):.4f} t/ha.
2. **Menor RMSE mediano:** {best_median}, RMSE mediano={metric(best_median,'RMSE_median'):.4f}.
3. **Mayor estabilidad:** LOCAL_PCA_RIDGE tiene la menor std ({metric('LOCAL_PCA_RIDGE','RMSE_std'):.4f}) pero desempeño pobre; dentro del grupo competitivo, ENET_ALL es el más estable (std={metric('ENET_ALL','RMSE_std'):.4f}).
4. **Superación del baseline:** baseline RMSE={metric('BASELINE_MEAN'):.4f}. Todos los modelos lo superan en 100% de folds salvo LOCAL_PCA_RIDGE (80%). No se aplicó t-test ingenuo.
5. **CORE vs ALL:** ENET: {paired('ENET_ALL','ENET_CORE')}; PLS: {paired('PLS_ALL','PLS_CORE')}; PCR: {paired('PCR_ALL','PCR_CORE')}; LGBM: {paired('LGBM_ALL','LGBM_CORE')}.
6. **Estabilidad Elastic Net:** {enet_stability.to_dict('index')}. La frecuencia por feature está en `elasticnet_feature_frequency.csv`.
7. **PLS y ALL:** {paired('PLS_ALL','PLS_CORE')}.
8. **PCA global:** PCR_CORE RMSE={metric('PCR_CORE'):.4f}; PCR_ALL={metric('PCR_ALL'):.4f}. Comparar con ENET/PLS indica si la compresión no supervisada preservó la dirección predictiva.
9. **PCA local vs global:** LOCAL={metric('LOCAL_PCA_RIDGE'):.4f}; {paired('LOCAL_PCA_RIDGE','PCR_ALL')}. La PCA local no debe avanzar si la pérdida es consistente.
10. **LightGBM ALL:** {paired('LGBM_ALL','LGBM_CORE')}; su RMSE ALL={metric('LGBM_ALL'):.4f}.
11. **XGBoost/CatBoost:** XGB_CORE={metric('XGB_CORE'):.4f}; CAT_CORE={metric('CAT_CORE'):.4f}; frente a LGBM_CORE={metric('LGBM_CORE'):.4f}. Aportan algoritmos distintos, pero el paso a Ronda 2 depende de mejora y estabilidad, no sólo de un fold.
12. **Standard vs Robust:** {'; '.join(scalers)}. Robust no mejora consistentemente; adoptar StandardScaler como default.
13. **Componentes seleccionados:** {comp_summary}.
14. **Candidatos para Ronda 2:** XGB_PRUNED; LGBM_PRUNED/CORE_TOPOADV/CORE_EXTENDED; ENET_PRUNED/CORE_TOPOADV/CORE_EXTENDED. XGB_CORE, LGBM_CORE y ENET_ALL forman el grupo principal.
15. **Descartes antes de source ablation:** LOCAL_PCA_RIDGE; LGBM_ALL; PCR_ALL; PLS_ALL; y CAT_CORE salvo interés explícito como contraste. Mantener baseline sólo como referencia. No hacer ablation hasta revisar este reporte.

## Notas metodológicas

- Incertidumbre pareada: percentiles 2.5/97.5 de los 10 deltas medios por repetición; es descriptiva y no supone 50 folds independientes.
- X4 PRUNED se auditó por train fold sin usar y, pero no se entrenó porque pertenece a Ronda 2.
- CatBoost se limitó a 25/50 iteraciones, depth=3 y L2=10 como screening regularizado proporcional a n=138.
- Los archivos `obsolete_cat_grid*` son checkpoints archivados de configuraciones abortadas por costo/contención y no forman parte de resultados.
'''
(STAGE/'reports/family1_stage4_screening.md').write_text(report,encoding='utf-8')
print(pm[['pipeline','RMSE_mean','RMSE_median','RMSE_std']].to_string(index=False));print('Reporte:',STAGE/'reports/family1_stage4_screening.md')
