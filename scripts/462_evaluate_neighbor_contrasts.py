"""Complete OOF evaluation, rule replay and uncertainty diagnostics; no refit."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
import pandas as pd
import joblib
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
from sklearn.tree import export_text
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.neighbor_signal_contrasts import OUT,JOINT,SIGNALS,load_assets
from src.geoc_bridge import OLD
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
spec=importlib.util.spec_from_file_location('neighbor_audit449',ROOT/'scripts/449_j7_both_residual_audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
D=OUT/'tables';PROTOCOLS=['random','climate_profile','municipality','spatial']


def md(frame):
    def cell(v):return f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v).replace('|','/')
    return '\n'.join(['| '+' | '.join(map(str,frame.columns))+' |','| '+' | '.join(['---']*len(frame.columns))+' |']+['| '+' | '.join(map(cell,row))+' |' for row in frame.itertuples(index=False,name=None)])


def write(name,rows,keys):
    d=pd.DataFrame(rows);d.to_csv(D/(name+'_by_repeat.csv'),index=False);s=d.drop(columns='repeat',errors='ignore').groupby(keys,dropna=False).mean(numeric_only=True).reset_index();s.to_csv(D/(name+'_summary.csv'),index=False);return s


def main():
    if (OUT/'evaluation_complete.json').exists():raise FileExistsError('Preserve completed evaluation')
    assert (OUT/'execution_complete.json').exists();cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    a=load_assets();t=a['a']['train'];ids=t.ID_POLIGONO.tolist();y=a['y'];p=pd.read_parquet(D/'predictions.parquet');assert len(p)==6*1794 and not p.duplicated(['experiment','protocol','repeat','ID_POLIGONO']).any();old=pd.read_parquet(JOINT/'tables/predictions.parquet')
    for name in ['CT3','J7_BOTH']:
        z=p[p.experiment==name].merge(old[old.experiment==name],on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');assert len(z)==1794;np.testing.assert_array_equal(z.y_true,z.y_true_ref);np.testing.assert_array_equal(z.y_pred,z.y_pred_ref)
    p=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');p['error']=p.y_pred-p.y_true;p['absolute_error']=abs(p.error);p['squared_error']=p.error**2;p.to_parquet(D/'oof_residuals.parquet',index=False)
    bins=dict(zip(ids,pd.qcut(pd.Series(y),4,duplicates='drop').astype(str)));p['target_quartile']=p.ID_POLIGONO.map(bins);metrics=[];regions=[];omissions=[];quartiles=[];without=[];intraprofile=[]
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.nunique()==138;key=dict(experiment=name,protocol=pro,repeat=re);m=audit.stats(g);assert np.isclose(m['rmse']**2,m['error_variance']+m['bias_squared']);metrics.append(dict(**key,**m));intraprofile.append(dict(**key,**pair_metrics(g)));without.append(dict(**key,**audit.stats(g[~g.ID_POLIGONO.isin(['AGC_171','AGC_015'])])))
        for kind in ['Estado','Municipio','fold','climate_profile']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(zone),**audit.stats(h)))
                if kind!='climate_profile':omissions.append(dict(**key,kind=kind,omitted=str(zone),**audit.stats(g[g[kind]!=zone])))
        for zone,h in g.groupby('target_quartile'):quartiles.append(dict(**key,zone=zone,**audit.stats(h)))
    summary=write('metrics',metrics,['experiment','protocol']);write('regions',regions,['experiment','protocol','kind','zone']);write('omissions',omissions,['experiment','protocol','kind','omitted']);write('quartiles',quartiles,['experiment','protocol','zone']);write('intraprofile',intraprofile,['experiment','protocol']);write('without_171_015',without,['experiment','protocol'])
    for source,keys in [('regions',['protocol','kind','zone']),('omissions',['protocol','kind','omitted']),('without_171_015',['protocol'])]:
        data=pd.read_csv(D/(source+'_summary.csv'));rows=[]
        for name in cfg['recipes']:
            z=data[data.experiment==name].merge(data[data.experiment=='J7_BOTH'],on=keys,suffixes=('','_reference'),validate='one_to_one')
            for col in ['rmse','mae','r2','bias']:z['delta_'+col]=z[col]-z[col+'_reference']
            rows.append(z)
        pd.concat(rows,ignore_index=True).to_csv(D/(source+'_paired_changes.csv'),index=False)
    parcel=p.groupby(['experiment','protocol','ID_POLIGONO','Estado','Municipio','climate_profile']).agg(y_true=('y_true','first'),prediction=('y_pred','mean'),mean_error=('error','mean'),mean_absolute_error=('absolute_error','mean'),mean_squared_error=('squared_error','mean')).reset_index();parcel.to_csv(D/'parcel_errors.csv',index=False);parcel[parcel.ID_POLIGONO.isin(['AGC_171','AGC_015'])].to_csv(D/'cases_171_015.csv',index=False)
    contrasts=[(n,'J7_BOTH','reference') for n in cfg['recipes']]+[(f'GEO_{use}',f'COMPACT_{use}','neighborhood') for use in ['ATTENUATE','RESIDUAL']]+[(f'{kind}_RESIDUAL',f'{kind}_ATTENUATE','use') for kind in ['GEO','COMPACT']];tests=[];gains=[];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids]
    with threadpool_limits(limits=1):
        for pro,g in p.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();weights,_=cluster_weights(group,5000,2026);arrays={name:h.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy() for name,h in g.groupby('experiment')};samples={name:sampled_metrics(y,v,weights) for name,v in arrays.items()}
            for name,ref,kind in contrasts:
                aa=arrays[name];bb=arrays[ref];delta=samples[name]['rmse']-samples[ref]['rmse'];point=np.sqrt(np.mean((aa-y)**2,axis=1)).mean()-np.sqrt(np.mean((bb-y)**2,axis=1)).mean();loss=np.sum((aa-y)**2-(bb-y)**2,axis=0);tests.append(dict(experiment=name,reference=ref,contrast=kind,protocol=pro,delta_rmse=float(point),low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
                for j,i in enumerate(ids):gains.append(dict(experiment=name,reference=ref,contrast=kind,protocol=pro,ID_POLIGONO=i,sse_gain=float(np.mean((bb[:,j]-y[j])**2-(aa[:,j]-y[j])**2)),absolute_error_gain=float(np.mean(abs(bb[:,j]-y[j])-abs(aa[:,j]-y[j])))))
    tests=pd.DataFrame(tests);assert len(tests)==32;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'paired_tests.csv',index=False);gains=pd.DataFrame(gains);gains.to_csv(D/'parcel_gains.csv',index=False);gainstats=[]
    for (name,pro),g in gains[gains.contrast=='reference'].groupby(['experiment','protocol']):gainstats.append(dict(experiment=name,protocol=pro,total_sse_gain=g.sse_gain.sum(),cases_sse_gain=g[g.ID_POLIGONO.isin(['AGC_171','AGC_015'])].sse_gain.sum(),fraction_improved=float(np.mean(g.absolute_error_gain>1e-12)),fraction_worsened=float(np.mean(g.absolute_error_gain < -1e-12))))
    pd.DataFrame(gainstats).to_csv(D/'gain_distribution.csv',index=False)
    detail=[];rules=[];warn=[];fallback=[];timings=[];ledger_count=0;replay_max=0.
    feature_names=[key+'_local_z' for key in SIGNALS]+[key+'_global_delta' for key in SIGNALS]
    with threadpool_limits(limits=1):
        for fi in range(65):
            ck=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');va=np.asarray(pack['validation_positions']);tr=np.asarray(pack['train_positions']);timings.append(dict(execution_index=fi,seconds=ck['seconds']));warn.extend(dict(r,execution_index=fi) for r in ck['warnings']);fallback.extend(dict(r,execution_index=fi) for r in ck['deep_support_logs'])
            for row in ck['ledger']:assert not set(row['train'])&(set(row['held'])|set(va));ledger_count+=1
            for row in ck['details']:
                assert row['position'] in set(va) and set(row['neighbors']).issubset(set(tr)) and row['position'] not in row['neighbors'];r={k:v for k,v in row.items() if k not in ['reference_medians','reference_mad','local_z','global_delta']}
                for j,key in enumerate(SIGNALS):
                    for name in ['reference_medians','reference_mad','local_z','global_delta']:r[key+'_'+name]=row[name][j]
                r['anomaly_score']=max(abs(np.array(row['local_z'])));detail.append(r)
            for name,model in pack['models'].items():
                rows=[r for r in ck['details'] if r['experiment']==name];assert [r['position'] for r in rows]==va.tolist();bp=np.array([r['base_prediction'] for r in rows]);cp=np.array([r['ct3_prediction'] for r in rows]);expected=np.array([r['prediction'] for r in rows]);z=model['contrast'].transform(va);pred=model['adjustment'].predict(z,bp,cp);diff=float(max(abs(pred-expected)));replay_max=max(replay_max,diff);assert diff<1e-12
                if name.endswith('ATTENUATE'):assert np.all(pred>=np.minimum(cp,bp)-1e-12) and np.all(pred<=np.maximum(cp,bp)+1e-12)
                else:assert max(abs(pred-bp))<=.5+1e-12
                adjustment=model['adjustment'];rules.append(dict(execution_index=fi,experiment=name,amplitude=adjustment.amplitude,depth=adjustment.depth,leaf=adjustment.leaf,values=json.dumps(adjustment.values),rule=export_text(adjustment.tree,feature_names=feature_names) if adjustment.tree is not None else 'IDENTITY: unchanged J7',fallback=adjustment.fallback))
    detail=pd.DataFrame(detail);detail.to_parquet(D/'contrast_neighbors.parquet',index=False);detail.drop(columns='neighbors').to_csv(D/'contrast_features_and_adjustments.csv',index=False);detail[detail.ID_POLIGONO.isin(['AGC_171','AGC_015'])].drop(columns='neighbors').to_csv(D/'case_contrasts_171_015.csv',index=False);pd.DataFrame(rules).to_csv(D/'rules_by_fold.csv',index=False);pd.DataFrame(timings).to_csv(D/'execution_times.csv',index=False);pd.DataFrame(warn,columns=['execution_index','category','message']).groupby(['category','message']).size().rename('count').reset_index().to_csv(D/'warning_summary.csv',index=False)
    support=pd.DataFrame(fallback)
    if len(support):support.groupby('kind').size().rename('events').reset_index().to_csv(D/'deep_support_summary.csv',index=False)
    else:pd.DataFrame(columns=['kind','events']).to_csv(D/'deep_support_summary.csv',index=False)
    risk=[];adjustments=[]
    for (name,pro,re),g in detail.groupby(['experiment','protocol','repeat']):
        difference=abs(g.adjustment);adjustments.append(dict(experiment=name,protocol=pro,repeat=re,fraction_changed=float(np.mean(difference>1e-12)),mean_absolute_adjustment=float(difference.mean()),max_absolute_adjustment=float(difference.max())))
        if not name.endswith('ATTENUATE'):continue
        h=g.merge(p[(p.experiment=='J7_BOTH')&(p.protocol==pro)&(p['repeat']==re)][['ID_POLIGONO','absolute_error','error','Estado','climate_profile']],on='ID_POLIGONO',validate='one_to_one')
        cohorts=[('overall','ALL',h),('overall','WITHOUT_171_015',h[~h.ID_POLIGONO.isin(['AGC_171','AGC_015'])])]
        cohorts += [('state',str(zone),v) for zone,v in h.groupby('Estado') if len(v)>=10]
        cohorts += [('climate_profile',str(zone),v) for zone,v in h.groupby('climate_profile') if len(v)>=10]
        for cohort_kind,cohort,v in cohorts:
            score=v.anomaly_score.to_numpy();error=v.absolute_error.to_numpy();large=error>1.;threshold=np.quantile(score,.8);top=score>=threshold;rho=float(spearmanr(score,error).statistic) if np.std(score)>1e-12 and np.std(error)>1e-12 else np.nan;rest=error[~top]
            risk.append(dict(neighborhood=name.split('_')[0],protocol=pro,repeat=re,cohort_kind=cohort_kind,cohort=cohort,n=len(v),spearman_anomaly_absolute_error=rho,auc_error_above_1=float(roc_auc_score(large,score)) if len(np.unique(large))==2 else np.nan,n_large_errors=int(large.sum()),n_top=int(top.sum()),top_mae=float(error[top].mean()),rest_mae=float(rest.mean()) if len(rest) else np.nan,top_rmse=float(np.sqrt(np.mean(error[top]**2))),rest_rmse=float(np.sqrt(np.mean(rest**2))) if len(rest) else np.nan))
    risk_summary=write('uncertainty_diagnostic',risk,['neighborhood','protocol','cohort_kind','cohort']);write('adjustment_magnitude',adjustments,['experiment','protocol']);selection=pd.read_parquet(D/'selection.parquet');selection.to_csv(D/'selection_by_fold.csv',index=False);selection.groupby(['experiment','protocol','amplitude','depth','leaf']).size().rename('folds').reset_index().to_csv(D/'selection_counts.csv',index=False)
    presentation=pd.DataFrame(index=['J7_BOTH','CT3']+list(cfg['recipes']))
    for pro in PROTOCOLS:
        q=summary[summary.protocol==pro].set_index('experiment');presentation[pro]=[f'{q.loc[name,"rmse"]:.4f} / {q.loc[name,"r2"]:.4f}' for name in presentation.index]
    presentation.index.name='modelo';presentation.to_csv(D/'presentation_RMSE_R2.csv')
    delta=tests[tests.contrast=='reference'].pivot(index='experiment',columns='protocol',values='delta_rmse').reindex(index=list(cfg['recipes']),columns=PROTOCOLS);fig,ax=plt.subplots(figsize=(9,4));limit=max(abs(delta.to_numpy()).max(),.001);im=ax.imshow(delta,cmap='RdBu_r',vmin=-limit,vmax=limit,aspect='auto');ax.set_xticks(range(4),['Aleatoria','Perfil','Municipal','Espacial']);ax.set_yticks(range(4),delta.index)
    for i in range(4):
        for j in range(4):ax.text(j,i,f'{delta.iloc[i,j]:+.4f}',ha='center',va='center')
    ax.set_title('Contrastes vecinales: cambio RMSE respecto a J7; negativo mejora');fig.colorbar(im,ax=ax,label='t/ha');fig.tight_layout();fig.savefig(OUT/'figures/rmse_changes.png',dpi=160);plt.close(fig)
    report=ROOT/'documentation/neighbor_signal_contrasts_results.md';narrative=['# Contrastes de señales respecto a vecinos: resultados','Cuatro alternativas congeladas y dos referencias exactas, mismas 65 particiones. GEO/COMPACT indican los vecinos; ATTENUATE reduce J7 hacia CT3; RESIDUAL añade un ajuste contraído y limitado a ±0.5 t/ha. Cortes y parámetros seleccionados internamente. Resultados exploratorios, sin promoción automática.','## RMSE / R²',md(presentation.reset_index()),'## RMSE, MAE, sesgo y dispersión',md(summary[['experiment','protocol','rmse','mae','r2','bias','error_sd','p95_absolute']]),'## Comparaciones pareadas: 32 contrastes con Holm conjunto',md(tests),'## Diagnóstico de incertidumbre de J7, sin usar correcciones',md(risk_summary),'La AUC y el quintil son diagnósticos descriptivos del error observado, no probabilidades operativas ni intervalos calibrados. Las relaciones de signo, error absoluto y ajuste se interpretan por separado.','## Distribución de ganancias',md(pd.DataFrame(gainstats)),'## Integridad y límites',f'Replay máximo {replay_max:.3g}; {ledger_count} exclusiones verificadas. Las referencias externas coinciden exactamente. Las calibraciones profundas pueden requerir respaldos por soporte territorial, registrados en deep_support_summary y audit/deep_support_logs.json. No se sustituyó ningún protocolo por aleatorio. El experimento no utiliza PRED59 ni ajusta modelo final138.','Los CSV y Excel incluyen análisis sin 171/015, omisiones de zonas, cuartiles, intraperfil, reglas por fold, residuos por parcela, predicciones base y ajustes. La interpretación y recomendación están en neighbor_signal_contrasts_conclusions.md.']
    report.write_text('\n\n'.join(narrative),encoding='utf-8')
    with pd.ExcelWriter(OUT/'evaluacion_contrastes_vecinales.xlsx',engine='openpyxl') as writer:
        pd.DataFrame({'lectura':['RMSE t/ha / R² en RESUMEN; error=predicho−observado.','GEO/COMPACT: vecinos geográficos o en compact4; k24 con empates.','ATTENUATE reduce J7 hacia CT3; RESIDUAL añade corrección acotada.','Calibración interna anidada; nunca vecinos ni targets de validación para entrenar.','Resultados exploratorios; respaldos por soporte territorial registrados.','Vecinos completos en contrast_neighbors.parquet; no PRED59 ni modelo final.']}).to_excel(writer,sheet_name='LEEME',index=False)
        presentation.reset_index().to_excel(writer,sheet_name='RESUMEN',index=False)
        for f in sorted(D.glob('*.csv')):
            if f.stem in ['contrast_features_and_adjustments','parcel_gains','presentation_RMSE_R2']:continue
            pd.read_csv(f).to_excel(writer,sheet_name=f.stem[:31],index=False)
        for sheet in writer.book.worksheets:sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());result=dict(status='complete',recipes=4,models=6,folds=65,oof_rows=len(p),paired_tests=32,significant_holm=int((tests.p_holm<.05).sum()),reference_parity='exact',replay_max_difference=replay_max,ledger_exclusions_verified=ledger_count,protected_sources_unchanged=True,no_PRED=True,no_final138_fit=True,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());(OUT/'evaluation_complete.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(presentation.to_string());print(risk_summary.to_string(index=False));print('Significant Holm:',result['significant_holm'])


if __name__=='__main__':main()
