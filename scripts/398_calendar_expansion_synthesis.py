"""Sealed OOF metrics, block ablations and selection stability; no fits."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.calendar_expansion import OUT,BASE,metric
from src.family_8.research import pair_metrics

def run():
    DEST=OUT/'diagnostics'
    if DEST.exists():raise FileExistsError('Preserve diagnostics')
    DEST.mkdir()
    p=pd.read_parquet(OUT/'tables/oof_predictions.parquet')
    t=pd.read_parquet(BASE/'train138.parquet',columns=['ID_POLIGONO','Estado','Municipio','climate_profile','RENDIMIENTO_T_HA'])
    z=p.merge(t,on='ID_POLIGONO',validate='many_to_one');np.testing.assert_allclose(z.y_true,z.RENDIMIENTO_T_HA)
    metrics=[];pairs=[];regions=[];omissions=[];decomp=[]
    for (name,pro,re),g in z.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique
        key=dict(experiment=name,protocol=pro,repeat=re)
        metrics.append(dict(**key,**metric(g.y_true,g.y_pred)));pairs.append(dict(**key,**pair_metrics(g)))
        error=g.y_pred-g.y_true;decomp.append(dict(**key,bias_squared=error.mean()**2,error_variance=error.var(ddof=0),mse=np.mean(error**2)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=zone,n=len(h),**metric(h.y_true,h.y_pred)))
                q=g[g[kind]!=zone]
                if len(q)>1:omissions.append(dict(**key,kind=kind,omitted=str(zone),n=len(q),**metric(q.y_true,q.y_pred)))
    reps=pd.DataFrame(metrics);reps.to_csv(DEST/'metrics_by_repeat.csv',index=False)
    summary=reps.groupby(['experiment','protocol'])[['rmse','mae','bias','r2']].mean().reset_index();summary.to_csv(DEST/'metrics_summary.csv',index=False)
    pd.DataFrame(pairs).to_csv(DEST/'intraprofile_by_repeat.csv',index=False)
    pd.DataFrame(pairs).groupby(['experiment','protocol']).mean(numeric_only=True).reset_index().to_csv(DEST/'intraprofile_summary.csv',index=False)
    regional=pd.DataFrame(regions);regional.to_csv(DEST/'regional_by_repeat.csv',index=False)
    regional.groupby(['experiment','protocol','kind','zone'])[['n','rmse','mae','bias','r2']].mean().reset_index().to_csv(DEST/'regional_summary.csv',index=False)
    om=pd.DataFrame(omissions);om.to_csv(DEST/'omission_without_refit.csv',index=False)
    pd.DataFrame(decomp).to_csv(DEST/'bias_dispersion.csv',index=False)
    plans=[('CAL01','CAL00'),('CAL02','CAL01'),('CAL03','CAL00'),('CAL04','CAL02'),('CAL05','CAL04'),('CAL06','CAL04'),('CAL07','CAL05'),('CAL08','CAL04'),('CAL09','CAL04'),('CAL10','CAL04'),('CAL10','CAL08'),('CAL10','CAL09'),('CAL11','CAL04'),('CAL12','CAL04'),('CAL13','CAL00'),('CAL14','CAL00'),('CAL15','CAL02'),('CAL16','CAL15')]
    contrasts=[(a+'_'+n,a+'_'+b) for a in ['EN','CB'] for n,b in plans]
    contrasts += [('CB_CAL'+f'{i:02d}','EN_CAL'+f'{i:02d}') for i in range(17)]
    contrasts += [(name,reference) for name in p.experiment.unique() if name.startswith(('EN_','CB_')) for reference in ['C-T3','F7-00']]
    contrasts += [(a+'_'+f'CAL{i:02d}','R_'+f'CAL{i:02d}') for a in ['EN','CB'] for i in range(8)]
    contrasts=list(dict.fromkeys(contrasts));paired=[];gainframes=[];ompaired=[]
    for name,reference in contrasts:
        j=reps[reps.experiment.eq(name)].merge(reps[reps.experiment.eq(reference)].drop(columns='experiment'),on=['protocol','repeat'],suffixes=('','_ref'),validate='one_to_one')
        for _,r in j.iterrows():paired.append(dict(experiment=name,reference=reference,protocol=r.protocol,repeat=r['repeat'],**{'delta_'+k:r[k]-r[k+'_ref'] for k in ['rmse','mae','bias','r2']}))
        # Per-parcel paired changes for all planned comparisons.
        a=p[p.experiment.eq(name)][['protocol','repeat','fold','ID_POLIGONO','y_true','y_pred']]
        b=p[p.experiment.eq(reference)][['protocol','repeat','fold','ID_POLIGONO','y_true','y_pred']]
        g=a.merge(b,on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');np.testing.assert_allclose(g.y_true,g.y_true_ref)
        g['experiment']=name;g['reference']=reference;g['sse_gain']=(g.y_pred_ref-g.y_true)**2-(g.y_pred-g.y_true)**2;g['absolute_error_gain']=abs(g.y_pred_ref-g.y_true)-abs(g.y_pred-g.y_true)
        gainframes.append(g)
        if reference in ['C-T3','F7-00'] or name.endswith(('CAL05','CAL06','CAL11','CAL12')):
            h=om[om.experiment.eq(name)].merge(om[om.experiment.eq(reference)].drop(columns='experiment'),on=['protocol','repeat','kind','omitted'],suffixes=('','_ref'),validate='one_to_one');h['reference']=reference;h['delta_rmse']=h.rmse-h.rmse_ref
            ompaired.append(h[['experiment','reference','protocol','repeat','kind','omitted','delta_rmse']])
    paired=pd.DataFrame(paired);paired.to_csv(DEST/'paired_by_repeat.csv',index=False)
    paired.groupby(['experiment','reference','protocol'])[['delta_rmse','delta_mae','delta_bias','delta_r2']].mean().reset_index().to_csv(DEST/'paired_summary.csv',index=False)
    pd.concat(ompaired).to_csv(DEST/'paired_omissions.csv',index=False)
    gains=pd.concat(gainframes,ignore_index=True).merge(t[['ID_POLIGONO','Estado','Municipio']],on='ID_POLIGONO',validate='many_to_one');gains.to_parquet(DEST/'parcel_gains.parquet',index=False)
    parcel=gains.groupby(['experiment','reference','protocol','ID_POLIGONO','Estado','Municipio'],as_index=False)[['sse_gain','absolute_error_gain']].mean();parcel.to_csv(DEST/'parcel_gain_repeat_average.csv',index=False)
    parcel.groupby(['experiment','reference','protocol','Estado','Municipio']).agg(n=('ID_POLIGONO','size'),sse_gain=('sse_gain','sum'),mean_absolute_error_gain=('absolute_error_gain','mean'),fraction_improved=('absolute_error_gain',lambda a:(a>0).mean())).reset_index().to_csv(DEST/'municipal_gain_contributions.csv',index=False)
    extreme=[]
    for _,g in parcel.groupby(['experiment','reference','protocol']):
        for label,h in [('best',g.nlargest(5,'sse_gain')),('worst',g.nsmallest(5,'sse_gain'))]:
            h=h.copy();h['direction']=label;extreme.append(h)
    pd.concat(extreme).to_csv(DEST/'largest_improvements_deteriorations.csv',index=False)
    registry=pd.read_parquet(OUT/'tables/registry.parquet');params=registry.params.map(json.loads)
    registry['gamma']=[v.get('gamma',np.nan) for v in params];registry['alpha']=[v.get('alpha',np.nan) for v in params]
    registry['l1_ratio']=[v.get('l1_ratio',np.nan) for v in params];registry['depth']=[v.get('depth',np.nan) for v in params];registry['trees']=[v.get('iterations',np.nan) for v in params]
    registry['max_leaf_values']=(2**registry.depth)*registry.trees
    registry.to_csv(DEST/'registry_parameters.csv',index=False)
    registry.groupby(['experiment','protocol']).agg(n_input=('n_input','first'),n_design=('n_design','first'),selected_median=('n_selected','median'),selected_min=('n_selected','min'),selected_max=('n_selected','max'),selected_history_median=('n_selected_history','median'),mean_trees=('trees','mean'),mean_max_leaf_values=('max_leaf_values','mean'),fraction_null_history=('gamma',lambda a:(a==0).mean()),mean_seconds=('seconds','mean'),warnings=('warnings','sum')).reset_index().to_csv(DEST/'selection_complexity.csv',index=False)
    registry.groupby(['experiment','protocol','params']).size().rename('outer_folds').reset_index().to_csv(DEST/'configuration_frequency.csv',index=False)
    usage=pd.read_parquet(OUT/'tables/usage.parquet')
    usage.groupby(['experiment','protocol','feature']).agg(fraction_selected=('used','mean'),median_effect=('effect_standardized','median'),fraction_positive=('effect_standardized',lambda a:(a>0).mean()),mean_split_count=('split_count','mean'),history=('history','first')).reset_index().to_csv(DEST/'feature_selection_stability.csv',index=False)
    # Predefined exploratory association: does a historical departure track its incremental OOF gain?
    features=pd.read_parquet(OUT/'cache/features_train138.parquet');assoc=[]
    for algorithm in ['EN','CB']:
        q=parcel[(parcel.experiment==algorithm+'_CAL05')&(parcel.reference==algorithm+'_CAL04')].merge(features,on='ID_POLIGONO',validate='many_to_one')
        for pro,g in q.groupby('protocol'):
            for f in ['DELTA_CAL_S2_ndvi_post_jul_aug','DELTA_CAL_S2_ndvi_late_sep_oct','HIST_SD_CAL_S2_ndvi_post_jul_aug']:
                a=g[[f,'sse_gain']].dropna();assoc.append(dict(algorithm=algorithm,protocol=pro,feature=f,n=len(a),spearman_gain=a[f].corr(a.sse_gain,method='spearman')))
    pd.DataFrame(assoc).to_csv(DEST/'exploratory_anomaly_gain_associations.csv',index=False)
    pro=['random','climate_profile','municipality','spatial'];mat=summary.pivot(index='experiment',columns='protocol',values='rmse')
    fig,axes=plt.subplots(1,2,figsize=(13,10));limit=np.max(abs(mat.loc[[a+f'_CAL{i:02d}' for a in ['EN','CB'] for i in range(17)],pro].to_numpy()-mat.loc['C-T3',pro].to_numpy()))
    for ax,algorithm in zip(axes,['EN','CB']):
        rows=[algorithm+f'_CAL{i:02d}' for i in range(17)];delta=mat.loc[rows,pro]-mat.loc['C-T3',pro]
        im=ax.imshow(delta,aspect='auto',cmap='RdBu_r',vmin=-limit,vmax=limit)
        ax.set(xticks=range(4),xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],yticks=range(17),yticklabels=[f'CAL{i:02d}' for i in range(17)],title='Elastic Net' if algorithm=='EN' else 'CatBoost')
        for i in range(17):
            for j in range(4):ax.text(j,i,f'{delta.iloc[i,j]:+.3f}',ha='center',va='center',fontsize=8,color='white' if abs(delta.iloc[i,j])>.65*limit else 'black')
    fig.suptitle('Cambio de RMSE frente a C-T3: negativo = menor error\nComparaciones exploratorias sobre las mismas 138 parcelas');fig.tight_layout(rect=(0,0,.92,.95));fig.colorbar(im,ax=axes.ravel().tolist(),fraction=.025,pad=.02);fig.savefig(DEST/'rmse_vs_ct3.png',dpi=160);plt.close(fig)
    print(mat[pro].to_string())

if __name__=='__main__':run()
