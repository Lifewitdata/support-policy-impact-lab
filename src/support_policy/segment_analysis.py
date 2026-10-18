import polars as pl
from statsmodels.stats.multitest import multipletests
from .common import ROOT, config
from .estimate_effects import difference


def analyse_segments(mart):
    rows=[]
    for segment in config('analysis_plan')['segments']:
        for value in sorted(mart[segment].unique().to_list()):
            group=mart.filter(pl.col(segment)==value)
            for metric in ['unresolved_hours_7d','repeat_contact_7d']:
                result=difference(group.filter(pl.col('treatment')==0)[metric].to_numpy(),
                                  group.filter(pl.col('treatment')==1)[metric].to_numpy())
                rows.append({'segment':segment,'value':value,'metric':metric,**result})
    adjusted=multipletests([r['p_value'] for r in rows],method='fdr_bh')[1]
    for row,q in zip(rows,adjusted): row['q_value_bh']=float(q)
    result=pl.DataFrame(rows);result.write_csv(ROOT/'outputs/tables/segment_effects.csv')
    return result
