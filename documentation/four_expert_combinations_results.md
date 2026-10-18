# Combinaciones de cuatro expertos: resultados

Investigación exploratoria; no selección de modelos usando folds externos ni promoción automática. Pesos aprendidos en predicciones internas honestas.

| experiment | climate_profile | fresh_97_41 | municipality | random | spatial |
| --- | --- | --- | --- | --- | --- |
| B1 | 0.4839 / 0.6744 | 0.4622 / 0.6975 | 0.5681 / 0.5513 | 0.4755 / 0.6856 | 0.6813 / 0.3546 |
| B2 | 0.4793 / 0.6805 | 0.4657 / 0.6939 | 0.5849 / 0.5244 | 0.4781 / 0.6821 | 0.6864 / 0.3450 |
| B3 | 0.4803 / 0.6792 | 0.4710 / 0.6858 | 0.6096 / 0.4833 | 0.4778 / 0.6824 | 0.7152 / 0.2888 |
| B4 | 0.4827 / 0.6760 | 0.4688 / 0.6888 | 0.6041 / 0.4926 | 0.4778 / 0.6825 | 0.6832 / 0.3511 |
| B5 | 0.4832 / 0.6754 | 0.4624 / 0.6972 | 0.5688 / 0.5502 | 0.4757 / 0.6853 | 0.6820 / 0.3533 |
| B6 | 0.4808 / 0.6786 | 0.4706 / 0.6862 | 0.6095 / 0.4835 | 0.4774 / 0.6830 | 0.7175 / 0.2841 |
| CT3 | 0.5206 / 0.6232 | 0.4918 / 0.6571 | 0.5813 / 0.5302 | 0.5116 / 0.6361 | 0.6788 / 0.3594 |
| Compact14 | 0.4793 / 0.6805 | 0.4661 / 0.6933 | 0.5755 / 0.5395 | 0.4773 / 0.6832 | 0.6431 / 0.4250 |
| L40 | 0.5031 / 0.6481 | 0.4893 / 0.6621 | 0.7602 / 0.1964 | 0.4930 / 0.6619 | 0.9794 / -0.3337 |
| Reference26 | 0.4774 / 0.6831 | 0.4625 / 0.6971 | 0.5752 / 0.5400 | 0.4748 / 0.6865 | 0.6333 / 0.4423 |

## Residuos

