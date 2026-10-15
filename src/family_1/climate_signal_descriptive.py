"""G/H target-free spatial/temporal descriptions and separately labeled associations."""
import json,itertools
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from pyproj import Geod
from .climate_signal_features import *
from .rainfall_pcr_reporting import save

def geography():
    g=gpd.read_file(SHAPE).rename(columns={'ID_POLIGON':ID}).to_crs(6372)
    centers=g.geometry.centroid.to_crs(4326)
    g['longitude']=centers.x;g['latitude']=centers.y
    return g

def pca_description(frame,cols,name,out,geo,train,balanced=False):
    X=frame[cols];scaler=StandardScaler().fit(X);z=scaler.transform(X)
    weights=np.ones(len(cols))
    if balanced:
        weights=np.array([1/np.sqrt(7) if c in RAIN else 1/np.sqrt(14) for c in cols]);z=z*weights
    model=PCA(svd_solver='full').fit(z);scores=model.transform(z)
    pc=[f'PC{i+1}' for i in range(len(cols))]
    variance=pd.DataFrame(dict(component=pc,eigenvalue=model.explained_variance_,variance_fraction=model.explained_variance_ratio_,cumulative=np.cumsum(model.explained_variance_ratio_)))
    variance.to_csv(out/'tables'/f'20_{name}_variance.csv',index=False)
    loads=pd.DataFrame(model.components_.T,index=cols,columns=pc);loads.to_csv(out/'tables'/f'21_{name}_loadings.csv')
    loads.pow(2).groupby(lambda c:c.split('_')[0]).sum().to_csv(out/'tables'/f'22_{name}_block_contributions.csv')
    score=pd.DataFrame(scores,columns=pc);score.insert(0,ID,frame[ID].to_numpy())
    score.to_parquet(out/'tables'/f'23_{name}_scores_197_descriptive.parquet',index=False)
    pd.DataFrame(dict(feature=cols,mean=scaler.mean_,scale=scaler.scale_,variance=scaler.var_,block_weight=weights)).to_csv(out/'tables'/f'24_{name}_scaling.csv',index=False)
    pd.DataFrame(np.corrcoef(scores.T,X.to_numpy().T)[:len(cols),len(cols):],index=pc,columns=cols).to_csv(out/'tables'/f'25_{name}_pc_month_correlations.csv')
    q=score.merge(train[[ID,TARGET]],on=ID)
    pd.DataFrame([dict(component=c,pearson_y=q[c].corr(q[TARGET]),spearman_y=q[c].corr(q[TARGET],method='spearman'),n=138,role='descriptive only') for c in pc]).to_csv(out/'tables'/f'26_{name}_pc_y_association.csv',index=False)
    region=score.merge(geo[[ID,'Estado','Municipio','longitude','latitude']],on=ID)
    label=region.merge(train[[ID,TARGET]],on=ID,how='left')
    fig,axes=plt.subplots(1,2,figsize=(11,4));axes[0].plot(range(1,len(pc)+1),variance.variance_fraction,'o-');axes[0].set(xlabel='PC',ylabel='Varianza explicada')
    axes[1].plot(range(1,len(pc)+1),variance.cumulative,'o-');axes[1].axhline(.95,ls='--',c='grey');axes[1].set(xlabel='K',ylabel='Varianza acumulada');fig.suptitle(name+' — descriptivo 197, no entrada CV');save(fig,out,f'20_{name}_scree.png')
    fig,ax=plt.subplots(figsize=(9,max(5,len(cols)*.28)));sns.heatmap(loads.iloc[:,:min(5,len(pc))],annot=True,fmt='.2f',cmap='coolwarm',center=0,ax=ax);ax.set_title(name+' — eigenvectores');save(fig,out,f'21_{name}_loadings.png')
    fig,axes=plt.subplots(1,3,figsize=(17,5))
    for field,ax in zip(['Estado','Municipio'],axes):
        sns.scatterplot(data=region,x='PC1',y='PC2',hue=field,s=30,ax=ax);ax.legend(fontsize=6);ax.set_title(field)
    unlabeled=label[TARGET].isna();axes[2].scatter(label.loc[unlabeled,'PC1'],label.loc[unlabeled,'PC2'],c='lightgrey',s=20)
    sc=axes[2].scatter(label.loc[~unlabeled,'PC1'],label.loc[~unlabeled,'PC2'],c=label.loc[~unlabeled,TARGET],s=25,cmap='viridis');fig.colorbar(sc,ax=axes[2],label='Y observado 138 TRAIN');axes[2].set(xlabel='PC1',ylabel='PC2');fig.suptitle(name);save(fig,out,f'22_{name}_PC_geography_and_y.png')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for c,ax in zip(['PC1','PC2'],axes):
        sc=ax.scatter(region.longitude,region.latitude,c=region[c],cmap='coolwarm',s=20);fig.colorbar(sc,ax=ax,label=c);ax.set(xlabel='Longitud',ylabel='Latitud')
    save(fig,out,f'23_{name}_PC_maps.png')
    eta=[]
    for field in ['Estado','Municipio']:
        for c in pc:
            den=((region[c]-region[c].mean())**2).sum()
            eta.append(dict(field=field,component=c,between_fraction=sum(len(g)*(g[c].mean()-region[c].mean())**2 for _,g in region.groupby(field))/den if den>1e-12 else np.nan))
    pd.DataFrame(eta).to_csv(out/'tables'/f'27_{name}_region_structure.csv',index=False)
    import joblib
    joblib.dump(dict(scaler=scaler,pca=model,block_weights=weights,columns=cols,role='197 target-free exploration only'),out/'models'/f'descriptive_{name}.joblib',compress=3)
    return dict(name=name,k90=int(np.searchsorted(variance.cumulative,.90)+1),k95=int(np.searchsorted(variance.cumulative,.95)+1),rank=int(np.linalg.matrix_rank(z)),n_columns=len(cols),zero_variance=list(X.columns[scaler.var_==0]),PC1_top_loadings=loads.PC1.reindex(loads.PC1.abs().nlargest(5).index).to_dict(),PC2_top_loadings=loads.PC2.reindex(loads.PC2.abs().nlargest(5).index).to_dict())

