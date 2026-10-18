> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Indicadores y pesos continuos: resultados exploratorios

Todos los hiperparámetros fijados antes de entrenamiento. Pesos aprendidos sobre candidatos cross-fitted; ruta por signo del candidato predicho. No son probabilidades calibradas de sobre/subestimación. C4_FIXED nuevo usa alpha=0.01, l1_ratio=0.5 y amplitud=0.5; C4previo P_RAW se conserva como benchmark distinto.

## RMSE / R²

| modelo | random | climate_profile | municipality | spatial |
| --- | --- | --- | --- | --- |
| CT3 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| J7_BOTH | 0.4864 / 0.6709 | 0.4890 / 0.6675 | 0.5808 / 0.5309 | 0.6808 / 0.3556 |
| CT3_P_RAW | 0.5121 / 0.6353 | 0.5235 / 0.6189 | 0.5787 / 0.5344 | 0.6656 / 0.3839 |
| J7_P_RAW | 0.4863 / 0.6711 | 0.4955 / 0.6586 | 0.5774 / 0.5365 | 0.6490 / 0.4143 |
| CT3_C4_FIXED | 0.5147 / 0.6316 | 0.5273 / 0.6134 | 0.5958 / 0.5064 | 0.6612 / 0.3921 |
| CT3_C4_CONSTANT | 0.5122 / 0.6352 | 0.5224 / 0.6206 | 0.5806 / 0.5312 | 0.6702 / 0.3755 |
| CT3_C4_SHARED | 0.5121 / 0.6353 | 0.5216 / 0.6218 | 0.5814 / 0.5300 | 0.6661 / 0.3830 |
| CT3_C4_DIRECTIONAL | 0.5117 / 0.6359 | 0.5203 / 0.6236 | 0.5831 / 0.5273 | 0.6673 / 0.3808 |
| CT3_INDICATORS_DIRECT | 0.5064 / 0.6434 | 0.5185 / 0.6262 | 0.5896 / 0.5167 | 0.6696 / 0.3765 |
| CT3_C4_INDICATORS_DIRECT | 0.5102 / 0.6380 | 0.5240 / 0.6182 | 0.5955 / 0.5069 | 0.6692 / 0.3774 |
| J7_C4_FIXED | 0.4895 / 0.6668 | 0.4922 / 0.6632 | 0.5991 / 0.5010 | 0.6497 / 0.4131 |
| J7_C4_CONSTANT | 0.4866 / 0.6707 | 0.4937 / 0.6611 | 0.5800 / 0.5323 | 0.6574 / 0.3992 |
| J7_C4_SHARED | 0.4865 / 0.6708 | 0.4915 / 0.6642 | 0.5815 / 0.5298 | 0.6508 / 0.4112 |
| J7_C4_DIRECTIONAL | 0.4865 / 0.6708 | 0.4911 / 0.6647 | 0.5831 / 0.5273 | 0.6539 / 0.4054 |
| J7_INDICATORS_DIRECT | 0.4827 / 0.6759 | 0.4865 / 0.6709 | 0.5852 / 0.5238 | 0.6595 / 0.3953 |
| J7_C4_INDICATORS_DIRECT | 0.4867 / 0.6705 | 0.4917 / 0.6639 | 0.5962 / 0.5058 | 0.6570 / 0.3999 |

## Métricas completas

