"""OOF evaluation of reductions and paired neighborhood correction architectures."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.indicator_neighborhoods import OUT,PREVIOUS,ENGINEERING,haversine,REDUCTIONS
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
spec=importlib.util.spec_from_file_location('neighbor_audit',ROOT/'scripts/449_j7_both_residual_audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
D=OUT/'tables';PROTOCOLS=['random','climate_profile','municipality','spatial']


def write(name,rows,keys):
    f=pd.DataFrame(rows);f.to_csv(D/(name+'_by_repeat.csv'),index=False);s=f.drop(columns='repeat',errors='ignore').groupby(keys,dropna=False).mean(numeric_only=True).reset_index();s.to_csv(D/(name+'_summary.csv'),index=False);return s


def md(f):
    def cell(v):return f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v).replace('|','/')
    return '\n'.join(['| '+' | '.join(f.columns)+' |','| '+' | '.join(['---']*len(f.columns))+' |']+['| '+' | '.join(map(cell,row))+' |' for row in f.itertuples(index=False,name=None)])


def main():
    if (OUT/'evaluation_complete.json').exists():raise FileExistsError('Preserve neighborhood evaluation')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert (OUT/'execution_complete.json').exists();assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');ids=t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy();x=pd.read_parquet(OUT/'cache/features_train138_target_free.parquet');assert x.ID_POLIGONO.tolist()==ids
    keys=['experiment','protocol','repeat','fold','ID_POLIGONO','y_true','y_pred'];new=pd.read_parquet(D/'predictions.parquet');prior=pd.read_parquet(PREVIOUS/'tables/predictions.parquet');eng=pd.read_parquet(ENGINEERING/'tables/predictions.parquet')
    for name in ['CT3','J7_BOTH']:
        z=new[new.experiment==name].merge(prior[prior.experiment==name],on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');assert len(z)==1794;np.testing.assert_array_equal(z.y_pred,z.y_pred_ref);np.testing.assert_array_equal(z.y_true,z.y_true_ref)
    p=pd.concat([new[keys],prior[prior.experiment.isin(['CT3_INDICATORS_DIRECT','J7_INDICATORS_DIRECT'])][keys],eng[eng.experiment.isin(['CT3_P_RAW','J7_P_RAW'])][keys]],ignore_index=True);assert len(p)==40*1794 and not p.duplicated(['experiment','protocol','repeat','ID_POLIGONO']).any();p=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');p['error']=p.y_pred-p.y_true;p['squared_error']=p.error**2;p['absolute_error']=abs(p.error);p.to_parquet(D/'oof_residuals.parquet',index=False)
    hard=pd.read_csv(ROOT/'outputs/research/difficult_quartile/v1/tables/parcel_groups.csv');hard=hard[hard.hard_quartile].ID_POLIGONO.tolist();top=pd.read_csv(ROOT/'outputs/research/top10_difficult_parcels/v1/tables/top10_J7_random.csv').ID_POLIGONO.tolist();bins=dict(zip(ids,pd.qcut(pd.Series(y),4,duplicates='drop').astype(str)));p['target_quartile']=p.ID_POLIGONO.map(bins)
    metrics=[];regions=[];omits=[];without=[];quartiles=[];pairs=[]
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;key=dict(experiment=name,protocol=pro,repeat=re);m=audit.stats(g);assert np.isclose(m['rmse']**2,m['error_variance']+m['bias_squared']);metrics.append(dict(**key,**m));pairs.append(dict(**key,**pair_metrics(g)))
        for label,exclude in [('171_015',['AGC_171','AGC_015']),('top10',top),('hard35',hard)]:without.append(dict(**key,excluded=label,**audit.stats(g[~g.ID_POLIGONO.isin(exclude)])))
        for kind in ['Estado','Municipio','fold','climate_profile']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(zone),**audit.stats(h)))
                if kind!='climate_profile':omits.append(dict(**key,kind=kind,omitted=str(zone),**audit.stats(g[g[kind]!=zone])))
        for zone,h in g.groupby('target_quartile'):quartiles.append(dict(**key,zone=zone,**audit.stats(h)))
    summary=write('metrics',metrics,['experiment','protocol']);write('regions',regions,['experiment','protocol','kind','zone']);write('omissions',omits,['experiment','protocol','kind','omitted']);write('without_cases',without,['experiment','protocol','excluded']);write('quartiles',quartiles,['experiment','protocol','zone']);write('intraprofile',pairs,['experiment','protocol'])
    comparisons=[]
    for name,r in cfg['recipes'].items():comparisons.append((name,'CT3' if r['base']=='CT3' else 'J7_BOTH','vs_base'))
    for base in ['CT3','J7']:
        for mode in ['KNN','CLUSTER']:
            for geometry in ['GEO','PHYSICAL','SATELLITE']:comparisons.append((f'{base}_{mode}_{geometry}_WEIGHT',f'{base}_{mode}_{geometry}_DIRECT','paired_use'))
        comparisons.append((base+'_GLOBAL_R4',base+'_GLOBAL_R9','reduction'))
        for geometry in ['PHYSICAL','SATELLITE']:comparisons.append((f'{base}_KNN_{geometry}_WEIGHT',f'{base}_KNN_GEO_WEIGHT','weight_geometry'))
    assert len(comparisons)==52;tests=[];gains=[];groups=pd.read_csv(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/groups.csv').set_index('ID_POLIGONO').loc[ids]
    with threadpool_limits(limits=1):
        for pro,g in p.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();w,_=cluster_weights(group,5000,2026);arrays={name:h.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy() for name,h in g.groupby('experiment')};samples={name:sampled_metrics(y,v,w) for name,v in arrays.items()}
            for name,ref,kind in comparisons:
                aa=arrays[name];bb=arrays[ref];delta=samples[name]['rmse']-samples[ref]['rmse'];point=np.sqrt(np.mean((aa-y)**2,axis=1)).mean()-np.sqrt(np.mean((bb-y)**2,axis=1)).mean();loss=np.sum((aa-y)**2-(bb-y)**2,axis=0);tests.append(dict(experiment=name,reference=ref,contrast=kind,protocol=pro,delta_rmse=float(point),low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
                for j,i in enumerate(ids):gains.append(dict(experiment=name,reference=ref,contrast=kind,protocol=pro,ID_POLIGONO=i,sse_gain=float(np.mean((bb[:,j]-y[j])**2-(aa[:,j]-y[j])**2)),absolute_error_gain=float(np.mean(abs(bb[:,j]-y[j])-abs(aa[:,j]-y[j])))))
    tests=pd.DataFrame(tests);assert len(tests)==208;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'paired_tests.csv',index=False);gains=pd.DataFrame(gains);gains.to_csv(D/'parcel_gains.csv',index=False);distribution=[]
    for (name,pro),g in gains[gains.contrast=='vs_base'].groupby(['experiment','protocol']):distribution.append(dict(experiment=name,protocol=pro,total_sse_gain=g.sse_gain.sum(),hard35_sse_gain=g[g.ID_POLIGONO.isin(hard)].sse_gain.sum(),remaining103_sse_gain=g[~g.ID_POLIGONO.isin(hard)].sse_gain.sum(),fraction_improved=float((g.absolute_error_gain>1e-12).mean()),fraction_worsened=float((g.absolute_error_gain < -1e-12).mean())))
    pd.DataFrame(distribution).to_csv(D/'gain_distribution.csv',index=False)
    for label,join in [('regions',['protocol','kind','zone']),('omissions',['protocol','kind','omitted']),('without_cases',['protocol','excluded'])]:
        f=pd.read_csv(D/(label+'_summary.csv'));changes=[]
        for name,r in cfg['recipes'].items():
            ref='CT3' if r['base']=='CT3' else 'J7_BOTH';z=f[f.experiment==name].merge(f[f.experiment==ref],on=join,suffixes=('','_reference'),validate='one_to_one')
            for c in ['rmse','r2','mae','bias']:z['delta_'+c]=z[c]-z[c+'_reference']
            changes.append(z)
        pd.concat(changes,ignore_index=True).to_csv(D/(label+'_paired_changes.csv'),index=False)
    parcel=p.groupby(['experiment','protocol','ID_POLIGONO','Estado','Municipio','climate_profile']).agg(y_true=('y_true','first'),prediction=('y_pred','mean'),mean_error=('error','mean'),mean_absolute_error=('absolute_error','mean'),mean_squared_error=('squared_error','mean')).reset_index();parcel.to_csv(D/'parcel_errors.csv',index=False)
    selection=pd.read_parquet(D/'models_selected.parquet');selection.to_csv(D/'selection_by_fold.csv',index=False);selection.groupby(['experiment','protocol','param','amplitude']).size().rename('folds').reset_index().to_csv(D/'selection_counts.csv',index=False)
    detail=pd.read_parquet(D/'details.parquet');meta=t.set_index('ID_POLIGONO');coords=x.set_index('ID_POLIGONO')[['base_centroid_lat','base_centroid_lon']];neighbor_rows=[]
    for r in detail.itertuples():
        neighbors=list(r.neighbor_ids);geo=haversine(coords.loc[[r.ID_POLIGONO]].to_numpy(),coords.loc[neighbors].to_numpy())[0] if neighbors else np.array([])
        neighbor_rows.append(dict(experiment=r.experiment,protocol=r.protocol,repeat=r.repeat,fold=r.fold,ID_POLIGONO=r.ID_POLIGONO,neighbor_count=r.neighbor_count,effective_neighbor_count=r.effective_neighbor_count,fallback_global=r.fallback_global,weight=r.weight,mean_geo_distance_km=float(np.mean(geo)) if len(geo) else np.nan,same_municipality_fraction=float(np.mean(meta.loc[neighbors].Municipio.to_numpy()==meta.loc[r.ID_POLIGONO,'Municipio'])) if neighbors else np.nan,same_profile_fraction=float(np.mean(meta.loc[neighbors].climate_profile.to_numpy()==meta.loc[r.ID_POLIGONO,'climate_profile'])) if neighbors else np.nan))
    neighbor_rows=pd.DataFrame(neighbor_rows);neighbor_rows.to_csv(D/'neighbor_diagnostics_by_parcel.csv',index=False);neighbor_rows.groupby(['experiment','protocol'])[['neighbor_count','effective_neighbor_count','fallback_global','weight','mean_geo_distance_km','same_municipality_fraction','same_profile_fraction']].mean().reset_index().to_csv(D/'neighbor_diagnostics_summary.csv',index=False)
    replay=[];loadings=[];times=[]
    with threadpool_limits(limits=1):
        for fi in range(65):
            ck=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];assert not set(tr)&set(va);rows=pd.DataFrame(ck['predictions']);times.append(dict(execution_index=fi,seconds=ck['seconds']))
            for name,item in pack['models'].items():
                base=cfg['recipes'][name]['base'];ref='CT3' if base=='CT3' else 'J7_BOTH';bp=rows[rows.experiment==ref].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();expected=rows[rows.experiment==name].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy()
                if item['mode']=='GLOBAL':
                    delta=item['amplitude']/.5*item['model'].delta(x.iloc[va]);pc=item['model'].space
                    if pc.model is not None:
                        for component,(vector,variance) in enumerate(zip(pc.model.components_,pc.model.explained_variance_ratio_)):
                            for feature,loading in zip(np.array(pc.columns)[pc.support],vector):loadings.append(dict(execution_index=fi,experiment=name,protocol=rows.protocol.iloc[0],component=component+1,feature=feature,loading=loading,explained_variance=variance))
                else:
                    delta,record=item['model'].predict(x.iloc[va],item['use'],item['amplitude'],True)
                    for r in record:assert set(r['neighbor_ids']).issubset(set(t.iloc[tr].ID_POLIGONO)) and not set(r['neighbor_ids'])&set(t.iloc[va].ID_POLIGONO)
                difference=float(max(abs(bp+delta-expected)));assert difference<1e-12 and max(abs(delta))<=.25+1e-12;replay.append(dict(execution_index=fi,experiment=name,max_difference=difference))
                candidates=[r for r in ck['candidates'] if r['experiment']==name];mode=cfg['recipes'][name]['mode'];best=min(candidates,key=lambda z:(round(z['rmse'],12),z['amplitude'],-z['param'] if mode=='KNN' else z.get('param',0)));selected=selection[(selection.execution_index==fi)&(selection.experiment==name)].iloc[0];assert selected.amplitude==best['amplitude'];assert mode=='GLOBAL' or selected.param==best['param']
    pd.DataFrame(replay).to_csv(OUT/'audit/model_replay.csv',index=False);pd.DataFrame(loadings).to_csv(D/'PCA_loadings_by_fold.csv',index=False);pd.DataFrame(times).to_csv(D/'execution_times.csv',index=False)
    presentation=pd.DataFrame(index=['CT3','J7_BOTH','CT3_INDICATORS_DIRECT','J7_INDICATORS_DIRECT','CT3_P_RAW','J7_P_RAW']+list(cfg['recipes']))
    for pro in PROTOCOLS:
        q=summary[summary.protocol==pro].set_index('experiment');presentation[pro]=[f'{q.loc[n,"rmse"]:.4f} / {q.loc[n,"r2"]:.4f}' for n in presentation.index]
    presentation.index.name='modelo';presentation.to_csv(D/'presentation_RMSE_R2.csv')
    report=ROOT/'documentation/indicator_neighborhoods_results.md';report.write_text('\n\n'.join(['# Reducciones y vecindarios: resultados exploratorios','k/clusters/amplitud seleccionados sólo con OOF internas DIRECT, compartidos con WEIGHT. El peso no se optimizó independientemente. Las distancias físicas/satelitales no utilizan coordenadas como entrada, pero pueden correlacionarse con territorio.','## RMSE / R²',md(presentation.reset_index()),'## Diagnóstico de vecinos',md(pd.read_csv(D/'neighbor_diagnostics_summary.csv')),'## Ganancias por parcela',md(pd.DataFrame(distribution)),'208pruebas pareadas con Holm, omisiones, métricas sin35/sin10/sin171/015, regiones, intraperfil y selección interna están en las tablas/Excel. No se selecciona un Champion con estos resultados exploratorios.']),encoding='utf-8')
    with pd.ExcelWriter(OUT/'evaluacion_reducciones_y_vecindarios.xlsx',engine='openpyxl') as writer:
        pd.DataFrame({'lectura':['RMSE t/ha / R²; protocolos separados.','GLOBAL_R9/R4/R3/R2/PCA2 son representaciones, PCA2 conserva9variables fuente.','KNN: k8/16/24/48/72; CLUSTER:4/8.','GEO=centroides; PHYSICAL=suelo/geología/relieve; SATELLITE=3indicadores puros.','DIRECT=Ridge local de residuos; WEIGHT=peso local de propuesta globalR4.','Mismo k/cluster y amplitud internos para ambos usos; peso no retuneado aparte.','SATELLITEsin historia usa respaldo global; no elimina parcelas.','Evaluación exploratoria, sin PRED59 ni ajuste final138.']}).to_excel(writer,sheet_name='LEEME',index=False);presentation.reset_index().to_excel(writer,sheet_name='RESUMEN',index=False)
        for f in sorted(D.glob('*.csv')):
            if f.stem in ['presentation_RMSE_R2','parcel_gains','PCA_loadings_by_fold','neighbor_diagnostics_by_parcel']:continue
            pd.read_csv(f).to_excel(writer,sheet_name=f.stem[:31],index=False)
        for sheet in writer.book.worksheets:sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'evaluation_complete.json').write_text(json.dumps(dict(status='complete',new_recipes=34,models_replayed=len(replay),OOF_rows=len(p),paired_tests=208,significant_holm=int((tests.p_holm<.05).sum()),protected_sources_unchanged=True,external_references_exact=True,no_PRED=True,no_final138_fit=True),indent=2),encoding='utf-8');print(presentation.to_string());print('\nHolm significant:');print(tests[tests.p_holm<.05].to_string(index=False))


if __name__=='__main__':main()
