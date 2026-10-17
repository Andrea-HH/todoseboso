# Contrastes continuos: resultados y comparación conjunta

Elastic Net solo sobre los seis contrastes, sin intercepto, con SD del entrenamiento y sin centrar. Cero diferencia implica cero ajuste. Corrección máxima ±0.5 t/ha. Misma base, vecinos y calibración que el experimento de árboles; referencias externas exactas.

## RMSE / R²

| modelo | random | climate_profile | municipality | spatial |
| --- | --- | --- | --- | --- |
| J7_BOTH | 0.4864 / 0.6709 | 0.4890 / 0.6675 | 0.5808 / 0.5309 | 0.6808 / 0.3556 |
| CT3 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| GEO_LINEAR | 0.4882 / 0.6686 | 0.4851 / 0.6728 | 0.5813 / 0.5302 | 0.7402 / 0.2383 |
| COMPACT_LINEAR | 0.4904 / 0.6656 | 0.4853 / 0.6725 | 0.5829 / 0.5277 | 0.7072 / 0.3047 |
| GEO_ATTENUATE | 0.4875 / 0.6694 | 0.4868 / 0.6706 | 0.5811 / 0.5305 | 0.6749 / 0.3667 |
| COMPACT_ATTENUATE | 0.4877 / 0.6692 | 0.4881 / 0.6687 | 0.5775 / 0.5362 | 0.6756 / 0.3655 |
| GEO_RESIDUAL | 0.4894 / 0.6669 | 0.4932 / 0.6618 | 0.5910 / 0.5144 | 0.7096 / 0.3000 |
| COMPACT_RESIDUAL | 0.4900 / 0.6660 | 0.4869 / 0.6703 | 0.5794 / 0.5332 | 0.7152 / 0.2888 |

## Métricas completas

| experiment | protocol | rmse | mae | r2 | bias | error_sd |
| --- | --- | --- | --- | --- | --- | --- |
| COMPACT_ATTENUATE | climate_profile | 0.4881 | 0.3445 | 0.6687 | -0.0106 | 0.4880 |
| COMPACT_ATTENUATE | municipality | 0.5775 | 0.4577 | 0.5362 | -0.0222 | 0.5771 |
| COMPACT_ATTENUATE | random | 0.4877 | 0.3477 | 0.6692 | -0.0122 | 0.4875 |
| COMPACT_ATTENUATE | spatial | 0.6756 | 0.5184 | 0.3655 | 0.2557 | 0.6253 |
| COMPACT_LINEAR | climate_profile | 0.4853 | 0.3459 | 0.6725 | -0.0178 | 0.4850 |
| COMPACT_LINEAR | municipality | 0.5829 | 0.4642 | 0.5277 | -0.0301 | 0.5821 |
| COMPACT_LINEAR | random | 0.4904 | 0.3498 | 0.6656 | -0.0140 | 0.4901 |
| COMPACT_LINEAR | spatial | 0.7072 | 0.5686 | 0.3047 | 0.2532 | 0.6603 |
| COMPACT_RESIDUAL | climate_profile | 0.4869 | 0.3416 | 0.6703 | -0.0075 | 0.4869 |
| COMPACT_RESIDUAL | municipality | 0.5794 | 0.4598 | 0.5332 | -0.0331 | 0.5785 |
| COMPACT_RESIDUAL | random | 0.4900 | 0.3496 | 0.6660 | -0.0087 | 0.4899 |
| COMPACT_RESIDUAL | spatial | 0.7152 | 0.5824 | 0.2888 | 0.1476 | 0.6998 |
| CT3 | climate_profile | 0.5206 | 0.3915 | 0.6232 | 0.0046 | 0.5206 |
| CT3 | municipality | 0.5813 | 0.4603 | 0.5302 | -0.0203 | 0.5809 |
| CT3 | random | 0.5116 | 0.3749 | 0.6361 | 0.0005 | 0.5115 |
| CT3 | spatial | 0.6788 | 0.5306 | 0.3594 | 0.1912 | 0.6513 |
| GEO_ATTENUATE | climate_profile | 0.4868 | 0.3420 | 0.6706 | -0.0064 | 0.4867 |
| GEO_ATTENUATE | municipality | 0.5811 | 0.4600 | 0.5305 | -0.0199 | 0.5808 |
| GEO_ATTENUATE | random | 0.4875 | 0.3473 | 0.6694 | -0.0118 | 0.4873 |
| GEO_ATTENUATE | spatial | 0.6749 | 0.5188 | 0.3667 | 0.2480 | 0.6277 |
| GEO_LINEAR | climate_profile | 0.4851 | 0.3433 | 0.6728 | -0.0162 | 0.4849 |
| GEO_LINEAR | municipality | 0.5813 | 0.4615 | 0.5302 | -0.0267 | 0.5807 |
| GEO_LINEAR | random | 0.4882 | 0.3482 | 0.6686 | -0.0131 | 0.4880 |
| GEO_LINEAR | spatial | 0.7402 | 0.5959 | 0.2383 | 0.2783 | 0.6858 |
| GEO_RESIDUAL | climate_profile | 0.4932 | 0.3519 | 0.6618 | -0.0100 | 0.4931 |
| GEO_RESIDUAL | municipality | 0.5910 | 0.4635 | 0.5144 | -0.0891 | 0.5842 |
| GEO_RESIDUAL | random | 0.4894 | 0.3489 | 0.6669 | -0.0090 | 0.4893 |
| GEO_RESIDUAL | spatial | 0.7096 | 0.5762 | 0.3000 | 0.1467 | 0.6942 |
| J7_BOTH | climate_profile | 0.4890 | 0.3445 | 0.6675 | -0.0139 | 0.4888 |
| J7_BOTH | municipality | 0.5808 | 0.4604 | 0.5309 | -0.0205 | 0.5805 |
| J7_BOTH | random | 0.4864 | 0.3470 | 0.6709 | -0.0121 | 0.4862 |
| J7_BOTH | spatial | 0.6808 | 0.5291 | 0.3556 | 0.2913 | 0.6153 |

