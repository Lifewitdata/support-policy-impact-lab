import streamlit as st
import polars as pl
from ui import setup,table,effect_chart,LABELS
setup('Where should we investigate next?')
s=table('segment_effects')
segment=st.selectbox('Compare by',s['segment'].unique().sort().to_list())
metric=st.selectbox('Outcome',['unresolved_hours_7d','repeat_contact_7d'],format_func=lambda x:LABELS[x])
view=s.filter((pl.col('segment')==segment)&(pl.col('metric')==metric))
st.plotly_chart(effect_chart(view,metric,category='value'),width='stretch')
st.dataframe(view,hide_index=True,width='stretch')
st.info('These are exploratory estimates in predefined segments. The q-values apply Benjamini–Hochberg adjustment across all segment/outcome tests. Intervals remain pointwise. A significant effect in one group and a nonsignificant effect in another does not prove the groups differ.')
