#!/usr/bin/env python3
"""
OVERWATCH: TACTICAL COMMODITY DASHBOARD v2.0
=============================================
Primary Focus: Brent Crude, Hormuz Theater, Med-Dev Supply Chain Impacts
Includes Live AIS Maritime, ADS-B Flight Tracking, and Mean-Reverting MC

v2.0 CHANGES:
  - Replaced GBM drift model with Ornstein-Uhlenbeck mean-reverting jump-diffusion
  - Added seasonal demand curves, fundamental equilibrium, risk premium overlays
  - Added OVX (oil volatility index) and DXY (dollar index) context
  - Added Anthropic Claude AI tactical briefing with live web search
  - Added model parameter transparency and diagnostics panel
  - Added contango/backwardation detection from BZ/WTI dynamics
"""

import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
import json
import time
import random
import requests

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# CONFIG & AUTO-REFRESH
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="OVERWATCH SITREP",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from streamlit_autorefresh import st_autorefresh

    st_autorefresh(interval=120_000, limit=None, key="data_refresh")
except ImportError:
    pass

CACHE_TTL = 300  # default; overridden by sidebar

# ---------------------------------------------------------------------------
# UI HELPERS
# ---------------------------------------------------------------------------
def var_color(val):
    try:
        val = float(val)
        return "var(--green)" if val > 0 else "var(--red)" if val < 0 else "#94a3b8"
    except (ValueError, TypeError):
        return "#94a3b8"


def alert_class(val, warn_thresh=5, crit_thresh=10):
    """Returns CSS alert class based on absolute magnitude."""
    try:
        val = abs(float(val))
        if val >= crit_thresh:
            return "alert-critical"
        elif val >= warn_thresh:
            return "alert-warn"
        return ""
    except (ValueError, TypeError):
        return ""


# ---------------------------------------------------------------------------
# TACTICAL UI/UX CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@300;400;600;800&display=swap');

:root {
    --bg-base: #020617;
    --panel-bg: rgba(15, 23, 42, 0.6);
    --border-glow: rgba(6, 182, 212, 0.4);
    --text-main: #e2e8f0;
    --cyan: #06b6d4;
    --amber: #f59e0b;
    --red: #ef4444;
    --green: #10b981;
    --mono: 'Share Tech Mono', monospace;
    --sans: 'Inter', sans-serif;
}

