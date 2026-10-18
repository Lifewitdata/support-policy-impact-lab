"""Seeded potential-outcome simulation; truth is kept out of the analysis mart."""
from datetime import datetime, timedelta
import numpy as np
import polars as pl
from .common import ROOT, config, write_json


def generate():
    cfg = config('simulation')
    plan = config('analysis_plan')
    rng = np.random.default_rng(cfg['seed'])
    n = cfg['n_customers']
    ids = np.arange(1, n + 1)
    issue = rng.choice(['Fare adjustment', 'Duplicate charge', 'Cancellation refund'], n, p=[.45,.30,.25])
    region = rng.choice(['Region A','Region B','Region C'], n, p=[.50,.30,.20])
    tenure = rng.integers(1, 1500, n)
    prior = rng.poisson(.7, n)
    treatment = rng.binomial(1, .5, n)
    start = datetime.fromisoformat(cfg['start_date'])
    offsets = rng.integers(0, cfg['enrolment_days'] * 86400, n)
    times = [start + timedelta(seconds=int(s)) for s in offsets]
    complexity = np.where(issue == 'Duplicate charge', 1.45, np.where(issue == 'Cancellation refund', .8, 1.0))
    base_hours = rng.lognormal(np.log(24), .9, n) * complexity
    # Some customers remain unresolved beyond the complete seven-day window.
    base_hours = np.where(rng.random(n) < .055, base_hours + 200, base_hours)
    effect_multiplier = np.where(issue == 'Duplicate charge', .90, cfg['treatment_resolution_multiplier'])
    alt_hours = base_hours * effect_multiplier
    observed_hours = np.where(treatment == 1, alt_hours, base_hours)
    cutoff = plan['followup_hours']
    resolution = [t + timedelta(hours=float(h)) if h <= cutoff else None for t,h in zip(times, observed_hours)]
    prob_repeat = np.clip(.08 + .035*(issue=='Duplicate charge') + .012*prior, 0, .6)
    repeat_u = rng.random(n)
    rep0 = repeat_u < prob_repeat
    rep1 = repeat_u < (prob_repeat + cfg['treatment_repeat_increase'] + .018*(issue=='Duplicate charge'))
    repeat = np.where(treatment == 1, rep1, rep0)
    late = rng.random(n) < .03
    esc_u = rng.random(n)
    esc0 = esc_u < (.045 + .025*(issue=='Duplicate charge'))
    esc1 = esc_u < (.045 + .025*(issue=='Duplicate charge') + .001)
    escalation = np.where(treatment == 1, esc1, esc0)
    refund_base = np.where(rng.random(n)<.62, rng.gamma(2, 3, n), 0)
    refund_alt = refund_base + np.where(refund_base>0, cfg['treatment_refund_increase_usd'], 0)
    refunds = np.round(np.where(treatment==1, refund_alt, refund_base), 2)
    write_json(ROOT/'data/processed/simulation_truth.json', {
        'warning': 'Simulation verification only. Never used to fit models or make rollout decisions.',
        'unresolved_hours_7d': float(np.mean(np.minimum(alt_hours,cutoff)-np.minimum(base_hours,cutoff))),
        'repeat_contact_7d': float(np.mean(rep1.astype(float)-rep0.astype(float))),
        'escalated_7d': float(np.mean(esc1.astype(float)-esc0.astype(float))),
        'refund_usd_7d': float(np.mean(np.round(refund_alt,2)-np.round(refund_base,2))),
    })
    frames = {}
    frames['customers'] = pl.DataFrame({'customer_id':ids, 'region':region, 'issue_type':issue,
        'tenure_days':tenure, 'prior_contacts_30d':prior}).with_columns(
        pl.when(pl.col('tenure_days')<180).then(pl.lit('Under 6 months')).otherwise(pl.lit('6 months or more')).alias('tenure_group'))
    frames['assignments'] = pl.DataFrame({'customer_id':ids,'treatment':treatment,'assigned_at':times,'index_case_id':ids})
    case_rows = [{'case_id':int(i),'customer_id':int(i),'opened_at':t,'resolved_at':r,'is_index':True} for i,t,r in zip(ids,times,resolution)]
    next_id = n+1
    for mask,lo,hi in [(repeat, .25, 6.99), (late, 7.01, 9.0)]:
        for idx in np.flatnonzero(mask):
            opened = times[idx]+timedelta(days=float(rng.uniform(lo,hi)))
            case_rows.append({'case_id':next_id,'customer_id':int(ids[idx]),'opened_at':opened,
                              'resolved_at':opened+timedelta(hours=2),'is_index':False})
            next_id += 1
    frames['support_cases'] = pl.DataFrame(case_rows)
    events = []
    for c in case_rows:
        events.append({'case_id':c['case_id'],'event_at':c['opened_at'],'event_type':'opened'})
        if c['resolved_at'] is not None:
            events.append({'case_id':c['case_id'],'event_at':c['resolved_at'],'event_type':'resolved'})
    for idx in np.flatnonzero(escalation):
        # Escalation precedes resolution for the index case.
        h = min(float(observed_hours[idx])*.4, 72)
        events.append({'case_id':int(ids[idx]),'event_at':times[idx]+timedelta(hours=h),'event_type':'escalated'})
    frames['case_events'] = pl.DataFrame(events).with_row_index('event_id', offset=1)
    paid = np.flatnonzero(refunds>0)
    frames['refund_transactions'] = pl.DataFrame({'refund_id':np.arange(1,len(paid)+1),
        'case_id':ids[paid], 'paid_at':[times[i]+timedelta(hours=12) for i in paid],
        'amount_usd':refunds[paid]})
    response_prob = .50 - .09*repeat - .04*treatment
    responded = np.flatnonzero(rng.random(n)<response_prob)
    ratings = np.clip(np.rint(rng.normal(4.1 - .65*repeat[responded] - .10*treatment[responded], .8)),1,5).astype(int)
    frames['satisfaction_responses'] = pl.DataFrame({'response_id':np.arange(1,len(responded)+1),
        'case_id':ids[responded], 'responded_at':[times[i]+timedelta(days=6.5) for i in responded], 'score':ratings})
    for name, frame in frames.items():
        frame.write_parquet(ROOT/'data/raw'/f'{name}.parquet')
    return {name:f.height for name,f in frames.items()}
