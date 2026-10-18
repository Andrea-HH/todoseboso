import numpy as np
from src.four_expert_combinations import constant_weight,ConditionalBlend,ConvexThree,fit_combinations,predict_combinations

def test_constant_endpoints_and_repeated_experts():
    a=np.arange(20.)/20;b=a+1
    assert constant_weight(a,a,b)==0 and constant_weight(b,a,b)==1 and constant_weight(a,a,a)==0

def test_conditional_convexity_and_identical_predictions():
    rng=np.random.default_rng(5);z=rng.normal(size=(40,4));z[0,0]=np.nan;a=rng.normal(size=40);b=a+rng.normal(size=40);y=.3*a+.7*b
    m=ConditionalBlend().fit(z,y,a,b);pred=m.predict(z,a,b);assert np.all(pred>=np.minimum(a,b)-1e-12) and np.all(pred<=np.maximum(a,b)+1e-12)
    same=ConditionalBlend().fit(z,y,a,a);np.testing.assert_allclose(same.predict(z,a,a),a)

def test_three_weights_simplex_and_prediction_bounds():
    rng=np.random.default_rng(8);p=rng.normal(size=(40,3));m=ConvexThree().fit(p,p[:,1]);assert abs(m.weights.sum()-1)<1e-12 and np.all(m.weights>=0);out=m.predict(p);assert np.all(out>=p.min(axis=1)-1e-12) and np.all(out<=p.max(axis=1)+1e-12)

def test_six_mixtures_are_bounded():
    rng=np.random.default_rng(7);p=rng.normal(size=(40,4));z={n:rng.normal(size=(40,4)) for n in ['B5','B6']};models=fit_combinations(p,z,p[:,3]);out,weights=predict_combinations(models,p,z);assert len(out)==6
    assert all(np.all((v>=0)&(v<=1)) for v in weights.values())
    for name,left,right in [('B1',0,3),('B2',0,2),('B3',3,1),('B5',0,3),('B6',3,1)]:assert np.all(out[name]>=np.minimum(p[:,left],p[:,right])-1e-12) and np.all(out[name]<=np.maximum(p[:,left],p[:,right])+1e-12)
