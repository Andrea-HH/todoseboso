"""Convex blend of frozen CT3 and original Local04D with X-only support."""
import numpy as np
WEIGHTS=[0.,.25,.5,.75,1.]

def blend(ct3,local,weight,support):
    support=np.asarray(support,float)
    if np.any((support<0)|(support>1)):raise ValueError('Support outside [0,1]')
    return np.asarray(ct3)+weight*support*(np.asarray(local)-np.asarray(ct3))

def choose(y,ct3,local,support):
    scores=[float(np.mean((blend(ct3,local,w,support)-np.asarray(y))**2)) for w in WEIGHTS]
    i=min(range(len(scores)),key=lambda j:(round(scores[j],12),WEIGHTS[j]))
    return WEIGHTS[i],scores
