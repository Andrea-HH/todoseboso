import numpy as np
import pandas as pd
import pytest
from src.physical_similarity import BlockRepresentation, ResidualCorrector, neighbor_weights, select_candidate


def test_representation_inductive_and_target_prohibited():
    x = pd.DataFrame({'a': [1., 2., np.nan, 4.], 'b': ['a', 'b', 'a', 'b']})
    m = BlockRepresentation(['a', 'b']).fit(x)
    before = m.transform(x)
    other = x.assign(RENDIMIENTO_T_HA=1e6)
    np.testing.assert_array_equal(before, m.transform(other))
    m.transform(pd.DataFrame({'a': [1e8], 'b': ['unseen']}))
    np.testing.assert_array_equal(before, m.transform(x))
    assert m.fields_['a']['median'] == 2.
    with pytest.raises(ValueError): BlockRepresentation(['RENDIMIENTO_T_HA']).fit(other)


def test_tied_neighbors_do_not_depend_on_order():
    x = np.zeros((5, 2)); y = np.arange(5.)
    w, _ = neighbor_weights(x, x[:1], 2)
    assert (w > 0).sum() == 5
    np.testing.assert_allclose(w@y, [2.])
    np.testing.assert_allclose(w[:, ::-1]@y[::-1], [2.])


def test_groups_shrink_and_center_and_constant_fallback():
    x = np.r_[np.zeros((10, 1)), np.ones((10, 1))]
    m = ResidualCorrector('groups', dict(n_clusters=4, shrinkage=20.)).fit(x, np.r_[np.ones(10), -np.ones(10)])
    assert np.max(abs(m.predict(x))) < 1.
    assert abs(m.predict(x).mean()) < 1e-12
    z = ResidualCorrector('groups', dict(n_clusters=4, shrinkage=20.)).fit(np.zeros((20, 1)), np.arange(20.))
    np.testing.assert_allclose(z.predict(np.zeros((3, 1))), 0.)


def test_selector_zero_correction_is_exact_and_prefers_simple_tie():
    y = np.arange(5.)
    best, _ = select_candidate(y, y, [np.ones(5)], [dict(k=12)])
    assert best['amplitude'] == 0.
    best, _ = select_candidate(y, y, [np.zeros(5)], [dict(k=12)])
    assert best['amplitude'] == 0.
