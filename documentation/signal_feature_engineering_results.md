# Ingeniería de señales: resultados exploratorios

H_RAW18 vs H_ENG6: componentes históricos vs anomalías propias. T_RAW21 vs T_ENG6: señal mensual vs resúmenes temporales. P_RAW4 vs P_ENG8: padres vs padres e interacciones. SHIFT: recalibración de intercepto sin señales. Correctores EN con ajuste máximo ±.25 t/ha, selección anidada y referencias externas exactas.

## RMSE / R²

| modelo | random | climate_profile | municipality | spatial |
| --- | --- | --- | --- | --- |
| CT3 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| J7_BOTH | 0.4864 / 0.6709 | 0.4890 / 0.6675 | 0.5808 / 0.5309 | 0.6808 / 0.3556 |
| CT3_H_RAW | 0.5128 / 0.6344 | 0.5259 / 0.6154 | 0.6056 / 0.4900 | 0.7109 / 0.2974 |
| CT3_H_ENG | 0.5131 / 0.6339 | 0.5313 / 0.6075 | 0.5784 / 0.5349 | 0.6839 / 0.3497 |
| CT3_T_RAW | 0.5148 / 0.6314 | 0.5226 / 0.6202 | 0.5988 / 0.5014 | 0.7007 / 0.3173 |
| CT3_T_ENG | 0.5129 / 0.6342 | 0.5209 / 0.6227 | 0.5808 / 0.5310 | 0.6839 / 0.3497 |
| CT3_P_RAW | 0.5121 / 0.6353 | 0.5235 / 0.6189 | 0.5787 / 0.5344 | 0.6656 / 0.3839 |
| CT3_P_ENG | 0.5130 / 0.6340 | 0.5274 / 0.6133 | 0.5793 / 0.5335 | 0.6737 / 0.3689 |
| CT3_SHIFT | 0.5115 / 0.6362 | 0.5226 / 0.6202 | 0.5784 / 0.5349 | 0.6839 / 0.3497 |
| J7_H_RAW | 0.4880 / 0.6689 | 0.5041 / 0.6466 | 0.5936 / 0.5101 | 0.6930 / 0.3323 |
| J7_H_ENG | 0.4872 / 0.6699 | 0.4909 / 0.6649 | 0.5774 / 0.5365 | 0.6929 / 0.3326 |
| J7_T_RAW | 0.4878 / 0.6690 | 0.4935 / 0.6614 | 0.6015 / 0.4970 | 0.6915 / 0.3352 |
| J7_T_ENG | 0.4869 / 0.6703 | 0.4906 / 0.6653 | 0.5803 / 0.5319 | 0.6842 / 0.3492 |
| J7_P_RAW | 0.4863 / 0.6711 | 0.4955 / 0.6586 | 0.5774 / 0.5365 | 0.6490 / 0.4143 |
| J7_P_ENG | 0.4864 / 0.6710 | 0.4972 / 0.6563 | 0.5810 / 0.5306 | 0.6605 / 0.3934 |
| J7_SHIFT | 0.4863 / 0.6712 | 0.4902 / 0.6659 | 0.5774 / 0.5365 | 0.6929 / 0.3326 |

## Métricas completas

