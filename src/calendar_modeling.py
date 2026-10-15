"""Conservative nested Ridge models for frozen agronomic representations."""
import numpy as np
from sklearn.linear_model import Ridge

class CalendarRidge:
    def __init__(self,columns,history,alpha,gamma=1.,indicators=False):
        self.columns=list(columns);self.history=list(history);self.alpha=alpha;self.gamma=gamma;self.indicators=indicators
    def fit(self,frame,y):
        x=frame[self.columns].to_numpy(dtype=float)
        self.medians_=np.array([np.median(v[np.isfinite(v)]) if np.isfinite(v).any() else 0. for v in x.T])
        self.indicator_positions_=[i for i,c in enumerate(self.columns) if c.startswith(('HIST_MEAN_','DELTA_'))] if self.indicators else []
        a=self._imputed(x);self.mean_=a.mean(axis=0);self.scale_=a.std(axis=0);self.scale_[self.scale_<1e-12]=1.
        self.weights_=np.array([self.gamma if c in self.history else 1. for c in self.columns]+[self.gamma]*len(self.indicator_positions_))
        z=(a-self.mean_)/self.scale_*self.weights_
        self.model_=Ridge(alpha=self.alpha*len(y),solver='svd').fit(z,np.asarray(y))
        sv=np.linalg.svd(z,compute_uv=False);self.effective_df_=float(1+np.sum(sv**2/(sv**2+self.alpha*len(y))))
        self.feature_names_=self.columns+[self.columns[i]+'__missing' for i in self.indicator_positions_]
        return self
    def _imputed(self,x):
        missing=~np.isfinite(x)
        a=np.where(missing,self.medians_,x)
        return np.column_stack([a,missing[:,self.indicator_positions_].astype(float)]) if self.indicator_positions_ else a
    def predict(self,frame):
        a=self._imputed(frame[self.columns].to_numpy(dtype=float))
        return self.model_.predict((a-self.mean_)/self.scale_*self.weights_)
