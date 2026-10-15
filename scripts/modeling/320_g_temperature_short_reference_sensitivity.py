"""Describe how including 2024 changes the short thermal reference; no model fits."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from family_1.climate_signal_features import sha

def run():
    source=ROOT/'outputs/modeling/family_1/g_temperature_signal/v1/tables/03_same_month_year_differences.csv'
    digest=sha(source)
    out=ROOT/'outputs/data_audit/family_1/g_temperature_signal/short_reference_sensitivity_v1'
    out.mkdir(parents=True,exist_ok=False)
    data=pd.read_csv(source);data=data[data.variable.isin(['tmin_mean','tmax_mean'])].copy()
    data['reference_2022_23']=data[['2022','2023']].mean(axis=1)
    data['anomaly_2025_vs_2022_23']=data['2025']-data.reference_2022_23
    data['reference_shift_from_2024']=data.historical_2022_24-data.reference_2022_23
    data['anomaly_sign_changes']=np.sign(data.delta_2025)!=np.sign(data.anomaly_2025_vs_2022_23)
    np.testing.assert_allclose(data.anomaly_2025_vs_2022_23-data.delta_2025,data.reference_shift_from_2024,rtol=1e-12,atol=1e-12)
    data.to_csv(out/'monthly_reference_sensitivity.csv',index=False)
    fig,axes=plt.subplots(2,2,figsize=(15,9))
    for row,(var,label) in enumerate([('tmin_mean','Tmin'),('tmax_mean','Tmax')]):
        z=data[data.variable.eq(var)]
        for year in ['2022','2023','2024','2025']:
            axes[row,0].plot(z.month,z[year],'o-',label=year,lw=2.5 if year=='2025' else 1.5)
        axes[row,0].plot(z.month,z.historical_2022_24,'k--',label='Referencia 2022–24')
        axes[row,0].set(title=label+' — cada año por separado',xlabel='Mes',ylabel='Promedio entre parcelas (°C)');axes[row,0].legend(ncol=2)
        axes[row,1].bar(z.month-.18,z.delta_2025,width=.36,label='2025 menos 2022–24')
        axes[row,1].bar(z.month+.18,z.anomaly_2025_vs_2022_23,width=.36,label='2025 menos 2022–23 (sensibilidad)')
        axes[row,1].axhline(0,c='black',lw=1);axes[row,1].set(title=label+' — efecto de incluir 2024',xlabel='Mes',ylabel='Diferencia (°C)');axes[row,1].legend()
    fig.suptitle('Abril–octubre: referencias de 2 o 3 años, sin inferencia de cambio climático',fontsize=15)
    fig.tight_layout();fig.savefig(out/'temperature_reference_sensitivity.png',dpi=170);plt.close(fig)
    assert sha(source)==digest
    report='''# Sensibilidad de la referencia térmica corta a 2024

Se separan 2022, 2023, 2024 y 2025, con el mismo mes y las mismas 197 parcelas. Los datos describen promedios mensuales de Tmin/Tmax, no extremos diarios ni promedios nacionales. No se usan etiquetas de rendimiento.

2024 eleva especialmente la referencia de Tmax de abril y mayo. En mayo, 2025 queda por debajo de la media 2022–24, pero por encima de 2022–23: el signo depende de esta referencia corta. En junio, 2025 sigue siendo más frío bajo ambas referencias. 2024 no fue uniformemente el año de mayor Tmax en todos los meses.

Excluir 2024 es una sensibilidad descriptiva para mostrar su influencia; no convierte dos años en una normal climatológica ni justifica eliminar un año caliente. La OMM define normales estándar sobre 30 años: [WMO Climatological Normals](https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/climate-services/wmo-climatological-normals).

No se pueden identificar ni descartar tendencias de cambio climático a partir de estas cuatro observaciones anuales por mes. Para ese objetivo se necesita una serie homogénea de largo plazo, con control de cambios de fuente y cobertura.

Este diagnóstico no altera las ablaciones G/H: las principales usan valores mensuales originales de 2025, no anomalías seleccionadas según 2024. No se ha cambiado ninguna especificación ni entrenado modelos.

![Años separados y sensibilidad de anomalías](temperature_reference_sensitivity.png)

[Tabla mensual completa](monthly_reference_sensitivity.csv)
'''
    (out/'report.md').write_text(report,encoding='utf-8')
    manifest=dict(status='complete',input_hash=digest,source_hash=sha(Path(__file__)),models_fitted=0,artifacts={p.name:sha(p) for p in out.iterdir() if p.is_file()})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(data[['variable','month','2024','2025','historical_2022_24','reference_2022_23','delta_2025','anomaly_2025_vs_2022_23']].round(3).to_string(index=False))

if __name__=='__main__':run()
