# Experiment design

## Assignment and observation

The unit of randomisation and analysis is the customer. One hundred thousand eligible customers enrol over 28 days from 1 March 2026. Allocation uses an independent Bernoulli draw with probability 0.5, so arm sizes are close rather than exactly equal. The observation cutoff is 8 April 2026 (UTC), allowing every assigned customer a full seven-day window. The SQL maturity filter also supports an earlier cutoff.

The simulation assumes full policy adherence, no cross-customer spillovers and no shared-agent congestion effects. A live support operation would need to assess these assumptions before selecting customer-level randomisation. Eligibility and issue category are determined before assignment. No outcome-based exclusions are allowed.

The analytical window is (assignment time, assignment time + 168 hours]. The index case begins at assignment. A repeat contact exactly at the end is included; one second later is excluded. A separate contact at the exact assignment timestamp is not counted. Raw data also include contacts after seven days, so the window logic is exercised.

## Primary endpoint

Time from assignment to first resolution of the index case, capped at 168 hours. An unresolved index case contributes 168 hours. A resolution at exactly 168 hours is recorded as resolved with 168 hours. This is a restricted waiting-time outcome, not uncapped mean resolution time and not agent handling effort. Reopened or repeat cases do not reset this clock; separate repeat-contact measures capture subsequent work.

Treatment minus control is the reported effect. Negative values improve the primary endpoint. The unadjusted customer-level difference in means drives the decision. A Welch t interval accommodates unequal variance; with roughly 50,000 customers per arm, mean-based inference is practical even for skewed cost and waiting outcomes. It does not imply normally distributed individual cases.

## Rollout rule

1. Experiment checks must pass: no sample-ratio mismatch at p < 0.001, unique customer grain and complete follow-up.
2. The upper endpoint of the primary two-sided 95% confidence interval must be at most -2 hours. Merely excluding zero is not sufficient.
3. The simultaneous one-sided upper confidence bounds must be no higher than +1 percentage point for repeat contact, +0.5 points for escalation and +$0.50 for refund spend per assigned customer.
4. Every one of these results must exist for every assigned customer. If the primary, repeat-contact, escalation or refund result is missing or covers only part of either arm, the recommendation is "Not enough information to decide" and rollout is not recommended. A missing result is never treated as a pass.

The values above are the defaults in `config/analysis_plan.yaml`. The pipeline reads the thresholds from that file, and the decision brief, dashboard and `outputs/decision.json` restate whichever targets were applied. The brief's direction words (increased, decreased, did not change) are generated from the signs of the current estimates rather than written by hand.

Guardrail bounds use a large-sample normal approximation with Bonferroni alpha = 0.05 / 3, giving at least 95% simultaneous coverage for the three upper bounds under the approximation. The plotted two-sided 95% intervals are pointwise and should not be substituted for these decision bounds. The conjunction rule requires every criterion to pass. It does not select the most favourable outcome.

Failure to pass a guardrail can reflect genuine harm or an interval too wide to rule out unacceptable harm. Read the effect and bounds together. There is no repeated peeking or sequential stopping in this fixed-horizon demonstration.

## Planning and sensitivity

Power calculations use an assumed 35-hour primary standard deviation. The primary calculation detects a 2-hour effect against zero; it does not give 80% power to prove an effect exceeds the 2-hour business threshold. Approximate repeat-contact noninferiority planning assumes no true increase, a 12% baseline and the adjusted one-sided alpha. Full joint power and production planning for all guardrails remain outside scope.

A secondary OLS model adjusts the primary endpoint for baseline tenure, prior contacts, issue category and region using HC3 robust standard errors. No post-treatment covariate enters this model.

Issue type, region and tenure group are predefined exploratory segments. Benjamini–Hochberg q-values cover all 16 segment/outcome tests in one family. Their confidence intervals remain pointwise. These tests concern treatment effects within groups, not differences in effects between groups. A targeted rollout would require an interaction analysis and confirmation in new data.

Survey satisfaction is descriptive among respondents. Because response can change with treatment, the respondent-only difference is not an intention-to-treat estimate for all customers and is excluded from the gate.

## Simulation verification

The generator constructs both potential outcomes using shared random draws before revealing the assigned outcome. The finite-sample average of those potential-outcome differences is stored separately. The analysis cannot access those values through its mart; the post-analysis diagnostic compares estimates against them. Not every 95% interval is expected to contain truth in every run. A separate 200-replication null diagnostic checks the estimator on normally distributed synthetic outcomes. Neither diagnostic establishes validity for real operational data.
