# Data dictionary

Six Parquet sources are written to `data/raw/`. IDs are generated integers, not identifiers from a real service. Money is synthetic USD. The SQL database can be inspected with any DuckDB-compatible query client.

| Table | Grain | Key | Fields |
|---|---|---|---|
| customers | One customer | customer_id | region (fictional A/B/C), issue_type (index issue), tenure_days, tenure_group (<180 days / otherwise), prior_contacts_30d |
| assignments | One assignment per customer | customer_id | treatment (0 current, 1 simplified), assigned_at (UTC), index_case_id |
| support_cases | One case | case_id | customer_id, opened_at, resolved_at (nullable), is_index |
| case_events | One case event | event_id | case_id, event_at, event_type (opened / resolved / escalated) |
| refund_transactions | One payment | refund_id | case_id, paid_at, amount_usd |
| satisfaction_responses | One submitted response | response_id | case_id, responded_at, score (1–5) |

`assignments.customer_id` and `support_cases.customer_id` reference customers. Events, refunds and responses reference cases. `assignments.index_case_id` references a case belonging to the assigned customer, opened at assignment.

## Analytical tables

- `eligible_customers`: assignment spine, baseline characteristics and window end; excludes only incomplete follow-up.
- `customer_outcomes`: one row per eligible customer, with the outcomes in metric_definitions.md.
- `experiment_mart`: assignment spine joined to outcomes; adds the human-readable policy label.
- `policy_summary`: one row per policy, with means and denominators.
- `daily_enrolment`: one row per assignment day and policy.

`data/processed/simulation_truth.json` contains counterfactual aggregate effects for simulation verification only. It is never joined into the mart. `outputs/tables/simulation_recovery.csv` compares these values with final estimates.

## Missing values

Null resolution means the first case did not resolve within seven days in the source simulation. Null satisfaction in the mart means no observed survey, never a zero rating. Missing required source fields, orphan keys, invalid chronology or invalid values fail source validation rather than being silently dropped.
