# PortPilot AI

A governed supply-chain ontology and conversational analytics copilot built on Snowflake.

**Hackathon:** Snowflake CoCo CLI Hackathon 2026  
**Author:** Yashas B N  
**Status:** Snowflake setup, data load, secure-view governance, and demo checks verified (2026-10-04)

## What this is

PortPilot models shipping operations from customer and booking through container, voyage,
port call, and delay event. The planned assistant experience combines Cortex Analyst,
Cortex Search, and a Cortex Agent over structured operations data and advisories; those
assistant components are deferred in this delivery.

Account parameter `QUOTED_IDENTIFIERS_IGNORE_CASE = TRUE` is required, because RAW columns are inferred from lowercase CSV headers. The cleaner long-term fix is to rebuild the RAW tables with uppercase column names, but that isn't worth doing before the deadline.

The demo question:

> "Why did on-time delivery for APAC drop last week, which customers were hit, and what
> should I do about it?"

On Snowflake Standard edition, functional roles read approved secure views in `SEMANTIC`.
They do not receive `USAGE` or object `SELECT` on `CURATED` or `MARTS`. Secure-view query
logic applies role-based customer filtering and masks contact emails. The governance audit
table is in `GOVERNANCE`.

## Repository layout

```text
portpilot/
├── sql/
│   ├── 00_setup_account.sql
│   ├── 02_curated_dwell.sql
│   └── 05_governance.sql
├── datagen/
│   ├── generate.py
│   └── planted_truths.md
├── eval/
│   ├── questions.yaml
│   └── answer_key.sql
├── tests/
│   └── test_truth5_event_stream.py
├── coco/transcripts/
└── PORTPILOT_STATUS.md
```

## Account and governance SQL

`sql/00_setup_account.sql` creates the account roles, database, schemas, warehouses, resource
monitors, audit table, and owner grants, and grants the roles to Snowflake user `YASHASBN`.
Functional roles get no access to `CURATED` or `MARTS`; `PORTPILOT_ENGINEER` retains
ownership grants. `sql/05_governance.sql`
creates `GOVERNANCE.CUSTOMER_ACCESS` and secure view `SEMANTIC.V_CONTAINER_JOURNEY`, then
adds demo access for `PORTPILOT_CUSTOMER_SUCCESS` to `MERIDIAN_CHEMICALS_GMBH`, `CUSTOMER_002`,
and `CUSTOMER_003`. Synthetic contact emails use `.invalid` and cannot receive mail.

`PORTPILOT_ENGINEER` inherits all four functional roles. Test view behavior while using the
functional roles directly, not the engineer role.

## Ground truth and generator

[datagen/planted_truths.md](datagen/planted_truths.md) is the generator/evaluation contract.
It defines six planted truths and three control cases. Week 33 is designed for an approximate
55/25/20 OTD probability-contribution mix across SGSIN congestion, the `NORTH_ASIA`
equipment-availability incident, and customer documentation. This is a design sanity target,
not a measured result. Weekly OTD noise is deterministic by ISO week and independent of
`--seed`.

Generate the final seed and gzip its CSV files:

```bash
python3 datagen/generate.py --output-dir datagen/output --containers-per-day 3000 --seed 20260926
find datagen/output -maxdepth 1 -name '*.csv' -exec gzip -f {} +
```

The generator streams rows and writes `seed_id` into journey facts. The answer-key-only
`truth_answer_key.csv` must never be loaded into the governed semantic layer.

## Evaluation and checks

`eval/questions.yaml` contains 25 questions with absolute date ranges or explicit as-of dates.
`eval/answer_key.sql` measures attribution after loading the final seed into Snowflake; do not
record its target as measured before running it there.

Run the local Truth #5 event-stream regression:

```bash
python3 -m unittest tests/test_truth5_event_stream.py
```

The regression checks the Rotterdam `GATE_OUT` gap, continuing Rotterdam sibling event
volumes, other source feeds, event-derived dwell inputs, and the capped open interval.

## Results

Full output: [snowflake/demo_results.txt](snowflake/demo_results.txt). Reproduce with
`bash snowflake/run_all.sh`.

| Check | Result |
|---|---|
| Load | 798,000 journeys · 6,948,049 events · 0 load errors |
| APAC OTD by ISO week (weeks 30–36) | 84.6% · 85.8% · 85.1% · **77.0%** · 82.7% · 84.7% · 86.0% |
| Week-33 delay causes | CONGESTION 4,269 · CUSTOMER_DOCUMENTATION 444 · EQUIPMENT 405 |
| Rotterdam GATE_OUT feed | 0 on Sep 1–3; other feeds report 5,410 · 5,422 · 5,508 |
| Governance role checks | OPS_ANALYST: 20 customers; CUSTOMER_SUCCESS: 3 customers and `***MASKED***` email |

## Built vs. deferred

**Built:** synthetic data with six planted truths and three controls · Snowflake account
foundation and RAW load · secure views with role-based customer filtering and email masking
· daily event-volume table · role-based governance checks and end-to-end verification.

**Deferred:** Cortex Analyst semantic view and Cortex Agent · Cortex Search · custom tools
(`ROOT_CAUSE_ATTRIBUTION`, `DATA_QUALITY_GUARD`) · Streamlit UI · full evaluation run ·
measured Truth #1 attribution.

**Setup note:** Requires `ALTER ACCOUNT SET QUOTED_IDENTIFIERS_IGNORE_CASE = TRUE;` because
RAW columns are inferred from lowercase CSV headers.

See [PORTPILOT_STATUS.md](PORTPILOT_STATUS.md) for the delivery checklist.
