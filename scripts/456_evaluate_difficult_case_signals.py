"""Paired frozen-OOF evaluation of signal placement; no predictive refit."""
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
from src.difficult_case_signals import OUT,JOINT,load_assets,SIGNALS
from src.signal_role_allocation import predict_role
from src.geoc_signal_research import predict_base
from src.geoc_bridge import OLD
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
spec=importlib.util.spec_from_file_location('audit449',ROOT/'scripts/449_j7_both_residual_audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
D=OUT/'tables';PROTOCOLS=['random','climate_profile','municipality','spatial']


def table(frame):
    def cell(v):return f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v).replace('|','/')
    return '\n'.join(['| '+' | '.join(map(str,frame.columns))+' |','| '+' | '.join(['---']*len(frame.columns))+' |']+['| '+' | '.join(map(cell,row))+' |' for row in frame.itertuples(index=False,name=None)])


def write(name,rows,keys):
    frame=pd.DataFrame(rows);frame.to_csv(D/(name+'_by_repeat.csv'),index=False)
    summary=frame.drop(columns='repeat',errors='ignore').groupby(keys,dropna=False).mean(numeric_only=True).reset_index();summary.to_csv(D/(name+'_summary.csv'),index=False);return summary


def main():
    assert (OUT/'execution_complete.json').exists()
    if (OUT/'evaluation_complete.json').exists():raise FileExistsError('Preserve completed evaluation')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    inherited=json.loads((JOINT/'frozen_design.json').read_text())['source_sha256']
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in inherited.items())
    a=load_assets();t=a['a']['train'];ids=t.ID_POLIGONO.tolist();y=a['y'];p=pd.read_parquet(D/'predictions.parquet');assert len(p)==15*1794
    control=pd.read_parquet(ROOT/'outputs/research/case_outliers_and_model_residual_comparison/v1/comparison_oof_residuals.parquet')
    for name in set(cfg['references'].values()):
        old={'DROP_SOIL':'MIX_EXPERT9','DROP_HISTORY_WATER':'MIX_EXPERT10'}.get(name,name)
        q=p[p.experiment==name].merge(control[control.experiment==old],on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('','_old'),validate='one_to_one');assert len(q)==1794 and np.array_equal(q.y_true,q.y_true_old) and np.array_equal(q.y_pred,q.y_pred_old)
    keys=['protocol','repeat','fold','ID_POLIGONO','y_true','y_pred','experiment'];p=pd.concat([p[keys],control[control.experiment.isin(['CT3','LOCAL04D'])][keys]],ignore_index=True)
    assert len(p)==17*1794 and not p.duplicated(['experiment','protocol','repeat','ID_POLIGONO']).any()
    p=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');p['error']=p.y_pred-p.y_true;p['squared_error']=p.error**2;p['absolute_error']=abs(p.error)
    p.to_parquet(D/'oof_residuals.parquet',index=False)
    bins=dict(zip(ids,pd.qcut(pd.Series(y),4,duplicates='drop').astype(str)));p['target_quartile']=p.ID_POLIGONO.map(bins)
    metrics=[];regions=[];quarters=[];omits=[];intraprofile=[];exclusions=[];concentration=[]
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.nunique()==138
        k=dict(experiment=name,protocol=pro,repeat=re);m=audit.stats(g);assert np.isclose(m['rmse']**2,m['error_variance']+m['bias_squared']);metrics.append(dict(**k,**m));intraprofile.append(dict(**k,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold','climate_profile']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**k,kind=kind,zone=str(zone),**audit.stats(h)))
                if kind!='climate_profile':omits.append(dict(**k,kind=kind,omitted=str(zone),**audit.stats(g[g[kind]!=zone])))
        for zone,h in g.groupby('target_quartile'):quarters.append(dict(**k,zone=zone,**audit.stats(h)))
        exclusions.append(dict(**k,**audit.stats(g[~g.ID_POLIGONO.isin(['AGC_171','AGC_015'])])))
        for top in [1,2,5,10,20]:concentration.append(dict(**k,top=top,sse_share=float(g.nlargest(top,'squared_error').squared_error.sum()/g.squared_error.sum())))
    summary=write('metrics',metrics,['experiment','protocol']);write('regions',regions,['experiment','protocol','kind','zone']);write('quartiles',quarters,['experiment','protocol','zone']);write('omissions',omits,['experiment','protocol','kind','omitted']);write('intraprofile',intraprofile,['experiment','protocol']);without=write('without_171_015',exclusions,['experiment','protocol']);write('concentration',concentration,['experiment','protocol','top'])
    for source,join_keys in [('regions',['protocol','kind','zone']),('omissions',['protocol','kind','omitted']),('without_171_015',['protocol'])]:
        data=pd.read_csv(D/(source+'_summary.csv'));matched=[]
        for name,ref in cfg['references'].items():
            z=data[data.experiment==name].merge(data[data.experiment==ref],on=join_keys,suffixes=('','_reference'),validate='one_to_one');z['reference']=ref
            for column in ['rmse','mae','r2','bias']:z['delta_'+column]=z[column]-z[column+'_reference']
            matched.append(z)
        pd.concat(matched,ignore_index=True).to_csv(D/(source+'_paired_changes.csv'),index=False)
    parcel=p.groupby(['experiment','protocol','ID_POLIGONO','Estado','Municipio','climate_profile']).agg(y_true=('y_true','first'),mean_prediction=('y_pred','mean'),mean_error=('error','mean'),mean_absolute_error=('absolute_error','mean'),mean_squared_error=('squared_error','mean')).reset_index();parcel.to_csv(D/'parcel_errors.csv',index=False);parcel[parcel.ID_POLIGONO.isin(['AGC_171','AGC_015'])].to_csv(D/'cases_171_015.csv',index=False)
    contrasts=[(name,ref,'reference') for name,ref in cfg['references'].items()]
    contrasts += [(f'{b}_{block}_LOCAL',f'{b}_{block}_CORRECTION','placement') for b in ['J7','E9','E10'] for block in ['ET','ETN']]
    contrasts += [(f'{b}_ETN_{place}',f'{b}_ET_{place}','third_signal') for b in ['J7','E9','E10'] for place in ['LOCAL','CORRECTION']]
    tests=[];gains=[];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids]
    with threadpool_limits(limits=1):
        for pro,g in p.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();weights,ncluster=cluster_weights(group,5000,2026)
            arrays={name:h.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy() for name,h in g.groupby('experiment')};sampled={name:sampled_metrics(y,x,weights) for name,x in arrays.items()}
            for name,ref,kind in contrasts:
                aa=arrays[name];bb=arrays[ref];delta=sampled[name]['rmse']-sampled[ref]['rmse'];point=np.sqrt(np.mean((aa-y)**2,axis=1)).mean()-np.sqrt(np.mean((bb-y)**2,axis=1)).mean();loss=np.sum((aa-y)**2-(bb-y)**2,axis=0)
                tests.append(dict(experiment=name,reference=ref,contrast=kind,protocol=pro,delta_rmse=float(point),low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
                for j,i in enumerate(ids):gains.append(dict(experiment=name,reference=ref,contrast=kind,protocol=pro,ID_POLIGONO=i,sse_gain=float(np.mean((bb[:,j]-y[j])**2-(aa[:,j]-y[j])**2)),absolute_error_gain=float(np.mean(abs(bb[:,j]-y[j])-abs(aa[:,j]-y[j])))))
    tests=pd.DataFrame(tests);assert len(tests)==96;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'paired_tests.csv',index=False);gains=pd.DataFrame(gains);gains.to_csv(D/'parcel_gains.csv',index=False)
    changes=[]
    for (name,ref,pro),g in gains[gains.contrast=='reference'].groupby(['experiment','reference','protocol']):
        total=g.sse_gain.sum();cases=g[g.ID_POLIGONO.isin(['AGC_171','AGC_015'])].sse_gain.sum();changes.append(dict(experiment=name,reference=ref,protocol=pro,total_sse_gain=total,cases_171_015_sse_gain=cases,remaining_sse_gain=total-cases,fraction_improved=float(np.mean(g.absolute_error_gain>1e-12)),fraction_worsened=float(np.mean(g.absolute_error_gain < -1e-12))))
    pd.DataFrame(changes).to_csv(D/'gain_distribution.csv',index=False)
    warning_rows=[];timings=[]
    for fi in range(65):
        checkpoint=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');timings.append(dict(index=fi,seconds=checkpoint['seconds'],warning_count=len(checkpoint['warnings'])))
        warning_rows.extend(dict(index=fi,**w) for w in checkpoint['warnings'])
    pd.DataFrame(timings).to_csv(D/'execution_times.csv',index=False)
    warnings_table=pd.DataFrame(warning_rows,columns=['index','category','message']);warnings_table.groupby(['category','message']).size().rename('count').reset_index().to_csv(D/'warning_summary.csv',index=False)
    # Replay saved branches and recover interpretable coefficient/activity diagnostics.
    branches=[];weights_rows=[];coefs=[];fallbacks=[]
    with threadpool_limits(limits=1):
        for fi in range(65):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');plan=joblib.load(OLD/'cache/execution_plan.joblib')[fi];va=np.asarray(plan['validation_positions']);assert np.array_equal(va,pack['validation_positions']);key={k:plan[k] for k in ['protocol','repeat','fold']}
            for name,r in cfg['recipes'].items():
                expert=pack['experts'][name];local=predict_base(expert['local'],va,a);corrected=predict_role(expert,va,a);model=pack['models'][name];z=model['space'].transform(a['role_frame'].iloc[va]);w=model['gate'].weights(z);pred=pack['ct3'].predict(t.iloc[va])+w*(corrected-pack['ct3'].predict(t.iloc[va]));expected=p[(p.experiment==name)&(p.protocol==key['protocol'])&(p['repeat']==key['repeat'])&(p.fold==key['fold'])].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO];np.testing.assert_allclose(pred,expected.y_pred.to_numpy(),rtol=0,atol=1e-12)
                for j,i in enumerate(va):
                    weights_rows.append(dict(**key,experiment=name,ID_POLIGONO=ids[i],expert_weight=float(w[j])))
                    for branch,values in [('local',local),('corrected',corrected)]:branches.append(dict(**key,experiment=name,branch=branch,ID_POLIGONO=ids[i],y_true=float(y[i]),y_pred=float(values[j])))
                fallbacks.append(dict(**key,experiment=name,amplitude=expert['amplitude'],fallback=expert['fallback']))
                if expert['corrector'] is not None:
                    rep=expert['corrector'].named_steps['repr'].core;coef=expert['corrector'].named_steps['model'].coef_
                    for feature,value in zip(rep.get_feature_names_out(),coef):coefs.append(dict(**key,experiment=name,feature=feature,coefficient=float(value),effective_coefficient=float(value*expert['amplitude'])))
    branch=pd.DataFrame(branches);branch.to_parquet(D/'branch_oof.parquet',index=False);bm=[]
    for (name,b,pro,re),g in branch.groupby(['experiment','branch','protocol','repeat']):bm.append(dict(experiment=name,branch=b,protocol=pro,repeat=re,**audit.stats(g)))
    write('branch_metrics',bm,['experiment','branch','protocol']);pd.DataFrame(weights_rows).to_csv(D/'weights_by_parcel.csv',index=False);pd.DataFrame(coefs).to_csv(D/'correction_coefficients.csv',index=False);pd.DataFrame(fallbacks).to_csv(D/'fallbacks_and_amplitudes.csv',index=False)
    presentation=pd.DataFrame(index=list(cfg['recipes'])+['J7_BOTH','DROP_SOIL','DROP_HISTORY_WATER','CT3','LOCAL04D'])
    for pro in PROTOCOLS:
        q=summary[summary.protocol==pro].set_index('experiment');presentation[pro]=[f'{q.loc[n,"rmse"]:.4f} / {q.loc[n,"r2"]:.4f}' for n in presentation.index]
    presentation.index.name='modelo';presentation.to_csv(D/'presentation_RMSE_R2.csv')
    delta=tests[tests.contrast=='reference'].pivot(index='experiment',columns='protocol',values='delta_rmse').reindex(index=list(cfg['recipes']),columns=PROTOCOLS)
    fig,ax=plt.subplots(figsize=(9,7));limit=max(abs(delta.to_numpy()).max(),.001);im=ax.imshow(delta,cmap='RdBu_r',vmin=-limit,vmax=limit,aspect='auto');ax.set_xticks(range(4),['Aleatoria','Perfil','Municipal','Espacial']);ax.set_yticks(range(len(delta)),delta.index)
    for i in range(len(delta)):
        for j in range(4):ax.text(j,i,f'{delta.iloc[i,j]:+.4f}',ha='center',va='center',fontsize=8)
    ax.set_title('Cambio de RMSE frente a su referencia; negativo mejora');fig.colorbar(im,ax=ax,label='t/ha');fig.tight_layout();fig.savefig(OUT/'figures/placement_rmse_changes.png',dpi=160);plt.close(fig)
    narrative=['# Señales adicionales: comparación de ubicación arquitectónica','Doce alternativas exploratorias congeladas antes del entrenamiento. ET = cambio EVI + TPI; ETN añade dinámica derivada NDVI. LOCAL amplía la Ridge local; CORRECTION amplía el corrector Elastic Net de residuos cross-fitted. CT3 y las entradas del gate físico permanecen iguales, con pesos aprendidos internamente.','## RMSE / R² por protocolo',table(presentation.reset_index()),'## Comparaciones frente a la referencia: cambio RMSE e incertidumbre',table(tests[tests.contrast=='reference']),'## ¿Dónde encajan mejor? LOCAL menos CORRECTION; negativo favorece LOCAL',table(tests[tests.contrast=='placement']),'## ¿Ayuda añadir la tercera señal? ETN menos ET; negativo favorece ETN',table(tests[tests.contrast=='third_signal']),'## Sensibilidad sin 171 y 015, sin reajuste',table(without[['experiment','protocol','rmse','mae','r2','bias']]),'## Distribución de ganancias y contribución de los dos casos',table(pd.DataFrame(changes)),'## Lectura y límites','Los parámetros y la ubicación no se seleccionaron usando el fold externo. Las características se propusieron tras examinar residuos de estos mismos datos: ninguna comparación es confirmación independiente. Holm se aplica conjuntamente a 96 contrastes. La ausencia de significancia no demuestra equivalencia. Los CSV/Excel contienen regiones, bloques, cuartiles, errores intraperfil, omisión de zonas y residuos por parcela; branch_metrics separa lo que aprende el experto de lo que conserva la mezcla. Los coeficientes del corrector están en escala estandarizada, varían entre folds y no representan efectos causales. Un peso pequeño del experto puede amortiguar tanto mejoras como deterioros. No se ajustó modelo final ni se usaron targets de PRED59.','La recomendación interpretativa se completa en la respuesta y en el documento de conclusiones tras revisar los resultados; las tablas no declaran un ganador automáticamente.']
    report=ROOT/'documentation/difficult_case_signals_results.md';report.write_text('\n\n'.join(narrative),encoding='utf-8')
    with pd.ExcelWriter(OUT/'evaluacion_ubicacion_senales.xlsx',engine='openpyxl') as writer:
        for f in sorted(D.glob('*.csv')):
            if f.stem in ['parcel_gains','weights_by_parcel']:continue
            pd.read_csv(f).to_excel(writer,sheet_name=f.stem[:31],index=False)
        for sheet in writer.book.worksheets:sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    (OUT/'evaluation_complete.json').write_text(json.dumps(dict(status='complete',recipes=12,models_in_comparison=17,outer_folds=65,oof_rows=len(p),paired_tests=len(tests),significant_holm=int((tests.p_holm<.05).sum()),reference_parity='exact',branch_replay_tolerance=1e-12,protected_sources_unchanged=True,no_PRED=True,no_final138_fit=True,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),report_sha256=hashlib.sha256(report.read_bytes()).hexdigest()),indent=2),encoding='utf-8')
    print(presentation.to_string());print(tests[tests.contrast=='reference'][['experiment','protocol','delta_rmse','p_holm']].to_string(index=False))


if __name__=='__main__':main()
