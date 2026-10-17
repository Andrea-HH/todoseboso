# Señales adicionales: comparación de ubicación arquitectónica

Doce alternativas exploratorias congeladas antes del entrenamiento. ET = cambio EVI + TPI; ETN añade dinámica derivada NDVI. LOCAL amplía la Ridge local; CORRECTION amplía el corrector Elastic Net de residuos cross-fitted. CT3 y las entradas del gate físico permanecen iguales, con pesos aprendidos internamente.

## RMSE / R² por protocolo

| modelo | random | climate_profile | municipality | spatial |
| --- | --- | --- | --- | --- |
| J7_ET_LOCAL | 0.4917 / 0.6638 | 0.4876 / 0.6694 | 0.5842 / 0.5255 | 0.6816 / 0.3541 |
| J7_ET_CORRECTION | 0.4893 / 0.6670 | 0.4915 / 0.6641 | 0.5810 / 0.5307 | 0.6810 / 0.3553 |
| J7_ETN_LOCAL | 0.4933 / 0.6616 | 0.4872 / 0.6699 | 0.5841 / 0.5257 | 0.6813 / 0.3546 |
| J7_ETN_CORRECTION | 0.4904 / 0.6656 | 0.4905 / 0.6655 | 0.5809 / 0.5309 | 0.6810 / 0.3552 |
| E9_ET_LOCAL | 0.4924 / 0.6628 | 0.4886 / 0.6681 | 0.5839 / 0.5259 | 0.6819 / 0.3534 |
| E9_ET_CORRECTION | 0.4901 / 0.6660 | 0.4918 / 0.6637 | 0.5809 / 0.5308 | 0.6812 / 0.3547 |
| E9_ETN_LOCAL | 0.4938 / 0.6608 | 0.4881 / 0.6688 | 0.5838 / 0.5261 | 0.6816 / 0.3540 |
| E9_ETN_CORRECTION | 0.4911 / 0.6646 | 0.4909 / 0.6649 | 0.5808 / 0.5310 | 0.6812 / 0.3547 |
| E10_ET_LOCAL | 0.4920 / 0.6633 | 0.4859 / 0.6717 | 0.5811 / 0.5305 | 0.6853 / 0.3470 |
| E10_ET_CORRECTION | 0.4892 / 0.6672 | 0.4899 / 0.6663 | 0.5810 / 0.5307 | 0.6840 / 0.3495 |
| E10_ETN_LOCAL | 0.4932 / 0.6617 | 0.4853 / 0.6726 | 0.5811 / 0.5305 | 0.6849 / 0.3478 |
| E10_ETN_CORRECTION | 0.4902 / 0.6658 | 0.4893 / 0.6672 | 0.5807 / 0.5312 | 0.6840 / 0.3495 |
| J7_BOTH | 0.4864 / 0.6709 | 0.4890 / 0.6675 | 0.5808 / 0.5309 | 0.6808 / 0.3556 |
| DROP_SOIL | 0.4874 / 0.6696 | 0.4897 / 0.6666 | 0.5807 / 0.5311 | 0.6811 / 0.3550 |
| DROP_HISTORY_WATER | 0.4870 / 0.6701 | 0.4871 / 0.6702 | 0.5811 / 0.5306 | 0.6840 / 0.3494 |
| CT3 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| LOCAL04D | 0.4930 / 0.6619 | 0.5031 / 0.6481 | 0.7602 / 0.1964 | 0.9794 / -0.3337 |

## Comparaciones frente a la referencia: cambio RMSE e incertidumbre

