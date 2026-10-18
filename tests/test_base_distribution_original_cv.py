import numpy as np
from src.base_distribution_correction import SimplifiedBases

def test_outer_base_uses_original_internal_splits():
    factory=SimplifiedBases.__new__(SimplifiedBases)
    factory.original_outer_positions=np.array([2,4,8])
    original=[(np.array([0,1]),np.array([2])),(np.array([2]),np.array([0,1]))]
    factory.original_outer_cv=original
    assert factory.cv(np.array([2,4,8])) is original
