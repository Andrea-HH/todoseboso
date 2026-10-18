> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# F8 — Recomendación y ocho respuestas

**Es viable una prueba residual pequeña, pero no una nueva búsqueda extensa. No se ejecutó F8.** Recomiendo C-T3 compact4 como base inicial, R1 Ridge de pendiente primero y R2 CatBoost pendiente+May únicamente tras revisión y con control May-only. No iniciar historia, R4, mezcla de modelos completos ni corrección del modelo TOP20/TOP15.

1. **Utilidad ya observada:** RS4 mostró mejora aleatoria de historia residual sobre bases climáticas concretas y RS5/modelo TOP20/TOP15 aportes topográficos modestos; K/L/M/F4 evaluaron correcciones honestas de lluvia con eta y algunos beneficios específicos. No existe demostración de utilidad uniforme de pendiente o historia sobre C-T3 con transferencia municipal/espacial. Los parámetros y bloques no son equivalentes a NDVI2/slope_mean aislados; la auditoría preserva los límites de anidamiento antiguos.
2. **Información nueva versus redundancia:** R1 cambia base a compact4 y corrector a Ridge centrado con targets honestos y contracción; K5/F4 slope mensual son controles conceptuales, no repetición idéntica. R2 con C-V investiga si queda estructura conjunta T,V más allá de May absorbido por la base. Repetir modelo TOP20/TOP15, K5 completo, spline F4, jerarquía C-H1, GP S1-C o pérdida B sería redundante. R3 solo es nueva si añade esas dos historias precisas al residual correcto y demuestra ganancia sobre R2.
3. **Base estricta o ampliada:** ampliada C-T3 como primera referencia reproducible y emparejada, sin llamarla clima puro. Rain3 sirve para contrastar la definición operacional del nivel, pero todavía no hay ElasticNet rain3 idéntico evaluado; GP rain3 no lo reemplaza. Posponer el factorial de dos bases por correctores.
4. **Pendiente lineal/no lineal:** primero lineal Ridge, por simplicidad, signo, contracción y prueba de información residual. R2 pequeño puede probar no linealidad conjunta, pero no atribuir diferencia respecto a R1 solo al algoritmo porque incorpora V adicional. El control C-V es indispensable para atribuir incremento a pendiente. La evidencia actual no decide que la forma no lineal sea superior.
5. **Historia:** requiere residual propio cross-fitted de la base y control R2, asociación condicional/local estable con suficiente soporte, después ablación interna y OOF externa territorial sin daño. Frequent TOP15, correlación histórica o mejora directa en otra familia no bastan; F7 history espacial severamente negativo obliga a posponerla.
6. **Evitar sesgo territorial:** base/entradas fijas, centrar corrección en TRAIN, λ0/.25/.5 interno, métricas absolutas primarias, ambas ponderaciones intraperfil, diagnóstico de sesgo y soporte por municipio/bloque y omisiones sin refits. No garantiza ausencia de sesgo: se detiene si la transferencia falla. No reglas Singuilucan/Chignahuapan ni labels externos para seleccionar signo o amplitud.
7. **Validación honesta:** cada predicción residual de entrenamiento excluye su label también de tuning; cada evaluación interna regenera su propia base/targets sin labels de validación interna; luego base y corrector se reajustan solo con outer-train y se evalúan una vez en outer-test. No OOF global modelo TOP20/TOP15 ni residuos in-sample. Reutilizar modelos/contextos solo con procedencia exacta. Documentar mismatch crossfit/refit.
8. **Viabilidad138:** computacionalmente factible con cache y pocos correctores; estadísticamente frágil por43 perfiles,12 repetidos,31singleton,9 municipios y una campaña etiquetada. Muchos pares y10 repeticiones no crean información independiente. No detener toda hipótesis residual aún, pero sí acotar primera prueba a R0/R1, exigir revisión para R2/C-V y detener expansión ante λ0/daños. Hace falta nueva evidencia independiente para superioridad general.

La versión entrega auditoría, evidencia por fuente, comparación conceptual, identificabilidad/extrapolación, cross-fitting detallado, matriz/costos, riesgos y recomendación. Todos los documentos son propuestas de investigación para revisión, no una ejecución autorizada de nuevas arquitecturas. modelo TOP20/TOP15/F4/F5/F6/F7 y decisiones anteriores permanecen intactos.


Evidencia recomputada, agregación compatible:

