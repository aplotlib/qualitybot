#!/usr/bin/env python3
"""
OVERWATCH: TACTICAL COMMODITY DASHBOARD
===========================================
Primary Focus: Brent Crude, Hormuz Theater, Med-Dev Supply Chain Impacts
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import warnings

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# CONFIG & AUTO-REFRESH
# ---------------------------------------------------------------------------
st.set_page_config(page_title="OVERWATCH SITREP", page_icon="📡", layout="wide", initial_sidebar_state="expanded")

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=120_000, limit=None, key="data_refresh")
except ImportError:
    pass

TARGET_PRICE = 94.50
TARGET_DATE = datetime(2026, 6, 15)
CACHE_TTL = 120

# ---------------------------------------------------------------------------
# UI HELPERS (Defined early to prevent NameError)
# ---------------------------------------------------------------------------
def var_color(val):
    """Returns CSS color variable based on positive/negative float value."""
    try:
        val = float(val)
        return "var(--green)" if val > 0 else "var(--red)" if val < 0 else "#94a3b8"
    except (ValueError, TypeError):
        return "#94a3b8"

# ---------------------------------------------------------------------------
# TACTICAL UI/UX CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@300;400;600;800&display=swap');

:root {
    --bg-base: #020617; /* Deep Slate */
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
p, span, div { font-family: var(--sans); }
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

/* TERMINAL FEED */
.terminal-feed { font-family: var(--mono); font-size: 12px; color: #cbd5e1; height: 300px; overflow-y: auto; padding: 10px; background: rgba(0,0,0,0.5); border: 1px solid #1e293b; }
.term-line { border-bottom: 1px dashed #1e293b; padding: 6px 0; }
.term-date { color: var(--cyan); margin-right: 10px; }
.term-crit { color: var(--red); }

/* HIDE STREAMLIT ELEMENTS */
#MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# DATA ENGINE
# ---------------------------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_stratcom_data():
    """Fetches Energy, Metals, and Petrochemical Proxies."""
    result = {"error": None}
    try:
        # Core Energy
        tickers = yf.Tickers("BZ=F CL=F")
        result["brent_1y"] = tickers.tickers["BZ=F"].history(period="1y", interval="1d")
        result["brent_1d"] = tickers.tickers["BZ=F"].history(period="1d", interval="1m")
        result["wti_1d"] = tickers.tickers["CL=F"].history(period="1d", interval="1m")
        
        # Med-Dev Commodities (Plastics/Metals)
        # ALI=F (Aluminum), HG=F (Copper), DOW (Petrochemical/Plastics Proxy for PP/PE)
        mat_tickers = yf.Tickers("ALI=F HG=F DOW")
        result["alum_1y"] = mat_tickers.tickers["ALI=F"].history(period="1y", interval="1d")
        result["copper_1y"] = mat_tickers.tickers["HG=F"].history(period="1y", interval="1d")
        result["plastic_proxy_1y"] = mat_tickers.tickers["DOW"].history(period="1y", interval="1d")
        
        result["fetch_time"] = datetime.now()
    except Exception as e:
        result["error"] = str(e)
    return result

# ---------------------------------------------------------------------------
# PREDICTIVE ANALYTICS (JUMP-DIFFUSION MONTE CARLO)
# ---------------------------------------------------------------------------
def tactical_monte_carlo(df, current_price, target_price, days_to_target, n_sims=50_000):
    if df.empty or len(df) < 60: return None
    log_ret = np.log(df["Close"] / df["Close"].shift(1)).dropna()
    
    # War Regime Adjustments (Higher Volatility, Upward Drift Bias)
    mu_base = log_ret.mean()
    sig_base = log_ret.std()
    mu_war = mu_base + 0.0015  # War premium drift
    sig_war = sig_base * 2.2   # 120% increase in volatility
    
    np.random.seed(42)
    prices = np.zeros((n_sims, max(1, days_to_target)))
    prices[:, 0] = current_price
    
    for t in range(1, max(1, days_to_target)):
        # 1% daily chance of severe escalation jump
        jump = np.where(np.random.random(n_sims) < 0.01, np.random.normal(0.05, 0.02, n_sims), 0)
        shock = np.random.normal(mu_war, sig_war, n_sims)
        prices[:, t] = prices[:, t - 1] * np.exp(shock + jump)
        
    finals = prices[:, -1]
    
    return {
        "p_hit_target": round(np.mean(finals >= target_price) * 100, 1),
        "p_above_120": round(np.mean(finals >= 120) * 100, 1),
        "median": round(np.percentile(finals, 50), 2),
        "p95": round(np.percentile(finals, 95), 2),
        "p5": round(np.percentile(finals, 5), 2),
        "sims": n_sims
    }, prices

# ---------------------------------------------------------------------------
# CHARTING FACTORY (DARK TACTICAL THEME)
# ---------------------------------------------------------------------------
CHART_THEME = dict(
    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Share Tech Mono", color="#94a3b8"), margin=dict(l=40, r=20, t=30, b=30),
    xaxis=dict(gridcolor="rgba(30, 41, 59, 0.5)", zeroline=False),
    yaxis=dict(gridcolor="rgba(30, 41, 59, 0.5)", zeroline=False)
)

def build_hud_chart(df, title, color, fill=True):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"], mode="lines", line=dict(color=color, width=1.5),
        fill="tozeroy" if fill else "none", fillcolor=color.replace('rgb', 'rgba').replace(')', ', 0.1)') if fill else None
    ))
    fig.update_layout(**CHART_THEME, height=250, title=dict(text=title, font=dict(size=14, color="#fff")))
    return fig

# ---------------------------------------------------------------------------
# MAIN APP ROUTING
# ---------------------------------------------------------------------------
data = fetch_stratcom_data()

# Side Navigation
with st.sidebar:
    st.markdown("<h2 style='color:var(--cyan); margin-bottom: 0;'>OVERWATCH</h2>", unsafe_allow_html=True)
    st.markdown("<p class='mono-text' style='color:#64748b; font-size: 10px;'>GLOBAL THREAT & COMMODITY DIRECTORATE</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    menu = st.radio("OPERATIONAL VIEWS", ["1. GLOBAL ENERGY (BRENT)", "2. HORMUZ THEATER", "3. MED-DEV SUPPLY CHAIN"])
    
    st.markdown("---")
    st.markdown("<div class='tac-panel alert-critical'><div class='panel-title'>THREAT LEVEL</div><div class='panel-value' style='font-size: 20px;'>ELEVATED (2)</div></div>", unsafe_allow_html=True)
    
    if st.button("EXECUTE REFRESH [F5]"):
        st.cache_data.clear()
        st.rerun()

# Pre-compute core variables
brent = data.get("brent_1y", pd.DataFrame())
brent_1d = data.get("brent_1d", pd.DataFrame())
current_bz = brent_1d["Close"].iloc[-1] if not brent_1d.empty else (brent["Close"].iloc[-1] if not brent.empty else 0)
bz_change = current_bz - brent["Close"].iloc[-2] if len(brent) > 1 else 0

# ===========================================================================
# VIEW 1: GLOBAL ENERGY (BRENT CRUDE)
# ===========================================================================
if menu.startswith("1"):
    st.markdown("<h2>GLOBAL ENERGY TRACKER: BZ=F</h2>", unsafe_allow_html=True)
    
    # Top HUD
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='tac-panel'><div class='panel-title'>BRENT SPOT (USD)</div><div class='panel-value'>${current_bz:.2f} <span style='font-size:14px; color:{var_color(bz_change)}'>[{bz_change:+.2f}]</span></div></div>", unsafe_allow_html=True)
    with c2:
        wti = data.get("wti_1d", pd.DataFrame())
        cur_wti = wti["Close"].iloc[-1] if not wti.empty else 0
        st.markdown(f"<div class='tac-panel'><div class='panel-title'>WTI SPOT (USD)</div><div class='panel-value'>${cur_wti:.2f}</div></div>", unsafe_allow_html=True)
    with c3:
        spread = current_bz - cur_wti
        st.markdown(f"<div class='tac-panel'><div class='panel-title'>BZ/WTI SPREAD</div><div class='panel-value'>${spread:.2f}</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='tac-panel'><div class='panel-title'>TARGET: {TARGET_DATE.strftime('%d%b%y').upper()}</div><div class='panel-value' style='color:var(--amber);'>${TARGET_PRICE:.2f}</div></div>", unsafe_allow_html=True)

    # Main Chart & Prediction
    c_chart, c_pred = st.columns([7, 3])
    with c_chart:
        if not brent.empty:
            fig = build_hud_chart(brent.tail(180), "6-MONTH BRENT PRICE ACTION", "rgb(6, 182, 212)")
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
            
    with c_pred:
        days_out = max(1, (TARGET_DATE - datetime.now()).days)
        mc_res, _ = tactical_monte_carlo(brent, current_bz, TARGET_PRICE, days_out)
        
        if mc_res:
            st.markdown("<div class='tac-panel' style='height: 450px;'>", unsafe_allow_html=True)
            st.markdown("<div class='panel-title'>STOCHASTIC REGIME-SWITCHING MODEL</div>", unsafe_allow_html=True)
            st.markdown("<p class='mono-text' style='font-size:10px; color:#64748b;'>SIMULATIONS: 50,000 | JUMP-DIFFUSION ENABLED</p><hr style='border-color:#1e293b'>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='margin-bottom: 20px;'>
                <div class='mono-text' style='color:#94a3b8; font-size:12px;'>P(TARGET >= ${TARGET_PRICE})</div>
                <div class='mono-text' style='color:var(--cyan); font-size:24px;'>{mc_res['p_hit_target']}%</div>
            </div>
            <div style='margin-bottom: 20px;'>
                <div class='mono-text' style='color:#94a3b8; font-size:12px;'>MEDIAN PROJECTION</div>
                <div class='mono-text' style='color:#fff; font-size:24px;'>${mc_res['median']}</div>
            </div>
            <div style='margin-bottom: 20px;'>
                <div class='mono-text' style='color:#94a3b8; font-size:12px;'>P(EXTREME SHOCK >= $120)</div>
                <div class='mono-text' style='color:var(--red); font-size:24px;'>{mc_res['p_above_120']}%</div>
            </div>
            <div style='margin-top: auto; padding-top:10px; border-top: 1px solid #1e293b;'>
                <div class='mono-text' style='font-size:11px; color:#94a3b8;'>90% CONFIDENCE INTERVAL</div>
                <div class='mono-text' style='color:var(--amber); font-size:14px;'>[{mc_res['p5']} - {mc_res['p95']}]</div>
            </div>
            </div>
            """, unsafe_allow_html=True)


