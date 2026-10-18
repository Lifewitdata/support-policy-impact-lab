# Build verification

The delivered project was executed locally with the versions in requirements.txt.

- Full pipeline completed for 100,000 synthetic customers.
- All 27 source-integrity checks passed.
- All 44 automated tests passed, including all five Streamlit pages and changes to outcome, segment and cost controls. The dashboard was checked with Streamlit AppTest; no browser-based visual test or hosted deployment is claimed.
- Decision-gate tests remove, blank out or partially remove each of the primary, repeat-contact, escalation and refund results and confirm the verdict is "Not enough information to decide". On the real mart, dropping any guardrail column, or blanking 10% of escalation values, gives the same verdict.
- Brief-wording tests confirm that rising waiting time is reported as "increased", falling waiting time as "decreased", and that changed waiting-time and guardrail targets appear in both the verdict and the brief.
- Four notebooks executed successfully: 28 code cells, with tables and four embedded plots. This environment blocks local kernel sockets, so execution used the documented IPython in-process mode. No outputs were invented or filled in by hand.
- Regeneration produced identical SHA-256 hashes for all six source files.
- The rebuilt DuckDB database was reopened read-only and contained 100,000 mart rows. Full refresh builds a new database before replacing prior output, avoiding dependence on an old recovery journal.
- The exported policy-effect PNG was visually inspected.

## Statistical diagnostics

Three of the four verification intervals contained their finite-sample simulated effects in this particular draw. The repeat-contact interval narrowly missed its known effect; this is retained, not hidden or repaired by changing the seed. The estimator's separate 200-replication null diagnostic gave 93.5% interval coverage and a 6.5% rejection rate. Those are finite-simulation diagnostics, not guarantees or real-world validation.

## What was not tested

No live support platform, cloud deployment, browser-hosted app, real policy rollout or real customer outcomes. The seven-day and cost assumptions remain illustrative. See docs/limitations.md.
