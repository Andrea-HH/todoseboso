import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import joblib,numpy as np,pandas as pd
from src.experimental_tree import OUT,sha
rows=[]; replay=[]
x=pd.read_parquet(OUT/'cache/train138_1867.parquet').set_index('ID_POLIGONO')
oof=pd.read_parquet(OUT/'tables/oof_predictions.parquet')
for f in (OUT/'models').glob('*.joblib'):
 p=joblib.load(f);m=p['tree'];rep=p['representation'];reg=p['registry']
 for i in np.flatnonzero(m.tree_.feature>=0):
  j=m.tree_.feature[i]
  rows.append(dict(protocol=reg['protocol'],repeat=reg['repeat'],fold=reg['fold'],node=int(i),variable=rep.names[j],threshold_original=float(m.tree_.threshold[i]*rep.scaler.scale_[j]+rep.scaler.mean_[j]),training_samples=int(m.tree_.n_node_samples[i]),impurity=float(m.tree_.impurity[i])))
 q=oof[(oof.protocol==reg['protocol'])&(oof.repeat==reg['repeat'])&(oof.fold==reg['fold'])]
 pred=m.predict(rep.transform(x.loc[q.ID_POLIGONO]))
 diff=float(np.max(abs(pred-q.y_pred)))
 assert diff<1e-10
 replay.append(dict(model=f.name,max_difference=diff))
r=pd.DataFrame(rows);r.to_csv(OUT/'tables/splits.csv',index=False)
r.groupby('variable').agg(split_nodes=('node','size'),folds=('fold','size')).sort_values('split_nodes',ascending=False).to_csv(OUT/'tables/split_frequency.csv')
pd.DataFrame(replay).to_csv(OUT/'tables/replay_verification.csv',index=False)
summary=pd.read_csv(OUT/'tables/metrics_summary.csv')
freq=r.variable.value_counts();registry=pd.read_csv(OUT/'tables/fit_registry.csv')
lines=['# Árbol exploratorio con 1,867 variables','', 'CART directo: 12 configuraciones de profundidad (2, 3, 5 o sin límite) y mínimo de hojas (5, 10 o 20). Selección por RMSE de OOF internas completas. 65 folds externos originales. Transformaciones ajustadas exclusivamente dentro del entrenamiento. No es una corrección residual.','','```text\n'+summary.to_string(index=False)+'\n```','',f'Profundidades efectivas: {registry.depth.value_counts().sort_index().to_dict()}. Hojas: {registry.leaves.min()}–{registry.leaves.max()}. Variables distintas utilizadas en los 65 árboles: {len(freq)}.','', 'Variables más frecuentes en particiones (descriptivo, sin interpretación causal):','','```text\n'+freq.head(20).to_string()+'\n```','','Las variables redundantes pueden intercambiarse: la frecuencia de una columna no mide su utilidad única. Las categorías pueden funcionar como proxies geográficos. Umbrales y reglas se incluyen por fold; no se ajustó un árbol final con los 138 rendimientos ni se generaron predicciones PRED.','', 'Se verificó la reproducción exacta de las 65 predicciones por modelo guardado. El runtime notificó coexistencia de Intel y LLVM OpenMP; la ejecución terminó sin interrupciones.']
lines += ['', 'Resultado: el arbol no mejora C-T3 en ninguno de los cuatro protocolos; el deterioro territorial es mayor que el aleatorio. No se recomienda integrar esta configuracion. La columna components en los CSV contiene (max_depth, min_samples_leaf), no componentes latentes. Los umbrales de rules_*.txt usan escala estandarizada; splits.csv contiene umbrales originales.']
(OUT/'interpretacion.md').write_text('\n'.join(lines),encoding='utf-8')
print(summary[summary.experiment.isin(['TREE1867','C-T3'])].to_string(index=False));print(freq.head(12).to_string());print(registry.depth.value_counts())
manifest=json.loads((OUT/'manifest.json').read_text());manifest['artifacts']={str(f.relative_to(OUT.parents[3])):sha(f) for f in OUT.rglob('*') if f.is_file() and f.name!='manifest.json'}
manifest['replay_verified_models']=65
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
