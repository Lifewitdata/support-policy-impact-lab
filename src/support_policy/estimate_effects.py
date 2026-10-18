"""Customer-level ITT estimates; unadjusted estimates drive the decision."""
import numpy as np
import polars as pl
from scipy import stats
import statsmodels.api as sm
from .common import ROOT, config

METRICS=['unresolved_hours_7d','repeat_contact_7d','escalated_7d','refund_usd_7d',
         'resolved_7d','csat','survey_responded']


def difference(control,treatment,alpha=.05):
    c,t=np.asarray(control,dtype=float),np.asarray(treatment,dtype=float)
    c,t=c[np.isfinite(c)],t[np.isfinite(t)]
    if min(len(c),len(t))<2:
        raise ValueError('Each arm needs at least two observed customers')
    vc,vt=c.var(ddof=1)/len(c),t.var(ddof=1)/len(t)
    se=float(np.sqrt(vc+vt)); effect=float(t.mean()-c.mean())
    df=(vc+vt)**2/(vc**2/(len(c)-1)+vt**2/(len(t)-1)) if se else float('inf')
    critical=stats.t.ppf(1-alpha/2,df)
    p=float(2*stats.t.sf(abs(effect/se),df)) if se else (1.0 if effect==0 else 0.0)
    return {'n_control':len(c),'n_treatment':len(t),'control_mean':float(c.mean()),
            'treatment_mean':float(t.mean()),'effect':effect,'se':se,
            'ci_low':float(effect-critical*se),'ci_high':float(effect+critical*se),'p_value':p}


def estimate(mart):
    plan=config('analysis_plan'); rows=[]
    for metric in METRICS:
        c=mart.filter(pl.col('treatment')==0)[metric].to_numpy()
        t=mart.filter(pl.col('treatment')==1)[metric].to_numpy()
        row={'metric':metric,**difference(c,t,plan['alpha'])}
        limit=plan['guardrail_limits'].get(metric)
        row['guardrail_limit']=limit
        row['guardrail_upper']=float(row['effect']+stats.norm.ppf(1-plan['alpha']/len(plan['guardrail_limits']))*row['se']) if limit is not None else None
        row['guardrail_pass']=row['guardrail_upper']<=limit if limit is not None else None
        rows.append(row)
    result=pl.DataFrame(rows)
    result.write_csv(ROOT/'outputs/tables/treatment_effects.csv')
    # Sensitivity analysis: baseline-only covariates and HC3 robust uncertainty.
    X=np.column_stack([np.ones(mart.height),mart['treatment'].to_numpy(),
                      mart['tenure_days'].to_numpy(),mart['prior_contacts_30d'].to_numpy(),
                      *[(mart['issue_type']==v).to_numpy().astype(float) for v in ['Duplicate charge','Cancellation refund']],
                      *[(mart['region']==v).to_numpy().astype(float) for v in ['Region B','Region C']]])
    fit=sm.OLS(mart['unresolved_hours_7d'].to_numpy(),X).fit(cov_type='HC3')
    ci=fit.conf_int()[1]
    pl.DataFrame([{'metric':'unresolved_hours_7d','method':'OLS baseline adjusted; HC3',
                  'effect':float(fit.params[1]),'ci_low':float(ci[0]),'ci_high':float(ci[1])}]).write_csv(ROOT/'outputs/tables/adjusted_primary.csv')
    return result
