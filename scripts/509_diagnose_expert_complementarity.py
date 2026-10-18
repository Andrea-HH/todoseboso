"""Descriptive hindsight expert selection; not a lower bound on convex mixtures."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.four_expert_combinations import OUT,NAMES
def main():
    p=pd.read_parquet(ROOT/'outputs/research/four_leaders/v1/matched_oof.parquet');rows=[];cases=[]
    for (pro,re),g in p.groupby(['protocol','repeat']):
        z=g.pivot(index='ID_POLIGONO',columns='experiment',values='y_pred');truth=g[['ID_POLIGONO','y_true']].drop_duplicates().set_index('ID_POLIGONO').loc[z.index].y_true.to_numpy();e=z.to_numpy()-truth[:,None];columns=z.columns.tolist();r=e[:,columns.index('Reference26')];ct=e[:,columns.index('CT3')];l=e[:,columns.index('L40')]
        for name,error in [('Oracle_R_L',np.where(abs(l)<abs(r),l,r)),('Oracle_R_C',np.where(abs(ct)<abs(r),ct,r)),('Oracle_four',e[np.arange(len(e)),np.argmin(abs(e),axis=1)])]:rows.append(dict(protocol=pro,repeat=re,experiment=name,rmse=np.sqrt(np.mean(error**2)),mae=abs(error).mean(),bias=error.mean(),warning='Uses true y to choose expert; not deployable or a bound on convex mixtures'))
        for i,id_ in enumerate(z.index):cases.append(dict(protocol=pro,repeat=re,ID_POLIGONO=id_,L40_better_than_R=abs(l[i])<abs(r[i]),CT3_better_than_R=abs(ct[i])<abs(r[i]),L40_opposite_sign=bool(l[i]*r[i]<0),CT3_opposite_sign=bool(ct[i]*r[i]<0),L40_mse_gain=r[i]**2-l[i]**2,CT3_mse_gain=r[i]**2-ct[i]**2,L40_disagreement=z.loc[id_,'L40']-z.loc[id_,'Reference26'],CT3_disagreement=z.loc[id_,'CT3']-z.loc[id_,'Reference26']))
    d=pd.DataFrame(rows);d.to_csv(OUT/'tables/oracle_bounds_by_repeat.csv',index=False);d.groupby(['protocol','experiment'])[['rmse','mae','bias']].mean().reset_index().to_csv(OUT/'tables/oracle_bounds.csv',index=False);d=pd.DataFrame(cases);d.to_csv(OUT/'tables/control_complementarity_by_oof.csv',index=False);d.groupby('protocol').agg(L40_better_fraction=('L40_better_than_R','mean'),CT3_better_fraction=('CT3_better_than_R','mean'),L40_opposite_sign_fraction=('L40_opposite_sign','mean'),CT3_opposite_sign_fraction=('CT3_opposite_sign','mean'),mean_L40_mse_gain=('L40_mse_gain','mean'),mean_CT3_mse_gain=('CT3_mse_gain','mean')).reset_index().to_csv(OUT/'tables/control_complementarity.csv',index=False)
if __name__=='__main__':main()
