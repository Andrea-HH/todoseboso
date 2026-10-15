"""Exploratory physical-similarity OOF results, inference and exact replay audit."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import data,OLD,OUT as BRIDGE
from src.calendar_expansion import metric
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
OUT=ROOT/'outputs/modeling/physical_similarity/v2';D=OUT/'diagnostics'

def main():
    assert (OUT/'execution_complete.json').exists()
    if (OUT/'manifest.json').exists():raise FileExistsError('Preserve completed diagnostics')
    cfg=json.loads((OUT/'frozen_design.json').read_text());t=data()['train'];ids=t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy()
    p=pd.read_parquet(OUT/'tables/predictions.parquet');expected=(len(cfg['specs'])*3+2)*138*13
    assert len(p)==expected and not p.duplicated(['experiment','protocol','repeat','fold','ID_POLIGONO']).any()
    old=pd.read_parquet(BRIDGE/'tables/oof_predictions.parquet');old=old[(old.protocol!='geoc_target_matched')&old.experiment.isin(['LOCAL04D','FIXED50'])]
    nc=pd.read_parquet(ROOT/'outputs/modeling/nonclimatic_local/v1/tables/new_oof_predictions.parquet');nc=nc[(nc.protocol!='geoc_target_matched')&nc.experiment.isin(['NONCLIM_LOCAL','CT3_PLUS_NONCLIM','NONCLIM_PLUS_COMPACT_EN'])]
    p=pd.concat([p,old,nc],ignore_index=True);p.to_parquet(OUT/'tables/oof_with_references.parquet',index=False)
    z=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one')
    metrics=[];regions=[];omissions=[];pairs=[]
    for (name,pro,re),g in z.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique
        key=dict(experiment=name,protocol=pro,repeat=re)
        values=metric(g.y_true,g.y_pred);e=g.y_pred-g.y_true;values['error_variance']=float(np.mean((e-e.mean())**2));values['bias_squared']=values['bias']**2
        metrics.append(dict(**key,**values));pairs.append(dict(**key,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for value,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(value),n=len(h),**metric(h.y_true,h.y_pred)))
                rest=g[g[kind]!=value]
                if len(rest)>1:omissions.append(dict(**key,kind=kind,omitted=str(value),n=len(rest),**metric(rest.y_true,rest.y_pred)))
    for name,records,keys in [('metrics',metrics,['experiment','protocol']),('regions',regions,['experiment','protocol','kind','zone']),('omissions',omissions,['experiment','protocol','kind','omitted']),('intraprofile',pairs,['experiment','protocol'])]:
        d=pd.DataFrame(records);d.to_csv(D/f'{name}_by_repeat.csv',index=False);d.drop(columns='repeat').groupby(keys).mean(numeric_only=True).reset_index().to_csv(D/f'{name}_summary.csv',index=False)
    summary=pd.read_csv(D/'metrics_summary.csv');selection=pd.read_parquet(OUT/'tables/selection.parquet')
    sel=selection.groupby(['experiment','protocol']).agg(mean_amplitude=('amplitude','mean'),zero_fraction=('amplitude',lambda s:float((s==0).mean())),n_folds=('amplitude','size')).reset_index();sel.to_csv(D/'selection_summary.csv',index=False)
    selection.to_csv(D/'selection_by_fold.csv',index=False)
    selection[selection.experiment=='INTERNAL_SELECTOR'].groupby(['protocol','selected_variant']).size().rename('folds').reset_index().to_csv(D/'internal_selector_choices.csv',index=False)
    support=pd.read_parquet(OUT/'tables/support.parquet');support.groupby(['spec','protocol']).agg(nearest_distance=('nearest_distance','mean'),fraction_outside_nn90=('outside_nn90','mean'),same_profile_neighbor_weight=('same_profile_neighbor_weight','mean'),same_municipality_neighbor_weight=('same_municipality_neighbor_weight','mean'),effective_neighbors=('effective_neighbors','mean')).reset_index().to_csv(D/'physical_neighbor_support.csv',index=False)
    gdiag=pd.read_parquet(OUT/'tables/group_diagnostics.parquet');gdiag.to_csv(D/'groups_regional_concentration.csv',index=False)
    groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids];tests=[];gains=[]
    primary=list(selection.experiment.unique())
    with threadpool_limits(limits=1):
        for pro,frame in z.groupby('protocol'):
            cluster=pro if pro in ['municipality','spatial'] else 'climate_profile';group=groups[cluster].to_numpy();weights,n=cluster_weights(group,5000,2026)
            reference=frame[frame.experiment=='CT3'][['repeat','fold','ID_POLIGONO','y_pred']]
            for name in primary:
                j=frame[frame.experiment==name].merge(reference,on=['repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one')
                e=j.y_pred-j.y_true;f=j.y_pred_ref-j.y_true;j['sse_gain']=f**2-e**2;j['absolute_error_gain']=abs(f)-abs(e);gains.append(j)
                aa=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy();bb=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred_ref').reindex(columns=ids).to_numpy()
                delta=sampled_metrics(y,aa,weights)['rmse']-sampled_metrics(y,bb,weights)['rmse'];point=float(sampled_metrics(y,aa,np.ones((1,138)))['rmse'][0]-sampled_metrics(y,bb,np.ones((1,138)))['rmse'][0])
                loss=j.assign(d=e**2-f**2).groupby('ID_POLIGONO').d.sum().reindex(ids).to_numpy()
                tests.append(dict(experiment=name,reference='CT3',protocol=pro,delta_rmse=point,low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
    tests=pd.DataFrame(tests);assert len(tests)==len(primary)*4;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'paired_cluster_tests.csv',index=False)
    gains=pd.concat(gains,ignore_index=True);gains.to_parquet(D/'parcel_gains.parquet',index=False)
    avg=gains.groupby(['experiment','protocol','ID_POLIGONO','Estado','Municipio'],as_index=False)[['sse_gain','absolute_error_gain']].mean();avg.to_csv(D/'parcel_gains_mean_repeat.csv',index=False)
    largest=[]
    for _,h in avg.groupby(['experiment','protocol']):largest.extend([h.nlargest(5,'sse_gain').assign(direction='improvement'),h.nsmallest(5,'sse_gain').assign(direction='deterioration')])
    pd.concat(largest).to_csv(D/'largest_changes.csv',index=False)
    # How often apparent benefit survives dropping a whole region without refitting.
    om=pd.read_csv(D/'omissions_summary.csv');base=om[om.experiment=='CT3'].drop(columns='experiment')
    comparison=om.merge(base,on=['protocol','kind','omitted'],suffixes=('','_CT3'));comparison['delta_rmse']=comparison.rmse-comparison.rmse_CT3;comparison.to_csv(D/'omission_deltas_vs_CT3.csv',index=False)
    # Exact replay all saved correction models, including the internal selector.
    x=pd.read_parquet(OUT/'cache/features138_target_free.parquet');replay=[];checks=0
    with threadpool_limits(limits=1):
        for fi in range(65):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];assert not set(tr)&set(va)
            proto,repeat,fold,*_=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi];ct=pack['ct3'].predict(t.iloc[va]);parts={b:m.transform(x.iloc[va]) for b,m in pack['representations'].items()};saved={}
            for name,info in pack['correctors'].items():
                q=np.column_stack([parts[b] for b in info['atoms']])/np.sqrt(len(info['atoms']));pred=ct+info['amplitude']*info['model'].predict(q) if info['amplitude'] else ct.copy();saved[name]=pred
            saved['INTERNAL_SELECTOR']=saved[pack['selected_variant']];saved['CT3']=ct
            for name,pred in saved.items():
                expected=z[(z.experiment==name)&(z.protocol==proto)&(z['repeat']==repeat)&(z.fold==fold)].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();difference=float(np.max(abs(expected-pred)));assert difference<1e-12
                replay.append(dict(index=fi,experiment=name,max_difference=difference))
            for entry in pack['ledger']:assert entry['verified'];checks+=1
    pd.DataFrame(replay).to_csv(OUT/'audit/exact_replay.csv',index=False)
    protocols=['random','climate_profile','municipality','spatial'];table=summary.pivot(index='experiment',columns='protocol',values='rmse')[protocols]
    table.to_csv(D/'RMSE_four_protocols.csv')
    # Fixed diagnostic subset, not external winner selection.
    display=['CT3','LOCAL04D','INTERNAL_SELECTOR','PHYSICAL_BALANCED__ridge','PHYSICAL_BALANCED__neighbors','PHYSICAL_BALANCED__groups','DYNAMIC_BALANCED__ridge','ALL_BALANCED__ridge']
    fig,ax=plt.subplots(figsize=(11,5.5));xx=np.arange(4)
    for i,name in enumerate(display):ax.plot(xx,table.loc[name],marker='o',label=name)
    ax.set(xticks=xx,xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],ylabel='RMSE t/ha',title='Correcciones de C-T3 por semejanza: protocolos originales');ax.legend(fontsize=7);fig.tight_layout();fig.savefig(D/'comparison.png',dpi=150);plt.close(fig)
    with pd.ExcelWriter(OUT/'resultados_semejanza_fisica.xlsx',engine='openpyxl') as writer:
        for path,sheet in [(D/'metrics_summary.csv','Metricas'),(D/'RMSE_four_protocols.csv','RMSE_4_protocolos'),(D/'paired_cluster_tests.csv','Contrastes_exploratorios'),(D/'intraprofile_summary.csv','Intraperfil'),(D/'regions_summary.csv','Regiones'),(D/'selection_summary.csv','Amplitudes'),(D/'internal_selector_choices.csv','Selector_interno'),(D/'physical_neighbor_support.csv','Soporte_vecinos'),(OUT/'audit/block_exploration.csv','Exploracion_X'),(OUT/'audit/source_folder_triage.csv','Fuentes'),(OUT/'audit/features.csv','Variables')]:pd.read_csv(path).to_excel(writer,sheet_name=sheet,index=False)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items())
    execution=json.loads((OUT/'execution_complete.json').read_text());manifest=dict(status='complete',outer_folds=65,new_correction_recipes=len(primary),new_correction_oof=len(primary)*138*13,saved_models=65,exact_replay_max_difference=float(pd.DataFrame(replay).max_difference.max()),residual_exclusion_checks=checks,tests_passed=4,protected_sources_unchanged=True,no_new_final138_fit=True,no_new_PRED=True,statistical_tests=len(tests),statistical_scope='Exploratory clustered fixed-OOF comparisons vs CT3; Holm across this phase, not historical search',execution=execution,environment_warning='Console/test threadpoolctl reported co-loaded Intel and LLVM OpenMP; OMP_NUM_THREADS=MKL_NUM_THREADS=1; no crash observed. Fit warning log is separately preserved.',diagnostic_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(table.to_string());print('\nHOLM<.05');print(tests[tests.p_holm<.05].to_string(index=False));print('\nSELECTOR');print(selection[selection.experiment=='INTERNAL_SELECTOR'][['protocol','selected_variant','amplitude']].value_counts().to_string())

if __name__=='__main__':main()
