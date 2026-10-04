# PortPilot AI: Planted Truths

**Status: APPROVED for generator implementation; Truth #1 measured attribution remains pending Day 6.**
**Date drafted:** 2026-09-26

This is the proposed ground truth for deliberately injected signals in the synthetic dataset. It must be approved and frozen before `generate.py` is implemented. If generator output disagrees with an approved version of this document, the generator is wrong.

## Global data window

| Parameter | Value |
|---|---|
| Dataset start | 2026-01-05 (ISO week 2, Monday) |
| Dataset end | 2026-09-27 (ISO week 39, Sunday) |
| `DEMO_AS_OF` | 2026-09-28 |
| Baseline global OTD | 87% with deterministic ISO-week noise within +/- 2 percentage points, independent of generator seed |
| Baseline berth wait | 6.0 hours mean, lognormal distribution |

`DEMO_AS_OF` is the single proposed as-of date. The generator must obtain it from this document rather than maintaining another hardcoded copy. Since the date is one day after the final data date, the demo has no future-dated records or empty trailing data week.

For evaluation, every relative request equivalent to "last week" is anchored to the absolute range **2026-09-21 through 2026-09-27**. The range is recorded in `eval/questions.yaml` so rerunning data generation cannot shift evaluation windows.

Truth #4 is active through dataset end and is therefore still ongoing at `DEMO_AS_OF`. At least one evaluation must distinguish this ongoing signal from a resolved issue.

## Truth #1: Singapore berth congestion

| Field | Proposed value |
|---|---|
| Scope | `port_code = 'SGSIN'` |
| Window | 2026-08-03 through 2026-08-23 (ISO weeks 32-34) |
| Peak | ISO week 33 |
| Effect | `berth_wait_hours` multiplied by 3.0 at peak and 2.0 in weeks 32 and 34 |
| Peak wait | 6.0-hour baseline becomes 18.0 hours |
| Downstream effect | Voyages calling SGSIN arrive late at the next 1-2 ports, decaying by 60% per hop |
| Cause code | `CONGESTION` |
| Advisories | Three documents from `PSA_SINGAPORE`, dated 2026-08-04, 2026-08-11, and 2026-08-18 |
| Attribution target | `TARGET: 50-58%` of APAC OTD drop in week 33 |
| Attribution measurement | `MEASURED: TBD (Day 6)` after `fact_container_journey` exists |

**Attribution method:**

- OTD cohort for both baseline and comparison: APAC containers (`trade_lane IN ('APAC_DOMESTIC', 'NORTH_ASIA', 'TRANS_TASMAN')`), i.e. all APAC lanes excluding `INDIA_APAC`. This keeps the Truth #3 monsoon effect out of the metric while retaining the SGSIN-routed APAC population. Truth #2 changes reefer-exception rates, not OTD, and therefore does not contaminate this OTD baseline.
- Baseline: mean `on_time_delivery_pct` for that cohort over ISO weeks 24-31, the eight weeks preceding the congestion window.
- Comparison: `on_time_delivery_pct` for the same cohort during the congestion window.
- Singapore-attributable share: the OTD drop among containers whose journey includes an SGSIN port call, measured in percentage points, divided by the total APAC OTD drop versus baseline, also measured in percentage points.
- Routing must be determined at container journey level using `fact_container_journey`, not inferred from trade lane.
- Confirm the measured percentage on Day 6. Update the target if measured data does not support it; the data must not be distorted to force the target.

**Control group:** `NORTH_ASIA` and `TRANS_TASMAN` never call SGSIN and make up about 35-40% of the attribution cohort (36.7% on a 20-containers/day check run). They are the non-SGSIN control population; `eval/answer_key.sql` reports lane/routing composition so the share can be confirmed after load.

**Week-33 driver mix design target:** within the APAC attribution cohort, allocate expected OTD probability-drop contributions approximately 55% to SGSIN congestion, 25% to Truth #6 vessel availability, and 20% to Truth #4 customer documentation. These are generator design targets, not measured results; realized OTD outcomes are stochastic and must not be recorded as measured here.

**Baseline-week audit:** the eight calendar weeks immediately preceding ISO week 32 are:

