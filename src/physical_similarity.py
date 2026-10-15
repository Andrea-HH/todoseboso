"""Inductive, block-balanced representations and centered residual correctors.

Neither identifiers, coordinates nor targets are accepted as representation inputs.
"""
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.linear_model import Ridge
from scipy.spatial.distance import cdist

AMPLITUDES = [0., .25, .5]
GRIDS = {'ridge': [dict(alpha=a) for a in [1., .1, .01]],
         'neighbors': [dict(k=k) for k in [12, 24, 48]],
         'groups': [dict(n_clusters=k, shrinkage=20.) for k in [4, 8]]}


class BlockRepresentation:
    def __init__(self, columns, components=5):
        self.columns = list(columns)
        self.components = components

    def _matrix(self, frame):
        arrays = []
        for c, spec in self.fields_.items():
            if spec['numeric']:
                x = pd.to_numeric(frame[c], errors='coerce').to_numpy(float)
                arrays.append(np.where(np.isfinite(x), x, spec['median'])[:, None])
            else:
                x = frame[c].fillna('__MISSING__').astype(str).to_numpy()
                arrays.append(np.column_stack([x == v for v in spec['levels']]).astype(float))
        return np.column_stack(arrays) if arrays else np.zeros((len(frame), 1))

    def fit(self, frame):
        forbidden = ['ID_POLIGONO', 'RENDIMIENTO_T_HA', 'Estado', 'Municipio', 'latitude', 'longitude', 'climate_profile']
        if set(self.columns) & set(forbidden):
            raise ValueError('Identifiers, target or geography in representation')
        self.fields_ = {}
        for c in self.columns:
            s = frame[c]
            if pd.api.types.is_numeric_dtype(s):
                x = pd.to_numeric(s, errors='coerce').to_numpy(float)
                self.fields_[c] = dict(numeric=True, median=float(np.median(x[np.isfinite(x)])) if np.isfinite(x).any() else 0.)
            else:
                self.fields_[c] = dict(numeric=False, levels=sorted(s.fillna('__MISSING__').astype(str).unique()))
        x = self._matrix(frame)
        self.mean_ = x.mean(axis=0); self.scale_ = x.std(axis=0)
        self.support_ = self.scale_ > 1e-10
        self.scale_[~self.support_] = 1.
        z = ((x-self.mean_)/self.scale_)[:, self.support_]
        self.pca_ = None
        if z.shape[1]:
            k = min(self.components, z.shape[1], len(z)-1)
            self.pca_ = PCA(n_components=k, svd_solver='full').fit(z)
            p = self.pca_.transform(z)
            self.norm_ = max(float(np.sqrt(np.mean(np.sum(p*p, axis=1)))), 1e-12)
            self.explained_ = float(self.pca_.explained_variance_ratio_.sum())
        else:
            self.norm_ = 1.; self.explained_ = 0.
        return self

    def transform(self, frame):
        if self.pca_ is None:
            return np.zeros((len(frame), 1))
        x = self._matrix(frame)
        return self.pca_.transform(((x-self.mean_)/self.scale_)[:, self.support_])/self.norm_


def neighbor_weights(train, query, k):
    """Include all boundary ties: identical physical profiles are interchangeable."""
    d = cdist(query, train)
    n = min(k, len(train))
    threshold = np.partition(d, n-1, axis=1)[:, n-1]
    w = np.where(d <= threshold[:, None]+1e-12, 1/(d+.25), 0.)
    return w/w.sum(axis=1, keepdims=True), d


class ResidualCorrector:
    def __init__(self, kind, params):
        self.kind = kind; self.params = params

    def fit(self, x, residual):
        self.x_ = np.asarray(x); self.target_ = np.asarray(residual)-np.mean(residual)
        if self.kind == 'ridge':
            self.model_ = Ridge(alpha=len(x)*self.params['alpha'], fit_intercept=False, solver='svd').fit(x, self.target_)
        elif self.kind == 'groups':
            k = min(self.params['n_clusters'], len(np.unique(x, axis=0)))
            self.model_ = KMeans(n_clusters=max(1, k), n_init=5, max_iter=100, random_state=2026).fit(x)
            labels = self.model_.labels_
            self.counts_ = np.bincount(labels, minlength=k)
            sums = np.bincount(labels, weights=self.target_, minlength=k)
            self.values_ = sums/(self.counts_+self.params['shrinkage'])
        self.center_ = 0.
        self.center_ = float(self.predict(x).mean())
        return self

    def predict(self, x):
        if self.kind == 'ridge':
            p = self.model_.predict(x)
        elif self.kind == 'groups':
            p = self.values_[self.model_.predict(x)]
        else:
            w, _ = neighbor_weights(self.x_, x, self.params['k'])
            p = w@self.target_
        return p-self.center_


def select_candidate(target, baseline, deltas, parameters):
    """Only complete internal OOF labels are supplied to this selector."""
    rows = [dict(params=None, amplitude=0., mse=float(np.mean((baseline-target)**2)), candidate=-1)]
    for i, (delta, params) in enumerate(zip(deltas, parameters)):
        for amplitude in AMPLITUDES[1:]:
            rows.append(dict(params=params, amplitude=amplitude, mse=float(np.mean((baseline+amplitude*delta-target)**2)), candidate=i))
    best = min(rows, key=lambda r: (round(r['mse'], 12), r['amplitude'], r['candidate']))
    return best, rows
