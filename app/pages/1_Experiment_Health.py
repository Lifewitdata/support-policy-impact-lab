import streamlit as st
import plotly.graph_objects as go
from ui import setup, table, read_json
setup('Can we trust the comparison?')
h=read_json('experiment_checks');validation=read_json('validation_report');power=read_json('power_analysis')
a,b,c=st.columns(3)
a.metric('Current policy customers',f"{h['n_control']:,}");b.metric('Simplified policy customers',f"{h['n_treatment']:,}");c.metric('Allocation check p-value',f"{h['srm_p_value']:.3f}")
st.write('An allocation p-value below 0.001 triggers investigation. Baseline balance is descriptive; customers are not removed because an outcome looks inconvenient.')
(st.success if validation['passed'] else st.error)('Source checks passed' if validation['passed'] else 'Source checks failed')
daily=table('daily_enrolment');fig=go.Figure()
for name in daily['policy'].unique().to_list():
    d=daily.filter(daily['policy']==name).sort('assignment_date')
    fig.add_trace(go.Scatter(x=d['assignment_date'].to_list(),y=d['customers'].to_list(),name=name))
fig.update_layout(title='Enrolment by day',template='plotly_white',yaxis_title='Customers')
st.plotly_chart(fig,width='stretch')
st.subheader('Baseline balance');st.dataframe(table('baseline_balance'),hide_index=True,width='stretch')
st.caption('SMD = standardised mean difference. Values above 0.1 in absolute size prompt investigation.')
st.subheader('Sample-size planning');st.json(power)
with st.expander('Source validation checks'):st.json(validation)