| ISO week | Monday through Sunday | Other planted truths active under the current exclusion rule? |
|---|---|---|
| 24 | 2026-06-08 through 2026-06-14 | Eligible: Truth #2 is not an OTD effect; INDIA_APAC is excluded from this OTD cohort |
| 25 | 2026-06-15 through 2026-06-21 | Eligible: Truth #2 is not an OTD effect; INDIA_APAC is excluded from this OTD cohort |
| 26 | 2026-06-22 through 2026-06-28 | Eligible: Truth #2 is not an OTD effect; INDIA_APAC is excluded from this OTD cohort |
| 27 | 2026-06-29 through 2026-07-05 | Eligible: Truth #2 is not an OTD effect; INDIA_APAC is excluded from this OTD cohort |
| 28 | 2026-07-06 through 2026-07-12 | Eligible: Truth #2 is not an OTD effect; INDIA_APAC is excluded from this OTD cohort |
| 29 | 2026-07-13 through 2026-07-19 | Eligible: Truth #2 is not an OTD effect; INDIA_APAC is excluded from this OTD cohort |
| 30 | 2026-07-20 through 2026-07-26 | Eligible: Truth #2 is not an OTD effect; INDIA_APAC is excluded from this OTD cohort |
| 31 | 2026-07-27 through 2026-08-02 | Eligible: Truth #2 is not an OTD effect; INDIA_APAC is excluded from this OTD cohort |

The baseline is therefore defined and eligible under the agreed OTD cohort. The measured attribution still depends on container routing in `fact_container_journey` and must be reported on Day 6 without tuning the generated data to force the target.

Evaluation question: "Why did APAC on-time delivery drop in week 33?" Expected primary attribution is Singapore congestion, with the measured attribution percentage pending Day 6.

## Truth #2: Reefer failures on one vessel class

| Field | Proposed value |
|---|---|
| Scope | `iso_type = '45R1'` on vessels operated by `NORDIC_REEFER_LINE` |
| Window | Entire dataset; chronic signal |
| Effect | Reefer temperature-excursion exception rate 4.5% versus 0.8% baseline |
| Affected fleet | Eight vessels out of 120 |
| Cause code | `EQUIPMENT` |
| Advisories | Two internal engineering notes; no public advisory |

This persistent signal tests detection of a structural issue rather than only week-over-week changes.

## Truth #3: Indian Ocean monsoon seasonality

| Field | Proposed value |
|---|---|
| Scope | `trade_lane IN ('INDIA_EUROPE', 'INDIA_APAC')` |
| Window | 2026-06-01 through 2026-09-15 |
| Effect | `avg_delay_hours` increases 40% versus non-monsoon months; schedule reliability decreases by up to 12 percentage points at the seasonal peak |
| Shape | Smooth half-sine seasonal curve peaking at the window midpoint, 2026-07-24 |
| Cause code | `WEATHER` |
| Advisories | Six weather bulletins across the window |

This overlaps Truth #1 in time but not geography. Weather must not be used to explain the Singapore congestion drop without evidence connecting those populations.

## Truth #4: Customer-caused documentation delays

| Field | Proposed value |
|---|---|
| Scope | Proposed customer `MERIDIAN_CHEMICALS_GMBH`, tier `GOLD`, segment `CHEMICALS` |
| Window | 2026-05-01 through dataset end; still active at `DEMO_AS_OF` |
| Effect | 34% of bookings have documentation submitted after cutoff |
| Consequence | Median 26-hour dwell penalty before gate-in; carrier schedule unaffected |
| Cause code | `CUSTOMER_DOCUMENTATION` |
| Advisories | Twelve exception notes referencing missing customs paperwork |
| Week-33 cohort effect | Meridian is assigned 20% of APAC-cohort bookings; late documentation applies to 34% of its active-window bookings |
| APAC week-33 OTD effect | Meridian is 20% of the APAC cohort; 34% of its bookings are late on documentation, with a 23.3pp OTD-probability penalty on those rows |

When asked why this customer's OTD is poor, attribute it to customer-side documentation rather than carrier operations. At least one evaluation question must ask whether the issue is ongoing or resolved as of `DEMO_AS_OF`; the expected status is ongoing.

