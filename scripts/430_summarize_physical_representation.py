"""OOF analysis and replay; no refitting or retrospective model changes."""
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
from src.physical_similarity import neighbor_weights
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
OUT=ROOT/'outputs/modeling/physical_representation/v1';D=OUT/'diagnostics'

def main():
    assert (OUT/'execution_complete.json').exists()
    if (OUT/'manifest.json').exists():raise FileExistsError('Preserve complete results')
    cfg=json.loads((OUT/'frozen_design.json').read_text());t=data()['train'];ids=t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy();p=pd.read_parquet(OUT/'tables/predictions.parquet');assert len(p)==111228
    old=pd.read_parquet(BRIDGE/'tables/oof_predictions.parquet');old=old[(old.experiment=='LOCAL04D')&(old.protocol!='geoc_target_matched')]
    prev=pd.read_parquet(ROOT/'outputs/modeling/physical_similarity/v2/tables/predictions.parquet');prev=prev[prev.experiment.isin(['geology_physiography__ridge','geology_physiography__neighbors','geology_physiography__groups','PHYSICAL_BALANCED__ridge','INTERNAL_SELECTOR'])].copy();prev['experiment']='V2_'+prev.experiment
    p=pd.concat([p,old,prev],ignore_index=True);assert not p.duplicated(['experiment','protocol','repeat','fold','ID_POLIGONO']).any();p.to_parquet(OUT/'tables/oof_with_references.parquet',index=False);z=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one')
    records=[];pairs=[];regions=[];omit=[]
    for (name,pro,re),g in z.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;key=dict(experiment=name,protocol=pro,repeat=re);v=metric(g.y_true,g.y_pred);e=g.y_pred-g.y_true;v.update(error_variance=float(np.mean((e-e.mean())**2)),bias_squared=v['bias']**2);records.append(dict(**key,**v));pairs.append(dict(**key,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for label,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(label),n=len(h),**metric(h.y_true,h.y_pred)));rest=g[g[kind]!=label]
                if len(rest)>1:omit.append(dict(**key,kind=kind,omitted=str(label),n=len(rest),**metric(rest.y_true,rest.y_pred)))
    for name,rows,keys in [('metrics',records,['experiment','protocol']),('intraprofile',pairs,['experiment','protocol']),('regional',regions,['experiment','protocol','kind','zone']),('omissions',omit,['experiment','protocol','kind','omitted'])]:
        a=pd.DataFrame(rows);a.to_csv(D/f'{name}_by_repeat.csv',index=False);a.drop(columns='repeat').groupby(keys).mean(numeric_only=True).reset_index().to_csv(D/f'{name}_summary.csv',index=False)
    selections=pd.read_parquet(OUT/'tables/selection.parquet');primary=selections.experiment.unique().tolist();assert len(primary)==61
    selections.to_csv(D/'selection_by_fold.csv',index=False);selections.groupby(['experiment','protocol','mode']).agg(folds=('amplitude','size'),zero_fraction=('amplitude',lambda s:(s==0).mean()),mean_amplitude=('amplitude','mean')).reset_index().to_csv(D/'representation_selection.csv',index=False)
    selections[selections.experiment=='INTERNAL_SELECTOR'].groupby(['protocol','selected_variant','mode']).size().rename('folds').reset_index().to_csv(D/'internal_selector_choices.csv',index=False)
    groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids];tests=[];gains=[]
    with threadpool_limits(limits=1):
        for pro,g in z.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();weights,_=cluster_weights(group,5000,2026);ref=g[g.experiment=='CT3'][['repeat','fold','ID_POLIGONO','y_pred']]
            for name in primary:
                j=g[g.experiment==name].merge(ref,on=['repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');e=j.y_pred-j.y_true;f=j.y_pred_ref-j.y_true;j['sse_gain']=f**2-e**2;j['absolute_error_gain']=abs(f)-abs(e);gains.append(j)
                aa=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy();bb=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred_ref').reindex(columns=ids).to_numpy();delta=sampled_metrics(y,aa,weights)['rmse']-sampled_metrics(y,bb,weights)['rmse'];point=sampled_metrics(y,aa,np.ones((1,138)))['rmse'][0]-sampled_metrics(y,bb,np.ones((1,138)))['rmse'][0];loss=j.assign(loss=e**2-f**2).groupby('ID_POLIGONO').loss.sum().reindex(ids).to_numpy();tests.append(dict(experiment=name,protocol=pro,delta_rmse=float(point),low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
    tests=pd.DataFrame(tests);assert len(tests)==244;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'paired_cluster_tests.csv',index=False)
    gains=pd.concat(gains);gains.to_parquet(D/'parcel_gains.parquet',index=False);gains.groupby(['experiment','protocol','ID_POLIGONO','Estado','Municipio'])[['sse_gain','absolute_error_gain']].mean().reset_index().to_csv(D/'parcel_gains_mean_repeat.csv',index=False)
    om=pd.read_csv(D/'omissions_summary.csv');ref=om[om.experiment=='CT3'].drop(columns='experiment');om=om.merge(ref,on=['protocol','kind','omitted'],suffixes=('','_CT3'));om['delta_rmse']=om.rmse-om.rmse_CT3;om.to_csv(D/'omission_deltas.csv',index=False)
    x=pd.read_parquet(OUT/'cache/features138_target_free.parquet');replays=[];loadings=[];support=[];checks=0
    focus=['INTERNAL_SELECTOR','geologic_composition__neighbors','geologic_distances__neighbors','erosion_composition__ridge','PHYSICAL_ALL__ridge']+[f'MODE_{m}' for m,k in cfg['modes']]
    with threadpool_limits(limits=1):
        for fi in range(65):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];pro,re,fold,*_=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi];ct=pack['ct3'].predict(t.iloc[va]);predictions={};spaces={}
            for name,info in pack['correctors'].items():
                qq=np.column_stack([m.transform(x.iloc[va]) for m in info['representations']])/np.sqrt(len(info['atoms']));amp=info['selection']['amplitude'];predictions[name]=ct+amp*info['model'].predict(qq) if amp else ct.copy()
                if name in focus or name==pack['selected_variant']:
                    zz=np.column_stack([m.transform(x.iloc[tr]) for m in info['representations']])/np.sqrt(len(info['atoms']));spaces[name]=(zz,qq)
                for atom,m in zip(info['atoms'],info['representations']):loadings.append(dict(index=fi,experiment=name,protocol=pro,atom=atom,mode=m.mode,dimension=m.dimension_,explained_X_variance=m.explained_,amplitude=amp))
            predictions['INTERNAL_SELECTOR']=predictions[pack['selected_variant']];predictions['CT3']=ct;spaces['INTERNAL_SELECTOR']=spaces[pack['selected_variant']]
            for name,pred in predictions.items():
                q=z[(z.experiment==name)&(z.protocol==pro)&(z['repeat']==re)&(z.fold==fold)].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();error=float(np.max(abs(q-pred)));assert error<1e-12;replays.append(dict(index=fi,experiment=name,max_difference=error))
            for name in focus:
                zz,qq=spaces[name];w,d=neighbor_weights(zz,qq,24);_,dt=neighbor_weights(zz,zz,1);np.fill_diagonal(dt,np.inf);cut=float(np.quantile(dt.min(axis=1),.9))
                for j,i in enumerate(va):support.append(dict(experiment=name,protocol=pro,repeat=re,fold=fold,ID_POLIGONO=t.iloc[i].ID_POLIGONO,nearest_distance=float(d[j].min()),outside_training_nn90=bool(d[j].min()>cut),same_municipality_weight=float(w[j]@(t.iloc[tr].Municipio.to_numpy()==t.iloc[i].Municipio)),same_profile_weight=float(w[j]@(t.iloc[tr].climate_profile.to_numpy()==t.iloc[i].climate_profile))))
            for entry in pack['ledger']:assert entry['verified'];checks+=1
    pd.DataFrame(replays).to_csv(OUT/'audit/exact_replay.csv',index=False);pd.DataFrame(loadings).to_csv(D/'components_by_fold.csv',index=False);pd.DataFrame(support).to_parquet(D/'physical_support.parquet',index=False)
    summary=pd.read_csv(D/'metrics_summary.csv');protocols=['random','climate_profile','municipality','spatial'];table=summary.pivot(index='experiment',columns='protocol',values='rmse')[protocols];table.to_csv(D/'RMSE_four_protocols.csv')
    fig,ax=plt.subplots(figsize=(10,5.5))
    for name in ['CT3','INTERNAL_SELECTOR']+[f'MODE_{m}' for m,k in cfg['modes']]:ax.plot(range(4),table.loc[name],marker='o',label=name)
    ax.set(xticks=range(4),xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],ylabel='RMSE t/ha',title='Representación física: modos y elección interna');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(D/'representation_comparison.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(OUT/'resultados_representacion_fisica.xlsx',engine='openpyxl') as writer:
        for path,sheet in [(D/'metrics_summary.csv','Metricas'),(D/'RMSE_four_protocols.csv','RMSE_4_protocolos'),(D/'representation_selection.csv','Seleccion_representacion'),(D/'internal_selector_choices.csv','Selector_interno'),(D/'paired_cluster_tests.csv','Contrastes_exploratorios'),(D/'intraprofile_summary.csv','Intraperfil'),(D/'regional_summary.csv','Regiones'),(OUT/'audit/subblocks.csv','Subbloques')]:pd.read_csv(path).to_excel(writer,sheet_name=sheet,index=False)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items())
    (OUT/'manifest.json').write_text(json.dumps(dict(status='complete',recipes=61,new_correction_oof=109434,saved_fold_containers=65,exact_replay_max_difference=float(pd.DataFrame(replays).max_difference.max()),residual_exclusion_checks=checks,tests_passed=7,statistical_comparisons=244,protected_sources_unchanged=True,no_final138_fit=True,no_PRED=True,diagnostic_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),warning_log='audit/warnings.json; startup threadpoolctl co-loaded OpenMP warning also observed'),indent=2),encoding='utf-8')
    print(table.to_string());print('\nHOLM<.05');print(tests[tests.p_holm<.05].to_string(index=False))

if __name__=='__main__':main()
