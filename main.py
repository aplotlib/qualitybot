import streamlit as st
import os
from datetime import datetime
import requests
import json

# --- API KEY HANDLING ---
# Try to get API key from Streamlit secrets
try:
    api_key = st.secrets["openai_api_key"]
except (FileNotFoundError, KeyError):
    # If not found in secrets, use environment variable if available
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # If not found anywhere, show error
    if not api_key:
        st.error("No API key found. Please set up your OpenAI API key in Streamlit secrets or as an environment variable.")

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Vive Quality Bot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Main Container Styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Header Styling */
    .custom-header {
        background-color: #1E88E5;
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Chat Message Styling */
    .chat-message {
        padding: 1.5rem; 
        border-radius: 10px; 
        margin-bottom: 1.5rem; 
        display: flex;
        align-items: flex-start;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        animation: fadeIn 0.5s;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .chat-message.user {
        background-color: #f5f7fa;
        border-left: 5px solid #1E88E5;
    }
    
    .chat-message.assistant {
        background-color: #e8f4fd;
        border-left: 5px solid #43A047;
    }
    
    .chat-message .avatar {
        width: 50px;
        height: 50px;
        margin-right: 1rem;
        border-radius: 50%;
        border: 2px solid #fff;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    
    .chat-message .message {
        flex: 1;
        line-height: 1.6;
    }
    
    /* Input Area Styling */
    .input-area {
        background-color: #fff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        margin-top: 2rem;
    }
    
    .stTextInput input, .stTextArea textarea {
        padding: 0.75rem !important;
        font-size: 1rem !important;
        border-radius: 8px !important;
        border: 1px solid #ddd !important;
    }
    
    /* Button Styling */
    .stButton > button {
        background-color: #1E88E5;
        color: white;
        padding: 0.25rem 1.75rem;
        font-weight: 600;
        border-radius: 10px;
        border: none;
        width: 100%;
        height: 1.5rem;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #1565C0;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Sidebar Styling */
    .sidebar .block-container {
        padding-top: 2rem;
        background-color: #f5f7fa;
    }
    
    .sidebar h1 {
        margin-bottom: 2rem;
        color: #1E88E5;
        font-size: 1.5rem;
    }
    
    /* Feature Card Styling */
    .feature-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        border-left: 4px solid #43A047;
    }
    
    /* Info Cards Styling */
    .info-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .info-card {
        background-color: white;
        padding: 1.2rem;
        border-radius: 8px;
        flex: 1;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        transition: transform 0.3s;
    }
    
    .info-card:hover {
        transform: translateY(-5px);
    }
    
    /* Footer Styling */
    .footer {
        text-align: center;
        padding: 1rem;
        margin-top: 2rem;
        color: #666;
        font-size: 0.9rem;
    }
    
    /* Vive Logo */
    .vive-logo {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Fix for mobile responsiveness */
    @media (max-width: 768px) {
        .info-container {
            flex-direction: column;
        }
        
        .custom-header {
            padding: 1rem;
        }
    }
    
    /* Fallback if tooltips don't work correctly */
    .tooltip-container {
        margin-bottom: 0.5rem;
    }
    
    .tooltip-text {
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.25rem;
        margin-bottom: 0.5rem;
    }
    
    /* Model recommendation banner */
    .model-recommendation {
        background-color: #FFF3CD;
        border-left: 4px solid #FFC107;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 8px;
        font-size: 0.9rem;
    }
    
    /* Models info card */
    .models-info-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        border-left: 4px solid #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# --- DIRECT API CALL FUNCTION ---
def call_openai_api(messages, model, temperature, max_tokens, api_key):
    """Call OpenAI API directly using requests to avoid client issues"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=60  # Add timeout to prevent hanging requests
        )
        
        response.raise_for_status()  # Raise exception for HTTP errors
        
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        error_message = f"API Request Error: {str(e)}"
        raise Exception(error_message)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        error_message = f"API Response Processing Error: {str(e)}"
        raise Exception(error_message)
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
        raise Exception(error_message)

# --- SYSTEM MESSAGE CONTENT ---
SYSTEM_MESSAGE = """You are Quality Bot, an AI assistant exclusively for internal Vive Health employee use. You provide knowledgeable, accurate, and helpful responses about Vive Health's quality assurance, quality control, compliance processes, and related inquiries. You have access to information from Vive Health's quality training program and can assist employees with quality-related questions.

Key Personnel Information:
- Alexander Popoff is the Quality Manager at Vive Health (email: alexander.popoff@vivehealth.com)
- Jessica Marshall is the Compliance Coordinator (email: jessica.marshall@vivehealth.com)

Company Quality Status:
- Vive Health is currently pursuing ISO 13485 certification and is under audit
- The company currently meets or exceeds all ISO 13485 requirements
- We follow a structured AQL (Acceptable Quality Limit) inspection process with specific thresholds for minor, major, and critical defects
- Our current standard AQL is 2.5% for major defects, with stricter requirements for safety-critical products

Quality Processes:
- We classify defects as Minor (up to 4% allowed), Major (2.5% AQL), and Critical (0% allowed)
- Safety devices like lift slings receive more rigorous testing with stricter AQL requirements (≤1%)
- We use the 7 Quality Tools for problem-solving: Fishbone Diagrams, Control Charts, Histograms, Pareto Charts, Scatter Diagrams, Check Sheets, and Flowcharts
- We follow the Kaizen philosophy of continuous improvement through small daily changes
- We use MIL-STD-105 sampling for quality inspections with defined AQLs

Product Quality Examples:
- CSH1014 Gel Seat Cushion: Previous quality issues with vacuum sealing creating compression defects
- SUP3072 OA Offloader Elite: Addressed issues with pins breaking through design improvements
- We prioritize real-world testing beyond short-term validation to ensure product quality"""

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "settings" not in st.session_state:
    st.session_state.settings = {
        "model": "gpt-4o",  # Default to GPT-4o as recommended
        "temperature": 0.5,
        "max_tokens": 2048
    }

# --- SIDEBAR ---
with st.sidebar:
    
    st.markdown("""
    """, unsafe_allow_html=True)
    
    st.title("Quality Bot Settings")
    
    # API Key Status
    if api_key:
        st.success("API Key connected ✅")
    else:
        st.error("API Key not configured ⚠️")
        st.info("Please contact IT to set up the API key for this application.")
    
    # Model Selection - Default to GPT-4o with recommendation
    st.markdown("""
    <div class="model-recommendation">
        <strong>⭐ Recommended:</strong> GPT-4o provides the best overall results for most quality inquiries.
    </div>
    """, unsafe_allow_html=True)
    
    model_options = ["gpt-4o", "gpt-3.5-turbo", "gpt-4-turbo"]
    model = st.selectbox(
        "Model",
        options=model_options,
        index=model_options.index(st.session_state.settings["model"]) if st.session_state.settings["model"] in model_options else 0
    )
    st.session_state.settings["model"] = model
    
    # Temperature with tooltip and explanation
    st.subheader("Temperature")
    st.markdown('<div class="tooltip-text">Controls how creative or focused the responses are.</div>', unsafe_allow_html=True)
    
    # Temperature descriptions
    temp_col1, temp_col2, temp_col3 = st.columns(3)
    with temp_col1:
        st.markdown('<div style="text-align:center;font-size:0.8rem;">Precise<br/>0.0-0.3</div>', unsafe_allow_html=True)
    with temp_col2:
        st.markdown('<div style="text-align:center;font-size:0.8rem;">Balanced<br/>0.4-0.7</div>', unsafe_allow_html=True)
    with temp_col3:
        st.markdown('<div style="text-align:center;font-size:0.8rem;">Creative<br/>0.8-1.0</div>', unsafe_allow_html=True)
    
    temperature = st.slider(
        "",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.settings["temperature"],
        step=0.1
    )
    st.session_state.settings["temperature"] = temperature
    
    # Maximum Length with explanation
    st.subheader("Response Length")
    st.markdown('<div class="tooltip-text">Controls how detailed the responses will be.</div>', unsafe_allow_html=True)
    
    # Token descriptions
    token_options = {
        512: "Brief",
        1024: "Standard",
        2048: "Detailed",
        4096: "Comprehensive"
    }
    
    token_cols = st.columns(len(token_options))
    for i, (tokens, desc) in enumerate(token_options.items()):
        with token_cols[i]:
            st.markdown(f'<div style="text-align:center;font-size:0.8rem;">{desc}<br/>{tokens}</div>', unsafe_allow_html=True)
    
    # Fix: Use default value if current value not in options
    current_tokens = st.session_state.settings["max_tokens"]
    if current_tokens not in token_options:
        current_tokens = 2048  # Default to detailed if not matching
    
    max_tokens = st.select_slider(
        "",
        options=list(token_options.keys()),
        value=current_tokens
    )
    st.session_state.settings["max_tokens"] = max_tokens
    
    st.markdown("---")
    
    # Conversation Management
    st.subheader("Conversation")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Chat", use_container_width=True, key="new_chat_sidebar"):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        # Fix: Simplified download functionality
        if st.button("Download Chat", use_container_width=True, key="download_sidebar"):
            pass
    
    # Moved outside the button to always show when messages exist
    if "messages" in st.session_state and st.session_state.messages:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vive_quality_chat_{timestamp}.txt"
        
        content = "Vive Health Quality Bot - Conversation Log\n"
        content += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for msg in st.session_state.messages:
            content += f"{msg['role'].upper()}: {msg['content']}\n\n"
        
        st.download_button(
            label="Save Chat Log",
            data=content,
            file_name=filename,
            mime="text/plain",
            use_container_width=True,
            key="download_button_sidebar"
        )
    
    st.markdown("---")
    st.markdown("© Vive Health Quality Department")

# --- MAIN CONTENT ---
# Custom Header
st.markdown("""
<div class="custom-header">
    <h1>Vive Health Quality Bot 🧠</h1>
    <p>Your AI assistant trained specifically on Vive Health quality processes and standards</p>
</div>
""", unsafe_allow_html=True)

# Bot Description and Features
st.markdown("""
<div class="feature-card">
    <h3>How Quality Bot Can Help You</h3>
    <p>Quality Bot has specialized training in Vive Health's quality standards, processes, and requirements. 
    With access to our quality training materials, the bot can assist with:</p>
    <ul>
        <li><strong>Quality Standards:</strong> Information about ISO 13485, FDA regulations, and Vive's quality policies</li>
        <li><strong>Inspection Procedures:</strong> Details on AQL sampling methods, inspection criteria, and defect classification</li>
        <li><strong>Quality Tools:</strong> Guidance on using the 7 Quality Tools for root cause analysis and problem-solving</li>
        <li><strong>Process Improvement:</strong> Help with CAPA processes, Kaizen implementation, and quality metrics</li>
    </ul>
    <p>The bot has specific knowledge about Vive Health's quality cases, products, and team contacts.</p>
</div>
""", unsafe_allow_html=True)

# Model Information Card
st.markdown("""
<div class="models-info-card">
    <h3>AI Model Selection Guide</h3>
    <p>Choose the appropriate model based on your needs:</p>
    <ul>
        <li><strong>GPT-4o (Recommended):</strong> The best overall choice for most quality inquiries. Provides balanced speed and accuracy.</li>
        <li><strong>GPT-3.5-Turbo:</strong> Best for simple, quick tasks and general questions when you need immediate responses.</li>
        <li><strong>GPT-4-Turbo:</strong> Optimized for complex technical questions, detailed analysis, and regulatory compliance inquiries.</li>
    </ul>
    <p><strong>Note:</strong> For the best experience, we recommend using GPT-4o as the default model.</p>
</div>
""", unsafe_allow_html=True)

# Quick Access Suggestion Cards - Only show for new conversations
if len(st.session_state.messages) == 0:
    st.markdown("<h3>Try asking about:</h3>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-container">
        <div class="info-card">
            <h4>📋 Quality Processes</h4>
            <p>"What is our AQL inspection process?"</p>
            <p>"How do we classify defects at Vive?"</p>
        </div>
        <div class="info-card">
            <h4>🔍 Quality Tools</h4>
            <p>"How can I use a Fishbone diagram?"</p>
            <p>"Explain Pareto analysis for quality issues"</p>
        </div>
        <div class="info-card">
            <h4>📊 Quality Standards</h4>
            <p>"What is our ISO 13485 certification status?"</p>
            <p>"FDA requirements for our product class"</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- DISPLAY CHAT MESSAGES ---
chat_container = st.container()
with chat_container:
    # Safely display messages with proper HTML escaping
    for message in st.session_state.messages:
        avatar_url = "https://api.dicebear.com/7.x/bottts/svg?seed=vive-quality" if message['role'] == 'assistant' else "https://api.dicebear.com/7.x/personas/svg?seed=user"
        
        # Escape HTML characters in content for security
        content = message['content']
        # Convert newlines to <br> tags but escape other HTML
        content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        content = content.replace("\n", "<br>")
        
        st.markdown(f"""
        <div class="chat-message {message['role']}">
            <img class="avatar" src="{avatar_url}" alt="{message['role']}"/>
            <div class="message">
                <p>{content}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- INPUT AREA ---
st.markdown("<div class='input-area'>", unsafe_allow_html=True)
user_input = st.text_area("Ask a quality-related question:", key="user_input", height=100)

# Button row with proper alignment
col1, col2, col3 = st.columns([6, 3, 1])
with col3:
    send_button = st.button("Send", use_container_width=True, key="send_main")

# Fix: Improved Enter to send logic
if user_input:
    # Check if send button is pressed or if Enter key was pressed (input ends with newline)
    if send_button or (len(user_input.strip()) > 1 and user_input.endswith("\n")):
        send_now = True
        user_input = user_input.strip()  # Remove the trailing newline if present
    else:
        send_now = False
else:
    send_now = False

st.markdown("</div>", unsafe_allow_html=True)

# --- PROCESS INPUT ---
if send_now and user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Clear the input box
    stored_input = user_input
    st.session_state.user_input = ""
    
    # Check if API key is available
    if not api_key:
        st.error("API Key not configured. Please contact IT support.")
    else:
        # Call OpenAI API directly
        try:
            with st.spinner("Processing your question..."):
                # Create messages array for API with system message first
                messages = [{"role": "system", "content": SYSTEM_MESSAGE}]
                
                # Add conversation history
                for m in st.session_state.messages:
                    messages.append({"role": m["role"], "content": m["content"]})
                
                # Get current settings from session state
                current_model = st.session_state.settings["model"]
                current_temp = st.session_state.settings["temperature"]
                current_max_tokens = st.session_state.settings["max_tokens"]
                
                # Direct API call
                assistant_response = call_openai_api(
                    messages=messages,
                    model=current_model,
                    temperature=current_temp,
                    max_tokens=current_max_tokens,
                    api_key=api_key
                )
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                
                # Rerun to update UI
                st.rerun()
        except requests.exceptions.Timeout:
            st.error("Request timed out. The server might be busy. Please try again.")
        except requests.exceptions.ConnectionError:
            st.error("Connection error. Please check your internet connection and try again.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
            # Log error for debugging but don't show to user
            print(f"API Error Details: {str(e)}")

# --- FOOTER ---
st.markdown("""
<div class="footer">
    <p>Vive Health Quality Bot v1.2 | For internal use only | Contact: alexander.popoff@vivehealth.com</p>
</div>
""", unsafe_allow_html=True)
