import numpy as np
import polars as pl
import pytest
from scipy.stats import ttest_ind
from support_policy.estimate_effects import difference
from support_policy.rollout_scenarios import scenario

def test_difference_matches_welch_reference():
    c=np.array([1,3,5,7,9.]);t=np.array([0,1,2,4,6.])
    result=difference(c,t)
    assert result['effect']==pytest.approx(t.mean()-c.mean())
    assert result['p_value']==pytest.approx(ttest_ind(t,c,equal_var=False).pvalue)
    assert result['ci_low']<result['effect']<result['ci_high']

def test_swap_arms_reverses_effect_and_interval():
    c=np.arange(30);t=np.arange(20)+3
    a,b=difference(c,t),difference(t,c)
    assert a['effect']==pytest.approx(-b['effect'])
    assert a['ci_low']==pytest.approx(-b['ci_high'])

def test_constant_outcomes_have_zero_width_interval():
    r=difference([1,1,1],[2,2,2]);assert r['ci_low']==r['ci_high']==1

def test_sparse_samples_raise():
    with pytest.raises(ValueError):difference([1],[2,3])

def test_scenario_uses_contacts_and_refunds_not_waiting_time():
    m=pl.DataFrame({'treatment':[0,0,1,1],'refund_usd_7d':[1.,1.,2.,2.],
                    'repeat_count_7d':[0,0,1,1],'unresolved_hours_7d':[100,100,1,1]})
    result=scenario(m,100,30,10)
    assert result['incremental_cost']==600 # 100 * ($1 refund + $5 repeat handling)
