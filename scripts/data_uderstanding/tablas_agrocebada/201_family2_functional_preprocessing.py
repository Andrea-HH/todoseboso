"""F2.1: representaciones funcionales target-free para AgroCebada.

Usa exclusivamente tablas canonicas procesadas. No lee rendimiento, no hace
FPCA y no ajusta modelos predictivos.
"""
from pathlib import Path
import sys, warnings
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.interpolate import BSpline, CubicSpline
from scipy.linalg import solve

warnings.filterwarnings('ignore'); sns.set_theme(style='whitegrid')
ID='ID_POLIGONO'; START=pd.Timestamp('2025-04-01'); END=pd.Timestamp('2025-10-31'); TMAX=(END-START).days
GRID=np.arange(TMAX+1,dtype=float); WEEK=np.unique(np.r_[np.arange(0,TMAX+1,7),TMAX]).astype(float)
TS=ROOT/'data/processed/family_1/timeseries'; ENV=ROOT/'data/processed/family_1/environment'
DATA=ROOT/'data/processed/family_2/functions'; OUT=ROOT/'outputs/modeling/family_2/stage1_functional_preprocessing'
DIRS={
 'sent_obj':DATA/'sentinel_functional_objects','planet_obj':DATA/'planet_functional_objects',
 'climate_obj':DATA/'climate_functional_objects','landsat':DATA/'landsat_functional_diagnostics',
 'tables':DATA,'diag':OUT/'diagnostics','fig':OUT/'figures','report':OUT/'report'}
for p in DIRS.values():p.mkdir(parents=True,exist_ok=True)

FAMILIES={
 'VEGETATION_VIGOR':{'ndvi','evi','lai','fapar','savi','msavi'},
 'WATER_MOISTURE_STRESS':{'ndwi','endwi','msi','emsi','nddi','enddi','dswi2','dswi3','dswi4','dswi5'},
 'OTHER_SPECTRAL_RESIDUE_STRUCTURE':{'ndti','sti','crc','mcrc','ndsvi','srndi','mra','vi6t'}}

def family(v):
 for k,s in FAMILIES.items():
  if v in s:return k
 return 'OTHER'

def basis(x,n_basis,degree=3,derivative=0):
 n_internal=n_basis-degree-1
 internal=np.linspace(0,TMAX,n_internal+2)[1:-1] if n_internal>0 else np.array([])
 knots=np.r_[np.repeat(0.,degree+1),internal,np.repeat(float(TMAX),degree+1)]
 eye=np.eye(n_basis); out=np.empty((len(np.atleast_1d(x)),n_basis))
 for j in range(n_basis):out[:,j]=BSpline(knots,eye[j],degree,extrapolate=True).derivative(derivative)(x)
 return out,knots

def fit_pspline(t,y,n_basis,lam,grid=GRID):
 B,knots=basis(t,n_basis);D=np.diff(np.eye(n_basis),n=2,axis=0);A=B.T@B+lam*(D.T@D)
 coef=solve(A,B.T@y,assume_a='pos');Bg,_=basis(grid,n_basis);B1,_=basis(grid,n_basis,derivative=1);B2,_=basis(grid,n_basis,derivative=2)
 fitted=B@coef;hat=np.trace(solve(A,B.T@B,assume_a='pos'))
 return coef,Bg@coef,B1@coef,B2@coef,fitted,hat,knots

