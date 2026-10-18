"""Validate C-T3 grid equivalence on real nested contexts before resuming."""
from pathlib import Path
import sys,json,time,hashlib
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.four_expert_combinations import OUT,OLD
from src.four_expert_fast_tuner import ORIGINAL,tune_base_cached_repr,ConditionalFeatures,CORE
from src.family_8.research import subcv
def main():
    t=pd.read_parquet(OLD/'cache/train138.parquet');y=t.RENDIMIENTO_T_HA.to_numpy();groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO');plan=joblib.load(OUT/'frozen81_splits.joblib');rows=[];skips=[]
    with threadpool_limits(limits=1):
        for fi in [0,13,50,55,60,65,72,80]:
            pro,_,_,tr,va,inner=plan[fi];pro='random' if pro=='fresh_97_41' else pro;aa=tr[inner[0][0]];contexts=[tr,aa,tr[inner[-1][0]]]
            try:contexts.append(aa[subcv(t,aa,pro,groups)[0][0]])
            except ValueError:pass
            for level,trr in enumerate(contexts):
                try:cv=inner if level==0 else subcv(t,trr,pro,groups)
                except ValueError:skips.append(dict(fi=fi,level=level,reason='No grouped CV; original fixed fallback'));continue
                if any(not ConditionalFeatures(tuple(CORE)).fit(t.iloc[trr[c]]).support_.any() for c,d in cv):skips.append(dict(fi=fi,level=level,reason='No supported inner predictors; original fixed fallback'));continue
                begin=time.perf_counter();a,ar,al=ORIGINAL(t,y,trr,cv);slow=time.perf_counter()-begin;begin=time.perf_counter();b,br,bl=tune_base_cached_repr(t,y,trr,cv);fast=time.perf_counter()-begin;difference=float(max(abs(a.predict(t)-b.predict(t))));assert difference<1e-12;assert ar['params']==br['params'] and ar['fit_count']==br['fit_count'];score_difference=float(max(abs(np.asarray(ar.get('candidate_mean_rmse',[0]))-np.asarray(br.get('candidate_mean_rmse',[0])))));assert score_difference<1e-12;assert al==bl;rows.append(dict(execution_index=fi,level=level,n_train=len(trr),prediction_difference=difference,score_difference=score_difference,params_equal=True,warnings_equal=True,original_seconds=slow,optimized_seconds=fast));print(f'Tuner parity {fi}/{level} {difference:.2g}',flush=True)
    files=[ROOT/'src/four_expert_fast_tuner.py',ROOT/'scripts/515_verify_four_expert_tuner.py',ROOT/'scripts/516_run_four_expert_cached_tuner.py',ROOT/'tests/test_four_expert_fast_tuner.py'];report=dict(reason='Reuse identical train-only preprocessing per inner fold across the twelve C-T3 grid points',no_grid_fold_seed_tie_or_loss_change=True,checks=len(rows),skips=skips,max_prediction_difference=max(r['prediction_difference'] for r in rows),max_candidate_score_difference=max(r['score_difference'] for r in rows),original_seconds=sum(r['original_seconds'] for r in rows),optimized_seconds=sum(r['optimized_seconds'] for r in rows),source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files});pd.DataFrame(rows).to_csv(OUT/'audit/cached_tuner_parity.csv',index=False);(OUT/'tuner_performance_amendment.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
