"""Refresh current result presentations from existing26/14 validation and59 outputs."""
from pathlib import Path
import csv
import json

ROOT=Path(__file__).resolve().parents[1]


def read(name):
    with (ROOT/name).open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))


def write(name,text):(ROOT/name).write_text(text,encoding='utf-8',newline='\n')


def main():
    audit=json.loads((ROOT/'results/current_champions_final/v1/prediction_audit.json').read_text(encoding='utf-8'))
    assert audit['n_predictions']==59 and audit['saved_model_replay_exact'] and audit['old_columns_unchanged']
    assert audit['champions_added']==['Reference26','Compact14']
    private=ROOT/'outputs/modeling/current_champions_final/v1'
    for name in ['Reference26','Compact14']:
        rows=read((private/(name+'_predictions59.csv')).relative_to(ROOT).as_posix())
        assert len(rows)==len({r['ID_POLIGONO'] for r in rows})==59
    index='''# Resultados vigentes — champions Reference26 y Compact14

**Los dos champions ya tienen ajuste final con138 rendimientos y59 predicciones generadas.** El modelo histórico TOP20/TOP15 y EQUAL3 son antecedentes; C-T3 es control y L40 benchmark externo. B1 es una sensibilidad, no un tercer champion.

| Presentación | Qué contiene | Cómo interpretarla |
|---|---|---|
| [Predicciones finales de26/14 y comparación59](current_champions_final/v1/README.md) | Distribución de las estimaciones y desacuerdos con C-T3, modelo histórico, EQUAL3 y L40 | Sin rendimientos verdaderos de59: no son errores ni R² de entrega |
| [Validación de los modelos actuales](current_champions/v1/README.md) | RMSE/R²/MAE, sesgo y residuos OOF de138 | Rendimiento bajo los cuatro protocolos originales; no rendimiento real de59 |
| [Banco adicional97/41](comparison_97_41/v1/README.md) |16 particiones con97 entrenamiento y41 evaluación | Mismas138 etiquetas; tabla separada, no confirmación independiente |
| [Relevancia de cuatro entradas C-T3](core4_relevance/v1/README.md) | Asociación y ablaciones reajustadas | Diagnóstico exploratorio; no significancia individual de26 entradas |
| [Evidencia por componente de26](reference26_component_evidence/v1/README.md) | Ablaciones históricas, interacciones y respaldo de funciones | Recuperación de experimentos existentes, con límites y faltantes |

Las predicciones por parcela, modelos, datos y OOF permanecen en `outputs/` y `data/`, excluidos de Git. Este directorio publica resúmenes agregados. Un clon sólo de Git no incluye los archivos privados.

[Fichas de los modelos](../documentation/models/README.md) · [Registro vigente](../documentation/model_registry.md).
'''
    if (ROOT/'results/four_final_checks/v1/README.md').exists():
        index+='\n[Cuatro investigaciones finales](four_final_checks/v1/README.md): reproducción limpia, soporte59, intervalos y sensibilidad completa sin HHI. No modifica los champions26/14.\n'
    write('results/README.md',index)
    metrics=read('results/current_champions/v1/metrics.csv')
    distributions=read('results/current_champions_final/v1/prediction_distributions.csv')
    pairs=read('results/current_champions_final/v1/pairwise_disagreement.csv')
    report='''# Resultados finales — Reference26 y Compact14

**Esta presentación corresponde a las59 predicciones finales de los dos champions actuales**, ajustados con los138 rendimientos conocidos. Incluye como referencias las estimaciones anteriores de C-T3, modelo histórico TOP20/TOP15, EQUAL3 y L40, preservadas sin cambios. No se promovió otro champion ni se eligieron pesos por acuerdo entre estas predicciones.

## Evidencia de validación de los champions

Estas métricas son OOF de las138 parcelas conocidas, **no errores de las59**. Son los65 folds originales:50 aleatorios,5 por perfil,5 municipales y5 espaciales. Aleatoria promedia métricas de10 OOF completas, no RMSE de folds.

| Modelo | Protocolo | RMSE t/ha | R² | MAE t/ha |
|---|---|---|---|---|
'''
    for model in ['Reference26','Compact14']:
        for protocol in ['random','climate_profile','municipality','spatial']:
            r=next(r for r in metrics if r['experiment']==model and r['protocol']==protocol)
            report+=f"| {model} | {protocol} | {float(r['rmse']):.4f} | {float(r['r2']):.4f} | {float(r['mae']):.4f} |\n"
    report+='\nEl resultado97/41 de26 (.4625 RMSE/.6971 R²) y14 (.4661/.6933) pertenece a [otra tabla de evaluación](../../comparison_97_41/v1/README.md), sobre las mismas etiquetas. Los residuos regionales y las auditorías OOF están en [validación actual](../../current_champions/v1/README.md).\n\n'
    report+='## Qué predicen para las59\n\nEstadísticos descriptivos en t/ha, no residuos ni intervalos de error:\n\n| Champion | Parcelas | Media | Desviación | Mínimo | Mediana | Máximo |\n|---|---|---|---|---|---|---|\n'
    for model in ['Reference26','Compact14']:
        r=next(r for r in distributions if r['model']==model+'_t_ha')
        report+=f"| {model} | {int(float(r['count']))} | {float(r['mean']):.4f} | {float(r['std']):.4f} | {float(r['min']):.4f} | {float(r['50%']):.4f} | {float(r['max']):.4f} |\n"
    report+='\n## Diferencias con otras predicciones\n\nDiferencia absoluta media: cercanía entre estimaciones, **no MAE contra rendimiento verdadero**. El rango entre modelos no es un intervalo predictivo.\n\n| A | B | Diferencia absoluta media, t/ha | Máxima diferencia absoluta |\n|---|---|---|---|\n'
    for r in pairs:
        if 'Reference26' not in r['model_A']+r['model_B'] and 'Compact14' not in r['model_A']+r['model_B']:continue
        report+=f"| {r['model_A']} | {r['model_B']} | {float(r['mean_absolute_disagreement']):.4f} | {float(r['max_absolute_disagreement']):.4f} |\n"
    report+='\n[Todos los pares y correlaciones](pairwise_disagreement.csv) · [Distribuciones de los seis modelos](prediction_distributions.csv). Los estados, municipios y parcelas con mayor desacuerdo están en el Excel privado.\n\n'
    report+='## Cómo se obtuvieron y comprobaron\n\n'
    report+='Las recetas congeladas se consolidaron con138 etiquetas y KFold interno4, shuffle y semilla2026. Las entradas PRED se incorporaron después de ajustar. Se verificó paridad de las26 variables reconstruidas en las138 conocidas y geometría congelada exacta. Las predicciones se reprodujeron desde el modelo guardado y no cambiaron al alterar etiquetas ficticias PRED sólo en memoria. El registro de exclusión interna se verificó.\n\n'
    report+=f"R3 dispone de soporte completo en{audit['R3_complete']}/59; en las otras se desactiva. La base C-T3 recalibrada nativamente difiere de su consolidación histórica en{audit['CT3_native_vs_historical_mean_abs']:.4f}t/ha de diferencia absoluta media. El Excel conserva ambas: la diferencia champion−C-T3 histórico incluye esa recalibración, además de las capas complementarias.\n\n"
    report+='La descomposición por parcela comprueba la suma de C-T3, mezcla local, corrector interno y ajuste R3. Es explicación del cálculo, no atribución causal. Se registró una advertencia ambiental OpenMP; el ajuste y las comprobaciones terminaron, sin advertencias de convergencia registradas. [Auditoría](prediction_audit.json) · [Procedencia de la generación](provenance.json). Las métricas de validación previas permanecen intactas.\n\n'
    report+='## Archivos finales locales\n\n'
    report+='| Archivo | Contenido |\n|---|---|\n'
    for name,label in [('Reference26_predictions59.csv','59 ID y rendimientos del champion26'),('Compact14_predictions59.csv','59 ID y rendimientos del champion14'),('comparacion_predicciones59.xlsx','Comparación de seis modelos, regiones, soporte y componentes'),('predictions59_comparison.csv','Tabla conjunta; ambas versiones C-T3 explícitas'),('champion_prediction_components.csv','Descomposición verificada de26/14'),('prediction_scatter59.png','Gráficas de desacuerdo por estado')]:
        report+=f'| [{name}](../../../outputs/modeling/current_champions_final/v1/{name}) | {label} |\n'
    report+='\nEstos enlaces requieren la copia local: `outputs/` no se sube a Git. Su existencia no acredita envío al comité. Todavía no conocemos el error de las59.\n\n'
    report+='[Ficha26](../../../documentation/models/Reference26/README.md) · [Ficha14](../../../documentation/models/Compact14/README.md) · [Índice de resultados](../../README.md). Generación reproducible: `scripts/526_current_champions_final59.py`; descomposición: `scripts/527_finalize_prediction_comparison.py`; esta presentación se regenera con `scripts/532_refresh_results_readmes.py` sin entrenar modelos.\n'
    if (ROOT/'results/reference26_distribution/v1/README.md').exists():
        report+='\n[Descriptivos de26:59 estimaciones frente a138 rendimientos, por estado y municipio](../../reference26_distribution/v1/README.md).\n'
    write('results/current_champions_final/v1/README.md',report)
    path=ROOT/'results/current_champions/v1/README.md';text=path.read_text(encoding='utf-8')
    text=text.replace('# Resultados actuales · Reference26 y Compact14','# Validación OOF — Reference26 y Compact14')
    text=text.replace('La selección de champions no implica que se hayan entrenado modelos finales con138 o generado una nueva entrega59.', 'Ambos champions ya tienen ajuste final138 y59 predicciones. Esos archivos se presentan por separado; esta página conserva exclusivamente la evidencia de validación.')
    note='**Predicciones finales disponibles:** [resultados de las59 de26/14](../../current_champions_final/v1/README.md). Las tablas de esta página son errores OOF sobre138 conocidas; no errores de las59.\n\n'
    if note not in text:
        first,_,rest=text.partition('\n');text=first+'\n\n'+note+rest.lstrip('\n')
    write(path.relative_to(ROOT),text)
    path=ROOT/'README.md';text=path.read_text(encoding='utf-8').replace('[Resultados](results/current_champions/v1/README.md)','[Resultados: validación y predicciones finales](results/README.md)')
    write('README.md',text)
    path=ROOT/'documentation/project_scope_and_guidelines.md';text=path.read_text(encoding='utf-8')
    old='Hay una [entrega histórica59](winner_predictions_statistical_validation.md). No sustituirla automáticamente por26/14: esos candidatos no tienen ajuste final138 ni nueva entrega59 en la última batería'
    new='Reference26 y Compact14 ya tienen ajuste final138 y archivos59 propios. [Predicciones vigentes y comparación](../results/current_champions_final/v1/README.md); las estimaciones del modelo histórico se conservan como antecedentes. Elegir el archivo a presentar no acredita envío al comité'
    text=text.replace(old,new)
    text=text.replace('Esta selección no produce automáticamente un ajuste final138, nuevas59 predicciones ni publicación del reto.', 'Ya se ejecutaron los ajustes finales138 y se generaron las59 predicciones de ambos champions por instrucción expresa. Esto no acredita publicación del reto ni conocer sus rendimientos reales.')
    write(path.relative_to(ROOT),text)
    path=ROOT/'documentation/model_registry.md';text=path.read_text(encoding='utf-8')
    text=text.replace('| Champion / `A_CURRENT_CH_H_T`','| Modelo histórico TOP20/TOP15 / `A_CURRENT_CH_H_T`')
    text=text.replace('La selección no genera automáticamente ajustes finales138 ni predicciones59.', 'Ambos champions ya tienen ajuste final138 y59 predicciones; la selección y la generación no acreditan envío ni conocer su error real.')
    text=text.replace('No implica nuevo ajuste final ni nuevas59.', 'Tiene ajuste final138 y59 estimaciones disponibles; su error real aún no se conoce.')
    write(path.relative_to(ROOT),text)
    print('Refreshed result indexes, OOF scope, final59 presentation and project status; no fits.')


if __name__=='__main__':main()
