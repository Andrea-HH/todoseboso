"""Evaluate and replay learned R3 weighting without external model selection."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.learned_r3_weight import OUT,FEATURES,R3,GateFeatures,LearnedWeight
from src.learned_r3_protocol import load_design
from src.indicator_neighborhoods import OUT as INDICATORS,ReducedCorrection
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
PRIOR=ROOT/'outputs/modeling/base_distribution_correction/v1';D=OUT/'tables';BASES=['CT3','J7','SHARES'];PROTOCOLS=['random','climate_profile','municipality','spatial'];KEY=['protocol','repeat','fold','ID_POLIGONO']
spec=importlib.util.spec_from_file_location('residual487',ROOT/'scripts/487_j7_r3_residual_simplification.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def md(d):
    def cell(v):return f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v).replace('|','/')
    return '\n'.join(['| '+' | '.join(d.columns)+' |','| '+' | '.join(['---']*len(d.columns))+' |']+['| '+' | '.join(map(cell,r))+' |' for r in d.itertuples(index=False,name=None)])

def write(name,rows,keys):
    f=pd.DataFrame(rows);f.to_csv(D/(name+'_by_repeat.csv'),index=False);s=f.drop(columns='repeat',errors='ignore').groupby(keys,dropna=False).mean(numeric_only=True).reset_index();s.to_csv(D/(name+'_summary.csv'),index=False);return s

def main():
    assert not (OUT/'evaluation_complete.json').exists();assert (OUT/'execution_complete.json').exists();cfg=load_design();assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');ids=t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy();x=pd.read_parquet(INDICATORS/'cache/features_train138_target_free.parquet');p=pd.read_parquet(D/'predictions.parquet');assert len(p)==33*1794 and not p.duplicated(['experiment','protocol','repeat','ID_POLIGONO']).any();previous=pd.read_parquet(PRIOR/'tables/predictions.parquet')
    for b in BASES:
        for suffix in ['_BASE','_GLOBAL_GLOBAL','_SATELLITE_SUPPORT']:
            name=b+suffix;z=p[p.experiment==name].merge(previous[previous.experiment==name],on=KEY,suffixes=('','_ref'),validate='one_to_one');assert len(z)==1794;np.testing.assert_array_equal(z.y_pred,z.y_pred_ref)
    p=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');p['error']=p.y_pred-p.y_true;p['absolute_error']=abs(p.error);p['squared_error']=p.error**2;p.to_parquet(D/'oof_residuals.parquet',index=False);bins=dict(zip(ids,pd.qcut(y,4,duplicates='drop').astype(str)));complete=dict(zip(ids,np.isfinite(x[R3].to_numpy(float)).all(axis=1)));hard=pd.read_csv(ROOT/'outputs/research/difficult_quartile/v1/tables/parcel_groups.csv');hard=hard[hard.hard_quartile].ID_POLIGONO.tolist();metrics=[];regions=[];omits=[];quartiles=[];support=[];without=[];pairs=[]
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;k=dict(experiment=name,protocol=pro,repeat=re);metrics.append(dict(**k,**audit.stats(g)));pairs.append(dict(**k,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):regions.append(dict(**k,kind=kind,zone=str(zone),**audit.stats(h)));omits.append(dict(**k,kind=kind,omitted=str(zone),**audit.stats(g[g[kind]!=zone])))
        for zone,h in g.groupby(g.ID_POLIGONO.map(bins)):quartiles.append(dict(**k,zone=zone,**audit.stats(h)))
        for c,h in g.groupby(g.ID_POLIGONO.map(complete)):support.append(dict(**k,complete_R3=c,**audit.stats(h)))
        for label,cases in [('hard35',hard),('171_015',['AGC_171','AGC_015'])]:without.append(dict(**k,excluded=label,**audit.stats(g[~g.ID_POLIGONO.isin(cases)])))
    summary=write('metrics',metrics,['experiment','protocol']);write('regions',regions,['experiment','protocol','kind','zone']);write('omissions',omits,['experiment','protocol','kind','omitted']);write('quartiles',quartiles,['experiment','protocol','zone']);write('support_groups',support,['experiment','protocol','complete_R3']);write('without_cases',without,['experiment','protocol','excluded']);write('intraprofile',pairs,['experiment','protocol'])
    selection=pd.read_parquet(D/'selection.parquet');selection.to_csv(D/'selection_by_fold.csv',index=False);selection.assign(active=selection.strength>0).groupby(['experiment','protocol']).agg(active_folds=('active','sum'),total_folds=('active','size')).reset_index().to_csv(D/'activation.csv',index=False);selection[selection.strength>0].groupby(['experiment','protocol','penalty','strength']).size().rename('active_folds').reset_index().to_csv(D/'active_selection_counts.csv',index=False)
    details=pd.read_parquet(D/'details.parquet');details['sign']=np.where(details.candidate_delta>1e-8,'positive',np.where(details.candidate_delta < -1e-8,'negative','zero'));details.groupby(['experiment','protocol','sign']).agg(mean_weight=('weight','mean'),mean_absolute_delta=('applied_delta',lambda z:abs(z).mean()),zero_weight_fraction=('weight',lambda z:(z<1e-12).mean()),one_weight_fraction=('weight',lambda z:(z>1-1e-12).mean()),n=('weight','size')).reset_index().to_csv(D/'weights_by_sign.csv',index=False);diagnostics=[]
    for name,g in details.groupby('experiment'):
        z=g.merge(p[p.experiment==name][KEY+['y_true']],on=KEY,validate='one_to_one');z['proposal_helps']=abs(z.base_prediction+z.candidate_delta-z.y_true)<abs(z.base_prediction-z.y_true)-1e-12;z['proposal_harms']=abs(z.base_prediction+z.candidate_delta-z.y_true)>abs(z.base_prediction-z.y_true)+1e-12
        for pro,h in z.groupby('protocol'):diagnostics.append(dict(experiment=name,protocol=pro,weight_if_proposal_helps=h.loc[h.proposal_helps,'weight'].mean(),weight_if_proposal_harms=h.loc[h.proposal_harms,'weight'].mean(),mean_weight=h.weight.mean()))
    pd.DataFrame(diagnostics).to_csv(D/'weight_discrimination.csv',index=False)
    comparisons=[]
    for b in BASES:
        for kind in cfg['recipes']:
            name=b+'_'+kind
            for ref,contrast in [(b+'_BASE','own_base'),(b+'_GLOBAL_GLOBAL','own_global'),('J7_GLOBAL_GLOBAL','vs_J7R3')]:comparisons.append((name,ref,contrast))
            if kind!='MASK':comparisons.append((name,b+'_MASK','vs_mask'))
    assert len(comparisons)==93;groups=pd.read_csv(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/groups.csv').set_index('ID_POLIGONO').loc[ids];tests=[];gains=[]
    with threadpool_limits(limits=1):
        for pro,g in p.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();w,_=cluster_weights(group,5000,2026);arrays={n:h.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy() for n,h in g.groupby('experiment')};samples={n:sampled_metrics(y,v,w) for n,v in arrays.items()}
            for name,ref,contrast in comparisons:
                a=arrays[name];b=arrays[ref];delta=samples[name]['rmse']-samples[ref]['rmse'];point=np.sqrt(np.mean((a-y)**2,axis=1)).mean()-np.sqrt(np.mean((b-y)**2,axis=1)).mean();tests.append(dict(experiment=name,reference=ref,contrast=contrast,protocol=pro,delta_rmse=point,low95=np.quantile(delta,.025),high95=np.quantile(delta,.975),**paired_signflip(np.sum((a-y)**2-(b-y)**2,axis=0),group)))
                for j,i in enumerate(ids):gains.append(dict(experiment=name,reference=ref,contrast=contrast,protocol=pro,ID_POLIGONO=i,sse_gain=float(np.mean((b[:,j]-y[j])**2-(a[:,j]-y[j])**2)),absolute_gain=float(np.mean(abs(b[:,j]-y[j])-abs(a[:,j]-y[j])))))
    tests=pd.DataFrame(tests);tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'paired_tests.csv',index=False);gains=pd.DataFrame(gains);gains.to_csv(D/'parcel_gains.csv',index=False);dist=[]
    for (name,ref,contrast,pro),g in gains.groupby(['experiment','reference','contrast','protocol']):dist.append(dict(experiment=name,reference=ref,contrast=contrast,protocol=pro,total_sse_gain=g.sse_gain.sum(),hard35_sse_gain=g[g.ID_POLIGONO.isin(hard)].sse_gain.sum(),remaining103_sse_gain=g[~g.ID_POLIGONO.isin(hard)].sse_gain.sum(),fraction_improved=(g.absolute_gain>1e-12).mean(),fraction_worsened=(g.absolute_gain< -1e-12).mean()))
    pd.DataFrame(dist).to_csv(D/'gain_distribution.csv',index=False)
    # Replay every learned model and audit every additional residual exclusion.
    replay=[];coefficients=[];fallbacks=[];runtime=[];calibration_checks=[]
    with threadpool_limits(limits=1):
        for fi in range(65):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');ck=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];assert not set(tr)&set(va);r=pd.DataFrame(ck['predictions']);q=x.iloc[va];runtime.append(dict(execution_index=fi,seconds=ck['seconds']))
            old=joblib.load(PRIOR/'models'/f'{fi:02d}.joblib');old_ck=joblib.load(PRIOR/'checkpoints'/f'{fi:02d}.joblib');reconstructed={};z_reconstructed={}
            for b in BASES:
                proposal=np.full(len(tr),np.nan);zz=np.full((len(tr),6),np.nan)
                for ctx in old_ck['contexts']:
                    aa=np.asarray(ctx['aa']);d=ctx['where'];assert not set(aa)&(set(tr[d])|set(va));m=ReducedCorrection('R3').fit(x.iloc[aa],y[aa]-ctx['bases'][b]);proposal[d]=m.delta(x.iloc[tr[d]]);zz[d]=GateFeatures(cfg['definitions']).fit(x.iloc[aa]).transform(x.iloc[tr[d]],old['correctors'][b]['base_oof'][d],proposal[d])
                difference=float(max(abs(proposal-old['correctors'][b]['candidate_oof'])));assert difference<1e-12;reconstructed[b]=proposal;z_reconstructed[b]=zz;calibration_checks.append(dict(execution_index=fi,base=b,max_difference=difference))
            for name,item in pack['models'].items():
                base=r[r.experiment==item['base']+'_BASE'].set_index('ID_POLIGONO').loc[q.ID_POLIGONO].y_pred.to_numpy();d=item['corrector'].delta(q);z=pack['feature_space'].transform(q,base,d);w=item['weight'].predict(z,d);expected=r[r.experiment==name].set_index('ID_POLIGONO').loc[q.ID_POLIGONO].y_pred.to_numpy();difference=float(max(abs(base+w*d-expected)));assert difference<1e-12 and max(abs(w*d))<=.25+1e-12;replay.append(dict(execution_index=fi,experiment=name,max_difference=difference));s=[v for v in ck['selection'] if v['experiment']==name][0];best=min([v for v in ck['candidates'] if v['experiment']==name],key=lambda z:(round(z['rmse'],12),z['strength'],-z['penalty']));assert best['penalty']==s['penalty'] and best['strength']==s['strength']
                np.testing.assert_array_equal(item['candidate_oof'],reconstructed[item['base']]);np.testing.assert_allclose(item['features_oof'],z_reconstructed[item['base']],equal_nan=True,atol=1e-12,rtol=0);m=LearnedWeight(item['weight'].kind,item['weight'].penalty,item['weight'].strength).fit(item['features_oof'],y[tr]-item['base_oof'],item['candidate_oof']);np.testing.assert_allclose(m.predict(z,d),w,atol=1e-12,rtol=0)
                for group,beta in item['weight'].beta.items():
                    for feature,value in zip(['intercept']+FEATURES,beta):coefficients.append(dict(execution_index=fi,experiment=name,protocol=s['protocol'],group=group,feature=feature,coefficient=value,active=s['strength']>0))
                fallbacks.append(dict(execution_index=fi,experiment=name,protocol=s['protocol'],fallback_signs=','.join(item['weight'].fallbacks),constant=item['weight'].constant,active=s['strength']>0))
            for rec in ck['ledger']:assert not set(rec['train'])&(set(rec['held'])|set(rec['excluded'])|set(va))
            for z in ck['logs']:fallbacks.append(dict(execution_index=fi,experiment='nested_base',protocol=r.protocol.iloc[0],fallback_signs=z['kind'],constant=np.nan,active=True))
    pd.DataFrame(replay).to_csv(OUT/'audit/model_replay.csv',index=False);pd.DataFrame(calibration_checks).to_csv(OUT/'audit/calibration_rebuild.csv',index=False);pd.DataFrame(coefficients).to_csv(D/'weight_coefficients.csv',index=False);pd.DataFrame(fallbacks).to_csv(D/'fallbacks.csv',index=False);pd.DataFrame(runtime).to_csv(D/'execution_times.csv',index=False)
    presentation=pd.DataFrame(index=sorted(summary.experiment.unique()))
    for pro in PROTOCOLS:
        z=summary[summary.protocol==pro].set_index('experiment');presentation[pro]=[f'{z.loc[n,"rmse"]:.4f} / {z.loc[n,"r2"]:.4f}' for n in presentation.index]
    presentation.index.name='experiment';presentation.reset_index().to_csv(D/'presentation_RMSE_R2.csv',index=False)
    report=['# Pesos aprendidos y asimetría R3: resultados exploratorios','33 entradas: 24 nuevas y nueve referencias exactas; mismos 65 folds. Métricas por OOF completas de cada repetición, nunca media de errores por fold. BASE=base original; GLOBAL_GLOBAL=R3 global anterior; SATELLITE_SUPPORT=peso fijo anterior; MASK=sólo disponibilidad; CONSTANT=peso escalar aprendido; ASYM=pesos por signo; LEARNED=peso condicionado; LEARNED_ASYM=condicionado por signo. P1/P10 son sensibilidades fijas, no penalizaciones seleccionadas. Diseño inicial y enmienda previa a resultados deben leerse juntos.',md(presentation.reset_index()),'## Activación / aplicación',md(pd.read_csv(D/'activation.csv')),'La intensidad MASK se selecciona con propuestas R3 OOF internas. Los otros pesos se ajustan una vez sobre las entradas cross-fitted del entrenamiento externo, con penalización fija: su error de ajuste no es validación interna del metamodelo y no se usa para elegir penalización. La base sin corrección es un control explícito, no un apagado elegido por CV para esos pesos.','## Pesos y utilidad de las propuestas',md(pd.DataFrame(diagnostics)),f'372 contrastes predefinidos; significativos tras Holm: {int((tests.p_holm<.05).sum())}. Contienen comparaciones repetidas para J7 propio-global/referencia; se conserva el ajuste conjunto predefinido, conservador. No se interpreta no significancia como equivalencia. No se promovió Champion ni se generaron PRED59.','Los descriptores locales se construyen sólo con entrenamiento y k24 fijo. Las propuestas R3 para entrenar el peso son OOF: R3 se ajusta en A con residuos base OOF íntegramente dentro de A y predice D, excluyendo D y el fold externo. La auditoría reconstruye195 calibraciones y1,560 metamodelos. MASK/CONSTANT/ASYM requieren siete entradas con C-T3,31 con J7 y26 con SHARES; LEARNED añade FAPAR histórico para geometría satelital: ocho,32 y27 respectivamente. Los seis descriptores derivados no son nuevas fuentes independientes.']
    (ROOT/'documentation/learned_r3_weight_results.md').write_text('\n\n'.join(report),encoding='utf-8')
    with pd.ExcelWriter(OUT/'pesos_aprendidos_y_asimetria.xlsx',engine='openpyxl') as writer:
        presentation.reset_index().to_excel(writer,sheet_name='RMSE_R2',index=False)
        for f in sorted(D.glob('*.csv')):
            if f.stem.endswith('_by_repeat') or f.stem in ['parcel_gains','presentation_RMSE_R2','weight_coefficients','selection_by_fold']:continue
            pd.read_csv(f).to_excel(writer,sheet_name=f.stem[:31],index=False)
        for sheet in writer.book.worksheets:sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'evaluation_complete.json').write_text(json.dumps(dict(status='complete',entries=33,OOF_rows=len(p),models_replayed=len(replay),calibrations_rebuilt=len(calibration_checks),reference_predictions_exact=True,selection_verified=True,protected_sources_unchanged=True,paired_tests=len(tests),significant_holm=int((tests.p_holm<.05).sum()),no_PRED=True,no_final138_fit=True,no_champion_change=True),indent=2),encoding='utf-8');print(presentation.to_string())

if __name__=='__main__':main()
