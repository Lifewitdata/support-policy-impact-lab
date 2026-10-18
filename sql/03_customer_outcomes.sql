-- Aggregate each one-to-many relation BEFORE joining it to the customer spine.
-- Follow-up is (assigned_at, window_end]; assignment belongs to the index case.
CREATE OR REPLACE TABLE customer_outcomes AS
WITH repeat_contacts AS (
 SELECT a.customer_id, COUNT(c.case_id) AS repeat_count_7d
 FROM eligible_customers a LEFT JOIN stg_cases c ON a.customer_id=c.customer_id
 AND c.case_id<>a.index_case_id AND c.opened_at>a.assigned_at AND c.opened_at<=a.window_end
 GROUP BY a.customer_id
), escalations AS (
 SELECT a.customer_id, MAX(CASE WHEN e.event_type='escalated' THEN 1 ELSE 0 END) AS escalated_7d
 FROM eligible_customers a LEFT JOIN stg_cases c ON a.customer_id=c.customer_id
 LEFT JOIN stg_events e ON e.case_id=c.case_id AND e.event_at>a.assigned_at AND e.event_at<=a.window_end
 GROUP BY a.customer_id
), refunds AS (
 SELECT a.customer_id, COALESCE(SUM(r.amount_usd),0) AS refund_usd_7d
 FROM eligible_customers a LEFT JOIN stg_cases c ON a.customer_id=c.customer_id
 LEFT JOIN stg_refunds r ON c.case_id=r.case_id AND r.paid_at>a.assigned_at AND r.paid_at<=a.window_end
 GROUP BY a.customer_id
), survey AS (
 SELECT a.customer_id, AVG(s.score) AS csat, COUNT(s.response_id) AS survey_count
 FROM eligible_customers a LEFT JOIN stg_surveys s ON a.index_case_id=s.case_id
 AND s.responded_at>a.assigned_at AND s.responded_at<=a.window_end
 GROUP BY a.customer_id
)
SELECT a.customer_id,
 CASE WHEN i.resolved_at IS NOT NULL AND i.resolved_at<=a.window_end
      THEN date_diff('second',a.assigned_at,i.resolved_at)/3600.0
      ELSE {{followup_hours}} END AS unresolved_hours_7d,
 CASE WHEN i.resolved_at IS NOT NULL AND i.resolved_at<=a.window_end THEN 1 ELSE 0 END AS resolved_7d,
 CASE WHEN r.repeat_count_7d>0 THEN 1 ELSE 0 END AS repeat_contact_7d,
 r.repeat_count_7d, e.escalated_7d, f.refund_usd_7d, s.csat,
 CASE WHEN s.survey_count>0 THEN 1 ELSE 0 END AS survey_responded
FROM eligible_customers a JOIN stg_cases i ON a.index_case_id=i.case_id
JOIN repeat_contacts r ON a.customer_id=r.customer_id JOIN escalations e ON a.customer_id=e.customer_id
JOIN refunds f ON a.customer_id=f.customer_id JOIN survey s ON a.customer_id=s.customer_id;
