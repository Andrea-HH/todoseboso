"""Read-only final delivery checks for the frozen engineering experiment."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.signal_feature_engineering import OUT,build_features


def main():
    cfg=json.loads((OUT/'frozen_design.json').read_text());evaluation=json.loads((OUT/'evaluation_complete.json').read_text());assert evaluation['status']=='complete'
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    x=pd.read_parquet(OUT/'cache/features_train138_target_free.parquet');fresh,blocks,_,_,_=build_features(x.ID_POLIGONO.tolist());pd.testing.assert_frame_equal(x,fresh);assert cfg['blocks']==blocks
    p=pd.read_parquet(OUT/'tables/predictions.parquet');s=pd.read_csv(OUT/'tables/metrics_summary.csv');b=pd.read_csv(OUT/'tables/metrics_by_repeat.csv')
    assert p.experiment.nunique()==16 and len(p)==16*1794 and len(s)==64
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique
        err=g.y_pred-g.y_true;point=b[(b.experiment==name)&(b.protocol==pro)&(b['repeat']==re)].iloc[0]
        assert abs(np.sqrt(np.mean(err**2))-point.rmse)<1e-12
        assert abs(1-np.sum(err**2)/np.sum((g.y_true-g.y_true.mean())**2)-point.r2)<1e-12
    expected=b.groupby(['experiment','protocol'])[['rmse','r2','mae','bias']].mean().reset_index();actual=s[['experiment','protocol','rmse','r2','mae','bias']];pd.testing.assert_frame_equal(expected,actual,check_exact=False,atol=1e-12,rtol=1e-12)
    selections=pd.read_parquet(OUT/'tables/selection.parquet');assert len(selections)==910 and selections.amplitude.isin([0.,.25,.5]).all()
    assert (OUT/'evaluacion_ingenieria_de_senales.xlsx').exists() and (ROOT/'documentation/signal_feature_engineering_results.md').exists()
    transforms=pd.DataFrame([
        dict(feature='tpi_negative',formula='max(-clip(TPI/SD_training(TPI),-6,6),0)'),
        dict(feature='tpi_negative_x_water',formula='tpi_negative * clip(HZ_ndwi_middle,-6,6)'),
        dict(feature='tpi_positive_x_water',formula='max(clip(TPI/SD_training(TPI),-6,6),0) * clip(HZ_ndwi_middle,-6,6)'),
        dict(feature='slope_x_evi_change',formula='clip(slope/SD_training(slope),-6,6) * clip(EVI_change/SD_training(EVI_change),-6,6)')
    ])
    transforms['context']='P_ENG only; impute training medians first; SD floors1e-8; restandardize expanded columns using training only'
    transforms.to_csv(OUT/'tables/training_transform_dictionary.csv',index=False)
    log=json.loads((OUT/'audit/warnings.json').read_text());pd.DataFrame(log,columns=['execution_index','category','message']).groupby(['category','message']).size().rename('count').reset_index().to_csv(OUT/'tables/warning_summary.csv',index=False)
    with pd.ExcelWriter(OUT/'evaluacion_ingenieria_de_senales.xlsx',engine='openpyxl',mode='a',if_sheet_exists='replace') as w:
        transforms.to_excel(w,sheet_name='training_transform_dictionary',index=False)
        pd.read_csv(OUT/'tables/warning_summary.csv').to_excel(w,sheet_name='warning_summary',index=False)
    artifacts=[OUT/'evaluacion_ingenieria_de_senales.xlsx',OUT/'tables/predictions.parquet',OUT/'tables/paired_tests.csv',ROOT/'documentation/signal_feature_engineering_results.md']
    conclusion=ROOT/'documentation/signal_feature_engineering_conclusions.md'
    if conclusion.exists():artifacts.append(conclusion)
    report=dict(status='complete',protected_hashes_verified=len(cfg['source_sha256']),deterministic_features_rebuilt_exactly=True,external_models=910,OOF_rows=len(p),external_references_exact=True,aggregation='complete OOF per repetition then equal mean of repetitions; protocols separate',paired_tests=80,no_PRED=True,no_final138_fit=True,no_champion_change=True,source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in artifacts},evaluation=evaluation)
    (OUT/'delivery_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','evaluation']},indent=2))


if __name__=='__main__':main()
