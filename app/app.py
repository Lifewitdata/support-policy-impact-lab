import streamlit as st
import polars as pl
from ui import setup, table, read_json, effect_chart
from support_policy.common import ROOT

setup('Does faster support mean better support?')
effects=table('treatment_effects');decision=read_json('decision');health=read_json('experiment_checks')
st.subheader(decision['recommendation'])
st.write('The simplified refund process closes the first case sooner. The decision also depends on whether customers return and how much the process costs.')
cols=st.columns(4)
for col,metric,label,scale,suffix in zip(cols,['unresolved_hours_7d','repeat_contact_7d','refund_usd_7d','escalated_7d'],
        ['Waiting time change','Repeat contact change','Refund spend change','Escalation change'],[1,100,1,100],[' h',' pp',' USD',' pp']):
    r=effects.filter(pl.col('metric')==metric).row(0,named=True)
    col.metric(label,f"{r['effect']*scale:+.2f}{suffix}")
st.caption('All changes compare simplified policy with current policy. pp = percentage points. Waiting time is capped at seven days.')
left,right=st.columns(2)
with left:st.plotly_chart(effect_chart(effects,'unresolved_hours_7d'),width='stretch')
with right:st.plotly_chart(effect_chart(effects,'repeat_contact_7d'),width='stretch')
st.info('Use Policy Impact for the decision thresholds, Segment Explorer for follow-up hypotheses, and Rollout Scenarios to change cost assumptions.')
st.download_button('Download the decision brief',(ROOT/'outputs/decision_brief.md').read_text(),'decision_brief.md','text/markdown')
with st.expander('Read the full decision brief'):
    st.markdown((ROOT/'outputs/decision_brief.md').read_text())