| experiment | protocol | rmse | mae | r2 | bias | error_sd |
| --- | --- | --- | --- | --- | --- | --- |
| CT3 | climate_profile | 0.5206 | 0.3915 | 0.6232 | 0.0046 | 0.5206 |
| CT3 | municipality | 0.5813 | 0.4603 | 0.5302 | -0.0203 | 0.5809 |
| CT3 | random | 0.5116 | 0.3749 | 0.6361 | 0.0005 | 0.5115 |
| CT3 | spatial | 0.6788 | 0.5306 | 0.3594 | 0.1912 | 0.6513 |
| CT3_H_ENG | climate_profile | 0.5313 | 0.4093 | 0.6075 | -0.0055 | 0.5313 |
| CT3_H_ENG | municipality | 0.5784 | 0.4560 | 0.5349 | -0.0378 | 0.5771 |
| CT3_H_ENG | random | 0.5131 | 0.3775 | 0.6339 | 0.0002 | 0.5130 |
| CT3_H_ENG | spatial | 0.6839 | 0.5395 | 0.3497 | 0.1822 | 0.6592 |
| CT3_H_RAW | climate_profile | 0.5259 | 0.3924 | 0.6154 | 0.0089 | 0.5259 |
| CT3_H_RAW | municipality | 0.6056 | 0.4636 | 0.4900 | -0.0083 | 0.6056 |
| CT3_H_RAW | random | 0.5128 | 0.3757 | 0.6344 | 0.0010 | 0.5127 |
| CT3_H_RAW | spatial | 0.7109 | 0.5658 | 0.2974 | 0.1454 | 0.6958 |
| CT3_P_ENG | climate_profile | 0.5274 | 0.3958 | 0.6133 | 0.0112 | 0.5272 |
| CT3_P_ENG | municipality | 0.5793 | 0.4590 | 0.5335 | -0.0430 | 0.5777 |
| CT3_P_ENG | random | 0.5130 | 0.3771 | 0.6340 | 0.0005 | 0.5130 |
| CT3_P_ENG | spatial | 0.6737 | 0.5325 | 0.3689 | 0.1652 | 0.6532 |
| CT3_P_RAW | climate_profile | 0.5235 | 0.3936 | 0.6189 | 0.0061 | 0.5235 |
| CT3_P_RAW | municipality | 0.5787 | 0.4566 | 0.5344 | -0.0385 | 0.5774 |
| CT3_P_RAW | random | 0.5121 | 0.3755 | 0.6353 | 0.0010 | 0.5121 |
| CT3_P_RAW | spatial | 0.6656 | 0.5218 | 0.3839 | 0.1591 | 0.6463 |
| CT3_SHIFT | climate_profile | 0.5226 | 0.3929 | 0.6202 | 0.0104 | 0.5225 |
| CT3_SHIFT | municipality | 0.5784 | 0.4560 | 0.5349 | -0.0378 | 0.5771 |
| CT3_SHIFT | random | 0.5115 | 0.3749 | 0.6362 | 0.0007 | 0.5115 |
| CT3_SHIFT | spatial | 0.6839 | 0.5395 | 0.3497 | 0.1822 | 0.6592 |
| CT3_T_ENG | climate_profile | 0.5209 | 0.3919 | 0.6227 | 0.0080 | 0.5209 |
| CT3_T_ENG | municipality | 0.5808 | 0.4589 | 0.5310 | -0.0401 | 0.5794 |
| CT3_T_ENG | random | 0.5129 | 0.3753 | 0.6342 | 0.0017 | 0.5128 |
| CT3_T_ENG | spatial | 0.6839 | 0.5395 | 0.3497 | 0.1822 | 0.6592 |
| CT3_T_RAW | climate_profile | 0.5226 | 0.3929 | 0.6202 | 0.0104 | 0.5225 |
| CT3_T_RAW | municipality | 0.5988 | 0.4625 | 0.5014 | -0.0110 | 0.5987 |
| CT3_T_RAW | random | 0.5148 | 0.3770 | 0.6314 | 0.0007 | 0.5148 |
| CT3_T_RAW | spatial | 0.7007 | 0.5537 | 0.3173 | 0.1771 | 0.6780 |
| J7_BOTH | climate_profile | 0.4890 | 0.3445 | 0.6675 | -0.0139 | 0.4888 |
| J7_BOTH | municipality | 0.5808 | 0.4604 | 0.5309 | -0.0205 | 0.5805 |
| J7_BOTH | random | 0.4864 | 0.3470 | 0.6709 | -0.0121 | 0.4862 |
| J7_BOTH | spatial | 0.6808 | 0.5291 | 0.3556 | 0.2913 | 0.6153 |
| J7_H_ENG | climate_profile | 0.4909 | 0.3492 | 0.6649 | -0.0142 | 0.4907 |
| J7_H_ENG | municipality | 0.5774 | 0.4535 | 0.5365 | -0.0410 | 0.5759 |
| J7_H_ENG | random | 0.4872 | 0.3483 | 0.6699 | -0.0095 | 0.4870 |
| J7_H_ENG | spatial | 0.6929 | 0.5472 | 0.3326 | 0.2732 | 0.6367 |
| J7_H_RAW | climate_profile | 0.5041 | 0.3542 | 0.6466 | -0.0119 | 0.5040 |
| J7_H_RAW | municipality | 0.5936 | 0.4507 | 0.5101 | 0.0239 | 0.5931 |
| J7_H_RAW | random | 0.4880 | 0.3482 | 0.6689 | -0.0089 | 0.4878 |
| J7_H_RAW | spatial | 0.6930 | 0.5519 | 0.3323 | 0.2008 | 0.6632 |
| J7_P_ENG | climate_profile | 0.4972 | 0.3524 | 0.6563 | -0.0164 | 0.4969 |
| J7_P_ENG | municipality | 0.5810 | 0.4596 | 0.5306 | -0.0477 | 0.5791 |
| J7_P_ENG | random | 0.4864 | 0.3476 | 0.6710 | -0.0089 | 0.4862 |
| J7_P_ENG | spatial | 0.6605 | 0.5185 | 0.3934 | 0.2153 | 0.6244 |
| J7_P_RAW | climate_profile | 0.4955 | 0.3497 | 0.6586 | -0.0199 | 0.4951 |
| J7_P_RAW | municipality | 0.5774 | 0.4535 | 0.5365 | -0.0410 | 0.5759 |
| J7_P_RAW | random | 0.4863 | 0.3468 | 0.6711 | -0.0098 | 0.4862 |
| J7_P_RAW | spatial | 0.6490 | 0.5067 | 0.4143 | 0.2052 | 0.6157 |
| J7_SHIFT | climate_profile | 0.4902 | 0.3464 | 0.6659 | -0.0099 | 0.4901 |
| J7_SHIFT | municipality | 0.5774 | 0.4535 | 0.5365 | -0.0410 | 0.5759 |
| J7_SHIFT | random | 0.4863 | 0.3468 | 0.6712 | -0.0098 | 0.4861 |
| J7_SHIFT | spatial | 0.6929 | 0.5472 | 0.3326 | 0.2732 | 0.6367 |
| J7_T_ENG | climate_profile | 0.4906 | 0.3466 | 0.6653 | -0.0091 | 0.4905 |
| J7_T_ENG | municipality | 0.5803 | 0.4574 | 0.5319 | -0.0450 | 0.5785 |
| J7_T_ENG | random | 0.4869 | 0.3470 | 0.6703 | -0.0096 | 0.4867 |
| J7_T_ENG | spatial | 0.6842 | 0.5410 | 0.3492 | 0.2631 | 0.6316 |
| J7_T_RAW | climate_profile | 0.4935 | 0.3505 | 0.6614 | -0.0180 | 0.4932 |
| J7_T_RAW | municipality | 0.6015 | 0.4650 | 0.4970 | -0.0163 | 0.6013 |
| J7_T_RAW | random | 0.4878 | 0.3480 | 0.6690 | -0.0100 | 0.4876 |
| J7_T_RAW | spatial | 0.6915 | 0.5487 | 0.3352 | 0.2057 | 0.6601 |

