> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Comparación completa de residuos: L40, C-T3, J7 y expertos 9/10

## Alcance y comparabilidad

Se auditaron las predicciones externas de las 138 parcelas conocidas en las mismas 65 particiones: 50 aleatorias (10 repeticiones de cinco folds), cinco por perfil climático, cinco municipales y cinco espaciales. Cada modelo aporta 1,794 predicciones; nueve variantes, 16,146. En aleatoria se calcula cada métrica sobre las 138 OOF de cada repetición y después se promedian las diez métricas. No se promedian métricas de folds ni se fusionan protocolos. El error se define como predicho menos observado.

L40 significa Local04D original: representación de 2,082 descriptores, PCA20 y Ridge local con 24 vecinos geográficos. Su PCA original utiliza características de las 197 parcelas sin targets ocultos (representación transductiva); esta auditoría conserva esa definición. No es una comparación puramente inductiva de todos los preprocesamientos. Se excluyó el banco GeoC 97/41, incompatible con estas particiones. La referencia CT3 coincide exactamente entre pipelines y J7 se reprodujo exactamente desde sus modelos guardados.

J7_BOTH es la mezcla compacta con experto local de siete variables y asignación de peso mediante características físicas. MIX_EXPERT10 y MIX_EXPERT9 son las mezclas alternativas; no deben confundirse con sus ramas EXPERT10 y EXPERT9 aisladas. Los recuentos 28/31/30 son campos de entrada distintos de las arquitecturas completas, no grados de libertad efectivos; las etiquetas 7/9/10 cuentan variables del experto local. Se reconstruyeron las ramas desde parámetros congelados, sin reentrenar ni modificar modelos.

## Panorama: RMSE / R²


| modelo | fields | random | climate_profile | municipality | spatial |
| --- | --- | --- | --- | --- | --- |
| LOCAL04D | 2082 | 0.4930 / 0.6619 | 0.5031 / 0.6481 | 0.7602 / 0.1964 | 0.9794 / -0.3337 |
| CT3 | 4 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| J7_BOTH | 28 | 0.4864 / 0.6709 | 0.4890 / 0.6675 | 0.5808 / 0.5309 | 0.6808 / 0.3556 |
| MIX_EXPERT10 | 31 | 0.4870 / 0.6701 | 0.4871 / 0.6702 | 0.5811 / 0.5306 | 0.6840 / 0.3494 |
| MIX_EXPERT9 | 30 | 0.4874 / 0.6696 | 0.4897 / 0.6666 | 0.5807 / 0.5311 | 0.6811 / 0.3550 |
| BIG_BOTH | 1850 | 0.4852 / 0.6725 | 0.4996 / 0.6530 | 0.5847 / 0.5247 | 0.6811 / 0.3549 |
| EXPERT7 | 13 | 0.4898 / 0.6664 | 0.4880 / 0.6689 | 0.6560 / 0.4016 | 0.8089 / 0.0902 |
| EXPERT10 | 16 | 0.4905 / 0.6653 | 0.4862 / 0.6714 | 0.6564 / 0.4010 | 0.8342 / 0.0325 |
| EXPERT9 | 15 | 0.4908 / 0.6650 | 0.4885 / 0.6682 | 0.6568 / 0.4002 | 0.8139 / 0.0790 |



J7 reduce frente a CT3 el RMSE aleatorio en 0.0252 t/ha (4.9%) y por perfil en 0.0316 (6.1%). La diferencia municipal es 0.0004 y espacial empeora 0.0020: no hay evidencia de una ganancia territorial relevante. Local04D conserva una interpolación competitiva, pero pierde mucho al excluir municipios o bloques. Las tres mezclas compactas son prácticamente indistinguibles a esta escala.

## Magnitud, dirección y frecuencia del error


| experiment | protocol | rmse | mae | r2 | bias | error_sd | p95_absolute | within_050 | within_100 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CT3 | climate_profile | 0.5206 | 0.3915 | 0.6232 | 0.0046 | 0.5206 | 1.0115 | 0.7391 | 0.9493 |
| CT3 | municipality | 0.5813 | 0.4603 | 0.5302 | -0.0203 | 0.5809 | 1.0790 | 0.6739 | 0.9348 |
| CT3 | random | 0.5116 | 0.3749 | 0.6361 | 0.0005 | 0.5115 | 1.0529 | 0.7754 | 0.9384 |
| CT3 | spatial | 0.6788 | 0.5306 | 0.3594 | 0.1912 | 0.6513 | 1.4223 | 0.5942 | 0.8406 |
| J7_BOTH | climate_profile | 0.4890 | 0.3445 | 0.6675 | -0.0139 | 0.4888 | 0.9172 | 0.7609 | 0.9565 |
| J7_BOTH | municipality | 0.5808 | 0.4604 | 0.5309 | -0.0205 | 0.5805 | 1.0790 | 0.6884 | 0.9348 |
| J7_BOTH | random | 0.4864 | 0.3470 | 0.6709 | -0.0121 | 0.4862 | 0.8553 | 0.7616 | 0.9616 |
| J7_BOTH | spatial | 0.6808 | 0.5291 | 0.3556 | 0.2913 | 0.6153 | 1.4279 | 0.5580 | 0.8478 |
| LOCAL04D | climate_profile | 0.5031 | 0.3479 | 0.6481 | 0.0108 | 0.5029 | 1.0292 | 0.7174 | 0.9420 |
| LOCAL04D | municipality | 0.7602 | 0.5991 | 0.1964 | 0.1051 | 0.7529 | 1.4204 | 0.5145 | 0.8043 |
| LOCAL04D | random | 0.4930 | 0.3526 | 0.6619 | -0.0090 | 0.4928 | 0.9053 | 0.7355 | 0.9587 |
| LOCAL04D | spatial | 0.9794 | 0.7434 | -0.3337 | 0.4707 | 0.8589 | 1.9792 | 0.4928 | 0.6812 |
| MIX_EXPERT10 | climate_profile | 0.4871 | 0.3429 | 0.6702 | -0.0090 | 0.4870 | 0.8931 | 0.7609 | 0.9638 |
| MIX_EXPERT10 | municipality | 0.5811 | 0.4611 | 0.5306 | -0.0210 | 0.5807 | 1.0790 | 0.6812 | 0.9420 |
| MIX_EXPERT10 | random | 0.4870 | 0.3483 | 0.6701 | -0.0117 | 0.4868 | 0.8624 | 0.7623 | 0.9616 |
| MIX_EXPERT10 | spatial | 0.6840 | 0.5327 | 0.3494 | 0.3043 | 0.6126 | 1.4375 | 0.5580 | 0.8478 |
| MIX_EXPERT9 | climate_profile | 0.4897 | 0.3451 | 0.6666 | -0.0106 | 0.4896 | 0.8988 | 0.7609 | 0.9565 |
| MIX_EXPERT9 | municipality | 0.5807 | 0.4602 | 0.5311 | -0.0209 | 0.5803 | 1.0790 | 0.6884 | 0.9348 |
| MIX_EXPERT9 | random | 0.4874 | 0.3479 | 0.6696 | -0.0108 | 0.4872 | 0.8603 | 0.7594 | 0.9616 |
| MIX_EXPERT9 | spatial | 0.6811 | 0.5300 | 0.3550 | 0.2928 | 0.6149 | 1.4272 | 0.5652 | 0.8478 |



within_050 y within_100 son fracciones de errores absolutos dentro de 0.5 y 1 t/ha. RMSE penaliza especialmente errores grandes; MAE mide la desviación absoluta media. No son intervalos predictivos por parcela.

CT3 coloca el 77.5% de errores aleatorios dentro de 0.5 t/ha, frente al 76.2% de J7, aunque J7 tiene menor RMSE y MAE. J7 mejora el balance de magnitudes y reduce la cola: percentil 95 del error absoluto de 0.855 frente a 1.053 t/ha. Por ello no mejora cada parcela ni cada umbral. Local04D queda en 73.6% dentro de 0.5.

El sesgo aleatorio agregado es cercano a cero para todos, pero no significa ausencia de sesgos regionales. En espacial, CT3 sobreestima 0.191 t/ha; J7 0.291; Local04D 0.471. La componente local puede reducir dispersión mientras incrementa el desplazamiento positivo. Las tablas incluyen la identidad MSE = varianza del error + sesgo² por repetición.

