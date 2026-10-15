"""Standalone nested PLS experiment over the audited 1,867 named descriptors."""
from pathlib import Path
import hashlib,json,time,warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/modeling/experimental_pls1867/v1'
GRID=[1,2,3,5,8,12,16]

class TrainRepresentation:
    def fit(self,x):
        self.numeric=[c for c in x if pd.api.types.is_numeric_dtype(x[c]) or pd.api.types.is_bool_dtype(x[c])]
        self.categorical=[c for c in x if c not in self.numeric]
        raw=x[self.numeric].to_numpy(float);raw[~np.isfinite(raw)]=np.nan
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning);self.medians=np.nanmedian(raw,axis=0)
        self.medians=np.nan_to_num(self.medians,nan=0.)
        num=np.where(np.isfinite(raw),raw,self.medians)
        self.encoder=OneHotEncoder(handle_unknown='ignore',sparse_output=False,dtype=float)
        cat=self.encoder.fit_transform(x[self.categorical].fillna('__MISSING__').astype(str)) if self.categorical else np.empty((len(x),0))
        a=np.column_stack([num,cat]);self.support=np.std(a,axis=0)>1e-12
        self.scaler=StandardScaler().fit(a[:,self.support])
        self.names=np.array(self.numeric+(list(self.encoder.get_feature_names_out(self.categorical)) if self.categorical else []))[self.support]
        return self
    def transform(self,x):
        raw=x[self.numeric].to_numpy(float)
        num=np.where(np.isfinite(raw),raw,self.medians)
        cat=self.encoder.transform(x[self.categorical].fillna('__MISSING__').astype(str)) if self.categorical else np.empty((len(x),0))
        return self.scaler.transform(np.column_stack([num,cat])[:,self.support])

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def metrics(y,p):
    e=np.asarray(p)-np.asarray(y)
    return dict(rmse=float(np.sqrt(np.mean(e*e))),mae=float(np.mean(abs(e))),bias=float(np.mean(e)))

def prepare():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed experiment immutable')
    for sub in ['cache','models','checkpoints','tables','figures']: (OUT/sub).mkdir(parents=True,exist_ok=True)
    inventories=[ROOT/'outputs/research/variable_inventory/v1/inventario_1557.csv',ROOT/'outputs/research/experimental_variable_inventory/v1/variables_adicionales.csv']
    a,b=[pd.read_csv(p) for p in inventories]
    names=list(a.variable)+list(b.variable);assert len(names)==len(set(names))==1867
    reference_path=ROOT/'outputs/modeling/family_7/boosting/v1/cache/train138_exact_features.parquet'
    ref=pd.read_parquet(reference_path);ids=ref.ID_POLIGONO
    matrix=pd.DataFrame(index=pd.Index(ids,name='ID_POLIGONO'));groups={}
    for _,r in a.iterrows():groups.setdefault(r.tabla_procesada,[]).append(r.variable)
    for _,r in b.iterrows():groups.setdefault(r.tablas.split('; ')[0],[]).append(r.variable)
    consumed=inventories+[reference_path]
    for path,cols in groups.items():
        p=ROOT/path;d=pd.read_parquet(p).set_index('ID_POLIGONO')
        assert d.index.is_unique and set(ids)<=set(d.index)
        matrix=matrix.join(d[cols].reindex(ids));consumed.append(p)
    matrix=matrix[names];assert matrix.shape==(138,1867)
    matrix.reset_index().to_parquet(OUT/'cache/train138_1867.parquet',index=False)
    ref.to_parquet(OUT/'cache/labels_and_metadata.parquet',index=False)
    splitpath=ROOT/'outputs/modeling/family_7/boosting/v1/cache/frozen65_splits.joblib'
    splits=joblib.load(splitpath);assert len(splits)==65
    joblib.dump(splits,OUT/'cache/frozen65_splits.joblib');consumed.append(splitpath)
    reference_oof=ROOT/'outputs/modeling/family_7/boosting/v1/tables/oof_predictions.parquet'
    pd.read_parquet(reference_oof).to_parquet(OUT/'cache/reference_oof.parquet',index=False);consumed.append(reference_oof)
    pd.DataFrame({'variable':names}).to_csv(OUT/'tables/input_columns.csv',index=False)
    cfg=dict(experiment='PLS1867',n_inputs=1867,components=GRID,selection='complete inner OOF RMSE; ties rounded 10 decimals prefer fewer components',outer_folds=65,inner='original frozen inner splits',preprocessing='train-only numeric median (empty=0), categorical one-hot unknown=all-zero, train-only constants removed and StandardScaler; PLS scale=False',target='PLS centers target internally using training labels only; native t/ha',duplicates='retained intentionally; repeated descriptors may overweight signals',categorical_caution='includes locality names and soil map labels/summary; these may proxy geography',scope='whole-season Apr-Oct2025; exploratory, no final full138 fit, no PRED inference, no champion modification',source_hash=sha(__file__),inputs={str(p.relative_to(ROOT)):sha(p) for p in dict.fromkeys(consumed)})
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')

