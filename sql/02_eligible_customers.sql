-- Eligibility is determined at assignment. Maturity depends only on time, not outcomes.
CREATE OR REPLACE TABLE eligible_customers AS
SELECT a.*, a.assigned_at + INTERVAL '{{followup_hours}} hours' AS window_end,
       c.region, c.issue_type, c.tenure_days, c.tenure_group, c.prior_contacts_30d
FROM stg_assignments a JOIN stg_customers c USING (customer_id)
WHERE a.assigned_at + INTERVAL '{{followup_hours}} hours' <= TIMESTAMP '{{observation_end}}';
