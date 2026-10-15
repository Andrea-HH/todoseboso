"""Paired cluster resampling of immutable OOF, never an independent test."""
from pathlib import Path
import sys,json,hashlib,itertools
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
OUT=ROOT/'outputs/modeling/winner_predictions/v1'

def main():
    assert (OUT/'prediction_complete.json').exists()
    if (OUT/'manifest.json').exists():raise FileExistsError('Preserve completed results')
    cfg=json.loads((OUT/'frozen_design.json').read_text());dest=OUT/'statistics'
    p=pd.read_parquet(ROOT/'outputs/modeling/compact_ensemble/v1/tables/oof_predictions.parquet');p=p[p.experiment.isin(['C-T3','EQUAL3'])]
    ch=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet')
    ch=ch[ch.architecture.eq('A_CURRENT_CH_H_T')].copy();ch['experiment']='Champion';ch['protocol']='random'
    cols=['experiment','protocol','repeat','fold','ID_POLIGONO','y_true','y_pred'];p=pd.concat([p[cols],ch[cols]],ignore_index=True)
    assert len(p)==4968 and not p.duplicated(cols[:5]).any()
    t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');ids=t.ID_POLIGONO.tolist();lookup=t.set_index('ID_POLIGONO')
    np.testing.assert_allclose(p.y_true,lookup.loc[p.ID_POLIGONO].RENDIMIENTO_T_HA)
    split=joblib.load(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/frozen65_splits.joblib')
    valid={(pro,re,fo):set(t.iloc[va].ID_POLIGONO) for pro,re,fo,tr,va,inner in split}
    for (name,pro,re,fo),g in p.groupby(['experiment','protocol','repeat','fold']):assert set(g.ID_POLIGONO)==valid[(pro,re,fo)]
    p.to_parquet(dest/'compatible_oof.parquet',index=False);p.to_csv(dest/'compatible_oof.csv',index=False)
    groups=pd.read_csv(ROOT/'outputs/modeling/family_7/expansion/v1/splits/group_memberships.csv').set_index('ID_POLIGONO').loc[ids]
    rows=[];comparisons=[];repeat_metrics=[];region=[];omission=[]
    with threadpool_limits(limits=1):
        for pro,frame in p.groupby('protocol'):
            groupcol=cfg['statistics']['primary_clusters'][pro];group=groups[groupcol].to_numpy()
            weights,n_groups=cluster_weights(group,5000,2026);point=np.ones((1,138));boot={};predictions={}
            for name,g in frame.groupby('experiment'):
                matrix=g.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy();assert np.isfinite(matrix).all()
                y=lookup.loc[ids].RENDIMIENTO_T_HA.to_numpy();predictions[name]=matrix
                estimates=sampled_metrics(y,matrix,point);boot[name]=sampled_metrics(y,matrix,weights)
                entry=dict(experiment=name,protocol=pro,n_parcels=138,n_repeats=len(matrix),resampling_unit=groupcol,n_clusters=n_groups)
                for metric,values in boot[name].items():
                    entry[metric]=float(estimates[metric][0]);entry[metric+'_low95']=float(np.nanquantile(values,.025));entry[metric+'_high95']=float(np.nanquantile(values,.975))
                rows.append(entry)
                for re,h in g.groupby('repeat'):
                    h=h.set_index('ID_POLIGONO').loc[ids];m=sampled_metrics(h.y_true,h.y_pred,np.ones((1,138)))
                    repeat_metrics.append(dict(experiment=name,protocol=pro,repeat=re,**{k:float(v[0]) for k,v in m.items()}))
                    joined=h.join(lookup[['Estado','Municipio']])
                    for field in ['Estado','Municipio','fold']:
                        for zone,sub in joined.groupby(field):
                            met=sampled_metrics(sub.y_true,sub.y_pred,np.ones((1,len(sub))))
                            region.append(dict(experiment=name,protocol=pro,repeat=re,kind=field,zone=str(zone),n=len(sub),**{k:float(v[0]) for k,v in met.items()}))
                            keep=joined[joined[field]!=zone];m=sampled_metrics(keep.y_true,keep.y_pred,np.ones((1,len(keep))))
                            omission.append(dict(experiment=name,protocol=pro,repeat=re,kind=field,omitted=str(zone),**{k:float(v[0]) for k,v in m.items()}))
            for a,b in itertools.combinations(sorted(predictions),2):
                # Positive delta means model_a has more loss than model_b.
                ya=predictions[a];yb=predictions[b];loss=((ya-y)**2-(yb-y)**2).mean(axis=0)
                entry=dict(protocol=pro,model_a=a,model_b=b,delta_mse=float(loss.mean()),resampling_unit=groupcol,**paired_signflip(loss,group))
                pa=sampled_metrics(y,ya,point);pb=sampled_metrics(y,yb,point)
                for metric in pa:
                    delta=boot[a][metric]-boot[b][metric];entry['delta_'+metric]=float(pa[metric][0]-pb[metric][0]);entry['delta_'+metric+'_low95']=float(np.nanquantile(delta,.025));entry['delta_'+metric+'_high95']=float(np.nanquantile(delta,.975))
                comparisons.append(entry)
    summary=pd.DataFrame(rows);summary.to_csv(dest/'metrics_cluster_intervals.csv',index=False)
    comparisons=pd.DataFrame(comparisons);assert len(comparisons)==6;comparisons['p_mse_holm']=holm(comparisons.p_mse_signflip)
    comparisons.to_csv(dest/'paired_tests_and_intervals.csv',index=False)
    pd.DataFrame(repeat_metrics).to_csv(dest/'metrics_by_complete_repeat.csv',index=False)
    for name,data,key in [('regional',region,['experiment','protocol','kind','zone']),('omission_without_refit',omission,['experiment','protocol','kind','omitted'])]:
        d=pd.DataFrame(data);d.to_csv(dest/f'{name}_by_repeat.csv',index=False);d.drop(columns='repeat').groupby(key).mean(numeric_only=True).reset_index().to_csv(dest/f'{name}_summary.csv',index=False)
    # Replay final serialized predictors against 59 delivered rows.
    final=joblib.load(OUT/'models/final_winners_train138.joblib');x=pd.read_parquet(OUT/'tables/features197_target_free.parquet').set_index('ID_POLIGONO').loc[final['prediction_ids']].reset_index()
    delivered=pd.read_parquet(OUT/'tables/predictions59.parquet').set_index('ID_POLIGONO').loc[final['prediction_ids']]
    with threadpool_limits(limits=1):
        ct=final['ct3'].predict(x);gp=final['gpr'].predict(x);cb=final['catboost'];cp=np.asarray(cb.booster_.predict(cb.preprocess_.transform(x),thread_count=1));ch=np.column_stack([m.predict(x) for m in final['champion']]).sum(axis=1)
    replay={}
    for name,values in [('CT3_t_ha',ct),('Champion_t_ha',ch),('EQUAL3_t_ha',(ct+gp+cp)/3)]:
        delta=float(np.max(abs(delivered[name].to_numpy()-values)));assert delta==0.;replay[name]=delta
    (OUT/'audit/final_prediction_replay.json').write_text(json.dumps(replay,indent=2),encoding='utf-8')
    table=pd.read_csv(OUT/'tables/predictions59.csv');support=pd.read_csv(OUT/'tables/prediction_support.csv')
    with pd.ExcelWriter(OUT/'predicciones_ganadores_59.xlsx',engine='openpyxl') as writer:
        table.to_excel(writer,sheet_name='Predicciones_59',index=False);summary.to_excel(writer,sheet_name='Metricas_OOF_IC',index=False);comparisons.to_excel(writer,sheet_name='Comparaciones_pareadas',index=False);support.to_excel(writer,sheet_name='Soporte_predictivo',index=False)
    fig,axes=plt.subplots(1,2,figsize=(12,4.5))
    for name,col in [('C-T3','CT3_t_ha'),('Champion','Champion_t_ha'),('EQUAL3','EQUAL3_t_ha')]:
        axes[0].plot(np.arange(59),table[col],'.',label=name,alpha=.8)
    axes[0].set(xlabel='Parcela PRED (orden por ID)',ylabel='Rendimiento predicho, t/ha',title='59 predicciones; sin rendimiento observado');axes[0].legend()
    r=summary[summary.protocol.eq('random')].set_index('experiment').loc[['C-T3','Champion','EQUAL3']]
    axes[1].errorbar(np.arange(3),r.rmse,yerr=np.vstack([r.rmse-r.rmse_low95,r.rmse_high95-r.rmse]),fmt='o',capsize=5)
    axes[1].set(xticks=range(3),xticklabels=r.index,ylabel='RMSE, t/ha',title='OOF aleatoria: remuestreo por perfil\nIC descriptivos, predicciones congeladas')
    fig.tight_layout();fig.savefig(OUT/'statistics/predictions_and_validation.png',dpi=160);plt.close(fig)
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h for path,h in cfg['sha256'].items())
    sources=[ROOT/'src/winner_delivery.py',Path(__file__),ROOT/'scripts/411_predict_frozen_winners.py',ROOT/'tests/test_winner_delivery.py']
    (OUT/'manifest.json').write_text(json.dumps(dict(status='complete',n_train=138,n_PRED=59,n_winners=3,paired_hypotheses=6,tests_passed=4,protected_sources_unchanged=True,replay_max_difference=0.,champion_grouped_validation_available=False,statistical_interpretation='exploratory conditional fixed-OOF, not independent superiority confirmation',source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2),encoding='utf-8')
    print(summary[['experiment','protocol','rmse','rmse_low95','rmse_high95','mae','r2']].to_string(index=False));print(comparisons[['protocol','model_a','model_b','delta_rmse','delta_rmse_low95','delta_rmse_high95','p_mse_signflip','p_mse_holm']].to_string(index=False))

if __name__=='__main__':main()