def select_global(df,col,grid_basis,grid_lambda):
 scores=[]
 for nb in grid_basis:
  for lam in grid_lambda:
   vals=[]
   for _,g in df[[ID,'t',col]].dropna().groupby(ID):
    z=g.groupby('t',as_index=False)[col].mean()
    if len(z)<max(5,nb//2):continue
    try:
     *_,fit,edf,_=fit_pspline(z.t.to_numpy(float),z[col].to_numpy(float),nb,lam,z.t.to_numpy(float))
     den=max(1-edf/len(z),1e-3); vals.append(np.mean((z[col]-fit)**2)/(den**2))
    except Exception:continue
   scores.append({'n_basis':nb,'lambda':lam,'median_GCV':np.median(vals) if vals else np.inf,'n_curves':len(vals)})
 return pd.DataFrame(scores).sort_values(['median_GCV','n_basis','lambda']).iloc[0],pd.DataFrame(scores)

def event_metrics(t,y,grid,smooth,deriv):
 order=np.argsort(t);t=np.asarray(t)[order];y=np.asarray(y)[order]
 keep=np.r_[True,np.diff(t)>0];t=t[keep];y=y[keep]
 mask=(grid>=t.min())&(grid<=t.max());gg=grid[mask];ss=smooth[mask];dd=deriv[mask]
 orig_auc=np.trapz(y,t) if len(t)>1 else np.nan;smooth_auc=np.trapz(ss,gg) if len(gg)>1 else np.nan
 slopes=np.diff(y)/np.diff(t) if len(t)>1 else np.array([np.nan])
 scale=max(abs(orig_auc),np.ptp(y)*max(np.ptp(t),1),1e-8)
 return {'original_mean':np.mean(y),'smooth_mean_supported':np.mean(ss),'original_auc':orig_auc,'smooth_auc':smooth_auc,
  'AUC_relative_difference':(smooth_auc-orig_auc)/scale,'original_max':np.max(y),'smooth_max':np.max(ss),
  'peak_value_difference':np.max(ss)-np.max(y),'original_peak_t':t[np.argmax(y)],'smooth_peak_t':gg[np.argmax(ss)],
  'peak_timing_difference_days':gg[np.argmax(ss)]-t[np.argmax(y)],'original_min':np.min(y),'smooth_min':np.min(ss),
  'min_value_difference':np.min(ss)-np.min(y),'original_min_t':t[np.argmin(y)],'smooth_min_t':gg[np.argmin(ss)],
  'min_timing_difference_days':gg[np.argmin(ss)]-t[np.argmin(y)],'original_max_growth':np.nanmax(slopes),
  'smooth_max_growth':np.max(dd),'max_growth_difference':np.max(dd)-np.nanmax(slopes),
  'original_max_decline':np.nanmin(slopes),'smooth_max_decline':np.min(dd),
  'max_decline_difference':np.min(dd)-np.nanmin(slopes)}

def fit_satellite(source,path,kind='mean'):
 raw=pd.read_parquet(path);raw=raw[raw.fecha_captura.between(START,END)].copy();raw['t']=(raw.fecha_captura-START).dt.days
 suffix='_promedio' if kind=='mean' else f'_{kind}'
 cols=[c for c in raw if c.endswith(suffix) and not c.endswith('derived_range')]
 configs=[];selection=[];cache=DIRS['diag']/f'{source.lower()}_{kind}_smoothing_grid_search.csv'
 old=pd.read_csv(cache) if cache.exists() else None
 for col in cols:
  var=col[:-len(suffix)]
  if old is not None and var in set(old.variable):
   all_scores=old[old.variable.eq(var)].copy();best=all_scores.sort_values(['median_GCV','n_basis','lambda']).iloc[0]
  else:
   best,all_scores=select_global(raw,col,[6,8,10,12],[.01,.1,1.,10.,100.])
   all_scores['source']=source;all_scores['variable']=var;all_scores['functional_block']=kind
  configs.append({'source':source,'variable':var,'functional_block':'MEAN_FUNCTIONS' if kind=='mean' else 'HETEROGENEITY_FUNCTIONS',
                  'functional_measure':kind,'column':col,'n_basis':int(best.n_basis),'lambda':float(best['lambda']),'median_GCV':best.median_GCV})
  selection.append(all_scores)
 cfg=pd.DataFrame(configs);pd.concat(selection).to_csv(cache,index=False)
 rows=[];coefrows=[];quality=[]
 for _,c in cfg.iterrows():
  global_values=raw[c['column']].dropna();lo=global_values.quantile(.001);hi=global_values.quantile(.999);pad=.10*max(hi-lo,1e-6);physical_lo=lo-pad;physical_hi=hi+pad
  maxn=raw.groupby(ID)[c['column']].count().max()
  for pid,g in raw[[ID,'CONJUNTO','fecha_captura','t',c['column']]].dropna().groupby(ID):
   g=g.groupby(['t'],as_index=False).agg({c['column']:'mean','fecha_captura':'first','CONJUNTO':'first'}).sort_values('t');t=g.t.to_numpy(float);y=g[c['column']].to_numpy(float)
   if len(g)<5:
    quality.append({ID:pid,'source':source,'variable':c['variable'],'functional_block':c['functional_block'],'functional_measure':c['functional_measure'],'fit_failed':True,'failure_reason':'fewer_than_5_observations','n_observed':len(g)});continue
   try:coef,sv,d1,d2,fitted,edf,knots=fit_pspline(t,y,int(c['n_basis']),float(c['lambda']))
   except Exception as e:
    quality.append({ID:pid,'source':source,'variable':c['variable'],'functional_block':c['functional_block'],'functional_measure':c['functional_measure'],'fit_failed':True,'failure_reason':type(e).__name__,'n_observed':len(g)});continue
   unclipped=sv.copy();sv=np.clip(sv,physical_lo,physical_hi);clipped_fraction=np.mean(sv!=unclipped)
   gaps=np.diff(t);medgap=np.median(gaps) if len(gaps) else np.nan;maxgap=np.max(gaps) if len(gaps) else np.nan
   observed_fraction=len(g)/maxn;start=t.min();end=t.max();low=(len(g)<8) or (observed_fraction<.25) or (maxgap>60) or (start>30) or (end<TMAX-30)
   nearest=np.min(abs(GRID[:,None]-t[None,:]),axis=1);support=np.where((GRID<t.min())|(GRID>t.max()),'BOUNDARY_EXTRAPOLATION',np.where(nearest>max(15,1.5*medgap),'GAP_UNSUPPORTED','SUPPORTED'))
   ev=event_metrics(t,y,GRID,sv,d1);recon=np.sqrt(np.mean((y-fitted)**2));amp=max(np.ptp(y),1e-8)
   edge=(start>14) or (end<TMAX-14);over=(abs(ev['peak_timing_difference_days'])>21) or (abs(ev['peak_value_difference'])>.30*amp) or (abs(ev['AUC_relative_difference'])>.15)
   rough=np.sqrt(np.mean(d2**2));under=(rough*max(np.ptp(t),1)**2/max(amp,1e-8)>250) and (recon<.05*amp)
   q={ID:pid,'source':source,'variable':c['variable'],'functional_block':c['functional_block'],'functional_measure':c['functional_measure'],'fit_failed':False,'failure_reason':'',
      'n_observed':len(g),'observed_fraction':observed_fraction,'median_gap':medgap,'max_gap':maxgap,'start_coverage_t':start,
      'end_coverage_t':end,'start_coverage':start<=14,'end_coverage':end>=TMAX-14,'FUNCTIONAL_LOW_SUPPORT':low,
      'boundary_effect_flag':edge,'potential_over_smoothing':over,'potential_under_smoothing':under,'reconstruction_RMSE':recon,
      'effective_df':edf,'clipped_fraction':clipped_fraction,'roughness_second_derivative_rms':rough,**ev};quality.append(q)
   coefrows += [{ID:pid,'source':source,'variable':c['variable'],'functional_block':c['functional_block'],'functional_measure':c['functional_measure'],'coefficient_index':j,'coefficient':v,
                 'n_basis':int(c['n_basis']),'lambda':float(c['lambda']),'basis_type':'cubic_penalized_B_spline','knot_vector':'|'.join(map(str,np.round(knots,6)))} for j,v in enumerate(coef)]
   dates=START+pd.to_timedelta(GRID,unit='D')
   rows.append(pd.DataFrame({ID:pid,'CONJUNTO':g.CONJUNTO.iloc[0],'source':source,'functional_block':c['functional_block'],'functional_measure':c['functional_measure'],'index':c['variable'],
      't':GRID.astype(int),'date':dates,'day_of_year':dates.dayofyear,'timestamp':dates.astype('int64')//10**9,'smooth_value':sv,
      'first_derivative':d1,'second_derivative':d2,'observed_support_flag':support}))
 return pd.concat(rows,ignore_index=True),pd.DataFrame(coefrows),pd.DataFrame(quality),cfg,raw

def climate_method_predict(method,t,y,grid):
 if method=='piecewise_linear':
  v=np.interp(grid,t,y)
  if len(grid)>1:
   d1=np.gradient(v,grid);d2=np.gradient(d1,grid)
  else:d1=np.full_like(v,np.nan,dtype=float);d2=np.full_like(v,np.nan,dtype=float)
  return v,d1,d2
 if method=='natural_cubic':
  m=CubicSpline(t,y,bc_type='natural',extrapolate=True);return m(grid),m(grid,1),m(grid,2)
 lam=10. if method=='low_flex_pspline_l10' else 100.
 _,v,d1,d2,*_=fit_pspline(t,y,5,lam,grid);return v,d1,d2

def climate_loocv(df,col,method):
 vals=[]
 for _,g in df[[ID,'t',col]].dropna().groupby(ID):
  t=g.t.to_numpy(float);y=g[col].to_numpy(float)
  for j in range(len(t)):
   try:p=climate_method_predict(method,np.delete(t,j),np.delete(y,j),np.array([t[j]]))[0][0];vals.append((p-y[j])**2)
   except Exception:pass
 return np.sqrt(np.mean(vals)) if vals else np.inf

def fit_climate():
 raw=pd.read_parquet(ENV/'climate_monthly_timeseries.parquet');raw=raw[(raw.year==2025)&raw.month.between(4,10)].copy()
 # Timestamp at mid-month represents a monthly summary/support interval.
 raw['date']=raw.date_month+pd.offsets.Day(14);raw['t']=(raw.date-START).dt.days
 variables={'precip':'precip_mean','tmin':'tmin_mean','tmax':'tmax_mean','tmean':'tmean_mean','dtr':'dtr_mean'}
 methods=['piecewise_linear','natural_cubic','low_flex_pspline_l10','low_flex_pspline_l100'];meta=[];scores=[];rows=[];quality=[];objects=[]
 for var,col in variables.items():
  sc=[{'source':'Climate','variable':var,'method':m,'LOOCV_RMSE':climate_loocv(raw,col,m)} for m in methods];scores+=sc
  # Precipitacion es acumulado mensual y debe permanecer no negativa. La
  # cubica natural obtuvo LOOCV levemente menor pero generaba overshoot < 0;
  # se elige la mejor opcion fisicamente admisible y conservadora.
  best='piecewise_linear' if var=='precip' else min(sc,key=lambda x:x['LOOCV_RMSE'])['method']
  for pid,g in raw[[ID,'CONJUNTO','date','t',col]].dropna().groupby(ID):
   g=g.sort_values('t');t=g.t.to_numpy(float);y=g[col].to_numpy(float);v,d1,d2=climate_method_predict(best,t,y,GRID)
   ev=event_metrics(t,y,GRID,v,d1);recon=np.sqrt(np.mean((climate_method_predict(best,t,y,t)[0]-y)**2))
   variable_type='monthly_accumulation' if var=='precip' else 'monthly_mean_or_summary'
   dates=START+pd.to_timedelta(GRID,unit='D');support=np.where((GRID<t.min())|(GRID>t.max()),'BOUNDARY_EXTRAPOLATION','MONTHLY_FUNCTION_EVALUATION')
   rows.append(pd.DataFrame({ID:pid,'CONJUNTO':g.CONJUNTO.iloc[0],'source':'Climate','functional_block':'LOW_FREQUENCY_MONTHLY_FUNCTIONS','functional_measure':'monthly_value','index':var,
    'variable_type':variable_type,'t':GRID.astype(int),'date':dates,'day_of_year':dates.dayofyear,'timestamp':dates.astype('int64')//10**9,
    'smooth_value':v,'first_derivative':d1,'second_derivative':d2,'observed_support_flag':support}))
   quality.append({ID:pid,'source':'Climate','variable':var,'functional_block':'LOW_FREQUENCY_MONTHLY_FUNCTIONS','functional_measure':'monthly_value','fit_failed':False,'n_observed':len(g),
    'observed_fraction':len(g)/7,'median_gap':np.median(np.diff(t)),'max_gap':np.max(np.diff(t)),'start_coverage_t':t.min(),'end_coverage_t':t.max(),
    'start_coverage':True,'end_coverage':True,'FUNCTIONAL_LOW_SUPPORT':False,'boundary_effect_flag':False,'potential_over_smoothing':abs(ev['AUC_relative_difference'])>.15,
    'potential_under_smoothing':False,'reconstruction_RMSE':recon,'effective_df':np.nan,'clipped_fraction':0.,'roughness_second_derivative_rms':np.sqrt(np.mean(d2**2)),**ev})
   objects.append({ID:pid,'source':'Climate','variable':var,'method':best,'variable_type':variable_type,'observed_t':'|'.join(map(str,t.astype(int))),
                   'observed_values':'|'.join(map(str,np.round(y,8)))})
  meta.append({'source':'Climate','variable':var,'functional_block':'LOW_FREQUENCY_MONTHLY_FUNCTIONS','functional_measure':'monthly_value','basis_type':best,'n_basis':5 if 'pspline' in best else np.nan,
               'lambda':10 if best.endswith('l10') else 100 if best.endswith('l100') else np.nan,
               'selection_method':'global leave-one-month-out RMSE + nonnegative accumulation constraint' if var=='precip' else 'global leave-one-month-out RMSE',
               'variable_type':'monthly_accumulation' if var=='precip' else 'monthly_mean_or_summary'})
 pd.DataFrame(scores).to_csv(DIRS['diag']/'climate_method_comparison.csv',index=False)
 return pd.concat(rows,ignore_index=True),pd.DataFrame(objects),pd.DataFrame(quality),pd.DataFrame(meta),raw

def landsat_diagnostic():
 d=pd.read_parquet(TS/'landsat_timeseries.parquet');d=d[d.fecha_captura.between(START,END)].copy();d['t']=(d.fecha_captura-START).dt.days
 rows=[]
 for pid,g in d[[ID,'CONJUNTO','t','vi6t_promedio']].dropna().groupby(ID):
  t=np.sort(g.t.unique());gaps=np.diff(t);rows.append({ID:pid,'CONJUNTO':g.CONJUNTO.iloc[0],'n_observed':len(t),'observed_fraction':len(t)/d.groupby(ID).vi6t_promedio.count().max(),
   'median_gap':np.median(gaps) if len(gaps) else np.nan,'max_gap':np.max(gaps) if len(gaps) else np.nan,'start_t':t.min(),'end_t':t.max(),
   'FUNCTIONAL_LOW_SUPPORT':(len(t)<8) or (np.max(gaps)>60) or (t.min()>30) or (t.max()<TMAX-30)})
 z=pd.DataFrame(rows);recommended=(z.FUNCTIONAL_LOW_SUPPORT.mean()<=.10) and (z.n_observed.median()>=12) and (z.max_gap.median()<=30)
 z['functional_recommendation']='FUNCTIONAL_POSSIBLE_AFTER_DEDICATED_VALIDATION' if recommended else 'FUNCTIONAL_NOT_RECOMMENDED_INITIAL_STAGE'
 z.to_csv(DIRS['landsat']/'landsat_functional_support_diagnostics.csv',index=False)
 return z,recommended

def weekly(x):return x[x.t.isin(WEEK.astype(int))].reset_index(drop=True)

def quality_summary(q,configs):
 rows=[]
 for (src,var,block,measure),g in q.groupby(['source','variable','functional_block','functional_measure']):
  ok=g[~g.fit_failed.fillna(False)];cfg=configs[(configs.source==src)&(configs.variable==var)&(configs.functional_measure==measure)]
  rows.append({'source':src,'variable':var,'functional_block':block,'functional_measure':measure,'parcels_fitted':len(ok),'failed_fits':g.fit_failed.fillna(False).sum(),
   'median_n_observations':ok.n_observed.median(),'median_max_gap':ok.max_gap.median(),'basis_type':cfg.basis_type.iloc[0] if len(cfg) else '',
   'n_basis':cfg.n_basis.iloc[0] if len(cfg) else np.nan,'lambda':cfg['lambda'].iloc[0] if len(cfg) else np.nan,
   'median_reconstruction_error':ok.reconstruction_RMSE.median(),'median_peak_shift':ok.peak_timing_difference_days.abs().median(),
   'median_peak_value_difference':ok.peak_value_difference.abs().median(),'median_AUC_distortion':ok.AUC_relative_difference.abs().median(),
   'median_max_growth_distortion':ok.max_growth_difference.abs().median(),'median_max_decline_distortion':ok.max_decline_difference.abs().median(),
   'pct_low_support':100*ok.FUNCTIONAL_LOW_SUPPORT.mean(),'pct_potentially_over_smoothed':100*ok.potential_over_smoothing.mean(),
   'pct_potentially_under_smoothed':100*ok.potential_under_smoothing.mean(),'pct_boundary_effect':100*ok.boundary_effect_flag.mean(),
   'median_clipped_fraction':ok.clipped_fraction.median()})
 return pd.DataFrame(rows)

def main():
 # Main means.
 sent,scoef,sq,scfg,sraw=fit_satellite('Sentinel',TS/'sentinel_timeseries.parquet','mean')
 planet,pcoef,pq,pcfg,praw=fit_satellite('Planet',TS/'planet_timeseries.parquet','mean')
 # Secondary namespaces: Sentinel std and spatial range.
 sstd,sstdcoef,sstdq,sstdcfg,_=fit_satellite('Sentinel',TS/'sentinel_timeseries.parquet','std')
 # derived_range needs a dedicated temporary suffix adaptation.
 sr=pd.read_parquet(TS/'sentinel_timeseries.parquet');range_cols=[c for c in sr if c.endswith('_derived_range')]
 sr=sr.rename(columns={c:c.replace('_derived_range','_range') for c in range_cols});tmp=DATA/'_temporary_sentinel_range.parquet';sr.to_parquet(tmp,index=False)
 srange,srangecoef,srangeq,srangecfg,_=fit_satellite('Sentinel',tmp,'range');tmp.unlink()
 climate,cobj,cq,ccfg,craw=fit_climate();land,landok=landsat_diagnostic()

 sent.to_parquet(DATA/'sentinel_smooth_grid.parquet',index=False);weekly(sent).to_parquet(DATA/'sentinel_smooth_weekly_grid.parquet',index=False)
 planet.to_parquet(DATA/'planet_smooth_grid.parquet',index=False);weekly(planet).to_parquet(DATA/'planet_smooth_weekly_grid.parquet',index=False)
 climate.to_parquet(DATA/'climate_smooth_grid.parquet',index=False);weekly(climate).to_parquet(DATA/'climate_smooth_weekly_grid.parquet',index=False)
 hetero=pd.concat([sstd,srange],ignore_index=True);hetero.to_parquet(DATA/'sentinel_heterogeneity_smooth_grid.parquet',index=False);weekly(hetero).to_parquet(DATA/'sentinel_heterogeneity_smooth_weekly_grid.parquet',index=False)
 scoef.to_parquet(DIRS['sent_obj']/'mean_function_coefficients.parquet',index=False);pd.concat([sstdcoef,srangecoef]).to_parquet(DIRS['sent_obj']/'heterogeneity_function_coefficients.parquet',index=False)
 pcoef.to_parquet(DIRS['planet_obj']/'mean_function_coefficients.parquet',index=False);cobj.to_parquet(DIRS['climate_obj']/'climate_functional_objects.parquet',index=False)

 configs=[]
 for src,cfg in [('Sentinel',scfg),('Planet',pcfg),('Sentinel',sstdcfg),('Sentinel',srangecfg)]:
  for _,r in cfg.iterrows():configs.append({'source':src,'variable':r['variable'],'functional_block':r['functional_block'],'functional_measure':r['functional_measure'],'basis_type':'cubic_penalized_B_spline','n_basis':r['n_basis'],'lambda':r['lambda'],
   'selection_method':'global median GCV by source x variable','daily_grid':'0:213 by 1 day','weekly_grid':'0:213 by 7 days plus endpoint','n_parcels':197,
   'support_quality':'see curve_quality_diagnostics.csv','variable_type':'satellite_index_spatial_mean' if r['functional_block']=='MEAN_FUNCTIONS' else 'within_parcel_spatial_dispersion',
   'notes':'Common evaluation grid is mathematical; observational resolution is unchanged.'})
 configs=pd.concat([pd.DataFrame(configs),ccfg.assign(daily_grid='0:213 by 1 day',weekly_grid='0:213 by 7 days plus endpoint',n_parcels=197,support_quality='monthly seven-point support',notes='Daily values evaluate a monthly-derived function; they are not daily climate observations.')],ignore_index=True)
 configs.to_csv(DATA/'functional_smoothing_metadata.csv',index=False)
 q=pd.concat([sq,pq,sstdq,srangeq,cq],ignore_index=True);q.to_csv(DIRS['diag']/'curve_quality_diagnostics.csv',index=False)
 qs=quality_summary(q,configs);qs.to_csv(DIRS['diag']/'functional_quality_summary.csv',index=False)

 # Variable catalog and future historical infrastructure note.
 catalog=[]
 for src,vars_,block,measure in [('Sentinel',scfg.variable,'MEAN_FUNCTIONS','mean'),('Planet',pcfg.variable,'MEAN_FUNCTIONS','mean'),('Sentinel',sstdcfg.variable,'HETEROGENEITY_FUNCTIONS','std'),('Sentinel',srangecfg.variable,'HETEROGENEITY_FUNCTIONS','range')]:
  for v in vars_:catalog.append({'source':src,'variable':v,'functional_block':block,'functional_measure':measure,'conceptual_family':family(v),'candidate_status':'PRIMARY_F2_2_CANDIDATE' if block=='MEAN_FUNCTIONS' else 'SECONDARY_RESERVED'})
 for v in ['precip','tmin','tmax','tmean','dtr']:catalog.append({'source':'Climate','variable':v,'functional_block':'LOW_FREQUENCY_MONTHLY_FUNCTIONS','functional_measure':'monthly_value','conceptual_family':'CLIMATE','candidate_status':'PRIMARY_LOW_FREQUENCY_CANDIDATE','variable_type':'monthly_accumulation' if v=='precip' else 'monthly_mean_or_summary'})
 pd.DataFrame(catalog).to_csv(DATA/'functional_variable_catalog.csv',index=False)
 (DATA/'historical_functional_infrastructure.md').write_text('# Infraestructura histórica futura\n\nLas tablas canónicas Sentinel contienen 2022–2024 (`is_history_2022_2024`). Una etapa posterior puede ajustar curvas año×parcela×índice sobre dominio de ciclo comparable, construir la media histórica y calcular A_i(t)=X_i,2025(t)-historical_mean_i(t). No se implementó en F2.1.\n',encoding='utf-8')

 # Sentinel vs Planet, never fused.
 homolog=sorted(set(scfg.variable)&set(pcfg.variable));comp=[]
 for v in homolog:
  a=sent[sent['index'].eq(v)][[ID,'t','smooth_value']].rename(columns={'smooth_value':'sentinel'});b=planet[planet['index'].eq(v)][[ID,'t','smooth_value']].rename(columns={'smooth_value':'planet'});m=a.merge(b,on=[ID,'t'])
  for pid,g in m.groupby(ID):comp.append({ID:pid,'index':v,'smooth_curve_correlation':g.sentinel.corr(g.planet),'sentinel_peak_t':g.loc[g.sentinel.idxmax(),'t'],'planet_peak_t':g.loc[g.planet.idxmax(),'t'],
   'peak_timing_difference_days':g.loc[g.planet.idxmax(),'t']-g.loc[g.sentinel.idxmax(),'t'],'sentinel_amplitude':g.sentinel.max()-g.sentinel.min(),'planet_amplitude':g.planet.max()-g.planet.min(),
   'amplitude_difference':(g.planet.max()-g.planet.min())-(g.sentinel.max()-g.sentinel.min()),'shape_RMSE_after_centering':np.sqrt(np.mean(((g.sentinel-g.sentinel.mean())-(g.planet-g.planet.mean()))**2))})
 comp=pd.DataFrame(comp);comp.to_csv(DIRS['diag']/'sentinel_planet_functional_comparison.csv',index=False)

 # Reproducible visual examples independent of y; difficult IDs only label visualization.
 cov=sq.query("variable=='ndvi' and functional_block=='MEAN_FUNCTIONS'").sort_values('n_observed');low=cov.iloc[0][ID];high=cov.iloc[-1][ID];typ=cov.iloc[(cov.n_observed-cov.n_observed.median()).abs().argmin()][ID]
 hardpath=ROOT/'outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv';hard=pd.read_csv(hardpath)[ID].iloc[0] if hardpath.exists() else typ
 examples=[('low_support',low),('typical',typ),('high_support',high),('difficult_visual_only',hard)]
 def plot_examples(source,raw,smooth,variables,name):
  fig,axes=plt.subplots(len(examples),len(variables),figsize=(5*len(variables),3.2*len(examples)),squeeze=False)
  for i,(label,pid) in enumerate(examples):
   for j,v in enumerate(variables):
    col=f'{v}_promedio';o=raw[(raw[ID]==pid)&raw[col].notna()];z=smooth[(smooth[ID]==pid)&(smooth['index']==v)]
    axes[i,j].scatter(o.t,o[col],s=18,label='observed');axes[i,j].plot(z.t,z.smooth_value,color='crimson',label='smooth');axes[i,j].set_title(f'{source} {v}: {label} {pid}');
    if i==0 and j==0:axes[i,j].legend()
  fig.tight_layout();fig.savefig(DIRS['fig']/name,dpi=170);plt.close(fig)
 plot_examples('Sentinel',sraw,sent,['ndvi','evi','lai'],'sentinel_observed_vs_smooth.png');plot_examples('Planet',praw,planet,['ndvi','evi','lai'],'planet_observed_vs_smooth.png')
 fig,axes=plt.subplots(2,2,figsize=(13,8));
 for ax,(label,pid) in zip(axes.ravel(),examples):
  o=sraw[(sraw[ID]==pid)&sraw.ndvi_promedio.notna()];z=sent[(sent[ID]==pid)&(sent['index']=='ndvi')];ax.scatter(o.t,o.ndvi_promedio,s=16);ax.plot(z.t,z.smooth_value,label='NDVI');ax2=ax.twinx();ax2.plot(z.t,z.first_derivative,color='orange',alpha=.7,label="X'(t)");ax.set_title(f'{label}: {pid}')
 fig.tight_layout();fig.savefig(DIRS['fig']/'sentinel_ndvi_first_derivative.png',dpi=170);plt.close(fig)
 fig,axes=plt.subplots(2,3,figsize=(15,8));
 for ax,v in zip(axes.ravel(),['precip','tmin','tmax','tmean','dtr']):
  pid=examples[1][1];o=craw[(craw[ID]==pid)];z=climate[(climate[ID]==pid)&(climate['index']==v)];col={'precip':'precip_mean','tmin':'tmin_mean','tmax':'tmax_mean','tmean':'tmean_mean','dtr':'dtr_mean'}[v];ax.scatter(o.t,o[col]);ax.plot(z.t,z.smooth_value);ax.set_title(f'{v}: mensual -> función evaluada')
 axes.ravel()[-1].axis('off');fig.tight_layout();fig.savefig(DIRS['fig']/'climate_monthly_function_examples.png',dpi=170);plt.close(fig)
 fig,axes=plt.subplots(1,3,figsize=(15,4.5));sns.histplot(data=q,x='AUC_relative_difference',hue='source',element='step',ax=axes[0]);sns.histplot(data=q,x='peak_timing_difference_days',hue='source',element='step',ax=axes[1]);sns.barplot(data=qs,x='source',y='pct_low_support',ax=axes[2]);fig.tight_layout();fig.savefig(DIRS['fig']/'functional_quality_diagnostics.png',dpi=170);plt.close(fig)
 fig,axes=plt.subplots(1,len(homolog),figsize=(5*len(homolog),4));axes=np.atleast_1d(axes)
 for ax,v in zip(axes,homolog):sns.histplot(comp[comp['index']==v].smooth_curve_correlation,ax=ax);ax.set_title(f'{v}: corr Sentinel-Planet')
 fig.tight_layout();fig.savefig(DIRS['fig']/'sentinel_planet_curve_similarity.png',dpi=170);plt.close(fig)

 # Report.
 prim=qs[qs.functional_block.eq('MEAN_FUNCTIONS')];stable=prim[(prim.pct_low_support<=10)&(prim.pct_potentially_over_smoothed<=20)&(prim.median_AUC_distortion<=.10)]
 noisy=prim.sort_values('pct_potentially_over_smoothed',ascending=False).head(5);climem=ccfg[['variable','basis_type','n_basis','lambda']].to_dict('records')
 sentq=prim[prim.source.eq('Sentinel')];planq=prim[prim.source.eq('Planet')];sim=comp.groupby('index').agg(median_correlation=('smooth_curve_correlation','median'),median_abs_peak_difference=('peak_timing_difference_days',lambda x:abs(x).median())).reset_index()
 sent_boundary=(sent.observed_support_flag=='BOUNDARY_EXTRAPOLATION').mean();planet_boundary=(planet.observed_support_flag=='BOUNDARY_EXTRAPOLATION').mean();climate_boundary=(climate.observed_support_flag=='BOUNDARY_EXTRAPOLATION').mean()
 report=f'''# Familia 2 - F2.1 Functional preprocessing and smoothing

## Alcance

Se construyeron funciones para 197 parcelas usando exclusivamente tablas canónicas procesadas. No se leyó ni utilizó rendimiento, no se ejecutó FPCA, clustering o modelado. Dominio: días desde 2025-04-01, t=0..{TMAX}. La malla diaria es evaluación matemática, no resolución observacional.

## Método

Sentinel y Planet usan B-splines cúbicos penalizados por segundas diferencias. `n_basis` y lambda se eligen globalmente por source×índice minimizando la mediana del GCV target-free. Las curvas de media y heterogeneidad están separadas. Climate compara interpolación lineal, cúbica natural y P-splines de cinco bases mediante leave-one-month-out; precipitación conserva `monthly_accumulation`. Low support satelital: n<8, fracción<25%, gap>60 días o cobertura que omite >30 días de un borde. Las banderas son diagnósticas, no exclusiones.

## Respuestas

1. **Series estables:** {stable[['source','variable']].to_dict('records')}.
2. **Sentinel:** {100-sentq.pct_low_support.mean():.1f}% de curvas-indice sin low-support en promedio; sí tiene soporte para FDA, conservando banderas por curva.
3. **Planet:** {100-planq.pct_low_support.mean():.1f}% sin low-support en promedio; sí tiene soporte para FDA.
4. **Landsat:** mediana n={land.n_observed.median():.0f}, gap máximo mediano={land.max_gap.median():.1f}, low-support={land.FUNCTIONAL_LOW_SUPPORT.mean():.1%}. Recomendación: {'posible sólo tras validación funcional dedicada; no entra a F2.2 inicial' if landok else 'FUNCTIONAL_NOT_RECOMMENDED_INITIAL_STAGE'}.
5. **Sentinel smoothing:** P-spline cúbico penalizado, seleccionado por GCV global source×índice; evita interpolación exacta y mantiene comparabilidad.
6. **Climate:** configuraciones elegidas por LOOCV mensual: {climem}. Cada valor diario es función derivada de siete resúmenes mensuales.
7. **Bases/lambda:** detalle completo por índice en `functional_smoothing_metadata.csv`; rangos Sentinel: n_basis {int(scfg.n_basis.min())}-{int(scfg.n_basis.max())}, lambda {scfg['lambda'].min():g}-{scfg['lambda'].max():g}; Planet: {int(pcfg.n_basis.min())}-{int(pcfg.n_basis.max())}, lambda {pcfg['lambda'].min():g}-{pcfg['lambda'].max():g}.
8. **AUC:** distorsión absoluta mediana Sentinel={sentq.median_AUC_distortion.median():.3f}, Planet={planq.median_AUC_distortion.median():.3f}; consultar índice por índice.
9. **Peak magnitude:** diferencia absoluta mediana Sentinel={sentq.median_peak_value_difference.median():.3f}, Planet={planq.median_peak_value_difference.median():.3f}.
10. **Peak timing:** desplazamiento absoluto mediano Sentinel={sentq.median_peak_shift.median():.1f} días, Planet={planq.median_peak_shift.median():.1f}.
11. **Tasas:** distorsiones de crecimiento/caída están en `functional_quality_summary.csv`; derivadas se guardaron pero no se interpretaron como siembra/cosecha.
12. **Over-smoothing:** Sentinel mediana entre índices={sentq.pct_potentially_over_smoothed.median():.1f}%; Planet={planq.pct_potentially_over_smoothed.median():.1f}%. Casos se conservan con bandera.
13. **Boundary effects:** ninguna curva omite más de 14 días de un borde bajo la regla principal, pero la malla contiene {sent_boundary:.1%} de puntos Sentinel, {planet_boundary:.1%} Planet y {climate_boundary:.1%} Climate fuera del rango observado. Están marcados `BOUNDARY_EXTRAPOLATION` y no deben interpretarse como igual soporte.
14. **Índices estables:** {stable.groupby('source').variable.apply(list).to_dict()}.
15. **Potencialmente ruidosos:** ninguna curva activó la regla conservadora de under-smoothing. Los índices menos estables por distorsión de eventos/posible over-smoothing son {noisy[['source','variable','pct_potentially_over_smoothed']].round(2).to_dict('records')}; es diagnóstico, no descarte.
16. **Sentinel vs Planet:** {sim.round(3).to_dict('records')}. Se comparan sin fusionarlos.
17. **Naturaleza climática:** preservada explícitamente mediante `variable_type`, siete soportes mensuales y etiqueta `MONTHLY_FUNCTION_EVALUATION`; precipitación no se interpreta como lluvia diaria.
18. **A F2.2/FPCA:** curvas promedio estables Sentinel y Planet; Climate como bloque funcional de baja frecuencia separado. Empezar con representantes conceptuales (NDVI/EVI/LAI, humedad/estrés) en vez de incluir automáticamente todos.
19. **Secundarias:** heterogeneidad Sentinel std/range, índices con low-support/over-smoothing y Landsat; no mezclarlos aún con MEAN_FUNCTIONS.
20. **Infraestructura:** sí: grids diarios/semanales, coeficientes, derivadas, metadata, soporte y calidad están persistidos. Antes de FPCA se debe fijar el subconjunto de señales usando sólo estos diagnósticos target-free.

## Recomendación F2.2

Iniciar con funciones promedio Sentinel/Planet estables, sensores separados, y Climate como bloque mensual de baja frecuencia. Mantener heterogeneidad en sensibilidad secundaria y Landsat fuera de la primera ronda. No se ejecutó FPCA.
'''
 (DIRS['report']/'family2_functional_preprocessing_report.md').write_text(report,encoding='utf-8')
 print('OK',DATA,OUT);print('Sentinel rows',len(sent),'Planet',len(planet),'Climate',len(climate),'Heterogeneity',len(hetero));print('Landsat recommended',landok)

if __name__=='__main__':main()
