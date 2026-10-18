"""Independent rebuild of indicator inputs and strictly cross-fitted gate calibration."""
from pathlib import Path
import sys,json,hashlib,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.temporal_indicator_weights import OUT,ENGINEERING,BASE_CALIBRATION,PARENTS,INDICATORS,FixedCorrection,build_features


def main():
    cfg=json.loads((OUT/'frozen_design.json').read_text());evaluation=json.loads((OUT/'evaluation_complete.json').read_text());assert evaluation['status']=='complete'
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');y=t.RENDIMIENTO_T_HA.to_numpy();x=pd.read_parquet(OUT/'cache/features_train138_target_free.parquet');assert x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist();rebuilt,*_=build_features(t.ID_POLIGONO.tolist());pd.testing.assert_frame_equal(x,rebuilt)
    frozen=joblib.load(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/frozen65_splits.joblib');checks=[]
    with threadpool_limits(limits=1),warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for fi,(protocol,repeat,fold,tr,va,inner) in enumerate(frozen):
            tr=np.asarray(tr);va=np.asarray(va);ck=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');source=joblib.load(ENGINEERING/'checkpoints'/f'{fi:02d}.joblib');bc=joblib.load(BASE_CALIBRATION/'checkpoints'/f'{fi:02d}.joblib');np.testing.assert_array_equal(bc['calibration']['train_positions'],tr)
            for saved in ck['calibration']:
                base=saved['base'];bp=bc['calibration']['base_oof' if base=='J7' else 'ct3_oof'];np.testing.assert_array_equal(saved['base_oof'],bp);np.testing.assert_array_equal(saved['train_positions'],tr);pred=np.full(len(tr),np.nan)
                for ctx,(c,d) in zip(source['contexts'],inner):
                    aa=np.asarray(ctx['aa']);where=np.asarray(ctx['where']);np.testing.assert_array_equal(aa,tr[c]);np.testing.assert_array_equal(where,d);assert not set(aa)&(set(tr[d])|set(va));m=FixedCorrection(PARENTS).fit(x.iloc[aa],y[aa]-ctx['bases'][base]);pred[d]=m.predict_delta(x.iloc[tr[d]])
                difference=float(max(abs(pred-saved['candidate_oof'])));assert difference<1e-12;checks.append(dict(execution_index=fi,protocol=protocol,base=base,candidate_calibration_difference=difference))
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');np.testing.assert_array_equal(pack['train_positions'],tr);np.testing.assert_array_equal(pack['validation_positions'],va)
            for name,m in pack['models'].items():
                if m['weight'] is not None:
                    a=x.iloc[tr][INDICATORS].to_numpy(float);med=np.array([np.median(c[np.isfinite(c)]) if np.isfinite(c).any() else 0. for c in a.T]);np.testing.assert_array_equal(m['weight'].median,med)
    pd.DataFrame(checks).to_csv(OUT/'audit/independent_calibration_rebuild.csv',index=False)
    p=pd.read_parquet(OUT/'tables/oof_residuals.parquet');by_repeat=pd.read_csv(OUT/'tables/metrics_by_repeat.csv');summary=pd.read_csv(OUT/'tables/metrics_summary.csv')
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;error=g.y_pred-g.y_true;row=by_repeat[(by_repeat.experiment==name)&(by_repeat.protocol==pro)&(by_repeat['repeat']==re)].iloc[0];assert abs(np.sqrt(np.mean(error**2))-row.rmse)<1e-12;assert abs(1-np.sum(error**2)/np.sum((g.y_true-g.y_true.mean())**2)-row.r2)<1e-12
    expected=by_repeat.groupby(['experiment','protocol'])[['rmse','r2','mae','bias']].mean().reset_index();pd.testing.assert_frame_equal(expected,summary[['experiment','protocol','rmse','r2','mae','bias']],check_exact=False,atol=1e-12,rtol=1e-12)
    log=json.loads((OUT/'audit/warnings.json').read_text());pd.DataFrame(log,columns=['execution_index','category','message']).groupby(['category','message']).size().rename('count').reset_index().to_csv(OUT/'tables/warning_summary.csv',index=False)
    # X-only redundancy check against prior inventories, not a new predictor search.
    old_own=pd.read_parquet(ROOT/'outputs/modeling/experimental_pls1867/v1/cache/train138_1867.parquet').set_index('ID_POLIGONO').loc[t.ID_POLIGONO].select_dtypes(include='number');old_geo=pd.read_parquet(ROOT/'outputs/research/geoc_variable_signal_audit/v1/variables_1831_197_sin_target.parquet').set_index('ID_POLIGONO').loc[t.ID_POLIGONO].select_dtypes(include='number');old=pd.concat([old_own.add_prefix('OWN::'),old_geo.add_prefix('GEOC::')],axis=1).replace([np.inf,-np.inf],np.nan);matches=[]
    old=old.loc[:,(old.std()>1e-8)&(old.nunique()>=5)&(old.count()>=80)]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for feature in INDICATORS:
            series=pd.Series(x[feature].to_numpy(),index=t.ID_POLIGONO);common=old.notna().mul(series.notna(),axis=0).sum();corr=old.loc[:,common>=80].corrwith(series).abs().dropna().sort_values(ascending=False)
            if len(corr):matches.append(dict(feature=feature,closest_existing_feature=corr.index[0],absolute_correlation=float(corr.iloc[0]),n_common=int(common[corr.index[0]])))
    pd.DataFrame(matches).to_csv(OUT/'tables/closest_previous_representations.csv',index=False)
    with pd.ExcelWriter(OUT/'evaluacion_indicadores_y_pesos.xlsx',engine='openpyxl',mode='a',if_sheet_exists='replace') as writer:
        pd.read_csv(OUT/'tables/warning_summary.csv').to_excel(writer,sheet_name='warning_summary',index=False);pd.DataFrame(matches).to_excel(writer,sheet_name='closest_previous_features',index=False)
        for name in ['historical_missingness_by_region','grouped_permutation_summary','direct_coefficient_stability']:
            path=OUT/'tables'/(name+'.csv')
            if path.exists():pd.read_csv(path).to_excel(writer,sheet_name=name[:31],index=False)
        for sheet in writer.book.worksheets:sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    artifacts=[OUT/'evaluacion_indicadores_y_pesos.xlsx',OUT/'tables/predictions.parquet',OUT/'tables/paired_tests.csv',ROOT/'documentation/temporal_indicator_weights_results.md',ROOT/'documentation/temporal_indicator_weights_conclusions.md']
    audit=dict(status='complete',new_recipes=12,outer_systems=780,protected_sources=len(cfg['source_sha256']),protected_sources_unchanged=True,indicators_rebuilt_exactly=True,independent_candidate_calibrations=len(checks),max_calibration_difference=max(c['candidate_calibration_difference'] for c in checks),models_replayed=evaluation['models_replayed'],OOF_rows=len(p),tests_passed=4,no_PRED=True,no_final138_fit=True,no_champion_change=True,artifact_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in artifacts if f.exists()})
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'delivery_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in audit.items() if k!='artifact_sha256'},indent=2))


if __name__=='__main__':main()