| experiment | protocol | rmse | r2 | mae | bias | error_sd |
| --- | --- | --- | --- | --- | --- | --- |
| CT3 | climate_profile | 0.5206 | 0.6232 | 0.3915 | 0.0046 | 0.5206 |
| CT3 | municipality | 0.5813 | 0.5302 | 0.4603 | -0.0203 | 0.5809 |
| CT3 | random | 0.5116 | 0.6361 | 0.3749 | 0.0005 | 0.5115 |
| CT3 | spatial | 0.6788 | 0.3594 | 0.5306 | 0.1912 | 0.6513 |
| CT3_C4_CONSTANT | climate_profile | 0.5224 | 0.6206 | 0.3924 | 0.0032 | 0.5223 |
| CT3_C4_CONSTANT | municipality | 0.5806 | 0.5312 | 0.4598 | -0.0272 | 0.5800 |
| CT3_C4_CONSTANT | random | 0.5122 | 0.6352 | 0.3756 | 0.0004 | 0.5121 |
| CT3_C4_CONSTANT | spatial | 0.6702 | 0.3755 | 0.5262 | 0.1660 | 0.6493 |
| CT3_C4_DIRECTIONAL | climate_profile | 0.5203 | 0.6236 | 0.3908 | 0.0068 | 0.5203 |
| CT3_C4_DIRECTIONAL | municipality | 0.5831 | 0.5273 | 0.4595 | -0.0345 | 0.5821 |
| CT3_C4_DIRECTIONAL | random | 0.5117 | 0.6359 | 0.3749 | 0.0016 | 0.5116 |
| CT3_C4_DIRECTIONAL | spatial | 0.6673 | 0.3808 | 0.5293 | 0.1765 | 0.6435 |
| CT3_C4_FIXED | climate_profile | 0.5273 | 0.6134 | 0.4003 | 0.0069 | 0.5273 |
| CT3_C4_FIXED | municipality | 0.5958 | 0.5064 | 0.4816 | -0.0872 | 0.5894 |
| CT3_C4_FIXED | random | 0.5147 | 0.6316 | 0.3785 | 0.0013 | 0.5147 |
| CT3_C4_FIXED | spatial | 0.6612 | 0.3921 | 0.5281 | 0.1550 | 0.6428 |
| CT3_C4_INDICATORS_DIRECT | climate_profile | 0.5240 | 0.6182 | 0.3958 | 0.0134 | 0.5239 |
| CT3_C4_INDICATORS_DIRECT | municipality | 0.5955 | 0.5069 | 0.4722 | -0.0636 | 0.5921 |
| CT3_C4_INDICATORS_DIRECT | random | 0.5102 | 0.6380 | 0.3674 | 0.0018 | 0.5101 |
| CT3_C4_INDICATORS_DIRECT | spatial | 0.6692 | 0.3774 | 0.5459 | 0.1060 | 0.6607 |
| CT3_C4_SHARED | climate_profile | 0.5216 | 0.6218 | 0.3917 | 0.0063 | 0.5215 |
| CT3_C4_SHARED | municipality | 0.5814 | 0.5300 | 0.4580 | -0.0327 | 0.5805 |
| CT3_C4_SHARED | random | 0.5121 | 0.6353 | 0.3756 | 0.0014 | 0.5121 |
| CT3_C4_SHARED | spatial | 0.6661 | 0.3830 | 0.5291 | 0.1736 | 0.6431 |
| CT3_INDICATORS_DIRECT | climate_profile | 0.5185 | 0.6262 | 0.3896 | 0.0106 | 0.5184 |
| CT3_INDICATORS_DIRECT | municipality | 0.5896 | 0.5167 | 0.4621 | -0.0690 | 0.5856 |
| CT3_INDICATORS_DIRECT | random | 0.5064 | 0.6434 | 0.3641 | 0.0021 | 0.5064 |
| CT3_INDICATORS_DIRECT | spatial | 0.6696 | 0.3765 | 0.5472 | 0.1164 | 0.6594 |
| CT3_P_RAW | climate_profile | 0.5235 | 0.6189 | 0.3936 | 0.0061 | 0.5235 |
| CT3_P_RAW | municipality | 0.5787 | 0.5344 | 0.4566 | -0.0385 | 0.5774 |
| CT3_P_RAW | random | 0.5121 | 0.6353 | 0.3755 | 0.0010 | 0.5121 |
| CT3_P_RAW | spatial | 0.6656 | 0.3839 | 0.5218 | 0.1591 | 0.6463 |
| J7_BOTH | climate_profile | 0.4890 | 0.6675 | 0.3445 | -0.0139 | 0.4888 |
| J7_BOTH | municipality | 0.5808 | 0.5309 | 0.4604 | -0.0205 | 0.5805 |
| J7_BOTH | random | 0.4864 | 0.6709 | 0.3470 | -0.0121 | 0.4862 |
| J7_BOTH | spatial | 0.6808 | 0.3556 | 0.5291 | 0.2913 | 0.6153 |
| J7_C4_CONSTANT | climate_profile | 0.4937 | 0.6611 | 0.3481 | -0.0156 | 0.4935 |
| J7_C4_CONSTANT | municipality | 0.5800 | 0.5323 | 0.4596 | -0.0296 | 0.5792 |
| J7_C4_CONSTANT | random | 0.4866 | 0.6707 | 0.3472 | -0.0121 | 0.4864 |
| J7_C4_CONSTANT | spatial | 0.6574 | 0.3992 | 0.5137 | 0.2222 | 0.6187 |
| J7_C4_DIRECTIONAL | climate_profile | 0.4911 | 0.6647 | 0.3464 | -0.0081 | 0.4910 |
| J7_C4_DIRECTIONAL | municipality | 0.5831 | 0.5273 | 0.4611 | -0.0364 | 0.5820 |
| J7_C4_DIRECTIONAL | random | 0.4865 | 0.6708 | 0.3474 | -0.0105 | 0.4864 |
| J7_C4_DIRECTIONAL | spatial | 0.6539 | 0.4054 | 0.5179 | 0.2150 | 0.6176 |
| J7_C4_FIXED | climate_profile | 0.4922 | 0.6632 | 0.3494 | -0.0104 | 0.4921 |
| J7_C4_FIXED | municipality | 0.5991 | 0.5010 | 0.4874 | -0.0960 | 0.5914 |
| J7_C4_FIXED | random | 0.4895 | 0.6668 | 0.3502 | -0.0071 | 0.4894 |
| J7_C4_FIXED | spatial | 0.6497 | 0.4131 | 0.5201 | 0.1835 | 0.6233 |
| J7_C4_INDICATORS_DIRECT | climate_profile | 0.4917 | 0.6639 | 0.3467 | 0.0042 | 0.4916 |
| J7_C4_INDICATORS_DIRECT | municipality | 0.5962 | 0.5058 | 0.4748 | -0.0664 | 0.5925 |
| J7_C4_INDICATORS_DIRECT | random | 0.4867 | 0.6705 | 0.3468 | -0.0075 | 0.4866 |
| J7_C4_INDICATORS_DIRECT | spatial | 0.6570 | 0.3999 | 0.5283 | 0.1582 | 0.6376 |
| J7_C4_SHARED | climate_profile | 0.4915 | 0.6642 | 0.3470 | -0.0116 | 0.4913 |
| J7_C4_SHARED | municipality | 0.5815 | 0.5298 | 0.4594 | -0.0323 | 0.5806 |
| J7_C4_SHARED | random | 0.4865 | 0.6708 | 0.3474 | -0.0108 | 0.4863 |
| J7_C4_SHARED | spatial | 0.6508 | 0.4112 | 0.5109 | 0.2188 | 0.6129 |
| J7_INDICATORS_DIRECT | climate_profile | 0.4865 | 0.6709 | 0.3425 | 0.0009 | 0.4865 |
| J7_INDICATORS_DIRECT | municipality | 0.5852 | 0.5238 | 0.4615 | -0.0692 | 0.5811 |
| J7_INDICATORS_DIRECT | random | 0.4827 | 0.6759 | 0.3432 | -0.0072 | 0.4826 |
| J7_INDICATORS_DIRECT | spatial | 0.6595 | 0.3953 | 0.5291 | 0.1618 | 0.6393 |
| J7_P_RAW | climate_profile | 0.4955 | 0.6586 | 0.3497 | -0.0199 | 0.4951 |
| J7_P_RAW | municipality | 0.5774 | 0.5365 | 0.4535 | -0.0410 | 0.5759 |
| J7_P_RAW | random | 0.4863 | 0.6711 | 0.3468 | -0.0098 | 0.4862 |
| J7_P_RAW | spatial | 0.6490 | 0.4143 | 0.5067 | 0.2052 | 0.6157 |

