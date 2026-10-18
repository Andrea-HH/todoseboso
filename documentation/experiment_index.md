# Índice de investigación y experimentos

Este índice conserva la historia sin mover ni renumerar archivos. Las filas agrupan líneas de investigación, **no cuentan modelos**. Diseños, resultados, controles y sensibilidades se distinguen por sus documentos. La existencia de código o un diseño congelado no prueba que se haya ejecutado.

## Etapas y evidencia

| Línea | Pregunta / finalidad | Documentación principal | Implementación o scripts para localizarla |
|---|---|---|---|
| Datos y EDA | Integrar fuentes, series y diagnóstico de soporte | [Target](target_analysis.md), `documentation/eda/` | `scripts/data_uderstanding/`, `src/family_1/` |
| RS y Champion histórico | Clima, historia y topografía residual | [Entrega histórica](winner_predictions_statistical_validation.md) | `scripts/data_uderstanding/tablas_agrocebada/207*`–`210*`; buscar Champion en inventario |
| Lluvia, PCA/PCR | Intensidad y distribución temporal de lluvia | [Lluvia](rainfall_yield_modeling.md) | `src/family_1/`; scripts de lluvia en inventario |
| G/H y extensión | Complementariedad precipitación–Tmax | [G/H](g_h_climate_signal_exploration.md), [extensiónH](h_rain_tmax_extension.md) | Módulos climáticos de `src/family_1/` |
| I/J/K | Aporte geográfico, suelo y topografía, directo/residual | [I](i_geographic_edaphological_exploration.md), [J](j_incremental_yield_modeling.md), [K](k_decision_summary.md) | `src/family_1/`; inventario por títulos |
| L/M | Representaciones multibloque e historia satelital | [Síntesis](l_m_synthesis.md) | `src/family_1/` |
| F4 y programaA–D | Información intraperfil, jerarquía y transferencia | [F4](family4_e_decision_summary.md), [síntesisD](territorial_program_stage_d_executive.md) | `src/family_4/`, scripts337–347 |
| F5 y S1 | GPR, representación, suavidad y extrapolación | [Inicial](family5_gpr_initial_decision.md), [S1](family5_gpr_s1.md) | `src/family_5/`, scripts348–352 |
| F6 y F6-E | Bagging y complementariedad | [F6](family6_bagging.md), [expansión](family6_expansion.md) | `src/family_6/`, scripts353–358; E4/E5 no se infieren ejecutados |
| F7 y F7-E | CatBoost/XGBoost y ablaciones de historia/pendiente | [F7](family7_boosting.md), [expansión](family7_expansion.md) | `src/family_7/`, scripts359–363 |
| F8 | Auditoría y propuesta de modelos residuales | [Recomendación](family8_recommendation.md) | `src/family_8/`, scripts364–365; el informe declara que no se ejecutóF8 |
| PLS/árbol completo | Controles exploratorios de alta dimensión | [PLS](experimental_pls1867.md), [árbol](experimental_tree1867.md) | `src/experimental_pls.py`, `src/experimental_tree.py` |
| Información incrementalC-T3 | Identificar complementos condicionados al núcleo | [Hallazgos](ct3_incremental_information_findings.md), [faseIII](ct3_information_phase_iii.md) | `src/ct3_information/` |
| Residual condicional | Correcciones honestas sobreC-T3 | [Diseño](ct3_residual_conditional_design.md), [resultados](ct3_residual_conditional.md) | `src/ct3_residual_conditional/` |
| Coherencia/ensambles/territorio | Estabilidad y mezclas sin reglas retrospectivas | [Coherencia](ct3_residual_coherence.md), [ensamble](compact_ensemble.md), [territorio](territorial_mixtures.md) | `src/ct3_residual_coherence.py`, `src/compact_ensemble.py` |
| Calendario y nuevas variables | Ventanas2025, historia y anomalías | [Conjunto](agronomic_calendar_set.md), [modelado](agronomic_calendar_modeling_results.md), [expansión](agronomic_calendar_expansion_results.md) | `src/agronomic_calendar_features.py`, `src/calendar_modeling.py` |
| Entrega histórica59 | Consolidación C-T3/Champion/EQUAL3 | [Entrega y validación](winner_predictions_statistical_validation.md) | `outputs/modeling/winner_predictions/v1/`; no equivale a entrega 26/14 |
| GeoC y L40 | Reproducir vecino local y comparar con C-T3 | [Puente](geoc_bridge_results.md), [auditoría variables](geoc_variable_signal_audit.md) | `src/geoc_bridge.py`, `src/geoc_local04d_snapshot.py` |
| Local no climático | Separar representación local y señal global | [Resultados](nonclimatic_local_results.md) | `src/nonclimatic_local.py` |
| Similitud/representación física | Vecinos y reducciones físicas | [Similitud](physical_similarity_results.md), [representación](physical_representation_results.md) | `src/physical_similarity.py`, `src/physical_representation.py` |
| Fases locales y reparto | Pesos físicos y roles de las señales | [Fases](conditional_local_phases_results.md), [roles](signal_role_allocation_results.md) | `src/conditional_local_phases.py`, `src/signal_role_allocation.py` |
| Simplificación conjunta | Reducción de expertos y compuertas | [Resultados](joint_simplification_results.md) | Buscar `joint_simplification` en el inventario de scripts y recetas |
| Residuos/J7/casos difíciles | Errores completos, regiones y diferenciadores | [J7](j7_both_residual_audit.md), [señales](difficult_case_signals_conclusions.md), [cuartil difícil](difficult_quartile_conclusions.md) | `src/difficult_case_signals.py`, `src/difficult_quartile.py` |
| Contrastes con vecinos | Desviación respecto a vecindarios geo/físicos/satelitales | [Contrastes](neighbor_signal_contrasts_conclusions.md), [lineal](neighbor_signal_linear_conclusions.md) | `src/neighbor_signal_contrasts.py`, `src/neighbor_signal_linear.py` |
| Ingeniería e indicadores | Variables temporales, reducción y correcciónR3 | [Ingeniería](signal_feature_engineering_conclusions.md), [indicadores](temporal_indicator_weights_conclusions.md), [vecindarios](indicator_neighborhoods_conclusions.md) | `src/temporal_indicator_weights.py`, `src/indicator_neighborhoods.py` |
| Base y R3 | Simplificación de base y aplicación de correcciones | [Base](base_distribution_correction_conclusions.md), [pesoR3](learned_r3_weight_conclusions.md) | `src/base_distribution_correction.py`, scripts494–496 |
| Descomposición26/14 | Interacción entre quitar fuentes, corrector y compuerta | [Conclusiones](architecture_decomposition_conclusions.md) | scripts497–501; `src/architecture_decomposition.py` |
| Comparación de cuatro líderes | OOF y residuos compatibles | [Comparación](four_leaders_comparison.md) | script502; sin entrenamiento nuevo |
| MezclasB1–B6 | Complementariedad entreCT3,14,26,L40 | [Diseño](four_expert_combinations_design.md), [conclusión](four_expert_combinations_conclusions.md) | scripts503–517; secuencia vigente abajo |
| Explicación de arquitecturas | Métricas/predicciones/residuos de 26/14/B1/L40 | [Informe](four_architecture_explanation.md) | script518; sólo análisis deOOF existentes |