.stApp { background-color: var(--bg-base); background-image: radial-gradient(circle at 50% 0%, #0f172a 0%, #020617 70%); color: var(--text-main); }
h1, h2, h3 { font-family: var(--sans); font-weight: 800; letter-spacing: -1px; text-transform: uppercase; color: #fff; }
p, span, div, label { font-family: var(--sans); }
.mono-text { font-family: var(--mono); text-transform: uppercase; }

/* TACTICAL PANELS */
.tac-panel {
    background: var(--panel-bg); border: 1px solid rgba(148, 163, 184, 0.1);
    border-radius: 4px; padding: 16px; margin-bottom: 12px;
    box-shadow: inset 0 0 20px rgba(0,0,0,0.5); position: relative;
    border-left: 2px solid var(--cyan);
}
.tac-panel::before {
    content: ''; position: absolute; top: 0; left: 0; width: 10px; height: 10px;
    border-top: 2px solid var(--cyan); border-left: 2px solid var(--cyan);
}
.tac-panel::after {
    content: ''; position: absolute; bottom: 0; right: 0; width: 10px; height: 10px;
    border-bottom: 2px solid var(--cyan); border-right: 2px solid var(--cyan);
}
.panel-title { font-family: var(--mono); font-size: 11px; color: #94a3b8; letter-spacing: 2px; margin-bottom: 8px; }
.panel-value { font-family: var(--mono); font-size: 28px; font-weight: 400; color: #fff; text-shadow: 0 0 10px var(--border-glow); }

/* ALERTS */
.alert-critical { border-left-color: var(--red); box-shadow: 0 0 15px rgba(239, 68, 68, 0.1); }
.alert-critical .panel-value { color: var(--red); text-shadow: 0 0 10px rgba(239, 68, 68, 0.5); }
.alert-critical::before, .alert-critical::after { border-color: var(--red); }
.alert-warn { border-left-color: var(--amber); box-shadow: 0 0 15px rgba(245, 158, 11, 0.1); }
.alert-warn .panel-value { color: var(--amber); text-shadow: 0 0 10px rgba(245, 158, 11, 0.5); }
.alert-warn::before, .alert-warn::after { border-color: var(--amber); }

/* TERMINAL FEED */
.terminal-feed { font-family: var(--mono); font-size: 12px; color: #cbd5e1; height: 300px; overflow-y: auto; padding: 10px; background: rgba(0,0,0,0.5); border: 1px solid #1e293b; }
.term-line { border-bottom: 1px dashed #1e293b; padding: 6px 0; }
.term-date { color: var(--cyan); margin-right: 10px; }
.term-crit { color: var(--red); }
.term-warn { color: var(--amber); }

/* AI BRIEFING */
.ai-briefing {
    font-family: var(--mono); font-size: 13px; color: #e2e8f0;
    line-height: 1.8; padding: 20px; background: rgba(0,0,0,0.5);
    border: 1px solid #1e293b; white-space: pre-wrap;
}
.ai-briefing h3, .ai-briefing strong { color: var(--cyan); }

/* MODEL DIAGNOSTICS */
.diag-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed #1e293b; }
.diag-label { color: #94a3b8; font-family: var(--mono); font-size: 11px; }
.diag-value { color: #fff; font-family: var(--mono); font-size: 11px; }

/* DATA FRESHNESS BAR */
.freshness-bar {
    display: flex; align-items: center; gap: 6px; padding: 6px 12px;
    background: rgba(0,0,0,0.4); border: 1px solid #1e293b;
    border-radius: 3px; margin-bottom: 12px; flex-wrap: wrap;
}
.freshness-dot {
    width: 6px; height: 6px; border-radius: 50%; display: inline-block;
}
.freshness-item {
    font-family: var(--mono); font-size: 9px; color: #94a3b8;
    display: inline-flex; align-items: center; gap: 4px; margin-right: 10px;
}
.source-tag {
    font-family: var(--mono); font-size: 8px; padding: 1px 4px;
    border-radius: 2px; display: inline-block;
}
.src-yf { background: rgba(6, 182, 212, 0.2); color: var(--cyan); }
.src-fred { background: rgba(16, 185, 129, 0.2); color: var(--green); }
.src-fail { background: rgba(239, 68, 68, 0.2); color: var(--red); }

/* STREAMLIT OVERRIDES */
#MainMenu, footer, header {visibility: hidden;}
div[data-baseweb="input"] { background-color: rgba(15, 23, 42, 0.8) !important; border: 1px solid var(--cyan) !important; color: #fff !important; }
div[data-baseweb="select"] > div { background-color: rgba(15, 23, 42, 0.8) !important; border: 1px solid var(--cyan) !important; color: #fff !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# DATA ENGINE (MULTI-SOURCE, RETRY-HARDENED)
# ---------------------------------------------------------------------------
# FRED API: Free, extremely reliable (US Federal Reserve infrastructure)
# Register for a free key at https://fred.stlouisfed.org/docs/api/api_key.html
# Series: DCOILBRENTEU (Brent daily), DCOILWTICO (WTI daily)
FRED_SERIES = {
    "brent": "DCOILBRENTEU",
    "wti": "DCOILWTICO",
}


def _fetch_single_yf(ticker: str, period: str, interval: str, retries: int = 3) -> pd.DataFrame:
    """
    Fetch a single ticker from yfinance with exponential backoff + jitter.
    Individual fetches are far less likely to get rate-limited than batch.
    """
    for attempt in range(retries):
        try:
            t = yf.Ticker(ticker)
            df = t.history(period=period, interval=interval)
            if df is not None and not df.empty:
                return df
        except Exception:
            pass
        # Exponential backoff: 1s, 2s, 4s + random jitter 0-1s
        wait = (2 ** attempt) + random.uniform(0, 1)
        time.sleep(wait)
    return pd.DataFrame()


def _fetch_fred_series(series_id: str, lookback_days: int = 400) -> pd.DataFrame:
    """
    Fetch daily price data from FRED (Federal Reserve Economic Data).
    No API key required for basic access; key improves rate limits.
    Returns DataFrame with DatetimeIndex and 'Close' column to match yfinance shape.
    """
    fred_key = st.secrets.get("FRED_API_KEY", "")
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "observation_start": start_date,
        "observation_end": end_date,
        "file_type": "json",
        "sort_order": "asc",
    }
    if fred_key:
        params["api_key"] = fred_key

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return pd.DataFrame()
        data = resp.json().get("observations", [])
        if not data:
            return pd.DataFrame()

        rows = []
        for obs in data:
            if obs["value"] != ".":
                rows.append({"date": obs["date"], "Close": float(obs["value"])})
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        # Add OHLV columns to match yfinance shape
        df["Open"] = df["Close"]
        df["High"] = df["Close"]
        df["Low"] = df["Close"]
        df["Volume"] = 0
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_stratcom_data(cache_ttl_key: int = 300):
    """
    Multi-source data engine with FRED fallback and per-source freshness tracking.
    cache_ttl_key is a dummy param that changes when TTL changes, busting the cache.
    """
    result: dict = {"error": None, "sources": {}, "fetch_time": datetime.now()}

    # --- HELPER: fetch with source tracking ---
    def tracked_fetch(key, ticker, period, interval, fred_series=None, fred_days=400):
        """Try yfinance first, then FRED fallback. Track which source succeeded."""
        df = _fetch_single_yf(ticker, period, interval)
        if not df.empty:
            result["sources"][key] = {
                "source": "yfinance",
                "rows": len(df),
                "latest": df.index[-1].strftime("%Y-%m-%d %H:%M") if hasattr(df.index[-1], "strftime") else str(df.index[-1]),
            }
            return df

        # FRED fallback (daily data only, no intraday)
        if fred_series and interval in ("1d", "1wk"):
            df_fred = _fetch_fred_series(fred_series, lookback_days=fred_days)
            if not df_fred.empty:
                result["sources"][key] = {
                    "source": "FRED",
                    "rows": len(df_fred),
                    "latest": df_fred.index[-1].strftime("%Y-%m-%d"),
                }
                return df_fred

        result["sources"][key] = {"source": "FAILED", "rows": 0, "latest": "N/A"}
        return pd.DataFrame()

    # --- ENERGY COMPLEX (staggered fetches to avoid rate limiting) ---
    result["brent_1y"] = tracked_fetch("brent_1y", "BZ=F", "1y", "1d", fred_series="DCOILBRENTEU")
    time.sleep(0.5)
    result["brent_5y"] = tracked_fetch("brent_5y", "BZ=F", "5y", "1wk", fred_series="DCOILBRENTEU", fred_days=1900)
    time.sleep(0.5)
    result["brent_1d"] = tracked_fetch("brent_1d", "BZ=F", "1d", "1m")  # no FRED fallback for intraday
    time.sleep(0.5)
    result["wti_1d"] = tracked_fetch("wti_1d", "CL=F", "1d", "1m")
    time.sleep(0.5)
    result["wti_1y"] = tracked_fetch("wti_1y", "CL=F", "1y", "1d", fred_series="DCOILWTICO")
    time.sleep(0.5)
    result["natgas_1y"] = tracked_fetch("natgas_1y", "NG=F", "1y", "1d")
    time.sleep(0.5)

    # --- VOLATILITY & MACRO ---
    result["ovx_1y"] = tracked_fetch("ovx_1y", "^OVX", "1y", "1d")
    time.sleep(0.5)
    result["dxy_1y"] = tracked_fetch("dxy_1y", "DX-Y.NYB", "1y", "1d")
    time.sleep(0.5)

    # --- MATERIALS ---
    result["alum_1y"] = tracked_fetch("alum_1y", "ALI=F", "1y", "1d")
    time.sleep(0.5)
    result["copper_1y"] = tracked_fetch("copper_1y", "HG=F", "1y", "1d")
    time.sleep(0.5)
    result["plastic_proxy_1y"] = tracked_fetch("plastic_proxy_1y", "DOW", "1y", "1d")

    result["fetch_time"] = datetime.now()
    return result


def format_data_age(fetch_time):
    """Returns a human-readable age string + color class for staleness."""
    if fetch_time is None:
        return "UNKNOWN", "var(--red)"
    age = (datetime.now() - fetch_time).total_seconds()
    if age < 120:
        return f"{int(age)}S AGO", "var(--green)"
    elif age < 600:
        return f"{int(age / 60)}M AGO", "var(--cyan)"
    elif age < 3600:
        return f"{int(age / 60)}M AGO", "var(--amber)"
    else:
        return f"{int(age / 3600)}H AGO", "var(--red)"


# ---------------------------------------------------------------------------
# LIVE RECON: ADS-B FLIGHT TRACKING + VESSELFINDER AIS
# ---------------------------------------------------------------------------
# Persian Gulf / Hormuz center and radius
HORMUZ_CENTER = {"lat": 26.0, "lon": 55.5}
HORMUZ_RADIUS_NM = 250  # nautical miles


def _parse_adsb_lol(data: dict) -> pd.DataFrame:
    """Parse adsb.lol API response into a standard DataFrame."""
    ac_list = data.get("ac", [])
    if not ac_list:
        return pd.DataFrame()
    rows = []
    for ac in ac_list:
        lat = ac.get("lat")
        lon = ac.get("lon")
        if lat is None or lon is None:
            continue
        rows.append({
            "icao24": ac.get("hex", ""),
            "callsign": (ac.get("flight") or "").strip(),
            "origin": ac.get("r", ""),  # registration country
            "type": ac.get("t", ""),  # aircraft type
            "lon": lon,
            "lat": lat,
            "alt_m": (ac.get("alt_baro", 0) or 0) * 0.3048 if isinstance(ac.get("alt_baro"), (int, float)) else 0,
            "alt_ft_raw": ac.get("alt_baro", 0) if isinstance(ac.get("alt_baro"), (int, float)) else 0,
            "on_ground": ac.get("alt_baro") == "ground",
            "velocity_ms": (ac.get("gs", 0) or 0) * 0.5144,  # ground speed kts -> m/s
            "speed_kts_raw": ac.get("gs", 0) or 0,
            "heading": ac.get("track", 0) or 0,
        })
    return pd.DataFrame(rows)


def _parse_opensky(data: dict) -> pd.DataFrame:
    """Parse OpenSky Network API response into a standard DataFrame."""
    states = data.get("states", [])
    if not states:
        return pd.DataFrame()
    rows = []
    for s in states:
        if s[5] is not None and s[6] is not None:
            alt_m = s[7] if s[7] is not None else 0
            vel_ms = s[9] if s[9] is not None else 0
            rows.append({
                "icao24": s[0],
                "callsign": (s[1] or "").strip(),
                "origin": s[2] or "",
                "type": "",
                "lon": s[5],
                "lat": s[6],
                "alt_m": alt_m,
                "alt_ft_raw": int(alt_m * 3.281),
                "on_ground": s[8],
                "velocity_ms": vel_ms,
                "speed_kts_raw": int(vel_ms * 1.944),
                "heading": s[10] if s[10] is not None else 0,
            })
    return pd.DataFrame(rows)


@st.cache_data(ttl=45, show_spinner=False)
def fetch_adsb_data():
    """
    Multi-source ADS-B fetcher: adsb.lol (primary) -> OpenSky (fallback).

    adsb.lol: Free community ADS-B aggregator. Fast, reliable, no auth.
              Endpoint: /v2/lat/{lat}/lon/{lon}/dist/{nm}
    OpenSky:  Academic network. Slower, frequent timeouts on large AOIs.
              Endpoint: /api/states/all?lamin=..&lamax=..&lomin=..&lomax=..
    """
    errors = []

    # --- PRIMARY: adsb.lol ---
    try:
        url = (
            f"https://api.adsb.lol/v2/lat/{HORMUZ_CENTER['lat']}"
            f"/lon/{HORMUZ_CENTER['lon']}/dist/{HORMUZ_RADIUS_NM}"
        )
        resp = requests.get(url, timeout=8, headers={"Accept": "application/json"})
        if resp.status_code == 200:
            data = resp.json()
            df = _parse_adsb_lol(data)
            if not df.empty:
                now_str = datetime.utcnow().strftime("%H:%M:%SZ")
                return df, f"{len(df)} aircraft | {now_str}", "adsb.lol"
            errors.append("adsb.lol: 0 aircraft in AOI")
        else:
            errors.append(f"adsb.lol: HTTP {resp.status_code}")
    except requests.exceptions.Timeout:
        errors.append("adsb.lol: timeout")
    except Exception as e:
        errors.append(f"adsb.lol: {e}")

    # --- FALLBACK: OpenSky Network ---
    try:
        url = "https://opensky-network.org/api/states/all"
        params = {"lamin": 23.0, "lamax": 28.5, "lomin": 51.0, "lomax": 59.0}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            df = _parse_opensky(data)
            if not df.empty:
                ts = data.get("time", 0)
                ts_str = datetime.utcfromtimestamp(ts).strftime("%H:%M:%SZ") if ts else "?"
                return df, f"{len(df)} aircraft | {ts_str}", "OpenSky"
            errors.append("OpenSky: 0 aircraft in AOI")
        else:
            errors.append(f"OpenSky: HTTP {resp.status_code}")
    except requests.exceptions.Timeout:
        errors.append("OpenSky: timeout")
    except Exception as e:
        errors.append(f"OpenSky: {e}")

    return pd.DataFrame(), " | ".join(errors), "FAILED"


def build_adsb_map(df, source_name=""):
    """Builds a Plotly scattermapbox of live aircraft positions."""
    if df.empty:
        return None

    df = df.copy()
    df["alt_ft"] = df["alt_ft_raw"].astype(int)
    df["speed_kts"] = df["speed_kts_raw"].astype(int)

    df["label"] = df.apply(
        lambda r: (
            f"{'<b>' + r['callsign'] + '</b>' if r['callsign'] else r['icao24']}"
            f"{' [' + r['type'] + ']' if r['type'] else ''}"
            f" | {r['origin']}<br>"
            f"ALT: {r['alt_ft']:,}ft | SPD: {r['speed_kts']}kts | HDG: {int(r['heading'])}deg"
        ),
        axis=1,
    )

    # Color by altitude: ground=green, low=cyan, mid=amber, high=red
    alt_colors = []
    for _, row in df.iterrows():
        if row["on_ground"]:
            alt_colors.append("#10b981")
        elif row["alt_ft"] < 5000:
            alt_colors.append("#06b6d4")
        elif row["alt_ft"] < 25000:
            alt_colors.append("#f59e0b")
        else:
            alt_colors.append("#ef4444")

    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        lat=df["lat"],
        lon=df["lon"],
        mode="markers+text",
        marker=dict(size=7, color=alt_colors, opacity=0.85),
        text=df["callsign"],
        textposition="top right",
        textfont=dict(size=7, color="#94a3b8", family="Share Tech Mono"),
        hovertext=df["label"],
        hoverinfo="text",
        name="Aircraft",
    ))

    # Hormuz strait chokepoint marker
    fig.add_trace(go.Scattermapbox(
        lat=[26.57], lon=[56.25],
        mode="markers+text",
        marker=dict(size=12, color="#ef4444", symbol="circle"),
        text=["HORMUZ"],
        textposition="bottom center",
        textfont=dict(size=10, color="#ef4444", family="Share Tech Mono"),
        hovertext=["Strait of Hormuz - Critical Chokepoint<br>~21% of global oil transit"],
        hoverinfo="text",
        name="Chokepoint",
    ))

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=HORMUZ_CENTER["lat"], lon=HORMUZ_CENTER["lon"]),
            zoom=5.2,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Share Tech Mono", color="#94a3b8"),
        margin=dict(l=0, r=0, t=0, b=0),
        height=480,
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# FUNDAMENTAL EQUILIBRIUM ESTIMATOR
# ---------------------------------------------------------------------------
def estimate_fundamental_equilibrium(df_1y, df_5y):
    """
    Estimates a fundamental equilibrium price for crude oil using:
    1. 5-year rolling median (structural floor/ceiling)
    2. 1-year weighted mean (recent supply/demand balance)
    3. Blended estimate with recency bias
    """
    eq_5y = np.nan
    eq_1y = np.nan

    if df_5y is not None and not df_5y.empty and len(df_5y) > 20:
        eq_5y = df_5y["Close"].median()
    if df_1y is not None and not df_1y.empty and len(df_1y) > 20:
        # Exponentially-weighted mean gives more weight to recent prices
        weights = np.exp(np.linspace(-1, 0, len(df_1y)))
        weights /= weights.sum()
        eq_1y = np.average(df_1y["Close"].values, weights=weights)

    if np.isnan(eq_5y) and np.isnan(eq_1y):
        return 75.0  # fallback
    elif np.isnan(eq_5y):
        return round(eq_1y, 2)
    elif np.isnan(eq_1y):
        return round(eq_5y, 2)
    else:
        # 60% weight to recent (1Y), 40% to structural (5Y)
        return round(0.6 * eq_1y + 0.4 * eq_5y, 2)


# ---------------------------------------------------------------------------
# MEAN-REVERTING JUMP-DIFFUSION MONTE CARLO (O-U PROCESS)
# ---------------------------------------------------------------------------
# Seasonal crude demand adjustment (daily additive to log-equilibrium)
# Peaks in Q4/Q1 (winter heating + refinery runs), troughs Q2/Q3
SEASONAL_MONTHLY = {
    1: 0.020, 2: 0.010, 3: -0.005, 4: -0.015,
    5: -0.020, 6: -0.015, 7: -0.005, 8: 0.005,
    9: 0.015, 10: 0.025, 11: 0.020, 12: 0.020,
}


def commodity_mean_reversion_mc(
    df_1y, current_price, target_price, days_to_target,
    regime, fundamental_eq, n_sims=30_000,
):
    """
    Ornstein-Uhlenbeck Mean-Reverting Jump-Diffusion for commodity prices.

    Model (in log-price space):
        dX = kappa * (theta_adj - X) dt  +  sigma * dW  +  J * dN

    Key differences from v1 GBM:
        - Mean-reverting: prices pull toward equilibrium, not drift to infinity
        - Equilibrium shifts with regime (risk premium) and season
        - Reversion speed decreases in crisis (prices stay elevated longer)
        - Calibrated from historical data via OLS on log-price increments
    """
    if df_1y is None or df_1y.empty or len(df_1y) < 60:
        return None, None

    close = df_1y["Close"].dropna()
    log_prices = np.log(close.values)
    log_ret = np.diff(log_prices)

    # --- Estimate O-U parameters via OLS: dX_t = a + b * X_{t-1} + eps ---
    X_lag = log_prices[:-1]
    if np.var(X_lag) < 1e-12:
        return None, None

    b_hat = np.cov(log_ret, X_lag)[0, 1] / np.var(X_lag)
    a_hat = np.mean(log_ret) - b_hat * np.mean(X_lag)

    kappa_est = max(-b_hat, 0.002)  # enforce positive mean reversion
    theta_est = -a_hat / b_hat if abs(b_hat) > 1e-8 else np.mean(log_prices)
    sigma_est = np.std(log_ret)

    # Override theta with fundamental estimate (more robust than pure OLS)
    theta_base = np.log(max(fundamental_eq, 10.0))

    # --- Regime switching ---
    regime_params = {
        "NORMAL (HISTORICAL)": {
            "kappa_mult": 1.0, "sigma_mult": 1.0,
            "jump_prob": 0.002, "jump_mu": 0.00, "jump_sig": 0.01,
            "risk_premium": 0.00,
        },
        "BLOCKADE (ACTIVE)": {
            "kappa_mult": 0.30, "sigma_mult": 1.80,
            "jump_prob": 0.015, "jump_mu": 0.04, "jump_sig": 0.03,
            "risk_premium": 0.15,
        },
        "REGIONAL ESCALATION": {
            "kappa_mult": 0.10, "sigma_mult": 2.50,
            "jump_prob": 0.040, "jump_mu": 0.08, "jump_sig": 0.06,
            "risk_premium": 0.30,
        },
    }
    rp = regime_params.get(regime, regime_params["NORMAL (HISTORICAL)"])

    kappa = kappa_est * rp["kappa_mult"]
    sigma = sigma_est * rp["sigma_mult"]
    risk_premium = rp["risk_premium"]
    theta_adj = theta_base + np.log(1.0 + risk_premium)

    # --- Simulate ---
    rng = np.random.default_rng(seed=42)
    n_days = max(1, days_to_target)
    log_S = np.empty((n_sims, n_days))
    log_S[:, 0] = np.log(current_price)

    dt = 1.0
    sqrt_dt = np.sqrt(dt)

    for t in range(1, n_days):
        future_month = (datetime.now() + timedelta(days=t)).month
        seasonal = SEASONAL_MONTHLY.get(future_month, 0.0) / 30.0  # daily portion

        # Target for this timestep includes seasonal demand shift
        theta_t = theta_adj + seasonal

        # Mean-reverting drift
        drift = kappa * (theta_t - log_S[:, t - 1]) * dt

        # Diffusion (Brownian motion)
        diffusion = sigma * rng.normal(0, 1, n_sims) * sqrt_dt

        # Poisson jumps (supply disruptions, OPEC surprises, etc.)
        jump_mask = rng.random(n_sims) < rp["jump_prob"]
        jumps = np.where(
            jump_mask,
            rng.normal(rp["jump_mu"], rp["jump_sig"], n_sims),
            0.0,
        )

        log_S[:, t] = log_S[:, t - 1] + drift + diffusion + jumps

    prices = np.exp(log_S)
    finals = prices[:, -1]
    half_life = round(np.log(2) / kappa, 1) if kappa > 1e-6 else float("inf")

    stats = {
        "p_hit_target": round(np.mean(finals >= target_price) * 100, 1),
        "p_above_120": round(np.mean(finals >= 120) * 100, 1),
        "p_below_60": round(np.mean(finals <= 60) * 100, 1),
        "median": round(float(np.percentile(finals, 50)), 2),
        "mean": round(float(np.mean(finals)), 2),
        "p95": round(float(np.percentile(finals, 95)), 2),
        "p75": round(float(np.percentile(finals, 75)), 2),
        "p25": round(float(np.percentile(finals, 25)), 2),
        "p5": round(float(np.percentile(finals, 5)), 2),
        "mode": round(float(
            np.histogram(finals, bins=200)[1][np.argmax(np.histogram(finals, bins=200)[0])]
        ), 2),
        "sims": n_sims,
        "regime": regime,
        "model": {
            "type": "Ornstein-Uhlenbeck Mean-Reverting Jump-Diffusion",
            "kappa_raw": round(float(kappa_est), 5),
            "kappa_regime": round(float(kappa), 5),
            "theta_fundamental": round(float(fundamental_eq), 2),
            "theta_regime_adj": round(float(np.exp(theta_adj)), 2),
            "sigma_raw": round(float(sigma_est), 5),
            "sigma_regime": round(float(sigma), 5),
            "risk_premium_pct": round(risk_premium * 100, 1),
            "half_life_days": half_life,
            "jump_prob_daily": rp["jump_prob"],
            "jump_mu": rp["jump_mu"],
        },
    }
    return stats, prices


# ---------------------------------------------------------------------------
# CHARTING FACTORY
# ---------------------------------------------------------------------------
CHART_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Share Tech Mono", color="#94a3b8"),
    margin=dict(l=40, r=20, t=30, b=30),
    xaxis=dict(gridcolor="rgba(30, 41, 59, 0.5)", zeroline=False),
    yaxis=dict(gridcolor="rgba(30, 41, 59, 0.5)", zeroline=False),
)


def build_fan_chart(historical_df, paths, start_price, days_to_target, eq_price, eq_adj):
    """Builds a predictive cone showing mean-reversion toward equilibrium."""
    hist = historical_df.tail(90)
    future_dates = [datetime.now() + timedelta(days=i) for i in range(days_to_target)]

    p5 = np.percentile(paths, 5, axis=0)
    p25 = np.percentile(paths, 25, axis=0)
    p50 = np.percentile(paths, 50, axis=0)
    p75 = np.percentile(paths, 75, axis=0)
    p95 = np.percentile(paths, 95, axis=0)

    fig = go.Figure()

    # Historical trace
    fig.add_trace(go.Scatter(
        x=hist.index, y=hist["Close"], mode="lines",
        name="Historical", line=dict(color="#94a3b8", width=2),
    ))

    # 90% confidence band (P5-P95)
    fig.add_trace(go.Scatter(
        x=future_dates, y=p95, mode="lines", line=dict(width=0), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=future_dates, y=p5, mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(6, 182, 212, 0.08)", name="90% Band",
    ))

    # 50% confidence band (P25-P75)
    fig.add_trace(go.Scatter(
        x=future_dates, y=p75, mode="lines", line=dict(width=0), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=future_dates, y=p25, mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(6, 182, 212, 0.18)", name="50% Band",
    ))

    # Median prediction
    fig.add_trace(go.Scatter(
        x=future_dates, y=p50, mode="lines", name="Median Path",
        line=dict(color="#06b6d4", width=2, dash="dot"),
    ))

    # Fundamental equilibrium line
    fig.add_hline(
        y=eq_price, line_dash="dash", line_color="#64748b",
        annotation_text=f"Fundamental EQ: ${eq_price:.0f}",
        annotation_font=dict(color="#64748b", size=10, family="Share Tech Mono"),
    )
    # Regime-adjusted equilibrium
    if abs(eq_adj - eq_price) > 1.0:
        fig.add_hline(
            y=eq_adj, line_dash="dash", line_color="#f59e0b",
            annotation_text=f"Regime EQ: ${eq_adj:.0f}",
            annotation_font=dict(color="#f59e0b", size=10, family="Share Tech Mono"),
        )

    fig.update_layout(
        **CHART_THEME, height=380,
        title=dict(text="MEAN-REVERTING PRICE TRAJECTORY", font=dict(size=14, color="#fff")),
        showlegend=True, legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )
    return fig


def build_distribution_chart(paths):
    """Histogram of terminal price distribution."""
    finals = paths[:, -1]
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=finals, nbinsx=120, marker_color="rgba(6, 182, 212, 0.6)",
        marker_line=dict(color="#06b6d4", width=0.5),
    ))
    fig.add_vline(x=np.median(finals), line_dash="dash", line_color="#fff",
                  annotation_text="Median", annotation_font=dict(color="#fff", size=10))
    fig.update_layout(
        **CHART_THEME, height=250,
        title=dict(text="TERMINAL PRICE DISTRIBUTION", font=dict(size=12, color="#fff")),
        xaxis_title="Price (USD)", yaxis_title="Frequency",
        bargap=0.02,
    )
    return fig


def build_spread_chart(brent_1y, wti_1y):
    """BZ/WTI spread chart indicating market structure."""
    if brent_1y.empty or wti_1y.empty:
        return None
    merged = pd.DataFrame({
        "Brent": brent_1y["Close"], "WTI": wti_1y["Close"],
    }).dropna().tail(252)
    if merged.empty:
        return None
    merged["Spread"] = merged["Brent"] - merged["WTI"]
    avg_spread = merged["Spread"].mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=merged.index, y=merged["Spread"], mode="lines",
        name="BZ/WTI Spread", line=dict(color="#06b6d4", width=1.5),
        fill="tozeroy", fillcolor="rgba(6, 182, 212, 0.1)",
    ))
    fig.add_hline(y=avg_spread, line_dash="dash", line_color="#64748b",
                  annotation_text=f"Avg: ${avg_spread:.2f}",
                  annotation_font=dict(color="#64748b", size=10))
    fig.update_layout(
        **CHART_THEME, height=220,
        title=dict(text="BZ/WTI SPREAD (MARKET STRUCTURE)", font=dict(size=12, color="#fff")),
        yaxis_title="USD",
    )
    return fig


# ---------------------------------------------------------------------------
# ANTHROPIC AI ENGINE
# ---------------------------------------------------------------------------
def get_anthropic_client():
    """Returns an Anthropic client if API key is configured."""
    try:
        import anthropic
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return None
        return anthropic.Anthropic(api_key=api_key)
    except Exception:
        return None


@st.cache_data(ttl=900, show_spinner=False)  # cache briefings for 15 min
def generate_tactical_briefing(
    current_price, price_change, spread, regime, mc_stats_json, eq_price, ovx_val
):
    """
    Calls Claude with web search to generate a live tactical intelligence briefing.
    """
    client = get_anthropic_client()
    if client is None:
        return None

    mc_stats = json.loads(mc_stats_json) if mc_stats_json else {}

    system_prompt = (
        "You are OVERWATCH, a tactical commodity intelligence system used by a "
        "medical device company's quality and supply chain team. Your analysis directly "
        "informs procurement timing, supplier contract negotiations, and risk mitigation "
        "for a 2,500-SKU DME portfolio sourced primarily from China.\n\n"
        "Write in concise, direct military-style intelligence format. Use uppercase section "
        "headers. No filler. Every sentence should be actionable or informative. "
        "Reference specific data points from your web search results."
    )

    user_prompt = f"""CURRENT LIVE MARKET DATA (as of {datetime.now().strftime('%d %b %Y %H:%M UTC')}):
- Brent Crude Spot: ${current_price:.2f} ({price_change:+.2f} today)
- BZ/WTI Spread: ${spread:.2f}
- OVX (Oil Volatility Index): {ovx_val:.1f}
- Active Threat Regime: {regime}
- Monte Carlo Median ({mc_stats.get('model', {}).get('half_life_days', 'N/A')}d half-life): ${mc_stats.get('median', 'N/A')}
- MC 90% Confidence Band: [${mc_stats.get('p5', 'N/A')} - ${mc_stats.get('p95', 'N/A')}]
- P(>=$120 shock): {mc_stats.get('p_above_120', 'N/A')}%
- Fundamental Equilibrium: ${eq_price:.2f}

Search the web for the latest information on ALL of the following topics, then synthesize into a single briefing:
1. Brent crude oil price drivers and recent movements
2. OPEC+ production decisions and compliance
3. Strait of Hormuz and Persian Gulf tensions
4. Iran sanctions status and regional military developments
5. Global crude oil inventory levels (EIA, IEA)
6. Petrochemical and plastic resin price trends
7. China manufacturing activity and PMI data
8. Container shipping rates (relevant for China-sourced medical devices)

REQUIRED OUTPUT FORMAT (use these exact headers):

SITUATION OVERVIEW
(2-3 sentences: what is driving Brent right now)

SUPPLY ASSESSMENT
(OPEC actions, US shale output, inventory trends, production disruptions)

DEMAND SIGNALS
(China PMI, global refinery runs, seasonal patterns, macro indicators)

GEOPOLITICAL RISK FACTORS
(Hormuz, Iran, sanctions, naval activity, escalation probability)

PRICE OUTLOOK ({mc_stats.get('model', {}).get('half_life_days', 90)}-DAY HORIZON)
(Your assessment synthesizing the MC model data with fundamental/geopolitical context. State whether you believe the model output is reasonable, conservative, or aggressive given current conditions.)

MED-DEV SUPPLY CHAIN IMPACT
(Specific implications for: polypropylene/nylon resin pricing, aluminum smelting surcharges, container freight rates, and recommended procurement actions for a DME company sourcing from China)

BOTTOM LINE
(One-paragraph executive summary with the single most important takeaway)"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=system_prompt,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": user_prompt}],
        )

        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        return "\n".join(text_parts)
    except Exception as e:
        return f"[COMMS ERROR] Briefing generation failed: {e}"


@st.cache_data(ttl=900, show_spinner=False)
def generate_supply_chain_briefing(
    brent_price, plastic_price, plastic_pct, alum_price, alum_pct, copper_price, copper_pct
):
    """Calls Claude for a focused med-dev supply chain impact analysis."""
    client = get_anthropic_client()
    if client is None:
        return None

    prompt = f"""You are a supply chain intelligence analyst for a medical device / DME company with 2,500+ SKUs sourced primarily from Chinese manufacturers. Analyze the current raw material situation:

LIVE COMMODITY DATA:
- Brent Crude: ${brent_price:.2f}
- Petrochemical Proxy (DOW): ${plastic_price:.2f} ({plastic_pct:+.1f}% 30-day)
- Aluminum Futures: ${alum_price:.2f} ({alum_pct:+.1f}% 30-day)
- Copper Futures: ${copper_price:.4f} ({copper_pct:+.1f}% 30-day)

Search the web for current polypropylene resin prices, PA6 nylon prices, injection molding cost trends, and China-to-US container shipping rates. Then provide:

1. MATERIAL COST TRAJECTORY (30/60/90 day outlook for PP, PA6, PE, aluminum)
2. SPECIFIC PRODUCT IMPACTS (walker boots, knee braces, wheelchairs, TENS units, nebulizers -- these are real product categories)
3. RECOMMENDED ACTIONS (contract lock-ins, alternative sourcing, inventory buffer recommendations)
4. FREIGHT OUTLOOK (container rates, port congestion, lead time expectations)

Be specific with numbers. No filler. This goes directly to procurement and quality leadership."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}],
        )
        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        return "\n".join(text_parts)
    except Exception as e:
        return f"[COMMS ERROR] Supply chain briefing failed: {e}"


# ---------------------------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------------------------
# Cache TTL is configurable from sidebar (needs to be before sidebar renders)
if "cache_ttl" not in st.session_state:
    st.session_state["cache_ttl"] = 300

data = fetch_stratcom_data(cache_ttl_key=st.session_state["cache_ttl"])

brent = data.get("brent_1y", pd.DataFrame())
brent_5y = data.get("brent_5y", pd.DataFrame())
brent_1d = data.get("brent_1d", pd.DataFrame())
wti_1y = data.get("wti_1y", pd.DataFrame())

# Best-effort current price: intraday -> daily -> FRED daily
current_bz = 0.0
bz_source_label = "N/A"
if not brent_1d.empty:
    current_bz = brent_1d["Close"].iloc[-1]
    bz_source_label = "INTRADAY"
elif not brent.empty:
    current_bz = brent["Close"].iloc[-1]
    bz_source_label = "DAILY CLOSE"

bz_change = current_bz - brent["Close"].iloc[-2] if len(brent) > 1 else 0.0

ovx_df = data.get("ovx_1y", pd.DataFrame())
ovx_val = ovx_df["Close"].iloc[-1] if not ovx_df.empty else 0.0

dxy_df = data.get("dxy_1y", pd.DataFrame())
dxy_val = dxy_df["Close"].iloc[-1] if not dxy_df.empty else 0.0

fetch_time = data.get("fetch_time", None)
data_age_str, data_age_color = format_data_age(fetch_time)
sources = data.get("sources", {})

# Estimate fundamental equilibrium
auto_eq = estimate_fundamental_equilibrium(brent, brent_5y)

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        "<h2 style='color:var(--cyan); margin-bottom: 0;'>OVERWATCH</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p class='mono-text' style='color:#64748b; font-size: 10px;'>"
        "GLOBAL THREAT & COMMODITY DIRECTORATE v2.1</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    menu = st.radio(
        "OPERATIONAL VIEWS",
        [
            "1. GLOBAL ENERGY (BRENT)",
            "2. HORMUZ THEATER [LIVE RECON]",
            "3. MED-DEV SUPPLY CHAIN",
            "4. AI TACTICAL BRIEFING",
        ],
    )

    st.markdown("---")
    st.markdown("<div class='panel-title'>PREDICTIVE TARGETING</div>", unsafe_allow_html=True)
    target_date = st.date_input(
        "ESTIMATE PRICE ON DATE:", datetime.now() + timedelta(days=90)
    )
    target_price = st.number_input(
        "TARGET PRICE THRESHOLD ($):", min_value=10.0, max_value=300.0, value=94.50, step=0.5
    )
    regime = st.selectbox(
        "THREAT REGIME (VOL/DRIFT)",
        ["NORMAL (HISTORICAL)", "BLOCKADE (ACTIVE)", "REGIONAL ESCALATION"],
        index=1,
    )

    st.markdown("---")
    st.markdown("<div class='panel-title'>FUNDAMENTAL EQUILIBRIUM</div>", unsafe_allow_html=True)
    eq_override = st.number_input(
        "EQUILIBRIUM PRICE ($):",
        min_value=20.0, max_value=200.0, value=float(auto_eq), step=1.0,
        help="Auto-estimated from 1Y/5Y price history. Override to set your own supply/demand thesis.",
    )
    st.markdown(
        f"<p class='mono-text' style='color:#64748b; font-size:9px;'>"
        f"AUTO-ESTIMATE: ${auto_eq:.2f} (60% 1Y EWM + 40% 5Y MEDIAN)</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("<div class='panel-title'>DATA & CACHING</div>", unsafe_allow_html=True)
    cache_ttl_opt = st.select_slider(
        "CACHE TTL (SEC):",
        options=[60, 120, 300, 600, 900, 1800],
        value=st.session_state.get("cache_ttl", 300),
        help="Higher = fewer API calls = less rate-limiting. 300s recommended.",
    )
    if cache_ttl_opt != st.session_state.get("cache_ttl"):
        st.session_state["cache_ttl"] = cache_ttl_opt
        st.cache_data.clear()
        st.rerun()

    # Data source status
    yf_count = sum(1 for s in sources.values() if s.get("source") == "yfinance")
    fred_count = sum(1 for s in sources.values() if s.get("source") == "FRED")
    fail_count = sum(1 for s in sources.values() if s.get("source") == "FAILED")
    total = len(sources)

    st.markdown(
        f"<div style='margin-top:8px;'>"
        f"<span class='source-tag src-yf'>YF: {yf_count}/{total}</span> "
        f"<span class='source-tag src-fred'>FRED: {fred_count}/{total}</span> "
        f"<span class='source-tag src-fail'>FAIL: {fail_count}/{total}</span>"
        f"</div>"
        f"<p class='mono-text' style='color:{data_age_color}; font-size:10px; margin-top:4px;'>"
        f"DATA AGE: {data_age_str}</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown(
        "<p class='mono-text' style='color:#94a3b8; font-size:9px;'>"
        "PRIMARY: YFINANCE (INDIVIDUAL+RETRY)<br>"
        "FALLBACK: FRED API (DAILY CLOSE)<br>"
        "MAPS: LIVE SATELLITE AIS/ADSB<br>"
        "MODEL: O-U MEAN-REVERTING JUMP-DIFFUSION<br>"
        "AI: ANTHROPIC CLAUDE + WEB SEARCH</p>",
        unsafe_allow_html=True,
    )

    if st.button("EXECUTE REFRESH [F5]"):
        st.cache_data.clear()
        st.rerun()

days_out = max(1, (target_date - datetime.now().date()).days)

# Compute MC once -- reused across views
mc_res, paths = commodity_mean_reversion_mc(
    brent, current_bz, target_price, days_out, regime, eq_override
)

# WTI / Spread
wti_1d = data.get("wti_1d", pd.DataFrame())
cur_wti = wti_1d["Close"].iloc[-1] if not wti_1d.empty else 0.0
spread = current_bz - cur_wti

# ===========================================================================
# VIEW 1: GLOBAL ENERGY
# ===========================================================================
if menu.startswith("1"):
    st.markdown("<h2>GLOBAL ENERGY TRACKER: BRENT CRUDE (BZ=F)</h2>", unsafe_allow_html=True)

    # --- Data freshness bar ---
    source_items_html = ""
    for key in ["brent_1d", "brent_1y", "wti_1d", "ovx_1y"]:
        s = sources.get(key, {})
        src = s.get("source", "?")
        src_cls = "src-yf" if src == "yfinance" else "src-fred" if src == "FRED" else "src-fail"
        dot_color = "var(--green)" if src == "yfinance" else "var(--cyan)" if src == "FRED" else "var(--red)"
        label = key.upper().replace("_", " ")
        source_items_html += (
            f"<span class='freshness-item'>"
            f"<span class='freshness-dot' style='background:{dot_color};'></span>"
            f"{label} <span class='source-tag {src_cls}'>{src}</span></span>"
        )
    st.markdown(
        f"<div class='freshness-bar'>"
        f"<span class='freshness-item' style='color:{data_age_color};'>FETCHED: {data_age_str}</span>"
        f"{source_items_html}</div>",
        unsafe_allow_html=True,
    )

    # --- Top cards ---
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(
            f"<div class='tac-panel'><div class='panel-title'>BRENT SPOT [{bz_source_label}]</div>"
            f"<div class='panel-value'>${current_bz:.2f} "
            f"<span style='font-size:14px; color:{var_color(bz_change)}'>[{bz_change:+.2f}]</span>"
            f"</div></div>",
            unsafe_allow_html=True,
        )
    with c2:
        wti_src = sources.get("wti_1d", {}).get("source", "?")
        wti_label = "INTRADAY" if wti_src == "yfinance" and not data.get("wti_1d", pd.DataFrame()).empty else "DAILY"
        st.markdown(
            f"<div class='tac-panel'><div class='panel-title'>WTI SPOT [{wti_label}]</div>"
            f"<div class='panel-value'>${cur_wti:.2f}</div></div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"<div class='tac-panel'><div class='panel-title'>BZ/WTI SPREAD</div>"
            f"<div class='panel-value'>${spread:.2f}</div></div>",
            unsafe_allow_html=True,
        )
    with c4:
        ovx_cls = alert_class(ovx_val, warn_thresh=30, crit_thresh=45)
        st.markdown(
            f"<div class='tac-panel {ovx_cls}'><div class='panel-title'>OVX (OIL VOL)</div>"
            f"<div class='panel-value' style='font-size:24px;'>{ovx_val:.1f}</div></div>",
            unsafe_allow_html=True,
        )
    with c5:
        panel_class = (
            "alert-warn" if regime == "BLOCKADE (ACTIVE)"
            else "alert-critical" if regime == "REGIONAL ESCALATION"
            else ""
        )
        st.markdown(
            f"<div class='tac-panel {panel_class}'><div class='panel-title'>THREAT REGIME</div>"
            f"<div class='panel-value' style='font-size:18px; margin-top:8px;'>"
            f"{regime.split()[0]}</div></div>",
            unsafe_allow_html=True,
        )

    # --- Fan chart + projections ---
    c_chart, c_pred = st.columns([6, 4])

    with c_chart:
        if not brent.empty and paths is not None:
            eq_adj = mc_res["model"]["theta_regime_adj"] if mc_res else eq_override
            fig = build_fan_chart(brent, paths, current_bz, days_out, eq_override, eq_adj)
            st.plotly_chart(fig, use_container_width=True)

    with c_pred:
        if mc_res:
            st.markdown("<div class='tac-panel' style='min-height:370px;'>", unsafe_allow_html=True)
            st.markdown("<div class='panel-title'>MEAN-REVERTING PROJECTION</div>", unsafe_allow_html=True)
            st.markdown(
                f"<p class='mono-text' style='font-size:10px; color:#64748b;'>"
                f"TARGET: {target_date.strftime('%d %b %Y').upper()} | "
                f"SIMS: {mc_res['sims']:,} | HALF-LIFE: {mc_res['model']['half_life_days']}D</p>"
                f"<hr style='border-color:#1e293b'>",
                unsafe_allow_html=True,
            )

            p1, p2 = st.columns(2)
            with p1:
                st.markdown(
                    f"<div style='margin-bottom:12px;'>"
                    f"<div class='mono-text' style='color:#94a3b8; font-size:11px;'>P(>= ${target_price:.2f})</div>"
                    f"<div class='mono-text' style='color:var(--cyan); font-size:22px;'>{mc_res['p_hit_target']}%</div></div>"
                    f"<div style='margin-bottom:12px;'>"
                    f"<div class='mono-text' style='color:#94a3b8; font-size:11px;'>P(SHOCK >= $120)</div>"
                    f"<div class='mono-text' style='color:var(--red); font-size:22px;'>{mc_res['p_above_120']}%</div></div>"
                    f"<div style='margin-bottom:12px;'>"
                    f"<div class='mono-text' style='color:#94a3b8; font-size:11px;'>P(COLLAPSE <= $60)</div>"
                    f"<div class='mono-text' style='color:var(--green); font-size:22px;'>{mc_res['p_below_60']}%</div></div>",
                    unsafe_allow_html=True,
                )
            with p2:
                st.markdown(
                    f"<div style='margin-bottom:12px;'>"
                    f"<div class='mono-text' style='color:#94a3b8; font-size:11px;'>MEDIAN</div>"
                    f"<div class='mono-text' style='color:#fff; font-size:22px;'>${mc_res['median']}</div></div>"
                    f"<div style='margin-bottom:12px;'>"
                    f"<div class='mono-text' style='color:#94a3b8; font-size:11px;'>MEAN</div>"
                    f"<div class='mono-text' style='color:#fff; font-size:22px;'>${mc_res['mean']}</div></div>"
                    f"<div style='margin-bottom:12px;'>"
                    f"<div class='mono-text' style='color:#94a3b8; font-size:11px;'>MODE (MOST LIKELY)</div>"
                    f"<div class='mono-text' style='color:#fff; font-size:22px;'>${mc_res['mode']}</div></div>",
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"<div style='padding-top:8px; border-top: 1px solid #1e293b;'>"
                f"<div class='mono-text' style='font-size:11px; color:#94a3b8;'>CONFIDENCE INTERVALS</div>"
                f"<div class='mono-text' style='color:var(--amber); font-size:13px;'>"
                f"90%: [{mc_res['p5']} - {mc_res['p95']}]</div>"
                f"<div class='mono-text' style='color:#06b6d4; font-size:13px;'>"
                f"50%: [{mc_res['p25']} - {mc_res['p75']}]</div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

    # --- Distribution + Spread row ---
    c_dist, c_spread = st.columns([6, 4])
    with c_dist:
        if paths is not None:
            fig_dist = build_distribution_chart(paths)
            st.plotly_chart(fig_dist, use_container_width=True)
    with c_spread:
        fig_sp = build_spread_chart(brent, wti_1y)
        if fig_sp:
            st.plotly_chart(fig_sp, use_container_width=True)

    # --- Model diagnostics ---
    if mc_res:
        with st.expander("MODEL DIAGNOSTICS & PARAMETERS", expanded=False):
            m = mc_res["model"]
            st.markdown(
                f"""
<div class='tac-panel' style='padding:12px;'>
<div class='panel-title'>ORNSTEIN-UHLENBECK MEAN-REVERTING JUMP-DIFFUSION</div>
<div style='display:grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-top:10px;'>
    <div><div class='diag-label'>KAPPA (RAW)</div><div class='diag-value'>{m["kappa_raw"]}</div></div>
    <div><div class='diag-label'>KAPPA (REGIME-ADJ)</div><div class='diag-value'>{m["kappa_regime"]}</div></div>
    <div><div class='diag-label'>HALF-LIFE (DAYS)</div><div class='diag-value'>{m["half_life_days"]}</div></div>
    <div><div class='diag-label'>THETA (FUNDAMENTAL)</div><div class='diag-value'>${m["theta_fundamental"]}</div></div>
    <div><div class='diag-label'>THETA (REGIME-ADJ)</div><div class='diag-value'>${m["theta_regime_adj"]}</div></div>
    <div><div class='diag-label'>RISK PREMIUM</div><div class='diag-value'>{m["risk_premium_pct"]}%</div></div>
    <div><div class='diag-label'>SIGMA (RAW)</div><div class='diag-value'>{m["sigma_raw"]}</div></div>
    <div><div class='diag-label'>SIGMA (REGIME-ADJ)</div><div class='diag-value'>{m["sigma_regime"]}</div></div>
    <div><div class='diag-label'>JUMP PROB (DAILY)</div><div class='diag-value'>{m["jump_prob_daily"]}</div></div>
</div>
<div style='margin-top:12px; padding-top:8px; border-top: 1px dashed #1e293b;'>
    <div class='mono-text' style='font-size:10px; color:#64748b; line-height:1.6;'>
    MODEL: dX = kappa*(theta - X)*dt + sigma*dW + J*dN where X=ln(S). Mean-reverting: prices pull toward
    fundamental equilibrium (theta) at speed kappa. Crisis regimes slow reversion (prices stay elevated)
    and inflate theta by the geopolitical risk premium. Jumps model discrete supply disruptions.
    Seasonal demand curve overlays monthly crude consumption patterns.
    </div>
</div>
</div>
""",
                unsafe_allow_html=True,
            )

    # --- Data source diagnostics ---
    with st.expander("DATA SOURCE DIAGNOSTICS", expanded=False):
        source_rows = ""
        for key, info in sorted(sources.items()):
            src = info.get("source", "?")
            src_cls = "src-yf" if src == "yfinance" else "src-fred" if src == "FRED" else "src-fail"
            source_rows += (
                f"<div class='diag-row'>"
                f"<span class='diag-label'>{key.upper()}</span>"
                f"<span class='diag-value'>"
                f"<span class='source-tag {src_cls}'>{src}</span> "
                f"{info.get('rows', 0)} rows | latest: {info.get('latest', 'N/A')}"
                f"</span></div>"
            )
        fred_key_status = "CONFIGURED" if st.secrets.get("FRED_API_KEY", "") else "NOT SET (anonymous access)"
        st.markdown(
            f"<div class='tac-panel' style='padding:12px;'>"
            f"<div class='panel-title'>PER-TICKER SOURCE & FRESHNESS</div>"
            f"{source_rows}"
            f"<div style='margin-top:10px; padding-top:8px; border-top:1px dashed #1e293b;'>"
            f"<div class='mono-text' style='font-size:10px; color:#64748b; line-height:1.6;'>"
            f"FETCH STRATEGY: Individual tickers with 3x exponential backoff + jitter (0.5s inter-ticker delay).<br>"
            f"FALLBACK: FRED API for daily Brent/WTI when yfinance is rate-limited.<br>"
            f"FRED KEY: {fred_key_status}<br>"
            f"NOTE: yfinance futures data is inherently 15-20 min delayed on free tier. "
            f"FRED provides daily close only (no intraday). For real-time futures, "
            f"a paid feed (Polygon, Twelve Data, etc.) is required."
            f"</div></div></div>",
            unsafe_allow_html=True,
        )


# ===========================================================================
# VIEW 2: HORMUZ THEATER [LIVE RECON]
# ===========================================================================
elif menu.startswith("2"):
    st.markdown("<h2>THEATER SITREP: STRAIT OF HORMUZ</h2>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.markdown(
        "<div class='tac-panel alert-critical'><div class='panel-title'>BLOCKADE STATUS [SIMULATED]</div>"
        "<div class='panel-value'>ACTIVE</div></div>",
        unsafe_allow_html=True,
    )
    c2.markdown(
        "<div class='tac-panel'><div class='panel-title'>CHOKEPOINT</div>"
        "<div class='panel-value'>26.4 N, 56.2 E</div></div>",
        unsafe_allow_html=True,
    )
    c3.markdown(
        "<div class='tac-panel alert-critical'><div class='panel-title'>GLOBAL FLOW DISRUPTION [SIMULATED]</div>"
        "<div class='panel-value'>95%</div></div>",
        unsafe_allow_html=True,
    )

    c_ship, c_air = st.columns(2)

    with c_ship:
        st.markdown(
            "<div class='panel-title' style='color:var(--cyan);'>LIVE AIS MARITIME TRAFFIC (STRAIT OF HORMUZ)</div>",
            unsafe_allow_html=True,
        )
        # VesselFinder free embed -- explicitly supports iframe embedding
        vf_html = """
        <iframe
            src="https://www.vesselfinder.com/aismap?lat=26.4&lon=56.2&zoom=7&width=100%25&height=460&names=false&mmsi=0&track=0&fleet=&fleet_name=&fleet_id="
            style="width:100%; height:460px; border:1px solid #1e293b; border-radius:4px;"
            sandbox="allow-scripts allow-same-origin"
            loading="lazy"
        ></iframe>
        <div style="font-family: monospace; font-size: 10px; color: #64748b; margin-top:5px; text-align: right;">
            DATA: VESSELFINDER LIVE AIS | <a href="https://www.vesselfinder.com/?lat=26.4&lon=56.2&zoom=7" target="_blank" style="color:#06b6d4;">OPEN FULL MAP</a>
        </div>
        """
        components.html(vf_html, height=500)

    with c_air:
        st.markdown(
            "<div class='panel-title' style='color:var(--cyan);'>LIVE ADS-B FLIGHT RADAR (PERSIAN GULF)</div>",
            unsafe_allow_html=True,
        )
        adsb_df, adsb_status, adsb_source = fetch_adsb_data()

        if not adsb_df.empty:
            fig_adsb = build_adsb_map(adsb_df, adsb_source)
            if fig_adsb:
                st.plotly_chart(fig_adsb, use_container_width=True)
            src_cls = "src-yf" if adsb_source == "adsb.lol" else "src-fred" if adsb_source == "OpenSky" else "src-fail"
            st.markdown(
                f"<div style='font-family: monospace; font-size: 10px; color: #64748b; text-align: right;'>"
                f"DATA: <span class='source-tag {src_cls}'>{adsb_source.upper()}</span> LIVE ADS-B | {adsb_status} | "
                f"<span style='color:#10b981;'>GND</span> "
                f"<span style='color:#06b6d4;'>LOW</span> "
                f"<span style='color:#f59e0b;'>MED</span> "
                f"<span style='color:#ef4444;'>HIGH</span> ALT</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class='tac-panel alert-warn' style='height:460px; display:flex; flex-direction:column; justify-content:center; align-items:center;'>"
                f"<div class='panel-title'>ADS-B FEED STATUS</div>"
                f"<div class='mono-text' style='color:var(--amber); font-size:14px; margin-top:10px;'>{adsb_status}</div>"
                f"<div class='mono-text' style='color:#64748b; font-size:11px; margin-top:15px; text-align:center; line-height:1.6;'>"
                f"Both adsb.lol and OpenSky Network failed.<br>"
                f"Data refreshes every 45 seconds automatically.<br>"
                f"This is usually transient -- wait for next cycle.</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown(
        "<div class='panel-title'>SIGINT TIMELINE [SIMULATED WARGAME SCENARIO]</div>",
        unsafe_allow_html=True,
    )
    feed_html = """
    <div class="terminal-feed" style="height: 150px;">
        <div class="term-line"><span class="term-date">20MAR26 0800Z</span> <span class="term-crit">[CRITICAL]</span> BRENT SURPASSES $107. ONLY 21 TRANSITS LOGGED SINCE LATE FEB.</div>
        <div class="term-line"><span class="term-date">19MAR26 1430Z</span> <span class="term-crit">[CRITICAL]</span> ISRAELI STRIKE CONFIRMED ON SOUTH PARS. IRAN RETALIATES AT RAS LAFFAN.</div>
        <div class="term-line"><span class="term-date">18MAR26 0915Z</span> [INFO] TURKISH AND INDIAN SHIPS GRANTED SAFE PASSAGE EXCEPTION.</div>
        <div class="term-line"><span class="term-date">17MAR26 1100Z</span> <span class="term-crit">[CRITICAL]</span> SUPREME LEADER MOJTABA KHAMENEI REITERATES TOTAL BLOCKADE ON WESTERN HULLS.</div>
    </div>
    """
    st.markdown(feed_html, unsafe_allow_html=True)


# ===========================================================================
# VIEW 3: MED-DEV SUPPLY CHAIN
# ===========================================================================
elif menu.startswith("3"):
    st.markdown("<h2>RAW MATERIAL SITREP: MEDICAL DEVICE IMPACT</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='mono-text' style='color:#94a3b8; font-size:12px;'>"
        "TRACKING BRENT CRUDE PASS-THROUGH TO PLASTICS, METALS, AND FREIGHT</p>",
        unsafe_allow_html=True,
    )

    alum = data.get("alum_1y", pd.DataFrame())
    cop = data.get("copper_1y", pd.DataFrame())
    plas = data.get("plastic_proxy_1y", pd.DataFrame())

    def get_metrics(df):
        if df.empty or len(df) < 30:
            return 0, 0
        cur = df["Close"].iloc[-1]
        hist = df["Close"].iloc[-30]
        return cur, ((cur - hist) / hist) * 100

    al_cur, al_pct = get_metrics(alum)
    cp_cur, cp_pct = get_metrics(cop)
    pl_cur, pl_pct = get_metrics(plas)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"<div class='tac-panel {alert_class(pl_pct)}'>"
            f"<div class='panel-title'>PETROCHEMICALS / PLASTICS [LIVE]</div>"
            f"<div class='panel-value'>${pl_cur:.2f} "
            f"<span style='font-size:14px; color:{var_color(pl_pct)}'>[{pl_pct:+.1f}% 30D]</span></div>"
            f"<div class='mono-text' style='font-size:10px; color:#64748b; margin-top:8px;'>"
            f"PP, PA6 NYLON, PE RESIN PROXY</div></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"<div class='tac-panel {alert_class(al_pct)}'>"
            f"<div class='panel-title'>ALUMINUM FUTURES (ALI=F) [LIVE]</div>"
            f"<div class='panel-value'>${al_cur:.2f} "
            f"<span style='font-size:14px; color:{var_color(al_pct)}'>[{al_pct:+.1f}% 30D]</span></div>"
            f"<div class='mono-text' style='font-size:10px; color:#64748b; margin-top:8px;'>"
            f"KNEE BRACE HINGES, WALKER STRUTS</div></div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"<div class='tac-panel {alert_class(cp_pct)}'>"
            f"<div class='panel-title'>COPPER FUTURES (HG=F) [LIVE]</div>"
            f"<div class='panel-value'>${cp_cur:.4f} "
            f"<span style='font-size:14px; color:{var_color(cp_pct)}'>[{cp_pct:+.1f}% 30D]</span></div>"
            f"<div class='mono-text' style='font-size:10px; color:#64748b; margin-top:8px;'>"
            f"ELECTRICAL COMPONENTS, MOTOR WINDINGS</div></div>",
            unsafe_allow_html=True,
        )

    # --- Correlation chart ---
    st.markdown(
        "<br><div class='panel-title'>90-DAY PRICE CORRELATION (INDEXED BASE 100)</div>",
        unsafe_allow_html=True,
    )

    if not plas.empty and not alum.empty and not brent.empty:
        natgas = data.get("natgas_1y", pd.DataFrame())
        merged = pd.DataFrame(
            {
                "Brent": brent["Close"].tail(90),
                "Plastics": plas["Close"].tail(90),
                "Aluminum": alum["Close"].tail(90),
            }
        ).dropna()
        if not natgas.empty:
            merged["NatGas"] = natgas["Close"].tail(90)
            merged = merged.dropna()

        merged_norm = (merged / merged.iloc[0]) * 100

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=merged_norm.index, y=merged_norm["Brent"],
            name="Brent Crude", line=dict(color="#06b6d4", width=2),
        ))
        fig.add_trace(go.Scatter(
            x=merged_norm.index, y=merged_norm["Plastics"],
            name="Plastic Proxy (DOW)", line=dict(color="#f59e0b", width=2),
        ))
        fig.add_trace(go.Scatter(
            x=merged_norm.index, y=merged_norm["Aluminum"],
            name="Aluminum", line=dict(color="#e2e8f0", width=2),
        ))
        if "NatGas" in merged_norm.columns:
            fig.add_trace(go.Scatter(
                x=merged_norm.index, y=merged_norm["NatGas"],
                name="Natural Gas", line=dict(color="#10b981", width=1.5, dash="dash"),
            ))

        # Calculate and display correlation coefficients
        corr_plas = merged["Brent"].corr(merged["Plastics"])
        corr_alum = merged["Brent"].corr(merged["Aluminum"])

        fig.update_layout(
            **CHART_THEME, height=400, yaxis_title="INDEXED PRICE (BASE 100)",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Correlation readout
        st.markdown(
            f"<div class='tac-panel' style='padding:10px;'>"
            f"<div class='panel-title'>90-DAY PEARSON CORRELATION WITH BRENT</div>"
            f"<span class='mono-text' style='color:#f59e0b; font-size:12px; margin-right:30px;'>"
            f"PLASTICS: {corr_plas:.3f}</span>"
            f"<span class='mono-text' style='color:#e2e8f0; font-size:12px;'>"
            f"ALUMINUM: {corr_alum:.3f}</span></div>",
            unsafe_allow_html=True,
        )

    # --- AI Supply Chain Briefing ---
    st.markdown("---")
    ai_available = get_anthropic_client() is not None

    if ai_available:
        if st.button("GENERATE AI SUPPLY CHAIN ANALYSIS", type="primary"):
            with st.spinner("OVERWATCH AI analyzing supply chain data..."):
                briefing = generate_supply_chain_briefing(
                    current_bz, pl_cur, pl_pct, al_cur, al_pct, cp_cur, cp_pct
                )
                if briefing:
                    st.markdown(
                        f"<div class='tac-panel'><div class='panel-title'>AI SUPPLY CHAIN INTELLIGENCE</div>"
                        f"<div class='ai-briefing'>{briefing}</div></div>",
                        unsafe_allow_html=True,
                    )
    else:
        st.markdown(
            "<div class='tac-panel alert-warn'>"
            "<div class='panel-title'>SUPPLY CHAIN INTELLIGENCE NOTE [STATIC]</div>"
            "<div class='mono-text' style='font-size:12px; color:#e2e8f0; line-height: 1.6;'>"
            "Petrochemical cracking margins track Brent with a 30-45 day lag. "
            "Anticipate proportional cost increases in wholesale PP and PA6 resin. "
            "Recommended: Lock in supplier contracts for injection-molded components. "
            "Energy-intensive aluminum smelting is also subject to surcharges.<br><br>"
            "<span style='color:var(--amber);'>Add ANTHROPIC_API_KEY to .streamlit/secrets.toml "
            "to enable live AI-powered supply chain analysis.</span></div></div>",
            unsafe_allow_html=True,
        )


# ===========================================================================
# VIEW 4: AI TACTICAL BRIEFING
# ===========================================================================
elif menu.startswith("4"):
    st.markdown("<h2>AI TACTICAL BRIEFING</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='mono-text' style='color:#94a3b8; font-size:12px;'>"
        "ANTHROPIC CLAUDE + LIVE WEB SEARCH | SYNTHESIZED INTELLIGENCE REPORT</p>",
        unsafe_allow_html=True,
    )

    ai_available = get_anthropic_client() is not None

    if not ai_available:
        st.markdown(
            "<div class='tac-panel alert-warn'>"
            "<div class='panel-title'>COMMS OFFLINE</div>"
            "<div class='mono-text' style='font-size:13px; color:var(--amber); line-height:1.8;'>"
            "Anthropic API key not configured.<br><br>"
            "To enable AI tactical briefings:<br>"
            "1. Create .streamlit/secrets.toml<br>"
            "2. Add: ANTHROPIC_API_KEY = \"sk-ant-...\"<br>"
            "3. Restart the dashboard<br><br>"
            "The AI module uses Claude with web search to pull live news on Brent crude, "
            "OPEC decisions, Hormuz tensions, and supply chain impacts -- then synthesizes "
            "a structured intelligence report contextualized with your live market data."
            "</div></div>",
            unsafe_allow_html=True,
        )
    else:
        # Context cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f"<div class='tac-panel'><div class='panel-title'>BRENT (INPUT)</div>"
                f"<div class='panel-value' style='font-size:22px;'>${current_bz:.2f}</div></div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"<div class='tac-panel'><div class='panel-title'>REGIME (INPUT)</div>"
                f"<div class='panel-value' style='font-size:16px; margin-top:6px;'>{regime}</div></div>",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"<div class='tac-panel'><div class='panel-title'>OVX (INPUT)</div>"
                f"<div class='panel-value' style='font-size:22px;'>{ovx_val:.1f}</div></div>",
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f"<div class='tac-panel'><div class='panel-title'>EQUILIBRIUM</div>"
                f"<div class='panel-value' style='font-size:22px;'>${eq_override:.2f}</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("GENERATE TACTICAL BRIEFING", type="primary"):
            with st.spinner("OVERWATCH AI conducting multi-source intelligence sweep..."):
                mc_json = json.dumps(mc_res) if mc_res else None
                briefing = generate_tactical_briefing(
                    current_bz, bz_change, spread, regime, mc_json, eq_override, ovx_val
                )
                if briefing:
                    st.markdown(
                        f"<div class='tac-panel'>"
                        f"<div class='panel-title'>CLASSIFIED: OVERWATCH TACTICAL BRIEFING | "
                        f"{datetime.now().strftime('%d %b %Y %H%MZ').upper()}</div>"
                        f"<div class='ai-briefing'>{briefing}</div></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.error("Briefing generation failed. Check API key and connectivity.")

        st.markdown(
            "<div class='tac-panel' style='margin-top:20px; padding:10px;'>"
            "<div class='panel-title'>AI MODULE INFO</div>"
            "<div class='mono-text' style='font-size:10px; color:#64748b; line-height:1.6;'>"
            "MODEL: CLAUDE SONNET 4 (claude-sonnet-4-20250514)<br>"
            "TOOLS: WEB SEARCH (LIVE)<br>"
            "INPUTS: LIVE MARKET DATA + MC MODEL OUTPUT + FUNDAMENTAL EQUILIBRIUM<br>"
            "CACHE: 15 MIN TTL (SAME INPUTS = CACHED RESPONSE)<br>"
            "SCOPE: BRENT CRUDE, OPEC+, HORMUZ, INVENTORIES, PETROCHEMICALS, FREIGHT"
            "</div></div>",
            unsafe_allow_html=True,
        )
