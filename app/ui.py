from pathlib import Path
import json
import streamlit as st
import polars as pl
import plotly.graph_objects as go
from support_policy.common import ROOT

LABELS={'unresolved_hours_7d':'Capped time to first resolution (hours)',
        'repeat_contact_7d':'Repeat contact (percentage points)',
        'escalated_7d':'Escalation (percentage points)',
        'refund_usd_7d':'Refund spend (USD/customer)',
        'resolved_7d':'Resolved within seven days (percentage points)',
        'csat':'Satisfaction among respondents (1–5)',
        'survey_responded':'Survey response (percentage points)'}
RATE_METRICS={'repeat_contact_7d','escalated_7d','resolved_7d','survey_responded'}


def setup(title):
    st.set_page_config(page_title=title+' | Support Policy Lab',page_icon='📊',layout='wide')
    st.markdown('<style>.block-container{padding-top:2rem;max-width:1280px} [data-testid="stMetric"]{background:#f1f5f9;border-radius:12px;padding:18px} h1{letter-spacing:-1px}</style>',unsafe_allow_html=True)
    st.caption('SUPPORT POLICY LAB  /  INDEPENDENT PORTFOLIO PROJECT')
    st.title(title)
    st.caption('100% synthetic data · customer-level randomisation · seven-day follow-up · USD')
    if not (ROOT/'outputs/decision.json').exists():
        st.error('Run python -m support_policy.pipeline from the project folder first.')
        st.stop()


def read_json(name):
    return json.loads((ROOT/'outputs'/f'{name}.json').read_text())


@st.cache_data
def load_table(name, modified):
    return pl.read_csv(ROOT/'outputs/tables'/f'{name}.csv')


def table(name):
    path=ROOT/'outputs/tables'/f'{name}.csv'
    return load_table(name,path.stat().st_mtime_ns)


@st.cache_data
def load_mart(modified):
    return pl.read_parquet(ROOT/'data/marts/experiment_mart.parquet')


def mart():
    path=ROOT/'data/marts/experiment_mart.parquet'
    return load_mart(path.stat().st_mtime_ns)


def effect_chart(frame, metric, category=None):
    data=frame.filter(pl.col('metric')==metric)
    scale=100 if metric in RATE_METRICS else 1
    labels=data[category].to_list() if category else ['Policy effect']
    effect=(data['effect']*scale).to_list()
    fig=go.Figure(go.Scatter(x=effect,y=labels,mode='markers',marker={'size':13,'color':'#087f8c'},
        error_x={'type':'data','symmetric':False,'array':((data['ci_high']-data['effect'])*scale).to_list(),
                 'arrayminus':((data['effect']-data['ci_low'])*scale).to_list()}))
    fig.add_vline(x=0,line_dash='dash',line_color='#94a3b8')
    fig.update_layout(title=LABELS[metric],xaxis_title='Treatment − control; pointwise 95% CI',
                      template='plotly_white',height=300,margin={'l':15,'r':15,'t':55,'b':40})
    return fig
