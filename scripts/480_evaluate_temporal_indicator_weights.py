"""Paired evaluation of continuous weights, direct integration and fixed controls."""
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
from src.temporal_indicator_weights import OUT,ENGINEERING,INDICATORS,PARENTS
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
spec=importlib.util.spec_from_file_location('weights_audit',ROOT/'scripts/449_j7_both_residual_audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
D=OUT/'tables';PROTOCOLS=['random','climate_profile','municipality','spatial']


def md(f):
    def cell(v):return f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v).replace('|','/')
    return '\n'.join(['| '+' | '.join(f.columns)+' |','| '+' | '.join(['---']*len(f.columns))+' |']+['| '+' | '.join(map(cell,r))+' |' for r in f.itertuples(index=False,name=None)])


def write(name,rows,keys):
    f=pd.DataFrame(rows);f.to_csv(D/(name+'_by_repeat.csv'),index=False);s=f.drop(columns='repeat',errors='ignore').groupby(keys,dropna=False).mean(numeric_only=True).reset_index();s.to_csv(D/(name+'_summary.csv'),index=False);return s


def main():
    if (OUT/'evaluation_complete.json').exists():raise FileExistsError('Preserve weight evaluation')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert (OUT/'execution_complete.json').exists();assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');ids=t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy();x=pd.read_parquet(OUT/'cache/features_train138_target_free.parquet');assert x.ID_POLIGONO.tolist()==ids
    new=pd.read_parquet(D/'predictions.parquet');prior=pd.read_parquet(ENGINEERING/'tables/predictions.parquet');keys=['experiment','protocol','repeat','fold','ID_POLIGONO','y_true','y_pred']
    for name in ['CT3','J7_BOTH']:
        z=new[new.experiment==name].merge(prior[prior.experiment==name],on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('','_prior'),validate='one_to_one');assert len(z)==1794;np.testing.assert_array_equal(z.y_pred,z.y_pred_prior);np.testing.assert_array_equal(z.y_true,z.y_true_prior)
    p=pd.concat([new[keys],prior[prior.experiment.isin(['CT3_P_RAW','J7_P_RAW'])][keys]],ignore_index=True);assert len(p)==16*1794 and not p.duplicated(['experiment','protocol','repeat','ID_POLIGONO']).any()
    p=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');p['error']=p.y_pred-p.y_true;p['squared_error']=p.error**2;p['absolute_error']=abs(p.error);p.to_parquet(D/'oof_residuals.parquet',index=False)
    cohorts=pd.read_csv(ROOT/'outputs/research/difficult_quartile/v1/tables/parcel_groups.csv');hard=cohorts[cohorts.hard_quartile].ID_POLIGONO.tolist();top=pd.read_csv(ROOT/'outputs/research/top10_difficult_parcels/v1/tables/top10_J7_random.csv').ID_POLIGONO.tolist();bins=dict(zip(ids,pd.qcut(pd.Series(y),4,duplicates='drop').astype(str)));p['target_quartile']=p.ID_POLIGONO.map(bins)
    overall=[];regions=[];omits=[];without=[];quartiles=[];pairs=[]
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;key=dict(experiment=name,protocol=pro,repeat=re);m=audit.stats(g);assert np.isclose(m['rmse']**2,m['bias_squared']+m['error_variance']);overall.append(dict(**key,**m));pairs.append(dict(**key,**pair_metrics(g)))
        for label,exclude in [('171_015',['AGC_171','AGC_015']),('top10',top),('hard35',hard)]:without.append(dict(**key,excluded=label,**audit.stats(g[~g.ID_POLIGONO.isin(exclude)])))
        for kind in ['Estado','Municipio','fold','climate_profile']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(zone),**audit.stats(h)))
                if kind!='climate_profile':omits.append(dict(**key,kind=kind,omitted=str(zone),**audit.stats(g[g[kind]!=zone])))
        for zone,h in g.groupby('target_quartile'):quartiles.append(dict(**key,zone=zone,**audit.stats(h)))
    summary=write('metrics',overall,['experiment','protocol']);write('regions',regions,['experiment','protocol','kind','zone']);write('omissions',omits,['experiment','protocol','kind','omitted']);write('without_cases',without,['experiment','protocol','excluded']);write('quartiles',quartiles,['experiment','protocol','zone']);write('intraprofile',pairs,['experiment','protocol'])
    comparisons=[]
    for base,ref in [('CT3','CT3'),('J7','J7_BOTH')]:
        for name,r in cfg['recipes'].items():
            if r['base']==base:comparisons.append((name,ref,'vs_base'))
        for kind in ['CONSTANT','SHARED','DIRECTIONAL']:comparisons.append((base+'_C4_'+kind,base+'_C4_FIXED','weight_vs_unweighted'))
        for kind in ['SHARED','DIRECTIONAL']:comparisons.append((base+'_C4_'+kind,base+'_C4_CONSTANT','variable_vs_constant'))
        comparisons += [(base+'_C4_SHARED',base+'_C4_DIRECTIONAL','weight_architecture'),(base+'_C4_INDICATORS_DIRECT',base+'_INDICATORS_DIRECT','direct_representation'),(base+'_C4_FIXED',base+'_P_RAW','fixed_vs_previous_tuned')]
    assert len(comparisons)==28
    tests=[];gains=[];groups=pd.read_csv(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/groups.csv').set_index('ID_POLIGONO').loc[ids]
    with threadpool_limits(limits=1):
        for pro,g in p.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();weights,_=cluster_weights(group,5000,2026);arrays={name:h.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy() for name,h in g.groupby('experiment')};sample={n:sampled_metrics(y,v,weights) for n,v in arrays.items()}
            for name,ref,kind in comparisons:
                aa=arrays[name];bb=arrays[ref];delta=sample[name]['rmse']-sample[ref]['rmse'];point=np.sqrt(np.mean((aa-y)**2,axis=1)).mean()-np.sqrt(np.mean((bb-y)**2,axis=1)).mean();loss=np.sum((aa-y)**2-(bb-y)**2,axis=0)
                tests.append(dict(experiment=name,reference=ref,contrast=kind,protocol=pro,delta_rmse=float(point),low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
                for j,i in enumerate(ids):gains.append(dict(experiment=name,reference=ref,contrast=kind,protocol=pro,ID_POLIGONO=i,sse_gain=float(np.mean((bb[:,j]-y[j])**2-(aa[:,j]-y[j])**2)),absolute_error_gain=float(np.mean(abs(bb[:,j]-y[j])-abs(aa[:,j]-y[j])))))
    tests=pd.DataFrame(tests);assert len(tests)==112;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'paired_tests.csv',index=False);gains=pd.DataFrame(gains);gains.to_csv(D/'parcel_gains.csv',index=False)
    distributions=[]
    for (name,ref,pro),g in gains[gains.contrast=='vs_base'].groupby(['experiment','reference','protocol']):distributions.append(dict(experiment=name,reference=ref,protocol=pro,total_sse_gain=g.sse_gain.sum(),hard35_sse_gain=g[g.ID_POLIGONO.isin(hard)].sse_gain.sum(),remaining103_sse_gain=g[~g.ID_POLIGONO.isin(hard)].sse_gain.sum(),fraction_improved=float((g.absolute_error_gain>1e-12).mean()),fraction_worsened=float((g.absolute_error_gain < -1e-12).mean())))
    pd.DataFrame(distributions).to_csv(D/'gain_distribution.csv',index=False)
    for label,join in [('regions',['protocol','kind','zone']),('omissions',['protocol','kind','omitted']),('without_cases',['protocol','excluded'])]:
        f=pd.read_csv(D/(label+'_summary.csv'));changes=[]
        for name,r in cfg['recipes'].items():
            ref='CT3' if r['base']=='CT3' else 'J7_BOTH';z=f[f.experiment==name].merge(f[f.experiment==ref],on=join,suffixes=('','_reference'),validate='one_to_one')
            for c in ['rmse','r2','mae','bias']:z['delta_'+c]=z[c]-z[c+'_reference']
            changes.append(z)
        pd.concat(changes,ignore_index=True).to_csv(D/(label+'_paired_changes.csv'),index=False)
    parcel=p.groupby(['experiment','protocol','ID_POLIGONO','Estado','Municipio','climate_profile']).agg(y_true=('y_true','first'),prediction=('y_pred','mean'),mean_error=('error','mean'),mean_absolute_error=('absolute_error','mean'),mean_squared_error=('squared_error','mean')).reset_index();parcel.to_csv(D/'parcel_errors.csv',index=False);parcel[parcel.ID_POLIGONO.isin(hard)].to_csv(D/'hard35_errors.csv',index=False)
    detail=pd.read_parquet(D/'details.parquet').merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');detail['correct_candidate_direction']=detail.candidate_delta*detail.actual_error_before < 0;detail['gain']=(detail.actual_error_before**2)-(detail.actual_error_before+detail.applied_delta)**2;detail.to_csv(D/'weights_and_corrections.csv',index=False)
    diagnostic=[];weight_regions=[]
    for (name,pro,re),g in detail.groupby(['experiment','protocol','repeat']):
        key=dict(experiment=name,protocol=pro,repeat=re);active=g[abs(g.candidate_delta)>1e-8];weighted=active[active.weight.notna()];good=weighted[weighted.correct_candidate_direction];bad=weighted[~weighted.correct_candidate_direction]
        diagnostic.append(dict(**key,n=len(g),mean_weight=g.weight.mean(),weight_below_01=float((g.weight<.1).mean()),weight_above_09=float((g.weight>.9).mean()),candidate_correct_fraction=float(active.correct_candidate_direction.mean()),weight_when_direction_correct=good.weight.mean(),weight_when_direction_wrong=bad.weight.mean(),mean_abs_correction=abs(g.applied_delta).mean(),mean_sse_gain=g.gain.mean()))
        for kind in ['Municipio','fold']:
            for zone,h in g.groupby(kind):weight_regions.append(dict(**key,kind=kind,zone=str(zone),mean_weight=h.weight.mean(),mean_candidate_delta=h.candidate_delta.mean(),mean_applied_delta=h.applied_delta.mean(),mean_sse_gain=h.gain.mean()))
    write('weight_diagnostics',diagnostic,['experiment','protocol']);write('weight_regions',weight_regions,['experiment','protocol','kind','zone'])
    coefficients=[];fallbacks=[];replay=[];timings=[];source_ledger_count=0
    with threadpool_limits(limits=1):
        for fi in range(65):
            ck=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');tr=np.asarray(pack['train_positions']);va=np.asarray(pack['validation_positions']);assert not set(tr)&set(va);rows=pd.DataFrame(ck['details']);timings.append(dict(execution_index=fi,seconds=ck['seconds']));source_ledger_count+=ck['source_ledger_count']
            for rec in ck['ledger']:assert not set(rec['train'])&(set(rec['held'])|set(rec['outer_held']))
            for name,item in pack['models'].items():
                g=rows[rows.experiment==name].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO];candidate=item['candidate'];delta=candidate.predict_delta(x.iloc[va]);np.testing.assert_allclose(delta,g.candidate_delta,atol=1e-12,rtol=0)
                if item['direct'] is not None:applied=item['direct'].predict_delta(x.iloc[va])
                elif item['weight'] is not None:
                    weight=item['weight'];w=weight.predict_weight(x.iloc[va],delta);applied=w*delta;np.testing.assert_allclose(w,g.weight,atol=1e-12,rtol=0);assert ((w>=0)&(w<=1)).all()
                    fallbacks.append(dict(execution_index=fi,experiment=name,protocol=g.protocol.iloc[0],constant_weight=weight.constant,fallbacks=';'.join(weight.fallbacks)))
                    active=np.array(INDICATORS)[weight.support]
                    for route,beta in weight.coefficients.items():
                        if beta is not None:
                            for feature,b in zip(['intercept']+active.tolist(),beta):coefficients.append(dict(execution_index=fi,experiment=name,protocol=g.protocol.iloc[0],route=route,feature=feature,coefficient=b))
                else:applied=delta
                pred=g.base_prediction.to_numpy()+applied;difference=float(abs(pred-g.prediction.to_numpy()).max());assert difference<1e-12 and max(abs(applied))<=.25+1e-12;replay.append(dict(execution_index=fi,experiment=name,max_difference=difference))
    pd.DataFrame(replay).to_csv(OUT/'audit/model_replay.csv',index=False);pd.DataFrame(fallbacks).to_csv(D/'weight_fallbacks.csv',index=False);pd.DataFrame(coefficients).to_csv(D/'weight_coefficients_by_fold.csv',index=False);pd.DataFrame(coefficients).groupby(['experiment','protocol','route','feature']).coefficient.agg(['mean','std','count']).reset_index().to_csv(D/'weight_coefficient_stability.csv',index=False);pd.DataFrame(timings).to_csv(D/'execution_times.csv',index=False)
    corr=x[INDICATORS].corr();corr.to_csv(D/'indicator_correlations.csv')
    presentation=pd.DataFrame(index=['CT3','J7_BOTH','CT3_P_RAW','J7_P_RAW']+list(cfg['recipes']))
    for pro in PROTOCOLS:
        q=summary[summary.protocol==pro].set_index('experiment');presentation[pro]=[f'{q.loc[n,"rmse"]:.4f} / {q.loc[n,"r2"]:.4f}' for n in presentation.index]
    presentation.index.name='modelo';presentation.to_csv(D/'presentation_RMSE_R2.csv')
    delta=tests[tests.contrast=='vs_base'].pivot(index='experiment',columns='protocol',values='delta_rmse').reindex(index=list(cfg['recipes']),columns=PROTOCOLS);fig,ax=plt.subplots(figsize=(10,7));limit=max(abs(delta.to_numpy()).max(),.001);im=ax.imshow(delta,cmap='RdBu_r',vmin=-limit,vmax=limit,aspect='auto');ax.set_xticks(range(4),['Aleatoria','Perfil','Municipal','Espacial']);ax.set_yticks(range(len(delta)),delta.index)
    for i in range(len(delta)):
        for j in range(4):ax.text(j,i,f'{delta.iloc[i,j]:+.4f}',ha='center',va='center',fontsize=8)
    ax.set_title('Pesos de corrección: cambio RMSE frente a base propia');fig.colorbar(im,ax=ax,label='t/ha');fig.tight_layout();fig.savefig(OUT/'figures/rmse_changes.png',dpi=160);plt.close(fig)
    report=ROOT/'documentation/temporal_indicator_weights_results.md';report.write_text('\n\n'.join(['# Indicadores y pesos continuos: resultados exploratorios','Todos los hiperparámetros fijados antes de entrenamiento. Pesos aprendidos sobre candidatos cross-fitted; ruta por signo del candidato predicho. No son probabilidades calibradas de sobre/subestimación. C4_FIXED nuevo usa alpha.01/l1.5/amplitud.5; C4previo P_RAW se conserva como benchmark distinto.','## RMSE / R²',md(presentation.reset_index()),'## Métricas completas',md(summary[['experiment','protocol','rmse','r2','mae','bias','error_sd']]),'## Peso variable frente a constante',md(tests[tests.contrast=='variable_vs_constant']),'## Ganancias por parcela',md(pd.DataFrame(distributions)),'Las112pruebas pareadas, omisiones, regiones, sin35/sin10/sin171/015, intraperfil, soporte, pesos y coeficientes están en tablas/Excel. Son resultados exploratorios del banco reutilizado. No se selecciona un nuevo Champion ni se infiere causalidad.']),encoding='utf-8')
    with pd.ExcelWriter(OUT/'evaluacion_indicadores_y_pesos.xlsx',engine='openpyxl') as writer:
        pd.DataFrame({'lectura':['RMSE t/ha / R², protocolos separados.','C4_FIXED=candidato con parámetros fijos; P_RAW=benchmark previo seleccionado internamente.','CONSTANT=un peso; SHARED=peso dependiente de indicadores; DIRECTIONAL=pesos por signo predicho.','INDICATORS_DIRECT/13directas comparan integración con ponderación.','Pesos0..1, ajuste máximo±.25t/ha; no probabilidades de clasificación.','OOF completas por repetición; no métricas medias por fold.','Etapa exploratoria; no PRED59 ni ajuste final138.']}).to_excel(writer,sheet_name='LEEME',index=False);presentation.reset_index().to_excel(writer,sheet_name='RESUMEN',index=False)
        for file in sorted(D.glob('*.csv')):
            if file.stem in ['presentation_RMSE_R2','weights_and_corrections','parcel_gains','weight_coefficients_by_fold']:continue
            pd.read_csv(file).to_excel(writer,sheet_name=file.stem[:31],index=False)
        for sheet in writer.book.worksheets:sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    (OUT/'evaluation_complete.json').write_text(json.dumps(dict(status='complete',new_recipes=12,models_replayed=len(replay),oof_rows=len(p),paired_tests=112,significant_holm=int((tests.p_holm<.05).sum()),source_ledger_exclusions_verified=source_ledger_count,protected_sources_unchanged=True,no_PRED=True,no_final138_fit=True,external_references_exact=True),indent=2),encoding='utf-8');print(presentation.to_string());print('\nHolm significant:');print(tests[tests.p_holm<.05].to_string(index=False))


if __name__=='__main__':main()