## Dónde funciona cada modelo


| experiment | protocol | zone | n | rmse | mae | r2 | bias |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CT3 | climate_profile | Hidalgo | 36.0000 | 0.4565 | 0.3483 | 0.6455 | 0.0366 |
| CT3 | climate_profile | Puebla | 71.0000 | 0.5495 | 0.3912 | 0.1033 | -0.0553 |
| CT3 | climate_profile | Tlaxcala | 31.0000 | 0.5224 | 0.4423 | -0.9946 | 0.1047 |
| CT3 | municipality | Hidalgo | 36.0000 | 0.6452 | 0.5180 | 0.2918 | 0.2143 |
| CT3 | municipality | Puebla | 71.0000 | 0.5807 | 0.4483 | -0.0014 | -0.2011 |
| CT3 | municipality | Tlaxcala | 31.0000 | 0.4983 | 0.4209 | -0.8143 | 0.1212 |
| CT3 | random | Hidalgo | 36.0000 | 0.4385 | 0.3295 | 0.6727 | 0.0252 |
| CT3 | random | Puebla | 71.0000 | 0.5564 | 0.3824 | 0.0804 | -0.0186 |
| CT3 | random | Tlaxcala | 31.0000 | 0.4822 | 0.4108 | -0.6998 | 0.0156 |
| CT3 | spatial | Hidalgo | 36.0000 | 0.6530 | 0.5401 | 0.2746 | 0.2732 |
| CT3 | spatial | Puebla | 71.0000 | 0.5499 | 0.3906 | 0.1018 | -0.0817 |
| CT3 | spatial | Tlaxcala | 31.0000 | 0.9291 | 0.8403 | -5.3079 | 0.7209 |
| J7_BOTH | climate_profile | Hidalgo | 36.0000 | 0.3505 | 0.2626 | 0.7910 | -0.0179 |
| J7_BOTH | climate_profile | Puebla | 71.0000 | 0.5625 | 0.3732 | 0.0602 | -0.0149 |
| J7_BOTH | climate_profile | Tlaxcala | 31.0000 | 0.4441 | 0.3738 | -0.4410 | -0.0069 |
| J7_BOTH | municipality | Hidalgo | 36.0000 | 0.6615 | 0.5375 | 0.2558 | 0.2164 |
| J7_BOTH | municipality | Puebla | 71.0000 | 0.5798 | 0.4465 | 0.0015 | -0.1983 |
| J7_BOTH | municipality | Tlaxcala | 31.0000 | 0.4731 | 0.4025 | -0.6355 | 0.1114 |
| J7_BOTH | random | Hidalgo | 36.0000 | 0.3678 | 0.2715 | 0.7698 | -0.0278 |
| J7_BOTH | random | Puebla | 71.0000 | 0.5626 | 0.3928 | 0.0598 | -0.0127 |
| J7_BOTH | random | Tlaxcala | 31.0000 | 0.4136 | 0.3298 | -0.2520 | 0.0077 |
| J7_BOTH | spatial | Hidalgo | 36.0000 | 0.6536 | 0.5408 | 0.2733 | 0.3002 |
| J7_BOTH | spatial | Puebla | 71.0000 | 0.5493 | 0.3846 | 0.1040 | 0.0928 |
| J7_BOTH | spatial | Tlaxcala | 31.0000 | 0.9361 | 0.8463 | -5.4032 | 0.7357 |
| LOCAL04D | climate_profile | Hidalgo | 36.0000 | 0.3293 | 0.2470 | 0.8155 | -0.0066 |
| LOCAL04D | climate_profile | Puebla | 71.0000 | 0.5927 | 0.3911 | -0.0432 | -0.0143 |
| LOCAL04D | climate_profile | Tlaxcala | 31.0000 | 0.4428 | 0.3662 | -0.4328 | 0.0884 |
| LOCAL04D | municipality | Hidalgo | 36.0000 | 0.9694 | 0.7490 | -0.5983 | 0.4662 |
| LOCAL04D | municipality | Puebla | 71.0000 | 0.6539 | 0.5152 | -0.2697 | -0.2844 |
| LOCAL04D | municipality | Tlaxcala | 31.0000 | 0.7089 | 0.6172 | -2.6725 | 0.5778 |
| LOCAL04D | random | Hidalgo | 36.0000 | 0.3406 | 0.2537 | 0.8024 | -0.0355 |
| LOCAL04D | random | Puebla | 71.0000 | 0.5829 | 0.4156 | -0.0099 | -0.0166 |
| LOCAL04D | random | Tlaxcala | 31.0000 | 0.4106 | 0.3232 | -0.2333 | 0.0391 |
| LOCAL04D | spatial | Hidalgo | 36.0000 | 0.9835 | 0.7601 | -0.6454 | 0.6248 |
| LOCAL04D | spatial | Puebla | 71.0000 | 0.6082 | 0.4170 | -0.0985 | -0.0442 |
| LOCAL04D | spatial | Tlaxcala | 31.0000 | 1.5164 | 1.4713 | -15.8056 | 1.4713 |
| MIX_EXPERT10 | climate_profile | Hidalgo | 36.0000 | 0.3507 | 0.2629 | 0.7908 | -0.0198 |
| MIX_EXPERT10 | climate_profile | Puebla | 71.0000 | 0.5598 | 0.3707 | 0.0694 | -0.0067 |
| MIX_EXPERT10 | climate_profile | Tlaxcala | 31.0000 | 0.4422 | 0.3724 | -0.4292 | -0.0018 |
| MIX_EXPERT10 | municipality | Hidalgo | 36.0000 | 0.6589 | 0.5368 | 0.2615 | 0.2129 |
| MIX_EXPERT10 | municipality | Puebla | 71.0000 | 0.5799 | 0.4467 | 0.0012 | -0.1984 |
| MIX_EXPERT10 | municipality | Tlaxcala | 31.0000 | 0.4781 | 0.4063 | -0.6702 | 0.1137 |
| MIX_EXPERT10 | random | Hidalgo | 36.0000 | 0.3687 | 0.2711 | 0.7686 | -0.0279 |
| MIX_EXPERT10 | random | Puebla | 71.0000 | 0.5632 | 0.3951 | 0.0577 | -0.0122 |
| MIX_EXPERT10 | random | Tlaxcala | 31.0000 | 0.4140 | 0.3306 | -0.2541 | 0.0084 |
| MIX_EXPERT10 | spatial | Hidalgo | 36.0000 | 0.6544 | 0.5420 | 0.2716 | 0.3009 |
| MIX_EXPERT10 | spatial | Puebla | 71.0000 | 0.5513 | 0.3883 | 0.0973 | 0.1129 |
| MIX_EXPERT10 | spatial | Tlaxcala | 31.0000 | 0.9431 | 0.8529 | -5.5002 | 0.7467 |
| MIX_EXPERT9 | climate_profile | Hidalgo | 36.0000 | 0.3544 | 0.2673 | 0.7864 | -0.0168 |
| MIX_EXPERT9 | climate_profile | Puebla | 71.0000 | 0.5625 | 0.3724 | 0.0603 | -0.0106 |
| MIX_EXPERT9 | climate_profile | Tlaxcala | 31.0000 | 0.4439 | 0.3732 | -0.4401 | -0.0032 |
| MIX_EXPERT9 | municipality | Hidalgo | 36.0000 | 0.6615 | 0.5375 | 0.2557 | 0.2161 |
| MIX_EXPERT9 | municipality | Puebla | 71.0000 | 0.5798 | 0.4466 | 0.0015 | -0.1983 |
| MIX_EXPERT9 | municipality | Tlaxcala | 31.0000 | 0.4722 | 0.4017 | -0.6295 | 0.1104 |
| MIX_EXPERT9 | random | Hidalgo | 36.0000 | 0.3719 | 0.2749 | 0.7646 | -0.0247 |
| MIX_EXPERT9 | random | Puebla | 71.0000 | 0.5624 | 0.3921 | 0.0604 | -0.0121 |
| MIX_EXPERT9 | random | Tlaxcala | 31.0000 | 0.4150 | 0.3313 | -0.2606 | 0.0082 |
| MIX_EXPERT9 | spatial | Hidalgo | 36.0000 | 0.6538 | 0.5413 | 0.2729 | 0.3006 |
| MIX_EXPERT9 | spatial | Puebla | 71.0000 | 0.5501 | 0.3863 | 0.1012 | 0.0960 |
| MIX_EXPERT9 | spatial | Tlaxcala | 31.0000 | 0.9357 | 0.8461 | -5.3989 | 0.7346 |



