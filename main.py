import streamlit as st
import os
import hashlib
from datetime import datetime
import requests
import json
import io
from pathlib import Path

# Try to get API key from Streamlit secrets
try:
    api_key = st.secrets["openai_api_key"]
except (FileNotFoundError, KeyError):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        st.error("No API key found. Please set up your OpenAI API key.")

# --- PAGE CONFIG ---
st.set_page_config(page_title="质量控制助手 | Quality Control Assistant", page_icon="🔍", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'language' not in st.session_state:
    st.session_state.language = "zh"  # Default to Mandarin
    
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Password hash (for "MPFvive8955@#@")
CORRECT_PASSWORD_HASH = "67f49a115b64c1a8affbc851384932f5e3e32a4bcc3a1bf3dd7933a48e4a11c3"

def verify_password(password):
    """Verify the password by comparing hashes"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == CORRECT_PASSWORD_HASH

# Translations dictionary (simplified for stability)
translations = {
    "app_title": {"zh": "质量控制助手", "en": "Quality Control Assistant"},
    "login": {"zh": "登录", "en": "Login"},
    "password": {"zh": "密码", "en": "Password"},
    "enter_password": {"zh": "请输入密码访问系统", "en": "Please enter password to access the system"},
    "incorrect_password": {"zh": "密码不正确，请重试", "en": "Incorrect password, please try again"},
    "login_button": {"zh": "登录系统", "en": "Login to System"},
    "logout": {"zh": "退出登录", "en": "Logout"},
    "welcome": {"zh": "欢迎使用宁海威斐质量控制系统", "en": "Welcome to Ninghai Vive Quality Control System"},
    "settings": {"zh": "设置", "en": "Settings"},
    "language": {"zh": "语言", "en": "Language"},
    "chinese": {"zh": "中文", "en": "Chinese"},
    "english": {"zh": "英文", "en": "English"},
    "temperature": {"zh": "温度", "en": "Temperature"},
    "max_response_length": {"zh": "最大响应长度", "en": "Maximum response length"},
    "new_conversation": {"zh": "新对话", "en": "New Conversation"},
    "download_conversation": {"zh": "下载对话", "en": "Download Conversation"},
    "chat_bot": {"zh": "聊天机器人 🤖", "en": "Chat Bot 🤖"},
    "document_translator": {"zh": "文档翻译 🔄", "en": "Document Translator 🔄"},
    "sop_library": {"zh": "SOP标准库 📚", "en": "SOP Library 📚"},
    "faq": {"zh": "常见问题 ❓", "en": "FAQ ❓"},
    "your_message": {"zh": "您的消息：", "en": "Your message:"},
    "send": {"zh": "发送", "en": "Send"},
    "thinking": {"zh": "思考中...", "en": "Thinking..."},
    "greeting": {"zh": "👋 您好！请尝试向我询问有关质量控制的问题：", "en": "👋 Hello! Please try asking me questions about quality control:"},
    "contact_alex": {"zh": "如有不确定，请联系质量经理Alex: alexander.popoff@vivehealth.com", "en": "When in doubt, contact Quality Manager Alex: alexander.popoff@vivehealth.com"},
    "by_vive": {"zh": "宁海威斐质量控制系统", "en": "Ninghai Vive Quality Control System"}
}

# Helper function to get translated text
def t(key):
    if key in translations:
        return translations[key][st.session_state.language]
    return key

# --- STYLES (simplified to avoid indentation errors) ---
st.markdown("""
<style>
/* Login styles */
.login-container { max-width: 400px; margin: 0 auto; padding: 2rem; border-radius: 10px; background-color: #f0f2f6; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; }
.login-title { font-size: 1.5rem; margin-bottom: 1.5rem; color: #0d47a1; }
.login-button { background-color: #4285F4; color: white; padding: 0.6rem 1.2rem; border-radius: 4px; border: none; font-size: 1rem; cursor: pointer; margin-top: 1rem; }
.login-error { color: #d32f2f; margin-top: 1rem; }

/* Chat styles */
.chat-message { padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; flex-direction: row; align-items: flex-start; }
.chat-message.user { background-color: #f0f2f6; }
.chat-message.assistant { background-color: #e3f2fd; }
.chat-message .avatar { width: 40px; height: 40px; margin-right: 1rem; border-radius: 50%; object-fit: cover; }
.chat-message .message { flex: 1; }

/* Other styles */
.floating-button { position: fixed; bottom: 20px; right: 20px; z-index: 1000; }
.sidebar .block-container { padding-top: 2rem; }
.language-toggle { margin-bottom: 1rem; }
.contact-alex { margin-top: 1rem; padding: 1rem; border-radius: 0.5rem; background-color: #ffebee; color: #c62828; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- DIRECT API CALL FUNCTION ---
def call_openai_api(messages, temperature, max_tokens, api_key):
    """Call OpenAI API directly using requests to avoid client issues"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Use the fine-tuned model specifically for quality control
    fine_tuned_model = "ft:gpt-4o-2024-08-06:vive-health-quality-department:1vive-quality-training-data:BQqHZoPo"
    
    payload = {
        "model": fine_tuned_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            # Fallback to standard gpt-4o
            fallback_payload = {
                "model": "gpt-4o",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            fallback_response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(fallback_payload)
            )
            
            if fallback_response.status_code == 200:
                return "(Fallback to standard GPT-4o) " + fallback_response.json()["choices"][0]["message"]["content"]
            else:
                error_message = f"API Error: {fallback_response.status_code} - {fallback_response.text}"
                raise Exception(error_message)
    except Exception as e:
        error_message = f"Error: {str(e)}"
        raise Exception(error_message)

# Create system message with SOP information
sop_system_message = """You are a Quality Control Assistant for Vive Health. Your primary role is to help the quality team in the Ninghai, China facility with questions about quality control procedures, especially regarding critical safety products.

Respond in the same language the user uses (Chinese or English). For Mandarin responses, use simple, clear language appropriate for manufacturing staff in Ninghai, China.

IMPORTANT: Always advise users to contact Quality Manager Alex at alexander.popoff@vivehealth.com if they are uncertain about any quality procedures or find any defects.
"""

# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
    st.markdown(f"""
    <div class="login-container">
        <div class="login-title">{t("welcome")}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create centered login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2>Quality Control Assistant</h2>
            <h3>质量控制助手</h3>
            <p>Please enter your password to access the system</p>
            <p>请输入密码访问系统</p>
        </div>
        """, unsafe_allow_html=True)
        
        password_input = st.text_input(
            t("password"), 
            type="password", 
            placeholder=t("enter_password"),
            help="请输入管理员提供的访问密码 | Please enter the access password provided by your administrator"
        )
        
        login_error = st.empty()  # Placeholder for login error
        
        if st.button(t("login_button") + " / 登录", use_container_width=True):
            try:
                if verify_password(password_input):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    login_error.error(t("incorrect_password") + " / 密码不正确，请重试")
            except Exception as e:
                login_error.error(f"Login error: {str(e)}")
                
        st.image("https://api.dicebear.com/7.x/bottts/svg?seed=gpt", width=150)
        
        # Version info at bottom of login page
        st.markdown("""
        <div style="position: fixed; bottom: 10px; left: 0; right: 0; text-align: center; font-size: 0.8em; color: #666;">
            Version 1.0.2 | Powered by Vive Health Quality Department<br>
            Using custom trained model: ft:gpt-4o:vive-health-quality-department:1vive-quality-training-data
        </div>
        """, unsafe_allow_html=True)
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title(t("settings"))
        
        # Language selector
        st.markdown('<div class="language-toggle">', unsafe_allow_html=True)
        lang_col1, lang_col2 = st.columns(2)
        with lang_col1:
            if st.button("🇨🇳 " + t("chinese"), use_container_width=True):
                st.session_state.language = "zh"
                st.rerun()
        with lang_col2:
            if st.button("🇺🇸 " + t("english"), use_container_width=True):
                st.session_state.language = "en"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display model info
        st.success("""
        **使用专门训练的质量控制模型 ✅**
        **Using fine-tuned quality control model ✅**
        """)
        
        # Temperature Slider
        temperature = st.slider(
            t("temperature"),
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1
        )
        
        # Maximum Length
        max_tokens = st.slider(
            t("max_response_length"),
            min_value=256,
            max_value=4096,
            value=1024,
            step=256
        )
        
        # Reset Conversation
        if st.button(t("new_conversation")):
            st.session_state.messages = []
            st.rerun()
        
        # Download Conversation
        if st.session_state.messages:
            if st.button(t("download_conversation")):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"conversation_{timestamp}.txt"
                
                content = ""
                for msg in st.session_state.messages:
                    content += f"{msg['role'].title()}: {msg['content']}\n\n"
                
                st.download_button(
                    label=t("download_conversation"),
                    data=content,
                    file_name=filename,
                    mime="text/plain"
                )
        
        # Logout button
        if st.button(t("logout"), type="primary"):
            st.session_state.authenticated = False
            st.rerun()

        st.markdown("---")
        st.markdown(t("by_vive"))

    # --- MAIN TABS ---
    # Create tabs first
    tabs = st.tabs([t("chat_bot"), t("sop_library"), t("faq")])
    
    # Tab 1: Chat Bot
    with tabs[0]:
        st.header(t("app_title") + " 🤖")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.container():
                st.markdown(f"""
                <div class="chat-message {message['role']}">
                    <img class="avatar" src="{'https://api.dicebear.com/7.x/bottts/svg?seed=gpt' if message['role'] == 'assistant' else 'https://api.dicebear.com/7.x/personas/svg?seed=user'}" />
                    <div class="message">
                        <p>{message['content']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Input area
        with st.container():
            user_input = st.text_area(t("your_message"), key="user_input", height=100)
            col1, col2 = st.columns([6, 1])
            
            with col2:
                submit_button = st.button(t("send"))
        
        # Process input
        if submit_button and user_input:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Check if API key is available
            if not api_key:
                st.error("API Key not configured. Please set up API key.")
            else:
                # Call OpenAI API
                try:
                    with st.spinner(t("thinking") + " / 思考中..."):
                        # Create messages for API
                        messages = [
                            {"role": "system", "content": sop_system_message}
                        ]
                        
                        # Add previous messages
                        for m in st.session_state.messages:
                            messages.append({"role": m["role"], "content": m["content"]})
                        
                        # API call with fine-tuned model
                        assistant_response = call_openai_api(
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            api_key=api_key
                        )
                        
                        # Add assistant response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                        
                        # Rerun to update UI
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Add sample questions for empty conversation
        if len(st.session_state.messages) == 0:
            st.info(t("greeting"))
            st.markdown(f'<div class="contact-alex">{t("contact_alex")}</div>', unsafe_allow_html=True)
    
    # Tab 2: SOP Library (simplified)
    with tabs[1]:
        st.header(t("sop_library") + " 📚")
        st.info("This is a simplified version of the SOP Library. The complete version will include all product specifications, testing procedures, and quality standards.")
        
        # Basic SOP content
        st.subheader("Product Groups:")
        st.markdown("""
        **GROUP 1: HIGH LOAD TRANSFER PRODUCTS**
        - S-3 Level, 408kg load, 20 min test, 0.1% AQL
        - Products: Transfer Sling, Transfer Blanket, Patient Lift Systems
        
        **GROUP 2: SUPPORT DEVICES**
        - S-2 Level, 0.1% AQL, 5 min test
        - Products: Car Assist Handle (137kg), Portable Stand Assist (115kg)
        
        **GROUP 3: PERSONAL SUPPORT ITEM**
        - S-1 Level, 0.1% AQL
        - Products: Transfer Harness, Transfer Belts
        """)
    
    # Tab 3: FAQ (simplified)
    with tabs[2]:
        st.header(t("faq") + " ❓")
        st.info("This is a simplified version of the FAQ section. The complete version will include detailed answers to common quality control questions.")
        
        # Basic FAQ content
        st.subheader("Common Questions:")
        st.markdown("""
        **What's the AQL standard for our safety products?**
        All critical safety products use an AQL of 0.1%, which essentially means zero defects are allowed for normal batch sizes.
        
        **What should I do if I find a defect during inspection?**
        If a defect is found: 1) Reinspect the lot at the next higher inspection level, 2) Contact material vendors if defects are from materials, 3) For high-risk products, no relaxation of standards is allowed - contact Alex immediately.
        
        **What does load testing being destructive mean?**
        Products that undergo load testing should not be sold after testing, as the structural integrity may be compromised even if no visible damage is present.
        """)
        
        # Add contact information
        st.markdown(f'<div class="contact-alex">{t("contact_alex")}</div>', unsafe_allow_html=True)

    # Add floating help button
    st.markdown("""
    <div class="floating-button">
        <a href="mailto:alexander.popoff@vivehealth.com" target="_blank" style="text-decoration:none;">
            <button style="background-color:#4285F4; color:white; border:none; padding:10px 15px; border-radius:50%; font-size:16px;">
                ?
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)