## Etapa vigente: reproducción de los champions

Reference26 y Compact14 son los champions actuales; C-T3 es control y B1 sensibilidad. L40 se conserva sólo como historial. El punto de entrada es `scripts/521_current_champions.py` con `export`, `replay` y `refit`: ver [instrucciones actuales](current_champions_reproduction.md) y [resultados](../results/current_champions/v1/README.md). La reconstrucción y el reentrenamiento no usanC4/PCA20 ni el repositorio GeoC. El alcance efectivamente verificado se registra por separado.

## Batería histórica de mezclas: secuencia conservada

Consultar primero [reproducción detallada](four_expert_combinations_reproduction.md), insumos y configuraciones en [configs](../configs/README.md).

| Paso | Script | Función |
|---|---|---|
| Congelar una ejecución nueva | `503_prepare_four_expert_combinations.py` | Sólo si no existe el diseño local; no ejecutar sobre una ejecución congelada |
| Verificar optimizaciones | `508_verify_four_expert_fast.py`, `515_verify_four_expert_tuner.py` | Equivalencia numérica; no nuevas rejillas |
| Entrenar/reanudar | `516_run_four_expert_cached_tuner.py all` | Ejecutor optimizado vigente; no lanzar trabajadores duplicados |
| Recoger/revisar checkpoints | `507_run_four_expert_fast.py` | Con todos completos, recoger sin volver a entrenar; ver instrucciones específicas |
| Evaluar y entregar | `511_finalize_four_expert_combinations.py` | Usa evaluación510 y entrega506, diagnósticos y pruebas |
| Interpretar | `513_summarize_four_expert_combinations.py`, `517_review_four_expert_results.py` | Síntesis y revisión numérica final |
| Explicar cuatro modelos | `518_explain_four_architectures.py` | Exportar comparación deOOF; no entrenar ni generar59 |

`504` y `505` son implementaciones anteriores conservadas. `509`, `510`, `512` son herramientas de diagnóstico/evaluación/recogida utilizadas por la batería. `514` es un auxiliar operativo para evitar suspensión durante entrenamiento; no forma parte de la arquitectura ni es necesario para interpretar resultados. Esta clasificación evita confundir varios ejecutores con nuevos experimentos.

## Inventario completo y mantenimiento

- [Inventario de archivos](inventories/repository_files.csv): ruta, área, función y título extraído de cada archivo. Los tipos se infieren del nombre/docstring y pueden requerir revisión; no son evidencia de ejecución.
- [Manifiesto de diseños exportados](../configs/experiments/manifest.json):30 diseños locales recuperados inicialmente, incluidos estados no ejecutados; el total futuro lo determina el manifiesto.
- `scripts/519_export_research_metadata.py`: actualiza los inventarios y exporta metadatos desde los artefactos locales, sin entrenamiento. No es un comando de arranque para un clon sin insumos.
- `scripts/520_validate_repository_documentation.py`: comprueba enlaces principales, registros, hashes y particiones versionadas sin cargar datos privados.

Para una nueva batería, documentar antes pregunta, controles, variables, selección interna, protocolo, límites y decisión. Añadir su fila y registro sin reasignar nombres históricos. No elegir una sensibilidad con resultados externos y presentar esos mismos resultados como confirmación independiente.
