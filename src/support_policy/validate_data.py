"""Fail closed: invalid source records stop the analytical pipeline."""
import polars as pl
from .common import ROOT, config, write_json


def validate_frames(f):
    checks = {}
    keys = {'customers':'customer_id','assignments':'customer_id','support_cases':'case_id',
            'case_events':'event_id','refund_transactions':'refund_id','satisfaction_responses':'response_id'}
    for name,key in keys.items():
        frame=f[name]
        checks[f'{name}_unique_key'] = frame[key].n_unique()==frame.height and frame[key].null_count()==0
        required=[c for c in frame.columns if c!='resolved_at']
        checks[f'{name}_required_fields'] = all(frame[c].null_count()==0 for c in required)
    checks['one_assignment_per_customer'] = f['assignments'].height == f['customers'].height
    for name,parent,key in [('assignments','customers','customer_id'),('support_cases','customers','customer_id'),
                            ('case_events','support_cases','case_id'),('refund_transactions','support_cases','case_id'),
                            ('satisfaction_responses','support_cases','case_id')]:
        checks[f'{name}_foreign_key'] = f[name].join(f[parent].select(key),on=key,how='anti').is_empty()
    cases=f['support_cases']
    checks['resolution_after_opening'] = cases.filter(pl.col('resolved_at')<pl.col('opened_at')).is_empty()
    checks['valid_assignment'] = set(f['assignments']['treatment'].unique().to_list()) <= {0,1}
    checks['nonnegative_refunds'] = f['refund_transactions'].filter(pl.col('amount_usd')<0).is_empty()
    checks['valid_survey_scores'] = f['satisfaction_responses'].filter(~pl.col('score').is_between(1,5)).is_empty()
    checks['valid_events'] = set(f['case_events']['event_type'].unique().to_list()) <= {'opened','resolved','escalated'}
    index=f['assignments'].join(cases,left_on='index_case_id',right_on='case_id',how='left',suffix='_case')
    checks['correct_index_case'] = index.filter(pl.col('opened_at').is_null() | (pl.col('customer_id')!=pl.col('customer_id_case')) |
        (pl.col('assigned_at')!=pl.col('opened_at')) | ~pl.col('is_index')).is_empty()
    for name,time in [('case_events','event_at'),('refund_transactions','paid_at'),('satisfaction_responses','responded_at')]:
        joined=f[name].join(cases.select('case_id','opened_at'),on='case_id')
        checks[f'{name}_chronology']=joined.filter(pl.col(time)<pl.col('opened_at')).is_empty()
    return {k:bool(v) for k,v in checks.items()}


def validate():
    f={p.stem:pl.read_parquet(p) for p in (ROOT/'data/raw').glob('*.parquet')}
    checks=validate_frames(f)
    report={'source':'synthetic','checks':checks,'passed':all(checks.values()),'row_counts':{k:v.height for k,v in f.items()}}
    write_json(ROOT/'outputs/validation_report.json',report)
    if not report['passed']:
        raise ValueError('Source validation failed: '+str([k for k,v in checks.items() if not v]))
    return report
