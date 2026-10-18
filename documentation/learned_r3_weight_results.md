> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Pesos aprendidos y asimetría R3: resultados exploratorios

33 entradas: 24 nuevas y nueve referencias exactas; mismos 65 folds. Métricas por OOF completas de cada repetición, nunca media de errores por fold. BASE=base original; GLOBAL_GLOBAL=R3 global anterior; SATELLITE_SUPPORT=peso fijo anterior; MASK=sólo disponibilidad; CONSTANT=peso escalar aprendido; ASYM=pesos por signo; LEARNED=peso condicionado; LEARNED_ASYM=condicionado por signo. P1/P10 son sensibilidades fijas, no penalizaciones seleccionadas. Diseño inicial y enmienda previa a resultados deben leerse juntos.

| experiment | random | climate_profile | municipality | spatial |
| --- | --- | --- | --- | --- |
| CT3_ASYM_P1 | 0.4971 / 0.6564 | 0.5057 / 0.6444 | 0.5696 / 0.5489 | 0.6811 / 0.3551 |
| CT3_ASYM_P10 | 0.4970 / 0.6565 | 0.5054 / 0.6449 | 0.5706 / 0.5474 | 0.6771 / 0.3626 |
| CT3_BASE | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| CT3_CONSTANT | 0.4970 / 0.6565 | 0.5054 / 0.6449 | 0.5708 / 0.5470 | 0.6763 / 0.3641 |
| CT3_GLOBAL_GLOBAL | 0.4968 / 0.6568 | 0.5050 / 0.6454 | 0.5726 / 0.5442 | 0.6766 / 0.3635 |
| CT3_LEARNED_ASYM_P1 | 0.4975 / 0.6558 | 0.5101 / 0.6382 | 0.5668 / 0.5533 | 0.6620 / 0.3907 |
| CT3_LEARNED_ASYM_P10 | 0.4971 / 0.6564 | 0.5060 / 0.6440 | 0.5690 / 0.5498 | 0.6762 / 0.3642 |
| CT3_LEARNED_P1 | 0.4974 / 0.6560 | 0.5056 / 0.6445 | 0.5674 / 0.5524 | 0.6661 / 0.3831 |
| CT3_LEARNED_P10 | 0.4970 / 0.6565 | 0.5052 / 0.6452 | 0.5703 / 0.5477 | 0.6727 / 0.3707 |
| CT3_MASK | 0.4961 / 0.6578 | 0.5033 / 0.6478 | 0.5668 / 0.5533 | 0.6668 / 0.3818 |
| CT3_SATELLITE_SUPPORT | 0.5016 / 0.6502 | 0.5096 / 0.6390 | 0.5706 / 0.5472 | 0.6581 / 0.3979 |
| J7_ASYM_P1 | 0.4758 / 0.6851 | 0.4749 / 0.6865 | 0.5726 / 0.5441 | 0.6583 / 0.3975 |
| J7_ASYM_P10 | 0.4757 / 0.6853 | 0.4747 / 0.6866 | 0.5726 / 0.5442 | 0.6644 / 0.3863 |
| J7_BASE | 0.4864 / 0.6709 | 0.4890 / 0.6675 | 0.5808 / 0.5309 | 0.6808 / 0.3556 |
| J7_CONSTANT | 0.4757 / 0.6853 | 0.4747 / 0.6866 | 0.5726 / 0.5442 | 0.6662 / 0.3830 |
| J7_GLOBAL_GLOBAL | 0.4756 / 0.6854 | 0.4748 / 0.6865 | 0.5726 / 0.5442 | 0.6550 / 0.4035 |
| J7_LEARNED_ASYM_P1 | 0.4763 / 0.6844 | 0.4748 / 0.6866 | 0.5731 / 0.5434 | 0.6549 / 0.4036 |
| J7_LEARNED_ASYM_P10 | 0.4759 / 0.6850 | 0.4749 / 0.6864 | 0.5732 / 0.5432 | 0.6563 / 0.4011 |
| J7_LEARNED_P1 | 0.4760 / 0.6849 | 0.4741 / 0.6875 | 0.5746 / 0.5410 | 0.6623 / 0.3901 |
| J7_LEARNED_P10 | 0.4757 / 0.6852 | 0.4745 / 0.6869 | 0.5728 / 0.5438 | 0.6612 / 0.3922 |
| J7_MASK | 0.4749 / 0.6863 | 0.4752 / 0.6861 | 0.5727 / 0.5440 | 0.6521 / 0.4087 |
| J7_SATELLITE_SUPPORT | 0.4792 / 0.6806 | 0.4789 / 0.6812 | 0.5744 / 0.5412 | 0.6440 / 0.4234 |
| SHARES_ASYM_P1 | 0.4757 / 0.6852 | 0.4772 / 0.6833 | 0.5754 / 0.5397 | 0.6408 / 0.4291 |
| SHARES_ASYM_P10 | 0.4755 / 0.6855 | 0.4772 / 0.6834 | 0.5751 / 0.5401 | 0.6498 / 0.4130 |
| SHARES_BASE | 0.4865 / 0.6708 | 0.4913 / 0.6644 | 0.5835 / 0.5266 | 0.6894 / 0.3393 |
| SHARES_CONSTANT | 0.4755 / 0.6855 | 0.4772 / 0.6834 | 0.5751 / 0.5402 | 0.6539 / 0.4055 |
| SHARES_GLOBAL_GLOBAL | 0.4753 / 0.6858 | 0.4772 / 0.6834 | 0.5751 / 0.5402 | 0.6447 / 0.4221 |
| SHARES_LEARNED_ASYM_P1 | 0.4763 / 0.6845 | 0.4768 / 0.6839 | 0.5805 / 0.5315 | 0.6474 / 0.4172 |
| SHARES_LEARNED_ASYM_P10 | 0.4758 / 0.6851 | 0.4773 / 0.6832 | 0.5774 / 0.5364 | 0.6419 / 0.4270 |
| SHARES_LEARNED_P1 | 0.4759 / 0.6850 | 0.4763 / 0.6846 | 0.5781 / 0.5354 | 0.6526 / 0.4078 |
| SHARES_LEARNED_P10 | 0.4756 / 0.6854 | 0.4771 / 0.6836 | 0.5753 / 0.5398 | 0.6453 / 0.4210 |
| SHARES_MASK | 0.4748 / 0.6865 | 0.4774 / 0.6831 | 0.5752 / 0.5400 | 0.6333 / 0.4423 |
| SHARES_SATELLITE_SUPPORT | 0.4792 / 0.6807 | 0.4808 / 0.6786 | 0.5771 / 0.5370 | 0.6412 / 0.4283 |