| experiment | reference | contrast | protocol | delta_rmse | low95 | high95 | p_mse_signflip | n_clusters | exact_sign_enumeration | n_sign_assignments | p_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J7_ET_LOCAL | J7_BOTH | reference | climate_profile | -0.0014 | -0.0035 | 0.0002 | 0.1327 | 43 | False | 20000 | 1.0000 |
| J7_ET_CORRECTION | J7_BOTH | reference | climate_profile | 0.0025 | -0.0013 | 0.0063 | 0.3035 | 43 | False | 20000 | 1.0000 |
| J7_ETN_LOCAL | J7_BOTH | reference | climate_profile | -0.0018 | -0.0045 | 0.0000 | 0.0794 | 43 | False | 20000 | 1.0000 |
| J7_ETN_CORRECTION | J7_BOTH | reference | climate_profile | 0.0014 | -0.0033 | 0.0063 | 0.6286 | 43 | False | 20000 | 1.0000 |
| E9_ET_LOCAL | DROP_SOIL | reference | climate_profile | -0.0011 | -0.0020 | 0.0001 | 0.1085 | 43 | False | 20000 | 1.0000 |
| E9_ET_CORRECTION | DROP_SOIL | reference | climate_profile | 0.0021 | -0.0013 | 0.0060 | 0.3060 | 43 | False | 20000 | 1.0000 |
| E9_ETN_LOCAL | DROP_SOIL | reference | climate_profile | -0.0016 | -0.0037 | -0.0003 | 0.0429 | 43 | False | 20000 | 1.0000 |
| E9_ETN_CORRECTION | DROP_SOIL | reference | climate_profile | 0.0012 | -0.0031 | 0.0057 | 0.6797 | 43 | False | 20000 | 1.0000 |
| E10_ET_LOCAL | DROP_HISTORY_WATER | reference | climate_profile | -0.0012 | -0.0020 | 0.0000 | 0.0890 | 43 | False | 20000 | 1.0000 |
| E10_ET_CORRECTION | DROP_HISTORY_WATER | reference | climate_profile | 0.0029 | -0.0005 | 0.0065 | 0.2106 | 43 | False | 20000 | 1.0000 |
| E10_ETN_LOCAL | DROP_HISTORY_WATER | reference | climate_profile | -0.0018 | -0.0046 | 0.0001 | 0.0876 | 43 | False | 20000 | 1.0000 |
| E10_ETN_CORRECTION | DROP_HISTORY_WATER | reference | climate_profile | 0.0022 | -0.0018 | 0.0065 | 0.3425 | 43 | False | 20000 | 1.0000 |
| J7_ET_LOCAL | J7_BOTH | reference | municipality | 0.0033 | -0.0002 | 0.0096 | 0.2656 | 9 | True | 512 | 1.0000 |
| J7_ET_CORRECTION | J7_BOTH | reference | municipality | 0.0002 | -0.0062 | 0.0071 | 0.9531 | 9 | True | 512 | 1.0000 |
| J7_ETN_LOCAL | J7_BOTH | reference | municipality | 0.0032 | -0.0002 | 0.0091 | 0.2734 | 9 | True | 512 | 1.0000 |
| J7_ETN_CORRECTION | J7_BOTH | reference | municipality | 0.0000 | -0.0072 | 0.0076 | 0.9766 | 9 | True | 512 | 1.0000 |
| E9_ET_LOCAL | DROP_SOIL | reference | municipality | 0.0032 | -0.0002 | 0.0089 | 0.2578 | 9 | True | 512 | 1.0000 |
| E9_ET_CORRECTION | DROP_SOIL | reference | municipality | 0.0002 | -0.0062 | 0.0074 | 0.9688 | 9 | True | 512 | 1.0000 |
| E9_ETN_LOCAL | DROP_SOIL | reference | municipality | 0.0031 | -0.0002 | 0.0084 | 0.2734 | 9 | True | 512 | 1.0000 |
| E9_ETN_CORRECTION | DROP_SOIL | reference | municipality | 0.0001 | -0.0071 | 0.0078 | 0.9688 | 9 | True | 512 | 1.0000 |
| E10_ET_LOCAL | DROP_HISTORY_WATER | reference | municipality | 0.0000 | -0.0006 | 0.0003 | 0.8906 | 9 | True | 512 | 1.0000 |
| E10_ET_CORRECTION | DROP_HISTORY_WATER | reference | municipality | -0.0001 | -0.0033 | 0.0032 | 0.6094 | 9 | True | 512 | 1.0000 |
| E10_ETN_LOCAL | DROP_HISTORY_WATER | reference | municipality | 0.0001 | -0.0006 | 0.0005 | 0.6484 | 9 | True | 512 | 1.0000 |
| E10_ETN_CORRECTION | DROP_HISTORY_WATER | reference | municipality | -0.0004 | -0.0043 | 0.0029 | 0.5391 | 9 | True | 512 | 1.0000 |
| J7_ET_LOCAL | J7_BOTH | reference | random | 0.0052 | 0.0015 | 0.0081 | 0.0428 | 43 | False | 20000 | 1.0000 |
| J7_ET_CORRECTION | J7_BOTH | reference | random | 0.0029 | 0.0005 | 0.0064 | 0.0501 | 43 | False | 20000 | 1.0000 |
| J7_ETN_LOCAL | J7_BOTH | reference | random | 0.0069 | 0.0011 | 0.0101 | 0.0687 | 43 | False | 20000 | 1.0000 |
| J7_ETN_CORRECTION | J7_BOTH | reference | random | 0.0040 | 0.0007 | 0.0082 | 0.0521 | 43 | False | 20000 | 1.0000 |
| E9_ET_LOCAL | DROP_SOIL | reference | random | 0.0050 | 0.0015 | 0.0079 | 0.0384 | 43 | False | 20000 | 1.0000 |
| E9_ET_CORRECTION | DROP_SOIL | reference | random | 0.0027 | 0.0004 | 0.0062 | 0.0463 | 43 | False | 20000 | 1.0000 |
| E9_ETN_LOCAL | DROP_SOIL | reference | random | 0.0064 | 0.0011 | 0.0096 | 0.0678 | 43 | False | 20000 | 1.0000 |
| E9_ETN_CORRECTION | DROP_SOIL | reference | random | 0.0037 | 0.0006 | 0.0080 | 0.0496 | 43 | False | 20000 | 1.0000 |
| E10_ET_LOCAL | DROP_HISTORY_WATER | reference | random | 0.0050 | 0.0012 | 0.0082 | 0.0460 | 43 | False | 20000 | 1.0000 |
| E10_ET_CORRECTION | DROP_HISTORY_WATER | reference | random | 0.0021 | 0.0000 | 0.0058 | 0.0767 | 43 | False | 20000 | 1.0000 |
| E10_ETN_LOCAL | DROP_HISTORY_WATER | reference | random | 0.0062 | 0.0006 | 0.0093 | 0.0833 | 43 | False | 20000 | 1.0000 |
| E10_ETN_CORRECTION | DROP_HISTORY_WATER | reference | random | 0.0031 | 0.0003 | 0.0074 | 0.0604 | 43 | False | 20000 | 1.0000 |
| J7_ET_LOCAL | J7_BOTH | reference | spatial | 0.0008 | -0.0007 | 0.0017 | 0.3125 | 5 | True | 32 | 1.0000 |
| J7_ET_CORRECTION | J7_BOTH | reference | spatial | 0.0002 | -0.0019 | 0.0015 | 0.9375 | 5 | True | 32 | 1.0000 |
| J7_ETN_LOCAL | J7_BOTH | reference | spatial | 0.0005 | -0.0011 | 0.0014 | 0.3750 | 5 | True | 32 | 1.0000 |
| J7_ETN_CORRECTION | J7_BOTH | reference | spatial | 0.0002 | -0.0017 | 0.0017 | 0.8125 | 5 | True | 32 | 1.0000 |
| E9_ET_LOCAL | DROP_SOIL | reference | spatial | 0.0008 | -0.0006 | 0.0017 | 0.3125 | 5 | True | 32 | 1.0000 |
| E9_ET_CORRECTION | DROP_SOIL | reference | spatial | 0.0001 | -0.0019 | 0.0014 | 0.9375 | 5 | True | 32 | 1.0000 |
| E9_ETN_LOCAL | DROP_SOIL | reference | spatial | 0.0005 | -0.0010 | 0.0014 | 0.3750 | 5 | True | 32 | 1.0000 |
| E9_ETN_CORRECTION | DROP_SOIL | reference | spatial | 0.0001 | -0.0017 | 0.0016 | 0.9375 | 5 | True | 32 | 1.0000 |
| E10_ET_LOCAL | DROP_HISTORY_WATER | reference | spatial | 0.0013 | -0.0007 | 0.0025 | 0.3125 | 5 | True | 32 | 1.0000 |
| E10_ET_CORRECTION | DROP_HISTORY_WATER | reference | spatial | -0.0000 | -0.0019 | 0.0019 | 0.9375 | 5 | True | 32 | 1.0000 |
| E10_ETN_LOCAL | DROP_HISTORY_WATER | reference | spatial | 0.0009 | -0.0011 | 0.0020 | 0.3125 | 5 | True | 32 | 1.0000 |
| E10_ETN_CORRECTION | DROP_HISTORY_WATER | reference | spatial | -0.0000 | -0.0017 | 0.0021 | 0.9375 | 5 | True | 32 | 1.0000 |

