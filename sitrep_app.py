# sitrep_app.py
# Project SITREP — Internal Resource Hub AI Assistant
# Run with:  streamlit run sitrep_app.py
# Embed in Google Sites via: Insert → Embed → paste the app URL

import streamlit as st
import openai

from src.sitrep_knowledge import (
    SITREP_SYSTEM_PROMPT,
    get_sitrep_context,
)

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (centered layout keeps it clean inside an iframe)
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="SITREP Assistant",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS — lightweight dark-card style, friendly for iframe embedding
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'DM Sans', sans-serif;
}
.block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
header[data-testid="stHeader"] { display: none; }

.sitrep-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #0a1628 100%);
    border-radius: 12px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 1.2rem;
}
.sitrep-logo {
    width: 38px; height: 38px; border-radius: 8px;
    background: linear-gradient(135deg, #38bdf8, #3b82f6);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; font-weight: 700; color: #fff;
    flex-shrink: 0;
}
.sitrep-title { color: #f1f5f9; font-size: 17px; font-weight: 700; line-height: 1.2; }
.sitrep-subtitle { color: #94a3b8; font-size: 12px; margin-top: 2px; }

.suggested-btn button {
    background: #f0f7ff !important;
    border: 1px solid #bfdbfe !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    color: #1e40af !important;
    text-align: left !important;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────────────────────

def _init():
    defaults = {
        "sitrep_messages": [],
        "sitrep_extra_kb": "",   # admin-added extra knowledge base content
        "admin_unlocked": False,
        "openai_client": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ──────────────────────────────────────────────────────────────────────────────
# OPENAI CLIENT
# ──────────────────────────────────────────────────────────────────────────────

def _get_client():
    if st.session_state["openai_client"] is None:
        try:
            api_key = st.secrets.get("openai_api_key", "")
            if api_key:
                st.session_state["openai_client"] = openai.OpenAI(api_key=api_key)
        except Exception:
            pass
    return st.session_state["openai_client"]

def _ai_response(user_input: str) -> str:
    client = _get_client()
    if not client:
        return (
            "The AI assistant isn't configured yet. "
            "Please add `openai_api_key` to `.streamlit/secrets.toml`."
        )
    kb = get_sitrep_context(st.session_state["sitrep_extra_kb"])
    system = (
        SITREP_SYSTEM_PROMPT
        + "\n\n--- KNOWLEDGE BASE ---\n"
        + kb
        + "\n--- END KNOWLEDGE BASE ---"
    )
    messages = [{"role": "system", "content": system}]
    for m in st.session_state["sitrep_messages"][-12:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_input})
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",   # fast + cheap for internal Q&A
            messages=messages,
            max_tokens=1200,
            temperature=0.3,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Request failed: {e}"

# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="sitrep-header">
    <div class="sitrep-logo">S</div>
    <div>
        <div class="sitrep-title">SITREP Assistant</div>
        <div class="sitrep-subtitle">Your internal resource hub AI — ask me anything</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# TABS:  Chat  |  Admin
# ──────────────────────────────────────────────────────────────────────────────

tab_chat, tab_admin = st.tabs(["Chat", "Admin / Knowledge Base"])

# ── CHAT TAB ──────────────────────────────────────────────────────────────────
with tab_chat:

    # Show message history
    for msg in st.session_state["sitrep_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Empty state — suggested questions
    if not st.session_state["sitrep_messages"]:
        st.markdown("**Try asking:**")
        suggestions = [
            "What is Project SITREP?",
            "How do I submit a help desk ticket?",
            "Where can I find the team directory?",
            "What's the time-off policy?",
            "What tools do we use and how do I get access?",
        ]
        cols = st.columns(2)
        for i, q in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(q, key=f"sugg_{i}", use_container_width=True):
                    st.session_state["sitrep_messages"].append(
                        {"role": "user", "content": q}
                    )
                    with st.spinner("Thinking..."):
                        answer = _ai_response(q)
                    st.session_state["sitrep_messages"].append(
                        {"role": "assistant", "content": answer}
                    )
                    st.rerun()

    # Chat input
    if user_input := st.chat_input("Ask about SITREP resources, policies, tools..."):
        st.session_state["sitrep_messages"].append(
            {"role": "user", "content": user_input}
        )
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = _ai_response(user_input)
            st.markdown(answer)
        st.session_state["sitrep_messages"].append(
            {"role": "assistant", "content": answer}
        )

    # Clear chat button
    if st.session_state["sitrep_messages"]:
        if st.button("Clear conversation", key="clear_chat"):
            st.session_state["sitrep_messages"] = []
            st.rerun()


# ── ADMIN TAB ─────────────────────────────────────────────────────────────────
with tab_admin:
    st.markdown("### Knowledge Base Management")
    st.caption(
        "Paste content from your Google Intranet (Google Sites) pages here. "
        "The AI will use this as its source of truth when answering questions. "
        "Changes here persist for the current session — to make them permanent, "
        "update `src/sitrep_knowledge.py` and redeploy."
    )

    # Simple admin toggle (replace with a real password check if needed)
    if not st.session_state["admin_unlocked"]:
        admin_pw = st.text_input("Admin password", type="password", key="admin_pw_input")
        try:
            expected = st.secrets.get("sitrep_admin_password", "FDSwVSTr8595%$%")
        except Exception:
            expected = "sitrep2024"
        if st.button("Unlock", key="unlock_admin"):
            if admin_pw == expected:
                st.session_state["admin_unlocked"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    else:
        st.success("Admin mode active")

        st.markdown("#### Paste Additional Google Sites Content")
        st.caption(
            "Copy content directly from your Google Intranet pages and paste it below. "
            "This supplements the base knowledge in `src/sitrep_knowledge.py`."
        )
        extra = st.text_area(
            "Additional knowledge base content",
            value=st.session_state["sitrep_extra_kb"],
            height=300,
            placeholder=(
                "Paste Google Sites page content here.\n\n"
                "Example:\n"
                "=== Benefits Overview ===\n"
                "Employees receive health, dental, and vision coverage starting Day 1...\n"
            ),
            label_visibility="collapsed",
            key="admin_extra_kb",
        )
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Save to session", key="save_kb", type="primary"):
                st.session_state["sitrep_extra_kb"] = extra
                st.success("Knowledge base updated for this session.")
        with col2:
            st.caption(
                "To persist permanently: copy this text into the "
                "`SITREP_KNOWLEDGE_BASE` variable in `src/sitrep_knowledge.py`."
            )

        st.divider()
        st.markdown("#### How to pull content from Google Sites")
        st.markdown("""
1. Open your Google Intranet page in a browser
2. Select all text on the page (`Ctrl+A` / `Cmd+A`) — or copy section by section
3. Paste into the text area above and click **Save to session**
4. To make it permanent, paste into the matching section in `src/sitrep_knowledge.py`

**For richer extraction:** Use **Google Sites → More options (⋮) → Download as PDF**,
then copy text from the PDF, or ask your admin to export the site content.

**Google Sites API (advanced):** If you have a Google Workspace admin account,
you can use the [Google Sites API](https://developers.google.com/sites/api/reference)
to programmatically export page content.
        """)

        st.divider()
        st.markdown("#### Embed in Google Sites")
        st.markdown("""
**To embed this chatbot in your Google Intranet:**

1. Deploy this Streamlit app to [Streamlit Community Cloud](https://streamlit.io/cloud)
   - Point it to `sitrep_app.py` (not `main.py`)
   - Add your `openai_api_key` as a secret in the deployment settings
2. Copy your app URL (e.g. `https://yourapp.streamlit.app`)
3. In Google Sites:
   - Edit your SITREP page
   - Click **Insert → Embed**
   - Paste the Streamlit URL
   - Resize the embed block to your preferred height (600–800px recommended)
4. Publish the Google Sites page

> **Note:** The `.streamlit/config.toml` in this repo has `enableCORS = false`
> and `enableXsrfProtection = false` which is required for iframe embedding.
        """)

        if st.button("Lock admin", key="lock_admin"):
            st.session_state["admin_unlocked"] = False
            st.rerun()
