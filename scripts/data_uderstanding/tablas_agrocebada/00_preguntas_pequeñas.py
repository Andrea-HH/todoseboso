#%%
import pandas as pd

#read data
basico = pd.read_csv("data/original/01_tablas_maestras/Conjunto_datos_BASICO_AgroCebada2026.csv")
pro = pd.read_csv("data/original/01_tablas_maestras/Conjunto_datos_PRO_AgroCebada.csv")


print("Basico data shape:", basico.shape)
print("Pro data shape:", pro.shape)

#%%

#columnas de cada tabla
basico_columns = basico.columns.tolist()
pro_columns = pro.columns.tolist()
ambas_columns = set(basico_columns).intersection(set(pro_columns))

print("Columnas en Basico:", basico_columns)
print("Columnas en Pro:", pro_columns)
print("Columnas en ambas tablas:", list(ambas_columns))

# %%

basico_landsat = basico[basico['sensor'] == 'Landsat']
basico_sentinel = basico[basico['sensor'] == 'Sentinel-2']

#drop null columns
#identify columns with all null values as null or empty columns or space as the value 
null_columns_landsat = basico_landsat.columns[basico_landsat.isnull().all()].tolist()
print("Null columns in Basic Landsat data:", null_columns_landsat)
basico_landsat = basico_landsat.drop(columns=null_columns_landsat)

null_columns_sentinel = basico_sentinel.columns[basico_sentinel.isnull().all()].tolist()
print("Null columns in Basic Sentinel data:", null_columns_sentinel)
basico_sentinel = basico_sentinel.drop(columns=null_columns_sentinel)

print("Basic Landsat data shape:", basico_landsat.shape)
print("Basic Sentinel data shape:", basico_sentinel.shape)
# %%
landsat = basico_landsat
sentinel = basico_sentinel
planet = pro

fechas_landsat = landsat['fecha_captura'].unique()
fechas_sentinel = sentinel['fecha_captura'].unique()
fechas_planet = planet['fecha_captura'].unique()

#porcentaje de fechas  que coincide y fechas que no coincide
fechas_landsat_set = set(fechas_landsat)
fechas_sentinel_set = set(fechas_sentinel)
fechas_planet_set = set(fechas_planet)

all_fechas = fechas_landsat_set.union(fechas_sentinel_set).union(fechas_planet_set)

intersection_landsat_sentinel = fechas_landsat_set.intersection(fechas_sentinel_set)
intersection_landsat_planet = fechas_landsat_set.intersection(fechas_planet_set)
intersection_sentinel_planet = fechas_sentinel_set.intersection(fechas_planet_set)  

three_way_intersection = fechas_landsat_set.intersection(fechas_sentinel_set).intersection(fechas_planet_set)


#print the results
print("Total dates", len(all_fechas))

print("Total unique dates in Landsat:", len(fechas_landsat_set))
print("Total unique dates in Sentinel:", len(fechas_sentinel_set))
print("Total unique dates in Planet:", len(fechas_planet_set))
print("Intersection of all three:", len(three_way_intersection))


# %%

#entender preriodicidad y frecuencia de las fechas de captura de cada sensor

#planet
#reformat the date column from "%d/%m/%Y" to "%m/%d/%Y"
planet["fecha_captura"] = pd.to_datetime(planet["fecha_captura"], format="%d/%m/%Y")
#frecuecnia de capturas planet
fechas_planet = planet["fecha_captura"].dropna().drop_duplicates()

yearly_frequency_planet = (
    fechas_planet.dt.year
    .value_counts()
    .sort_index()
)

monthly_frequency_planet = (
    fechas_planet.dt.to_period("M")
    .value_counts()
    .sort_index()
)

print("Capturas por año:")
print(yearly_frequency_planet)

print("\nCapturas por año-mes:")
print(monthly_frequency_planet)



initial_date_planet = planet['fecha_captura'].min()
final_date_planet = planet['fecha_captura'].max()
print("Initial date in Planet data:", initial_date_planet)
print("Final date in Planet data:", final_date_planet)

#landsat
landsat['fecha_captura'] = pd.to_datetime(landsat['fecha_captura'], format="%d/%m/%Y")

# Frecuencia de capturas de landsat
fechas_landsat = landsat["fecha_captura"].dropna().drop_duplicates()

yearly_frequency_landsat = (
    fechas_landsat.dt.year
    .value_counts()
    .sort_index()
)

monthly_frequency_landsat = (
    fechas_landsat.dt.to_period("M")
    .value_counts()
    .sort_index()
)

print("Capturas por año:")
print(yearly_frequency_landsat)

print("\nCapturas por año-mes:")
print(monthly_frequency_landsat)

initial_date_landsat = landsat['fecha_captura'].min()
final_date_landsat = landsat['fecha_captura'].max()
print("Initial date in Landsat data:", initial_date_landsat)
print("Final date in Landsat data:", final_date_landsat)    

#sentinel
sentinel['fecha_captura'] = pd.to_datetime(sentinel['fecha_captura'], format="%d/%m/%Y")
frequency_sentinel = sentinel['fecha_captura'].value_counts().sort_index()  
# Frecuencia de capturas de sentinel
fechas_sentinel = sentinel["fecha_captura"].dropna().drop_duplicates()

yearly_frequency_sentinel = (
    fechas_sentinel.dt.year
    .value_counts()
    .sort_index()
)

monthly_frequency_sentinel = (
    fechas_sentinel.dt.to_period("M")
    .value_counts()
    .sort_index()
)

print("Capturas por año:")
print(yearly_frequency_sentinel)

print("\nCapturas por año-mes:")
print(monthly_frequency_sentinel)
initial_date_sentinel = sentinel['fecha_captura'].min()
final_date_sentinel = sentinel['fecha_captura'].max()
print("Initial date in Sentinel data:", initial_date_sentinel)
print("Final date in Sentinel data:", final_date_sentinel)
# %%

print("intersecciones")
#imprimir las intersecciones entre los pares 
#planet y landsat dates 

print('planet y landsat', len(intersection_landsat_planet))

#planet y sentinel

print('planet y sentinel', len(intersection_sentinel_planet))

#sentinel y landsat
print('sentinel landsat', len(intersection_landsat_sentinel))
# %%
#para las 3 tabals guardarlas con las fechas ya tranformadas a datetime

#planet

from pathlib import Path

processed_dir = Path("data/processed/01_tablas_maestras")
processed_dir.mkdir(parents=True, exist_ok=True)

sentinel.to_csv(processed_dir / "sentinel.csv", index=False)
landsat.to_csv(processed_dir / "landsat.csv", index=False)
planet.to_csv(processed_dir / "planet.csv", index=False)
# %%