## Activación / aplicación

| experiment | protocol | active_folds | total_folds |
| --- | --- | --- | --- |
| CT3_ASYM_P1 | climate_profile | 5 | 5 |
| CT3_ASYM_P1 | municipality | 5 | 5 |
| CT3_ASYM_P1 | random | 50 | 50 |
| CT3_ASYM_P1 | spatial | 5 | 5 |
| CT3_ASYM_P10 | climate_profile | 5 | 5 |
| CT3_ASYM_P10 | municipality | 5 | 5 |
| CT3_ASYM_P10 | random | 50 | 50 |
| CT3_ASYM_P10 | spatial | 5 | 5 |
| CT3_CONSTANT | climate_profile | 5 | 5 |
| CT3_CONSTANT | municipality | 5 | 5 |
| CT3_CONSTANT | random | 50 | 50 |
| CT3_CONSTANT | spatial | 5 | 5 |
| CT3_LEARNED_ASYM_P1 | climate_profile | 5 | 5 |
| CT3_LEARNED_ASYM_P1 | municipality | 5 | 5 |
| CT3_LEARNED_ASYM_P1 | random | 50 | 50 |
| CT3_LEARNED_ASYM_P1 | spatial | 5 | 5 |
| CT3_LEARNED_ASYM_P10 | climate_profile | 5 | 5 |
| CT3_LEARNED_ASYM_P10 | municipality | 5 | 5 |
| CT3_LEARNED_ASYM_P10 | random | 50 | 50 |
| CT3_LEARNED_ASYM_P10 | spatial | 5 | 5 |
| CT3_LEARNED_P1 | climate_profile | 5 | 5 |
| CT3_LEARNED_P1 | municipality | 5 | 5 |
| CT3_LEARNED_P1 | random | 50 | 50 |
| CT3_LEARNED_P1 | spatial | 5 | 5 |
| CT3_LEARNED_P10 | climate_profile | 5 | 5 |
| CT3_LEARNED_P10 | municipality | 5 | 5 |
| CT3_LEARNED_P10 | random | 50 | 50 |
| CT3_LEARNED_P10 | spatial | 5 | 5 |
| CT3_MASK | climate_profile | 5 | 5 |
| CT3_MASK | municipality | 3 | 5 |
| CT3_MASK | random | 50 | 50 |
| CT3_MASK | spatial | 4 | 5 |
| J7_ASYM_P1 | climate_profile | 5 | 5 |
| J7_ASYM_P1 | municipality | 5 | 5 |
| J7_ASYM_P1 | random | 50 | 50 |
| J7_ASYM_P1 | spatial | 5 | 5 |
| J7_ASYM_P10 | climate_profile | 5 | 5 |
| J7_ASYM_P10 | municipality | 5 | 5 |
| J7_ASYM_P10 | random | 50 | 50 |
| J7_ASYM_P10 | spatial | 5 | 5 |
| J7_CONSTANT | climate_profile | 5 | 5 |
| J7_CONSTANT | municipality | 5 | 5 |
| J7_CONSTANT | random | 50 | 50 |
| J7_CONSTANT | spatial | 5 | 5 |
| J7_LEARNED_ASYM_P1 | climate_profile | 5 | 5 |
| J7_LEARNED_ASYM_P1 | municipality | 5 | 5 |
| J7_LEARNED_ASYM_P1 | random | 50 | 50 |
| J7_LEARNED_ASYM_P1 | spatial | 5 | 5 |
| J7_LEARNED_ASYM_P10 | climate_profile | 5 | 5 |
| J7_LEARNED_ASYM_P10 | municipality | 5 | 5 |
| J7_LEARNED_ASYM_P10 | random | 50 | 50 |
| J7_LEARNED_ASYM_P10 | spatial | 5 | 5 |
| J7_LEARNED_P1 | climate_profile | 5 | 5 |
| J7_LEARNED_P1 | municipality | 5 | 5 |
| J7_LEARNED_P1 | random | 50 | 50 |
| J7_LEARNED_P1 | spatial | 5 | 5 |
| J7_LEARNED_P10 | climate_profile | 5 | 5 |
| J7_LEARNED_P10 | municipality | 5 | 5 |
| J7_LEARNED_P10 | random | 50 | 50 |
| J7_LEARNED_P10 | spatial | 5 | 5 |
| J7_MASK | climate_profile | 5 | 5 |
| J7_MASK | municipality | 2 | 5 |
| J7_MASK | random | 50 | 50 |
| J7_MASK | spatial | 5 | 5 |
| SHARES_ASYM_P1 | climate_profile | 5 | 5 |
| SHARES_ASYM_P1 | municipality | 5 | 5 |
| SHARES_ASYM_P1 | random | 50 | 50 |
| SHARES_ASYM_P1 | spatial | 5 | 5 |
| SHARES_ASYM_P10 | climate_profile | 5 | 5 |
| SHARES_ASYM_P10 | municipality | 5 | 5 |
| SHARES_ASYM_P10 | random | 50 | 50 |
| SHARES_ASYM_P10 | spatial | 5 | 5 |
| SHARES_CONSTANT | climate_profile | 5 | 5 |
| SHARES_CONSTANT | municipality | 5 | 5 |
| SHARES_CONSTANT | random | 50 | 50 |
| SHARES_CONSTANT | spatial | 5 | 5 |
| SHARES_LEARNED_ASYM_P1 | climate_profile | 5 | 5 |
| SHARES_LEARNED_ASYM_P1 | municipality | 5 | 5 |
| SHARES_LEARNED_ASYM_P1 | random | 50 | 50 |
| SHARES_LEARNED_ASYM_P1 | spatial | 5 | 5 |
| SHARES_LEARNED_ASYM_P10 | climate_profile | 5 | 5 |
| SHARES_LEARNED_ASYM_P10 | municipality | 5 | 5 |
| SHARES_LEARNED_ASYM_P10 | random | 50 | 50 |
| SHARES_LEARNED_ASYM_P10 | spatial | 5 | 5 |
| SHARES_LEARNED_P1 | climate_profile | 5 | 5 |
| SHARES_LEARNED_P1 | municipality | 5 | 5 |
| SHARES_LEARNED_P1 | random | 50 | 50 |
| SHARES_LEARNED_P1 | spatial | 5 | 5 |
| SHARES_LEARNED_P10 | climate_profile | 5 | 5 |
| SHARES_LEARNED_P10 | municipality | 5 | 5 |
| SHARES_LEARNED_P10 | random | 50 | 50 |
| SHARES_LEARNED_P10 | spatial | 5 | 5 |
| SHARES_MASK | climate_profile | 5 | 5 |
| SHARES_MASK | municipality | 2 | 5 |
| SHARES_MASK | random | 50 | 50 |
| SHARES_MASK | spatial | 5 | 5 |

