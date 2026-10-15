# Informaci?n incremental condicionada a C-T3: hallazgos

Se completaron las fases I y II diagn?sticas. No se ejecutaron las fases III?IV, F8, nuevos predictores de rendimiento, modelos finales ni predicciones PRED. Se verificaron los 197 IDs, las 138 etiquetas y las 65 particiones originales. Los 65 modelos C-T3 reprodujeron exactamente sus OOF. Nueve pruebas automatizadas pasaron.

## Informaci?n disponible y redundancia

El cat?logo contiene 1,867 nombres: 1,839 num?ricos (incluidas binarias) y 28 categ?ricos. Cincuenta son constantes o vac?os en las 138 parcelas. Hay 1,501 columnas con contraste dentro de alg?n perfil, incluyendo NDVI del propio n?cleo y representaciones redundantes: no son 1,501 se?ales nuevas. Setenta y cuatro grupos de igualdad observada re?nen 162 columnas. La igualdad num?rica no certifica equivalencia f?sica ni independencia fuera de esta muestra.

El rango num?rico de la matriz centrada es 137, limitado por las 138 filas. Su rango efectivo espectral es 37.14 con ponderaci?n por columna y 26.66 con ponderaci?n por bloques de inventario. Es una descripci?n de redundancia sensible a la ponderaci?n, no un n?mero de factores agron?micos o dimensiones predictivas. Las componentes descriptivas calculadas sobre 197 parcelas no se entregan como transformaciones para validaci?n inductiva.

## Contraste y asociaci?n local

| Descriptor | Perfiles con contraste | Variaci?n no explicada por proyecci?n lineal C-T3 | Asociaci?n intraperfil equilibrada, controlando NDVI | Fuera de Chignahuapan | Sin ambos perfiles dominantes |
|---|---:|---:|---:|---:|---:|
| Inicio del ascenso LAI | 11 | 97.5% | ?0.230 | ?0.223 | ?0.253 |
| Duraci?n del ascenso SAVI | 12 | 97.3% | +0.232 | +0.194 | +0.228 |
| Pendiente media | 12 | 69.3% | +0.072 | +0.106 | +0.006 |
| NDVI hist?rico medio | 12 | 76.3% | ?0.024 | ?0.085 | ?0.008 |
| Dispersi?n hist?rica NDVI | 12 | 48.1% | ?0.048 | ?0.064 | ?0.009 |
| Entrop?a geol?gica | 7 | 96.8% | +0.088 | +0.097 | +0.150 |

Estas son asociaciones descriptivas, no efectos causales ni mejoras predictivas. La proyecci?n es lineal; su residuo no demuestra informaci?n condicional independiente. Los valores hist?ricos NDVI2 conservan la definici?n del proyecto: promedio y desviaci?n sobre las siete referencias mensuales hist?ricas; la desviaci?n no debe interpretarse como variabilidad interanual.

LAI presenta el contraste local m?s defendible por evidencia previa y estabilidad: al omitir cada perfil por turno, su correlaci?n queda entre ?0.281 y ?0.195. Fuera de Chignahuapan su contraste se respalda en 8 perfiles y 38 parcelas, frente a 2 perfiles y 62 parcelas dentro. SAVI tambi?n mantiene asociaci?n local, pero no tiene una demostraci?n de utilidad incremental equivalente.

La asociaci?n global OLS condicionada a C-T3 es peque?a para LAI (?0.042) y SAVI (+0.065). La relaci?n con errores OOF cambia de signo entre protocolos. Por tanto, estabilidad local no significa una ganancia global o territorial.

Pendiente conserva variaci?n pero su se?al intraperfil es d?bil y casi desaparece al omitir ambos perfiles grandes. No se fortalece la hip?tesis de una correcci?n local general; F8 sigue siendo un dise?o falsable pendiente de revisi?n.

