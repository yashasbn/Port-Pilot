# PortPilot AI

A governed supply-chain ontology and conversational analytics copilot built on Snowflake.

**Hackathon:** Snowflake CoCo CLI Hackathon 2026  
**Author:** Yashas B N  
**Status:** Week 1 artifacts prepared locally; Snowflake setup/load pending

## What this is

PortPilot models shipping operations from customer and booking through container, voyage,
port call, and delay event. Cortex Analyst answers operational questions, Cortex Search
retrieves advisories, and a Cortex Agent grounds explanations in both structured and
unstructured data.

The demo question:

> "Why did on-time delivery for APAC drop last week, which customers were hit, and what
> should I do about it?"

On Snowflake Standard edition, functional roles read approved secure views in `SEMANTIC`.
They do not receive `USAGE` or object `SELECT` on `CURATED` or `MARTS`. The secure views
implement role filtering and email masking in their query logic; this setup does not depend
on separate masking-policy or row-access-policy objects. Agent activity is audited in
`GOVERNANCE`.

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
monitors, audit table, and owner grants. Replace the five
`REPLACE_WITH_SNOWFLAKE_USERNAME` tokens before running it. Functional roles get no access
to `CURATED` or `MARTS`; `PORTPILOT_ENGINEER` retains ownership grants. `sql/05_governance.sql`
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

## Current status

The Standard-edition secure-view design, lane model, six truths, 25-question eval, and local
CSV generation are prepared. Snowflake account DDL, data load, view execution, and measured
answer-key queries have not been run from this workspace. See `PORTPILOT_STATUS.md` for the
current handoff.