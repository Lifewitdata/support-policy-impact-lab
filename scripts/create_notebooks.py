"""Create readable notebook sources. Execution is a separate, explicit step."""
from pathlib import Path
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]
bootstrap="""from pathlib import Path
import sys, json
import numpy as np
import polars as pl
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
ROOT = Path.cwd()
if not (ROOT / 'config').exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / 'src'))
from support_policy.common import config
mart = pl.read_parquet(ROOT / 'data/marts/experiment_mart.parquet')
plt.rcParams.update({'figure.figsize': (9, 4), 'axes.spines.top': False, 'axes.spines.right': False})
pl.Config.set_tbl_rows(20)
print(f'{mart.height:,} customers; synthetic data only')
"""
def save(name,cells):
 nb=nbf.v4.new_notebook()
 nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}}
 nb.cells=[nbf.v4.new_markdown_cell(txt) if kind=='md' else nbf.v4.new_code_cell(txt) for kind,txt in cells]
 nbf.write(nb,ROOT/'notebooks'/name)

save('01_data_quality_and_eda.ipynb',[
('md',"""# 1. What is in the experiment, and can we use it?

The goal is to understand the source data before interpreting treatment effects. Every record is synthetic. We inspect missingness, case mix, skew, repeat contacts and survey coverage. The experiment plan is stored separately; this EDA does not change its decision thresholds."""),
('code',bootstrap),
('md','## Source inventory and analytical grain\nSix source tables feed one customer-level mart. Event rows must never become the experiment sample size.'),
('code',"""inventory=[]
for path in sorted((ROOT/'data/raw').glob('*.parquet')):
    f=pl.read_parquet(path)
    inventory.append({'table':path.stem,'rows':f.height,'columns':f.width})
display(pl.DataFrame(inventory))
assert mart['customer_id'].n_unique()==mart.height
print('One row per customer:', mart.height)
"""),
('md','## Required fields and missing outcomes\nAn unresolved case contributes 168 hours. Missing satisfaction stays missing. Replacing it with zero would mix nonresponse with a bad rating.'),
('code',"""display(mart.null_count().unpivot(variable_name='field',value_name='nulls').filter(pl.col('nulls')>0))
validation=json.loads((ROOT/'outputs/validation_report.json').read_text())
print('Source checks passed:',sum(validation['checks'].values()),'of',len(validation['checks']))
assert validation['passed']
display(mart.group_by('policy').agg(pl.len().alias('customers'),
    (1-pl.col('resolved_7d').mean()).alias('unresolved_rate'),
    pl.col('survey_responded').mean().alias('response_rate')).sort('policy'))
"""),
('md','## Case mix\nIssue category is known before assignment. The simulation makes duplicate-charge cases more complex; that is an input assumption, not a discovered fact about real customers.'),
('code',"""mix=mart.group_by('issue_type','policy').agg(pl.len().alias('customers'),
    pl.col('prior_contacts_30d').mean().alias('prior_contacts_mean'),
    pl.col('tenure_days').median().alias('median_tenure_days')).sort('issue_type','policy')
display(mix)
region=mart.group_by('region','policy').agg(pl.len().alias('customers')).sort('region','policy')
display(region)
"""),
('md','## Enrolment over time\nLarge allocation changes by day would prompt a logging or randomisation investigation. The overall allocation check appears in Notebook 2.'),
('code',"""daily=pl.read_parquet(ROOT/'data/marts/daily_enrolment.parquet')
fig,ax=plt.subplots()
for label in sorted(daily['policy'].unique().to_list()):
    d=daily.filter(pl.col('policy')==label).sort('assignment_date')
    ax.plot(d['assignment_date'].to_list(),d['customers'].to_list(),label=label)
ax.set(ylabel='Assigned customers',title='Daily enrolment');ax.legend();fig.autofmt_xdate();plt.show()
"""),
('md','## Waiting-time distribution\nThe mean alone hides the right tail and the mass at the cap. The primary endpoint includes that cap rather than excluding unresolved customers.'),
('code',"""display(mart.group_by('policy').agg(
    pl.col('unresolved_hours_7d').mean().alias('mean_hours'),
    pl.col('unresolved_hours_7d').median().alias('median_hours'),
    pl.col('unresolved_hours_7d').quantile(.90).alias('p90_hours'),
    pl.col('unresolved_hours_7d').quantile(.95).alias('p95_hours')))
fig,ax=plt.subplots()
for label in sorted(mart['policy'].unique().to_list()):
    x=mart.filter(pl.col('policy')==label)['unresolved_hours_7d'].to_numpy()
    ax.hist(x,bins=35,alpha=.5,density=True,label=label)
ax.set(xlabel='Hours to first resolution, capped at 168',ylabel='Density');ax.legend();plt.show()
"""),
('md','## Contacts outside the follow-up window\nThe raw source deliberately includes late contacts. They should not enter seven-day outcomes.'),
('code',"""cases=pl.read_parquet(ROOT/'data/raw/support_cases.parquet')
linked=cases.join(mart.select('customer_id','assigned_at','window_end'),on='customer_id').filter(~pl.col('is_index'))
display(linked.select(pl.len().alias('all_repeat_cases'),
    (pl.col('opened_at')<=pl.col('window_end')).sum().alias('within_seven_days'),
    (pl.col('opened_at')>pl.col('window_end')).sum().alias('after_seven_days')))
assert mart['repeat_count_7d'].sum()==linked.filter((pl.col('opened_at')>pl.col('assigned_at'))&(pl.col('opened_at')<=pl.col('window_end'))).height
"""),
('md','## Refund distribution and denominator\nSpend is calculated per assigned customer, including zero-refund cases. Comparing only paid customers would change the population after treatment.'),
('code',"""display(mart.group_by('policy').agg(pl.col('refund_usd_7d').mean().alias('mean_per_assigned_customer'),
    (pl.col('refund_usd_7d')==0).mean().alias('zero_refund_share'),
    pl.col('refund_usd_7d').quantile(.99).alias('p99_refund_usd')))
"""),
('md','## Survey selection\nCheck who replied before interpreting the rating. A policy can change both the experience and the chance that a customer responds.'),
('code',"""display(mart.group_by('policy','repeat_contact_7d').agg(pl.len().alias('customers'),
    pl.col('survey_responded').mean().alias('response_rate'),pl.col('csat').mean().alias('respondent_score')).sort('policy','repeat_contact_7d'))
"""),
('md','## What this EDA establishes\nThe mart has the right grain, complete follow-up and explicit outcome denominators. The wait distribution is skewed and satisfaction is incomplete. Those observations explain the capped primary endpoint and separate response-rate reporting. Causal estimates and uncertainty come next; descriptive group differences alone are not the rollout decision.')
])
save('02_power_and_experiment_checks.ipynb',[
('md','# 2. Was the comparison planned and allocated sensibly?\n\nThis notebook reads the documented plan, reproduces its sample-size calculations and checks allocation and baseline balance.'),
('code',bootstrap),
('md','## Decision thresholds\nThese are illustrative business choices fixed for this exercise, not Uber targets. Changing them after seeing results would weaken the decision process.'),
('code',"display(config('analysis_plan'))"),
('md','## Sample-size planning\nThe primary calculation tests a 2-hour change against zero. Proving at least a 2-hour improvement is a stronger requirement and needs additional power planning.'),
('code',"""from support_policy.power_analysis import calculate_power
power=calculate_power()
display(power)
"""),
('md','## Allocation check\nIndependent 50/50 randomisation does not require exactly equal arm sizes. The sample-ratio mismatch test flags an unexpected imbalance, not treatment success.'),
('code',"""from support_policy.experiment_checks import check_experiment
health=check_experiment(mart)
display(health)
assert health['unique_customer_grain'] and health['complete_followup']
"""),
('md','## Baseline balance\nStandardised differences describe comparability. They are not used to drop customers or search for favourable subgroups.'),
('code',"""balance=pl.read_csv(ROOT/'outputs/tables/baseline_balance.csv')
display(balance)
fig,ax=plt.subplots(figsize=(9,5))
ax.scatter(balance['smd'].to_list(),balance['feature'].to_list(),color='#087f8c')
ax.axvline(0,color='grey');ax.axvline(.1,ls='--',color='grey');ax.axvline(-.1,ls='--',color='grey')
ax.set(xlabel='Standardised difference',title='Baseline characteristics');plt.tight_layout();plt.show()
"""),
('md','## Follow-up maturity\nThe inclusion rule depends on assignment time and the data cutoff, never on whether a case resolved.'),
('code',"""from datetime import datetime
end=datetime.fromisoformat(config('simulation')['observation_end'])
print('Observation cutoff:',end,'UTC')
print('Latest window end:',mart['window_end'].max())
assert mart['window_end'].max()<=end
assert ((mart['window_end']-mart['assigned_at']).dt.total_hours()==168).all()
"""),
('md','## Interpretation\nPassing these checks supports the mechanics of the comparison. It does not prove that logging is perfect in a real system, or remove spillover and nonresponse risks. Those are assumptions to investigate before a live launch.')
])
save('03_treatment_effects.ipynb',[
('md','# 3. Did the simplified process help, and at what cost?\n\nWe compare customers by original assignment. Negative changes improve the capped waiting-time endpoint. Rate differences are shown in percentage points; costs are USD per assigned customer.'),
('code',bootstrap),
('md','## Unadjusted intention-to-treat estimates\nEach customer contributes once. We use Welch intervals for mean differences; binary means are risks. Survey ratings remain a respondent-only descriptive exception.'),
('code',"""from support_policy.estimate_effects import estimate
effects=estimate(mart)
display(effects.select('metric','n_control','n_treatment','control_mean','treatment_mean','effect','ci_low','ci_high','p_value'))
"""),
('md','## Explain the primary outcome in ordinary language'),
('code',"""r=effects.filter(pl.col('metric')=='unresolved_hours_7d').row(0,named=True)
print(f"The new policy changed capped time to first resolution by {r['effect']:.2f} hours.")
print(f"The 95% interval is {r['ci_low']:.2f} to {r['ci_high']:.2f} hours.")
print('This is customer waiting time. It is not measured agent labour saved.')
"""),
('md','## Operational guardrails\nThe decision uses simultaneous one-sided upper bounds. The point estimate alone cannot establish that harm is acceptably small.'),
('code',"""guards=effects.filter(pl.col('guardrail_limit').is_not_null())
display(guards.select('metric','effect','ci_low','ci_high','guardrail_upper','guardrail_limit','guardrail_pass'))
repeat=effects.filter(pl.col('metric')=='repeat_contact_7d').row(0,named=True)
print(f"Repeat contacts changed by {100*repeat['effect']:.2f} percentage points.")
print(f"Simultaneous upper bound: {100*repeat['guardrail_upper']:.2f} points; allowed limit: 1.00 point.")
"""),
('md','## Baseline-adjusted sensitivity\nThis model adjusts only for pre-assignment attributes. HC3 uncertainty allows heteroskedasticity. The unadjusted result remains the planned primary analysis.'),
('code',"display(pl.read_csv(ROOT/'outputs/tables/adjusted_primary.csv'))"),
('md','## Satisfaction and the missing denominator\nA difference among responders does not estimate the effect for all assigned customers when treatment changes response.'),
('code',"display(effects.filter(pl.col('metric').is_in(['csat','survey_responded'])).select('metric','n_control','n_treatment','control_mean','treatment_mean','effect','ci_low','ci_high'))"),
('md','## Check against the simulation design, after analysis\nOnly this diagnostic accesses counterfactual aggregate truth. It was not used to select models or make the policy decision. One interval can miss truth by chance.'),
('code',"""display(pl.read_csv(ROOT/'outputs/tables/simulation_recovery.csv'))
display(json.loads((ROOT/'outputs/estimator_calibration.json').read_text()))
"""),
('md','## Read the trade-off, not only the p-value\nA large sample can make small effects statistically clear. The rollout gate therefore combines a minimum practical benefit with predeclared harm limits. Notebook 4 applies that gate and examines follow-up questions.')
])
save('04_segments_and_rollout_decision.ipynb',[
('md','# 4. What would I recommend to the support lead?\n\nFirst apply the planned decision rule. Then use segment results to identify what to investigate, without turning exploratory results into a new success criterion.'),
('code',bootstrap),
('md','## Apply the original gate'),
('code',"""from support_policy.rollout_scenarios import decision,scenario
health=json.loads((ROOT/'outputs/experiment_checks.json').read_text())
effects=pl.read_csv(ROOT/'outputs/tables/treatment_effects.csv')
verdict=decision(effects,health)
display(verdict)
"""),
('md','## Predefined exploratory segments\nThere are 16 segment/outcome tests. Q-values adjust their p-values together; the displayed intervals are still pointwise. These are not interaction tests.'),
('code',"""segments=pl.read_csv(ROOT/'outputs/tables/segment_effects.csv')
display(segments.select('segment','value','metric','n_control','n_treatment','effect','ci_low','ci_high','q_value_bh'))
"""),
('md','## Look closely at issue type\nThe simulation assigns different complexities to issue types. This view can suggest a follow-up experiment; it cannot establish an optimal targeted rollout.'),
('code',"""d=segments.filter((pl.col('segment')=='issue_type')&(pl.col('metric')=='repeat_contact_7d')).sort('value')
fig,ax=plt.subplots()
x=d['effect'].to_numpy()*100
ax.errorbar(x,d['value'].to_list(),xerr=np.array([(d['effect']-d['ci_low']).to_numpy()*100,(d['ci_high']-d['effect']).to_numpy()*100]),fmt='o',capsize=5,color='#087f8c')
ax.axvline(0,color='grey',ls='--');ax.set(xlabel='Repeat-contact change (percentage points), 95% CI');plt.tight_layout();plt.show()
"""),
('md','## Cost assumptions, not measured savings\nCombine refund spend and assumed repeat-contact handling costs per customer. Do not convert elapsed waiting time into agent salary savings. The confidence interval captures sampling uncertainty, not uncertainty in the chosen assumptions.'),
('code',"""scenarios=[]
for minutes in [6,12,20]:
    for hourly in [12,18,30]:
        result=scenario(mart,100000,minutes,hourly)
        scenarios.append({k:v for k,v in result.items() if k!='assumption'})
display(pl.DataFrame(scenarios))
"""),
('md','## Decision brief\nThe brief below is generated from the current run. It reports the result, the operational trade-off, the next action and what remains unknown.'),
('code',"display(Markdown((ROOT/'outputs/decision_brief.md').read_text()))"),
('md','## Handoff\nFor a real follow-up, agree the guardrail limits with support and finance before launch, inspect repeat-contact reasons, confirm logging and assignment, and test the revised process in new data. Keep the original experiment result intact rather than changing thresholds to make it pass.')
])
print('Created four notebooks')
