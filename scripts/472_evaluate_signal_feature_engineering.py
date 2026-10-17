"""OOF evaluation, paired exploratory inference and replay of all engineered models."""
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
from src.signal_feature_engineering import OUT
from src.neighbor_signal_linear import OUT as PREVIOUS
from src.geoc_bridge import OLD
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
spec=importlib.util.spec_from_file_location('engineering_audit',ROOT/'scripts/449_j7_both_residual_audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
D=OUT/'tables';PROTOCOLS=['random','climate_profile','municipality','spatial']


def md(f):
    def cell(v):return f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v).replace('|','/')
    return '\n'.join(['| '+' | '.join(f.columns)+' |','| '+' | '.join(['---']*len(f.columns))+' |']+['| '+' | '.join(map(cell,r))+' |' for r in f.itertuples(index=False,name=None)])


def write(name,rows,keys):
    f=pd.DataFrame(rows);f.to_csv(D/(name+'_by_repeat.csv'),index=False);s=f.drop(columns='repeat',errors='ignore').groupby(keys,dropna=False).mean(numeric_only=True).reset_index();s.to_csv(D/(name+'_summary.csv'),index=False);return s


def main():
    if (OUT/'evaluation_complete.json').exists():raise FileExistsError('Preserve completed engineering evaluation')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert (OUT/'execution_complete.json').exists()
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');ids=t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy();x=pd.read_parquet(OUT/'cache/features_train138_target_free.parquet');assert x.ID_POLIGONO.tolist()==ids
    p=pd.read_parquet(D/'predictions.parquet');old=pd.read_parquet(PREVIOUS/'tables/predictions.parquet');keys=['protocol','repeat','fold','ID_POLIGONO']
    for name in ['CT3','J7_BOTH']:
        z=p[p.experiment==name].merge(old[old.experiment==name],on=keys,suffixes=('','_ref'),validate='one_to_one');assert len(z)==1794;np.testing.assert_array_equal(z.y_pred,z.y_pred_ref);np.testing.assert_array_equal(z.y_true,z.y_true_ref)
    assert len(p)==16*1794 and not p.duplicated(['experiment','protocol','repeat','ID_POLIGONO']).any()
    p=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');p['error']=p.y_pred-p.y_true;p['squared_error']=p.error**2;p['absolute_error']=abs(p.error)
    p.to_parquet(D/'oof_residuals.parquet',index=False)
    top=pd.read_csv(ROOT/'outputs/research/top10_difficult_parcels/v1/tables/top10_J7_random.csv').ID_POLIGONO.tolist();bins=dict(zip(ids,pd.qcut(pd.Series(y),4,duplicates='drop').astype(str)));p['target_quartile']=p.ID_POLIGONO.map(bins)
    metrics=[];regions=[];omits=[];without=[];quarters=[];pairs=[]
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;key=dict(experiment=name,protocol=pro,repeat=re)
        m=audit.stats(g);assert np.isclose(m['rmse']**2,m['error_variance']+m['bias_squared']);metrics.append(dict(**key,**m));pairs.append(dict(**key,**pair_metrics(g)))
        for label,excluded in [('171_015',['AGC_171','AGC_015']),('top10',top)]:without.append(dict(**key,excluded=label,**audit.stats(g[~g.ID_POLIGONO.isin(excluded)])))
        for kind in ['Estado','Municipio','fold','climate_profile']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(zone),**audit.stats(h)))
                if kind!='climate_profile':omits.append(dict(**key,kind=kind,omitted=str(zone),**audit.stats(g[g[kind]!=zone])))
        for zone,h in g.groupby('target_quartile'):quarters.append(dict(**key,zone=zone,**audit.stats(h)))
    summary=write('metrics',metrics,['experiment','protocol']);write('regions',regions,['experiment','protocol','kind','zone']);write('omissions',omits,['experiment','protocol','kind','omitted']);write('without_cases',without,['experiment','protocol','excluded']);write('quartiles',quarters,['experiment','protocol','zone']);write('intraprofile',pairs,['experiment','protocol'])
    parcel=p.groupby(['experiment','protocol','ID_POLIGONO','Estado','Municipio','climate_profile']).agg(y_true=('y_true','first'),prediction=('y_pred','mean'),mean_error=('error','mean'),mean_absolute_error=('absolute_error','mean'),mean_squared_error=('squared_error','mean')).reset_index();parcel.to_csv(D/'parcel_errors.csv',index=False);parcel[parcel.ID_POLIGONO.isin(top)].to_csv(D/'top10_errors.csv',index=False)
    contrasts=[(n,'CT3' if r['base']=='CT3' else 'J7_BOTH','vs_base') for n,r in cfg['recipes'].items()]
    contrasts += [(base+'_'+block+'_ENG',base+'_'+block+'_RAW','engineering_vs_raw') for base in ['CT3','J7'] for block in ['H','T','P']]
    tests=[];gains=[];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids]
    with threadpool_limits(limits=1):
        for pro,g in p.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();weights,_=cluster_weights(group,5000,2026)
            arrays={name:h.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy() for name,h in g.groupby('experiment')};samples={n:sampled_metrics(y,v,weights) for n,v in arrays.items()}
            for name,ref,kind in contrasts:
                aa=arrays[name];bb=arrays[ref];delta=samples[name]['rmse']-samples[ref]['rmse'];point=np.sqrt(np.mean((aa-y)**2,axis=1)).mean()-np.sqrt(np.mean((bb-y)**2,axis=1)).mean();loss=np.sum((aa-y)**2-(bb-y)**2,axis=0)
                tests.append(dict(experiment=name,reference=ref,contrast=kind,protocol=pro,delta_rmse=float(point),low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
                for j,i in enumerate(ids):gains.append(dict(experiment=name,reference=ref,contrast=kind,protocol=pro,ID_POLIGONO=i,sse_gain=float(np.mean((bb[:,j]-y[j])**2-(aa[:,j]-y[j])**2)),absolute_error_gain=float(np.mean(abs(bb[:,j]-y[j])-abs(aa[:,j]-y[j])))))
    tests=pd.DataFrame(tests);assert len(tests)==80;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'paired_tests.csv',index=False);gains=pd.DataFrame(gains);gains.to_csv(D/'parcel_gains.csv',index=False)
    distributions=[]
    for (name,ref,pro),g in gains[gains.contrast=='vs_base'].groupby(['experiment','reference','protocol']):
        distributions.append(dict(experiment=name,reference=ref,protocol=pro,total_sse_gain=g.sse_gain.sum(),top10_sse_gain=g[g.ID_POLIGONO.isin(top)].sse_gain.sum(),outside_top10_sse_gain=g[~g.ID_POLIGONO.isin(top)].sse_gain.sum(),fraction_improved=float((g.absolute_error_gain>1e-12).mean()),fraction_worsened=float((g.absolute_error_gain < -1e-12).mean())))
    pd.DataFrame(distributions).to_csv(D/'gain_distribution.csv',index=False)
    for label,join in [('regions',['protocol','kind','zone']),('omissions',['protocol','kind','omitted']),('without_cases',['protocol','excluded'])]:
        f=pd.read_csv(D/(label+'_summary.csv'));changes=[]
        for name,r in cfg['recipes'].items():
            ref='CT3' if r['base']=='CT3' else 'J7_BOTH';z=f[f.experiment==name].merge(f[f.experiment==ref],on=join,suffixes=('','_reference'),validate='one_to_one')
            for c in ['rmse','r2','mae','bias']:z['delta_'+c]=z[c]-z[c+'_reference']
            changes.append(z)
        pd.concat(changes,ignore_index=True).to_csv(D/(label+'_paired_changes.csv'),index=False)
    selections=pd.read_parquet(D/'selection.parquet');selections.to_csv(D/'selection_by_fold.csv',index=False);selections.groupby(['experiment','protocol','alpha','l1_ratio','amplitude']).size().rename('folds').reset_index().to_csv(D/'selection_counts.csv',index=False)
    replay=[];coefs=[];timings=[];checks=[];ledger_count=0
    with threadpool_limits(limits=1):
        for fi in range(65):
            ck=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');tr=np.asarray(pack['train_positions']);va=np.asarray(pack['validation_positions']);assert not set(tr)&set(va);rows=pd.DataFrame(ck['predictions']);timings.append(dict(execution_index=fi,seconds=ck['seconds'],**ck['warm_hits']))
            for rec in ck['calibration_checks']:assert abs(rec['null_rmse']-rec['direct_base_rmse'])<1e-12;checks.append(dict(execution_index=fi,**rec))
            for rec in ck['ledger']:
                assert not set(rec['train'])&(set(rec['held'])|set(va)|set(rec.get('excluded_inner',[])));ledger_count+=1
            for name,m in pack['models'].items():
                r=cfg['recipes'][name];ref='CT3' if r['base']=='CT3' else 'J7_BOTH';bp=rows[rows.experiment==ref].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();expected=rows[rows.experiment==name].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();pred=m.predict(x.iloc[va],bp);diff=float(max(abs(pred-expected)));assert diff<1e-12 and max(abs(pred-bp))<=.25+1e-12
                selected=selections[(selections.execution_index==fi)&(selections.experiment==name)].iloc[0];candidates=[r for r in ck['candidates'] if r['experiment']==name];best=min(candidates,key=lambda v:(round(v['rmse'],12),v['amplitude'],-v['alpha'],-v['l1_ratio']))
                assert all(selected[c]==best[c] for c in ['alpha','l1_ratio','amplitude']);replay.append(dict(execution_index=fi,experiment=name,max_difference=diff))
                cf=np.zeros(len(m.feature_names))
                if m.model is not None:cf[m.support]=m.model.coef_
                for j,feature in enumerate(m.feature_names):coefs.append(dict(execution_index=fi,protocol=selected.protocol,experiment=name,feature=feature,coefficient=cf[j],amplitude=m.amplitude,nonzero=bool(abs(cf[j])>1e-10)))
    pd.DataFrame(replay).to_csv(OUT/'audit/model_replay.csv',index=False);pd.DataFrame(checks).to_csv(OUT/'audit/calibration_parity.csv',index=False);pd.DataFrame(timings).to_csv(D/'execution_times.csv',index=False);pd.DataFrame(coefs).to_csv(D/'coefficients_by_fold.csv',index=False);pd.DataFrame(coefs).groupby(['experiment','protocol','feature'])[['coefficient','nonzero','amplitude']].mean().reset_index().to_csv(D/'coefficient_stability.csv',index=False)
    # Feature redundancy is descriptive X-only; no selection is made from this table.
    redundancy=[]
    for name,cols in cfg['blocks'].items():
        corr=x[cols].corr().abs()
        for i,a in enumerate(cols):
            for b in cols[i+1:]:
                if pd.notna(corr.loc[a,b]) and corr.loc[a,b]>.95:redundancy.append(dict(block=name,feature_a=a,feature_b=b,absolute_correlation=corr.loc[a,b]))
    pd.DataFrame(redundancy,columns=['block','feature_a','feature_b','absolute_correlation']).to_csv(D/'high_redundancy_pairs.csv',index=False)
    presentation=pd.DataFrame(index=['CT3','J7_BOTH']+list(cfg['recipes']))
    for pro in PROTOCOLS:
        q=summary[summary.protocol==pro].set_index('experiment');presentation[pro]=[f'{q.loc[n,"rmse"]:.4f} / {q.loc[n,"r2"]:.4f}' for n in presentation.index]
    presentation.index.name='modelo';presentation.to_csv(D/'presentation_RMSE_R2.csv')
    delta=tests[tests.contrast=='vs_base'].pivot(index='experiment',columns='protocol',values='delta_rmse').reindex(index=list(cfg['recipes']),columns=PROTOCOLS);fig,ax=plt.subplots(figsize=(9,8));lim=max(abs(delta.to_numpy()).max(),.001);im=ax.imshow(delta,cmap='RdBu_r',vmin=-lim,vmax=lim,aspect='auto');ax.set_xticks(range(4),['Aleatoria','Perfil','Municipal','Espacial']);ax.set_yticks(range(len(delta)),delta.index)
    for i in range(len(delta)):
        for j in range(4):ax.text(j,i,f'{delta.iloc[i,j]:+.4f}',ha='center',va='center',fontsize=8)
    ax.set_title('Cambio RMSE frente a la base propia');fig.colorbar(im,ax=ax,label='t/ha');fig.tight_layout();fig.savefig(OUT/'figures/rmse_changes.png',dpi=160);plt.close(fig)
    report=ROOT/'documentation/signal_feature_engineering_results.md';report.write_text('\n\n'.join(['# Ingeniería de señales: resultados exploratorios','H_RAW18 vs H_ENG6: componentes históricos vs anomalías propias. T_RAW21 vs T_ENG6: señal mensual vs resúmenes temporales. P_RAW4 vs P_ENG8: padres vs padres e interacciones. SHIFT: recalibración de intercepto sin señales. Correctores EN con ajuste máximo ±.25 t/ha, selección anidada y referencias externas exactas.','## RMSE / R²',md(presentation.reset_index()),'## Métricas completas',md(summary[['experiment','protocol','rmse','mae','r2','bias','error_sd']]),'## Derivadas frente a componentes originales',md(tests[tests.contrast=='engineering_vs_raw']),'## Distribución de ganancias',md(pd.DataFrame(distributions)),'Las comparaciones con la base, 80 pruebas pareadas con Holm, omisiones, análisis sin top10/171/015, cuartiles, pares intraperfil y coeficientes están en las tablas y Excel. El top10 se congeló antes de esta etapa pero fue identificado usando estos mismos datos; excluirlo es sensibilidad descriptiva, no una prueba independiente.',f'Replay de {len(replay)} modelos; {ledger_count} exclusiones verificadas; sin cambio de fuentes ni PRED/final138.']),encoding='utf-8')
    with pd.ExcelWriter(OUT/'evaluacion_ingenieria_de_senales.xlsx',engine='openpyxl') as w:
        pd.DataFrame({'lectura':['RMSE t/ha / R²; protocolos separados.','H=historia propia, T=temporal/heterogeneidad, P=interacciones físicas.','RAW=componentes originales; ENG=transformaciones; SHIFT=sólo intercepto.','Referencia CT3 o J7 según prefijo. Selección exclusivamente interna.','Resultados exploratorios, no confirmación independiente ni causalidad.','Ver sin top10 y omisiones antes de interpretar mejoras.']}).to_excel(w,sheet_name='LEEME',index=False);presentation.reset_index().to_excel(w,sheet_name='RESUMEN',index=False)
        for file in sorted(D.glob('*.csv')):
            if file.stem in ['presentation_RMSE_R2','coefficients_by_fold','parcel_gains']:continue
            pd.read_csv(file).to_excel(w,sheet_name=file.stem[:31],index=False)
        for sheet in w.book.worksheets:sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    (OUT/'evaluation_complete.json').write_text(json.dumps(dict(status='complete',new_recipes=14,models_replayed=len(replay),oof_rows=len(p),paired_tests=len(tests),significant_holm=int((tests.p_holm<.05).sum()),ledger_exclusions=ledger_count,protected_sources_unchanged=True,external_references_exact=True,no_PRED=True,no_final138_fit=True),indent=2),encoding='utf-8');print(presentation.to_string());print('\nHolm significant:');print(tests[tests.p_holm<.05].to_string(index=False))


if __name__=='__main__':main()
