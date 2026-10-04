# PortPilot AI - Streamlit Operations Command Center

Governed operational analytics dashboard with planted-truth validation, data-quality safeguards, and role-aware access control built natively on Snowflake (Streamlit in Snowflake - SiS).

---

## Overview

The **PortPilot AI** Streamlit prototype delivers supply chain operational visibility directly on Snowflake Standard Edition using secure views and Snowpark session context. It validates known operational ground truths without requiring an external middle-tier server or exposed credentials.

### Four Core Capabilities

1. **Executive Overview (APAC OTD Trend)**:
   - Tracks 798,000 container journeys and 6.95M container events.
   - Live query of APAC cohort (`APAC_DOMESTIC`, `NORTH_ASIA`, `TRANS_TASMAN`) on-time delivery across ISO weeks 30–36.
   - Highlights the week-33 performance drop to **77.0%** (-8.1 pp vs. week 32) and subsequent recovery to 86.0% by week 36.

2. **Root-Cause Breakdown**:
   - Analyzes week-33 delay incidents for the APAC cohort from `PORTPILOT.SEMANTIC.V_DELAY_EVENT`.
   - Distinguishes observed event drivers (Congestion: 4,269 events; Customer Documentation: 444; Equipment: 405) from formal counterfactual attribution models.

3. **Data Quality Guard (Rotterdam Feed Telemetry)**:
   - Audits daily event ingestion volumes from `PORTPILOT.SEMANTIC.EVENT_VOLUME_DAILY`.
   - Flags the TOS_ROTTERDAM zero-event gap (`GATE_OUT = 0`) on September 1–3, 2026, while normal network feeds persist (~5,400 events/day), preventing false operational alarms.

4. **Role-Aware Governed Access**:
   - Visualizes live `CURRENT_ROLE()` session state and secure view masking from `PORTPILOT.SEMANTIC.V_CONTAINER_JOURNEY`.
   - Demonstrates row filtering and column masking (`PORTPILOT_OPS_ANALYST` sees 20 customers unmasked; `PORTPILOT_CUSTOMER_SUCCESS` sees only 3 assigned customers with emails masked as `***MASKED***`).

---

## Deployment Instructions

### Method 1: Snowsight UI (Recommended / Fast Deployment)

1. Log in to Snowflake Snowsight under account **`TSNUGNW-GW48763`** as user **`YASHASBN`**.
2. Navigate to **Projects** → **Streamlit**.
3. Click **+ Streamlit App** (top right).
4. Enter the application settings:
   - **App name:** `PORTPILOT_APP`
   - **App location (Database & Schema):** `PORTPILOT` → `SEMANTIC`
   - **Warehouse:** `PORTPILOT_WH`
5. Replace the template code in the editor with the full contents of `streamlit/app.py`.
6. (Optional) In the **Packages** dropdown, ensure `altair` and `snowflake-snowpark-python` are included (included by default).
7. Click **Run** (top right).
8. Click **Share** (top right) to copy the application URL.

### Method 2: Stage & SQL Deployment

Run [sql/06_streamlit_app.sql](file:///c:/Users/Yashas/Downloads/portpilot/portpilot/sql/06_streamlit_app.sql) in Snowsight or via SnowSQL:

```sql
-- 1. Create stage
CREATE STAGE IF NOT EXISTS PORTPILOT.SEMANTIC.PORTPILOT_APP_STAGE DIRECTORY = (ENABLE = TRUE);

-- 2. Upload files (via SnowSQL or Snow CLI)
-- PUT file://streamlit/app.py @PORTPILOT.SEMANTIC.PORTPILOT_APP_STAGE/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
-- PUT file://streamlit/environment.yml @PORTPILOT.SEMANTIC.PORTPILOT_APP_STAGE/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;

-- 3. Create Streamlit application
CREATE OR REPLACE STREAMLIT PORTPILOT.SEMANTIC.PORTPILOT_APP
  ROOT_LOCATION = '@PORTPILOT.SEMANTIC.PORTPILOT_APP_STAGE'
  MAIN_FILE = 'app.py'
  QUERY_WAREHOUSE = PORTPILOT_WH
  COMMENT = 'PortPilot AI Governed Supply-Chain Operations Command Center';

-- 4. Grant access to functional roles
GRANT USAGE ON STREAMLIT PORTPILOT.SEMANTIC.PORTPILOT_APP TO ROLE PORTPILOT_OPS_ANALYST;
GRANT USAGE ON STREAMLIT PORTPILOT.SEMANTIC.PORTPILOT_APP TO ROLE PORTPILOT_CUSTOMER_SUCCESS;
GRANT USAGE ON STREAMLIT PORTPILOT.SEMANTIC.PORTPILOT_APP TO ROLE PORTPILOT_EXEC;
GRANT USAGE ON STREAMLIT PORTPILOT.SEMANTIC.PORTPILOT_APP TO ROLE PORTPILOT_AUDITOR;
```

---

## Application URL

- **Direct Snowsight App Link:**  
  `https://app.snowflake.com/TSNUGNW/GW48763/#/streamlit-apps/PORTPILOT.SEMANTIC.PORTPILOT_APP`
- **Submission Field ("Prototype Deployed Link"):**  
  `https://app.snowflake.com/TSNUGNW/GW48763/#/streamlit-apps/PORTPILOT.SEMANTIC.PORTPILOT_APP`
