"""Comparable OOF, nested audit and decisions for three conditional local lines."""
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
from src.geoc_bridge import OUT as BRIDGE,OLD
from src.conditional_local_phases import predict_leader
from src.calendar_expansion import metric
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
import importlib.util
spec=importlib.util.spec_from_file_location('runner432',ROOT/'scripts/432_run_conditional_local_phases.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
OUT=runner.OUT;D=OUT/'diagnostics'

def main():
    assert (OUT/'execution_complete.json').exists()
    if (OUT/'manifest.json').exists():raise FileExistsError('Preserve completed analysis')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assets=runner.load_assets();t=assets['a']['train'];ids=t.ID_POLIGONO.tolist();y=assets['y'];p=pd.read_parquet(OUT/'tables/predictions.parquet');assert len(p)==50232 and not p.duplicated(['experiment','protocol','repeat','fold','ID_POLIGONO']).any()
    old=pd.read_parquet(BRIDGE/'tables/oof_predictions.parquet');old=old[(old.experiment.isin(['LOCAL04D','FIXED50']))&(old.protocol!='geoc_target_matched')]
    nc=pd.read_parquet(runner.NC/'tables/new_oof_predictions.parquet');nc=nc[(nc.experiment=='NONCLIM_LOCAL')&(nc.protocol!='geoc_target_matched')];p=pd.concat([p,old,nc],ignore_index=True);p.to_parquet(OUT/'tables/oof_with_references.parquet',index=False);z=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one')
    metrics=[];pairs=[];regions=[];omissions=[]
    for (name,pro,re),g in z.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;key=dict(experiment=name,protocol=pro,repeat=re);v=metric(g.y_true,g.y_pred);e=g.y_pred-g.y_true;v.update(error_variance=float(np.mean((e-e.mean())**2)),bias_squared=v['bias']**2);metrics.append(dict(**key,**v));pairs.append(dict(**key,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for label,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(label),n=len(h),**metric(h.y_true,h.y_pred)));rest=g[g[kind]!=label]
                if len(rest)>1:omissions.append(dict(**key,kind=kind,omitted=str(label),n=len(rest),**metric(rest.y_true,rest.y_pred)))
    for name,rows,keys in [('metrics',metrics,['experiment','protocol']),('intraprofile',pairs,['experiment','protocol']),('regional',regions,['experiment','protocol','kind','zone']),('omissions',omissions,['experiment','protocol','kind','omitted'])]:
        d=pd.DataFrame(rows);d.to_csv(D/f'{name}_by_repeat.csv',index=False);d.drop(columns='repeat').groupby(keys).mean(numeric_only=True).reset_index().to_csv(D/f'{name}_summary.csv',index=False)
    selection=pd.read_parquet(OUT/'tables/selection.parquet');selection.to_csv(D/'selection_by_fold.csv',index=False);primary=[n for n in selection.experiment.unique() if n not in ['CT3','LEADER']];assert len(primary)==26
    sel=selection[selection.experiment.str.endswith('SELECTOR')];sel.groupby(['experiment','protocol','selected_variant']).size().rename('folds').reset_index().to_csv(D/'selector_choices.csv',index=False)
    groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids];tests=[];gains=[]
    with threadpool_limits(limits=1):
        for pro,g in z.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();weights,_=cluster_weights(group,5000,2026)
            for refname in ['CT3','LEADER']:
                ref=g[g.experiment==refname][['repeat','fold','ID_POLIGONO','y_pred']]
                for name in primary:
                    j=g[g.experiment==name].merge(ref,on=['repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');e=j.y_pred-j.y_true;f=j.y_pred_ref-j.y_true;j['reference']=refname;j['sse_gain']=f**2-e**2;j['absolute_error_gain']=abs(f)-abs(e);gains.append(j)
                    aa=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy();bb=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred_ref').reindex(columns=ids).to_numpy();delta=sampled_metrics(y,aa,weights)['rmse']-sampled_metrics(y,bb,weights)['rmse'];point=sampled_metrics(y,aa,np.ones((1,138)))['rmse'][0]-sampled_metrics(y,bb,np.ones((1,138)))['rmse'][0];loss=j.assign(loss=e**2-f**2).groupby('ID_POLIGONO').loss.sum().reindex(ids).to_numpy();tests.append(dict(experiment=name,reference=refname,protocol=pro,delta_rmse=float(point),low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
    tests=pd.DataFrame(tests);assert len(tests)==208;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'paired_cluster_tests.csv',index=False);gains=pd.concat(gains);gains.to_parquet(D/'parcel_gains.parquet',index=False);avg=gains.groupby(['experiment','reference','protocol','ID_POLIGONO','Estado','Municipio'])[['sse_gain','absolute_error_gain']].mean().reset_index();avg.to_csv(D/'parcel_gains_mean_repeat.csv',index=False)
    largest=[]
    for _,h in avg.groupby(['experiment','reference','protocol']):largest.extend([h.nlargest(5,'sse_gain').assign(direction='improvement'),h.nsmallest(5,'sse_gain').assign(direction='deterioration')])
    pd.concat(largest).to_csv(D/'largest_changes.csv',index=False)
    om=pd.read_csv(D/'omissions_summary.csv');out=[]
    for refname in ['CT3','LEADER']:
        ref=om[om.experiment==refname].drop(columns='experiment');j=om.merge(ref,on=['protocol','kind','omitted'],suffixes=('','_ref'));j['reference']=refname;j['delta_rmse']=j.rmse-j.rmse_ref;out.append(j)
    pd.concat(out).to_csv(D/'omission_deltas.csv',index=False)
    replay=[];weights_saved=[];fallbacks=[];checks=0;reference_diff=[]
    with threadpool_limits(limits=1):
        for fi in range(65):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];pro,re,fold,*_=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi];ct=pack['ct3'].predict(t.iloc[va]);predictions={};cache={}
            def expert(p):
                k=id(p)
                if k not in cache:cache[k]=predict_leader(p,va,assets)
                return cache[k]
            for name,m in pack['pipelines'].items():
                if m['type']=='ct3':pred=ct
                elif m['type']=='leader':pred=expert(m['leader'])
                elif m['type']=='gate':
                    q=m['space'].transform(assets['features'].iloc[va]) if m['space'] is not None else np.zeros((len(va),1));lp=expert(m['leader']);pred=m['gate'].predict(q,ct,lp);w=m['gate'].weights(q);assert np.all(pred>=np.minimum(ct,lp)-1e-12) and np.all(pred<=np.maximum(ct,lp)+1e-12)
                    weights_saved.extend(dict(experiment=name,protocol=pro,repeat=re,fold=fold,ID_POLIGONO=t.iloc[i].ID_POLIGONO,leader_weight=float(v)) for i,v in zip(va,w))
                elif m['type']=='residual':
                    pred=expert(m['leader']);amp=m['amplitude']
                    if amp:pred=pred+amp*m['model'].predict(m['space'].transform(assets['features'].iloc[va]))
                else:pred=predictions[m['name']]
                predictions[name]=pred;q=z[(z.experiment==name)&(z.protocol==pro)&(z['repeat']==re)&(z.fold==fold)].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();error=float(np.max(abs(q-pred)));assert error<1e-12;replay.append(dict(index=fi,experiment=name,max_difference=error))
            for entry in pack['ledger']:assert not set(entry['train'])&(set(entry['held'])|set(va));checks+=1
            for entry in pack['ct3_ledger']:assert entry['verified'];checks+=1
            reference_diff.append(pack['reference_max_difference'])
            # Cache context audit also covers contexts loaded on a resumed run.
            for path in (OUT/'cache'/f'{fi:02d}').glob('*.joblib'):
                m=joblib.load(path);positions=m['train_positions'];assert set(positions)<=set(tr) and not set(positions)&set(va)
                if m['fallback']:fallbacks.append(dict(index=fi,protocol=pro,n_train=len(positions),n_groups=int(groups.iloc[positions][pro].nunique()) if pro!='random' else len(positions),variant=m['local']['variant'],k=m['local']['k'],reason=m['fallback'],cache=str(path.relative_to(OUT))))
    pd.DataFrame(replay).to_csv(OUT/'audit/exact_replay.csv',index=False);pd.DataFrame(fallbacks).to_csv(OUT/'audit/deep_fallbacks.csv',index=False);w=pd.DataFrame(weights_saved);w.to_parquet(D/'expert_weights.parquet',index=False);w.groupby(['experiment','protocol']).leader_weight.agg(['mean','median','min','max']).reset_index().to_csv(D/'expert_weight_summary.csv',index=False)
    summary=pd.read_csv(D/'metrics_summary.csv');protocols=['random','climate_profile','municipality','spatial'];table=summary.pivot(index='experiment',columns='protocol',values='rmse')[protocols];table.to_csv(D/'RMSE_four_protocols.csv');fig,ax=plt.subplots(figsize=(10,5))
    for name in ['CT3','LEADER','P1_SELECTOR','P2_SELECTOR','P3_SELECTOR']:ax.plot(range(4),table.loc[name],marker='o',label=name)
    ax.set(xticks=range(4),xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],ylabel='RMSE t/ha',title='Tres líneas: selectores internos frente a referencias');ax.legend();fig.tight_layout();fig.savefig(D/'three_phase_comparison.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(OUT/'resultados_tres_fases.xlsx',engine='openpyxl') as writer:
        for path,sheet in [(D/'metrics_summary.csv','Metricas'),(D/'RMSE_four_protocols.csv','RMSE_4_protocolos'),(D/'selection_by_fold.csv','Seleccion_interna'),(D/'selector_choices.csv','Selectores'),(D/'expert_weight_summary.csv','Pesos_expertos'),(D/'paired_cluster_tests.csv','Contrastes'),(D/'intraprofile_summary.csv','Intraperfil'),(D/'regional_summary.csv','Regiones'),(OUT/'audit/deep_fallbacks.csv','Soporte_profundo')]:pd.read_csv(path).to_excel(writer,sheet_name=sheet,index=False)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items());(OUT/'manifest.json').write_text(json.dumps(dict(status='complete',new_recipes=26,new_correction_oof=46644,reference_oof=3588,tests_passed=3,exact_replay_max_difference=float(pd.DataFrame(replay).max_difference.max()),original_leader_reference_difference=max(reference_diff),exclusion_checks=checks,deep_fallback_contexts=len(fallbacks),comparisons=208,protected_sources_unchanged=True,no_final138_fit=True,no_PRED=True,diagnostic_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2),encoding='utf-8')
    print(table.to_string());print('\nHOLM<.05');print(tests[tests.p_holm<.05].to_string(index=False))

if __name__=='__main__':main()
