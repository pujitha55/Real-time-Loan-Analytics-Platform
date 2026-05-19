# -*- coding: utf-8 -*-
# ======================================================
# 💫 Real-Time Loan Analytics Dashboard (Refined & Readable)
# ======================================================

import streamlit as st
import mysql.connector
import pandas as pd
from configparser import ConfigParser
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
import datetime
import time
import numpy as np

# ======================================================
# 1️⃣ Read MySQL Config
# ======================================================
def read_config():
    config_parser = ConfigParser()
    base_dir = Path(__file__).resolve().parent
    config_path = base_dir / "config" / "config.ini"

    if not config_path.exists():
        st.error(f"❌ Config file not found: {config_path}")
        st.stop()

    config_parser.read(config_path)
    if not config_parser.has_section("mysql"):
        st.error("❌ [mysql] section missing in config.ini.")
        st.stop()

    return {key: value for key, value in config_parser.items("mysql")}


# ======================================================
# 2️⃣ MySQL Connection
# ======================================================
def create_mysql_connection():
    mysql_config = read_config()
    try:
        conn = mysql.connector.connect(
            host=mysql_config["host"],
            database=mysql_config["database"],
            user=mysql_config["user"],
            password=mysql_config["password"],
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"🚫 MySQL connection error: {err}")
        return None


# ======================================================
# 3️⃣ Fetch Loan Data
# ======================================================
def get_loan_data():
    try:
        conn = create_mysql_connection()
        if not conn:
            return pd.DataFrame()
        df = pd.read_sql("SELECT * FROM loan_events ORDER BY timestamp DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching loan data: {e}")
        return pd.DataFrame()


# ======================================================
# 4️⃣ Compute Summary
# ======================================================
def get_summary(df):
    summary = {}
    summary["total_loans"] = df.shape[0]
    summary["total_amount"] = df["amount"].sum()
    summary["status_count"] = df["status"].value_counts().to_dict()
    summary["amount_by_status"] = df.groupby("status")["amount"].sum().to_dict()
    summary["avg_loan"] = summary["total_amount"] / summary["total_loans"] if summary["total_loans"] > 0 else 0
    summary["approval_rate"] = (
        (summary["status_count"].get("approved", 0) / summary["total_loans"]) * 100
        if summary["total_loans"] > 0 else 0
    )
    return summary


