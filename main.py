#!/usr/bin/env python3
"""
BRENT CRUDE OIL - LIVE TRACKER & PREDICTIVE ANALYTICS DASHBOARD
================================================================
Run:  pip install -r requirements.txt
      streamlit run main.py

Features:
  - Real-time Brent/WTI via yfinance (30s auto-refresh)
  - Technical indicators: SMA, EMA, Bollinger Bands, RSI, MACD
  - Regime-aware Monte Carlo (conflict vs. normal volatility)
  - User-selectable prediction date with confidence intervals
  - Iran/Hormuz conflict timeline and status tracker
  - Analyst forecast consensus band
  - Supply/demand fundamentals
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from scipy import stats as sp_stats
import time
import warnings

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Brent Crude - Live Tracker & Analytics",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

TARGET_PRICE = 94.50
TARGET_DATE = datetime(2026, 6, 15)
TARGET_DATE_STR = "June 15, 2026"
REFRESH_INTERVAL = 30

# Conflict start date
CONFLICT_START = datetime(2026, 2, 28)

# ---------------------------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

    .stApp { background: linear-gradient(165deg, #06080f 0%, #0c1019 40%, #0f1520 100%); }
    .main .block-container { padding-top: 1.5rem; max-width: 1400px; }
    h1,h2,h3,h4,h5,h6 { font-family: 'Outfit', sans-serif !important; }
    p, span, div, li { font-family: 'Outfit', sans-serif; }

    .big-price {
        font-family: 'Outfit', sans-serif; font-size: 56px; font-weight: 800;
        letter-spacing: -2px; text-shadow: 0 0 40px rgba(34,211,238,0.15); line-height: 1.1;
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
        background: rgba(15,21,32,0.7); border: 1px solid rgba(100,116,139,0.12);
        border-radius: 12px; padding: 16px 18px; margin-bottom: 8px;
    }
    .metric-label {
        font-size: 10px; color: #64748b; letter-spacing: 1.5px; text-transform: uppercase;
        font-family: 'JetBrains Mono', monospace; margin-bottom: 6px;
    }
    .metric-value { font-size: 18px; font-weight: 700; color: #f1f5f9; }

    .conflict-card {
        background: linear-gradient(135deg, rgba(239,68,68,0.06) 0%, rgba(249,115,22,0.04) 100%);
        border: 1px solid rgba(239,68,68,0.2); border-radius: 14px; padding: 20px 24px;
    }
    .target-card {
        background: linear-gradient(135deg, rgba(34,211,238,0.06) 0%, rgba(167,139,250,0.04) 100%);
        border: 1px solid rgba(34,211,238,0.2); border-radius: 14px; padding: 20px 24px;
    }
    .analyst-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 0; border-bottom: 1px solid rgba(100,116,139,0.08); font-size: 13px;
    }
    .status-badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 11px;
        font-weight: 700; letter-spacing: 1px; font-family: 'JetBrains Mono', monospace;
    }
    .status-critical { background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.4); }
    .status-elevated { background: rgba(249,115,22,0.2); color: #fdba74; border: 1px solid rgba(249,115,22,0.4); }
    .status-normal { background: rgba(34,197,94,0.2); color: #86efac; border: 1px solid rgba(34,197,94,0.4); }

    .live-pulse {
        display: inline-block; width: 10px; height: 10px; border-radius: 50%;
        animation: pulse 2s infinite; margin-right: 8px; vertical-align: middle;
    }
    @keyframes pulse { 0%,100%{opacity:1;transform:scale(1);} 50%{opacity:0.4;transform:scale(1.4);} }

    div[data-testid="stSidebar"] {
        background: rgba(8,10,18,0.95); border-right: 1px solid rgba(100,116,139,0.1);
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DATA FETCHING
# ---------------------------------------------------------------------------
@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_market_data():
    """Pull live Brent + WTI data from Yahoo Finance with error handling."""
    result = {
        "intraday": pd.DataFrame(),
        "hist_1y": pd.DataFrame(),
        "hist_5y": pd.DataFrame(),
        "wti_1y": pd.DataFrame(),
        "wti_intraday": pd.DataFrame(),
        "info": None,
        "fetch_time": datetime.now(),
        "error": None,
    }
    try:
        brent = yf.Ticker("BZ=F")
        wti = yf.Ticker("CL=F")

        result["intraday"] = brent.history(period="1d", interval="1m")
        result["hist_1y"] = brent.history(period="1y", interval="1d")
        result["hist_5y"] = brent.history(period="5y", interval="1wk")
        result["wti_1y"] = wti.history(period="1y", interval="1d")
        result["wti_intraday"] = wti.history(period="1d", interval="1m")
        result["info"] = brent.fast_info
    except Exception as e:
        result["error"] = str(e)
    return result


# ---------------------------------------------------------------------------
# TECHNICAL INDICATORS
# ---------------------------------------------------------------------------
def compute_technicals(df):
    """Compute SMA, EMA, Bollinger Bands, RSI, MACD on a daily close series."""
    if df.empty or len(df) < 30:
        return df

    out = df.copy()
    c = out["Close"]

    # Moving averages
    out["SMA_20"] = c.rolling(20).mean()
    out["SMA_50"] = c.rolling(50).mean()
    out["SMA_200"] = c.rolling(200).mean()
    out["EMA_12"] = c.ewm(span=12, adjust=False).mean()
    out["EMA_26"] = c.ewm(span=26, adjust=False).mean()

    # Bollinger Bands (20-day, 2 std)
    out["BB_mid"] = out["SMA_20"]
    bb_std = c.rolling(20).std()
    out["BB_upper"] = out["BB_mid"] + 2 * bb_std
    out["BB_lower"] = out["BB_mid"] - 2 * bb_std

    # RSI (14-day)
    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    out["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    out["MACD"] = out["EMA_12"] - out["EMA_26"]
    out["MACD_signal"] = out["MACD"].ewm(span=9, adjust=False).mean()
    out["MACD_hist"] = out["MACD"] - out["MACD_signal"]

    # ATR (14-day Average True Range)
    high = out["High"]
    low = out["Low"]
    prev_c = c.shift(1)
    tr = pd.concat([high - low, (high - prev_c).abs(), (low - prev_c).abs()], axis=1).max(axis=1)
    out["ATR_14"] = tr.rolling(14).mean()

    return out


# ---------------------------------------------------------------------------
# PREDICTIVE ANALYTICS - REGIME-AWARE MONTE CARLO
# ---------------------------------------------------------------------------
def regime_monte_carlo(hist_df, current_price, target_price, days_to_target,
                       conflict_active=True, n_sims=100_000):
    """
    Regime-switching Monte Carlo:
      - Normal regime: uses pre-conflict historical vol
      - Conflict regime: uses post-conflict vol (elevated)
      - Transition probability: models gradual de-escalation
    """
    if hist_df.empty or len(hist_df) < 60:
        return None, None, None

    closes = hist_df["Close"].dropna()
    log_returns = np.log(closes / closes.shift(1)).dropna()

    # Split into pre-conflict and conflict regimes
    conflict_start_idx = hist_df.index.get_indexer(
        [pd.Timestamp(CONFLICT_START)], method="nearest"
    )[0]

    if conflict_start_idx > 30 and conflict_start_idx < len(log_returns):
        pre_returns = log_returns.iloc[:conflict_start_idx]
        post_returns = log_returns.iloc[conflict_start_idx:]

        mu_normal = pre_returns.mean()
        sigma_normal = pre_returns.std()
        mu_conflict = post_returns.mean()
        sigma_conflict = post_returns.std()
    else:
        mu_normal = log_returns.mean()
        sigma_normal = log_returns.std()
        mu_conflict = mu_normal * 1.5
        sigma_conflict = sigma_normal * 2.0

    n_days = max(1, days_to_target)
    np.random.seed(42)

    # Regime transition: probability of de-escalation increases over time
    # P(transition to normal on day t) = min(0.02 * t/30, 0.8)
    price_paths = np.zeros((n_sims, n_days))
    price_paths[:, 0] = current_price

    in_conflict = np.ones(n_sims, dtype=bool) if conflict_active else np.zeros(n_sims, dtype=bool)

    for t in range(1, n_days):
        # Transition probability increases over time
        p_deescalate = min(0.015 * t / 30, 0.6) if conflict_active else 0.0
        transitions = np.random.random(n_sims) < p_deescalate
        in_conflict = in_conflict & ~transitions

        # Generate returns based on regime
        normal_shock = np.random.normal(mu_normal, sigma_normal, n_sims)
        conflict_shock = np.random.normal(mu_conflict, sigma_conflict, n_sims)

        shocks = np.where(in_conflict, conflict_shock, normal_shock)
        price_paths[:, t] = price_paths[:, t - 1] * np.exp(shocks)

    final_prices = price_paths[:, -1]

    # Compute stats
    results = {
        "prob_within_3": round(np.mean(np.abs(final_prices - target_price) <= 3) * 100, 1),
        "prob_within_5": round(np.mean(np.abs(final_prices - target_price) <= 5) * 100, 1),
        "prob_at_or_below": round(np.mean(final_prices <= target_price) * 100, 1),
        "prob_above_100": round(np.mean(final_prices > 100) * 100, 1),
        "prob_above_120": round(np.mean(final_prices > 120) * 100, 1),
        "prob_below_80": round(np.mean(final_prices < 80) * 100, 1),
        "p5": round(np.percentile(final_prices, 5), 2),
        "p10": round(np.percentile(final_prices, 10), 2),
        "p25": round(np.percentile(final_prices, 25), 2),
        "median": round(np.percentile(final_prices, 50), 2),
        "p75": round(np.percentile(final_prices, 75), 2),
        "p90": round(np.percentile(final_prices, 90), 2),
        "p95": round(np.percentile(final_prices, 95), 2),
        "mean": round(np.mean(final_prices), 2),
        "mu_normal": round(mu_normal * 252 * 100, 1),
        "sigma_normal": round(sigma_normal * np.sqrt(252) * 100, 1),
        "mu_conflict": round(mu_conflict * 252 * 100, 1),
        "sigma_conflict": round(sigma_conflict * np.sqrt(252) * 100, 1),
        "n_sims": n_sims,
        "pct_still_conflict": round(np.mean(in_conflict) * 100, 1),
    }

    return results, price_paths, final_prices


def predict_price_on_date(hist_df, current_price, target_date, conflict_active=True):
    """Predict price on a specific user-chosen date with confidence intervals."""
    days_out = (target_date - datetime.now()).days
    if days_out <= 0:
        return None
    results, paths, finals = regime_monte_carlo(
        hist_df, current_price, 0, days_out, conflict_active, n_sims=50_000
    )
    if results is None:
        return None
    results["target_date"] = target_date.strftime("%B %d, %Y")
    results["days_out"] = days_out
    return results


# ---------------------------------------------------------------------------
# CONFLICT EVENT LOG
# ---------------------------------------------------------------------------
CONFLICT_EVENTS = [
    {"date": "Feb 28", "severity": "critical", "event": "US launches Operation Epic Fury. Joint US-Israeli strikes kill Supreme Leader Ali Khamenei. 17+ Iranian naval vessels destroyed. CENTCOM: 'Not a single Iranian ship underway.'"},
    {"date": "Mar 1-2", "severity": "critical", "event": "Iran retaliates: missiles/drones on US bases, Israel, UAE, Saudi. IRGC declares Hormuz 'closed.' Brent gaps from $73 to ~$85-90."},
    {"date": "Mar 4", "severity": "critical", "event": "Iran formally closes Strait. Attacks on transiting vessels begin. Tanker traffic drops 70%. 150+ ships anchor outside."},
    {"date": "Mar 5", "severity": "elevated", "event": "IRGC clarifies: closure targets US/Israel/Western-allied ships only. China-flagged vessels test transit."},
    {"date": "Mar 8", "severity": "critical", "event": "Brent passes $100/bbl (first since 2022). Peaks at $126 intraday."},
    {"date": "Mar 11", "severity": "elevated", "event": "IEA agrees to release 400M barrels from emergency reserves (largest since 2022). US commits 172M from SPR."},
    {"date": "Mar 12-13", "severity": "critical", "event": "21 confirmed Iranian attacks on merchant vessels. 7 seafarers killed (IMO). China-owned vessel hit despite AIS broadcast."},
    {"date": "Mar 14", "severity": "critical", "event": "Iran strikes UAE Shah gas field (drone), Fujairah Oil Industry Zone fire. 3+ mb/d of Gulf refining shut."},
    {"date": "Mar 16", "severity": "elevated", "event": "Pakistan tanker crosses Hormuz with Iranian permission (first non-Iranian cargo since closure). Dubai airport fire from drone fuel tank hit."},
    {"date": "Mar 17", "severity": "critical", "event": "New Supreme Leader Mojtaba Khamenei vows to maintain blockade. QatarEnergy force majeure on Ras Laffan LNG. Repairs: up to 5 years."},
    {"date": "Mar 18", "severity": "elevated", "event": "Turkish, Indian, Saudi ships permitted to transit. Iran strikes Oman bypass ports (Duqm, Salalah). Fuel storage damaged."},
    {"date": "Mar 19", "severity": "critical", "event": "Israeli strike on Iran's South Pars. Iran retaliates against Ras Laffan. Brent spikes $119 intraday, settles $108.65."},
    {"date": "Mar 20", "severity": "critical", "event": "Brent ~$107-110. Only 21 tanker transits since Feb 28 (vs 100+/day). ~400 vessels waiting. US considers intercepting Iranian crude tankers."},
]


def get_hormuz_status():
    """Current Strait of Hormuz operational status."""
    return {
        "status": "CRITICAL",
        "tanker_transits_since_conflict": 21,
        "normal_daily_transits": "100+",
        "vessels_waiting": "~400",
        "flow_disrupted_pct": 95,
        "oil_flow_mbpd_normal": 20.0,
        "oil_flow_mbpd_current": "~1.0 (Iran-to-China only)",
        "insurance_war_risk": "0.2-0.4% hull value",
        "permitted_flags": ["Pakistan", "Turkey", "India", "Saudi (for India)"],
        "blocked_flags": ["US", "Israel", "UK", "EU-flagged", "most Western"],
        "days_since_closure": (datetime.now() - datetime(2026, 3, 4)).days,
    }


# ---------------------------------------------------------------------------
# CHART CONFIG
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
        bgcolor="rgba(10,12,18,0.95)", bordercolor="rgba(34,211,238,0.3)",
        font=dict(family="JetBrains Mono, monospace", size=12),
    ),
)


# ---------------------------------------------------------------------------
# CHART BUILDERS
# ---------------------------------------------------------------------------
def make_intraday_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"], mode="lines",
        line=dict(color="#22d3ee", width=2),
        fill="tozeroy", fillcolor="rgba(34,211,238,0.08)",
        name="Brent", hovertemplate="$%{y:.2f}<extra></extra>",
    ))
    fig.update_layout(
        **CHART_LAYOUT, height=300,
        title=dict(text="Intraday (1-min bars)", font=dict(size=15, color="#f1f5f9")),
        yaxis=dict(title="USD/bbl", tickprefix="$", **CHART_LAYOUT["yaxis"]),
        xaxis=dict(title="", **CHART_LAYOUT["xaxis"]),
        showlegend=False,
    )
    return fig


def make_technical_chart(df, show_bb=True, show_sma=True):
    """Price chart with optional Bollinger Bands, SMAs, and volume."""
    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True,
        row_heights=[0.50, 0.18, 0.18, 0.14],
        vertical_spacing=0.02,
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        increasing_line_color="#22c55e", decreasing_line_color="#ef4444",
        increasing_fillcolor="rgba(34,197,94,0.4)", decreasing_fillcolor="rgba(239,68,68,0.4)",
        name="OHLC", showlegend=False,
    ), row=1, col=1)

    # SMAs
    if show_sma:
        for col_name, color, label in [
            ("SMA_20", "#22d3ee", "SMA 20"),
            ("SMA_50", "#f97316", "SMA 50"),
            ("SMA_200", "#a78bfa", "SMA 200"),
        ]:
            if col_name in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[col_name], mode="lines",
                    line=dict(color=color, width=1.2, dash="dot"),
                    name=label, hovertemplate="$%{y:.2f}<extra></extra>",
                ), row=1, col=1)

    # Bollinger Bands
    if show_bb and "BB_upper" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_upper"], mode="lines",
            line=dict(color="rgba(251,191,36,0.4)", width=1), name="BB Upper",
            showlegend=False, hovertemplate="$%{y:.2f}<extra></extra>",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_lower"], mode="lines",
            line=dict(color="rgba(251,191,36,0.4)", width=1), name="BB Lower",
            fill="tonexty", fillcolor="rgba(251,191,36,0.04)",
            showlegend=False, hovertemplate="$%{y:.2f}<extra></extra>",
        ), row=1, col=1)

    # RSI
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["RSI"], mode="lines",
            line=dict(color="#22d3ee", width=1.5), name="RSI",
            hovertemplate="%{y:.1f}<extra></extra>",
        ), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="rgba(239,68,68,0.4)", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="rgba(34,197,94,0.4)", row=2, col=1)

    # MACD
    if "MACD" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MACD"], mode="lines",
            line=dict(color="#f97316", width=1.5), name="MACD",
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MACD_signal"], mode="lines",
            line=dict(color="#a78bfa", width=1.2, dash="dot"), name="Signal",
        ), row=3, col=1)
        if "MACD_hist" in df.columns:
            colors = ["#22c55e" if v >= 0 else "#ef4444" for v in df["MACD_hist"]]
            fig.add_trace(go.Bar(
                x=df.index, y=df["MACD_hist"], marker_color=colors, opacity=0.5,
                name="MACD Hist", showlegend=False,
            ), row=3, col=1)

    # Volume
    if "Volume" in df.columns:
        vol_colors = ["#22c55e" if c >= o else "#ef4444"
                      for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"], marker_color=vol_colors, opacity=0.4,
            name="Volume", showlegend=False,
        ), row=4, col=1)

    fig.update_layout(
        **CHART_LAYOUT, height=700, showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(size=10)),
        title=dict(text="Brent Crude - Technical Analysis", font=dict(size=16, color="#f1f5f9")),
        xaxis_rangeslider_visible=False,
    )
    fig.update_yaxes(title="USD/bbl", tickprefix="$", row=1, col=1, gridcolor="rgba(100,116,139,0.08)")
    fig.update_yaxes(title="RSI", row=2, col=1, range=[0, 100], gridcolor="rgba(100,116,139,0.08)")
    fig.update_yaxes(title="MACD", row=3, col=1, gridcolor="rgba(100,116,139,0.08)")
    fig.update_yaxes(title="Vol", row=4, col=1, gridcolor="rgba(100,116,139,0.08)")
    for i in range(1, 5):
        fig.update_xaxes(gridcolor="rgba(100,116,139,0.08)", row=i, col=1)

    return fig


def make_spread_chart(brent_df, wti_df):
    merged = pd.DataFrame({"Brent": brent_df["Close"], "WTI": wti_df["Close"]}).dropna()
    merged["Spread"] = merged["Brent"] - merged["WTI"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=merged.index, y=merged["Spread"], mode="lines",
        line=dict(color="#a78bfa", width=2), fill="tozeroy",
        fillcolor="rgba(167,139,250,0.08)", hovertemplate="$%{y:.2f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color="rgba(100,116,139,0.3)", line_width=1)
    fig.update_layout(
        **CHART_LAYOUT, height=300,
        title=dict(text="Brent-WTI Spread", font=dict(size=15, color="#f1f5f9")),
        yaxis=dict(title="$/bbl", tickprefix="$", **CHART_LAYOUT["yaxis"]),
        showlegend=False,
    )
    return fig


def make_supply_demand_chart():
    quarters = ["Q3 '25", "Q4 '25", "Q1 '26", "Q2 '26F", "Q3 '26F", "Q4 '26F"]
    supply = [108.0, 107.2, 106.6, 107.8, 108.5, 109.2]
    demand = [106.1, 105.8, 105.9, 106.5, 107.1, 107.5]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Supply", x=quarters, y=supply,
                         marker_color="rgba(34,211,238,0.7)", text=[f"{v}" for v in supply],
                         textposition="outside", textfont=dict(size=10, color="#94a3b8")))
    fig.add_trace(go.Bar(name="Demand", x=quarters, y=demand,
                         marker_color="rgba(249,115,22,0.7)", text=[f"{v}" for v in demand],
                         textposition="outside", textfont=dict(size=10, color="#94a3b8")))
    fig.update_layout(
        **CHART_LAYOUT, height=350, barmode="group",
        title=dict(text="Global Oil Supply vs Demand (mb/d)", font=dict(size=15, color="#f1f5f9")),
        yaxis=dict(range=[103, 111], title="mb/d", **CHART_LAYOUT["yaxis"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
    )
    return fig


def make_inventory_chart():
    regions = ["OECD", "China Crude", "Oil on Water", "Other Non-OECD"]
    values = [4.10, 1.23, 2.05, 0.82]
    colors = ["#22d3ee", "#f97316", "#a78bfa", "#22c55e"]
    fig = go.Figure(go.Pie(
        labels=regions, values=values, hole=0.55,
        marker=dict(colors=colors, line=dict(color="#0c1019", width=2)),
        textinfo="label+percent", textfont=dict(size=12, color="#e2e8f0"),
        hovertemplate="%{label}: %{value:.2f}B bbl<extra></extra>",
    ))
    fig.update_layout(
        **CHART_LAYOUT, height=350,
        title=dict(text="Global Oil Inventory (8.2B bbl total)", font=dict(size=15, color="#f1f5f9")),
        annotations=[dict(text="8.2B<br>bbl", x=0.5, y=0.5, font_size=18, font_color="#f1f5f9", showarrow=False)],
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=11)),
    )
    return fig


def make_monte_carlo_chart(final_prices, target_price, current_price, custom_label=None):
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=final_prices, nbinsx=150,
        marker_color="rgba(34,211,238,0.35)", marker_line_color="rgba(34,211,238,0.5)",
        marker_line_width=0.5, hovertemplate="$%{x:.0f}: %{y:,} sims<extra></extra>",
    ))
    fig.add_vline(x=target_price, line_dash="dash", line_color="#22c55e", line_width=2,
                  annotation_text=f"Target ${target_price}", annotation_font_color="#22c55e", annotation_font_size=11)
    fig.add_vline(x=current_price, line_dash="dot", line_color="#f97316", line_width=2,
                  annotation_text=f"Current ${current_price:.2f}", annotation_font_color="#f97316", annotation_font_size=11)

    # Add confidence interval shading
    p10 = np.percentile(final_prices, 10)
    p90 = np.percentile(final_prices, 90)
    fig.add_vrect(x0=p10, x1=p90, fillcolor="rgba(167,139,250,0.08)", line_width=0,
                  annotation_text="80% CI", annotation_position="top left",
                  annotation_font_color="#a78bfa", annotation_font_size=10)

    title_text = custom_label or "Regime-Aware Monte Carlo Distribution"
    fig.update_layout(
        **CHART_LAYOUT, height=350,
        title=dict(text=title_text, font=dict(size=15, color="#f1f5f9")),
        xaxis=dict(title="Price (USD/bbl)", tickprefix="$", **CHART_LAYOUT["xaxis"]),
        yaxis=dict(title="Frequency", **CHART_LAYOUT["yaxis"]),
        showlegend=False,
    )
    return fig


def make_prediction_fan_chart(price_paths, current_price, days, target_price=None):
    """Fan chart showing percentile bands over time."""
    n_days = min(days, price_paths.shape[1])
    x_dates = [datetime.now() + timedelta(days=i) for i in range(n_days)]

    p5 = np.percentile(price_paths[:, :n_days], 5, axis=0)
    p10 = np.percentile(price_paths[:, :n_days], 10, axis=0)
    p25 = np.percentile(price_paths[:, :n_days], 25, axis=0)
    p50 = np.percentile(price_paths[:, :n_days], 50, axis=0)
    p75 = np.percentile(price_paths[:, :n_days], 75, axis=0)
    p90 = np.percentile(price_paths[:, :n_days], 90, axis=0)
    p95 = np.percentile(price_paths[:, :n_days], 95, axis=0)

    fig = go.Figure()

    # 90% band
    fig.add_trace(go.Scatter(x=x_dates, y=p95, mode="lines", line=dict(width=0),
                             showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x_dates, y=p5, mode="lines", line=dict(width=0),
                             fill="tonexty", fillcolor="rgba(34,211,238,0.06)",
                             name="90% CI", hoverinfo="skip"))

    # 50% band
    fig.add_trace(go.Scatter(x=x_dates, y=p75, mode="lines", line=dict(width=0),
                             showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x_dates, y=p25, mode="lines", line=dict(width=0),
                             fill="tonexty", fillcolor="rgba(34,211,238,0.12)",
                             name="50% CI", hoverinfo="skip"))

    # Median
    fig.add_trace(go.Scatter(x=x_dates, y=p50, mode="lines",
                             line=dict(color="#22d3ee", width=2.5), name="Median",
                             hovertemplate="$%{y:.2f}<extra></extra>"))

    # Target line
    if target_price:
        fig.add_hline(y=target_price, line_dash="dash", line_color="rgba(34,197,94,0.5)",
                      annotation_text=f"Target ${target_price}", annotation_font_color="#22c55e",
                      annotation_font_size=11)

    # Current price start
    fig.add_hline(y=current_price, line_dash="dot", line_color="rgba(249,115,22,0.3)", line_width=1)

    fig.update_layout(
        **CHART_LAYOUT, height=400,
        title=dict(text="Price Prediction Fan Chart (Regime-Aware)", font=dict(size=15, color="#f1f5f9")),
        yaxis=dict(title="USD/bbl", tickprefix="$", **CHART_LAYOUT["yaxis"]),
        xaxis=dict(title="", **CHART_LAYOUT["xaxis"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
    )
    return fig


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛢️ Dashboard Controls")
    st.markdown("---")

    chart_range = st.selectbox("Historical Range", ["1 Month", "3 Months", "6 Months", "1 Year"], index=2)
    show_technicals = st.checkbox("Technical Indicators", value=True)
    show_bollinger = st.checkbox("Bollinger Bands", value=True)
    show_monte_carlo = st.checkbox("Monte Carlo Analysis", value=True)
    show_fan_chart = st.checkbox("Prediction Fan Chart", value=True)
    show_conflict = st.checkbox("Conflict Intel", value=True)

    st.markdown("---")
    st.markdown("#### Custom Price Prediction")
    pred_date = st.date_input(
        "Predict price on date",
        value=TARGET_DATE.date(),
        min_value=datetime.now().date() + timedelta(days=1),
        max_value=datetime(2027, 12, 31).date(),
    )
    conflict_assumption = st.selectbox(
        "Conflict regime",
        ["Active (current)", "De-escalating", "Resolved"],
        index=0,
    )

    st.markdown("---")
    st.markdown("#### Primary Target")
    st.markdown(f"""
    <div class='target-card'>
        <div class='metric-label'>CLOSE BY {TARGET_DATE_STR.upper()}</div>
        <div style='font-size:28px;font-weight:800;color:#22d3ee;'>${TARGET_PRICE:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Hormuz quick status
    hz = get_hormuz_status()
    status_class = "status-critical" if hz["status"] == "CRITICAL" else "status-elevated"
    st.markdown(f"""
    <div class='metric-card' style='border-left:3px solid #ef4444;'>
        <div class='metric-label'>STRAIT OF HORMUZ</div>
        <div style='margin-top:6px;'>
            <span class='status-badge {status_class}'>{hz["status"]}</span>
        </div>
        <div style='margin-top:10px;font-size:12px;color:#94a3b8;line-height:1.6;'>
            Day {hz["days_since_closure"]} of closure<br>
            {hz["tanker_transits_since_conflict"]} transits since Feb 28<br>
            {hz["vessels_waiting"]} vessels waiting<br>
            ~{hz["flow_disrupted_pct"]}% flow disrupted
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='dim mono' style='margin-top:12px;'>
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
data = fetch_market_data()

if data["error"]:
    st.error(f"Data fetch error: {data['error']}. Retrying in {REFRESH_INTERVAL}s...")
    time.sleep(REFRESH_INTERVAL)
    st.rerun()

info = data["info"]
intraday = data["intraday"]
hist_1y = data["hist_1y"]
hist_5y = data["hist_5y"]
wti_1y = data["wti_1y"]

# Safe extraction of price info
def safe_attr(obj, attr, default=0):
    try:
        val = getattr(obj, attr, default)
        return round(float(val), 2) if val is not None else default
    except Exception:
        return default

if not intraday.empty:
    current_price = round(float(intraday["Close"].iloc[-1]), 2)
    prev_close = safe_attr(info, "previous_close", current_price)
    change = round(current_price - prev_close, 2)
    change_pct = round((change / prev_close) * 100, 2) if prev_close else 0
    is_up = change >= 0
else:
    current_price = prev_close = 0
    change = change_pct = 0
    is_up = True

day_high = safe_attr(info, "day_high")
day_low = safe_attr(info, "day_low")
year_high = safe_attr(info, "year_high")
year_low = safe_attr(info, "year_low")
open_price = safe_attr(info, "open")

wti_price = round(float(data["wti_intraday"]["Close"].iloc[-1]), 2) if not data["wti_intraday"].empty else 0
spread = round(current_price - wti_price, 2) if wti_price else 0

yoy = None
if len(hist_1y) > 5:
    first_price = float(hist_1y["Close"].iloc[0])
    if first_price > 0:
        yoy = round(((current_price - first_price) / first_price) * 100, 1)

days_to_target = (TARGET_DATE - datetime.now()).days

# Compute technicals
tech_df = compute_technicals(hist_1y) if not hist_1y.empty else hist_1y
current_rsi = round(float(tech_df["RSI"].iloc[-1]), 1) if "RSI" in tech_df.columns and not tech_df["RSI"].isna().iloc[-1] else None
current_atr = round(float(tech_df["ATR_14"].iloc[-1]), 2) if "ATR_14" in tech_df.columns and not tech_df["ATR_14"].isna().iloc[-1] else None

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
    rsi_color = "#ef4444" if current_rsi and current_rsi > 70 else "#22c55e" if current_rsi and current_rsi < 30 else "#fbbf24"
    rsi_label = "OVERBOUGHT" if current_rsi and current_rsi > 70 else "OVERSOLD" if current_rsi and current_rsi < 30 else "NEUTRAL"
    st.markdown(f"""
    <div style='text-align:right;'>
        <div style='background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.3);border-radius:8px;padding:8px 14px;display:inline-block;margin-bottom:6px;'>
            <span class='mono' style='font-size:12px;font-weight:600;color:#fca5a5;'>
                52W HIGH ${year_high:.2f} &middot; LOW ${year_low:.2f}
            </span>
        </div><br>
        <div style='background:rgba(167,139,250,0.1);border:1px solid rgba(167,139,250,0.25);border-radius:8px;padding:8px 14px;display:inline-block;margin-bottom:6px;'>
            <span class='mono' style='font-size:12px;font-weight:600;color:#c4b5fd;'>
                Spread: ${spread:.2f} &middot; ATR(14): ${current_atr if current_atr else 'N/A'}
            </span>
        </div><br>
        <div style='background:rgba({rsi_color[1:][:2]},{rsi_color[1:][2:4]},{rsi_color[1:][4:]},0.1);border:1px solid {rsi_color}40;border-radius:8px;padding:8px 14px;display:inline-block;'>
            <span class='mono' style='font-size:12px;font-weight:600;color:{rsi_color};'>
                RSI(14): {current_rsi if current_rsi else 'N/A'} &middot; {rsi_label}
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

# ===== INTRADAY =====
st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
if not intraday.empty:
    st.plotly_chart(make_intraday_chart(intraday), use_container_width=True)

# ===== TECHNICAL CHART =====
range_map = {
    "1 Month": 22, "3 Months": 66, "6 Months": 132, "1 Year": 252,
}
n_days = range_map.get(chart_range, 132)
chart_df = tech_df.tail(n_days) if not tech_df.empty else tech_df

if show_technicals and not chart_df.empty:
    st.plotly_chart(make_technical_chart(chart_df, show_bb=show_bollinger), use_container_width=True)

# ===== SPREAD + SUPPLY/DEMAND =====
col_sp, col_sd = st.columns(2)
with col_sp:
    if not hist_1y.empty and not wti_1y.empty:
        st.plotly_chart(make_spread_chart(hist_1y, wti_1y), use_container_width=True)
with col_sd:
    st.plotly_chart(make_supply_demand_chart(), use_container_width=True)

# ===== INVENTORY + ANALYST FORECASTS =====
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
            <span class='mono' style='color:#fbbf24;font-weight:600;'>$71 Q4 (base), $111 Q4 (worst)</span>
        </div>
        <div class='analyst-row'>
            <span style='color:#94a3b8;'>Standard Chartered</span>
            <span class='mono' style='color:#fbbf24;font-weight:600;'>$98 Q2, $85 Q3, $80.50 Q4</span>
        </div>
        <div class='analyst-row'>
            <span style='color:#94a3b8;'>Fitch Ratings</span>
            <span class='mono' style='color:#fbbf24;font-weight:600;'>$70 avg (Hormuz ~1mo closure)</span>
        </div>
        <div class='analyst-row'>
            <span style='color:#94a3b8;'>J.P. Morgan</span>
            <span class='mono' style='color:#fbbf24;font-weight:600;'>$60 avg (pre-conflict, bearish)</span>
        </div>
        <div class='analyst-row' style='border-bottom:none;'>
            <span style='color:#94a3b8;'>Long Forecast (AI)</span>
            <span class='mono' style='color:#fbbf24;font-weight:600;'>$132 high Jun, $118.75 YE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ===== PREDICTIVE ANALYTICS =====
st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("## 🎯 Predictive Analytics")

conflict_active_map = {
    "Active (current)": True,
    "De-escalating": True,  # still active but with higher transition prob
    "Resolved": False,
}
conflict_flag = conflict_active_map[conflict_assumption]

# Primary target Monte Carlo
mc_results, price_paths, final_prices = regime_monte_carlo(
    hist_1y, current_price, TARGET_PRICE, days_to_target, conflict_flag
)

if mc_results and show_monte_carlo:
    col_mc1, col_mc2 = st.columns([2, 1])

    with col_mc1:
        st.plotly_chart(make_monte_carlo_chart(
            final_prices, TARGET_PRICE, current_price,
            f"Regime-Aware MC: ${TARGET_PRICE} by Jun 15 ({mc_results['n_sims']:,} sims)"
        ), use_container_width=True)

    with col_mc2:
        st.markdown(f"""
        <div class='target-card'>
            <div class='metric-label'>REGIME-AWARE MONTE CARLO</div>
            <div style='margin-top:8px;font-size:11px;color:#475569;'>
                Normal vol: {mc_results['sigma_normal']}% ann. | Conflict vol: {mc_results['sigma_conflict']}% ann.<br>
                Sims still in conflict regime at expiry: {mc_results['pct_still_conflict']}%
            </div>
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
                <div class='analyst-row'>
                    <span style='color:#94a3b8;'>P(above $100)</span>
                    <span class='mono orange' style='font-weight:700;font-size:16px;'>{mc_results['prob_above_100']}%</span>
                </div>
                <div class='analyst-row'>
                    <span style='color:#94a3b8;'>P(above $120)</span>
                    <span class='mono red' style='font-weight:700;font-size:16px;'>{mc_results['prob_above_120']}%</span>
                </div>
                <div style='margin-top:14px;border-top:1px solid rgba(100,116,139,0.15);padding-top:12px;'>
                    <div class='metric-label'>PRICE DISTRIBUTION (JUN 15)</div>
                    <div class='analyst-row'><span style='color:#64748b;'>5th %ile</span><span class='mono' style='color:#ef4444;'>${mc_results['p5']}</span></div>
                    <div class='analyst-row'><span style='color:#64748b;'>10th %ile</span><span class='mono' style='color:#ef4444;'>${mc_results['p10']}</span></div>
                    <div class='analyst-row'><span style='color:#64748b;'>25th %ile</span><span class='mono orange'>${mc_results['p25']}</span></div>
                    <div class='analyst-row'><span style='color:#64748b;'>Median</span><span class='mono' style='color:#f1f5f9;font-weight:700;'>${mc_results['median']}</span></div>
                    <div class='analyst-row'><span style='color:#64748b;'>Mean</span><span class='mono' style='color:#f1f5f9;'>${mc_results['mean']}</span></div>
                    <div class='analyst-row'><span style='color:#64748b;'>75th %ile</span><span class='mono orange'>${mc_results['p75']}</span></div>
                    <div class='analyst-row'><span style='color:#64748b;'>90th %ile</span><span class='mono red'>${mc_results['p90']}</span></div>
                    <div class='analyst-row' style='border-bottom:none;'><span style='color:#64748b;'>95th %ile</span><span class='mono red'>${mc_results['p95']}</span></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Fan chart
if show_fan_chart and price_paths is not None:
    st.plotly_chart(make_prediction_fan_chart(
        price_paths, current_price, days_to_target, TARGET_PRICE
    ), use_container_width=True)

# ===== CUSTOM DATE PREDICTION =====
st.markdown("---")
pred_dt = datetime.combine(pred_date, datetime.min.time())
custom_pred = predict_price_on_date(hist_1y, current_price, pred_dt, conflict_flag)

if custom_pred:
    st.markdown(f"### 📅 Custom Prediction: {custom_pred['target_date']} ({custom_pred['days_out']} days out)")
    cp1, cp2, cp3, cp4, cp5 = st.columns(5)
    with cp1:
        st.markdown(f"""
        <div class='metric-card' style='border-left:3px solid #22d3ee;'>
            <div class='metric-label'>MEDIAN</div>
            <div class='metric-value'>${custom_pred['median']}</div>
        </div>""", unsafe_allow_html=True)
    with cp2:
        st.markdown(f"""
        <div class='metric-card' style='border-left:3px solid #22c55e;'>
            <div class='metric-label'>25TH %ILE</div>
            <div class='metric-value'>${custom_pred['p25']}</div>
        </div>""", unsafe_allow_html=True)
    with cp3:
        st.markdown(f"""
        <div class='metric-card' style='border-left:3px solid #f97316;'>
            <div class='metric-label'>75TH %ILE</div>
            <div class='metric-value'>${custom_pred['p75']}</div>
        </div>""", unsafe_allow_html=True)
    with cp4:
        st.markdown(f"""
        <div class='metric-card' style='border-left:3px solid #ef4444;'>
            <div class='metric-label'>P(&gt;$100)</div>
            <div class='metric-value'>{custom_pred['prob_above_100']}%</div>
        </div>""", unsafe_allow_html=True)
    with cp5:
        st.markdown(f"""
        <div class='metric-card' style='border-left:3px solid #a78bfa;'>
            <div class='metric-label'>P(&lt;$80)</div>
            <div class='metric-value'>{custom_pred['prob_below_80']}%</div>
        </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='font-size:12px;color:#475569;margin-top:8px;'>
        Full range: ${custom_pred['p5']} (5th) to ${custom_pred['p95']} (95th) &middot;
        Mean: ${custom_pred['mean']} &middot;
        Conflict regime: {conflict_assumption} &middot;
        {custom_pred['pct_still_conflict']}% sims still in conflict at expiry
    </div>
    """, unsafe_allow_html=True)


# Qualitative Assessment
st.markdown(f"""
<div class='target-card' style='margin-top:20px;'>
    <div style='font-size:18px;font-weight:700;color:#22d3ee;margin-bottom:14px;'>
        Qualitative Assessment: Is $94.50 by June 15 Realistic?
    </div>
    <div style='font-size:14px;color:#cbd5e1;line-height:1.8;'>
        <p><strong style='color:#22c55e;'>FACTORS SUPPORTING TARGET:</strong></p>
        <p>
        The $94.50 target sits in the consensus corridor. EIA's March 10 STEO forecasts Brent above $95 through May,
        dropping below $80 in Q3. Mid-June falls in the transition zone. Standard Chartered's Q2 avg of $98 and Q3 avg
        of $85 make $94.50 a reasonable interpolation. Goldman's base case assumes 21-day low-flow at Hormuz with 30-day
        recovery, implying normalization by late April/May and a glide path through the low-to-mid $90s in June.
        </p>
        <p><strong style='color:#ef4444;'>FACTORS AGAINST:</strong></p>
        <p>
        Hormuz staying closed past analyst assumptions is the primary risk. Mojtaba Khamenei has vowed continued blockade.
        Only 21 transits since Feb 28 vs 100+/day normal. If blockade persists into May, the conflict premium keeps $94.50
        too low. Long Forecast projects $132 high in June under deepening disruption. IEA notes 3+ mb/d of Gulf refining
        already shut with LPG/naphtha losses cascading through petrochemicals.
        </p>
        <p><strong style='color:#fbbf24;'>NET:</strong></p>
        <p>
        Moderate-probability outcome. Requires: (1) Hormuz meaningfully reopening by late April/early May, (2) IEA 400M barrel
        release dampening the spike, (3) OPEC+ following through on 206K b/d April increase. If all three hold, the surplus
        (1.9M b/d forecast) reasserts and Brent enters the $90-95 corridor. If any fails (especially Hormuz), expect $100-115+.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)


# ===== CONFLICT INTEL =====
if show_conflict:
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.markdown("---")

    hz = get_hormuz_status()
    st.markdown(f"""
    ## ⚠️ Strait of Hormuz / Iran Conflict Intel
    <div style='margin-bottom:16px;'>
        <span class='status-badge status-critical' style='font-size:13px;padding:6px 16px;'>
            STRAIT STATUS: {hz["status"]} &middot; DAY {hz["days_since_closure"]} OF CLOSURE
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Quick stats
    hz_c1, hz_c2, hz_c3, hz_c4 = st.columns(4)
    hz_stats = [
        (hz_c1, "Transits Since Feb 28", str(hz["tanker_transits_since_conflict"]), "#ef4444"),
        (hz_c2, "Normal Daily Transits", hz["normal_daily_transits"], "#22c55e"),
        (hz_c3, "Vessels Waiting", hz["vessels_waiting"], "#f97316"),
        (hz_c4, "Flow Disrupted", f"{hz['flow_disrupted_pct']}%", "#ef4444"),
    ]
    for col, label, val, color in hz_stats:
        with col:
            st.markdown(f"""
            <div class='metric-card' style='border-left:3px solid {color};'>
                <div class='metric-label'>{label}</div>
                <div class='metric-value'>{val}</div>
            </div>""", unsafe_allow_html=True)

    # Permitted vs blocked
    st.markdown(f"""
    <div style='display:flex;gap:16px;margin:12px 0;flex-wrap:wrap;'>
        <div class='metric-card' style='flex:1;min-width:200px;border-left:3px solid #22c55e;'>
            <div class='metric-label'>PERMITTED FLAGS</div>
            <div style='color:#86efac;font-size:13px;margin-top:6px;'>{", ".join(hz["permitted_flags"])}</div>
        </div>
        <div class='metric-card' style='flex:1;min-width:200px;border-left:3px solid #ef4444;'>
            <div class='metric-label'>BLOCKED FLAGS</div>
            <div style='color:#fca5a5;font-size:13px;margin-top:6px;'>{", ".join(hz["blocked_flags"])}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Event timeline
    st.markdown("#### Conflict Timeline")
    for evt in CONFLICT_EVENTS:
        sev_color = {"critical": "#ef4444", "elevated": "#f97316"}.get(evt["severity"], "#64748b")
        sev_bg = {"critical": "rgba(239,68,68,0.08)", "elevated": "rgba(249,115,22,0.06)"}.get(evt["severity"], "rgba(100,116,139,0.05)")
        st.markdown(f"""
        <div style='background:{sev_bg};border-left:3px solid {sev_color};border-radius:0 8px 8px 0;
                    padding:10px 14px;margin-bottom:6px;font-size:13px;color:#cbd5e1;'>
            <span class='mono' style='color:{sev_color};font-weight:700;font-size:12px;'>{evt["date"]}</span>
            <span style='margin-left:8px;'>{evt["event"]}</span>
        </div>
        """, unsafe_allow_html=True)

    # Market impacts
    st.markdown("""
    <div class='conflict-card' style='margin-top:16px;'>
        <div style='font-size:16px;font-weight:700;color:#fca5a5;margin-bottom:12px;'>Key Market Impacts</div>
        <div style='font-size:13px;color:#cbd5e1;line-height:1.8;'>
            <strong style='color:#f97316;'>Oil flow:</strong> ~20M b/d (20% of global seaborne) normally transits Hormuz. Effectively halted for most operators.<br>
            <strong style='color:#f97316;'>Iran exports:</strong> 11.7M bbl shipped since Feb 28, all to China. Rate down from 2.16 to 1.22 mb/d.<br>
            <strong style='color:#f97316;'>Production:</strong> Saudi reducing output (onshore storage full). Iraq Kurdish fields halted.<br>
            <strong style='color:#f97316;'>Bypass routes:</strong> Fujairah under attack. Oman's Duqm damaged. Sohar in war-risk zone.<br>
            <strong style='color:#f97316;'>LNG:</strong> European gas surged 30 to 60+ EUR/MWh. QatarEnergy 17% capacity loss (years to restore).<br>
            <strong style='color:#f97316;'>Insurance:</strong> War-risk premiums 0.125% to 0.2-0.4% hull value. Most commercial insurers withdrew.<br>
            <strong style='color:#f97316;'>Fed:</strong> Rate cut expectations collapsed. 73% P(no cuts in 2026).
        </div>
    </div>
    """, unsafe_allow_html=True)

    # What to watch
    st.markdown("""
    <div class='target-card' style='margin-top:12px;'>
        <div style='font-size:16px;font-weight:700;color:#67e8f9;margin-bottom:12px;'>Key Watchpoints</div>
        <div style='font-size:13px;color:#cbd5e1;line-height:1.8;'>
            <strong style='color:#22d3ee;'>Hormuz reopening signals:</strong> Transit frequency, insurance market moves, CENTCOM de-mining ops.<br>
            <strong style='color:#22d3ee;'>OPEC+ Apr 5 meeting:</strong> Will they accelerate output beyond 206K b/d?<br>
            <strong style='color:#22d3ee;'>US Kharg Island strikes:</strong> Friday overnight attacks on Iran's main export hub. Success = reduced Iranian leverage.<br>
            <strong style='color:#22d3ee;'>IEA Apr 7 STEO:</strong> First update reflecting actual March disruption data.<br>
            <strong style='color:#22d3ee;'>Bilateral transit deals:</strong> Pakistan, Turkey, India deals with Iran. If "permission-based" transit normalizes, gradual reopening begins.
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
    }).reset_index(drop=True)

    st.dataframe(
        display_df.style.format({
            "Open": "${:.2f}", "High": "${:.2f}", "Low": "${:.2f}", "Close": "${:.2f}",
            "Change": "${:+.2f}", "Change%": "{:+.2f}%", "Volume": "{:,.0f}",
        }).applymap(
            lambda v: "color: #22c55e" if isinstance(v, (int, float)) and v > 0
            else "color: #ef4444" if isinstance(v, (int, float)) and v < 0 else "",
            subset=["Change", "Change%"],
        ),
        use_container_width=True, height=400,
    )


# ===== FOOTER =====
n_sims_label = mc_results['n_sims'] if mc_results else 100_000
st.markdown(f"""
<div style='text-align:center;margin-top:24px;font-size:10px;color:#334155;font-family:"JetBrains Mono",monospace;
border-top:1px solid rgba(100,116,139,0.08);padding-top:16px;'>
Data: Yahoo Finance (BZ=F, CL=F) &middot; MC: {n_sims_label:,} regime-switching GBM sims &middot; Technicals: SMA/EMA/BB/RSI/MACD/ATR<br>
Analyst forecasts: EIA, GS, StanChart, Fitch, JPM &middot; Conflict data: CRS, IEA, Bloomberg, CNBC, Reuters, Al Jazeera<br>
Not financial advice &middot; Built {datetime.now().strftime("%Y-%m-%d %H:%M")}
</div>
""", unsafe_allow_html=True)

# Auto-rerun
time.sleep(REFRESH_INTERVAL)
st.rerun()