La intensidad MASK se selecciona con propuestas R3 OOF internas. Los otros pesos se ajustan una vez sobre las entradas cross-fitted del entrenamiento externo, con penalización fija: su error de ajuste no es validación interna del metamodelo y no se usa para elegir penalización. La base sin corrección es un control explícito, no un apagado elegido por CV para esos pesos.

## Pesos y utilidad de las propuestas

| experiment | protocol | weight_if_proposal_helps | weight_if_proposal_harms | mean_weight |
| --- | --- | --- | --- | --- |
| CT3_ASYM_P1 | climate_profile | 0.9566 | 0.9695 | 0.9626 |
| CT3_ASYM_P1 | municipality | 0.4311 | 0.2294 | 0.3376 |
| CT3_ASYM_P1 | random | 0.9897 | 0.9880 | 0.9889 |
| CT3_ASYM_P1 | spatial | 0.1897 | 0.3284 | 0.2520 |
| CT3_ASYM_P10 | climate_profile | 0.9623 | 0.9715 | 0.9666 |
| CT3_ASYM_P10 | municipality | 0.4001 | 0.2225 | 0.3177 |
| CT3_ASYM_P10 | random | 0.9906 | 0.9910 | 0.9908 |
| CT3_ASYM_P10 | spatial | 0.1761 | 0.2634 | 0.2153 |
| CT3_CONSTANT | climate_profile | 0.9464 | 0.9587 | 0.9521 |
| CT3_CONSTANT | municipality | 0.3932 | 0.2209 | 0.3133 |
| CT3_CONSTANT | random | 0.9898 | 0.9913 | 0.9905 |
| CT3_CONSTANT | spatial | 0.1731 | 0.2489 | 0.2071 |
| CT3_LEARNED_ASYM_P1 | climate_profile | 0.6932 | 0.7241 | 0.7075 |
| CT3_LEARNED_ASYM_P1 | municipality | 0.5520 | 0.3263 | 0.4473 |
| CT3_LEARNED_ASYM_P1 | random | 0.9286 | 0.9267 | 0.9277 |
| CT3_LEARNED_ASYM_P1 | spatial | 0.6228 | 0.7664 | 0.6873 |
| CT3_LEARNED_ASYM_P10 | climate_profile | 0.9467 | 0.9682 | 0.9567 |
| CT3_LEARNED_ASYM_P10 | municipality | 0.4400 | 0.2313 | 0.3432 |
| CT3_LEARNED_ASYM_P10 | random | 0.9879 | 0.9887 | 0.9883 |
| CT3_LEARNED_ASYM_P10 | spatial | 0.2260 | 0.3811 | 0.2957 |
| CT3_LEARNED_P1 | climate_profile | 0.8537 | 0.8089 | 0.8329 |
| CT3_LEARNED_P1 | municipality | 0.5544 | 0.3261 | 0.4485 |
| CT3_LEARNED_P1 | random | 0.9525 | 0.9463 | 0.9497 |
| CT3_LEARNED_P1 | spatial | 0.8366 | 0.9412 | 0.8836 |
| CT3_LEARNED_P10 | climate_profile | 0.9685 | 0.9723 | 0.9703 |
| CT3_LEARNED_P10 | municipality | 0.4022 | 0.2295 | 0.3222 |
| CT3_LEARNED_P10 | random | 0.9927 | 0.9926 | 0.9927 |
| CT3_LEARNED_P10 | spatial | 0.2841 | 0.3659 | 0.3208 |
| CT3_MASK | climate_profile | 0.8514 | 0.7188 | 0.7899 |
| CT3_MASK | municipality | 0.4257 | 0.2266 | 0.3333 |
| CT3_MASK | random | 0.8305 | 0.7399 | 0.7899 |
| CT3_MASK | spatial | 0.3224 | 0.3226 | 0.3225 |
| J7_ASYM_P1 | climate_profile | 0.9404 | 0.9331 | 0.9371 |
| J7_ASYM_P1 | municipality | 0.3227 | 0.2070 | 0.2741 |
| J7_ASYM_P1 | random | 0.9753 | 0.9717 | 0.9736 |
| J7_ASYM_P1 | spatial | 0.5688 | 0.5717 | 0.5702 |
| J7_ASYM_P10 | climate_profile | 0.9199 | 0.9230 | 0.9213 |
| J7_ASYM_P10 | municipality | 0.3450 | 0.2210 | 0.2929 |
| J7_ASYM_P10 | random | 0.9802 | 0.9816 | 0.9809 |
| J7_ASYM_P10 | spatial | 0.4866 | 0.5486 | 0.5167 |
| J7_CONSTANT | climate_profile | 0.9153 | 0.9208 | 0.9178 |
| J7_CONSTANT | municipality | 0.3500 | 0.2241 | 0.2971 |
| J7_CONSTANT | random | 0.9796 | 0.9821 | 0.9808 |
| J7_CONSTANT | spatial | 0.4733 | 0.5544 | 0.5127 |
| J7_LEARNED_ASYM_P1 | climate_profile | 0.9460 | 0.9359 | 0.9414 |
| J7_LEARNED_ASYM_P1 | municipality | 0.3748 | 0.2915 | 0.3398 |
| J7_LEARNED_ASYM_P1 | random | 0.9291 | 0.9233 | 0.9263 |
| J7_LEARNED_ASYM_P1 | spatial | 0.7679 | 0.7535 | 0.7609 |
| J7_LEARNED_ASYM_P10 | climate_profile | 0.9462 | 0.9419 | 0.9442 |
| J7_LEARNED_ASYM_P10 | municipality | 0.3388 | 0.2357 | 0.2955 |
| J7_LEARNED_ASYM_P10 | random | 0.9785 | 0.9794 | 0.9790 |
| J7_LEARNED_ASYM_P10 | spatial | 0.6766 | 0.6643 | 0.6706 |
| J7_LEARNED_P1 | climate_profile | 0.9734 | 0.9736 | 0.9735 |
| J7_LEARNED_P1 | municipality | 0.3301 | 0.2490 | 0.2960 |
| J7_LEARNED_P1 | random | 0.9693 | 0.9612 | 0.9654 |
| J7_LEARNED_P1 | spatial | 0.7359 | 0.8519 | 0.7922 |
| J7_LEARNED_P10 | climate_profile | 0.9310 | 0.9348 | 0.9327 |
| J7_LEARNED_P10 | municipality | 0.3426 | 0.2241 | 0.2928 |
| J7_LEARNED_P10 | random | 0.9878 | 0.9909 | 0.9893 |
| J7_LEARNED_P10 | spatial | 0.5812 | 0.6299 | 0.6048 |
| J7_MASK | climate_profile | 0.7133 | 0.7143 | 0.7138 |
| J7_MASK | municipality | 0.3250 | 0.2241 | 0.2826 |
| J7_MASK | random | 0.8244 | 0.7530 | 0.7899 |
| J7_MASK | spatial | 0.5845 | 0.5149 | 0.5507 |
| SHARES_ASYM_P1 | climate_profile | 0.9165 | 0.9232 | 0.9194 |
| SHARES_ASYM_P1 | municipality | 0.3198 | 0.2144 | 0.2762 |
| SHARES_ASYM_P1 | random | 0.9791 | 0.9762 | 0.9778 |
| SHARES_ASYM_P1 | spatial | 0.6429 | 0.5527 | 0.6063 |
| SHARES_ASYM_P10 | climate_profile | 0.9071 | 0.9167 | 0.9112 |
| SHARES_ASYM_P10 | municipality | 0.3410 | 0.2256 | 0.2933 |
| SHARES_ASYM_P10 | random | 0.9842 | 0.9846 | 0.9844 |
| SHARES_ASYM_P10 | spatial | 0.5417 | 0.4987 | 0.5243 |
| SHARES_CONSTANT | climate_profile | 0.9051 | 0.9153 | 0.9094 |
| SHARES_CONSTANT | municipality | 0.3457 | 0.2281 | 0.2971 |
| SHARES_CONSTANT | random | 0.9843 | 0.9851 | 0.9847 |
| SHARES_CONSTANT | spatial | 0.5069 | 0.4913 | 0.5006 |
| SHARES_LEARNED_ASYM_P1 | climate_profile | 0.9622 | 0.9472 | 0.9558 |
| SHARES_LEARNED_ASYM_P1 | municipality | 0.3416 | 0.3275 | 0.3358 |
| SHARES_LEARNED_ASYM_P1 | random | 0.9239 | 0.9254 | 0.9247 |
| SHARES_LEARNED_ASYM_P1 | spatial | 0.7162 | 0.7081 | 0.7129 |
| SHARES_LEARNED_ASYM_P10 | climate_profile | 0.9246 | 0.9316 | 0.9276 |
| SHARES_LEARNED_ASYM_P10 | municipality | 0.3311 | 0.2580 | 0.3009 |
| SHARES_LEARNED_ASYM_P10 | random | 0.9817 | 0.9844 | 0.9830 |
| SHARES_LEARNED_ASYM_P10 | spatial | 0.6779 | 0.6280 | 0.6576 |
| SHARES_LEARNED_P1 | climate_profile | 0.9663 | 0.9673 | 0.9667 |
| SHARES_LEARNED_P1 | municipality | 0.3310 | 0.2716 | 0.3065 |
| SHARES_LEARNED_P1 | random | 0.9620 | 0.9602 | 0.9612 |
| SHARES_LEARNED_P1 | spatial | 0.7246 | 0.7861 | 0.7496 |
| SHARES_LEARNED_P10 | climate_profile | 0.9167 | 0.9277 | 0.9214 |
| SHARES_LEARNED_P10 | municipality | 0.3401 | 0.2298 | 0.2945 |
| SHARES_LEARNED_P10 | random | 0.9905 | 0.9929 | 0.9916 |
| SHARES_LEARNED_P10 | spatial | 0.6192 | 0.5600 | 0.5952 |
| SHARES_MASK | climate_profile | 0.7215 | 0.7034 | 0.7138 |
| SHARES_MASK | municipality | 0.3210 | 0.2281 | 0.2826 |
| SHARES_MASK | random | 0.8322 | 0.7427 | 0.7899 |
| SHARES_MASK | spatial | 0.6890 | 0.4911 | 0.6087 |

372 contrastes predefinidos; significativos tras Holm: 0. Contienen comparaciones repetidas para J7 propio-global/referencia; se conserva el ajuste conjunto predefinido, conservador. No se interpreta no significancia como equivalencia. No se promovió modelo TOP20/TOP15 ni se generaron PRED59.

Los descriptores locales se construyen sólo con entrenamiento y k24 fijo. Las propuestas R3 para entrenar el peso son OOF: R3 se ajusta en A con residuos base OOF íntegramente dentro de A y predice D, excluyendo D y el fold externo. La auditoría reconstruye195 calibraciones y1,560 metamodelos. MASK/CONSTANT/ASYM requieren siete entradas con C-T3,31 con J7 y26 con SHARES; LEARNED añade FAPAR histórico para geometría satelital: ocho,32 y27 respectivamente. Los seis descriptores derivados no son nuevas fuentes independientes.