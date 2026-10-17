"""Descriptive extension: ten largest J7 random OOF errors; no model training."""
from pathlib import Path
import importlib.util
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
# Resolve the preserved original audit by its numeric prefix.
source=next((ROOT/'scripts').glob('451*.py'))
spec=importlib.util.spec_from_file_location('caseaudit',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=ROOT/'outputs/research/case_outliers_and_model_residual_comparison/v1/tables'
e=pd.read_csv(old/'all_parcel_errors.csv')
top=e[(e.experiment=='J7_BOTH')&(e.protocol=='random')].nlargest(10,'mean_squared_error').copy()
m.OUT=ROOT/'outputs/research/top10_difficult_parcels/v1';m.CASES=top.ID_POLIGONO.tolist()
if __name__=='__main__':
 m.main()
 top.to_csv(m.OUT/'tables/top10_J7_random.csv',index=False)
 e[e.ID_POLIGONO.isin(m.CASES)].to_csv(m.OUT/'tables/top10_errors_all_models_protocols.csv',index=False)
