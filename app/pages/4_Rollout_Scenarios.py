import streamlit as st
from ui import setup,mart
from support_policy.rollout_scenarios import scenario
setup('What would the trade-off cost?')
st.write('Estimate incremental refund spend and repeat-contact handling cost. Customer waiting hours are not converted into agent salary savings.')
a,b,c=st.columns(3)
volume=a.number_input('Future eligible customers',min_value=1000,max_value=10000000,value=100000,step=1000)
minutes=b.slider('Minutes per repeat contact',1,60,12)
hourly=c.slider('Handling cost per hour (USD)',1,100,18)
r=scenario(mart(),volume,minutes,hourly)
st.metric('Estimated incremental cost',f"${r['incremental_cost']:,.0f}")
st.write(f"95% sampling interval: ${r['ci_low']:,.0f} to ${r['ci_high']:,.0f}")
st.caption(r['assumption'])
st.warning('This is a partial-cost scenario, not total ROI. Initial-case effort, implementation costs, retention, congestion and future changes in customer mix are not measured.')
st.write('The interval comes from a per-customer combined cost outcome, preserving the relationship between refunds and repeat contacts. Changing the assumptions does not change the experiment’s original rollout decision.')
