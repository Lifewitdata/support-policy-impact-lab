import numpy as np
import polars as pl
from scipy.stats import chisquare
from .common import ROOT, write_json, config
from datetime import datetime


def check_experiment(mart):
    counts=[mart.filter(pl.col('treatment')==i).height for i in [0,1]]
    srm=float(chisquare(counts,f_exp=[sum(counts)/2]*2).pvalue)
    rows=[]
    for name in ['tenure_days','prior_contacts_30d']:
        x=mart[name].to_numpy(); t=mart['treatment'].to_numpy()
        c,a=x[t==0],x[t==1]; denom=np.sqrt((c.var(ddof=1)+a.var(ddof=1))/2)
        rows.append({'feature':name,'control':float(c.mean()),'treatment':float(a.mean()),'smd':float((a.mean()-c.mean())/denom)})
    for name in ['region','issue_type','tenure_group']:
        for value in sorted(mart[name].unique().to_list()):
            c=mart.filter(pl.col('treatment')==0);t=mart.filter(pl.col('treatment')==1)
            pc=float((c[name]==value).mean());pt=float((t[name]==value).mean())
            den=np.sqrt((pc*(1-pc)+pt*(1-pt))/2)
            rows.append({'feature':name+': '+value,'control':pc,'treatment':pt,'smd':float((pt-pc)/den) if den else 0.0})
    balance=pl.DataFrame(rows);balance.write_csv(ROOT/'outputs/tables/baseline_balance.csv')
    result={'n_control':counts[0],'n_treatment':counts[1],'srm_p_value':srm,'srm_pass':srm>=.001,
            'max_absolute_smd':float(balance['smd'].abs().max()),
            'unique_customer_grain':mart['customer_id'].n_unique()==mart.height,
            'complete_followup':bool((mart['window_end']<=datetime.fromisoformat(config('simulation')['observation_end'])).all()),
            'note':'SRM flags p<0.001. SMD is descriptive; |SMD|>0.1 prompts investigation, not outcome-based exclusions.'}
    write_json(ROOT/'outputs/experiment_checks.json',result)
    return result
