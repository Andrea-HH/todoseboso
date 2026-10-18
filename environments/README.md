# Entorno de investigación

`research_environment.json` y `../requirements-research.txt` registran versiones instaladas de distribuciones asociadas a imports detectados estáticamente en el código. Es una fotografía del entorno que tiene disponibles los artefactos de investigación; **no es un lock completo de dependencias transitivas ni una instalación limpia verificada**. El JSON indica la versión de Python y el sistema operativo observados.

El proyecto usa paquetes numéricos, aprendizaje automático, extracción geoespacial, tablas, gráficos y lectura documental. Algunos sólo son necesarios para preparar datos; interpretarOOF existentes requiere menos dependencias. No se eliminan esas diferencias ocultándolas tras una supuesta instalación mínima universal.

Preparación orientativa en un entorno separado:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-research.txt
python scripts/520_validate_repository_documentation.py
```

Las bibliotecas geoespaciales pueden requerir binarios compatibles con la versión de Python y el sistema. La receta anterior no se ejecutó en un entorno nuevo durante esta reorganización. Si falla la resolución, revisar versiones/plataforma; no modificar hiperparámetros de modelos para resolver instalación. Los módulos listados como imports no resueltos pueden ser módulos locales o imports dinámicos y deben revisarse, no instalarse ciegamente conpip.

Para reconstruir una etapa concreta, consultar su diseño y requisitos de datos. Clonar el código no instala los insumos privados ni descarga la representaciónGeoC. No cargar archivos `joblib/pickle` de fuentes desconocidas: los artefactos de este proyecto deben proceder de una fuente confiable y verificarse contra su procedencia.