## Comparaciones pareadas: ampliación exploratoria de 20 contrastes

| experiment | reference | contrast | protocol | delta_rmse | low95 | high95 | p_mse_signflip | n_clusters | exact_sign_enumeration | n_sign_assignments | p_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GEO_LINEAR | J7_BOTH | reference | climate_profile | -0.0039 | -0.0060 | 0.0014 | 0.2545 | 43 | False | 20000 | 1.0000 |
| COMPACT_LINEAR | J7_BOTH | reference | climate_profile | -0.0037 | -0.0099 | 0.0044 | 0.7377 | 43 | False | 20000 | 1.0000 |
| GEO_LINEAR | COMPACT_LINEAR | neighborhood | climate_profile | -0.0002 | -0.0063 | 0.0054 | 0.9504 | 43 | False | 20000 | 1.0000 |
| GEO_LINEAR | GEO_RESIDUAL | continuous_vs_tree | climate_profile | -0.0081 | -0.0125 | -0.0009 | 0.0705 | 43 | False | 20000 | 1.0000 |
| COMPACT_LINEAR | COMPACT_RESIDUAL | continuous_vs_tree | climate_profile | -0.0016 | -0.0050 | 0.0044 | 0.7377 | 43 | False | 20000 | 1.0000 |
| GEO_LINEAR | J7_BOTH | reference | municipality | 0.0005 | -0.0003 | 0.0042 | 0.7500 | 9 | True | 512 | 1.0000 |
| COMPACT_LINEAR | J7_BOTH | reference | municipality | 0.0020 | -0.0029 | 0.0170 | 0.5000 | 9 | True | 512 | 1.0000 |
| GEO_LINEAR | COMPACT_LINEAR | neighborhood | municipality | -0.0015 | -0.0133 | 0.0029 | 0.5000 | 9 | True | 512 | 1.0000 |
| GEO_LINEAR | GEO_RESIDUAL | continuous_vs_tree | municipality | -0.0097 | -0.0471 | -0.0025 | 0.0625 | 9 | True | 512 | 1.0000 |
| COMPACT_LINEAR | COMPACT_RESIDUAL | continuous_vs_tree | municipality | 0.0034 | -0.0018 | 0.0198 | 0.2500 | 9 | True | 512 | 1.0000 |
| GEO_LINEAR | J7_BOTH | reference | random | 0.0018 | -0.0000 | 0.0026 | 0.1380 | 43 | False | 20000 | 1.0000 |
| COMPACT_LINEAR | J7_BOTH | reference | random | 0.0039 | 0.0016 | 0.0061 | 0.0001 | 43 | False | 20000 | 0.0030 |
| GEO_LINEAR | COMPACT_LINEAR | neighborhood | random | -0.0022 | -0.0042 | -0.0001 | 0.0428 | 43 | False | 20000 | 0.8132 |
| GEO_LINEAR | GEO_RESIDUAL | continuous_vs_tree | random | -0.0013 | -0.0034 | 0.0009 | 0.2938 | 43 | False | 20000 | 1.0000 |
| COMPACT_LINEAR | COMPACT_RESIDUAL | continuous_vs_tree | random | 0.0003 | -0.0053 | 0.0042 | 0.9418 | 43 | False | 20000 | 1.0000 |
| GEO_LINEAR | J7_BOTH | reference | spatial | 0.0594 | -0.0085 | 0.1517 | 0.3750 | 5 | True | 32 | 1.0000 |
| COMPACT_LINEAR | J7_BOTH | reference | spatial | 0.0264 | 0.0010 | 0.0585 | 0.2500 | 5 | True | 32 | 1.0000 |
| GEO_LINEAR | COMPACT_LINEAR | neighborhood | spatial | 0.0330 | -0.0159 | 0.1127 | 0.8750 | 5 | True | 32 | 1.0000 |
| GEO_LINEAR | GEO_RESIDUAL | continuous_vs_tree | spatial | 0.0306 | -0.0574 | 0.1318 | 0.7500 | 5 | True | 32 | 1.0000 |
| COMPACT_LINEAR | COMPACT_RESIDUAL | continuous_vs_tree | spatial | -0.0080 | -0.0633 | 0.0359 | 0.7500 | 5 | True | 32 | 1.0000 |

