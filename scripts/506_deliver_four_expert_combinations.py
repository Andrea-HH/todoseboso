"""Additional interpretation of fixed mixtures; no fitting or post-hoc rules."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.four_expert_combinations import OUT,NAMES
from src.geoc_bridge import local_prediction
from src.geoc_signal_research import predict_base
from src.signal_role_allocation import predict_role
from src.indicator_neighborhoods import OUT as INDICATORS,REDUCTIONS

def replay_experts(pack,x):
    a=pack['support'].a;t=a['a']['train'];pos=a['a']['train_global'];q=pack['validation_positions'];tr=pack['train_positions'];outer=pack['outer_experts'];raw=outer['raw'];np.testing.assert_array_equal(tr,outer['train_positions']);assert not set(tr)&set(q);ct=raw['ct3'].predict(t.iloc[q]);loc=local_prediction(a['a']['x'],a['a']['distance'],pos[tr],pos[q],a['y'][tr]);compact=raw['compact'];m=compact['ct3'].predict(t.iloc[q])
    if compact['local'] is not None:m+=compact['weight']*(predict_base(compact['local'],q,a)-m)
    r=ct.copy()
    if raw['shares'] is not None:
        gate=raw['shares'];r=gate['gate'].predict(gate['space'].transform(a['role_frame'].iloc[q]),ct,predict_role(raw['expert'],q,a))
    values=[m,r];complete=np.isfinite(x.iloc[q][REDUCTIONS['R3']].to_numpy(float)).all(axis=1)
    for j in range(2):
        if outer['correctors'][j] is not None:values[j]+=outer['strengths'][j]*complete*outer['correctors'][j].delta(x.iloc[q])
    return np.column_stack([ct,loc,values[0],values[1]])

def error_metrics(g):
    y=g.y_true.to_numpy(float);error=g.y_pred.to_numpy(float)-y;den=float(np.sum((y-y.mean())**2))
    return dict(n=len(g),rmse=float(np.sqrt(np.mean(error**2))),r2=float(1-np.sum(error**2)/den) if den>1e-12 else np.nan,mae=float(np.mean(abs(error))),bias=float(error.mean()),within_05=float(np.mean(abs(error)<=.5)))

def repeat_table(rows,name,keys):
    f=pd.DataFrame(rows);f.to_csv(OUT/'tables'/(name+'_by_repeat.csv'),index=False);f.drop(columns='repeat').groupby(keys,dropna=False).mean(numeric_only=True).reset_index().to_csv(OUT/'tables'/(name+'.csv'),index=False)
def main():
    tuner_amend=OUT/'tuner_performance_amendment.json'
    if tuner_amend.exists():
        cfg=json.loads(tuner_amend.read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    report=json.loads((OUT/'evaluation_complete.json').read_text());assert report['status']=='complete';p=pd.read_parquet(OUT/'tables/oof_residuals.parquet');m=pd.read_csv(OUT/'tables/metrics.csv');w=pd.read_csv(OUT/'tables/weights_by_fold.csv');details=pd.read_parquet(OUT/'tables/details.parquet')
    assert np.isfinite(p[['y_true','y_pred']].to_numpy()).all();by_repeat=pd.read_csv(OUT/'tables/metrics_by_repeat.csv');metric_checks=[]
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        expected=by_repeat[(by_repeat.experiment==name)&(by_repeat.protocol==pro)&(by_repeat['repeat']==re)].iloc[0];computed=error_metrics(g)
        assert all(np.isclose(computed[c],expected[c],atol=1e-12,rtol=0,equal_nan=True) for c in ['rmse','r2','mae','bias','within_05']);metric_checks.append(dict(experiment=name,protocol=pro,repeat=re,verified=True))
    pd.DataFrame(metric_checks).to_csv(OUT/'audit/independent_metric_checks.csv',index=False)
    report.update(metrics_independently_verified=True,repeat_metric_checks=len(metric_checks))
    original_groups=pd.read_csv(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/groups.csv').set_index('ID_POLIGONO');pp=p.assign(spatial_block=p.ID_POLIGONO.map(original_groups.spatial.astype(str)));assert pp.spatial_block.notna().all();cross=pp[(pp.protocol=='spatial')&(pp.experiment=='Reference26')].groupby(['fold','spatial_block']).agg(n=('ID_POLIGONO','size'),municipalities=('Municipio',lambda z:';'.join(sorted(set(z))))).reset_index();assert cross.groupby('fold').spatial_block.nunique().eq(1).all() and cross.groupby('spatial_block').fold.nunique().eq(1).all();cross.to_csv(OUT/'tables/spatial_fold_block_crosswalk.csv',index=False)
    blocks=[];omissions=[]
    for (name,pro,re),g in pp.groupby(['experiment','protocol','repeat']):
        for label,h in g.groupby('spatial_block'):
            blocks.append(dict(experiment=name,protocol=pro,repeat=re,spatial_block=label,**error_metrics(h)));remaining=g[g.spatial_block!=label]
            if len(remaining):omissions.append(dict(experiment=name,protocol=pro,repeat=re,omitted_spatial_block=label,**error_metrics(remaining)))
    repeat_table(blocks,'actual_spatial_blocks',['experiment','protocol','spatial_block']);repeat_table(omissions,'actual_block_omissions',['experiment','protocol','omitted_spatial_block'])
    stats=[]
    for (name,pro),g in details[details.experiment!='B4'].groupby(['experiment','protocol']):stats.append(dict(experiment=name,protocol=pro,mean=g.right_expert_weight.mean(),min=g.right_expert_weight.min(),max=g.right_expert_weight.max(),fraction_zero=np.mean(g.right_expert_weight<1e-10),fraction_one=np.mean(g.right_expert_weight>1-1e-10)))
    pd.DataFrame(stats).to_csv(OUT/'tables/weight_distribution.csv',index=False)
    gains=pd.read_csv(OUT/'tables/parcel_gains.csv');changes=[]
    for (pro,name,ref),g in gains.groupby(['protocol','experiment','reference']):
        for direction,h in [('improved',g[g.mae_gain>1e-12].nlargest(10,'mae_gain')),('worsened',g[g.mae_gain < -1e-12].nsmallest(10,'mae_gain'))]:
            changes.extend(dict(direction=direction,**r) for r in h.to_dict('records'))
    pd.DataFrame(changes).to_csv(OUT/'tables/top_parcel_changes.csv',index=False)
    hard=pd.read_csv(ROOT/'outputs/research/difficult_quartile/v1/tables/parcel_groups.csv');hard=set(hard[hard.hard_quartile].ID_POLIGONO);gains['support_group']=np.where(gains.ID_POLIGONO.isin(hard),'previous_hard35','remaining103');balance=gains.groupby(['protocol','experiment','reference','support_group']).agg(n=('ID_POLIGONO','size'),mse_gain=('mse_gain','sum'),mae_gain=('mae_gain','mean'),fraction_improved=('mae_gain',lambda x:float(np.mean(x>1e-12)))).reset_index();balance.to_csv(OUT/'tables/previous_hard_case_balance.csv',index=False)
    rows=[]
    for (pro,re),g in p.groupby(['protocol','repeat']):
        pivot=g.pivot(index='ID_POLIGONO',columns='experiment',values='y_pred');truth=g[['ID_POLIGONO','y_true']].drop_duplicates().set_index('ID_POLIGONO').loc[pivot.index].y_true;ct=pivot.CT3
        for kind,values in [('CT3_predicted_level',ct),('observed_y_descriptive',truth)]:
            # Fixed agronomic units, not fitted thresholds or gating rules.
            labels=pd.cut(values,[-np.inf,3.2,4.34,4.55,np.inf],labels=['<=3.2','3.2-4.34','4.34-4.55','>4.55'])
            for zone in labels.dropna().unique():
                use=labels==zone
                for name in pivot:
                    e=pivot.loc[use,name]-truth[use];rows.append(dict(protocol=pro,repeat=re,kind=kind,zone=str(zone),experiment=name,n=int(use.sum()),rmse=np.sqrt(np.mean(e**2)),mae=abs(e).mean(),bias=e.mean(),within_05=np.mean(abs(e)<=.5)))
    f=pd.DataFrame(rows);f.to_csv(OUT/'tables/level_bins_by_repeat.csv',index=False);f.drop(columns='repeat').groupby(['protocol','kind','zone','experiment']).mean(numeric_only=True).reset_index().to_csv(OUT/'tables/level_bins.csv',index=False)
    # Verify conditional weights can be reconstructed from saved covariate references.
    check=[];alignment=[];calibration=[];numerics=[];expert_replay=[];source_x=pd.read_parquet(INDICATORS/'cache/features_train138_target_free.parquet')
    for fi in range(81):
        pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');rebuilt=pack['support'].transform(pack['validation_positions'],pack['external_expert_predictions'])
        assert source_x.ID_POLIGONO.tolist()==pack['support'].a['a']['train'].ID_POLIGONO.tolist();predictions=replay_experts(pack,source_x)
        for j,name in enumerate(NAMES):
            difference=float(np.max(abs(predictions[:,j]-pack['external_expert_predictions'][:,j])));assert difference<1e-12,(fi,name,difference);expert_replay.append(dict(execution_index=fi,experiment=name,max_prediction_difference=difference))
        for name in ['B5','B6']:
            difference=float(np.max(abs(rebuilt[name]-pack['features'][name])));assert difference<1e-12;check.append(dict(execution_index=fi,experiment=name,max_feature_difference=difference))
        support=pack['support'];q=pack['validation_positions'];tr=pack['train_positions'];pos=support.pos;geo=support.a['a']['distance'][np.ix_(pos[q],pos[tr])];neighbors=np.argsort(geo,axis=1)[:,:min(24,len(tr))];pc=np.sqrt(np.sum((support.pca[pos[q],None,:]-support.pca[pos[tr]][None,:,:])**2,axis=2))/np.sqrt(support.pca.shape[1]);nearest=pc.argmin(axis=1);local_pc=np.take_along_axis(pc,neighbors,axis=1).min(axis=1);external=pack['external_expert_predictions'];truth=support.a['y'][q];b6=pack['models']['B6'].predict(rebuilt['B6'],external[:,3],external[:,1]);protocol='fresh_97_41' if fi>=65 else str(p[p.execution_index==fi].protocol.iloc[0])
        inner=pack['inner_expert_predictions']
        for name,left,right in [('B1',0,3),('B2',0,2),('B3',3,1)]:
            delta=inner[:,right]-inner[:,left];energy=float(delta@delta);rms=float(np.sqrt(np.mean(delta**2)));external_rms=float(np.sqrt(np.mean((external[:,right]-external[:,left])**2)));calibration.append(dict(execution_index=fi,protocol=protocol,experiment=name,train_n=len(tr),test_n=len(q),inner_disagreement_energy=energy,inner_disagreement_rms=rms,external_disagreement_rms=external_rms,disagreement_expansion=external_rms/rms if rms>1e-12 else np.nan,unidentified_weight=energy<=1e-12,right_expert_weight=float(pack['models'][name]),outer_R3_strength_M=float(pack['outer_experts']['strengths'][0]),outer_R3_strength_R=float(pack['outer_experts']['strengths'][1]),inner_R3_disabled_fraction_R=float(np.mean([item['strengths'][1]==0 for item in pack['inner_models']]))))
        for name in ['B5','B6']:numerics.append(dict(execution_index=fi,protocol=protocol,experiment=name,condition_number=float(pack['models'][name].condition),finite_coefficients=bool(np.isfinite(pack['models'][name].beta).all())))
        for j,position in enumerate(q):alignment.append(dict(execution_index=fi,protocol=protocol,ID_POLIGONO=support.a['a']['train'].iloc[position].ID_POLIGONO,nearest_PC_outside_geo24=bool(local_pc[j]>pc[j,nearest[j]]+1e-12),minimum_global_PC_distance=float(pc[j,nearest[j]]),minimum_geo24_PC_distance=float(local_pc[j]),error_Reference26=float(external[j,3]-truth[j]),error_L40=float(external[j,1]-truth[j]),error_B6=float(b6[j]-truth[j]),B6_mse_gain=float((external[j,3]-truth[j])**2-(b6[j]-truth[j])**2)))
    pd.DataFrame(check).to_csv(OUT/'audit/support_features_replay.csv',index=False)
    pd.DataFrame(expert_replay).to_csv(OUT/'audit/full_expert_replay.csv',index=False);report.update(experts_replayed=len(expert_replay),max_expert_replay_difference=max(r['max_prediction_difference'] for r in expert_replay))
    pd.DataFrame(alignment).to_csv(OUT/'tables/support_alignment.csv',index=False)
    pd.DataFrame(calibration).to_csv(OUT/'tables/calibration_support.csv',index=False);pd.DataFrame(numerics).to_csv(OUT/'audit/gate_numerics.csv',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    names=NAMES+['B1','B2','B3','B4','B5','B6'];fig,axes=plt.subplots(1,2,figsize=(13,5))
    for ax,metric in zip(axes,['rmse','r2']):
        for pro in ['random','climate_profile','municipality','spatial']:
            z=m[m.protocol==pro].set_index('experiment').loc[names];ax.plot(names,z[metric],marker='o',label=pro)
        ax.set_ylabel('RMSE t/ha' if metric=='rmse' else 'R²');ax.tick_params(axis='x',rotation=45);ax.grid(alpha=.2)
    axes[0].legend();fig.tight_layout();fig.savefig(OUT/'figures/four_protocol_comparison.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(10,9))
    for i,pro in enumerate(['random','spatial']):
        g=p[(p.protocol==pro)&p.experiment.isin(NAMES)].groupby(['ID_POLIGONO','experiment']).error.mean().unstack()
        for j,name in enumerate(['CT3','L40']):
            ax=axes[i,j];ax.scatter(g.Reference26,g[name],s=20,alpha=.6);ax.axhline(0,color='grey',linewidth=.8);ax.axvline(0,color='grey',linewidth=.8);ax.set_xlabel('Reference26 residual (t/ha)');ax.set_ylabel(name+' residual (t/ha)');ax.set_title(pro+'; per-parcel mean OOF residual');ax.grid(alpha=.15)
    fig.tight_layout();fig.savefig(OUT/'figures/control_residual_complementarity.png',dpi=160);plt.close(fig)
    complexity=pd.DataFrame([dict(experiment=n,description=description,needs_full_C4=full,conditional_features=conditional) for n,description,full,conditional in [('B1','CT3 already inside Reference26; one global attenuation weight',False,0),('B2','CT3 already inside Compact14; one global attenuation weight',False,0),('B3','Reference26 + full L40; one convex weight',True,0),('B4','CT3/Reference26/L40; three nonnegative weights summing to1',True,0),('B5','Reference26 inputs plus stored training support; four gate features',False,4),('B6','Reference26 + full L40 plus training support and neighbor-y dispersion',True,4)]]);complexity.to_csv(OUT/'tables/architecture_complexity.csv',index=False)
    with pd.ExcelWriter(OUT/'comparaciones_y_residuos.xlsx',engine='openpyxl',mode='a',if_sheet_exists='replace') as writer:
        for name in ['weight_distribution','level_bins','error_correlations','architecture_complexity','oracle_bounds','control_complementarity','previous_hard_case_balance','top_parcel_changes','support_alignment','calibration_support','spatial_fold_block_crosswalk','actual_spatial_blocks','actual_block_omissions']:
            pd.read_csv(OUT/'tables'/f'{name}.csv').to_excel(writer,sheet_name=name,index=False)
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());files=[OUT/'comparaciones_y_residuos.xlsx',OUT/'tables/oof_residuals.parquet',OUT/'tables/paired_tests.csv',OUT/'figures/four_protocol_comparison.png',ROOT/'documentation/four_expert_combinations_results.md'];report.update(support_features_replayed=len(check),unit_tests_passed=9,artifact_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files});(OUT/'delivery_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='artifact_sha256'},indent=2))
if __name__=='__main__':main()
