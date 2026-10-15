import numpy as np,pandas as pd
from src.family_6.diagnostics import ale,interaction

class KnownResponse:
    def __init__(self,product=False):self.product=product
    def predict(self,X):return X.a.to_numpy()*X.b.to_numpy() if self.product else 2*X.a.to_numpy()+3*X.b.to_numpy()

def test_ale_centering_and_support_gaps():
    X=pd.DataFrame({'a':np.linspace(0,1,60),'b':np.tile(np.arange(10),6)})
    rows=ale(KnownResponse(),X,'a');assert len(rows)==6
    np.testing.assert_allclose([r['local_difference'] for r in rows],[2*(r['upper']-r['lower']) for r in rows],atol=1e-12)
    np.testing.assert_allclose(np.average([r['ALE'] for r in rows],weights=[r['n'] for r in rows]),0,atol=1e-12)
    rows=ale(KnownResponse(),X.iloc[:12],'a');assert all(np.isnan(r['ALE']) for r in rows)

def test_local_mixed_difference_and_cell_support():
    X=pd.DataFrame([(a,b) for a in np.arange(9.) for b in np.arange(9.)],columns=['a','b'])
    rows=interaction(KnownResponse(),X,'a','b');assert all(r['supported'] for r in rows)
    np.testing.assert_allclose([r['mixed_local_difference'] for r in rows],0,atol=1e-12)
    rows=interaction(KnownResponse(True),X,'a','b')
    np.testing.assert_allclose([r['mixed_local_difference'] for r in rows],[(r['first_high']-r['first_low'])*(r['second_high']-r['second_low']) for r in rows],atol=1e-12)
