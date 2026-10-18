-- Timestamp convention: all naive timestamps represent UTC.
CREATE OR REPLACE VIEW stg_customers AS SELECT * FROM raw_customers;
CREATE OR REPLACE VIEW stg_assignments AS SELECT * FROM raw_assignments;
CREATE OR REPLACE VIEW stg_cases AS SELECT * FROM raw_support_cases;
CREATE OR REPLACE VIEW stg_events AS SELECT * FROM raw_case_events;
CREATE OR REPLACE VIEW stg_refunds AS SELECT * FROM raw_refund_transactions;
CREATE OR REPLACE VIEW stg_surveys AS SELECT * FROM raw_satisfaction_responses;