# ======================================================
# 5️⃣ Streamlit Dashboard
# ======================================================
def loan_dashboard():
    st.set_page_config(page_title="💫 Real-Time Loan Analytics Dashboard", layout="wide")
    st_autorefresh(interval=10000, key="refresh")

    # ===================== CSS =====================
    st.markdown("""
        <style>
        body, .block-container, [data-testid="stSidebar"] {
            background-color: #000000;
            color: #FFFFFF;
        }
        h1 {
            color: #00E6FF;
            text-align: center;
            font-weight: 900;
            font-size: 42px !important;
            text-shadow: 0px 0px 25px #00FFFF;
        }
        .metric-container {
            background: linear-gradient(145deg, #0D0D0D, #111111);
            border: 1px solid #00E6FF;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0px 0px 20px #00FFFF33;
        }
        .metric-label {
            font-size: 17px;
            color: #00E6FF;
            font-weight: 600;
        }
        .metric-value {
            font-size: 30px;
            color: #FFFFFF;
            font-weight: 800;
        }
        .live-indicator {
            width: 10px; height: 10px;
            background-color: #00FF7F;
            border-radius: 50%;
            display: inline-block;
            margin-right: 6px;
            box-shadow: 0 0 10px #00FF7F;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% {opacity: 1; transform: scale(1);}
            50% {opacity: 0.5; transform: scale(1.4);}
            100% {opacity: 1; transform: scale(1);}
        }
        table {
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # ===================== Header =====================
    st.markdown("<h1>🏦 Real-Time Loan Analytics Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:#AAAAAA;'>"
        "<span class='live-indicator'></span> Streaming live loan data from Kafka → MySQL → Streamlit"
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='border:1px solid #00E6FF;'>", unsafe_allow_html=True)

    # ===================== Data =====================
    loan_data = get_loan_data()
    if loan_data.empty:
        st.warning("⚠️ Waiting for live data...")
        components.html("<center><img src='https://i.gifer.com/YCZH.gif' width='150'></center>", height=200)
        st.stop()

    if "timestamp" in loan_data.columns:
        loan_data["date"] = pd.to_datetime(loan_data["timestamp"], unit="s")

    # ===================== Filters =====================
    st.sidebar.header("🔎 Filters")
    statuses = loan_data["status"].unique().tolist()
    selected_status = st.sidebar.multiselect("Loan Status", statuses, default=statuses)
    min_amt, max_amt = float(loan_data["amount"].min()), float(loan_data["amount"].max())
    amount_range = st.sidebar.slider("Loan Amount Range", min_amt, max_amt, (min_amt, max_amt))

    filtered_data = loan_data[
        (loan_data["status"].isin(selected_status)) &
        (loan_data["amount"].between(amount_range[0], amount_range[1]))
    ]
    summary = get_summary(filtered_data)

    # ===================== KPIs (3 per row) =====================
    st.markdown("### 📈 Key Performance Indicators")

    kpi_values = [
        ("💳 Total Loans", f"{summary['total_loans']:,}"),
        ("💰 Total Amount", f"{summary['total_amount']:,.0f}"),
        ("✅ Approved", f"{summary['status_count'].get('approved', 0):,}"),
        ("⏳ Pending", f"{summary['status_count'].get('pending', 0):,}"),
        ("📊 Approval Rate", f"{summary['approval_rate']:.2f}%"),
        ("💸 Avg Loan", f"{summary['avg_loan']:,.0f}")
    ]

    for i in range(0, len(kpi_values), 3):
        cols = st.columns(3)
        for j, (label, value) in enumerate(kpi_values[i:i+3]):
            cols[j].markdown(
                f"<div class='metric-container'><div class='metric-label'>{label}</div>"
                f"<div class='metric-value'>{value}</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ===================== Charts =====================

    # Loan Amount by Status
    st.subheader("💵 Loan Amount by Status")
    if summary["amount_by_status"]:
        color_map = {"approved": "#00FF7F", "pending": "#FFA500", "rejected": "#FF007F"}
        fig = px.bar(
            x=list(summary["amount_by_status"].keys()),
            y=list(summary["amount_by_status"].values()),
            text=list(summary["amount_by_status"].values()),
            color=list(summary["amount_by_status"].keys()),
            color_discrete_map=color_map,
            labels={"x": "Status", "y": "Loan Amount"},
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(
            plot_bgcolor="#000000",
            paper_bgcolor="#000000",
            font=dict(color="#FFFFFF", size=14),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Loan Count Pie Chart
    st.subheader("📊 Loan Count by Status")
    if summary["status_count"]:
        fig2 = px.pie(
            names=list(summary["status_count"].keys()),
            values=list(summary["status_count"].values()),
            color=list(summary["status_count"].keys()),
            color_discrete_map=color_map,
            hole=0.4,
        )
        fig2.update_layout(
            plot_bgcolor="#000000",
            paper_bgcolor="#000000",
            font=dict(color="#FFFFFF"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Average Loan Trend
    st.subheader("📈 Average Loan Amount Over Time")
    if "date" in loan_data.columns:
        avg_trend = loan_data.groupby(loan_data["date"].dt.date)["amount"].mean().reset_index()
        fig_trend = px.line(avg_trend, x="date", y="amount", markers=True, color_discrete_sequence=["#00FFFF"])
        fig_trend.update_layout(plot_bgcolor="#000000", paper_bgcolor="#000000", font=dict(color="#FFFFFF"))
        st.plotly_chart(fig_trend, use_container_width=True)

    # Top Borrowers
    st.subheader("🏆 Top 5 Borrowers by Loan Amount")
    top_borrowers = loan_data.sort_values(by="amount", ascending=False).head(5)
    st.dataframe(top_borrowers[["user_id", "amount", "status"]].style.format({"amount": "{:,.2f}"}), use_container_width=True)

    # Detailed Table
    with st.expander("📋 View Detailed Loan Data"):
        search_term = st.text_input("🔍 Search by Loan ID or User ID:")
        df_display = filtered_data.copy()
        if search_term:
            df_display = df_display[
                df_display["loan_id"].str.contains(search_term, case=False) |
                df_display["user_id"].str.contains(search_term, case=False)
            ]
        st.dataframe(df_display[["loan_id", "user_id", "amount", "status", "date"]].style.format({"amount": "{:,.2f}"}), use_container_width=True)

    # Footer
    st.markdown("<hr style='border:1px solid #00E6FF;'>", unsafe_allow_html=True)
    st.caption(f"🔄 Last refreshed: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ======================================================
if __name__ == "__main__":
    loan_dashboard()
