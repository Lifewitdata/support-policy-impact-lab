import hashlib
import json
from datetime import datetime, timezone
import numpy as np
import polars as pl
import plotly.graph_objects as go
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .common import ROOT, config, write_json
from .brief import brief_text, headline, known
from .generate_data import generate
from .validate_data import validate
from .build_marts import build
from .power_analysis import calculate_power
from .experiment_checks import check_experiment
from .estimate_effects import estimate, difference
from .segment_analysis import analyse_segments
from .rollout_scenarios import decision, scenario


def report(mart,effects,health,verdict):
    lookup={r['metric']:r for r in effects.iter_rows(named=True)}
    cost=scenario(mart,100000,12,18)
    write_json(ROOT/'outputs/default_scenario.json',cost)
    (ROOT/'outputs/decision_brief.md').write_text(brief_text(lookup,health,verdict,cost,config('analysis_plan')))
    metrics=['unresolved_hours_7d','repeat_contact_7d','escalated_7d','refund_usd_7d']
    labels=['Time to first resolution, capped (hours)','Repeat contact (percentage points)',
            'Escalation (percentage points)','Refund spend (USD/customer)']
    fig,axes=plt.subplots(2,2,figsize=(11,6),layout='constrained')
    for ax,m,label in zip(axes.flat,metrics,labels):
        row=lookup.get(m);scale=100 if m in ['repeat_contact_7d','escalated_7d'] else 1
        if known(row,'effect','ci_low','ci_high'):
            point=row['effect']*scale
            ax.errorbar(point,0,xerr=[[point-row['ci_low']*scale],[row['ci_high']*scale-point]],fmt='o',color='#087f8c',capsize=7)
        else:
            ax.text(0.5,0.5,'Not available',transform=ax.transAxes,ha='center',va='center',color='#b42318')
        ax.axvline(0,color='#88939f',ls='--');ax.set_yticks([]);ax.set_title(label,fontsize=11)
        ax.set_xlabel('Simplified policy minus current policy; 95% CI')
    fig.suptitle(headline(lookup)+'\nSynthetic support-policy experiment',fontsize=15)
    fig.savefig(ROOT/'outputs/figures/policy_effects.png',dpi=160);plt.close(fig)
    summary=pl.read_parquet(ROOT/'data/marts/policy_summary.parquet')
    chart=go.Figure(go.Bar(x=summary['policy'].to_list(),y=(summary['repeat_contact_7d']*100).to_list(),marker_color=['#334155','#087f8c']))
    chart.update_layout(title='Seven-day repeat contact | synthetic data',yaxis_title='Customers (%)',template='plotly_white')
    chart.write_html(ROOT/'outputs/figures/repeat_contacts.html',include_plotlyjs=True)


def verify_simulation(effects):
    truth=json.loads((ROOT/'data/processed/simulation_truth.json').read_text())
    rows=[]
    for row in effects.iter_rows(named=True):
        m=row['metric']
        if m in truth:
            rows.append({'metric':m,'finite_sample_true_effect':truth[m],'estimate':row['effect'],
                         'estimation_error':row['effect']-truth[m],
                         'truth_in_95_interval':row['ci_low']<=truth[m]<=row['ci_high']})
    pl.DataFrame(rows).write_csv(ROOT/'outputs/tables/simulation_recovery.csv')
    rng=np.random.default_rng(813);covered=0;false_positive=0
    for _ in range(200):
        c=rng.normal(0,1,2000);t=rng.normal(0,1,2000)
        d=difference(c,t);covered+=d['ci_low']<=0<=d['ci_high'];false_positive+=d['p_value']<.05
    write_json(ROOT/'outputs/estimator_calibration.json',{'replications':200,'null_ci_coverage':covered/200,
        'null_false_positive_rate':false_positive/200,'note':'Diagnostic on normal synthetic outcomes; not a guarantee for every distribution.'})


def main():
    generate();validate();build();calculate_power()
    mart=pl.read_parquet(ROOT/'data/marts/experiment_mart.parquet')
    health=check_experiment(mart);effects=estimate(mart);analyse_segments(mart)
    verdict=decision(effects,health);report(mart,effects,health,verdict);verify_simulation(effects)
    paths=sorted((ROOT/'data/raw').glob('*.parquet'))
    write_json(ROOT/'outputs/run_manifest.json',{'completed_utc':datetime.now(timezone.utc).isoformat(),
        'customers':mart.height,'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'analysis_plan_sha256':hashlib.sha256((ROOT/'config/analysis_plan.yaml').read_bytes()).hexdigest()})
    print(json.dumps({'customers':mart.height,**verdict},indent=2))

if __name__=='__main__': main()
