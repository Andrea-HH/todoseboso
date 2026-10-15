"""Complete OOF aggregation and local/regional diagnostics, no extra fits."""
from pathlib import Path
import json
import numpy as np,pandas as pd,joblib
from .execution import ROOT,OUT,ID,TARGET,LAI,load,base,sha
from .models import SPECS
from src.family_8.research import pair_metrics

def metrics(g):
    e=g.y_pred.to_numpy()-g.y_true.to_numpy()
    return dict(n=len(g),RMSE=float(np.sqrt(np.mean(e*e))),MAE=float(abs(e).mean()),bias=float(e.mean()))
def metric_summary(p):
    rows=[]
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g[ID].nunique()==138
        rows.append(dict(experiment=name,protocol=pro,repeat=re,**metrics(g)))
    d=pd.DataFrame(rows);return d,d.groupby(['experiment','protocol'])[['RMSE','MAE','bias']].mean().reset_index()
def table(d):
    d=d.fillna('no evaluable').copy()
    for c in d:d[c]=d[c].map(lambda v:f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v))
    return '| '+' | '.join(d.columns)+' |\n|'+'---|'*len(d.columns)+'\n'+'\n'.join('| '+' | '.join(v)+' |' for v in d.to_numpy())

def build(wall):
    t,splits,groups=load();plans=joblib.load(OUT/'cache/execution_plan.joblib');packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    p=pd.DataFrame([r for pack in packs for r in pack['predictions']]);assert len(p)==8970
    p.to_parquet(OUT/'tables/oof_predictions.parquet',index=False);p.to_csv(OUT/'tables/oof_predictions.csv',index=False)
    for key,name in [('registry','corrector_registry'),('tuning','inner_selection'),('rules','tree_rules'),('leaves','tree_leaf_support'),('provenance','residual_provenance')]:pd.DataFrame([r for pack in packs for r in pack[key]]).to_csv(OUT/f'tables/{name}.csv',index=False)
    pd.DataFrame([r for pack in packs for r in pack['targets']]).to_parquet(OUT/'tables/honest_training_residuals.parquet',index=False)
    ref=pd.read_parquet(OUT/'cache/reference_oof.parquet');a=p[p.experiment.eq('M0')].merge(ref,on=['protocol','repeat','fold',ID],suffixes=('_new','_old'),validate='one_to_one');np.testing.assert_allclose(a.y_pred_new,a.y_pred_old,atol=1e-12)
    repeats,summary=metric_summary(p);repeats.to_csv(OUT/'tables/metrics_repeat.csv',index=False);summary.to_csv(OUT/'tables/metrics_summary.csv',index=False)
    dominant=t[t.Municipio.eq('Chignahuapan')].groupby('climate_profile').size().nlargest(2).index.tolist()
    joined=p.merge(t[[ID,'Estado','Municipio','climate_profile']],on=ID,validate='many_to_one');subsets={'all':lambda g:np.ones(len(g),bool),'Chignahuapan':lambda g:g.Municipio.eq('Chignahuapan'),'outside_Chignahuapan':lambda g:g.Municipio.ne('Chignahuapan'),'omit_dominant_profiles':lambda g:~g.climate_profile.isin(dominant)}
    local=[];regions=[];pairs=[]
    for (name,pro,re),g in joined.groupby(['experiment','protocol','repeat']):
        for label,maskfn in subsets.items():
            q=g.loc[maskfn(g)];local.append(dict(experiment=name,protocol=pro,repeat=re,subset=label,**pair_metrics(q)))
            for (fold,profile),h in q.groupby(['fold','climate_profile']):
                if len(h)<2:continue
                h=h.sort_values(ID);ii,jj=np.triu_indices(len(h),1);obs=h.y_true.to_numpy();pred=h.y_pred.to_numpy();corr=h.correction.to_numpy();ids=h[ID].to_numpy()
                for i,j in zip(ii,jj):pairs.append(dict(experiment=name,protocol=pro,repeat=re,fold=fold,profile=profile,subset=label,id_a=ids[i],id_b=ids[j],observed_difference=float(obs[i]-obs[j]),predicted_difference=float(pred[i]-pred[j]),correction_difference=float(corr[i]-corr[j]),changed=abs(corr[i]-corr[j])>1e-10,error=float((obs[i]-obs[j])-(pred[i]-pred[j]))))
        for field in ['Estado','Municipio','fold']:
            for group,q in g.groupby(field):regions.append(dict(experiment=name,protocol=pro,repeat=re,group_type=field,group=group,**metrics(q)))
    l=pd.DataFrame(local);l.to_csv(OUT/'tables/intraprofile_repeat.csv',index=False);ls=l.groupby(['experiment','protocol','subset']).mean(numeric_only=True).drop(columns='repeat').reset_index();ls.to_csv(OUT/'tables/intraprofile_summary.csv',index=False)
    pair=pd.DataFrame(pairs);pair.to_parquet(OUT/'tables/same_model_pairs.parquet',index=False)
    pair.groupby(['experiment','protocol','subset']).changed.mean().reset_index().to_csv(OUT/'tables/fraction_pairs_changed.csv',index=False)
    regional=pd.DataFrame(regions);regional.to_csv(OUT/'tables/regional_repeat.csv',index=False);regional.groupby(['experiment','protocol','group_type','group']).mean(numeric_only=True).drop(columns='repeat').to_csv(OUT/'tables/regional_summary.csv')
    paired=[];omissions=[];parcel=[]
    references={'M1_LAI':['M0'],'M1_Z':['M0','M1_LAI'],'M2_Z':['M0','M1_Z','C_CONTEXT'],'C_CONTEXT':['M0']}
    for name,refs in references.items():
        for reference in refs:
            a=joined[joined.experiment.eq(name)];b=joined[joined.experiment.eq(reference)][['protocol','repeat','fold',ID,'y_pred']].rename(columns={'y_pred':'reference_prediction'});q=a.merge(b,on=['protocol','repeat','fold',ID],validate='one_to_one');q['gain_squared']=(q.reference_prediction-q.y_true)**2-(q.y_pred-q.y_true)**2;q['gain_absolute']=abs(q.reference_prediction-q.y_true)-abs(q.y_pred-q.y_true)
            for (pro,re),g in q.groupby(['protocol','repeat']):
                r=g.copy();r.y_pred=r.reference_prediction;ma=metrics(g);mb=metrics(r)
                paired.append(dict(experiment=name,reference=reference,protocol=pro,repeat=re,delta_RMSE=ma['RMSE']-mb['RMSE'],delta_MAE=ma['MAE']-mb['MAE'],delta_bias=ma['bias']-mb['bias'],fraction_absolute_improved=float((g.gain_absolute>0).mean()),net_SSE_gain=float(g.gain_squared.sum())))
                cases=[('all',np.ones(len(g),bool))]+[(f'omit_municipality:{v}',g.Municipio.ne(v)) for v in g.Municipio.unique()]+[(f'omit_fold:{v}',g.fold.ne(v)) for v in g.fold.unique()]
                for count in [1,5,10]:cases.append((f'omit_top{count}_beneficiaries',~g.index.isin(g.nlargest(count,'gain_squared').index)))
                for label,mask in cases:
                    a=g.loc[mask].copy();b=a.copy();b.y_pred=b.reference_prediction;ma=metrics(a);mb=metrics(b)
                    omissions.append(dict(experiment=name,reference=reference,protocol=pro,repeat=re,subset=label,n=len(a),delta_RMSE=ma['RMSE']-mb['RMSE'],delta_MAE=ma['MAE']-mb['MAE']))
            q['reference']=reference;parcel.append(q)
    pd.DataFrame(paired).to_csv(OUT/'tables/paired_metrics_repeat.csv',index=False);pd.DataFrame(paired).groupby(['experiment','reference','protocol']).mean(numeric_only=True).drop(columns='repeat').to_csv(OUT/'tables/paired_metrics_summary.csv')
    pd.DataFrame(omissions).to_csv(OUT/'tables/omission_sensitivity.csv',index=False);pd.concat(parcel).to_parquet(OUT/'tables/parcel_gains.parquet',index=False)
    cuts=t[TARGET].quantile([.25,.5,.75]).to_numpy();q=joined.copy();q['quartile']=np.searchsorted(cuts,q.y_true,side='left')+1;quart=[]
    for (name,pro,re,k),g in q.groupby(['experiment','protocol','repeat','quartile']):quart.append(dict(experiment=name,protocol=pro,repeat=re,quartile=k,**metrics(g)))
    pd.DataFrame(quart).groupby(['experiment','protocol','quartile']).mean(numeric_only=True).drop(columns='repeat').to_csv(OUT/'tables/target_quartile_metrics.csv')
    tree_pair_attribution=[];temporal=[];support=[];known=[];replay=[]
    perturb=pd.read_csv(OUT/'cache/temporal_sensitivity.csv');perturb=perturb[(perturb.sensor=='S2')&(perturb['index']=='lai_promedio')&(perturb.statistic=='runup_start_day')]
    coverage=pd.read_csv(OUT/'cache/temporal_coverage.csv');coverage=coverage[(coverage.sensor=='S2')&(coverage['index']=='lai_promedio')].set_index(ID)
    for i,plan in enumerate(plans):
        va=plan['validation_positions'];tr=plan['train_positions'];frame=t.iloc[va].copy();train=t.iloc[tr];threshold=float(coverage.loc[train[ID]].n_dates.quantile(.25))
        for name in SPECS:
            pack=joblib.load(OUT/'models'/f'{name}_{i:02d}_outer.joblib');model=pack['model'];amplitude=pack['amplitude'];b=base(pack['base_key']).predict(frame);raw=model.predict(frame) if model else np.zeros(len(frame));pred=b+amplitude*raw
            q=p[(p.experiment==name)&(p.protocol==plan['protocol'])&(p['repeat']==plan['repeat'])&(p.fold==plan['fold'])].set_index(ID)
            diff=float(np.max(abs(pred-q.y_pred.reindex(frame[ID]))));assert diff<1e-10;replay.append(dict(experiment=name,outer_index=i,max_abs_difference=diff))
            for j,r in frame.iterrows():
                known.append(dict(experiment=name,protocol=plan['protocol'],repeat=plan['repeat'],ID_POLIGONO=r[ID],profile_known=bool(r.climate_profile in set(train.climate_profile)),y_true=r[TARGET],y_pred=float(pred[list(frame.index).index(j)])))
            for label,mask in [('low_dates',coverage.loc[frame[ID]].n_dates.to_numpy()<=threshold),('higher_dates',coverage.loc[frame[ID]].n_dates.to_numpy()>threshold)]:
                if mask.any():g=pd.DataFrame({'y_true':frame[TARGET].to_numpy()[mask],'y_pred':pred[mask]});support.append(dict(experiment=name,protocol=plan['protocol'],repeat=plan['repeat'],fold=plan['fold'],temporal_group=label,threshold_train=threshold,**metrics(g),mean_abs_correction=float(np.mean(abs(amplitude*raw[mask])))))
            if model:
                for case,part in perturb[perturb[ID].isin(frame[ID])].groupby('case'):
                    alt=frame.copy();alt[LAI]=alt[ID].map(part.set_index(ID).perturbed);delta=amplitude*(model.predict(alt)-raw)
                    temporal.append(dict(experiment=name,protocol=plan['protocol'],repeat=plan['repeat'],fold=plan['fold'],case=case,mean_abs_prediction_change=float(np.mean(abs(delta))),max_abs_prediction_change=float(np.max(abs(delta))),fraction_changed=float((abs(delta)>1e-10).mean())))
            if model and model.kind=='tree':
                tree=model.model;paths=tree.decision_path(model.preprocess.transform(frame));leaves=model.leaves(frame)
                for profile,h in frame.groupby('climate_profile'):
                    ix=[frame.index.get_loc(j) for j in h.index];sep=0;lai_first=0;context_first=0;n_pairs=len(ix)*(len(ix)-1)//2
                    for a in range(len(ix)):
                        for b in range(a+1,len(ix)):
                            aa=ix[a];bb=ix[b]
                            if abs(raw[aa]-raw[bb])<=1e-10:continue
                            sep+=1;common=set(paths[aa].indices)&set(paths[bb].indices);node=max(common);feature=model.names[tree.tree_.feature[node]]
                            if feature==LAI:lai_first+=1
                            else:context_first+=1
                    tree_pair_attribution.append(dict(experiment=name,protocol=plan['protocol'],repeat=plan['repeat'],fold=plan['fold'],profile=profile,n_parcels=len(ix),n_pairs=n_pairs,separated_pairs=sep,first_separation_LAI=lai_first,first_separation_context=context_first,n_leaves=len(set(leaves[ix]))))
    pd.DataFrame(replay).to_csv(OUT/'audit/model_replay.csv',index=False);pd.DataFrame(temporal).to_csv(OUT/'tables/fixed_model_temporal_sensitivity.csv',index=False);pd.DataFrame(support).to_csv(OUT/'tables/temporal_support_errors.csv',index=False);pd.DataFrame(tree_pair_attribution).to_csv(OUT/'tables/tree_pair_separation.csv',index=False)
    known=pd.DataFrame(known);knownrows=[]
    for (name,pro,re,flag),g in known.groupby(['experiment','protocol','repeat','profile_known']):knownrows.append(dict(experiment=name,protocol=pro,repeat=re,profile_known=flag,**metrics(g)))
    pd.DataFrame(knownrows).to_csv(OUT/'tables/known_new_profiles.csv',index=False)
    registry=pd.read_csv(OUT/'tables/corrector_registry.csv');base_registry=pd.read_csv(OUT/'tables/base_fit_registry.csv');amp=registry.groupby(['experiment','protocol']).amplitude.agg(['mean',lambda a:float((a==0).mean())]).reset_index().rename(columns={'<lambda_0>':'fraction_zero'})
    amp.to_csv(OUT/'tables/amplitude_summary.csv',index=False)
    total_fits=int(base_registry.fit_count.sum()+sum(pack['n_corrector_fits'] for pack in packs))
    lines=['# Corrección residual condicional sobre C-T3','', 'Se ejecutaron cinco series de OOF sobre65folds: M0referencia, M1_LAI, M1_Zmatched, M2_ZyC_CONTEXT. Residuos internos honestos con selección recursiva de base y cachés por IDs/CVexactos. Correcciones centradasTRAIN, amplitud0/.25/.5 y selección sobreOOFinterna completa. No modelo final138ni59PRED.','',table(summary),'', '## Amplitudes y ausencia de corrección','',table(amp),'', '## Diferencias intraperfil, todos los perfiles elegibles','',table(ls[ls.subset.eq('all')][['experiment','protocol','n_parcels','n_profiles','pair_weighted_RMSE','equal_profile_RMSE','pair_weighted_MAE','equal_profile_MAE']]),'', 'Los pares comparten modelo externo, nunca se mezclan predicciones de folds diferentes para atribuir diferenciación. Chignahuapan, fuera y omisiones de perfiles dominantes están separados; parejas y10repeticiones son dependientes. Las métricas absolutas usan138OOFcompletas por repetición y luego media aleatoria10, no mediasRMSEporfold.','', 'M1_ZvsM2_Zaísla un cambio de arquitectura con idénticas entradas; M1_LAIvsM1_Zno aísla arquitectura. C_CONTEXTpermite identificar recalibración del núcleo. Ganar a ambos no demuestra interacción frente a una función aditiva: H3es exploratoria, con diagnóstico de caminos/primera separación porLAI. No se prueba causalidad.','', 'Reglas, umbrales físicos, soporte de hojas, amplitudes, discrepancia entre basecrossfit/refit, omisiones sin refits, errores pareados por parcela, cuartiles posteriores, perfiles nuevos/conocidos y sensibilidad a fechas se guardan en tablas. No se reajustaron modelos al omitir regiones o perturbarfechas. No se forzaron divisiones cuandoleaf15/25no permite partir el entrenamiento. Soporte por perfiles es diagnóstico, no un filtro geográfico retrospectivo.','', f'Ajustes científicos: {total_fits}; tiempo principal: {wall:.1f}s. Máximo replay de correctores: {max(r["max_abs_difference"] for r in replay):.3g}t/ha. Los65modelosM0reprodujeron lasOOFarchivadas. Advertencias de base registradas; la regla original detiene anteConvergenceWarning.','', 'Los márgenes0.01t/hason exploratorios, no significación ni relevancia económica demostrada. Interpretar conjuntamente errores absolutos, ambos pesos intraperfil, municipios/espacio, concentración y corrección0. Las mismas138etiquetas se han reutilizado extensamente; OOFanidada correcta no aporta confirmación independiente. No promover un Champion ni rechazar todas las interacciones si este árbol no mejora.']
    (OUT/'report/technical_report.md').write_text('\n'.join(lines),encoding='utf-8')
    # Explicit, prospective exploratory gates, with no external winner selection.
    decisions=[];lookup=summary.set_index(['experiment','protocol']);lp=ls[ls.subset.eq('all')].set_index(['experiment','protocol'])
    for name in SPECS:
        deltas=[lookup.loc[(name,pro),m]-lookup.loc[('M0',pro),m] for pro in ['random','climate_profile','municipality','spatial'] for m in ['RMSE','MAE']]
        local_gains=[lp.loc[('M0',pro),m]-lp.loc[(name,pro),m] for pro in ['random','climate_profile','municipality','spatial'] for m in ['pair_weighted_RMSE','equal_profile_RMSE']]
        grouped_gains=[lookup.loc[('M0',pro),'RMSE']-lookup.loc[(name,pro),'RMSE'] for pro in ['municipality','spatial']]
        decisions.append(dict(experiment=name,max_absolute_RMSE_MAE_harm=float(max(deltas)),max_grouped_RMSE_gain=float(max(grouped_gains)),max_local_RMSE_gain=float(max(local_gains)),passes_no_absolute_harm=bool(max(deltas)<=.01),frequent_zero_fraction=float((registry[registry.experiment.eq(name)].amplitude==0).mean()),interpretation='exploratory checks, not automatic promotion'))
    pd.DataFrame(decisions).to_csv(OUT/'report/decision_checks.csv',index=False)
    from matplotlib import pyplot as plt
    fig,ax=plt.subplots(figsize=(8,4));pivot=summary.pivot(index='protocol',columns='experiment',values='RMSE');pivot.plot.bar(ax=ax);ax.set(ylabel='RMSE (t/ha)',title='Correcciones residuales:OOF completas');fig.tight_layout();fig.savefig(OUT/'figures/protocol_rmse.png',dpi=150);plt.close(fig)
    doc=ROOT/'documentation/ct3_residual_conditional.md';doc.write_text('# Corrección residual condicional sobre C-T3\n\n[Informe técnico](../outputs/modeling/ct3_residual_conditional/v1/report/technical_report.md), [métricas](../outputs/modeling/ct3_residual_conditional/v1/tables/metrics_summary.csv), [OOF](../outputs/modeling/ct3_residual_conditional/v1/tables/oof_predictions.parquet).\n\nInvestigación independiente; F8no ejecutado, Champion intacto, no59PREDni ajuste final138. Implementación src/ct3_residual_conditional; script376.\n',encoding='utf-8')
    for r in pd.read_csv(OUT/'audit/protected_consumed_inputs.csv').itertuples():assert sha(ROOT/r.path)==r.sha256
    cfg=json.loads((OUT/'frozen_design.json').read_text())
    for path,h in {**cfg['source_sha'],**cfg['cache_sha']}.items():assert sha(ROOT/path)==h
    artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()}
    (OUT/'manifest.json').write_text(json.dumps(dict(status='complete',n_oof=8970,n_outer_base_recovered=65,n_outer_corrector_packs=260,scientific_fits=total_fits,wall_seconds=wall,no_final_fit138=True,PRED_predictions=0,F8_executed=False,artifacts=artifacts),indent=2),encoding='utf-8')
    print(summary.to_string(index=False),flush=True)
