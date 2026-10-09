"""Utilidades de Etapa 4: CV congelada, representaciones y transformadores."""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[2]
FEATURE_DIR=ROOT/'data/processed/family_1/features'
STAGE=ROOT/'outputs/modeling/family_1/stage4'
for p in ['splits','screening/checkpoints','stability','correlation_communities','reports']:(STAGE/p).mkdir(parents=True,exist_ok=True)
ID='ID_POLIGONO'; TARGET='RENDIMIENTO_T_HA'; SEED=2026

def load_xy():
    x=pd.read_parquet(FEATURE_DIR/'family1_features_all.parquet')
    y=pd.read_csv(ROOT/'data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv')[[ID,TARGET]].dropna()
    d=y.merge(x,on=ID,how='inner',validate='one_to_one').sort_values(ID).reset_index(drop=True)
    if len(d)!=138: raise ValueError(f'Se esperaban 138 TRAIN y se encontraron {len(d)}')
    return d[ID],d.drop(columns=[ID,TARGET]),d[TARGET]

def representations(columns):
    cols=set(columns)
    core_files=['sentinel_features_core.parquet','landsat_features.parquet','planet_features.parquet','climate_features.parquet','history_features.parquet','anomaly_features.parquet','topography_basic_features.parquet']
    x0=[]
    for f in core_files:
        x0 += [c for c in pd.read_parquet(FEATURE_DIR/f).columns if c!=ID and c in cols]
    return {'CORE':list(dict.fromkeys(x0)),'ALL':list(columns)}

class CommunityPCA(BaseEstimator,TransformerMixin):
    """Imputa/escala y hace PCA local en comunidades de correlación.

    Los componentes conectados grandes se subdividen con greedy modularity para
    reducir el chain effect. Los nodos aislados se conservan escalados.
    """
    def __init__(self,threshold=.98,variance=.95,min_community=2):
        self.threshold=threshold;self.variance=variance;self.min_community=min_community
    def fit(self,X,y=None):
        import networkx as nx
        self.feature_names_in_=np.asarray(getattr(X,'columns',[f'x{i}' for i in range(np.asarray(X).shape[1])]))
        self.imputer_=SimpleImputer(strategy='median'); z=self.imputer_.fit_transform(X)
        self.scaler_=StandardScaler(); z=self.scaler_.fit_transform(z)
        corr=np.nan_to_num(np.corrcoef(z,rowvar=False)); g=nx.Graph();g.add_nodes_from(range(z.shape[1])); ii,jj=np.where(np.triu(abs(corr)>=self.threshold,1));g.add_edges_from(zip(ii.tolist(),jj.tolist()))
        groups=[]
        for comp in nx.connected_components(g):
            sub=g.subgraph(comp)
            if len(comp)>2 and sub.number_of_edges()>1:
                groups.extend([sorted(c) for c in nx.algorithms.community.greedy_modularity_communities(sub)])
            else: groups.append(sorted(comp))
        self.groups_=groups;self.models_=[];self.metadata_=[]
        for k,idx in enumerate(groups):
            if len(idx)>=self.min_community:
                p=PCA(n_components=self.variance,svd_solver='full').fit(z[:,idx]);self.models_.append(p);nc=p.n_components_;ev=float(p.explained_variance_ratio_.sum())
            else:p=None;self.models_.append(None);nc=len(idx);ev=1.0
            self.metadata_.append({'community_id':k,'original_features':'|'.join(self.feature_names_in_[idx]),'n_features':len(idx),'n_components':nc,'explained_variance':ev,'threshold':self.threshold,'variance_target':self.variance})
        return self
    def transform(self,X):
        z=self.scaler_.transform(self.imputer_.transform(X)); parts=[]
        for idx,p in zip(self.groups_,self.models_): parts.append(p.transform(z[:,idx]) if p is not None else z[:,idx])
        return np.column_stack(parts)

