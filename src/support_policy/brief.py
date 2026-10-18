"""Decision-brief wording derived only from the current estimates, verdict and analysis plan."""
import math

PRIMARY='unresolved_hours_7d'
NOT_ENOUGH_INFORMATION='Not enough information to decide'
METRIC_NAMES={'unresolved_hours_7d':'waiting time','repeat_contact_7d':'repeat contact',
              'escalated_7d':'escalation','refund_usd_7d':'refund cost'}
GUARDRAIL_KIND={'repeat_contact_7d':'rate','escalated_7d':'rate','refund_usd_7d':'usd'}
GUARDRAIL_SUBJECT={'repeat_contact_7d':'Repeat contact','escalated_7d':'Escalation',
                   'refund_usd_7d':'Refund spend per assigned customer'}


def known(row,*fields):
    return row is not None and all(isinstance(row.get(f),(int,float)) and math.isfinite(row[f]) for f in fields)


def change_word(effect,decimals=2):
    shown=round(effect,decimals)
    return 'increased' if shown>0 else 'decreased' if shown<0 else 'did not change'


def usd(value,decimals=2):
    return f"{'-' if value<0 else ''}${abs(value):,.{decimals}f}"


def _signed(value,suffix,decimals=2):
    return f'{value:+.{decimals}f}{suffix}'


UNITS={'hours':(1,lambda v:f'{v:.2f} hours',lambda v:f'{v:.2f} hours',lambda v,d=2:_signed(v,' hours',d)),
       'rate':(100,lambda v:f'{v:.2%}',lambda v:f'{v:.2f} percentage points',lambda v,d=2:_signed(v,' points',d)),
       'usd':(1,usd,usd,lambda v,d=2:('+' if v>=0 else '')+usd(v,d))}


def describe_change(subject,row,kind):
    scale,level,size,signed=UNITS[kind]
    effect=row['effect']*scale;word=change_word(effect)
    control,treatment=level(row['control_mean']),level(row['treatment_mean'])
    interval=f"95% CI {signed(row['ci_low']*scale)} to {signed(row['ci_high']*scale)}"
    if word=='did not change':
        text=f'{subject} did not change ({control} under the current policy, {treatment} under the simplified policy; {interval}).'
    else:
        noun='an increase' if word=='increased' else 'a decrease'
        text=f'{subject} {word} from {control} to {treatment}, {noun} of {size(abs(effect))} ({interval}).'
    if not (row['ci_low']>0 or row['ci_high']<0):
        text+=' The interval includes zero, so the direction of the change is not established.'
    return text


def headline(lookup):
    parts=[]
    for metric in [PRIMARY,'repeat_contact_7d']:
        row=lookup.get(metric);kind='hours' if metric==PRIMARY else 'rate'
        word=change_word(row['effect']*UNITS[kind][0]) if known(row,'effect') else 'not available'
        parts.append(f'{METRIC_NAMES[metric]} {word}')
    return ', '.join(parts).capitalize()


def _primary_paragraph(row,verdict,target):
    if not known(row,'effect','ci_low','ci_high','control_mean','treatment_mean'):
        return f'The waiting-time result is not available, so the {target:g}-hour reduction target cannot be assessed.'
    text=describe_change('Under the simplified process, seven-day capped time to first resolution',row,'hours')
    met='met' if verdict['primary_pass'] else 'not met'
    text+=(f' The rollout target requires the whole 95% interval to sit at or below -{target:g} hours,'
           f' a reduction of at least {target:g} hours; this target was {met}.')
    word=change_word(row['effect'])
    if word=='decreased':
        text+=' Customers waited less for a first resolution. This is elapsed customer waiting time, not a measurement of agent labour saved.'
    elif word=='increased':
        text+=' Customers waited longer for a first resolution under the simplified process.'
    return text


def _guardrail_sentence(metric,row,limit,verdict):
    subject=GUARDRAIL_SUBJECT.get(metric,metric);kind=GUARDRAIL_KIND.get(metric,'usd')
    if not known(row,'effect','ci_low','ci_high','control_mean','treatment_mean','guardrail_upper'):
        return f'{subject}: result not available, so this guardrail cannot be assessed.'
    scale,_,_,signed=UNITS[kind]
    text=describe_change(subject,row,kind)
    if metric in verdict['missing_results']:
        return text+' Outcome data are incomplete for some assigned customers, so this guardrail cannot be used for the decision.'
    outcome='failed' if metric in verdict['failed_guardrails'] else 'passed'
    return text+(f" Its simultaneous one-sided upper bound is {signed(row['guardrail_upper']*scale,3)}"
                 f' against a limit of {signed(limit*scale,3)}, so this guardrail {outcome}.')


