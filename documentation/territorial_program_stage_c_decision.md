> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Etapa C — Síntesis de decisiones

**La representación compacta de lluvia merece validación municipal independiente. El intercepto jerárquico no aporta una ventaja general sobre su control de regularización.**

RMSE en t/ha, media de métricas de validación completa por repetición; las repeticiones y las parejas no son independientes.

| Modelo | Aleatoria | Por perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T0 / C-H0: lluvia mensual + NDVI mayo, Elastic Net | 0.50483 | 0.52626 | 0.67110 | 0.73904 |
| C-T1: lluvia mensual + DTR | 0.52412 | 0.56029 | 0.68540 | 0.60047 |
| C-T2: lluvia mensual + NDVI + DTR | 0.50638 | 0.53369 | 0.65442 | 0.75987 |
| C-T3: lluvia compacta + NDVI | 0.51158 | 0.52060 | 0.58126 | 0.67878 |
| C-T4: lluvia compacta + NDVI + DTR | 0.51375 | 0.52618 | 0.60285 | 0.67659 |
| C-H0M: control Gaussian Ridge emparejado | 0.50945 | 0.51777 | 0.63945 | 0.67244 |
| C-H1: mismo control + intercepto aleatorio de perfil | 0.51341 | 0.51873 | 0.63945 | 0.69096 |

1. **Arquitectura:** H1 no supera H0M en ninguno de los cuatro RMSE globales. Las mejoras frente a Elastic Net pertenecen principalmente a la regularización emparejada, no a la agrupación parcial.
2. **Representación:** T3 resume lluvia mediante total, fracción abril–junio y concentración mensual. Baja RMSE municipal 0.67110→0.58126 y MAE 0.49856→0.46033. El costo aleatorio de RMSE es +0.00675; el de MAE es +0.01085, ligeramente superior al margen congelado 0.01. No cumple una aceptación universal.
3. **Perfiles conocidos:** en aleatoria H1 empeora RMSE conocido 0.50402→0.50674 frente a H0M. En espacio mejora conocido 0.51847→0.50742, pero perjudica perfiles nuevos. No hay ventaja consistente.
4. **Perfiles nuevos:** H1 usa efecto medio cero y añade tau² a la incertidumbre. En espacio nuevo empeora RMSE 0.72065→0.74700 frente a H0M; municipio empata porque todos los ajustes seleccionan ratio cero. Los intervalos nominales 90% cubren solo 77.9% de nuevos casos municipales: no están calibrados para ese dominio.
5. **Diferenciación intraperfil:** el intercepto de perfil y la lluvia se cancelan en diferencias entre parcelas del mismo perfil y modelo externo. H1 no añade una nueva señal parcelaria; sigue dependiendo de NDVI. No se observa mejora local general suficiente para justificar complejidad.
6. **Transferencia espacial:** la ventaja de T3 depende especialmente del bloque 3. Al excluirlo, frente a T0 empeoran RMSE +0.0324 y MAE +0.0219. La ventaja de DTR solo también se concentra en ese bloque. La mejor cifra espacial no demuestra generalización regional robusta.
7. **Complementariedad:** NDVI y DTR describen escalas distintas, pero T2 no combina sus fortalezas predictivas: pierde la ventaja espacial de T1. Añadir DTR a T3 empeora municipal y aleatoria, con mejora espacial mínima.
8. **Chignahuapan:** T3 mejora principalmente fuera: RMSE municipal externo 0.7769→0.5819, mientras dentro empeora 0.5530→0.5807. Los resultados no justifican una solución local uniforme.
9. **Identificabilidad:** hay solo 12 perfiles repetidos. H1 elige ratio cero en 36/50 ajustes aleatorios, 4/5 por perfil, 5/5 municipales y 3/5 espaciales. El ratio se selecciona por CV interna; no es una estimación continua de máxima verosimilitud. La evidencia de una varianza de perfil general no nula es débil. La sensibilidad por disponibilidad de perfiles dominantes se documenta con los folds existentes, sin crear candidatos adicionales.
10. **Decisión:** conservar T3 como candidato exploratorio municipal y H0M como control parsimonioso. Validar en municipios/campañas independientes; no promover H1, T2 ni un ganador universal. Mantener T1 como hipótesis espacial pendiente de confirmar entre regiones.

Se ejecutaron exclusivamente los experimentos C: 325 modelos nuevos, 65 folds externos congelados con sus particiones internas, ocho series comparables y 14,352 registros OOF. Pasaron 13 pruebas matemáticas y de integración, incluyendo reproducción de todos los modelos guardados, controles exactos, preprocesamiento entrenado sin validación, perfiles nuevos y cancelación de interceptos. Las 59 PRED se conservan sin etiquetas ni entrenamiento final. Los hashes protegen las etapas anteriores y las fuentes de ajuste congeladas. Todas las conclusiones son exploratorias. Champion, mezcla 50/50 y etapas A/B permanecen intactos; D no se ejecutó.
