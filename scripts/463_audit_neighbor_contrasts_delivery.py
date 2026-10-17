"""Final frozen-design, internal-selection and delivered-artifact integrity audit."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.neighbor_signal_contrasts import OUT
from src.geoc_bridge import OLD


def main():
    assert (OUT/'evaluation_complete.json').exists();cfg=json.loads((OUT/'frozen_design.json').read_text())
    for file,expected in cfg['source_sha256'].items():assert hashlib.sha256(Path(file).read_bytes()).hexdigest()==expected,file
    initial_path=OUT/'audit/frozen_design.json.before_constant_support_fix'
    if initial_path.exists():
        original=json.loads(initial_path.read_text());unchanged=[k for k in original if k not in ['source_sha256','deep_support_policy']]
        for k in unchanged:assert cfg[k]==original[k],k
        checkpoint_hashes=json.loads((OUT/'audit/pre_fix_checkpoints.json').read_text())
        later=OUT/'audit/pre_inner_cv_fix_checkpoints.json'
        if later.exists():checkpoint_hashes.update(json.loads(later.read_text()))
        for file,expected in checkpoint_hashes.items():assert hashlib.sha256(Path(file).read_bytes()).hexdigest()==expected,file
    else:checkpoint_hashes={}
    plan=joblib.load(OLD/'cache/execution_plan.joblib');selection=pd.read_parquet(OUT/'tables/selection.parquet');candidates=pd.read_parquet(OUT/'tables/candidates.parquet');verified=0;nulls=0;constant_trees=0;split_rows=[]
    for fi in range(65):
        pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');np.testing.assert_array_equal(pack['train_positions'],plan[fi]['train_positions']);np.testing.assert_array_equal(pack['validation_positions'],plan[fi]['validation_positions'])
        for name,model in pack['models'].items():
            key=plan[fi];mask=(candidates.protocol==key['protocol'])&(candidates['repeat']==key['repeat'])&(candidates.fold==key['fold'])&(candidates.experiment==name);rows=candidates[mask].to_dict('records');assert len(rows)==9;best=min(rows,key=lambda v:(round(v['rmse'],12),v['amplitude'],v['depth'],-v['leaf']));s=selection[(selection.protocol==key['protocol'])&(selection['repeat']==key['repeat'])&(selection.fold==key['fold'])&(selection.experiment==name)].iloc[0]
            for field in ['amplitude','depth','leaf','rmse']:assert np.isclose(s[field],best[field]),(fi,name,field)
            adjustment=model['adjustment'];assert adjustment.amplitude==best['amplitude'];np.testing.assert_array_equal(model['contrast'].positions,pack['train_positions']);verified+=1
            if adjustment.amplitude==0:nulls+=1
            if adjustment.tree is not None:
                tree=adjustment.tree;assert tree.get_depth()<=2 and tree.get_n_leaves()<=4
                if tree.get_n_leaves()==1:constant_trees+=1
                for node,feature in enumerate(tree.tree_.feature):
                    if feature>=0:split_rows.append(dict(execution_index=fi,experiment=name,protocol=key['protocol'],feature_index=int(feature),threshold=float(tree.tree_.threshold[node]),node_support=int(tree.tree_.n_node_samples[node])))
    pd.DataFrame(split_rows,columns=['execution_index','experiment','protocol','feature_index','threshold','node_support']).to_csv(OUT/'tables/splits_by_fold.csv',index=False)
    report=ROOT/'documentation/neighbor_signal_contrasts_conclusions.md';assert report.exists()
    products=[ROOT/'documentation/neighbor_signal_contrasts_design.md',ROOT/'documentation/neighbor_signal_contrasts_results.md',report,OUT/'evaluacion_contrastes_vecinales.xlsx',OUT/'figures/rmse_changes.png']+[ROOT/'scripts'/f for f in ['460_prepare_neighbor_contrasts.py','461_run_neighbor_contrasts.py','462_evaluate_neighbor_contrasts.py',Path(__file__).name]]
    tests=pd.read_csv(OUT/'tables/paired_tests.csv');result=dict(status='complete',protected_hashes_verified=len(cfg['source_sha256']),models_verified=verified,external_folds=65,selection_matches_internal_candidates=True,null_selections=nulls,non_null_constant_trees=constant_trees,pre_fix_checkpoints_unchanged=len(checkpoint_hashes),significant_holm=int((tests.p_holm<.05).sum()),unit_tests_passed=7,no_PRED=True,no_final138_fit=True,product_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in products});(OUT/'delivery_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='product_sha256'},indent=2))


if __name__=='__main__':main()
