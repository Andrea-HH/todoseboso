> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Simplificación de bases y corrección por distribución de vecinos: resultados

48 entradas, mismos 65 folds. RMSE t/ha / R² por OOF completa de cada repetición; no media de folds. Exploración sobre validaciones usadas anteriormente, sin promoción de Champion ni PRED59.

BASE=sin R3 final; GLOBAL_GLOBAL=R3 sin ponderación local; SUPPORT=más corrección al parecerse a sus vecinos; NOVELTY=más corrección al diferir de ellos. El peso depende de las tres variables R3 respecto a la mediana/MAD de vecinos definidos por GEO/PHYSICAL/SATELLITE. No usa rendimientos para calcular la semejanza. El signo de la corrección procede de R3, no de la distancia. k/amplitud se seleccionan dentro del entrenamiento de cada combinación.

| experiment | random | climate_profile | municipality | spatial | input_count |
| --- | --- | --- | --- | --- | --- |
| CT3_BASE | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 | 4 |
| CT3_GEO_NOVELTY | 0.5022 / 0.6492 | 0.5090 / 0.6398 | 0.5723 / 0.5446 | 0.6734 / 0.3695 | 9 |
| CT3_GEO_SUPPORT | 0.5027 / 0.6486 | 0.5108 / 0.6372 | 0.5682 / 0.5511 | 0.6622 / 0.3903 | 9 |
| CT3_GLOBAL_GLOBAL | 0.4968 / 0.6568 | 0.5050 / 0.6454 | 0.5726 / 0.5442 | 0.6766 / 0.3635 | 7 |
| CT3_PHYSICAL_NOVELTY | 0.5023 / 0.6491 | 0.5062 / 0.6437 | 0.5719 / 0.5452 | 0.6679 / 0.3797 | 25 |
| CT3_PHYSICAL_SUPPORT | 0.5033 / 0.6478 | 0.5123 / 0.6351 | 0.5699 / 0.5484 | 0.6617 / 0.3913 | 25 |
| CT3_SATELLITE_NOVELTY | 0.5046 / 0.6459 | 0.5117 / 0.6359 | 0.5751 / 0.5401 | 0.6738 / 0.3688 | 8 |
| CT3_SATELLITE_SUPPORT | 0.5016 / 0.6502 | 0.5096 / 0.6390 | 0.5706 / 0.5472 | 0.6581 / 0.3979 | 8 |
| EQUAL7_BASE | 0.4880 / 0.6688 | 0.4820 / 0.6770 | 0.5982 / 0.5025 | 0.7288 / 0.2615 | 13 |
| EQUAL7_GEO_NOVELTY | 0.4795 / 0.6802 | 0.4734 / 0.6884 | 0.5919 / 0.5128 | 0.7160 / 0.2871 | 16 |
| EQUAL7_GEO_SUPPORT | 0.4806 / 0.6787 | 0.4718 / 0.6906 | 0.5926 / 0.5117 | 0.6899 / 0.3382 | 16 |
| EQUAL7_GLOBAL_GLOBAL | 0.4756 / 0.6854 | 0.4664 / 0.6975 | 0.5909 / 0.5146 | 0.7192 / 0.2808 | 16 |
| EQUAL7_PHYSICAL_NOVELTY | 0.4797 / 0.6799 | 0.4690 / 0.6942 | 0.5919 / 0.5129 | 0.7095 / 0.3001 | 33 |
| EQUAL7_PHYSICAL_SUPPORT | 0.4812 / 0.6780 | 0.4730 / 0.6890 | 0.5932 / 0.5107 | 0.6960 / 0.3264 | 33 |
| EQUAL7_SATELLITE_NOVELTY | 0.4820 / 0.6769 | 0.4742 / 0.6873 | 0.5920 / 0.5127 | 0.7210 / 0.2772 | 17 |
| EQUAL7_SATELLITE_SUPPORT | 0.4798 / 0.6798 | 0.4715 / 0.6910 | 0.5922 / 0.5124 | 0.6858 / 0.3461 | 17 |
| EXPERT7_BASE | 0.4898 / 0.6664 | 0.4880 / 0.6689 | 0.6560 / 0.4016 | 0.8089 / 0.0902 | 13 |
| EXPERT7_GEO_NOVELTY | 0.4829 / 0.6756 | 0.4830 / 0.6756 | 0.6522 / 0.4086 | 0.7846 / 0.1441 | 16 |
| EXPERT7_GEO_SUPPORT | 0.4843 / 0.6738 | 0.4818 / 0.6772 | 0.6543 / 0.4049 | 0.7526 / 0.2125 | 16 |
| EXPERT7_GLOBAL_GLOBAL | 0.4808 / 0.6784 | 0.4774 / 0.6831 | 0.6526 / 0.4079 | 0.7882 / 0.1363 | 16 |
| EXPERT7_PHYSICAL_NOVELTY | 0.4833 / 0.6750 | 0.4807 / 0.6788 | 0.6537 / 0.4058 | 0.7932 / 0.1251 | 33 |
| EXPERT7_PHYSICAL_SUPPORT | 0.4847 / 0.6731 | 0.4821 / 0.6768 | 0.6565 / 0.4008 | 0.7593 / 0.1983 | 33 |
| EXPERT7_SATELLITE_NOVELTY | 0.4851 / 0.6726 | 0.4838 / 0.6746 | 0.6533 / 0.4065 | 0.8024 / 0.1047 | 17 |
| EXPERT7_SATELLITE_SUPPORT | 0.4836 / 0.6747 | 0.4800 / 0.6796 | 0.6542 / 0.4050 | 0.7493 / 0.2193 | 17 |
| J7_BASE | 0.4864 / 0.6709 | 0.4890 / 0.6675 | 0.5808 / 0.5309 | 0.6808 / 0.3556 | 28 |
| J7_GEO_NOVELTY | 0.4785 / 0.6815 | 0.4814 / 0.6778 | 0.5768 / 0.5374 | 0.6723 / 0.3716 | 31 |
| J7_GEO_SUPPORT | 0.4800 / 0.6795 | 0.4794 / 0.6805 | 0.5750 / 0.5404 | 0.6513 / 0.4102 | 31 |
| J7_GLOBAL_GLOBAL | 0.4756 / 0.6854 | 0.4748 / 0.6865 | 0.5726 / 0.5442 | 0.6550 / 0.4035 | 31 |
| J7_PHYSICAL_NOVELTY | 0.4790 / 0.6809 | 0.4778 / 0.6826 | 0.5767 / 0.5375 | 0.6676 / 0.3803 | 33 |
| J7_PHYSICAL_SUPPORT | 0.4805 / 0.6789 | 0.4804 / 0.6791 | 0.5748 / 0.5405 | 0.6504 / 0.4118 | 33 |
| J7_SATELLITE_NOVELTY | 0.4808 / 0.6785 | 0.4828 / 0.6759 | 0.5775 / 0.5363 | 0.6766 / 0.3634 | 32 |
| J7_SATELLITE_SUPPORT | 0.4792 / 0.6806 | 0.4789 / 0.6812 | 0.5744 / 0.5412 | 0.6440 / 0.4234 | 32 |
| RAW7_BASE | 0.4937 / 0.6610 | 0.4950 / 0.6594 | 0.7569 / 0.2035 | 0.9760 / -0.3245 | 9 |
| RAW7_GEO_NOVELTY | 0.4866 / 0.6706 | 0.4882 / 0.6687 | 0.7527 / 0.2123 | 0.9562 / -0.2711 | 12 |
| RAW7_GEO_SUPPORT | 0.4872 / 0.6698 | 0.4861 / 0.6715 | 0.7456 / 0.2270 | 0.9284 / -0.1983 | 12 |
| RAW7_GLOBAL_GLOBAL | 0.4832 / 0.6752 | 0.4802 / 0.6794 | 0.7434 / 0.2316 | 0.9312 / -0.2056 | 12 |
| RAW7_PHYSICAL_NOVELTY | 0.4868 / 0.6704 | 0.4845 / 0.6736 | 0.7509 / 0.2161 | 0.9594 / -0.2799 | 29 |
| RAW7_PHYSICAL_SUPPORT | 0.4876 / 0.6692 | 0.4877 / 0.6693 | 0.7435 / 0.2315 | 0.9339 / -0.2126 | 29 |
| RAW7_SATELLITE_NOVELTY | 0.4887 / 0.6678 | 0.4889 / 0.6677 | 0.7523 / 0.2131 | 0.9624 / -0.2878 | 13 |
| RAW7_SATELLITE_SUPPORT | 0.4865 / 0.6708 | 0.4849 / 0.6731 | 0.7418 / 0.2348 | 0.9260 / -0.1922 | 13 |
| SHARES_BASE | 0.4865 / 0.6708 | 0.4913 / 0.6644 | 0.5835 / 0.5266 | 0.6894 / 0.3393 | 23 |
| SHARES_GEO_NOVELTY | 0.4786 / 0.6814 | 0.4836 / 0.6749 | 0.5793 / 0.5334 | 0.6670 / 0.3814 | 26 |
| SHARES_GEO_SUPPORT | 0.4801 / 0.6795 | 0.4813 / 0.6779 | 0.5775 / 0.5362 | 0.6438 / 0.4237 | 26 |
| SHARES_GLOBAL_GLOBAL | 0.4753 / 0.6858 | 0.4772 / 0.6834 | 0.5751 / 0.5402 | 0.6447 / 0.4221 | 26 |
| SHARES_PHYSICAL_NOVELTY | 0.4790 / 0.6809 | 0.4802 / 0.6794 | 0.5793 / 0.5334 | 0.6737 / 0.3690 | 33 |
| SHARES_PHYSICAL_SUPPORT | 0.4806 / 0.6788 | 0.4823 / 0.6766 | 0.5775 / 0.5364 | 0.6490 / 0.4144 | 33 |
| SHARES_SATELLITE_NOVELTY | 0.4808 / 0.6785 | 0.4855 / 0.6723 | 0.5800 / 0.5322 | 0.6763 / 0.3641 | 27 |
| SHARES_SATELLITE_SUPPORT | 0.4792 / 0.6807 | 0.4808 / 0.6786 | 0.5771 / 0.5370 | 0.6412 / 0.4283 | 27 |