La principal fortaleza propia de Local04D aparece en Hidalgo bajo aleatoria: RMSE 0.341 y R² 0.802, frente a 0.368/0.770 de J7 y 0.439/0.673 de CT3. Con vecinos territoriales presentes aprovecha estructura local. Esta ventaja no se conserva al retirar territorios.

En Puebla aleatoria, CT3 obtiene RMSE 0.556 y R² 0.080 frente a 0.563/0.060 de J7. El R² global de aproximadamente 0.67 no equivale a explicar 67% dentro de cada estado. En Tlaxcala el R² aleatorio es negativo para todos; su escasa variabilidad del target hace que diferencias moderadas de error produzcan R² muy negativos. Un R² negativo compara contra la media observada del subconjunto, que no sería conocida al predecir.

## Transferencia municipal


| experiment | zone | n | rmse | mae | r2 | bias |
| --- | --- | --- | --- | --- | --- | --- |
| CT3 | Almoloya | 10.0000 | 0.3529 | 0.3197 | -2.8963 | -0.3197 |
| CT3 | Apan | 1.0000 | 0.4102 | 0.4102 | nan | 0.4102 |
| CT3 | Calpulalpan | 30.0000 | 0.4933 | 0.4140 | -0.8254 | 0.1043 |
| CT3 | Chignahuapan | 71.0000 | 0.5807 | 0.4483 | -0.0014 | -0.2011 |
| CT3 | Cuautepec de Hinojosa | 5.0000 | 0.4827 | 0.3799 | -11.8493 | -0.1396 |
| CT3 | Emiliano Zapata | 3.0000 | 0.1977 | 0.1684 | nan | -0.1483 |
| CT3 | Nanacamilpa de Mariano Arista | 1.0000 | 0.6280 | 0.6280 | nan | 0.6280 |
| CT3 | Singuilucan | 16.0000 | 0.8677 | 0.7589 | -3.2651 | 0.7589 |
| CT3 | Tepeapulco | 1.0000 | 0.4959 | 0.4959 | nan | -0.4959 |
| J7_BOTH | Almoloya | 10.0000 | 0.3529 | 0.3197 | -2.8963 | -0.3197 |
| J7_BOTH | Apan | 1.0000 | 0.4037 | 0.4037 | nan | 0.4037 |
| J7_BOTH | Calpulalpan | 30.0000 | 0.4710 | 0.3982 | -0.6641 | 0.0975 |
| J7_BOTH | Chignahuapan | 71.0000 | 0.5798 | 0.4465 | 0.0015 | -0.1983 |
| J7_BOTH | Cuautepec de Hinojosa | 5.0000 | 0.4810 | 0.3782 | -11.7561 | -0.0913 |
| J7_BOTH | Emiliano Zapata | 3.0000 | 0.3152 | 0.2937 | nan | -0.2937 |
| J7_BOTH | Nanacamilpa de Mariano Arista | 1.0000 | 0.5304 | 0.5304 | nan | 0.5304 |
| J7_BOTH | Singuilucan | 16.0000 | 0.8877 | 0.7781 | -3.4641 | 0.7781 |
| J7_BOTH | Tepeapulco | 1.0000 | 0.5290 | 0.5290 | nan | -0.5290 |
| LOCAL04D | Almoloya | 10.0000 | 0.2140 | 0.1800 | -0.4323 | -0.1546 |
| LOCAL04D | Apan | 1.0000 | 0.0526 | 0.0526 | nan | -0.0526 |
| LOCAL04D | Calpulalpan | 30.0000 | 0.7134 | 0.6192 | -2.8171 | 0.5785 |
| LOCAL04D | Chignahuapan | 71.0000 | 0.6539 | 0.5152 | -0.2697 | -0.2844 |
| LOCAL04D | Cuautepec de Hinojosa | 5.0000 | 0.3714 | 0.2888 | -6.6047 | -0.1535 |
| LOCAL04D | Emiliano Zapata | 3.0000 | 0.5555 | 0.5555 | nan | -0.5555 |
| LOCAL04D | Nanacamilpa de Mariano Arista | 1.0000 | 0.5571 | 0.5571 | nan | 0.5571 |
| LOCAL04D | Singuilucan | 16.0000 | 1.4009 | 1.3381 | -10.1180 | 1.3381 |
| LOCAL04D | Tepeapulco | 1.0000 | 0.5919 | 0.5919 | nan | -0.5919 |
| MIX_EXPERT10 | Almoloya | 10.0000 | 0.3529 | 0.3197 | -2.8963 | -0.3197 |
| MIX_EXPERT10 | Apan | 1.0000 | 0.4023 | 0.4023 | nan | 0.4023 |
| MIX_EXPERT10 | Calpulalpan | 30.0000 | 0.4764 | 0.4023 | -0.7021 | 0.0999 |
| MIX_EXPERT10 | Chignahuapan | 71.0000 | 0.5799 | 0.4467 | 0.0012 | -0.1984 |
| MIX_EXPERT10 | Cuautepec de Hinojosa | 5.0000 | 0.4851 | 0.3830 | -11.9745 | -0.0963 |
| MIX_EXPERT10 | Emiliano Zapata | 3.0000 | 0.3225 | 0.3020 | nan | -0.3020 |
| MIX_EXPERT10 | Nanacamilpa de Mariano Arista | 1.0000 | 0.5260 | 0.5260 | nan | 0.5260 |
| MIX_EXPERT10 | Singuilucan | 16.0000 | 0.8822 | 0.7734 | -3.4092 | 0.7734 |
| MIX_EXPERT10 | Tepeapulco | 1.0000 | 0.5300 | 0.5300 | nan | -0.5300 |
| MIX_EXPERT9 | Almoloya | 10.0000 | 0.3529 | 0.3197 | -2.8963 | -0.3197 |
| MIX_EXPERT9 | Apan | 1.0000 | 0.4061 | 0.4061 | nan | 0.4061 |
| MIX_EXPERT9 | Calpulalpan | 30.0000 | 0.4702 | 0.3975 | -0.6585 | 0.0966 |
| MIX_EXPERT9 | Chignahuapan | 71.0000 | 0.5798 | 0.4466 | 0.0015 | -0.1983 |
| MIX_EXPERT9 | Cuautepec de Hinojosa | 5.0000 | 0.4803 | 0.3755 | -11.7207 | -0.0920 |
| MIX_EXPERT9 | Emiliano Zapata | 3.0000 | 0.3192 | 0.2981 | nan | -0.2981 |
| MIX_EXPERT9 | Nanacamilpa de Mariano Arista | 1.0000 | 0.5273 | 0.5273 | nan | 0.5273 |
| MIX_EXPERT9 | Singuilucan | 16.0000 | 0.8877 | 0.7781 | -3.4637 | 0.7781 |
| MIX_EXPERT9 | Tepeapulco | 1.0000 | 0.5258 | 0.5258 | nan | -0.5258 |



En Singuilucan, Local04D tiene RMSE 1.401 y sesgo +1.338, frente a 0.888/+0.778 de J7 y 0.868/+0.759 de CT3. En Calpulalpan, J7 mejora respecto a CT3 (0.471 frente a 0.493) y claramente respecto a Local04D (0.713). En Chignahuapan, J7 y CT3 quedan prácticamente empatados (0.580 y 0.581). Los expertos 9/10 no resuelven una estructura municipal diferente de J7.

## Transferencia espacial y bloques


