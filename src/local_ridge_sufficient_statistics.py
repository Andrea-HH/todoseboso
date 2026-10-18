"""Equivalent small dense weighted Ridge solve without per-query estimator setup."""
import numpy as np
from scipy import linalg

def predict_local_ridge(x,distance,observed,query,targets,k=24,alpha=30.):
    observed=np.asarray(observed,int);query=np.asarray(query,int);targets=np.asarray(targets,float);assert not set(observed)&set(query)
    if len(observed)<3:return np.full(len(query),targets.mean())
    y=np.full(len(x),np.nan);y[observed]=targets;result=[]
    for position in query:
        distances=np.asarray(distance[position,observed],float);finite=np.isfinite(distances);candidates=observed[finite];dd=distances[finite]
        if len(candidates)<3:result.append(float(targets.mean()));continue
        order=np.argsort(dd);take=order[:max(3,min(k,len(order)))];local=candidates[take];w=1/(dd[take]+1e-6);xx=np.array(x[local],dtype=float,copy=True);yy=np.array(y[local],dtype=float,copy=True);xm=np.average(xx,axis=0,weights=w);ym=np.average(yy,weights=w);xx-=xm;yy-=ym;sw=np.sqrt(w);xx*=sw[:,None];yy*=sw
        if xx.shape[1]>xx.shape[0]:
            a=xx@xx.T;a.flat[::a.shape[0]+1]+=alpha;coef=xx.T@linalg.solve(a,yy,assume_a='pos',overwrite_a=False)
        else:
            a=xx.T@xx;a.flat[::a.shape[0]+1]+=alpha;b=xx.T@yy;coef=linalg.solve(a,b,assume_a='pos',overwrite_a=True)
        intercept=ym-xm@coef;result.append(float(x[position]@coef+intercept))
    return np.asarray(result)
