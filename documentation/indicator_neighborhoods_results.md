> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Reducciones y vecindarios: resultados exploratorios

k/clusters/amplitud seleccionados sólo con OOF internas DIRECT, compartidos con WEIGHT. El peso no se optimizó independientemente. Las distancias físicas/satelitales no utilizan coordenadas como entrada, pero pueden correlacionarse con territorio.

## RMSE / R²

| modelo | random | climate_profile | municipality | spatial |
| --- | --- | --- | --- | --- |
| CT3 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| J7_BOTH | 0.4864 / 0.6709 | 0.4890 / 0.6675 | 0.5808 / 0.5309 | 0.6808 / 0.3556 |
| CT3_INDICATORS_DIRECT | 0.5064 / 0.6434 | 0.5185 / 0.6262 | 0.5896 / 0.5167 | 0.6696 / 0.3765 |
| J7_INDICATORS_DIRECT | 0.4827 / 0.6759 | 0.4865 / 0.6709 | 0.5852 / 0.5238 | 0.6595 / 0.3953 |
| CT3_P_RAW | 0.5121 / 0.6353 | 0.5235 / 0.6189 | 0.5787 / 0.5344 | 0.6656 / 0.3839 |
| J7_P_RAW | 0.4863 / 0.6711 | 0.4955 / 0.6586 | 0.5774 / 0.5365 | 0.6490 / 0.4143 |
| CT3_GLOBAL_R9 | 0.5104 / 0.6377 | 0.5237 / 0.6187 | 0.5826 / 0.5280 | 0.6804 / 0.3564 |
| CT3_GLOBAL_R4 | 0.4969 / 0.6567 | 0.5102 / 0.6380 | 0.5714 / 0.5461 | 0.6792 / 0.3585 |
| CT3_GLOBAL_R3 | 0.4968 / 0.6568 | 0.5050 / 0.6454 | 0.5726 / 0.5442 | 0.6766 / 0.3635 |
| CT3_GLOBAL_R2 | 0.5038 / 0.6471 | 0.5137 / 0.6331 | 0.5744 / 0.5413 | 0.6735 / 0.3694 |
| CT3_GLOBAL_PCA2 | 0.5019 / 0.6496 | 0.5106 / 0.6375 | 0.5791 / 0.5338 | 0.6864 / 0.3449 |
| CT3_KNN_GEO_DIRECT | 0.4940 / 0.6606 | 0.5038 / 0.6471 | 0.5767 / 0.5375 | 0.6676 / 0.3803 |
| CT3_KNN_GEO_WEIGHT | 0.4974 / 0.6559 | 0.5106 / 0.6375 | 0.5798 / 0.5326 | 0.6797 / 0.3577 |
| CT3_KNN_PHYSICAL_DIRECT | 0.4966 / 0.6570 | 0.5055 / 0.6447 | 0.5692 / 0.5495 | 0.6722 / 0.3717 |
| CT3_KNN_PHYSICAL_WEIGHT | 0.4972 / 0.6563 | 0.5105 / 0.6377 | 0.5736 / 0.5425 | 0.6796 / 0.3578 |
| CT3_KNN_SATELLITE_DIRECT | 0.4934 / 0.6614 | 0.5070 / 0.6427 | 0.5687 / 0.5503 | 0.6714 / 0.3732 |
| CT3_KNN_SATELLITE_WEIGHT | 0.4968 / 0.6568 | 0.5079 / 0.6414 | 0.5726 / 0.5441 | 0.6741 / 0.3682 |
| CT3_CLUSTER_GEO_DIRECT | 0.4985 / 0.6545 | 0.5080 / 0.6413 | 0.5649 / 0.5563 | 0.6742 / 0.3679 |
| CT3_CLUSTER_GEO_WEIGHT | 0.4976 / 0.6557 | 0.5111 / 0.6368 | 0.5795 / 0.5331 | 0.6772 / 0.3623 |
| CT3_CLUSTER_PHYSICAL_DIRECT | 0.5001 / 0.6522 | 0.5087 / 0.6402 | 0.5804 / 0.5316 | 0.6749 / 0.3667 |
| CT3_CLUSTER_PHYSICAL_WEIGHT | 0.4982 / 0.6549 | 0.5146 / 0.6318 | 0.5786 / 0.5346 | 0.6761 / 0.3645 |
| CT3_CLUSTER_SATELLITE_DIRECT | 0.4964 / 0.6573 | 0.5080 / 0.6412 | 0.5695 / 0.5491 | 0.6764 / 0.3639 |
| CT3_CLUSTER_SATELLITE_WEIGHT | 0.4979 / 0.6553 | 0.5099 / 0.6385 | 0.5733 / 0.5431 | 0.6788 / 0.3594 |
| J7_GLOBAL_R9 | 0.4855 / 0.6722 | 0.4894 / 0.6670 | 0.5811 / 0.5306 | 0.6705 / 0.3750 |
| J7_GLOBAL_R4 | 0.4755 / 0.6856 | 0.4765 / 0.6843 | 0.5782 / 0.5351 | 0.6615 / 0.3916 |
| J7_GLOBAL_R3 | 0.4756 / 0.6854 | 0.4748 / 0.6865 | 0.5726 / 0.5442 | 0.6550 / 0.4035 |
| J7_GLOBAL_R2 | 0.4802 / 0.6793 | 0.4802 / 0.6793 | 0.5746 / 0.5409 | 0.6528 / 0.4075 |
| J7_GLOBAL_PCA2 | 0.4795 / 0.6802 | 0.4840 / 0.6744 | 0.5787 / 0.5344 | 0.6929 / 0.3326 |
| J7_KNN_GEO_DIRECT | 0.4786 / 0.6814 | 0.4795 / 0.6804 | 0.5783 / 0.5351 | 0.6644 / 0.3863 |
| J7_KNN_GEO_WEIGHT | 0.4763 / 0.6844 | 0.4768 / 0.6839 | 0.5786 / 0.5345 | 0.6636 / 0.3878 |
| J7_KNN_PHYSICAL_DIRECT | 0.4784 / 0.6817 | 0.4758 / 0.6852 | 0.5760 / 0.5387 | 0.6589 / 0.3964 |
| J7_KNN_PHYSICAL_WEIGHT | 0.4759 / 0.6850 | 0.4779 / 0.6825 | 0.5768 / 0.5374 | 0.6600 / 0.3943 |
| J7_KNN_SATELLITE_DIRECT | 0.4725 / 0.6895 | 0.4745 / 0.6869 | 0.5767 / 0.5376 | 0.6536 / 0.4060 |
| J7_KNN_SATELLITE_WEIGHT | 0.4755 / 0.6856 | 0.4761 / 0.6849 | 0.5769 / 0.5373 | 0.6602 / 0.3940 |
| J7_CLUSTER_GEO_DIRECT | 0.4790 / 0.6809 | 0.4795 / 0.6803 | 0.5826 / 0.5280 | 0.6850 / 0.3476 |
| J7_CLUSTER_GEO_WEIGHT | 0.4764 / 0.6844 | 0.4783 / 0.6820 | 0.5792 / 0.5335 | 0.6551 / 0.4034 |
| J7_CLUSTER_PHYSICAL_DIRECT | 0.4793 / 0.6805 | 0.4797 / 0.6801 | 0.5789 / 0.5341 | 0.6763 / 0.3641 |
| J7_CLUSTER_PHYSICAL_WEIGHT | 0.4773 / 0.6832 | 0.4786 / 0.6816 | 0.5772 / 0.5367 | 0.6742 / 0.3680 |
| J7_CLUSTER_SATELLITE_DIRECT | 0.4747 / 0.6865 | 0.4757 / 0.6854 | 0.5767 / 0.5376 | 0.6528 / 0.4075 |
| J7_CLUSTER_SATELLITE_WEIGHT | 0.4760 / 0.6849 | 0.4760 / 0.6850 | 0.5777 / 0.5361 | 0.6613 / 0.3920 |

