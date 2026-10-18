import numpy as np
import polars as pl
from .common import ROOT, config, write_json
from .estimate_effects import difference
from .brief import PRIMARY, NOT_ENOUGH_INFORMATION, known


def _complete(row,health,field):
    # A result over only some assigned customers is not an intention-to-treat estimate.
    return known(row,field) and row.get('n_control')==health['n_control'] and row.get('n_treatment')==health['n_treatment']


def decide(effects,health,plan):
    rows={r['metric']:r for r in effects.iter_rows(named=True)}
    target=plan['primary_required_reduction_hours'];limits=plan['guardrail_limits']
    missing=[] if _complete(rows.get(PRIMARY),health,'ci_high') else [PRIMARY]
    missing+=[m for m in limits if not _complete(rows.get(m),health,'guardrail_upper')]
    benefit=rows[PRIMARY]['ci_high']<=-target if PRIMARY not in missing else None
    failed=[m for m in limits if m not in missing and rows[m]['guardrail_upper']>limits[m]]
    valid=health['srm_pass'] and health['unique_customer_grain'] and health['complete_followup']
    if missing: verdict=NOT_ENOUGH_INFORMATION
    elif not valid: verdict='Investigate experiment validity'
    elif benefit and not failed: verdict='Scale with monitoring'
    else: verdict='Revise and retest'
    bounds=', '.join(f'{m} <= {v:g}' for m,v in limits.items())
    return {'recommendation':verdict,'primary_pass':benefit,'failed_guardrails':failed,'missing_results':missing,
            'primary_target_hours':target,'guardrail_limits':limits,
            'rule':f'Primary 95% CI upper bound <= -{target:g} hours AND every simultaneous guardrail upper bound <= its limit '
                   f'({bounds}) AND experiment checks pass. Any missing or incomplete primary or guardrail result gives '
                   f'"{NOT_ENOUGH_INFORMATION}".'}


def decision(effects,health):
    result=decide(effects,health,config('analysis_plan'))
    write_json(ROOT/'outputs/decision.json',result)
    return result


def scenario(mart, volume, repeat_handling_minutes, handling_cost_per_hour):
    """Net incremental cost is refund spend plus assumed cost of extra contacts.

    Compute one per-customer composite outcome to preserve covariance; never
    translate elapsed resolution hours into paid agent hours.
    """
    result={'volume':volume,'repeat_handling_minutes':repeat_handling_minutes,
            'handling_cost_per_hour':handling_cost_per_hour,'incremental_cost':None,'ci_low':None,'ci_high':None,
            'assumption':'Same case mix and effects as the experiment; fixed user-supplied handling cost. CI covers sampling uncertainty only.'}
    if not {'refund_usd_7d','repeat_count_7d'}<=set(mart.columns):
        return result
    unit_cost=repeat_handling_minutes/60*handling_cost_per_hour
    values=mart.with_columns((pl.col('refund_usd_7d')+pl.col('repeat_count_7d')*unit_cost).alias('scenario_cost'))
    control=values.filter(pl.col('treatment')==0)['scenario_cost']
    treatment=values.filter(pl.col('treatment')==1)['scenario_cost']
    if control.null_count() or treatment.null_count() or min(len(control),len(treatment))<2:
        return result
    r=difference(control.to_numpy(),treatment.to_numpy())
    return {**result,'incremental_cost':r['effect']*volume,'ci_low':r['ci_low']*volume,'ci_high':r['ci_high']*volume}