## Derivadas frente a componentes originales

| experiment | reference | contrast | protocol | delta_rmse | low95 | high95 | p_mse_signflip | n_clusters | exact_sign_enumeration | n_sign_assignments | p_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CT3_H_ENG | CT3_H_RAW | engineering_vs_raw | climate_profile | 0.0054 | -0.0112 | 0.0191 | 0.8456 | 43 | False | 20000 | 1.0000 |
| CT3_T_ENG | CT3_T_RAW | engineering_vs_raw | climate_profile | -0.0017 | -0.0059 | 0.0013 | 0.3420 | 43 | False | 20000 | 1.0000 |
| CT3_P_ENG | CT3_P_RAW | engineering_vs_raw | climate_profile | 0.0038 | -0.0003 | 0.0110 | 0.1204 | 43 | False | 20000 | 1.0000 |
| J7_H_ENG | J7_H_RAW | engineering_vs_raw | climate_profile | -0.0132 | -0.0412 | -0.0015 | 0.0550 | 43 | False | 20000 | 1.0000 |
| J7_T_ENG | J7_T_RAW | engineering_vs_raw | climate_profile | -0.0029 | -0.0101 | 0.0004 | 0.1331 | 43 | False | 20000 | 1.0000 |
| J7_P_ENG | J7_P_RAW | engineering_vs_raw | climate_profile | 0.0016 | -0.0023 | 0.0088 | 0.4985 | 43 | False | 20000 | 1.0000 |
| CT3_H_ENG | CT3_H_RAW | engineering_vs_raw | municipality | -0.0272 | -0.0429 | 0.0301 | 0.5000 | 9 | True | 512 | 1.0000 |
| CT3_T_ENG | CT3_T_RAW | engineering_vs_raw | municipality | -0.0180 | -0.0331 | 0.0130 | 1.0000 | 9 | True | 512 | 1.0000 |
| CT3_P_ENG | CT3_P_RAW | engineering_vs_raw | municipality | 0.0006 | -0.0057 | 0.0149 | 0.7500 | 9 | True | 512 | 1.0000 |
| J7_H_ENG | J7_H_RAW | engineering_vs_raw | municipality | -0.0162 | -0.0410 | 0.0134 | 0.3047 | 9 | True | 512 | 1.0000 |
| J7_T_ENG | J7_T_RAW | engineering_vs_raw | municipality | -0.0212 | -0.0369 | -0.0016 | 0.1094 | 9 | True | 512 | 1.0000 |
| J7_P_ENG | J7_P_RAW | engineering_vs_raw | municipality | 0.0037 | -0.0008 | 0.0269 | 1.0000 | 9 | True | 512 | 1.0000 |
| CT3_H_ENG | CT3_H_RAW | engineering_vs_raw | random | 0.0003 | -0.0042 | 0.0063 | 0.8938 | 43 | False | 20000 | 1.0000 |
| CT3_T_ENG | CT3_T_RAW | engineering_vs_raw | random | -0.0020 | -0.0057 | 0.0004 | 0.1239 | 43 | False | 20000 | 1.0000 |
| CT3_P_ENG | CT3_P_RAW | engineering_vs_raw | random | 0.0009 | -0.0016 | 0.0038 | 0.5203 | 43 | False | 20000 | 1.0000 |
| J7_H_ENG | J7_H_RAW | engineering_vs_raw | random | -0.0008 | -0.0032 | 0.0019 | 0.8190 | 43 | False | 20000 | 1.0000 |
| J7_T_ENG | J7_T_RAW | engineering_vs_raw | random | -0.0009 | -0.0037 | 0.0005 | 0.2449 | 43 | False | 20000 | 1.0000 |
| J7_P_ENG | J7_P_RAW | engineering_vs_raw | random | 0.0000 | -0.0041 | 0.0053 | 0.9873 | 43 | False | 20000 | 1.0000 |
| CT3_H_ENG | CT3_H_RAW | engineering_vs_raw | spatial | -0.0270 | -0.0859 | 0.0027 | 1.0000 | 5 | True | 32 | 1.0000 |
| CT3_T_ENG | CT3_T_RAW | engineering_vs_raw | spatial | -0.0168 | -0.0525 | 0.0000 | 1.0000 | 5 | True | 32 | 1.0000 |
| CT3_P_ENG | CT3_P_RAW | engineering_vs_raw | spatial | 0.0081 | 0.0007 | 0.0166 | 0.2500 | 5 | True | 32 | 1.0000 |
| J7_H_ENG | J7_H_RAW | engineering_vs_raw | spatial | -0.0001 | -0.0357 | 0.0444 | 1.0000 | 5 | True | 32 | 1.0000 |
| J7_T_ENG | J7_T_RAW | engineering_vs_raw | spatial | -0.0073 | -0.0325 | 0.0404 | 0.8750 | 5 | True | 32 | 1.0000 |
| J7_P_ENG | J7_P_RAW | engineering_vs_raw | spatial | 0.0115 | 0.0011 | 0.0215 | 0.1250 | 5 | True | 32 | 1.0000 |