## Diagnóstico de vecinos

| experiment | protocol | neighbor_count | effective_neighbor_count | fallback_global | weight | mean_geo_distance_km | same_municipality_fraction | same_profile_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CT3_CLUSTER_GEO_DIRECT | climate_profile | 29.5435 | 29.5435 | 0.0652 | nan | 4.7331 | 0.8315 | 0.0000 |
| CT3_CLUSTER_GEO_DIRECT | municipality | 10.4348 | 10.4348 | 0.1159 | nan | 9.1546 | 0.0000 | 0.0518 |
| CT3_CLUSTER_GEO_DIRECT | random | 31.5681 | 31.5681 | 0.0101 | nan | 3.9261 | 0.8616 | 0.3385 |
| CT3_CLUSTER_GEO_DIRECT | spatial | 30.5507 | 30.5507 | 0.0000 | nan | 14.5192 | 0.4803 | 0.0248 |
| CT3_CLUSTER_GEO_WEIGHT | climate_profile | 29.5435 | 29.5435 | 0.0000 | 0.8912 | 4.7331 | 0.8315 | 0.0000 |
| CT3_CLUSTER_GEO_WEIGHT | municipality | 10.4348 | 10.4348 | 0.0000 | 0.2725 | 9.1546 | 0.0000 | 0.0518 |
| CT3_CLUSTER_GEO_WEIGHT | random | 31.5681 | 31.5681 | 0.0000 | 0.9331 | 3.9261 | 0.8616 | 0.3385 |
| CT3_CLUSTER_GEO_WEIGHT | spatial | 30.5507 | 30.5507 | 0.0000 | 0.1121 | 14.5192 | 0.4803 | 0.0248 |
| CT3_CLUSTER_PHYSICAL_DIRECT | climate_profile | 20.7174 | 20.7174 | 0.0000 | nan | 11.7671 | 0.4603 | 0.0000 |
| CT3_CLUSTER_PHYSICAL_DIRECT | municipality | 24.7681 | 24.7681 | 0.0000 | nan | 24.5643 | 0.0000 | 0.0167 |
| CT3_CLUSTER_PHYSICAL_DIRECT | random | 22.5101 | 22.5101 | 0.0058 | nan | 7.2213 | 0.6655 | 0.3021 |
| CT3_CLUSTER_PHYSICAL_DIRECT | spatial | 32.6522 | 32.6522 | 0.0000 | nan | 26.6227 | 0.1023 | 0.0113 |
| CT3_CLUSTER_PHYSICAL_WEIGHT | climate_profile | 20.7174 | 20.7174 | 0.0000 | 0.7422 | 11.7671 | 0.4603 | 0.0000 |
| CT3_CLUSTER_PHYSICAL_WEIGHT | municipality | 24.7681 | 24.7681 | 0.0000 | 0.2672 | 24.5643 | 0.0000 | 0.0167 |
| CT3_CLUSTER_PHYSICAL_WEIGHT | random | 22.5101 | 22.5101 | 0.0000 | 0.9072 | 7.2213 | 0.6655 | 0.3021 |
| CT3_CLUSTER_PHYSICAL_WEIGHT | spatial | 32.6522 | 32.6522 | 0.0000 | 0.1331 | 26.6227 | 0.1023 | 0.0113 |
| CT3_CLUSTER_SATELLITE_DIRECT | climate_profile | 14.3768 | 14.3768 | 0.2101 | nan | 26.5503 | 0.2361 | 0.0000 |
| CT3_CLUSTER_SATELLITE_DIRECT | municipality | 16.6957 | 16.6957 | 0.2174 | nan | 33.6831 | 0.0000 | 0.0096 |
| CT3_CLUSTER_SATELLITE_DIRECT | random | 14.5341 | 14.5341 | 0.2101 | nan | 23.8258 | 0.3093 | 0.1117 |
| CT3_CLUSTER_SATELLITE_DIRECT | spatial | 17.1812 | 17.1812 | 0.2101 | nan | 31.9572 | 0.1055 | 0.0105 |
| CT3_CLUSTER_SATELLITE_WEIGHT | climate_profile | 14.3768 | 14.3768 | 0.2101 | 0.8411 | 26.5503 | 0.2361 | 0.0000 |
| CT3_CLUSTER_SATELLITE_WEIGHT | municipality | 16.6957 | 16.6957 | 0.2101 | 0.3297 | 33.6831 | 0.0000 | 0.0096 |
| CT3_CLUSTER_SATELLITE_WEIGHT | random | 14.5341 | 14.5341 | 0.2101 | 0.9117 | 23.8258 | 0.3093 | 0.1117 |
| CT3_CLUSTER_SATELLITE_WEIGHT | spatial | 17.1812 | 17.1812 | 0.2101 | 0.1153 | 31.9572 | 0.1055 | 0.0105 |
| CT3_KNN_GEO_DIRECT | climate_profile | 39.3043 | 27.7458 | 0.0000 | nan | 6.8357 | 0.6897 | 0.0000 |
| CT3_KNN_GEO_DIRECT | municipality | 59.6884 | 35.8018 | 0.0000 | nan | 27.8429 | 0.0000 | 0.0169 |
| CT3_KNN_GEO_DIRECT | random | 55.3681 | 23.6966 | 0.0000 | nan | 10.0753 | 0.6073 | 0.2487 |
| CT3_KNN_GEO_DIRECT | spatial | 26.3188 | 25.3176 | 0.0000 | nan | 14.7799 | 0.5091 | 0.0328 |
| CT3_KNN_GEO_WEIGHT | climate_profile | 39.3043 | 27.7458 | 0.0000 | 0.8863 | 6.8357 | 0.6897 | 0.0000 |
| CT3_KNN_GEO_WEIGHT | municipality | 59.6884 | 35.8018 | 0.0000 | 0.2722 | 27.8429 | 0.0000 | 0.0169 |
| CT3_KNN_GEO_WEIGHT | random | 55.3681 | 23.6966 | 0.0000 | 0.9443 | 10.0753 | 0.6073 | 0.2487 |
| CT3_KNN_GEO_WEIGHT | spatial | 26.3188 | 25.3176 | 0.0000 | 0.0757 | 14.7799 | 0.5091 | 0.0328 |
| CT3_KNN_PHYSICAL_DIRECT | climate_profile | 22.4348 | 20.3837 | 0.0000 | nan | 15.1064 | 0.4511 | 0.0000 |
| CT3_KNN_PHYSICAL_DIRECT | municipality | 55.5145 | 53.1138 | 0.0000 | nan | 28.6714 | 0.0000 | 0.0109 |
| CT3_KNN_PHYSICAL_DIRECT | random | 24.5623 | 20.7521 | 0.0000 | nan | 9.0583 | 0.6587 | 0.3034 |
| CT3_KNN_PHYSICAL_DIRECT | spatial | 52.6377 | 49.7535 | 0.0000 | nan | 27.6266 | 0.1715 | 0.0122 |
| CT3_KNN_PHYSICAL_WEIGHT | climate_profile | 22.4348 | 20.3837 | 0.0000 | 0.9381 | 15.1064 | 0.4511 | 0.0000 |
| CT3_KNN_PHYSICAL_WEIGHT | municipality | 55.5145 | 53.1138 | 0.0000 | 0.3135 | 28.6714 | 0.0000 | 0.0109 |
| CT3_KNN_PHYSICAL_WEIGHT | random | 24.5623 | 20.7521 | 0.0000 | 0.9290 | 9.0583 | 0.6587 | 0.3034 |
| CT3_KNN_PHYSICAL_WEIGHT | spatial | 52.6377 | 49.7535 | 0.0000 | 0.1551 | 27.6266 | 0.1715 | 0.0122 |
| CT3_KNN_SATELLITE_DIRECT | climate_profile | 21.0435 | 17.3774 | 0.2101 | nan | 26.1965 | 0.2297 | 0.0000 |
| CT3_KNN_SATELLITE_DIRECT | municipality | 28.0290 | 22.3553 | 0.2101 | nan | 33.5727 | 0.0000 | 0.0068 |
| CT3_KNN_SATELLITE_DIRECT | random | 14.8000 | 12.6575 | 0.2101 | nan | 23.4567 | 0.3192 | 0.1084 |
| CT3_KNN_SATELLITE_DIRECT | spatial | 37.8551 | 30.1670 | 0.2101 | nan | 31.2718 | 0.1190 | 0.0111 |
| CT3_KNN_SATELLITE_WEIGHT | climate_profile | 21.0435 | 17.3774 | 0.2101 | 0.8846 | 26.1965 | 0.2297 | 0.0000 |
| CT3_KNN_SATELLITE_WEIGHT | municipality | 28.0290 | 22.3553 | 0.2101 | 0.3109 | 33.5727 | 0.0000 | 0.0068 |
| CT3_KNN_SATELLITE_WEIGHT | random | 14.8000 | 12.6575 | 0.2101 | 0.8969 | 23.4567 | 0.3192 | 0.1084 |
| CT3_KNN_SATELLITE_WEIGHT | spatial | 37.8551 | 30.1670 | 0.2101 | 0.1692 | 31.2718 | 0.1190 | 0.0111 |
| J7_CLUSTER_GEO_DIRECT | climate_profile | 29.5435 | 29.5435 | 0.0652 | nan | 4.7331 | 0.8315 | 0.0000 |
| J7_CLUSTER_GEO_DIRECT | municipality | 14.7246 | 14.7246 | 0.0000 | nan | 9.7176 | 0.0000 | 0.0518 |
| J7_CLUSTER_GEO_DIRECT | random | 36.6667 | 36.6667 | 0.0051 | nan | 4.2074 | 0.8549 | 0.2917 |
| J7_CLUSTER_GEO_DIRECT | spatial | 29.5435 | 29.5435 | 0.0072 | nan | 14.4012 | 0.4865 | 0.0251 |
| J7_CLUSTER_GEO_WEIGHT | climate_profile | 29.5435 | 29.5435 | 0.0000 | 0.8079 | 4.7331 | 0.8315 | 0.0000 |
| J7_CLUSTER_GEO_WEIGHT | municipality | 14.7246 | 14.7246 | 0.0000 | 0.2622 | 9.7176 | 0.0000 | 0.0518 |
| J7_CLUSTER_GEO_WEIGHT | random | 36.6667 | 36.6667 | 0.0000 | 0.9109 | 4.2074 | 0.8549 | 0.2917 |
| J7_CLUSTER_GEO_WEIGHT | spatial | 29.5435 | 29.5435 | 0.0000 | 0.2206 | 14.4012 | 0.4865 | 0.0251 |
| J7_CLUSTER_PHYSICAL_DIRECT | climate_profile | 20.7174 | 20.7174 | 0.0000 | nan | 11.7671 | 0.4603 | 0.0000 |
| J7_CLUSTER_PHYSICAL_DIRECT | municipality | 24.7681 | 24.7681 | 0.0000 | nan | 24.5643 | 0.0000 | 0.0167 |
| J7_CLUSTER_PHYSICAL_DIRECT | random | 23.7652 | 23.7652 | 0.0029 | nan | 7.9350 | 0.6440 | 0.2939 |
| J7_CLUSTER_PHYSICAL_DIRECT | spatial | 25.0580 | 25.0580 | 0.0000 | nan | 21.3932 | 0.1826 | 0.0276 |
| J7_CLUSTER_PHYSICAL_WEIGHT | climate_profile | 20.7174 | 20.7174 | 0.0000 | 0.7841 | 11.7671 | 0.4603 | 0.0000 |
| J7_CLUSTER_PHYSICAL_WEIGHT | municipality | 24.7681 | 24.7681 | 0.0000 | 0.2602 | 24.5643 | 0.0000 | 0.0167 |
| J7_CLUSTER_PHYSICAL_WEIGHT | random | 23.7652 | 23.7652 | 0.0000 | 0.8705 | 7.9350 | 0.6440 | 0.2939 |
| J7_CLUSTER_PHYSICAL_WEIGHT | spatial | 25.0580 | 25.0580 | 0.0000 | 0.2612 | 21.3932 | 0.1826 | 0.0276 |
| J7_CLUSTER_SATELLITE_DIRECT | climate_profile | 14.3768 | 14.3768 | 0.2101 | nan | 26.5503 | 0.2361 | 0.0000 |
| J7_CLUSTER_SATELLITE_DIRECT | municipality | 17.7391 | 17.7391 | 0.2101 | nan | 33.6302 | 0.0000 | 0.0096 |
| J7_CLUSTER_SATELLITE_DIRECT | random | 14.1159 | 14.1159 | 0.2101 | nan | 23.8014 | 0.3102 | 0.1130 |
| J7_CLUSTER_SATELLITE_DIRECT | spatial | 13.4348 | 13.4348 | 0.2101 | nan | 31.0505 | 0.1349 | 0.0135 |
| J7_CLUSTER_SATELLITE_WEIGHT | climate_profile | 14.3768 | 14.3768 | 0.2101 | 0.9174 | 26.5503 | 0.2361 | 0.0000 |
| J7_CLUSTER_SATELLITE_WEIGHT | municipality | 17.7391 | 17.7391 | 0.2101 | 0.2856 | 33.6302 | 0.0000 | 0.0096 |
| J7_CLUSTER_SATELLITE_WEIGHT | random | 14.1159 | 14.1159 | 0.2101 | 0.8785 | 23.8014 | 0.3102 | 0.1130 |
| J7_CLUSTER_SATELLITE_WEIGHT | spatial | 13.4348 | 13.4348 | 0.2101 | 0.4989 | 31.0505 | 0.1349 | 0.0135 |
| J7_KNN_GEO_DIRECT | climate_profile | 33.6232 | 24.0400 | 0.0000 | nan | 5.8617 | 0.7063 | 0.0000 |
| J7_KNN_GEO_DIRECT | municipality | 59.6884 | 35.8018 | 0.0000 | nan | 27.8429 | 0.0000 | 0.0169 |
| J7_KNN_GEO_DIRECT | random | 55.4203 | 23.3767 | 0.0000 | nan | 10.0685 | 0.6077 | 0.2547 |
| J7_KNN_GEO_DIRECT | spatial | 21.9130 | 21.4170 | 0.0000 | nan | 14.4943 | 0.5151 | 0.0545 |
| J7_KNN_GEO_WEIGHT | climate_profile | 33.6232 | 24.0400 | 0.0000 | 0.8459 | 5.8617 | 0.7063 | 0.0000 |
| J7_KNN_GEO_WEIGHT | municipality | 59.6884 | 35.8018 | 0.0000 | 0.2734 | 27.8429 | 0.0000 | 0.0169 |
| J7_KNN_GEO_WEIGHT | random | 55.4203 | 23.3767 | 0.0000 | 0.8829 | 10.0685 | 0.6077 | 0.2547 |
| J7_KNN_GEO_WEIGHT | spatial | 21.9130 | 21.4170 | 0.0000 | 0.2611 | 14.4943 | 0.5151 | 0.0545 |
| J7_KNN_PHYSICAL_DIRECT | climate_profile | 9.6812 | 9.1729 | 0.0000 | nan | 9.0827 | 0.6110 | 0.0000 |
| J7_KNN_PHYSICAL_DIRECT | municipality | 55.5145 | 53.1138 | 0.0000 | nan | 28.6714 | 0.0000 | 0.0109 |
| J7_KNN_PHYSICAL_DIRECT | random | 49.8319 | 41.3296 | 0.0000 | nan | 15.4223 | 0.4880 | 0.2122 |
| J7_KNN_PHYSICAL_DIRECT | spatial | 44.2899 | 42.1547 | 0.0000 | nan | 28.1037 | 0.1514 | 0.0110 |
| J7_KNN_PHYSICAL_WEIGHT | climate_profile | 9.6812 | 9.1729 | 0.0000 | 0.8364 | 9.0827 | 0.6110 | 0.0000 |
| J7_KNN_PHYSICAL_WEIGHT | municipality | 55.5145 | 53.1138 | 0.0000 | 0.2756 | 28.6714 | 0.0000 | 0.0109 |
| J7_KNN_PHYSICAL_WEIGHT | random | 49.8319 | 41.3296 | 0.0000 | 0.9362 | 15.4223 | 0.4880 | 0.2122 |
| J7_KNN_PHYSICAL_WEIGHT | spatial | 44.2899 | 42.1547 | 0.0000 | 0.5058 | 28.1037 | 0.1514 | 0.0110 |
| J7_KNN_SATELLITE_DIRECT | climate_profile | 8.5217 | 7.7695 | 0.2101 | nan | 26.6942 | 0.2311 | 0.0000 |
| J7_KNN_SATELLITE_DIRECT | municipality | 34.5217 | 27.2805 | 0.2101 | nan | 33.6457 | 0.0000 | 0.0068 |
| J7_KNN_SATELLITE_DIRECT | random | 14.5449 | 12.6147 | 0.2101 | nan | 23.4586 | 0.3195 | 0.1075 |
| J7_KNN_SATELLITE_DIRECT | spatial | 22.6667 | 19.1354 | 0.2101 | nan | 31.7470 | 0.1036 | 0.0109 |
| J7_KNN_SATELLITE_WEIGHT | climate_profile | 8.5217 | 7.7695 | 0.2101 | 0.8763 | 26.6942 | 0.2311 | 0.0000 |
| J7_KNN_SATELLITE_WEIGHT | municipality | 34.5217 | 27.2805 | 0.2101 | 0.2750 | 33.6457 | 0.0000 | 0.0068 |
| J7_KNN_SATELLITE_WEIGHT | random | 14.5449 | 12.6147 | 0.2101 | 0.8819 | 23.4586 | 0.3195 | 0.1075 |
| J7_KNN_SATELLITE_WEIGHT | spatial | 22.6667 | 19.1354 | 0.2101 | 0.6011 | 31.7470 | 0.1036 | 0.0109 |

