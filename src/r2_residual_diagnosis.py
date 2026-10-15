"""Read-only municipal residual support audit; no external OOF used for fitting."""
from pathlib import Path
import json,time
import numpy as np,pandas as pd
from matplotlib import pyplot as plt
from src.compact_ensemble import ROOT,OLD,ID,Y,sha
from src.territorial_mixtures import OUT as R2OUT

OUT=ROOT/'outputs/research/r2_residual_diagnosis/v1'
BOOTSTRAPS=4000
SEED=2026

def stability(values,groups,seed=SEED,n_boot=BOOTSTRAPS):
    """Frozen-residual resampling; NOT uncertainty of full retrained pipelines."""
    a=np.asarray(values,float);g=np.asarray(groups);unique=np.unique(g);rng=np.random.default_rng(seed)
    parcel=np.mean(a[rng.integers(0,len(a),(n_boot,len(a)))],axis=1)
    sums=np.array([a[g==z].sum() for z in unique]);counts=np.array([sum(g==z) for z in unique])
    ix=rng.integers(0,len(unique),(n_boot,len(unique)));cluster=sums[ix].sum(axis=1)/counts[ix].sum(axis=1)
    result={}
    for name,dist in [('parcel',parcel),('profile',cluster)]:
        result.update({name+'_low':float(np.quantile(dist,.025)),name+'_high':float(np.quantile(dist,.975)),name+'_fraction_positive':float(np.mean(dist>0))})
    return result

def omissions(values,groups):
    a=np.asarray(values,float);g=np.asarray(groups);result=[]
    for k in [1,3,5]:
        if len(a)<=k:continue
        for mode in ['largest_absolute','largest_positive','largest_negative']:
            order=np.argsort(-abs(a)) if mode=='largest_absolute' else np.argsort(-a if mode=='largest_positive' else a)
            keep=np.ones(len(a),bool);keep[order[:k]]=False
            result.append(dict(omission=mode,k=k,n_remaining=int(keep.sum()),remaining_residual_mean=float(a[keep].mean())))
    for group in np.unique(g):
        keep=g!=group
        if keep.any():result.append(dict(omission='profile',k=int(sum(~keep)),profile=str(group),n_remaining=int(keep.sum()),remaining_residual_mean=float(a[keep].mean())))
    return result

