"""Exploratory error-group diagnosis; training-only classification of hard errors."""
from pathlib import Path
import re,hashlib,warnings
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.feature_selection import f_classif
from sklearn.linear_model import LogisticRegression

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/research/difficult_quartile/v1'
SOURCE=ROOT/'outputs/research/case_outliers_and_model_residual_comparison/v1/tables/all_parcel_errors.csv'
CALIBRATION=ROOT/'outputs/modeling/neighbor_signal_linear/v1'


def labels_for_errors(errors,cutoff):
    """0=remaining,1=hard overprediction,2=hard underprediction."""
    errors=np.asarray(errors);return np.where(abs(errors)>=cutoff,np.where(errors>0,1,2),0)


def family(feature):
    s=feature.lower()
    # A temporal NDVI/MSI slope is not a terrain slope. Use physical namespaces.
    if any(v in s for v in ['topo','terrain','tpi','curvature','elev','altitud','relief']) or s.startswith(('p_slope','slope_degrees')):return 'Relieve/topografía'
    if any(v in s for v in ['soil','suelo','edaph','soilgrid']):return 'Suelo'
    if any(v in s for v in ['geol','geo250','phys_','physiograph']):return 'Geología/fisiografía'
    if any(v in s for v in ['wet','humedal','waterbody']):return 'Humedales/agua cartográfica'
    if any(v in s for v in ['precip','climate','rain','tmax','tmin','tmean','dtr']):return 'Clima'
    if any(v in s for v in ['ndwi','msi','nddi','water']):return 'Señal satelital de humedad'
    if any(v in s for v in ['ndvi','evi','lai','fapar','savi','vigor']):return 'Vegetación/heterogeneidad'
    if any(v in s for v in ['centroid','distance','area','perimeter','compactness','loc_']):return 'Geometría/contexto geográfico'
    return 'Otras señales'


def load_inventory(ids):
    """X only; exact numeric aliases are collapsed before associations/classification."""
    paths={
        'OWN1867':ROOT/'outputs/modeling/experimental_pls1867/v1/cache/train138_1867.parquet',
        'GEOC1831':ROOT/'outputs/research/geoc_variable_signal_audit/v1/variables_1831_197_sin_target.parquet',
        'PHYSICAL':ROOT/'outputs/modeling/physical_representation/v1/cache/features138_target_free.parquet',
        'ENGINEERED':ROOT/'outputs/modeling/signal_feature_engineering/v1/cache/features_train138_target_free.parquet'}
    master=pd.read_csv(ROOT/'outputs/research/variable_inventory/v1/inventario_1557.csv').set_index('variable')
    extra=pd.read_csv(ROOT/'outputs/research/experimental_variable_inventory/v1/variables_adicionales.csv').set_index('variable')
    geo=pd.read_csv(ROOT/'outputs/research/geoc_variable_signal_audit/v1/inventario_1831_geoc.csv').set_index('feature')
    numeric={};categorical={};meta=[];aliases=[];hashes={}
    for source,path in paths.items():
        frame=pd.read_parquet(path).set_index('ID_POLIGONO').loc[ids]
        for feature in frame:
            assert not any(v in feature.lower() for v in ['rendimiento','y_true','y_pred'])
            name=source+'::'+feature;s=frame[feature];description='';origin=''
            if source=='OWN1867' and feature in master.index:
                description=str(master.loc[feature,'descripcion_documentada']);origin=str(master.loc[feature,'fuente'])
            elif source=='OWN1867' and feature in extra.index:
                description=str(extra.loc[feature,'definicion_documentada']);origin=str(extra.loc[feature,'grupo'])
            elif source=='GEOC1831' and feature in geo.index:
                description=str(geo.loc[feature,'description']);origin=str(geo.loc[feature,'root_sources'])
            text=feature.lower()
            quality=any(v in text for v in ['n_obs','valid_count','coverage','missing','support','n_years','key_found','cloud','max_gap','n_valid','all_missing'])
            identifier=bool(re.search(r'centroid|municip|estado|(^|_)lat(itude)?($|_)|(^|_)lon(gitude)?($|_)|nearest_name|(^|_)id($|_)',text))
            entry=dict(feature=name,original_feature=feature,source=source,family=family(feature),description=description,origin=origin,quality=quality,geographic_identifier=identifier)
            if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s):
                values=pd.to_numeric(s,errors='coerce').to_numpy(float);values[~np.isfinite(values)]=np.nan
                # Numeric equality exact, including missing locations. No rounding-based merging.
                stable=values.copy();stable[np.isnan(stable)]=np.nan;stable[stable==0]=0.
                key=hashlib.sha256(stable.tobytes()).hexdigest()
                if key in hashes:
                    aliases.append(dict(alias=name,canonical=hashes[key],source=source,original_feature=feature));continue
                hashes[key]=name;numeric[name]=values;entry['kind']='numeric';entry['n_unique']=s.nunique();entry['missing_fraction']=np.mean(~np.isfinite(values))
            else:
                categorical[name]=s.to_numpy();entry['kind']='categorical';entry['n_unique']=s.nunique();entry['missing_fraction']=s.isna().mean()
            meta.append(entry)
    return pd.DataFrame(numeric,index=pd.Index(ids,name='ID_POLIGONO')),pd.DataFrame(categorical,index=pd.Index(ids,name='ID_POLIGONO')),pd.DataFrame(meta),pd.DataFrame(aliases),paths


