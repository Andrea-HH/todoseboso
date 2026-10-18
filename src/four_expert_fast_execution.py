"""Performance-only execution amendment: equivalent weighted dense Ridge."""
import numpy as np
from src.local_ridge_sufficient_statistics import predict_local_ridge
from src import geoc_bridge

ORIGINAL=geoc_bridge.predict_weighted_local_ridge
def equivalent_weighted_local_ridge(x,distance_matrix,y,observed_positions,query_positions,*,k,alpha,distance_power):
    if distance_power!=1.:return ORIGINAL(x,distance_matrix,y,observed_positions,query_positions,k=k,alpha=alpha,distance_power=distance_power)
    observed=np.asarray(observed_positions,int)
    if len(observed)<3:raise ValueError('Local Ridge requires at least three observed parcels.')
    return predict_local_ridge(x,distance_matrix,observed,np.asarray(query_positions,int),np.asarray(y)[observed],k=k,alpha=alpha)
def activate():geoc_bridge.predict_weighted_local_ridge=equivalent_weighted_local_ridge
