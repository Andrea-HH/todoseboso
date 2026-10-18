"""OOF evaluation and full replay of base simplification x conditional R3."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.indicator_neighborhoods import OUT as SOURCE
from src.base_distribution_correction import load_design,R3
from src.neighbor_signal_contrasts import load_assets
from src.geoc_signal_research import predict_base
from src.signal_role_allocation import predict_role
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
OUT=ROOT/'outputs/modeling/base_distribution_correction/v1';D=OUT/'tables';PROTOCOLS=['random','climate_profile','municipality','spatial'];REF='J7_GLOBAL_GLOBAL'
spec=importlib.util.spec_from_file_location('research487',ROOT/'scripts/487_j7_r3_residual_simplification.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def md(d):
    def cell(v):return f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v).replace('|','/')
    return '\n'.join(['| '+' | '.join(d.columns)+' |','| '+' | '.join(['---']*len(d.columns))+' |']+['| '+' | '.join(map(cell,r))+' |' for r in d.itertuples(index=False,name=None)])

def write(name,rows,keys):
    f=pd.DataFrame(rows);f.to_csv(D/(name+'_by_repeat.csv'),index=False);s=f.drop(columns='repeat',errors='ignore').groupby(keys,dropna=False).mean(numeric_only=True).reset_index();s.to_csv(D/(name+'_summary.csv'),index=False);return s

def main():
    assert not (OUT/'evaluation_complete.json').exists();assert (OUT/'execution_complete.json').exists();cfg=load_design(OUT);assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    assets=load_assets();t=assets['a']['train'];ids=t.ID_POLIGONO.tolist();y=assets['y'];x=pd.read_parquet(SOURCE/'cache/features_train138_target_free.parquet');p=pd.read_parquet(D/'predictions.parquet');assert len(p)==48*1794 and not p.duplicated(['experiment','protocol','repeat','ID_POLIGONO']).any();p=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');p['error']=p.y_pred-p.y_true;p['absolute_error']=abs(p.error);p['squared_error']=p.error**2;p.to_parquet(D/'oof_residuals.parquet',index=False)
    previous=pd.read_parquet(SOURCE/'tables/oof_residuals.parquet');keys=['protocol','repeat','fold','ID_POLIGONO']
    for name,ref in [('CT3_BASE','CT3'),('J7_BASE','J7_BOTH'),('CT3_GLOBAL_GLOBAL','CT3_GLOBAL_R3'),('J7_GLOBAL_GLOBAL','J7_GLOBAL_R3')]:
        z=p[p.experiment==name].merge(previous[previous.experiment==ref],on=keys,suffixes=('','_ref'),validate='one_to_one');assert len(z)==1794;np.testing.assert_array_equal(z.y_pred,z.y_pred_ref)
    original_shares=pd.read_parquet(ROOT/'outputs/modeling/joint_simplification/v1/tables/predictions.parquet');z=p[p.experiment=='SHARES_BASE'].merge(original_shares[original_shares.experiment=='J7_SHARES'],on=keys,suffixes=('','_ref'),validate='one_to_one');assert len(z)==1794;z['absolute_difference']=abs(z.y_pred-z.y_pred_ref);z.groupby('protocol').absolute_difference.agg(['mean','max']).reset_index().to_csv(OUT/'audit/shares_reconstruction_parity.csv',index=False)
    metrics=[];regions=[];quartiles=[];omits=[];pairs=[];without=[];support_groups=[];complete=dict(zip(ids,np.isfinite(x[R3].to_numpy(float)).all(axis=1)));bins=dict(zip(ids,pd.qcut(y,4,duplicates='drop').astype(str)));hard=pd.read_csv(ROOT/'outputs/research/difficult_quartile/v1/tables/parcel_groups.csv');hard=hard[hard.hard_quartile].ID_POLIGONO.tolist()
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;k=dict(experiment=name,protocol=pro,repeat=re);metrics.append(dict(**k,**audit.stats(g)));pairs.append(dict(**k,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):regions.append(dict(**k,kind=kind,zone=str(zone),**audit.stats(h)));omits.append(dict(**k,kind=kind,omitted=str(zone),**audit.stats(g[g[kind]!=zone])))
        for zone,h in g.groupby(g.ID_POLIGONO.map(bins)):quartiles.append(dict(**k,zone=zone,**audit.stats(h)))
        for supported,h in g.groupby(g.ID_POLIGONO.map(complete)):support_groups.append(dict(**k,complete_R3=supported,**audit.stats(h)))
        for label,cases in [('hard35',hard),('171_015',['AGC_171','AGC_015'])]:without.append(dict(**k,excluded=label,**audit.stats(g[~g.ID_POLIGONO.isin(cases)])))
    summary=write('metrics',metrics,['experiment','protocol']);write('regions',regions,['experiment','protocol','kind','zone']);write('quartiles',quartiles,['experiment','protocol','zone']);write('omissions',omits,['experiment','protocol','kind','omitted']);write('intraprofile',pairs,['experiment','protocol']);write('without_cases',without,['experiment','protocol','excluded']);write('support_groups',support_groups,['experiment','protocol','complete_R3'])
    selection=pd.read_parquet(D/'selection.parquet');selection.to_csv(D/'selection_by_fold.csv',index=False);selection[selection.amplitude>0].groupby(['experiment','protocol','k','amplitude']).size().rename('active_folds').reset_index().to_csv(D/'active_selection_counts.csv',index=False);selection.assign(active=selection.amplitude>0).groupby(['experiment','protocol']).agg(active_folds=('active','sum'),total_folds=('active','size')).reset_index().to_csv(D/'activation.csv',index=False)
    detail=pd.read_parquet(D/'details.parquet');detail.merge(selection[['experiment','protocol','repeat','fold','amplitude']],on=['experiment','protocol','repeat','fold'],validate='many_to_one').groupby(['experiment','protocol']).agg(mean_weight=('weight','mean'),supported_fraction=('support','mean'),mean_neighbors=('neighbor_count','mean'),mean_abs_delta=('applied_delta',lambda z:abs(z).mean()),fraction_zero_weight=('weight',lambda z:(z<1e-12).mean()),mean_amplitude=('amplitude','mean')).reset_index().to_csv(D/'weight_diagnostics.csv',index=False)
    discrimination=[]
    for name,h in detail.groupby('experiment'):
        base=name.split('_')[0];z=h.merge(p[p.experiment==base+'_BASE'][keys+['absolute_error']],on=keys,validate='one_to_one').merge(p[p.experiment==base+'_GLOBAL_GLOBAL'][keys+['absolute_error']],on=keys,suffixes=('_base','_global'),validate='one_to_one').merge(selection[selection.experiment==name][['protocol','repeat','fold','amplitude']],on=['protocol','repeat','fold'],validate='many_to_one')
        for pro,g in z.groupby('protocol'):
            active=g.amplitude>0;good=g.absolute_error_global<g.absolute_error_base-1e-12;bad=g.absolute_error_global>g.absolute_error_base+1e-12;discrimination.append(dict(experiment=name,protocol=pro,active_rows=int(active.sum()),mean_weight_when_global_helped=float(g.loc[active&good,'weight'].mean()),mean_weight_when_global_harmed=float(g.loc[active&bad,'weight'].mean()),helped_rows=int((active&good).sum()),harmed_rows=int((active&bad).sum())))
    pd.DataFrame(discrimination).to_csv(D/'weight_discrimination.csv',index=False)
    # Regional gain without averaging regional RMSE to form the global metric.
    regional=pd.read_csv(D/'regions_summary.csv');regional_changes=[]
    for name in summary.experiment.unique():
        if name==REF:continue
        z=regional[regional.experiment==name].merge(regional[regional.experiment==REF],on=['protocol','kind','zone'],suffixes=('','_reference'),validate='one_to_one');z['delta_rmse']=z.rmse-z.rmse_reference;regional_changes.append(z)
    pd.concat(regional_changes).to_csv(D/'regions_vs_J7R3.csv',index=False)
    groups=pd.read_csv(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/groups.csv').set_index('ID_POLIGONO').loc[ids];tests=[];gains=[];comparisons=[]
    for name in sorted(p.experiment.unique()):
        if name.endswith('_BASE'):continue
        base=name.split('_')[0];comparisons.append((name,base+'_BASE','own_base'))
        if name!=REF:comparisons.append((name,REF,'vs_J7R3'))
    assert len(comparisons)==83
    with threadpool_limits(limits=1):
        for pro,g in p.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();w,_=cluster_weights(group,5000,2026);arrays={n:h.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy() for n,h in g.groupby('experiment')};samples={n:sampled_metrics(y,v,w) for n,v in arrays.items()}
            for name,ref,contrast in comparisons:
                a=arrays[name];b=arrays[ref];delta=samples[name]['rmse']-samples[ref]['rmse'];point=np.sqrt(np.mean((a-y)**2,axis=1)).mean()-np.sqrt(np.mean((b-y)**2,axis=1)).mean();tests.append(dict(experiment=name,reference=ref,contrast=contrast,protocol=pro,delta_rmse=point,low95=np.quantile(delta,.025),high95=np.quantile(delta,.975),**paired_signflip(np.sum((a-y)**2-(b-y)**2,axis=0),group)))
                for i,j in enumerate(ids):gains.append(dict(experiment=name,reference=ref,contrast=contrast,protocol=pro,ID_POLIGONO=j,sse_gain=float(np.mean((b[:,i]-y[i])**2-(a[:,i]-y[i])**2)),absolute_gain=float(np.mean(abs(b[:,i]-y[i])-abs(a[:,i]-y[i])))))
    tests=pd.DataFrame(tests);tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'paired_tests.csv',index=False);gains=pd.DataFrame(gains);gains.to_csv(D/'parcel_gains.csv',index=False)
    dist=[]
    for (name,ref,contrast,pro),g in gains.groupby(['experiment','reference','contrast','protocol']):dist.append(dict(experiment=name,reference=ref,contrast=contrast,protocol=pro,total_sse_gain=g.sse_gain.sum(),hard35_sse_gain=g[g.ID_POLIGONO.isin(hard)].sse_gain.sum(),remaining103_sse_gain=g[~g.ID_POLIGONO.isin(hard)].sse_gain.sum(),fraction_improved=(g.absolute_gain>1e-12).mean(),fraction_worsened=(g.absolute_gain< -1e-12).mean()))
    pd.DataFrame(dist).to_csv(D/'gain_distribution.csv',index=False)
    # Independently replay every saved outer base and correction.
    replay=[];base_replay=[]
    with threadpool_limits(limits=1):
        for fi in range(65):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');ck=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];r=pd.DataFrame(ck['predictions']);q=x.iloc[va];b=pack['bases'];ct=b['ct3'].predict(t.iloc[va]);raw=predict_base(b['expert']['local'],va,assets);ep=predict_role(b['expert'],va,assets);sh=ct if b['shares'] is None else b['shares']['gate'].predict(b['shares']['space'].transform(assets['role_frame'].iloc[va]),ct,ep);predictions=dict(CT3=ct,RAW7=raw,EXPERT7=ep,EQUAL7=(ct+ep)/2,SHARES=sh,J7=r[r.experiment=='J7_BASE'].set_index('ID_POLIGONO').loc[q.ID_POLIGONO].y_pred.to_numpy())
            for name,value in predictions.items():
                expected=r[r.experiment==name+'_BASE'].set_index('ID_POLIGONO').loc[q.ID_POLIGONO].y_pred.to_numpy();difference=float(max(abs(value-expected)));assert difference<1e-12;base_replay.append(dict(execution_index=fi,base=name,max_difference=difference))
            for s in ck['selection']:
                name=s['experiment'];base=s['base'];m=pack['correctors'][base]['corrector'];delta=m.delta(q)
                if s['geometry']=='GLOBAL':w=np.ones(len(q))
                else:
                    w,records=pack['weight_models'][(s['geometry'],s['k'])].weights(q,s['use'],True)
                    for rr in records:assert set(rr['neighbor_ids']).issubset(set(t.iloc[tr].ID_POLIGONO)) and not set(rr['neighbor_ids'])&set(q.ID_POLIGONO)
                value=predictions[base]+s['amplitude']/.5*w*delta;expected=r[r.experiment==name].set_index('ID_POLIGONO').loc[q.ID_POLIGONO].y_pred.to_numpy();difference=float(max(abs(value-expected)));assert difference<1e-12;replay.append(dict(execution_index=fi,experiment=name,max_difference=difference));best=min([z for z in ck['candidates'] if z['experiment']==name],key=lambda z:(round(z['rmse'],12),z['amplitude'],-z['k']));assert best['k']==s['k'] and best['amplitude']==s['amplitude']
            for rec in ck['ledger']:assert not set(rec['train'])&(set(rec['held'])|set(va)|set(rec.get('excluded_inner',[])))
    pd.DataFrame(replay).to_csv(OUT/'audit/correction_replay.csv',index=False);pd.DataFrame(base_replay).to_csv(OUT/'audit/base_replay.csv',index=False)
    presentation=pd.DataFrame(index=sorted(summary.experiment.unique()))
    for pro in PROTOCOLS:
        z=summary[summary.protocol==pro].set_index('experiment');presentation[pro]=[f'{z.loc[n,"rmse"]:.4f} / {z.loc[n,"r2"]:.4f}' for n in presentation.index]
    inventory={(v['base'],v['geometry']):v for v in cfg['inventory']};presentation['input_count']=[inventory[(n.split('_')[0],'BASE' if n.endswith('_BASE') else n.split('_')[1])]['input_count'] for n in presentation.index];presentation.index.name='experiment';presentation.reset_index().to_csv(D/'presentation_RMSE_R2.csv',index=False);pd.DataFrame(cfg['inventory']).to_json(D/'input_inventory.json',orient='records',indent=2,force_ascii=False)
    report=['# Simplificación de bases y corrección por distribución de vecinos: resultados',
            '48 entradas, mismos 65 folds. RMSE t/ha / R² por OOF completa de cada repetición; no media de folds. Exploración sobre validaciones usadas anteriormente, sin promoción de Champion ni PRED59.',
            'BASE=sin R3 final; GLOBAL_GLOBAL=R3 sin ponderación local; SUPPORT=más corrección al parecerse a sus vecinos; NOVELTY=más corrección al diferir de ellos. El peso depende de las tres variables R3 respecto a la mediana/MAD de vecinos definidos por GEO/PHYSICAL/SATELLITE. No usa rendimientos para calcular la semejanza. El signo de la corrección procede de R3, no de la distancia. k/amplitud se seleccionan dentro del entrenamiento de cada combinación.',
            md(presentation.reset_index()),'## Pruebas pareadas',f'332 contrastes; significativos tras Holm: {int((tests.p_holm<.05).sum())}. Los intervalos son de OOF fijas con conglomerados; no incluyen toda selección histórica ni son intervalos de predicción.',
            '## Soporte y pesos',md(pd.read_csv(D/'weight_diagnostics.csv')),'El número de entradas incluye lo necesario para construir el vecindario; una base compacta con distancia física deja de ser un sistema de siete entradas. Con R3 incompleto o menos de cuatro referencias, el peso vale cero en ambos usos y se conserva la base. Las referencias nunca incluyen la parcela evaluada.',
            '## Complejidad y nombres','RAW7 elimina gate y corrector climático interno; EXPERT7 conserva ese corrector pero elimina gate; EQUAL7 combina C-T3 y EXPERT7 con .5 fijo; SHARES reconstruye gate de diez proporciones geológicas; J7 es referencia exacta. C-T3+R3 y J7+R3 se reprodujeron exactamente y no se presentan como descubrimientos nuevos. SHARES se reconstruye con calibración anidada de esta etapa; no se presume igualdad con un archivo antiguo. Los campos cuentan entradas, no parámetros efectivos.']
    (ROOT/'documentation/base_distribution_correction_results.md').write_text('\n\n'.join(report),encoding='utf-8')
    with pd.ExcelWriter(OUT/'bases_y_correccion_por_distribucion.xlsx',engine='openpyxl') as writer:
        presentation.reset_index().to_excel(writer,sheet_name='RMSE_R2',index=False)
        for f in sorted(D.glob('*.csv')):
            if f.stem.endswith('_by_repeat') or f.stem in ['parcel_gains','presentation_RMSE_R2','selection_by_fold']:continue
            pd.read_csv(f).to_excel(writer,sheet_name=f.stem[:31],index=False)
        for sheet in writer.book.worksheets:sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());result=dict(status='complete',entries=48,OOF_rows=len(p),base_replays=len(base_replay),correction_replays=len(replay),selection_verified=True,protected_sources_unchanged=True,reference_predictions_exact=True,paired_tests=len(tests),significant_holm=int((tests.p_holm<.05).sum()),no_PRED=True,no_final138_fit=True,no_champion_change=True);(OUT/'evaluation_complete.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(presentation.to_string());print(json.dumps(result,indent=2))

if __name__=='__main__':main()
