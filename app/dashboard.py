import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ---------------------------------------------------------
# 1. Page Configuration & Data Loading
# ---------------------------------------------------------
st.set_page_config(
    page_title="India Economic Transformation & Trade (1960–2025)",
    page_icon="🇮🇳",
    layout="wide"
)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "india_econ_trade.parquet"

@st.cache_data
def query_data(sql_query: str) -> pd.DataFrame:
    con = duckdb.connect()
    return con.execute(sql_query).df()

if not DATA_PATH.exists():
    st.error(f"Processed file not found at `{DATA_PATH}`. Please run `python src/clean_data.py` first.")
    st.stop()

# ---------------------------------------------------------
# 2. Sidebar Controls
# ---------------------------------------------------------
st.sidebar.title("Filters & Policy Eras")
year_range = st.sidebar.slider("Select Year Range", min_value=1960, max_value=2025, value=(1960, 2025))
show_milestones = st.sidebar.checkbox("Show Key Policy Milestones", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Key Milestones:**\n"
    "- **1991:** Economic Liberalization & BoP Reform\n"
    "- **2008:** Global Financial Crisis\n"
    "- **2020:** COVID-19 Pandemic Shock"
)

# Helper to add milestone vertical lines
def add_policy_lines(fig):
    if show_milestones:
        milestones = [(1991, "1991 Reforms"), (2008, "2008 GFC"), (2020, "2020 COVID")]
        for yr, label in milestones:
            if year_range[0] <= yr <= year_range[1]:
                fig.add_vline(x=yr, line_dash="dash", line_color="gray", annotation_text=label, annotation_position="top left")
    return fig

# ---------------------------------------------------------
# 3. Header & Top-Line KPI Cards
# ---------------------------------------------------------
st.title("🇮🇳 India: Economic Transformation & Trade Analytics")
st.markdown("Exploring six decades of structural shift, trade openness, and export modernization using World Bank WDI data.")

# Fetch latest available KPIs within selected range
kpi_df = query_data(f"""
    SELECT "Indicator Code", Year, Value
    FROM '{DATA_PATH}'
    WHERE Year BETWEEN {year_range[0]} AND {year_range[1]}
""")

def get_latest_metric(code):
    sub = kpi_df[kpi_df["Indicator Code"] == code].sort_values("Year")
    if sub.empty:
        return None, None, None
    latest = sub.iloc[-1]
    prev = sub.iloc[-2] if len(sub) > 1 else latest
    return latest["Value"], int(latest["Year"]), latest["Value"] - prev["Value"]

gdp_pc, yr_gdp, diff_gdp = get_latest_metric("NY.GDP.PCAP.KD")
srv_share, yr_srv, diff_srv = get_latest_metric("NV.SRV.TOTL.ZS")
trd_share, yr_trd, diff_trd = get_latest_metric("NE.TRD.GNFS.ZS")
tech_exp, yr_tech, diff_tech = get_latest_metric("TX.VAL.TECH.MF.ZS")

col1, col2, col3, col4 = st.columns(4)
with col1:
    if gdp_pc:
        st.metric(f"GDP per Capita ({yr_gdp})", f"${gdp_pc:,.0f}", f"${diff_gdp:+,.0f} YoY", help="Constant 2015 US$")
with col2:
    if srv_share:
        st.metric(f"Services Share ({yr_srv})", f"{srv_share:.1f}%", f"{diff_srv:+.2f} pp", help="Value added (% of GDP)")
with col3:
    if trd_share:
        st.metric(f"Trade Openness ({yr_trd})", f"{trd_share:.1f}%", f"{diff_trd:+.2f} pp", help="Exports + Imports (% of GDP)")
with col4:
    if tech_exp:
        st.metric(f"High-Tech Exports ({yr_tech})", f"{tech_exp:.1f}%", f"{diff_tech:+.2f} pp", help="% of Manufactured Exports")

st.markdown("---")

# ---------------------------------------------------------
# 4. Analytical Tabs
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "1. Sectoral Shift",
    "2. Trade Openness & Tariffs",
    "3. High-Tech & External Flows",
    "4. Raw Data Explorer"
])

