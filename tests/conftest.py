import duckdb
import pytest
import polars as pl
from datetime import datetime, timedelta
from support_policy.build_marts import execute_models

@pytest.fixture
def frames():
    t=datetime(2026,3,1)
    return {
      'customers':pl.DataFrame({'customer_id':[1,2,3,4],'region':['A']*4,'issue_type':['Fare']*4,
           'tenure_days':[100]*4,'tenure_group':['New']*4,'prior_contacts_30d':[0]*4}),
      'assignments':pl.DataFrame({'customer_id':[1,2,3,4],'treatment':[0,1,0,1],
           'assigned_at':[t]*4,'index_case_id':[1,2,3,4]}),
      'support_cases':pl.DataFrame({'case_id':[1,2,3,4,5,6,7],'customer_id':[1,2,3,4,1,1,1],
           'opened_at':[t,t,t,t,t+timedelta(hours=168),t+timedelta(hours=168,seconds=1),t],
           'resolved_at':[t+timedelta(hours=2),None,t+timedelta(hours=200),t+timedelta(hours=168),None,None,None],
           'is_index':[True]*4+[False]*3}),
      'case_events':pl.DataFrame({'event_id':[1,2,3],'case_id':[1,1,2],
           'event_at':[t+timedelta(hours=1),t+timedelta(hours=1,minutes=10),t+timedelta(hours=169)],
           'event_type':['escalated']*3}),
      'refund_transactions':pl.DataFrame({'refund_id':[1,2,3,4],'case_id':[1,1,5,6],
           'paid_at':[t+timedelta(hours=1),t+timedelta(hours=2),t+timedelta(hours=168),t+timedelta(hours=169)],
           'amount_usd':[3.,4.,2.,99.]}),
      'satisfaction_responses':pl.DataFrame({'response_id':[1],'case_id':[1],
           'responded_at':[t+timedelta(hours=4)],'score':[4]})}

@pytest.fixture
def con(frames):
    db=duckdb.connect(config={'threads':2})
    for name,f in frames.items():
        db.register('incoming',f.to_arrow())
        db.execute(f'CREATE TABLE raw_{name} AS SELECT * FROM incoming')
    execute_models(db,168,'2026-04-08')
    yield db
    db.close()
