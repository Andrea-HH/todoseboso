"""Matched OOF diagnostics, regional sensitivity and saved-mixture replay."""
from pathlib import Path
import sys,json,hashlib,itertools
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.four_expert_combinations import OUT,NAMES,OLD,predict_combinations
from src.family_8.research import pair_metrics
from src.winner_delivery import paired_signflip,holm
KEY=['protocol','repeat','fold','ID_POLIGONO']
def stats(g):
    y=g.y_true.to_numpy();e=g.y_pred.to_numpy()-y;den=np.sum((y-y.mean())**2)
    return dict(n=len(g),rmse=float(np.sqrt(np.mean(e**2))),r2=float(1-np.sum(e**2)/den) if den>1e-12 else np.nan,mae=float(abs(e).mean()),bias=float(e.mean()),error_sd=float(e.std()),p95_absolute=float(np.quantile(abs(e),.95)),within_05=float(np.mean(abs(e)<=.5)))
def save(rows,name,keys):
    f=pd.DataFrame(rows);f.to_csv(OUT/'tables'/(name+'_by_repeat.csv'),index=False);s=f.drop(columns='repeat',errors='ignore').groupby(keys,dropna=False).mean(numeric_only=True).reset_index();s.to_csv(OUT/'tables'/(name+'.csv'),index=False);return s
def md(d):
    def cell(x):return f'{x:.4f}' if isinstance(x,(float,np.floating)) else str(x).replace('|','/')
    return '\n'.join(['| '+' | '.join(d.columns)+' |','| '+' | '.join(['---']*len(d.columns))+' |']+['| '+' | '.join(map(cell,r))+' |' for r in d.itertuples(index=False,name=None)])
