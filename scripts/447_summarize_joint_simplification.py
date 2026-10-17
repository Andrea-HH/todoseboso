"""Joint reductions: paired RMSE/R2 tables, interactions, regional audits and replay."""
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
from src.signal_role_allocation import predict_role
from src.calendar_expansion import metric
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
spec=importlib.util.spec_from_file_location('runner446',ROOT/'scripts/446_run_joint_simplification.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner);OUT=runner.OUT;D=OUT/'diagnostics'
PROTOCOLS=['random','climate_profile','municipality','spatial']


def main():
    assert (OUT/'execution_complete.json').exists()
    if (OUT/'manifest.json').exists():raise FileExistsError('Preserve completed joint synthesis')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assets=runner.load_assets();t=assets['a']['train'];ids=t.ID_POLIGONO.tolist();y=assets['y'];frame=assets['role_frame'];p=pd.read_parquet(OUT/'tables/predictions.parquet');assert len(p)==11*1794 and not p.duplicated(['experiment','protocol','repeat','fold','ID_POLIGONO']).any();z=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');metrics=[];regions=[];omits=[];pairs=[];agreement=[]
    for (name,pro,re),g in z.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;key=dict(experiment=name,protocol=pro,repeat=re);m=metric(g.y_true,g.y_pred);e=g.y_pred-g.y_true;metrics.append(dict(**key,**m,mse=float(np.mean(e**2)),error_variance=float(np.var(e)),bias_squared=m['bias']**2));pairs.append(dict(**key,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for label,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(label),n=len(h),**metric(h.y_true,h.y_pred)));rest=g[g[kind]!=label]
                if len(rest)>1:omits.append(dict(**key,kind=kind,omitted=str(label),n=len(rest),**metric(rest.y_true,rest.y_pred)))
    for name,rows,keys in [('metrics',metrics,['experiment','protocol']),('intraprofile',pairs,['experiment','protocol']),('regional',regions,['experiment','protocol','kind','zone']),('omissions',omits,['experiment','protocol','kind','omitted'])]:
        table=pd.DataFrame(rows);table.to_csv(D/f'{name}_by_repeat.csv',index=False);table.drop(columns='repeat').groupby(keys).mean(numeric_only=True).reset_index().to_csv(D/f'{name}_summary.csv',index=False)
    selection=pd.read_parquet(OUT/'tables/selection.parquet');selection.to_csv(D/'selection_by_fold.csv',index=False);selection.groupby(['experiment','protocol','gate_k','expert_amplitude']).size().rename('folds').reset_index().to_csv(D/'hyperparameter_choices.csv',index=False);groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids];tests=[];gains=[]
    with threadpool_limits(limits=1):
        for pro,g in z.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();weights,_=cluster_weights(group,5000,2026)
            for name,refname in cfg['references'].items():
                ref=g[g.experiment==refname][['repeat','fold','ID_POLIGONO','y_pred']];j=g[g.experiment==name].merge(ref,on=['repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');e=j.y_pred-j.y_true;f=j.y_pred_ref-j.y_true;j['reference']=refname;j['sse_gain']=f**2-e**2;j['absolute_error_gain']=abs(f)-abs(e);gains.append(j)
                aa=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy();bb=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred_ref').reindex(columns=ids).to_numpy();delta=sampled_metrics(y,aa,weights)['rmse']-sampled_metrics(y,bb,weights)['rmse'];point=sampled_metrics(y,aa,np.ones((1,138)))['rmse'][0]-sampled_metrics(y,bb,np.ones((1,138)))['rmse'][0];loss=j.assign(loss=e**2-f**2).groupby('ID_POLIGONO').loss.sum().reindex(ids).to_numpy();tests.append(dict(experiment=name,reference=refname,protocol=pro,delta_rmse=float(point),low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
            base=g[g.experiment=='BASE12_BOTH'].set_index(['repeat','fold','ID_POLIGONO']).y_pred
            for (name,re),h in g.groupby(['experiment','repeat']):
                b=base.loc[list(zip(h['repeat'],h.fold,h.ID_POLIGONO))].to_numpy();a=h.y_pred.to_numpy();d=a-b;agreement.append(dict(experiment=name,protocol=pro,repeat=re,correlation=float(np.corrcoef(a,b)[0,1]),rms_difference=float(np.sqrt(np.mean(d**2))),mean_absolute_difference=float(np.mean(abs(d))),max_absolute_difference=float(np.max(abs(d)))))
    tests=pd.DataFrame(tests);assert len(tests)==16;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'matched_cluster_tests.csv',index=False);gains=pd.concat(gains);gains.to_parquet(D/'parcel_gains.parquet',index=False);avg=gains.groupby(['experiment','reference','protocol','ID_POLIGONO','Estado','Municipio'])[['sse_gain','absolute_error_gain']].mean().reset_index();avg.to_csv(D/'parcel_gains_mean_repeat.csv',index=False);pd.concat([s.assign(direction=direction) for _,h in avg.groupby(['experiment','reference','protocol']) for s,direction in [(h.nlargest(5,'sse_gain'),'improvement'),(h.nsmallest(5,'sse_gain'),'deterioration')]]).to_csv(D/'largest_changes.csv',index=False);pd.DataFrame(agreement).drop(columns='repeat').groupby(['experiment','protocol']).mean(numeric_only=True).reset_index().to_csv(D/'prediction_agreement_vs_base.csv',index=False)
    summary=pd.read_csv(D/'metrics_summary.csv');base=summary[summary.experiment=='BASE12_BOTH'].drop(columns='experiment');j=summary.merge(base,on='protocol',suffixes=('','_base'));j['delta_rmse']=j.rmse-j.rmse_base;j['delta_r2']=j.r2-j.r2_base;j.to_csv(D/'loss_vs_full12_base.csv',index=False);om=pd.read_csv(D/'omissions_summary.csv');omrows=[]
    for name,refname in cfg['references'].items():
        for ref in [refname,'BASE12_BOTH']:
            j=om[om.experiment==name].merge(om[om.experiment==ref].drop(columns='experiment'),on=['protocol','kind','omitted'],suffixes=('','_ref'));j['reference']=ref;j['delta_rmse']=j.rmse-j.rmse_ref;omrows.append(j)
    pd.concat(omrows).to_csv(D/'omission_deltas.csv',index=False);interaction=[];m=pd.DataFrame(metrics)
    for (pro,re),g in m.groupby(['protocol','repeat']):
        q=g.set_index('experiment').mse
        for label,combined,first,second in [('WATER_x_SOIL','J7_BOTH','DROP_HISTORY_WATER','DROP_SOIL'),('SOIL_x_GATE','J9_SHARES','DROP_SOIL','GATE_ONLY_SHARES'),('WATER_x_GATE','J10_SHARES','DROP_HISTORY_WATER','GATE_ONLY_SHARES')]:interaction.append(dict(protocol=pro,repeat=re,combination=label,interaction_mse=float(q[combined]-q[first]-q[second]+q['BASE12_BOTH'])))
    pd.DataFrame(interaction).to_csv(D/'nonadditivity_by_repeat.csv',index=False);pd.DataFrame(interaction).drop(columns='repeat').groupby(['protocol','combination']).mean().reset_index().to_csv(D/'nonadditivity_summary.csv',index=False)
    replay=[];fallback=[];weights_saved=[];checks=0;execution=[];reuse_diffs=[]
    with threadpool_limits(limits=1):
        for fi in range(65):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];checkpoint=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');first=checkpoint['predictions'][0];key={k:first[k] for k in ['protocol','repeat','fold']};ct=pack['ct3'].predict(t.iloc[va]);ep={};execution.append(dict(index=fi,**key,seconds=checkpoint['seconds'],warnings=len(checkpoint['warnings'])));reuse_diffs.extend(pack['reference_difference'].values());assert max(pack['reference_difference'].values())<1e-12
            candidates=checkpoint['candidates']
            for name,model in pack['models'].items():
                eligible=[c for c in candidates if c['recipe']==name];best=min(eligible,key=lambda c:(round(c['rmse'],12),c['k']));assert model['gate'].param==best['k'];v=model['variant']
                if v not in ep:ep[v]=predict_role(pack['experts'][v],va,assets)
                q=model['space'].transform(frame.iloc[va]);w=model['gate'].weights(q);assert np.all((w>=0)&(w<=1));pred=model['gate'].predict(q,ct,ep[v]);assert np.all(pred>=np.minimum(ct,ep[v])-1e-12) and np.all(pred<=np.maximum(ct,ep[v])+1e-12);expected=z[(z.experiment==name)&(z.protocol==key['protocol'])&(z['repeat']==key['repeat'])&(z.fold==key['fold'])].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();err=float(np.max(abs(pred-expected)));assert err<1e-12;replay.append(dict(index=fi,**key,experiment=name,max_difference=err));weights_saved.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,expert_weight=float(a)) for i,a in zip(va,w))
            for row in pack['ledger']:assert not set(row['train'])&(set(row['held'])|set(va));checks+=1
            for row in pack['ct3_ledger']:assert row['verified'];checks+=1
            for path in (OUT/'cache'/f'{fi:02d}').glob('*.joblib'):
                a=joblib.load(path);assert set(a['train_positions'])<=set(tr)
                if a['fallback']:fallback.append(dict(index=fi,**key,variant=a['local']['variant'],n_train=len(a['train_positions']),reason=a['fallback']))
            if fi%10==9:print(f'Joint replay audit {fi+1}/65',flush=True)
    assert len(replay)==260;pd.DataFrame(replay).to_csv(OUT/'audit/exact_replay.csv',index=False);pd.DataFrame(fallback).to_csv(OUT/'audit/deep_fallbacks.csv',index=False);pd.DataFrame(execution).to_csv(D/'execution_by_fold.csv',index=False);w=pd.DataFrame(weights_saved);w.to_parquet(D/'expert_weights.parquet',index=False);w.groupby(['experiment','protocol']).expert_weight.agg(['mean','median','min','max']).reset_index().to_csv(D/'expert_weight_summary.csv',index=False)
    old=pd.read_parquet(runner.PREV/'tables/predictions.parquet');reference_checks={};keys=['protocol','repeat','fold','ID_POLIGONO']
    for name in runner.ARCHIVES:
        a=p[p.experiment==name].merge(old[old.experiment==name],on=keys,suffixes=('','_ref'),validate='one_to_one');assert len(a)==1794 and np.array_equal(a.y_true,a.y_true_ref);reference_checks[name]=float(abs(a.y_pred-a.y_pred_ref).max());assert reference_checks[name]<1e-12
    inventory=[]
    for name,r in cfg['recipes'].items():
        roles=[('core4',list(assets['core'].columns)),('local_expert',cfg['variants'][r['variant']]['columns']),('coordinates',['base_centroid_lat','base_centroid_lon'])]+[('physical_gate',assets['physical_definitions'][atom]['columns']) for atom in r['gate_atoms']];unique=set()
        for role,cols in roles:
            unique.update(cols);inventory.extend(dict(experiment=name,role=role,feature=c) for c in cols)
        assert len(unique)==r['input_count']
    pd.DataFrame(inventory).to_csv(D/'input_inventory.csv',index=False);counts={'CT3':4,'BASE12_BOTH':33,'DROP_HISTORY_WATER':31,'DROP_SOIL':30,'GATE_ONLY_SHARES':28,'MEAN_BOTH':21,'PRIOR_BIGBOTH':1850,**{n:r['input_count'] for n,r in cfg['recipes'].items()}};table=pd.DataFrame(index=summary.experiment.unique());table['input_fields']=table.index.map(counts)
    for pro in PROTOCOLS:
        q=summary[summary.protocol==pro].set_index('experiment');table[pro+'_RMSE']=q.rmse;table[pro+'_R2']=q.r2
    table.to_csv(D/'RMSE_R2_four_protocols.csv');presentation=pd.DataFrame(index=table.index);presentation['fields']=table.input_fields
    for pro in PROTOCOLS:presentation[pro]=[f'{r:.4f} / {s:.4f}' for r,s in zip(table[pro+'_RMSE'],table[pro+'_R2'])]
    presentation.to_csv(D/'presentation_RMSE_R2.csv');fig,axes=plt.subplots(1,2,figsize=(12,4))
    for metric_name,ax in zip(['RMSE','R2'],axes):
        for name in ['CT3','BASE12_BOTH','J7_BOTH','J9_SHARES','J10_SHARES','J7_SHARES']:ax.plot(range(4),[table.loc[name,pro+'_'+metric_name] for pro in PROTOCOLS],marker='o',label=name)
        ax.set(xticks=range(4),xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],ylabel=metric_name+(' t/ha' if metric_name=='RMSE' else ''));ax.legend(fontsize=7)
    fig.tight_layout();fig.savefig(D/'joint_RMSE_R2.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(OUT/'resultados_simplificacion_conjunta.xlsx',engine='openpyxl') as writer:
        for f,sheet in [('presentation_RMSE_R2.csv','Resumen_RMSE_R2'),('RMSE_R2_four_protocols.csv','RMSE_R2_numericos'),('metrics_summary.csv','Metricas'),('loss_vs_full12_base.csv','Perdidas_vs_base'),('matched_cluster_tests.csv','Contrastes'),('nonadditivity_summary.csv','No_aditividad_MSE'),('input_inventory.csv','Variables_y_roles'),('hyperparameter_choices.csv','Elecciones_internas'),('expert_weight_summary.csv','Pesos'),('intraprofile_summary.csv','Intraperfil'),('regional_summary.csv','Regiones'),('omission_deltas.csv','Omisiones'),('prediction_agreement_vs_base.csv','Concordancia')]:pd.read_csv(D/f).to_excel(writer,sheet_name=sheet,index=False)
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'manifest.json').write_text(json.dumps(dict(status='complete',new_recipes=4,new_oof=7176,reference_oof=12558,tests_passed=5,exact_replay_max_difference=float(pd.DataFrame(replay).max_difference.max()),reused_expert_max_difference=max(reuse_diffs),reference_checks=reference_checks,gate_decisions_verified=260,exclusion_checks=checks,deep_fallback_uses=len(fallback),matched_comparisons=16,protected_sources_unchanged=True,no_final138_fit=True,no_PRED=True,analysis_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2),encoding='utf-8');print(presentation.to_string());print('Holm significant:',int((tests.p_holm<.05).sum()))


if __name__=='__main__':main()
