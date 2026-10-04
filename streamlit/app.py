import streamlit as st
import pandas as pd
import altair as alt

# Set page configuration
st.set_page_config(
    page_title="PortPilot AI | Operations Command Center",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling with Blue and Teal accents
st.markdown("""
<style>
    /* Global accents */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .callout-info {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 14px 16px;
        border-radius: 4px;
        margin: 14px 0;
        color: #1e3a8a;
    }
    .callout-warning {
        background-color: #fff7ed;
        border-left: 4px solid #f97316;
        padding: 14px 16px;
        border-radius: 4px;
        margin: 14px 0;
        color: #7c2d12;
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

# Query Helper with Caching
@st.cache_data(ttl=600, show_spinner=False)
def execute_query(_session, query_sql: str) -> pd.DataFrame:
    if _session is None:
        return pd.DataFrame()
    return _session.sql(query_sql).to_pandas()

# Title and Subtitle
st.markdown('<div class="main-header">PortPilot AI</div>', unsafe_allow_html=True)
st.markdown('<div class="main-header" style="font-size: 1.4rem; color: #0284c7; margin-top:-0.5rem;">Governed Supply-Chain Operations Command Center</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Operational analytics with planted-truth validation, data-quality safeguards, and role-aware access.</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚓ Navigation & Config")
    st.markdown("---")
    st.markdown("**Project:** PortPilot AI")
    st.markdown("**Challenge:** Supply Chain Ontology and Governed Conversational Analytics")
    st.markdown("**Dataset window:** 2026-01-05 to 2026-09-27")
    st.markdown("**Demo as-of date:** 2026-09-28")
    st.markdown("**Snowflake edition:** Standard")
    st.markdown("**Governance method:** Secure views using `IS_ROLE_IN_SESSION`")
    st.markdown("---")
    
    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.caption("Active Session Status:")
    if session is not None:
        st.success("Connected to Snowflake", icon="🟢")
    else:
        st.warning("Standalone Preview Mode (No active Snowpark session)", icon="🟡")

if session is None:
    st.info(
        "⚠️ **Snowflake Session Required:** This application is designed to run inside **Streamlit in Snowflake (SiS)**. "
        "When opened via Snowsight, the application automatically connects using `get_active_session()`."
    )

# Four Tabs Definition
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
    st.subheader("APAC Container Delivery & Network Performance")
    
    # Query metrics from Snowflake
    total_journeys_val = 798000
    total_events_val = 6948049
    week33_otd_val = 77.0
    otd_delta_val = -8.1
    
    otd_df = pd.DataFrame()
    
    if session is not None:
        try:
            # 1. Total Journeys
            j_df = execute_query(session, "SELECT COUNT(*) AS CNT FROM PORTPILOT.SEMANTIC.V_CONTAINER_JOURNEY")
            if not j_df.empty:
                total_journeys_val = int(j_df["CNT"].iloc[0])
            
            # 2. Total Events
            e_df = execute_query(session, "SELECT SUM(EVENT_COUNT) AS CNT FROM PORTPILOT.SEMANTIC.EVENT_VOLUME_DAILY")
            if not e_df.empty and pd.notnull(e_df["CNT"].iloc[0]):
                total_events_val = int(e_df["CNT"].iloc[0])
            
            # 3. OTD Trend Query
            otd_query = """
            SELECT
                ISO_WEEK,
                ROUND(100 * AVG(ON_TIME_DELIVERY), 1) AS OTD_PCT,
                COUNT(*) AS CONTAINERS
            FROM PORTPILOT.SEMANTIC.V_CONTAINER_JOURNEY
            WHERE TRADE_LANE IN ('APAC_DOMESTIC', 'NORTH_ASIA', 'TRANS_TASMAN')
              AND ISO_WEEK BETWEEN 30 AND 36
            GROUP BY ISO_WEEK
            ORDER BY ISO_WEEK;
            """
            otd_df = execute_query(session, otd_query)
            
            if not otd_df.empty and len(otd_df) >= 4:
                w33_row = otd_df[otd_df["ISO_WEEK"] == 33]
                w32_row = otd_df[otd_df["ISO_WEEK"] == 32]
                if not w33_row.empty and not w32_row.empty:
                    week33_otd_val = float(w33_row["OTD_PCT"].iloc[0])
                    week32_otd_val = float(w32_row["OTD_PCT"].iloc[0])
                    otd_delta_val = round(week33_otd_val - week32_otd_val, 1)
        except Exception as e:
            st.error(f"Error querying Executive Overview data from Snowflake: {str(e)}")
    else:
        # Fallback benchmark data for local preview
        otd_df = pd.DataFrame([
            {"ISO_WEEK": 30, "OTD_PCT": 84.6, "CONTAINERS": 38400},
            {"ISO_WEEK": 31, "OTD_PCT": 85.8, "CONTAINERS": 39100},
            {"ISO_WEEK": 32, "OTD_PCT": 85.1, "CONTAINERS": 38900},
            {"ISO_WEEK": 33, "OTD_PCT": 77.0, "CONTAINERS": 39500},
            {"ISO_WEEK": 34, "OTD_PCT": 82.7, "CONTAINERS": 38800},
            {"ISO_WEEK": 35, "OTD_PCT": 84.7, "CONTAINERS": 39200},
            {"ISO_WEEK": 36, "OTD_PCT": 86.0, "CONTAINERS": 39000},
        ])

    # Top metric cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Journeys", value=f"{total_journeys_val:,}")
    with col2:
        st.metric(label="Total Events", value=f"{total_events_val:,}")
    with col3:
        st.metric(label="Week-33 APAC OTD", value=f"{week33_otd_val:.1f}%")
    with col4:
        st.metric(
            label="OTD Change vs Week 32",
            value=f"{otd_delta_val:+.1f} pp",
            delta=f"{otd_delta_val:+.1f} pp",
            delta_color="inverse"
        )

    st.markdown("---")
    st.markdown("#### APAC On-Time Delivery Trend (ISO Weeks 30–36)")
    st.caption("APAC Cohort: `APAC_DOMESTIC`, `NORTH_ASIA`, `TRANS_TASMAN`")

    if not otd_df.empty:
        # Altair line chart with teal and blue styling
        base = alt.Chart(otd_df).encode(
            x=alt.X("ISO_WEEK:O", title="ISO Calendar Week (2026)"),
            y=alt.Y("OTD_PCT:Q", title="On-Time Delivery (%)", scale=alt.Scale(domain=[70, 95]))
        )
        
        line = base.mark_line(color="#0284c7", strokeWidth=3).encode()
        points = base.mark_circle(size=80, color="#0f766e").encode(
            tooltip=[
                alt.Tooltip("ISO_WEEK:O", title="ISO Week"),
                alt.Tooltip("OTD_PCT:Q", title="OTD %", format=".1f"),
                alt.Tooltip("CONTAINERS:Q", title="Volume", format=",")
            ]
        )
        
        # Benchmark threshold line at 85%
        rule = alt.Chart(pd.DataFrame({'y': [85.0]})).mark_rule(
            color='#94a3b8',
            strokeDash=[4, 4]
        ).encode(y='y:Q')
        
        chart = (rule + line + points).properties(height=340)
        st.altair_chart(chart, use_container_width=True)

    st.markdown(
        """
        <div class="callout-info">
            <strong>Key Finding:</strong> APAC OTD declined from 85.1% in week 32 to 77.0% in week 33, followed by recovery to 86.0% by week 36.
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------------------------------------------------
# TAB 2: Root-Cause Breakdown
# -------------------------------------------------------------
with tab2:
    st.subheader("Week-33 APAC Delay Driver Analysis")
    st.markdown("Analysis of delay events affecting APAC trade lanes during the week 33 performance anomaly.")
    
    causes_df = pd.DataFrame()
    if session is not None:
        try:
            cause_query = """
            SELECT
                CAUSE_CODE,
                COUNT(*) AS EVENT_COUNT,
                ROUND(SUM(DELAY_HOURS), 1) AS TOTAL_DELAY_HOURS
            FROM PORTPILOT.SEMANTIC.V_DELAY_EVENT
            WHERE ISO_WEEK = 33
              AND TRADE_LANE IN ('APAC_DOMESTIC', 'NORTH_ASIA', 'TRANS_TASMAN')
            GROUP BY CAUSE_CODE
            ORDER BY EVENT_COUNT DESC;
            """
            causes_df = execute_query(session, cause_query)
        except Exception as e:
            st.error(f"Error querying Root-Cause data from Snowflake: {str(e)}")
    else:
        causes_df = pd.DataFrame([
            {"CAUSE_CODE": "CONGESTION", "EVENT_COUNT": 4269, "TOTAL_DELAY_HOURS": 18240.5},
            {"CAUSE_CODE": "CUSTOMER_DOCUMENTATION", "EVENT_COUNT": 444, "TOTAL_DELAY_HOURS": 1920.0},
            {"CAUSE_CODE": "EQUIPMENT", "EVENT_COUNT": 405, "TOTAL_DELAY_HOURS": 1782.4}
        ])

    col_chart, col_table = st.columns([3, 2])
    
    with col_chart:
        st.markdown("#### Event Counts by Cause Code")
        if not causes_df.empty:
            bar_chart = alt.Chart(causes_df).mark_bar(color="#0e7490", cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("EVENT_COUNT:Q", title="Incident Event Count"),
                y=alt.Y("CAUSE_CODE:N", sort="-x", title="Root Cause Code"),
                tooltip=[
                    alt.Tooltip("CAUSE_CODE:N", title="Cause"),
                    alt.Tooltip("EVENT_COUNT:Q", title="Events", format=","),
                    alt.Tooltip("TOTAL_DELAY_HOURS:Q", title="Total Delay (Hours)", format=",.1f")
                ]
            ).properties(height=260)
            st.altair_chart(bar_chart, use_container_width=True)

    with col_table:
        st.markdown("#### Driver Details")
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
            <strong>Analyst Note:</strong> Congestion is the largest observed event-level driver in week 33, with additional customer-documentation and equipment incidents. These are event counts, not formal counterfactual attribution percentages.
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------------------------------------------------
# TAB 3: Data Quality Guard
# -------------------------------------------------------------
with tab3:
    st.subheader("Data Quality Telemetry: Rotterdam Terminal Feed Incident")
    st.markdown(
        "Monitoring feed ingestion completeness across terminal operating systems (TOS). "
        "Verifying whether downstream dwell shifts represent real operational degradation or feed suppression."
    )
    
    dq_df = pd.DataFrame()
    if session is not None:
        try:
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
        except Exception as e:
            st.error(f"Error querying Data Quality telemetry from Snowflake: {str(e)}")
    else:
        dq_df = pd.DataFrame([
            {"EVENT_DAY": "2026-08-31", "ROTTERDAM_GATE_OUT": 1120, "OTHER_GATE_OUT": 5387},
            {"EVENT_DAY": "2026-09-01", "ROTTERDAM_GATE_OUT": 0, "OTHER_GATE_OUT": 5410},
            {"EVENT_DAY": "2026-09-02", "ROTTERDAM_GATE_OUT": 0, "OTHER_GATE_OUT": 5422},
            {"EVENT_DAY": "2026-09-03", "ROTTERDAM_GATE_OUT": 0, "OTHER_GATE_OUT": 5508},
            {"EVENT_DAY": "2026-09-04", "ROTTERDAM_GATE_OUT": 1106, "OTHER_GATE_OUT": 5458},
        ])

    # Incident Warning Callout
    st.markdown(
        """
        <div class="callout-warning">
            ⚠️ <strong>Data completeness incident detected.</strong> Rotterdam GATE_OUT volume is zero from September 1 through September 3, 2026, while other source feeds remain stable. Do not interpret the resulting dwell anomaly as an operational regression.
        </div>
        """,
        unsafe_allow_html=True
    )

    if not dq_df.empty:
        # Prepare data for grouped chart
        melted_dq = dq_df.melt(
            id_vars=["EVENT_DAY"],
            value_vars=["ROTTERDAM_GATE_OUT", "OTHER_GATE_OUT"],
            var_name="SOURCE_FEED",
            value_name="GATE_OUT_VOLUME"
        )
        melted_dq["FEED_LABEL"] = melted_dq["SOURCE_FEED"].map({
            "ROTTERDAM_GATE_OUT": "TOS_ROTTERDAM (Audited Terminal)",
            "OTHER_GATE_OUT": "Other Network Terminals"
        })

        dq_chart = alt.Chart(melted_dq).mark_bar().encode(
            x=alt.X("EVENT_DAY:O", title="Event Date (UTC)"),
            y=alt.Y("GATE_OUT_VOLUME:Q", title="Daily Gate-Out Events"),
            color=alt.Color(
                "FEED_LABEL:N",
                scale=alt.Scale(
                    domain=["TOS_ROTTERDAM (Audited Terminal)", "Other Network Terminals"],
                    range=["#f97316", "#0284c7"]
                ),
                title="Feed Source"
            ),
            xOffset="FEED_LABEL:N",
            tooltip=[
                alt.Tooltip("EVENT_DAY:O", title="Date"),
                alt.Tooltip("FEED_LABEL:N", title="Source"),
                alt.Tooltip("GATE_OUT_VOLUME:Q", title="Volume", format=",")
            ]
        ).properties(height=320)

        st.altair_chart(dq_chart, use_container_width=True)

        st.markdown("#### Telemetry Log Table")
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
    st.subheader("Role-Based Governed Access Verification")
    st.markdown(
        "Demonstrating active role inheritance and column-level masking enforced via Snowflake secure views."
    )

    gov_role = "PORTPILOT_ENGINEER"
    rows_visible = 798000
    customers_visible = 20
    sample_email = "pacific-retail@example.invalid"

    if session is not None:
        try:
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
                gov_role = str(gov_df["ACTIVE_ROLE"].iloc[0])
                rows_visible = int(gov_df["ROWS_VISIBLE"].iloc[0])
                customers_visible = int(gov_df["CUSTOMERS_VISIBLE"].iloc[0])
                sample_email = str(gov_df["SAMPLE_EMAIL"].iloc[0])
        except Exception as e:
            st.error(f"Error querying Governance status from Snowflake: {str(e)}")

    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    with col_g1:
        st.metric(label="Active Session Role", value=gov_role)
    with col_g2:
        st.metric(label="Total Visible Rows", value=f"{rows_visible:,}")
    with col_g3:
        st.metric(label="Distinct Visible Customers", value=f"{customers_visible}")
    with col_g4:
        st.metric(label="Sample Contact Email", value=sample_email)

    st.markdown("---")
    st.markdown("#### Governance Policy Rules & Role Specifications")
    
    st.markdown("""
    - **`PORTPILOT_OPS_ANALYST`**: Full cross-lane operational visibility. Sees all **20 customers** with unmasked synthetic contact emails.
    - **`PORTPILOT_CUSTOMER_SUCCESS`**: Scoped row-level access via `PORTPILOT.GOVERNANCE.CUSTOMER_ACCESS`. Sees only **3 assigned customers**, with `CONTACT_EMAIL` masked as `***MASKED***`.
    - **`PORTPILOT_ENGINEER` / `PORTPILOT_EXEC` / `PORTPILOT_AUDITOR`**: Inherit administrative, executive, and compliance-level access respectively.
    """)

    st.markdown("""
    <div class="callout-info">
        <strong>Session Enforcement Note:</strong> The application does not attempt dynamic <code>USE ROLE</code> execution inside Streamlit.
        Governance is inherited directly from the active Snowflake session and the secure view definition (<code>PORTPILOT.SEMANTIC.V_CONTAINER_JOURNEY</code>) using <code>IS_ROLE_IN_SESSION()</code>.
        To test different policy views, launch or run the Streamlit app under the corresponding Snowflake functional role.
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown(
    '<div class="footer-text">PortPilot AI | Governed analytics on Snowflake | Synthetic hackathon dataset</div>',
    unsafe_allow_html=True
)
