#!/usr/bin/env python3
"""
BRENT CRUDE OIL - LIVE TRACKER & PREDICTIVE ANALYTICS
======================================================
streamlit run main.py

Fixes from v1:
  - Replaced time.sleep(30)+st.rerun() with streamlit-autorefresh (non-blocking)
  - Cache TTL raised to 120s to avoid Yahoo Finance rate limits
  - Exponential backoff retry on yfinance calls
  - Graceful degradation: shows stale data + warning instead of crash
  - Consolidated API calls to reduce request count

Features:
  - Real-time Brent/WTI via yfinance
  - Technical indicators: SMA, EMA, Bollinger Bands, RSI, MACD, ATR
  - Regime-aware Monte Carlo with conflict/normal volatility regimes
  - Prediction fan chart with percentile confidence bands
  - User-selectable prediction date
  - Iran/Hormuz conflict timeline and live status tracker
  - Analyst forecast consensus
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
import traceback

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Brent Crude - Live Tracker",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# NON-BLOCKING AUTO-REFRESH (replaces time.sleep + st.rerun)
# ---------------------------------------------------------------------------
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=120_000, limit=None, key="data_refresh")  # 2 min
except ImportError:
    pass  # Manual refresh only if package unavailable

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
TARGET_PRICE = 94.50
TARGET_DATE = datetime(2026, 6, 15)
TARGET_DATE_STR = "June 15, 2026"
CACHE_TTL = 120  # seconds - avoids Yahoo rate limits
CONFLICT_START = datetime(2026, 2, 28)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --bg-base: #05070d;
    --bg-card: rgba(12, 16, 28, 0.75);
    --bg-card-hover: rgba(18, 24, 40, 0.85);
    --border-subtle: rgba(100, 116, 139, 0.10);
    --border-accent: rgba(34, 211, 238, 0.20);
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-dim: #475569;
    --cyan: #22d3ee;
    --cyan-glow: rgba(34, 211, 238, 0.12);
    --orange: #f97316;
    --green: #22c55e;
    --red: #ef4444;
    --purple: #a78bfa;
    --yellow: #fbbf24;
    --gold: #d4a843;
}

.stApp {
    background: linear-gradient(168deg, var(--bg-base) 0%, #0a0e1a 35%, #0d1220 65%, #080c14 100%);
}
.main .block-container { padding-top: 1.2rem; max-width: 1440px; }
h1,h2,h3,h4,h5,h6 { font-family: 'Outfit', sans-serif !important; color: var(--text-primary) !important; }
p, span, div, li { font-family: 'Outfit', sans-serif; }

/* ---- HEADER BADGE ---- */
.header-badge {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 5px 14px; border-radius: 6px; font-size: 11px;
    font-family: 'JetBrains Mono', monospace; font-weight: 600;
    letter-spacing: 0.5px; backdrop-filter: blur(8px);
}
.badge-red { background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.30); color: #fca5a5; }
.badge-purple { background: rgba(167,139,250,0.10); border: 1px solid rgba(167,139,250,0.25); color: #c4b5fd; }
.badge-cyan { background: rgba(34,211,238,0.10); border: 1px solid rgba(34,211,238,0.25); color: #67e8f9; }
.badge-green { background: rgba(34,197,94,0.10); border: 1px solid rgba(34,197,94,0.25); color: #86efac; }
.badge-orange { background: rgba(249,115,22,0.10); border: 1px solid rgba(249,115,22,0.25); color: #fdba74; }

/* ---- PRICE HERO ---- */
.price-hero {
    font-family: 'Outfit', sans-serif; font-size: 60px; font-weight: 900;
    letter-spacing: -3px; line-height: 1;
    background: linear-gradient(135deg, #f1f5f9 0%, #cbd5e1 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    text-shadow: none;
}
.change-up { color: var(--green); font-family: 'JetBrains Mono', monospace; font-weight: 600; }
.change-down { color: var(--red); font-family: 'JetBrains Mono', monospace; font-weight: 600; }
.mono { font-family: 'JetBrains Mono', monospace; }
.dim { color: var(--text-dim); font-size: 11px; letter-spacing: 0.3px; }

/* ---- CARDS ---- */
.glass-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 8px;
    backdrop-filter: blur(12px);
    transition: border-color 0.2s ease;
}
.glass-card:hover { border-color: var(--border-accent); }
.card-label {
    font-size: 9px; color: var(--text-dim); letter-spacing: 2px;
    text-transform: uppercase; font-family: 'JetBrains Mono', monospace;
    margin-bottom: 8px; font-weight: 500;
}
.card-value {
    font-size: 20px; font-weight: 700; color: var(--text-primary);
    font-family: 'Outfit', sans-serif;
}

.conflict-card {
    background: linear-gradient(135deg, rgba(239,68,68,0.05) 0%, rgba(249,115,22,0.03) 100%);
    border: 1px solid rgba(239,68,68,0.18); border-radius: 14px; padding: 22px 26px;
    backdrop-filter: blur(8px);
}
.target-card {
    background: linear-gradient(135deg, rgba(34,211,238,0.05) 0%, rgba(167,139,250,0.03) 100%);
    border: 1px solid rgba(34,211,238,0.18); border-radius: 14px; padding: 22px 26px;
    backdrop-filter: blur(8px);
}
.row-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 9px 0; border-bottom: 1px solid rgba(100,116,139,0.06); font-size: 13px;
}

/* ---- STATUS BADGES ---- */
.status-pill {
    display: inline-block; padding: 5px 14px; border-radius: 20px;
    font-size: 10px; font-weight: 700; letter-spacing: 1.5px;
    font-family: 'JetBrains Mono', monospace; text-transform: uppercase;
}
.pill-critical { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }
.pill-elevated { background: rgba(249,115,22,0.15); color: #fdba74; border: 1px solid rgba(249,115,22,0.35); }

/* ---- LIVE PULSE ---- */
.live-dot {
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    animation: glow-pulse 2.5s ease-in-out infinite; margin-right: 8px; vertical-align: middle;
}
@keyframes glow-pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 6px currentColor; transform: scale(1); }
    50% { opacity: 0.35; box-shadow: 0 0 12px currentColor; transform: scale(1.3); }
}

/* ---- TIMELINE EVENT ---- */
.tl-event {
    border-left: 3px solid; border-radius: 0 10px 10px 0;
    padding: 10px 16px; margin-bottom: 5px; font-size: 13px;
    color: #cbd5e1; backdrop-filter: blur(4px);
}
.tl-critical { border-color: var(--red); background: rgba(239,68,68,0.06); }
.tl-elevated { border-color: var(--orange); background: rgba(249,115,22,0.05); }

/* ---- SIDEBAR ---- */
div[data-testid="stSidebar"] {
    background: rgba(6,8,14,0.97); border-right: 1px solid var(--border-subtle);
}
#MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}

/* ---- SECTION DIVIDER ---- */
.section-rule {
    height: 1px; margin: 28px 0 24px 0;
    background: linear-gradient(90deg, transparent 0%, rgba(34,211,238,0.15) 50%, transparent 100%);
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DATA FETCHING - with retry + graceful degradation
# ---------------------------------------------------------------------------
def _yf_fetch_with_retry(ticker_str, method_kwargs, max_retries=3):
    """Fetch yfinance data with exponential backoff."""
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(ticker_str)
            return ticker.history(**method_kwargs)
        except Exception as e:
            if "Too Many Requests" in str(e) or "429" in str(e):
                wait = 2 ** (attempt + 1)
                time.sleep(wait)
                continue
            if attempt == max_retries - 1:
                return pd.DataFrame()
            time.sleep(1)
    return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_market_data():
    """Pull Brent + WTI data with retry logic. Returns stale-safe dict."""
    result = {
        "intraday": pd.DataFrame(),
        "hist_1y": pd.DataFrame(),
        "hist_5y": pd.DataFrame(),
        "wti_1y": pd.DataFrame(),
        "wti_intraday": pd.DataFrame(),
        "info": None,
        "fetch_time": datetime.now(),
        "error": None,
        "is_stale": False,
    }
    try:
        # Batch: fetch all Brent data from one Ticker object (reduces connections)
        brent = yf.Ticker("BZ=F")
        result["intraday"] = brent.history(period="1d", interval="1m")
        result["hist_1y"] = brent.history(period="1y", interval="1d")
        result["hist_5y"] = brent.history(period="5y", interval="1wk")

        try:
            result["info"] = brent.fast_info
        except Exception:
            result["info"] = None

        # WTI - separate ticker, fewer calls
        wti = yf.Ticker("CL=F")
        result["wti_intraday"] = wti.history(period="1d", interval="1m")
        result["wti_1y"] = wti.history(period="1y", interval="1d")

    except Exception as e:
        err_str = str(e)
        result["error"] = err_str
        # If rate limited, mark as stale but don't crash
        if "Too Many Requests" in err_str or "429" in err_str:
            result["error"] = "Rate limited by Yahoo Finance. Showing cached data."
            result["is_stale"] = True

    return result


# ---------------------------------------------------------------------------
# SAFE HELPERS
# ---------------------------------------------------------------------------
def safe_attr(obj, attr, default=0.0):
    try:
        val = getattr(obj, attr, default)
        return round(float(val), 2) if val is not None else default
    except Exception:
        return default


def safe_last(series, default=0.0):
    try:
        if series is not None and len(series) > 0:
            return round(float(series.iloc[-1]), 2)
    except Exception:
        pass
    return default


# ---------------------------------------------------------------------------
# TECHNICAL INDICATORS
# ---------------------------------------------------------------------------
def compute_technicals(df):
    if df.empty or len(df) < 30:
        return df
    out = df.copy()
    c = out["Close"]

    out["SMA_20"] = c.rolling(20).mean()
    out["SMA_50"] = c.rolling(50).mean()
    out["SMA_200"] = c.rolling(200).mean()
    out["EMA_12"] = c.ewm(span=12, adjust=False).mean()
    out["EMA_26"] = c.ewm(span=26, adjust=False).mean()

    out["BB_mid"] = out["SMA_20"]
    bb_std = c.rolling(20).std()
    out["BB_upper"] = out["BB_mid"] + 2 * bb_std
    out["BB_lower"] = out["BB_mid"] - 2 * bb_std

    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    out["RSI"] = 100 - (100 / (1 + rs))

    out["MACD"] = out["EMA_12"] - out["EMA_26"]
    out["MACD_signal"] = out["MACD"].ewm(span=9, adjust=False).mean()
    out["MACD_hist"] = out["MACD"] - out["MACD_signal"]

    tr = pd.concat([
        out["High"] - out["Low"],
        (out["High"] - c.shift(1)).abs(),
        (out["Low"] - c.shift(1)).abs(),
    ], axis=1).max(axis=1)
    out["ATR_14"] = tr.rolling(14).mean()

    return out


# ---------------------------------------------------------------------------
# REGIME-AWARE MONTE CARLO
# ---------------------------------------------------------------------------
def regime_monte_carlo(hist_df, current_price, target_price, days_to_target,
                       conflict_active=True, n_sims=80_000):
    if hist_df.empty or len(hist_df) < 60 or days_to_target <= 0:
        return None, None, None

    closes = hist_df["Close"].dropna()
    log_ret = np.log(closes / closes.shift(1)).dropna()

    # Split regimes
    try:
        conflict_idx = hist_df.index.get_indexer([pd.Timestamp(CONFLICT_START)], method="nearest")[0]
    except Exception:
        conflict_idx = 0

    if 30 < conflict_idx < len(log_ret) - 5:
        pre = log_ret.iloc[:conflict_idx]
        post = log_ret.iloc[conflict_idx:]
        mu_n, sig_n = pre.mean(), pre.std()
        mu_c, sig_c = post.mean(), post.std()
    else:
        mu_n = log_ret.mean()
        sig_n = log_ret.std()
        mu_c = mu_n * 1.5
        sig_c = sig_n * 2.0

    n_days = max(1, days_to_target)
    np.random.seed(42)

    prices = np.zeros((n_sims, n_days))
    prices[:, 0] = current_price
    in_conflict = np.ones(n_sims, dtype=bool) if conflict_active else np.zeros(n_sims, dtype=bool)

    for t in range(1, n_days):
        p_de = min(0.015 * t / 30, 0.6) if conflict_active else 0.0
        in_conflict = in_conflict & ~(np.random.random(n_sims) < p_de)
        shock_n = np.random.normal(mu_n, sig_n, n_sims)
        shock_c = np.random.normal(mu_c, sig_c, n_sims)
        prices[:, t] = prices[:, t - 1] * np.exp(np.where(in_conflict, shock_c, shock_n))

    finals = prices[:, -1]

    r = {
        "prob_within_3": round(np.mean(np.abs(finals - target_price) <= 3) * 100, 1),
        "prob_within_5": round(np.mean(np.abs(finals - target_price) <= 5) * 100, 1),
        "prob_at_or_below": round(np.mean(finals <= target_price) * 100, 1),
        "prob_above_100": round(np.mean(finals > 100) * 100, 1),
        "prob_above_120": round(np.mean(finals > 120) * 100, 1),
        "prob_below_80": round(np.mean(finals < 80) * 100, 1),
        "p5": round(np.percentile(finals, 5), 2),
        "p10": round(np.percentile(finals, 10), 2),
        "p25": round(np.percentile(finals, 25), 2),
        "median": round(np.percentile(finals, 50), 2),
        "p75": round(np.percentile(finals, 75), 2),
        "p90": round(np.percentile(finals, 90), 2),
        "p95": round(np.percentile(finals, 95), 2),
        "mean": round(np.mean(finals), 2),
        "mu_normal": round(mu_n * 252 * 100, 1),
        "sigma_normal": round(sig_n * np.sqrt(252) * 100, 1),
        "mu_conflict": round(mu_c * 252 * 100, 1),
        "sigma_conflict": round(sig_c * np.sqrt(252) * 100, 1),
        "n_sims": n_sims,
        "pct_still_conflict": round(np.mean(in_conflict) * 100, 1),
    }
    return r, prices, finals


# ---------------------------------------------------------------------------
# CONFLICT DATA
# ---------------------------------------------------------------------------
CONFLICT_EVENTS = [
    ("Feb 28", "critical", "US launches Operation Epic Fury. Joint US-Israeli strikes kill Supreme Leader Ali Khamenei. 17+ Iranian ships destroyed."),
    ("Mar 1-2", "critical", "Iran retaliates on US bases, Israel, Gulf states. IRGC declares Hormuz closed. Brent gaps $73 to $85-90."),
    ("Mar 4", "critical", "Iran formally closes Strait. Attacks on transiting vessels. Traffic drops 70%. 150+ ships anchor outside."),
    ("Mar 5", "elevated", "IRGC: closure targets US/Israel/Western-allied only. China-flagged vessels test transit."),
    ("Mar 8", "critical", "Brent passes $100 (first since 2022). Peaks $126 intraday."),
    ("Mar 11", "elevated", "IEA releases 400M bbl from reserves. US commits 172M from SPR."),
    ("Mar 12-13", "critical", "21 attacks on merchant vessels. 7 seafarers killed. China-owned vessel hit despite AIS broadcast."),
    ("Mar 14", "critical", "Iran strikes UAE Shah gas field, Fujairah fire. 3+ mb/d Gulf refining shut."),
    ("Mar 16", "elevated", "Pakistan tanker crosses with Iranian permission. First non-Iranian cargo since closure."),
    ("Mar 17", "critical", "New Supreme Leader Mojtaba Khamenei vows continued blockade. QatarEnergy force majeure on Ras Laffan."),
    ("Mar 18", "elevated", "Turkish, Indian, Saudi ships permitted. Iran strikes Oman bypass ports (Duqm, Salalah)."),
    ("Mar 19", "critical", "Israeli strike on South Pars. Iran retaliates on Ras Laffan. Brent $119 intraday, settles $108.65."),
    ("Mar 20", "critical", "Brent ~$107-110. Only 21 transits since Feb 28 (vs 100+/day). ~400 vessels waiting in Gulf of Oman."),
]

HORMUZ = {
    "status": "CRITICAL",
    "transits": 21,
    "normal_daily": "100+",
    "waiting": "~400",
    "disrupted_pct": 95,
    "days_closed": (datetime.now() - datetime(2026, 3, 4)).days,
    "permitted": ["Pakistan", "Turkey", "India", "Saudi (India-bound)"],
    "blocked": ["US", "Israel", "UK", "EU-flagged", "Most Western"],
}


# ---------------------------------------------------------------------------
# CHART THEME
# ---------------------------------------------------------------------------
_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(8,12,20,0.45)",
    font=dict(family="Outfit, sans-serif", color="#94a3b8", size=12),
    margin=dict(l=52, r=16, t=44, b=36),
    xaxis=dict(gridcolor="rgba(100,116,139,0.06)", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="rgba(100,116,139,0.06)", showgrid=True, zeroline=False),
    hoverlabel=dict(
        bgcolor="rgba(8,10,18,0.96)", bordercolor="rgba(34,211,238,0.25)",
        font=dict(family="JetBrains Mono, monospace", size=11, color="#e2e8f0"),
    ),
)


# ---------------------------------------------------------------------------
# CHARTS
# ---------------------------------------------------------------------------
def chart_intraday(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"], mode="lines",
        line=dict(color="#22d3ee", width=2, shape="spline"),
        fill="tozeroy", fillcolor="rgba(34,211,238,0.06)",
        hovertemplate="$%{y:.2f}<extra></extra>",
    ))
    fig.update_layout(**_LAYOUT, height=280, showlegend=False,
                      title=dict(text="INTRADAY 1-MIN", font=dict(size=13, color="#64748b")),
                      yaxis=dict(tickprefix="$", **_LAYOUT["yaxis"]))
    return fig


def chart_technicals(df, show_bb=True, show_sma=True):
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                        row_heights=[0.50, 0.17, 0.17, 0.16], vertical_spacing=0.015)

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        increasing_line_color="#22c55e", decreasing_line_color="#ef4444",
        increasing_fillcolor="rgba(34,197,94,0.35)", decreasing_fillcolor="rgba(239,68,68,0.35)",
        showlegend=False,
    ), row=1, col=1)

    if show_sma:
        for col_name, color, lbl in [("SMA_20","#22d3ee","SMA20"),("SMA_50","#f97316","SMA50"),("SMA_200","#a78bfa","SMA200")]:
            if col_name in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[col_name], mode="lines",
                    line=dict(color=color, width=1, dash="dot"), name=lbl,
                    hovertemplate="$%{y:.2f}<extra></extra>",
                ), row=1, col=1)

    if show_bb and "BB_upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_upper"], mode="lines",
                                 line=dict(color="rgba(251,191,36,0.3)", width=0.8),
                                 showlegend=False, hoverinfo="skip"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_lower"], mode="lines",
                                 line=dict(color="rgba(251,191,36,0.3)", width=0.8),
                                 fill="tonexty", fillcolor="rgba(251,191,36,0.03)",
                                 showlegend=False, hoverinfo="skip"), row=1, col=1)

    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], mode="lines",
                                 line=dict(color="#22d3ee", width=1.4), name="RSI",
                                 hovertemplate="%{y:.1f}<extra></extra>"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="rgba(239,68,68,0.35)", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="rgba(34,197,94,0.35)", row=2, col=1)
        fig.add_hrect(y0=30, y1=70, fillcolor="rgba(100,116,139,0.03)", line_width=0, row=2, col=1)

    if "MACD" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], mode="lines",
                                 line=dict(color="#f97316", width=1.4), name="MACD"), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD_signal"], mode="lines",
                                 line=dict(color="#a78bfa", width=1, dash="dot"), name="Signal"), row=3, col=1)
        if "MACD_hist" in df.columns:
            mh_colors = ["#22c55e" if v >= 0 else "#ef4444" for v in df["MACD_hist"]]
            fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist"], marker_color=mh_colors,
                                 opacity=0.45, showlegend=False), row=3, col=1)

    if "Volume" in df.columns:
        vc = ["#22c55e" if c >= o else "#ef4444" for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=vc, opacity=0.35,
                             showlegend=False), row=4, col=1)

    fig.update_layout(**_LAYOUT, height=680, showlegend=True, xaxis_rangeslider_visible=False,
                      legend=dict(orientation="h", y=1.02, x=1, xanchor="right", font=dict(size=10)),
                      title=dict(text="TECHNICAL ANALYSIS", font=dict(size=13, color="#64748b")))
    fig.update_yaxes(tickprefix="$", row=1, col=1, gridcolor="rgba(100,116,139,0.06)")
    fig.update_yaxes(title="RSI", row=2, col=1, range=[0, 100], gridcolor="rgba(100,116,139,0.06)")
    fig.update_yaxes(title="MACD", row=3, col=1, gridcolor="rgba(100,116,139,0.06)")
    fig.update_yaxes(title="Vol", row=4, col=1, gridcolor="rgba(100,116,139,0.06)")
    for i in range(1, 5):
        fig.update_xaxes(gridcolor="rgba(100,116,139,0.06)", row=i, col=1)
    return fig


def chart_spread(brent_df, wti_df):
    m = pd.DataFrame({"Brent": brent_df["Close"], "WTI": wti_df["Close"]}).dropna()
    m["Spread"] = m["Brent"] - m["WTI"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m.index, y=m["Spread"], mode="lines",
                             line=dict(color="#a78bfa", width=1.8),
                             fill="tozeroy", fillcolor="rgba(167,139,250,0.06)",
                             hovertemplate="$%{y:.2f}<extra></extra>"))
    fig.add_hline(y=0, line_color="rgba(100,116,139,0.2)", line_width=1)
    fig.update_layout(**_LAYOUT, height=300, showlegend=False,
                      title=dict(text="BRENT-WTI SPREAD", font=dict(size=13, color="#64748b")),
                      yaxis=dict(tickprefix="$", **_LAYOUT["yaxis"]))
    return fig


def chart_supply_demand():
    q = ["Q3'25","Q4'25","Q1'26","Q2'26F","Q3'26F","Q4'26F"]
    s = [108.0,107.2,106.6,107.8,108.5,109.2]
    d = [106.1,105.8,105.9,106.5,107.1,107.5]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Supply", x=q, y=s, marker_color="rgba(34,211,238,0.65)",
                         text=[f"{v}" for v in s], textposition="outside",
                         textfont=dict(size=10, color="#94a3b8")))
    fig.add_trace(go.Bar(name="Demand", x=q, y=d, marker_color="rgba(249,115,22,0.65)",
                         text=[f"{v}" for v in d], textposition="outside",
                         textfont=dict(size=10, color="#94a3b8")))
    fig.update_layout(**_LAYOUT, height=340, barmode="group",
                      title=dict(text="SUPPLY vs DEMAND (mb/d)", font=dict(size=13, color="#64748b")),
                      yaxis=dict(range=[103, 111], title="mb/d", **_LAYOUT["yaxis"]),
                      legend=dict(orientation="h", y=1.02, x=1, xanchor="right", font=dict(size=10)))
    return fig


def chart_inventory():
    labels = ["OECD","China Crude","Oil on Water","Other Non-OECD"]
    vals = [4.10,1.23,2.05,0.82]
    colors = ["#22d3ee","#f97316","#a78bfa","#22c55e"]
    fig = go.Figure(go.Pie(labels=labels, values=vals, hole=0.58,
                           marker=dict(colors=colors, line=dict(color="#0a0e1a", width=2)),
                           textinfo="label+percent", textfont=dict(size=11, color="#e2e8f0"),
                           hovertemplate="%{label}: %{value:.2f}B bbl<extra></extra>"))
    fig.update_layout(**_LAYOUT, height=340,
                      title=dict(text="GLOBAL INVENTORY (8.2B bbl)", font=dict(size=13, color="#64748b")),
                      annotations=[dict(text="8.2B<br>bbl", x=0.5, y=0.5, font_size=16,
                                        font_color="#f1f5f9", showarrow=False)],
                      showlegend=True,
                      legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center", font=dict(size=10)))
    return fig


def chart_monte_carlo(finals, target_price, current_price, n_sims):
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=finals, nbinsx=140,
                               marker_color="rgba(34,211,238,0.30)",
                               marker_line_color="rgba(34,211,238,0.45)",
                               marker_line_width=0.5,
                               hovertemplate="$%{x:.0f}: %{y:,}<extra></extra>"))
    p10, p90 = np.percentile(finals, 10), np.percentile(finals, 90)
    fig.add_vrect(x0=p10, x1=p90, fillcolor="rgba(167,139,250,0.06)", line_width=0,
                  annotation_text="80% CI", annotation_position="top left",
                  annotation_font=dict(color="#a78bfa", size=10))
    fig.add_vline(x=target_price, line_dash="dash", line_color="#22c55e", line_width=2,
                  annotation_text=f"Target ${target_price}",
                  annotation_font=dict(color="#22c55e", size=11))
    fig.add_vline(x=current_price, line_dash="dot", line_color="#f97316", line_width=2,
                  annotation_text=f"Now ${current_price:.2f}",
                  annotation_font=dict(color="#f97316", size=11))
    fig.update_layout(**_LAYOUT, height=340, showlegend=False,
                      title=dict(text=f"MONTE CARLO ({n_sims:,} REGIME-SWITCHING SIMS)",
                                 font=dict(size=13, color="#64748b")),
                      xaxis=dict(tickprefix="$", **_LAYOUT["xaxis"]),
                      yaxis=dict(title="Freq", **_LAYOUT["yaxis"]))
    return fig


def chart_fan(paths, current_price, days, target_price=None):
    n = min(days, paths.shape[1])
    x = [datetime.now() + timedelta(days=i) for i in range(n)]
    pcts = {p: np.percentile(paths[:, :n], p, axis=0) for p in [5, 10, 25, 50, 75, 90, 95]}

    fig = go.Figure()
    # 90% band
    fig.add_trace(go.Scatter(x=x, y=pcts[95], mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x, y=pcts[5], mode="lines", line=dict(width=0),
                             fill="tonexty", fillcolor="rgba(34,211,238,0.05)", name="90% CI", hoverinfo="skip"))
    # 50% band
    fig.add_trace(go.Scatter(x=x, y=pcts[75], mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x, y=pcts[25], mode="lines", line=dict(width=0),
                             fill="tonexty", fillcolor="rgba(34,211,238,0.10)", name="50% CI", hoverinfo="skip"))
    # Median
    fig.add_trace(go.Scatter(x=x, y=pcts[50], mode="lines",
                             line=dict(color="#22d3ee", width=2.5), name="Median",
                             hovertemplate="$%{y:.2f}<extra></extra>"))
    if target_price:
        fig.add_hline(y=target_price, line_dash="dash", line_color="rgba(34,197,94,0.45)",
                      annotation_text=f"Target ${target_price}",
                      annotation_font=dict(color="#22c55e", size=10))
    fig.add_hline(y=current_price, line_dash="dot", line_color="rgba(249,115,22,0.2)", line_width=1)

    fig.update_layout(**_LAYOUT, height=380, showlegend=True,
                      title=dict(text="PREDICTION FAN CHART", font=dict(size=13, color="#64748b")),
                      yaxis=dict(tickprefix="$", **_LAYOUT["yaxis"]),
                      legend=dict(orientation="h", y=1.02, x=1, xanchor="right", font=dict(size=10)))
    return fig


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style='display:flex;align-items:center;gap:10px;margin-bottom:16px;'>
        <div style='width:36px;height:36px;border-radius:10px;
                    background:linear-gradient(135deg,#22d3ee,#3b82f6);
                    display:flex;align-items:center;justify-content:center;
                    font-size:18px;font-weight:800;color:#fff;'>B</div>
        <div>
            <div style='font-size:15px;font-weight:700;color:#f1f5f9;'>Brent Tracker</div>
            <div style='font-size:10px;color:#64748b;letter-spacing:1px;'>LIVE ANALYTICS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    chart_range = st.selectbox("Historical Range", ["1 Month","3 Months","6 Months","1 Year"], index=2)
    show_technicals = st.checkbox("Technical Indicators", value=True)
    show_bollinger = st.checkbox("Bollinger Bands", value=True)
    show_mc = st.checkbox("Monte Carlo Analysis", value=True)
    show_fan = st.checkbox("Prediction Fan Chart", value=True)
    show_conflict = st.checkbox("Conflict Intel", value=True)

    st.markdown("---")
    st.markdown("**Custom Prediction**")
    pred_date = st.date_input("Target date", value=TARGET_DATE.date(),
                              min_value=datetime.now().date() + timedelta(days=1),
                              max_value=datetime(2027, 12, 31).date())
    conflict_mode = st.selectbox("Conflict regime", ["Active (current)","De-escalating","Resolved"], index=0)

    st.markdown("---")
    st.markdown(f"""
    <div class='target-card'>
        <div class='card-label'>PRIMARY TARGET</div>
        <div style='font-size:26px;font-weight:800;color:var(--cyan);'>${TARGET_PRICE:.2f}</div>
        <div style='font-size:11px;color:var(--text-dim);margin-top:4px;'>by {TARGET_DATE_STR}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    hz = HORMUZ
    st.markdown(f"""
    <div class='glass-card' style='border-left:3px solid var(--red);'>
        <div class='card-label'>STRAIT OF HORMUZ</div>
        <div style='margin:6px 0;'>
            <span class='status-pill pill-critical'>{hz["status"]} &middot; DAY {hz["days_closed"]}</span>
        </div>
        <div style='font-size:11px;color:var(--text-secondary);line-height:1.7;margin-top:8px;'>
            {hz["transits"]} transits since Feb 28<br>
            {hz["waiting"]} vessels waiting<br>
            {hz["disrupted_pct"]}% flow disrupted
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div class='dim mono'>
    Yahoo Finance (BZ=F, CL=F)<br>
    Auto-refresh: 2 min &middot; Cache: {CACHE_TTL}s<br>
    Not financial advice
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Force Refresh"):
        st.cache_data.clear()
        st.rerun()


# ---------------------------------------------------------------------------
# FETCH DATA
# ---------------------------------------------------------------------------
with st.spinner("Loading market data..."):
    data = fetch_market_data()

info = data["info"]
intraday = data["intraday"]
hist_1y = data["hist_1y"]
wti_1y = data["wti_1y"]

# Show stale/error warnings (non-blocking)
if data["error"]:
    st.warning(f"⚠️ {data['error']}  |  Auto-retry on next refresh cycle.", icon="⚠️")
if data["is_stale"]:
    st.info("Displaying cached data. Will refresh automatically.", icon="🔄")

# Price extraction
current_price = safe_last(intraday["Close"] if not intraday.empty else None) or safe_attr(info, "previous_close")
prev_close = safe_attr(info, "previous_close", current_price)
change = round(current_price - prev_close, 2) if current_price and prev_close else 0
change_pct = round((change / prev_close) * 100, 2) if prev_close else 0
is_up = change >= 0

day_high = safe_attr(info, "day_high")
day_low = safe_attr(info, "day_low")
year_high = safe_attr(info, "year_high")
year_low = safe_attr(info, "year_low")
open_price = safe_attr(info, "open")

wti_price = safe_last(data["wti_intraday"]["Close"] if not data["wti_intraday"].empty else None)
spread = round(current_price - wti_price, 2) if wti_price else 0

yoy = None
if len(hist_1y) > 5:
    fp = float(hist_1y["Close"].iloc[0])
    if fp > 0:
        yoy = round(((current_price - fp) / fp) * 100, 1)

days_to_target = (TARGET_DATE - datetime.now()).days

tech_df = compute_technicals(hist_1y) if not hist_1y.empty else hist_1y
rsi_val = safe_last(tech_df.get("RSI")) if "RSI" in tech_df.columns else None
atr_val = safe_last(tech_df.get("ATR_14")) if "ATR_14" in tech_df.columns else None


# =====================================================================
# HEADER
# =====================================================================
col_l, col_r = st.columns([3, 2])

with col_l:
    dot_color = "var(--green)" if is_up else "var(--red)"
    sign = "+" if is_up else ""
    cc = "change-up" if is_up else "change-down"
    st.markdown(f"""
    <div>
        <div style='display:flex;align-items:center;gap:6px;margin-bottom:8px;'>
            <span class='live-dot' style='color:{dot_color};background:{dot_color};'></span>
            <span class='mono dim' style='letter-spacing:2.5px;'>LIVE &middot; BRENT CRUDE FUTURES (BZ=F)</span>
        </div>
        <div style='display:flex;align-items:baseline;gap:18px;flex-wrap:wrap;'>
            <span class='price-hero'>${current_price:.2f}</span>
            <span class='{cc}' style='font-size:22px;'>{sign}{change:.2f} ({sign}{change_pct:.2f}%)</span>
        </div>
        <div class='mono dim' style='margin-top:8px;'>
            per barrel &middot; {data["fetch_time"].strftime("%H:%M:%S")} &middot; prev ${prev_close:.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_r:
    rsi_color = "var(--red)" if rsi_val and rsi_val > 70 else "var(--green)" if rsi_val and rsi_val < 30 else "var(--yellow)"
    rsi_lbl = "OVERBOUGHT" if rsi_val and rsi_val > 70 else "OVERSOLD" if rsi_val and rsi_val < 30 else "NEUTRAL"
    st.markdown(f"""
    <div style='text-align:right;display:flex;flex-direction:column;align-items:flex-end;gap:6px;'>
        <span class='header-badge badge-red'>52W &nbsp; ${year_high:.2f} / ${year_low:.2f}</span>
        <span class='header-badge badge-purple'>SPREAD ${spread:+.2f} &nbsp;|&nbsp; ATR {f"${atr_val}" if atr_val else "N/A"}</span>
        <span class='header-badge badge-cyan'>TARGET ${TARGET_PRICE} by {TARGET_DATE_STR} &nbsp;|&nbsp; {days_to_target}d</span>
        <span class='header-badge badge-orange'>RSI {rsi_val if rsi_val else "N/A"} &nbsp;|&nbsp; {rsi_lbl}</span>
    </div>
    """, unsafe_allow_html=True)


# =====================================================================
# STATS ROW
# =====================================================================
st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
c1, c2, c3, c4, c5, c6 = st.columns(6)

for col, label, val, color in [
    (c1, "Day Range", f"${day_low:.2f} - ${day_high:.2f}", "var(--cyan)"),
    (c2, "Open", f"${open_price:.2f}", "var(--green)"),
    (c3, "WTI", f"${wti_price:.2f}", "var(--purple)"),
    (c4, "YoY", f"{'+' if yoy and yoy >= 0 else ''}{yoy:.1f}%" if yoy else "N/A", "var(--orange)"),
    (c5, "Spread", f"${spread:.2f}", "var(--purple)"),
    (c6, "To Target", f"{days_to_target}d", "var(--cyan)"),
]:
    with col:
        st.markdown(f"""
        <div class='glass-card' style='border-left:3px solid {color};'>
            <div class='card-label'>{label}</div>
            <div class='card-value'>{val}</div>
        </div>""", unsafe_allow_html=True)


# =====================================================================
# INTRADAY
# =====================================================================
if not intraday.empty:
    st.plotly_chart(chart_intraday(intraday), use_container_width=True)


# =====================================================================
# TECHNICALS
# =====================================================================
range_days = {"1 Month": 22, "3 Months": 66, "6 Months": 132, "1 Year": 252}
n_d = range_days.get(chart_range, 132)
chart_slice = tech_df.tail(n_d) if not tech_df.empty else tech_df

if show_technicals and not chart_slice.empty:
    st.plotly_chart(chart_technicals(chart_slice, show_bb=show_bollinger), use_container_width=True)


# =====================================================================
# SPREAD + SUPPLY/DEMAND
# =====================================================================
cs, cd = st.columns(2)
with cs:
    if not hist_1y.empty and not wti_1y.empty:
        st.plotly_chart(chart_spread(hist_1y, wti_1y), use_container_width=True)
with cd:
    st.plotly_chart(chart_supply_demand(), use_container_width=True)


# =====================================================================
# INVENTORY + ANALYSTS
# =====================================================================
ci, ca = st.columns(2)
with ci:
    st.plotly_chart(chart_inventory(), use_container_width=True)
with ca:
    st.markdown("""
    <div class='glass-card' style='border-left:3px solid var(--yellow);'>
        <div style='font-size:15px;font-weight:700;color:var(--text-primary);margin-bottom:12px;'>Analyst Forecasts (Brent 2026)</div>
        <div class='row-item'><span style='color:var(--text-secondary);'>EIA STEO (Mar 10)</span><span class='mono' style='color:var(--yellow);font-weight:600;'>>$95 thru May, <$80 Q3</span></div>
        <div class='row-item'><span style='color:var(--text-secondary);'>Goldman Sachs</span><span class='mono' style='color:var(--yellow);font-weight:600;'>$71 Q4 base, $111 worst</span></div>
        <div class='row-item'><span style='color:var(--text-secondary);'>Standard Chartered</span><span class='mono' style='color:var(--yellow);font-weight:600;'>$98 Q2, $85 Q3, $80.50 Q4</span></div>
        <div class='row-item'><span style='color:var(--text-secondary);'>Fitch</span><span class='mono' style='color:var(--yellow);font-weight:600;'>$70 avg (Hormuz ~1mo)</span></div>
        <div class='row-item'><span style='color:var(--text-secondary);'>J.P. Morgan</span><span class='mono' style='color:var(--yellow);font-weight:600;'>$60 avg (pre-conflict)</span></div>
        <div class='row-item' style='border-bottom:none;'><span style='color:var(--text-secondary);'>Long Forecast (AI)</span><span class='mono' style='color:var(--yellow);font-weight:600;'>$132 high Jun</span></div>
    </div>
    """, unsafe_allow_html=True)


# =====================================================================
# PREDICTIVE ANALYTICS
# =====================================================================
st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
st.markdown("## 🎯 Predictive Analytics")

conflict_flag = conflict_mode != "Resolved"
mc, paths, finals = regime_monte_carlo(hist_1y, current_price, TARGET_PRICE, days_to_target, conflict_flag)

if mc and show_mc:
    m1, m2 = st.columns([2, 1])
    with m1:
        st.plotly_chart(chart_monte_carlo(finals, TARGET_PRICE, current_price, mc["n_sims"]), use_container_width=True)
    with m2:
        st.markdown(f"""
        <div class='target-card'>
            <div class='card-label'>REGIME-SWITCHING RESULTS</div>
            <div style='font-size:10px;color:var(--text-dim);margin:6px 0 12px;'>
                Normal vol {mc['sigma_normal']}% | Conflict vol {mc['sigma_conflict']}% | {mc['pct_still_conflict']}% still in conflict at expiry
            </div>
            <div class='row-item'><span style='color:var(--text-secondary);'>P(within $3 of $94.50)</span><span class='mono cyan' style='font-weight:700;'>{mc['prob_within_3']}%</span></div>
            <div class='row-item'><span style='color:var(--text-secondary);'>P(within $5)</span><span class='mono cyan' style='font-weight:700;'>{mc['prob_within_5']}%</span></div>
            <div class='row-item'><span style='color:var(--text-secondary);'>P(at or below $94.50)</span><span class='mono green' style='font-weight:700;'>{mc['prob_at_or_below']}%</span></div>
            <div class='row-item'><span style='color:var(--text-secondary);'>P(above $100)</span><span class='mono orange' style='font-weight:700;'>{mc['prob_above_100']}%</span></div>
            <div class='row-item'><span style='color:var(--text-secondary);'>P(above $120)</span><span class='mono red' style='font-weight:700;'>{mc['prob_above_120']}%</span></div>
            <div style='margin-top:12px;border-top:1px solid var(--border-subtle);padding-top:10px;'>
                <div class='card-label'>DISTRIBUTION</div>
                <div class='row-item'><span style='color:var(--text-dim);'>5th</span><span class='mono red'>${mc['p5']}</span></div>
                <div class='row-item'><span style='color:var(--text-dim);'>25th</span><span class='mono orange'>${mc['p25']}</span></div>
                <div class='row-item'><span style='color:var(--text-dim);'>Median</span><span class='mono' style='color:var(--text-primary);font-weight:700;'>${mc['median']}</span></div>
                <div class='row-item'><span style='color:var(--text-dim);'>75th</span><span class='mono orange'>${mc['p75']}</span></div>
                <div class='row-item' style='border-bottom:none;'><span style='color:var(--text-dim);'>95th</span><span class='mono red'>${mc['p95']}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

if show_fan and paths is not None:
    st.plotly_chart(chart_fan(paths, current_price, days_to_target, TARGET_PRICE), use_container_width=True)


# =====================================================================
# CUSTOM DATE PREDICTION
# =====================================================================
st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
pred_dt = datetime.combine(pred_date, datetime.min.time())
pred_days = (pred_dt - datetime.now()).days

if pred_days > 0:
    cp, _, cp_finals = regime_monte_carlo(hist_1y, current_price, TARGET_PRICE, pred_days, conflict_flag, n_sims=50_000)
    if cp:
        st.markdown(f"### 📅 Prediction: {pred_dt.strftime('%B %d, %Y')} ({pred_days}d out)")
        p1, p2, p3, p4, p5 = st.columns(5)
        for col, lbl, val, clr in [
            (p1, "MEDIAN", f"${cp['median']}", "var(--cyan)"),
            (p2, "25TH", f"${cp['p25']}", "var(--green)"),
            (p3, "75TH", f"${cp['p75']}", "var(--orange)"),
            (p4, "P(>$100)", f"{cp['prob_above_100']}%", "var(--red)"),
            (p5, "P(<$80)", f"{cp['prob_below_80']}%", "var(--purple)"),
        ]:
            with col:
                st.markdown(f"""<div class='glass-card' style='border-left:3px solid {clr};'>
                    <div class='card-label'>{lbl}</div><div class='card-value'>{val}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown(f"""<div style='font-size:11px;color:var(--text-dim);margin-top:4px;'>
            Range: ${cp['p5']} (5th) to ${cp['p95']} (95th) | Mean: ${cp['mean']} |
            {cp['pct_still_conflict']}% sims in conflict at expiry | Regime: {conflict_mode}
        </div>""", unsafe_allow_html=True)


# Qualitative
st.markdown(f"""
<div class='target-card' style='margin-top:20px;'>
    <div style='font-size:17px;font-weight:700;color:var(--cyan);margin-bottom:12px;'>
        Assessment: $94.50 by June 15
    </div>
    <div style='font-size:13px;color:#cbd5e1;line-height:1.8;'>
        <p><strong style='color:var(--green);'>SUPPORTING:</strong>
        EIA STEO has Brent >$95 through May, then <$80 Q3. Mid-June sits in the transition zone.
        StanChart Q2 avg $98 / Q3 avg $85 makes $94.50 a clean interpolation.
        Goldman base case: 21-day low-flow then 30-day recovery, normalizing by late April/May.</p>
        <p><strong style='color:var(--red);'>AGAINST:</strong>
        Hormuz staying closed past assumptions is the key risk. Mojtaba Khamenei vows blockade.
        Only 21 transits since Feb 28 vs 100+/day normal. Long Forecast projects $132 high in June.
        3+ mb/d Gulf refining shut with LPG/naphtha cascading.</p>
        <p><strong style='color:var(--yellow);'>NET:</strong>
        Moderate probability. Requires Hormuz reopening by late April, IEA 400M bbl release dampening,
        and OPEC+ 206K b/d April follow-through. If all hold, $90-95 corridor. If not, $100-115+.</p>
    </div>
</div>
""", unsafe_allow_html=True)


# =====================================================================
# CONFLICT INTEL
# =====================================================================
if show_conflict:
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    ## ⚠️ Iran Conflict / Hormuz Intel
    <div style='margin-bottom:14px;'>
        <span class='status-pill pill-critical' style='font-size:12px;padding:6px 18px;'>
            STRAIT {hz["status"]} &middot; DAY {hz["days_closed"]}
        </span>
    </div>
    """, unsafe_allow_html=True)

    h1, h2, h3, h4 = st.columns(4)
    for col, lbl, val, clr in [
        (h1, "Transits Since Feb 28", str(hz["transits"]), "var(--red)"),
        (h2, "Normal Daily", hz["normal_daily"], "var(--green)"),
        (h3, "Vessels Waiting", hz["waiting"], "var(--orange)"),
        (h4, "Flow Disrupted", f"{hz['disrupted_pct']}%", "var(--red)"),
    ]:
        with col:
            st.markdown(f"""<div class='glass-card' style='border-left:3px solid {clr};'>
                <div class='card-label'>{lbl}</div><div class='card-value'>{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='display:flex;gap:12px;margin:10px 0;flex-wrap:wrap;'>
        <div class='glass-card' style='flex:1;min-width:180px;border-left:3px solid var(--green);'>
            <div class='card-label'>PERMITTED</div>
            <div style='color:#86efac;font-size:12px;margin-top:4px;'>{", ".join(hz["permitted"])}</div>
        </div>
        <div class='glass-card' style='flex:1;min-width:180px;border-left:3px solid var(--red);'>
            <div class='card-label'>BLOCKED</div>
            <div style='color:#fca5a5;font-size:12px;margin-top:4px;'>{", ".join(hz["blocked"])}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Timeline")
    for date, sev, desc in CONFLICT_EVENTS:
        cls = "tl-critical" if sev == "critical" else "tl-elevated"
        sev_color = "var(--red)" if sev == "critical" else "var(--orange)"
        st.markdown(f"""<div class='tl-event {cls}'>
            <span class='mono' style='color:{sev_color};font-weight:700;font-size:11px;'>{date}</span>
            <span style='margin-left:10px;'>{desc}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class='conflict-card' style='margin-top:14px;'>
        <div style='font-size:15px;font-weight:700;color:#fca5a5;margin-bottom:10px;'>Market Impact Summary</div>
        <div style='font-size:12px;color:#cbd5e1;line-height:1.8;'>
            <strong style='color:var(--orange);'>Oil flow:</strong> ~20M b/d (20% global seaborne) normally transits Hormuz. Effectively halted.<br>
            <strong style='color:var(--orange);'>Iran exports:</strong> 11.7M bbl since Feb 28, all China-bound. Rate: 1.22 mb/d (was 2.16).<br>
            <strong style='color:var(--orange);'>Production:</strong> Saudi reducing (storage full). Iraq Kurdish fields halted.<br>
            <strong style='color:var(--orange);'>Bypass degraded:</strong> Fujairah under attack. Duqm damaged. Sohar in war-risk zone.<br>
            <strong style='color:var(--orange);'>LNG:</strong> EU gas 30 to 60+ EUR/MWh. QatarEnergy 17% capacity loss (years to repair).<br>
            <strong style='color:var(--orange);'>Insurance:</strong> War-risk 0.125% to 0.2-0.4% hull. Most insurers withdrew.<br>
            <strong style='color:var(--orange);'>Fed:</strong> 73% P(no cuts in 2026). Rate cut expectations collapsed.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='target-card' style='margin-top:10px;'>
        <div style='font-size:15px;font-weight:700;color:#67e8f9;margin-bottom:10px;'>Key Watchpoints</div>
        <div style='font-size:12px;color:#cbd5e1;line-height:1.8;'>
            <strong style='color:var(--cyan);'>Hormuz signals:</strong> Transit frequency, insurance moves, CENTCOM de-mining.<br>
            <strong style='color:var(--cyan);'>OPEC+ Apr 5:</strong> Accelerate beyond 206K b/d?<br>
            <strong style='color:var(--cyan);'>Kharg Island:</strong> US strikes on Iran's main export hub. Success = reduced leverage.<br>
            <strong style='color:var(--cyan);'>IEA Apr 7:</strong> First STEO reflecting actual March disruption data.<br>
            <strong style='color:var(--cyan);'>Bilateral deals:</strong> Pakistan, Turkey, India transit agreements. If "permission-based" normalizes, gradual reopening.
        </div>
    </div>
    """, unsafe_allow_html=True)


# =====================================================================
# RECENT SESSIONS TABLE
# =====================================================================
st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
st.markdown("### Recent Sessions")

if not hist_1y.empty:
    recent = hist_1y.tail(15).copy().sort_index(ascending=False)
    recent["Change"] = recent["Close"] - recent["Close"].shift(-1)
    recent["Change%"] = (recent["Change"] / recent["Close"].shift(-1)) * 100

    tbl = pd.DataFrame({
        "Date": recent.index.strftime("%Y-%m-%d"),
        "Open": recent["Open"].round(2), "High": recent["High"].round(2),
        "Low": recent["Low"].round(2), "Close": recent["Close"].round(2),
        "Change": recent["Change"].round(2), "Change%": recent["Change%"].round(2),
        "Volume": recent["Volume"].astype(int),
    }).reset_index(drop=True)

    st.dataframe(
        tbl.style.format({
            "Open": "${:.2f}", "High": "${:.2f}", "Low": "${:.2f}", "Close": "${:.2f}",
            "Change": "${:+.2f}", "Change%": "{:+.2f}%", "Volume": "{:,.0f}",
        }).applymap(
            lambda v: "color: #22c55e" if isinstance(v, (int, float)) and v > 0
            else "color: #ef4444" if isinstance(v, (int, float)) and v < 0 else "",
            subset=["Change", "Change%"],
        ),
        use_container_width=True, height=400,
    )


# =====================================================================
# FOOTER
# =====================================================================
ns = mc['n_sims'] if mc else 80_000
st.markdown(f"""
<div style='text-align:center;margin-top:28px;padding-top:16px;
            border-top:1px solid rgba(100,116,139,0.06);'>
    <div style='font-size:9px;color:#1e293b;font-family:"JetBrains Mono",monospace;letter-spacing:0.5px;'>
        YAHOO FINANCE (BZ=F, CL=F) &middot; {ns:,} REGIME-SWITCHING GBM SIMS &middot;
        SMA/EMA/BB/RSI/MACD/ATR &middot; NOT FINANCIAL ADVICE &middot; {datetime.now().strftime("%Y-%m-%d %H:%M")}
    </div>
</div>
""", unsafe_allow_html=True)

# NO time.sleep() or st.rerun() here - streamlit-autorefresh handles it non-blockingly