## Truth #5: Missing Rotterdam GATE_OUT events

| Field | Proposed value |
|---|---|
| Scope | `source_system = 'TOS_ROTTERDAM'` and `event_type = 'GATE_OUT'` only |
| Window | 2026-09-01 00:00 through 2026-09-03 23:59 UTC, inclusive |
| Effect | 100% of `GATE_OUT` events are suppressed; rows are absent, not null |
| Other event types | Unaffected; `GATE_IN`, `DISCHARGE`, and `LOAD` continue normally |
| Apparent symptom | Curated dwell at NLRTM is derived from event timestamps. With no GATE_OUT, the open interval is measured from GATE_IN to the 2026-09-28 demo snapshot and capped at 72 hours, producing an apparent dwell up to about 2.4x the normal ~30-hour interval |
| Actual operational impact | None; actual dwell is normal and stored only in `truth_answer_key.csv`, which is not loaded into governed analytics |
| Cause code | None; do not generate `DELAY_EVENT` rows for this signal |
| Advisories | None; no unstructured document explains this anomaly |

Every port call emits a source-specific event stream: `TOS_ROTTERDAM` for NLRTM, `TOS_SINGAPORE` for SGSIN, and a distinct `TOS_*` source for each other port in the route. Journeys calling NLRTM emit events even when Rotterdam is an intermediate call. For each port call, offsets from its call-day midnight UTC are `GATE_IN` +0 hours, `DISCHARGE` +8 hours, `LOAD` +20 hours, and `GATE_OUT` +30 hours with +/-2 hours of deterministic-seed noise. The Rotterdam GATE_OUT rows are suppressed for NLRTM calls dated September 1-3. Other port-source event volumes and other Rotterdam event types continue normally.

The curated dwell view derives dwell from `GATE_OUT - GATE_IN`; for an open interval without `GATE_OUT`, it uses the fixed demo snapshot `DEMO_AS_OF` as the upper bound and caps that open interval at 72 hours. A normal complete interval is about 28-32 hours, so the maximum apparent interval is about 2.4x normal: plausible enough to tempt an operational explanation, but it is derived from event timestamps rather than a precomputed multiplier. Daily GATE_OUT volume for `TOS_ROTTERDAM` falls to zero for these three days while sibling event types and sibling port source systems remain present. The data-quality guard must detect the source-specific volume anomaly. The agent should report a data completeness gap and refuse to assert an operational dwell regression.

## Truth #6: NORTH_ASIA vessel availability

| Field | Proposed value |
|---|---|
| Scope | `trade_lane = 'NORTH_ASIA'`; affected vessels `VESSEL_001` through `VESSEL_036` (30% of the fleet) |
| Window | 2026-08-10 through 2026-08-16 (ISO week 33) |
| Effect | Affected NORTH_ASIA journeys receive a 31-percentage-point OTD probability reduction and an equipment delay |
| Cause code | `EQUIPMENT` |
| Delay event | Emit `DELAY_EVENT` rows with 24 hours for each affected NORTH_ASIA journey |

This incident supplies the equipment component of the week-33 APAC driver mix. It is a synthetic availability incident, not a reefer-temperature excursion.

## Deliberate non-signals

| Control | Proposed definition |
|---|---|
| Random weekly OTD noise | +/- 2 percentage points, no cause; do not manufacture a narrative |
| One-week LAX blip | ISO week 20 (2026-05-11 through 2026-05-17), containers with a USLAX port call show a -3 percentage-point OTD deviation; no cause code or delay event; isolated and not a persistent trend |
| High-volume customer with normal performance | `PACIFIC_RETAIL_GROUP` receives 25% of bookings throughout the dataset, with no injected customer-specific delay or exception rate; guards against treating volume as poor performance |

The LAX control is specified as a one-week -3 percentage-point blip. Since the global weekly noise range is +/- 2 percentage points, -3 is not numerically within that range; its non-signal status is based on being isolated to one week, not on falling within +/- 2 points. The LAX week and high-volume customer/share above are deterministic implementation details added to make the original control descriptions generatable.

