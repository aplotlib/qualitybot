#!/usr/bin/env python3
"""
BRENT CRUDE OIL - LIVE TRACKER DASHBOARD (Streamlit)
=====================================================
Run:  pip install -r requirements.txt
      streamlit run brent_dashboard_st.py

Pulls real-time Brent crude futures (BZ=F) and WTI (CL=F) via yfinance.
Auto-refreshes every 30 seconds.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Brent Crude Oil - Live Tracker",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Target
TARGET_PRICE = 94.50
TARGET_DATE = datetime(2026, 6, 15)
TARGET_DATE_STR = "June 15, 2026"

REFRESH_INTERVAL = 30  # seconds

# ---------------------------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

    .stApp {
        background: linear-gradient(165deg, #06080f 0%, #0c1019 40%, #0f1520 100%);
    }
    .main .block-container { padding-top: 1.5rem; max-width: 1400px; }

    h1, h2, h3, h4, h5, h6 { font-family: 'Outfit', sans-serif !important; }
    p, span, div, li { font-family: 'Outfit', sans-serif; }

    .big-price {
        font-family: 'Outfit', sans-serif;
        font-size: 56px;
        font-weight: 800;
        letter-spacing: -2px;
        text-shadow: 0 0 40px rgba(34,211,238,0.15);
        line-height: 1.1;
    }
    .change-up { color: #22c55e; font-family: 'JetBrains Mono', monospace; font-weight: 600; }
    .change-down { color: #ef4444; font-family: 'JetBrains Mono', monospace; font-weight: 600; }
    .mono { font-family: 'JetBrains Mono', monospace; }
    .dim { color: #64748b; font-size: 12px; }
    .cyan { color: #22d3ee; }
    .orange { color: #f97316; }
    .green { color: #22c55e; }
    .red { color: #ef4444; }
    .purple { color: #a78bfa; }
    .yellow { color: #fbbf24; }

    .metric-card {
        background: rgba(15,21,32,0.7);
        border: 1px solid rgba(100,116,139,0.12);
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 8px;
    }
    .metric-label {
        font-size: 10px;
        color: #64748b;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 18px;
        font-weight: 700;
        color: #f1f5f9;
    }

    .conflict-card {
        background: linear-gradient(135deg, rgba(239,68,68,0.06) 0%, rgba(249,115,22,0.04) 100%);
        border: 1px solid rgba(239,68,68,0.2);
        border-radius: 14px;
        padding: 20px 24px;
    }

    .target-card {
        background: linear-gradient(135deg, rgba(34,211,238,0.06) 0%, rgba(167,139,250,0.04) 100%);
        border: 1px solid rgba(34,211,238,0.2);
        border-radius: 14px;
        padding: 20px 24px;
    }

    .analyst-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid rgba(100,116,139,0.08);
        font-size: 13px;
    }

    .stMetric > div { background: rgba(15,21,32,0.5); border-radius: 10px; padding: 12px; }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .live-pulse {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        animation: pulse 2s infinite;
        margin-right: 8px;
        vertical-align: middle;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(1.4); }
    }

    div[data-testid="stSidebar"] {
        background: rgba(8,10,18,0.95);
        border-right: 1px solid rgba(100,116,139,0.1);
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DATA FETCHING
# ---------------------------------------------------------------------------
@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_brent_data():
    """Pull live Brent + WTI data from Yahoo Finance."""
    brent = yf.Ticker("BZ=F")
    wti = yf.Ticker("CL=F")

    # Intraday 1-min
    intraday = brent.history(period="1d", interval="1m")

    # 1-year daily
    hist_1y = brent.history(period="1y", interval="1d")

    # 5-year weekly for long view
    hist_5y = brent.history(period="5y", interval="1wk")

    # WTI for spread
    wti_1y = wti.history(period="1y", interval="1d")
    wti_intraday = wti.history(period="1d", interval="1m")

    # Current info
    info = brent.fast_info

    return {
        "intraday": intraday,
        "hist_1y": hist_1y,
        "hist_5y": hist_5y,
        "wti_1y": wti_1y,
        "wti_intraday": wti_intraday,
        "info": info,
        "fetch_time": datetime.now(),
    }


def compute_target_probability(hist_df, current_price, target_price, days_to_target):
    """
    Monte Carlo + historical vol approach to estimate probability of
    Brent hitting target_price by target_date.
    """
    if hist_df.empty or len(hist_df) < 30:
        return None, None, None

    # Daily log returns
    closes = hist_df["Close"].dropna()
    log_returns = np.log(closes / closes.shift(1)).dropna()

    mu = log_returns.mean()
    sigma = log_returns.std()

    n_sims = 50_000
    n_days = max(1, days_to_target)

    # GBM simulation
    np.random.seed(42)
    daily_shocks = np.random.normal(mu, sigma, (n_sims, n_days))
    price_paths = current_price * np.exp(np.cumsum(daily_shocks, axis=1))
    final_prices = price_paths[:, -1]

    # Probability within +/- $3 of target
    tolerance = 3.0
    prob_near = np.mean(np.abs(final_prices - target_price) <= tolerance) * 100
    # Probability of being AT OR BELOW target
    prob_at_or_below = np.mean(final_prices <= target_price) * 100
    # Probability of being within $5
    prob_within_5 = np.mean(np.abs(final_prices - target_price) <= 5) * 100

    # Percentiles
    p10 = np.percentile(final_prices, 10)
    p25 = np.percentile(final_prices, 25)
    p50 = np.percentile(final_prices, 50)
    p75 = np.percentile(final_prices, 75)
    p90 = np.percentile(final_prices, 90)

    return {
        "prob_within_3": round(prob_near, 1),
        "prob_at_or_below": round(prob_at_or_below, 1),
        "prob_within_5": round(prob_within_5, 1),
        "p10": round(p10, 2),
        "p25": round(p25, 2),
        "median": round(p50, 2),
        "p75": round(p75, 2),
        "p90": round(p90, 2),
        "mu_annual": round(mu * 252 * 100, 1),
        "sigma_annual": round(sigma * np.sqrt(252) * 100, 1),
        "n_sims": n_sims,
    }, price_paths, final_prices


# ---------------------------------------------------------------------------
# CHART HELPERS
# ---------------------------------------------------------------------------
CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(10,14,22,0.5)",
    font=dict(family="Outfit, sans-serif", color="#94a3b8"),
    margin=dict(l=50, r=20, t=40, b=40),
    xaxis=dict(gridcolor="rgba(100,116,139,0.08)", showgrid=True),
    yaxis=dict(gridcolor="rgba(100,116,139,0.08)", showgrid=True),
    hoverlabel=dict(
        bgcolor="rgba(10,12,18,0.95)",
        bordercolor="rgba(34,211,238,0.3)",
        font=dict(family="JetBrains Mono, monospace", size=12),
    ),
)


def make_intraday_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"],
        mode="lines",
        line=dict(color="#22d3ee", width=2),
        fill="tozeroy",
        fillcolor="rgba(34,211,238,0.08)",
        name="Brent",
        hovertemplate="$%{y:.2f}<extra></extra>",
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        height=320,
        title=dict(text="Intraday Price (1-min bars)", font=dict(size=16, color="#f1f5f9")),
        yaxis=dict(title="USD/bbl", tickprefix="$", **CHART_LAYOUT["yaxis"]),
        xaxis=dict(title="", **CHART_LAYOUT["xaxis"]),
        showlegend=False,
    )
    return fig


def make_history_chart(df, period_label, target_price=None, target_date=None):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)

    # Price
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"],
        mode="lines",
        line=dict(color="#f97316", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(249,115,22,0.06)",
        name="Brent Close",
        hovertemplate="$%{y:.2f}<extra></extra>",
    ), row=1, col=1)

    # Target line
    if target_price:
        fig.add_hline(y=target_price, line_dash="dash", line_color="rgba(34,211,238,0.5)",
                      annotation_text=f"Target ${target_price}", annotation_font_color="#22d3ee",
                      annotation_font_size=11, row=1, col=1)

    # Target date vertical
    if target_date and target_date > df.index.min():
        fig.add_vline(x=target_date, line_dash="dot", line_color="rgba(167,139,250,0.4)",
                      annotation_text="Jun 15", annotation_font_color="#a78bfa",
                      annotation_font_size=11, row=1, col=1)

    # Volume
    if "Volume" in df.columns:
        colors = ["#22c55e" if c >= o else "#ef4444"
                  for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            marker_color=colors, opacity=0.4,
            name="Volume",
            hovertemplate="%{y:,.0f}<extra></extra>",
        ), row=2, col=1)

    fig.update_layout(
        **CHART_LAYOUT,
        height=480,
        title=dict(text=f"Brent Crude - {period_label}", font=dict(size=16, color="#f1f5f9")),
        showlegend=False,
    )
    fig.update_yaxes(title="USD/bbl", tickprefix="$", row=1, col=1,
                     gridcolor="rgba(100,116,139,0.08)")
    fig.update_yaxes(title="Vol", row=2, col=1,
                     gridcolor="rgba(100,116,139,0.08)")
    fig.update_xaxes(gridcolor="rgba(100,116,139,0.08)")
    return fig


def make_spread_chart(brent_df, wti_df):
    # Align on dates
    merged = pd.DataFrame({
        "Brent": brent_df["Close"],
        "WTI": wti_df["Close"],
    }).dropna()
    merged["Spread"] = merged["Brent"] - merged["WTI"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=merged.index, y=merged["Spread"],
        mode="lines",
        line=dict(color="#a78bfa", width=2),
        fill="tozeroy",
        fillcolor="rgba(167,139,250,0.08)",
        name="Spread",
        hovertemplate="$%{y:.2f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color="rgba(100,116,139,0.3)", line_width=1)
    fig.update_layout(
        **CHART_LAYOUT,
        height=300,
        title=dict(text="Brent-WTI Spread", font=dict(size=16, color="#f1f5f9")),
        yaxis=dict(title="$/bbl", tickprefix="$", **CHART_LAYOUT["yaxis"]),
        showlegend=False,
    )
    return fig


def make_supply_demand_chart():
    """Static supply/demand from IEA/EIA data."""
    quarters = ["Q3 '25", "Q4 '25", "Q1 '26", "Q2 '26F", "Q3 '26F", "Q4 '26F"]
    supply = [108.0, 107.2, 106.6, 107.8, 108.5, 109.2]
    demand = [106.1, 105.8, 105.9, 106.5, 107.1, 107.5]
    surplus = [s - d for s, d in zip(supply, demand)]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Supply", x=quarters, y=supply,
                         marker_color="rgba(34,211,238,0.7)", text=[f"{v}" for v in supply],
                         textposition="outside", textfont=dict(size=10, color="#94a3b8")))
    fig.add_trace(go.Bar(name="Demand", x=quarters, y=demand,
                         marker_color="rgba(249,115,22,0.7)", text=[f"{v}" for v in demand],
                         textposition="outside", textfont=dict(size=10, color="#94a3b8")))
    fig.update_layout(
        **CHART_LAYOUT,
        height=350,
        title=dict(text="Global Oil Supply vs Demand (mb/d)", font=dict(size=16, color="#f1f5f9")),
        barmode="group",
        yaxis=dict(range=[103, 111], title="mb/d", **CHART_LAYOUT["yaxis"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=11)),
    )
    return fig


def make_inventory_chart():
    """Global inventory breakdown from IEA March 2026 OMR."""
    regions = ["OECD", "China Crude", "Oil on Water", "Other Non-OECD"]
    values = [4.10, 1.23, 2.05, 0.82]
    colors = ["#22d3ee", "#f97316", "#a78bfa", "#22c55e"]

    fig = go.Figure(go.Pie(
        labels=regions, values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#0c1019", width=2)),
        textinfo="label+percent",
        textfont=dict(size=12, color="#e2e8f0"),
        hovertemplate="%{label}: %{value:.2f}B bbl<extra></extra>",
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        height=350,
        title=dict(text="Global Oil Inventory (8.2B bbl total)", font=dict(size=16, color="#f1f5f9")),
        annotations=[dict(text="8.2B<br>bbl", x=0.5, y=0.5, font_size=18,
                          font_color="#f1f5f9", showarrow=False,
                          font=dict(family="Outfit, sans-serif", weight=700))],
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5,
                    font=dict(size=11)),
    )
    return fig


def make_monte_carlo_chart(final_prices, target_price, current_price):
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=final_prices,
        nbinsx=120,
        marker_color="rgba(34,211,238,0.4)",
        marker_line_color="rgba(34,211,238,0.6)",
        marker_line_width=0.5,
        name="Simulated Outcomes",
        hovertemplate="$%{x:.0f}: %{y} sims<extra></extra>",
    ))
    fig.add_vline(x=target_price, line_dash="dash", line_color="#22c55e", line_width=2,
                  annotation_text=f"Target ${target_price}",
                  annotation_font_color="#22c55e", annotation_font_size=12)
    fig.add_vline(x=current_price, line_dash="dot", line_color="#f97316", line_width=2,
                  annotation_text=f"Current ${current_price:.2f}",
                  annotation_font_color="#f97316", annotation_font_size=12)
    fig.update_layout(
        **CHART_LAYOUT,
        height=350,
        title=dict(text="Monte Carlo Price Distribution (Jun 15 Close)", font=dict(size=16, color="#f1f5f9")),
        xaxis=dict(title="Price (USD/bbl)", tickprefix="$", **CHART_LAYOUT["xaxis"]),
        yaxis=dict(title="Frequency", **CHART_LAYOUT["yaxis"]),
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛢️ Dashboard Controls")
    st.markdown("---")

    chart_range = st.selectbox("Historical Range", ["1 Month", "3 Months", "6 Months", "1 Year", "5 Years"], index=2)
    show_target = st.checkbox("Show Target Overlay", value=True)
    show_conflict = st.checkbox("Show Conflict Intel", value=True)
    show_monte_carlo = st.checkbox("Show Monte Carlo Analysis", value=True)

    st.markdown("---")
    st.markdown("#### Target Estimate")
    st.markdown(f"""
    <div class='target-card'>
        <div class='metric-label'>CLOSE BY {TARGET_DATE_STR.upper()}</div>
        <div style='font-size:28px;font-weight:800;color:#22d3ee;'>${TARGET_PRICE:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div class='dim mono'>
    Data: Yahoo Finance (BZ=F, CL=F)<br>
    Refresh: Every 30s<br>
    Not financial advice
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Force Refresh"):
        st.cache_data.clear()
        st.rerun()


# ---------------------------------------------------------------------------
# MAIN DASHBOARD
# ---------------------------------------------------------------------------
data = fetch_brent_data()
info = data["info"]
intraday = data["intraday"]
hist_1y = data["hist_1y"]
hist_5y = data["hist_5y"]
wti_1y = data["wti_1y"]

# Current price
if not intraday.empty:
    current_price = round(float(intraday["Close"].iloc[-1]), 2)
    prev_close = round(float(info.previous_close), 2) if hasattr(info, "previous_close") else current_price
    change = round(current_price - prev_close, 2)
    change_pct = round((change / prev_close) * 100, 2) if prev_close else 0
    is_up = change >= 0
else:
    current_price = prev_close = change = change_pct = 0
    is_up = True

day_high = round(float(info.day_high), 2) if hasattr(info, "day_high") else 0
day_low = round(float(info.day_low), 2) if hasattr(info, "day_low") else 0
year_high = round(float(info.year_high), 2) if hasattr(info, "year_high") else 0
year_low = round(float(info.year_low), 2) if hasattr(info, "year_low") else 0
open_price = round(float(info.open), 2) if hasattr(info, "open") else 0

# WTI
wti_price = round(float(data["wti_intraday"]["Close"].iloc[-1]), 2) if not data["wti_intraday"].empty else 0
spread = round(current_price - wti_price, 2) if wti_price else 0

# YoY
yoy = None
if len(hist_1y) > 5:
    first_price = float(hist_1y["Close"].iloc[0])
    if first_price > 0:
        yoy = round(((current_price - first_price) / first_price) * 100, 1)

# Days to target
days_to_target = (TARGET_DATE - datetime.now()).days

# ===== HEADER =====
col_left, col_right = st.columns([3, 2])

with col_left:
    dot_color = "#22c55e" if is_up else "#ef4444"
    sign = "+" if is_up else ""
    change_class = "change-up" if is_up else "change-down"
    st.markdown(f"""
    <div>
        <div style='display:flex;align-items:center;margin-bottom:6px;'>
            <span class='live-pulse' style='background:{dot_color};box-shadow:0 0 12px {dot_color};'></span>
            <span class='mono dim' style='letter-spacing:2px;text-transform:uppercase;'>
                LIVE &middot; Brent Crude Oil Futures (BZ=F)
            </span>
        </div>
        <div style='display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;'>
            <span class='big-price'>${current_price:.2f}</span>
            <span class='{change_class}' style='font-size:22px;'>
                {sign}{change:.2f} ({sign}{change_pct:.2f}%)
            </span>
        </div>
        <div class='mono dim' style='margin-top:6px;'>
            per barrel &middot; Updated {data["fetch_time"].strftime("%H:%M:%S")} &middot; Prev close ${prev_close:.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    st.markdown(f"""
    <div style='text-align:right;'>
        <div style='background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.3);border-radius:8px;padding:8px 14px;display:inline-block;margin-bottom:6px;'>
            <span class='mono' style='font-size:12px;font-weight:600;color:#fca5a5;'>
                52W HIGH ${year_high:.2f} &middot; LOW ${year_low:.2f}
            </span>
        </div><br>
        <div style='background:rgba(167,139,250,0.1);border:1px solid rgba(167,139,250,0.25);border-radius:8px;padding:8px 14px;display:inline-block;margin-bottom:6px;'>
            <span class='mono' style='font-size:12px;font-weight:600;color:#c4b5fd;'>
                Brent-WTI Spread: ${spread:.2f}
            </span>
        </div><br>
        <div style='background:rgba(34,211,238,0.1);border:1px solid rgba(34,211,238,0.25);border-radius:8px;padding:8px 14px;display:inline-block;'>
            <span class='mono' style='font-size:12px;font-weight:600;color:#67e8f9;'>
                Target: ${TARGET_PRICE} by {TARGET_DATE_STR} &middot; {days_to_target}d out
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ===== STATS ROW =====
st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
c1, c2, c3, c4, c5, c6 = st.columns(6)

stats = [
    (c1, "Day Range", f"${day_low:.2f} - ${day_high:.2f}", "#22d3ee"),
    (c2, "Open", f"${open_price:.2f}", "#22c55e"),
    (c3, "WTI Price", f"${wti_price:.2f}", "#a78bfa"),
    (c4, "YoY Change", f"{'+' if yoy and yoy >= 0 else ''}{yoy:.1f}%" if yoy else "N/A", "#f97316"),
    (c5, "Spread", f"${spread:.2f}", "#a78bfa"),
    (c6, "Days to Target", f"{days_to_target}", "#22d3ee"),
]

for col, label, value, color in stats:
    with col:
        st.markdown(f"""
        <div class='metric-card' style='border-left:3px solid {color};'>
            <div class='metric-label'>{label}</div>
            <div class='metric-value'>{value}</div>
        </div>
        """, unsafe_allow_html=True)

# ===== INTRADAY CHART =====
st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
if not intraday.empty:
    st.plotly_chart(make_intraday_chart(intraday), use_container_width=True)

# ===== HISTORICAL CHART =====
range_map = {
    "1 Month": ("1mo", "1 Month"),
    "3 Months": ("3mo", "3 Months"),
    "6 Months": ("6mo", "6 Months"),
    "1 Year": ("1y", "1 Year"),
    "5 Years": ("5y", "5 Years"),
}
rkey, rlabel = range_map[chart_range]

if rkey == "5y":
    chart_df = hist_5y
elif rkey == "1y":
    chart_df = hist_1y
else:
    days_map = {"1mo": 22, "3mo": 66, "6mo": 132}
    chart_df = hist_1y.tail(days_map.get(rkey, 132))

target_overlay = TARGET_PRICE if show_target else None
target_date_overlay = TARGET_DATE if show_target else None
st.plotly_chart(make_history_chart(chart_df, rlabel, target_overlay, target_date_overlay), use_container_width=True)

# ===== SPREAD + SUPPLY/DEMAND =====
col_sp, col_sd = st.columns(2)
with col_sp:
    st.plotly_chart(make_spread_chart(hist_1y, wti_1y), use_container_width=True)
with col_sd:
    st.plotly_chart(make_supply_demand_chart(), use_container_width=True)

# ===== INVENTORY =====
col_inv, col_analysts = st.columns(2)
with col_inv:
    st.plotly_chart(make_inventory_chart(), use_container_width=True)

with col_analysts:
    st.markdown("""
    <div class='metric-card' style='border-left:3px solid #fbbf24;'>
        <div style='font-size:16px;font-weight:700;color:#f1f5f9;margin-bottom:12px;'>Analyst Forecasts (Brent, 2026)</div>

        <div class='analyst-row'>
            <span style='color:#94a3b8;'>EIA STEO (Mar 10)</span>
            <span class='mono' style='color:#fbbf24;font-weight:600;'>>$95 thru May, <$80 Q3, ~$70 Q4</span>
        </div>
        <div class='analyst-row'>
            <span style='color:#94a3b8;'>Goldman Sachs</span>
            <span class='mono' style='color:#fbbf24;font-weight:600;'>$71/bbl Q4 (base), $111 Q4 (worst)</span>
        </div>
        <div class='analyst-row'>
            <span style='color:#94a3b8;'>Standard Chartered</span>
            <span class='mono' style='color:#fbbf24;font-weight:600;'>$98 Q2, $85 Q3, $80.50 Q4</span>
        </div>
        <div class='analyst-row'>
            <span style='color:#94a3b8;'>Fitch Ratings</span>
            <span class='mono' style='color:#fbbf24;font-weight:600;'>$70 avg (Hormuz closed ~1mo)</span>
        </div>
        <div class='analyst-row'>
            <span style='color:#94a3b8;'>J.P. Morgan</span>
            <span class='mono' style='color:#fbbf24;font-weight:600;'>$60 avg (pre-conflict, bearish)</span>
        </div>
        <div class='analyst-row' style='border-bottom:none;'>
            <span style='color:#94a3b8;'>Long Forecast (AI)</span>
            <span class='mono' style='color:#fbbf24;font-weight:600;'>$132 high Jun, $118.75 year-end</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ===== TARGET ESTIMATE ANALYSIS =====
st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("## 🎯 Target Estimate Analysis: $94.50 by June 15 Close")

# Monte Carlo
mc_results, price_paths, final_prices = compute_target_probability(
    hist_1y, current_price, TARGET_PRICE, days_to_target
)

if mc_results and show_monte_carlo:
    col_mc1, col_mc2 = st.columns([2, 1])

    with col_mc1:
        st.plotly_chart(make_monte_carlo_chart(final_prices, TARGET_PRICE, current_price), use_container_width=True)

    with col_mc2:
        st.markdown(f"""
        <div class='target-card'>
            <div class='metric-label'>MONTE CARLO RESULTS ({mc_results['n_sims']:,} SIMULATIONS)</div>
            <div style='margin-top:12px;'>
                <div class='analyst-row'>
                    <span style='color:#94a3b8;'>P(within +/-$3 of $94.50)</span>
                    <span class='mono cyan' style='font-weight:700;font-size:16px;'>{mc_results['prob_within_3']}%</span>
                </div>
                <div class='analyst-row'>
                    <span style='color:#94a3b8;'>P(within +/-$5 of $94.50)</span>
                    <span class='mono cyan' style='font-weight:700;font-size:16px;'>{mc_results['prob_within_5']}%</span>
                </div>
                <div class='analyst-row'>
                    <span style='color:#94a3b8;'>P(at or below $94.50)</span>
                    <span class='mono green' style='font-weight:700;font-size:16px;'>{mc_results['prob_at_or_below']}%</span>
                </div>
                <div style='margin-top:14px;border-top:1px solid rgba(100,116,139,0.15);padding-top:12px;'>
                    <div class='metric-label'>PRICE DISTRIBUTION (JUN 15)</div>
                    <div class='analyst-row'><span style='color:#64748b;'>10th %ile</span><span class='mono' style='color:#ef4444;'>${mc_results['p10']}</span></div>
                    <div class='analyst-row'><span style='color:#64748b;'>25th %ile</span><span class='mono orange'>${mc_results['p25']}</span></div>
                    <div class='analyst-row'><span style='color:#64748b;'>Median</span><span class='mono' style='color:#f1f5f9;font-weight:700;'>${mc_results['median']}</span></div>
                    <div class='analyst-row'><span style='color:#64748b;'>75th %ile</span><span class='mono orange'>${mc_results['p75']}</span></div>
                    <div class='analyst-row' style='border-bottom:none;'><span style='color:#64748b;'>90th %ile</span><span class='mono red'>${mc_results['p90']}</span></div>
                </div>
                <div style='margin-top:12px;font-size:11px;color:#475569;'>
                    Vol: {mc_results['sigma_annual']}% annualized &middot; Drift: {mc_results['mu_annual']}%/yr
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Qualitative Assessment
st.markdown(f"""
<div class='target-card' style='margin-top:16px;'>
    <div style='font-size:18px;font-weight:700;color:#22d3ee;margin-bottom:14px;'>
        Qualitative Assessment: Is $94.50 by June 15 Realistic?
    </div>
    <div style='font-size:14px;color:#cbd5e1;line-height:1.8;'>
        <p><strong style='color:#22c55e;'>FACTORS SUPPORTING YOUR TARGET:</strong></p>
        <p>
        Your $94.50 target sits right in the consensus corridor. The EIA's March 10 STEO forecasts Brent
        staying above $95/bbl through approximately May, then dropping below $80 in Q3. That puts mid-June
        squarely in the transition zone where $94.50 is plausible. Standard Chartered's revised forecast
        has Q2 averaging $98 and Q3 averaging $85, making $94.50 a reasonable mid-June interpolation point.
        Goldman Sachs' base case assumes a 21-day low-flow period at Hormuz followed by 30 days of gradual
        recovery, which would imply normalization roughly by late April/May, with prices trending down from
        the current spike toward the $70s by Q4. A June print in the low-to-mid $90s falls on that glide path.
        </p>

        <p><strong style='color:#ef4444;'>FACTORS WORKING AGAINST IT:</strong></p>
        <p>
        The biggest risk is Hormuz staying closed longer than analysts assume. Iran's new Supreme Leader Mojtaba
        Khamenei has vowed to keep the Strait blocked. As of today, only 21 tankers have transited since Feb 28
        vs. 100+ per day normally. If the blockade persists into May, the conflict premium stays elevated and $94.50
        becomes too low. The Long Forecast algorithmic model projects a $132 high in June, reflecting a scenario
        where disruption deepens. Additionally, the IEA notes 3+ mb/d of Gulf refining capacity is already shut
        and LPG/naphtha supply losses are cascading through petrochemicals. If this becomes a sustained supply
        destruction event, prices stay triple-digit through summer.
        </p>

        <p><strong style='color:#fbbf24;'>NET ASSESSMENT:</strong></p>
        <p>
        Your target of $94.50 by June 15 is a <strong>moderate-probability outcome</strong>. It requires the
        Strait of Hormuz to begin meaningfully reopening by late April/early May, the IEA emergency 400M barrel
        release to dampen the spike, and OPEC+ to follow through on the 206K b/d April increase. If those three
        conditions are met, the conflict premium bleeds off and the underlying surplus (1.9M b/d forecast for 2026)
        reasserts itself, pulling Brent into the $90-95 corridor by mid-June. If any of those conditions fail,
        particularly Hormuz, expect $100-115+. The Monte Carlo above gives you the statistical distribution
        based on historical volatility.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)


# ===== CONFLICT INTEL =====
if show_conflict:
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## ⚠️ Strait of Hormuz / Iran Conflict Intel")

    st.markdown("""
    <div class='conflict-card'>
        <div style='font-size:18px;font-weight:700;color:#fca5a5;margin-bottom:14px;'>
            Active Conflict Summary (as of March 20, 2026)
        </div>
        <div style='font-size:14px;color:#cbd5e1;line-height:1.8;'>

        <p><strong style='color:#f97316;'>TIMELINE OF EVENTS:</strong></p>
        <ul style='margin-left:18px;'>
            <li><strong>Feb 28:</strong> US launched Operation Epic Fury. Joint US-Israeli air and maritime strikes on Iran, killing
            Supreme Leader Ali Khamenei. Targets included IRGC HQ, ballistic missile sites, naval assets, air defense, and military airfields.
            CENTCOM reported 17+ Iranian ships destroyed. "Not a single Iranian ship underway" in the Gulf.</li>
            <li><strong>Mar 1-2:</strong> Iran retaliates with missile and drone strikes on US bases, Israeli territory, and Gulf states (UAE, Saudi Arabia).
            IRGC declares Strait of Hormuz "closed." Brent opens ~$85-90 from Friday's $73.</li>
            <li><strong>Mar 4:</strong> Iran formally announces Strait closure, begins attacking transiting vessels. Tanker traffic drops ~70% immediately.
            150+ ships anchor outside the strait.</li>
            <li><strong>Mar 5:</strong> IRGC clarifies closure applies only to US, Israel, and Western-allied ships. China-flagged vessels begin testing transit.</li>
            <li><strong>Mar 8:</strong> Brent surpasses $100/bbl for first time since 2022. Rises to $126 peak.</li>
            <li><strong>Mar 11:</strong> IEA member countries agree to release 400M barrels from emergency reserves (largest since 2022 Ukraine release). US commits 172M barrels from SPR.</li>
            <li><strong>Mar 12-13:</strong> 21 confirmed Iranian attacks on merchant vessels. 7 seafarers killed (IMO). A China-owned vessel hit despite broadcasting "China Owner" via AIS.</li>
            <li><strong>Mar 14:</strong> Iran strikes UAE Shah gas field (drone), Fujairah Oil Industry Zone fire, another tanker hit. 3+ mb/d of Gulf refining shut.</li>
            <li><strong>Mar 16:</strong> Pakistan tanker crosses Hormuz with Iranian permission. First confirmed non-Iranian cargo vessel since closure. Dubai airport fire from drone-related fuel tank hit. UAE briefly closes airspace.</li>
            <li><strong>Mar 17:</strong> New Supreme Leader Mojtaba Khamenei vows to maintain Strait blockade. QatarEnergy declares force majeure after Ras Laffan LNG facility strikes. Says repairs could take up to 5 years.</li>
            <li><strong>Mar 18:</strong> Turkish ship permitted to transit. Indian gas carriers and Saudi oil tanker (1M bbl for India) allowed through.
            Iran drone strikes on Oman's Duqm and Salalah ports (Hormuz bypass routes). Fuel storage damaged at Duqm.</li>
            <li><strong>Mar 19:</strong> Brent spikes to $119/bbl intraday after Israeli strike on Iran's South Pars gas field and Iranian
            retaliation against Qatar's Ras Laffan (world's largest LNG facility). Settles at $108.65.</li>
            <li><strong>Mar 20 (Today):</strong> Brent at ~$107-110. Only 21 tankers have transited the strait since Feb 28 (vs 100+/day normally).
            ~400 vessels waiting in Gulf of Oman. US considers intercepting Iranian crude tankers and deploying additional carrier strike group.</li>
        </ul>

        <p><strong style='color:#f97316;'>KEY MARKET IMPACTS:</strong></p>
        <ul style='margin-left:18px;'>
            <li><strong>~20% of global seaborne oil (20M b/d)</strong> normally flows through Hormuz. Effectively halted for most operators.</li>
            <li><strong>Iran still exporting to China:</strong> 11.7M barrels shipped since Feb 28, all to China. But rate (1.22 mb/d) is down from 2.16 mb/d pre-war.</li>
            <li><strong>Gulf production cuts:</strong> Saudi Arabia reducing output as onshore storage fills. Iraq's Kurdish fields halted as precaution.</li>
            <li><strong>Bypass routes degraded:</strong> UAE's Fujairah (key export hub outside Hormuz) under repeated attack. Oman's Duqm damaged. Sohar in insurer war-risk zone.</li>
            <li><strong>LNG crisis:</strong> European gas surged from ~30 to 60+ EUR/MWh. QatarEnergy's 17% capacity loss could take years to restore.</li>
            <li><strong>Insurance:</strong> War-risk premiums jumped from 0.125% to 0.2-0.4% of hull value. Most commercial insurers have withdrawn from the corridor.</li>
            <li><strong>Fed impact:</strong> Rate cut expectations collapsed. 73% probability of no cuts in 2026 (was 74% chance of 2+ cuts one month ago).</li>
        </ul>

        <p><strong style='color:#f97316;'>WHAT TO WATCH:</strong></p>
        <ul style='margin-left:18px;'>
            <li><strong>Hormuz reopening signals:</strong> Frequency of permitted transits, insurance market moves, CENTCOM de-mining operations.</li>
            <li><strong>OPEC+ April 5 meeting:</strong> Will they accelerate output increases beyond 206K b/d?</li>
            <li><strong>US Kharg Island strikes:</strong> Friday overnight attacks targeted Iran's main oil export hub. If successful, Iran's leverage diminishes.</li>
            <li><strong>IEA April 7 STEO update:</strong> Will reflect actual March disruption data.</li>
            <li><strong>Ceasefire/negotiation track:</strong> Countries are striking bilateral deals with Iran for transit (Pakistan, Turkey, India). If this de facto "permission-based" transit becomes the norm, gradual normalization begins.</li>
        </ul>

        </div>
    </div>
    """, unsafe_allow_html=True)


# ===== OHLC TABLE =====
st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("### Recent Sessions")

if not hist_1y.empty:
    recent = hist_1y.tail(15).copy()
    recent = recent.sort_index(ascending=False)
    recent["Change"] = recent["Close"] - recent["Close"].shift(-1)
    recent["Change%"] = (recent["Change"] / recent["Close"].shift(-1)) * 100

    display_df = pd.DataFrame({
        "Date": recent.index.strftime("%Y-%m-%d"),
        "Open": recent["Open"].round(2),
        "High": recent["High"].round(2),
        "Low": recent["Low"].round(2),
        "Close": recent["Close"].round(2),
        "Change": recent["Change"].round(2),
        "Change%": recent["Change%"].round(2),
        "Volume": recent["Volume"].astype(int),
    })
    display_df = display_df.reset_index(drop=True)

    st.dataframe(
        display_df.style.format({
            "Open": "${:.2f}",
            "High": "${:.2f}",
            "Low": "${:.2f}",
            "Close": "${:.2f}",
            "Change": "${:+.2f}",
            "Change%": "{:+.2f}%",
            "Volume": "{:,.0f}",
        }).applymap(
            lambda v: "color: #22c55e" if isinstance(v, (int, float)) and v > 0 else "color: #ef4444" if isinstance(v, (int, float)) and v < 0 else "",
            subset=["Change", "Change%"],
        ),
        use_container_width=True,
        height=400,
    )


# ===== AUTO REFRESH =====
st.markdown(f"""
<div style='text-align:center;margin-top:24px;font-size:10px;color:#334155;font-family:"JetBrains Mono",monospace;
border-top:1px solid rgba(100,116,139,0.08);padding-top:16px;'>
Data: Yahoo Finance (BZ=F, CL=F) &middot; Monte Carlo: {mc_results['n_sims']:,} GBM sims, trailing 1Y vol &middot; Analyst forecasts from EIA, GS, StanChart, Fitch, JPM<br>
Conflict data sourced from CRS, IEA, Bloomberg, CNBC, Reuters, Al Jazeera &middot; Not financial advice &middot; Dashboard built {datetime.now().strftime("%Y-%m-%d")}
</div>
""", unsafe_allow_html=True)

# Auto-rerun every 30 seconds
time.sleep(REFRESH_INTERVAL)
st.rerun()
