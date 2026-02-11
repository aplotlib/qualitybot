import streamlit as st
import pandas as pd
from typing import List, Dict
import openai

from src.regulatory_data import (
    MARKETS,
    ISO_13485_CLAUSES,
    STANDARDS_MAP,
    GAP_ANALYSIS_ITEMS,
    get_applicable_standards,
    get_applicable_tests,
    get_gap_stats,
    get_classification_info,
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

.block-container { padding-top: 1rem; }

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

.stat-card {
    background: #fff; border-radius: 12px;
    border: 1px solid #e2e8f0; padding: 18px 20px;
    border-left: 4px solid var(--accent, #3b82f6);
}
.stat-card .label { font-size: 12px; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }
.stat-card .value { font-size: 22px; font-weight: 700; color: #0f172a; margin-top: 4px; font-family: 'Source Serif 4', Georgia, serif; }
.stat-card .sublabel { font-size: 12px; color: #94a3b8; margin-top: 4px; }

.market-card {
    padding: 14px 16px; border-radius: 10px;
    border: 1px solid #e2e8f0; background: #fafafa;
    transition: all 0.2s;
}
.market-card.active { border-color: var(--mcolor, #3b82f6); background: color-mix(in srgb, var(--mcolor, #3b82f6) 5%, white); }
.market-card .flag { font-size: 20px; }
.market-card .name { font-weight: 600; font-size: 13px; color: #0f172a; }
.market-card .agency { font-size: 12px; color: #64748b; }

.section-header {
    font-size: 18px; font-weight: 600; color: #0f172a;
    font-family: 'Source Serif 4', Georgia, serif;
    margin: 0 0 16px 0;
}

.critical-badge {
    background: #fee2e2; color: #dc2626;
    padding: 1px 6px; border-radius: 4px;
    font-size: 10px; font-weight: 700;
    margin-left: 6px;
}

.std-category {
    color: #fff; padding: 2px 8px; border-radius: 4px;
    font-size: 10px; font-weight: 600; text-transform: uppercase;
    white-space: nowrap;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ══════════════════════════════════════════════════════════════════

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "active_tab": "Dashboard",
        "product_profile": {
            "name": "",
            "description": "",
            "class_us": "",
            "class_eu": "",
            "contact_type": "",
            "contact_duration": "",
            "sterile": False,
            "sterilization_method": "",
            "has_software": False,
            "software_safety_class": "",
            "is_electrical": False,
            "is_implantable": False,
            "target_markets": [],
            "intended_use": "",
            "predicate_device": "",
        },
        "gap_statuses": {},
        "chat_messages": [],
        "openai_client": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# ══════════════════════════════════════════════════════════════════
# OPENAI CLIENT
# ══════════════════════════════════════════════════════════════════

def get_openai_client():
    """Get or initialize the OpenAI client."""
    if st.session_state["openai_client"] is None:
        try:
            api_key = st.secrets.get("openai_api_key", "")
            if api_key:
                st.session_state["openai_client"] = openai.OpenAI(api_key=api_key)
        except Exception:
            pass
    return st.session_state["openai_client"]


def get_ai_response(messages: List[Dict[str, str]], max_tokens: int = 4000, temperature: float = 0.4) -> str:
    """Get a response from OpenAI using the latest model."""
    client = get_openai_client()
    if not client:
        return "OpenAI API not configured. Add your openai_api_key to .streamlit/secrets.toml."
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI request failed: {e}"


# ══════════════════════════════════════════════════════════════════
# HELPER: shorthand for profile
# ══════════════════════════════════════════════════════════════════

def profile():
    return st.session_state["product_profile"]


def gap_statuses():
    return st.session_state["gap_statuses"]


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
# SIDEBAR NAVIGATION
# ══════════════════════════════════════════════════════════════════

TABS = [
    ("Dashboard", "Dashboard"),
    ("Product Profile", "Product Profile"),
    ("Requirements Matrix", "Requirements Matrix"),
    ("Gap Analysis", "Gap Analysis"),
    ("Standards Library", "Standards Library"),
    ("AI Advisor", "AI Advisor"),
]

with st.sidebar:
    st.markdown("### Navigation")
    for label, tab_id in TABS:
        if st.button(label, key=f"nav_{tab_id}", use_container_width=True,
                     type="primary" if st.session_state["active_tab"] == tab_id else "secondary"):
            st.session_state["active_tab"] = tab_id
            st.rerun()

    st.divider()
    st.caption("ISO 13485 | FDA 21 CFR 820")
    st.caption("EU MDR | UK MDR | ANVISA")
    st.caption("COFEPRIS | INVIMA | ANMAT")


# ══════════════════════════════════════════════════════════════════
# TAB: DASHBOARD
# ══════════════════════════════════════════════════════════════════

def render_dashboard():
    p = profile()
    gs = get_gap_stats(gap_statuses())
    profile_complete = bool(p["name"] and p["target_markets"])
    markets_selected = len(p["target_markets"])
    applicable = get_applicable_standards(p["target_markets"])

    # Hero
    st.markdown("""
    <div class="hero">
        <h2>Regulatory Intelligence Center</h2>
        <p>Your unified compliance hub for ISO 13485 and multi-market medical device regulatory requirements across the US, EU, UK, and Latin America.</p>
    </div>
    """, unsafe_allow_html=True)

    # Quick Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Product Profile", "Configured" if profile_complete else "Not Set",
                   help=p["name"] if profile_complete else "Configure in Product Profile tab")
    with c2:
        flags = " ".join(MARKETS[m]["flag"] for m in p["target_markets"]) if p["target_markets"] else "None"
        st.metric("Target Markets", markets_selected, help=flags)
    with c3:
        st.metric("Applicable Standards", len(applicable))
    with c4:
        st.metric("Gap Analysis", f"{gs['compliant']}/{gs['total']}",
                   help=f"{gs['non_compliant']} gaps | {gs['partial']} partial | {gs['not_assessed']} unassessed")

    st.markdown("---")

    # Quick Actions
    st.subheader("Quick Actions")
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        st.markdown("**Configure Product Profile**")
        st.caption("Define your device characteristics, classification, and target markets.")
        if st.button("Set Up Profile", key="qa_profile"):
            st.session_state["active_tab"] = "Product Profile"
            st.rerun()
    with qa2:
        st.markdown("**View Requirements Matrix**")
        st.caption("Testing, documentation, and submission requirements by market.")
        if st.button("View Matrix", key="qa_matrix"):
            st.session_state["active_tab"] = "Requirements Matrix"
            st.rerun()
    with qa3:
        st.markdown("**Run Gap Analysis**")
        st.caption("Assess your QMS against ISO 13485 clause-by-clause.")
        if st.button("Start Analysis", key="qa_gap"):
            st.session_state["active_tab"] = "Gap Analysis"
            st.rerun()
    with qa4:
        st.markdown("**Ask the AI Advisor**")
        st.caption("Get instant answers on regulatory questions and pathways.")
        if st.button("Open Chat", key="qa_chat"):
            st.session_state["active_tab"] = "AI Advisor"
            st.rerun()

    st.markdown("---")

    # Market Overview
    st.subheader("Market Overview")
    cols = st.columns(len(MARKETS))
    for i, (code, market) in enumerate(MARKETS.items()):
        with cols[i]:
            active = code in p["target_markets"]
            st.markdown(f"**{market['flag']} {market['name']}**")
            st.caption(market["agency"])
            if active:
                st.success("Active Market", icon=None)


# ══════════════════════════════════════════════════════════════════
# TAB: PRODUCT PROFILE
# ══════════════════════════════════════════════════════════════════

def render_product_profile():
    st.header("Product Profile")
    p = profile()

    # Device Information
    with st.container(border=True):
        st.subheader("Device Information")
        c1, c2 = st.columns(2)
        with c1:
            p["name"] = st.text_input("Device Name", value=p["name"], placeholder="e.g., WoundSeal Pro Bandage System")
        with c2:
            p["predicate_device"] = st.text_input("Predicate Device (510(k))", value=p["predicate_device"], placeholder="e.g., K123456")
        p["description"] = st.text_area("Device Description", value=p["description"], placeholder="Brief description of the device, its components, and function...", height=80)
        p["intended_use"] = st.text_area("Intended Use / Indications for Use", value=p["intended_use"], placeholder="The device is intended for...", height=80)

    # Classification
    with st.container(border=True):
        st.subheader("Classification")
        c1, c2 = st.columns(2)
        with c1:
            us_options = ["", "Class I", "Class I (510(k) required)", "Class II", "Class II (De Novo)"]
            us_labels = ["Select...", "Class I - Low Risk", "Class I - 510(k) Required", "Class II - Moderate Risk (510(k))", "Class II - De Novo"]
            idx = us_options.index(p["class_us"]) if p["class_us"] in us_options else 0
            p["class_us"] = st.selectbox("US FDA Classification", us_options, index=idx, format_func=lambda x: us_labels[us_options.index(x)])
        with c2:
            eu_options = ["", "Class I", "Class I (sterile)", "Class I (measuring)", "Class I (reusable surgical)", "Class IIa", "Class IIb"]
            eu_labels = ["Select...", "Class I", "Class I - Sterile", "Class I - Measuring Function", "Class I - Reusable Surgical", "Class IIa", "Class IIb"]
            idx = eu_options.index(p["class_eu"]) if p["class_eu"] in eu_options else 0
            p["class_eu"] = st.selectbox("EU MDR Classification", eu_options, index=idx, format_func=lambda x: eu_labels[eu_options.index(x)])

    # Device Characteristics
    with st.container(border=True):
        st.subheader("Device Characteristics")
        c1, c2 = st.columns(2)
        with c1:
            contact_options = ["", "none", "intact-skin", "mucosal-membrane", "breached-skin", "blood-path-indirect", "blood-contact", "tissue-bone", "implant"]
            contact_labels = ["Select...", "No patient contact", "Intact skin surface", "Mucosal membrane", "Breached/compromised skin", "Blood path - indirect", "Blood contacting", "Tissue/bone contact", "Implant"]
            idx = contact_options.index(p["contact_type"]) if p["contact_type"] in contact_options else 0
            p["contact_type"] = st.selectbox("Patient Contact Type", contact_options, index=idx, format_func=lambda x: contact_labels[contact_options.index(x)])
        with c2:
            dur_options = ["", "limited", "prolonged", "permanent"]
            dur_labels = ["Select...", "Limited (< 24 hours)", "Prolonged (24 hrs - 30 days)", "Permanent (> 30 days)"]
            idx = dur_options.index(p["contact_duration"]) if p["contact_duration"] in dur_options else 0
            p["contact_duration"] = st.selectbox("Contact Duration", dur_options, index=idx, format_func=lambda x: dur_labels[dur_options.index(x)])

        c1, c2, c3 = st.columns(3)
        with c1:
            p["sterile"] = st.toggle("Sterile Device", value=p["sterile"])
        with c2:
            p["has_software"] = st.toggle("Contains Software", value=p["has_software"])
        with c3:
            p["is_electrical"] = st.toggle("Electrical / Electronic", value=p["is_electrical"])

        if p["sterile"]:
            ster_options = ["", "EO", "gamma", "e-beam", "steam", "dry-heat", "other"]
            ster_labels = ["Select...", "Ethylene Oxide (EO)", "Gamma Radiation", "Electron Beam", "Steam (Autoclave)", "Dry Heat", "Other"]
            idx = ster_options.index(p["sterilization_method"]) if p["sterilization_method"] in ster_options else 0
            p["sterilization_method"] = st.selectbox("Sterilization Method", ster_options, index=idx, format_func=lambda x: ster_labels[ster_options.index(x)])

        if p["has_software"]:
            sw_options = ["", "A", "B", "C"]
            sw_labels = ["Select...", "Class A - No injury or damage to health", "Class B - Non-serious injury", "Class C - Death or serious injury possible"]
            idx = sw_options.index(p["software_safety_class"]) if p["software_safety_class"] in sw_options else 0
            p["software_safety_class"] = st.selectbox("Software Safety Classification (IEC 62304)", sw_options, index=idx, format_func=lambda x: sw_labels[sw_options.index(x)])

    # Target Markets
    with st.container(border=True):
        st.subheader("Target Markets")
        st.caption("Select all markets where you intend to sell this device:")
        cols = st.columns(len(MARKETS))
        for i, (code, market) in enumerate(MARKETS.items()):
            with cols[i]:
                active = code in p["target_markets"]
                if st.checkbox(f"{market['flag']} {market['name']}", value=active, key=f"market_{code}"):
                    if code not in p["target_markets"]:
                        p["target_markets"].append(code)
                else:
                    if code in p["target_markets"]:
                        p["target_markets"].remove(code)

    st.session_state["product_profile"] = p


# ══════════════════════════════════════════════════════════════════
# TAB: REQUIREMENTS MATRIX
# ══════════════════════════════════════════════════════════════════

def render_requirements_matrix():
    st.header("Requirements Matrix")
    p = profile()

    if not p["name"]:
        st.warning("Configure your Product Profile first for tailored requirements. Showing general requirements for all markets.")

    markets = p["target_markets"] if p["target_markets"] else list(MARKETS.keys())

    # Submission Pathways by Market
    with st.container(border=True):
        st.subheader("Submission Pathways by Market")
        rows = []
        for mkt in markets:
            info = get_classification_info(mkt, p)
            if not info:
                continue
            # Determine class key for display
            if mkt == "EU":
                class_key = p.get("class_eu") or "Class IIa"
            else:
                raw = p.get("class_us", "")
                if "Class II" in raw:
                    class_key = "Class II"
                elif "Class I" in raw:
                    class_key = "Class I"
                else:
                    class_key = "Class II"
            rows.append({
                "Market": f"{MARKETS[mkt]['flag']} {MARKETS[mkt]['agency']}",
                "Class": class_key,
                "Pathway": info["pathway"],
                "QMS Requirement": info["qsr"],
                "Timeline": info["timeline"],
                "Establishment": info["establishment"],
            })
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # Testing Requirements
    with st.container(border=True):
        st.subheader("Testing Requirements")
        tests = get_applicable_tests(p)
        if tests:
            test_rows = []
            for t in tests:
                test_rows.append({
                    "Test": t["name"],
                    "Applicability": t["required"],
                    "Est. Duration": t["duration"],
                    "Status": "Pending",
                })
            df_tests = pd.DataFrame(test_rows)
            st.dataframe(df_tests, use_container_width=True, hide_index=True)

    # Applicable Standards
    with st.container(border=True):
        st.subheader("Applicable Standards")
        standards = get_applicable_standards(p["target_markets"])
        for key, std in standards:
            with st.expander(f"**{key}** - {std['title']}"):
                st.markdown(f"**Category:** :blue[{std['category']}]")
                st.write(std["summary"])
                market_flags = " ".join(MARKETS[m]["flag"] for m in std["applicableMarkets"] if m in MARKETS)
                st.caption(f"Markets: {market_flags}")


# ══════════════════════════════════════════════════════════════════
# TAB: GAP ANALYSIS
# ══════════════════════════════════════════════════════════════════

def render_gap_analysis():
    st.header("Gap Analysis")
    gs = get_gap_stats(gap_statuses())

    # Stats bar
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Items", gs["total"])
    c2.metric("Compliant", gs["compliant"])
    c3.metric("Partial", gs["partial"])
    c4.metric("Non-Compliant", gs["non_compliant"])
    c5.metric("Not Assessed", gs["not_assessed"])

    # Progress bar
    st.progress(gs["score"] / 100 if gs["score"] > 0 else 0, text=f"{gs['score']}% overall compliance score")

    # Checklist by Category
    categories = list(dict.fromkeys(item["category"] for item in GAP_ANALYSIS_ITEMS))

    for cat in categories:
        items = [item for item in GAP_ANALYSIS_ITEMS if item["category"] == cat]
        cat_compliant = sum(1 for i in items if gap_statuses().get(i["id"]) == "compliant")
        cat_total = len(items)

        with st.expander(f"**{cat}** ({cat_compliant}/{cat_total} compliant)", expanded=False):
            for item in items:
                col_label, col_btns = st.columns([3, 1])
                with col_label:
                    critical_mark = " :red[CRITICAL]" if item.get("critical") else ""
                    st.markdown(f"**{item['item']}**{critical_mark}")
                    st.caption(f"Clause {item['clause']}")
                with col_btns:
                    current = gap_statuses().get(item["id"])
                    options = ["Not assessed", "Compliant", "Partial", "Non-compliant"]
                    status_map = {
                        "Not assessed": None,
                        "Compliant": "compliant",
                        "Partial": "partial",
                        "Non-compliant": "non-compliant",
                    }
                    reverse_map = {v: k for k, v in status_map.items()}
                    current_label = reverse_map.get(current, "Not assessed")
                    new_label = st.selectbox(
                        "Status",
                        options,
                        index=options.index(current_label),
                        key=f"gap_{item['id']}",
                        label_visibility="collapsed",
                    )
                    new_status = status_map[new_label]
                    if new_status is not None:
                        st.session_state["gap_statuses"][item["id"]] = new_status
                    elif item["id"] in st.session_state["gap_statuses"]:
                        del st.session_state["gap_statuses"][item["id"]]


# ══════════════════════════════════════════════════════════════════
# TAB: STANDARDS LIBRARY
# ══════════════════════════════════════════════════════════════════

def render_standards_library():
    st.header("Standards Library")

    # Search across all knowledge
    search_query = st.text_input("Search standards knowledge base", placeholder="e.g., nebulizer, CAPA, anti-asphyxia, sling, software validation...")
    if search_query:
        results = search_standards_knowledge(search_query)
        if results:
            st.success(f"Found {len(results)} result(s) for **{search_query}**")
            for std_key, section, content in results[:20]:
                with st.expander(f"**{std_key}** - {section}"):
                    st.write(content[:2000])
        else:
            st.warning(f"No results found for '{search_query}'")

    # ISO 13485 Clause-Level Reference
    with st.container(border=True):
        st.subheader("ISO 13485:2016 - Clause-Level Reference")
        st.caption("Quality management systems - Requirements for regulatory purposes")

        for section in ISO_13485_CLAUSES:
            with st.expander(f"**Section {section['id']} - {section['title']}**"):
                for sub in section["subclauses"]:
                    critical = sub.get("critical", False)
                    badge = " :red[**CRITICAL**]" if critical else ""
                    st.markdown(f"`{sub['id']}` **{sub['title']}**{badge}")
                    st.caption(sub["summary"])
                    # Show related audit items
                    audit_items = get_audit_checklist_for_clause(sub["id"])
                    if audit_items:
                        st.caption(f"Audit checklist: {len(audit_items)} item(s)")
                    st.markdown("---")

    # Integrated Standards Deep Knowledge
    with st.container(border=True):
        st.subheader("Integrated Standards - Full Knowledge Base")
        st.caption(f"{len(DOCUMENT_REGISTRY)} source documents integrated with detailed requirements, test methods, and regulatory context")

        for std_key, knowledge in ALL_STANDARDS_KNOWLEDGE.items():
            doc_info = DOCUMENT_REGISTRY.get(std_key, {})
            with st.expander(f"**{std_key}** - {knowledge['title']}"):
                st.markdown(f"**Category:** {doc_info.get('category', 'N/A')}")
                st.markdown(f"**Edition:** {doc_info.get('edition', 'N/A')}")
                st.markdown(f"**Source:** `{doc_info.get('source_file', 'N/A')}`")
                st.markdown("---")
                st.markdown("**Scope:**")
                st.write(knowledge.get("scope", ""))
                if knowledge.get("classification"):
                    st.markdown("**Classification:**")
                    st.write(knowledge["classification"])
                if knowledge.get("regulatory_notes"):
                    st.markdown("**Regulatory Notes:**")
                    st.write(knowledge["regulatory_notes"])

                # Show key sections
                sections = knowledge.get("sections", {})
                if sections:
                    st.markdown("**Key Sections:**")
                    for sec_key, sec_val in sections.items():
                        if isinstance(sec_val, str):
                            with st.expander(f"{sec_key}"):
                                st.write(sec_val[:3000])
                        elif isinstance(sec_val, dict):
                            title = sec_val.get("title", sec_key)
                            content = sec_val.get("content", "")
                            if content:
                                with st.expander(f"{sec_key} - {title}"):
                                    st.write(content[:3000])

    # FDA Audit Checklist
    with st.container(border=True):
        st.subheader("FDA QSR/QMSR/ISO 13485 Internal Audit Checklist")
        st.caption(FDA_AUDIT_CHECKLIST["description"])

        for subsystem, data in FDA_AUDIT_CHECKLIST["subsystems"].items():
            if isinstance(data, dict) and "items" in data:
                items = data["items"]
                with st.expander(f"**{subsystem}** ({len(items)} items)"):
                    for item in items:
                        st.markdown(f"**#{item['item']}** - {item['detail']}")
                        refs = []
                        if item.get("iso_ref"):
                            refs.append(f"ISO: {item['iso_ref']}")
                        if item.get("qsr_ref"):
                            refs.append(f"QSR: {item['qsr_ref']}")
                        if refs:
                            st.caption(" | ".join(refs))
                        if item.get("auditor_notes"):
                            st.caption(f"Notes: {item['auditor_notes']}")
                        st.markdown("---")
            elif isinstance(data, dict) and "description" in data:
                with st.expander(f"**{subsystem}**"):
                    st.write(data["description"])
                    if "key_areas" in data:
                        for area in data["key_areas"]:
                            st.markdown(f"- {area}")

    # Standards Reference Library
    with st.container(border=True):
        st.subheader("Standards Reference Library")
        for key, std in STANDARDS_MAP.items():
            with st.expander(f"**{key}** - {std['title']}"):
                st.markdown(f"**Category:** {std['category']}")
                st.write(std["summary"])
                market_flags = " ".join(MARKETS[m]["flag"] for m in std["applicableMarkets"] if m in MARKETS)
                st.caption(f"Markets: {market_flags}")
                if std["deviceTypes"] != ["all"]:
                    st.caption(f"Device types: {', '.join(std['deviceTypes'])}")


# ══════════════════════════════════════════════════════════════════
# TAB: AI ADVISOR
# ══════════════════════════════════════════════════════════════════

def render_ai_advisor():
    st.header("AI Regulatory Advisor")
    p = profile()
    context_note = f"Context: **{p['name']}** profile is loaded." if p["name"] else "No product profile loaded - configure one for context-aware advice."
    st.caption(f"Ask about regulatory requirements, testing, submission pathways, standards interpretation, and more. {context_note}")

    # Display chat history
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Suggested questions (only when chat is empty)
    if not st.session_state["chat_messages"]:
        st.info("Try asking:")
        suggestions = [
            "What are the key differences between FDA 510(k) and EU MDR for Class II?",
            "What does ANVISA require for GMP compliance?",
            "List all biocompatibility tests for prolonged mucosal contact",
            "Compare submission timelines across all my target markets",
        ]
        cols = st.columns(2)
        for i, q in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(q, key=f"suggest_{i}", use_container_width=True):
                    st.session_state["_pending_question"] = q
                    st.rerun()

    # Handle pending suggested question
    if "_pending_question" in st.session_state:
        question = st.session_state.pop("_pending_question")
        _process_chat_message(question)
        st.rerun()

    # Chat input
    if user_input := st.chat_input("Ask about regulatory requirements, testing, pathways..."):
        _process_chat_message(user_input)
        st.rerun()


def _process_chat_message(user_input: str):
    """Process a chat message and get AI response."""
    st.session_state["chat_messages"].append({"role": "user", "content": user_input})

    system_prompt = build_system_prompt(profile(), gap_statuses())

    messages = [{"role": "system", "content": system_prompt}]
    # Include last 10 messages for context
    for msg in st.session_state["chat_messages"][-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    response = get_ai_response(messages, max_tokens=4000, temperature=0.4)
    st.session_state["chat_messages"].append({"role": "assistant", "content": response})


# ══════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ══════════════════════════════════════════════════════════════════

tab = st.session_state["active_tab"]

if tab == "Dashboard":
    render_dashboard()
elif tab == "Product Profile":
    render_product_profile()
elif tab == "Requirements Matrix":
    render_requirements_matrix()
elif tab == "Gap Analysis":
    render_gap_analysis()
elif tab == "Standards Library":
    render_standards_library()
elif tab == "AI Advisor":
    render_ai_advisor()