| experiment | zone | n | rmse | mae | r2 | bias |
| --- | --- | --- | --- | --- | --- | --- |
| CT3 | 1 | 38.0000 | 0.5054 | 0.3501 | 0.1355 | -0.0369 |
| CT3 | 2 | 37.0000 | 0.5725 | 0.4169 | -0.0227 | -0.1193 |
| CT3 | 3 | 35.0000 | 0.9096 | 0.8240 | -4.8248 | 0.7182 |
| CT3 | 4 | 18.0000 | 0.7990 | 0.6878 | -0.6987 | 0.5743 |
| CT3 | 5 | 10.0000 | 0.3602 | 0.3278 | -3.0584 | -0.3278 |
| J7_BOTH | 1 | 38.0000 | 0.5246 | 0.3640 | 0.0687 | 0.1869 |
| J7_BOTH | 2 | 37.0000 | 0.5537 | 0.3911 | 0.0436 | 0.0131 |
| J7_BOTH | 3 | 35.0000 | 0.9160 | 0.8291 | -4.9067 | 0.7311 |
| J7_BOTH | 4 | 18.0000 | 0.7988 | 0.6875 | -0.6980 | 0.5746 |
| J7_BOTH | 5 | 10.0000 | 0.3621 | 0.3316 | -3.1012 | -0.3316 |
| LOCAL04D | 1 | 38.0000 | 0.5675 | 0.3253 | -0.0897 | 0.1738 |
| LOCAL04D | 2 | 37.0000 | 0.6176 | 0.4810 | -0.1902 | -0.2604 |
| LOCAL04D | 3 | 35.0000 | 1.4594 | 1.3962 | -13.9947 | 1.3962 |
| LOCAL04D | 4 | 18.0000 | 1.3127 | 1.2088 | -3.5854 | 1.1485 |
| LOCAL04D | 5 | 10.0000 | 0.2140 | 0.1800 | -0.4323 | -0.1546 |
| MIX_EXPERT10 | 1 | 38.0000 | 0.5259 | 0.3656 | 0.0642 | 0.1892 |
| MIX_EXPERT10 | 2 | 37.0000 | 0.5566 | 0.3971 | 0.0334 | 0.0498 |
| MIX_EXPERT10 | 3 | 35.0000 | 0.9227 | 0.8352 | -4.9935 | 0.7411 |
| MIX_EXPERT10 | 4 | 18.0000 | 0.7988 | 0.6875 | -0.6977 | 0.5746 |
| MIX_EXPERT10 | 5 | 10.0000 | 0.3630 | 0.3325 | -3.1220 | -0.3325 |
| MIX_EXPERT9 | 1 | 38.0000 | 0.5254 | 0.3653 | 0.0659 | 0.1884 |
| MIX_EXPERT9 | 2 | 37.0000 | 0.5547 | 0.3933 | 0.0400 | 0.0180 |
| MIX_EXPERT9 | 3 | 35.0000 | 0.9157 | 0.8290 | -4.9033 | 0.7302 |
| MIX_EXPERT9 | 4 | 18.0000 | 0.7988 | 0.6875 | -0.6980 | 0.5746 |
| MIX_EXPERT9 | 5 | 10.0000 | 0.3622 | 0.3317 | -3.1038 | -0.3317 |



En bloque 3, Local04D presenta RMSE 1.459 y sesgo +1.396; CT3 0.910/+0.718; J7 0.916/+0.731. El bloque 4 también es difícil: Local04D 1.313, CT3 0.799 y J7 0.799. No todo el problema espacial se limita al bloque 3. Local04D sí gana en bloque 5 (0.214 frente a 0.360 de CT3): su debilidad es la inestabilidad entre territorios, no una derrota en absolutamente todos.

## Rendimientos bajos, medios y altos


