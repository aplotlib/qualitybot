import streamlit as st
import os
import hashlib
import requests
import json
from datetime import datetime
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Quality Control Assistant | 质量控制助手",
    page_icon="🔍",
    layout="wide"
)

# --- SESSION STATE INITIALIZATION ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'language' not in st.session_state:
    st.session_state.language = "zh"  # Default to Mandarin

if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- PASSWORD VERIFICATION ---
CORRECT_PASSWORD_HASH = "67f49a115b64c1a8affbc851384932f5e3e32a4bcc3a1bf3dd7933a48e4a11c3"  # For "MPFvive8955@#@"

def verify_password(password):
    """Verify the password by comparing hashes"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == CORRECT_PASSWORD_HASH

# --- API KEY HANDLING ---
try:
    api_key = st.secrets["openai_api_key"]
except (FileNotFoundError, KeyError):
    api_key = os.environ.get("OPENAI_API_KEY", "")

# --- TRANSLATIONS ---
translations = {
    "zh": {
        "app_title": "质量控制助手",
        "welcome": "欢迎使用宁海威斐质量控制系统",
        "password": "密码",
        "enter_password": "请输入密码访问系统",
        "login_button": "登录系统",
        "incorrect_password": "密码不正确，请重试",
        "settings": "设置",
        "chinese": "中文",
        "english": "英文",
        "logout": "退出登录",
        "chat_bot": "聊天机器人 🤖",
        "sop_library": "SOP标准库 📚",
        "faq": "常见问题 ❓",
        "quality_assistant": "您的质量相关问题和任务的AI助手。",
        "your_message": "您的消息：",
        "send": "发送",
        "thinking": "思考中...",
        "by_vive": "宁海威斐质量控制系统",
        "new_conversation": "新对话",
        "model_info": "使用专门训练的质量控制模型"
    },
    "en": {
        "app_title": "Quality Control Assistant",
        "welcome": "Welcome to Ninghai Vive Quality Control System",
        "password": "Password",
        "enter_password": "Enter password to access the system",
        "login_button": "Login to System",
        "incorrect_password": "Incorrect password, please try again",
        "settings": "Settings",
        "chinese": "Chinese",
        "english": "English",
        "logout": "Logout",
        "chat_bot": "Chat Bot 🤖",
        "sop_library": "SOP Library 📚",
        "faq": "FAQ ❓",
        "quality_assistant": "Your AI assistant for quality-related questions and tasks.",
        "your_message": "Your message:",
        "send": "Send",
        "thinking": "Thinking...",
        "by_vive": "Ninghai Vive Quality Control System",
        "new_conversation": "New Conversation",
        "model_info": "Using fine-tuned quality control model"
    }
}

def t(key):
    """Get translated text based on current language"""
    lang = st.session_state.language
    if lang in translations and key in translations[lang]:
        return translations[lang][key]
    return key

# --- CSS STYLES ---
st.markdown("""
<style>
/* Main styles */
body {
    font-family: 'Arial', sans-serif;
}

/* Login page */
.login-container {
    max-width: 400px;
    margin: 40px auto;
    padding: 2rem;
    border-radius: 10px;
    background-color: #f0f2f6;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    text-align: center;
}

.login-title {
    margin-bottom: 1.5rem;
    color: #0d47a1;
}

/* Chat styles */
.chat-message {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: flex-start;
}

.chat-message.user {
    background-color: #f0f2f6;
}

.chat-message.assistant {
    background-color: #e3f2fd;
}

.chat-message .avatar {
    width: 40px;
    height: 40px;
    margin-right: 1rem;
    border-radius: 50%;
}

.chat-message .message {
    flex: 1;
}

/* Help button */
.help-button {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: #4285F4;
    color: white;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    z-index: 1000;
    text-decoration: none;
}