## Ganancias por parcela

| experiment | protocol | total_sse_gain | hard35_sse_gain | remaining103_sse_gain | fraction_improved | fraction_worsened |
| --- | --- | --- | --- | --- | --- | --- |
| CT3_CLUSTER_GEO_DIRECT | climate_profile | 1.7952 | 1.2618 | 0.5334 | 0.6449 | 0.3551 |
| CT3_CLUSTER_GEO_DIRECT | municipality | 2.5853 | 0.5993 | 1.9860 | 0.6304 | 0.3696 |
| CT3_CLUSTER_GEO_DIRECT | random | 1.8282 | 1.5469 | 0.2813 | 0.5652 | 0.4348 |
| CT3_CLUSTER_GEO_DIRECT | spatial | 0.8491 | -0.4511 | 1.3002 | 0.5652 | 0.4348 |
| CT3_CLUSTER_GEO_WEIGHT | climate_profile | 1.3486 | 1.5887 | -0.2402 | 0.5000 | 0.4783 |
| CT3_CLUSTER_GEO_WEIGHT | municipality | 0.2840 | -0.1087 | 0.3927 | 0.2101 | 0.1377 |
| CT3_CLUSTER_GEO_WEIGHT | random | 1.9525 | 1.8271 | 0.1254 | 0.5652 | 0.4348 |
| CT3_CLUSTER_GEO_WEIGHT | spatial | 0.2906 | 0.3388 | -0.0482 | 0.2754 | 0.1812 |
| CT3_CLUSTER_PHYSICAL_DIRECT | climate_profile | 1.6939 | 1.4067 | 0.2872 | 0.5362 | 0.4638 |
| CT3_CLUSTER_PHYSICAL_DIRECT | municipality | 0.1380 | -0.0983 | 0.2364 | 0.1739 | 0.1232 |
| CT3_CLUSTER_PHYSICAL_DIRECT | random | 1.5977 | 1.4668 | 0.1309 | 0.5725 | 0.4275 |
| CT3_CLUSTER_PHYSICAL_DIRECT | spatial | 0.7275 | 0.4076 | 0.3200 | 0.2609 | 0.1957 |
| CT3_CLUSTER_PHYSICAL_WEIGHT | climate_profile | 0.8542 | 1.1107 | -0.2565 | 0.5145 | 0.4855 |
| CT3_CLUSTER_PHYSICAL_WEIGHT | municipality | 0.4320 | -0.0649 | 0.4969 | 0.1739 | 0.1232 |
| CT3_CLUSTER_PHYSICAL_WEIGHT | random | 1.8655 | 1.7108 | 0.1547 | 0.5725 | 0.4275 |
| CT3_CLUSTER_PHYSICAL_WEIGHT | spatial | 0.5023 | 0.3303 | 0.1719 | 0.2609 | 0.1812 |
| CT3_CLUSTER_SATELLITE_DIRECT | climate_profile | 1.7940 | 1.8918 | -0.0977 | 0.5217 | 0.4783 |
| CT3_CLUSTER_SATELLITE_DIRECT | municipality | 1.8706 | 0.6399 | 1.2307 | 0.2754 | 0.1377 |
| CT3_CLUSTER_SATELLITE_DIRECT | random | 2.1099 | 2.0855 | 0.0244 | 0.5725 | 0.4275 |
| CT3_CLUSTER_SATELLITE_DIRECT | spatial | 0.4426 | 0.6869 | -0.2442 | 0.1739 | 0.1522 |
| CT3_CLUSTER_SATELLITE_WEIGHT | climate_profile | 1.5256 | 1.6377 | -0.1121 | 0.4928 | 0.4710 |
| CT3_CLUSTER_SATELLITE_WEIGHT | municipality | 1.2752 | 0.1991 | 1.0761 | 0.2754 | 0.1304 |
| CT3_CLUSTER_SATELLITE_WEIGHT | random | 1.9118 | 1.8427 | 0.0691 | 0.5797 | 0.4203 |
| CT3_CLUSTER_SATELLITE_WEIGHT | spatial | -0.0011 | 0.5191 | -0.5202 | 0.1014 | 0.1014 |
| CT3_GLOBAL_PCA2 | climate_profile | 1.4209 | 1.0580 | 0.3629 | 0.5725 | 0.4275 |
| CT3_GLOBAL_PCA2 | municipality | 0.3493 | -0.0167 | 0.3660 | 0.1667 | 0.1304 |
| CT3_GLOBAL_PCA2 | random | 1.3474 | 1.1068 | 0.2407 | 0.5942 | 0.4058 |
| CT3_GLOBAL_PCA2 | spatial | -1.4429 | 0.0000 | -1.4429 | 0.0000 | 0.0725 |
| CT3_GLOBAL_R2 | climate_profile | 0.9890 | 1.0860 | -0.0971 | 0.5435 | 0.4565 |
| CT3_GLOBAL_R2 | municipality | 1.0940 | 0.5053 | 0.5887 | 0.2101 | 0.0870 |
| CT3_GLOBAL_R2 | random | 1.0917 | 1.0790 | 0.0126 | 0.5652 | 0.4348 |
| CT3_GLOBAL_R2 | spatial | 0.9936 | 1.5367 | -0.5431 | 0.3116 | 0.2826 |
| CT3_GLOBAL_R3 | climate_profile | 2.2052 | 2.1308 | 0.0744 | 0.5362 | 0.4638 |
| CT3_GLOBAL_R3 | municipality | 1.3818 | 0.6919 | 0.6900 | 0.1957 | 0.1014 |
| CT3_GLOBAL_R3 | random | 2.0546 | 2.0618 | -0.0072 | 0.5652 | 0.4348 |
| CT3_GLOBAL_R3 | spatial | 0.4063 | 0.7004 | -0.2941 | 0.1739 | 0.1522 |
| CT3_GLOBAL_R4 | climate_profile | 1.4761 | 1.7402 | -0.2640 | 0.5072 | 0.4928 |
| CT3_GLOBAL_R4 | municipality | 1.5724 | 0.3752 | 1.1972 | 0.2826 | 0.1304 |
| CT3_GLOBAL_R4 | random | 2.0459 | 1.9728 | 0.0732 | 0.5652 | 0.4348 |
| CT3_GLOBAL_R4 | spatial | -0.0868 | 0.3631 | -0.4499 | 0.1594 | 0.1667 |
| CT3_GLOBAL_R9 | climate_profile | -0.4433 | 0.5245 | -0.9678 | 0.2681 | 0.3043 |
| CT3_GLOBAL_R9 | municipality | -0.2215 | -0.3310 | 0.1095 | 0.1377 | 0.1594 |
| CT3_GLOBAL_R9 | random | 0.1571 | 0.3387 | -0.1817 | 0.5362 | 0.4638 |
| CT3_GLOBAL_R9 | spatial | -0.2976 | 0.2677 | -0.5654 | 0.1449 | 0.1812 |
| CT3_KNN_GEO_DIRECT | climate_profile | 2.3793 | 1.6163 | 0.7629 | 0.6014 | 0.3986 |
| CT3_KNN_GEO_DIRECT | municipality | 0.7229 | 0.2006 | 0.5224 | 0.2246 | 0.1449 |
| CT3_KNN_GEO_DIRECT | random | 2.4351 | 2.1267 | 0.3085 | 0.5725 | 0.4275 |
| CT3_KNN_GEO_DIRECT | spatial | 2.0708 | 0.5964 | 1.4744 | 0.6232 | 0.3768 |
| CT3_KNN_GEO_WEIGHT | climate_profile | 1.4187 | 1.5934 | -0.1747 | 0.5072 | 0.4855 |
| CT3_KNN_GEO_WEIGHT | municipality | 0.2382 | -0.1941 | 0.4324 | 0.1739 | 0.1232 |
| CT3_KNN_GEO_WEIGHT | random | 1.9727 | 1.9070 | 0.0657 | 0.5725 | 0.4275 |
| CT3_KNN_GEO_WEIGHT | spatial | -0.1727 | 0.0111 | -0.1838 | 0.2246 | 0.1957 |
| CT3_KNN_PHYSICAL_DIRECT | climate_profile | 2.1422 | 2.1149 | 0.0273 | 0.5725 | 0.4275 |
| CT3_KNN_PHYSICAL_DIRECT | municipality | 1.9104 | 0.5277 | 1.3827 | 0.2971 | 0.1159 |
| CT3_KNN_PHYSICAL_DIRECT | random | 2.0764 | 1.8818 | 0.1947 | 0.5797 | 0.4203 |
| CT3_KNN_PHYSICAL_DIRECT | spatial | 1.2220 | 0.7773 | 0.4446 | 0.2681 | 0.1884 |
| CT3_KNN_PHYSICAL_WEIGHT | climate_profile | 1.4386 | 1.6960 | -0.2574 | 0.5072 | 0.4928 |
| CT3_KNN_PHYSICAL_WEIGHT | municipality | 1.2200 | 0.2344 | 0.9856 | 0.2826 | 0.1304 |
| CT3_KNN_PHYSICAL_WEIGHT | random | 2.0059 | 1.9093 | 0.0965 | 0.5725 | 0.4275 |
| CT3_KNN_PHYSICAL_WEIGHT | spatial | -0.1559 | 0.3611 | -0.5170 | 0.2681 | 0.1739 |
| CT3_KNN_SATELLITE_DIRECT | climate_profile | 1.9357 | 2.1769 | -0.2412 | 0.5797 | 0.4203 |
| CT3_KNN_SATELLITE_DIRECT | municipality | 1.9915 | 0.6442 | 1.3473 | 0.2754 | 0.1377 |
| CT3_KNN_SATELLITE_DIRECT | random | 2.5169 | 2.3880 | 0.1290 | 0.5870 | 0.4130 |
| CT3_KNN_SATELLITE_DIRECT | spatial | 1.3666 | 1.1253 | 0.2413 | 0.2681 | 0.1884 |
| CT3_KNN_SATELLITE_WEIGHT | climate_profile | 1.8082 | 1.8800 | -0.0718 | 0.5000 | 0.4783 |
| CT3_KNN_SATELLITE_WEIGHT | municipality | 1.3777 | 0.3159 | 1.0618 | 0.2681 | 0.1304 |
| CT3_KNN_SATELLITE_WEIGHT | random | 2.0556 | 1.9571 | 0.0985 | 0.5507 | 0.4493 |
| CT3_KNN_SATELLITE_WEIGHT | spatial | 0.8764 | 0.9248 | -0.0484 | 0.2609 | 0.1739 |
| J7_CLUSTER_GEO_DIRECT | climate_profile | 1.2745 | 1.3276 | -0.0531 | 0.5797 | 0.4203 |
| J7_CLUSTER_GEO_DIRECT | municipality | -0.2850 | -0.4988 | 0.2138 | 0.2101 | 0.1594 |
| J7_CLUSTER_GEO_DIRECT | random | 0.9893 | 1.2898 | -0.3005 | 0.4928 | 0.5072 |
| J7_CLUSTER_GEO_DIRECT | spatial | -0.7906 | 0.6373 | -1.4280 | 0.4348 | 0.4928 |
| J7_CLUSTER_GEO_WEIGHT | climate_profile | 1.4354 | 1.6302 | -0.1947 | 0.5652 | 0.4348 |
| J7_CLUSTER_GEO_WEIGHT | municipality | 0.2619 | -0.2828 | 0.5448 | 0.1739 | 0.1377 |
| J7_CLUSTER_GEO_WEIGHT | random | 1.3303 | 1.5012 | -0.1709 | 0.5145 | 0.4855 |
| J7_CLUSTER_GEO_WEIGHT | spatial | 4.7455 | 1.7056 | 3.0398 | 0.2609 | 0.1159 |
| J7_CLUSTER_PHYSICAL_DIRECT | climate_profile | 1.2514 | 1.2865 | -0.0351 | 0.5797 | 0.4203 |
| J7_CLUSTER_PHYSICAL_DIRECT | municipality | 0.3184 | -0.1625 | 0.4809 | 0.1739 | 0.1232 |
| J7_CLUSTER_PHYSICAL_DIRECT | random | 0.9469 | 1.1465 | -0.1996 | 0.5000 | 0.5000 |
| J7_CLUSTER_PHYSICAL_DIRECT | spatial | 0.8449 | 1.5367 | -0.6917 | 0.4058 | 0.3261 |
| J7_CLUSTER_PHYSICAL_WEIGHT | climate_profile | 1.3985 | 1.5738 | -0.1752 | 0.5725 | 0.4275 |
| J7_CLUSTER_PHYSICAL_WEIGHT | municipality | 0.5755 | -0.1094 | 0.6849 | 0.1739 | 0.1232 |
| J7_CLUSTER_PHYSICAL_WEIGHT | random | 1.2142 | 1.4038 | -0.1896 | 0.5145 | 0.4855 |
| J7_CLUSTER_PHYSICAL_WEIGHT | spatial | 1.2380 | 1.2085 | 0.0295 | 0.4130 | 0.3116 |
| J7_CLUSTER_SATELLITE_DIRECT | climate_profile | 1.7763 | 2.0331 | -0.2568 | 0.5435 | 0.4565 |
| J7_CLUSTER_SATELLITE_DIRECT | municipality | 0.6606 | 0.0476 | 0.6131 | 0.1739 | 0.1232 |
| J7_CLUSTER_SATELLITE_DIRECT | random | 1.5460 | 1.8083 | -0.2624 | 0.5362 | 0.4638 |
| J7_CLUSTER_SATELLITE_DIRECT | spatial | 5.1582 | 3.7902 | 1.3680 | 0.5145 | 0.4855 |
| J7_CLUSTER_SATELLITE_WEIGHT | climate_profile | 1.7368 | 1.9364 | -0.1996 | 0.5652 | 0.4348 |
| J7_CLUSTER_SATELLITE_WEIGHT | municipality | 0.5109 | -0.2748 | 0.7858 | 0.1739 | 0.1232 |
| J7_CLUSTER_SATELLITE_WEIGHT | random | 1.3831 | 1.5163 | -0.1332 | 0.5145 | 0.4855 |
| J7_CLUSTER_SATELLITE_WEIGHT | spatial | 3.6145 | 3.1024 | 0.5121 | 0.4420 | 0.4420 |
| J7_GLOBAL_PCA2 | climate_profile | 0.6810 | 0.8932 | -0.2122 | 0.4348 | 0.3841 |
| J7_GLOBAL_PCA2 | municipality | 0.3494 | -0.0448 | 0.3942 | 0.1594 | 0.1377 |
| J7_GLOBAL_PCA2 | random | 0.9204 | 0.8475 | 0.0729 | 0.6014 | 0.3986 |
| J7_GLOBAL_PCA2 | spatial | -2.2828 | 0.0000 | -2.2828 | 0.0000 | 0.0725 |
| J7_GLOBAL_R2 | climate_profile | 1.1749 | 1.2100 | -0.0351 | 0.5725 | 0.4275 |
| J7_GLOBAL_R2 | municipality | 0.9929 | 0.3681 | 0.6248 | 0.2029 | 0.0942 |
| J7_GLOBAL_R2 | random | 0.8245 | 0.9325 | -0.1080 | 0.5217 | 0.4783 |
| J7_GLOBAL_R2 | spatial | 5.1578 | 4.6283 | 0.5295 | 0.5652 | 0.4348 |
| J7_GLOBAL_R3 | climate_profile | 1.8879 | 2.0663 | -0.1784 | 0.5435 | 0.4565 |
| J7_GLOBAL_R3 | municipality | 1.3156 | 0.5648 | 0.7507 | 0.2029 | 0.0942 |
| J7_GLOBAL_R3 | random | 1.4299 | 1.7344 | -0.3046 | 0.5217 | 0.4783 |
| J7_GLOBAL_R3 | spatial | 4.7568 | 3.8747 | 0.8821 | 0.5362 | 0.4638 |
| J7_GLOBAL_R4 | climate_profile | 1.6640 | 1.8512 | -0.1872 | 0.5652 | 0.4348 |
| J7_GLOBAL_R4 | municipality | 0.4195 | -0.2748 | 0.6943 | 0.1739 | 0.1232 |
| J7_GLOBAL_R4 | random | 1.4522 | 1.6461 | -0.1939 | 0.5072 | 0.4928 |
| J7_GLOBAL_R4 | spatial | 3.5751 | 3.5231 | 0.0520 | 0.5000 | 0.5000 |
| J7_GLOBAL_R9 | climate_profile | -0.0460 | 0.4556 | -0.5017 | 0.4348 | 0.3841 |
| J7_GLOBAL_R9 | municipality | -0.0325 | -0.3561 | 0.3236 | 0.1449 | 0.1522 |
| J7_GLOBAL_R9 | random | 0.1239 | 0.3322 | -0.2083 | 0.4565 | 0.5435 |
| J7_GLOBAL_R9 | spatial | 1.9288 | 1.8297 | 0.0991 | 0.4058 | 0.3261 |
| J7_KNN_GEO_DIRECT | climate_profile | 1.2784 | 1.5531 | -0.2747 | 0.5290 | 0.4710 |
| J7_KNN_GEO_DIRECT | municipality | 0.4121 | 0.1146 | 0.2975 | 0.2319 | 0.1377 |
| J7_KNN_GEO_DIRECT | random | 1.0375 | 1.4977 | -0.4602 | 0.4783 | 0.5217 |
| J7_KNN_GEO_DIRECT | spatial | 3.0477 | 2.4280 | 0.6197 | 0.5217 | 0.4058 |
| J7_KNN_GEO_WEIGHT | climate_profile | 1.6273 | 1.7953 | -0.1680 | 0.5652 | 0.4348 |
| J7_KNN_GEO_WEIGHT | municipality | 0.3543 | -0.2748 | 0.6291 | 0.1739 | 0.1232 |
| J7_KNN_GEO_WEIGHT | random | 1.3399 | 1.4973 | -0.1574 | 0.5290 | 0.4710 |
| J7_KNN_GEO_WEIGHT | spatial | 3.1960 | 1.3365 | 1.8595 | 0.4130 | 0.2391 |
| J7_KNN_PHYSICAL_DIRECT | climate_profile | 1.7562 | 1.9217 | -0.1655 | 0.5580 | 0.4420 |
| J7_KNN_PHYSICAL_DIRECT | municipality | 0.7768 | -0.1113 | 0.8880 | 0.1884 | 0.1087 |
| J7_KNN_PHYSICAL_DIRECT | random | 1.0639 | 1.3930 | -0.3291 | 0.4783 | 0.5217 |
| J7_KNN_PHYSICAL_DIRECT | spatial | 4.0571 | 2.7226 | 1.3345 | 0.4058 | 0.3261 |
| J7_KNN_PHYSICAL_WEIGHT | climate_profile | 1.4875 | 1.6607 | -0.1732 | 0.5652 | 0.4348 |
| J7_KNN_PHYSICAL_WEIGHT | municipality | 0.6453 | -0.0650 | 0.7103 | 0.1739 | 0.1232 |
| J7_KNN_PHYSICAL_WEIGHT | random | 1.3931 | 1.5527 | -0.1596 | 0.5217 | 0.4783 |
| J7_KNN_PHYSICAL_WEIGHT | spatial | 3.8490 | 2.6735 | 1.1755 | 0.4130 | 0.3188 |
| J7_KNN_SATELLITE_DIRECT | climate_profile | 1.9303 | 2.0846 | -0.1544 | 0.5652 | 0.4348 |
| J7_KNN_SATELLITE_DIRECT | municipality | 0.6671 | -0.0129 | 0.6800 | 0.1667 | 0.1304 |
| J7_KNN_SATELLITE_DIRECT | random | 1.8406 | 2.0608 | -0.2202 | 0.5145 | 0.4855 |
| J7_KNN_SATELLITE_DIRECT | spatial | 5.0041 | 3.7888 | 1.2153 | 0.5145 | 0.4855 |
| J7_KNN_SATELLITE_WEIGHT | climate_profile | 1.7229 | 1.9150 | -0.1921 | 0.5652 | 0.4348 |
| J7_KNN_SATELLITE_WEIGHT | municipality | 0.6312 | -0.1421 | 0.7733 | 0.1739 | 0.1232 |
| J7_KNN_SATELLITE_WEIGHT | random | 1.4550 | 1.6254 | -0.1704 | 0.5072 | 0.4928 |
| J7_KNN_SATELLITE_WEIGHT | spatial | 3.8191 | 3.6228 | 0.1963 | 0.4710 | 0.4638 |

208pruebas pareadas con Holm, omisiones, métricas sin35/sin10/sin171/015, regiones, intraperfil y selección interna están en las tablas/Excel. No se selecciona un Champion con estos resultados exploratorios.