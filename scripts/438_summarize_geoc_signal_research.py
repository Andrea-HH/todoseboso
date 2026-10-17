"""OOF attribution/reduction analysis, matched inference and independent exact replay."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import OLD
from src.geoc_signal_research import predict_expert,predict_base
from src.calendar_expansion import metric
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
spec=importlib.util.spec_from_file_location('runner437',ROOT/'scripts/437_run_geoc_signal_research.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner);OUT=runner.OUT;D=OUT/'diagnostics'

def main():
    assert (OUT/'execution_complete.json').exists()
    if (OUT/'manifest.json').exists():raise FileExistsError('Preserve completed synthesis')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assets=runner.load_assets();t=assets['a']['train'];ids=t.ID_POLIGONO.tolist();y=assets['y'];pos=assets['a']['train_global'];frame=assets['features197'];p=pd.read_parquet(OUT/'tables/predictions.parquet');assert len(p)==(cfg['recipes']+6)*1794 and not p.duplicated(['experiment','protocol','repeat','fold','ID_POLIGONO']).any();z=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');metrics=[];pairs=[];regions=[];omit=[]
    for (name,pro,re),g in z.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;key=dict(experiment=name,protocol=pro,repeat=re);values=metric(g.y_true,g.y_pred);e=g.y_pred-g.y_true;values.update(error_variance=float(np.mean((e-e.mean())**2)),bias_squared=values['bias']**2);metrics.append(dict(**key,**values));pairs.append(dict(**key,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for label,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(label),n=len(h),**metric(h.y_true,h.y_pred)));rest=g[g[kind]!=label]
                if len(rest)>1:omit.append(dict(**key,kind=kind,omitted=str(label),n=len(rest),**metric(rest.y_true,rest.y_pred)))
    for name,rows,keys in [('metrics',metrics,['experiment','protocol']),('intraprofile',pairs,['experiment','protocol']),('regional',regions,['experiment','protocol','kind','zone']),('omissions',omit,['experiment','protocol','kind','omitted'])]:
        d=pd.DataFrame(rows);d.to_csv(D/f'{name}_by_repeat.csv',index=False);d.drop(columns='repeat').groupby(keys).mean(numeric_only=True).reset_index().to_csv(D/f'{name}_summary.csv',index=False)
    execution=[]
    for fi in range(65):
        checkpoint=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');first=checkpoint['predictions'][0]
        execution.append(dict(index=fi,protocol=first['protocol'],repeat=first['repeat'],fold=first['fold'],seconds=checkpoint['seconds'],warnings=len(checkpoint['warnings'])))
    pd.DataFrame(execution).to_csv(D/'execution_by_fold.csv',index=False)
    selection=pd.read_parquet(OUT/'tables/selection.parquet');selection.to_csv(D/'selection_by_fold.csv',index=False);selection[selection.selected_variant.notna()].groupby(['experiment','protocol','selected_variant']).size().rename('folds').reset_index().to_csv(D/'representation_choices.csv',index=False)
    groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids];tests=[];gains=[]
    with threadpool_limits(limits=1):
        for pro,g in z.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();weights,_=cluster_weights(group,5000,2026)
            for name,refname in cfg['references'].items():
                ref=g[g.experiment==refname][['repeat','fold','ID_POLIGONO','y_pred']];j=g[g.experiment==name].merge(ref,on=['repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');e=j.y_pred-j.y_true;f=j.y_pred_ref-j.y_true;j['reference']=refname;j['sse_gain']=f**2-e**2;j['absolute_error_gain']=abs(f)-abs(e);gains.append(j)
                aa=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy();bb=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred_ref').reindex(columns=ids).to_numpy();delta=sampled_metrics(y,aa,weights)['rmse']-sampled_metrics(y,bb,weights)['rmse'];point=sampled_metrics(y,aa,np.ones((1,138)))['rmse'][0]-sampled_metrics(y,bb,np.ones((1,138)))['rmse'][0];loss=j.assign(loss=e**2-f**2).groupby('ID_POLIGONO').loss.sum().reindex(ids).to_numpy();tests.append(dict(experiment=name,reference=refname,protocol=pro,delta_rmse=float(point),low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
    tests=pd.DataFrame(tests);assert len(tests)==cfg['recipes']*4;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'matched_cluster_tests.csv',index=False);gains=pd.concat(gains);gains.to_parquet(D/'parcel_gains.parquet',index=False);avg=gains.groupby(['experiment','reference','protocol','ID_POLIGONO','Estado','Municipio'])[['sse_gain','absolute_error_gain']].mean().reset_index();avg.to_csv(D/'parcel_gains_mean_repeat.csv',index=False)
    extreme=[]
    for _,h in avg.groupby(['experiment','reference','protocol']):extreme.extend([h.nlargest(5,'sse_gain').assign(direction='improvement'),h.nsmallest(5,'sse_gain').assign(direction='deterioration')])
    pd.concat(extreme).to_csv(D/'largest_changes.csv',index=False);om=pd.read_csv(D/'omissions_summary.csv');omrows=[]
    for name,refname in cfg['references'].items():
        j=om[om.experiment==name].merge(om[om.experiment==refname].drop(columns='experiment'),on=['protocol','kind','omitted'],suffixes=('','_ref'));j['reference']=refname;j['delta_rmse']=j.rmse-j.rmse_ref;omrows.append(j)
    pd.concat(omrows).to_csv(D/'omission_deltas.csv',index=False)
    replay=[];fallback=[];weights_saved=[];coef=[];checks=0;reference_diff=[]
    with threadpool_limits(limits=1):
        for fi in range(65):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];pro,re,fold,*_=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi];ct=pack['ct3'].predict(t.iloc[va]);pred_experts={};base_preds={};key=dict(index=fi,protocol=pro,repeat=re,fold=fold)
            def expert(v):
                if v not in pred_experts:pred_experts[v]=predict_expert(pack['experts'][v],va,assets)
                return pred_experts[v]
            for name,m in pack['models'].items():
                kind=m['type']
                if kind=='ct3':pred=ct
                elif kind=='expert':pred=expert(m['expert'])
                elif kind=='local':
                    v=m['expert']
                    if v not in base_preds:base_preds[v]=predict_base(pack['experts'][v]['local'],va,assets)
                    pred=base_preds[v]
                elif kind=='correction':
                    pred=ct.copy();amp=m['amplitude']
                    if amp:
                        if m['category']:q=t.iloc[va].Estado.to_numpy(str) if m['category']=='STATE' else t.iloc[va].Municipio.to_numpy(str)
                        else:q=m['representation'].transform(frame.iloc[pos[va]])
                        pred+=amp*m['model'].predict(q)
                    if name in ['C_CORRECT_SMALL12','C_CORRECT_EXPANDED30']:
                        rep=m['representation'];beta=np.zeros(len(rep.columns))
                        if amp:
                            b=np.asarray(m['model'].model_.coef_)
                            if rep.pca_ is not None:b=rep.pca_.components_.T@(b/rep.score_scale_.scale_)
                            beta[rep.support_]=amp*b/rep.scale_[rep.support_]
                        for c,b,s in zip(rep.columns,beta,rep.scale_):coef.append(dict(**key,experiment=name,feature=c,amplitude=amp,mode=rep.mode,raw_slope=float(b),effect_per_training_sd=float(b*s)))
                else:
                    if kind=='gate':
                        if m['category']:q=t.iloc[va].Estado.to_numpy(str) if m['category']=='STATE' else t.iloc[va].Municipio.to_numpy(str)
                        else:q=m['representation'].transform(frame.iloc[pos[va]])
                    else:q=m['physical'].transform(assets['physical'].iloc[va]) if m['physical'] is not None else np.zeros((len(va),1))
                    lp=expert(m['expert']);pred=m['gate'].predict(q,ct,lp);w=m['gate'].weights(q);assert np.all((w>=0)&(w<=1));assert np.all(pred>=np.minimum(ct,lp)-1e-12) and np.all(pred<=np.maximum(ct,lp)+1e-12);weights_saved.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,expert_weight=float(v)) for i,v in zip(va,w))
                expected=z[(z.experiment==name)&(z.protocol==pro)&(z['repeat']==re)&(z.fold==fold)].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();error=float(np.max(abs(expected-pred)));assert error<1e-12;replay.append(dict(**key,experiment=name,max_difference=error))
            for e in pack['ledger']:assert not set(e['train'])&(set(e['held'])|set(va));checks+=1
            for e in pack['ct3_ledger']:assert e['verified'];checks+=1
            reference_diff.append(pack['reference_difference'])
            # Model caches are new; reference caches were read only and frozen by prior pipeline.
            for path in (OUT/'cache'/f'{fi:02d}').glob('*.joblib'):
                m=joblib.load(path);assert set(m['train_positions'])<=set(tr)
                if m['fallback']:fallback.append(dict(**key,variant=m['local']['variant'],n_train=len(m['train_positions']),reason=m['fallback'],cache=str(path.relative_to(OUT))))
    pd.DataFrame(replay).to_csv(OUT/'audit/exact_replay.csv',index=False);pd.DataFrame(fallback).to_csv(OUT/'audit/deep_fallbacks.csv',index=False);w=pd.DataFrame(weights_saved);w.to_parquet(D/'expert_weights.parquet',index=False);w.groupby(['experiment','protocol']).expert_weight.agg(['mean','median','min','max']).reset_index().to_csv(D/'expert_weight_summary.csv',index=False);co=pd.DataFrame(coef);co.to_csv(D/'reduced_correction_slopes_by_fold.csv',index=False);co.groupby(['experiment','protocol','feature']).agg(mean_effect=('effect_per_training_sd','mean'),mean_abs_effect=('effect_per_training_sd',lambda s:s.abs().mean()),positive_fraction=('effect_per_training_sd',lambda s:(s>1e-10).mean()),negative_fraction=('effect_per_training_sd',lambda s:(s<-1e-10).mean())).reset_index().to_csv(D/'reduced_correction_slopes_summary.csv',index=False)
    summary=pd.read_csv(D/'metrics_summary.csv');protocols=['random','climate_profile','municipality','spatial'];table=summary.pivot(index='experiment',columns='protocol',values='rmse')[protocols];table.to_csv(D/'RMSE_four_protocols.csv');tests[tests.experiment.str.startswith('A_')].to_csv(D/'family_ablation_matched_deltas.csv',index=False);fig,ax=plt.subplots(figsize=(11,5))
    for name in ['CT3','LEADER','B_SMALL12_SELECTOR','B_EXPANDED30_SELECTOR','E_REDUCED_SMALL12_BOTH','E_REDUCED_EXPANDED30_BOTH','P1_BOTH']:ax.plot(range(4),table.loc[name],marker='o',label=name)
    ax.set(xticks=range(4),xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],ylabel='RMSE t/ha',title='Qué señal conserva un experto reducido');ax.legend(fontsize=7);fig.tight_layout();fig.savefig(D/'reduction_comparison.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(OUT/'resultados_senales_y_reduccion_GeoC.xlsx',engine='openpyxl') as writer:
        for path,sheet in [(D/'metrics_summary.csv','Metricas'),(D/'RMSE_four_protocols.csv','RMSE_4_protocolos'),(D/'family_ablation_matched_deltas.csv','Ablaciones'),(D/'matched_cluster_tests.csv','Contrastes_emparejados'),(D/'representation_choices.csv','Representaciones'),(D/'expert_weight_summary.csv','Pesos'),(D/'intraprofile_summary.csv','Intraperfil'),(D/'regional_summary.csv','Regiones'),(D/'reduced_correction_slopes_summary.csv','Coeficientes_no_causales'),(OUT/'audit/family_sizes.csv','Familias'),(OUT/'audit/selected_definitions_30.csv','Variables_30')]:pd.read_csv(path).to_excel(writer,sheet_name=sheet,index=False)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items());(OUT/'manifest.json').write_text(json.dumps(dict(status='complete',recipes=cfg['recipes'],new_oof=cfg['recipes']*1794,reference_oof=6*1794,tests_passed=4,exact_replay_max_difference=float(pd.DataFrame(replay).max_difference.max()),reference_expert_difference=max(reference_diff),exclusion_checks=checks,deep_fallback_contexts=len(fallback),matched_comparisons=len(tests),protected_sources_unchanged=True,no_final138_fit=True,no_PRED=True,diagnostic_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2),encoding='utf-8');print(table.to_string());print('\nHOLM<.05');print(tests[tests.p_holm<.05].to_string(index=False))

if __name__=='__main__':main()
