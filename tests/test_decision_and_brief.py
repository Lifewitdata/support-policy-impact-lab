import polars as pl
import pytest
from support_policy.brief import brief_text, NOT_ENOUGH_INFORMATION
from support_policy.rollout_scenarios import decide, scenario

PLAN={'primary_required_reduction_hours':2.0,'alpha':0.05,
      'guardrail_limits':{'repeat_contact_7d':0.01,'escalated_7d':0.005,'refund_usd_7d':0.50}}
HEALTH={'n_control':100,'n_treatment':100,'srm_p_value':0.5,'srm_pass':True,'max_absolute_smd':0.01,
        'unique_customer_grain':True,'complete_followup':True}
COST={'volume':100000,'repeat_handling_minutes':12,'handling_cost_per_hour':18,
      'incremental_cost':1000.0,'ci_low':500.0,'ci_high':1500.0}


def row(metric,control,effect,half_width,upper=None):
    return {'metric':metric,'n_control':100,'n_treatment':100,'control_mean':control,'treatment_mean':control+effect,
            'effect':effect,'ci_low':effect-half_width,'ci_high':effect+half_width,'guardrail_upper':upper}


def passing_rows(primary_effect=-5.0):
    return [row('unresolved_hours_7d',44.0,primary_effect,0.5),
            row('repeat_contact_7d',0.10,0.002,0.001,0.004),
            row('escalated_7d',0.05,-0.001,0.001,0.001),
            row('refund_usd_7d',3.5,0.10,0.05,0.20),
            row('survey_responded',0.5,-0.01,0.005)]


def frame(rows):
    return pl.DataFrame(rows)


def brief(rows,plan=PLAN,cost=COST):
    effects=frame(rows);verdict=decide(effects,HEALTH,plan)
    return verdict,brief_text({r['metric']:r for r in rows},HEALTH,verdict,cost,plan)


def test_all_results_present_and_passing_scales():
    assert decide(frame(passing_rows()),HEALTH,PLAN)['recommendation']=='Scale with monitoring'


@pytest.mark.parametrize('metric',['repeat_contact_7d','escalated_7d','refund_usd_7d','unresolved_hours_7d'])
@pytest.mark.parametrize('how',['row_absent','value_missing','incomplete_sample'])
def test_missing_result_never_recommends_rollout(metric,how):
    rows=passing_rows()
    if how=='row_absent':
        rows=[r for r in rows if r['metric']!=metric]
    else:
        target=next(r for r in rows if r['metric']==metric)
        if how=='value_missing':
            target.update(effect=None,ci_low=None,ci_high=None,guardrail_upper=None)
        else:
            target['n_treatment']=60
    verdict,text=brief(rows)
    assert verdict['recommendation']==NOT_ENOUGH_INFORMATION
    assert metric in verdict['missing_results']
    assert f'**Recommendation: {NOT_ENOUGH_INFORMATION}.**' in text
    assert 'Expand in stages' not in text


def test_missing_result_survives_csv_round_trip(tmp_path):
    rows=passing_rows()
    next(r for r in rows if r['metric']=='refund_usd_7d').update(effect=None,ci_low=None,ci_high=None,guardrail_upper=None)
    path=tmp_path/'effects.csv';frame(rows).write_csv(path)
    assert decide(pl.read_csv(path),HEALTH,PLAN)['recommendation']==NOT_ENOUGH_INFORMATION


def test_brief_says_increased_when_waiting_time_rises():
    verdict,text=brief(passing_rows(primary_effect=3.0))
    assert 'time to first resolution increased from 44.00 hours to 47.00 hours, an increase of 3.00 hours' in text
    assert 'decreased from 44.00' not in text and 'reduced' not in text
    assert 'waited longer' in text and 'target was not met' in text
    assert verdict['recommendation']=='Revise and retest'


def test_brief_says_decreased_when_waiting_time_falls():
    _,text=brief(passing_rows(primary_effect=-5.0))
    assert 'time to first resolution decreased from 44.00 hours to 39.00 hours, a decrease of 5.00 hours' in text
    assert 'target was met' in text


def test_brief_guardrail_wording_follows_sign():
    _,text=brief(passing_rows())
    assert 'Repeat contact increased from 10.00% to 10.20%' in text
    assert 'Escalation decreased from 5.00% to 4.90%' in text
    assert 'Refund spend per assigned customer increased from $3.50 to $3.60' in text


def test_changed_targets_flow_into_decision_and_brief():
    plan={**PLAN,'primary_required_reduction_hours':6.0,
          'guardrail_limits':{'repeat_contact_7d':0.003,'escalated_7d':0.005,'refund_usd_7d':0.50}}
    verdict,text=brief(passing_rows(primary_effect=-5.0),plan=plan)
    assert verdict['primary_pass'] is False and verdict['failed_guardrails']==['repeat_contact_7d']
    assert 'at or below -6 hours' in text and 'at least 6 hours' in text and 'target was not met' in text
    assert 'against a limit of +0.300 points, so this guardrail failed' in text
    assert '-6 hours' in verdict['rule'] and 'repeat_contact_7d <= 0.003' in verdict['rule']


def test_cost_scenario_wording_and_assumptions_follow_inputs():
    _,text=brief(passing_rows(),cost={**COST,'volume':250000,'repeat_handling_minutes':20,'handling_cost_per_hour':30,
                                      'incremental_cost':-2000.0,'ci_low':-3000.0,'ci_high':-1000.0})
    assert '250,000 future cases, 20 minutes per repeat contact and $30 per handling hour' in text
    assert 'costs fall by $2,000 (95% sampling interval -$3,000 to -$1,000)' in text


def test_missing_cost_inputs_are_reported_not_crashed():
    m=pl.DataFrame({'treatment':[0,0,1,1],'repeat_count_7d':[0,0,1,1]})
    cost=scenario(m,100,30,10)
    assert cost['incremental_cost'] is None
    _,text=brief(passing_rows(),cost=cost)
    assert 'cost scenario cannot be calculated' in text
