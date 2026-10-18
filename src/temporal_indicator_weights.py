"""Temporal X-only indicators and bounded, cross-fitted correction weights."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNet

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/modeling/temporal_indicator_weights/v1'
ENGINEERING=ROOT/'outputs/modeling/signal_feature_engineering/v1'
BASE_CALIBRATION=ROOT/'outputs/modeling/neighbor_signal_linear/v1'
PARENTS=['P_tpi','P_slope','P_water','P_evi_change']
INDICATORS=['I_history_ndvi_floor','I_history_fapar_floor','I_gap_excess_intensity','I_gap_excess_persistence','I_gap_volatility_anomaly','I_msi_upper_excess','I_evi_peak_shape_anomaly','I_sensor_shape_disagreement','I_slope_min']
ALPHA=.01
L1_RATIO=.5
AMPLITUDE=.5


def positive_persistence(z):
    """Effective fraction of active months; no target or arbitrary event threshold."""
    z=np.maximum(np.asarray(z,float),0);den=z.shape[1]*np.sum(z*z,axis=1)
    return np.divide(np.sum(z,axis=1)**2,den,out=np.zeros(len(z)),where=den>1e-12)


def peak_shape(evi):
    evi=np.asarray(evi,float)
    return (np.max(evi,axis=1)-np.median(evi,axis=1))/np.maximum(np.ptp(evi,axis=1),.05)


def derive_indicators(ndvi_min,fapar_min,gap,msi_upper,evi,planet_evi,slope_min):
    """Annual input shape (n,4,6), years2022..2025, monthsMay..October."""
    def z_current(a,floor):
        old=np.asarray(a)[:,:3,:];return np.clip((a[:,3,:]-np.mean(old,axis=1))/np.maximum(np.std(old,axis=1,ddof=1),floor),-6,6)
    excess=np.maximum(z_current(gap,.05),0);vol=np.std(gap,axis=2)
    shape=np.column_stack([peak_shape(evi[:,j,:]) for j in range(4)])
    left=evi[:,3,:];right=np.asarray(planet_evi,float);lc=left-left.mean(axis=1)[:,None];rc=right-right.mean(axis=1)[:,None];den=np.sqrt(np.sum(lc*lc,axis=1)*np.sum(rc*rc,axis=1));cor=np.divide(np.sum(lc*rc,axis=1),den,out=np.full(len(left),np.nan),where=den>1e-10)
    vals=np.column_stack([
        np.mean(np.mean(ndvi_min[:,:3,:],axis=2),axis=1),
        np.mean(np.mean(fapar_min[:,:3,:],axis=2),axis=1),
        np.mean(excess,axis=1),positive_persistence(excess),
        np.clip((vol[:,3]-np.mean(vol[:,:3],axis=1))/np.maximum(np.std(vol[:,:3],axis=1,ddof=1),.05),-6,6),
        np.mean(np.maximum(z_current(msi_upper,.05),0),axis=1),
        np.clip((shape[:,3]-np.mean(shape[:,:3],axis=1))/np.maximum(np.std(shape[:,:3],axis=1,ddof=1),.05),-6,6),
        np.clip((1-cor)/2,0,1),np.asarray(slope_min,float)])
    # Missing monthly support is propagated, never converted to a zero event count.
    vals[~np.isfinite(excess).all(axis=1),3]=np.nan
    return vals


def build_features(ids):
    satpath=ROOT/'data/processed/family_1/timeseries/sentinel_timeseries.parquet'
    planetpath=ROOT/'data/processed/family_1/timeseries/planet_timeseries.parquet'
    cols=['ID_POLIGONO','year','month','ndvi_promedio','ndvi_min','fapar_min','msi_promedio','msi_max','evi_promedio']
    s=pd.read_parquet(satpath,columns=cols);s=s[s.ID_POLIGONO.isin(ids)&s.year.between(2022,2025)&s.month.between(5,10)].copy();s=s.replace([np.inf,-np.inf],np.nan)
    ng=s.ndvi_promedio-s.ndvi_min;mg=s.msi_max-s.msi_promedio
    quality=dict(negative_ndvi_gap_pairs=int((ng < -1e-8).sum()),negative_msi_gap_pairs=int((mg < -1e-8).sum()))
    s['relative_gap']=np.clip(ng.where(ng>=-1e-8).clip(lower=0)/np.maximum(abs(s.ndvi_promedio),.1),0,5)
    s['relative_msi_upper']=np.clip(mg.where(mg>=-1e-8).clip(lower=0)/np.maximum(abs(s.msi_promedio),.1),0,5)
    names=['ndvi_min','fapar_min','relative_gap','relative_msi_upper','evi_promedio'];monthly=s.groupby(['ID_POLIGONO','year','month'])[names].median();counts=s.groupby(['ID_POLIGONO','year','month'])[names].count()
    index=pd.MultiIndex.from_product([ids,range(2022,2026),range(5,11)],names=['ID_POLIGONO','year','month']);panel=monthly.reindex(index);arrays=[panel[c].to_numpy().reshape(len(ids),4,6) for c in names]
    planet=pd.read_parquet(planetpath,columns=['ID_POLIGONO','year','month','evi_promedio']);planet=planet[planet.ID_POLIGONO.isin(ids)&planet.year.eq(2025)&planet.month.between(5,10)];pm=planet.groupby(['ID_POLIGONO','month']).evi_promedio.median().unstack('month').reindex(index=ids,columns=range(5,11)).to_numpy(float)
    own=pd.read_parquet(ROOT/'outputs/modeling/experimental_pls1867/v1/cache/train138_1867.parquet').set_index('ID_POLIGONO').loc[ids]
    x=pd.DataFrame(derive_indicators(*arrays,pm,own.TOPO_BASIC_slope_min.to_numpy(float)),columns=INDICATORS,index=pd.Index(ids,name='ID_POLIGONO'))
    parents=pd.read_parquet(ENGINEERING/'cache/features_train138_target_free.parquet').set_index('ID_POLIGONO').loc[ids,PARENTS];x=pd.concat([parents,x],axis=1)
    dictionary=pd.DataFrame([
        dict(feature='I_history_ndvi_floor',formula='Mean2022:2024 of annual mean monthly median NDVImin May-Oct; require3 complete years'),
        dict(feature='I_history_fapar_floor',formula='Same as NDVI floor with FAPARmin'),
        dict(feature='I_gap_excess_intensity',formula='Mean positive z of2025 relative NDVI gap against own3year reference per calendar month; SD floor.05; clip z±6'),
        dict(feature='I_gap_excess_persistence',formula='(sum positive monthly z)^2/(6*sum z^2); zero if all zero, missing if support missing'),
        dict(feature='I_gap_volatility_anomaly',formula='z of2025 SD(relative monthly NDVI gap) against mean/SD of annual SD2022:2024; SD floor.05, clip±6'),
        dict(feature='I_msi_upper_excess',formula='Mean positive z of relative MSI(max-mean)/max(abs(mean),.1), clipped0..5 per acquisition; own monthly history SDfloor.05'),
        dict(feature='I_evi_peak_shape_anomaly',formula='Own-history z of (season max EVI - median EVI)/max(range,.05); complete monthly May-Oct; history SDfloor.05, clip±6'),
        dict(feature='I_sensor_shape_disagreement',formula='(1-Pearson correlation)/2 of6monthly EVI medians S2 and Planet2025; constant/missing series=>missing'),
        dict(feature='I_slope_min',formula='Preserved TOPO_BASIC_slope_min; context for temporal indicators, not a satellite temporal slope')])
    support=pd.DataFrame([dict(feature=c,missing_fraction=x[c].isna().mean(),n_unique=x[c].nunique(),minimum=x[c].min(),maximum=x[c].max()) for c in x])
    monthly_output=panel.reset_index();monthly_support=counts.reindex(index).reset_index();quality.update(dict(n_ids=len(ids),n_annual_month_slots=len(panel),history_years=[2022,2023,2024],months=[5,6,7,8,9,10],interpolation=False))
    return x.reset_index(),dictionary,support,monthly_output,monthly_support,quality


class FixedCorrection:
    """Same fixed conservative EN for C4, indicators and direct integration."""
    def __init__(self,columns):self.columns=list(columns)
    def fit(self,frame,residual):
        a=frame[self.columns].to_numpy(float);self.median=np.array([np.median(c[np.isfinite(c)]) if np.isfinite(c).any() else 0. for c in a.T]);a=np.where(np.isfinite(a),a,self.median);self.mean=a.mean(axis=0);self.scale=np.maximum(a.std(axis=0),1e-8);self.support=a.std(axis=0)>1e-8;self.model=None;self.offset=float(np.mean(residual))
        if self.support.any():self.model=ElasticNet(alpha=ALPHA,l1_ratio=L1_RATIO,fit_intercept=True,max_iter=200000,random_state=2026).fit(((a-self.mean)/self.scale)[:,self.support],residual)
        return self
    def predict_delta(self,frame):
        a=frame[self.columns].to_numpy(float);a=np.where(np.isfinite(a),a,self.median)
        pred=self.model.predict(((a-self.mean)/self.scale)[:,self.support]) if self.model is not None else np.full(len(frame),self.offset)
        return AMPLITUDE*np.clip(pred,-.5,.5)


class ContinuousWeight:
    """Weighted ridge on cross-fitted candidate deltas, clipped to [0,1]."""
    def __init__(self,kind='SHARED'):self.kind=kind
    def fit(self,frame,residual,delta):
        a=frame[INDICATORS].to_numpy(float);self.median=np.array([np.median(c[np.isfinite(c)]) if np.isfinite(c).any() else 0. for c in a.T]);a=np.where(np.isfinite(a),a,self.median);self.mean=a.mean(axis=0);self.scale=np.maximum(a.std(axis=0),1e-8);self.support=a.std(axis=0)>1e-8;z=np.clip(((a-self.mean)/self.scale)[:,self.support],-6,6);self.fallbacks=[]
        r=np.asarray(residual,float);d=np.asarray(delta,float);s=float(d@d)
        self.constant=float(np.clip(d@r/(1.1*s),0,1)) if s>1e-12 else 0.
        def fit_group(use):
            if use.sum()<15 or float(d[use]@d[use])<1e-12:return None
            zz=np.column_stack([np.ones(use.sum()),z[use]]);design=d[use,None]*zz;energy=float(d[use]@d[use]);penalty=np.diag([.1]+[1.]*z.shape[1])*energy
            return np.linalg.solve(design.T@design+penalty,design.T@r[use])
        self.coefficients={}
        if self.kind=='SHARED':
            self.coefficients['shared']=fit_group(np.ones(len(d),bool))
            if self.coefficients['shared'] is None:self.fallbacks.append('shared_constant')
        elif self.kind=='DIRECTIONAL':
            for name,use in [('positive',d>1e-8),('negative',d < -1e-8)]:
                self.coefficients[name]=fit_group(use)
                if self.coefficients[name] is None:self.fallbacks.append(name+'_constant')
        return self
    def predict_weight(self,frame,delta):
        d=np.asarray(delta,float)
        if self.kind=='CONSTANT':return np.full(len(d),self.constant)
        a=frame[INDICATORS].to_numpy(float);a=np.where(np.isfinite(a),a,self.median);z=np.clip(((a-self.mean)/self.scale)[:,self.support],-6,6);design=np.column_stack([np.ones(len(d)),z]);w=np.full(len(d),self.constant)
        for name,beta in self.coefficients.items():
            use=np.ones(len(d),bool) if name=='shared' else (d>1e-8 if name=='positive' else d < -1e-8)
            if beta is not None:w[use]=np.clip(design[use]@beta,0,1)
        return np.clip(w,0,1)
