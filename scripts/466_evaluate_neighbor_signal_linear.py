"""Continuous contrast alternatives, compared with frozen J7 and tree variants."""
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
from src.neighbor_signal_linear import OUT,TREE_OUT
from src.neighbor_signal_contrasts import load_assets,SIGNALS
from src.geoc_bridge import OLD
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
spec=importlib.util.spec_from_file_location('continuous_audit449',ROOT/'scripts/449_j7_both_residual_audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
D=OUT/'tables';PROTOCOLS=['random','climate_profile','municipality','spatial']


def md(frame):
    def cell(v):return f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v).replace('|','/')
    return '\n'.join(['| '+' | '.join(map(str,frame.columns))+' |','| '+' | '.join(['---']*len(frame.columns))+' |']+['| '+' | '.join(map(cell,row))+' |' for row in frame.itertuples(index=False,name=None)])


def write(name,rows,keys):
    d=pd.DataFrame(rows);d.to_csv(D/(name+'_by_repeat.csv'),index=False);s=d.drop(columns='repeat',errors='ignore').groupby(keys,dropna=False).mean(numeric_only=True).reset_index();s.to_csv(D/(name+'_summary.csv'),index=False);return s


def main():
    if (OUT/'evaluation_complete.json').exists():raise FileExistsError('Preserve completed continuous evaluation')
    assert (OUT/'execution_complete.json').exists();cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    a=load_assets();t=a['a']['train'];ids=t.ID_POLIGONO.tolist();y=a['y'];new=pd.read_parquet(D/'predictions.parquet');tree=pd.read_parquet(TREE_OUT/'tables/predictions.parquet');keys=['experiment','protocol','repeat','fold','ID_POLIGONO','y_true','y_pred'];assert len(new)==4*1794 and len(tree)==6*1794
    for name in ['J7_BOTH','CT3']:
        z=new[new.experiment==name].merge(tree[tree.experiment==name],on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');np.testing.assert_array_equal(z.y_true,z.y_true_ref);np.testing.assert_array_equal(z.y_pred,z.y_pred_ref)
    p=pd.concat([tree[keys],new[new.experiment.isin(cfg['recipes'])][keys]],ignore_index=True);assert len(p)==8*1794 and not p.duplicated(['experiment','protocol','repeat','ID_POLIGONO']).any();p=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');p['error']=p.y_pred-p.y_true;p['absolute_error']=abs(p.error);p['squared_error']=p.error**2;p.to_parquet(D/'combined_oof_residuals.parquet',index=False);bins=dict(zip(ids,pd.qcut(pd.Series(y),4,duplicates='drop').astype(str)));p['target_quartile']=p.ID_POLIGONO.map(bins)
    metrics=[];regions=[];omits=[];without=[];quarters=[];pairs=[]
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.nunique()==138;key=dict(experiment=name,protocol=pro,repeat=re);m=audit.stats(g);assert np.isclose(m['rmse']**2,m['error_variance']+m['bias_squared']);metrics.append(dict(**key,**m));without.append(dict(**key,**audit.stats(g[~g.ID_POLIGONO.isin(['AGC_171','AGC_015'])])));pairs.append(dict(**key,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold','climate_profile']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(zone),**audit.stats(h)))
                if kind!='climate_profile':omits.append(dict(**key,kind=kind,omitted=str(zone),**audit.stats(g[g[kind]!=zone])))
        for zone,h in g.groupby('target_quartile'):quarters.append(dict(**key,zone=zone,**audit.stats(h)))
    summary=write('metrics',metrics,['experiment','protocol']);write('regions',regions,['experiment','protocol','kind','zone']);write('omissions',omits,['experiment','protocol','kind','omitted']);write('without_171_015',without,['experiment','protocol']);write('quartiles',quarters,['experiment','protocol','zone']);write('intraprofile',pairs,['experiment','protocol'])
    for source,join in [('regions',['protocol','kind','zone']),('omissions',['protocol','kind','omitted']),('without_171_015',['protocol'])]:
        data=pd.read_csv(D/(source+'_summary.csv'));rows=[]
        for name in cfg['recipes']:
            z=data[data.experiment==name].merge(data[data.experiment=='J7_BOTH'],on=join,suffixes=('','_reference'),validate='one_to_one')
            for column in ['rmse','mae','r2','bias']:z['delta_'+column]=z[column]-z[column+'_reference']
            rows.append(z)
        pd.concat(rows,ignore_index=True).to_csv(D/(source+'_paired_changes.csv'),index=False)
    parcel=p.groupby(['experiment','protocol','ID_POLIGONO','Estado','Municipio','climate_profile']).agg(y_true=('y_true','first'),prediction=('y_pred','mean'),mean_error=('error','mean'),mean_absolute_error=('absolute_error','mean'),mean_squared_error=('squared_error','mean')).reset_index();parcel.to_csv(D/'parcel_errors.csv',index=False);parcel[parcel.ID_POLIGONO.isin(['AGC_171','AGC_015'])].to_csv(D/'cases_171_015.csv',index=False)
    contrasts=[(n,'J7_BOTH','reference') for n in cfg['recipes']]+[('GEO_LINEAR','COMPACT_LINEAR','neighborhood')]+[(f'{kind}_LINEAR',f'{kind}_RESIDUAL','continuous_vs_tree') for kind in ['GEO','COMPACT']];tests=[];gains=[];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids]
    with threadpool_limits(limits=1):
        for pro,g in p.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();weights,_=cluster_weights(group,5000,2026);arrays={name:h.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy() for name,h in g.groupby('experiment')};samples={name:sampled_metrics(y,v,weights) for name,v in arrays.items()}
            for name,ref,kind in contrasts:
                aa=arrays[name];bb=arrays[ref];delta=samples[name]['rmse']-samples[ref]['rmse'];point=np.sqrt(np.mean((aa-y)**2,axis=1)).mean()-np.sqrt(np.mean((bb-y)**2,axis=1)).mean();loss=np.sum((aa-y)**2-(bb-y)**2,axis=0);tests.append(dict(experiment=name,reference=ref,contrast=kind,protocol=pro,delta_rmse=float(point),low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
                for j,i in enumerate(ids):gains.append(dict(experiment=name,reference=ref,contrast=kind,protocol=pro,ID_POLIGONO=i,sse_gain=float(np.mean((bb[:,j]-y[j])**2-(aa[:,j]-y[j])**2)),absolute_error_gain=float(np.mean(abs(bb[:,j]-y[j])-abs(aa[:,j]-y[j])))))
    tests=pd.DataFrame(tests);assert len(tests)==20;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'paired_tests.csv',index=False);gains=pd.DataFrame(gains);gains.to_csv(D/'parcel_gains.csv',index=False);gs=[]
    for (name,pro),g in gains[gains.contrast=='reference'].groupby(['experiment','protocol']):gs.append(dict(experiment=name,protocol=pro,total_sse_gain=g.sse_gain.sum(),cases_sse_gain=g[g.ID_POLIGONO.isin(['AGC_171','AGC_015'])].sse_gain.sum(),remaining_sse_gain=g[~g.ID_POLIGONO.isin(['AGC_171','AGC_015'])].sse_gain.sum(),fraction_improved=float(np.mean(g.absolute_error_gain>1e-12)),fraction_worsened=float(np.mean(g.absolute_error_gain < -1e-12))))
    pd.DataFrame(gs).to_csv(D/'gain_distribution.csv',index=False)
    coefs=[];details=[];checks=[];warn=[];timings=[];ledger_count=0;max_replay=0.;calibration_difference=0.;feature_names=[k+'_local_z' for k in SIGNALS]+[k+'_global_delta' for k in SIGNALS]
    with threadpool_limits(limits=1):
        for fi in range(65):
            ck=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');old=joblib.load(TREE_OUT/'checkpoints'/f'{fi:02d}.joblib');pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');va=np.asarray(pack['validation_positions']);tr=np.asarray(pack['train_positions']);assert not set(tr)&set(va);timings.append(dict(execution_index=fi,seconds=ck['seconds'],**ck['warm_hits']));warn.extend(dict(r,execution_index=fi) for r in ck['warnings'])
            old_null=[r['rmse'] for r in old['candidates'] if r['amplitude']==0];new_null=[r['rmse'] for r in ck['candidates'] if r['amplitude']==0];diff=max(abs(np.array(new_null)-old_null[0]));assert diff<1e-12;calibration_difference=max(calibration_difference,float(diff));checks.append(dict(execution_index=fi,null_calibration_rmse_difference=float(diff)))
            for r in ck['ledger']:assert not set(r['train'])&(set(r['held'])|set(va));ledger_count+=1
            for name,model in pack['models'].items():
                rows=[r for r in ck['details'] if r['experiment']==name];assert [r['position'] for r in rows]==va.tolist();m=model['adjustment'];assert m.model is None or m.model.fit_intercept is False;z=model['contrast'].transform(va);bp=np.array([r['base_prediction'] for r in rows]);ct=np.array([r['ct3_prediction'] for r in rows]);pred=m.predict(z,bp,ct);expected=np.array([r['prediction'] for r in rows]);diff=float(max(abs(pred-expected)));assert diff<1e-12 and max(abs(pred-bp))<=.5+1e-12;max_replay=max(max_replay,diff);np.testing.assert_array_equal(m.predict(np.zeros((3,6)),np.ones(3),np.ones(3)),np.ones(3))
                coefficients=np.zeros(6)
                if m.model is not None:coefficients[m.support]=m.model.coef_
                for j,feature in enumerate(feature_names):coefs.append(dict(execution_index=fi,protocol=rows[0]['protocol'],experiment=name,feature=feature,coefficient=float(coefficients[j]),effective_coefficient_per_contrast=float(m.amplitude*coefficients[j]/m.scale[j]),nonzero=bool(abs(coefficients[j])>1e-10),amplitude=m.amplitude))
            for r in ck['details']:
                assert set(r['neighbors']).issubset(set(tr)) and r['position'] not in r['neighbors'];row={k:v for k,v in r.items() if k not in ['reference_medians','reference_mad','local_z','global_delta']}
                for j,feature in enumerate(SIGNALS):
                    for field in ['reference_medians','reference_mad','local_z','global_delta']:row[feature+'_'+field]=r[field][j]
                details.append(row)
    pd.DataFrame(coefs).to_csv(D/'coefficients_by_fold.csv',index=False);pd.DataFrame(coefs).groupby(['experiment','protocol','feature'])[['coefficient','effective_coefficient_per_contrast','nonzero']].mean().reset_index().to_csv(D/'coefficient_stability.csv',index=False);detail=pd.DataFrame(details);detail.to_parquet(D/'contrast_neighbors.parquet',index=False);detail.drop(columns='neighbors').to_csv(D/'contrast_features_and_adjustments.csv',index=False);pd.DataFrame(checks).to_csv(D/'calibration_parity.csv',index=False);pd.DataFrame(timings).to_csv(D/'execution_times_and_reuse.csv',index=False);pd.DataFrame(warn,columns=['execution_index','category','message']).groupby(['category','message']).size().rename('count').reset_index().to_csv(D/'warning_summary.csv',index=False)
    selections=pd.read_parquet(D/'selection.parquet');selections.to_csv(D/'selection_by_fold.csv',index=False);selections.groupby(['experiment','protocol','alpha','l1_ratio','amplitude']).size().rename('folds').reset_index().to_csv(D/'selection_counts.csv',index=False)
    presentation=pd.DataFrame(index=['J7_BOTH','CT3','GEO_LINEAR','COMPACT_LINEAR','GEO_ATTENUATE','COMPACT_ATTENUATE','GEO_RESIDUAL','COMPACT_RESIDUAL'])
    for pro in PROTOCOLS:
        q=summary[summary.protocol==pro].set_index('experiment');presentation[pro]=[f'{q.loc[n,"rmse"]:.4f} / {q.loc[n,"r2"]:.4f}' for n in presentation.index]
    presentation.index.name='modelo';presentation.to_csv(D/'presentation_RMSE_R2.csv');delta=tests[tests.contrast=='reference'].pivot(index='experiment',columns='protocol',values='delta_rmse').reindex(index=list(cfg['recipes']),columns=PROTOCOLS);fig,ax=plt.subplots(figsize=(9,3));limit=max(abs(delta.to_numpy()).max(),.001);im=ax.imshow(delta,cmap='RdBu_r',vmin=-limit,vmax=limit,aspect='auto');ax.set_xticks(range(4),['Aleatoria','Perfil','Municipal','Espacial']);ax.set_yticks(range(2),delta.index)
    for i in range(2):
        for j in range(4):ax.text(j,i,f'{delta.iloc[i,j]:+.4f}',ha='center',va='center')
    ax.set_title('Contrastes continuos: cambio RMSE frente a J7');fig.colorbar(im,ax=ax,label='t/ha');fig.tight_layout();fig.savefig(OUT/'figures/continuous_rmse_changes.png',dpi=160);plt.close(fig)
    report=ROOT/'documentation/neighbor_signal_linear_results.md';report.write_text('\n\n'.join(['# Contrastes continuos: resultados y comparación conjunta','Elastic Net solo sobre los seis contrastes, sin intercepto, con SD del entrenamiento y sin centrar. Cero diferencia implica cero ajuste. Corrección máxima ±0.5 t/ha. Misma base, vecinos y calibración que el experimento de árboles; referencias externas exactas.','## RMSE / R²',md(presentation.reset_index()),'## Métricas completas',md(summary[['experiment','protocol','rmse','mae','r2','bias','error_sd']]),'## Comparaciones pareadas: ampliación exploratoria de 20 contrastes',md(tests),'## Ganancias por parcela',md(pd.DataFrame(gs)),'Las tablas incluyen regiones, omisiones, cuartiles, intraperfil y análisis sin 171/015. Coeficientes estandarizados y estabilidad de selección se conservan por fold; no son efectos causales ni significancia estadística individual.',f'Calibración nula frente a árboles: diferencia máxima {calibration_difference:.3g}; replay máximo {max_replay:.3g}; {ledger_count} exclusiones verificadas. Sin uso de PRED59 ni modelo final138.','Conclusiones y recomendación: neighbor_signal_linear_conclusions.md.']),encoding='utf-8')
    with pd.ExcelWriter(OUT/'evaluacion_contrastes_continuos_y_arboles.xlsx',engine='openpyxl') as writer:
        pd.DataFrame({'lectura':['RESUMEN: RMSE t/ha / R²; menor RMSE y mayor R² son preferibles.','LINEAR = contraste continuo con Elastic Net, sin intercepto; cero contraste implica cero ajuste.','ATTENUATE = árbol que reduce J7 hacia CT3; RESIDUAL = corrector arbóreo.','GEO/COMPACT = vecinos geográficos o similares en compact4.','Aleatoria: OOF completas por repetición, luego promedio de diez.','Dos etapas exploratorias; Holm de 20 contrastes para la ampliación continua.','Sin modelo final ni PRED59. Coeficientes no causales.']}).to_excel(writer,sheet_name='LEEME',index=False);presentation.reset_index().to_excel(writer,sheet_name='RESUMEN',index=False)
        for f in sorted(D.glob('*.csv')):
            if f.stem in ['contrast_features_and_adjustments','parcel_gains','presentation_RMSE_R2']:continue
            pd.read_csv(f).to_excel(writer,sheet_name=f.stem[:31],index=False)
        for sheet in writer.book.worksheets:sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'evaluation_complete.json').write_text(json.dumps(dict(status='complete',models=8,new_continuous_models=2,folds=65,oof_rows=len(p),paired_tests=20,significant_holm=int((tests.p_holm<.05).sum()),calibration_null_max_difference=calibration_difference,replay_max_difference=max_replay,ledger_exclusions_verified=ledger_count,protected_sources_unchanged=True,zero_anchor_verified=True,no_PRED=True,no_final138_fit=True,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2),encoding='utf-8');print(presentation.to_string());print(tests.to_string(index=False))


if __name__=='__main__':main()