## ¿Dónde encajan mejor? LOCAL menos CORRECTION; negativo favorece LOCAL

| experiment | reference | contrast | protocol | delta_rmse | low95 | high95 | p_mse_signflip | n_clusters | exact_sign_enumeration | n_sign_assignments | p_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J7_ET_LOCAL | J7_ET_CORRECTION | placement | climate_profile | -0.0039 | -0.0079 | -0.0003 | 0.0655 | 43 | False | 20000 | 1.0000 |
| J7_ETN_LOCAL | J7_ETN_CORRECTION | placement | climate_profile | -0.0032 | -0.0086 | 0.0017 | 0.2819 | 43 | False | 20000 | 1.0000 |
| E9_ET_LOCAL | E9_ET_CORRECTION | placement | climate_profile | -0.0032 | -0.0068 | 0.0000 | 0.1057 | 43 | False | 20000 | 1.0000 |
| E9_ETN_LOCAL | E9_ETN_CORRECTION | placement | climate_profile | -0.0028 | -0.0078 | 0.0018 | 0.2932 | 43 | False | 20000 | 1.0000 |
| E10_ET_LOCAL | E10_ET_CORRECTION | placement | climate_profile | -0.0040 | -0.0074 | -0.0008 | 0.0198 | 43 | False | 20000 | 1.0000 |
| E10_ETN_LOCAL | E10_ETN_CORRECTION | placement | climate_profile | -0.0040 | -0.0089 | 0.0001 | 0.1076 | 43 | False | 20000 | 1.0000 |
| J7_ET_LOCAL | J7_ET_CORRECTION | placement | municipality | 0.0032 | -0.0031 | 0.0154 | 0.6719 | 9 | True | 512 | 1.0000 |
| J7_ETN_LOCAL | J7_ETN_CORRECTION | placement | municipality | 0.0032 | -0.0033 | 0.0158 | 0.5938 | 9 | True | 512 | 1.0000 |
| E9_ET_LOCAL | E9_ET_CORRECTION | placement | municipality | 0.0030 | -0.0031 | 0.0147 | 0.6484 | 9 | True | 512 | 1.0000 |
| E9_ETN_LOCAL | E9_ETN_CORRECTION | placement | municipality | 0.0030 | -0.0033 | 0.0150 | 0.5625 | 9 | True | 512 | 1.0000 |
| E10_ET_LOCAL | E10_ET_CORRECTION | placement | municipality | 0.0001 | -0.0031 | 0.0031 | 0.7812 | 9 | True | 512 | 1.0000 |
| E10_ETN_LOCAL | E10_ETN_CORRECTION | placement | municipality | 0.0004 | -0.0026 | 0.0041 | 0.6016 | 9 | True | 512 | 1.0000 |
| J7_ET_LOCAL | J7_ET_CORRECTION | placement | random | 0.0023 | -0.0019 | 0.0047 | 0.3065 | 43 | False | 20000 | 1.0000 |
| J7_ETN_LOCAL | J7_ETN_CORRECTION | placement | random | 0.0029 | -0.0032 | 0.0056 | 0.3295 | 43 | False | 20000 | 1.0000 |
| E9_ET_LOCAL | E9_ET_CORRECTION | placement | random | 0.0023 | -0.0018 | 0.0045 | 0.2898 | 43 | False | 20000 | 1.0000 |
| E9_ETN_LOCAL | E9_ETN_CORRECTION | placement | random | 0.0027 | -0.0034 | 0.0054 | 0.3479 | 43 | False | 20000 | 1.0000 |
| E10_ET_LOCAL | E10_ET_CORRECTION | placement | random | 0.0029 | -0.0017 | 0.0054 | 0.2760 | 43 | False | 20000 | 1.0000 |
| E10_ETN_LOCAL | E10_ETN_CORRECTION | placement | random | 0.0030 | -0.0035 | 0.0060 | 0.3571 | 43 | False | 20000 | 1.0000 |
| J7_ET_LOCAL | J7_ET_CORRECTION | placement | spatial | 0.0006 | -0.0001 | 0.0013 | 0.3750 | 5 | True | 32 | 1.0000 |
| J7_ETN_LOCAL | J7_ETN_CORRECTION | placement | spatial | 0.0003 | -0.0004 | 0.0008 | 0.5000 | 5 | True | 32 | 1.0000 |
| E9_ET_LOCAL | E9_ET_CORRECTION | placement | spatial | 0.0007 | 0.0001 | 0.0014 | 0.1250 | 5 | True | 32 | 1.0000 |
| E9_ETN_LOCAL | E9_ETN_CORRECTION | placement | spatial | 0.0004 | -0.0002 | 0.0008 | 0.3750 | 5 | True | 32 | 1.0000 |
| E10_ET_LOCAL | E10_ET_CORRECTION | placement | spatial | 0.0013 | -0.0003 | 0.0025 | 0.3750 | 5 | True | 32 | 1.0000 |
| E10_ETN_LOCAL | E10_ETN_CORRECTION | placement | spatial | 0.0009 | -0.0004 | 0.0022 | 0.5000 | 5 | True | 32 | 1.0000 |