## Pruebas pareadas

332 contrastes; significativos tras Holm: 0. Los intervalos son de OOF fijas con conglomerados; no incluyen toda selección histórica ni son intervalos de predicción.

## Soporte y pesos

| experiment | protocol | mean_weight | supported_fraction | mean_neighbors | mean_abs_delta | fraction_zero_weight | mean_amplitude |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CT3_GEO_NOVELTY | climate_profile | 0.4353 | 0.7899 | 17.1594 | 0.0333 | 0.2101 | 0.5000 |
| CT3_GEO_NOVELTY | municipality | 0.3897 | 0.7899 | 21.3913 | 0.0259 | 0.2101 | 0.3351 |
| CT3_GEO_NOVELTY | random | 0.3832 | 0.7899 | 11.3623 | 0.0301 | 0.2101 | 0.5000 |
| CT3_GEO_NOVELTY | spatial | 0.4044 | 0.7899 | 32.0000 | 0.0282 | 0.2101 | 0.2627 |
| CT3_GEO_SUPPORT | climate_profile | 0.4900 | 0.7899 | 66.0870 | 0.0302 | 0.2101 | 0.5000 |
| CT3_GEO_SUPPORT | municipality | 0.4170 | 0.7899 | 33.5072 | 0.0290 | 0.2101 | 0.3351 |
| CT3_GEO_SUPPORT | random | 0.4736 | 0.7899 | 64.0232 | 0.0262 | 0.2101 | 0.5000 |
| CT3_GEO_SUPPORT | spatial | 0.4611 | 0.7899 | 22.0870 | 0.0510 | 0.2101 | 0.5000 |
| CT3_PHYSICAL_NOVELTY | climate_profile | 0.4479 | 0.7899 | 8.0000 | 0.0358 | 0.2101 | 0.5000 |
| CT3_PHYSICAL_NOVELTY | municipality | 0.3962 | 0.7899 | 17.6812 | 0.0281 | 0.2101 | 0.3351 |
| CT3_PHYSICAL_NOVELTY | random | 0.3632 | 0.7899 | 17.1594 | 0.0284 | 0.2101 | 0.5000 |
| CT3_PHYSICAL_NOVELTY | spatial | 0.3863 | 0.7899 | 26.6667 | 0.0264 | 0.2101 | 0.2627 |
| CT3_PHYSICAL_SUPPORT | climate_profile | 0.4536 | 0.7899 | 72.0000 | 0.0273 | 0.2101 | 0.5000 |
| CT3_PHYSICAL_SUPPORT | municipality | 0.4045 | 0.7899 | 29.9710 | 0.0313 | 0.2101 | 0.4529 |
| CT3_PHYSICAL_SUPPORT | random | 0.4592 | 0.7899 | 61.8145 | 0.0251 | 0.2101 | 0.5000 |
| CT3_PHYSICAL_SUPPORT | spatial | 0.4454 | 0.7899 | 56.3478 | 0.0446 | 0.2101 | 0.4312 |
| CT3_SATELLITE_NOVELTY | climate_profile | 0.3250 | 0.7899 | 20.1739 | 0.0253 | 0.2101 | 0.5000 |
| CT3_SATELLITE_NOVELTY | municipality | 0.3428 | 0.7899 | 25.2754 | 0.0214 | 0.2101 | 0.3062 |
| CT3_SATELLITE_NOVELTY | random | 0.3082 | 0.7899 | 24.6145 | 0.0235 | 0.2101 | 0.5000 |
| CT3_SATELLITE_NOVELTY | spatial | 0.3447 | 0.7899 | 29.9130 | 0.0220 | 0.2101 | 0.2627 |
| CT3_SATELLITE_SUPPORT | climate_profile | 0.4274 | 0.7899 | 16.5217 | 0.0278 | 0.2101 | 0.5000 |
| CT3_SATELLITE_SUPPORT | municipality | 0.4350 | 0.7899 | 35.6812 | 0.0208 | 0.2101 | 0.1775 |
| CT3_SATELLITE_SUPPORT | random | 0.4663 | 0.7899 | 24.5623 | 0.0269 | 0.2101 | 0.5000 |
| CT3_SATELLITE_SUPPORT | spatial | 0.4365 | 0.7899 | 17.7971 | 0.0451 | 0.2101 | 0.4312 |
| EQUAL7_GEO_NOVELTY | climate_profile | 0.3838 | 0.7899 | 15.7681 | 0.0264 | 0.2101 | 0.5000 |
| EQUAL7_GEO_NOVELTY | municipality | 0.3908 | 0.7899 | 24.1739 | 0.0256 | 0.2101 | 0.2772 |
| EQUAL7_GEO_NOVELTY | random | 0.3884 | 0.7899 | 9.7681 | 0.0284 | 0.2101 | 0.5000 |
| EQUAL7_GEO_NOVELTY | spatial | 0.4294 | 0.7899 | 29.9130 | 0.0346 | 0.2101 | 0.2627 |
| EQUAL7_GEO_SUPPORT | climate_profile | 0.4900 | 0.7899 | 66.0870 | 0.0279 | 0.2101 | 0.5000 |
| EQUAL7_GEO_SUPPORT | municipality | 0.4562 | 0.7899 | 65.8261 | 0.0215 | 0.2101 | 0.1486 |
| EQUAL7_GEO_SUPPORT | random | 0.4695 | 0.7899 | 56.1565 | 0.0238 | 0.2101 | 0.5000 |
| EQUAL7_GEO_SUPPORT | spatial | 0.4796 | 0.7899 | 33.3333 | 0.0699 | 0.2101 | 0.5000 |
| EQUAL7_PHYSICAL_NOVELTY | climate_profile | 0.4479 | 0.7899 | 8.0000 | 0.0330 | 0.2101 | 0.5000 |
| EQUAL7_PHYSICAL_NOVELTY | municipality | 0.3883 | 0.7899 | 46.8116 | 0.0261 | 0.2101 | 0.2772 |
| EQUAL7_PHYSICAL_NOVELTY | random | 0.3710 | 0.7899 | 14.0986 | 0.0269 | 0.2101 | 0.5000 |
| EQUAL7_PHYSICAL_NOVELTY | spatial | 0.3863 | 0.7899 | 26.6667 | 0.0313 | 0.2101 | 0.2627 |
| EQUAL7_PHYSICAL_SUPPORT | climate_profile | 0.4595 | 0.7899 | 61.8551 | 0.0256 | 0.2101 | 0.5000 |
| EQUAL7_PHYSICAL_SUPPORT | municipality | 0.4327 | 0.7899 | 57.3623 | 0.0222 | 0.2101 | 0.1667 |
| EQUAL7_PHYSICAL_SUPPORT | random | 0.4585 | 0.7899 | 59.7043 | 0.0230 | 0.2101 | 0.5000 |
| EQUAL7_PHYSICAL_SUPPORT | spatial | 0.4035 | 0.7899 | 53.3913 | 0.0605 | 0.2101 | 0.5000 |
| EQUAL7_SATELLITE_NOVELTY | climate_profile | 0.3250 | 0.7899 | 20.1739 | 0.0232 | 0.2101 | 0.5000 |
| EQUAL7_SATELLITE_NOVELTY | municipality | 0.3428 | 0.7899 | 25.2754 | 0.0301 | 0.2101 | 0.4058 |
| EQUAL7_SATELLITE_NOVELTY | random | 0.3039 | 0.7899 | 22.9739 | 0.0216 | 0.2101 | 0.5000 |
| EQUAL7_SATELLITE_NOVELTY | spatial | 0.3447 | 0.7899 | 29.9130 | 0.0259 | 0.2101 | 0.2627 |
| EQUAL7_SATELLITE_SUPPORT | climate_profile | 0.4385 | 0.7899 | 27.1884 | 0.0254 | 0.2101 | 0.5000 |
| EQUAL7_SATELLITE_SUPPORT | municipality | 0.4391 | 0.7899 | 42.1739 | 0.0206 | 0.2101 | 0.1486 |
| EQUAL7_SATELLITE_SUPPORT | random | 0.4702 | 0.7899 | 28.4116 | 0.0249 | 0.2101 | 0.5000 |
| EQUAL7_SATELLITE_SUPPORT | spatial | 0.4365 | 0.7899 | 17.7971 | 0.0643 | 0.2101 | 0.5000 |
| EXPERT7_GEO_NOVELTY | climate_profile | 0.4464 | 0.7899 | 9.4493 | 0.0283 | 0.2101 | 0.4547 |
| EXPERT7_GEO_NOVELTY | municipality | 0.3908 | 0.7899 | 24.1739 | 0.0297 | 0.2101 | 0.2772 |
| EXPERT7_GEO_NOVELTY | random | 0.3885 | 0.7899 | 9.1246 | 0.0263 | 0.2101 | 0.5000 |
| EXPERT7_GEO_NOVELTY | spatial | 0.4335 | 0.7899 | 33.9710 | 0.0503 | 0.2101 | 0.3297 |
| EXPERT7_GEO_SUPPORT | climate_profile | 0.4761 | 0.7899 | 57.3913 | 0.0239 | 0.2101 | 0.4547 |
| EXPERT7_GEO_SUPPORT | municipality | 0.4533 | 0.7899 | 61.7681 | 0.0273 | 0.2101 | 0.1667 |
| EXPERT7_GEO_SUPPORT | random | 0.4625 | 0.7899 | 46.3246 | 0.0215 | 0.2101 | 0.5000 |
| EXPERT7_GEO_SUPPORT | spatial | 0.4666 | 0.7899 | 25.3333 | 0.0802 | 0.2101 | 0.5000 |
| EXPERT7_PHYSICAL_NOVELTY | climate_profile | 0.3984 | 0.7899 | 19.5942 | 0.0289 | 0.2101 | 0.5000 |
| EXPERT7_PHYSICAL_NOVELTY | municipality | 0.3883 | 0.7899 | 46.8116 | 0.0185 | 0.2101 | 0.1486 |
| EXPERT7_PHYSICAL_NOVELTY | random | 0.3736 | 0.7899 | 14.2435 | 0.0250 | 0.2101 | 0.5000 |
| EXPERT7_PHYSICAL_NOVELTY | spatial | 0.3945 | 0.7899 | 11.2464 | 0.0355 | 0.2101 | 0.2681 |
| EXPERT7_PHYSICAL_SUPPORT | climate_profile | 0.4332 | 0.7899 | 51.7101 | 0.0227 | 0.2101 | 0.5000 |
| EXPERT7_PHYSICAL_SUPPORT | municipality | 0.4409 | 0.7899 | 58.5217 | 0.0288 | 0.2101 | 0.1848 |
| EXPERT7_PHYSICAL_SUPPORT | random | 0.4558 | 0.7899 | 55.2000 | 0.0210 | 0.2101 | 0.5000 |
| EXPERT7_PHYSICAL_SUPPORT | spatial | 0.4074 | 0.7899 | 38.5507 | 0.0701 | 0.2101 | 0.5000 |
| EXPERT7_SATELLITE_NOVELTY | climate_profile | 0.3214 | 0.7899 | 23.8261 | 0.0209 | 0.2101 | 0.4547 |
| EXPERT7_SATELLITE_NOVELTY | municipality | 0.3428 | 0.7899 | 25.2754 | 0.0257 | 0.2101 | 0.2772 |
| EXPERT7_SATELLITE_NOVELTY | random | 0.3013 | 0.7899 | 20.8058 | 0.0198 | 0.2101 | 0.4949 |
| EXPERT7_SATELLITE_NOVELTY | spatial | 0.3385 | 0.7899 | 32.4638 | 0.0247 | 0.2101 | 0.1993 |
| EXPERT7_SATELLITE_SUPPORT | climate_profile | 0.4455 | 0.7899 | 24.8116 | 0.0250 | 0.2101 | 0.5000 |
| EXPERT7_SATELLITE_SUPPORT | municipality | 0.4410 | 0.7899 | 38.9275 | 0.0263 | 0.2101 | 0.1667 |
| EXPERT7_SATELLITE_SUPPORT | random | 0.4734 | 0.7899 | 32.4580 | 0.0231 | 0.2101 | 0.5000 |
| EXPERT7_SATELLITE_SUPPORT | spatial | 0.4424 | 0.7899 | 19.1884 | 0.0765 | 0.2101 | 0.5000 |
| J7_GEO_NOVELTY | climate_profile | 0.4370 | 0.7899 | 13.7971 | 0.0304 | 0.2101 | 0.5000 |
| J7_GEO_NOVELTY | municipality | 0.3881 | 0.7899 | 47.4493 | 0.0147 | 0.2101 | 0.1486 |
| J7_GEO_NOVELTY | random | 0.3877 | 0.7899 | 9.6000 | 0.0273 | 0.2101 | 0.5000 |
| J7_GEO_NOVELTY | spatial | 0.4162 | 0.7899 | 30.9565 | 0.0451 | 0.2101 | 0.3297 |
| J7_GEO_SUPPORT | climate_profile | 0.4900 | 0.7899 | 66.0870 | 0.0278 | 0.2101 | 0.5000 |
| J7_GEO_SUPPORT | municipality | 0.4562 | 0.7899 | 65.8261 | 0.0199 | 0.2101 | 0.1486 |
| J7_GEO_SUPPORT | random | 0.4653 | 0.7899 | 51.1420 | 0.0227 | 0.2101 | 0.5000 |
| J7_GEO_SUPPORT | spatial | 0.4740 | 0.7899 | 31.4203 | 0.0752 | 0.2101 | 0.5000 |
| J7_PHYSICAL_NOVELTY | climate_profile | 0.4479 | 0.7899 | 8.0000 | 0.0332 | 0.2101 | 0.5000 |
| J7_PHYSICAL_NOVELTY | municipality | 0.3883 | 0.7899 | 46.8116 | 0.0159 | 0.2101 | 0.1486 |
| J7_PHYSICAL_NOVELTY | random | 0.3724 | 0.7899 | 15.6754 | 0.0259 | 0.2101 | 0.5000 |
| J7_PHYSICAL_NOVELTY | spatial | 0.3863 | 0.7899 | 26.6667 | 0.0325 | 0.2101 | 0.2627 |
| J7_PHYSICAL_SUPPORT | climate_profile | 0.4595 | 0.7899 | 61.8551 | 0.0255 | 0.2101 | 0.5000 |
| J7_PHYSICAL_SUPPORT | municipality | 0.4451 | 0.7899 | 61.3623 | 0.0198 | 0.2101 | 0.1486 |
| J7_PHYSICAL_SUPPORT | random | 0.4573 | 0.7899 | 57.7855 | 0.0222 | 0.2101 | 0.5000 |
| J7_PHYSICAL_SUPPORT | spatial | 0.3903 | 0.7899 | 20.9275 | 0.0662 | 0.2101 | 0.5000 |
| J7_SATELLITE_NOVELTY | climate_profile | 0.3227 | 0.7899 | 18.8986 | 0.0233 | 0.2101 | 0.5000 |
| J7_SATELLITE_NOVELTY | municipality | 0.3552 | 0.7899 | 43.7391 | 0.0120 | 0.2101 | 0.1486 |
| J7_SATELLITE_NOVELTY | random | 0.3028 | 0.7899 | 20.8812 | 0.0208 | 0.2101 | 0.5000 |
| J7_SATELLITE_NOVELTY | spatial | 0.3447 | 0.7899 | 29.9130 | 0.0285 | 0.2101 | 0.2627 |
| J7_SATELLITE_SUPPORT | climate_profile | 0.4385 | 0.7899 | 27.1884 | 0.0253 | 0.2101 | 0.5000 |
| J7_SATELLITE_SUPPORT | municipality | 0.4391 | 0.7899 | 42.1739 | 0.0192 | 0.2101 | 0.1486 |
| J7_SATELLITE_SUPPORT | random | 0.4719 | 0.7899 | 31.0261 | 0.0241 | 0.2101 | 0.5000 |
| J7_SATELLITE_SUPPORT | spatial | 0.4325 | 0.7899 | 16.8696 | 0.0705 | 0.2101 | 0.5000 |
| RAW7_GEO_NOVELTY | climate_profile | 0.4501 | 0.7899 | 10.8986 | 0.0373 | 0.2101 | 0.5000 |
| RAW7_GEO_NOVELTY | municipality | 0.3940 | 0.7899 | 25.1594 | 0.0522 | 0.2101 | 0.4638 |
| RAW7_GEO_NOVELTY | random | 0.3867 | 0.7899 | 9.6058 | 0.0267 | 0.2101 | 0.5000 |
| RAW7_GEO_NOVELTY | spatial | 0.4297 | 0.7899 | 17.3913 | 0.0705 | 0.2101 | 0.4674 |
| RAW7_GEO_SUPPORT | climate_profile | 0.4794 | 0.7899 | 61.7391 | 0.0357 | 0.2101 | 0.5000 |
| RAW7_GEO_SUPPORT | municipality | 0.4516 | 0.7899 | 39.8841 | 0.0520 | 0.2101 | 0.4239 |
| RAW7_GEO_SUPPORT | random | 0.4632 | 0.7899 | 44.8812 | 0.0236 | 0.2101 | 0.5000 |
| RAW7_GEO_SUPPORT | spatial | 0.4701 | 0.7899 | 27.0725 | 0.0880 | 0.2101 | 0.5000 |
| RAW7_PHYSICAL_NOVELTY | climate_profile | 0.4479 | 0.7899 | 8.0000 | 0.0387 | 0.2101 | 0.5000 |
| RAW7_PHYSICAL_NOVELTY | municipality | 0.3940 | 0.7899 | 25.4493 | 0.0521 | 0.2101 | 0.4638 |
| RAW7_PHYSICAL_NOVELTY | random | 0.3793 | 0.7899 | 12.6203 | 0.0260 | 0.2101 | 0.5000 |
| RAW7_PHYSICAL_NOVELTY | spatial | 0.3415 | 0.7899 | 29.6812 | 0.0576 | 0.2101 | 0.4674 |
| RAW7_PHYSICAL_SUPPORT | climate_profile | 0.4448 | 0.7899 | 47.2464 | 0.0325 | 0.2101 | 0.5000 |
| RAW7_PHYSICAL_SUPPORT | municipality | 0.4333 | 0.7899 | 59.6522 | 0.0476 | 0.2101 | 0.4239 |
| RAW7_PHYSICAL_SUPPORT | random | 0.4562 | 0.7899 | 52.7478 | 0.0231 | 0.2101 | 0.5000 |
| RAW7_PHYSICAL_SUPPORT | spatial | 0.4128 | 0.7899 | 40.6957 | 0.0800 | 0.2101 | 0.5000 |
| RAW7_SATELLITE_NOVELTY | climate_profile | 0.3368 | 0.7899 | 21.1594 | 0.0276 | 0.2101 | 0.5000 |
| RAW7_SATELLITE_NOVELTY | municipality | 0.3374 | 0.7899 | 22.4348 | 0.0433 | 0.2101 | 0.4638 |
| RAW7_SATELLITE_NOVELTY | random | 0.2998 | 0.7899 | 18.9275 | 0.0205 | 0.2101 | 0.5000 |
| RAW7_SATELLITE_NOVELTY | spatial | 0.3385 | 0.7899 | 32.4638 | 0.0552 | 0.2101 | 0.4674 |
| RAW7_SATELLITE_SUPPORT | climate_profile | 0.4385 | 0.7899 | 27.1884 | 0.0334 | 0.2101 | 0.5000 |
| RAW7_SATELLITE_SUPPORT | municipality | 0.4462 | 0.7899 | 21.6812 | 0.0511 | 0.2101 | 0.4239 |
| RAW7_SATELLITE_SUPPORT | random | 0.4711 | 0.7899 | 33.5594 | 0.0250 | 0.2101 | 0.5000 |
| RAW7_SATELLITE_SUPPORT | spatial | 0.4548 | 0.7899 | 16.2319 | 0.0868 | 0.2101 | 0.5000 |
| SHARES_GEO_NOVELTY | climate_profile | 0.3838 | 0.7899 | 15.7681 | 0.0263 | 0.2101 | 0.5000 |
| SHARES_GEO_NOVELTY | municipality | 0.3881 | 0.7899 | 47.4493 | 0.0151 | 0.2101 | 0.1486 |
| SHARES_GEO_NOVELTY | random | 0.3877 | 0.7899 | 9.6058 | 0.0272 | 0.2101 | 0.5000 |
| SHARES_GEO_NOVELTY | spatial | 0.4203 | 0.7899 | 35.0145 | 0.0456 | 0.2101 | 0.2953 |
| SHARES_GEO_SUPPORT | climate_profile | 0.4900 | 0.7899 | 66.0870 | 0.0284 | 0.2101 | 0.5000 |
| SHARES_GEO_SUPPORT | municipality | 0.4562 | 0.7899 | 65.8261 | 0.0201 | 0.2101 | 0.1486 |
| SHARES_GEO_SUPPORT | random | 0.4663 | 0.7899 | 52.6029 | 0.0228 | 0.2101 | 0.5000 |
| SHARES_GEO_SUPPORT | spatial | 0.4796 | 0.7899 | 33.3333 | 0.0787 | 0.2101 | 0.5000 |
| SHARES_PHYSICAL_NOVELTY | climate_profile | 0.4479 | 0.7899 | 8.0000 | 0.0332 | 0.2101 | 0.5000 |
| SHARES_PHYSICAL_NOVELTY | municipality | 0.3883 | 0.7899 | 46.8116 | 0.0162 | 0.2101 | 0.1486 |
| SHARES_PHYSICAL_NOVELTY | random | 0.3716 | 0.7899 | 15.2174 | 0.0259 | 0.2101 | 0.5000 |
| SHARES_PHYSICAL_NOVELTY | spatial | 0.3838 | 0.7899 | 43.8261 | 0.0312 | 0.2101 | 0.2319 |
| SHARES_PHYSICAL_SUPPORT | climate_profile | 0.4595 | 0.7899 | 61.8551 | 0.0260 | 0.2101 | 0.5000 |
| SHARES_PHYSICAL_SUPPORT | municipality | 0.4451 | 0.7899 | 61.3623 | 0.0200 | 0.2101 | 0.1486 |
| SHARES_PHYSICAL_SUPPORT | random | 0.4557 | 0.7899 | 53.2870 | 0.0220 | 0.2101 | 0.5000 |
| SHARES_PHYSICAL_SUPPORT | spatial | 0.3903 | 0.7899 | 20.9275 | 0.0676 | 0.2101 | 0.5000 |
| SHARES_SATELLITE_NOVELTY | climate_profile | 0.3227 | 0.7899 | 18.8986 | 0.0232 | 0.2101 | 0.5000 |
| SHARES_SATELLITE_NOVELTY | municipality | 0.3552 | 0.7899 | 43.7391 | 0.0124 | 0.2101 | 0.1486 |
| SHARES_SATELLITE_NOVELTY | random | 0.3016 | 0.7899 | 21.3681 | 0.0208 | 0.2101 | 0.5000 |
| SHARES_SATELLITE_NOVELTY | spatial | 0.3385 | 0.7899 | 32.4638 | 0.0338 | 0.2101 | 0.2953 |
| SHARES_SATELLITE_SUPPORT | climate_profile | 0.4385 | 0.7899 | 27.1884 | 0.0258 | 0.2101 | 0.5000 |
| SHARES_SATELLITE_SUPPORT | municipality | 0.4391 | 0.7899 | 42.1739 | 0.0194 | 0.2101 | 0.1486 |
| SHARES_SATELLITE_SUPPORT | random | 0.4690 | 0.7899 | 27.5826 | 0.0241 | 0.2101 | 0.5000 |
| SHARES_SATELLITE_SUPPORT | spatial | 0.4522 | 0.7899 | 22.6087 | 0.0738 | 0.2101 | 0.5000 |

El número de entradas incluye lo necesario para construir el vecindario; una base compacta con distancia física deja de ser un sistema de siete entradas. Con R3 incompleto o menos de cuatro referencias, el peso vale cero en ambos usos y se conserva la base. Las referencias nunca incluyen la parcela evaluada.

## Complejidad y nombres

RAW7 elimina gate y corrector climático interno; EXPERT7 conserva ese corrector pero elimina gate; EQUAL7 combina C-T3 y EXPERT7 con .5 fijo; SHARES reconstruye gate de diez proporciones geológicas; J7 es referencia exacta. C-T3+R3 y J7+R3 se reprodujeron exactamente y no se presentan como descubrimientos nuevos. SHARES se reconstruye con calibración anidada de esta etapa; no se presume igualdad con un archivo antiguo. Los campos cuentan entradas, no parámetros efectivos.