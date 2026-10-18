# Metric definitions

All effects are simplified policy minus current policy. The default cohort contains every assigned customer with a mature seven-day window.

| Metric | Numerator or value | Denominator / missingness | Interpretation |
|---|---|---|---|
| `unresolved_hours_7d` | min(hours to first index-case resolution, 168); unresolved = 168 | All mature assigned customers | Lower is better; elapsed customer time |
| `repeat_contact_7d` | 1 if another case opens within the window, else 0 | All mature assigned customers | Lower is better; rate effect reported as percentage points |
| `repeat_count_7d` | Number of other cases opened within the window | All mature assigned customers | Used in the partial-cost scenario |
| `escalated_7d` | 1 if any linked case has an escalation event within the window | All mature assigned customers | Repeated escalation events remain one customer |
| `refund_usd_7d` | Sum of all linked refund transactions paid in the window | All mature assigned customers; no payment = zero | USD per assigned customer, not per paid customer |
| `resolved_7d` | 1 if the index case resolves at or before 168 hours | All mature assigned customers | Higher is better; secondary endpoint |
| `csat` | Average submitted score for index case in the window | Responding customers only; nonresponse stays null | Descriptive; 1–5 scale |
| `survey_responded` | 1 if an index-case response exists in the window | All mature assigned customers | Shows possible respondent selection |

SQL first aggregates contacts, escalations, refunds and surveys separately by customer. It then joins the aggregates to the assignment spine. This prevents event and transaction joins from multiplying outcomes. If several surveys exist for one customer, their average gets one customer's weight.

All raw datetime fields use UTC semantics. They are stored without timezone metadata because this is a single-timezone synthetic export; ingestion of real local timestamps would require explicit conversion.

The scenario outcome is refund USD + repeat-count × assumed minutes per contact / 60 × assumed hourly cost. Differences and uncertainty are calculated on this combined customer-level quantity to preserve covariance. It excludes initial-case effort and is not a profit estimate.
