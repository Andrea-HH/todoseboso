"""Paired role recovery, compactness, regional diagnostics and exact replay."""
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
spec=importlib.util.spec_from_file_location('runner442',ROOT/'scripts/442_run_signal_role_allocation.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner);OUT=runner.OUT;D=OUT/'diagnostics'


def main():
    assert (OUT/'execution_complete.json').exists()
    if (OUT/'manifest.json').exists():raise FileExistsError('Preserve completed role analysis')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assets=runner.load_assets();t=assets['a']['train'];ids=t.ID_POLIGONO.tolist();y=assets['y'];frame=assets['role_frame'];p=pd.read_parquet(OUT/'tables/predictions.parquet');assert len(p)==34*1794 and not p.duplicated(['experiment','protocol','repeat','fold','ID_POLIGONO']).any();z=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');metrics=[];regions=[];omits=[];pairs=[];agreement=[]
    for (name,pro,re),g in z.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;key=dict(experiment=name,protocol=pro,repeat=re);m=metric(g.y_true,g.y_pred);e=g.y_pred-g.y_true;metrics.append(dict(**key,**m,error_variance=float(np.var(e)),bias_squared=m['bias']**2));pairs.append(dict(**key,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for label,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(label),n=len(h),**metric(h.y_true,h.y_pred)));rest=g[g[kind]!=label]
                if len(rest)>1:omits.append(dict(**key,kind=kind,omitted=str(label),n=len(rest),**metric(rest.y_true,rest.y_pred)))
    for name,rows,keys in [('metrics',metrics,['experiment','protocol']),('intraprofile',pairs,['experiment','protocol']),('regional',regions,['experiment','protocol','kind','zone']),('omissions',omits,['experiment','protocol','kind','omitted'])]:
        table=pd.DataFrame(rows);table.to_csv(D/f'{name}_by_repeat.csv',index=False);table.drop(columns='repeat').groupby(keys).mean(numeric_only=True).reset_index().to_csv(D/f'{name}_summary.csv',index=False)
    selection=pd.read_parquet(OUT/'tables/selection.parquet');selection.to_csv(D/'selection_by_fold.csv',index=False);selection[selection.experiment.str.startswith('SELECT_')].groupby(['experiment','protocol','selected_recipe','input_count']).size().rename('folds').reset_index().to_csv(D/'selector_choices.csv',index=False);selection.groupby(['experiment','protocol']).input_count.agg(['mean','median','min','max']).reset_index().to_csv(D/'input_count_summary.csv',index=False)
    tests=[];gains=[];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids]
    with threadpool_limits(limits=1):
        for pro,g in z.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();weights,_=cluster_weights(group,5000,2026)
            for name,refname in cfg['references'].items():
                ref=g[g.experiment==refname][['repeat','fold','ID_POLIGONO','y_pred']];j=g[g.experiment==name].merge(ref,on=['repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');e=j.y_pred-j.y_true;f=j.y_pred_ref-j.y_true;j['reference']=refname;j['sse_gain']=f**2-e**2;j['absolute_error_gain']=abs(f)-abs(e);gains.append(j)
                aa=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy();bb=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred_ref').reindex(columns=ids).to_numpy();delta=sampled_metrics(y,aa,weights)['rmse']-sampled_metrics(y,bb,weights)['rmse'];point=sampled_metrics(y,aa,np.ones((1,138)))['rmse'][0]-sampled_metrics(y,bb,np.ones((1,138)))['rmse'][0];loss=j.assign(loss=e**2-f**2).groupby('ID_POLIGONO').loss.sum().reindex(ids).to_numpy();tests.append(dict(experiment=name,reference=refname,protocol=pro,delta_rmse=float(point),low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
            base=g[g.experiment=='BASE12_BOTH'].set_index(['repeat','fold','ID_POLIGONO']).y_pred
            for (name,re),h in g.groupby(['experiment','repeat']):
                b=base.loc[list(zip(h['repeat'],h.fold,h.ID_POLIGONO))].to_numpy();a=h.y_pred.to_numpy();delta=a-b;agreement.append(dict(experiment=name,protocol=pro,repeat=re,correlation=float(np.corrcoef(a,b)[0,1]),rms_difference=float(np.sqrt(np.mean(delta**2))),mean_absolute_difference=float(np.mean(abs(delta))),max_absolute_difference=float(np.max(abs(delta)))))
    tests=pd.DataFrame(tests);assert len(tests)==120;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'matched_cluster_tests.csv',index=False);gains=pd.concat(gains);gains.to_parquet(D/'parcel_gains.parquet',index=False);avg=gains.groupby(['experiment','reference','protocol','ID_POLIGONO','Estado','Municipio'])[['sse_gain','absolute_error_gain']].mean().reset_index();avg.to_csv(D/'parcel_gains_mean_repeat.csv',index=False);pd.concat([sub.assign(direction=direction) for _,h in avg.groupby(['experiment','reference','protocol']) for sub,direction in [(h.nlargest(5,'sse_gain'),'improvement'),(h.nsmallest(5,'sse_gain'),'deterioration')]]).to_csv(D/'largest_changes.csv',index=False)
    pd.DataFrame(agreement).drop(columns='repeat').groupby(['experiment','protocol']).mean(numeric_only=True).reset_index().to_csv(D/'prediction_agreement_vs_base.csv',index=False);summary=pd.read_csv(D/'metrics_summary.csv');base=summary[summary.experiment=='BASE12_BOTH'].drop(columns='experiment');j=summary.merge(base,on='protocol',suffixes=('','_base'));j['delta_rmse']=j.rmse-j.rmse_base;j['delta_mae']=j.mae-j.mae_base;j.to_csv(D/'loss_vs_full12_base.csv',index=False)
    om=pd.read_csv(D/'omissions_summary.csv');rows=[]
    for name,refname in cfg['references'].items():
        j=om[om.experiment==name].merge(om[om.experiment==refname].drop(columns='experiment'),on=['protocol','kind','omitted'],suffixes=('','_ref'));j['reference']=refname;j['delta_rmse']=j.rmse-j.rmse_ref;rows.append(j)
    pd.concat(rows).to_csv(D/'omission_deltas.csv',index=False);recovery=[]
    for group in cfg['groups']:
        for pro in summary.protocol.unique():
            q=summary[summary.protocol==pro].set_index('experiment');b=q.loc['BASE12_BOTH','rmse'];drop=q.loc['DROP_'+group,'rmse']
            recovery.append(dict(group=group,protocol=pro,base_rmse=b,drop_rmse=drop,drop_loss=drop-b,corrector_rmse=q.loc['MOVE_CORRECT_'+group,'rmse'],corrector_change_vs_drop=q.loc['MOVE_CORRECT_'+group,'rmse']-drop,corrector_loss_vs_base=q.loc['MOVE_CORRECT_'+group,'rmse']-b,gate_rmse=q.loc['MOVE_GATE_'+group,'rmse'],gate_change_vs_drop=q.loc['MOVE_GATE_'+group,'rmse']-drop,gate_loss_vs_base=q.loc['MOVE_GATE_'+group,'rmse']-b))
    pd.DataFrame(recovery).to_csv(D/'role_recovery.csv',index=False);inventory=[]
    for name,r in cfg['recipes'].items():
        v=cfg['variants'][r['variant']];parts=[('local_expert',v['columns']),('compact_core',list(assets['core'].columns)),('correction_extra',v['correction_columns']),('gate_extra',r['gate_columns']),('coordinates',['base_centroid_lat','base_centroid_lon'])]
        parts += [('gate_physical',assets['physical_definitions'][a]['columns']) for a in r['gate_atoms']];parts += [('correction_physical',assets['physical_definitions'][a]['columns']) for a in v['correction_atoms']]
        unique=set()
        for role,cols in parts:
            for c in cols:inventory.append(dict(experiment=name,role=role,feature=c));unique.update(cols)
        assert len(unique)==r['input_count']
    pd.DataFrame(inventory).to_csv(D/'role_input_inventory.csv',index=False);replay=[];checks=0;fallback=[];weights=[];execution=[]
    with threadpool_limits(limits=1):
        for fi in range(65):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];checkpoint=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');first=checkpoint['predictions'][0];key={k:first[k] for k in ['protocol','repeat','fold']};ct=pack['ct3'].predict(t.iloc[va]);ep={};execution.append(dict(index=fi,**key,seconds=checkpoint['seconds'],warnings=len(checkpoint['warnings'])));assert pack['reference_difference']<1e-12
            for name,m in pack['models'].items():
                if name=='CT3':pred=ct
                else:
                    v=m['variant']
                    if v not in ep:ep[v]=predict_role(pack['experts'][v],va,assets)
                    q=m['space'].transform(frame.iloc[va]);w=m['gate'].weights(q);assert np.all((w>=0)&(w<=1));pred=m['gate'].predict(q,ct,ep[v]);assert np.all(pred>=np.minimum(ct,ep[v])-1e-12) and np.all(pred<=np.maximum(ct,ep[v])+1e-12);weights.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,expert_weight=float(a)) for i,a in zip(va,w))
                expected=z[(z.experiment==name)&(z.protocol==key['protocol'])&(z['repeat']==key['repeat'])&(z.fold==key['fold'])].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();err=float(np.max(abs(pred-expected)));assert err<1e-12;replay.append(dict(index=fi,**key,experiment=name,max_difference=err))
            for row in pack['ledger']:assert not set(row['train'])&(set(row['held'])|set(va));checks+=1
            for row in pack['ct3_ledger']:assert row['verified'];checks+=1
            for f in (OUT/'cache'/f'{fi:02d}').glob('*.joblib'):
                m=joblib.load(f);assert set(m['train_positions'])<=set(tr)
                if m['fallback']:fallback.append(dict(index=fi,**key,variant=m['local']['variant'],n_train=len(m['train_positions']),reason=m['fallback']))
            if fi%10==9:print(f'Replay and exclusion audit {fi+1}/65',flush=True)
    assert len(replay)==2015;pd.DataFrame(replay).to_csv(OUT/'audit/exact_replay.csv',index=False);pd.DataFrame(fallback).to_csv(OUT/'audit/deep_fallbacks.csv',index=False);pd.DataFrame(execution).to_csv(D/'execution_by_fold.csv',index=False);w=pd.DataFrame(weights);w.to_parquet(D/'expert_weights.parquet',index=False);w.groupby(['experiment','protocol']).expert_weight.agg(['mean','median','min','max']).reset_index().to_csv(D/'expert_weight_summary.csv',index=False)
    protocols=['random','climate_profile','municipality','spatial'];table=summary.pivot(index='experiment',columns='protocol',values='rmse')[protocols];table.to_csv(D/'RMSE_four_protocols.csv');fig,ax=plt.subplots(figsize=(10,5))
    for name in ['CT3','PRIOR_SMALL12','BASE12_BOTH','MEAN_GLOBAL','SELECT_MIN_RMSE','SELECT_COMPACT_001']:ax.plot(range(4),table.loc[name],marker='o',label=name)
    ax.set(xticks=range(4),xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],ylabel='RMSE t/ha',title='Retirada y reasignación de señales');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(D/'role_comparison.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(OUT/'resultados_composicion_y_roles.xlsx',engine='openpyxl') as writer:
        for f,sheet in [('RMSE_four_protocols.csv','RMSE'),('metrics_summary.csv','Metricas'),('role_recovery.csv','Recuperacion_por_rol'),('loss_vs_full12_base.csv','Perdida_vs_base'),('matched_cluster_tests.csv','Contrastes'),('selector_choices.csv','Seleccion_interna'),('input_count_summary.csv','Cantidad_entradas'),('role_input_inventory.csv','Variables_y_roles'),('expert_weight_summary.csv','Pesos'),('intraprofile_summary.csv','Intraperfil'),('regional_summary.csv','Regiones'),('omission_deltas.csv','Omisiones'),('prediction_agreement_vs_base.csv','Concordancia'),('execution_by_fold.csv','Tiempo')]:pd.read_csv(D/f).to_excel(writer,sheet_name=sheet,index=False)
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'manifest.json').write_text(json.dumps(dict(status='complete',new_recipes=30,new_oof=30*1794,reference_oof=4*1794,tests_passed=3,exact_replay_max_difference=float(pd.DataFrame(replay).max_difference.max()),exclusion_checks=checks,deep_fallback_uses=len(fallback),matched_comparisons=120,protected_sources_unchanged=True,no_final138_fit=True,no_PRED=True,analysis_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2),encoding='utf-8');print(table.round(6).to_string());print('Holm significant:',int((tests.p_holm<.05).sum()))


if __name__=='__main__':main()
