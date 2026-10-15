import numpy as np
import pandas as pd
from src.agronomic_calendar_features import strict_average,history_representation,build_year

def test_missing_month_not_silently_renormalized():
    assert np.isnan(strict_average(pd.Series({5:10.}),[5,6]))
    assert strict_average(pd.Series({5:10.,6:20.}),[5,6])==15.

def test_historical_reference_excludes_2025_and_requires_three_years():
    p=pd.DataFrame({'ID_POLIGONO':['A']*4,'year':[2022,2023,2024,2025],'CAL_x':[1.,2.,3.,100.]})
    a,_=history_representation(p)
    assert a.HIST_MEAN_CAL_x.iloc[0]==2.
    assert a.HIST_SD_CAL_x.iloc[0]==1.
    assert a.DELTA_CAL_x.iloc[0]==98.
    p.loc[0,'CAL_x']=np.nan
    a,_=history_representation(p);assert np.isnan(a.HIST_MEAN_CAL_x.iloc[0])

def test_month_weighting_cutoff_and_monthly_precipitation():
    s=pd.DataFrame({'ID_POLIGONO':['A']*4,'year':[2025]*4,'month':[5,5,6,11],
        'fecha_captura':pd.to_datetime(['2025-05-01','2025-05-20','2025-06-10','2025-11-01']),
        'cloud_raw':[0.]*4})
    for col in ['ndvi_promedio','evi_promedio','ndwi_promedio','msi_promedio','ndvi_std']:s[col]=[0.,2.,4.,999.]
    c=pd.DataFrame({'ID_POLIGONO':['A']*7,'year':[2025]*7,'month':range(4,11),'precip_mean':[10.]*7,'tmax_mean':[20.]*7,'tmin_mean':[5.]*7})
    a,_,_=build_year(s,c,['A'],2025)
    assert a.CAL_S2_ndvi_sowing_may_jun.iloc[0]==2.5
    assert a.CAL_CLIM_precip_sowing_may_jun.iloc[0]==20.
    assert a.CAL_CLIM_tmax_sowing_may_jun.iloc[0]==20.
    assert np.isnan(a.CAL_S2_ndvi_peak_month.iloc[0])