| experiment | protocol | mae | bias | p95_absolute | within_05 |
| --- | --- | --- | --- | --- | --- |
| B1 | climate_profile | 0.3408 | 0.0021 | 0.8754 | 0.7754 |
| B1 | fresh_97_41 | 0.3373 | 0.0026 | 0.8597 | 0.7774 |
| B1 | municipality | 0.4426 | -0.0417 | 1.0790 | 0.6884 |
| B1 | random | 0.3396 | -0.0069 | 0.8278 | 0.7732 |
| B1 | spatial | 0.5388 | 0.2857 | 1.4223 | 0.5507 |
| B2 | climate_profile | 0.3336 | 0.0177 | 0.9121 | 0.7319 |
| B2 | fresh_97_41 | 0.3392 | 0.0026 | 0.8962 | 0.7713 |
| B2 | municipality | 0.4583 | -0.0178 | 1.0790 | 0.6667 |
| B2 | random | 0.3406 | -0.0075 | 0.8549 | 0.7681 |
| B2 | spatial | 0.5481 | 0.1625 | 1.4223 | 0.5362 |
| B3 | climate_profile | 0.3323 | 0.0040 | 0.8897 | 0.7609 |
| B3 | fresh_97_41 | 0.3440 | -0.0031 | 0.8942 | 0.7607 |
| B3 | municipality | 0.4725 | -0.0178 | 1.0790 | 0.6377 |
| B3 | random | 0.3406 | -0.0070 | 0.8322 | 0.7609 |
| B3 | spatial | 0.5607 | 0.2893 | 1.4489 | 0.5362 |
| B4 | climate_profile | 0.3350 | 0.0065 | 0.8857 | 0.7609 |
| B4 | fresh_97_41 | 0.3414 | -0.0016 | 0.8913 | 0.7668 |
| B4 | municipality | 0.4670 | -0.0167 | 1.0790 | 0.6594 |
| B4 | random | 0.3404 | -0.0067 | 0.8322 | 0.7667 |
| B4 | spatial | 0.5416 | 0.2660 | 1.4223 | 0.5580 |
| B5 | climate_profile | 0.3401 | 0.0014 | 0.8719 | 0.7609 |
| B5 | fresh_97_41 | 0.3374 | 0.0033 | 0.8572 | 0.7759 |
| B5 | municipality | 0.4440 | -0.0396 | 1.0790 | 0.6884 |
| B5 | random | 0.3396 | -0.0061 | 0.8284 | 0.7725 |
| B5 | spatial | 0.5398 | 0.2848 | 1.4223 | 0.5507 |
| B6 | climate_profile | 0.3328 | 0.0026 | 0.8973 | 0.7609 |
| B6 | fresh_97_41 | 0.3436 | -0.0029 | 0.8868 | 0.7591 |
| B6 | municipality | 0.4725 | -0.0183 | 1.0790 | 0.6377 |
| B6 | random | 0.3403 | -0.0069 | 0.8290 | 0.7638 |
| B6 | spatial | 0.5613 | 0.2836 | 1.4499 | 0.5435 |
| CT3 | climate_profile | 0.3915 | 0.0046 | 1.0115 | 0.7391 |
| CT3 | fresh_97_41 | 0.3642 | 0.0172 | 0.9660 | 0.7683 |
| CT3 | municipality | 0.4603 | -0.0203 | 1.0790 | 0.6739 |
| CT3 | random | 0.3749 | 0.0005 | 1.0529 | 0.7754 |
| CT3 | spatial | 0.5306 | 0.1912 | 1.4223 | 0.5942 |
| Compact14 | climate_profile | 0.3336 | 0.0177 | 0.9121 | 0.7319 |
| Compact14 | fresh_97_41 | 0.3398 | 0.0020 | 0.8971 | 0.7668 |
| Compact14 | municipality | 0.4468 | -0.0103 | 1.0173 | 0.6522 |
| Compact14 | random | 0.3399 | -0.0074 | 0.8510 | 0.7645 |
| Compact14 | spatial | 0.5140 | 0.1232 | 1.2776 | 0.5580 |
| L40 | climate_profile | 0.3479 | 0.0108 | 1.0292 | 0.7174 |
| L40 | fresh_97_41 | 0.3552 | -0.0023 | 0.9239 | 0.7439 |
| L40 | municipality | 0.5991 | 0.1051 | 1.4204 | 0.5145 |
| L40 | random | 0.3526 | -0.0090 | 0.9053 | 0.7355 |
| L40 | spatial | 0.7434 | 0.4707 | 1.9792 | 0.4928 |
| Reference26 | climate_profile | 0.3342 | -0.0010 | 0.8544 | 0.7681 |
| Reference26 | fresh_97_41 | 0.3387 | 0.0016 | 0.8614 | 0.7744 |
| Reference26 | municipality | 0.4491 | -0.0413 | 1.0790 | 0.6667 |
| Reference26 | random | 0.3396 | -0.0071 | 0.8147 | 0.7688 |
| Reference26 | spatial | 0.5004 | 0.2285 | 1.2538 | 0.5507 |

## Contrastes pareados

