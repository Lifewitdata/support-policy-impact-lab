from support_policy.build_marts import execute_models

def test_one_row_per_customer(con):
    assert con.execute('SELECT COUNT(*),COUNT(DISTINCT customer_id) FROM experiment_mart').fetchone()==(4,4)

def test_event_fanout_does_not_inflate_cost(con):
    assert con.execute('SELECT SUM(refund_usd_7d) FROM experiment_mart').fetchone()[0]==9

def test_repeated_escalations_remain_binary(con):
    assert con.execute('SELECT SUM(escalated_7d) FROM experiment_mart').fetchone()[0]==1

def test_no_response_is_missing_not_zero_score(con):
    assert con.execute('SELECT csat,survey_responded FROM experiment_mart WHERE customer_id=2').fetchone()==(None,0)

def test_sql_rerun_is_idempotent(con):
    first=con.execute('SELECT * FROM experiment_mart ORDER BY customer_id').fetchall()
    execute_models(con,168,'2026-04-08')
    assert first==con.execute('SELECT * FROM experiment_mart ORDER BY customer_id').fetchall()
