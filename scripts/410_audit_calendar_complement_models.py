"""Numerical and tree-support audit after all fits; no refits."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
import joblib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.calendar_complements import OUT,OLD

if __name__=='__main__':
    contexts=[];trees=[];complexity=[]
    splits=joblib.load(OLD/'frozen65_splits.joblib')
    for directory in sorted((OUT/'context_cache').iterdir()):
        fi=int(directory.name);pro,re,fo,*_=splits[fi]
        for path in directory.glob('*.joblib'):
            pack=joblib.load(path)
            for name,b in pack['representations'].items():
                m=b['model']
                contexts.append(dict(context=path.stem,external_fold_index=fi,protocol=pro,representation=name,n_train=len(pack['train_positions']),selected_representation=name==pack['chosen'],n_iter=int(m.model_.n_iter_),dual_gap=float(m.model_.dual_gap_),warnings=len(m.warnings_)))
    for fi,(pro,re,fo,*_) in enumerate(splits):
        pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib')
        for name,b in pack['base']['representations'].items():
            m=b['model'];complexity.append(dict(experiment=name,protocol=pro,repeat=re,fold=fo,n_input=len(m.columns),n_selected=int(m.used_.sum()),n_iter=int(m.model_.n_iter_),warnings=len(m.warnings_)))
        b=pack['base']['representations'][pack['base']['chosen']];m=b['model']
        complexity.append(dict(experiment='SELECTED_BASE',protocol=pro,repeat=re,fold=fo,n_input=len(m.columns),n_selected=int(m.used_.sum()),n_iter=int(m.model_.n_iter_),warnings=len(m.warnings_)))
        for name,b in pack['corrections'].items():
            m=b['model']
            if m is not None and m.kind=='tree':
                for node,f in enumerate(m.model_.tree_.feature):
                    if f>=0:trees.append(dict(experiment=name,protocol=pro,repeat=re,fold=fo,node=node,feature=m.columns[f],n_samples=int(m.model_.tree_.n_node_samples[node]),threshold_standardized=float(m.model_.tree_.threshold[node])))
    c=pd.DataFrame(contexts);c.to_csv(OUT/'audit/context_selected_model_convergence.csv',index=False)
    pd.DataFrame(trees).to_csv(OUT/'diagnostics/corrector_tree_splits.csv',index=False)
    d=pd.DataFrame(complexity);d.to_csv(OUT/'diagnostics/base_complexity_by_fold.csv',index=False)
    d.groupby(['experiment','protocol']).agg(n_input_median=('n_input','median'),n_selected_median=('n_selected','median'),n_selected_min=('n_selected','min'),n_selected_max=('n_selected','max'),warnings=('warnings','sum')).reset_index().to_csv(OUT/'diagnostics/base_complexity_summary.csv',index=False)
    audit=dict(tuned_contexts=c[['external_fold_index','context']].drop_duplicates().shape[0],context_representation_refits=len(c),context_refits_with_warnings=int(c.warnings.gt(0).sum()),context_refits_at_iteration_cap=int(c.n_iter.ge(100000).sum()),outer_base_refits_with_warnings=int(d[d.experiment.ne('SELECTED_BASE')].warnings.gt(0).sum()),candidate_warning_events_recorded=len(json.loads((OUT/'audit/warnings.json').read_text())),candidate_warning_capture_limitation='Completed-fold logs retained; interrupted pre-checkpoint contexts preserve selected-model warnings but not every discarded candidate warning. Exhaustive selected-model audit supplied.',runtime_warning='Intel and LLVM OpenMP warning at threadpool discovery; Windows execution completed and prediction replay exact.',preprocessing_memoization=json.loads((OUT/'audit/execution_memoization.json').read_text()),export='Final outer base objects exported to original BlockEstimator; no prediction memoization in delivered outer models.')
    (OUT/'audit/numerical_summary.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print(json.dumps(audit,indent=2));print(pd.DataFrame(trees).to_string(index=False))
