"""Per-parcel descriptive inventory, readable figures and final provenance checks."""
from pathlib import Path
import sys,json,hashlib,warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.difficult_quartile import OUT,labels_for_errors


def main():
    D=OUT/'tables';cfg=json.loads((OUT/'frozen_design.json').read_text());t=pd.read_csv(D/'parcel_groups.csv');x=pd.read_parquet(OUT/'cache/numeric_X138.parquet');meta=pd.read_csv(D/'feature_catalog.csv').set_index('feature');hard=t[t.hard_quartile];assert len(hard)==35
    eligible=meta[(meta.kind=='numeric')&(~meta.quality)&(~meta.geographic_identifier)].index.tolist();a=x[eligible].to_numpy();records=[];support=[];cohorts={}
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for _,r in hard.iterrows():
            row=t.index[t.ID_POLIGONO==r.ID_POLIGONO][0]
            for scope,mask in [('TRAIN138',np.ones(len(t),bool)),('municipality',t.Municipio.eq(r.Municipio).to_numpy()),('climate_profile',t.climate_profile.eq(r.climate_profile).to_numpy())]:
                positions=np.flatnonzero(mask);key=tuple(positions)
                if key not in cohorts:
                    z=a[positions];q1,med,q3=np.nanquantile(z,[.25,.5,.75],axis=0);mad=np.nanmedian(abs(z-med),axis=0);n=np.isfinite(z).sum(axis=0);distinct=np.array([len(np.unique(c[np.isfinite(c)])) for c in z.T]);cohorts[key]=(z,q1,med,q3,mad,n,distinct)
                z,q1,med,q3,mad,n,distinct=cohorts[key];values=a[row];valid=(n>=12)&(distinct>=5)&((q3-q1)>1e-10)&np.isfinite(values)
                support.append(dict(ID_POLIGONO=r.ID_POLIGONO,scope=scope,n_cohort=len(positions),supported_numeric_features=int(valid.sum())))
                percent=100*(np.sum(z<values-1e-12,axis=0)+.5*np.sum(np.isclose(z,values,rtol=0,atol=1e-12),axis=0))/np.maximum(n,1);rz=np.divide(.67448975*(values-med),mad,out=np.full_like(values,np.nan),where=mad>1e-10)
                order=np.argsort(-abs(percent-50),kind='stable');chosen=[];counts={}
                for j in order:
                    if not valid[j]:continue
                    feature=eligible[j];family=meta.loc[feature,'family']
                    if counts.get(family,0)>=3:continue
                    if chosen:
                        corr=[x[feature].corr(x[c]) for c in chosen]
                        if any(pd.notna(c) and abs(c)>.9 for c in corr):continue
                    chosen.append(feature);counts[family]=counts.get(family,0)+1
                    records.append(dict(ID_POLIGONO=r.ID_POLIGONO,error_group=r.error_group,Municipio=r.Municipio,scope=scope,n_cohort=len(positions),feature=feature,original_feature=meta.loc[feature,'original_feature'],family=family,value=values[j],median=med[j],q25=q1[j],q75=q3[j],percentile=percent[j],robust_z=rz[j],flag_iqr=bool(values[j]<q1[j]-1.5*(q3[j]-q1[j]) or values[j]>q3[j]+1.5*(q3[j]-q1[j]))))
                    if len(chosen)>=12:break
    differences=pd.DataFrame(records);differences.to_csv(D/'parcel_specific_differences.csv',index=False);pd.DataFrame(support).to_csv(D/'parcel_specific_support.csv',index=False)
    # Prespecified known signals plus the observed directional signals are retained as descriptive tables.
    full=pd.read_csv(D/'numeric_group_differences.csv');features=['TOPO_BASIC_slope_min','TOPO_BASIC_slope_mean','S2_ndvi_derived_lower_gap_max','S2_ndvi_derived_lower_gap_max_growth_rate','S2_msi_derived_upper_gap_normalized_auc','PLANET_ndvi_derived_range_std','HIST_S2_ndvi_promedio_mean','sat_basic_hist__sentinel_2__fapar_min__mean']
    q=full[(full.contrast=='hard_over_vs_hard_under')&full.original_feature.isin(features)].copy();q.to_csv(D/'selected_directional_signals.csv',index=False)
    names={'TOPO_BASIC_slope_min':'Pendiente mínima','TOPO_BASIC_slope_mean':'Pendiente media','S2_ndvi_derived_lower_gap_max':'Brecha NDVI medio−mínimo: máximo','S2_ndvi_derived_lower_gap_max_growth_rate':'Brecha NDVI: máximo aumento','S2_msi_derived_upper_gap_normalized_auc':'Brecha MSI máximo−medio: AUC','PLANET_ndvi_derived_range_std':'Variación temporal del rango NDVI','HIST_S2_ndvi_promedio_mean':'NDVI histórico medio','sat_basic_hist__sentinel_2__fapar_min__mean':'FAPAR mínimo histórico: media'}
    q=q.set_index('original_feature').loc[features];fig,ax=plt.subplots(figsize=(11,6));pos=np.arange(len(q));ax.barh(pos-.17,q.municipal_equal_weight_delta,height=.32,label='Dentro de municipio');ax.barh(pos+.17,q.profile_equal_weight_delta,height=.32,label='Dentro de perfil');ax.set_yticks(pos,[names[c] for c in q.index]);ax.axvline(0,color='black',lw=.8);ax.set_xlim(-1,1);ax.set_xlabel('Cliff delta: positivo = valores mayores en sobreestimadas');ax.set_title('17 sobreestimadas frente a 18 subestimadas difíciles\nComparaciones descriptivas; soporte: 2 municipios / 3 perfiles');ax.legend();ax.invert_yaxis();fig.tight_layout();fig.savefig(OUT/'figures/directional_signal_differences.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,6));colors={'hard_over':'tab:red','hard_under':'tab:blue','remaining':'lightgray'}
    for group,g in t.groupby('error_group'):ax.scatter(g.mean_prediction,g.y_true,c=colors[group],label=f'{group}: n={len(g)}',s=35,alpha=.8)
    ax.plot([1.8,5.8],[1.8,5.8],'k--');ax.set(xlabel='Predicción OOF media J7 (t/ha)',ylabel='Rendimiento observado (t/ha)',title='Cuartil difícil y dirección del error');ax.legend();fig.tight_layout();fig.savefig(OUT/'figures/error_quartile_scatter.png',dpi=160);plt.close(fig)
    # Check the classifier correction changed PHYSICAL only, and that test labels use training thresholds.
    old=pd.read_parquet(OUT/'audit/initial_family_label_attempt/tables/classification_OOF.parquet');new=pd.read_parquet(D/'classification_OOF.parquet');keys=['classifier','protocol','repeat','fold','ID_POLIGONO'];z=old[old.classifier.isin(['ALL_SIGNALS','PRIOR'])].merge(new,on=keys,suffixes=('_initial','_fixed'),validate='one_to_one');assert len(z)==2*1794
    for c in ['p_remaining','p_over','p_under']:np.testing.assert_array_equal(z[c+'_initial'],z[c+'_fixed'])
    for cutoff,g in new.groupby('training_cutoff'):np.testing.assert_array_equal(labels_for_errors(g.outer_error.to_numpy(),cutoff),g.actual.to_numpy())
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    with pd.ExcelWriter(OUT/'inventario_cuartil_dificil_y_signo.xlsx',engine='openpyxl',mode='a',if_sheet_exists='replace') as w:
        for name in ['selected_directional_signals','parcel_specific_differences','parcel_specific_support']:pd.read_csv(D/(name+'.csv')).to_excel(w,sheet_name=name[:31],index=False)
        for sheet in w.book.worksheets:sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    p=OUT/'delivery_audit.json';delivery=json.loads(p.read_text());delivery.update(dict(per_parcel_differences=len(differences),test_labels_verified=True,all_signals_unchanged_after_physical_namespace_fix=True,tests_passed=4,physical_pool_count=len(cfg['classifiers']['PHYSICAL']),all_signals_pool_count=len(cfg['classifiers']['ALL_SIGNALS']),amendments=cfg['implementation_amendments']))
    artifact_paths=[OUT/'inventario_cuartil_dificil_y_signo.xlsx',D/'classification_OOF.parquet',D/'numeric_group_differences.csv',ROOT/'documentation/difficult_quartile_results.md',ROOT/'documentation/difficult_quartile_conclusions.md']
    delivery['artifact_sha256']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in artifact_paths if f.exists()};p.write_text(json.dumps(delivery,ensure_ascii=False,indent=2),encoding='utf-8');print('Verified final classification labels, source hashes, amendment parity and individual inventories:',len(differences),'rows.')


if __name__=='__main__':main()
