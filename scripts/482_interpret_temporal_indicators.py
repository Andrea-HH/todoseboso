"""Read-only grouped permutation within municipality; no new model training."""
from pathlib import Path
import sys,json,hashlib,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.temporal_indicator_weights import OUT,INDICATORS


def main():
    if (OUT/'indicator_interpretation_complete.json').exists():raise FileExistsError('Preserve interpretation')
    blocks={'historical_floors':INDICATORS[:2],'gap_dynamics':INDICATORS[2:5],'msi_upper_tail':[INDICATORS[5]],'season_shape_and_agreement':INDICATORS[6:8],'minimum_slope':[INDICATORS[8]]}
    names=[base+'_'+kind for base in ['CT3','J7'] for kind in ['C4_SHARED','C4_DIRECTIONAL','INDICATORS_DIRECT']]
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert (OUT/'evaluation_complete.json').exists();sources=[OUT/'tables/details.parquet',OUT/'cache/features_train138_target_free.parquet']+sorted((OUT/'models').glob('*.joblib'));protected={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}
    (OUT/'indicator_interpretation_design.json').write_text(json.dumps(dict(status='fixed_before_permutation',posthoc_exploratory=True,blocks=blocks,models=names,draws=5,seed=2026,method='Joint block permutation within municipality of each outer held-out fold. No retraining. Held-out Y only scores predictions. Candidate C4 stays unchanged for weight analyses.',limitations='Grouped permutation may break correlations with other blocks; missing historical support can be re-paired. Importance is not causal nor independent confirmation. Metrics recomputed over complete OOF, then repetitions.',source_sha256=protected),indent=2),encoding='utf-8')
    t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');x=pd.read_parquet(OUT/'cache/features_train138_target_free.parquet');details=pd.read_parquet(OUT/'tables/details.parquet');permuted=[];coefficients=[];coverage=t[['ID_POLIGONO','Estado','Municipio']].copy();coverage['history_missing']=x.I_history_ndvi_floor.isna();coverage.groupby(['Estado','Municipio']).history_missing.agg(['sum','count','mean']).reset_index().to_csv(OUT/'tables/historical_missingness_by_region.csv',index=False)
    with threadpool_limits(limits=1),warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for fi in range(65):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');va=pack['validation_positions'];frame=x.iloc[va].reset_index(drop=True);municipalities=t.iloc[va].Municipio.to_numpy();context=details[details.execution_index==fi];draw_orders={}
            for block in blocks:
                for draw in range(5):
                    rng=np.random.default_rng(2026+fi*1000+list(blocks).index(block)*20+draw);order=np.arange(len(va))
                    for municipality in np.unique(municipalities):
                        use=np.flatnonzero(municipalities==municipality);order[use]=rng.permutation(use)
                    draw_orders[(block,draw)]=order
            for name,item in pack['models'].items():
                direct=item['direct']
                if direct is not None:
                    cf=np.zeros(len(direct.columns))
                    if direct.model is not None:cf[direct.support]=direct.model.coef_
                    for feature,coefficient in zip(direct.columns,cf):coefficients.append(dict(execution_index=fi,experiment=name,protocol=context.protocol.iloc[0],feature=feature,coefficient=coefficient,nonzero=bool(abs(coefficient)>1e-10)))
                if name not in names:continue
                g=context[context.experiment==name].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO];bp=g.base_prediction.to_numpy();delta=g.candidate_delta.to_numpy()
                for block,columns in blocks.items():
                    for draw in range(5):
                        order=draw_orders[(block,draw)];altered=frame.copy();altered.loc[:,columns]=frame.iloc[order][columns].to_numpy()
                        applied=direct.predict_delta(altered) if direct is not None else item['weight'].predict_weight(altered,delta)*delta;pred=bp+applied
                        permuted.extend(dict(experiment=name,protocol=g.protocol.iloc[0],repeat=int(g['repeat'].iloc[0]),fold=int(g.fold.iloc[0]),ID_POLIGONO=t.iloc[pos].ID_POLIGONO,block=block,draw=draw,y_true=float(t.iloc[pos].RENDIMIENTO_T_HA),y_pred=float(pred[j]),reference_prediction=float(g.prediction.iloc[j])) for j,pos in enumerate(va))
            if fi%20==0:print(f'Permutation interpretation {fi+1}/65',flush=True)
    pd.DataFrame(coefficients).to_csv(OUT/'tables/direct_coefficients_by_fold.csv',index=False);pd.DataFrame(coefficients).groupby(['experiment','protocol','feature'])[['coefficient','nonzero']].mean().reset_index().to_csv(OUT/'tables/direct_coefficient_stability.csv',index=False);pred=pd.DataFrame(permuted);pred.to_parquet(OUT/'tables/grouped_permutation_predictions.parquet',index=False);metrics=[]
    for (name,pro,re,block,draw),g in pred.groupby(['experiment','protocol','repeat','block','draw']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;e=g.y_pred-g.y_true;ref=g.reference_prediction-g.y_true;tss=float(np.sum((g.y_true-g.y_true.mean())**2));rmse=float(np.sqrt(np.mean(e**2)));original=float(np.sqrt(np.mean(ref**2)));metrics.append(dict(experiment=name,protocol=pro,repeat=re,block=block,draw=draw,rmse=rmse,reference_rmse=original,delta_rmse=rmse-original,r2=1-float(np.sum(e**2))/tss,reference_r2=1-float(np.sum(ref**2))/tss))
    m=pd.DataFrame(metrics);m.to_csv(OUT/'tables/grouped_permutation_by_repeat.csv',index=False);m.groupby(['experiment','protocol','block']).agg(delta_rmse=('delta_rmse','mean'),permutation_sd=('delta_rmse','std'),rmse=('rmse','mean'),reference_rmse=('reference_rmse','mean'),r2=('r2','mean')).reset_index().to_csv(OUT/'tables/grouped_permutation_summary.csv',index=False)
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in protected.items());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'indicator_interpretation_complete.json').write_text(json.dumps(dict(status='complete',new_model_fits=0,permuted_OOF_rows=len(pred),models=names,blocks=len(blocks),draws=5,all_sources_unchanged=True),indent=2),encoding='utf-8');print('Interpretation complete:',len(pred),'permuted prediction rows; zero model fits.')


if __name__=='__main__':main()