| experiment | protocol | ymin | ymax | n | rmse | mae | r2 | bias |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CT3 | climate_profile | 2.0000 | 3.2000 | 36.0000 | 0.7436 | 0.5682 | -5.1994 | 0.4654 |
| CT3 | climate_profile | 3.3000 | 4.3000 | 33.0000 | 0.4474 | 0.3421 | -1.2178 | 0.0443 |
| CT3 | climate_profile | 4.3800 | 4.5500 | 35.0000 | 0.2453 | 0.2065 | -21.0227 | -0.0780 |
| CT3 | climate_profile | 4.5600 | 5.5900 | 34.0000 | 0.5083 | 0.4428 | -1.5782 | -0.4369 |
| CT3 | municipality | 2.0000 | 3.2000 | 36.0000 | 0.8098 | 0.6486 | -6.3528 | 0.5997 |
| CT3 | municipality | 3.3000 | 4.3000 | 33.0000 | 0.4487 | 0.3551 | -1.2311 | 0.0641 |
| CT3 | municipality | 4.3800 | 4.5500 | 35.0000 | 0.2983 | 0.2651 | -31.5460 | -0.2094 |
| CT3 | municipality | 4.5600 | 5.5900 | 34.0000 | 0.6245 | 0.5641 | -2.8909 | -0.5641 |
| CT3 | random | 2.0000 | 3.2000 | 36.0000 | 0.7212 | 0.5188 | -4.8329 | 0.4275 |
| CT3 | random | 3.3000 | 4.3000 | 33.0000 | 0.4851 | 0.3879 | -1.6094 | 0.0103 |
| CT3 | random | 4.3800 | 4.5500 | 35.0000 | 0.2151 | 0.1752 | -15.9501 | -0.0503 |
| CT3 | random | 4.5600 | 5.5900 | 34.0000 | 0.4850 | 0.4157 | -1.3479 | -0.4087 |
| CT3 | spatial | 2.0000 | 3.2000 | 36.0000 | 1.1084 | 1.0172 | -12.7742 | 1.0129 |
| CT3 | spatial | 3.3000 | 4.3000 | 33.0000 | 0.4915 | 0.4218 | -1.6769 | 0.3020 |
| CT3 | spatial | 4.3800 | 4.5500 | 35.0000 | 0.2298 | 0.1951 | -18.3205 | -0.1197 |
| CT3 | spatial | 4.5600 | 5.5900 | 34.0000 | 0.5296 | 0.4665 | -1.7983 | -0.4665 |
| J7_BOTH | climate_profile | 2.0000 | 3.2000 | 36.0000 | 0.6697 | 0.4438 | -4.0286 | 0.3729 |
| J7_BOTH | climate_profile | 3.3000 | 4.3000 | 33.0000 | 0.4779 | 0.4071 | -1.5307 | -0.0011 |
| J7_BOTH | climate_profile | 4.3800 | 4.5500 | 35.0000 | 0.1301 | 0.1059 | -5.1968 | -0.0253 |
| J7_BOTH | climate_profile | 4.5600 | 5.5900 | 34.0000 | 0.5067 | 0.4241 | -1.5613 | -0.4241 |
| J7_BOTH | municipality | 2.0000 | 3.2000 | 36.0000 | 0.8089 | 0.6404 | -6.3360 | 0.6004 |
| J7_BOTH | municipality | 3.3000 | 4.3000 | 33.0000 | 0.4516 | 0.3682 | -1.2603 | 0.0509 |
| J7_BOTH | municipality | 4.3800 | 4.5500 | 35.0000 | 0.3005 | 0.2673 | -32.0326 | -0.2044 |
| J7_BOTH | municipality | 4.5600 | 5.5900 | 34.0000 | 0.6210 | 0.5580 | -2.8482 | -0.5580 |
| J7_BOTH | random | 2.0000 | 3.2000 | 36.0000 | 0.6648 | 0.4110 | -3.9580 | 0.3710 |
| J7_BOTH | random | 3.3000 | 4.3000 | 33.0000 | 0.4723 | 0.4050 | -1.4735 | -0.0132 |
| J7_BOTH | random | 4.3800 | 4.5500 | 35.0000 | 0.2006 | 0.1598 | -13.7554 | -0.0177 |
| J7_BOTH | random | 4.5600 | 5.5900 | 34.0000 | 0.4837 | 0.4158 | -1.3367 | -0.4108 |
| J7_BOTH | spatial | 2.0000 | 3.2000 | 36.0000 | 1.1198 | 1.0269 | -13.0601 | 1.0247 |
| J7_BOTH | spatial | 3.3000 | 4.3000 | 33.0000 | 0.5535 | 0.5023 | -2.3955 | 0.3884 |
| J7_BOTH | spatial | 4.3800 | 4.5500 | 35.0000 | 0.2508 | 0.2118 | -22.0141 | 0.0394 |
| J7_BOTH | spatial | 4.5600 | 5.5900 | 34.0000 | 0.4374 | 0.3546 | -0.9090 | -0.3201 |
| LOCAL04D | climate_profile | 2.0000 | 3.2000 | 36.0000 | 0.6841 | 0.4607 | -4.2476 | 0.4435 |
| LOCAL04D | climate_profile | 3.3000 | 4.3000 | 33.0000 | 0.4602 | 0.3960 | -1.3466 | 0.0304 |
| LOCAL04D | climate_profile | 4.3800 | 4.5500 | 35.0000 | 0.1198 | 0.0933 | -4.2467 | -0.0111 |
| LOCAL04D | climate_profile | 4.5600 | 5.5900 | 34.0000 | 0.5579 | 0.4439 | -2.1059 | -0.4439 |
| LOCAL04D | municipality | 2.0000 | 3.2000 | 36.0000 | 1.1501 | 1.0250 | -13.8317 | 1.0221 |
| LOCAL04D | municipality | 3.3000 | 4.3000 | 33.0000 | 0.5512 | 0.4171 | -2.3675 | 0.2740 |
| LOCAL04D | municipality | 4.3800 | 4.5500 | 35.0000 | 0.3001 | 0.2764 | -31.9428 | -0.2571 |
| LOCAL04D | municipality | 4.5600 | 5.5900 | 34.0000 | 0.7467 | 0.6569 | -4.5636 | -0.6569 |
| LOCAL04D | random | 2.0000 | 3.2000 | 36.0000 | 0.6578 | 0.4075 | -3.8589 | 0.3752 |
| LOCAL04D | random | 3.3000 | 4.3000 | 33.0000 | 0.4609 | 0.4034 | -1.3568 | 0.0155 |
| LOCAL04D | random | 4.3800 | 4.5500 | 35.0000 | 0.2050 | 0.1631 | -14.3971 | -0.0145 |
| LOCAL04D | random | 4.5600 | 5.5900 | 34.0000 | 0.5274 | 0.4403 | -1.7771 | -0.4340 |
| LOCAL04D | spatial | 2.0000 | 3.2000 | 36.0000 | 1.6697 | 1.6395 | -30.2595 | 1.6395 |
| LOCAL04D | spatial | 3.3000 | 4.3000 | 33.0000 | 0.7736 | 0.7110 | -5.6326 | 0.7110 |
| LOCAL04D | spatial | 4.3800 | 4.5500 | 35.0000 | 0.1442 | 0.1259 | -6.6066 | -0.0543 |
| LOCAL04D | spatial | 4.5600 | 5.5900 | 34.0000 | 0.5822 | 0.4615 | -2.3824 | -0.4594 |
| MIX_EXPERT10 | climate_profile | 2.0000 | 3.2000 | 36.0000 | 0.6696 | 0.4434 | -4.0277 | 0.3743 |
| MIX_EXPERT10 | climate_profile | 3.3000 | 4.3000 | 33.0000 | 0.4792 | 0.4100 | -1.5445 | 0.0042 |
| MIX_EXPERT10 | climate_profile | 4.3800 | 4.5500 | 35.0000 | 0.1295 | 0.1034 | -5.1387 | -0.0184 |
| MIX_EXPERT10 | climate_profile | 4.5600 | 5.5900 | 34.0000 | 0.4980 | 0.4182 | -1.4741 | -0.4182 |
| MIX_EXPERT10 | municipality | 2.0000 | 3.2000 | 36.0000 | 0.8082 | 0.6418 | -6.3236 | 0.5999 |
| MIX_EXPERT10 | municipality | 3.3000 | 4.3000 | 33.0000 | 0.4531 | 0.3686 | -1.2748 | 0.0505 |
| MIX_EXPERT10 | municipality | 4.3800 | 4.5500 | 35.0000 | 0.3005 | 0.2674 | -32.0384 | -0.2046 |
| MIX_EXPERT10 | municipality | 4.5600 | 5.5900 | 34.0000 | 0.6218 | 0.5590 | -2.8571 | -0.5590 |
| MIX_EXPERT10 | random | 2.0000 | 3.2000 | 36.0000 | 0.6635 | 0.4106 | -3.9381 | 0.3715 |
| MIX_EXPERT10 | random | 3.3000 | 4.3000 | 33.0000 | 0.4745 | 0.4066 | -1.4968 | -0.0119 |
| MIX_EXPERT10 | random | 4.3800 | 4.5500 | 35.0000 | 0.2018 | 0.1613 | -13.9213 | -0.0170 |
| MIX_EXPERT10 | random | 4.5600 | 5.5900 | 34.0000 | 0.4856 | 0.4180 | -1.3554 | -0.4116 |
| MIX_EXPERT10 | spatial | 2.0000 | 3.2000 | 36.0000 | 1.1253 | 1.0329 | -13.1983 | 1.0316 |
| MIX_EXPERT10 | spatial | 3.3000 | 4.3000 | 33.0000 | 0.5635 | 0.5114 | -2.5185 | 0.4007 |
| MIX_EXPERT10 | spatial | 4.3800 | 4.5500 | 35.0000 | 0.2606 | 0.2210 | -23.8543 | 0.0551 |
| MIX_EXPERT10 | spatial | 4.5600 | 5.5900 | 34.0000 | 0.4245 | 0.3448 | -0.7979 | -0.3029 |
| MIX_EXPERT9 | climate_profile | 2.0000 | 3.2000 | 36.0000 | 0.6719 | 0.4473 | -4.0622 | 0.3794 |
| MIX_EXPERT9 | climate_profile | 3.3000 | 4.3000 | 33.0000 | 0.4784 | 0.4085 | -1.5366 | 0.0004 |
| MIX_EXPERT9 | climate_profile | 4.3800 | 4.5500 | 35.0000 | 0.1310 | 0.1050 | -5.2802 | -0.0216 |
| MIX_EXPERT9 | climate_profile | 4.5600 | 5.5900 | 34.0000 | 0.5054 | 0.4227 | -1.5490 | -0.4227 |
| MIX_EXPERT9 | municipality | 2.0000 | 3.2000 | 36.0000 | 0.8084 | 0.6396 | -6.3279 | 0.5997 |
| MIX_EXPERT9 | municipality | 3.3000 | 4.3000 | 33.0000 | 0.4518 | 0.3687 | -1.2624 | 0.0504 |
| MIX_EXPERT9 | municipality | 4.3800 | 4.5500 | 35.0000 | 0.3003 | 0.2670 | -31.9952 | -0.2046 |
| MIX_EXPERT9 | municipality | 4.5600 | 5.5900 | 34.0000 | 0.6211 | 0.5580 | -2.8484 | -0.5580 |
| MIX_EXPERT9 | random | 2.0000 | 3.2000 | 36.0000 | 0.6681 | 0.4154 | -4.0066 | 0.3761 |
| MIX_EXPERT9 | random | 3.3000 | 4.3000 | 33.0000 | 0.4722 | 0.4047 | -1.4732 | -0.0124 |
| MIX_EXPERT9 | random | 4.3800 | 4.5500 | 35.0000 | 0.2000 | 0.1589 | -13.6654 | -0.0186 |
| MIX_EXPERT9 | random | 4.5600 | 5.5900 | 34.0000 | 0.4833 | 0.4157 | -1.3325 | -0.4110 |
| MIX_EXPERT9 | spatial | 2.0000 | 3.2000 | 36.0000 | 1.1193 | 1.0265 | -13.0464 | 1.0240 |
| MIX_EXPERT9 | spatial | 3.3000 | 4.3000 | 33.0000 | 0.5555 | 0.5041 | -2.4194 | 0.3896 |
| MIX_EXPERT9 | spatial | 4.3800 | 4.5500 | 35.0000 | 0.2548 | 0.2139 | -22.7542 | 0.0430 |
| MIX_EXPERT9 | spatial | 4.5600 | 5.5900 | 34.0000 | 0.4361 | 0.3549 | -0.8971 | -0.3181 |



