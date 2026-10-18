"""Read-only matched OOF comparison; no fitting or model selection."""
from pathlib import Path
import sys,itertools,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.winner_delivery import paired_signflip,holm
from src.family_8.research import pair_metrics
OUT=ROOT/'outputs/research/four_leaders/v1';OUT.mkdir(parents=True,exist_ok=True)
KEY=['protocol','repeat','fold','ID_POLIGONO']
def stats(g):
    e=g.y_pred-g.y_true;den=((g.y_true-g.y_true.mean())**2).sum()
    return dict(n=len(g),rmse=np.sqrt(np.mean(e**2)),r2=1-(e**2).sum()/den if den>1e-12 else np.nan,mae=abs(e).mean(),bias=e.mean(),error_sd=e.std(ddof=0),p95_absolute=abs(e).quantile(.95),within_05=(abs(e)<=.5).mean())
def save(rows,name,keys):
    f=pd.DataFrame(rows);f.to_csv(OUT/(name+'_by_repeat.csv'),index=False)
    s=f.drop(columns='repeat').groupby(keys,dropna=False).mean(numeric_only=True).reset_index();s.to_csv(OUT/(name+'.csv'),index=False);return s
def main():
    a=pd.read_parquet(ROOT/'outputs/modeling/architecture_decomposition/v1/tables/oof_residuals.parquet');mapping={'CT3_BASE':'CT3','NO_PLANET_OFF_GLOBAL_MASK':'Compact14','FULL7_ON_RAW_MASK':'Reference26'}
    a=a[a.experiment.isin(mapping)].copy();a['experiment']=a.experiment.map(mapping)
    b=pd.read_parquet(ROOT/'outputs/modeling/geoc_bridge/v1/tables/oof_predictions.parquet');b=b[(b.experiment=='LOCAL04D')&(b.protocol!='geoc_target_matched')].copy();b['experiment']='L40'
    anchor=a[a.experiment=='CT3'][KEY+['y_true','y_pred']];old=pd.read_parquet(ROOT/'outputs/modeling/geoc_bridge/v1/tables/oof_predictions.parquet');old=old[(old.experiment=='CT3')&(old.protocol!='geoc_target_matched')];check=anchor.merge(old,on=KEY,validate='one_to_one');assert len(check)==1794;np.testing.assert_allclose(check.y_pred_x,check.y_pred_y,atol=1e-12,rtol=0)
    t=a[['ID_POLIGONO','Estado','Municipio','climate_profile']].drop_duplicates();b=b.merge(t,on='ID_POLIGONO',validate='many_to_one');p=pd.concat([a[b.columns],b],ignore_index=True)
    assert len(p)==7176 and not p.duplicated(['experiment']+KEY).any()
    for _,g in p.groupby('experiment'):
        z=anchor.merge(g,on=KEY,validate='one_to_one');assert len(z)==1794;np.testing.assert_array_equal(z.y_true_x,z.y_true_y)
    y=t.merge(p[['ID_POLIGONO','y_true']].drop_duplicates(),on='ID_POLIGONO');bins=dict(zip(y.ID_POLIGONO,pd.qcut(y.y_true,4).astype(str)))
    metrics=[];regions=[];quartiles=[];omits=[];pairs=[]
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138;k=dict(experiment=name,protocol=pro,repeat=re);metrics.append(dict(**k,**stats(g)));pairs.append(dict(**k,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**k,kind=kind,zone=str(zone),**stats(h)));omits.append(dict(**k,kind=kind,omitted=str(zone),**stats(g[g[kind]!=zone])))
        for zone,h in g.groupby(g.ID_POLIGONO.map(bins)):quartiles.append(dict(**k,zone=zone,**stats(h)))
    summaries={'metrics':save(metrics,'metrics',['experiment','protocol']),'regions':save(regions,'regions',['experiment','protocol','kind','zone']),'quartiles':save(quartiles,'quartiles',['experiment','protocol','zone']),'omissions':save(omits,'omissions',['experiment','protocol','kind','omitted']),'intraprofile':save(pairs,'intraprofile',['experiment','protocol'])}
    groups=pd.read_csv(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/groups.csv').set_index('ID_POLIGONO');tests=[];gains=[]
    for pro,g in p.groupby('protocol'):
        ids=sorted(g.ID_POLIGONO.unique());truth=g[['ID_POLIGONO','y_true']].drop_duplicates().set_index('ID_POLIGONO').loc[ids].y_true.to_numpy();arrays={n:h.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy() for n,h in g.groupby('experiment')};gr=groups.loc[ids,pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy()
        for left,right in itertools.combinations(sorted(arrays),2):
            aa=arrays[left]-truth;bb=arrays[right]-truth;tests.append(dict(protocol=pro,left=left,right=right,delta_rmse=np.sqrt(np.mean(aa**2,axis=1)).mean()-np.sqrt(np.mean(bb**2,axis=1)).mean(),**paired_signflip(np.mean(aa**2-bb**2,axis=0),gr)))
            for i,id_ in enumerate(ids):gains.append(dict(protocol=pro,left=left,right=right,ID_POLIGONO=id_,mae_gain=np.mean(abs(bb[:,i])-abs(aa[:,i])),mse_gain=np.mean(bb[:,i]**2-aa[:,i]**2)))
    tests=pd.DataFrame(tests);tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(OUT/'paired_tests.csv',index=False);summaries['paired_tests']=tests
    gains=pd.DataFrame(gains);gains.to_csv(OUT/'parcel_pairwise_gains.csv',index=False);p['error']=p.y_pred-p.y_true;p.to_parquet(OUT/'matched_oof.parquet',index=False)
    parcels=p.groupby(['experiment','protocol','ID_POLIGONO','Municipio']).agg(y_true=('y_true','first'),mean_error=('error','mean'),mae=('error',lambda x:abs(x).mean()),rmse=('error',lambda x:np.sqrt(np.mean(x*x)))).reset_index();parcels.to_csv(OUT/'parcel_residuals.csv',index=False)
    with pd.ExcelWriter(OUT/'comparacion_cuatro_modelos.xlsx') as w:
        for name,f in summaries.items():f.to_excel(w,sheet_name=name,index=False)
        parcels.to_excel(w,sheet_name='parcel_residuals',index=False)
    report=dict(status='complete',matched_rows=len(p),same_CT3_predictions=True,external_folds=65,tests=len(tests),significant_holm=int((tests.p_holm<.05).sum()),no_training=True,no_PRED=True);(OUT/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));print(summaries['metrics'].to_string(index=False));print('SPATIAL MUNICIPAL');print(summaries['regions'].query("protocol=='spatial' and kind=='Municipio'")[['experiment','zone','n','rmse','bias']].to_string(index=False));print('QUARTILES');print(summaries['quartiles'].query("protocol in ['random','spatial']")[['experiment','protocol','zone','rmse','bias']].to_string(index=False));print('PAIRED');print(tests.to_string(index=False))
if __name__=='__main__':main()
