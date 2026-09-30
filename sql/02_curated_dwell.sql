-- Dwell is derived from the port event stream, never from a precomputed multiplier.
-- Load dataset_metadata.csv into PORTPILOT.RAW.DATASET_METADATA and event rows into
-- PORTPILOT.RAW.FACT_CONTAINER_EVENT before creating this view.
CREATE OR REPLACE VIEW PORTPILOT.CURATED.CONTAINER_PORT_DWELL AS
WITH snapshot AS (
  SELECT TO_TIMESTAMP_TZ(
           MAX(IFF(metadata_key = 'DEMO_AS_OF', metadata_value, NULL)) || ' 23:59:59 +00:00'
         ) AS snapshot_at
  FROM PORTPILOT.RAW.DATASET_METADATA
), port_events AS (
  SELECT
    container_id,
    port_code,
    source_system,
    MIN(IFF(event_type = 'GATE_IN', event_at_utc::TIMESTAMP_TZ, NULL)) AS gate_in_at,
    MIN(IFF(event_type = 'GATE_OUT', event_at_utc::TIMESTAMP_TZ, NULL)) AS gate_out_at,
    MAX(event_at_utc::TIMESTAMP_TZ) AS last_observed_event_at
  FROM PORTPILOT.RAW.FACT_CONTAINER_EVENT
  GROUP BY container_id, port_code, source_system
)
SELECT
  events.container_id,
  events.port_code,
  events.source_system,
  events.gate_in_at,
  events.gate_out_at,
  events.last_observed_event_at,
  events.gate_out_at IS NULL AS is_open_interval,
  CASE
    WHEN events.gate_out_at IS NULL THEN LEAST(
      DATEDIFF('second', events.gate_in_at, snapshot.snapshot_at) / 3600.0,
      72.0
    )
    ELSE DATEDIFF('second', events.gate_in_at, events.gate_out_at) / 3600.0
  END AS dwell_time_hours
FROM port_events AS events
CROSS JOIN snapshot
WHERE events.gate_in_at IS NOT NULL;
