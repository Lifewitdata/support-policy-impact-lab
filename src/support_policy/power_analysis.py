import math
from scipy.stats import norm
from statsmodels.stats.power import TTestIndPower
from .common import ROOT, config, write_json


def calculate_power():
    p=config('analysis_plan');alpha=p['alpha'];power=p['power']
    delta=p['primary_required_reduction_hours']; sd=p['planning_primary_sd_hours']
    primary=math.ceil(TTestIndPower().solve_power(effect_size=delta/sd,alpha=alpha,power=power,ratio=1))
    baseline=p['planning_repeat_baseline']; margin=p['guardrail_limits']['repeat_contact_7d']
    # Approximate NI planning under a true zero difference, with Bonferroni alpha.
    critical=norm.ppf(1-alpha/len(p['guardrail_limits']))+norm.ppf(power)
    repeat=math.ceil(2*baseline*(1-baseline)*critical**2/margin**2)
    result={'primary_n_per_arm':primary,'repeat_guardrail_n_per_arm_approx':repeat,
            'planned_total':config('simulation')['n_customers'],
            'note':'Primary power detects a 2-hour difference from zero; it does not give 80% power to prove at least a 2-hour reduction. Guardrail planning assumes a true zero effect. No joint power guarantee; escalation and cost need separate planning in production.'}
    write_json(ROOT/'outputs/power_analysis.json',result)
    return result