# --- TAB 1: Sectoral Transformation ---
with tab1:
    st.subheader("The Services-Led Structural Shift")
    st.write("Tracking how India transitioned from an agrarian economy directly into services while manufacturing stayed relatively flat.")
    
    sec_df = query_data(f"""
        SELECT Year,
               CASE "Indicator Code"
                   WHEN 'NV.AGR.TOTL.ZS' THEN 'Agriculture'
                   WHEN 'NV.IND.MANF.ZS' THEN 'Manufacturing'
                   WHEN 'NV.SRV.TOTL.ZS' THEN 'Services'
               END AS Sector,
               Value
        FROM '{DATA_PATH}'
        WHERE "Indicator Code" IN ('NV.AGR.TOTL.ZS', 'NV.IND.MANF.ZS', 'NV.SRV.TOTL.ZS')
          AND Year BETWEEN {year_range[0]} AND {year_range[1]}
        ORDER BY Year
    """)
    
    fig_sec = px.line(
        sec_df, x="Year", y="Value", color="Sector",
        labels={"Value": "Value Added (% of GDP)"},
        color_discrete_map={"Agriculture": "#2ca02c", "Manufacturing": "#ff7f0e", "Services": "#1f77b4"},
        template="plotly_white"
    )
    st.plotly_chart(add_policy_lines(fig_sec), use_container_width=True)

# --- TAB 2: Trade Openness & Tariffs ---
with tab2:
    st.subheader("Liberalization: Rising Trade vs. Falling Tariffs")
    col_a, col_b = st.columns(2)
    
    with col_a:
        trd_df = query_data(f"""
            SELECT Year,
                   CASE "Indicator Code"
                       WHEN 'NE.EXP.GNFS.ZS' THEN 'Exports (% of GDP)'
                       WHEN 'NE.IMP.GNFS.ZS' THEN 'Imports (% of GDP)'
                   END AS Metric,
                   Value
            FROM '{DATA_PATH}'
            WHERE "Indicator Code" IN ('NE.EXP.GNFS.ZS', 'NE.IMP.GNFS.ZS')
              AND Year BETWEEN {year_range[0]} AND {year_range[1]}
            ORDER BY Year
        """)
        fig_trd = px.area(trd_df, x="Year", y="Value", color="Metric",
                          title="Exports vs. Imports (% of GDP)", template="plotly_white")
        st.plotly_chart(add_policy_lines(fig_trd), use_container_width=True)

    with col_b:
        tar_df = query_data(f"""
            SELECT Year, Value
            FROM '{DATA_PATH}'
            WHERE "Indicator Code" = 'TM.TAX.MRCH.WM.AR.ZS'
              AND Year BETWEEN {year_range[0]} AND {year_range[1]}
            ORDER BY Year
        """)
        fig_tar = px.line(tar_df, x="Year", y="Value", markers=True,
                          title="Applied Weighted Mean Tariff Rate (%)",
                          labels={"Value": "Tariff Rate (%)"}, template="plotly_white")
        fig_tar.update_traces(line_color="#d62728")
        st.plotly_chart(add_policy_lines(fig_tar), use_container_width=True)

# --- TAB 3: High-Tech & External Flows ---
with tab3:
    st.subheader("Modern Exports, ICT Services & Capital Inflows")
    col_c, col_d = st.columns(2)
    
    with col_c:
        ict_df = query_data(f"""
            SELECT Year, Value / 1e9 AS Value_Billions
            FROM '{DATA_PATH}'
            WHERE "Indicator Code" = 'BX.GSR.CCIS.CD'
              AND Year BETWEEN {year_range[0]} AND {year_range[1]}
            ORDER BY Year
        """)
        fig_ict = px.bar(ict_df, x="Year", y="Value_Billions",
                         title="ICT Service Exports (Current US$ Billions)",
                         labels={"Value_Billions": "US$ Billions"}, template="plotly_white")
        st.plotly_chart(add_policy_lines(fig_ict), use_container_width=True)

    with col_d:
        fdi_rem_df = query_data(f"""
            SELECT Year,
                   CASE "Indicator Code"
                       WHEN 'BX.TRF.PWKR.DT.GD.ZS' THEN 'Personal Remittances (% of GDP)'
                       WHEN 'TX.VAL.TECH.MF.ZS' THEN 'High-Tech Exports (% of Mfg Exports)'
                   END AS Indicator,
                   Value
            FROM '{DATA_PATH}'
            WHERE "Indicator Code" IN ('BX.TRF.PWKR.DT.GD.ZS', 'TX.VAL.TECH.MF.ZS')
              AND Year BETWEEN {year_range[0]} AND {year_range[1]}
            ORDER BY Year
        """)
        fig_modern = px.line(fdi_rem_df, x="Year", y="Value", color="Indicator", markers=True,
                             title="Remittances vs. High-Tech Export Share", template="plotly_white")
        st.plotly_chart(add_policy_lines(fig_modern), use_container_width=True)

# --- TAB 4: Raw Data & SQL Query ---
with tab4:
    st.subheader("Filtered Dataset & Download")
    st.dataframe(kpi_df, use_container_width=True)
    csv_export = kpi_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Filtered CSV", data=csv_export, file_name="india_econ_filtered.csv", mime="text/csv")