class CorrelationPruner(BaseEstimator,TransformerMixin):
    """Imputación y pruning no supervisado aprendido sólo durante ``fit``.

    Prioridad: menor missingness, CORE antes que otros niveles, menor razón
    max-abs/IQR (estabilidad ante extremos) y nombre lexicográfico.
    """
    def __init__(self,threshold=.98,scale=False,variance_epsilon=1e-10,dictionary_path=None):
        self.threshold=threshold;self.scale=scale;self.variance_epsilon=variance_epsilon;self.dictionary_path=dictionary_path
    def fit(self,X,y=None):
        frame=pd.DataFrame(X).copy();self.feature_names_in_=np.asarray(getattr(X,'columns',[f'x{i}' for i in range(frame.shape[1])]))
        frame.columns=self.feature_names_in_;self.missing_fraction_=frame.isna().mean()
        self.imputer_=SimpleImputer(strategy='median');z=self.imputer_.fit_transform(frame)
        self.scaler_=StandardScaler().fit(z) if self.scale else None
        work=self.scaler_.transform(z) if self.scaler_ is not None else z
        std=np.std(work,axis=0);valid=np.flatnonzero(np.isfinite(std)&(std>self.variance_epsilon));self.near_zero_removed_=sorted(set(range(work.shape[1]))-set(valid))
        q25,q75=np.quantile(work[:,valid],[.25,.75],axis=0);iqr=q75-q25;maxabs=np.max(abs(work[:,valid]),axis=0);instability=maxabs/np.maximum(iqr,1e-12)
        levels={}
        path=Path(self.dictionary_path) if self.dictionary_path else FEATURE_DIR/'family1_feature_dictionary.csv'
        if path.exists():
            dd=pd.read_csv(path).set_index('feature_name');levels=dd.core_or_extended.to_dict()
        order=sorted(range(len(valid)),key=lambda k:(self.missing_fraction_.iloc[valid[k]],0 if levels.get(self.feature_names_in_[valid[k]])=='CORE' else 1,instability[k],self.feature_names_in_[valid[k]]))
        corr=np.nan_to_num(np.corrcoef(work[:,valid],rowvar=False));kept_local=[]
        for k in order:
            if not kept_local or not np.any(np.abs(corr[k,kept_local])>=self.threshold):kept_local.append(k)
        self.retained_indices_=valid[np.asarray(kept_local,dtype=int)];self.retained_features_=self.feature_names_in_[self.retained_indices_].tolist();self.removed_features_=[c for i,c in enumerate(self.feature_names_in_) if i not in set(self.retained_indices_)]
        return self
    def transform(self,X):
        z=self.imputer_.transform(X);z=self.scaler_.transform(z) if self.scaler_ is not None else z
        return z[:,self.retained_indices_]

def save_splits(ids):
    from sklearn.model_selection import RepeatedKFold
    path=STAGE/'splits/outer_splits.csv'
    if path.exists():
        old=pd.read_csv(path)
        flat=set(sum([json.loads(v) for v in old.train_ID_POLIGONO],[])+sum([json.loads(v) for v in old.validation_ID_POLIGONO],[]))
        if flat!=set(ids): raise ValueError('Los splits persistidos no corresponden a los IDs actuales')
        return old
    rk=RepeatedKFold(n_splits=5,n_repeats=10,random_state=SEED);rows=[]
    for k,(tr,va) in enumerate(rk.split(ids)):
        rows.append({'repeat':k//5+1,'fold':k%5+1,'train_ID_POLIGONO':json.dumps(ids.iloc[tr].tolist()),'validation_ID_POLIGONO':json.dumps(ids.iloc[va].tolist()),'random_state':SEED})
    pd.DataFrame(rows).to_csv(path,index=False)
    (STAGE/'splits/inner_split_config.json').write_text(json.dumps({'type':'KFold','n_splits':4,'shuffle':True,'random_state_rule':'2026 + outer_split_index','outer_validation_never_used_in_preprocessing_or_tuning':True},indent=2),encoding='utf-8')
    return pd.DataFrame(rows)
