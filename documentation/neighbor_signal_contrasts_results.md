# Contrastes de señales respecto a vecinos: resultados

Cuatro alternativas congeladas y dos referencias exactas, mismas 65 particiones. GEO/COMPACT indican los vecinos; ATTENUATE reduce J7 hacia CT3; RESIDUAL añade un ajuste contraído y limitado a ±0.5 t/ha. Cortes y parámetros seleccionados internamente. Resultados exploratorios, sin promoción automática.

## RMSE / R²

| modelo | random | climate_profile | municipality | spatial |
| --- | --- | --- | --- | --- |
| J7_BOTH | 0.4864 / 0.6709 | 0.4890 / 0.6675 | 0.5808 / 0.5309 | 0.6808 / 0.3556 |
| CT3 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| GEO_ATTENUATE | 0.4875 / 0.6694 | 0.4868 / 0.6706 | 0.5811 / 0.5305 | 0.6749 / 0.3667 |
| GEO_RESIDUAL | 0.4894 / 0.6669 | 0.4932 / 0.6618 | 0.5910 / 0.5144 | 0.7096 / 0.3000 |
| COMPACT_ATTENUATE | 0.4877 / 0.6692 | 0.4881 / 0.6687 | 0.5775 / 0.5362 | 0.6756 / 0.3655 |
| COMPACT_RESIDUAL | 0.4900 / 0.6660 | 0.4869 / 0.6703 | 0.5794 / 0.5332 | 0.7152 / 0.2888 |

## RMSE, MAE, sesgo y dispersión

| experiment | protocol | rmse | mae | r2 | bias | error_sd | p95_absolute |
| --- | --- | --- | --- | --- | --- | --- | --- |
| COMPACT_ATTENUATE | climate_profile | 0.4881 | 0.3445 | 0.6687 | -0.0106 | 0.4880 | 0.8926 |
| COMPACT_ATTENUATE | municipality | 0.5775 | 0.4577 | 0.5362 | -0.0222 | 0.5771 | 1.0790 |
| COMPACT_ATTENUATE | random | 0.4877 | 0.3477 | 0.6692 | -0.0122 | 0.4875 | 0.8657 |
| COMPACT_ATTENUATE | spatial | 0.6756 | 0.5184 | 0.3655 | 0.2557 | 0.6253 | 1.4279 |
| COMPACT_RESIDUAL | climate_profile | 0.4869 | 0.3416 | 0.6703 | -0.0075 | 0.4869 | 0.8929 |
| COMPACT_RESIDUAL | municipality | 0.5794 | 0.4598 | 0.5332 | -0.0331 | 0.5785 | 1.0790 |
| COMPACT_RESIDUAL | random | 0.4900 | 0.3496 | 0.6660 | -0.0087 | 0.4899 | 0.8653 |
| COMPACT_RESIDUAL | spatial | 0.7152 | 0.5824 | 0.2888 | 0.1476 | 0.6998 | 1.4792 |
| CT3 | climate_profile | 0.5206 | 0.3915 | 0.6232 | 0.0046 | 0.5206 | 1.0115 |
| CT3 | municipality | 0.5813 | 0.4603 | 0.5302 | -0.0203 | 0.5809 | 1.0790 |
| CT3 | random | 0.5116 | 0.3749 | 0.6361 | 0.0005 | 0.5115 | 1.0529 |
| CT3 | spatial | 0.6788 | 0.5306 | 0.3594 | 0.1912 | 0.6513 | 1.4223 |
| GEO_ATTENUATE | climate_profile | 0.4868 | 0.3420 | 0.6706 | -0.0064 | 0.4867 | 0.8912 |
| GEO_ATTENUATE | municipality | 0.5811 | 0.4600 | 0.5305 | -0.0199 | 0.5808 | 1.0790 |
| GEO_ATTENUATE | random | 0.4875 | 0.3473 | 0.6694 | -0.0118 | 0.4873 | 0.8747 |
| GEO_ATTENUATE | spatial | 0.6749 | 0.5188 | 0.3667 | 0.2480 | 0.6277 | 1.4279 |
| GEO_RESIDUAL | climate_profile | 0.4932 | 0.3519 | 0.6618 | -0.0100 | 0.4931 | 0.9335 |
| GEO_RESIDUAL | municipality | 0.5910 | 0.4635 | 0.5144 | -0.0891 | 0.5842 | 1.1194 |
| GEO_RESIDUAL | random | 0.4894 | 0.3489 | 0.6669 | -0.0090 | 0.4893 | 0.8675 |
| GEO_RESIDUAL | spatial | 0.7096 | 0.5762 | 0.3000 | 0.1467 | 0.6942 | 1.4792 |
| J7_BOTH | climate_profile | 0.4890 | 0.3445 | 0.6675 | -0.0139 | 0.4888 | 0.9172 |
| J7_BOTH | municipality | 0.5808 | 0.4604 | 0.5309 | -0.0205 | 0.5805 | 1.0790 |
| J7_BOTH | random | 0.4864 | 0.3470 | 0.6709 | -0.0121 | 0.4862 | 0.8553 |
| J7_BOTH | spatial | 0.6808 | 0.5291 | 0.3556 | 0.2913 | 0.6153 | 1.4279 |

