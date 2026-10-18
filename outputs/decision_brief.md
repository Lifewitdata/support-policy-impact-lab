# Support policy decision brief

**Recommendation: Revise and retest.** This is a simulated experiment, not an Uber deployment.

Under the simplified process, seven-day capped time to first resolution decreased from 44.52 hours to 39.29 hours, a decrease of 5.23 hours (95% CI -5.79 hours to -4.68 hours). The rollout target requires the whole 95% interval to sit at or below -2 hours, a reduction of at least 2 hours; this target was met. Customers waited less for a first resolution. This is elapsed customer waiting time, not a measurement of agent labour saved.

Repeat contact increased from 10.02% to 11.99%, an increase of 1.97 percentage points (95% CI +1.58 points to +2.36 points). Its simultaneous one-sided upper bound is +2.388 points against a limit of +1.000 points, so this guardrail failed. Escalation decreased from 5.44% to 5.29%, a decrease of 0.15 percentage points (95% CI -0.43 points to +0.13 points). The interval includes zero, so the direction of the change is not established. Its simultaneous one-sided upper bound is +0.150 points against a limit of +0.500 points, so this guardrail passed. Refund spend per assigned customer increased from $3.69 to $4.13, an increase of $0.44 (95% CI +$0.38 to +$0.49). Its simultaneous one-sided upper bound is +$0.497 against a limit of +$0.500, so this guardrail passed.

The trade-off is repeat contact: a faster first resolution does not settle the full customer problem if more people return. Guardrails that did not establish acceptable harm: repeat_contact_7d. A failed guardrail can mean harm or insufficient precision; inspect its interval before deciding which.

## What I would do next

Keep the current process as the default. Review repeat-contact reasons for duplicate-charge cases, where the simulation deliberately models a harder support problem. Use the segment results to form a follow-up hypothesis, not to claim that differences between segments have been proved. Test a revised explanation or evidence-check step in a fresh customer-randomised experiment before broad rollout.

For an assumed 100,000 future cases, 12 minutes per repeat contact and $18 per handling hour, refund and repeat-contact handling costs rise by $50,656 (95% sampling interval $44,869 to $56,443). These assumptions are editable in the app. The scenario excludes unmeasured changes in initial handling effort, retention and satisfaction value; it is not total profit or ROI.

## Why the comparison is usable

There are 50,180 control and 49,820 treatment customers with a complete seven-day window. Randomisation is per customer, and analysis follows original assignment. The sample-ratio mismatch p-value is 0.255, at or above the 0.001 investigation threshold. The largest absolute baseline standardised difference is 0.008. Each one-to-many table is aggregated before joins, so repeated events cannot multiply refunds.

## What this experiment cannot tell us

Survey response was 49.2% in control and 44.8% in treatment. Satisfaction is measured among respondents and is not a causal estimate for all customers. Outcomes stop at seven days. We have not measured long-run retention, agent congestion, spillovers, actual process adherence or live costs. All patterns were generated from explicit assumptions, and the conclusions apply only to this simulation.
