import numpy as np
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm

def test_identical_predictions_have_zero_paired_difference_and_p_one():
    y=np.arange(8.);pred=np.array([y+.2,y-.1]);groups=np.repeat(np.arange(4),2)
    w,g=cluster_weights(groups,100);a=sampled_metrics(y,pred,w);b=sampled_metrics(y,pred,w)
    for key in a:np.testing.assert_array_equal(a[key]-b[key],np.zeros(100))
    assert g==4 and paired_signflip(np.zeros(8),groups)['p_mse_signflip']==1

def test_five_cluster_two_sided_test_cannot_claim_p_below_05():
    result=paired_signflip(np.ones(10),np.repeat(np.arange(5),2))
    assert result['exact_sign_enumeration'] and result['p_mse_signflip']==.0625

def test_repeats_are_metrics_then_averaged_not_prediction_average():
    y=np.array([0.,1.]);p=np.array([[1.,2.],[-1.,0.]])
    result=sampled_metrics(y,p,np.ones((1,2)))
    assert result['rmse'][0]==1 and result['mae'][0]==1

def test_holm_is_monotone_in_order_and_never_less_than_raw():
    p=np.array([.04,.001,.03]);a=holm(p)
    np.testing.assert_allclose(a,[.06,.003,.06]);assert (a>=p).all()