# ===========================================================================
# VIEW 2: HORMUZ THEATER
# ===========================================================================
elif menu.startswith("2"):
    st.markdown("<h2>THEATER SITREP: STRAIT OF HORMUZ</h2>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.markdown("<div class='tac-panel alert-critical'><div class='panel-title'>BLOCKADE STATUS</div><div class='panel-value'>ACTIVE</div></div>", unsafe_allow_html=True)
    c2.markdown("<div class='tac-panel'><div class='panel-title'>EST. VESSEL BACKLOG</div><div class='panel-value'>~400 HULLS</div></div>", unsafe_allow_html=True)
    c3.markdown("<div class='tac-panel alert-critical'><div class='panel-title'>GLOBAL FLOW DISRUPTION</div><div class='panel-value'>95%</div></div>", unsafe_allow_html=True)
    
    c_feed, c_map = st.columns([2, 1])
    
    with c_feed:
        st.markdown("<div class='panel-title'>SIGINT TIMELINE [CLASSIFIED OVERVIEW]</div>", unsafe_allow_html=True)
        # Terminal-style output
        feed_html = """
        <div class="terminal-feed">
            <div class="term-line"><span class="term-date">20MAR26 0800Z</span> <span class="term-crit">[CRITICAL]</span> BRENT SURPASSES $107. ONLY 21 TRANSITS LOGGED SINCE LATE FEB.</div>
            <div class="term-line"><span class="term-date">19MAR26 1430Z</span> <span class="term-crit">[CRITICAL]</span> ISRAELI STRIKE CONFIRMED ON SOUTH PARS. IRAN RETALIATES AT RAS LAFFAN.</div>
            <div class="term-line"><span class="term-date">18MAR26 0915Z</span> [INFO] TURKISH AND INDIAN SHIPS GRANTED SAFE PASSAGE EXCEPTION.</div>
            <div class="term-line"><span class="term-date">17MAR26 1100Z</span> <span class="term-crit">[CRITICAL]</span> SUPREME LEADER MOJTABA KHAMENEI REITERATES TOTAL BLOCKADE ON WESTERN HULLS.</div>
            <div class="term-line"><span class="term-date">14MAR26 1645Z</span> <span class="term-crit">[CRITICAL]</span> 3+ MB/D GULF REFINING CAPACITY FORCED OFFLINE DUE TO UAE SHAH GAS FIELD STRIKE.</div>
            <div class="term-line"><span class="term-date">11MAR26 1200Z</span> [INFO] IEA AUTHORIZES EMERGENCY RELEASE OF 400M BARRELS.</div>
            <div class="term-line"><span class="term-date">04MAR26 0000Z</span> <span class="term-crit">[CRITICAL]</span> IRAN FORMALLY DECLARES STRAIT OF HORMUZ CLOSED.</div>
        </div>
        """
        st.markdown(feed_html, unsafe_allow_html=True)

    with c_map:
        st.markdown("""
        <div class='tac-panel' style='height: 330px; display:flex; flex-direction:column; justify-content:center; align-items:center;'>
            <div class='mono-text' style='color:var(--red); font-size:40px; margin-bottom:10px;'>⚠</div>
            <div class='mono-text' style='color:#fff; text-align:center;'>OVERWATCH MARITIME MAP<br>CURRENTLY UNAVAILABLE</div>
            <div class='mono-text' style='color:#64748b; font-size:10px; margin-top:20px;'>AWAITING SATELLITE TELEMETRY LINK</div>
        </div>
        """, unsafe_allow_html=True)


# ===========================================================================
# VIEW 3: MED-DEV SUPPLY CHAIN (RAW MATERIALS)
# ===========================================================================
elif menu.startswith("3"):
    st.markdown("<h2>RAW MATERIAL SITREP: MEDICAL DEVICE IMPACT</h2>", unsafe_allow_html=True)
    st.markdown("<p class='mono-text' style='color:#94a3b8; font-size:12px;'>TRACKING BRENT CRUDE SPIKE PASS-THROUGH TO PLASTICS & STRUCTURAL METALS</p>", unsafe_allow_html=True)
    
    alum = data.get("alum_1y", pd.DataFrame())
    cop = data.get("copper_1y", pd.DataFrame())
    plas = data.get("plastic_proxy_1y", pd.DataFrame())
    
    # Get latest prices and 30-day changes
    def get_metrics(df):
        if df.empty or len(df) < 30: return 0, 0
        cur = df["Close"].iloc[-1]
        hist = df["Close"].iloc[-30]
        return cur, ((cur - hist) / hist) * 100
        
    al_cur, al_pct = get_metrics(alum)
    cp_cur, cp_pct = get_metrics(cop)
    pl_cur, pl_pct = get_metrics(plas)
    
    # HUD Metrics
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class='tac-panel'>
            <div class='panel-title'>PETROCHEMICALS / PLASTICS PROXY</div>
            <div class='panel-value'>${pl_cur:.2f} <span style='font-size:14px; color:{var_color(pl_pct)}'>[{pl_pct:+.1f}% 30D]</span></div>
            <div class='mono-text' style='font-size:10px; color:#64748b; margin-top:8px;'>CRITICAL FOR: WALKER BOOT SHELLS (PP/PE), COMPRESSION PLASTICS</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='tac-panel'>
            <div class='panel-title'>ALUMINUM FUTURES (ALI=F)</div>
            <div class='panel-value'>${al_cur:.2f} <span style='font-size:14px; color:{var_color(al_pct)}'>[{al_pct:+.1f}% 30D]</span></div>
            <div class='mono-text' style='font-size:10px; color:#64748b; margin-top:8px;'>CRITICAL FOR: KNEE BRACE HINGES, WALKER BOOT STRUTS</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class='tac-panel'>
            <div class='panel-title'>COPPER FUTURES (HG=F)</div>
            <div class='panel-value'>${cp_cur:.4f} <span style='font-size:14px; color:{var_color(cp_pct)}'>[{cp_pct:+.1f}% 30D]</span></div>
            <div class='mono-text' style='font-size:10px; color:#64748b; margin-top:8px;'>MACRO INDUSTRIAL INDEX</div>
        </div>""", unsafe_allow_html=True)

    # Correlation Analysis
    st.markdown("<br><div class='panel-title'>90-DAY PRICE CORRELATION (MATERIAL VS. BRENT CRUDE)</div>", unsafe_allow_html=True)
    
    if not plas.empty and not alum.empty and not brent.empty:
        # Align indexes for charting
        merged = pd.DataFrame({
            "Brent": brent["Close"].tail(90),
            "Plastics": plas["Close"].tail(90),
            "Aluminum": alum["Close"].tail(90)
        }).dropna()
        
        # Normalize to base 100 for comparison
        merged_norm = (merged / merged.iloc[0]) * 100
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=merged_norm.index, y=merged_norm["Brent"], name="Brent Crude", line=dict(color="#06b6d4", width=2)))
        fig.add_trace(go.Scatter(x=merged_norm.index, y=merged_norm["Plastics"], name="Plastic Proxy", line=dict(color="#f59e0b", width=2)))
        fig.add_trace(go.Scatter(x=merged_norm.index, y=merged_norm["Aluminum"], name="Aluminum", line=dict(color="#e2e8f0", width=2)))
        
        fig.update_layout(**CHART_THEME, height=400, yaxis_title="INDEXED PRICE (BASE 100)")
        st.plotly_chart(fig, use_container_width=True)
        
    st.markdown("""
    <div class='tac-panel alert-critical'>
        <div class='panel-title'>SUPPLY CHAIN INTELLIGENCE NOTE</div>
        <div class='mono-text' style='font-size:12px; color:#e2e8f0; line-height: 1.6;'>
        Petrochemical cracking margins are severely compressed due to the Brent spike. Anticipate an 8-15% cost increase in wholesale Polypropylene resin within 45 days. Recommended action: Lock in supplier contracts for injection-molded components immediately to protect margins on high-volume plastic lines. Energy-intensive aluminum smelting is also passing surcharges down the supply chain.
        </div>
    </div>
    """, unsafe_allow_html=True)