| family | experiment | protocol | RMSE | MAE | bias | n | n_repeats |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F4 | F4-A | climate_profile | 0.549807 | 0.398476 | 0.046673 | 138 | 1 |
| F4 | F4-A | municipality | 0.730058 | 0.518849 | 0.114275 | 138 | 1 |
| F4 | F4-A | random | 0.518089 | 0.370944 | 0.000436 | 138 | 10 |
| F4 | F4-A | spatial | 0.710570 | 0.543471 | 0.269478 | 138 | 1 |
| F4 | F4-G1 | climate_profile | 0.542770 | 0.399407 | 0.054478 | 138 | 1 |
| F4 | F4-G1 | municipality | 0.702072 | 0.521247 | 0.134597 | 138 | 1 |
| F4 | F4-G1 | random | 0.517114 | 0.372587 | -0.001168 | 138 | 10 |
| F4 | F4-G1 | spatial | 0.708128 | 0.551881 | 0.266503 | 138 | 1 |
| F4 | F4-S2 | climate_profile | 0.534475 | 0.382459 | 0.065805 | 138 | 1 |
| F4 | F4-S2 | municipality | 0.723291 | 0.524961 | 0.191214 | 138 | 1 |
| F4 | F4-S2 | random | 0.508642 | 0.359219 | -0.000049 | 138 | 10 |
| F4 | F4-S2 | spatial | 0.673392 | 0.511788 | 0.316662 | 138 | 1 |
| F7 | C-T3 | climate_profile | 0.520604 | 0.391501 | 0.004588 | 138 | 1 |
| F7 | C-T3 | municipality | 0.581259 | 0.460329 | -0.020332 | 138 | 1 |
| F7 | C-T3 | random | 0.511582 | 0.374948 | 0.000530 | 138 | 10 |
| F7 | C-T3 | spatial | 0.678778 | 0.530612 | 0.191161 | 138 | 1 |
| F7 | F7-00 | climate_profile | 0.515345 | 0.389830 | -0.022875 | 138 | 1 |
| F7 | F7-00 | municipality | 0.528223 | 0.374773 | 0.004674 | 138 | 1 |
| F7 | F7-00 | random | 0.504874 | 0.366623 | -0.003447 | 138 | 10 |
| F7 | F7-00 | spatial | 0.642591 | 0.492676 | 0.137384 | 138 | 1 |
| F7 | F7-E1 | climate_profile | 0.522021 | 0.388945 | -0.003375 | 138 | 1 |
| F7 | F7-E1 | municipality | 0.544530 | 0.397806 | 0.049911 | 138 | 1 |
| F7 | F7-E1 | random | 0.512823 | 0.376006 | -0.011643 | 138 | 10 |
| F7 | F7-E1 | spatial | 0.763684 | 0.588800 | 0.190774 | 138 | 1 |
| F7 | F7-E2 | climate_profile | 0.520118 | 0.391381 | -0.001912 | 138 | 1 |
| F7 | F7-E2 | municipality | 0.553412 | 0.407488 | 0.031463 | 138 | 1 |
| F7 | F7-E2 | random | 0.514374 | 0.377119 | -0.003500 | 138 | 10 |
| F7 | F7-E2 | spatial | 0.671957 | 0.508473 | 0.169634 | 138 | 1 |
| F7 | F7-E3 | climate_profile | 0.524171 | 0.393871 | -0.015236 | 138 | 1 |
| F7 | F7-E3 | municipality | 0.563640 | 0.428209 | 0.031908 | 138 | 1 |
| F7 | F7-E3 | random | 0.519740 | 0.381379 | -0.013643 | 138 | 10 |
| F7 | F7-E3 | spatial | 0.755083 | 0.579799 | 0.197215 | 138 | 1 |
| J | J0_RAIN | climate_profile | 0.544351 | 0.390346 | 0.023073 | 138 | 1 |
| J | J0_RAIN | municipality | 0.695358 | 0.500224 | 0.083793 | 138 | 1 |
| J | J0_RAIN | random | 0.521358 | 0.369458 | -0.001564 | 138 | 10 |
| J | J0_RAIN | spatial | 0.734787 | 0.561994 | 0.302321 | 138 | 1 |
| J | J1_RAIN_SLOPE | climate_profile | 0.513017 | 0.386285 | -0.023662 | 138 | 1 |
| J | J1_RAIN_SLOPE | municipality | 0.675491 | 0.496693 | 0.123955 | 138 | 1 |
| J | J1_RAIN_SLOPE | random | 0.515417 | 0.375562 | -0.002569 | 138 | 10 |
| J | J1_RAIN_SLOPE | spatial | 0.975331 | 0.728624 | 0.385958 | 138 | 1 |
| K | K5_RAIN_RESID_SLOPE | climate_profile | 0.537564 | 0.401700 | 0.047879 | 138 | 1 |
| K | K5_RAIN_RESID_SLOPE | municipality | 0.696060 | 0.512390 | 0.125385 | 138 | 1 |
| K | K5_RAIN_RESID_SLOPE | random | 0.516238 | 0.371351 | -0.000700 | 138 | 10 |
| K | K5_RAIN_RESID_SLOPE | spatial | 0.713927 | 0.563506 | 0.252388 | 138 | 1 |
| K | K6_RAIN_RESID_TOPO | climate_profile | 0.540723 | 0.395345 | 0.051838 | 138 | 1 |
| K | K6_RAIN_RESID_TOPO | municipality | 0.706736 | 0.518861 | 0.119361 | 138 | 1 |
| K | K6_RAIN_RESID_TOPO | random | 0.517538 | 0.371783 | -0.000216 | 138 | 10 |
| K | K6_RAIN_RESID_TOPO | spatial | 0.727929 | 0.573425 | 0.248376 | 138 | 1 |
| RS4 | PRECIPITATION_XGB_BASE | random | 0.513122 | 0.364323 | 0.009360 | 138 | 10 |
| RS4 | PRECIPITATION_XGB_HISTORY15 | random | 0.501137 | 0.362425 | -0.011173 | 138 | 10 |
| RS4 | TOP20_ENET_BASE | random | 0.516016 | 0.366421 | 0.002193 | 138 | 10 |
| RS4 | TOP20_ENET_HISTORY15 | random | 0.501106 | 0.356147 | -0.006323 | 138 | 10 |
| RS6 | A_CURRENT_CH_H_T | random | 0.498127 | 0.358869 | 0.001833 | 138 | 10 |

GP bloque3 archivado:

```json
{
  "n": 35,
  "mean_linear_prediction": 3.7538608164543468,
  "mean_gp_correction": -3.506588943596188e-05,
  "mean_y": 3.0285714285714285,
  "mean_prediction": 3.753825750564911,
  "target_style": "within-training fitted trend residual; not F8 OOF residual"
}
```


Verificación: cinco pruebas pasaron; cero ajustes/predicciones nuevos; 158 fuentes consumidas verificadas. Se conserva inventario de15382 hashes anteriores; los archivos no utilizados no se reabrieron para rehash. Escrituras limitadas a nueva versión F8 y sus documentos.