## Ganancias por parcela

| experiment | protocol | total_sse_gain | cases_sse_gain | remaining_sse_gain | fraction_improved | fraction_worsened |
| --- | --- | --- | --- | --- | --- | --- |
| COMPACT_LINEAR | climate_profile | 0.4968 | 0.7949 | -0.2981 | 0.3623 | 0.4565 |
| COMPACT_LINEAR | municipality | -0.3226 | 0.0000 | -0.3226 | 0.0290 | 0.0435 |
| COMPACT_LINEAR | random | -0.5344 | -0.0920 | -0.4424 | 0.3188 | 0.5145 |
| COMPACT_LINEAR | spatial | -5.0476 | 2.0451 | -7.0928 | 0.2681 | 0.4058 |
| GEO_LINEAR | climate_profile | 0.5231 | 0.6070 | -0.0839 | 0.4203 | 0.3986 |
| GEO_LINEAR | municipality | -0.0742 | 0.0000 | -0.0742 | 0.0217 | 0.0507 |
| GEO_LINEAR | random | -0.2325 | -0.0412 | -0.1913 | 0.3261 | 0.3768 |
| GEO_LINEAR | spatial | -11.6383 | -0.4216 | -11.2168 | 0.2826 | 0.4638 |

Las tablas incluyen regiones, omisiones, cuartiles, intraperfil y análisis sin 171/015. Coeficientes estandarizados y estabilidad de selección se conservan por fold; no son efectos causales ni significancia estadística individual.

Calibración nula frente a árboles: diferencia máxima 0; replay máximo 0; 20440 exclusiones verificadas. Sin uso de PRED59 ni modelo final138.

Conclusiones y recomendación: neighbor_signal_linear_conclusions.md.