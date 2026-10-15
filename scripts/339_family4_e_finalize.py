"""Finalize exploratory interpretation and integrity after the frozen model matrix."""
import sys,json,importlib.metadata
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from src.family_4 import within_profile_complementarity as e

def main():
    from src.family_4.within_profile_reporting import build
    build()
    d,t=e.load();out=e.OUT;rows=[]
    for pid in t[e.ID]:
        z=t[t[e.ID].ne(pid)];w,eligible=e.within(z,e.CANDIDATES+[e.TARGET])
        for c in e.CANDIDATES:
            if c==e.f.NDVI:continue
            a=w[[e.f.NDVI,c,e.TARGET]].dropna();design=np.column_stack([np.ones(len(a)),a[e.f.NDVI]])
            rx=a[c]-design@np.linalg.lstsq(design,a[c],rcond=None)[0];ry=a[e.TARGET]-design@np.linalg.lstsq(design,a[e.TARGET],rcond=None)[0]
            rows.append(dict(excluded_id=pid,feature=c,n=len(a),n_profiles=eligible.climate_profile.nunique(),partial_correlation=pd.Series(rx).corr(pd.Series(ry))))
    pd.DataFrame(rows).to_csv(out/'audit/leave_one_parcel_partial.csv',index=False)
    orient=[]
    for near in [True,False]:
        z=t[(t[e.SLOPE]<2)==near];w,eligible=e.within(z,[e.SIN,e.COS,e.TARGET])
        for c in [e.SIN,e.COS]:orient.append(dict(near_flat_slope_q10_lt2=near,feature=c,n=len(z),n_within=len(w),n_profiles=eligible.climate_profile.nunique(),global_correlation=z[c].corr(z[e.TARGET]),within_correlation=w[c].corr(w[e.TARGET])))
    pd.DataFrame(orient).to_csv(out/'audit/orientation_flat_sensitivity.csv',index=False)
    summary='''# F4-E — Síntesis para decisiones

**La dimensión temporal LAI añade una mejora intraperfil pequeña; no mejora la predicción general.** Mantener lluvia + NDVI mayo como referencia sencilla. Considerar el inicio del mayor ascenso LAI únicamente como candidato de diferenciación local que merece validación independiente.

| Modelo | RMSE aleatorio | RMSE municipal | RMSE espacial | RMSE diferencias, igual peso por perfil, aleatorio |
|---|---:|---:|---:|---:|
| E1 lluvia + NDVI mayo | 0.50483 | 0.67110 | 0.73904 | 0.58920 |
| E2 añade inicio ascenso LAI | 0.50561 | 0.67500 | 0.73845 | 0.58335 |
| E3 añade relieve medio | 0.50740 | 0.68197 | 0.78146 | 0.59240 |
| E4 sustituye NDVI por LAI q10 | 0.51194 | 0.83558 | 0.95262 | 0.57991 |

**Estado frente a dinámica.** La correlación parcial del inicio LAI con diferencias de Y, después de controlar NDVI dentro del perfil, es −0.210 y −0.237 fuera de Chignahuapan. Al excluir perfiles por turno permanece entre −0.232 y −0.202. La mejora predictiva de E2 es pequeña, pero aparece con igual peso por perfil en los cuatro protocolos y también al excluir Chignahuapan. En aleatoria, el RMSE ponderado por parejas baja 0.77325→0.76724 y el MAE global apenas 0.36411→0.36368. Su signo es negativo en 94% de ajustes aleatorios. Es una dimensión temporal parcialmente distinta del estado NDVI, sin demostrar una fase fenológica real ni efecto causal.

**Estado frente a relieve.** La asociación parcial del relieve baja a +0.077 global intraperfil y +0.006 fuera de Chignahuapan. E3 no mejora la perspectiva local con igual peso por perfil en aleatoria, y empeora transferencia espacial en +0.0424 t/ha. Un coeficiente frecuentemente positivo no basta para justificar su incorporación. No añadir esta representación de relieve a E1.

**Redundancia entre índices.** NDVI q10, LAI q10 y FAPAR q10 muestran asociaciones parciales intraperfil pequeñas en el conjunto completo: −0.008, −0.026 y +0.024. Hay diferencias al excluir Chignahuapan; no puede afirmarse redundancia perfecta en todas las regiones. EVI mayo conserva una asociación parcial negativa (−0.173), pero no se entrenó una sensibilidad para convertir ese diagnóstico en búsqueda de un ganador. E4 mejora algunas métricas locales con igual peso, pero empeora la perspectiva ponderada por parejas frente a E1 y deteriora mucho municipios y espacio. LAI q10 no es una alternativa más estable para transferencia.

**Dentro frente a entre perfiles.** La evidencia más clara de E2 es local: mejora de diferencias entre parcelas del mismo clima, mismo modelo externo y después de controlar NDVI. Su RMSE general aumenta ligeramente. Los cambios de E2 en RMSE y MAE globales por protocolo permanecen dentro del margen descriptivo de 0.01 t/ha, pero eso no prueba equivalencia estadística. E4 ilustra que una mejora local de determinados perfiles puede coexistir con una transferencia regional pobre.

**Dependencia de Chignahuapan.** En aleatoria hay en promedio 208.4 parejas, 8.6 perfiles y 87.7 parcelas por repetición. Sin Chignahuapan quedan 21.3 parejas, 6.4 perfiles y 24.2 parcelas. El RMSE con igual peso fuera de ese municipio mejora E1→E2 de 0.50572 a 0.49992; no es exclusivamente un hallazgo de Chignahuapan. Esa muestra restante es pequeña y las parejas se solapan. E2 mejora MSE de diferencias en aproximadamente 76% de perfiles elegibles por repetición aleatoria y 70% fuera de Chignahuapan; son promedios de proporciones, no probabilidades independientes.

**Soporte y significado.** Los cinco índices tienen 31–43 fechas válidas únicas y siete meses válidos por parcela, con gaps máximos de hasta 28 días. Ninguna parcela incumple el umbral descriptivo de cuatro fechas/cuatro meses, pero eso no elimina sensibilidad a la distribución temporal. Al omitir un mes, el percentil 90 del cambio absoluto del inicio LAI es 15 días. Hay LAI negativos y no se estableció una escala física; el predictor representa la forma del índice suministrado. El relieve de DEM120m/vecindad360m no mide microtopografía fina. Las reservas de orientación en terrenos planos están en una auditoría secundaria, sin convertirlas en modelos nuevos.

**Complejidad y conjunto mínimo.** Para predicción general conservar lluvia + NDVI mayo. Para estudiar diferencias locales, añadir únicamente inicio LAI como candidato de una dimensión temporal, sin sumar índices de estado redundantes ni relieve medio. No se cambia el Champion ni se adopta automáticamente E2. No se entrenó una corrección residual adicional.

**Cuatro niveles de evidencia.** Las correlaciones parciales y descomposiciones son asociaciones descriptivas. E2 muestra complementariedad predictiva local modesta en estos folds. E3/E4 no muestran una mejora de transferencia frente a E1. Todo el módulo conserva sesgo de descubrimiento del screening retrospectivo: se necesitan nuevos rendimientos o geografías para confirmación independiente.

Se congelaron tres contrastes y se guardaron 195 modelos nuevos, cinco referencias/candidatos y 8,970 predicciones fuera de muestra. Los controles originales se recuperaron y reprodujeron en los 65 folds. Cinco pruebas automatizadas pasaron, incluidos replay de los 195 modelos, comparación exacta de controles, definiciones de características y métrica intraperfil. Ningún modelo ni resultado anterior se sobrescribió.
'''
    (out/'report/decision_summary.md').write_text(summary,encoding='utf-8')
    (e.ROOT/'documentation/family4_e_decision_summary.md').write_text(summary,encoding='utf-8')
    previous=json.loads((e.f.OUT/'manifest.json').read_text())
    assert all(e.sha(e.ROOT/path)==digest for path,digest in previous['artifacts'].items())
    config=json.loads((out/'configuration.json').read_text())
    assert config['source_hashes'][str(Path(e.__file__).relative_to(e.ROOT))]==e.sha(Path(e.__file__))
    files=[p for p in out.rglob('*') if p.is_file() and p.name!='manifest.json']+list(e.PROC.glob('*'))
    files += [e.ROOT/p for p in ['src/family_4/within_profile_complementarity.py','src/family_4/within_profile_reporting.py','scripts/338_family4_within_profile_complementarity.py','scripts/339_family4_e_finalize.py','tests/test_family4_within_profile_complementarity.py','documentation/family4_e_within_profile_complementarity.md','documentation/family4_e_decision_summary.md']]
    manifest=dict(status='complete',exploratory=True,n_train=138,n_prediction=59,n_experiments=5,n_new_experiments=3,n_outer=65,n_new_models=195,n_oof=8970,tests='5 passed',previous_family4_artifacts_verified=len(previous['artifacts']),hidden_y_used=False,packages={k:importlib.metadata.version(k) for k in ['numpy','pandas','scikit-learn','joblib']},artifacts={str(p.relative_to(e.ROOT)):e.sha(p) for p in files})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('F4-E COMPLETE;',len(previous['artifacts']),'previous artifacts unchanged;',len(files),'versioned files')

if __name__=='__main__':main()