## Peso variable frente a constante

| experiment | reference | contrast | protocol | delta_rmse | low95 | high95 | p_mse_signflip | n_clusters | exact_sign_enumeration | n_sign_assignments | p_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CT3_C4_SHARED | CT3_C4_CONSTANT | variable_vs_constant | climate_profile | -0.0008 | -0.0033 | 0.0006 | 0.3033 | 43 | False | 20000 | 1.0000 |
| CT3_C4_DIRECTIONAL | CT3_C4_CONSTANT | variable_vs_constant | climate_profile | -0.0021 | -0.0048 | 0.0011 | 0.2771 | 43 | False | 20000 | 1.0000 |
| J7_C4_SHARED | J7_C4_CONSTANT | variable_vs_constant | climate_profile | -0.0022 | -0.0071 | -0.0002 | 0.0590 | 43 | False | 20000 | 1.0000 |
| J7_C4_DIRECTIONAL | J7_C4_CONSTANT | variable_vs_constant | climate_profile | -0.0026 | -0.0080 | 0.0002 | 0.1110 | 43 | False | 20000 | 1.0000 |
| CT3_C4_SHARED | CT3_C4_CONSTANT | variable_vs_constant | municipality | 0.0008 | -0.0082 | 0.0056 | 0.9062 | 9 | True | 512 | 1.0000 |
| CT3_C4_DIRECTIONAL | CT3_C4_CONSTANT | variable_vs_constant | municipality | 0.0024 | -0.0092 | 0.0098 | 0.7656 | 9 | True | 512 | 1.0000 |
| J7_C4_SHARED | J7_C4_CONSTANT | variable_vs_constant | municipality | 0.0016 | -0.0090 | 0.0071 | 0.6875 | 9 | True | 512 | 1.0000 |
| J7_C4_DIRECTIONAL | J7_C4_CONSTANT | variable_vs_constant | municipality | 0.0031 | -0.0097 | 0.0134 | 0.6562 | 9 | True | 512 | 1.0000 |
| CT3_C4_SHARED | CT3_C4_CONSTANT | variable_vs_constant | random | -0.0001 | -0.0005 | 0.0004 | 0.7597 | 43 | False | 20000 | 1.0000 |
| CT3_C4_DIRECTIONAL | CT3_C4_CONSTANT | variable_vs_constant | random | -0.0005 | -0.0018 | 0.0003 | 0.3004 | 43 | False | 20000 | 1.0000 |
| J7_C4_SHARED | J7_C4_CONSTANT | variable_vs_constant | random | -0.0001 | -0.0004 | 0.0006 | 0.6701 | 43 | False | 20000 | 1.0000 |
| J7_C4_DIRECTIONAL | J7_C4_CONSTANT | variable_vs_constant | random | -0.0001 | -0.0005 | 0.0006 | 0.8582 | 43 | False | 20000 | 1.0000 |
| CT3_C4_SHARED | CT3_C4_CONSTANT | variable_vs_constant | spatial | -0.0041 | -0.0141 | 0.0045 | 0.4375 | 5 | True | 32 | 1.0000 |
| CT3_C4_DIRECTIONAL | CT3_C4_CONSTANT | variable_vs_constant | spatial | -0.0029 | -0.0088 | 0.0037 | 0.6250 | 5 | True | 32 | 1.0000 |
| J7_C4_SHARED | J7_C4_CONSTANT | variable_vs_constant | spatial | -0.0066 | -0.0222 | 0.0037 | 0.5000 | 5 | True | 32 | 1.0000 |
| J7_C4_DIRECTIONAL | J7_C4_CONSTANT | variable_vs_constant | spatial | -0.0034 | -0.0093 | 0.0026 | 0.5000 | 5 | True | 32 | 1.0000 |

