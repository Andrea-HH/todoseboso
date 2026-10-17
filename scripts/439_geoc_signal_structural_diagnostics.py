"""Post-fit descriptions of geographic means, local shrinkage and compact mixtures.

No refits, selection changes or PRED predictions. Effective degrees of freedom
condition on the fixed neighborhood, representation and weights of each query.
"""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('runner437',ROOT/'scripts/437_run_geoc_signal_research.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


def main():
    out=runner.OUT;d=out/'diagnostics';assert (out/'execution_complete.json').exists()
    if (d/'local_shrinkage_by_query.csv').exists():raise FileExistsError('Preserve structural diagnostics')
    assets=runner.load_assets();a=assets['a'];t=a['train'];pos=a['train_global'];p=pd.read_parquet(out/'tables/predictions.parquet');rows=[];comparisons=[]
    with threadpool_limits(limits=1):
        for fi in range(65):
            pack=joblib.load(out/'models'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];first=joblib.load(out/'checkpoints'/f'{fi:02d}.joblib')['predictions'][0];key={k:first[k] for k in ['protocol','repeat','fold']}
            for name in ['FULL_LOCAL','E_REDUCED_SMALL12_BOTH','E_REDUCED_EXPANDED30_BOTH']:
                variant=pack['models'][name]['expert'];local=pack['experts'][variant]['local'];x=assets['static'][variant] if local['representation'] is None else local['representation'].transform(assets['features197'])
                for i in va:
                    distances=a['distance'][pos[i],pos[tr]];take=np.argsort(distances)[:min(24,len(tr))];w=1/(distances[take]+1e-6);z=x[pos[tr[take]]];center=(w[:,None]*z).sum(axis=0)/w.sum();zc=z-center;eigen=np.linalg.eigvalsh(zc.T@(w[:,None]*zc));eigen=np.maximum(eigen,0)
                    rows.append(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,n_neighbors=len(take),n_features=x.shape[1],weight_sum=float(w.sum()),effective_neighbors=float(w.sum()**2/(w@w)),conditional_df=float(1+np.sum(eigen/(eigen+30))),largest_shrinkage_factor=float(eigen.max()/(eigen.max()+30))))
        for (pro,re),g in p.groupby(['protocol','repeat']):
            wide=g.pivot(index='ID_POLIGONO',columns='experiment',values='y_pred')
            for name,control in [('FULL_LOCAL','A_NEIGHBOR_MEAN_LOCAL'),('LEADER','A_NEIGHBOR_MEAN_COMPACT'),('E_REDUCED_SMALL12_BOTH','P1_BOTH'),('E_REDUCED_EXPANDED30_BOTH','P1_BOTH')]:
                delta=wide[name]-wide[control];comparisons.append(dict(protocol=pro,repeat=re,experiment=name,control=control,prediction_correlation=float(wide[name].corr(wide[control])),rms_prediction_difference=float(np.sqrt(np.mean(delta**2))),mean_absolute_prediction_difference=float(abs(delta).mean()),max_absolute_prediction_difference=float(abs(delta).max())))
    r=pd.DataFrame(rows);r.to_csv(d/'local_shrinkage_by_query.csv',index=False)
    r.groupby(['experiment','protocol']).agg(mean_conditional_df=('conditional_df','mean'),median_conditional_df=('conditional_df','median'),min_conditional_df=('conditional_df','min'),max_conditional_df=('conditional_df','max'),mean_effective_neighbors=('effective_neighbors','mean'),median_weight_sum=('weight_sum','median'),mean_largest_shrinkage_factor=('largest_shrinkage_factor','mean')).reset_index().to_csv(d/'local_shrinkage_summary.csv',index=False)
    c=pd.DataFrame(comparisons);c.to_csv(d/'prediction_agreement_by_repeat.csv',index=False);c.drop(columns='repeat').groupby(['experiment','control','protocol']).mean(numeric_only=True).reset_index().to_csv(d/'prediction_agreement_summary.csv',index=False)
    cfg=json.loads((out/'frozen_design.json').read_text());defs=assets['physical_definitions'];gate=sum([defs[k]['columns'] for k in ['soil_texture_phase','geologic_composition','geologic_distances']],[]);inventory=[]
    for bundle in cfg['bundles']:
        for role,columns in [('compact_core',list(assets['core'].columns)),('local_expert',cfg['bundles'][bundle]),('physical_gate',gate),('neighbor_coordinates',['base_centroid_lat','base_centroid_lon'])]:
            inventory.extend(dict(bundle=bundle,role=role,feature=f) for f in columns)
    pd.DataFrame(inventory).to_csv(d/'reduced_mixture_input_inventory.csv',index=False)
    print(r.groupby(['experiment','protocol']).conditional_df.agg(['mean','min','max']).to_string());print(c.drop(columns='repeat').groupby(['experiment','control','protocol']).mean(numeric_only=True).round(6).to_string())


if __name__=='__main__':main()
