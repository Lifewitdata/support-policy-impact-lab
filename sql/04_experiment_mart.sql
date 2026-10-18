CREATE OR REPLACE TABLE experiment_mart AS
SELECT a.*, CASE WHEN a.treatment=1 THEN 'Simplified policy' ELSE 'Current policy' END AS policy,
       o.* EXCLUDE (customer_id)
FROM eligible_customers a JOIN customer_outcomes o USING (customer_id);
