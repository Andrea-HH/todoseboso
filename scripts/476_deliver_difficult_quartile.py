"""Evaluate honest diagnostic classification and package error-quartile inventories."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import accuracy_score,balanced_accuracy_score,f1_score,log_loss,roc_auc_score,confusion_matrix,precision_recall_fscore_support
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.difficult_quartile import OUT


def md(f):
    def cell(v):return f'{v:.3f}' if isinstance(v,(float,np.floating)) else str(v).replace('|','/')
    return '\n'.join(['| '+' | '.join(f.columns)+' |','| '+' | '.join(['---']*len(f.columns))+' |']+['| '+' | '.join(map(cell,r))+' |' for r in f.itertuples(index=False,name=None)])


def classification_metrics(g):
    y=g.actual.to_numpy(int);p=g[['p_remaining','p_over','p_under']].to_numpy(float);pred=p.argmax(axis=1);hard=y!=0
    direction_probability=p[:,1]/np.maximum(p[:,1]+p[:,2],1e-15);direction=(direction_probability>=.5).astype(int);truth=(y==1).astype(int)
    return dict(n=len(g),n_hard=int(hard.sum()),accuracy=accuracy_score(y,pred),balanced_accuracy=balanced_accuracy_score(y,pred),macro_f1=f1_score(y,pred,labels=[0,1,2],average='macro',zero_division=0),log_loss=log_loss(y,p,labels=[0,1,2]),hard_detection_auc=roc_auc_score(hard,p[:,1]+p[:,2]) if len(np.unique(hard))==2 else np.nan,hard_direction_auc=roc_auc_score(truth[hard],direction_probability[hard]) if len(np.unique(truth[hard]))==2 else np.nan,hard_direction_balanced_accuracy=balanced_accuracy_score(truth[hard],direction[hard]) if len(np.unique(truth[hard]))==2 else np.nan)


def main():
    if (OUT/'delivery_audit.json').exists():raise FileExistsError('Preserve delivered quartile analysis')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert (OUT/'analysis_complete.json').exists();assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    D=OUT/'tables';t=pd.read_csv(D/'parcel_groups.csv');x=pd.read_parquet(OUT/'cache/numeric_X138.parquet');meta=pd.read_csv(D/'feature_catalog.csv');p=pd.read_parquet(D/'classification_OOF.parquet')
    assert len(p)==3*1794 and not p.duplicated(['classifier','protocol','repeat','ID_POLIGONO']).any();metrics=[];confusions=[];classrows=[]
    for (name,pro,re),g in p.groupby(['classifier','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;metrics.append(dict(classifier=name,protocol=pro,repeat=re,**classification_metrics(g)));y=g.actual.to_numpy(int);pred=g[['p_remaining','p_over','p_under']].to_numpy().argmax(axis=1);cm=confusion_matrix(y,pred,labels=[0,1,2]);precision,recall,fscore,support=precision_recall_fscore_support(y,pred,labels=[0,1,2],zero_division=0)
        for a in range(3):
            classrows.append(dict(classifier=name,protocol=pro,repeat=re,actual=a,precision=precision[a],recall=recall[a],f1=fscore[a],support=support[a]))
            for b in range(3):confusions.append(dict(classifier=name,protocol=pro,repeat=re,actual=a,predicted=b,n=int(cm[a,b])))
    m=pd.DataFrame(metrics);m.to_csv(D/'classification_metrics_by_repeat.csv',index=False);summary=m.drop(columns='repeat').groupby(['classifier','protocol']).mean(numeric_only=True).reset_index();summary.to_csv(D/'classification_metrics_summary.csv',index=False);pd.DataFrame(confusions).to_csv(D/'confusions_by_repeat.csv',index=False);pd.DataFrame(classrows).to_csv(D/'class_metrics_by_repeat.csv',index=False)
    sels=pd.read_csv(D/'classifier_selected_features.csv');stab=sels.groupby(['classifier','protocol','feature']).agg(n_selected=('execution_index','nunique'),coef_remaining=('coef_remaining','mean'),coef_hard_over=('coef_hard_over','mean'),coef_hard_under=('coef_hard_under','mean')).reset_index();denom={'random':50,'climate_profile':5,'municipality':5,'spatial':5};stab['selection_fraction']=stab.n_selected/stab.protocol.map(denom);stab=stab.merge(meta,on='feature',validate='many_to_one');stab.to_csv(D/'classifier_selection_stability.csv',index=False)
    # Replay every fitted diagnostic classifier against the saved external predictions.
    trframe=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');source_ids=trframe.ID_POLIGONO.tolist();xx=x.loc[source_ids];replay=[]
    for fi in range(65):
        pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];assert not set(tr)&set(va)
        for name,entry in pack['models'].items():
            got=entry['model'].predict_proba(xx.iloc[va][entry['columns']].to_numpy(float));expected=p[(p.execution_index==fi)&(p.classifier==name)].set_index('ID_POLIGONO').loc[trframe.iloc[va].ID_POLIGONO][['p_remaining','p_over','p_under']].to_numpy();difference=float(abs(got-expected).max());assert difference<1e-12;replay.append(dict(execution_index=fi,classifier=name,max_difference=difference))
    pd.DataFrame(replay).to_csv(OUT/'audit/classifier_replay.csv',index=False)
    cohort_rows=[]
    for municipality,g in t.groupby('Municipio'):
        cohort_rows.append(dict(Municipio=municipality,n=len(g),hard_n=int(g.hard_quartile.sum()),hard_fraction=float(g.hard_quartile.mean()),hard_over=int(g.error_group.eq('hard_over').sum()),hard_under=int(g.error_group.eq('hard_under').sum()),low_yield_n=int(g.low_yield_quartile.sum())))
    composition=pd.DataFrame(cohort_rows);composition.to_csv(D/'municipal_composition.csv',index=False)
    counts=[]
    for group,g in t.groupby('error_group'):
        counts.append(dict(group=group,n=len(g),yield_median=g.y_true.median(),prediction_median=g.mean_prediction.median(),mean_error=g.mean_error.mean(),mean_absolute_error=g.mean_absolute_error.mean(),sse_share=g.mean_squared_error.sum()/t.mean_squared_error.sum()))
    pd.DataFrame(counts).to_csv(D/'error_group_summary.csv',index=False)
    # Cohorts stay frozen from original J7 random diagnostics across other models/protocols.
    pred=pd.read_parquet(ROOT/'outputs/modeling/signal_feature_engineering/v1/tables/predictions.parquet');pred=pred[pred.experiment.isin(['CT3','J7_BOTH','J7_P_RAW'])];cohorts={'hard35':t[t.hard_quartile].ID_POLIGONO.tolist(),'remaining103':t[~t.hard_quartile].ID_POLIGONO.tolist(),'hard_over':t[t.error_group=='hard_over'].ID_POLIGONO.tolist(),'hard_under':t[t.error_group=='hard_under'].ID_POLIGONO.tolist(),'low_yield':t[t.low_yield_quartile].ID_POLIGONO.tolist()};perf=[]
    for (name,pro,re),g in pred.groupby(['experiment','protocol','repeat']):
        for cohort,ids in cohorts.items():
            h=g[g.ID_POLIGONO.isin(ids)];e=h.y_pred-h.y_true;tss=((h.y_true-h.y_true.mean())**2).sum();perf.append(dict(experiment=name,protocol=pro,repeat=re,cohort=cohort,n=len(h),rmse=float(np.sqrt(np.mean(e**2))),mae=float(abs(e).mean()),bias=float(e.mean()),r2=float(1-np.sum(e**2)/tss) if tss>1e-12 else np.nan))
    perf=pd.DataFrame(perf);perf.to_csv(D/'cohort_regression_metrics_by_repeat.csv',index=False);perf.drop(columns='repeat').groupby(['experiment','protocol','cohort']).mean(numeric_only=True).reset_index().to_csv(D/'cohort_regression_metrics_summary.csv',index=False)
    # Present a short, nonredundant inventory. This is descriptive ranking, not feature selection for CV.
    allrows=pd.read_csv(D/'numeric_group_differences.csv');readable=[]
    for contrast,g in allrows.groupby('contrast'):
        g=g[(~g.quality)&(~g.geographic_identifier)&(g.n_a>=8)&(g.n_b>=8)&(g.n_supported_municipalities>=2)&g.municipal_sign_consistent].copy();g['abs_effect']=abs(g.municipal_equal_weight_delta);g=g.sort_values('abs_effect',ascending=False);chosen=[];family_counts={}
        for _,r in g.iterrows():
            if family_counts.get(r.family,0)>=2:continue
            if chosen:
                correlations=[x[r.feature].corr(x[c]) for c in chosen]
                if any(pd.notna(c) and abs(c)>.9 for c in correlations):continue
            chosen.append(r.feature);family_counts[r.family]=family_counts.get(r.family,0)+1;readable.append(r)
            if len(chosen)>=12:break
    readable=pd.DataFrame(readable);readable.to_csv(D/'readable_conditional_inventory.csv',index=False)
    # Known signals remain visible even when their ranking is weak.
    known=['PLANET_evi_promedio_last_minus_first','TOPO_ADV_tpi_3x3_mean','S2_ndvi_derived_lower_gap_max_growth_rate','TOPO_BASIC_slope_mean','P_water','P_evi_change']
    allrows[allrows.original_feature.isin(known)].to_csv(D/'previously_nominated_signals.csv',index=False)
    best=readable[readable.contrast.isin(['hard_vs_remaining','hard_over_vs_hard_under','hard_over_vs_remaining','hard_under_vs_remaining'])]
    report=ROOT/'documentation/difficult_quartile_results.md';report.write_text('\n\n'.join(['# Cuartil difícil y signo del error: resultados exploratorios','El inventario usa35parcelas por error OOF J7 original. Los clasificadores usan umbrales y etiquetas cross-fitted dentro del entrenamiento de cada fold, no la etiqueta global top35. No se entrenaron correctores de rendimiento.','## Composición',md(pd.DataFrame(counts)),md(composition),'## Variables descriptivas con contraste dentro de municipio',md(best[['contrast','original_feature','family','median_a','median_b','cliffs_delta','municipal_equal_weight_delta','n_supported_municipalities','profile_equal_weight_delta','n_supported_profiles']]),'Cliff delta positivo: primer grupo tiene valores más altos. Medianas son globales; efectos condicionados comparan sólo dentro del mismo municipio/perfil. Las categorías y todas las variables están en Excel. No se atribuyen causas ni significancia confirmatoria.','## Clasificación fuera de muestra',md(summary[['classifier','protocol','balanced_accuracy','macro_f1','hard_detection_auc','hard_direction_auc','hard_direction_balanced_accuracy']]),'Accuracy y métricas por clase están en tablas. PHYSICAL=suelo/relieve/geología numéricos; ALL_SIGNALS=todas las señales numéricas sin campos de calidad ni identificadores geográficos directos; PRIOR=frecuencias internas. La probabilidad de difícil no es un intervalo predictivo ni una corrección de rendimiento.','La reutilización histórica de estos datos y el origen de algunas features en residuos examinados hacen exploratoria toda la etapa. El cuartil de bajo rendimiento se conserva como cohorte separada, con empates.']),encoding='utf-8')
    with pd.ExcelWriter(OUT/'inventario_cuartil_dificil_y_signo.xlsx',engine='openpyxl') as w:
        pd.DataFrame({'lectura':['35difíciles por error J7 aleatorio; no equivalen a rendimiento bajo.','Sobreestimación=predicho−observado>0. Subestimación<0.','Efecto positivo: valores más altos en el primer grupo del contraste.','Contrastes dentro de municipio/perfil para distinguir confusión regional.','P y BH exploratorios; no causalidad ni confirmación independiente.','Clasificadores: objetivos definidos sólo dentro del entrenamiento; no corrección de rendimientos.']}).to_excel(w,sheet_name='LEEME',index=False)
        for file in sorted(D.glob('*.csv')):
            if file.stem in ['exact_numeric_aliases','classifier_selected_features']:continue
            pd.read_csv(file).to_excel(w,sheet_name=file.stem[:31],index=False)
        for sheet in w.book.worksheets:sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    (OUT/'delivery_audit.json').write_text(json.dumps(dict(status='complete',hard_n=35,hard_over_n=int((t.error_group=='hard_over').sum()),hard_under_n=int((t.error_group=='hard_under').sum()),low_yield_n=int(t.low_yield_quartile.sum()),diagnostic_models_replayed=len(replay),classification_OOF_rows=len(p),protected_hashes=len(cfg['source_sha256']),protected_sources_unchanged=True,no_PRED=True,no_final138_fit=True,no_champion_change=True),indent=2),encoding='utf-8');print(summary.to_string(index=False));print('\nREADABLE DIFFERENCES');print(best[['contrast','original_feature','median_a','median_b','municipal_equal_weight_delta']].to_string(index=False))


if __name__=='__main__':main()