## ¿Ayuda añadir la tercera señal? ETN menos ET; negativo favorece ETN

| experiment | reference | contrast | protocol | delta_rmse | low95 | high95 | p_mse_signflip | n_clusters | exact_sign_enumeration | n_sign_assignments | p_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J7_ETN_LOCAL | J7_ET_LOCAL | third_signal | climate_profile | -0.0003 | -0.0018 | 0.0004 | 0.4186 | 43 | False | 20000 | 1.0000 |
| J7_ETN_CORRECTION | J7_ET_CORRECTION | third_signal | climate_profile | -0.0010 | -0.0025 | 0.0005 | 0.2537 | 43 | False | 20000 | 1.0000 |
| E9_ETN_LOCAL | E9_ET_LOCAL | third_signal | climate_profile | -0.0005 | -0.0022 | 0.0003 | 0.2726 | 43 | False | 20000 | 1.0000 |
| E9_ETN_CORRECTION | E9_ET_CORRECTION | third_signal | climate_profile | -0.0009 | -0.0024 | 0.0006 | 0.3011 | 43 | False | 20000 | 1.0000 |
| E10_ETN_LOCAL | E10_ET_LOCAL | third_signal | climate_profile | -0.0006 | -0.0031 | 0.0008 | 0.4070 | 43 | False | 20000 | 1.0000 |
| E10_ETN_CORRECTION | E10_ET_CORRECTION | third_signal | climate_profile | -0.0007 | -0.0017 | 0.0007 | 0.3279 | 43 | False | 20000 | 1.0000 |
| J7_ETN_LOCAL | J7_ET_LOCAL | third_signal | municipality | -0.0001 | -0.0006 | 0.0002 | 0.7031 | 9 | True | 512 | 1.0000 |
| J7_ETN_CORRECTION | J7_ET_CORRECTION | third_signal | municipality | -0.0001 | -0.0011 | 0.0005 | 0.5781 | 9 | True | 512 | 1.0000 |
| E9_ETN_LOCAL | E9_ET_LOCAL | third_signal | municipality | -0.0001 | -0.0006 | 0.0002 | 0.7031 | 9 | True | 512 | 1.0000 |
| E9_ETN_CORRECTION | E9_ET_CORRECTION | third_signal | municipality | -0.0001 | -0.0010 | 0.0005 | 0.5859 | 9 | True | 512 | 1.0000 |
| E10_ETN_LOCAL | E10_ET_LOCAL | third_signal | municipality | 0.0000 | -0.0001 | 0.0002 | 0.7031 | 9 | True | 512 | 1.0000 |
| E10_ETN_CORRECTION | E10_ET_CORRECTION | third_signal | municipality | -0.0003 | -0.0011 | -0.0000 | 0.0859 | 9 | True | 512 | 1.0000 |
| J7_ETN_LOCAL | J7_ET_LOCAL | third_signal | random | 0.0016 | -0.0007 | 0.0032 | 0.2692 | 43 | False | 20000 | 1.0000 |
| J7_ETN_CORRECTION | J7_ET_CORRECTION | third_signal | random | 0.0011 | -0.0002 | 0.0021 | 0.1219 | 43 | False | 20000 | 1.0000 |
| E9_ETN_LOCAL | E9_ET_LOCAL | third_signal | random | 0.0014 | -0.0008 | 0.0030 | 0.3250 | 43 | False | 20000 | 1.0000 |
| E9_ETN_CORRECTION | E9_ET_CORRECTION | third_signal | random | 0.0010 | -0.0002 | 0.0022 | 0.1398 | 43 | False | 20000 | 1.0000 |
| E10_ETN_LOCAL | E10_ET_LOCAL | third_signal | random | 0.0012 | -0.0010 | 0.0025 | 0.3697 | 43 | False | 20000 | 1.0000 |
| E10_ETN_CORRECTION | E10_ET_CORRECTION | third_signal | random | 0.0010 | -0.0002 | 0.0021 | 0.1391 | 43 | False | 20000 | 1.0000 |
| J7_ETN_LOCAL | J7_ET_LOCAL | third_signal | spatial | -0.0003 | -0.0005 | -0.0001 | 0.0625 | 5 | True | 32 | 1.0000 |
| J7_ETN_CORRECTION | J7_ET_CORRECTION | third_signal | spatial | 0.0000 | -0.0003 | 0.0003 | 0.9375 | 5 | True | 32 | 1.0000 |
| E9_ETN_LOCAL | E9_ET_LOCAL | third_signal | spatial | -0.0003 | -0.0005 | -0.0000 | 0.0625 | 5 | True | 32 | 1.0000 |
| E9_ETN_CORRECTION | E9_ET_CORRECTION | third_signal | spatial | 0.0000 | -0.0003 | 0.0004 | 1.0000 | 5 | True | 32 | 1.0000 |
| E10_ETN_LOCAL | E10_ET_LOCAL | third_signal | spatial | -0.0004 | -0.0007 | 0.0000 | 0.3125 | 5 | True | 32 | 1.0000 |
| E10_ETN_CORRECTION | E10_ET_CORRECTION | third_signal | spatial | -0.0000 | -0.0003 | 0.0003 | 0.8750 | 5 | True | 32 | 1.0000 |

