-- Day 6 Truth #1 measurement.
-- Load fact_container_journey.csv for two --seed values into
-- PORTPILOT.MARTS.FACT_CONTAINER_JOURNEY, appending both loads. The CSV includes
-- SEED_ID so each run is measured independently. Use PORTPILOT_LOAD_WH.
--
-- Assign each journey to its exposure week using BOOKING_DATE, the date on
-- which congestion effects are applied by the generator.
-- Baseline: eight complete weeks 2026-06-08 through 2026-08-02 (ISO weeks 24-31).
-- Comparison: ISO week 33, 2026-08-10 through 2026-08-16.
-- Per the approved cohort, INDIA_APAC is excluded to avoid Truth #3 overlap.
-- The composition query below reports if the remaining cohort lacks an
-- unrouted comparison group; do not accept an attribution percentage without
-- reviewing that diagnostic.
USE WAREHOUSE PORTPILOT_LOAD_WH;

WITH eligible_journeys AS (
  SELECT
    seed_id,
    booking_date::DATE AS exposure_date,
    trade_lane,
    routed_through_sgsin = 1 AS routed_through_sgsin,
    on_time_delivery::FLOAT AS on_time_delivery
  FROM PORTPILOT.MARTS.FACT_CONTAINER_JOURNEY
  WHERE trade_lane IN ('APAC_DOMESTIC', 'NORTH_ASIA', 'TRANS_TASMAN')
    AND booking_date::DATE BETWEEN '2026-06-08' AND '2026-08-16'
), seed_metrics AS (
  SELECT
    seed_id,
    AVG(IFF(exposure_date BETWEEN '2026-06-08' AND '2026-08-02', on_time_delivery, NULL)) AS baseline_apac_otd,
    AVG(IFF(exposure_date BETWEEN '2026-08-10' AND '2026-08-16', on_time_delivery, NULL)) AS week33_apac_otd,
    AVG(IFF(exposure_date BETWEEN '2026-06-08' AND '2026-08-02' AND routed_through_sgsin, on_time_delivery, NULL)) AS baseline_sgsin_otd,
    AVG(IFF(exposure_date BETWEEN '2026-08-10' AND '2026-08-16' AND routed_through_sgsin, on_time_delivery, NULL)) AS week33_sgsin_otd,
    COUNT_IF(exposure_date BETWEEN '2026-08-10' AND '2026-08-16' AND NOT routed_through_sgsin) AS week33_unrouted_rows
  FROM eligible_journeys
  GROUP BY seed_id
)
SELECT
  seed_id,
  baseline_apac_otd * 100 AS baseline_apac_otd_pct,
  week33_apac_otd * 100 AS week33_apac_otd_pct,
  (baseline_apac_otd - week33_apac_otd) * 100 AS total_apac_drop_pp,
  baseline_sgsin_otd * 100 AS baseline_sgsin_otd_pct,
  week33_sgsin_otd * 100 AS week33_sgsin_otd_pct,
  (baseline_sgsin_otd - week33_sgsin_otd) * 100 AS sgsin_group_drop_pp,
  100 * (baseline_sgsin_otd - week33_sgsin_otd)
      / NULLIF(baseline_apac_otd - week33_apac_otd, 0) AS requested_attribution_pct,
  week33_unrouted_rows,
  CASE
    WHEN week33_unrouted_rows = 0 THEN 'NO UNROUTED APAC CONTROL; REVIEW COHORT BEFORE ACCEPTING ATTRIBUTION'
    ELSE 'REVIEW AGAINST 50-58% TARGET'
  END AS interpretation
FROM seed_metrics
ORDER BY seed_id;

-- Cohort composition by seed. INDIA_APAC is shown for context but excluded from
-- the attribution cohort; NORTH_ASIA and TRANS_TASMAN are the non-SGSIN control.
SELECT
  seed_id,
  trade_lane,
  routed_through_sgsin,
  COUNT(*) AS journey_count,
  AVG(on_time_delivery::FLOAT) * 100 AS otd_pct
FROM PORTPILOT.MARTS.FACT_CONTAINER_JOURNEY
WHERE booking_date::DATE BETWEEN '2026-06-08' AND '2026-08-16'
  AND trade_lane IN ('INDIA_APAC', 'APAC_DOMESTIC', 'NORTH_ASIA', 'TRANS_TASMAN')
GROUP BY seed_id, trade_lane, routed_through_sgsin
ORDER BY seed_id, trade_lane, routed_through_sgsin;