## Generator output contract

`generate.py` writes deterministic, headered CSV files into an output directory (default `datagen/output/`). Identifiers are stable within a seed. Dates and truth windows are read from this document; timestamps are UTC. Use `--containers-per-day 3000` for 798,000 containers and approximately 6.95 million port events, near the 800,000-container / 6-million-event scale target; rows are streamed to disk to bound generator memory. Congestion propagation applies the remaining 40% delay at the next port and 16% at the following port, reflecting 60% decay per hop.

| File | Grain and required fields |
|---|---|
| `dim_vessel.csv` | One row per vessel: `vessel_id`, `operator`, `fleet_group` |
| `dim_customer.csv` | One row per customer: `customer_id`, `tier`, `segment`, `contact_email`, `account_manager` (synthetic contacts and manager identifiers) |
| `fact_container_journey.csv` | One row per container and generator seed: `seed_id`, `container_id`, `booking_date`, `delivery_date`, `customer_id`, `trade_lane`, `vessel_id`, `iso_type`, `temperature_excursion`, `on_time_delivery`, `delay_hours`, `documentation_late`, `dwell_penalty_hours`, `routed_through_sgsin` |
| `fact_port_call.csv` | One row per container port call: `container_id`, `port_code`, `call_sequence`, `arrival_date`, `berth_wait_hours`, `delay_hours` |
| `fact_container_event.csv` | One row per emitted event: `event_id`, `container_id`, `port_code`, `source_system`, `event_type`, `event_at_utc` |
| `fact_delay_event.csv` | One row per causal delay: `event_id`, `container_id`, `cause_code`, `delay_hours`, `event_date` |
| `fact_equipment_exception.csv` | One row per reefer excursion: `event_id`, `container_id`, `cause_code`, `iso_type`, `vessel_id`, `event_date` |
| `truth_answer_key.csv` | One row per container: `container_id`, `actual_dwell_hours`; answer-key only, never load into governed analytics |
| `dataset_metadata.csv` | Two rows: `DEMO_AS_OF = 2026-09-28` and `GENERATOR_SEED = <seed>`; load to `PORTPILOT.RAW.DATASET_METADATA` for fixed-snapshot dwell derivation and reproducibility |
| `advisory_documents.csv` | One row per advisory/note: `doc_id`, `publisher`, `issued_at`, `doc_type`, `content` |

