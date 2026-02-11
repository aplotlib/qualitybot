import streamlit as st
import pandas as pd
from typing import List, Dict
import openai

from src.regulatory_data import (
    MARKETS,
    ISO_13485_CLAUSES,
    STANDARDS_MAP,
    GAP_ANALYSIS_ITEMS,
    REQUIREMENT_TIERS,
    FIVETEN_K_GUIDANCE,
    PDAC_HCPCS_GUIDANCE,
    get_applicable_standards,
    get_gap_stats,
    get_classification_info,
    get_tiered_requirements,
    build_system_prompt,
)
from src.standards_knowledge import (
    ALL_STANDARDS_KNOWLEDGE,
    FDA_AUDIT_CHECKLIST,
    DOCUMENT_REGISTRY,
    search_standards_knowledge,
    get_audit_checklist_for_clause,
)

# ══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="RegIntel - Medical Device Regulatory Intelligence",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ══════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Source+Serif+4:wght@400;600;700&display=swap');

.block-container { padding-top: 2rem; }
header[data-testid="stHeader"] { background: transparent; }

.top-bar {
    background: #0a1628;
    padding: 12px 24px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid #1e3a5f;
}
.top-bar .logo {
    width: 32px; height: 32px; border-radius: 6px;
    background: linear-gradient(135deg, #38bdf8, #3b82f6);
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; font-weight: 700; color: #fff;
}
.top-bar .title { color: #fff; font-weight: 700; font-size: 16px; font-family: 'Source Serif 4', Georgia, serif; }
.top-bar .subtitle { color: #475569; font-size: 12px; margin-left: 6px; }

.hero {
    background: linear-gradient(135deg, #0a1628 0%, #1a2d50 50%, #0f2040 100%);
    border-radius: 16px; padding: 32px 36px; color: #fff;
    position: relative; overflow: hidden; margin-bottom: 1.5rem;
}
.hero h2 { font-size: 24px; font-weight: 700; margin: 0; font-family: 'Source Serif 4', Georgia, serif; }
.hero p { color: #94a3b8; margin-top: 8px; font-size: 14px; line-height: 1.6; }

.tier-bare-minimum { border-left: 4px solid #dc2626; }
.tier-highly-suggested { border-left: 4px solid #f59e0b; }
.tier-nice-to-have { border-left: 4px solid #3b82f6; }
.tier-not-needed { border-left: 4px solid #94a3b8; }

.section-header {
    font-size: 18px; font-weight: 600; color: #0f172a;
    font-family: 'Source Serif 4', Georgia, serif;
    margin: 0 0 16px 0;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# WORKFLOWS
# ══════════════════════════════════════════════════════════════════

WORKFLOWS = {
    "market_entry": {
        "title": "Bring a Product to Market",
        "subtitle": "From device description to full requirements -- tiered by priority",
        "persona": "Product Developers",
        "steps": ["Describe Your Device", "Classification & Details", "Your Requirements", "Timeline & Costs"],
    },
    "fiveten_k": {
        "title": "510(k) & Predicate Questions",
        "subtitle": "Find predicates, understand substantial equivalence, prep your submission",
        "persona": "RA Specialists",
        "steps": ["Device Info", "Predicate Search", "SE Comparison", "Submission Checklist"],
    },
    "testing": {
        "title": "What Testing Do I Need?",
        "subtitle": "Quick profile to tiered testing requirements in 60 seconds",
        "persona": "Product Developers",
        "steps": ["Quick Profile", "Your Testing Requirements"],
    },
    "pdac_hcpcs": {
        "title": "PDAC / HCPCS Billing Codes",
        "subtitle": "Documentation requirements for billing code submissions",
        "persona": "RA / Reimbursement Specialists",
        "steps": ["Product Category", "Submission Requirements"],
    },
    "standards_edu": {
        "title": "Understand a Standard",
        "subtitle": "ISO 13485, QSR vs QMSR, and more -- explained practically",
        "persona": "QMS Professionals",
        "steps": ["Pick a Topic", "Deep Dive"],
    },
    "gap_audit": {
        "title": "Gap Analysis & Audit Prep",
        "subtitle": "Assess your QMS readiness clause by clause",
        "persona": "QMS Professionals",
        "steps": ["Scope", "Assessment", "Report"],
    },
}


# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════

def init_session_state():
    defaults = {
        "active_workflow": None,
        "workflow_step": 0,
        "product_profile": {
            "name": "", "description": "", "class_us": "", "class_eu": "",
            "contact_type": "", "contact_duration": "", "sterile": False,
            "sterilization_method": "", "has_software": False, "software_safety_class": "",
            "is_electrical": False, "is_implantable": False, "target_markets": [],
            "intended_use": "", "predicate_device": "",
        },
        "gap_statuses": {},
        "chat_messages": [],
        "openai_client": None,
        "ai_model": "o3-mini",
        "show_chat": False,
        "edu_topic": None,
        "audit_scope": [],
        "pdac_category": None,
        "se_notes": {},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()


# ══════════════════════════════════════════════════════════════════
# NAVIGATION
# ══════════════════════════════════════════════════════════════════

def navigate_to(workflow_id, step=0):
    st.session_state["active_workflow"] = workflow_id
    st.session_state["workflow_step"] = step
    st.rerun()

def navigate_home():
    st.session_state["active_workflow"] = None
    st.session_state["workflow_step"] = 0
    st.rerun()

def advance_step():
    st.session_state["workflow_step"] += 1
    st.rerun()

def go_to_step(step):
    st.session_state["workflow_step"] = step
    st.rerun()


# ══════════════════════════════════════════════════════════════════
# OPENAI CLIENT
# ══════════════════════════════════════════════════════════════════

def get_openai_client():
    if st.session_state["openai_client"] is None:
        try:
            api_key = st.secrets.get("openai_api_key", "")
            if api_key:
                st.session_state["openai_client"] = openai.OpenAI(api_key=api_key)
        except Exception:
            pass
    return st.session_state["openai_client"]

AI_MODELS = {
    "o3-mini": {
        "label": "o3-mini (Recommended)",
        "description": "Best for regulatory analysis. Strong reasoning for interpreting standards and compliance questions.",
        "supports_temperature": False,
    },
    "gpt-4.1": {
        "label": "GPT-4.1",
        "description": "Best for detailed document drafting, audit reports, and structured output.",
        "supports_temperature": True,
    },
    "gpt-4o": {
        "label": "GPT-4o",
        "description": "Fast all-rounder for quick regulatory questions and market comparisons.",
        "supports_temperature": True,
    },
    "gpt-4o-mini": {
        "label": "GPT-4o Mini",
        "description": "Fastest and cheapest. Good for simple lookups and quick classification checks.",
        "supports_temperature": True,
    },
}

def get_ai_response(messages: List[Dict[str, str]], max_tokens: int = 4000, temperature: float = 0.4) -> str:
    client = get_openai_client()
    if not client:
        return "OpenAI API not configured. Add your openai_api_key to .streamlit/secrets.toml."
    try:
        model = st.session_state.get("ai_model", "o3-mini")
        model_info = AI_MODELS.get(model, {})
        token_param = "max_completion_tokens" if not model_info.get("supports_temperature", True) else "max_tokens"
        kwargs = {"model": model, "messages": messages, token_param: max_tokens}
        if model_info.get("supports_temperature", True):
            kwargs["temperature"] = temperature
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        return f"AI request failed: {e}"


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def profile():
    return st.session_state["product_profile"]

def gap_statuses():
    return st.session_state["gap_statuses"]

def _get_workflow_context():
    wf_id = st.session_state.get("active_workflow")
    if not wf_id or wf_id not in WORKFLOWS:
        return ""
    wf = WORKFLOWS[wf_id]
    step = st.session_state.get("workflow_step", 0)
    step_name = wf["steps"][step] if step < len(wf["steps"]) else ""
    return f"{wf['title']} - {step_name}"

def _process_chat_message(user_input: str):
    st.session_state["chat_messages"].append({"role": "user", "content": user_input})
    ctx = _get_workflow_context()
    system_prompt = build_system_prompt(profile(), gap_statuses(), workflow_context=ctx)
    messages = [{"role": "system", "content": system_prompt}]
    for msg in st.session_state["chat_messages"][-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    response = get_ai_response(messages, max_tokens=4000, temperature=0.4)
    st.session_state["chat_messages"].append({"role": "assistant", "content": response})

def _ask_ai_button(question: str, key: str):
    if st.button("Ask AI", key=key, type="secondary"):
        st.session_state["show_chat"] = True
        _process_chat_message(question)
        st.rerun()


# ══════════════════════════════════════════════════════════════════
# TOP BAR
# ══════════════════════════════════════════════════════════════════

st.markdown("""
<div class="top-bar">
    <div class="logo">R</div>
    <span class="title">RegIntel</span>
    <span class="subtitle">Medical Device Regulatory Intelligence</span>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════

with st.sidebar:
    if st.button("Home", key="nav_home", width="stretch",
                 type="primary" if st.session_state["active_workflow"] is None else "secondary"):
        navigate_home()

    wf_id = st.session_state.get("active_workflow")
    if wf_id and wf_id in WORKFLOWS:
        wf = WORKFLOWS[wf_id]
        st.markdown(f"**{wf['title']}**")
        current_step = st.session_state.get("workflow_step", 0)
        for i, step_name in enumerate(wf["steps"]):
            prefix = ">> " if i == current_step else ("   " if i > current_step else "   ")
            btn_type = "primary" if i == current_step else "secondary"
            if st.button(f"{prefix}{step_name}", key=f"wf_step_{i}", width="stretch",
                         type=btn_type, disabled=(i > current_step)):
                go_to_step(i)

    st.divider()

    if st.button("AI Advisor Chat", key="toggle_chat", width="stretch"):
        st.session_state["show_chat"] = not st.session_state.get("show_chat", False)
        st.rerun()

    with st.expander("AI Model", expanded=False):
        model_keys = list(AI_MODELS.keys())
        current_idx = model_keys.index(st.session_state.get("ai_model", "o3-mini"))
        selected = st.radio("Model", model_keys, index=current_idx,
                           format_func=lambda k: AI_MODELS[k]["label"], key="model_sel", label_visibility="collapsed")
        st.caption(AI_MODELS[selected]["description"])
        if selected != st.session_state.get("ai_model"):
            st.session_state["ai_model"] = selected

    st.divider()
    st.caption("ISO 13485 | FDA 21 CFR 820")
    st.caption("EU MDR | ANVISA | COFEPRIS")


# ══════════════════════════════════════════════════════════════════
# CHAT SIDEBAR RENDERER
# ══════════════════════════════════════════════════════════════════

def render_chat_panel():
    st.markdown("### AI Regulatory Advisor")
    p = profile()
    if p["name"]:
        st.caption(f"Context: **{p['name']}**")

    for msg in st.session_state["chat_messages"][-20:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not st.session_state["chat_messages"]:
        st.info("Ask anything about medical device regulations, testing, submissions, standards, or compliance.")

    if user_input := st.chat_input("Ask about regulations, testing, standards...", key="chat_input"):
        _process_chat_message(user_input)
        st.rerun()


# ══════════════════════════════════════════════════════════════════
# LANDING PAGE
# ══════════════════════════════════════════════════════════════════

def render_landing_page():
    st.markdown("""
    <div class="hero">
        <h2>What are you trying to do?</h2>
        <p>Pick a starting point below. Every path gives you clear, prioritized requirements --
        what's legally required, what's recommended, and what you can skip.</p>
    </div>
    """, unsafe_allow_html=True)

    row1 = st.columns(3)
    row2 = st.columns(3)
    all_cols = row1 + row2
    for i, (wf_id, wf) in enumerate(WORKFLOWS.items()):
        with all_cols[i]:
            with st.container(border=True):
                st.markdown(f"**{wf['title']}**")
                st.caption(wf['subtitle'])
                st.caption(f"For: {wf['persona']}")
                if st.button("Start", key=f"start_{wf_id}", width="stretch"):
                    navigate_to(wf_id, step=0)

    # Status summary at bottom
    st.markdown("---")
    p = profile()
    gs = get_gap_stats(gap_statuses())
    applicable = get_applicable_standards(p["target_markets"])
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Product Profile", "Set" if p["name"] else "Not Set")
    with c2:
        st.metric("Target Markets", len(p["target_markets"]) if p["target_markets"] else 0)
    with c3:
        st.metric("Applicable Standards", len(applicable))
    with c4:
        st.metric("Gap Analysis", f"{gs['compliant']}/{gs['total']}")


# ══════════════════════════════════════════════════════════════════
# SHARED: PROFILE FORM WIDGETS
# ══════════════════════════════════════════════════════════════════

def _render_device_basics(p, key_suffix=""):
    c1, c2 = st.columns(2)
    with c1:
        p["name"] = st.text_input("Device Name", value=p["name"], placeholder="e.g., SleepWell CPAP Mask", key=f"dev_name{key_suffix}")
    with c2:
        p["predicate_device"] = st.text_input("Predicate Device (if known)", value=p["predicate_device"], placeholder="e.g., K123456", key=f"pred{key_suffix}")
    p["description"] = st.text_area("Describe your device", value=p["description"], placeholder="What is it? What does it do? What is it made of?", height=80, key=f"desc{key_suffix}")
    p["intended_use"] = st.text_area("Intended Use", value=p["intended_use"], placeholder="The device is intended for...", height=60, key=f"iu{key_suffix}")

def _render_classification(p, key_suffix=""):
    c1, c2 = st.columns(2)
    with c1:
        us_options = ["", "Class I", "Class I (510(k) required)", "Class II", "Class II (De Novo)"]
        us_labels = ["Select...", "Class I - Low Risk", "Class I - 510(k) Required", "Class II - 510(k)", "Class II - De Novo"]
        idx = us_options.index(p["class_us"]) if p["class_us"] in us_options else 0
        p["class_us"] = st.selectbox("US FDA Classification", us_options, index=idx,
                                      format_func=lambda x: us_labels[us_options.index(x)], key=f"us_cls{key_suffix}")
    with c2:
        eu_options = ["", "Class I", "Class I (sterile)", "Class I (measuring)", "Class I (reusable surgical)", "Class IIa", "Class IIb"]
        eu_labels = ["Select...", "Class I", "Class I - Sterile", "Class I - Measuring", "Class I - Reusable Surgical", "Class IIa", "Class IIb"]
        idx = eu_options.index(p["class_eu"]) if p["class_eu"] in eu_options else 0
        p["class_eu"] = st.selectbox("EU MDR Classification (if targeting EU)", eu_options, index=idx,
                                      format_func=lambda x: eu_labels[eu_options.index(x)], key=f"eu_cls{key_suffix}")

def _render_characteristics(p, key_suffix=""):
    c1, c2 = st.columns(2)
    with c1:
        contact_options = ["", "none", "intact-skin", "mucosal-membrane", "breached-skin", "blood-path-indirect", "blood-contact", "tissue-bone", "implant"]
        contact_labels = ["Select...", "No patient contact", "Intact skin", "Mucosal membrane", "Breached skin", "Blood path - indirect", "Blood contacting", "Tissue/bone", "Implant"]
        idx = contact_options.index(p["contact_type"]) if p["contact_type"] in contact_options else 0
        p["contact_type"] = st.selectbox("Patient Contact Type", contact_options, index=idx,
                                          format_func=lambda x: contact_labels[contact_options.index(x)], key=f"ct{key_suffix}")
    with c2:
        dur_options = ["", "limited", "prolonged", "permanent"]
        dur_labels = ["Select...", "Limited (< 24 hours)", "Prolonged (24h - 30 days)", "Permanent (> 30 days)"]
        idx = dur_options.index(p["contact_duration"]) if p["contact_duration"] in dur_options else 0
        p["contact_duration"] = st.selectbox("Contact Duration", dur_options, index=idx,
                                              format_func=lambda x: dur_labels[dur_options.index(x)], key=f"cd{key_suffix}")

    c1, c2, c3 = st.columns(3)
    with c1:
        p["sterile"] = st.toggle("Sterile", value=p["sterile"], key=f"ster{key_suffix}")
    with c2:
        p["has_software"] = st.toggle("Has Software", value=p["has_software"], key=f"sw{key_suffix}")
    with c3:
        p["is_electrical"] = st.toggle("Electrical", value=p["is_electrical"], key=f"elec{key_suffix}")

    if p["sterile"]:
        ster_options = ["", "EO", "gamma", "e-beam", "steam", "dry-heat", "other"]
        ster_labels = ["Select...", "Ethylene Oxide (EO)", "Gamma Radiation", "Electron Beam", "Steam", "Dry Heat", "Other"]
        idx = ster_options.index(p["sterilization_method"]) if p["sterilization_method"] in ster_options else 0
        p["sterilization_method"] = st.selectbox("Sterilization Method", ster_options, index=idx,
                                                  format_func=lambda x: ster_labels[ster_options.index(x)], key=f"sm{key_suffix}")
    if p["has_software"]:
        sw_options = ["", "A", "B", "C"]
        sw_labels = ["Select...", "Class A - No harm", "Class B - Non-serious injury", "Class C - Death/serious injury"]
        idx = sw_options.index(p["software_safety_class"]) if p["software_safety_class"] in sw_options else 0
        p["software_safety_class"] = st.selectbox("Software Safety Class (IEC 62304)", sw_options, index=idx,
                                                   format_func=lambda x: sw_labels[sw_options.index(x)], key=f"ssc{key_suffix}")

def _render_market_selection(p, key_suffix=""):
    st.caption("Select your target markets (US is selected by default):")
    # Auto-select US if nothing selected
    if not p["target_markets"]:
        p["target_markets"] = ["US"]
    cols = st.columns(len(MARKETS))
    for i, (code, market) in enumerate(MARKETS.items()):
        with cols[i]:
            active = code in p["target_markets"]
            if st.checkbox(f"{market['flag']} {market['name']}", value=active, key=f"mkt_{code}{key_suffix}"):
                if code not in p["target_markets"]:
                    p["target_markets"].append(code)
            else:
                if code in p["target_markets"]:
                    p["target_markets"].remove(code)

def _render_tiered_requirements(reqs, show_not_needed=True):
    """Render requirements grouped by tier with visual styling."""
    for tier_key in ["BARE_MINIMUM", "HIGHLY_SUGGESTED", "NICE_TO_HAVE", "NOT_NEEDED"]:
        tier_reqs = [r for r in reqs if r["tier"] == tier_key]
        if not tier_reqs:
            continue
        if tier_key == "NOT_NEEDED" and not show_not_needed:
            continue

        tier_info = REQUIREMENT_TIERS[tier_key]
        expanded = tier_key in ("BARE_MINIMUM", "HIGHLY_SUGGESTED")

        with st.expander(f"**{tier_info['label']}** ({len(tier_reqs)} items) -- {tier_info['description']}", expanded=expanded):
            for r in tier_reqs:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.markdown(f"**{r['name']}**")
                        st.caption(f"{r['reference']} -- {r['detail']}")
                    with c2:
                        st.caption(f"Timeline: {r['timeline']}")
                    with c3:
                        st.caption(f"Cost: {r['cost']}")


# ══════════════════════════════════════════════════════════════════
# WORKFLOW 1: BRING A PRODUCT TO MARKET
# ══════════════════════════════════════════════════════════════════

def render_market_entry(step):
    p = profile()

    if step == 0:
        st.header("Step 1: Describe Your Device")
        st.caption("Tell us about your device. We'll figure out what you need.")

        with st.container(border=True):
            _render_device_basics(p, key_suffix="_me")

        with st.container(border=True):
            st.subheader("Target Markets")
            _render_market_selection(p, key_suffix="_me")

        st.session_state["product_profile"] = p
        if st.button("Next: Classification", key="me_next_0", type="primary"):
            advance_step()

    elif step == 1:
        st.header("Step 2: Classification & Device Details")
        st.caption("Help us understand the device characteristics so we can determine exact requirements.")

        with st.container(border=True):
            st.subheader("FDA / EU Classification")
            _render_classification(p, key_suffix="_me")
            _ask_ai_button(f"Help me determine the FDA classification for: {p['description'] or p['name'] or 'my medical device'}", "me_ai_class")

        with st.container(border=True):
            st.subheader("Device Characteristics")
            _render_characteristics(p, key_suffix="_me")

        st.session_state["product_profile"] = p
        if st.button("Next: Show My Requirements", key="me_next_1", type="primary"):
            advance_step()

    elif step == 2:
        st.header("Step 3: Your Requirements")
        if p["name"]:
            st.caption(f"Requirements for **{p['name']}** -- organized by priority")
        else:
            st.caption("Requirements organized by priority based on your device profile")

        reqs = get_tiered_requirements(p)
        bare = [r for r in reqs if r["tier"] == "BARE_MINIMUM"]
        suggested = [r for r in reqs if r["tier"] == "HIGHLY_SUGGESTED"]
        nice = [r for r in reqs if r["tier"] == "NICE_TO_HAVE"]
        not_needed = [r for r in reqs if r["tier"] == "NOT_NEEDED"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Bare Minimum", len(bare))
        c2.metric("Highly Suggested", len(suggested))
        c3.metric("Nice to Have", len(nice))
        c4.metric("Not Needed", len(not_needed))

        _render_tiered_requirements(reqs)

        if st.button("Next: Timeline & Costs", key="me_next_2", type="primary"):
            advance_step()

    elif step == 3:
        st.header("Step 4: Timeline & Costs")
        st.caption("Estimated timeline and costs for your requirements")

        reqs = get_tiered_requirements(p)
        bare = [r for r in reqs if r["tier"] == "BARE_MINIMUM"]
        suggested = [r for r in reqs if r["tier"] == "HIGHLY_SUGGESTED"]

        # Market pathways
        markets = p["target_markets"] if p["target_markets"] else ["US"]
        with st.container(border=True):
            st.subheader("Submission Pathways by Market")
            rows = []
            for mkt in markets:
                info = get_classification_info(mkt, p)
                if not info:
                    continue
                if mkt == "EU":
                    class_key = p.get("class_eu") or "Class IIa"
                else:
                    raw = p.get("class_us", "")
                    class_key = "Class II" if "Class II" in raw else ("Class I" if "Class I" in raw else "Class II")
                rows.append({
                    "Market": f"{MARKETS[mkt]['flag']} {MARKETS[mkt]['agency']}",
                    "Class": class_key,
                    "Pathway": info["pathway"],
                    "Timeline": info["timeline"],
                    "Fees": info.get("fees", ""),
                })
            if rows:
                st.dataframe(pd.DataFrame(rows), hide_index=True)

        # Cost summary
        with st.container(border=True):
            st.subheader("Requirements Summary")
            summary_rows = []
            for r in bare + suggested:
                summary_rows.append({
                    "Requirement": r["name"],
                    "Priority": REQUIREMENT_TIERS[r["tier"]]["label"],
                    "Timeline": r["timeline"],
                    "Est. Cost": r["cost"],
                    "Reference": r["reference"],
                })
            if summary_rows:
                st.dataframe(pd.DataFrame(summary_rows), hide_index=True)

        _ask_ai_button(f"Give me a project plan and critical path for bringing {p['name'] or 'my device'} to market in {', '.join(markets)}. Device: {p['description']}", "me_ai_plan")

        if st.button("Start Over", key="me_restart"):
            navigate_home()


# ══════════════════════════════════════════════════════════════════
# WORKFLOW 2: 510(k) & PREDICATE
# ══════════════════════════════════════════════════════════════════

def render_fiveten_k(step):
    p = profile()

    if step == 0:
        st.header("Step 1: Your Device")
        st.caption("Describe your device so we can help find predicates and prep your 510(k).")

        with st.container(border=True):
            _render_device_basics(p, key_suffix="_5k")
        with st.container(border=True):
            st.subheader("Classification")
            _render_classification(p, key_suffix="_5k")

        st.session_state["product_profile"] = p
        if st.button("Next: Find Predicates", key="5k_next_0", type="primary"):
            advance_step()

    elif step == 1:
        st.header("Step 2: Predicate Search")
        guidance = FIVETEN_K_GUIDANCE["predicate_search"]
        st.caption("How to find a predicate device for your 510(k)")

        with st.container(border=True):
            st.subheader(guidance["title"])
            for i, s in enumerate(guidance["steps"], 1):
                st.markdown(f"**{i}.** {s}")

        st.info("Use the AI Advisor to help identify potential predicate devices based on your device description.")
        _ask_ai_button(f"Help me find FDA 510(k) predicate devices for: {p['name']}. Description: {p['description']}. Intended use: {p['intended_use']}", "5k_ai_pred")

        if st.button("Next: SE Comparison", key="5k_next_1", type="primary"):
            advance_step()

    elif step == 2:
        st.header("Step 3: Substantial Equivalence Comparison")
        se = FIVETEN_K_GUIDANCE["substantial_equivalence"]
        st.caption("Compare your device to the predicate across these areas:")

        for area_info in se["comparison_areas"]:
            with st.container(border=True):
                c1, c2 = st.columns([2, 3])
                with c1:
                    required_badge = " :red[**Required**]" if area_info["required"] else " (if applicable)"
                    st.markdown(f"**{area_info['area']}**{required_badge}")
                    st.caption(area_info["description"])
                with c2:
                    area_key = area_info["area"].replace(" ", "_").replace("/", "_")
                    notes = st.session_state["se_notes"].get(area_key, "")
                    new_notes = st.text_area("Your comparison notes", value=notes, key=f"se_{area_key}", height=60, label_visibility="collapsed", placeholder="Same as predicate / Different because...")
                    st.session_state["se_notes"][area_key] = new_notes

        _ask_ai_button(f"Help me write a substantial equivalence argument for my device: {p['name']}. Description: {p['description']}. Predicate: {p['predicate_device']}", "5k_ai_se")

        if st.button("Next: Submission Checklist", key="5k_next_2", type="primary"):
            advance_step()

    elif step == 3:
        st.header("Step 4: 510(k) Submission Checklist")
        st.caption("Everything you need in your 510(k) submission package")

        sections = FIVETEN_K_GUIDANCE["submission_sections"]
        for sec in sections:
            tier = sec["tier"]
            if tier == "conditional":
                cond = sec.get("condition", "")
                if cond == "patient-contact" and (not p.get("contact_type") or p["contact_type"] == "none"):
                    tier = "NOT_NEEDED"
                elif cond == "sterile" and not p.get("sterile"):
                    tier = "NOT_NEEDED"
                elif cond == "software" and not p.get("has_software"):
                    tier = "NOT_NEEDED"
                elif cond == "electrical" and not p.get("is_electrical"):
                    tier = "NOT_NEEDED"
                else:
                    tier = "BARE_MINIMUM"

            tier_info = REQUIREMENT_TIERS.get(tier, REQUIREMENT_TIERS["BARE_MINIMUM"])
            color = tier_info["color"]
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{sec['name']}**")
                    st.caption(sec["detail"])
                with c2:
                    st.markdown(f'<span style="background:{color}; color:#fff; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700;">{tier_info["label"]}</span>', unsafe_allow_html=True)

        _ask_ai_button(f"Review my 510(k) submission plan for {p['name']}. What am I likely missing?", "5k_ai_review")


# ══════════════════════════════════════════════════════════════════
# WORKFLOW 3: WHAT TESTING DO I NEED?
# ══════════════════════════════════════════════════════════════════

def render_testing(step):
    p = profile()

    if step == 0:
        st.header("Quick Device Profile")
        st.caption("Answer a few questions and we'll tell you exactly what testing you need.")

        with st.container(border=True):
            p["name"] = st.text_input("Device name (optional)", value=p["name"], key="test_name")
            _render_characteristics(p, key_suffix="_test")

        with st.container(border=True):
            st.subheader("Classification")
            us_options = ["", "Class I", "Class I (510(k) required)", "Class II", "Class II (De Novo)"]
            us_labels = ["Select...", "Class I - Low Risk", "Class I - 510(k) Required", "Class II - 510(k)", "Class II - De Novo"]
            idx = us_options.index(p["class_us"]) if p["class_us"] in us_options else 0
            p["class_us"] = st.selectbox("US FDA Classification", us_options, index=idx,
                                          format_func=lambda x: us_labels[us_options.index(x)], key="test_us_cls")

        if not p["target_markets"]:
            p["target_markets"] = ["US"]
        st.session_state["product_profile"] = p

        if st.button("Show My Testing Requirements", key="test_go", type="primary"):
            advance_step()

    elif step == 1:
        st.header("Your Testing Requirements")
        if p["name"]:
            st.caption(f"Testing requirements for **{p['name']}**")

        reqs = get_tiered_requirements(p)
        test_reqs = [r for r in reqs if r["category"] in ("Testing", "Biocompatibility", "Sterilization", "Software")]
        if not test_reqs:
            test_reqs = [r for r in reqs if r["category"] != "Regulatory" and r["category"] != "QMS" and r["category"] != "Labeling" and r["category"] != "Post-Market"]

        _render_tiered_requirements(test_reqs)

        _ask_ai_button(f"What testing do I need for: {p['name'] or 'my device'}? Contact: {p['contact_type']}, Duration: {p['contact_duration']}, Sterile: {p['sterile']}, Software: {p['has_software']}, Electrical: {p['is_electrical']}", "test_ai")

        if st.button("See Full Requirements (all categories)", key="test_full"):
            navigate_to("market_entry", step=2)


# ══════════════════════════════════════════════════════════════════
# WORKFLOW 4: PDAC / HCPCS
# ══════════════════════════════════════════════════════════════════

def render_pdac_hcpcs(step):
    if step == 0:
        st.header("PDAC / HCPCS Billing Codes")
        st.caption(PDAC_HCPCS_GUIDANCE["overview"])

        st.subheader("Select Your Product Category")
        for cat_name, cat_info in PDAC_HCPCS_GUIDANCE["common_codes"].items():
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{cat_name}**")
                    st.caption(f"HCPCS Range: {cat_info['range']} -- {cat_info['examples']}")
                with c2:
                    if st.button("Select", key=f"pdac_{cat_name}"):
                        st.session_state["pdac_category"] = cat_name
                        advance_step()

        _ask_ai_button("Help me determine the correct HCPCS code for my medical device. What information do you need?", "pdac_ai_code")

    elif step == 1:
        cat = st.session_state.get("pdac_category", "")
        st.header(f"Submission Requirements: {cat}")
        if cat:
            cat_info = PDAC_HCPCS_GUIDANCE["common_codes"].get(cat, {})
            st.caption(f"HCPCS Range: {cat_info.get('range', '')} -- {cat_info.get('examples', '')}")

        st.subheader("What You Need to Submit")
        for req in PDAC_HCPCS_GUIDANCE["submission_requirements"]:
            tier_info = REQUIREMENT_TIERS.get(req["tier"], REQUIREMENT_TIERS["BARE_MINIMUM"])
            color = tier_info["color"]
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{req['name']}**")
                    st.caption(req["detail"])
                with c2:
                    st.markdown(f'<span style="background:{color}; color:#fff; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700;">{tier_info["label"]}</span>', unsafe_allow_html=True)

        _ask_ai_button(f"What documentation do I need to submit a PDAC coding verification request for a {cat} device? Walk me through the process.", "pdac_ai_docs")


# ══════════════════════════════════════════════════════════════════
# WORKFLOW 5: UNDERSTAND A STANDARD
# ══════════════════════════════════════════════════════════════════

def render_standards_edu(step):
    if step == 0:
        st.header("Understand a Standard")
        st.caption("Pick a topic for a practical, plain-language explanation.")

        topics = [
            ("iso13485", "ISO 13485:2016 -- Quality Management Systems", "The foundation QMS standard for medical devices. What it requires, clause by clause."),
            ("qsr_qmsr", "QSR vs QMSR -- What Changed?", "FDA's transition from 21 CFR 820 (QSR) to the new QMSR aligned with ISO 13485. Key differences explained."),
            ("fda_510k", "FDA 510(k) Process Explained", "How 510(k) works, what you submit, how to find predicates, and common pitfalls."),
            ("eu_mdr", "EU MDR 2017/745 Explained", "European Medical Device Regulation requirements, Notified Bodies, CE marking, and technical documentation."),
            ("risk_mgmt", "Risk Management (ISO 14971)", "The risk management process for medical devices -- hazard identification, risk controls, and residual risk."),
            ("browse_all", "Browse Full Standards Library", "Search and explore all integrated standards, audit checklists, and regulatory knowledge."),
        ]

        # Search
        search_query = st.text_input("Search standards knowledge base", placeholder="e.g., CAPA, nebulizer, anti-asphyxia...", key="edu_search")
        if search_query:
            results = search_standards_knowledge(search_query)
            if results:
                st.success(f"Found {len(results)} result(s)")
                for std_key, section, content in results[:10]:
                    with st.expander(f"**{std_key}** - {section}"):
                        st.write(content[:2000])
            else:
                st.warning(f"No results for '{search_query}'")

        cols = st.columns(2)
        for i, (topic_id, title, desc) in enumerate(topics):
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.caption(desc)
                    if st.button("Explore", key=f"edu_{topic_id}"):
                        st.session_state["edu_topic"] = topic_id
                        advance_step()

    elif step == 1:
        topic = st.session_state.get("edu_topic", "browse_all")

        if topic == "iso13485":
            st.header("ISO 13485:2016 -- Clause-Level Reference")
            st.caption("Quality management systems -- Requirements for regulatory purposes")
            for section in ISO_13485_CLAUSES:
                with st.expander(f"**Section {section['id']} - {section['title']}**"):
                    for sub in section["subclauses"]:
                        badge = " :red[**CRITICAL**]" if sub.get("critical") else ""
                        st.markdown(f"`{sub['id']}` **{sub['title']}**{badge}")
                        st.caption(sub["summary"])
                        audit_items = get_audit_checklist_for_clause(sub["id"])
                        if audit_items:
                            st.caption(f"Audit checklist: {len(audit_items)} item(s)")
                        st.markdown("---")

        elif topic == "qsr_qmsr":
            st.header("QSR vs QMSR -- What Changed?")
            st.caption("FDA's Quality Management System Regulation (QMSR) replaces the old QSR (21 CFR 820) and aligns with ISO 13485:2016.")
            st.markdown("""
**Key Changes:**
- **Old:** 21 CFR 820 (Quality System Regulation) -- US-specific requirements
- **New:** QMSR -- incorporates ISO 13485:2016 by reference
- **Effective:** February 2, 2026
- **Impact:** Companies with ISO 13485 certification are largely compliant already

**What Stays the Same:**
- Design controls still required
- CAPA still required
- Complaint handling still required
- Management responsibility still required

**What Changes:**
- Terminology aligns with ISO 13485 (e.g., "Design History File" terminology)
- Some US-specific requirements removed or simplified
- Greater alignment with international requirements = easier multi-market compliance
""")

            st.subheader("FDA Audit Checklist -- QSR vs QMSR References")
            for subsystem, data in FDA_AUDIT_CHECKLIST["subsystems"].items():
                if isinstance(data, dict) and "items" in data:
                    with st.expander(f"**{subsystem}** ({len(data['items'])} items)"):
                        for item in data["items"]:
                            st.markdown(f"**#{item['item']}** - {item['detail']}")
                            refs = []
                            if item.get("iso_ref"):
                                refs.append(f"ISO: {item['iso_ref']}")
                            if item.get("qsr_ref"):
                                refs.append(f"QSR: {item['qsr_ref']}")
                            if refs:
                                st.caption(" | ".join(refs))
                            st.markdown("---")

            _ask_ai_button("Explain the key differences between FDA QSR (21 CFR 820) and the new QMSR for a company already certified to ISO 13485. What do we need to change?", "edu_ai_qmsr")

        elif topic == "fda_510k":
            st.header("FDA 510(k) Process Explained")
            st.markdown("""
**What is a 510(k)?**

A 510(k) is a premarket submission to FDA demonstrating that your device is **substantially equivalent** to a legally marketed device (predicate) that is not subject to PMA.

**The Process:**
1. **Identify your device classification** -- search FDA's Product Classification Database
2. **Find a predicate device** -- search the 510(k) database
3. **Determine substantial equivalence** -- same intended use + similar technology
4. **Prepare your submission** -- technical documentation, testing, labeling
5. **Submit to FDA** -- electronically via eSTAR
6. **FDA Review** -- 90-day review clock (often takes 3-6 months)
7. **Decision** -- Substantially Equivalent (SE), Not SE, or Additional Information needed

**Types of 510(k):**
- **Traditional** -- most common, full comparison to predicate
- **Abbreviated** -- uses guidance documents or special controls
- **Special** -- for modifications to your own cleared device

**Cost:** ~$22,124 (small business) or ~$88,495 (standard) FY2025
""")
            _ask_ai_button("Walk me through the 510(k) process step by step for a Class II medical device. What are the most common reasons for FDA rejection?", "edu_ai_510k")

        elif topic == "eu_mdr":
            st.header("EU MDR 2017/745 Explained")
            st.markdown("""
**What is EU MDR?**

The Medical Device Regulation (EU) 2017/745 replaced the old Medical Device Directives (MDD/AIMDD) and is the current regulatory framework for medical devices in the European Union.

**Key Requirements:**
- **Classification:** Class I, IIa, IIb, III (Annex VIII rules)
- **Technical Documentation:** Annex II and III requirements
- **Clinical Evaluation:** Annex XIV -- more rigorous than MDD
- **Post-Market Surveillance:** Systematic PMS plan required
- **UDI:** Unique Device Identification system (EUDAMED)
- **Notified Body:** Required for Class IIa and above
- **Authorized Representative:** Required for non-EU manufacturers

**Timeline to CE Mark:**
- Class I: 6-12 months
- Class IIa: 12-18 months
- Class IIb: 18-24+ months
""")
            _ask_ai_button("Compare EU MDR requirements to FDA 510(k) for a Class II / Class IIa medical device. What additional work is needed for EU market entry?", "edu_ai_mdr")

        elif topic == "risk_mgmt":
            st.header("Risk Management -- ISO 14971:2019")
            st.markdown("""
**ISO 14971 defines the risk management process for medical devices throughout their lifecycle.**

**Key Steps:**
1. **Risk Management Plan** -- scope, criteria, review schedule
2. **Hazard Identification** -- systematic identification of hazards
3. **Risk Estimation** -- severity x probability for each hazardous situation
4. **Risk Evaluation** -- compare against acceptability criteria
5. **Risk Control** -- implement controls (inherent safety, protective measures, information)
6. **Residual Risk Evaluation** -- verify controls are effective
7. **Risk Management Report** -- summary of entire process
8. **Production & Post-Production** -- ongoing monitoring

**Risk Acceptability Matrix:**
- Severity levels: Negligible, Minor, Serious, Critical, Catastrophic
- Probability levels: Incredible, Remote, Occasional, Probable, Frequent
""")
            _ask_ai_button("Help me set up a risk management file for a medical device per ISO 14971. What hazard categories should I consider?", "edu_ai_risk")

        else:  # browse_all
            st.header("Standards Library")
            search_query = st.text_input("Search", placeholder="Search standards...", key="lib_search")
            if search_query:
                results = search_standards_knowledge(search_query)
                if results:
                    for std_key, section, content in results[:20]:
                        with st.expander(f"**{std_key}** - {section}"):
                            st.write(content[:2000])
                else:
                    st.warning(f"No results for '{search_query}'")

            for std_key, knowledge in ALL_STANDARDS_KNOWLEDGE.items():
                doc_info = DOCUMENT_REGISTRY.get(std_key, {})
                with st.expander(f"**{std_key}** - {knowledge['title']}"):
                    st.markdown(f"**Category:** {doc_info.get('category', 'N/A')} | **Edition:** {doc_info.get('edition', 'N/A')}")
                    st.write(knowledge.get("scope", ""))
                    sections = knowledge.get("sections", {})
                    for sec_key, sec_val in sections.items():
                        if isinstance(sec_val, str):
                            with st.expander(f"{sec_key}"):
                                st.write(sec_val[:3000])
                        elif isinstance(sec_val, dict):
                            content = sec_val.get("content", "")
                            if content:
                                with st.expander(f"{sec_key} - {sec_val.get('title', '')}"):
                                    st.write(content[:3000])

            for key, std in STANDARDS_MAP.items():
                with st.expander(f"**{key}** - {std['title']}"):
                    st.markdown(f"**Category:** {std['category']}")
                    st.write(std["summary"])
                    flags = " ".join(MARKETS[m]["flag"] for m in std["applicableMarkets"] if m in MARKETS)
                    st.caption(f"Markets: {flags}")

        if st.button("Back to Topics", key="edu_back"):
            go_to_step(0)


# ══════════════════════════════════════════════════════════════════
# WORKFLOW 6: GAP ANALYSIS & AUDIT PREP
# ══════════════════════════════════════════════════════════════════

def render_gap_audit(step):
    if step == 0:
        st.header("Gap Analysis & Audit Prep")
        st.caption("What are you preparing for?")

        audit_types = [
            ("FDA Inspection", "Prepare for an FDA Quality System inspection", ["QMS Foundation", "Management", "Resources", "Design Controls", "Purchasing", "Production", "Feedback & Improvement"]),
            ("Notified Body Audit", "Prepare for a CE marking / ISO 13485 audit", ["QMS Foundation", "Management", "Resources", "Design Controls", "Purchasing", "Production", "Feedback & Improvement"]),
            ("Internal Audit", "Run an internal audit against ISO 13485", ["QMS Foundation", "Management", "Resources", "Design Controls", "Purchasing", "Production", "Feedback & Improvement"]),
            ("Quick Check -- Design Controls Only", "Focus on design and development controls", ["Design Controls"]),
            ("Quick Check -- CAPA & Complaints", "Focus on feedback and improvement systems", ["Feedback & Improvement"]),
        ]

        for name, desc, categories in audit_types:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{name}**")
                    st.caption(desc)
                with c2:
                    if st.button("Start", key=f"audit_{name}"):
                        st.session_state["audit_scope"] = categories
                        advance_step()

    elif step == 1:
        scope = st.session_state.get("audit_scope", [])
        st.header("Assessment")
        gs = get_gap_stats(gap_statuses())

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Items", gs["total"])
        c2.metric("Compliant", gs["compliant"])
        c3.metric("Partial", gs["partial"])
        c4.metric("Non-Compliant", gs["non_compliant"])
        c5.metric("Not Assessed", gs["not_assessed"])
        st.progress(gs["score"] / 100 if gs["score"] > 0 else 0, text=f"{gs['score']}% compliance score")

        categories = list(dict.fromkeys(item["category"] for item in GAP_ANALYSIS_ITEMS))
        filtered_cats = [c for c in categories if c in scope] if scope else categories

        for cat in filtered_cats:
            items = [item for item in GAP_ANALYSIS_ITEMS if item["category"] == cat]
            cat_compliant = sum(1 for i in items if gap_statuses().get(i["id"]) == "compliant")

            with st.expander(f"**{cat}** ({cat_compliant}/{len(items)} compliant)", expanded=True):
                for item in items:
                    col_label, col_btns = st.columns([3, 1])
                    with col_label:
                        critical_mark = " :red[CRITICAL]" if item.get("critical") else ""
                        st.markdown(f"**{item['item']}**{critical_mark}")
                        st.caption(f"Clause {item['clause']}")
                    with col_btns:
                        current = gap_statuses().get(item["id"])
                        options = ["Not assessed", "Compliant", "Partial", "Non-compliant"]
                        status_map = {"Not assessed": None, "Compliant": "compliant", "Partial": "partial", "Non-compliant": "non-compliant"}
                        reverse_map = {v: k for k, v in status_map.items()}
                        current_label = reverse_map.get(current, "Not assessed")
                        new_label = st.selectbox("Status", options, index=options.index(current_label),
                                                  key=f"gap_{item['id']}", label_visibility="collapsed")
                        new_status = status_map[new_label]
                        if new_status is not None:
                            st.session_state["gap_statuses"][item["id"]] = new_status
                        elif item["id"] in st.session_state["gap_statuses"]:
                            del st.session_state["gap_statuses"][item["id"]]

        if st.button("View Report", key="audit_report", type="primary"):
            advance_step()

    elif step == 2:
        st.header("Gap Analysis Report")
        gs = get_gap_stats(gap_statuses())

        c1, c2, c3 = st.columns(3)
        c1.metric("Compliance Score", f"{gs['score']}%")
        c2.metric("Compliant", gs["compliant"])
        c3.metric("Gaps Found", gs["non_compliant"] + gs["partial"])

        # Priority actions
        st.subheader("Priority Actions")
        critical_gaps = [item for item in GAP_ANALYSIS_ITEMS
                        if item.get("critical") and gap_statuses().get(item["id"]) == "non-compliant"]
        other_gaps = [item for item in GAP_ANALYSIS_ITEMS
                     if gap_statuses().get(item["id"]) == "non-compliant" and item not in critical_gaps]
        partial_items = [item for item in GAP_ANALYSIS_ITEMS
                        if gap_statuses().get(item["id"]) == "partial"]

        if critical_gaps:
            st.error(f"**{len(critical_gaps)} Critical Non-Compliant Items -- Address Immediately**")
            for item in critical_gaps:
                st.markdown(f"- **{item['item']}** (Clause {item['clause']})")
        if other_gaps:
            st.warning(f"**{len(other_gaps)} Non-Compliant Items**")
            for item in other_gaps:
                st.markdown(f"- **{item['item']}** (Clause {item['clause']})")
        if partial_items:
            st.info(f"**{len(partial_items)} Partially Compliant Items -- Needs Improvement**")
            for item in partial_items:
                st.markdown(f"- **{item['item']}** (Clause {item['clause']})")

        if not critical_gaps and not other_gaps and not partial_items:
            if gs["compliant"] > 0:
                st.success("All assessed items are compliant!")
            else:
                st.info("No items assessed yet. Go back to the Assessment step to evaluate your QMS.")

        _ask_ai_button(f"Based on my gap analysis: {gs['compliant']} compliant, {gs['partial']} partial, {gs['non_compliant']} non-compliant out of {gs['total']} items. Generate an executive summary and prioritized remediation plan.", "audit_ai_report")


# ══════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ══════════════════════════════════════════════════════════════════

show_chat = st.session_state.get("show_chat", False)
wf = st.session_state.get("active_workflow")
step = st.session_state.get("workflow_step", 0)

if show_chat:
    main_col, chat_col = st.columns([3, 1])
    with chat_col:
        render_chat_panel()
    with main_col:
        if wf is None:
            render_landing_page()
        elif wf == "market_entry":
            render_market_entry(step)
        elif wf == "fiveten_k":
            render_fiveten_k(step)
        elif wf == "testing":
            render_testing(step)
        elif wf == "pdac_hcpcs":
            render_pdac_hcpcs(step)
        elif wf == "standards_edu":
            render_standards_edu(step)
        elif wf == "gap_audit":
            render_gap_audit(step)
else:
    if wf is None:
        render_landing_page()
    elif wf == "market_entry":
        render_market_entry(step)
    elif wf == "fiveten_k":
        render_fiveten_k(step)
    elif wf == "testing":
        render_testing(step)
    elif wf == "pdac_hcpcs":
        render_pdac_hcpcs(step)
    elif wf == "standards_edu":
        render_standards_edu(step)
    elif wf == "gap_audit":
        render_gap_audit(step)
