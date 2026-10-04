# PortPilot Account Foundation Transcript

Date: 2026-09-26

This is the engineering decision record for the account-foundation setup and its review. It records decisions and unresolved verification items from the conversation; it does not claim that the SQL was executed.

## Requested foundation

- Create `PORTPILOT` with `RAW`, `CURATED`, `MARTS`, `SEMANTIC`, and `GOVERNANCE` schemas.
- Create `PORTPILOT_WH` and a separate data-generation warehouse, initially XSMALL, auto-suspending after 60 seconds and auto-resuming.
- Establish monthly credit controls, functional roles, an engineering owner role, scoped future access grants, and `GOVERNANCE.AGENT_AUDIT`.
- Review the full DDL before execution and verify created objects and warehouse monitor assignments.

## Review decisions

1. Use explicit `USERADMIN`, `SYSADMIN`, `ACCOUNTADMIN`, and `SECURITYADMIN` role contexts for role creation/hierarchy, database and warehouse creation, monitors, and grants respectively.
2. Prefix functional roles with `PORTPILOT_`; keep `PORTPILOT_ENGINEER` as the ownership/build role.
3. Grant `PORTPILOT_ENGINEER` to `SYSADMIN`; grant all four functional roles to `PORTPILOT_ENGINEER`. The engineer role therefore inherits functional access and must not be used to test row-access-policy behavior.
4. Split the shared quota into `PORTPILOT_RM` at 35 credits for `PORTPILOT_WH`, and `PORTPILOT_LOAD_RM` at 15 credits for `PORTPILOT_LOAD_WH`, each monthly with notification at 50% and 75%, suspend at 90%, and immediate suspend at 100%.
5. Functional roles use only `PORTPILOT_WH`; `PORTPILOT_ENGINEER` alone uses the load warehouse. The data-generator connection must explicitly select `PORTPILOT_LOAD_WH` and role `PORTPILOT_ENGINEER` to preserve load-cost attribution.
6. Functional-role future reads are scoped to `CURATED`, `MARTS`, and `SEMANTIC`; there is no functional-role blanket `SELECT` on `RAW`. `PORTPILOT_AUDITOR` alone gets schema usage on `GOVERNANCE` and `SELECT` on `AGENT_AUDIT`.
7. Future dynamic-table grants are included for `MARTS`. Future semantic-view and Cortex Search Service grants remain in the script but are unverified. On the first execution, run statement-by-statement; if either form is rejected, grant access explicitly when creating those objects.
8. Transfer ownership of the database, schemas, audit table, and both warehouses to `PORTPILOT_ENGINEER`, preserving current grants.
9. Verification switches to `PORTPILOT_ENGINEER` and `PORTPILOT_WH`; `SHOW RESOURCE MONITORS` runs under `ACCOUNTADMIN`. The final statement switches back to `PORTPILOT_ENGINEER`.
10. The current setup script grants all five roles to Snowflake user `YASHASBN` in
	`sql/00_setup_account.sql`.

## Execution status

At that earlier handoff, no Snowflake connection was configured in the VS Code session.
The subsequent setup, load, and role checks are recorded in `snowflake/demo_results.txt`.

## Day 2 handoff

The initial handoff correctly left planted signals and the missing `GATE_OUT` window unresolved. The user subsequently supplied and approved a draft spec with `DEMO_AS_OF = 2026-09-28`, dataset end 2026-09-27, and the exact Rotterdam `TOS_ROTTERDAM` `GATE_OUT` suppression window of 2026-09-01 through 2026-09-03 UTC. Truth #1's APAC OTD cohort was clarified to exclude `INDIA_APAC`; ISO weeks 24-31 are its baseline, with container-level SGSIN routing attribution to be measured on Day 6 rather than forced to the target.

`datagen/planted_truths.md`, `eval/questions.yaml`, and `datagen/generate.py` were then added. The generator reads dates/windows from the truths document and emits deterministic CSVs. The measured Truth #1 attribution remains pending Day 6. No Snowflake operations were performed as part of this Day 2 work.
