#!/usr/bin/env python3
"""
OVERWATCH: TACTICAL COMMODITY DASHBOARD
===========================================
Primary Focus: Brent Crude, Hormuz Theater, Med-Dev Supply Chain Impacts
Includes Live AIS Maritime, ADS-B Flight Tracking, and Jump-Diffusion MC
"""

import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
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

CACHE_TTL = 120

# ---------------------------------------------------------------------------
# UI HELPERS 
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

/* STREAMLIT OVERRIDES */
#MainMenu, footer, header {visibility: hidden;}
div[data-baseweb="input"] { background-color: rgba(15, 23, 42, 0.8) !important; border: 1px solid var(--cyan) !important; color: #fff !important; }
div[data-baseweb="select"] > div { background-color: rgba(15, 23, 42, 0.8) !important; border: 1px solid var(--cyan) !important; color: #fff !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# DATA ENGINE
# ---------------------------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_stratcom_data():
    """Fetches Live Energy, Metals, and Petrochemical Proxies."""
    result = {"error": None}
    try:
        tickers = yf.Tickers("BZ=F CL=F")
        result["brent_1y"] = tickers.tickers["BZ=F"].history(period="1y", interval="1d")
        result["brent_1d"] = tickers.tickers["BZ=F"].history(period="1d", interval="1m")
        result["wti_1d"] = tickers.tickers["CL=F"].history(period="1d", interval="1m")
        
        mat_tickers = yf.Tickers("ALI=F HG=F DOW")
        result["alum_1y"] = mat_tickers.tickers["ALI=F"].history(period="1y", interval="1d")
        result["copper_1y"] = mat_tickers.tickers["HG=F"].history(period="1y", interval="1d")
        result["plastic_proxy_1y"] = mat_tickers.tickers["DOW"].history(period="1y", interval="1d")
        
        result["fetch_time"] = datetime.now()
    except Exception as e:
        result["error"] = str(e)
    return result

# ---------------------------------------------------------------------------
# JUMP-DIFFUSION MONTE CARLO ENGINE
# ---------------------------------------------------------------------------
def tactical_jump_diffusion_mc(df, current_price, target_price, days_to_target, regime, n_sims=30_000):
    """
    Advanced Stochastic Regime-Switching Jump-Diffusion Model.
    Simulates price paths using Geometric Brownian Motion + Poisson Jumps.
    """
    if df.empty or len(df) < 60: return None, None
    log_ret = np.log(df["Close"] / df["Close"].shift(1)).dropna()
    
    mu_base = log_ret.mean()
    sig_base = log_ret.std()
    
    # REGIME SWITCHING LOGIC
    if regime == "NORMAL (HISTORICAL)":
        mu, sig = mu_base, sig_base
        jump_prob, jump_mu, jump_sig = 0.001, 0.02, 0.01
    elif regime == "BLOCKADE (ACTIVE)":
        mu, sig = mu_base + 0.001, sig_base * 1.8
        jump_prob, jump_mu, jump_sig = 0.015, 0.05, 0.03 # 1.5% chance of 5% spike
    else: # REGIONAL ESCALATION
        mu, sig = mu_base + 0.002, sig_base * 2.5
        jump_prob, jump_mu, jump_sig = 0.04, 0.10, 0.06 # 4% chance of 10% spike
    
    np.random.seed(42)
    n_days = max(1, days_to_target)
    prices = np.zeros((n_sims, n_days))
    prices[:, 0] = current_price
    
    for t in range(1, n_days):
        # Continuous diffusion (Brownian motion)
        shock = np.random.normal(mu, sig, n_sims)
        # Discrete jumps (Poisson process)
        jumps = np.where(np.random.random(n_sims) < jump_prob, np.random.normal(jump_mu, jump_sig, n_sims), 0)
        
        prices[:, t] = prices[:, t - 1] * np.exp(shock + jumps)
        
    finals = prices[:, -1]
    
    stats = {
        "p_hit_target": round(np.mean(finals >= target_price) * 100, 1),
        "p_above_120": round(np.mean(finals >= 120) * 100, 1),
        "median": round(np.percentile(finals, 50), 2),
        "mean": round(np.mean(finals), 2),
        "p95": round(np.percentile(finals, 95), 2),
        "p5": round(np.percentile(finals, 5), 2),
        "sims": n_sims,
        "regime": regime
    }
    return stats, prices

# ---------------------------------------------------------------------------
# CHARTING FACTORY
# ---------------------------------------------------------------------------
CHART_THEME = dict(
    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Share Tech Mono", color="#94a3b8"), margin=dict(l=40, r=20, t=30, b=30),
    xaxis=dict(gridcolor="rgba(30, 41, 59, 0.5)", zeroline=False),
    yaxis=dict(gridcolor="rgba(30, 41, 59, 0.5)", zeroline=False)
)

def build_fan_chart(historical_df, paths, start_price, days_to_target):
    """Builds a predictive cone of uncertainty mapping future dates."""
    hist = historical_df.tail(60)
    
    # Create future date index
    future_dates = [datetime.now() + timedelta(days=i) for i in range(days_to_target)]
    
    # Calculate percentiles across all simulations
    p5 = np.percentile(paths, 5, axis=0)
    p50 = np.percentile(paths, 50, axis=0)
    p95 = np.percentile(paths, 95, axis=0)
    
    fig = go.Figure()
    
    # Historical Trace
    fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name="Historical", line=dict(color="#94a3b8", width=2)))
    
    # Predictive Cone (P5 to P95)
    fig.add_trace(go.Scatter(x=future_dates, y=p95, mode="lines", line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(
        x=future_dates, y=p5, mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(6, 182, 212, 0.15)", name="90% Confidence Interval"
    ))
    
    # Median Prediction
    fig.add_trace(go.Scatter(x=future_dates, y=p50, mode="lines", name="Median Path", line=dict(color="#06b6d4", width=2, dash="dot")))
    
    fig.update_layout(**CHART_THEME, height=350, title=dict(text="PRICE TRAJECTORY: CONE OF UNCERTAINTY", font=dict(size=14, color="#fff")), showlegend=True, legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    return fig

# ---------------------------------------------------------------------------
# MAIN APP ROUTING
# ---------------------------------------------------------------------------
data = fetch_stratcom_data()

with st.sidebar:
    st.markdown("<h2 style='color:var(--cyan); margin-bottom: 0;'>OVERWATCH</h2>", unsafe_allow_html=True)
    st.markdown("<p class='mono-text' style='color:#64748b; font-size: 10px;'>GLOBAL THREAT & COMMODITY DIRECTORATE</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    menu = st.radio("OPERATIONAL VIEWS", ["1. GLOBAL ENERGY (BRENT)", "2. HORMUZ THEATER [LIVE RECON]", "3. MED-DEV SUPPLY CHAIN"])
    
    st.markdown("---")
    st.markdown("<div class='panel-title'>PREDICTIVE TARGETING</div>", unsafe_allow_html=True)
    target_date = st.date_input("ESTIMATE PRICE ON DATE:", datetime.now() + timedelta(days=90))
    target_price = st.number_input("TARGET PRICE THRESHOLD ($):", min_value=10.0, max_value=300.0, value=94.50, step=0.5)
    regime = st.selectbox("THREAT REGIME (VOL/DRIFT)", ["NORMAL (HISTORICAL)", "BLOCKADE (ACTIVE)", "REGIONAL ESCALATION"], index=1)
    
    st.markdown("---")
    st.markdown("<p class='mono-text' style='color:#94a3b8; font-size:9px;'>FINANCIALS: LIVE YFINANCE<br>MAPS: LIVE SATELLITE AIS/ADSB<br>MODEL: JUMP-DIFFUSION MONTE CARLO</p>", unsafe_allow_html=True)

    if st.button("EXECUTE REFRESH [F5]"):
        st.cache_data.clear()
        st.rerun()

brent = data.get("brent_1y", pd.DataFrame())
brent_1d = data.get("brent_1d", pd.DataFrame())
current_bz = brent_1d["Close"].iloc[-1] if not brent_1d.empty else (brent["Close"].iloc[-1] if not brent.empty else 0)
bz_change = current_bz - brent["Close"].iloc[-2] if len(brent) > 1 else 0

days_out = max(1, (target_date - datetime.now().date()).days)

# ===========================================================================
# VIEW 1: GLOBAL ENERGY
# ===========================================================================
if menu.startswith("1"):
    st.markdown("<h2>GLOBAL ENERGY TRACKER: BZ=F</h2>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='tac-panel'><div class='panel-title'>BRENT SPOT (USD) [LIVE]</div><div class='panel-value'>${current_bz:.2f} <span style='font-size:14px; color:{var_color(bz_change)}'>[{bz_change:+.2f}]</span></div></div>", unsafe_allow_html=True)
    with c2:
        wti = data.get("wti_1d", pd.DataFrame())
        cur_wti = wti["Close"].iloc[-1] if not wti.empty else 0
        st.markdown(f"<div class='tac-panel'><div class='panel-title'>WTI SPOT (USD) [LIVE]</div><div class='panel-value'>${cur_wti:.2f}</div></div>", unsafe_allow_html=True)
    with c3:
        spread = current_bz - cur_wti
        st.markdown(f"<div class='tac-panel'><div class='panel-title'>BZ/WTI SPREAD</div><div class='panel-value'>${spread:.2f}</div></div>", unsafe_allow_html=True)
    with c4:
        panel_class = "alert-warn" if regime == "BLOCKADE (ACTIVE)" else "alert-critical" if regime == "REGIONAL ESCALATION" else ""
        st.markdown(f"<div class='tac-panel {panel_class}'><div class='panel-title'>THREAT REGIME</div><div class='panel-value' style='font-size:18px; margin-top:8px;'>{regime.split()[0]}</div></div>", unsafe_allow_html=True)

    c_chart, c_pred = st.columns([6, 4])
    
    mc_res, paths = tactical_jump_diffusion_mc(brent, current_bz, target_price, days_out, regime)
    
    with c_chart:
        if not brent.empty and paths is not None:
            fig = build_fan_chart(brent, paths, current_bz, days_out)
            st.plotly_chart(fig, use_container_width=True)
            
    with c_pred:
        if mc_res:
            st.markdown("<div class='tac-panel' style='height: 350px;'>", unsafe_allow_html=True)
            st.markdown("<div class='panel-title'>JUMP-DIFFUSION PROJECTION</div>", unsafe_allow_html=True)
            st.markdown(f"<p class='mono-text' style='font-size:10px; color:#64748b;'>TARGET DATE: {target_date.strftime('%d %b %Y').upper()} | SIMS: 30,000</p><hr style='border-color:#1e293b'>", unsafe_allow_html=True)
            
            p1, p2 = st.columns(2)
            with p1:
                st.markdown(f"""
                <div style='margin-bottom: 15px;'>
                    <div class='mono-text' style='color:#94a3b8; font-size:11px;'>P(PRICE >= ${target_price:.2f})</div>
                    <div class='mono-text' style='color:var(--cyan); font-size:22px;'>{mc_res['p_hit_target']}%</div>
                </div>
                <div style='margin-bottom: 15px;'>
                    <div class='mono-text' style='color:#94a3b8; font-size:11px;'>P(SHOCK >= $120)</div>
                    <div class='mono-text' style='color:var(--red); font-size:22px;'>{mc_res['p_above_120']}%</div>
                </div>
                """, unsafe_allow_html=True)
            with p2:
                st.markdown(f"""
                <div style='margin-bottom: 15px;'>
                    <div class='mono-text' style='color:#94a3b8; font-size:11px;'>EST. MEDIAN PRICE</div>
                    <div class='mono-text' style='color:#fff; font-size:22px;'>${mc_res['median']}</div>
                </div>
                <div style='margin-bottom: 15px;'>
                    <div class='mono-text' style='color:#94a3b8; font-size:11px;'>EST. MEAN PRICE</div>
                    <div class='mono-text' style='color:#fff; font-size:22px;'>${mc_res['mean']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='margin-top: auto; padding-top:10px; border-top: 1px solid #1e293b;'>
                <div class='mono-text' style='font-size:11px; color:#94a3b8;'>90% CONFIDENCE INTERVAL (TARGET DATE)</div>
                <div class='mono-text' style='color:var(--amber); font-size:14px;'>[{mc_res['p5']} - {mc_res['p95']}]</div>
            </div>
            </div>
            """, unsafe_allow_html=True)


# ===========================================================================
# VIEW 2: HORMUZ THEATER [LIVE RECON]
# ===========================================================================
elif menu.startswith("2"):
    st.markdown("<h2>THEATER SITREP: STRAIT OF HORMUZ</h2>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.markdown("<div class='tac-panel alert-critical'><div class='panel-title'>BLOCKADE STATUS [SIMULATED]</div><div class='panel-value'>ACTIVE</div></div>", unsafe_allow_html=True)
    c2.markdown("<div class='tac-panel'><div class='panel-title'>CHOKEPOINT</div><div class='panel-value'>26.4° N, 56.2° E</div></div>", unsafe_allow_html=True)
    c3.markdown("<div class='tac-panel alert-critical'><div class='panel-title'>GLOBAL FLOW DISRUPTION [SIMULATED]</div><div class='panel-value'>95%</div></div>", unsafe_allow_html=True)
    
    c_ship, c_air = st.columns(2)
    
    with c_ship:
        st.markdown("<div class='panel-title' style='color:var(--cyan);'>LIVE AIS MARITIME RADAR (STRAIT OF HORMUZ)</div>", unsafe_allow_html=True)
        marine_traffic_html = """
        <script type="text/javascript">
            width='100%'; height='450'; border='0'; shownames='false';
            latitude='26.4'; longitude='56.2'; zoom='7'; maptype='2'; trackvessel='0'; fleet='';
        </script>
        <script type="text/javascript" src="https://www.marinetraffic.com/js/embed.js"></script>
        <div style="font-family: monospace; font-size: 10px; color: #64748b; margin-top:5px; text-align: right;">DATA: MARINETRAFFIC AIS</div>
        """
        components.html(marine_traffic_html, height=480)

    with c_air:
        st.markdown("<div class='panel-title' style='color:var(--cyan);'>LIVE ADS-B FLIGHT RADAR (PERSIAN GULF)</div>", unsafe_allow_html=True)
        adsb_url = "https://globe.adsbexchange.com/?lat=26.4&lon=56.2&zoom=7&hideSidebar=1&hideButtons=1"
        components.iframe(adsb_url, height=450)
        st.markdown("<div style='font-family: monospace; font-size: 10px; color: #64748b; text-align: right;'>DATA: ADSB EXCHANGE RAW TELEMETRY</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div class='panel-title'>SIGINT TIMELINE [SIMULATED WARGAME SCENARIO]</div>", unsafe_allow_html=True)
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
    st.markdown("<p class='mono-text' style='color:#94a3b8; font-size:12px;'>TRACKING BRENT CRUDE SPIKE PASS-THROUGH TO PLASTICS & STRUCTURAL METALS</p>", unsafe_allow_html=True)
    
    alum = data.get("alum_1y", pd.DataFrame())
    cop = data.get("copper_1y", pd.DataFrame())
    plas = data.get("plastic_proxy_1y", pd.DataFrame())
    
    def get_metrics(df):
        if df.empty or len(df) < 30: return 0, 0
        cur = df["Close"].iloc[-1]
        hist = df["Close"].iloc[-30]
        return cur, ((cur - hist) / hist) * 100
        
    al_cur, al_pct = get_metrics(alum)
    cp_cur, cp_pct = get_metrics(cop)
    pl_cur, pl_pct = get_metrics(plas)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class='tac-panel'>
            <div class='panel-title'>PETROCHEMICALS / PLASTICS [LIVE]</div>
            <div class='panel-value'>${pl_cur:.2f} <span style='font-size:14px; color:{var_color(pl_pct)}'>[{pl_pct:+.1f}% 30D]</span></div>
            <div class='mono-text' style='font-size:10px; color:#64748b; margin-top:8px;'>CRITICAL FOR: WALKER BOOT SHELLS, PLASTICS</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='tac-panel'>
            <div class='panel-title'>ALUMINUM FUTURES (ALI=F) [LIVE]</div>
            <div class='panel-value'>${al_cur:.2f} <span style='font-size:14px; color:{var_color(al_pct)}'>[{al_pct:+.1f}% 30D]</span></div>
            <div class='mono-text' style='font-size:10px; color:#64748b; margin-top:8px;'>CRITICAL FOR: KNEE BRACE HINGES, STRUTS</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class='tac-panel'>
            <div class='panel-title'>COPPER FUTURES (HG=F) [LIVE]</div>
            <div class='panel-value'>${cp_cur:.4f} <span style='font-size:14px; color:{var_color(cp_pct)}'>[{cp_pct:+.1f}% 30D]</span></div>
            <div class='mono-text' style='font-size:10px; color:#64748b; margin-top:8px;'>MACRO INDUSTRIAL INDEX</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br><div class='panel-title'>90-DAY PRICE CORRELATION (MATERIAL VS. BRENT CRUDE)</div>", unsafe_allow_html=True)
    
    if not plas.empty and not alum.empty and not brent.empty:
        merged = pd.DataFrame({
            "Brent": brent["Close"].tail(90),
            "Plastics": plas["Close"].tail(90),
            "Aluminum": alum["Close"].tail(90)
        }).dropna()
        
        merged_norm = (merged / merged.iloc[0]) * 100
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=merged_norm.index, y=merged_norm["Brent"], name="Brent Crude", line=dict(color="#06b6d4", width=2)))
        fig.add_trace(go.Scatter(x=merged_norm.index, y=merged_norm["Plastics"], name="Plastic Proxy", line=dict(color="#f59e0b", width=2)))
        fig.add_trace(go.Scatter(x=merged_norm.index, y=merged_norm["Aluminum"], name="Aluminum", line=dict(color="#e2e8f0", width=2)))
        
        fig.update_layout(**CHART_THEME, height=400, yaxis_title="INDEXED PRICE (BASE 100)")
        st.plotly_chart(fig, use_container_width=True)
        
    st.markdown("""
    <div class='tac-panel alert-critical'>
        <div class='panel-title'>SUPPLY CHAIN INTELLIGENCE NOTE [SIMULATED]</div>
        <div class='mono-text' style='font-size:12px; color:#e2e8f0; line-height: 1.6;'>
        Petrochemical cracking margins are severely compressed due to the Brent spike. Anticipate an 8-15% cost increase in wholesale Polypropylene resin within 45 days. Recommended action: Lock in supplier contracts for injection-molded components immediately to protect margins on high-volume plastic lines. Energy-intensive aluminum smelting is also passing surcharges down the supply chain.
        </div>
    </div>
    """, unsafe_allow_html=True)