| protocol | experiment | reference | delta_rmse | p_mse_signflip | n_clusters | exact_sign_enumeration | n_sign_assignments | p_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| climate_profile | B1 | CT3 | -0.0367 | 0.0078 | 43 | False | 20000 | 0.9577 |
| climate_profile | B1 | L40 | -0.0191 | 0.4098 | 43 | False | 20000 | 1.0000 |
| climate_profile | B1 | Compact14 | 0.0046 | 0.5316 | 43 | False | 20000 | 1.0000 |
| climate_profile | B1 | Reference26 | 0.0065 | 0.0052 | 43 | False | 20000 | 0.6396 |
| climate_profile | B2 | CT3 | -0.0413 | 0.0001 | 43 | False | 20000 | 0.0195 |
| climate_profile | B2 | L40 | -0.0237 | 0.3095 | 43 | False | 20000 | 1.0000 |
| climate_profile | B2 | Compact14 | 0.0000 | 1.0000 | 43 | False | 20000 | 1.0000 |
| climate_profile | B2 | Reference26 | 0.0019 | 0.7966 | 43 | False | 20000 | 1.0000 |
| climate_profile | B3 | CT3 | -0.0403 | 0.0144 | 43 | False | 20000 | 1.0000 |
| climate_profile | B3 | L40 | -0.0227 | 0.1970 | 43 | False | 20000 | 1.0000 |
| climate_profile | B3 | Compact14 | 0.0010 | 0.9007 | 43 | False | 20000 | 1.0000 |
| climate_profile | B3 | Reference26 | 0.0029 | 0.4676 | 43 | False | 20000 | 1.0000 |
| climate_profile | B4 | CT3 | -0.0379 | 0.0136 | 43 | False | 20000 | 1.0000 |
| climate_profile | B4 | L40 | -0.0203 | 0.2863 | 43 | False | 20000 | 1.0000 |
| climate_profile | B4 | Compact14 | 0.0034 | 0.6490 | 43 | False | 20000 | 1.0000 |
| climate_profile | B4 | Reference26 | 0.0053 | 0.0484 | 43 | False | 20000 | 1.0000 |
| climate_profile | B5 | CT3 | -0.0374 | 0.0081 | 43 | False | 20000 | 0.9861 |
| climate_profile | B5 | L40 | -0.0199 | 0.3937 | 43 | False | 20000 | 1.0000 |
| climate_profile | B5 | Compact14 | 0.0038 | 0.6078 | 43 | False | 20000 | 1.0000 |
| climate_profile | B5 | Reference26 | 0.0057 | 0.0082 | 43 | False | 20000 | 0.9900 |
| climate_profile | B6 | CT3 | -0.0398 | 0.0144 | 43 | False | 20000 | 1.0000 |
| climate_profile | B6 | L40 | -0.0222 | 0.1972 | 43 | False | 20000 | 1.0000 |
| climate_profile | B6 | Compact14 | 0.0015 | 0.8565 | 43 | False | 20000 | 1.0000 |
| climate_profile | B6 | Reference26 | 0.0034 | 0.4998 | 43 | False | 20000 | 1.0000 |
| climate_profile | B5 | B1 | -0.0007 | 0.1132 | 43 | False | 20000 | 1.0000 |
| climate_profile | B6 | B3 | 0.0005 | 0.7169 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B1 | CT3 | -0.0296 | 0.0102 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B1 | L40 | -0.0271 | 0.1640 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B1 | Compact14 | -0.0039 | 0.5121 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B1 | Reference26 | -0.0003 | 0.8222 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B2 | CT3 | -0.0261 | 0.0389 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B2 | L40 | -0.0236 | 0.1612 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B2 | Compact14 | -0.0005 | 0.1598 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B2 | Reference26 | 0.0032 | 0.5521 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B3 | CT3 | -0.0208 | 0.1227 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B3 | L40 | -0.0183 | 0.1762 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B3 | Compact14 | 0.0049 | 0.5293 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B3 | Reference26 | 0.0085 | 0.1069 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B4 | CT3 | -0.0230 | 0.0669 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B4 | L40 | -0.0205 | 0.1754 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B4 | Compact14 | 0.0027 | 0.6946 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B4 | Reference26 | 0.0063 | 0.1189 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B5 | CT3 | -0.0294 | 0.0096 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B5 | L40 | -0.0269 | 0.1819 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B5 | Compact14 | -0.0037 | 0.5867 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B5 | Reference26 | -0.0001 | 0.9330 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B6 | CT3 | -0.0212 | 0.1196 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B6 | L40 | -0.0187 | 0.1548 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B6 | Compact14 | 0.0045 | 0.5953 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B6 | Reference26 | 0.0082 | 0.1676 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B5 | B1 | 0.0002 | 0.6323 | 43 | False | 20000 | 1.0000 |
| fresh_97_41 | B6 | B3 | -0.0004 | 0.3621 | 43 | False | 20000 | 1.0000 |
| municipality | B1 | CT3 | -0.0132 | 1.0000 | 9 | True | 512 | 1.0000 |
| municipality | B1 | L40 | -0.1922 | 0.1680 | 9 | True | 512 | 1.0000 |
| municipality | B1 | Compact14 | -0.0074 | 0.7500 | 9 | True | 512 | 1.0000 |
| municipality | B1 | Reference26 | -0.0072 | 0.2969 | 9 | True | 512 | 1.0000 |
| municipality | B2 | CT3 | 0.0036 | 1.0000 | 9 | True | 512 | 1.0000 |
| municipality | B2 | L40 | -0.1754 | 0.1680 | 9 | True | 512 | 1.0000 |
| municipality | B2 | Compact14 | 0.0094 | 0.3750 | 9 | True | 512 | 1.0000 |
| municipality | B2 | Reference26 | 0.0096 | 0.5000 | 9 | True | 512 | 1.0000 |
| municipality | B3 | CT3 | 0.0284 | 0.6484 | 9 | True | 512 | 1.0000 |
| municipality | B3 | L40 | -0.1506 | 0.2227 | 9 | True | 512 | 1.0000 |
| municipality | B3 | Compact14 | 0.0341 | 0.1445 | 9 | True | 512 | 1.0000 |
| municipality | B3 | Reference26 | 0.0344 | 1.0000 | 9 | True | 512 | 1.0000 |
| municipality | B4 | CT3 | 0.0229 | 0.8125 | 9 | True | 512 | 1.0000 |
| municipality | B4 | L40 | -0.1561 | 0.1680 | 9 | True | 512 | 1.0000 |
| municipality | B4 | Compact14 | 0.0286 | 0.2695 | 9 | True | 512 | 1.0000 |
| municipality | B4 | Reference26 | 0.0289 | 0.7969 | 9 | True | 512 | 1.0000 |
| municipality | B5 | CT3 | -0.0125 | 1.0000 | 9 | True | 512 | 1.0000 |
| municipality | B5 | L40 | -0.1915 | 0.1680 | 9 | True | 512 | 1.0000 |
| municipality | B5 | Compact14 | -0.0067 | 0.8750 | 9 | True | 512 | 1.0000 |
| municipality | B5 | Reference26 | -0.0064 | 0.3984 | 9 | True | 512 | 1.0000 |
| municipality | B6 | CT3 | 0.0283 | 0.6367 | 9 | True | 512 | 1.0000 |
| municipality | B6 | L40 | -0.1507 | 0.2227 | 9 | True | 512 | 1.0000 |
| municipality | B6 | Compact14 | 0.0340 | 0.1445 | 9 | True | 512 | 1.0000 |
| municipality | B6 | Reference26 | 0.0343 | 0.5000 | 9 | True | 512 | 1.0000 |
| municipality | B5 | B1 | 0.0007 | 1.0000 | 9 | True | 512 | 1.0000 |
| municipality | B6 | B3 | -0.0001 | 1.0000 | 9 | True | 512 | 1.0000 |
| random | B1 | CT3 | -0.0361 | 0.0005 | 43 | False | 20000 | 0.0704 |
| random | B1 | L40 | -0.0175 | 0.3317 | 43 | False | 20000 | 1.0000 |
| random | B1 | Compact14 | -0.0018 | 0.7417 | 43 | False | 20000 | 1.0000 |
| random | B1 | Reference26 | 0.0007 | 0.5608 | 43 | False | 20000 | 1.0000 |
| random | B2 | CT3 | -0.0335 | 0.0022 | 43 | False | 20000 | 0.2772 |
| random | B2 | L40 | -0.0149 | 0.3540 | 43 | False | 20000 | 1.0000 |
| random | B2 | Compact14 | 0.0008 | 0.2904 | 43 | False | 20000 | 1.0000 |
| random | B2 | Reference26 | 0.0033 | 0.2186 | 43 | False | 20000 | 1.0000 |
| random | B3 | CT3 | -0.0337 | 0.0033 | 43 | False | 20000 | 0.4154 |
| random | B3 | L40 | -0.0151 | 0.2794 | 43 | False | 20000 | 1.0000 |
| random | B3 | Compact14 | 0.0005 | 0.8753 | 43 | False | 20000 | 1.0000 |
| random | B3 | Reference26 | 0.0031 | 0.3388 | 43 | False | 20000 | 1.0000 |
| random | B4 | CT3 | -0.0338 | 0.0014 | 43 | False | 20000 | 0.1841 |
| random | B4 | L40 | -0.0152 | 0.3201 | 43 | False | 20000 | 1.0000 |
| random | B4 | Compact14 | 0.0005 | 0.8806 | 43 | False | 20000 | 1.0000 |
| random | B4 | Reference26 | 0.0030 | 0.1707 | 43 | False | 20000 | 1.0000 |
| random | B5 | CT3 | -0.0359 | 0.0005 | 43 | False | 20000 | 0.0645 |
| random | B5 | L40 | -0.0173 | 0.3398 | 43 | False | 20000 | 1.0000 |
| random | B5 | Compact14 | -0.0016 | 0.8048 | 43 | False | 20000 | 1.0000 |
| random | B5 | Reference26 | 0.0009 | 0.5346 | 43 | False | 20000 | 1.0000 |
| random | B6 | CT3 | -0.0342 | 0.0026 | 43 | False | 20000 | 0.3312 |
| random | B6 | L40 | -0.0155 | 0.2720 | 43 | False | 20000 | 1.0000 |
| random | B6 | Compact14 | 0.0001 | 0.9685 | 43 | False | 20000 | 1.0000 |
| random | B6 | Reference26 | 0.0026 | 0.3846 | 43 | False | 20000 | 1.0000 |
| random | B5 | B1 | 0.0002 | 0.5807 | 43 | False | 20000 | 1.0000 |
| random | B6 | B3 | -0.0004 | 0.0554 | 43 | False | 20000 | 1.0000 |
| spatial | B1 | CT3 | 0.0026 | 1.0000 | 5 | True | 32 | 1.0000 |
| spatial | B1 | L40 | -0.2981 | 0.1875 | 5 | True | 32 | 1.0000 |
| spatial | B1 | Compact14 | 0.0383 | 0.4375 | 5 | True | 32 | 1.0000 |
| spatial | B1 | Reference26 | 0.0480 | 0.5000 | 5 | True | 32 | 1.0000 |
| spatial | B2 | CT3 | 0.0076 | 0.2500 | 5 | True | 32 | 1.0000 |
| spatial | B2 | L40 | -0.2930 | 0.1875 | 5 | True | 32 | 1.0000 |
| spatial | B2 | Compact14 | 0.0433 | 0.5000 | 5 | True | 32 | 1.0000 |
| spatial | B2 | Reference26 | 0.0530 | 0.2500 | 5 | True | 32 | 1.0000 |
| spatial | B3 | CT3 | 0.0364 | 0.6875 | 5 | True | 32 | 1.0000 |
| spatial | B3 | L40 | -0.2642 | 0.1875 | 5 | True | 32 | 1.0000 |
| spatial | B3 | Compact14 | 0.0721 | 0.6875 | 5 | True | 32 | 1.0000 |
| spatial | B3 | Reference26 | 0.0818 | 0.5000 | 5 | True | 32 | 1.0000 |
| spatial | B4 | CT3 | 0.0044 | 1.0000 | 5 | True | 32 | 1.0000 |
| spatial | B4 | L40 | -0.2962 | 0.1875 | 5 | True | 32 | 1.0000 |
| spatial | B4 | Compact14 | 0.0401 | 0.4375 | 5 | True | 32 | 1.0000 |
| spatial | B4 | Reference26 | 0.0498 | 0.3750 | 5 | True | 32 | 1.0000 |
| spatial | B5 | CT3 | 0.0032 | 1.0000 | 5 | True | 32 | 1.0000 |
| spatial | B5 | L40 | -0.2974 | 0.1875 | 5 | True | 32 | 1.0000 |
| spatial | B5 | Compact14 | 0.0389 | 0.4375 | 5 | True | 32 | 1.0000 |
| spatial | B5 | Reference26 | 0.0487 | 0.5000 | 5 | True | 32 | 1.0000 |
| spatial | B6 | CT3 | 0.0388 | 0.6250 | 5 | True | 32 | 1.0000 |
| spatial | B6 | L40 | -0.2619 | 0.1875 | 5 | True | 32 | 1.0000 |
| spatial | B6 | Compact14 | 0.0745 | 0.6875 | 5 | True | 32 | 1.0000 |
| spatial | B6 | Reference26 | 0.0842 | 0.5000 | 5 | True | 32 | 1.0000 |
| spatial | B5 | B1 | 0.0007 | 1.0000 | 5 | True | 32 | 1.0000 |
| spatial | B6 | B3 | 0.0024 | 0.5000 | 5 | True | 32 | 1.0000 |

El banco fresh97/41 son particiones nuevas de respuestas ya estudiadas, no evidencia independiente. Los grupos de inferencia son perfiles (incluyendo fresh), municipios o bloques; las repeticiones no son muestras independientes. L40 conserva representación transductiva. Los diagnósticos por parcela, cuartil, municipio, bloque e intraperfil están en el Excel.
