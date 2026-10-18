CREATE OR REPLACE VIEW policy_summary AS
SELECT policy, COUNT(*) AS customers,
 AVG(unresolved_hours_7d) AS unresolved_hours_7d,
 AVG(repeat_contact_7d) AS repeat_contact_7d,
 AVG(escalated_7d) AS escalated_7d, AVG(refund_usd_7d) AS refund_usd_7d,
 AVG(resolved_7d) AS resolved_7d, AVG(csat) AS csat,
 AVG(survey_responded) AS survey_response_rate
FROM experiment_mart GROUP BY policy;
CREATE OR REPLACE VIEW daily_enrolment AS
SELECT CAST(assigned_at AS DATE) AS assignment_date, policy, COUNT(*) AS customers
FROM experiment_mart GROUP BY ALL;
