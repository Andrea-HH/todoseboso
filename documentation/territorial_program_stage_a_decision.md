# Etapa A — Decisión territorial

**La fuente edafológica histórica1:50,000 solicitada no está presente.** La carpeta chignahuapan contiene la carta topográfica E14B13, segunda edición1996, fotografías mayo1994 e imagen preparada mayo2002. Datum NAD27/UTM14N. No puede usarse como mapa de suelo.

**La carta geológico-minera es SGM1:50,000 de diciembre2017**, con base cartográfica INEGI2004. El PDF no contiene georreferenciación temática recuperable; se conserva para inventario visual. Sus metadatos PDF2018/2022 no son fechas de levantamiento geológico. La cobertura nominal de las dos hojas alcanza118 parcelas —82 etiquetas y36PRED—, con las62 etiquetas de los dos perfiles dominantes completamente dentro del marco. No hay parcelas parcialmente cubiertas en este marco. Cobertura nominal no equivale a clasificación temática.

**Sí existe una capa vectorial geológica INEGI1:250,000 diferente**, con compilación1982/conversión2000 documentadas. Su CRS NAD27 UTM14N se recuperó de AUX/cuadrícula; la transformación proyectada registra una precisión operacional13m, separada de la precisión cartográfica250k. Cubre las197parcelas y permite intersecciones físicas completas, sin renormalizar clases.

En los dos perfiles locales de33/29etiquetas, la composición geológica250k distingue727de934parejas posibles —77.8%—;480mantienen NDVI mayo similar. Cada perfil contiene cuatro unidades dominantes diferentes. Son contrastes disponibles, no evidencia de que una unidad explique rendimiento. Las727parejas comparten únicamente62etiquetas y dos perfiles, por lo que no permiten tratar727casos como observaciones independientes. Veinte de esas62parcelas intersectan la reserva descriptiva125m alrededor de límites250k, lo que exige cautela con diferencias pequeñas y cartografía histórica.

El RMSE de diferencias de F4-S1 es0.798t/ha en parejas internas aleatorias; entre parejas con NDVI similar y geología250k distinta permanece alrededor de0.796. Estos estratos se definieron usando soloX. Que el error siga siendo alto no demuestra que geología lo explique: todavía no hay predicción territorial validada. Las asociaciones parciales OOF de TPI, convergencia, flujo, TWI y diversidad geológica son débiles en los62casos después de controlar perfil yNDVI. Las asociaciones por unidad se documentan como descripciones sujetas a soporte, nunca como selección de una clase ganadora.

Quince parejas tienen clima, NDVI, dinámica, geomorfología, suelo amplio y geología amplia similares según los umbrales congelados. Conservan diferencias de rendimiento importantes, pero el soporte es pequeño y las reglas dependen de escala: esto no estima error irreducible.

**Decisiones:**

- Suelo50k1996: suspender comparación multiescala hasta disponer de la fuente verdadera.
- Geología SGM50k2017: mantener inventario y cobertura nominal; suspender asignación parcelaria sin geometría oficial fiable.
- Topografía1996: conservar revisión visual y marco; no extraer hidrografía o curvas de colores automáticamente.
- Geología INEGI250k: conservar composición completa como candidata descriptiva. Tiene variación intraperfil y cobertura, pero no se recomienda integrarla automáticamente ni atribuirle resolución50k. Un ensayo futuro, separado y congelado, necesitaría categorías con soporte, sensibilidades de límites y controles sobre las mismas parcelas.
- Geomorfología DEM120m: conservar TPI/convergencia/flujo/TWI para diagnóstico. No se identifica aquí una mejora adicional clara sobre vegetación/terreno actual, ni se deriva humedad observada.
- EtapaB: puede continuar como segunda entrega independiente con datos existentes, porque estas limitaciones territoriales no invalidan el objetivo intraperfil ni la mezcla fija. No se ejecutóB/C en esta primera entrega.

Se conservan matriz target-free197, cobertura, geometrías, composiciones completas, inventario de fuentes, categorías, pares definidos porX, residuos OOF solo descriptivos, figuras y6pruebas automatizadas. Las referencias numéricas J0/K5/F4-S1/F4-S5 se verificaron desde las OOF originales. No se alteraron etiquetas, modelos ni resultados congelados.
