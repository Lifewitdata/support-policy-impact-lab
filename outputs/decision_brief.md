# Support policy decision brief

**Recommendation: Revise and retest.** This is a simulated experiment, not an Uber deployment.

The simplified process reduced seven-day capped time to first resolution from 44.52 to 39.29 hours. The estimated change was -5.23 hours (95% CI -5.79 to -4.68). That is an improvement in elapsed customer waiting time; it is not a measurement of agent labour saved.

The trade-off is repeat contact. The rate moved from 10.02% to 11.99%, a change of 1.97 percentage points (95% CI 1.58 to 2.36). The simultaneous one-sided upper bound is 2.39 points, against a 1-point limit. A faster first resolution does not settle the full customer problem if more people return.

Refund spend changed by $0.44 per assigned customer (95% CI $0.38 to $0.49). Escalation changed by -0.15 percentage points. Guardrails that did not establish acceptable harm: repeat_contact_7d. A failed guardrail can mean harm or insufficient precision; inspect its interval before deciding which.

## What I would do next

Keep the current process as the default. Review repeat-contact reasons for duplicate-charge cases, where the simulation deliberately models a harder support problem. Use the segment results to form a follow-up hypothesis, not to claim that differences between segments have been proved. Test a revised explanation or evidence-check step in a fresh customer-randomised experiment before broad rollout.

For an assumed 100,000 future cases, 12 minutes per repeat contact and $18 per handling hour, incremental refund and repeat-contact handling costs are $50,656 (95% sampling interval $44,869 to $56,443). These assumptions are editable in the app. The scenario excludes unmeasured changes in initial handling effort, retention and satisfaction value; it is not total profit or ROI.

## Why the comparison is usable

There are 50,180 control and 49,820 treatment customers with a complete seven-day window. Randomisation is per customer, and analysis follows original assignment. The sample-ratio mismatch p-value is 0.255. The largest absolute baseline standardised difference is 0.008. Each one-to-many table is aggregated before joins, so repeated events cannot multiply refunds.

## What this experiment cannot tell us

Survey response was 49.2% in control and 44.8% in treatment. Satisfaction is measured among respondents and is not a causal estimate for all customers. Outcomes stop at seven days. We have not measured long-run retention, agent congestion, spillovers, actual process adherence or live costs. All patterns were generated from explicit assumptions, and the conclusions apply only to this simulation.
