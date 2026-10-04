import streamlit as st
import pandas as pd
import altair as alt

# Set page configuration
st.set_page_config(
    page_title="PortPilot AI | Governed Operations Command Center",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling with Blue and Teal accents
st.markdown("""
<style>
    /* Global layout & typography */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.35rem;
        font-weight: 600;
        color: #0284c7;
        margin-bottom: 0.4rem;
    }
    .app-description {
        font-size: 1.0rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .callout-info {
        background-color: #eff6ff;
        border-left: 4px solid #0284c7;
        padding: 14px 16px;
        border-radius: 4px;
        margin: 14px 0;
        color: #0c4a6e;
        font-size: 0.95rem;
    }
    .callout-warning {
        background-color: #fff7ed;
        border-left: 4px solid #ea580c;
        padding: 14px 16px;
        border-radius: 4px;
        margin: 14px 0;
        color: #7c2d12;
        font-size: 0.95rem;
    }
    .footer-text {
        font-size: 0.85rem;
        color: #64748b;
        text-align: center;
        border-top: 1px solid #e2e8f0;
        padding-top: 20px;
        margin-top: 40px;
    }
</style>
""", unsafe_allow_html=True)

# Acquire active Snowflake session
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except Exception:
    session = None

# Query Helper with Caching (TTL = 600 seconds)
@st.cache_data(ttl=600, show_spinner=False)
def execute_query(_session, query_sql: str) -> pd.DataFrame:
    if _session is None:
        return pd.DataFrame()
    return _session.sql(query_sql).to_pandas()

# Header: Title, Subtitle, Description
st.markdown('<div class="main-title">PortPilot AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Governed Supply-Chain Operations Command Center</div>', unsafe_allow_html=True)
st.markdown('<div class="app-description">Operational analytics with planted-truth validation, data-quality safeguards, and role-aware access.</div>', unsafe_allow_html=True)

# Determine Current Snowflake Role
current_role = "PORTPILOT_ENGINEER"
if session is not None:
    try:
        role_df = execute_query(session, "SELECT CURRENT_ROLE() AS ROLE_NAME")
        if not role_df.empty and pd.notnull(role_df["ROLE_NAME"].iloc[0]):
            current_role = str(role_df["ROLE_NAME"].iloc[0])
    except Exception:
        pass

# App Sidebar
with st.sidebar:
    st.title("⚓ Navigation & Config")
    st.markdown("---")
    st.markdown("**Project:** PortPilot AI")
    st.markdown("**Challenge:** Supply Chain Ontology and Governed Conversational Analytics")
    st.markdown("**Dataset window:** 2026-01-05 to 2026-09-27")
    st.markdown("**Demo as-of date:** 2026-09-28")
    st.markdown("**Snowflake edition:** Standard")
    st.markdown("**Governance method:** Secure views using IS_ROLE_IN_SESSION")
    st.markdown(f"**Current Snowflake role:** `{current_role}`")
    st.markdown("---")
    
    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.caption("Active Session Status:")
    if session is not None:
        st.success(f"Connected to Snowflake (`{current_role}`)", icon="🟢")
    else:
        st.warning("Standalone Preview Mode (No active Snowpark session)", icon="🟡")

if session is None:
    st.info(
        "ℹ️ **Snowflake Session Required:** This application is configured to run natively inside "
        "**Streamlit in Snowflake (SiS)** using `get_active_session()`. Benchmark preview data is displayed below."
    )

# Four Tabs Layout
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Executive Overview",
    "🔍 Root-Cause Breakdown",
    "🛡️ Data Quality Guard",
    "🔒 Governance"
])

