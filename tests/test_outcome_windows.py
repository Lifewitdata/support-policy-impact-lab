from support_policy.build_marts import execute_models

def test_repeat_window_boundaries(con):
    # Exactly 168 hours is included; one second later and time zero are excluded.
    assert con.execute('SELECT repeat_count_7d FROM experiment_mart WHERE customer_id=1').fetchone()[0]==1

def test_unresolved_and_late_resolution_are_capped(con):
    values=con.execute('SELECT customer_id,unresolved_hours_7d,resolved_7d FROM experiment_mart ORDER BY customer_id').fetchall()
    assert values==[(1,2.0,1),(2,168.0,0),(3,168.0,0),(4,168.0,1)]

def test_maturity_exclusion_does_not_depend_on_outcomes(con):
    execute_models(con,168,'2026-03-07')
    assert con.execute('SELECT COUNT(*) FROM experiment_mart').fetchone()[0]==0

def test_followup_refunds_included_late_refunds_excluded(con):
    assert con.execute('SELECT refund_usd_7d FROM experiment_mart WHERE customer_id=1').fetchone()[0]==9.0