En el cuartil bajo (2–3.2 t/ha), todos tienden a sobreestimar. En aleatoria Local04D tiene RMSE 0.658, J7 0.665 y CT3 0.721. En espacial Local04D se deteriora a 1.670 con sesgo +1.640; CT3 queda en 1.108 y J7 en 1.120. En el cuartil alto (4.56–5.59), todos subestiman: J7 mejora espacialmente respecto a CT3 (0.437 frente a 0.530), pero ese beneficio se compensa con otros errores. Los cuartiles dependen del target observado: sirven para diagnóstico, nunca para decidir qué modelo usar en una parcela sin rendimiento conocido.

## Diferencias entre parcelas del mismo perfil

Se comparan errores al predecir diferencias de rendimiento entre pares del mismo perfil, separando igual peso a cada perfil y peso por número de pares. Estas métricas no son el RMSE convencional por parcela.


| experiment | protocol | n_pairs | n_profiles | n_parcels | equal_profile_RMSE | pair_weighted_RMSE | equal_profile_MAE | pair_weighted_MAE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BIG_BOTH | climate_profile | 1073.0000 | 12.0000 | 107.0000 | 0.5375 | 0.7905 | 0.3878 | 0.5534 |
| BIG_BOTH | municipality | 1034.0000 | 12.0000 | 103.0000 | 0.5235 | 0.7701 | 0.3563 | 0.5361 |
| BIG_BOTH | random | 208.4000 | 8.6000 | 87.7000 | 0.5703 | 0.7765 | 0.4013 | 0.5460 |
| BIG_BOTH | spatial | 1007.0000 | 12.0000 | 106.0000 | 0.5364 | 0.7697 | 0.3826 | 0.5634 |
| CT3 | climate_profile | 1073.0000 | 12.0000 | 107.0000 | 0.5479 | 0.7634 | 0.4020 | 0.5284 |
| CT3 | municipality | 1034.0000 | 12.0000 | 103.0000 | 0.5210 | 0.7688 | 0.3522 | 0.5349 |
| CT3 | random | 208.4000 | 8.6000 | 87.7000 | 0.5900 | 0.7712 | 0.4357 | 0.5332 |
| CT3 | spatial | 1007.0000 | 12.0000 | 106.0000 | 0.5401 | 0.7675 | 0.3838 | 0.5337 |
| EXPERT10 | climate_profile | 1073.0000 | 12.0000 | 107.0000 | 0.5291 | 0.7737 | 0.3641 | 0.5426 |
| EXPERT10 | municipality | 1034.0000 | 12.0000 | 103.0000 | 0.5300 | 0.7811 | 0.3483 | 0.5405 |
| EXPERT10 | random | 208.4000 | 8.6000 | 87.7000 | 0.5800 | 0.7909 | 0.3992 | 0.5653 |
| EXPERT10 | spatial | 1007.0000 | 12.0000 | 106.0000 | 0.5321 | 0.7784 | 0.3709 | 0.5465 |
| EXPERT7 | climate_profile | 1073.0000 | 12.0000 | 107.0000 | 0.5286 | 0.7729 | 0.3630 | 0.5386 |
| EXPERT7 | municipality | 1034.0000 | 12.0000 | 103.0000 | 0.5303 | 0.7813 | 0.3484 | 0.5406 |
| EXPERT7 | random | 208.4000 | 8.6000 | 87.7000 | 0.5792 | 0.7910 | 0.3986 | 0.5640 |
| EXPERT7 | spatial | 1007.0000 | 12.0000 | 106.0000 | 0.5326 | 0.7783 | 0.3703 | 0.5425 |
| EXPERT9 | climate_profile | 1073.0000 | 12.0000 | 107.0000 | 0.5307 | 0.7747 | 0.3643 | 0.5414 |
| EXPERT9 | municipality | 1034.0000 | 12.0000 | 103.0000 | 0.5305 | 0.7813 | 0.3483 | 0.5401 |
| EXPERT9 | random | 208.4000 | 8.6000 | 87.7000 | 0.5813 | 0.7926 | 0.4011 | 0.5656 |
| EXPERT9 | spatial | 1007.0000 | 12.0000 | 106.0000 | 0.5332 | 0.7800 | 0.3707 | 0.5452 |
| J7_BOTH | climate_profile | 1073.0000 | 12.0000 | 107.0000 | 0.5317 | 0.7750 | 0.3779 | 0.5361 |
| J7_BOTH | municipality | 1034.0000 | 12.0000 | 103.0000 | 0.5257 | 0.7706 | 0.3590 | 0.5367 |
| J7_BOTH | random | 208.4000 | 8.6000 | 87.7000 | 0.5777 | 0.7774 | 0.4045 | 0.5434 |
| J7_BOTH | spatial | 1007.0000 | 12.0000 | 106.0000 | 0.5320 | 0.7596 | 0.3808 | 0.5576 |
| LOCAL04D | climate_profile | 1073.0000 | 12.0000 | 107.0000 | 0.5347 | 0.8032 | 0.3680 | 0.5643 |
| LOCAL04D | municipality | 1034.0000 | 12.0000 | 103.0000 | 0.5336 | 0.8128 | 0.3411 | 0.5620 |
| LOCAL04D | random | 208.4000 | 8.6000 | 87.7000 | 0.5747 | 0.8006 | 0.3917 | 0.5752 |
| LOCAL04D | spatial | 1007.0000 | 12.0000 | 106.0000 | 0.5361 | 0.8080 | 0.3598 | 0.5644 |
| MIX_EXPERT10 | climate_profile | 1073.0000 | 12.0000 | 107.0000 | 0.5310 | 0.7755 | 0.3778 | 0.5390 |
| MIX_EXPERT10 | municipality | 1034.0000 | 12.0000 | 103.0000 | 0.5236 | 0.7703 | 0.3567 | 0.5362 |
| MIX_EXPERT10 | random | 208.4000 | 8.6000 | 87.7000 | 0.5776 | 0.7767 | 0.4042 | 0.5442 |
| MIX_EXPERT10 | spatial | 1007.0000 | 12.0000 | 106.0000 | 0.5320 | 0.7610 | 0.3814 | 0.5627 |
| MIX_EXPERT9 | climate_profile | 1073.0000 | 12.0000 | 107.0000 | 0.5323 | 0.7764 | 0.3789 | 0.5388 |
| MIX_EXPERT9 | municipality | 1034.0000 | 12.0000 | 103.0000 | 0.5258 | 0.7706 | 0.3591 | 0.5367 |
| MIX_EXPERT9 | random | 208.4000 | 8.6000 | 87.7000 | 0.5790 | 0.7779 | 0.4066 | 0.5439 |
| MIX_EXPERT9 | spatial | 1007.0000 | 12.0000 | 106.0000 | 0.5324 | 0.7609 | 0.3814 | 0.5600 |



En aleatoria, con igual peso por perfil, Local04D obtiene 0.575, J7 0.578 y CT3 0.590; ponderando por pares, Local04D obtiene 0.801, J7 0.777 y CT3 0.771. La conclusión cambia con la ponderación: no hay una superioridad intraperfil universal. Los perfiles grandes requieren atención propia.

## Concentración, dependencia espacial y estabilidad al omitir zonas

Las cinco parcelas de mayor error concentran aproximadamente el 39.3% del SSE aleatorio de Local04D, 37.5% de CT3 y 40.8% de J7. No se eliminaron casos. Una fracción alta muestra influencia de la cola; una fracción menor tampoco implica robustez si muchos errores son grandes, como ocurre con Local04D espacial.

El Moran descriptivo espacial de residuos es 0.676 para Local04D, 0.441 para CT3 y 0.389 para J7. Tras centrar residuos por estado queda en 0.323, 0.245 y 0.254. Parte de la estructura de error es regional, pero queda dependencia local. No se presentan estos índices como pruebas de significancia ni como evidencia causal.

Las tablas omissions_* recalculan métricas quitando una zona completa, conservando todas las predicciones originales: no se reajusta ningún modelo. Permiten comprobar si la conclusión depende de un bloque, estado o municipio. El bloque 4 confirma que el deterioro de Local04D no procede exclusivamente del bloque 3.

## ¿Se complementan los residuos?