def fold(index):
    start=time.perf_counter()
    x=pd.read_parquet(OUT/'cache/train138_1867.parquet').set_index('ID_POLIGONO')
    t=pd.read_parquet(OUT/'cache/labels_and_metadata.parquet')
    protocol,repeat,fo,tr,va,inner=joblib.load(OUT/'cache/frozen65_splits.joblib')[index]
    y=t.RENDIMIENTO_T_HA.to_numpy(float);a=x.iloc[tr]; candidates={k:np.full(len(tr),np.nan) for k in GRID};warn=[];fits=0
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for itr,iva in inner:
            rep=TrainRepresentation().fit(a.iloc[itr]);z=rep.transform(a.iloc[itr]);v=rep.transform(a.iloc[iva])
            for k in GRID:
                if k>min(z.shape[0]-1,z.shape[1]):continue
                m=PLSRegression(n_components=k,scale=False,max_iter=1000,tol=1e-7).fit(z,y[np.asarray(tr)[itr]])
                candidates[k][iva]=m.predict(v).reshape(-1);fits+=1
        scores=[dict(components=k,**metrics(y[tr],p)) for k,p in candidates.items() if np.isfinite(p).all()]
        if not scores:raise ValueError('No supported candidate')
        selected=min(scores,key=lambda r:(round(r['rmse'],10),r['components']))['components']
        rep=TrainRepresentation().fit(a);m=PLSRegression(n_components=selected,scale=False,max_iter=1000,tol=1e-7).fit(rep.transform(a),y[tr]);fits+=1
        pred=m.predict(rep.transform(x.iloc[va])).reshape(-1)
        warn=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]
    assert np.isfinite(pred).all()
    key=dict(experiment='PLS1867',protocol=protocol,repeat=repeat,fold=fo)
    rows=[{**key,'ID_POLIGONO':pid,'y_true':float(v),'y_pred':float(p)} for pid,v,p in zip(t.iloc[va].ID_POLIGONO,y[va],pred)]
    reg={**key,'components':selected,'encoded_retained':len(rep.names),'fits':fits,'seconds':time.perf_counter()-start,'warnings':json.dumps(warn),'train_ids':json.dumps(t.iloc[tr].ID_POLIGONO.tolist()),'validation_ids':json.dumps(t.iloc[va].ID_POLIGONO.tolist())}
    joblib.dump(dict(representation=rep,pls=m,columns=list(x),registry=reg),OUT/'models'/f'{protocol}_{repeat}_{fo}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,registry=reg,tuning=[{**key,**r} for r in scores]),OUT/'checkpoints'/f'{index:02d}.joblib',compress=3)
    print(f'PLS fold {index+1}/65 {protocol} k={selected}',flush=True)

def finish(wall):
    packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    p=pd.DataFrame([r for pack in packs for r in pack['predictions']]);assert len(p)==1794
    p.to_parquet(OUT/'tables/oof_predictions.parquet',index=False);p.to_csv(OUT/'tables/oof_predictions.csv',index=False)
    registry=pd.DataFrame([pack['registry'] for pack in packs]);registry.to_csv(OUT/'tables/fit_registry.csv',index=False)
    pd.DataFrame([r for pack in packs for r in pack['tuning']]).to_csv(OUT/'tables/inner_selection.csv',index=False)
    ref=pd.read_parquet(OUT/'cache/reference_oof.parquet');ref=ref[ref.experiment.isin(['C-T3','F5-01','F6-E0','F7-00','F7-01','CHAMPION'])]
    allp=pd.concat([p,ref],ignore_index=True);r=[]
    for (exp,pro,re),g in allp.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.nunique()==138
        r.append(dict(experiment=exp,protocol=pro,repeat=re,**metrics(g.y_true,g.y_pred)))
    rm=pd.DataFrame(r);rm.to_csv(OUT/'tables/metrics_per_repeat.csv',index=False)
    summary=rm.groupby(['experiment','protocol'])[['rmse','mae','bias']].mean().reset_index();summary.to_csv(OUT/'tables/metrics_summary.csv',index=False)
    paired=[]
    for exp in ref.experiment.unique():
        q=p.merge(ref[ref.experiment.eq(exp)],on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('_pls','_ref'),validate='one_to_one')
        assert np.allclose(q.y_true_pls,q.y_true_ref)
        for (pro,re),g in q.groupby(['protocol','repeat']):
            ma=metrics(g.y_true_pls,g.y_pred_pls);mb=metrics(g.y_true_ref,g.y_pred_ref)
            paired.append(dict(reference=exp,protocol=pro,repeat=re,**{f'delta_{k}':ma[k]-mb[k] for k in ma},fraction_improved=float(np.mean(abs(g.y_pred_pls-g.y_true_pls)<abs(g.y_pred_ref-g.y_true_ref)))))
    pd.DataFrame(paired).to_csv(OUT/'tables/paired_comparisons.csv',index=False)
    t=pd.read_parquet(OUT/'cache/labels_and_metadata.parquet');q=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');regional=[]
    for col in ['Estado','Municipio','fold']:
        for (pro,re,group),g in q.groupby(['protocol','repeat',col]):regional.append(dict(protocol=pro,repeat=re,group_type=col,group=group,n=len(g),**metrics(g.y_true,g.y_pred)))
    pd.DataFrame(regional).to_csv(OUT/'tables/regional_metrics.csv',index=False)
    from matplotlib import pyplot as plt
    fig,axes=plt.subplots(1,4,figsize=(15,4))
    for ax,(pro,g) in zip(axes,p.groupby('protocol')):
        avg=g.groupby('ID_POLIGONO')[['y_true','y_pred']].mean();ax.scatter(avg.y_true,avg.y_pred,s=15,alpha=.6);ax.plot([2,5.6],[2,5.6],color='gray');ax.set(title=pro,xlabel='Observado (t/ha)',ylabel='OOF (t/ha)')
    fig.tight_layout();fig.savefig(OUT/'figures/oof_scatter.png',dpi=150);plt.close(fig)
    lines=['# PLS1867: experimento exploratorio','', '1,867 descriptores de partida, conservando redundancias; categorías codificadas y columnas constantes eliminadas solo dentro de entrenamiento. Las dimensiones efectivas pueden variar por fold. 65 particiones externas originales, número de componentes seleccionado con OOF internas originales completas. Métricas externas sobre 138 OOF por repetición y media de las 10 repeticiones aleatorias; no media de métricas por fold.','', '| Modelo | Protocolo | RMSE | MAE | Sesgo |','|---|---|---:|---:|---:|']
    lines += [f'| {r.experiment} | {r.protocol} | {r.rmse:.4f} | {r.mae:.4f} | {r.bias:.4f} |' for r in summary.itertuples()]
    lines += ['', 'Todos los comparadores se recuperaron de OOF compatibles, sin reajustarlos. Champion solo dispone de referencia aleatoria compatible. Los resultados son exploratorios sobre una base repetidamente investigada; no implican superioridad estadística. Categorías de localidades y suelo pueden actuar como proxies territoriales. Duplicados exactos y otras redundancias cambian el peso relativo en PLS. No hubo selección por resultados externos ni ajuste final sobre 138 ni predicciones PRED.','',f'Componentes seleccionados: {registry.components.value_counts().sort_index().to_dict()}. Dimensiones retenidas: {registry.encoded_retained.min()}–{registry.encoded_retained.max()}. Ajustes: {registry.fits.sum()}; tiempo de ejecución: {wall:.1f} s. Advertencias por fold en fit_registry.csv.']
    (OUT/'informe.md').write_text('\n'.join(lines),encoding='utf-8')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert cfg['source_hash']==sha(__file__)
    for path,h in cfg['inputs'].items():assert sha(ROOT/path)==h
    artifacts={str(f.relative_to(ROOT)):sha(f) for f in OUT.rglob('*') if f.is_file() and f.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(dict(status='complete',n_oof=1794,n_outer_models=65,n_fits=int(registry.fits.sum()),wall_seconds=wall,artifacts=artifacts),indent=2),encoding='utf-8')
    print(summary.to_string(index=False),flush=True)

def run():
    prepare();start=time.perf_counter()
    joblib.Parallel(n_jobs=4,backend='loky',inner_max_num_threads=1)(joblib.delayed(fold)(i) for i in range(65))
    finish(time.perf_counter()-start)
