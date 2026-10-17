"""Freeze the expanded error-quartile inventory and nested diagnostic classification."""
from pathlib import Path
import sys,json,hashlib,math
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.difficult_quartile import OUT,SOURCE,CALIBRATION,load_inventory


def main():
    if (OUT/'frozen_design.json').exists():raise FileExistsError('Preserve difficult-quartile design')
    for name in ['tables','cache','models','audit','figures']:(OUT/name).mkdir(parents=True,exist_ok=True)
    errors=pd.read_csv(SOURCE);t=errors[(errors.experiment=='J7_BOTH')&(errors.protocol=='random')].sort_values('ID_POLIGONO').copy();assert len(t)==138 and t.ID_POLIGONO.is_unique
    hard=t.sort_values(['mean_squared_error','ID_POLIGONO'],ascending=[False,True]).head(math.ceil(.25*len(t))).ID_POLIGONO.tolist()
    t['hard_quartile']=t.ID_POLIGONO.isin(hard);t['direction']=t.mean_error.gt(0).map({True:'over',False:'under'});t['error_group']='remaining';t.loc[t.hard_quartile,'error_group']=t.loc[t.hard_quartile,'direction'].map({'over':'hard_over','under':'hard_under'})
    t['low_yield_quartile']=t.y_true.le(t.y_true.quantile(.25));t.to_csv(OUT/'tables/parcel_groups.csv',index=False)
    x,c,meta,aliases,paths=load_inventory(t.ID_POLIGONO.tolist());x.to_parquet(OUT/'cache/numeric_X138.parquet');c.to_parquet(OUT/'cache/categorical_X138.parquet');meta.to_csv(OUT/'tables/feature_catalog.csv',index=False);aliases.to_csv(OUT/'tables/exact_numeric_aliases.csv',index=False)
    eligible=meta[(meta.kind=='numeric')&(~meta.quality)&(~meta.geographic_identifier)]
    pools={'PHYSICAL':eligible[eligible.family.isin(['Relieve/topografía','Suelo','Geología/fisiografía'])].feature.tolist(),'ALL_SIGNALS':eligible.feature.tolist()}
    protected={}
    files=[SOURCE,*paths.values(),ROOT/'src/difficult_quartile.py',Path(__file__),ROOT/'scripts/475_analyze_difficult_quartile.py',ROOT/'scripts/476_deliver_difficult_quartile.py',ROOT/'tests/test_difficult_quartile.py',ROOT/'documentation/difficult_quartile_design.md',ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/frozen65_splits.joblib',ROOT/'outputs/modeling/signal_feature_engineering/v1/tables/predictions.parquet',CALIBRATION/'tables/predictions.parquet',OUT/'cache/numeric_X138.parquet',OUT/'cache/categorical_X138.parquet',OUT/'tables/parcel_groups.csv']+sorted((CALIBRATION/'checkpoints').glob('*.joblib'))
    for file in files:protected[str(file)]=hashlib.sha256(file.read_bytes()).hexdigest()
    cfg=dict(status='frozen_before_associations_and_classification',reference='J7_BOTH',primary_protocol='random',hard_n=len(hard),hard_ids=hard,hard_definition='top ceil(.25*138) by mean squared OOF error across ten random repetitions; ties ID',lower_target_definition='y <= empirical .25 quantile; retain ties separately from hard errors',classifiers=pools,classifier_parameters=dict(k=6,C=.1,class_weight='balanced',max_absolute_feature_correlation=.9,max_training_missing_fraction=.2),class_labels={'0':'remaining','1':'hard_over','2':'hard_under'},classification_target='For each outer fold use training-only q75(abs(crossfitted J7 residual)); train labels from saved training-only crossfit; test labels from exact outer J7 residual using that training threshold.',classification_validation='65 original outer folds; fixed classifier parameters; univariate feature selection/imputation/scaling only inside train; no residual correction performed.',contrasts=['hard_vs_remaining','hard_over_vs_hard_under','hard_over_vs_remaining','hard_under_vs_remaining','all_over_vs_under','low_yield_vs_other'],descriptive_statistics='Cliffs delta pooled and conditioned by municipality/profile; medians; BH over pooled tests within contrast; nominal p values exploratory with spatial dependence not accounted for.',source_sha256=protected,no_PRED=True,no_final138_fit=True,no_champion_change=True)
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Frozen',len(hard),'hard parcels;',len(x.columns),'distinct numeric vectors;',len(aliases),'exact aliases;',len(c.columns),'categorical descriptors.')
    print(t.groupby('error_group').size().to_string());print({k:len(v) for k,v in pools.items()})


if __name__=='__main__':main()
