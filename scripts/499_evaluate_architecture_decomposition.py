"""OOF metrics, paired architectural effects and replay of the fixed factorial."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.architecture_decomposition import OUT,load_assets,predict_routes,local_sets,load_design
from src.indicator_neighborhoods import OUT as INDICATORS,REDUCTIONS,ReducedCorrection
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
REF='FULL7_ON_RAW_MASK';D=OUT/'tables';KEY=['protocol','repeat','fold','ID_POLIGONO'];PROTOCOLS=['random','climate_profile','municipality','spatial']
spec=importlib.util.spec_from_file_location('metrics487',ROOT/'scripts/487_j7_r3_residual_simplification.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def md(d):
    def c(v):return f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v).replace('|','/')
    return '\n'.join(['| '+' | '.join(d.columns)+' |','| '+' | '.join(['---']*len(d.columns))+' |']+['| '+' | '.join(map(c,r))+' |' for r in d.itertuples(index=False,name=None)])

def write(name,rows,keys):
    f=pd.DataFrame(rows);f.to_csv(D/(name+'_by_repeat.csv'),index=False);s=f.drop(columns='repeat',errors='ignore').groupby(keys,dropna=False).mean(numeric_only=True).reset_index();s.to_csv(D/(name+'_summary.csv'),index=False);return s

def main():
    assert not (OUT/'evaluation_complete.json').exists();assert (OUT/'execution_complete.json').exists();cfg=load_design();assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());a=load_assets();t=a['a']['train'];ids=t.ID_POLIGONO.tolist();y=a['y'];x=pd.read_parquet(INDICATORS/'cache/features_train138_target_free.parquet');p=pd.read_parquet(D/'predictions.parquet');assert len(p)==99*1794 and not p.duplicated(['experiment','protocol','repeat','ID_POLIGONO']).any();p=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');p['error']=p.y_pred-p.y_true;p['absolute_error']=abs(p.error);p['squared_error']=p.error**2;p.to_parquet(D/'oof_residuals.parquet',index=False)
    old=pd.read_parquet(ROOT/'outputs/modeling/learned_r3_weight/v1/tables/predictions.parquet')
    for name,ref in [(REF,'SHARES_MASK'),('FULL7_ON_RAW_BASE','SHARES_BASE'),('CT3_BASE','CT3_BASE'),('CT3_MASK','CT3_MASK'),('J7_GLOBAL_GLOBAL','J7_GLOBAL_GLOBAL')]:
        z=p[p.experiment==name].merge(old[old.experiment==ref],on=KEY,suffixes=('','_ref'),validate='one_to_one');assert len(z)==1794;np.testing.assert_allclose(z.y_pred,z.y_pred_ref,atol=1e-12,rtol=0)
    metrics=[];regions=[];omits=[];quartiles=[];supports=[];without=[];pairs=[];bins=dict(zip(ids,pd.qcut(y,4,duplicates='drop').astype(str)));complete=dict(zip(ids,np.isfinite(x[REDUCTIONS['R3']].to_numpy(float)).all(axis=1)));hard=pd.read_csv(ROOT/'outputs/research/difficult_quartile/v1/tables/parcel_groups.csv');hard=hard[hard.hard_quartile].ID_POLIGONO.tolist()
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;k=dict(experiment=name,protocol=pro,repeat=re);metrics.append(dict(**k,**audit.stats(g)));pairs.append(dict(**k,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):regions.append(dict(**k,kind=kind,zone=str(zone),**audit.stats(h)));omits.append(dict(**k,kind=kind,omitted=str(zone),**audit.stats(g[g[kind]!=zone])))
        for zone,h in g.groupby(g.ID_POLIGONO.map(bins)):quartiles.append(dict(**k,zone=zone,**audit.stats(h)))
        for c,h in g.groupby(g.ID_POLIGONO.map(complete)):supports.append(dict(**k,complete_R3=c,**audit.stats(h)))
        for label,cases in [('hard35',hard),('171_015',['AGC_171','AGC_015'])]:without.append(dict(**k,excluded=label,**audit.stats(g[~g.ID_POLIGONO.isin(cases)])))
    summary=write('metrics',metrics,['experiment','protocol']);write('regions',regions,['experiment','protocol','kind','zone']);write('omissions',omits,['experiment','protocol','kind','omitted']);write('quartiles',quartiles,['experiment','protocol','zone']);write('support_groups',supports,['experiment','protocol','complete_R3']);write('without_cases',without,['experiment','protocol','excluded']);write('intraprofile',pairs,['experiment','protocol'])
    # Fixed paired comparisons: do not choose a winner inside an external fold.
    comparisons=[]
    for name in cfg['recipes']:
        if name+'_MASK'!=REF:comparisons.append((name+'_MASK',REF,'vs_reference'))
    for local in local_sets():
        for gate in ['RAW','PCA2','GLOBAL']:comparisons.append((f'{local}_OFF_{gate}_MASK',f'{local}_ON_{gate}_MASK','remove_internal'))
        for internal in ['OFF','ON']:
            for gate in ['PCA2','GLOBAL']:comparisons.append((f'{local}_{internal}_{gate}_MASK',f'{local}_{internal}_RAW_MASK','gate_'+gate))
    assert len(comparisons)==103;groups=pd.read_csv(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/groups.csv').set_index('ID_POLIGONO').loc[ids];tests=[];gains=[]
    with threadpool_limits(limits=1):
        for pro,g in p.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();w,_=cluster_weights(group,5000,2026);arrays={n:h.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy() for n,h in g.groupby('experiment')};samples={n:sampled_metrics(y,v,w) for n,v in arrays.items()}
            for name,ref,contrast in comparisons:
                aa=arrays[name];bb=arrays[ref];delta=samples[name]['rmse']-samples[ref]['rmse'];point=np.sqrt(np.mean((aa-y)**2,axis=1)).mean()-np.sqrt(np.mean((bb-y)**2,axis=1)).mean();tests.append(dict(experiment=name,reference=ref,contrast=contrast,protocol=pro,delta_rmse=point,low95=np.quantile(delta,.025),high95=np.quantile(delta,.975),**paired_signflip(np.sum((aa-y)**2-(bb-y)**2,axis=0),group)))
                if contrast=='vs_reference':
                    for j,i in enumerate(ids):gains.append(dict(experiment=name,reference=ref,protocol=pro,ID_POLIGONO=i,sse_gain=float(np.mean((bb[:,j]-y[j])**2-(aa[:,j]-y[j])**2)),absolute_gain=float(np.mean(abs(bb[:,j]-y[j])-abs(aa[:,j]-y[j])))))
    tests=pd.DataFrame(tests);tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'paired_tests.csv',index=False);gains=pd.DataFrame(gains);gains.to_csv(D/'parcel_gains.csv',index=False);dist=[]
    for (name,pro),g in gains.groupby(['experiment','protocol']):dist.append(dict(experiment=name,protocol=pro,total_sse_gain=g.sse_gain.sum(),hard35_sse_gain=g[g.ID_POLIGONO.isin(hard)].sse_gain.sum(),remaining103_sse_gain=g[~g.ID_POLIGONO.isin(hard)].sse_gain.sum(),fraction_improved=(g.absolute_gain>1e-12).mean(),fraction_worsened=(g.absolute_gain< -1e-12).mean()))
    pd.DataFrame(dist).to_csv(D/'gain_distribution.csv',index=False)
    # Architectural and interaction effects are computed on repeat MSE, not sums of RMSE.
    effects=[];interactions=[]
    for (pro,re),g in pd.DataFrame(metrics).groupby(['protocol','repeat']):
        z=g.set_index('experiment');mse=lambda n:z.loc[n,'rmse']**2
        for name,r in cfg['recipes'].items():
            for ref,kind in [(name+'_BASE','R3_effect'),('FULL7_'+r['internal']+'_'+r['gate']+'_MASK','local_set_effect')]:
                for col in ['rmse','r2','mae','bias']:effects.append(dict(experiment=name+'_MASK',reference=ref,protocol=pro,repeat=re,contrast=kind,metric=col,difference=z.loc[name+'_MASK',col]-z.loc[ref,col]))
        for local in local_sets():
            for gate in ['PCA2','GLOBAL']:
                value=mse(f'{local}_OFF_{gate}_MASK')-mse(f'{local}_ON_{gate}_MASK')-mse(f'{local}_OFF_RAW_MASK')+mse(f'{local}_ON_RAW_MASK');interactions.append(dict(local=local,gate=gate,protocol=pro,repeat=re,interaction='internal_x_gate',delta_mse=value))
                if local!='FULL7':
                    val=value-(mse(f'FULL7_OFF_{gate}_MASK')-mse(f'FULL7_ON_{gate}_MASK')-mse('FULL7_OFF_RAW_MASK')+mse('FULL7_ON_RAW_MASK'));interactions.append(dict(local=local,gate=gate,protocol=pro,repeat=re,interaction='local_x_internal_x_gate',delta_mse=val))
    write('architectural_effects',effects,['experiment','reference','protocol','contrast','metric']);write('MSE_interactions',interactions,['local','gate','protocol','interaction'])
    selection=pd.read_parquet(D/'selection.parquet');selection.to_csv(D/'selection_by_fold.csv',index=False);selection.assign(active=selection.strength>0).groupby(['experiment','protocol']).agg(active_folds=('active','sum'),total_folds=('active','size')).reset_index().to_csv(D/'activation.csv',index=False);details=pd.read_parquet(D/'details.parquet');details.groupby(['experiment','protocol']).agg(expert_weight=('expert_weight','mean'),internal_amplitude=('internal_amplitude','mean'),mean_abs_R3=('applied_delta',lambda z:abs(z).mean())).reset_index().to_csv(D/'component_weights.csv',index=False)
    # Replay saved models and independently rebuild correction calibrations.
    replay=[];calibration=[];gate_selection=[];pca=[];pca_loadings=[];times=[]
    with threadpool_limits(limits=1):
        for fi in range(65):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');ck=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];assert not set(tr)&set(va);r=pd.DataFrame(ck['predictions']);external=predict_routes(pack['base_model'],va,a);valid=np.isfinite(x.iloc[va][REDUCTIONS['R3']].to_numpy(float)).all(axis=1);times.append(dict(execution_index=fi,seconds=ck['seconds']))
            for name,item in pack['adjustments'].items():
                correct=item['strength']*valid*item['corrector'].delta(x.iloc[va])
                for suffix,pred in [('_BASE',external[name]),('_MASK',external[name]+correct)]:
                    expected=r[r.experiment==name+suffix].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();difference=float(max(abs(pred-expected)));assert difference<1e-12;replay.append(dict(execution_index=fi,experiment=name+suffix,max_difference=difference))
                reconstructed=np.full(len(tr),np.nan)
                for ctx in ck['contexts']:
                    aa=np.asarray(ctx['aa']);d=ctx['where'];assert not set(aa)&(set(tr[d])|set(va));m=ReducedCorrection('R3').fit(x.iloc[aa],y[aa]-ctx['base_oof'][name]);reconstructed[d]=m.delta(x.iloc[tr[d]])*np.isfinite(x.iloc[tr[d]][REDUCTIONS['R3']].to_numpy(float)).all(axis=1)
                scores=[dict(strength=s,rmse=float(np.sqrt(np.mean((item['base_oof']+s*reconstructed-y[tr])**2)))) for s in cfg['strengths']];best=min(scores,key=lambda v:(round(v['rmse'],12),v['strength']));assert best['strength']==item['strength'];calibration.append(dict(execution_index=fi,experiment=name,strength_verified=True))
                route=pack['base_model']['routes'][name];best_gate=min(route['candidates'],key=lambda v:(round(v['rmse'],12),v['k']));assert best_gate['k']==route['selection']['k'];gate_selection.append(dict(execution_index=fi,experiment=name,protocol=r.protocol.iloc[0],k=best_gate['k']))
                if route['space'].pca is not None:
                    pca.append(dict(execution_index=fi,experiment=name,protocol=r.protocol.iloc[0],variance_2PC=float(route['space'].pca.explained_variance_ratio_.sum())))
                    if name=='FULL7_OFF_PCA2':
                        for component,(vector,variance) in enumerate(zip(route['space'].pca.components_,route['space'].pca.explained_variance_ratio_)):
                            for feature,value in zip(a['physical_definitions']['geologic_composition']['columns'],vector):pca_loadings.append(dict(execution_index=fi,protocol=r.protocol.iloc[0],component=component+1,feature=feature,loading=value,explained_variance=variance))
            for rec in ck['ledger']:assert not set(rec['train'])&(set(rec['held'])|set(va)|set(rec.get('excluded_inner',[])))
    pd.DataFrame(replay).to_csv(OUT/'audit/model_replay.csv',index=False);pd.DataFrame(calibration).to_csv(OUT/'audit/correction_calibration.csv',index=False);pd.DataFrame(gate_selection).to_csv(D/'gate_selection.csv',index=False);pd.DataFrame(pca).to_csv(D/'PCA_variance.csv',index=False);pd.DataFrame(pca_loadings).to_csv(D/'PCA_loadings.csv',index=False);pd.DataFrame(times).to_csv(D/'execution_times.csv',index=False)
    presentation=pd.DataFrame(index=sorted(summary.experiment.unique()))
    for pro in PROTOCOLS:
        z=summary[summary.protocol==pro].set_index('experiment');presentation[pro]=[f'{z.loc[n,"rmse"]:.4f} / {z.loc[n,"r2"]:.4f}' for n in presentation.index]
    def count(n):
        if n in ['CT3_BASE','CT3_MASK','J7_GLOBAL_GLOBAL']:return {'CT3_BASE':4,'CT3_MASK':7,'J7_GLOBAL_GLOBAL':31}[n]
        name,suffix=n.rsplit('_',1);return cfg['recipes'][name]['mask_input_count' if suffix=='MASK' else 'base_input_count']
    presentation['input_count']=[count(n) for n in presentation.index];presentation.index.name='experiment';presentation.reset_index().to_csv(D/'presentation_RMSE_R2.csv',index=False);pd.DataFrame([dict(experiment=n,**r) for n,r in cfg['recipes'].items()]).to_json(D/'input_inventory.json',orient='records',indent=2,force_ascii=False)
    report=['# Descomposición de bases: resultados exploratorios','99 entradas sobre65 folds:48 bases × BASE/MASK y3 controles. Métricas por OOF completas de cada repetición, aleatoria media10. OFF retira corrector interno; ON transfiere sus hiperparámetros del FULL7 del mismo entrenamiento y reajusta coeficientes por cada composición. RAW usa10 proporciones; PCA2 conserva esas10 entradas pero reduce a2 dimensiones; GLOBAL elimina geología y aprende peso escalar. No se seleccionó un Champion con las evaluaciones externas.',md(presentation.reset_index()),f'412 contrastes predefinidos con Holm; significativos: {int((tests.p_holm<.05).sum())}. Las retiradas y combinaciones son exploratorias sobre particiones previamente usadas. Los intervalos de OOF fijas no incluyen toda la búsqueda histórica y sólo hay5 bloques espaciales.','Se guardan efectos marginales e interacciones en MSE por repetición, pesos del experto, activación R3, errores regionales/cuartiles/intraperfil y omisiones. El conteo de campos no equivale a costo computacional: PCA2 requiere toda su geología y quitar corrector interno no elimina compact4 porque C-T3 permanece. No hay PRED59, ajuste final138 ni cambio de Champion.']
    (ROOT/'documentation/architecture_decomposition_results.md').write_text('\n\n'.join(report),encoding='utf-8')
    with pd.ExcelWriter(OUT/'descomposiciones_y_combinaciones.xlsx',engine='openpyxl') as writer:
        presentation.reset_index().to_excel(writer,sheet_name='RMSE_R2',index=False)
        for f in sorted(D.glob('*.csv')):
            if f.stem.endswith('_by_repeat') or f.stem in ['parcel_gains','presentation_RMSE_R2','selection_by_fold','gate_selection']:continue
            pd.read_csv(f).to_excel(writer,sheet_name=f.stem[:31],index=False)
        for sheet in writer.book.worksheets:sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());result=dict(status='complete',entries=99,OOF_rows=len(p),models_replayed=len(replay),correction_calibrations_verified=len(calibration),gates_verified=len(gate_selection),reference_predictions_exact=True,protected_sources_unchanged=True,paired_tests=len(tests),significant_holm=int((tests.p_holm<.05).sum()),no_PRED=True,no_final138_fit=True,no_champion_change=True);(OUT/'evaluation_complete.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(presentation.to_string());print(json.dumps(result,indent=2))

if __name__=='__main__':main()
