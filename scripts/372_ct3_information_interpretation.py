"""Interpret frozen diagnostics; effective contrast support, no model fitting."""
from pathlib import Path
import json,hashlib
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/research/ct3_incremental_information/v1'
OUT=ROOT/'outputs/research/ct3_incremental_information/interpretation/v1'
OUT.mkdir(parents=True,exist_ok=False)
v=pd.read_csv(SOURCE/'phase_i/profile_variation.csv')
w=pd.read_csv(SOURCE/'phase_ii/within_profile_associations.csv')
w=w.merge(v[['variable','subset','contrasting_profiles','contrast_parcels']],on=['variable','subset'],validate='many_to_one')
w['contrast_support_sufficient']=(w.contrasting_profiles>=3)&(w.contrast_parcels>=20)
w['support_caveat']='original support flag counts all eligible groups; contrast flag counts groups with actual X variation; neither guarantees identifiability'
w.to_csv(OUT/'effective_contrast_support.csv',index=False)
s=pd.read_csv(SOURCE/'phase_ii/candidate_evidence_summary.csv')
decisions=pd.DataFrame([
 dict(block='LAI timing',status='potential bounded local experiment after review',evidence='11 contrasting profiles/104 parcels; balanced within r=-.230, outside=-.223, dominant omission=-.253',new_question='increment beyond compact4 rather than previous monthly-rain model',counterevidence='global OLS partial=-.042; OOF association changes sign between protocols',refutation='no local OOF gain or territorial harm; stop without expanding variables'),
 dict(block='SAVI duration',status='descriptive secondary, no automatic predictive extension',evidence='within r=.232; outside=.194; dominant omission=.228',new_question='different temporal dimension',counterevidence='spatial OOF-error association reverses negative; never independently validated incremental gain',refutation='unstable transfer; cannot use partial association alone to authorize model'),
 dict(block='slope',status='weak conditioned local evidence; F8 only as existing falsification design',evidence='12 contrasting profiles,69.3% linear residual variance',new_question='small correction on compact4, not repeating direct extension',counterevidence='within r=.072, dominant omission=.006; OOF spatial association sign differs',refutation='correction zero or geographic harm; no new parallel battery'),
 dict(block='history NDVI2',status='regional error-structure hypothesis, not primary parcel discriminator',evidence='spatial OOF error association mean=.530/std=.491',new_question='whether regional pattern is stable beyond current territories',counterevidence='within r=-.024/-.048; outside spatial associations differ from Chignahuapan; F7 direct harms',refutation='no independent incremental transfer; do not promote by residual correlation'),
 dict(block='soil/geology',status='do not prioritize new predictive expansion',evidence='geology entropy7 contrast profiles; soil coverage varies in1–7 profiles',new_question='cartographic versus parcel measurement support',counterevidence='geology within=.088; some soil signs supported by1–2 groups; broad map not chemistry',refutation='no stable parcel signal; prioritize measurement rather than more encodings'),
 dict(block='temperature/DTR',status='regional controls only for this dataset',evidence='zero within-profile contrast; some OLS/OOF associations remain',new_question='regional temporal information beyond compact rainfall',counterevidence='cannot distinguish parcels of same profile; previous DTR sensitivities and VIP not incremental benefit',refutation='no robust independent territorial gain; do not include as local corrector'),
])
decisions.to_csv(OUT/'block_decisions.csv',index=False)
text='''# Hallazgos y decisión tras fases I–II

Se completaron únicamente diagnósticos sobre información, no nuevos modelos predictivos. Esta interpretación acompaña la versión v1 sellada sin sobrescribirla. Nueve pruebas pasaron y65modelos originales C-T3 reprodujeron exactamente susOOF. No se ejecutaron F8, fasesIII/IV, Champion niPRED.

**La señal parcelaria adicional existe como variación; su utilidad incremental transferible sigue sin demostrar.** Se auditaron1,867nombres:1,839numéricos y28categóricos. Cincuenta son constantes/vacíos en138;1,501varían dentro de algún perfil, incluyendo covariables deC-T3 y redundancias. Setenta y cuatro grupos de igualdad observada reúnen162columnas; no son equivalencias físicas certificadas. Se excluyeron dos textos de identificación/resumen del análisis de dimensiones y ninguno de los identificadores/target/municipio/estado/coordenadas entró como predictor.

El rango numérico global138 es137, limitado por tamaño muestral. El rango efectivo por entropía es37.14con ponderación por columnas y26.66por bloques de inventario; esa dependencia de ponderación impide hablar de37o27factores agronómicos independientes. Clima96variables necesita5componentes para95%de varianzaX; temperatura115no constantes necesita3; Sentinel846necesita63. Es diagnóstico no supervisado, no prueba de predictividad. La estabilidad top5 por bootstrap de perfiles es limitada para suelo/geología; si el bloque tiene cinco o menos dimensiones se compara todo su subespacio y estabilidad1es casi trivial, no validación de componentes individuales.

**LAI y SAVI son contrastes temporales locales, pero no ganadores predictivos.** LAIinicio conserva97.49%de su variación frente a la proyección linealC-T3 y varía en11perfiles/104parcelas; SAVIduración conserva97.25%y varía en12/107. ControlandoNDVI y equilibrando perfiles, correlaciones conY=-.230y+.232. Fuera deChignahuapan=-.223y+.194; omitiendo ambos perfiles dominantes=-.253y+.228. ParaLAI, omitir cada perfil deja correlación entre-.281y-.195. El contraste local no depende exclusivamente deChignahuapan. Pero el parcial globalOLS condicionadoC-T3 es solo-.042y+.065, y las asociaciones con erroresOOF cambian de signo según protocolo. No es evidencia de mejora universal. El índiceLAI entregado tiene valores negativos y su fecha de ascenso no certifica una fase fenológica real.

**Pendiente conserva variación pero asociación parcelaria débil.** Residual lineal69.28%; contraste12perfiles/107parcelas. Correlación local equilibrada+.072, fuera+.106, sin perfiles dominantes+.006. Así, los nuevos datos no fortalecen una corrección de pendiente como solución intraperfil general. F8 continúa como prueba falsable previamente diseñada, no como recomendación validada ni ejecución autorizada.

**Historia presenta un patrón territorial más que una señal intraperfil clara.** Promedio ySTDhistóricos mantienen76.28%y48.11%de variación residual lineal; varían en12perfiles. Sus correlaciones locales equilibradas son-.024y-.048 y se aproximan a cero sin los perfiles dominantes. En cambio, la correlación con erroresOOF espacialesC-T3 es+.530/+.491; fuera deChignahuapan+.610/+.568 y dentro-.084/-.158. Esta asociación no estima el beneficio de añadir historia: puede reflejar cambio de dominio, error del modelo base y/o extrapolación de la proyecciónX. F7 ya mostró daño al añadir esos bloques. No convertir esas cifras en correctores regionales ni selección por territorio.

**Suelo y geología tienen soporte desigual.** Entropía geológica varía en7perfiles/83parcelas; fuera deChignahuapan el contraste se apoya en19parcelas/5perfiles. La correlación local+.088es pequeña. Algunas asociaciones edafológicas proceden de solo1–2perfiles con contraste, aun cuando la tabla de asociaciones contiene12perfiles totales. effective_contrast_support.csv distingue ambos conteos. La aparente estabilidad de un signo no basta con tan pocos grupos. Cartografía250kno equivale a análisis de suelo parcelario.

**Temperatura y DTR no añaden resolución intraperfil.** Los10controles climáticos de la faseII tienen cero perfiles con contraste. DTRstd conserva7.36%de variación frente a la proyecciónC-T3; Tmaxmayo34.28%. CambiosDTRagosto-septiembre yTmediaseptiembre-octubre tienen parciales globales-.198/+ .209, pero siguen constantes dentro de perfil. SusVIPaltos enPLS no identifican información parcelaria ni ganancia incremental. No se descarta que ayuden entre perfiles o bajo otra medición futura.

**Recomendación:** no iniciar una nueva compresión global ni una selección extensa. Si el objetivo prioritario es local y se autoriza una prueba posterior, el contraste más defendible sigue siendoC-T3+inicioLAI, una sola dimensión, comparado conC-T3sin cambios; preguntar si gana intraperfil con ambas ponderaciones sin deteriorar transferencia. Esa prioridad proviene de evidencia previa y estabilidad local, no de elegir el máximo del diagnóstico. Si se exige primero una ventaja territorial general, esta entrega no da evidencia suficiente para recomendar una expansión. Historia queda secundaria, pendiente conserva el diseñoF8existente para eventual revisión y suelo/geología requieren mejor medición antes de más representaciones. No se ejecutó ninguna de estas propuestas.

FWLretrospectivo utilizaOLS; el modeloC-T3real esElasticNet y sus erroresOOF no son residuosFWL. ResidualizarXlinealmente no prueba independencia condicional. El estudio no implementa inferenciaDMLni causal y no calcula significación tratando parejas/repeticiones como independientes. Las138etiquetas ya utilizadas extensamente requieren confirmación con nuevos perfiles, municipios o campañas.

La propuesta original incluye controles, validación, riesgos, criterios de aceptación, costos y detención en ../v1/report/next_phase_proposal.md. Esta interpretación acota sus prioridades con resultados reales y mantiene todas las propuestas pendientes de revisión.
'''
(OUT/'findings.md').write_text(text,encoding='utf-8')
hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file()}
manifest=dict(status='complete',new_fits=0,new_predictions=0,source_manifest_sha256=hashlib.sha256((SOURCE/'manifest.json').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),artifacts=hashes)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
doc=ROOT/'documentation/ct3_incremental_information_findings.md'
doc.write_text('# Hallazgos condicionados a C-T3\n\n[Interpretación y decisiones](../outputs/research/ct3_incremental_information/interpretation/v1/findings.md).\n\nComplementa el [informe técnico](../outputs/research/ct3_incremental_information/v1/report/technical_report.md) y la [propuesta no ejecutada](../outputs/research/ct3_incremental_information/v1/report/next_phase_proposal.md).\n',encoding='utf-8')
print('Interpretation complete; no new fits/predictions')