# -------------------------------------------------------------
# TAB 1: Executive Overview
# -------------------------------------------------------------
with tab1:
    st.subheader("Executive Overview: APAC Container Delivery Performance")
    
    total_journeys_val = 798000
    week33_otd_val = 77.0
    week32_otd_val = 85.1
    otd_delta_val = -8.1
    otd_df = pd.DataFrame()
    
    try:
        if session is not None:
            # 1. Total Journeys
            j_df = execute_query(session, "SELECT COUNT(*) AS CNT FROM PORTPILOT.SEMANTIC.V_CONTAINER_JOURNEY")
            if not j_df.empty and pd.notnull(j_df["CNT"].iloc[0]):
                total_journeys_val = int(j_df["CNT"].iloc[0])
            
            # 2. Weekly OTD Query
            otd_query = """
            SELECT
                ISO_WEEK,
                ROUND(100 * AVG(ON_TIME_DELIVERY), 1) AS OTD_PCT,
                COUNT(*) AS CONTAINERS
            FROM PORTPILOT.SEMANTIC.V_CONTAINER_JOURNEY
            WHERE TRADE_LANE IN (
              'APAC_DOMESTIC',
              'NORTH_ASIA',
              'TRANS_TASMAN'
            )
              AND ISO_WEEK BETWEEN 30 AND 36
            GROUP BY ISO_WEEK
            ORDER BY ISO_WEEK;
            """
            otd_df = execute_query(session, otd_query)
            
            if not otd_df.empty and "ISO_WEEK" in otd_df.columns and "OTD_PCT" in otd_df.columns:
                w33_match = otd_df[otd_df["ISO_WEEK"] == 33]
                w32_match = otd_df[otd_df["ISO_WEEK"] == 32]
                if not w33_match.empty:
                    week33_otd_val = float(w33_match["OTD_PCT"].iloc[0])
                if not w32_match.empty:
                    week32_otd_val = float(w32_match["OTD_PCT"].iloc[0])
                otd_delta_val = round(week33_otd_val - week32_otd_val, 1)
        else:
            otd_df = pd.DataFrame([
                {"ISO_WEEK": 30, "OTD_PCT": 84.6, "CONTAINERS": 38412},
                {"ISO_WEEK": 31, "OTD_PCT": 85.8, "CONTAINERS": 39088},
                {"ISO_WEEK": 32, "OTD_PCT": 85.1, "CONTAINERS": 38945},
                {"ISO_WEEK": 33, "OTD_PCT": 77.0, "CONTAINERS": 39520},
                {"ISO_WEEK": 34, "OTD_PCT": 82.7, "CONTAINERS": 38814},
                {"ISO_WEEK": 35, "OTD_PCT": 84.7, "CONTAINERS": 39180},
                {"ISO_WEEK": 36, "OTD_PCT": 86.0, "CONTAINERS": 39041},
            ])
    except Exception as e:
        st.error(f"Error loading Executive Overview data: {str(e)}")

    # 4 Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(label="Total journeys", value=f"{total_journeys_val:,}")
    with c2:
        st.metric(label="Week-33 APAC OTD", value=f"{week33_otd_val:.1f}%")
    with c3:
        st.metric(label="Week-32 APAC OTD", value=f"{week32_otd_val:.1f}%")
    with c4:
        st.metric(
            label="Week-33 change versus week 32",
            value=f"{otd_delta_val:+.1f} pp",
            delta=f"{otd_delta_val:+.1f} pp",
            delta_color="inverse"
        )

    st.markdown("---")
    st.markdown("#### APAC On-Time Delivery Percentage by ISO Week (Weeks 30–36)")
    st.caption("Cohort: `TRADE_LANE IN ('APAC_DOMESTIC', 'NORTH_ASIA', 'TRANS_TASMAN')`")

    if not otd_df.empty and "ISO_WEEK" in otd_df.columns and "OTD_PCT" in otd_df.columns:
        base = alt.Chart(otd_df).encode(
            x=alt.X("ISO_WEEK:O", title="ISO Week (2026)"),
            y=alt.Y("OTD_PCT:Q", title="On-Time Delivery (%)", scale=alt.Scale(domain=[70, 95]))
        )
        line = base.mark_line(color="#0284c7", strokeWidth=3).encode()
        points = base.mark_circle(size=80, color="#0f766e").encode(
            tooltip=[
                alt.Tooltip("ISO_WEEK:O", title="ISO Week"),
                alt.Tooltip("OTD_PCT:Q", title="OTD %", format=".1f"),
                alt.Tooltip("CONTAINERS:Q", title="Containers", format=",")
            ]
        )
        threshold = alt.Chart(pd.DataFrame({'y': [85.0]})).mark_rule(
            color='#94a3b8',
            strokeDash=[4, 4]
        ).encode(y='y:Q')
        
        otd_chart = (threshold + line + points).properties(height=320)
        st.altair_chart(otd_chart, use_container_width=True)

        st.markdown("#### Weekly Performance Data Table")
        st.dataframe(
            otd_df.style.format({
                "OTD_PCT": "{:.1f}%",
                "CONTAINERS": "{:,}"
            }),
            use_container_width=True,
            hide_index=True
        )

    st.markdown(
        """
        <div class="callout-info">
            <strong>Observation:</strong> APAC OTD declined from 85.1% in week 32 to 77.0% in week 33 before recovering to 86.0% in week 36.
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------------------------------------------------
# TAB 2: Root-Cause Breakdown
# -------------------------------------------------------------
with tab2:
    st.subheader("Root-Cause Breakdown: Week-33 Delay Drivers")
    st.markdown("Evaluation of delay event frequencies across the APAC cohort during the week-33 performance drop.")
    
    causes_df = pd.DataFrame()
    try:
        if session is not None:
            cause_query = """
            SELECT
                CAUSE_CODE,
                COUNT(*) AS EVENT_COUNT,
                ROUND(SUM(DELAY_HOURS), 1) AS TOTAL_DELAY_HOURS
            FROM PORTPILOT.SEMANTIC.V_DELAY_EVENT
            WHERE ISO_WEEK = 33
              AND TRADE_LANE IN (
                'APAC_DOMESTIC',
                'NORTH_ASIA',
                'TRANS_TASMAN'
              )
            GROUP BY CAUSE_CODE
            ORDER BY EVENT_COUNT DESC;
            """
            causes_df = execute_query(session, cause_query)
        else:
            causes_df = pd.DataFrame([
                {"CAUSE_CODE": "CONGESTION", "EVENT_COUNT": 4269, "TOTAL_DELAY_HOURS": 18240.5},
                {"CAUSE_CODE": "CUSTOMER_DOCUMENTATION", "EVENT_COUNT": 444, "TOTAL_DELAY_HOURS": 1920.0},
                {"CAUSE_CODE": "EQUIPMENT", "EVENT_COUNT": 405, "TOTAL_DELAY_HOURS": 1782.4}
            ])
    except Exception as e:
        st.error(f"Error loading Root-Cause Breakdown: {str(e)}")

    col_bchart, col_btable = st.columns([3, 2])
    with col_bchart:
        st.markdown("#### Incident Events by Cause Code")
        if not causes_df.empty and "CAUSE_CODE" in causes_df.columns and "EVENT_COUNT" in causes_df.columns:
            bar_chart = alt.Chart(causes_df).mark_bar(color="#0e7490", cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("EVENT_COUNT:Q", title="Event Count"),
                y=alt.Y("CAUSE_CODE:N", sort="-x", title="Cause Code"),
                tooltip=[
                    alt.Tooltip("CAUSE_CODE:N", title="Cause"),
                    alt.Tooltip("EVENT_COUNT:Q", title="Events", format=","),
                    alt.Tooltip("TOTAL_DELAY_HOURS:Q", title="Delay Hours", format=",.1f")
                ]
            ).properties(height=260)
            st.altair_chart(bar_chart, use_container_width=True)

    with col_btable:
        st.markdown("#### Cause Driver Table")
        if not causes_df.empty:
            st.dataframe(
                causes_df.style.format({
                    "EVENT_COUNT": "{:,}",
                    "TOTAL_DELAY_HOURS": "{:,.1f}"
                }),
                use_container_width=True,
                hide_index=True
            )

    st.markdown(
        """
        <div class="callout-info">
            <strong>Driver Interpretation:</strong> Congestion is the largest observed event-level driver in week 33, with additional customer-documentation and equipment incidents. These are event counts and not formal counterfactual attribution percentages.
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------------------------------------------------
# TAB 3: Data Quality Guard
# -------------------------------------------------------------
with tab3:
    st.subheader("Data Quality Guard: Rotterdam TOS Ingestion Telemetry")
    st.markdown(
        "Real-time volume validation across terminal operating systems to detect upstream telemetry dropouts "
        "and prevent false operational regressions."
    )

    dq_df = pd.DataFrame()
    try:
        if session is not None:
            dq_query = """
            SELECT
                EVENT_DAY,
                SUM(
                    IFF(
                        SOURCE_SYSTEM = 'TOS_ROTTERDAM'
                        AND EVENT_TYPE = 'GATE_OUT',
                        EVENT_COUNT,
                        0
                    )
                ) AS ROTTERDAM_GATE_OUT,
                SUM(
                    IFF(
                        SOURCE_SYSTEM <> 'TOS_ROTTERDAM'
                        AND EVENT_TYPE = 'GATE_OUT',
                        EVENT_COUNT,
                        0
                    )
                ) AS OTHER_GATE_OUT
            FROM PORTPILOT.SEMANTIC.EVENT_VOLUME_DAILY
            WHERE EVENT_DAY BETWEEN '2026-08-31' AND '2026-09-04'
            GROUP BY EVENT_DAY
            ORDER BY EVENT_DAY;
            """
            dq_df = execute_query(session, dq_query)
        else:
            dq_df = pd.DataFrame([
                {"EVENT_DAY": "2026-08-31", "ROTTERDAM_GATE_OUT": 1120, "OTHER_GATE_OUT": 5387},
                {"EVENT_DAY": "2026-09-01", "ROTTERDAM_GATE_OUT": 0, "OTHER_GATE_OUT": 5410},
                {"EVENT_DAY": "2026-09-02", "ROTTERDAM_GATE_OUT": 0, "OTHER_GATE_OUT": 5422},
                {"EVENT_DAY": "2026-09-03", "ROTTERDAM_GATE_OUT": 0, "OTHER_GATE_OUT": 5508},
                {"EVENT_DAY": "2026-09-04", "ROTTERDAM_GATE_OUT": 1106, "OTHER_GATE_OUT": 5458},
            ])
    except Exception as e:
        st.error(f"Error loading Data Quality Telemetry: {str(e)}")

    # Prominent Warning Banner if zero volume detected
    rotterdam_zeros = False
    if not dq_df.empty and "ROTTERDAM_GATE_OUT" in dq_df.columns and "OTHER_GATE_OUT" in dq_df.columns:
        zero_rows = dq_df[(dq_df["ROTTERDAM_GATE_OUT"] == 0) & (dq_df["OTHER_GATE_OUT"] > 0)]
        if not zero_rows.empty:
            rotterdam_zeros = True

    if rotterdam_zeros:
        st.markdown(
            """
            <div class="callout-warning">
                ⚠️ <strong>Data completeness incident detected.</strong> Rotterdam GATE_OUT volume is zero from September 1 through September 3, 2026, while other source feeds remain stable. Do not interpret the resulting dwell anomaly as an operational regression.
            </div>
            """,
            unsafe_allow_html=True
        )

    if not dq_df.empty and "EVENT_DAY" in dq_df.columns:
        melted_dq = dq_df.melt(
            id_vars=["EVENT_DAY"],
            value_vars=["ROTTERDAM_GATE_OUT", "OTHER_GATE_OUT"],
            var_name="SOURCE_FEED",
            value_name="GATE_OUT_VOLUME"
        )
        melted_dq["FEED_NAME"] = melted_dq["SOURCE_FEED"].map({
            "ROTTERDAM_GATE_OUT": "TOS_ROTTERDAM (Audited)",
            "OTHER_GATE_OUT": "Other Network Terminals"
        })

        dq_chart = alt.Chart(melted_dq).mark_bar().encode(
            x=alt.X("EVENT_DAY:O", title="Event Date (UTC)"),
            y=alt.Y("GATE_OUT_VOLUME:Q", title="Gate-Out Event Volume"),
            color=alt.Color(
                "FEED_NAME:N",
                scale=alt.Scale(
                    domain=["TOS_ROTTERDAM (Audited)", "Other Network Terminals"],
                    range=["#ea580c", "#0284c7"]
                ),
                title="Feed Source"
            ),
            xOffset="FEED_NAME:N",
            tooltip=[
                alt.Tooltip("EVENT_DAY:O", title="Date"),
                alt.Tooltip("FEED_NAME:N", title="Source"),
                alt.Tooltip("GATE_OUT_VOLUME:Q", title="Events", format=",")
            ]
        ).properties(height=300)
        st.altair_chart(dq_chart, use_container_width=True)

        st.markdown("#### Ingestion Telemetry Table")
        st.dataframe(
            dq_df.style.format({
                "ROTTERDAM_GATE_OUT": "{:,}",
                "OTHER_GATE_OUT": "{:,}"
            }),
            use_container_width=True,
            hide_index=True
        )

# -------------------------------------------------------------
# TAB 4: Governance
# -------------------------------------------------------------
with tab4:
    st.subheader("Role-Based Governance & Policy Verification")
    st.markdown(
        "Live inspection of active Snowflake session role, visible row partitions, and column-level email masking "
        "enforced via `PORTPILOT.SEMANTIC.V_CONTAINER_JOURNEY`."
    )

    active_role_val = current_role
    rows_visible_val = 798000
    customers_visible_val = 20
    sample_email_val = "pacific-retail@example.invalid"

    try:
        if session is not None:
            gov_query = """
            SELECT
                CURRENT_ROLE() AS ACTIVE_ROLE,
                COUNT(*) AS ROWS_VISIBLE,
                COUNT(DISTINCT CUSTOMER_ID) AS CUSTOMERS_VISIBLE,
                MAX(CONTACT_EMAIL) AS SAMPLE_EMAIL
            FROM PORTPILOT.SEMANTIC.V_CONTAINER_JOURNEY;
            """
            gov_df = execute_query(session, gov_query)
            if not gov_df.empty:
                if "ACTIVE_ROLE" in gov_df.columns and pd.notnull(gov_df["ACTIVE_ROLE"].iloc[0]):
                    active_role_val = str(gov_df["ACTIVE_ROLE"].iloc[0])
                if "ROWS_VISIBLE" in gov_df.columns and pd.notnull(gov_df["ROWS_VISIBLE"].iloc[0]):
                    rows_visible_val = int(gov_df["ROWS_VISIBLE"].iloc[0])
                if "CUSTOMERS_VISIBLE" in gov_df.columns and pd.notnull(gov_df["CUSTOMERS_VISIBLE"].iloc[0]):
                    customers_visible_val = int(gov_df["CUSTOMERS_VISIBLE"].iloc[0])
                if "SAMPLE_EMAIL" in gov_df.columns and pd.notnull(gov_df["SAMPLE_EMAIL"].iloc[0]):
                    sample_email_val = str(gov_df["SAMPLE_EMAIL"].iloc[0])
    except Exception as e:
        st.error(f"Error loading Governance verification: {str(e)}")

    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    with col_g1:
        st.metric(label="Active Role", value=active_role_val)
    with col_g2:
        st.metric(label="Visible Rows", value=f"{rows_visible_val:,}")
    with col_g3:
        st.metric(label="Visible Customers", value=f"{customers_visible_val}")
    with col_g4:
        st.metric(label="Sample Email Result", value=sample_email_val)

    st.markdown("---")
    st.markdown("#### Governance Policy Rules & Role Specifications")
    st.markdown("""
    - **`PORTPILOT_OPS_ANALYST`**: Full cross-lane operational visibility. Sees all **20 customers** with unmasked synthetic contact emails.
    - **`PORTPILOT_CUSTOMER_SUCCESS`**: Scoped row-level access via `PORTPILOT.GOVERNANCE.CUSTOMER_ACCESS`. Sees only **3 assigned customers**, with `CONTACT_EMAIL` masked as `***MASKED***`.
    - **`PORTPILOT_ENGINEER` / `PORTPILOT_EXEC` / `PORTPILOT_AUDITOR`**: Inherit administrative, executive, and compliance-level access respectively.
    """)

    st.markdown("""
    <div class="callout-info">
        <strong>Session Governance Architecture:</strong> The application inherits access from the active Snowflake session. The same governed view returns different results under different functional roles.
        The application does not attempt dynamic role switching internally; role testing is performed by launching the app or opening Snowsight under the respective functional roles.
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown(
    '<div class="footer-text">PortPilot AI | Governed analytics on Snowflake | Synthetic hackathon dataset</div>',
    unsafe_allow_html=True
)