def _next_steps(lookup,verdict,plan,health):
    recommendation=verdict['recommendation']
    if recommendation=='Scale with monitoring':
        return 'Expand in stages with continued monitoring and a rollback plan.'
    steps=['Keep the current process as the default.']
    if recommendation==NOT_ENOUGH_INFORMATION:
        names=', '.join(METRIC_NAMES.get(m,m) for m in verdict['missing_results'])
        steps.append(f'Do not roll out. Measure the missing or incomplete results ({names}) for every assigned customer, then apply the full rollout gate.')
        return ' '.join(steps)
    if recommendation=='Investigate experiment validity':
        failed=[label for key,label in [('srm_pass','allocation ratio'),('unique_customer_grain','one row per customer'),
                ('complete_followup','complete seven-day follow-up')] if not health.get(key)]
        steps.append(f"Investigate the failed experiment checks ({', '.join(failed)}) before interpreting any effect.")
        return ' '.join(steps)
    if not verdict['primary_pass']:
        steps.append(f"The waiting-time benefit did not reach the {plan['primary_required_reduction_hours']:g}-hour target with enough confidence.")
    if 'repeat_contact_7d' in verdict['failed_guardrails']:
        steps.append('Review repeat-contact reasons for duplicate-charge cases, where the simulation deliberately models a harder support problem.')
    for metric in verdict['failed_guardrails']:
        if metric!='repeat_contact_7d':
            steps.append(f'Investigate why the {METRIC_NAMES.get(metric,metric)} guardrail failed.')
    steps.append('Use the segment results to form a follow-up hypothesis, not to claim that differences between segments have been proved. '
                 'Test a revised explanation or evidence-check step in a fresh customer-randomised experiment before broad rollout.')
    return ' '.join(steps)


def _cost_paragraph(cost):
    if cost['incremental_cost'] is None:
        return 'The cost scenario cannot be calculated because refund or repeat-contact results are missing.'
    total=cost['incremental_cost']
    move='rise' if round(total)>0 else 'fall' if round(total)<0 else 'do not change'
    amount='' if move=='do not change' else f' by {usd(abs(total),0)}'
    return (f"For an assumed {cost['volume']:,} future cases, {cost['repeat_handling_minutes']:g} minutes per repeat contact and "
            f"{usd(cost['handling_cost_per_hour'],0)} per handling hour, refund and repeat-contact handling costs {move}{amount} "
            f"(95% sampling interval {usd(cost['ci_low'],0)} to {usd(cost['ci_high'],0)}). These assumptions are editable in the app. "
            'The scenario excludes unmeasured changes in initial handling effort, retention and satisfaction value; it is not total profit or ROI.')


def _health_paragraph(health):
    srm='at or above' if health['srm_pass'] else 'below'
    text=(f"There are {health['n_control']:,} control and {health['n_treatment']:,} treatment customers with a complete seven-day window. "
          'Randomisation is per customer, and analysis follows original assignment. '
          f"The sample-ratio mismatch p-value is {health['srm_p_value']:.3f}, {srm} the 0.001 investigation threshold. "
          f"The largest absolute baseline standardised difference is {health['max_absolute_smd']:.3f}. "
          'Each one-to-many table is aggregated before joins, so repeated events cannot multiply refunds.')
    if not health['unique_customer_grain']: text+=' The mart does not have exactly one row per customer.'
    if not health['complete_followup']: text+=' Some customers do not have a complete seven-day follow-up window.'
    return text


def brief_text(lookup,health,verdict,cost,plan):
    recommendation=verdict['recommendation']
    lead=f'**Recommendation: {recommendation}.** This is a simulated experiment, not an Uber deployment.'
    if recommendation==NOT_ENOUGH_INFORMATION:
        names=', '.join(METRIC_NAMES.get(m,m) for m in verdict['missing_results'])
        lead+=f' Results are missing or incomplete for: {names}. The rollout gate cannot be applied, so rollout is not recommended.'
    primary=lookup.get(PRIMARY)
    limits=plan['guardrail_limits']
    guardrails=' '.join(_guardrail_sentence(m,lookup.get(m),limits[m],verdict) for m in limits)
    tradeoff=''
    repeat=lookup.get('repeat_contact_7d')
    if known(primary,'effect') and known(repeat,'effect') and change_word(primary['effect'])=='decreased' and change_word(repeat['effect']*100)=='increased':
        tradeoff='The trade-off is repeat contact: a faster first resolution does not settle the full customer problem if more people return. '
    failed=', '.join(verdict['failed_guardrails']) or 'none'
    usable=health['srm_pass'] and health['unique_customer_grain'] and health['complete_followup']
    survey=lookup.get('survey_responded')
    survey_text=(f"Survey response was {survey['control_mean']:.1%} in control and {survey['treatment_mean']:.1%} in treatment. "
                 if known(survey,'control_mean','treatment_mean') else 'Survey response rates are not available. ')
    return f"""# Support policy decision brief

{lead}

{_primary_paragraph(primary,verdict,plan['primary_required_reduction_hours'])}

{guardrails}

{tradeoff}Guardrails that did not establish acceptable harm: {failed}. A failed guardrail can mean harm or insufficient precision; inspect its interval before deciding which.

## What I would do next

{_next_steps(lookup,verdict,plan,health)}

{_cost_paragraph(cost)}

## {'Why the comparison is usable' if usable else 'Why the comparison may not be usable'}

{_health_paragraph(health)}

## What this experiment cannot tell us

{survey_text}Satisfaction is measured among respondents and is not a causal estimate for all customers. Outcomes stop at seven days. We have not measured long-run retention, agent congestion, spillovers, actual process adherence or live costs. All patterns were generated from explicit assumptions, and the conclusions apply only to this simulation.
"""