## Ganancias por parcela

| experiment | reference | protocol | total_sse_gain | hard35_sse_gain | remaining103_sse_gain | fraction_improved | fraction_worsened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CT3_C4_CONSTANT | CT3 | climate_profile | -0.2526 | -0.2319 | -0.0208 | 0.1667 | 0.1957 |
| CT3_C4_CONSTANT | CT3 | municipality | 0.0999 | -0.0948 | 0.1947 | 0.1812 | 0.1159 |
| CT3_C4_CONSTANT | CT3 | random | -0.0836 | -0.0416 | -0.0421 | 0.4710 | 0.4710 |
| CT3_C4_CONSTANT | CT3 | spatial | 1.5978 | 0.4492 | 1.1486 | 0.2826 | 0.1739 |
| CT3_C4_DIRECTIONAL | CT3 | climate_profile | 0.0431 | 0.0377 | 0.0054 | 0.1739 | 0.1667 |
| CT3_C4_DIRECTIONAL | CT3 | municipality | -0.2925 | -0.1966 | -0.0959 | 0.2464 | 0.1957 |
| CT3_C4_DIRECTIONAL | CT3 | random | -0.0150 | 0.0438 | -0.0588 | 0.4638 | 0.4493 |
| CT3_C4_DIRECTIONAL | CT3 | spatial | 2.1286 | 2.2271 | -0.0985 | 0.3333 | 0.2609 |
| CT3_C4_FIXED | CT3 | climate_profile | -0.9710 | -0.1443 | -0.8267 | 0.4275 | 0.5725 |
| CT3_C4_FIXED | CT3 | municipality | -2.3699 | -0.3424 | -2.0274 | 0.4420 | 0.5580 |
| CT3_C4_FIXED | CT3 | random | -0.4484 | -0.1758 | -0.2726 | 0.4420 | 0.5580 |
| CT3_C4_FIXED | CT3 | spatial | 3.2424 | 3.0058 | 0.2366 | 0.5290 | 0.4710 |
| CT3_C4_INDICATORS_DIRECT | CT3 | climate_profile | -0.4946 | 0.5865 | -1.0811 | 0.5000 | 0.5000 |
| CT3_C4_INDICATORS_DIRECT | CT3 | municipality | -2.3156 | 0.0110 | -2.3266 | 0.4420 | 0.5580 |
| CT3_C4_INDICATORS_DIRECT | CT3 | random | 0.1945 | 0.5400 | -0.3455 | 0.4855 | 0.5145 |
| CT3_C4_INDICATORS_DIRECT | CT3 | spatial | 1.7863 | 3.8453 | -2.0590 | 0.4855 | 0.5145 |
| CT3_C4_SHARED | CT3 | climate_profile | -0.1370 | -0.1723 | 0.0353 | 0.1087 | 0.1377 |
| CT3_C4_SHARED | CT3 | municipality | -0.0240 | -0.0799 | 0.0559 | 0.2246 | 0.1884 |
| CT3_C4_SHARED | CT3 | random | -0.0745 | -0.0069 | -0.0677 | 0.4638 | 0.4565 |
| CT3_C4_SHARED | CT3 | spatial | 2.3447 | 2.1168 | 0.2280 | 0.3913 | 0.2899 |
| CT3_INDICATORS_DIRECT | CT3 | climate_profile | 0.3056 | 1.0854 | -0.7798 | 0.5000 | 0.5000 |
| CT3_INDICATORS_DIRECT | CT3 | municipality | -1.3484 | 0.6103 | -1.9587 | 0.4928 | 0.5072 |
| CT3_INDICATORS_DIRECT | CT3 | random | 0.7268 | 0.9388 | -0.2120 | 0.5217 | 0.4783 |
| CT3_INDICATORS_DIRECT | CT3 | spatial | 1.6987 | 3.8230 | -2.1243 | 0.4638 | 0.5362 |
| J7_C4_CONSTANT | J7_BOTH | climate_profile | -0.6344 | -0.4642 | -0.1702 | 0.1739 | 0.1884 |
| J7_C4_CONSTANT | J7_BOTH | municipality | 0.1405 | -0.0957 | 0.2361 | 0.1232 | 0.0942 |
| J7_C4_CONSTANT | J7_BOTH | random | -0.0250 | -0.0132 | -0.0117 | 0.2319 | 0.3841 |
| J7_C4_CONSTANT | J7_BOTH | spatial | 4.3315 | 2.4195 | 1.9120 | 0.4565 | 0.2754 |
| J7_C4_DIRECTIONAL | J7_BOTH | climate_profile | -0.2807 | -0.2554 | -0.0252 | 0.2754 | 0.2971 |
| J7_C4_DIRECTIONAL | J7_BOTH | municipality | -0.3620 | -0.0515 | -0.3105 | 0.2464 | 0.2246 |
| J7_C4_DIRECTIONAL | J7_BOTH | random | -0.0173 | 0.0439 | -0.0611 | 0.4493 | 0.4420 |
| J7_C4_DIRECTIONAL | J7_BOTH | spatial | 4.9514 | 4.2878 | 0.6637 | 0.4493 | 0.3261 |
| J7_C4_FIXED | J7_BOTH | climate_profile | -0.4269 | -0.0750 | -0.3519 | 0.4710 | 0.5290 |
| J7_C4_FIXED | J7_BOTH | municipality | -2.9724 | 0.2703 | -3.2427 | 0.4638 | 0.5362 |
| J7_C4_FIXED | J7_BOTH | random | -0.4149 | -0.1997 | -0.2152 | 0.4493 | 0.5507 |
| J7_C4_FIXED | J7_BOTH | spatial | 5.7112 | 4.7720 | 0.9392 | 0.5362 | 0.4638 |
| J7_C4_INDICATORS_DIRECT | J7_BOTH | climate_profile | -0.3561 | 0.5857 | -0.9418 | 0.4855 | 0.5145 |
| J7_C4_INDICATORS_DIRECT | J7_BOTH | municipality | -2.4966 | 0.4394 | -2.9360 | 0.4565 | 0.5435 |
| J7_C4_INDICATORS_DIRECT | J7_BOTH | random | -0.0439 | 0.4453 | -0.4892 | 0.4493 | 0.5507 |
| J7_C4_INDICATORS_DIRECT | J7_BOTH | spatial | 4.4015 | 4.5710 | -0.1695 | 0.5000 | 0.5000 |
| J7_C4_SHARED | J7_BOTH | climate_profile | -0.3306 | -0.2967 | -0.0338 | 0.2174 | 0.2319 |
| J7_C4_SHARED | J7_BOTH | municipality | -0.1100 | 0.0039 | -0.1139 | 0.2246 | 0.1884 |
| J7_C4_SHARED | J7_BOTH | random | -0.0110 | 0.0394 | -0.0504 | 0.3551 | 0.3986 |
| J7_C4_SHARED | J7_BOTH | spatial | 5.5215 | 3.9653 | 1.5562 | 0.4928 | 0.2609 |
| J7_INDICATORS_DIRECT | J7_BOTH | climate_profile | 0.3407 | 1.1409 | -0.8003 | 0.5000 | 0.5000 |
| J7_INDICATORS_DIRECT | J7_BOTH | municipality | -0.7072 | 1.3508 | -2.0580 | 0.5000 | 0.5000 |
| J7_INDICATORS_DIRECT | J7_BOTH | random | 0.4959 | 0.8364 | -0.3406 | 0.4638 | 0.5362 |
| J7_INDICATORS_DIRECT | J7_BOTH | spatial | 3.9464 | 4.2213 | -0.2749 | 0.4855 | 0.5145 |

Las112pruebas pareadas, omisiones, regiones, sin35/sin10/sin171/015, intraperfil, soporte, pesos y coeficientes están en tablas/Excel. Son resultados exploratorios del banco reutilizado. No se selecciona un nuevo líder ni se infiere causalidad.

Interpretaci?n y decisi?n: [temporal_indicator_weights_conclusions.md](temporal_indicator_weights_conclusions.md).
