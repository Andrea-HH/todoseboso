"""Summarize frozen L/M results and verify provenance; never fit a model."""
from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np,pandas as pd
from src.family_1 import lm_multiblock as lm
from src.family_1 import k_geographic_edaphological as k

def synthesize(version='v1'):
    lo,_=lm.locations('L',version);mo,_=lm.locations('M',version)
    if not all((x/'manifest.json').exists() for x in [lo,mo]):raise ValueError('Both sections must be complete')
    l=pd.read_csv(lo/'tables/40_model_comparison.csv');m=pd.read_csv(mo/'tables/40_model_comparison.csv')
    li=l.set_index(['experiment','protocol']);mi=m.set_index(['experiment','protocol']);protocols=['random','climate_profile','municipality','spatial']
    comparisons=[]
    for representation in ['RAW','BLOCK_PCA']:
        for label,a,b in [('history','M0','M1'),('Planet','M0','M2'),('Landsat','M0','M3'),('Landsat_given_Planet','M2','M4'),('history_given_multisensor','M4','M5'),('multisensor_given_history','M1','M5')]:
            for protocol in protocols:
                aa=mi.loc[(a+'_'+representation,protocol)];bb=mi.loc[(b+'_'+representation,protocol)]
                comparisons.append(dict(question=label,representation=representation,protocol=protocol,baseline=a,candidate=b,delta_RMSE=aa.RMSE_mean-bb.RMSE_mean,delta_MAE=aa.MAE_mean-bb.MAE_mean))
    comparison=pd.DataFrame(comparisons);comparison.to_csv(mo/'tables/34_controlled_source_increments.csv',index=False)
    # Dimension budget is identical in candidate set, while chosen K is separately visible.
    registry=pd.read_csv(mo/'tables/11_registry.csv')
    registry[registry.experiment.str.endswith('BLOCK_PCA')].groupby(['experiment','protocol','n_effective']).size().rename('n_folds').reset_index().to_csv(mo/'tables/35_common_budget_dimensions.csv',index=False)
    def gain(table,a,b,protocol='random',metric='RMSE_mean'):return float(table.loc[(a,protocol),metric]-table.loc[(b,protocol),metric])
    lines=['# L/M — Síntesis transversal','','Se preservaron E–K, fuentes originales y Champion. Se usan138etiquetas,59parcelas sinY,53perfiles completos y los65folds congelados. Las métricas se calculan sobre cada OOF completo138 y luego se promedian las10repeticiones aleatorias.','', '1. **Base climática.** Lluvia y Climate Current48 tienen resultados aleatorios cercanos. Los valores por protocolo son:','',k.j.markdown_table(l[l.experiment.isin(['L0_BASE','L1_BASE'])][['experiment','protocol','RMSE_mean','MAE_mean','R2_mean']]),'', 'Se compara representación mensual de lluvia con una representación agregada más amplia que incluye temperatura: no es un efecto aislado de temperatura. Climate Current48 tampoco es TOP20 ni el Champion.','', '2. **PCA edafológico y arquitectura.** Ganancias deRMSE positivas favorecen al candidato. Misma S1 y mismas grillas en controles:','']
    soilrows=[]
    for base,number in [('rain',2),('current',3)]:
        for block,pcname in [('soil',f'L{number}'),('topo_soil',f'L{number+2}')]:
            raw=f'LC_{base}_{block}_residual_raw';direct=f'LC_{base}_{block}_direct_pca'
            for protocol in protocols:soilrows.append(dict(base=base,block=block,protocol=protocol,PCA_vs_original_residual=gain(li,raw,pcname,protocol),residual_vs_direct_PCA=gain(li,direct,pcname,protocol)))
    sd=pd.DataFrame(soilrows);sd.to_csv(lo/'tables/34_controlled_representation_architecture.csv',index=False);lines += [k.j.markdown_table(sd),'', 'PCA rota y reduce el espacio, pero no añade información intrínseca ni interacciones. Elastic Net L1 cambia geometría al rotar ejes; se distinguen cambio de representación y arquitectura. Los signos dePCs locales no se comparan ciegamente entre folds.','', '3. **Después del Champion.** Solo auditoría descriptiva de su residuo final OOF y asociaciones totales/intra/interperfil. L8 no se evaluó predictivamente: no se dispone de cross-fitting de las tres etapas con selección íntegramente anidada para reproducir fielmente el original. Las asociaciones no demuestran ganancia incremental ni justifican reentrenarlo.','', '4. **Historia, Planet y Landsat.** Incrementos controlados frente a Sentinel y otras combinaciones:','',k.j.markdown_table(comparison),'','La filaBLOCK_PCA usa presupuestos totales1/2/4, ajustados internamente; dimensiones efectivamente elegidas están en tabla35. Raw cambia número de variables: una ganancia allí no se atribuye exclusivamente a nueva información sin contrastar presupuesto.','', 'Las anomalías actuales−historia son deterministas a partir de esas dos fuentes. Familia1 ya contenía resúmenes históricos/anomalías; tabla05M identifica superposición. M estudia trayectoria mensual, soporte y diferencias de distribución, no un primer descubrimiento de historia. La referencia2022–24 no incluye2025 y no es una normal climatológica.','', 'Planet solo tiene2025 en Básico/PRO; sus datos agregados no permiten inventar percentiles espaciales de píxeles. NDVI/EVI compartidos no certifican ecuaciones/bandas idénticas ni calibración. LandsatVI6T se trata como bloque propio. Comparación por calendario no equivale a misma fecha ni prueba que la resolución cause una mejora.','', '5. **Transferencia y futura integración.** Cribado con mejora aleatoria y sin deterioro>.01 de RMSEagrupado/MAEen todos los protocolos:','']
    dl=pd.read_csv(lo/'tables/31_operational_decisions.csv');dm=pd.read_csv(mo/'tables/31_operational_decisions.csv')
    lines += [k.j.markdown_table(dl), '',k.j.markdown_table(dm),'', 'Estas pantallas son exploratorias, no significancia ni decisión automática. Para integración hacen falta además estabilidad, soporte, ausencia de correcciones extremas, mejora intraperfil y validación con nuevas etiquetas/geografías. Los folds/repeticiones comparten observaciones. Ningún resultado cambiaChampion.','', '6. **Suelo tras satélite.** Tabla32M informa asociaciones residuales de suelo tras clima+M5. Es exploración fuera de muestra, no una tercera etapa validada ni prueba de mejora predictiva adicional.','', 'Diagnósticos específicos: Chignahuapan71etiquetas pertenece al mismoOOF; parejas intraperfil solo por un mismo modelo externo; nubes/faltantes y reservas50/125/250m se retienen. Suelo1:250000 es cartografía temática, topografíaCEM4 tiene120m local, clima≈.05°, resoluciones satelitales son referencias de sensor no grillas verificadas de extracción. Fechas de procesamiento/disponibilidad y cultivos históricos no se suministran; los máximos no validan fenología. No hay etiquetas históricas para validar transferencia a otro año.','', 'Reportes: [L](l_multiblock_representation.md), [M](m_historical_multisensor.md).']
    text='\n'.join(lines)+'\n';(lm.ROOT/'documentation/l_m_synthesis.md').write_text(text,encoding='utf-8')
    # Add objective-based prose to the independent section reports, keeping numeric results fixed.
    for section,out in [('L',lo),('M',mo)]:
        name='l_report.md' if section=='L' else 'm_report.md';p=out/'report'/name
        current=p.read_text(encoding='utf-8').split('\n## Comparaciones controladas finales')[0]
        t=sd if section=='L' else comparison
        current+='\n## Comparaciones controladas finales\n\n'+k.j.markdown_table(t)+'\n\nMejoras positivas favorecen al candidato. Interpretar cada protocolo por separado; revisar MAE, categorías y error intraperfil antes de integrar. La síntesis transversal conserva resultados negativos y limita conclusiones al objetivo evaluado.\n'
        p.write_text(current,encoding='utf-8')
        doc='l_multiblock_representation.md' if section=='L' else 'm_historical_multisensor.md'
        (lm.ROOT/'documentation'/doc).write_text(current.replace('../figures/',f'../outputs/modeling/family_1/{lm.NAMES[section]}/{version}/figures/'),encoding='utf-8')
    print('L/M synthesis complete',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='v1');a=p.parse_args();synthesize(a.run_id)