## Sensibilidad sin 171 y 015, sin reajuste

| experiment | protocol | rmse | mae | r2 | bias |
| --- | --- | --- | --- | --- | --- |
| CT3 | climate_profile | 0.4639 | 0.3676 | 0.6893 | -0.0250 |
| CT3 | municipality | 0.5398 | 0.4396 | 0.5793 | -0.0481 |
| CT3 | random | 0.4483 | 0.3497 | 0.7098 | -0.0303 |
| CT3 | spatial | 0.6398 | 0.5092 | 0.4090 | 0.1647 |
| DROP_HISTORY_WATER | climate_profile | 0.4210 | 0.3177 | 0.7441 | -0.0394 |
| DROP_HISTORY_WATER | municipality | 0.5396 | 0.4404 | 0.5796 | -0.0488 |
| DROP_HISTORY_WATER | random | 0.4183 | 0.3223 | 0.7472 | -0.0429 |
| DROP_HISTORY_WATER | spatial | 0.6431 | 0.5106 | 0.4028 | 0.2788 |
| DROP_SOIL | climate_profile | 0.4240 | 0.3200 | 0.7404 | -0.0410 |
| DROP_SOIL | municipality | 0.5392 | 0.4395 | 0.5802 | -0.0487 |
| DROP_SOIL | random | 0.4178 | 0.3218 | 0.7478 | -0.0422 |
| DROP_SOIL | spatial | 0.6400 | 0.5078 | 0.4085 | 0.2672 |
| E10_ETN_CORRECTION | climate_profile | 0.4220 | 0.3201 | 0.7429 | -0.0352 |
| E10_ETN_CORRECTION | municipality | 0.5392 | 0.4397 | 0.5803 | -0.0475 |
| E10_ETN_CORRECTION | random | 0.4210 | 0.3227 | 0.7440 | -0.0409 |
| E10_ETN_CORRECTION | spatial | 0.6431 | 0.5094 | 0.4029 | 0.2793 |
| E10_ETN_LOCAL | climate_profile | 0.4192 | 0.3156 | 0.7462 | -0.0411 |
| E10_ETN_LOCAL | municipality | 0.5396 | 0.4404 | 0.5795 | -0.0485 |
| E10_ETN_LOCAL | random | 0.4215 | 0.3223 | 0.7434 | -0.0430 |
| E10_ETN_LOCAL | spatial | 0.6435 | 0.5102 | 0.4022 | 0.2804 |
| E10_ET_CORRECTION | climate_profile | 0.4230 | 0.3194 | 0.7417 | -0.0340 |
| E10_ET_CORRECTION | municipality | 0.5395 | 0.4401 | 0.5798 | -0.0472 |
| E10_ET_CORRECTION | random | 0.4199 | 0.3222 | 0.7453 | -0.0423 |
| E10_ET_CORRECTION | spatial | 0.6431 | 0.5095 | 0.4029 | 0.2801 |
| E10_ET_LOCAL | climate_profile | 0.4199 | 0.3168 | 0.7454 | -0.0401 |
| E10_ET_LOCAL | municipality | 0.5396 | 0.4404 | 0.5796 | -0.0485 |
| E10_ET_LOCAL | random | 0.4207 | 0.3220 | 0.7443 | -0.0425 |
| E10_ET_LOCAL | spatial | 0.6439 | 0.5110 | 0.4013 | 0.2814 |
| E9_ETN_CORRECTION | climate_profile | 0.4239 | 0.3217 | 0.7405 | -0.0371 |
| E9_ETN_CORRECTION | municipality | 0.5393 | 0.4396 | 0.5801 | -0.0471 |
| E9_ETN_CORRECTION | random | 0.4215 | 0.3229 | 0.7434 | -0.0403 |
| E9_ETN_CORRECTION | spatial | 0.6401 | 0.5063 | 0.4084 | 0.2682 |
| E9_ETN_LOCAL | climate_profile | 0.4225 | 0.3185 | 0.7423 | -0.0425 |
| E9_ETN_LOCAL | municipality | 0.5426 | 0.4423 | 0.5750 | -0.0462 |
| E9_ETN_LOCAL | random | 0.4219 | 0.3226 | 0.7429 | -0.0428 |
| E9_ETN_LOCAL | spatial | 0.6401 | 0.5072 | 0.4085 | 0.2687 |
| E9_ET_CORRECTION | climate_profile | 0.4254 | 0.3212 | 0.7387 | -0.0345 |
| E9_ET_CORRECTION | municipality | 0.5394 | 0.4397 | 0.5799 | -0.0469 |
| E9_ET_CORRECTION | random | 0.4203 | 0.3224 | 0.7448 | -0.0416 |
| E9_ET_CORRECTION | spatial | 0.6402 | 0.5063 | 0.4083 | 0.2692 |
| E9_ET_LOCAL | climate_profile | 0.4230 | 0.3191 | 0.7417 | -0.0419 |
| E9_ET_LOCAL | municipality | 0.5427 | 0.4423 | 0.5748 | -0.0460 |
| E9_ET_LOCAL | random | 0.4207 | 0.3221 | 0.7443 | -0.0419 |
| E9_ET_LOCAL | spatial | 0.6404 | 0.5080 | 0.4078 | 0.2695 |
| J7_BOTH | climate_profile | 0.4233 | 0.3193 | 0.7413 | -0.0443 |
| J7_BOTH | municipality | 0.5393 | 0.4397 | 0.5800 | -0.0483 |
| J7_BOTH | random | 0.4169 | 0.3209 | 0.7489 | -0.0434 |
| J7_BOTH | spatial | 0.6396 | 0.5069 | 0.4093 | 0.2656 |
| J7_ETN_CORRECTION | climate_profile | 0.4233 | 0.3209 | 0.7413 | -0.0404 |
| J7_ETN_CORRECTION | municipality | 0.5394 | 0.4396 | 0.5800 | -0.0469 |
| J7_ETN_CORRECTION | random | 0.4207 | 0.3219 | 0.7444 | -0.0416 |
| J7_ETN_CORRECTION | spatial | 0.6398 | 0.5054 | 0.4091 | 0.2667 |
| J7_ETN_LOCAL | climate_profile | 0.4216 | 0.3173 | 0.7434 | -0.0465 |
| J7_ETN_LOCAL | municipality | 0.5429 | 0.4425 | 0.5745 | -0.0457 |
| J7_ETN_LOCAL | random | 0.4213 | 0.3218 | 0.7436 | -0.0437 |
| J7_ETN_LOCAL | spatial | 0.6397 | 0.5062 | 0.4092 | 0.2671 |
| J7_ET_CORRECTION | climate_profile | 0.4248 | 0.3204 | 0.7394 | -0.0384 |
| J7_ET_CORRECTION | municipality | 0.5395 | 0.4398 | 0.5797 | -0.0466 |
| J7_ET_CORRECTION | random | 0.4195 | 0.3214 | 0.7458 | -0.0429 |
| J7_ET_CORRECTION | spatial | 0.6398 | 0.5055 | 0.4090 | 0.2676 |
| J7_ET_LOCAL | climate_profile | 0.4219 | 0.3176 | 0.7430 | -0.0455 |
| J7_ET_LOCAL | municipality | 0.5430 | 0.4426 | 0.5743 | -0.0455 |
| J7_ET_LOCAL | random | 0.4199 | 0.3211 | 0.7453 | -0.0428 |
| J7_ET_LOCAL | spatial | 0.6400 | 0.5070 | 0.4086 | 0.2679 |
| LOCAL04D | climate_profile | 0.4405 | 0.3230 | 0.7198 | -0.0190 |
| LOCAL04D | municipality | 0.7327 | 0.5811 | 0.2249 | 0.0799 |
| LOCAL04D | random | 0.4241 | 0.3265 | 0.7402 | -0.0405 |
| LOCAL04D | spatial | 0.9535 | 0.7240 | -0.3126 | 0.4474 |