/* Mobile optimization */
@media (max-width: 768px) {
    .chat-message {
        padding: 0.8rem;
    }
    .chat-message .avatar {
        width: 30px;
        height: 30px;
    }
}
</style>
""", unsafe_allow_html=True)

# --- API FUNCTION ---
def call_openai_api(messages, temperature=0.7, max_tokens=1024):
    """Call OpenAI API with the fine-tuned model"""
    if not api_key:
        st.error("API Key not found. Please set it up in your environment.")
        return "Error: API Key not configured."
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Use the fine-tuned model
    fine_tuned_model = "ft:gpt-4o-2024-08-06:vive-health-quality-department:1vive-quality-training-data:BQqHZoPo"
    
    try:
        payload = {
            "model": fine_tuned_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        
        # If successful
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        
        # If model not found, try with standard GPT-4o
        if response.status_code == 404:
            st.warning("Fine-tuned model not available. Using GPT-4o instead.")
            fallback_payload = {
                "model": "gpt-4o",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            fallback_response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(fallback_payload),
                timeout=30
            )
            
            if fallback_response.status_code == 200:
                return "(Using GPT-4o) " + fallback_response.json()["choices"][0]["message"]["content"]
            else:
                return f"Error with fallback API call: {fallback_response.status_code}"
        
        return f"Error: {response.status_code} - {response.text}"
    
    except Exception as e:
        return f"Error: {str(e)}"

# --- LOGIN PAGE ---
if not st.session_state.authenticated:
    # Center the login content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-container">
            <h1>Quality Control Assistant</h1>
            <h2>质量控制助手</h2>
            <p style="margin-top: 20px; margin-bottom: 20px;">
                Welcome to Ninghai Vive Quality Control System<br>
                欢迎使用宁海威斐质量控制系统
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Two-column layout for login form
        login_col1, login_col2 = st.columns([3, 1])
        
        with login_col1:
            st.markdown(f"##### {t('password')} / Password")
            password = st.text_input(
                "输入密码 | Enter password", 
                type="password", 
                help="请输入管理员提供的访问密码 | Please enter the access password provided by your administrator",
                label_visibility="collapsed"
            )
        
        with login_col2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)  # Spacer
        
        # Login button with both languages
        if st.button("登录 | Login", use_container_width=True):
            if verify_password(password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密码不正确，请重试 | Incorrect password, please try again")
        
        # Login page footer with version info
        st.markdown("""
        <div style="text-align: center; margin-top: 30px;">
            <img src="https://api.dicebear.com/7.x/bottts/svg?seed=gpt" width="120" />
            <p style="margin-top: 20px; color: #666; font-size: 0.8em;">
                Version 1.0.2 | Vive Health Quality Department<br>
                Using custom trained model for Quality Control
            </p>
        </div>
        """, unsafe_allow_html=True)

else:
    # --- MAIN APPLICATION AFTER LOGIN ---
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"{t('settings')} | Settings")
        
        # Language selector
        st.subheader("Language | 语言")
        lang_col1, lang_col2 = st.columns(2)
        with lang_col1:
            if st.button("🇨🇳 中文", use_container_width=True):
                st.session_state.language = "zh"
                st.rerun()
        with lang_col2:
            if st.button("🇺🇸 English", use_container_width=True):
                st.session_state.language = "en"
                st.rerun()
        
        # Model information
        st.success(f"{t('model_info')} ✅")
        
        with st.expander("Model details | 模型详情"):
            st.code("ft:gpt-4o-2024-08-06:vive-health-quality-department:1vive-quality-training-data:BQqHZoPo")
        
        # Conversation controls
        if st.button(f"{t('new_conversation')} | New Conversation"):
            st.session_state.messages = []
            st.rerun()
        
        # Logout button
        if st.button(f"{t('logout')} | Logout", type="primary"):
            st.session_state.authenticated = False
            st.rerun()
        
        st.markdown("---")
        st.markdown(f"{t('by_vive')} | Ninghai Vive Quality Control System")
    
    # --- TABS ---
    tab1, tab2, tab3 = st.tabs([
        f"{t('chat_bot')} | Chat Bot", 
        f"{t('sop_library')} | SOP Library", 
        f"{t('faq')} | FAQ"
    ])
    
    # --- CHAT TAB ---
    with tab1:
        st.header(f"{t('app_title')} | Quality Control Assistant 🤖")
        st.markdown(f"{t('quality_assistant')}")
        
        # Display chat history
        for message in st.session_state.messages:
            avatar_url = "https://api.dicebear.com/7.x/bottts/svg?seed=gpt" if message["role"] == "assistant" else "https://api.dicebear.com/7.x/personas/svg?seed=user"
            
            st.markdown(f"""
            <div class="chat-message {message['role']}">
                <img class="avatar" src="{avatar_url}" />
                <div class="message">
                    <p>{message['content']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Input area
        user_input = st.text_area(f"{t('your_message')} | Your message:", height=100)
        
        # Send button
        if st.button(f"{t('send')} | Send", key="send_button"):
            if user_input:
                # Add user message to chat
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                with st.spinner(f"{t('thinking')} | Thinking..."):
                    # Basic system message
                    messages = [
                        {"role": "system", "content": "You are a Quality Control Assistant for Vive Health, helping the quality team in Ninghai, China with quality control procedures, especially for critical safety products."}
                    ]
                    
                    # Add conversation history
                    for msg in st.session_state.messages:
                        messages.append({"role": msg["role"], "content": msg["content"]})
                    
                    # Get response from API
                    assistant_response = call_openai_api(messages)
                    
                    # Add assistant response to chat
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    
                    # Refresh the UI
                    st.rerun()
        
        # Show greeting for empty chat
        if not st.session_state.messages:
            st.info("👋 Hello! Ask me questions about quality control procedures. | 您好！请向我询问有关质量控制程序的问题。")
            
            # Sample questions
            st.markdown("**Sample questions | 示例问题:**")
            st.markdown("- How do I test transfer slings? | 如何测试转移吊带？")
            st.markdown("- What is the sampling inspection level? | 抽样检验水平是什么？")
            st.markdown("- What should I do when I find defects? | 发现缺陷时应该怎么做？")
    
    # --- SOP LIBRARY TAB ---
    with tab2:
        st.header(f"{t('sop_library')} | SOP Library 📚")
        
        # Simple SOP library with tabs for different categories
        sop_types = st.radio(
            "Category | 类别",
            ["All | 全部", "Testing | 测试", "Inspection | 检验", "Materials | 材料"],
            horizontal=True
        )
        
        st.subheader("Product Groups | 产品组")
        
        with st.expander("GROUP 1: HIGH LOAD TRANSFER PRODUCTS | 第一组：高负载转移产品", expanded=True):
            st.markdown("**S-3 Level, 408kg load, 20 min test, 0.1% AQL | S-3级别, 408kg负载, 20分钟测试, 0.1% AQL**")
            st.markdown("""
            - Transfer Sling (MI487/LVA2056BLK) | 转移吊带
            - Transfer Blanket Small (MI621/MOB1022WHTLS) | 小号转移床单
            - Transfer Blanket with Handles (MI624/LVA2000) | 带把手转移床单
            - Lift Sling with Opening (MI645/LVA2057BLU) | 开孔提升吊带
            - Wooden Transfer Board (RHB1037WOOD/L) | 木质转移板
            - Core Hydraulic Patient Lift (MOB1120) | 核心液压病人升降机
            - Hydraulic Patient Lift Systems (MOB1068PMP, MOB1068SLG) | 液压病人升降系统
            - Transfer Blanket Large (MI621-L/MOB1022WHTL) | 大号转移床单
            """)
        
        with st.expander("GROUP 2: SUPPORT DEVICES | 第二组：支撑设备"):
            st.markdown("**S-2 Level, 0.1% AQL, 5 min test | S-2级别, 0.1% AQL, 5分钟测试**")
            st.markdown("""
            - Car Assist Handle (MI474/LVA2098) - 137kg | 汽车辅助拉手
            - Portable Stand Assist (MI524-LVA3016BLK) - 115kg | 便携式站立辅助器
            """)
        
        with st.expander("GROUP 3: PERSONAL SUPPORT ITEMS | 第三组：个人支撑物品"):
            st.markdown("**S-1 Level, 0.1% AQL | S-1级别, 0.1% AQL**")
            st.markdown("""
            - Transfer Harness (MI471/RHB1054) - 181kg, 5 min - 4 handles each test | 转移背带
            - All Transfer Belts - 225kg, 5 min | 所有转移带
            """)
        
        # Material testing section
        if sop_types in ["All | 全部", "Materials | 材料"]:
            st.subheader("Material Testing | 材料测试")
            
            material_data = {
                "Material | 材料": ["Straps/Webbing | 织带/带子", "Hardware | 硬件", "Fabric/Mesh | 面料/网布"],
                "Test Method | 测试方法": ["Visual + 120% load test | 目视 + 120%负载测试", 
                                         "Visual + 120% load test | 目视 + 120%负载测试", 
                                         "Visual + 100% load test | 目视 + 100%负载测试"],
                "Acceptance | 接受标准": ["No tears/deformation | 无撕裂/变形", 
                                       "No breakage | 无断裂", 
                                       "No tears | 无撕裂"]
            }
            
            st.table(pd.DataFrame(material_data))
    
    # --- FAQ TAB ---
    with tab3:
        st.header(f"{t('faq')} | FAQ ❓")
        
        with st.expander("What load testing is required for transfer slings? | 转移吊带需要什么负载测试？", expanded=True):
            st.markdown("""
            **English:** Transfer slings (MI487/LVA2056BLK) require S-3 level inspection with a 408kg static load test for 20 minutes. The AQL is 0.1%, which essentially means zero defects for normal batch sizes.
            
            **中文:** 转移吊带（MI487/LVA2056BLK）需要S-3级别检验，进行408kg静态负载测试，持续20分钟。AQL为0.1%，这对于正常批量大小实际上意味着零缺陷。
            """)
        
        with st.expander("What should I do if I find a defect during inspection? | 如果在检验过程中发现缺陷，我应该怎么做？"):
            st.markdown("""
            **English:** If a defect is found:
            1. Reinspect the lot at the next higher inspection level (e.g., S-2 becomes S-3).
            2. Contact material vendors if defects are traced to incoming materials.
            3. For high-risk products like patient lift slings, no relaxation of standards is allowed.
            4. For lower-risk products, if defects are isolated and safe units can be confirmed, some adjustments may be acceptable.
            
            Always inform Quality Manager Alex if you're uncertain.
            
            **中文:** 如果发现缺陷：
            1. 使用更高检验水平重新检验批次（例如，S-2变为S-3）。
            2. 如果发现问题源于原材料而非MPF工艺，联系材料供应商。
            3. 对于高风险产品如病人升降吊带，不允许放宽标准。
            4. 对于较低风险产品，如果缺陷是孤立的且能确认安全单元，在咨询Alex后可能接受一些调整。
            
            如有不确定，请务必通知质量经理Alex。
            """)
        
        with st.expander("What does '120% load test' mean? | '120%负载测试'是什么意思？"):
            st.markdown("""
            **English:** The 120% load test refers to testing materials at 120% of the advertised maximum weight for the product. For example, if a product's advertised maximum weight is 200kg, the materials should be tested at 240kg.
            
            **中文:** 120%负载测试是指在产品宣传的最大承重的120%下测试材料。例如，如果产品宣传的最大承重是200kg，则材料应在240kg下测试。
            """)
        
        with st.expander("What are the material testing requirements before production? | 生产前的材料测试要求是什么？"):
            st.markdown("""
            **English:** Before production, test critical components using the same sampling level as the final product:
            1. Straps/Webbing: Visual + 120% load test with no tears/deformation allowed.
            2. Hardware: Visual + 120% load test with no breakage allowed.
            3. Fabric/Mesh: Visual + 100% load test with no tears allowed.
            
            **中文:** 生产前，使用与最终产品相同的抽样水平测试关键组件：
            1. 织带/带子：目视+120%负载测试，不允许有撕裂/变形。
            2. 硬件：目视+120%负载测试，不允许有断裂。
            3. 面料/网布：目视+100%负载测试，不允许有撕裂。
            """)
    
    # Contact button
    st.markdown("""
    <a href="mailto:alexander.popoff@vivehealth.com" class="help-button">?</a>
    """, unsafe_allow_html=True)
