# A faster first answer is not the whole outcome

A support team wants to shorten refund cases. Its proposed process removes a verification step and uses a simpler explanation. That could reduce waiting, but customers may return if the underlying issue is not settled.

The decision is whether to expand this process, revise it or stop. The support lead cares about repeat work; the customer-experience lead cares about waiting and escalation; finance cares about refund spend. A useful analysis makes those trade-offs visible rather than choosing the metric that looks best.

This repository is an independent portfolio exercise for a data analytics role. It uses no Uber data, policies, branding, internal systems or customer information. Every record is generated from code. The policy and parameters are fictional.

## What is delivered

A six-table synthetic source, a validated customer-level SQL mart, a reproducible experiment analysis, four executed notebooks, a five-page Streamlit application and a short decision brief. The app reads the pipeline's outputs; it does not silently rebuild data on page load.

## What success means

The new policy must reduce seven-day capped waiting time by at least two hours while establishing acceptable limits on repeat contacts, escalation and refund spend. Thresholds are demonstration business choices, not Uber targets. They are written in the analysis plan before examining the simulated run.

## Scope

Eligible customers have one index refund-support case. They are independently assigned with probability 0.5 to one policy and remain in that arm. All following contacts are attributed to their original assignment. No demographic or protected attributes are generated. Regions are fictional labels.
