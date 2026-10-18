from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from support_policy.common import ROOT

@pytest.mark.parametrize('page',[None,'1_Experiment_Health.py','2_Policy_Impact.py','3_Segment_Explorer.py','4_Rollout_Scenarios.py'])
def test_pages_and_controls(page):
    if not (ROOT/'outputs/decision.json').exists():pytest.skip('Run the pipeline before dashboard tests')
    app=AppTest.from_file(str(ROOT/'app/app.py'),default_timeout=30).run()
    assert not app.exception
    if page:
        app.switch_page('pages/'+page).run()
        assert not app.exception
    if page=='2_Policy_Impact.py':
        app.selectbox[0].select('csat').run();assert not app.exception
    if page=='3_Segment_Explorer.py':
        app.selectbox[0].select('region').run();assert not app.exception
    if page=='4_Rollout_Scenarios.py':
        before=app.metric[0].value
        app.number_input[0].set_value(200000).run()
        assert not app.exception and app.metric[0].value!=before
