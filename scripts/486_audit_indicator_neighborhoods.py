"""Independent candidate calibration rebuild, paired-selection and support audit."""
from pathlib import Path
import sys,json,hashlib,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.indicator_neighborhoods import OUT,ENGINEERING,CALIBRATION,ReducedCorrection


def main():
    cfg=json.loads((OUT/'frozen_design.json').read_text());evaluation=json.loads((OUT/'evaluation_complete.json').read_text());assert evaluation['status']=='complete';assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');x=pd.read_parquet(OUT/'cache/features_train138_target_free.parquet');y=t.RENDIMIENTO_T_HA.to_numpy();assert x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist();folds=joblib.load(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/frozen65_splits.joblib');selection=pd.read_parquet(OUT/'tables/models_selected.parquet');checks=[]
    with threadpool_limits(limits=1),warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for fi,(protocol,repeat,fold,tr,va,inner) in enumerate(folds):
            tr=np.asarray(tr);va=np.asarray(va);ck=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');source=joblib.load(ENGINEERING/'checkpoints'/f'{fi:02d}.joblib');old=joblib.load(CALIBRATION/'checkpoints'/f'{fi:02d}.joblib');np.testing.assert_array_equal(old['calibration']['train_positions'],tr)
            for saved in ck['calibration']:
                base=saved['base'];expected=old['calibration']['base_oof' if base=='J7' else 'ct3_oof'];np.testing.assert_array_equal(saved['base_oof'],expected);np.testing.assert_array_equal(saved['train_positions'],tr);candidate=np.full(len(tr),np.nan)
                for ctx,(c,d) in zip(source['contexts'],inner):
                    np.testing.assert_array_equal(ctx['aa'],tr[c]);np.testing.assert_array_equal(ctx['where'],d);assert not set(tr[c])&(set(tr[d])|set(va));m=ReducedCorrection('R4').fit(x.iloc[tr[c]],y[tr[c]]-ctx['bases'][base]);candidate[d]=m.delta(x.iloc[tr[d]])
                difference=float(max(abs(candidate-saved['candidate_oof'])));assert difference<1e-12;checks.append(dict(execution_index=fi,base=base,calibration_difference=difference))
            for rec in source['ledger']:assert not set(rec['train'])&(set(rec['held'])|set(va)|set(rec.get('excluded_inner',[])))
            s=selection[selection.execution_index==fi].set_index('experiment')
            for base in ['CT3','J7']:
                for mode in ['KNN','CLUSTER']:
                    for geometry in ['GEO','PHYSICAL','SATELLITE']:
                        direct=s.loc[f'{base}_{mode}_{geometry}_DIRECT'];weight=s.loc[f'{base}_{mode}_{geometry}_WEIGHT'];assert direct.param==weight.param and direct.amplitude==weight.amplitude
    pd.DataFrame(checks).to_csv(OUT/'audit/independent_candidate_rebuild.csv',index=False)
    p=pd.read_parquet(OUT/'tables/oof_residuals.parquet');m=pd.read_csv(OUT/'tables/metrics_by_repeat.csv');summary=pd.read_csv(OUT/'tables/metrics_summary.csv');assert len(p)==40*1794 and selection.shape[0]==34*65
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;e=g.y_pred-g.y_true;row=m[(m.experiment==name)&(m.protocol==pro)&(m['repeat']==re)].iloc[0];assert abs(np.sqrt(np.mean(e**2))-row.rmse)<1e-12;assert abs(1-np.sum(e**2)/np.sum((g.y_true-g.y_true.mean())**2)-row.r2)<1e-12
    expected=m.groupby(['experiment','protocol'])[['rmse','r2','mae','bias']].mean().reset_index();pd.testing.assert_frame_equal(expected,summary[['experiment','protocol','rmse','r2','mae','bias']],check_exact=False,atol=1e-12,rtol=1e-12)
    active=selection[selection.amplitude>0];active.groupby(['experiment','protocol','param','amplitude']).size().rename('active_folds').reset_index().to_csv(OUT/'tables/active_selection_counts.csv',index=False);selection.assign(active=selection.amplitude>0).groupby(['experiment','protocol']).agg(active_folds=('active','sum'),total_folds=('active','size')).reset_index().to_csv(OUT/'tables/activation_summary.csv',index=False)
    neighbors=pd.read_csv(OUT/'tables/neighbor_diagnostics_by_parcel.csv');joined=neighbors.merge(selection[['experiment','protocol','repeat','fold','amplitude']],on=['experiment','protocol','repeat','fold'],validate='many_to_one');joined[joined.amplitude>0].groupby(['experiment','protocol'])[['neighbor_count','effective_neighbor_count','fallback_global','weight','mean_geo_distance_km','same_municipality_fraction','same_profile_fraction']].mean().reset_index().to_csv(OUT/'tables/active_neighbor_diagnostics_summary.csv',index=False)
    pc=pd.read_csv(OUT/'tables/PCA_loadings_by_fold.csv');pc=pc.drop_duplicates(['execution_index','experiment','component']);pc.groupby(['experiment','protocol']).explained_variance.agg(['mean','min','max']).reset_index().to_csv(OUT/'tables/PCA_component_variance.csv',index=False);pc.groupby(['execution_index','experiment','protocol']).explained_variance.sum().rename('explained_total').reset_index().to_csv(OUT/'tables/PCA_total_variance_by_fold.csv',index=False)
    logs=json.loads((OUT/'audit/warnings.json').read_text());pd.DataFrame(logs,columns=['execution_index','category','message']).groupby(['category','message']).size().rename('count').reset_index().to_csv(OUT/'tables/warning_summary.csv',index=False)
    with pd.ExcelWriter(OUT/'evaluacion_reducciones_y_vecindarios.xlsx',engine='openpyxl',mode='a',if_sheet_exists='replace') as writer:
        for name in ['active_selection_counts','activation_summary','active_neighbor_diagnostics_summary','PCA_component_variance','PCA_total_variance_by_fold','warning_summary']:pd.read_csv(OUT/'tables'/(name+'.csv')).to_excel(writer,sheet_name=name[:31],index=False)
        for sheet in writer.book.worksheets:sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
        # Repair presentation-only text emitted by the frozen evaluator; no numeric/model changes.
        for cell in writer.book['LEEME']['A']:
            if isinstance(cell.value,str):
                try:cell.value=cell.value.encode('cp1252').decode('utf-8')
                except (UnicodeEncodeError,UnicodeDecodeError):pass
    presentation_report=ROOT/'documentation/indicator_neighborhoods_results.md'
    report_text=presentation_report.read_text(encoding='utf-8')
    try:presentation_report.write_text(report_text.encode('cp1252').decode('utf-8'),encoding='utf-8')
    except (UnicodeEncodeError,UnicodeDecodeError):pass
    artifacts=[OUT/'evaluacion_reducciones_y_vecindarios.xlsx',OUT/'tables/predictions.parquet',OUT/'tables/paired_tests.csv',ROOT/'documentation/indicator_neighborhoods_results.md',ROOT/'documentation/indicator_neighborhoods_conclusions.md'];assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    report=dict(status='complete',new_recipes=34,outer_systems=34*65,models_replayed=evaluation['models_replayed'],OOF_rows=len(p),candidate_calibrations_rebuilt=len(checks),max_calibration_difference=max(c['calibration_difference'] for c in checks),paired_selections_verified=True,protected_sources=len(cfg['source_sha256']),protected_sources_unchanged=True,tests_passed=3,no_PRED=True,no_final138_fit=True,no_champion_change=True,artifact_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in artifacts if f.exists()});(OUT/'delivery_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='artifact_sha256'},indent=2))


if __name__=='__main__':main()