Suelo y geolog?a muestran soporte desigual. Algunas clases edafol?gicas contrastan en solo uno o dos perfiles. La tabla suplementaria de soporte separa perfiles totales de perfiles con variaci?n efectiva, para evitar interpretar muchos pares como mucha informaci?n independiente. La cartograf?a 1:250,000 no equivale a medir propiedades f?sicas o qu?micas del suelo.

## Se?al territorial y errores de C-T3

Historia NDVI2 tiene correlaciones con los errores OOF espaciales de C-T3 de +0.530 y +0.491. Fuera de Chignahuapan son +0.610 y +0.568; dentro, ?0.084 y ?0.158. La se?al local equilibrada es d?bil. Esto apunta a un patr?n territorial en los errores o en la extrapolaci?n del modelo auxiliar, sin identificar su mecanismo ni demostrar que a?adir historia mejore la predicci?n. F7 ya mostr? costos al a?adir directamente esos bloques.

Los diez controles de temperatura/DTR carecen de contraste intraperfil. Algunos conservan asociaciones globales: cambio DTR agosto?septiembre ?0.198 y cambio Tmedia septiembre?octubre +0.209 despu?s del ajuste lineal por C-T3. Son se?ales entre perfiles; sus VIP altos no habilitan una correcci?n parcelaria dentro del mismo perfil.

El diagn?stico OOF utiliza predicciones C-T3 archivadas y proyecciones de X ajustadas solo con el entrenamiento externo. Sus errores no son residuos FWL: el C-T3 real es Elastic Net regularizado. No se implement? inferencia DML ni se entren? un corrector con esos errores.

## Decisi?n y propuesta

H1 se respalda para descriptores con contraste observado. H2 obtiene evidencia asociativa local moderada para din?mica vegetal y evidencia territorial para otros bloques, con reservas. H3 cuenta con un diagn?stico de compresibilidad, sin representaci?n predictiva validada. H4 no se ejecut? y sigue sin demostrarse.

No iniciar otra compresi?n global, screening de rendimiento ni divisi?n territorial autom?tica. Si se autoriza una prueba enfocada en diferenciaci?n local, C-T3 + inicio LAI es el contraste m?nimo m?s defendible: una sola variable adicional, frente al C-T3 congelado, validando errores absolutos y diferencias intraperfil con ambos pesos. La evidencia que lo justifica es F4-E y la estabilidad local de esta auditor?a; lo refutar?a ausencia de ganancia local OOF o deterioro territorial. No requiere PCA o PLS para una sola se?al.

Si el requisito prioritario es una mejora territorial general, esta entrega no basta para recomendar una expansi?n. Pendiente remite al dise?o F8 ya existente, sin duplicarlo ni ejecutarlo. Historia queda secundaria y no se priorizan nuevos modelos de cartograf?a gruesa. Necesitamos medici?n verificable de rendimiento/superficie, manejo y fechas, suelo parcelario y campa?as o municipios nuevos para confirmar beneficios.

## Entregables

- [Auditor?a por variable](../outputs/research/ct3_incremental_information/v1/phase_i/variable_audit.csv).
- [Dimensionalidad por bloques](../outputs/research/ct3_incremental_information/v1/phase_i/dimensionality.csv).
- [An?lisis condicionado](../outputs/research/ct3_incremental_information/v1/report/conditioned_analysis.md).
- [Informe t?cnico y diez respuestas](../outputs/research/ct3_incremental_information/v1/report/technical_report.md).
- [Propuesta posterior, no ejecutada](../outputs/research/ct3_incremental_information/v1/report/next_phase_proposal.md).
- [Soporte efectivo del contraste](../outputs/research/ct3_incremental_information/interpretation/v1/effective_contrast_support.csv).

La propuesta contiene controles, riesgos, costos y criterios de detenci?n. Los m?rgenes pr?cticos propuestos no son significaci?n estad?stica. Los nueve tests y los hashes validan la implementaci?n y preservaci?n de entradas, no resuelven el sesgo acumulado por reutilizar las mismas 138 etiquetas. Una ejecuci?n inicial incompleta qued? separada para trazabilidad; solo v1 con manifest completo contiene la entrega terminada.
