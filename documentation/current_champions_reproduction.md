# Etapa vigente: champions26 y 14, reproducción sin L40

## Decisión y alcance

Por instrucción explícita del responsable del proyecto, **Reference26 y Compact14 son los champions actuales**. C-T3 permanece como control compacto y B1 como sensibilidad evaluada. No se incorporaL40/Local04D a la entrega reproducible actual; su historial comparativo permanece disponible. La decisión está versionada en [current_stage.json](../configs/current_stage.json).

No se cambian variables, hiperparámetros,138 rendimientos o particiones. No se generan modelos finales138 ni predicciones59. Seleccionar champions y demostrar reproducción no equivale a conocer el error de 59 o demostrar superioridad estadística independiente.

## Código y entradas independientes del otro repositorio

- [`src/current_champions.py`](../src/current_champions.py): reconstrucción de las recetas y reentrenamiento con selección interna.
- [`scripts/521_current_champions.py`](../scripts/521_current_champions.py): exportación, reconstrucción y reentrenamiento por fold.
- Bundle privado: `data/processed/current_champions/v1/`. Contiene tabla138 con26 predictores derivados, metadata, grupos, distancias geográficas congeladas, particiones y81 paquetes de modelos guardados restringidos a estas recetas. No contieneC4, embeddingsPCA20 ni modelos/prediccionesL40.
- [Resultados agregados enGit](../results/current_champions/v1/README.md). OOF y detalles individuales: `outputs/research/current_champions/v1/`, excluidos.
- [Esquema de entradas y procedencia](../configs/current_champions_inputs.json): nombres exactos de las 26 variables, composición geológica y hashes de archivos privados; sin observaciones individuales.

Algunas variables satelitales y topográficas tienen procedencia compartida con la ingeniería de GeoC ya auditada; excluirL40 no cambia esa procedencia ni inventa otra fuente. El bundle conserva únicamente las entradas necesarias para nuestros modelos. **Tras preparar el bundle no se requiere acceso al repositorioGeoC ni a los antiguos caches/outputs para reconstruir o reentrenar.** Los imports internos con nombres heredados reutilizan código local; no cargan el modeloL40.

El comando reproduce conjuntamente los cuatro modelos y por eso su bundle reúne26 entradas. La recetaCompact14 utiliza14: las otras12 corresponden aReference26/B1. La independencia de fuentes de 14 fue comprobada también en la [auditoría de arquitectura podada](../scripts/501_audit_pruned_architectures.py); no se afirma que el comando conjunto sea una distribución mínima exclusiva de 14.

La geometría conserva la normalización y orden originales para no modificar la regularización efectiva deRidge o los desempates de vecinos. No se convierte distancia normalizada en kilómetros ni se recalcula una escala distinta en cada fold. Los24 vecinos se restringen a las etiquetas del entrenamiento correspondiente.

El ejecutor instala una barrera de acceso a archivos: al reconstruir/reentrenar rechaza lecturas en `data/`, `outputs/` históricos oGeoC fuera del bundle y del directorio específico de esa ejecución. Así se detectan dependencias ocultas, en lugar de asumir que no existen.

## Tres operaciones diferentes

### 1. Preparar el bundle una vez, desde la investigación local existente

```powershell
python scripts/521_current_champions.py export
```

Este paso extrae las 26 entradas, distancias, grupos, modelos propios guardados y las OOF de referencia de los artefactos locales actuales. No entrena y no copiaL40. Requiere esos insumos históricos para crear la primera copia. Se detiene si ya existe un manifiesto; no sobrescribe un bundle congelado. Para compartir reproducibilidad con otra computadora hay que entregar el bundle por el canal autorizado de datos, además del códigoGit.

Los hashes del manifiesto verifican sus archivos. Los `joblib` sólo deben cargarse de esta fuente confiable. La copia privada no se sube aGit. No se promete generar automáticamente todas las fuentes originales a partir de un clon vacío.

### 2. Reconstruir todas las predicciones y métricas

```powershell
python scripts/521_current_champions.py replay
```

Utiliza los 81 modelos de validación guardados:65 folds originales y16 splits97/41. Recalcula predicciones deC-T3,26,14 y B1 desde las entradas y compara cada una con laOOF archivada. No se limita a copiar una tabla de métricas. Verifica IDs, rendimientos y posiciones; la tolerancia de equivalencia es1e-10t/ha.

Genera OOF, diferencias numéricas, métricas por repetición, resultados agregados y auditorías. IncluyeCSV ancho con las cuatro predicciones/residuos y unExcel privado `comparacion_modelos_propios.xlsx`. Calcula cada métrica sobre OOF completas de una repetición y después promedia; el banco97/41 se mantiene aparte. Esta operación prueba reconstrucción numérica de modelos guardados, **no entrenamiento desde cero**. La resoluciónRidge por consulta sigue siendo parte de la predicción del experto local; no equivale a volver a seleccionar sus hiperparámetros.

### 3. Reentrenar las mismas recetas sin cachés históricos

```powershell
# Una verificación concreta (índices de ejecución base0):
python scripts/521_current_champions.py refit --folds 0,50,55,60,63,64,65 --output outputs/research/current_champions/v1/refit_check

# Toda la batería; puede ser costoso:
python scripts/521_current_champions.py refit --folds all --output outputs/research/current_champions/v1/refit_full
```

Reajusta imputación, escalas, C-T3, expertos locales, corrección interna de 26, compuerta geológica, peso global de 14, correctoresR3 y pesoB1, siempre con el entrenamiento correspondiente. C-T3 conserva su rejilla original y el fallback territorial de falta de grupos. R3 conserva su selección0/.5/1, máscara y límite. B1 se calibra con expertos completamente reajustados sobre OOF internas. No se selecciona una variante mirando el fold externo ni se sustituyen grupos insuficientes porCV aleatoria.

El ejecutor conserva las particiones externas/internas congeladas; los niveles recursivos siguen el procedimiento original. Los caches creados durante una nueva ejecución son propios de esa ejecución y no leen los archivos históricos. No lanzar reentrenamientos distintos con el mismo directorio de salida. Si ya existe el modelo del fold, se detiene para impedir reutilización silenciosa.

Una corrida parcial guarda predicciones y auditoría **sin publicar métricas de protocolo incompleto**. Sólo una corrida con los 81 folds genera las métricas completas. Las auditorías de entrenamiento indican exactamente cuáles se comprobaron; no se presenta una comprobación parcial como reentrenamiento completo de 81.

## Resultados, residuos y verificación

Las métricas actuales están en [results/current_champions/v1](../results/current_champions/v1/README.md). Error=predicho−observado; losCSV privados incluyen las cuatro predicciones y residuos en formato largo por parcela, repetición y fold. El coeficienteB1 y las advertencias de ejecución se registran por fold.

Los paquetes contienen las etapas ajustadas y sus selecciones. Ningún archivo de esta ruta usa las 59 parcelas para elegir modelos. El replay completo tiene prueba de equivalencia; el alcance del reentrenamiento comprobado se documenta en [verificación de entrenamiento](../results/current_champions/v1/cold_refit_verification.json) y no se infiere de la existencia del comando.

Las versiones del entorno se conservan en [environments](../environments/README.md). Un replay o un reentrenamiento en este entorno no certifica instalación limpia en cualquier plataforma. Durante la verificación local apareció una advertencia de bibliotecasOpenMP simultáneas; se registra en los logs por fold cuando se emite. No hubo deterioro numérico en las comprobaciones que pasaron; revisar el entorno si se reproduce un fallo de ejecución.