| experiment | reference | protocol | error_correlation | fraction_lower_absolute_error | fraction_tie |
| --- | --- | --- | --- | --- | --- |
| CT3 | J7_BOTH | climate_profile | 0.9126 | 0.3913 | 0.0000 |
| CT3 | J7_BOTH | municipality | 0.9970 | 0.1304 | 0.6377 |
| CT3 | J7_BOTH | random | 0.9438 | 0.3964 | 0.0094 |
| CT3 | J7_BOTH | spatial | 0.9743 | 0.4130 | 0.2609 |
| CT3 | MIX_EXPERT10 | climate_profile | 0.9145 | 0.3841 | 0.0000 |
| CT3 | MIX_EXPERT10 | municipality | 0.9978 | 0.1377 | 0.6377 |
| CT3 | MIX_EXPERT10 | random | 0.9441 | 0.3993 | 0.0130 |
| CT3 | MIX_EXPERT10 | spatial | 0.9712 | 0.4493 | 0.2609 |
| CT3 | MIX_EXPERT9 | climate_profile | 0.9122 | 0.3841 | 0.0000 |
| CT3 | MIX_EXPERT9 | municipality | 0.9969 | 0.1304 | 0.6377 |
| CT3 | MIX_EXPERT9 | random | 0.9457 | 0.3993 | 0.0145 |
| CT3 | MIX_EXPERT9 | spatial | 0.9734 | 0.4203 | 0.2609 |
| J7_BOTH | MIX_EXPERT10 | climate_profile | 0.9993 | 0.5217 | 0.0000 |
| J7_BOTH | MIX_EXPERT10 | municipality | 0.9999 | 0.2536 | 0.6377 |
| J7_BOTH | MIX_EXPERT10 | random | 0.9996 | 0.5413 | 0.0101 |
| J7_BOTH | MIX_EXPERT10 | spatial | 0.9990 | 0.5072 | 0.2609 |
| J7_BOTH | MIX_EXPERT9 | climate_profile | 0.9997 | 0.5217 | 0.0000 |
| J7_BOTH | MIX_EXPERT9 | municipality | 1.0000 | 0.1739 | 0.6377 |
| J7_BOTH | MIX_EXPERT9 | random | 0.9997 | 0.5341 | 0.0109 |
| J7_BOTH | MIX_EXPERT9 | spatial | 0.9999 | 0.3478 | 0.2609 |
| LOCAL04D | CT3 | climate_profile | 0.8260 | 0.5870 | 0.0000 |
| LOCAL04D | CT3 | municipality | 0.8600 | 0.3623 | 0.0000 |
| LOCAL04D | CT3 | random | 0.8845 | 0.5783 | 0.0000 |
| LOCAL04D | CT3 | spatial | 0.8810 | 0.3406 | 0.0000 |
| LOCAL04D | J7_BOTH | climate_profile | 0.9694 | 0.5000 | 0.0000 |
| LOCAL04D | J7_BOTH | municipality | 0.8718 | 0.3623 | 0.0000 |
| LOCAL04D | J7_BOTH | random | 0.9725 | 0.5051 | 0.0000 |
| LOCAL04D | J7_BOTH | spatial | 0.8502 | 0.3333 | 0.0000 |
| LOCAL04D | MIX_EXPERT10 | climate_profile | 0.9681 | 0.5072 | 0.0000 |
| LOCAL04D | MIX_EXPERT10 | municipality | 0.8701 | 0.3551 | 0.0000 |
| LOCAL04D | MIX_EXPERT10 | random | 0.9723 | 0.5130 | 0.0000 |
| LOCAL04D | MIX_EXPERT10 | spatial | 0.8449 | 0.3478 | 0.0000 |
| LOCAL04D | MIX_EXPERT9 | climate_profile | 0.9698 | 0.5145 | 0.0000 |
| LOCAL04D | MIX_EXPERT9 | municipality | 0.8720 | 0.3623 | 0.0000 |
| LOCAL04D | MIX_EXPERT9 | random | 0.9712 | 0.5080 | 0.0000 |
| LOCAL04D | MIX_EXPERT9 | spatial | 0.8485 | 0.3333 | 0.0000 |
| MIX_EXPERT10 | MIX_EXPERT9 | climate_profile | 0.9993 | 0.4928 | 0.0072 |
| MIX_EXPERT10 | MIX_EXPERT9 | municipality | 0.9999 | 0.1014 | 0.6377 |
| MIX_EXPERT10 | MIX_EXPERT9 | random | 0.9993 | 0.4841 | 0.0109 |
| MIX_EXPERT10 | MIX_EXPERT9 | spatial | 0.9992 | 0.2754 | 0.2609 |



J7 y las mezclas de expertos 9/10 tienen correlaciones de errores cercanas a 0.999–1: son pequeñas sensibilidades de una misma solución, no expertos de errores muy distintos. Local04D y J7 tienen correlación aproximada de 0.973 en aleatoria y 0.850 espacial. Esa menor correlación espacial no garantiza una mezcla útil: Local04D añade mucho sesgo y error propio. Se entregan ganancias pareadas por parcela; no se entrenó una nueva mezcla usando estos resultados.

Las ramas EXPERT7/9/10 aisladas tienen RMSE municipal de aproximadamente 0.656 y espacial de 0.809/0.814/0.834. Las mezclas completas bajan a aproximadamente 0.581 y 0.681. La protección territorial proviene en parte importante de conservar CT3 y controlar el peso del experto.

## Incertidumbre de las comparaciones