## Comparaciones pareadas: 32 contrastes con Holm conjunto

| experiment | reference | contrast | protocol | delta_rmse | low95 | high95 | p_mse_signflip | n_clusters | exact_sign_enumeration | n_sign_assignments | p_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GEO_ATTENUATE | J7_BOTH | reference | climate_profile | -0.0023 | -0.0064 | 0.0000 | 0.1222 | 43 | False | 20000 | 1.0000 |
| GEO_RESIDUAL | J7_BOTH | reference | climate_profile | 0.0042 | -0.0009 | 0.0092 | 0.1671 | 43 | False | 20000 | 1.0000 |
| COMPACT_ATTENUATE | J7_BOTH | reference | climate_profile | -0.0009 | -0.0034 | 0.0000 | 0.4995 | 43 | False | 20000 | 1.0000 |
| COMPACT_RESIDUAL | J7_BOTH | reference | climate_profile | -0.0021 | -0.0051 | 0.0000 | 1.0000 | 43 | False | 20000 | 1.0000 |
| GEO_ATTENUATE | COMPACT_ATTENUATE | neighborhood | climate_profile | -0.0014 | -0.0045 | 0.0008 | 0.3089 | 43 | False | 20000 | 1.0000 |
| GEO_RESIDUAL | COMPACT_RESIDUAL | neighborhood | climate_profile | 0.0063 | 0.0008 | 0.0100 | 0.0790 | 43 | False | 20000 | 1.0000 |
| GEO_RESIDUAL | GEO_ATTENUATE | use | climate_profile | 0.0065 | 0.0012 | 0.0130 | 0.0470 | 43 | False | 20000 | 1.0000 |
| COMPACT_RESIDUAL | COMPACT_ATTENUATE | use | climate_profile | -0.0012 | -0.0043 | 0.0032 | 1.0000 | 43 | False | 20000 | 1.0000 |
| GEO_ATTENUATE | J7_BOTH | reference | municipality | 0.0003 | -0.0052 | 0.0038 | 0.9375 | 9 | True | 512 | 1.0000 |
| GEO_RESIDUAL | J7_BOTH | reference | municipality | 0.0101 | 0.0025 | 0.0515 | 0.0625 | 9 | True | 512 | 1.0000 |
| COMPACT_ATTENUATE | J7_BOTH | reference | municipality | -0.0033 | -0.0157 | 0.0026 | 0.5625 | 9 | True | 512 | 1.0000 |
| COMPACT_RESIDUAL | J7_BOTH | reference | municipality | -0.0014 | -0.0061 | 0.0000 | 1.0000 | 9 | True | 512 | 1.0000 |
| GEO_ATTENUATE | COMPACT_ATTENUATE | neighborhood | municipality | 0.0036 | 0.0000 | 0.0144 | 0.1875 | 9 | True | 512 | 1.0000 |
| GEO_RESIDUAL | COMPACT_RESIDUAL | neighborhood | municipality | 0.0116 | 0.0028 | 0.0542 | 0.0625 | 9 | True | 512 | 1.0000 |
| GEO_RESIDUAL | GEO_ATTENUATE | use | municipality | 0.0099 | 0.0017 | 0.0545 | 0.0625 | 9 | True | 512 | 1.0000 |
| COMPACT_RESIDUAL | COMPACT_ATTENUATE | use | municipality | 0.0019 | -0.0067 | 0.0157 | 0.7812 | 9 | True | 512 | 1.0000 |
| GEO_ATTENUATE | J7_BOTH | reference | random | 0.0011 | -0.0010 | 0.0065 | 0.3761 | 43 | False | 20000 | 1.0000 |
| GEO_RESIDUAL | J7_BOTH | reference | random | 0.0030 | 0.0007 | 0.0051 | 0.0392 | 43 | False | 20000 | 1.0000 |
| COMPACT_ATTENUATE | J7_BOTH | reference | random | 0.0013 | -0.0009 | 0.0065 | 0.3158 | 43 | False | 20000 | 1.0000 |
| COMPACT_RESIDUAL | J7_BOTH | reference | random | 0.0036 | 0.0015 | 0.0073 | 0.0049 | 43 | False | 20000 | 0.1568 |
| GEO_ATTENUATE | COMPACT_ATTENUATE | neighborhood | random | -0.0002 | -0.0008 | 0.0006 | 0.6570 | 43 | False | 20000 | 1.0000 |
| GEO_RESIDUAL | COMPACT_RESIDUAL | neighborhood | random | -0.0006 | -0.0043 | 0.0012 | 0.5871 | 43 | False | 20000 | 1.0000 |
| GEO_RESIDUAL | GEO_ATTENUATE | use | random | 0.0019 | -0.0044 | 0.0046 | 0.4736 | 43 | False | 20000 | 1.0000 |
| COMPACT_RESIDUAL | COMPACT_ATTENUATE | use | random | 0.0023 | -0.0020 | 0.0056 | 0.2372 | 43 | False | 20000 | 1.0000 |
| GEO_ATTENUATE | J7_BOTH | reference | spatial | -0.0059 | -0.0201 | 0.0000 | 0.3750 | 5 | True | 32 | 1.0000 |
| GEO_RESIDUAL | J7_BOTH | reference | spatial | 0.0288 | -0.0320 | 0.1030 | 0.7500 | 5 | True | 32 | 1.0000 |
| COMPACT_ATTENUATE | J7_BOTH | reference | spatial | -0.0053 | -0.0194 | 0.0020 | 0.7500 | 5 | True | 32 | 1.0000 |
| COMPACT_RESIDUAL | J7_BOTH | reference | spatial | 0.0344 | -0.0178 | 0.1093 | 0.5000 | 5 | True | 32 | 1.0000 |
| GEO_ATTENUATE | COMPACT_ATTENUATE | neighborhood | spatial | -0.0007 | -0.0024 | 0.0002 | 1.0000 | 5 | True | 32 | 1.0000 |
| GEO_RESIDUAL | COMPACT_RESIDUAL | neighborhood | spatial | -0.0056 | -0.0194 | 0.0000 | 0.5000 | 5 | True | 32 | 1.0000 |
| GEO_RESIDUAL | GEO_ATTENUATE | use | spatial | 0.0347 | -0.0320 | 0.1242 | 0.6250 | 5 | True | 32 | 1.0000 |
| COMPACT_RESIDUAL | COMPACT_ATTENUATE | use | spatial | 0.0396 | -0.0201 | 0.1297 | 0.5000 | 5 | True | 32 | 1.0000 |