## Distribución de ganancias

| experiment | reference | protocol | total_sse_gain | top10_sse_gain | outside_top10_sse_gain | fraction_improved | fraction_worsened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CT3_H_ENG | CT3 | climate_profile | -1.5539 | 0.4501 | -2.0039 | 0.2246 | 0.3841 |
| CT3_H_ENG | CT3 | municipality | 0.4605 | 0.0000 | 0.4605 | 0.1957 | 0.1014 |
| CT3_H_ENG | CT3 | random | -0.2169 | 0.0852 | -0.3021 | 0.5000 | 0.5000 |
| CT3_H_ENG | CT3 | spatial | -0.9604 | 0.0000 | -0.9604 | 0.0000 | 0.0725 |
| CT3_H_RAW | CT3 | climate_profile | -0.7709 | 0.1142 | -0.8851 | 0.3188 | 0.2536 |
| CT3_H_RAW | CT3 | municipality | -3.9911 | -2.2257 | -1.7654 | 0.4420 | 0.4420 |
| CT3_H_RAW | CT3 | random | -0.1674 | 0.0088 | -0.1762 | 0.4783 | 0.5217 |
| CT3_H_RAW | CT3 | spatial | -6.1541 | -2.4369 | -3.7172 | 0.2101 | 0.3841 |
| CT3_P_ENG | CT3 | climate_profile | -0.9781 | -0.0853 | -0.8928 | 0.1594 | 0.2029 |
| CT3_P_ENG | CT3 | municipality | 0.3211 | 0.1142 | 0.2069 | 0.2319 | 0.1812 |
| CT3_P_ENG | CT3 | random | -0.2037 | -0.0235 | -0.1802 | 0.4710 | 0.5290 |
| CT3_P_ENG | CT3 | spatial | 0.9400 | 0.2778 | 0.6622 | 0.2609 | 0.1957 |
| CT3_P_RAW | CT3 | climate_profile | -0.4243 | -0.0477 | -0.3765 | 0.1667 | 0.1957 |
| CT3_P_RAW | CT3 | municipality | 0.4095 | 0.0000 | 0.4095 | 0.1957 | 0.1014 |
| CT3_P_RAW | CT3 | random | -0.0771 | -0.0134 | -0.0637 | 0.5000 | 0.5000 |
| CT3_P_RAW | CT3 | spatial | 2.4370 | 0.3120 | 2.1250 | 0.2899 | 0.1667 |
| CT3_SHIFT | CT3 | climate_profile | -0.2913 | -0.0477 | -0.2436 | 0.1594 | 0.2029 |
| CT3_SHIFT | CT3 | municipality | 0.4605 | 0.0000 | 0.4605 | 0.1957 | 0.1014 |
| CT3_SHIFT | CT3 | random | 0.0092 | -0.0029 | 0.0120 | 0.5217 | 0.4783 |
| CT3_SHIFT | CT3 | spatial | -0.9604 | 0.0000 | -0.9604 | 0.0000 | 0.0725 |
| CT3_T_ENG | CT3 | climate_profile | -0.0445 | 0.0667 | -0.1111 | 0.1594 | 0.2029 |
| CT3_T_ENG | CT3 | municipality | 0.0753 | 0.0000 | 0.0753 | 0.1522 | 0.1449 |
| CT3_T_ENG | CT3 | random | -0.1851 | -0.1480 | -0.0371 | 0.4565 | 0.5435 |
| CT3_T_ENG | CT3 | spatial | -0.9604 | 0.0000 | -0.9604 | 0.0000 | 0.0725 |
| CT3_T_RAW | CT3 | climate_profile | -0.2913 | -0.0477 | -0.2436 | 0.1594 | 0.2029 |
| CT3_T_RAW | CT3 | municipality | -2.8625 | -2.3928 | -0.4697 | 0.4203 | 0.3913 |
| CT3_T_RAW | CT3 | random | -0.4643 | -0.0662 | -0.3981 | 0.4493 | 0.5507 |
| CT3_T_RAW | CT3 | spatial | -4.1745 | -1.3879 | -2.7866 | 0.0942 | 0.2464 |
| J7_H_ENG | J7_BOTH | climate_profile | -0.2598 | 0.0736 | -0.3334 | 0.3261 | 0.4928 |
| J7_H_ENG | J7_BOTH | municipality | 0.5570 | 0.0000 | 0.5570 | 0.1957 | 0.1014 |
| J7_H_ENG | J7_BOTH | random | -0.1017 | -0.0152 | -0.0865 | 0.3913 | 0.6087 |
| J7_H_ENG | J7_BOTH | spatial | -2.2828 | 0.0000 | -2.2828 | 0.0000 | 0.0725 |
| J7_H_RAW | J7_BOTH | climate_profile | -2.0689 | 0.0706 | -2.1394 | 0.3696 | 0.4493 |
| J7_H_RAW | J7_BOTH | municipality | -2.0613 | -2.5310 | 0.4698 | 0.4565 | 0.4275 |
| J7_H_RAW | J7_BOTH | random | -0.2081 | -0.1707 | -0.0374 | 0.4420 | 0.5580 |
| J7_H_RAW | J7_BOTH | spatial | -2.3073 | 0.8634 | -3.1707 | 0.5000 | 0.5000 |
| J7_P_ENG | J7_BOTH | climate_profile | -1.1088 | -0.0357 | -1.0731 | 0.1884 | 0.3841 |
| J7_P_ENG | J7_BOTH | municipality | -0.0315 | 0.0000 | -0.0315 | 0.1449 | 0.1522 |
| J7_P_ENG | J7_BOTH | random | 0.0057 | -0.0605 | 0.0662 | 0.5362 | 0.4638 |
| J7_P_ENG | J7_BOTH | spatial | 3.7582 | 1.9728 | 1.7854 | 0.4348 | 0.2971 |
| J7_P_RAW | J7_BOTH | climate_profile | -0.8833 | -0.0269 | -0.8563 | 0.2391 | 0.3333 |
| J7_P_RAW | J7_BOTH | municipality | 0.5570 | 0.0000 | 0.5570 | 0.1957 | 0.1014 |
| J7_P_RAW | J7_BOTH | random | 0.0120 | -0.0307 | 0.0427 | 0.5290 | 0.4710 |
| J7_P_RAW | J7_BOTH | spatial | 5.8344 | 2.0987 | 3.7357 | 0.4565 | 0.2754 |
| J7_SHIFT | J7_BOTH | climate_profile | -0.1573 | -0.0344 | -0.1229 | 0.2246 | 0.3478 |
| J7_SHIFT | J7_BOTH | municipality | 0.5570 | 0.0000 | 0.5570 | 0.1957 | 0.1014 |
| J7_SHIFT | J7_BOTH | random | 0.0213 | -0.0260 | 0.0472 | 0.5290 | 0.4710 |
| J7_SHIFT | J7_BOTH | spatial | -2.2828 | 0.0000 | -2.2828 | 0.0000 | 0.0725 |
| J7_T_ENG | J7_BOTH | climate_profile | -0.2152 | -0.0512 | -0.1640 | 0.3768 | 0.4420 |
| J7_T_ENG | J7_BOTH | municipality | 0.0940 | 0.0000 | 0.0940 | 0.1522 | 0.1449 |
| J7_T_ENG | J7_BOTH | random | -0.0646 | -0.0488 | -0.0157 | 0.5797 | 0.4203 |
| J7_T_ENG | J7_BOTH | spatial | -0.6356 | 0.0000 | -0.6356 | 0.1594 | 0.1667 |
| J7_T_RAW | J7_BOTH | climate_profile | -0.6040 | -0.0344 | -0.5696 | 0.1957 | 0.3768 |
| J7_T_RAW | J7_BOTH | municipality | -3.3648 | -1.8239 | -1.5409 | 0.3986 | 0.4855 |
| J7_T_RAW | J7_BOTH | random | -0.1888 | -0.0221 | -0.1667 | 0.4710 | 0.5290 |
| J7_T_RAW | J7_BOTH | spatial | -2.0174 | 0.5476 | -2.5650 | 0.3551 | 0.3913 |

Las comparaciones con la base, 80 pruebas pareadas con Holm, omisiones, análisis sin top10/171/015, cuartiles, pares intraperfil y coeficientes están en las tablas y Excel. El top10 se congeló antes de esta etapa pero fue identificado usando estos mismos datos; excluirlo es sensibilidad descriptiva, no una prueba independiente.

Replay de 910 modelos; 19162 exclusiones verificadas; sin cambio de fuentes ni PRED/final138.

Interpretaci?n y decisi?n: [signal_feature_engineering_conclusions.md](signal_feature_engineering_conclusions.md).
