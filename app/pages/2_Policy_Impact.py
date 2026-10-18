import streamlit as st
import polars as pl
from ui import setup, table, read_json, effect_chart, LABELS
from support_policy.common import config
from support_policy.brief import METRIC_NAMES
setup('What changed, and is it enough?')
effects=table('treatment_effects');decision=read_json('decision')
metric=st.selectbox('Outcome',list(LABELS),format_func=lambda x:LABELS[x])
st.plotly_chart(effect_chart(effects,metric),width='stretch')
r=effects.filter(pl.col('metric')==metric)
st.dataframe(r,hide_index=True,width='stretch')
st.subheader('Rollout gate')
plan=config('analysis_plan')
st.write(f"The primary 95% interval must establish at least a {plan['primary_required_reduction_hours']:g}-hour reduction. "
         f"Each guardrail uses a simultaneous one-sided upper bound (Bonferroni across {len(plan['guardrail_limits'])} guardrails). "
         'If the primary result or any guardrail result is missing or incomplete, the decision is "Not enough information to decide".')
guards=effects.filter(pl.col('guardrail_limit').is_not_null()).select('metric','effect','guardrail_upper','guardrail_limit','guardrail_pass')
st.dataframe(guards,hide_index=True,width='stretch')
st.caption('Rate thresholds in the table are fractions: 0.01 means one percentage point. Pointwise chart intervals and simultaneous decision bounds serve different purposes.')
st.write('Decision:',decision['recommendation'])
if decision.get('missing_results'):
    st.warning('Missing or incomplete: '+', '.join(METRIC_NAMES.get(m,m) for m in decision['missing_results']))
st.subheader('Sensitivity check: baseline-adjusted waiting time')
st.dataframe(table('adjusted_primary'),hide_index=True,width='stretch')
st.warning('Satisfaction is observed only among survey respondents. A treatment-related response-rate change can bias that comparison. It does not drive the rollout gate.')
st.download_button('Download outcome estimates',effects.write_csv(),'treatment_effects.csv','text/csv')