**Lane model** (relative booking weight; each port call emits events from that port's TOS source):

| Lane | Region | Route | Weight | Calls SGSIN |
|---|---|---|---|---|
| `ASIA_EUROPE` | Asia-Europe | SGSIN → NLRTM → USLAX | 30 | Yes |
| `TRANS_PACIFIC` | Trans-Pacific | CNSHA → USLAX | 25 | No |
| `INDIA_EUROPE` | Indian Ocean | INNSA → NLRTM | 12 | No |
| `INDIA_APAC` | APAC (monsoon-excluded) | INNSA → SGSIN | 10 | Yes |
| `APAC_DOMESTIC` | APAC | SGSIN | 23 | Yes |
| `NORTH_ASIA` | APAC | CNSHA → KRPUS → JPYOK | 8 | No |
| `TRANS_TASMAN` | APAC | AUSYD → NZAKL → AUMEL | 6 | No |

TOS sources: SGSIN `TOS_SINGAPORE`, NLRTM `TOS_ROTTERDAM`, USLAX `TOS_LOS_ANGELES`, CNSHA `TOS_SHANGHAI`, INNSA `TOS_NHAVASHEVA`, GBFXT `TOS_FELIXSTOWE` (no current lane), AUSYD `TOS_SYDNEY`, KRPUS `TOS_BUSAN`, JPYOK `TOS_YOKOHAMA`, NZAKL `TOS_AUCKLAND`, AUMEL `TOS_MELBOURNE`.

`fact_container_journey` is the container-level population used for OTD calculations. For Truth #1 APAC attribution, filter out `INDIA_APAC` from both baseline and comparison before using the container-level `routed_through_sgsin` flag. `fact_port_call` records each routed port call. `fact_equipment_exception` records Truth #2 with cause code `EQUIPMENT`; it is not a delay event. `actual_dwell_hours` is answer-key-only and is never used to derive curated dwell. `curated_dwell.sql` derives each port-call dwell from the event timestamps; open intervals use the snapshot from `dataset_metadata.csv`. Truth #5's missing-event window is applied to events for NLRTM port calls.

`sql/05_governance.sql` creates the secure customer journey view. On Standard edition, functional roles read through secure views in `SEMANTIC`; they have no grants on `CURATED` or `MARTS`. The secure view applies role-based customer filtering and email masking in its query. The demo `CUSTOMER_ACCESS` mapping grants `PORTPILOT_CUSTOMER_SUCCESS` access to `MERIDIAN_CHEMICALS_GMBH`, `CUSTOMER_002`, and `CUSTOMER_003`. Synthetic customer emails use the reserved `.invalid` domain and are not deliverable addresses.

Weekly OTD noise is a deterministic function of ISO week number, bounded to +/-2 percentage points, and is independent of `--seed`.

## Sign-off checklist

- [x] Dataset window and `DEMO_AS_OF` approved
- [x] Truth #1 multipliers and week 33 peak approved
- [x] Truth #1 baseline cohort and eligible weeks explicitly confirmed
- [ ] Truth #1 measured attribution computed on Day 6 and doc updated to match
- [x] Truth #2 operator and `45R1` scope approved
- [x] Truth #3 lane names match the ontology's `trade_lane` values
- [x] Truth #4 customer, tier, and rate approved; ongoing-versus-resolved evaluation included
- [x] Truth #5 exact window, source, and event type approved
- [x] Control cases approved
- [x] Dataset/table contract documented before generator implementation

## Amendments

- 2026-09-26: Clarified Truth #3 reliability effect as up to -12 percentage points at seasonal peak to match the smooth seasonal coefficient.
- 2026-09-26: Expanded Truth #5 event generation to port-specific sources with staggered UTC event offsets; derived dwell from event intervals with open intervals measured to `DEMO_AS_OF`; removed precomputed dwell from governed journey output and isolated actual dwell in the answer-key file.
- 2026-09-26: Documented streamed 798,000-container / approximately 6.6-million-event generation settings and made sibling-source continuity part of the Truth #5 regression check.
- 2026-09-26: Capped open curated dwell intervals at 72 hours; amended the apparent Truth #5 symptom to at most approximately 2.4x the normal interval.
- 2026-09-26: Recorded that excluding `INDIA_APAC` currently leaves an all-SGSIN `APAC_DOMESTIC` cohort; Day 6 attribution remains blocked on a valid comparison cohort and Snowflake execution.
- 2026-09-29: Added APAC lanes `NORTH_ASIA` (CNSHA → KRPUS → JPYOK) and `TRANS_TASMAN` (AUSYD → NZAKL → AUMEL) with sources `TOS_BUSAN`, `TOS_YOKOHAMA`, `TOS_AUCKLAND`, `TOS_MELBOURNE`; reweighted lanes so the Truth #1 cohort is ~35-40% non-SGSIN. Resolves the 2026-09-26 control-group blocker. Corrected Truth #3 peak from "mid-July" to the implemented 2026-07-24 midpoint.
- 2026-09-30: Added the week-33 NORTH_ASIA vessel-availability incident (30% of vessel IDs, 31pp OTD-probability reduction, 24-hour `EQUIPMENT` delay events) and tuned expected APAC probability-drop contributions to ~55% congestion / 25% equipment / 20% customer documentation. Restated Truth #1 target to 50-58%; the mix is a sanity target, not a measured result. Weekly noise is now deterministic by ISO week and seed-independent.
- 2026-09-30: Standard-edition governance uses secure views in `SEMANTIC` only; functional grants on `CURATED` and `MARTS` are removed. `CUSTOMER_ACCESS` demo mappings are `PORTPILOT_CUSTOMER_SUCCESS` to `MERIDIAN_CHEMICALS_GMBH`, `CUSTOMER_002`, and `CUSTOMER_003`. Added synthetic `account_manager` values to `dim_customer`.