def main():
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert (OUT/'execution_complete.json').exists();assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());p=pd.read_parquet(OUT/'tables/predictions.parquet');t=pd.read_parquet(OLD/'cache/train138.parquet');p=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');assert len(p)==10*(1794+16*41) and not p.duplicated(['experiment']+KEY).any();p['error']=p.y_pred-p.y_true;p.to_parquet(OUT/'tables/oof_residuals.parquet',index=False);bins=dict(zip(t.ID_POLIGONO,pd.qcut(t.RENDIMIENTO_T_HA,4).astype(str)));metrics=[];regions=[];omits=[];quartiles=[];pairs=[]
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==(41 if pro=='fresh_97_41' else 138) and g.ID_POLIGONO.is_unique;k=dict(experiment=name,protocol=pro,repeat=re);metrics.append(dict(**k,**stats(g)));pairs.append(dict(**k,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**k,kind=kind,zone=str(zone),**stats(h)))
                if len(g[g[kind]!=zone]):omits.append(dict(**k,kind=kind,omitted=str(zone),**stats(g[g[kind]!=zone])))
        for zone,h in g.groupby(g.ID_POLIGONO.map(bins)):quartiles.append(dict(**k,zone=zone,**stats(h)))
    tables={'metrics':save(metrics,'metrics',['experiment','protocol']),'regions':save(regions,'regions',['experiment','protocol','kind','zone']),'omissions':save(omits,'omissions',['experiment','protocol','kind','omitted']),'quartiles':save(quartiles,'quartiles',['experiment','protocol','zone']),'intraprofile':save(pairs,'intraprofile',['experiment','protocol'])}
    parcel=p.groupby(['experiment','protocol','ID_POLIGONO','Estado','Municipio']).agg(y_true=('y_true','first'),bias=('error','mean'),mse=('error',lambda z:float(np.mean(z*z))),mae=('error',lambda z:float(abs(z).mean())),n_evaluations=('error','size')).reset_index();parcel.to_csv(OUT/'tables/parcel_residuals.csv',index=False);tables['parcel_residuals']=parcel
    gains=[];tests=[];correlations=[];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO')
    comparisons=[(b,ref) for b in ['B1','B2','B3','B4','B5','B6'] for ref in NAMES]+[('B5','B1'),('B6','B3')]
    for pro,g in p.groupby('protocol'):
        parcels={n:h.set_index('ID_POLIGONO') for n,h in parcel[parcel.protocol==pro].groupby('experiment')}
        for left,right in comparisons:
            aa=parcels[left];bb=parcels[right];assert aa.index.equals(bb.index)
            for id_ in aa.index:gains.append(dict(protocol=pro,experiment=left,reference=right,ID_POLIGONO=id_,Municipio=aa.loc[id_,'Municipio'],mae_gain=bb.loc[id_,'mae']-aa.loc[id_,'mae'],mse_gain=bb.loc[id_,'mse']-aa.loc[id_,'mse']))
            group=groups.loc[aa.index,pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();s=tables['metrics'];point=float(s[(s.experiment==left)&(s.protocol==pro)].rmse.iloc[0]-s[(s.experiment==right)&(s.protocol==pro)].rmse.iloc[0]);tests.append(dict(protocol=pro,experiment=left,reference=right,delta_rmse=point,**paired_signflip(aa.mse-bb.mse,group)))
        pivot=g.pivot(index=['repeat','ID_POLIGONO'],columns='experiment',values='error')
        for left,right in itertools.combinations(NAMES,2):correlations.append(dict(protocol=pro,left=left,right=right,error_correlation=pivot[left].corr(pivot[right]),absolute_error_correlation=abs(pivot[left]).corr(abs(pivot[right]))))
    tests=pd.DataFrame(tests);tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(OUT/'tables/paired_tests.csv',index=False);tables['paired_tests']=tests;pd.DataFrame(correlations).to_csv(OUT/'tables/error_correlations.csv',index=False);gains=pd.DataFrame(gains);gains.to_csv(OUT/'tables/parcel_gains.csv',index=False);distribution=gains.groupby(['protocol','experiment','reference']).agg(total_mse_gain=('mse_gain','sum'),fraction_improved=('mae_gain',lambda z:float(np.mean(z>1e-12))),fraction_worsened=('mae_gain',lambda z:float(np.mean(z < -1e-12)))).reset_index();distribution.to_csv(OUT/'tables/gain_distribution.csv',index=False);tables['gain_distribution']=distribution
    replay=[];selection=[];runtime=[]
    with threadpool_limits(limits=1):
        for fi in range(81):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');ck=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');r=pd.DataFrame(ck['predictions']);pred,weights=predict_combinations(pack['models'],pack['external_expert_predictions'],pack['features']);tr=pack['train_positions'];va=pack['validation_positions'];assert not set(tr)&set(va)
            for n,pp in pred.items():
                expected=r[r.experiment==n].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();diff=float(max(abs(pp-expected)));assert diff<1e-12;replay.append(dict(execution_index=fi,experiment=n,max_difference=diff))
                if n=='B4':selection.append(dict(execution_index=fi,protocol=r.protocol.iloc[0],experiment=n,weight_CT3=pack['models'][n].weights[0],weight_Reference26=pack['models'][n].weights[1],weight_L40=pack['models'][n].weights[2]))
                else:selection.append(dict(execution_index=fi,protocol=r.protocol.iloc[0],experiment=n,mean_right_weight=float(np.mean(weights[n])),min_right_weight=float(np.min(weights[n])),max_right_weight=float(np.max(weights[n]))))
            assert all(not set(v['train'])&(set(v['held'])|set(va)) for v in ck['ledger']);runtime.append(dict(execution_index=fi,protocol=r.protocol.iloc[0],seconds=ck['seconds'],warnings=len(ck['warnings']),fallbacks=len(ck['fallbacks'])))
    pd.DataFrame(replay).to_csv(OUT/'audit/mixture_replay.csv',index=False);pd.DataFrame(selection).to_csv(OUT/'tables/weights_by_fold.csv',index=False);pd.DataFrame(runtime).to_csv(OUT/'tables/runtime.csv',index=False);tables['weights_by_fold']=pd.DataFrame(selection)
    with pd.ExcelWriter(OUT/'comparaciones_y_residuos.xlsx') as writer:
        for name,f in tables.items():f.to_excel(writer,sheet_name=name[:31],index=False)
    presentation=tables['metrics'].copy();presentation['RMSE_R2']=[f'{r.rmse:.4f} / {r.r2:.4f}' for r in presentation.itertuples()];wide=presentation.pivot(index='experiment',columns='protocol',values='RMSE_R2').reset_index();wide.to_csv(OUT/'tables/presentation_RMSE_R2.csv',index=False)
    text='# Combinaciones de cuatro expertos: resultados\n\nInvestigación exploratoria; no selección de modelos usando folds externos ni promoción automática. Pesos aprendidos en predicciones internas honestas.\n\n'+md(wide)+'\n\n## Residuos\n\n'+md(tables['metrics'][['experiment','protocol','mae','bias','p95_absolute','within_05']])+'\n\n## Contrastes pareados\n\n'+md(tests)+'\n\nEl banco fresh97/41 son particiones nuevas de respuestas ya estudiadas, no evidencia independiente. Los grupos de inferencia son perfiles (incluyendo fresh), municipios o bloques; las repeticiones no son muestras independientes. L40 conserva representación transductiva. Los diagnósticos por parcela, cuartil, municipio, bloque e intraperfil están en el Excel.\n';(ROOT/'documentation/four_expert_combinations_results.md').write_text(text,encoding='utf-8')
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());report=dict(status='complete',entries=10,OOF_rows=len(p),original_folds=65,fresh_splits=16,mixtures_replayed=len(replay),original_expert_parity_rows=len(pd.read_parquet(OUT/'tables/parity.parquet')),paired_tests=len(tests),significant_holm=int((tests.p_holm<.05).sum()),protected_sources_unchanged=True,no_PRED=True,no_champion_change=True);(OUT/'evaluation_complete.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));print(wide.to_string(index=False))
if __name__=='__main__':main()