| experiment | reference | protocol | delta_rmse | low95 | high95 | p_mse_signflip | n_clusters | exact_sign_enumeration | n_sign_assignments | p_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LOCAL04D | CT3 | climate_profile | -0.0176 | -0.1149 | 0.0225 | 0.4995 | 43 | False | 20000 | 1.0000 |
| LOCAL04D | J7_BOTH | climate_profile | 0.0140 | -0.0234 | 0.0304 | 0.3719 | 43 | False | 20000 | 1.0000 |
| LOCAL04D | MIX_EXPERT10 | climate_profile | 0.0160 | -0.0223 | 0.0329 | 0.3560 | 43 | False | 20000 | 1.0000 |
| LOCAL04D | MIX_EXPERT9 | climate_profile | 0.0133 | -0.0241 | 0.0299 | 0.3963 | 43 | False | 20000 | 1.0000 |
| CT3 | J7_BOTH | climate_profile | 0.0316 | 0.0016 | 0.0986 | 0.0569 | 43 | False | 20000 | 1.0000 |
| CT3 | MIX_EXPERT10 | climate_profile | 0.0335 | 0.0039 | 0.0992 | 0.0348 | 43 | False | 20000 | 1.0000 |
| CT3 | MIX_EXPERT9 | climate_profile | 0.0309 | 0.0011 | 0.0977 | 0.0625 | 43 | False | 20000 | 1.0000 |
| J7_BOTH | MIX_EXPERT10 | climate_profile | 0.0020 | -0.0003 | 0.0038 | 0.1415 | 43 | False | 20000 | 1.0000 |
| J7_BOTH | MIX_EXPERT9 | climate_profile | -0.0007 | -0.0023 | 0.0005 | 0.2894 | 43 | False | 20000 | 1.0000 |
| MIX_EXPERT10 | MIX_EXPERT9 | climate_profile | -0.0026 | -0.0043 | -0.0003 | 0.0617 | 43 | False | 20000 | 1.0000 |
| LOCAL04D | CT3 | municipality | 0.1790 | 0.0299 | 0.4033 | 0.1680 | 9 | True | 512 | 1.0000 |
| LOCAL04D | J7_BOTH | municipality | 0.1794 | 0.0307 | 0.3859 | 0.1758 | 9 | True | 512 | 1.0000 |
| LOCAL04D | MIX_EXPERT10 | municipality | 0.1792 | 0.0303 | 0.3885 | 0.1797 | 9 | True | 512 | 1.0000 |
| LOCAL04D | MIX_EXPERT9 | municipality | 0.1795 | 0.0308 | 0.3860 | 0.1797 | 9 | True | 512 | 1.0000 |
| CT3 | J7_BOTH | municipality | 0.0004 | -0.0170 | 0.0159 | 0.9141 | 9 | True | 512 | 1.0000 |
| CT3 | MIX_EXPERT10 | municipality | 0.0002 | -0.0141 | 0.0120 | 0.9688 | 9 | True | 512 | 1.0000 |
| CT3 | MIX_EXPERT9 | municipality | 0.0006 | -0.0170 | 0.0166 | 0.8828 | 9 | True | 512 | 1.0000 |
| J7_BOTH | MIX_EXPERT10 | municipality | -0.0002 | -0.0045 | 0.0035 | 0.6250 | 9 | True | 512 | 1.0000 |
| J7_BOTH | MIX_EXPERT9 | municipality | 0.0001 | -0.0001 | 0.0007 | 0.4766 | 9 | True | 512 | 1.0000 |
| MIX_EXPERT10 | MIX_EXPERT9 | municipality | 0.0004 | -0.0035 | 0.0051 | 0.5391 | 9 | True | 512 | 1.0000 |
| LOCAL04D | CT3 | random | -0.0186 | -0.0993 | 0.0121 | 0.3220 | 43 | False | 20000 | 1.0000 |
| LOCAL04D | J7_BOTH | random | 0.0065 | -0.0221 | 0.0184 | 0.6031 | 43 | False | 20000 | 1.0000 |
| LOCAL04D | MIX_EXPERT10 | random | 0.0059 | -0.0234 | 0.0177 | 0.6143 | 43 | False | 20000 | 1.0000 |
| LOCAL04D | MIX_EXPERT9 | random | 0.0056 | -0.0245 | 0.0179 | 0.6640 | 43 | False | 20000 | 1.0000 |
| CT3 | J7_BOTH | random | 0.0252 | 0.0042 | 0.0780 | 0.0177 | 43 | False | 20000 | 0.7100 |
| CT3 | MIX_EXPERT10 | random | 0.0245 | 0.0039 | 0.0768 | 0.0190 | 43 | False | 20000 | 0.7429 |
| CT3 | MIX_EXPERT9 | random | 0.0242 | 0.0036 | 0.0758 | 0.0198 | 43 | False | 20000 | 0.7543 |
| J7_BOTH | MIX_EXPERT10 | random | -0.0006 | -0.0024 | 0.0005 | 0.3435 | 43 | False | 20000 | 1.0000 |
| J7_BOTH | MIX_EXPERT9 | random | -0.0010 | -0.0030 | -0.0001 | 0.0547 | 43 | False | 20000 | 1.0000 |
| MIX_EXPERT10 | MIX_EXPERT9 | random | -0.0004 | -0.0024 | 0.0015 | 0.7110 | 43 | False | 20000 | 1.0000 |
| LOCAL04D | CT3 | spatial | 0.3006 | 0.0336 | 0.5088 | 0.1250 | 5 | True | 32 | 1.0000 |
| LOCAL04D | J7_BOTH | spatial | 0.2986 | 0.0329 | 0.5046 | 0.1250 | 5 | True | 32 | 1.0000 |
| LOCAL04D | MIX_EXPERT10 | spatial | 0.2954 | 0.0312 | 0.5002 | 0.1250 | 5 | True | 32 | 1.0000 |
| LOCAL04D | MIX_EXPERT9 | spatial | 0.2983 | 0.0321 | 0.5048 | 0.1250 | 5 | True | 32 | 1.0000 |
| CT3 | J7_BOTH | spatial | -0.0020 | -0.0136 | 0.0119 | 0.8750 | 5 | True | 32 | 1.0000 |
| CT3 | MIX_EXPERT10 | spatial | -0.0053 | -0.0154 | 0.0100 | 0.3750 | 5 | True | 32 | 1.0000 |
| CT3 | MIX_EXPERT9 | spatial | -0.0023 | -0.0140 | 0.0113 | 0.6250 | 5 | True | 32 | 1.0000 |
| J7_BOTH | MIX_EXPERT10 | spatial | -0.0032 | -0.0056 | -0.0005 | 0.1250 | 5 | True | 32 | 1.0000 |
| J7_BOTH | MIX_EXPERT9 | spatial | -0.0003 | -0.0009 | 0.0002 | 0.3750 | 5 | True | 32 | 1.0000 |
| MIX_EXPERT10 | MIX_EXPERT9 | spatial | 0.0029 | 0.0002 | 0.0058 | 0.1250 | 5 | True | 32 | 1.0000 |



Se realizaron 40 comparaciones pareadas principales, con bootstrap agrupado y prueba de cambio de signo de diferencias de pérdida por grupo; ajuste Holm entre las 40. Ninguna conserva p<0.05 tras Holm. Hay pocos grupos territoriales y la potencia es limitada: con cinco bloques una prueba bilateral exacta de signos tiene resolución mínima de 0.0625. Los intervalos bootstrap y esta prueba responden a supuestos distintos; un intervalo que excluye cero no autoriza ignorar la prueba y su multiplicidad. Tampoco la falta de significancia demuestra equivalencia. La reutilización histórica de esta validación obliga a tratar las decisiones nuevas como exploratorias.

## Parcelas 171 y 015 en el contexto completo

Ambas son outliers de rendimiento en Chignahuapan y en su perfil, no outliers globales por Tukey. Ninguna presenta un outlier continuo evaluable en las 28 entradas de J7; sus categorías de suelo son comunes. Todos los modelos las sobreestiman cerca de 2 t/ha en aleatoria. No son un problema exclusivo de una arquitectura.

Fuera de esas entradas, 171 destaca por bajo cambio neto de EVI Planet (0.014 frente a mediana municipal 0.177); 015 por TPI 3×3 bajo (−3.637 frente a −0.065) y una tasa derivada de crecimiento NDVI alta (0.108 frente a 0.039). Son pistas distintas, no una causa compartida demostrada. TPI bajo no demuestra humedal ni inundación. Fechas y tasas derivadas no equivalen a fechas observadas de siembra/cosecha.

El censo cubre 1,867 variables propias, 1,831 predictores no climáticos auditados de GeoC y las entradas de J7; no equivale a auditar cada uno de los 2,082 descriptores originales de Local04D. Los outliers se describen en TRAIN138, estado, municipio y perfil, incluyendo el caso focal. Se usa Tukey y se muestra sensibilidad MAD; en variables climáticas repetidas, MAD muy pequeño puede producir z enormes sin percentiles extremos. No se cuentan columnas correlacionadas como pruebas independientes ni se atribuye causalidad a las banderas.

## Fortalezas, debilidades y recomendación

- **CT3:** referencia de cuatro entradas, mejor equilibrio espacial y resultados municipales casi idénticos a las mezclas. Pierde algo de precisión aleatoria/por perfil y no distingue todos los rendimientos dentro del mismo clima.
- **Local04D:** fortaleza de interpolación geográfica, especialmente Hidalgo, y algunos bloques. Debilidad de transferencia: errores regionales amplios y sesgo positivo fuerte al excluir territorios. Su complejidad y representación transductiva requieren documentar el escenario de uso.
- **J7_BOTH:** mejora pequeña pero consistente en magnitud aleatoria y por perfil; reduce cola de error y conserva el nivel territorial de CT3. No mejora realmente el RMSE espacial y aumenta su sesgo positivo. Es una alternativa de precisión/interpolación, no un ganador universal.
- **Mezcla experto10:** mínima ventaja por perfil (0.487 frente a 0.489 de J7), con mayor sesgo y RMSE espacial. No justifica por sí sola aumentar complejidad.
- **Mezcla experto9:** prácticamente reproduce J7 y logra una diferencia municipal de solo 0.00014 t/ha. No demuestra una ventaja material.

Conservar CT3 como benchmark territorial y J7 como mezcla compacta de referencia. No añadir 9/10 o una calibración global por diferencias milimétricas. La oportunidad es explicar fallos compartidos mediante información adicional respaldada por más casos y validación interna, no crear una regla para dos parcelas. Las trayectorias estacionales y posición topográfica son hipótesis para una fase futura acotada, no variables ya demostradas como correctores generales. No se promovió un champion ni se generaron predicciones PRED.

## Entregables

Libro `outputs/research/case_outliers_and_model_residual_comparison/v1/comparacion_residuos_y_outliers.xlsx`: métricas completas, regiones, bloques, cuartiles, intraperfil, omisiones, concentración, comparaciones y residuos por cada parcela. CSV y Parquet conservan los datos numéricos de origen. Figuras: `model_calibration_comparison.png` y `bias_and_threshold_comparison.png`. Scripts reproducibles: 451 (outliers), 452 (residuos), 453 (empaquetado y verificación).