def prepare():
    if OUT.exists():raise FileExistsError('Previous/partial versions preserved')
    for d in ['tables','audit','report','figures']:(OUT/d).mkdir(parents=True)
    paths=[R2OUT/'manifest.json',R2OUT/'tables/oof_predictions.parquet',OLD/'cache/train138.parquet',R2OUT/'frozen_design.json',R2OUT/'audit/implementation_fix.json',ROOT/'documentation/territorial_mixtures.md',Path(__file__)]
    hashes={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
    pd.DataFrame([dict(path=p,sha256=h) for p,h in hashes.items()]).to_csv(OUT/'audit/protected_inputs.csv',index=False)
    config=dict(stage='read-only residual diagnosis before optional calibration',residual='observed - R2 OOF; positive means underprediction',n_labels=138,random_repeats='average residual per parcel across10 repeats before resampling; never treat1380 as independent labels',resampling='4000 parcel and climate-profile cluster draws; percentile95 stability ranges, frozen predictions, no model retraining or formal significance',seed=SEED,minimum_support=dict(n_parcels=15,n_profiles=2,source='same support minimum as preceding R2'),omissions='remove1/3/5 largest absolute, positive and negative residuals; leave each whole profile; descriptive sensitivity without refit',conditional_calibration='advance only with supported municipality, direction shared random/profile, stability ranges both excluding zero, no sign reversal on absolute-error/profile omissions, >=80percent random-repeat sign agreement; exploratory screening on reused labels, not independent confirmation',calibration_if_supported='all municipalities screened same way; proposed lambda infinity/150/50/15, training-only nested R2 OOF targets and internally selected regularization, unseen municipality=0; NOT fit from archived external OOF',prospective_caveat='initial archived means and influence examples already inspected; this is an exploratory transparent audit, not a preregistered discovery test; no threshold picked to optimize external metrics',no_models_fitted=True,no_new_oof_predictions=True,no_champion_change=True,no_PRED=True)
    (OUT/'frozen_diagnostic_design.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    (OUT/'report/design.md').write_text('# Diagnóstico previo a calibración municipal de R2\n\nResiduos OOF observados menos predichos. Repeticiones aleatorias se colapsan por parcela para remuestreo. Soporte previo15 parcelas/2 perfiles. Remuestreo por parcelas y clusters de perfil, omisiones de casos y perfiles, consistencia de signo entre aleatoria y perfil. Intervalos de estabilidad de residuos fijos, sin reajustar modelos; no confirmación independiente ni prueba de ausencia de efecto. La primera lectura de medias ya ocurrió: criterios exploratorios explícitos, no registro previo a toda inspección.\n\nSolo si existe soporte y estabilidad se justificaría una calibración anidada separada. Nunca ajustar con OOF externas archivadas o recuperar residuos de otros folds cuyos entrenamientos incluyan la evaluación actual. La regularización y selección completas de R2 también deben respetar las exclusiones del target residual; no basta excluirlo únicamente del ajuste de expertos.\n',encoding='utf-8')

def run():
    prepare();start=time.perf_counter();t=pd.read_parquet(OLD/'cache/train138.parquet');p=pd.read_parquet(R2OUT/'tables/oof_predictions.parquet');p=p[p.experiment.eq('R2')].merge(t[[ID,'Estado','Municipio','climate_profile']],on=ID,validate='many_to_one')
    assert len(p)==1794;p['residual']=p.y_true-p.y_pred
    repeat=[]
    for (pro,re,st,mun),g in p.groupby(['protocol','repeat','Estado','Municipio']):repeat.append(dict(protocol=pro,repeat=re,Estado=st,Municipio=mun,n=len(g),residual_mean=float(g.residual.mean()),residual_sd=float(g.residual.std()),rmse=float(np.sqrt(np.mean(g.residual**2)))))
    pd.DataFrame(repeat).to_csv(OUT/'tables/municipal_repeat.csv',index=False)
    unit=p.groupby(['protocol','Estado','Municipio',ID,'climate_profile'],as_index=False).agg(y_true=('y_true','first'),y_pred=('y_pred','mean'),residual=('residual','mean'),n_repeats=('repeat','size'))
    unit.to_parquet(OUT/'tables/parcel_residuals.parquet',index=False)
    stats=[];leave=[]
    for (pro,st,mun),g in unit.groupby(['protocol','Estado','Municipio']):
        r=g.residual.to_numpy();groups=g.climate_profile.to_numpy();row=dict(protocol=pro,Estado=st,Municipio=mun,n_parcels=len(g),n_profiles=len(set(groups)),residual_mean=float(r.mean()),residual_sd=float(r.std(ddof=1)) if len(r)>1 else np.nan,median=float(np.median(r)),fraction_positive=float(np.mean(r>0)),**stability(r,groups))
        row['supported']=len(g)>=15 and len(set(groups))>=2
        if pro=='random':
            q=p[(p.protocol==pro)&(p.Estado==st)&(p.Municipio==mun)].groupby('repeat').residual.mean();row['repeat_sign_agreement']=float(np.mean(np.sign(q)==np.sign(r.mean())))
        stats.append(row)
        leave.extend(dict(protocol=pro,Estado=st,Municipio=mun,original_mean=float(r.mean()),**z) for z in omissions(r,groups))
    stats=pd.DataFrame(stats);leave=pd.DataFrame(leave);stats.to_csv(OUT/'tables/municipal_stability.csv',index=False);leave.to_csv(OUT/'tables/influence_sensitivity.csv',index=False)
    decisions=[]
    for (st,mun),g in stats.groupby(['Estado','Municipio']):
        a=g[g.protocol=='random'].iloc[0];b=g[g.protocol=='climate_profile'].iloc[0];l=leave[(leave.protocol=='random')&(leave.Estado==st)&(leave.Municipio==mun)];absolute=l[l.omission=='largest_absolute'];profiles=l[l.omission=='profile'];mean=a.residual_mean
        excludes=bool((a.parcel_low>0 and a.profile_low>0) or (a.parcel_high<0 and a.profile_high<0))
        omissions_ok=bool(np.all(np.sign(absolute.remaining_residual_mean)==np.sign(mean)) and np.all(np.sign(profiles.remaining_residual_mean)==np.sign(mean)))
        agreement=bool(np.sign(mean)==np.sign(b.residual_mean))
        proceed=bool(a.supported and excludes and omissions_ok and agreement and a.repeat_sign_agreement>=.8)
        decisions.append(dict(Estado=st,Municipio=mun,n_parcels=int(a.n_parcels),n_profiles=int(a.n_profiles),supported=bool(a.supported),random_residual_mean=float(mean),profile_residual_mean=float(b.residual_mean),repeat_sign_agreement=float(a.repeat_sign_agreement),both_stability_ranges_exclude_zero=excludes,absolute_and_profile_omissions_keep_sign=omissions_ok,random_and_profile_same_sign=agreement,calibration_justified=proceed))
    decisions=pd.DataFrame(decisions);decisions.to_csv(OUT/'tables/calibration_support_decision.csv',index=False)
    supported=stats[(stats.protocol=='random')&stats.supported].sort_values('Municipio');fig,axes=plt.subplots(1,2,figsize=(12,4))
    for ax,kind in zip(axes,['parcel','profile']):
        y=supported.residual_mean.to_numpy();low=supported[kind+'_low'].to_numpy();high=supported[kind+'_high'].to_numpy();ax.errorbar(np.arange(len(y)),y,yerr=np.vstack([y-low,high-y]),fmt='o',capsize=4);ax.axhline(0,color='gray',linewidth=1);ax.set_xticks(np.arange(len(y)),supported.Municipio,rotation=15);ax.set_title('Remuestreo '+('por parcela' if kind=='parcel' else 'por perfil climático'));ax.set_ylabel('Observado − R2 (t/ha)')
    fig.tight_layout();fig.savefig(OUT/'figures/supported_municipal_bias.png',dpi=160);plt.close(fig)
    eligible=decisions[decisions.calibration_justified]
    lines=['# Residuos municipales de R2: investigación previa a calibración','', '## Resultado del diagnóstico','', '```text',decisions.to_string(index=False),'```','', '## Estabilidad','', '```text',stats[stats.protocol=='random'][['Municipio','n_parcels','n_profiles','residual_mean','parcel_low','parcel_high','profile_low','profile_high','supported']].to_string(index=False),'```','', 'Los intervalos son rangos descriptivos de remuestreo de residuos y predicciones congeladas; no incluyen incertidumbre de volver a entrenar o de una campaña nueva. Repeticiones reutilizan las mismas138 etiquetas: acuerdo de signos no equivale a diez muestras independientes.','', '## Decisión','', ('No hay municipio con soporte y estabilidad suficiente bajo este diagnóstico. No se ejecuta calibrador: la condición de avance no se satisface. Se conserva R2 y no se producen nuevas métricas predictivas. Un resultado diagnóstico débil no demuestra ausencia de sesgo real.' if eligible.empty else 'Existen municipios con soporte para plantear una calibración anidada separada. El diagnóstico no estima su mejora predictiva; no ajustar correcciones directamente de estas OOF externas.'),'', 'La media por municipio nunca se convierte aquí en una corrección desplegable. Municipio retenido completo no tiene etiquetas para aprender su ajuste; usaría cero. Una constante municipal tampoco cambia diferencias entre parcelas del mismo municipio, por lo que no resuelve heterogeneidad intraperfil.','', '## Reproducibilidad','', 'No se ajustó ningún modelo, no se generaron nuevas OOF, PRED o cambios al Champion. Se preservaron fuentes por hash; semilla2026 y4000 remuestreos. Las decisiones son exploratorias y la inspección inicial de medias precedió al diseño de este audit, documentado explícitamente.']
    (OUT/'report/informe.md').write_text('\n'.join(lines),encoding='utf-8')
    for r in pd.read_csv(OUT/'audit/protected_inputs.csv').itertuples():assert sha(ROOT/r.path)==r.sha256
    (OUT/'manifest.json').write_text(json.dumps(dict(status='diagnostic_complete',n_eligible_municipalities=len(eligible),conditional_calibration_required=bool(len(eligible)),new_model_fits=0,new_oof_predictions=0,no_PRED=True,no_champion_change=True,wall_seconds=time.perf_counter()-start,artifacts={f.relative_to(ROOT).as_posix():sha(f) for f in OUT.rglob('*') if f.is_file() and f.name!='manifest.json'}),indent=2),encoding='utf-8')
    print(decisions.to_string(index=False));print(stats[stats.protocol=='random'][['Municipio','residual_mean','parcel_low','parcel_high','profile_low','profile_high']].to_string(index=False))
