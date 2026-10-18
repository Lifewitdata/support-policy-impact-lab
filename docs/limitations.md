# Limits and sensible extensions

- These are generated outcomes. They show an analytical workflow and trade-off, not the effect of any real company's support policy.
- Simulation parameters deliberately create faster resolution and more repeat contacts. Discovering this pattern is not evidence that real support customers behave the same way.
- All customers have full adherence and complete operational event capture. A real experiment would need assignment logging, exposure tracking, missing-event monitoring and contamination checks.
- Customer-level randomisation assumes no spillovers. Shared agents, queue congestion or policy learning could violate that assumption. Cluster assignment may be more appropriate in a live setting.
- Seven-day outcomes omit later contacts, refunds and customer retention. A longer horizon needs its own maturity rules.
- Capped first-resolution time does not measure total time spent unresolved across reopenings. Repeat contact is an additional outcome, not a complete measure of final resolution quality.
- Survey comparisons are subject to nonresponse bias. Response-rate differences are shown explicitly.
- Segment results are exploratory. Within-segment p-values and q-values are not treatment-by-segment interaction tests.
- The cost scenario excludes initial-case handling effort, implementation and training costs, long-term value and congestion. It must not be presented as ROI or measured savings.
- Welch intervals and normal guardrail bounds are asymptotic. Rare events, small segments or much heavier tails may require simulation-based calibration or other inferential methods.
- There is no live support integration, cloud deployment, real-time stream or connection to Uber. Streamlit runs locally or can be deployed from the repository by its owner.
- Source checks stop on bad data; this project does not implement an operational quarantine/replay service. Parallel pipeline writers are not supported.
- AI assisted code and documentation creation. Validation used known simulation truth, boundary fixtures, independent statistical reference calculations, executed notebooks and app interaction checks. Human review is still needed before applying this workflow to live decisions.
