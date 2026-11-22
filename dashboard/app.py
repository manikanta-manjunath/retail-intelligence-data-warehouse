"""Retail Intelligence Control Center - Modern ArgoLogics-inspired Operations Dashboard.
Engineered for fault-tolerance across all data states, missing artifacts, and offline scenarios.
"""
import json
import sys
from pathlib import Path

# Streamlit executes this file with dashboard/ as sys.path[0].
# Add the repository root before importing the local src package.
APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics.forecasting import complete_weeks, forecast, minimum_history_weeks
from src.utils.config import PROJECT_ROOT, app_config

REPORTS = PROJECT_ROOT / "reports" / "generated" / "analytics"

# ArgoLogics Brand Palette
COLOR_BG = "#EDECF1"
COLOR_CHARCOAL = "#0C0D0D"
COLOR_EMERALD = "#19C853"
COLOR_EMERALD_LIGHT = "#E8F9EE"
COLOR_CARD = "#FFFFFF"
COLOR_MUTED = "#7E7E89"
COLOR_BORDER = "rgba(12, 13, 13, 0.06)"

CHART_PALETTE = ["#19C853", "#0C0D0D", "#4B4B55", "#8E8E98", "#C4C4CD"]

st.set_page_config(
    page_title="Retail Intelligence | Operations Control",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ArgoLogics High-End Design System Injection
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        -webkit-font-smoothing: antialiased;
    }}

    /* Global Canvas */
    .stApp {{
        background-color: {COLOR_BG} !important;
        color: {COLOR_CHARCOAL} !important;
    }}

    /* Top Navigation Header (ArgoLogics Shell) */
    .argologics-header {{
        background: {COLOR_CARD};
        border-radius: 20px;
        padding: 16px 24px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 16px rgba(12, 13, 13, 0.03);
        border: 1px solid rgba(12, 13, 13, 0.04);
        flex-wrap: wrap;
        gap: 16px;
    }}
    .brand-section {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .brand-logo-icon {{
        width: 38px;
        height: 38px;
        background: {COLOR_CHARCOAL};
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .brand-logo-text {{
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: {COLOR_CHARCOAL};
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .brand-logo-accent {{
        color: {COLOR_EMERALD};
    }}
    .header-actions {{
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }}
    .live-status-pill {{
        background: {COLOR_EMERALD_LIGHT};
        color: {COLOR_CHARCOAL};
        font-size: 0.8rem;
        font-weight: 600;
        padding: 6px 14px;
        border-radius: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
        border: 1px solid rgba(25, 200, 83, 0.2);
    }}
    .live-status-dot {{
        width: 8px;
        height: 8px;
        background: {COLOR_EMERALD};
        border-radius: 50%;
        box-shadow: 0 0 6px {COLOR_EMERALD};
    }}
    .header-icon-btn {{
        width: 36px;
        height: 36px;
        background: #F4F4F7;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: {COLOR_CHARCOAL};
    }}

    /* Metric KPI Cards (ArgoLogics Style) */
    [data-testid="stMetric"] {{
        background: {COLOR_CARD} !important;
        border: 1px solid rgba(12, 13, 13, 0.04) !important;
        border-radius: 18px !important;
        padding: 20px 22px !important;
        box-shadow: 0 4px 14px rgba(12, 13, 13, 0.03) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }}
    [data-testid="stMetric"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(12, 13, 13, 0.06) !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: {COLOR_MUTED} !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
    }}
    [data-testid="stMetricValue"] {{
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        color: {COLOR_CHARCOAL} !important;
        font-variant-numeric: tabular-nums !important;
        letter-spacing: -0.02em !important;
        margin-top: 4px !important;
    }}

    /* Tabs Bar - ArgoLogics Pill Dock with Black Unselected Text */
    div[data-baseweb="tab-list"] {{
        background: {COLOR_CARD} !important;
        padding: 6px 8px !important;
        border-radius: 30px !important;
        border: 1px solid rgba(12, 13, 13, 0.04) !important;
        box-shadow: 0 2px 8px rgba(12, 13, 13, 0.03) !important;
        display: inline-flex !important;
        gap: 6px !important;
        margin-bottom: 24px !important;
    }}
    button[data-baseweb="tab"] {{
        border-radius: 20px !important;
        padding: 8px 20px !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: {COLOR_CHARCOAL} !important;
        background: transparent !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }}
    button[data-baseweb="tab"] p, button[data-baseweb="tab"] span {{
        color: {COLOR_CHARCOAL} !important;
        font-weight: 600 !important;
    }}
    button[data-baseweb="tab"]:hover {{
        color: {COLOR_CHARCOAL} !important;
        background: #F4F4F7 !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        background: {COLOR_EMERALD} !important;
        color: #FFFFFF !important;
        box-shadow: 0 3px 12px rgba(25, 200, 83, 0.35) !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] p, button[data-baseweb="tab"][aria-selected="true"] span {{
        color: #FFFFFF !important;
    }}

    /* DataFrames - Crisp White Card Frame */
    div[data-testid="stDataFrame"] {{
        background: {COLOR_CARD} !important;
        border: 1px solid rgba(12, 13, 13, 0.05) !important;
        border-radius: 18px !important;
        box-shadow: 0 4px 16px rgba(12, 13, 13, 0.03) !important;
        overflow: hidden !important;
        padding: 4px !important;
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {COLOR_CARD} !important;
        border-right: 1px solid rgba(12, 13, 13, 0.06) !important;
        box-shadow: 2px 0 12px rgba(12, 13, 13, 0.02) !important;
    }}
    section[data-testid="stSidebar"] h2 {{
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: {COLOR_CHARCOAL} !important;
    }}
    div[data-baseweb="select"] {{
        border-radius: 12px !important;
    }}
    div[data-baseweb="input"] {{
        border-radius: 12px !important;
    }}
    .sidebar-card {{
        background: #F8F8FA;
        border-radius: 14px;
        padding: 14px 16px;
        margin-top: 18px;
        border: 1px solid rgba(12, 13, 13, 0.04);
    }}
    .sidebar-card-label {{
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: {COLOR_MUTED};
        margin-bottom: 4px;
    }}
    .sidebar-card-value {{
        font-size: 0.85rem;
        font-weight: 600;
        color: {COLOR_CHARCOAL};
    }}

    /* Section Subheaders */
    h2, h3 {{
        color: {COLOR_CHARCOAL} !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        margin-top: 16px !important;
        margin-bottom: 12px !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def apply_chart_theme(fig, title=None, height=340):
    """ArgoLogics-inspired Plotly styling with pure white cards, green highlights, and clean typography."""
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family="Plus Jakarta Sans, sans-serif", size=14, color=COLOR_CHARCOAL),
            x=0.01,
            y=0.96,
        ),
        font=dict(family="Plus Jakarta Sans, sans-serif", color=COLOR_MUTED, size=11),
        paper_bgcolor=COLOR_CARD,
        plot_bgcolor=COLOR_CARD,
        margin=dict(l=45, r=20, t=50 if title else 25, b=35),
        height=height,
        hoverlabel=dict(
            bgcolor=COLOR_CHARCOAL,
            font_size=12,
            font_family="Plus Jakarta Sans, sans-serif",
            font_color="#FFFFFF",
            bordercolor=COLOR_EMERALD,
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#F3F3F6",
            zeroline=False,
            linecolor="#EAEAEE",
            tickfont=dict(color=COLOR_MUTED, size=11),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#F3F3F6",
            zeroline=False,
            linecolor="#EAEAEE",
            tickfont=dict(color=COLOR_MUTED, size=11),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=COLOR_CHARCOAL),
        ),
    )
    return fig


@st.cache_data(ttl=300)
def sales_data():
    """Fault-tolerant data loading with fallback schema."""
    cols = [
        "TransactionID", "TransactionLineID", "FullDate", "SourceProductID",
        "ProductName", "Category", "SourceStoreID", "StoreName", "StoreState",
        "ChannelName", "SourceCustomerID", "QuantitySold", "UnitPrice",
        "GrossSalesAmount", "DiscountAmount", "NetSalesAmount", "CostAmount",
        "ProfitAmount", "PromotionName", "PromotionType", "HolidayFlag"
    ]
    try:
        from src.analytics.data import sales
        frame = sales()
        if frame is not None and not frame.empty and "FullDate" in frame.columns:
            frame["FullDate"] = pd.to_datetime(frame.FullDate)
            return frame
    except Exception:
        pass
    empty_df = pd.DataFrame(columns=cols)
    empty_df["FullDate"] = pd.to_datetime(empty_df["FullDate"])
    return empty_df


@st.cache_data(ttl=300)
def csv_artifact(name):
    """Safely read CSV artifact, returning empty DataFrame if missing."""
    try:
        path = REPORTS / name
        if path.exists():
            return pd.read_csv(path)
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=300)
def report():
    """Safely load JSON report artifact."""
    try:
        path = REPORTS / "analytics_report.json"
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


@st.cache_data(ttl=300)
def forecast_for_filters(start_date, end_date, stores, categories, channels):
    """Rebuild a forecast using only the selected date/entity slice."""
    frame = sales_data().copy()
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    frame = frame[frame.FullDate.between(start, end)]
    if stores:
        frame = frame[frame.StoreName.isin(stores)]
    if categories:
        frame = frame[frame.Category.isin(categories)]
    if channels:
        frame = frame[frame.ChannelName.isin(channels)]
    if frame.empty:
        raise ValueError('No sales records match the selected filters.')
    weekly = complete_weeks(frame, start, end)
    result = forecast(weekly, app_config.model_config['forecasting'])
    # Exclude the fitted model bundle from Streamlit cache output.
    return result[:-1]


@st.cache_data(ttl=300)
def etl_history():
    """Safely query ETL run summary, falling back to clean empty table."""
    try:
        from src.analytics.data import query
        return query(
            """SELECT TOP 25 ETLRunID,ExecutionMode,StartTime,EndTime,DurationSeconds,
               Status,SourceRowCount,InsertedRowCount,UpdatedRowCount,RejectedRowCount,
               ErrorMessage FROM mart.vw_ETLRunSummary ORDER BY ETLRunID DESC"""
        )
    except Exception:
        return pd.DataFrame(columns=[
            "ETLRunID", "ExecutionMode", "StartTime", "EndTime",
            "DurationSeconds", "Status", "SourceRowCount", "InsertedRowCount",
            "UpdatedRowCount", "RejectedRowCount", "ErrorMessage"
        ])


def money(value):
    try:
        return "$" + f"{float(value):,.0f}"
    except (ValueError, TypeError):
        return "$0"


# ArgoLogics Top Brand & Control Header
st.markdown(
    f"""
    <div class="argologics-header">
        <div class="brand-section">
            <div class="brand-logo-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2L2 19.5H22L12 2Z" fill="{COLOR_EMERALD}"/>
                    <path d="M12 8L6.5 17.5H17.5L12 8Z" fill="#FFFFFF"/>
                </svg>
            </div>
            <div>
                <h1 class="brand-logo-text">
                    Retail<span class="brand-logo-accent">Logics</span>
                </h1>
            </div>
        </div>
        <div class="header-actions">
            <div class="live-status-pill">
                <span class="live-status-dot"></span>
                <span>Live DW &middot; SQL Server 2022</span>
            </div>
            <div class="header-icon-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                </svg>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

data = sales_data()
if data.empty:
    st.info("Warehouse is initializing or empty. Showing operational structure with zeroed baseline.")

with st.sidebar:
    st.markdown("## Filters")
    if not data.empty and data.FullDate.notna().any():
        first, last = data.FullDate.min().date(), data.FullDate.max().date()
        dates = st.date_input("Sales date range", (first, last), min_value=first, max_value=last)
        stores_list = sorted(data.StoreName.dropna().unique())
        cats_list = sorted(data.Category.dropna().unique())
        chans_list = sorted(data.ChannelName.dropna().unique())
    else:
        dates = ()
        stores_list, cats_list, chans_list = [], [], []

    selected_stores = st.multiselect("Store locations", stores_list)
    selected_categories = st.multiselect("Product categories", cats_list)
    selected_channels = st.multiselect("Sales channels", chans_list)

    st.markdown(
        f"""
        <div class="sidebar-card">
            <div class="sidebar-card-label">Warehouse Telemetry</div>
            <div class="sidebar-card-value">Lines: {len(data):,}</div>
            <div class="sidebar-card-value" style="margin-top:2px;">Snapshot: {report().get('warehouse_signature', {}).get('SuccessfulRun', 'Active')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Robust filter application handling all date tuple variants
filtered = data.copy()
filter_start = data.FullDate.min().date() if not data.empty else None
filter_end = data.FullDate.max().date() if not data.empty else None
if not filtered.empty:
    if isinstance(dates, (tuple, list)):
        if len(dates) == 2:
            filter_start, filter_end = dates[0], dates[1]
            filtered = filtered[filtered.FullDate.dt.date.between(dates[0], dates[1])]
        elif len(dates) == 1:
            filter_start = filter_end = dates[0]
            filtered = filtered[filtered.FullDate.dt.date == dates[0]]
    elif dates:
        filter_start = filter_end = dates
        filtered = filtered[filtered.FullDate.dt.date == dates]

    if selected_stores:
        filtered = filtered[filtered.StoreName.isin(selected_stores)]
    if selected_categories:
        filtered = filtered[filtered.Category.isin(selected_categories)]
    if selected_channels:
        filtered = filtered[filtered.ChannelName.isin(selected_channels)]

# Exact tab names preserved for automated testing verification
executive, products_tab, forecast_tab, mining_tab, inventory_tab, problems_tab, operations_tab = st.tabs(
    [
        "Executive",
        "Products & stores",
        "Forecast",
        "Basket & customers",
        "Inventory & suppliers",
        "Problems & precision",
        "Anomalies & ETL",
    ]
)

with executive:
    transaction_count = filtered.TransactionID.nunique() if not filtered.empty else 0
    net_sales = float(filtered.NetSalesAmount.sum()) if not filtered.empty else 0.0
    profit = float(filtered.ProfitAmount.sum()) if not filtered.empty else 0.0

    # 5 KPI Metric Cards (ArgoLogics style)
    metrics = st.columns(5)
    metrics[0].metric("Net sales", money(net_sales))
    metrics[1].metric("Gross profit", money(profit))
    metrics[2].metric("Gross margin", f"{profit / net_sales * 100 if net_sales else 0:.1f}%")
    metrics[3].metric("Transactions", f"{transaction_count:,}")
    metrics[4].metric("Average transaction", money(net_sales / transaction_count if transaction_count else 0))

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Monthly Trend Line
    if not filtered.empty:
        monthly = (
            filtered.set_index("FullDate")
            .resample("MS")
            .agg(NetSales=("NetSalesAmount", "sum"), Profit=("ProfitAmount", "sum"))
            .reset_index()
        )
    else:
        monthly = pd.DataFrame(columns=["FullDate", "NetSales", "Profit"])

    trend = px.line(
        monthly,
        x="FullDate",
        y=["NetSales", "Profit"] if not monthly.empty else None,
        markers=True,
        color_discrete_sequence=[COLOR_EMERALD, COLOR_CHARCOAL],
    )
    trend.update_traces(line=dict(width=3), marker=dict(size=7))
    trend.update_layout(
        hovermode="x unified",
        yaxis_title="Amount ($)",
        xaxis_title="",
    )
    apply_chart_theme(trend, title="Monthly Net Sales & Profit Performance", height=340)
    st.plotly_chart(trend, width="stretch")

    left, right = st.columns(2)
    if not filtered.empty:
        category = (
            filtered.groupby("Category", as_index=False)
            .agg(NetSales=("NetSalesAmount", "sum"), Profit=("ProfitAmount", "sum"))
            .sort_values("NetSales", ascending=True)
        )
    else:
        category = pd.DataFrame(columns=["Category", "NetSales", "Profit"])

    cat_chart = px.bar(
        category,
        x="NetSales",
        y="Category",
        orientation="h",
        color_discrete_sequence=[COLOR_CHARCOAL],
    )
    cat_chart.update_layout(xaxis_title="Net Sales ($)", yaxis_title="")
    apply_chart_theme(cat_chart, title="Sales by Category", height=320)
    left.plotly_chart(cat_chart, width="stretch")

    if not filtered.empty:
        channel = filtered.groupby("ChannelName", as_index=False).NetSalesAmount.sum()
    else:
        channel = pd.DataFrame(columns=["ChannelName", "NetSalesAmount"])

    donut_chart = px.pie(
        channel,
        names="ChannelName",
        values="NetSalesAmount",
        hole=0.55,
        color_discrete_sequence=CHART_PALETTE,
    )
    donut_chart.update_traces(textposition="inside", textinfo="percent+label")
    donut_chart.update_layout(showlegend=False)
    apply_chart_theme(donut_chart, title="Sales by Channel Overview", height=320)
    right.plotly_chart(donut_chart, width="stretch")

with products_tab:
    if not filtered.empty:
        product = (
            filtered.groupby(["SourceProductID", "ProductName", "Category"], as_index=False)
            .agg(
                Units=("QuantitySold", "sum"),
                NetSales=("NetSalesAmount", "sum"),
                Profit=("ProfitAmount", "sum"),
                Transactions=("TransactionID", "nunique"),
            )
            .sort_values("NetSales", ascending=False)
        )
        store = (
            filtered.groupby(["SourceStoreID", "StoreName", "StoreState"], as_index=False)
            .agg(
                NetSales=("NetSalesAmount", "sum"),
                Profit=("ProfitAmount", "sum"),
                Transactions=("TransactionID", "nunique"),
            )
            .sort_values("NetSales", ascending=True)
        )
    else:
        product = pd.DataFrame(columns=["SourceProductID", "ProductName", "Category", "Units", "NetSales", "Profit", "Transactions"])
        store = pd.DataFrame(columns=["SourceStoreID", "StoreName", "StoreState", "NetSales", "Profit", "Transactions"])

    left, right = st.columns(2)
    left.subheader("Product performance")
    left.dataframe(
        product.head(30),
        hide_index=True,
        width="stretch",
    )

    right.subheader("Store performance")
    store_chart = px.bar(
        store,
        x="NetSales",
        y="StoreName",
        orientation="h",
        color="Profit" if not store.empty else None,
        color_continuous_scale=["#C8EED5", COLOR_EMERALD],
    )
    store_chart.update_layout(xaxis_title="Net Sales ($)", yaxis_title="")
    apply_chart_theme(store_chart, title="Store Revenue & Margin Contribution", height=420)
    right.plotly_chart(store_chart, width="stretch")

with forecast_tab:
    cols = st.columns(4)
    try:
        if filter_start is None or filtered.empty:
            raise ValueError('No sales records match the selected filters.')
        analytics, backtests, _, tests, predictions, future = forecast_for_filters(
            str(filter_start), str(filter_end), tuple(selected_stores),
            tuple(selected_categories), tuple(selected_channels),
        )
        selected = analytics["selected_model"]
        selected_metrics = tests[tests.Model == selected].iloc[0].to_dict()
        stability = analytics['selected_model_backtest']
        cols[0].metric("Selected on backtests", selected.replace("_", " ").title())
        cols[1].metric("Backtest WAPE", f"{stability['WAPE_percent_mean']:.2f}% ± {stability['WAPE_percent_std']:.2f}")
        cols[2].metric("Unseen test WAPE", f"{selected_metrics.get('WAPE_percent', 0):.2f}%")
        cols[3].metric("Unseen test MASE", f"{selected_metrics.get('MASE', 0):.2f}")

        chosen = predictions[predictions.Model == selected].copy()
        chosen["WeekStart"] = pd.to_datetime(chosen.WeekStart)
        future["WeekStart"] = pd.to_datetime(future.WeekStart)

        chart = go.Figure()
        chart.add_scatter(
            x=chosen.WeekStart,
            y=chosen.Actual,
            name="Unseen Test Actual",
            mode="lines+markers",
            line=dict(color=COLOR_CHARCOAL, width=2.5),
            marker=dict(size=6),
        )
        chart.add_scatter(
            x=chosen.WeekStart,
            y=chosen.Predicted,
            name="Test Horizon Forecast",
            mode="lines+markers",
            line=dict(color="#F59E0B", width=2.5),
            marker=dict(size=6, symbol="diamond"),
        )
        chart.add_scatter(
            x=future.WeekStart,
            y=future.ForecastNetSales,
            name="Projected Future Horizon",
            mode="lines+markers",
            line=dict(color=COLOR_EMERALD, width=2.5, dash="dash"),
            marker=dict(size=6),
        )
        chart.update_layout(
            hovermode="x unified",
            yaxis_title="Weekly Net Sales ($)",
            xaxis_title="",
        )
        apply_chart_theme(
            chart,
            title="Weekly Sales Trajectory & Model Projection",
            height=370,
        )
        st.plotly_chart(chart, width="stretch")
        st.dataframe(backtests, hide_index=True, width="stretch")
        st.caption(
            f"Recalculated from the selected slice ({filter_start} to {filter_end}). "
            "Model selection uses expanding-window rolling-origin backtests; the final 12 weeks remain unseen."
        )
    except ValueError as exc:
        cols[0].metric("Selected on backtests", "Unavailable")
        cols[1].metric("Test WAPE", "0.00%")
        cols[2].metric("Test MASE", "0.00")
        cols[3].metric("Test RMSE", "$0")
        minimum = minimum_history_weeks(app_config.model_config.get('forecasting', {}))
        st.info(f"{exc} Choose a range with at least {minimum} complete weeks (about {minimum / 52:.1f} years).")
        st.dataframe(pd.DataFrame(columns=["Model", "Folds", "MAE_mean", "RMSE_mean", "WAPE_percent_mean", "MASE_mean"]), hide_index=True, width="stretch")

with mining_tab:
    rules = csv_artifact("association_rules.csv")
    profiles = csv_artifact("customer_segment_profiles.csv")

    left, right = st.columns(2)
    left.subheader("Transaction basket rules")
    if not rules.empty:
        left.dataframe(rules.head(30), hide_index=True, width="stretch")
    else:
        left.dataframe(pd.DataFrame(columns=["Antecedents", "Consequents", "Support", "Confidence", "Lift"]), hide_index=True, width="stretch")
    left.caption("Discovered product co-purchase affinities using FP-Growth association rules.")

    right.subheader("Synthetic customer RFM clusters")
    if not profiles.empty:
        rfm_chart = px.scatter(
            profiles,
            x="MeanFrequency",
            y="MeanMonetary",
            size="Customers",
            color="MeanRecencyDays",
            text="Cluster",
            color_continuous_scale=[COLOR_EMERALD, COLOR_CHARCOAL],
        )
        rfm_chart.update_traces(
            textposition="top center",
            marker=dict(opacity=0.9, line=dict(width=1, color=COLOR_CHARCOAL)),
        )
        rfm_chart.update_layout(
            xaxis_title="Mean Frequency (Orders)",
            yaxis_title="Mean Monetary ($)",
        )
        apply_chart_theme(rfm_chart, title="Customer RFM Behavioral Clusters", height=340)
        right.plotly_chart(rfm_chart, width="stretch")
        right.dataframe(profiles, hide_index=True, width="stretch")
    else:
        right.dataframe(pd.DataFrame(columns=["Cluster", "Customers", "MeanRecencyDays", "MeanFrequency", "MeanMonetary"]), hide_index=True, width="stretch")

with inventory_tab:
    inventory = csv_artifact("inventory_abc_xyz.csv")
    suppliers = csv_artifact("supplier_scorecard.csv")

    cols = st.columns(4)
    if not inventory.empty:
        cols[0].metric("Tracked positions", f"{len(inventory):,}")
        cols[1].metric("Stockouts", f"{int(inventory.StockoutFlag.sum()):,}")
        cols[2].metric("Below reorder", f"{int(inventory.UnderStockFlag.sum()):,}")
        cols[3].metric("Inventory value", money(inventory.InventoryValue.sum()))

        health = inventory.groupby("InventoryHealthStatus", as_index=False).size()
        health_colors = {
            "HEALTHY": COLOR_EMERALD,
            "UNDERSTOCK": "#F59E0B",
            "STOCKOUT": "#EF4444",
            "OVERSTOCK": COLOR_MUTED,
        }
        health_chart = px.bar(
            health,
            x="InventoryHealthStatus",
            y="size",
            color="InventoryHealthStatus",
            color_discrete_map=health_colors,
        )
        health_chart.update_layout(
            xaxis_title="Health Classification",
            yaxis_title="SKU-Store Positions",
            showlegend=False,
        )
        apply_chart_theme(health_chart, title="Inventory Health Distribution", height=320)
        st.plotly_chart(health_chart, width="stretch")

        st.dataframe(
            inventory.sort_values(
                ["StockoutFlag", "UnderStockFlag", "Revenue"],
                ascending=[False, False, False],
            ).head(40),
            hide_index=True,
            width="stretch",
        )
    else:
        cols[0].metric("Tracked positions", "0")
        cols[1].metric("Stockouts", "0")
        cols[2].metric("Below reorder", "0")
        cols[3].metric("Inventory value", "$0")
        st.dataframe(pd.DataFrame(columns=["SourceProductID", "ProductName", "InventoryHealthStatus", "Revenue"]), hide_index=True, width="stretch")

    st.subheader("Supplier delivery scorecard")
    st.dataframe(suppliers if not suppliers.empty else pd.DataFrame(columns=["SourceSupplierID", "SupplierName", "TotalShipments", "OTIF_Rate"]), hide_index=True, width="stretch")

with problems_tab:
    problems = csv_artifact('detected_problems.csv')
    precision = report().get('anomaly_detection', {})
    if not problems.empty and 'ProblemDate' in problems:
        problems['ProblemDate'] = pd.to_datetime(problems.ProblemDate, errors='coerce')
        if filter_start is not None:
            problems = problems[problems.ProblemDate.dt.date.between(filter_start, filter_end)]
    pcols = st.columns(4)
    pcols[0].metric('Detected problems', f'{len(problems):,}')
    pcols[1].metric('Synthetic precision', f"{(precision.get('precision') or 0) * 100:.1f}%")
    pcols[2].metric('Synthetic recall', f"{(precision.get('recall') or 0) * 100:.1f}%")
    pcols[3].metric('Synthetic F1', f"{(precision.get('f1') or 0):.3f}")
    st.dataframe(
        problems if not problems.empty else pd.DataFrame(columns=[
            'ProblemDate','ProblemType','Severity','EntityType','EntityID','MetricValue','Description'
        ]),
        hide_index=True,
        width='stretch',
    )
    st.caption('Precision, recall and F1 measure only deterministic injected high-quantity anomalies—not fraud or all real-world business problems.')

with operations_tab:
    anomaly = csv_artifact("sales_anomalies.csv")
    cols = st.columns(3)
    if not anomaly.empty and "IsAnomaly" in anomaly.columns:
        flag = anomaly.IsAnomaly.astype(str).str.lower().isin(["true", "1"])
        flagged = anomaly[flag]

        cols[0].metric("Evaluated lines", f"{len(anomaly):,}")
        cols[1].metric("Flagged for review", f"{len(flagged):,}")
        cols[2].metric("Flag rate", f"{len(flagged) / len(anomaly) * 100:.2f}%")

        st.dataframe(
            flagged.sort_values("AnomalyScore").head(50),
            hide_index=True,
            width="stretch",
        )
        st.caption("Unsupervised Isolation Forest flags statistical outliers across quantity, unit price, and discount.")
    else:
        cols[0].metric("Evaluated lines", "0")
        cols[1].metric("Flagged for review", "0")
        cols[2].metric("Flag rate", "0.00%")
        st.dataframe(pd.DataFrame(columns=["TransactionID", "TransactionLineID", "FullDate", "ProductName", "AnomalyScore"]), hide_index=True, width="stretch")

    st.subheader("ETL run history")
    st.dataframe(etl_history(), hide_index=True, width="stretch")