## Distribución de ganancias y contribución de los dos casos

| experiment | reference | protocol | total_sse_gain | cases_171_015_sse_gain | remaining_sse_gain | fraction_improved | fraction_worsened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E10_ETN_CORRECTION | DROP_HISTORY_WATER | climate_profile | -0.2947 | -0.1786 | -0.1161 | 0.4638 | 0.5362 |
| E10_ETN_CORRECTION | DROP_HISTORY_WATER | municipality | 0.0597 | 0.0000 | 0.0597 | 0.1957 | 0.1667 |
| E10_ETN_CORRECTION | DROP_HISTORY_WATER | random | -0.4212 | -0.1166 | -0.3045 | 0.5072 | 0.4928 |
| E10_ETN_CORRECTION | DROP_HISTORY_WATER | spatial | 0.0056 | -0.0016 | 0.0071 | 0.4275 | 0.3116 |
| E10_ETN_LOCAL | DROP_HISTORY_WATER | climate_profile | 0.2415 | 0.0467 | 0.1948 | 0.5507 | 0.4493 |
| E10_ETN_LOCAL | DROP_HISTORY_WATER | municipality | -0.0095 | 0.0000 | -0.0095 | 0.1304 | 0.2319 |
| E10_ETN_LOCAL | DROP_HISTORY_WATER | random | -0.8315 | -0.4708 | -0.3607 | 0.4928 | 0.5072 |
| E10_ETN_LOCAL | DROP_HISTORY_WATER | spatial | -0.1626 | -0.0991 | -0.0634 | 0.2681 | 0.4710 |
| E10_ET_CORRECTION | DROP_HISTORY_WATER | climate_profile | -0.3855 | -0.1503 | -0.2352 | 0.4928 | 0.5072 |
| E10_ET_CORRECTION | DROP_HISTORY_WATER | municipality | 0.0121 | 0.0000 | 0.0121 | 0.1812 | 0.1812 |
| E10_ET_CORRECTION | DROP_HISTORY_WATER | random | -0.2870 | -0.1085 | -0.1785 | 0.5507 | 0.4493 |
| E10_ET_CORRECTION | DROP_HISTORY_WATER | spatial | 0.0051 | 0.0016 | 0.0036 | 0.5217 | 0.2681 |
| E10_ET_LOCAL | DROP_HISTORY_WATER | climate_profile | 0.1546 | 0.0366 | 0.1180 | 0.4783 | 0.5217 |
| E10_ET_LOCAL | DROP_HISTORY_WATER | municipality | -0.0029 | 0.0000 | -0.0029 | 0.1232 | 0.2391 |
| E10_ET_LOCAL | DROP_HISTORY_WATER | random | -0.6725 | -0.3984 | -0.2741 | 0.4493 | 0.5507 |
| E10_ET_LOCAL | DROP_HISTORY_WATER | spatial | -0.2378 | -0.0922 | -0.1456 | 0.2826 | 0.4710 |
| E9_ETN_CORRECTION | DROP_SOIL | climate_profile | -0.1626 | -0.1730 | 0.0103 | 0.4928 | 0.5072 |
| E9_ETN_CORRECTION | DROP_SOIL | municipality | -0.0154 | 0.0000 | -0.0154 | 0.1884 | 0.1739 |
| E9_ETN_CORRECTION | DROP_SOIL | random | -0.5015 | -0.0863 | -0.4151 | 0.5145 | 0.4855 |
| E9_ETN_CORRECTION | DROP_SOIL | spatial | -0.0243 | -0.0071 | -0.0172 | 0.3406 | 0.4493 |
| E9_ETN_LOCAL | DROP_SOIL | climate_profile | 0.2184 | 0.0414 | 0.1770 | 0.5290 | 0.4710 |
| E9_ETN_LOCAL | DROP_SOIL | municipality | -0.4983 | 0.0000 | -0.4983 | 0.1232 | 0.3478 |
| E9_ETN_LOCAL | DROP_SOIL | random | -0.8704 | -0.4112 | -0.4591 | 0.4710 | 0.5290 |
| E9_ETN_LOCAL | DROP_SOIL | spatial | -0.0961 | -0.0898 | -0.0063 | 0.2754 | 0.4638 |
| E9_ET_CORRECTION | DROP_SOIL | climate_profile | -0.2867 | -0.1236 | -0.1631 | 0.4855 | 0.5145 |
| E9_ET_CORRECTION | DROP_SOIL | municipality | -0.0330 | 0.0000 | -0.0330 | 0.1812 | 0.1812 |
| E9_ET_CORRECTION | DROP_SOIL | random | -0.3636 | -0.0811 | -0.2825 | 0.5217 | 0.4783 |
| E9_ET_CORRECTION | DROP_SOIL | spatial | -0.0243 | -0.0027 | -0.0216 | 0.3768 | 0.4130 |
| E9_ET_LOCAL | DROP_SOIL | climate_profile | 0.1510 | 0.0322 | 0.1188 | 0.4855 | 0.5145 |
| E9_ET_LOCAL | DROP_SOIL | municipality | -0.5150 | 0.0000 | -0.5150 | 0.1232 | 0.3478 |
| E9_ET_LOCAL | DROP_SOIL | random | -0.6746 | -0.3481 | -0.3265 | 0.4710 | 0.5290 |
| E9_ET_LOCAL | DROP_SOIL | spatial | -0.1526 | -0.0863 | -0.0662 | 0.2971 | 0.4420 |
| J7_ETN_CORRECTION | J7_BOTH | climate_profile | -0.1928 | -0.1924 | -0.0004 | 0.5000 | 0.5000 |
| J7_ETN_CORRECTION | J7_BOTH | municipality | -0.0036 | 0.0000 | -0.0036 | 0.1884 | 0.1739 |
| J7_ETN_CORRECTION | J7_BOTH | random | -0.5339 | -0.1060 | -0.4279 | 0.5145 | 0.4855 |
| J7_ETN_CORRECTION | J7_BOTH | spatial | -0.0321 | -0.0095 | -0.0226 | 0.2971 | 0.4420 |
| J7_ETN_LOCAL | J7_BOTH | climate_profile | 0.2412 | 0.0484 | 0.1928 | 0.5362 | 0.4638 |
| J7_ETN_LOCAL | J7_BOTH | municipality | -0.5175 | 0.0000 | -0.5175 | 0.1232 | 0.3478 |
| J7_ETN_LOCAL | J7_BOTH | random | -0.9258 | -0.4273 | -0.4986 | 0.5000 | 0.5000 |
| J7_ETN_LOCAL | J7_BOTH | spatial | -0.0914 | -0.0841 | -0.0073 | 0.2826 | 0.4565 |
| J7_ET_CORRECTION | J7_BOTH | climate_profile | -0.3335 | -0.1572 | -0.1763 | 0.5000 | 0.5000 |
| J7_ET_CORRECTION | J7_BOTH | municipality | -0.0245 | 0.0000 | -0.0245 | 0.1812 | 0.1812 |
| J7_ET_CORRECTION | J7_BOTH | random | -0.3911 | -0.0977 | -0.2933 | 0.5507 | 0.4493 |
| J7_ET_CORRECTION | J7_BOTH | spatial | -0.0303 | -0.0060 | -0.0243 | 0.3768 | 0.4130 |
| J7_ET_LOCAL | J7_BOTH | climate_profile | 0.1942 | 0.0363 | 0.1579 | 0.5072 | 0.4928 |
| J7_ET_LOCAL | J7_BOTH | municipality | -0.5339 | 0.0000 | -0.5339 | 0.1304 | 0.3406 |
| J7_ET_LOCAL | J7_BOTH | random | -0.7063 | -0.3656 | -0.3407 | 0.4928 | 0.5072 |
| J7_ET_LOCAL | J7_BOTH | spatial | -0.1466 | -0.0824 | -0.0643 | 0.2971 | 0.4420 |

## Lectura y límites

Los parámetros y la ubicación no se seleccionaron usando el fold externo. Las características se propusieron tras examinar residuos de estos mismos datos: ninguna comparación es confirmación independiente. Holm se aplica conjuntamente a 96 contrastes. La ausencia de significancia no demuestra equivalencia. Los CSV/Excel contienen regiones, bloques, cuartiles, errores intraperfil, omisión de zonas y residuos por parcela; branch_metrics separa lo que aprende el experto de lo que conserva la mezcla. Los coeficientes del corrector están en escala estandarizada, varían entre folds y no representan efectos causales. Un peso pequeño del experto puede amortiguar tanto mejoras como deterioros. No se ajustó modelo final ni se usaron targets de PRED59.

La recomendación interpretativa se completa en la respuesta y en el documento de conclusiones tras revisar los resultados; las tablas no declaran un ganador automáticamente.