def effect(a,b):
    """Vectorized Cliff's delta: positive means higher values in group A."""
    a=np.asarray(a,float);b=np.asarray(b,float)
    na=np.isfinite(a).sum(axis=0);nb=np.isfinite(b).sum(axis=0)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore');test=mannwhitneyu(a,b,axis=0,nan_policy='omit',alternative='two-sided',method='asymptotic')
    pairs=na*nb;delta=np.divide(2*test.statistic,pairs,out=np.full(pairs.shape,np.nan),where=pairs>0)-1
    return delta,np.asarray(test.pvalue),na,nb


def conditional_effect(x,a,b,groups):
    """Within-group comparisons only; also equal-group weight to expose dominance."""
    weighted=np.zeros(x.shape[1]);weights=weighted.copy();total=weighted.copy();count=weighted.copy()
    for group in np.unique(groups):
        aa=a&(groups==group);bb=b&(groups==group)
        if aa.sum()<2 or bb.sum()<2:continue
        delta,_,na,nb=effect(x[aa],x[bb]);valid=(na>=2)&(nb>=2)&np.isfinite(delta)
        w=na*nb;weighted[valid]+=delta[valid]*w[valid];weights[valid]+=w[valid];total[valid]+=delta[valid];count[valid]+=1
    return np.divide(weighted,weights,out=np.full_like(weights,np.nan),where=weights>0),np.divide(total,count,out=np.full_like(count,np.nan),where=count>0),count


def bh(values):
    p=np.asarray(values,float);out=np.full(p.shape,np.nan);valid=np.flatnonzero(np.isfinite(p));order=valid[np.argsort(p[valid])];n=len(order)
    if n:out[order]=np.minimum(1,np.minimum.accumulate((p[order]*n/np.arange(1,n+1))[::-1])[::-1])
    return out


class DiagnosticClassifier:
    """Fixed conservative logistic diagnostic; all feature selection is train-only."""
    def __init__(self,k=6):self.k=k
    def fit(self,x,y):
        x=np.asarray(x,float);y=np.asarray(y,int);self.classes=np.array([0,1,2]);self.prior=np.bincount(y,minlength=3)/len(y);self.model=None;self.selected=np.array([],int)
        self.median=np.array([np.median(c[np.isfinite(c)]) if np.isfinite(c).any() else 0. for c in x.T]);z=np.where(np.isfinite(x),x,self.median)
        self.mean=z.mean(axis=0);self.scale=np.maximum(z.std(axis=0),1e-8);z=(z-self.mean)/self.scale
        support=(np.std(z,axis=0)>1e-8)&(np.mean(np.isfinite(x),axis=0)>=.8)
        if len(np.unique(y))<2 or not support.any():return self
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');scores=np.nan_to_num(f_classif(z,y)[0],nan=-np.inf,posinf=1e12,neginf=-np.inf)
        scores[~support]=-np.inf;chosen=[]
        for j in np.argsort(-scores,kind='stable'):
            if not np.isfinite(scores[j]):continue
            if chosen and np.max(abs(z[:,chosen].T@z[:,j]/len(z)))>.9:continue
            chosen.append(int(j))
            if len(chosen)>=self.k:break
        self.selected=np.array(chosen,int)
        if len(chosen):self.model=LogisticRegression(C=.1,class_weight='balanced',max_iter=10000,solver='lbfgs',random_state=2026).fit(z[:,chosen],y)
        return self
    def predict_proba(self,x):
        x=np.asarray(x,float)
        if self.model is None:return np.tile(self.prior,(len(x),1))
        z=(np.where(np.isfinite(x),x,self.median)-self.mean)/self.scale;p=np.zeros((len(x),3));p[:,self.model.classes_]=self.model.predict_proba(z[:,self.selected]);return p