## Diagnóstico de incertidumbre de J7, sin usar correcciones

| neighborhood | protocol | cohort_kind | cohort | n | spearman_anomaly_absolute_error | auc_error_above_1 | n_large_errors | n_top | top_mae | rest_mae | top_rmse | rest_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COMPACT | climate_profile | climate_profile | 24 | 34.0000 | 0.0105 | 0.7344 | 2.0000 | 7.0000 | 0.5405 | 0.2649 | 0.9328 | 0.3962 |
| COMPACT | climate_profile | climate_profile | 38 | 11.0000 | 0.1545 | nan | 0.0000 | 3.0000 | 0.4155 | 0.3941 | 0.4726 | 0.4314 |
| COMPACT | climate_profile | climate_profile | 4 | 29.0000 | -0.2039 | 0.6538 | 3.0000 | 13.0000 | 0.3963 | 0.4551 | 0.6246 | 0.5636 |
| COMPACT | climate_profile | overall | ALL | 138.0000 | -0.0792 | 0.6692 | 6.0000 | 28.0000 | 0.3643 | 0.3394 | 0.5228 | 0.4801 |
| COMPACT | climate_profile | overall | WITHOUT_171_015 | 136.0000 | -0.1095 | 0.5975 | 4.0000 | 28.0000 | 0.3021 | 0.3238 | 0.4033 | 0.4283 |
| COMPACT | climate_profile | state | Hidalgo | 36.0000 | -0.1495 | 0.2286 | 1.0000 | 8.0000 | 0.2590 | 0.2636 | 0.2836 | 0.3674 |
| COMPACT | climate_profile | state | Puebla | 71.0000 | -0.0423 | 0.7121 | 5.0000 | 15.0000 | 0.4125 | 0.3627 | 0.6259 | 0.5443 |
| COMPACT | climate_profile | state | Tlaxcala | 31.0000 | -0.0968 | nan | 0.0000 | 7.0000 | 0.3137 | 0.3913 | 0.3865 | 0.4595 |
| COMPACT | municipality | climate_profile | 24 | 34.0000 | 0.0533 | 0.7969 | 2.0000 | 7.0000 | 0.4513 | 0.4252 | 0.5450 | 0.5520 |
| COMPACT | municipality | climate_profile | 38 | 11.0000 | 0.1909 | nan | 0.0000 | 3.0000 | 0.4460 | 0.4461 | 0.5100 | 0.5170 |
| COMPACT | municipality | climate_profile | 4 | 29.0000 | -0.1507 | 0.3333 | 2.0000 | 6.0000 | 0.4133 | 0.4921 | 0.5371 | 0.6410 |
| COMPACT | municipality | overall | ALL | 138.0000 | -0.0158 | 0.5711 | 9.0000 | 28.0000 | 0.4388 | 0.4659 | 0.5897 | 0.5786 |
| COMPACT | municipality | overall | WITHOUT_171_015 | 136.0000 | -0.0312 | 0.5393 | 7.0000 | 28.0000 | 0.4059 | 0.4484 | 0.5103 | 0.5466 |
| COMPACT | municipality | state | Hidalgo | 36.0000 | -0.1467 | 0.5469 | 4.0000 | 8.0000 | 0.4729 | 0.5560 | 0.6181 | 0.6734 |
| COMPACT | municipality | state | Puebla | 71.0000 | -0.0043 | 0.5667 | 5.0000 | 15.0000 | 0.4391 | 0.4485 | 0.6235 | 0.5676 |
| COMPACT | municipality | state | Tlaxcala | 31.0000 | 0.0798 | nan | 0.0000 | 7.0000 | 0.3902 | 0.4061 | 0.4344 | 0.4838 |
| COMPACT | random | climate_profile | 24 | 34.0000 | 0.0360 | 0.8656 | 2.0000 | 7.0000 | 0.6224 | 0.3220 | 0.8947 | 0.4021 |
| COMPACT | random | climate_profile | 38 | 11.0000 | -0.0518 | nan | 0.0000 | 3.0000 | 0.3900 | 0.3798 | 0.4623 | 0.4318 |
| COMPACT | random | climate_profile | 4 | 29.0000 | -0.0011 | 0.6467 | 2.3000 | 6.0000 | 0.6112 | 0.3474 | 0.8664 | 0.4794 |
| COMPACT | random | overall | ALL | 138.0000 | -0.0535 | 0.6822 | 5.3000 | 28.0000 | 0.4267 | 0.3267 | 0.6566 | 0.4300 |
| COMPACT | random | overall | WITHOUT_171_015 | 136.0000 | -0.0907 | 0.5547 | 3.3000 | 28.0000 | 0.3221 | 0.3206 | 0.4302 | 0.4131 |
| COMPACT | random | state | Hidalgo | 36.0000 | 0.0410 | 0.2429 | 1.0000 | 8.0000 | 0.3041 | 0.2621 | 0.3757 | 0.3650 |
| COMPACT | random | state | Puebla | 71.0000 | -0.0471 | 0.7604 | 4.3000 | 15.0000 | 0.4901 | 0.3668 | 0.7491 | 0.4955 |
| COMPACT | random | state | Tlaxcala | 31.0000 | -0.1250 | nan | 0.0000 | 7.0000 | 0.2670 | 0.3481 | 0.3643 | 0.4268 |
| COMPACT | spatial | climate_profile | 24 | 34.0000 | -0.0050 | 0.8281 | 2.0000 | 7.0000 | 0.5213 | 0.3147 | 0.8291 | 0.4256 |
| COMPACT | spatial | climate_profile | 38 | 11.0000 | 0.1182 | 0.5357 | 7.0000 | 3.0000 | 1.0384 | 1.0175 | 1.1139 | 1.0999 |
| COMPACT | spatial | climate_profile | 4 | 29.0000 | -0.2039 | 0.5370 | 2.0000 | 13.0000 | 0.3724 | 0.4290 | 0.6325 | 0.5181 |
| COMPACT | spatial | overall | ALL | 138.0000 | -0.1868 | 0.5010 | 21.0000 | 28.0000 | 0.4192 | 0.5571 | 0.6073 | 0.6983 |
| COMPACT | spatial | overall | WITHOUT_171_015 | 136.0000 | -0.2236 | 0.4651 | 19.0000 | 28.0000 | 0.3495 | 0.5477 | 0.4754 | 0.6757 |
| COMPACT | spatial | state | Hidalgo | 36.0000 | -0.2245 | 0.5234 | 4.0000 | 8.0000 | 0.4206 | 0.5752 | 0.5830 | 0.6725 |
| COMPACT | spatial | state | Puebla | 71.0000 | -0.0764 | 0.6716 | 4.0000 | 15.0000 | 0.3958 | 0.3816 | 0.6234 | 0.5276 |
| COMPACT | spatial | state | Tlaxcala | 31.0000 | 0.0512 | 0.5598 | 13.0000 | 7.0000 | 0.9574 | 0.8139 | 1.0327 | 0.9059 |
| GEO | climate_profile | climate_profile | 24 | 34.0000 | -0.1471 | 0.7344 | 2.0000 | 7.0000 | 0.5128 | 0.2720 | 0.9287 | 0.3987 |
| GEO | climate_profile | climate_profile | 38 | 11.0000 | 0.0273 | nan | 0.0000 | 3.0000 | 0.3779 | 0.4083 | 0.4279 | 0.4486 |
| GEO | climate_profile | climate_profile | 4 | 29.0000 | -0.1064 | 0.6923 | 3.0000 | 11.0000 | 0.4584 | 0.4106 | 0.6967 | 0.5172 |
| GEO | climate_profile | overall | ALL | 138.0000 | -0.0826 | 0.6616 | 6.0000 | 28.0000 | 0.3449 | 0.3444 | 0.5179 | 0.4814 |
| GEO | climate_profile | overall | WITHOUT_171_015 | 136.0000 | -0.1158 | 0.5729 | 4.0000 | 28.0000 | 0.2917 | 0.3265 | 0.4003 | 0.4290 |
| GEO | climate_profile | state | Hidalgo | 36.0000 | -0.1191 | 0.0286 | 1.0000 | 8.0000 | 0.1974 | 0.2812 | 0.2310 | 0.3778 |
| GEO | climate_profile | state | Puebla | 71.0000 | -0.0273 | 0.7424 | 5.0000 | 15.0000 | 0.4064 | 0.3643 | 0.6362 | 0.5411 |
| GEO | climate_profile | state | Tlaxcala | 31.0000 | -0.0698 | nan | 0.0000 | 7.0000 | 0.3137 | 0.3913 | 0.3865 | 0.4595 |
| GEO | municipality | climate_profile | 24 | 34.0000 | 0.0432 | 0.9062 | 2.0000 | 7.0000 | 0.6613 | 0.3708 | 0.9008 | 0.4139 |
| GEO | municipality | climate_profile | 38 | 11.0000 | 0.1091 | nan | 0.0000 | 3.0000 | 0.4460 | 0.4461 | 0.5100 | 0.5170 |
| GEO | municipality | climate_profile | 4 | 29.0000 | -0.1128 | 0.2593 | 2.0000 | 6.0000 | 0.3678 | 0.5040 | 0.4721 | 0.6542 |
| GEO | municipality | overall | ALL | 138.0000 | -0.0761 | 0.4953 | 9.0000 | 28.0000 | 0.4289 | 0.4684 | 0.5116 | 0.5972 |
| GEO | municipality | overall | WITHOUT_171_015 | 136.0000 | -0.1021 | 0.4208 | 7.0000 | 28.0000 | 0.4289 | 0.4425 | 0.5116 | 0.5463 |
| GEO | municipality | state | Hidalgo | 36.0000 | -0.2779 | 0.3984 | 4.0000 | 8.0000 | 0.5135 | 0.5444 | 0.6413 | 0.6671 |
| GEO | municipality | state | Puebla | 71.0000 | -0.0055 | 0.5667 | 5.0000 | 15.0000 | 0.4679 | 0.4408 | 0.5757 | 0.5809 |
| GEO | municipality | state | Tlaxcala | 31.0000 | 0.0442 | nan | 0.0000 | 7.0000 | 0.3902 | 0.4061 | 0.4344 | 0.4838 |
| GEO | random | climate_profile | 24 | 34.0000 | 0.0825 | 0.8664 | 2.0000 | 7.0000 | 0.6045 | 0.3267 | 0.8762 | 0.4127 |
| GEO | random | climate_profile | 38 | 11.0000 | -0.1155 | nan | 0.0000 | 3.0000 | 0.3900 | 0.3798 | 0.4623 | 0.4318 |
| GEO | random | climate_profile | 4 | 29.0000 | 0.0885 | 0.6692 | 2.3000 | 6.0000 | 0.6768 | 0.3303 | 0.9108 | 0.4568 |
| GEO | random | overall | ALL | 138.0000 | -0.0364 | 0.6239 | 5.3000 | 28.0000 | 0.4163 | 0.3294 | 0.6446 | 0.4339 |
| GEO | random | overall | WITHOUT_171_015 | 136.0000 | -0.0680 | 0.4907 | 3.3000 | 28.0000 | 0.3191 | 0.3214 | 0.4334 | 0.4123 |
| GEO | random | state | Hidalgo | 36.0000 | -0.0582 | 0.0343 | 1.0000 | 8.0000 | 0.2169 | 0.2871 | 0.2756 | 0.3891 |
| GEO | random | state | Puebla | 71.0000 | 0.0397 | 0.7788 | 4.3000 | 15.0000 | 0.5977 | 0.3380 | 0.8648 | 0.4401 |
| GEO | random | state | Tlaxcala | 31.0000 | -0.0663 | nan | 0.0000 | 7.0000 | 0.2724 | 0.3466 | 0.3647 | 0.4262 |
| GEO | spatial | climate_profile | 24 | 34.0000 | 0.1013 | 0.8281 | 2.0000 | 7.0000 | 0.5213 | 0.3147 | 0.8291 | 0.4256 |
| GEO | spatial | climate_profile | 38 | 11.0000 | 0.1636 | 0.5357 | 7.0000 | 3.0000 | 1.3481 | 0.9013 | 1.3666 | 0.9873 |
| GEO | spatial | climate_profile | 4 | 29.0000 | -0.0440 | 0.6111 | 2.0000 | 15.0000 | 0.4026 | 0.4048 | 0.6229 | 0.5123 |
| GEO | spatial | overall | ALL | 138.0000 | -0.0929 | 0.5582 | 21.0000 | 28.0000 | 0.4501 | 0.5492 | 0.6404 | 0.6907 |
| GEO | spatial | overall | WITHOUT_171_015 | 136.0000 | -0.1256 | 0.5286 | 19.0000 | 28.0000 | 0.3939 | 0.5362 | 0.5231 | 0.6665 |
| GEO | spatial | state | Hidalgo | 36.0000 | -0.2533 | 0.5312 | 4.0000 | 8.0000 | 0.4579 | 0.5646 | 0.6040 | 0.6671 |
| GEO | spatial | state | Puebla | 71.0000 | -0.0116 | 0.7127 | 4.0000 | 17.0000 | 0.3965 | 0.3809 | 0.6073 | 0.5297 |
| GEO | spatial | state | Tlaxcala | 31.0000 | 0.0014 | 0.5577 | 13.0000 | 7.0000 | 0.7704 | 0.8685 | 0.8881 | 0.9496 |

