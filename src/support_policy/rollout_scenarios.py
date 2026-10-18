import numpy as np
import polars as pl
from .common import ROOT, config, write_json
from .estimate_effects import difference


def decision(effects,health):
    primary=effects.filter(pl.col('metric')=='unresolved_hours_7d').row(0,named=True)
    plan=config('analysis_plan')
    benefit=primary['ci_high']<=-plan['primary_required_reduction_hours']
    failed=effects.filter(pl.col('guardrail_pass')==False)['metric'].to_list()
    valid=health['srm_pass'] and health['unique_customer_grain'] and health['complete_followup']
    verdict='Scale with monitoring' if valid and benefit and not failed else 'Revise and retest'
    if not valid: verdict='Investigate experiment validity'
    result={'recommendation':verdict,'primary_pass':benefit,'failed_guardrails':failed,
            'rule':'Primary 95% CI upper bound <= -2 hours AND every simultaneous guardrail upper bound <= its limit AND experiment checks pass.'}
    write_json(ROOT/'outputs/decision.json',result)
    return result


def scenario(mart, volume, repeat_handling_minutes, handling_cost_per_hour):
    """Net incremental cost is refund spend plus assumed cost of extra contacts.

    Compute one per-customer composite outcome to preserve covariance; never
    translate elapsed resolution hours into paid agent hours.
    """
    unit_cost=repeat_handling_minutes/60*handling_cost_per_hour
    values=mart.with_columns((pl.col('refund_usd_7d')+pl.col('repeat_count_7d')*unit_cost).alias('scenario_cost'))
    r=difference(values.filter(pl.col('treatment')==0)['scenario_cost'].to_numpy(),
                 values.filter(pl.col('treatment')==1)['scenario_cost'].to_numpy())
    return {'volume':volume,'repeat_handling_minutes':repeat_handling_minutes,
            'handling_cost_per_hour':handling_cost_per_hour,
            'incremental_cost':r['effect']*volume,'ci_low':r['ci_low']*volume,'ci_high':r['ci_high']*volume,
            'assumption':'Same case mix and effects as the experiment; fixed user-supplied handling cost. CI covers sampling uncertainty only.'}