def profiles(frame,geo,train,out,section):
    groups={ID:frame[ID].to_numpy()};specs={'rain':RAIN,'tmin':MIN,'tmax':MAX,'thermal':TEMP,'joint':JOINT}
    for name,cols in specs.items():
        groups[name]=pd.factorize(pd.MultiIndex.from_frame(frame[cols]),sort=True)[0]+1
        # Complete linkage avoids tolerance chaining; no target informed grouping.
        tol=np.array([.01 if c in RAIN else .001 for c in cols])
        groups[name+'_near']=bounded_groups(frame[cols].to_numpy()/tol,1.)
    membership=pd.DataFrame(groups);membership.to_csv(out/'tables/06_profile_memberships.csv',index=False)
    q=membership.merge(geo[[ID,'Estado','Municipio','longitude','latitude']],on=ID).merge(train[[ID,TARGET]],on=ID,how='left')
    geod=Geod(ellps='WGS84');summaries=[];pairs=[]
    for kind in specs:
        for group,z in q.groupby(kind):
            distances=[]
            for a,b in itertools.combinations(z.to_dict('records'),2):
                _,_,m=geod.inv(a['longitude'],a['latitude'],b['longitude'],b['latitude']);distances.append(m/1000)
                pairs.append(dict(kind=kind,profile=group,ID_A=a[ID],ID_B=b[ID],distance_km=m/1000,same_state=a['Estado']==b['Estado'],same_municipality=a['Municipio']==b['Municipio']))
            summaries.append(dict(kind=kind,profile=group,n_parcels=len(z),n_labeled=z[TARGET].count(),n_states=z.Estado.nunique(),n_municipalities=z.Municipio.nunique(),max_distance_km=max(distances) if distances else 0,y_sd=z[TARGET].std(),y_min=z[TARGET].min(),y_max=z[TARGET].max(),y_range=z[TARGET].max()-z[TARGET].min()))
    summary=pd.DataFrame(summaries);summary.to_csv(out/'tables/07_profile_counts_geography_y.csv',index=False)
    pd.DataFrame(pairs).to_csv(out/'tables/08_identical_profile_pair_distances.csv',index=False)
    subdivision=q.groupby('rain').agg(n_parcels=(ID,'size'),n_joint_profiles=('joint','nunique'),n_thermal_profiles=('thermal','nunique'),n_labeled=(TARGET,'count')).reset_index()
    subdivision.to_csv(out/'tables/09_rain_profile_subdivision.csv',index=False)
    region=[]
    for field in ['Estado','Municipio']:
        for name,z in q.groupby(field):region.append(dict(field=field,region=name,n=len(z),**{kind+'_unique':z[kind].nunique() for kind in specs}))
    pd.DataFrame(region).to_csv(out/'tables/10_profiles_by_region.csv',index=False)
    lower=[]
    for kind in specs:
        labeled=q.dropna(subset=[TARGET]);means=labeled.groupby(kind)[TARGET].transform('mean')
        lower.append(dict(profile_definition=kind,n_groups=labeled[kind].nunique(),n_singleton_groups=int(labeled.groupby(kind).size().eq(1).sum()),empirical_in_sample_group_mean_RMSE=float(np.sqrt(np.mean((labeled[TARGET]-means)**2))),warning='in-sample identity; fragmentation mechanically lowers dispersion, not predictive improvement'))
    pd.DataFrame(lower).to_csv(out/'tables/11_intraprofile_y_identity.csv',index=False)
    # Verify shared raster support using previously checked parcel-grid geometry.
    support_file=ROOT/'outputs/data_audit/family_1/rainfall_yield/profile_geography_v1/parcel_coordinates_and_raster_support.csv'
    if support_file.exists():
        support=pd.read_csv(support_file)[[ID,'support']];z=q.merge(support,on=ID)
        z.groupby('thermal').agg(n_parcels=(ID,'size'),n_grid_supports=('support','nunique')).to_csv(out/'tables/12_thermal_profile_grid_support.csv')
    result=dict(exact_counts={name:int(membership[name].nunique()) for name in specs},near_counts={name:int(membership[name+'_near'].nunique()) for name in specs},
        subdivided_rain_groups=int(subdivision.n_joint_profiles.gt(1).sum()),parcels_in_subdivided_rain_groups=int(subdivision.loc[subdivision.n_joint_profiles.gt(1),'n_parcels'].sum()),
        pairs_distinguished_by_temperature=int(sum(len(z)*(len(z)-1)//2-sum(len(s)*(len(s)-1)//2 for _,s in z.groupby('joint')) for _,z in q.groupby('rain'))),
        profile_tolerance='rain .01 mm/month; temperature .001 degrees C/month; max coordinate distance, complete linkage',
        grid_support_verified=support_file.exists())
    (out/'report/profile_summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    fig,ax=plt.subplots(figsize=(12,4));labeled=q.dropna(subset=[TARGET]);ax.scatter(labeled.thermal,labeled[TARGET],s=20,alpha=.65);ax.set(xlabel='Perfil térmico exacto',ylabel='Y observado t/ha',title='Dispersión de Y dentro de perfiles — 138 parcelas');save(fig,out,'03_y_within_thermal_profiles.png')
    return membership,result

def temporal_eda(d,frame,geo,train,out):
    cycle=d[d.month.between(4,10)].copy()
    stats=cycle.groupby(['year','month'])[['tmin_mean','tmax_mean','tmean_mean','dtr_mean','precip_mean']].agg(['mean','std','min','max','median'])
    stats.to_csv(out/'tables/02_monthly_year_descriptions.csv')
    change=[]
    for var in ['tmin_mean','tmax_mean','tmean_mean','dtr_mean']:
        a=cycle.groupby(['year','month'])[var].mean().unstack(0)
        a['historical_2022_24']=a[[2022,2023,2024]].mean(axis=1);a['delta_2025']=a[2025]-a.historical_2022_24
        for m,r in a.iterrows():change.append({'variable':var,'month':m,**{str(k):v for k,v in r.to_dict().items()}})
    pd.DataFrame(change).to_csv(out/'tables/03_same_month_year_differences.csv',index=False)
    descriptive=frame.drop(columns=[ID,'CONJUNTO']).describe().T
    descriptive['unique_values']=frame.drop(columns=[ID,'CONJUNTO']).nunique();descriptive.to_csv(out/'tables/04_feature_distributions.csv')
    labeled=frame.merge(train[[ID,TARGET]],on=ID)
    association=pd.DataFrame([dict(feature=c,n=138,pearson=labeled[c].corr(labeled[TARGET]),spearman=labeled[c].corr(labeled[TARGET],method='spearman'),role='descriptive only, no retrospective feature selection') for c in frame if c not in [ID,'CONJUNTO']])
    association.to_csv(out/'tables/05_feature_y_associations.csv',index=False)
    topo=pd.read_parquet(ROOT/'data/processed/family_1/features/topography_basic_features.parquet')
    topo_cols=[c for c in topo if c.endswith(('elevation_mean','slope_mean'))]
    frame[TEMP].join(topo.set_index(ID).reindex(frame[ID])[topo_cols].reset_index(drop=True)).corr().loc[TEMP,topo_cols].to_csv(out/'tables/13_temperature_topography_descriptive_correlations.csv')
    regional=frame.merge(geo[[ID,'Estado','Municipio']],on=ID)
    regional.groupby(['Estado','Municipio'])[TEMP].agg(['count','mean','std','min','max']).to_csv(out/'tables/14_thermal_region_variation.csv')
    rows=[]
    low,high=train[TARGET].quantile([.25,.75]);labeled['yield_segment']=np.where(labeled[TARGET]<=low,'LOW',np.where(labeled[TARGET]>=high,'HIGH','MID'))
    labeled.groupby('yield_segment')[TEMP].agg(['mean','std','count']).to_csv(out/'tables/15_low_high_thermal_descriptions.csv')
    for var,cols in [('tmin',MIN),('tmax',MAX)]:
        fig,axes=plt.subplots(1,2,figsize=(12,4));cur=cycle[cycle.year.eq(2025)]
        sns.boxplot(data=cur,x='month',y=var+'_mean',ax=axes[0]);axes[0].set_ylabel('Promedio mensual (°C)')
        for year,z in cycle.groupby('year'):
            z=z.groupby('month')[var+'_mean'].agg(['mean','std']);axes[1].plot(z.index,z['mean'],'o-',label=str(year))
            if year==2025:axes[1].fill_between(z.index,z['mean']-z['std'],z['mean']+z['std'],alpha=.2,label='2025 ± SD espacial')
        axes[1].legend();axes[1].set(xlabel='Mes',ylabel='°C');fig.suptitle(var+' — medias mensuales, no extremos diarios');save(fig,out,f'01_{var}_box_and_years.png')
        fig,axes=plt.subplots(2,4,figsize=(13,6))
        for m,ax in zip(range(4,11),axes.flat):ax.hist(cur.loc[cur.month.eq(m),var+'_mean'],bins=18);ax.set(title=f'Mes {m}',xlabel='°C')
        axes.flat[-1].axis('off');save(fig,out,f'02_{var}_monthly_histograms.png')
        fig,axes=plt.subplots(2,4,figsize=(14,7));z=regional
        for col,ax in zip(cols,axes.flat):
            sc=ax.scatter(z.merge(geo[[ID,'longitude','latitude']],on=ID).longitude,z.merge(geo[[ID,'longitude','latitude']],on=ID).latitude,c=z[col],s=14,cmap='coolwarm');fig.colorbar(sc,ax=ax,label='°C');ax.set_title(col)
        axes.flat[-1].axis('off');save(fig,out,f'04_{var}_monthly_maps.png')
        frame[cols].corr().to_csv(out/'tables'/f'16_{var}_month_correlations.csv')
        fig,ax=plt.subplots(figsize=(7,6));sns.heatmap(frame[cols].corr(),vmin=-1,vmax=1,cmap='coolwarm',annot=True,fmt='.2f',ax=ax);save(fig,out,f'05_{var}_month_correlations.png')
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for var,ax in zip(['tmin_mean','tmax_mean'],axes):
        for year,z in cycle.groupby('year'):ax.plot(range(4,11),z.groupby('month')[var].std(),'o-',label=str(year))
        ax.set(title=var,xlabel='Mes',ylabel='SD espacial (°C)');ax.legend()
    save(fig,out,'06_spatial_variability_by_month.png')
    fig,axes=plt.subplots(1,3,figsize=(14,4))
    for col,ax in zip(['tmin_cycle_mean','tmax_cycle_mean','dtr_cycle_mean'],axes):
        sns.scatterplot(data=labeled.merge(geo[[ID,'Estado']],on=ID),x=col,y=TARGET,hue='Estado',ax=ax,s=25)
        sns.regplot(data=labeled,x=col,y=TARGET,scatter=False,lowess=True,ax=ax,color='black');ax.set_title('Relación descriptiva, no selección')
    save(fig,out,'07_thermal_y_apparent_nonlinearity.png')

def prepare_g(run_id):
    out,proc=paths('G',run_id)
    if (out/'manifest.json').exists():raise FileExistsError('Completed run; choose new run-id')
    out.mkdir(parents=True,exist_ok=True);proc.mkdir(parents=True,exist_ok=True)
    for name in ['tables','figures','report','models','splits','checkpoints']:(out/name).mkdir(exist_ok=True)
    print('G: protecting previous climate/family/Champion/raw artifacts',flush=True)
    if (out/'protected_inputs.json').exists():verify_snapshot(out)
    else:(out/'protected_inputs.json').write_text(json.dumps(original_snapshot(),indent=2),encoding='utf-8')
    context(out);d=load_longitudinal();audit=audit_sources(d,out);frame,dic=build_features(d)
    frame.to_parquet(proc/'climate_candidates_197.parquet',index=False);dic.to_csv(proc/'feature_dictionary.csv',index=False)
    train=supervised_data(frame,pd.read_csv(MASTER));geo=geography()
    temporal_eda(d,frame,geo,train,out);membership,result=profiles(frame,geo,train,out,'G')
    pcas=[pca_description(frame,cols,name,out,geo,train) for name,cols in [('Tmin',MIN),('Tmax',MAX),('Tmin_Tmax',TEMP),('Tmean_DTR',THERMAL['tmean']+THERMAL['dtr'])]]
    (out/'report/exploratory_pca_summary.json').write_text(json.dumps(pcas,indent=2),encoding='utf-8')
    (out/'descriptive_complete.json').write_text(json.dumps(dict(audit=audit,profiles=result,pca=pcas),indent=2),encoding='utf-8')
    print('G descriptive complete:',result,pcas,flush=True)

def joint_nonlinearity(d,out):
    """Same-month curves avoid confusing seasonal change with between-parcel association."""
    cycle=d[d.year.eq(2025)&d.month.between(4,10)]
    fig,axes=plt.subplots(2,7,figsize=(22,7));rows=[]
    for i,var in enumerate(['tmin_mean','tmax_mean']):
        for j,month in enumerate(range(4,11)):
            z=cycle[cycle.month.eq(month)];ax=axes[i,j]
            sns.regplot(data=z,x='precip_mean',y=var,lowess=True,scatter_kws=dict(s=9,alpha=.4),line_kws=dict(color='black'),ax=ax)
            ax.set(title=f'{var} — mes {month}',xlabel='mm/mes',ylabel='°C')
            rows.append(dict(month=month,variable=var,n_parcels=len(z),pearson=z.precip_mean.corr(z[var]),spearman=z.precip_mean.corr(z[var],method='spearman'),role='apparent shape only; spatially dependent parcels; no causal or inferential claim'))
    fig.suptitle('Relaciones lluvia–temperatura dentro de cada mes; LOWESS descriptivo')
    save(fig,out,'10_same_month_rain_temperature_lowess.png')
    pd.DataFrame(rows).to_csv(out/'tables/19_same_month_rain_thermal_associations.csv',index=False)

def prepare_h(run_id):
    gout,gproc=paths('G',run_id)
    if not (gout/'descriptive_complete.json').exists():raise ValueError('Complete G descriptive audit first')
    out,proc=paths('H',run_id);out.mkdir(parents=True,exist_ok=False);proc.mkdir(parents=True,exist_ok=False)
    for name in ['tables','figures','report','models','splits','checkpoints']:(out/name).mkdir()
    import shutil
    shutil.copy2(gout/'protected_inputs.json',out/'protected_inputs.json');context(out)
    frame=pd.read_parquet(gproc/'climate_candidates_197.parquet');train=supervised_data(frame,pd.read_csv(MASTER));geo=geography()
    frame[[ID,'CONJUNTO']+JOINT].to_parquet(proc/'joint_monthly_197.parquet',index=False)
    dictionary=pd.read_csv(gproc/'feature_dictionary.csv')
    dictionary[dictionary.feature.isin(JOINT)].to_csv(proc/'joint_monthly_dictionary.csv',index=False)
    current,cols=climate_current();current.to_parquet(proc/'climate_current_original_48.parquet',index=False)
    pd.DataFrame(dict(feature=cols,source=['CHIRPS' if c.startswith('CLIMATE_precip') else 'CHIRTS-ERA5' for c in cols],period='Apr-Oct 2025',role='exact original Climate Current retained feature schema')).to_csv(proc/'climate_current_original_dictionary.csv',index=False)
    _,result=profiles(frame,geo,train,out,'H')
    blocks={'rain':RAIN,'tmin':MIN,'tmax':MAX}
    full=frame[JOINT].corr();full.to_csv(out/'tables/17_joint_month_correlations.csv')
    pairs=[('rain','tmin'),('rain','tmax'),('tmin','tmax')]
    fig,axes=plt.subplots(1,3,figsize=(18,5))
    for (a,b),ax in zip(pairs,axes):
        block=full.loc[blocks[a],blocks[b]];block.to_csv(out/'tables'/f'18_{a}_{b}_correlations.csv');sns.heatmap(block,vmin=-1,vmax=1,cmap='coolwarm',ax=ax,annot=True,fmt='.2f');ax.set_title(a+' / '+b)
    save(fig,out,'08_cross_block_correlations.png')
    # Same-month relations and historical reference: descriptive, never selected from Y.
    d=load_longitudinal();current_long=d[d.year.eq(2025)&d.month.between(4,10)]
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for var,ax in zip(['tmin_mean','tmax_mean'],axes):
        sns.scatterplot(data=current_long,x='precip_mean',y=var,hue='month',palette='viridis',s=12,alpha=.5,ax=ax)
        ax.set_title('Parcela-mes descriptivo; no 1379 etiquetas Y')
    save(fig,out,'09_same_month_rain_temperature.png')
    joint_nonlinearity(d,out)
    cycle=d[d.month.between(4,10)]
    cycle.groupby(['year','month'])[['precip_mean','tmin_mean','tmax_mean']].agg(['mean','std']).to_csv(out/'tables/19_joint_year_month_reference.csv')
    pcas=[pca_description(frame,JOINT,name,out,geo,train,balanced=balanced) for name,balanced in [('Joint_standardized',False),('Joint_block_balanced',True)]]
    prior=pd.read_csv(ROOT/'outputs/modeling/family_1/rainfall_yield/e8/v1/tables/20_exploratory_variance.csv')
    prior.to_csv(out/'tables/28_prior_rain_PCA_variance_cached.csv',index=False)
    summary=json.loads((gout/'report/exploratory_pca_summary.json').read_text(encoding='utf-8'))+pcas
    pd.DataFrame([dict(name=x['name'],k90=x['k90'],k95=x['k95'],rank=x['rank'],n_columns=x['n_columns']) for x in summary]).to_csv(out/'tables/29_PCA_effective_dimensions.csv',index=False)
    (out/'report/exploratory_pca_summary.json').write_text(json.dumps(pcas,indent=2),encoding='utf-8')
    (out/'descriptive_complete.json').write_text(json.dumps(dict(profiles=result,pca=pcas),indent=2),encoding='utf-8')
    print('H descriptive complete:',result,pcas,flush=True)