La AUC y el quintil son diagnósticos descriptivos del error observado, no probabilidades operativas ni intervalos calibrados. Las relaciones de signo, error absoluto y ajuste se interpretan por separado.

## Distribución de ganancias

| experiment | protocol | total_sse_gain | cases_sse_gain | fraction_improved | fraction_worsened |
| --- | --- | --- | --- | --- | --- |
| COMPACT_ATTENUATE | climate_profile | 0.1214 | 0.0000 | 0.0580 | 0.0507 |
| COMPACT_ATTENUATE | municipality | 0.5285 | 0.0000 | 0.0652 | 0.0725 |
| COMPACT_ATTENUATE | random | -0.1740 | 0.0209 | 0.4783 | 0.4710 |
| COMPACT_ATTENUATE | spatial | 0.9827 | 0.1732 | 0.1812 | 0.1449 |
| COMPACT_RESIDUAL | climate_profile | 0.2810 | -0.1076 | 0.1522 | 0.0580 |
| COMPACT_RESIDUAL | municipality | 0.2293 | 0.0000 | 0.1232 | 0.0942 |
| COMPACT_RESIDUAL | random | -0.4891 | -0.0071 | 0.4203 | 0.5725 |
| COMPACT_RESIDUAL | spatial | -6.6268 | 1.8288 | 0.1812 | 0.2971 |
| GEO_ATTENUATE | climate_profile | 0.3061 | 0.0000 | 0.0797 | 0.0580 |
| GEO_ATTENUATE | municipality | -0.0407 | 0.0000 | 0.0580 | 0.0725 |
| GEO_ATTENUATE | random | -0.1525 | 0.0251 | 0.4493 | 0.4710 |
| GEO_ATTENUATE | spatial | 1.1079 | 0.1640 | 0.1884 | 0.1522 |
| GEO_RESIDUAL | climate_profile | -0.5667 | 0.0661 | 0.4348 | 0.5652 |
| GEO_RESIDUAL | municipality | -1.6386 | 0.0000 | 0.1377 | 0.1522 |
| GEO_RESIDUAL | random | -0.4053 | -0.0048 | 0.4130 | 0.5870 |
| GEO_RESIDUAL | spatial | -5.5178 | 1.8288 | 0.1957 | 0.2826 |

## Integridad y límites

Replay máximo 0; 249560 exclusiones verificadas. Las referencias externas coinciden exactamente. Las calibraciones profundas pueden requerir respaldos por soporte territorial, registrados en deep_support_summary y audit/deep_support_logs.json. No se sustituyó ningún protocolo por aleatorio. El experimento no utiliza PRED59 ni ajusta modelo final138.

Los CSV y Excel incluyen análisis sin 171/015, omisiones de zonas, cuartiles, intraperfil, reglas por fold, residuos por parcela, predicciones base y ajustes. La interpretación y recomendación están en neighbor_signal_contrasts_conclusions.md.