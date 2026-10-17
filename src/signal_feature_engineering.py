"""Frozen, target-free temporal representations and nested residual adjustments."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNet

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/modeling/signal_feature_engineering/v1'
WINDOWS={'early':[5,6],'middle':[7,8],'late':[9,10]}


def historical_z(current,mean,sd):
    """Three-year sample SD with a fixed .02 index-unit floor; no Y."""
    return np.clip((current-mean)/np.maximum(sd,.02),-6,6)


def temporal_summaries(evi,ndvi,gap):
    """Columns April..October; all monthly medians required for each summary."""
    evi=np.asarray(evi,float);ndvi=np.asarray(ndvi,float);gap=np.asarray(gap,float)
    early=np.mean(evi[:,1:3],axis=1);middle=np.mean(evi[:,3:5],axis=1);late=np.mean(evi[:,5:7],axis=1)
    rel=np.clip(gap/np.maximum(abs(ndvi),.1),0,5)
    valid=np.isfinite(rel[:,1:]).all(axis=1)
    peak=np.full(len(rel),np.nan);persist=peak.copy()
    if valid.any():
        q=rel[valid,1:];mx=q.max(axis=1)
        peak[valid]=np.where(mx>1e-12,np.argmax(q,axis=1)/5,np.nan)
        persist[valid]=np.divide(q.mean(axis=1),mx,out=np.zeros_like(mx),where=mx>1e-12)
    return np.column_stack([middle-early,late-middle,np.mean(rel[:,1:],axis=1),
                            np.mean(rel[:,5:7],axis=1)-np.mean(rel[:,1:3],axis=1),peak,persist])


def build_features(ids):
    """Build only requested TRAIN IDs; never load Y or impute using PRED."""
    cal=pd.read_parquet(ROOT/'data/processed/agronomic_calendar_set/v1/current_history_delta_197_target_free.parquet').set_index('ID_POLIGONO').loc[ids]
    own=pd.read_parquet(ROOT/'outputs/modeling/experimental_pls1867/v1/cache/train138_1867.parquet').set_index('ID_POLIGONO').loc[ids]
    x=pd.DataFrame(index=pd.Index(ids,name='ID_POLIGONO'));dictionary=[];blocks={}
    def add(name,values,block,formula):
        x[name]=np.asarray(values,float);dictionary.append(dict(feature=name,block=block,formula=formula))
    for index in ['ndvi','evi','ndwi']:
        for window,label in [('sowing_may_jun','early'),('post_jul_aug','middle')]:
            stem=f'CAL_S2_{index}_{window}';names=[]
            for prefix,short in [('CURRENT_','current'),('HIST_MEAN_','mean'),('HIST_SD_','sd')]:
                name=f'H_{index}_{label}_{short}';add(name,cal[prefix+stem],'H_RAW','Existing calendar: '+prefix+stem);names.append(name)
            add(f'HZ_{index}_{label}',historical_z(*(x[c] for c in names)),'H_ENG','clip((2025 - mean2022:2024)/max(sampleSD2022:2024,.02),-6,6); require 3 history years')
    satpath=ROOT/'data/processed/family_1/timeseries/sentinel_timeseries.parquet'
    s=pd.read_parquet(satpath,columns=['ID_POLIGONO','year','month','evi_promedio','ndvi_promedio','ndvi_min'])
    s=s[s.ID_POLIGONO.isin(ids)&s.year.eq(2025)&s.month.between(4,10)].copy()
    s['gap']=s.ndvi_promedio-s.ndvi_min
    # A materially inverted mean/min pair is invalid, never repaired with target information.
    invalid=(s.gap < -1e-8);s.loc[invalid,'gap']=np.nan;s['gap']=s.gap.clip(lower=0)
    monthly=s.groupby(['ID_POLIGONO','month'])[['evi_promedio','ndvi_promedio','gap']].median()
    arrays=[]
    for col,short in [('evi_promedio','evi'),('ndvi_promedio','ndvi'),('gap','gap')]:
        a=monthly[col].unstack('month').reindex(index=ids,columns=range(4,11)).to_numpy(float);arrays.append(a)
        for j,month in enumerate(range(4,11)):add(f'T_{short}_{month:02d}',a[:,j],'T_RAW','2025 monthly median '+col+'; no interpolation')
    temporal_names=['evi_early_change','evi_late_change','relative_gap_mean','relative_gap_late_change','relative_gap_peak_time','relative_gap_persistence']
    vals=temporal_summaries(*arrays)
    formulas=['EVI July-Aug minus May-Jun','EVI Sep-Oct minus July-Aug','mean May-Oct gap/max(abs(NDVImean),.1), clipped 0..5','relative gap Sep-Oct minus May-Jun','earliest peak relative gap month May-Oct rescaled (month-5)/5; zero gap => missing','mean/max relative gap May-Oct; zero gap => 0']
    for j,(name,formula) in enumerate(zip(temporal_names,formulas)):add('TE_'+name,vals[:,j],'T_ENG',formula)
    for name,values,formula in [('P_tpi',own.TOPO_ADV_tpi_3x3_mean,'Original TPI3x3 mean'),('P_slope',own.TOPO_BASIC_slope_mean,'Original mean slope'),('P_water',x.HZ_ndwi_middle,'Own-parcel historical NDWI anomaly July-Aug'),('P_evi_change',x.TE_evi_early_change,'EVI July-Aug minus May-Jun')]:add(name,values,'P_RAW',formula)
    for block in ['H_RAW','H_ENG','T_RAW','T_ENG','P_RAW']:
        blocks[block]=[d['feature'] for d in dictionary if d['block']==block]
    blocks['P_ENG']=blocks['P_RAW'].copy() # Four products/splits are fitted inside each training context.
    blocks['SHIFT']=[]
    support=pd.DataFrame([dict(feature=c,missing_fraction=x[c].isna().mean(),n_unique=x[c].nunique(),minimum=x[c].min(),maximum=x[c].max()) for c in x])
    quality=dict(inverted_ndvi_pairs=int(invalid.sum()),temporal_monthly_rows=len(monthly),historical_reference_years=[2022,2023,2024],history_sd_floor=.02,relative_gap_ndvi_floor=.1,no_interpolation=True)
    return x.reset_index(),blocks,pd.DataFrame(dictionary),support,quality


class EngineeringAdjustment:
    """Training-only imputation/scaling; explicit interaction hierarchy and null."""
    def __init__(self,block,columns,alpha=1.,l1_ratio=.9,amplitude=0.):
        self.block=block;self.columns=list(columns);self.alpha=alpha;self.l1_ratio=l1_ratio;self.amplitude=amplitude
    def fit(self,frame,y,base):
        raw=frame[self.columns].to_numpy(float)
        self.medians=np.array([np.median(c[np.isfinite(c)]) if np.isfinite(c).any() else 0. for c in raw.T])
        raw=np.where(np.isfinite(raw),raw,self.medians)
        self.parent_scale=np.maximum(raw.std(axis=0),1e-8)
        z=self.expand(raw);self.mean=z.mean(axis=0);self.scale=np.maximum(z.std(axis=0),1e-8);self.support=z.std(axis=0)>1e-8
        self.feature_names=self.columns.copy()
        if self.block=='P_ENG':self.feature_names+=['tpi_negative','tpi_negative_x_water','tpi_positive_x_water','slope_x_evi_change']
        self.model=None;self.offset=0.;self.residual=np.asarray(y)-np.asarray(base)
        if self.amplitude:
            self.offset=float(self.residual.mean())
            if self.support.any():self.model=ElasticNet(alpha=self.alpha,l1_ratio=self.l1_ratio,fit_intercept=True,max_iter=200000,random_state=2026).fit(((z-self.mean)/self.scale)[:,self.support],self.residual)
        return self
    def expand(self,raw):
        if self.block!='P_ENG':return raw
        # No Y, no validation-wide centering; retain raw parents for hierarchy.
        tpi=np.clip(raw[:,0]/self.parent_scale[0],-6,6);negative=np.maximum(-tpi,0);positive=np.maximum(tpi,0)
        water=np.clip(raw[:,2],-6,6);slope=np.clip(raw[:,1]/self.parent_scale[1],-6,6);evi=np.clip(raw[:,3]/self.parent_scale[3],-6,6)
        return np.column_stack([raw,negative,negative*water,positive*water,slope*evi])
    def predict(self,frame,base):
        base=np.asarray(base)
        if not self.amplitude:return base.copy()
        raw=frame[self.columns].to_numpy(float);raw=np.where(np.isfinite(raw),raw,self.medians);z=self.expand(raw)
        delta=self.model.predict(((z-self.mean)/self.scale)[:,self.support]) if self.model is not None else np.full(len(frame),self.offset)
        return base+self.amplitude*np.clip(delta,-.5,.5)
