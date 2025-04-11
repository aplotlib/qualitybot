import streamlit as st
import openai
from datetime import datetime
import os

# --- API KEY HANDLING ---
# Use st.secrets for the API key instead of importing from key.py
if "openai_api_key" in st.secrets:
    api_key = st.secrets["openai_api_key"]
else:
    # Fallback for local development without secrets configured
    st.error("API key not found in secrets. Please configure secrets for deployment.")
    api_key = None

# Set the API key if available
if api_key:
    openai.api_key = api_key

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Quality Bot",
    page_icon="🤖",
    layout="wide"
)

# --- STYLES ---
st.markdown("""
<style>
    .chat-message {
        padding: 1.5rem; 
        border-radius: 0.5rem; 
        margin-bottom: 1rem; 
        display: flex;
        flex-direction: row;
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
        object-fit: cover;
    }
    .chat-message .message {
        flex: 1;
    }
    .stTextInput input {
        padding: 0.5rem !important;
        font-size: 1rem !important;
    }
    .floating-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
    }
    .sidebar .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("Quality Bot Settings")
    
    # API Key Status
    if api_key:
        st.success("API Key configured ✅")
    else:
        st.warning("API Key not configured ⚠️")
    
    # Model Selection
    model = st.selectbox(
        "Choose a model",
        ["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo"],
        index=0
    )
    
    # Temperature Slider
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Higher values make output more random, lower values more deterministic"
    )
    
    # Maximum Length
    max_tokens = st.slider(
        "Maximum response length",
        min_value=256,
        max_value=4096,
        value=1024,
        step=256,
        help="Maximum number of tokens in the response"
    )
    
    # Reset Conversation
    if st.button("New Conversation"):
        st.session_state.messages = []
        st.experimental_rerun()
    
    # Download Conversation
    if st.button("Download Conversation"):
        if "messages" in st.session_state and st.session_state.messages:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.txt"
            
            content = ""
            for msg in st.session_state.messages:
                content += f"{msg['role'].title()}: {msg['content']}\n\n"
            
            st.download_button(
                label="Download Conversation",
                data=content,
                file_name=filename,
                mime="text/plain"
            )

    st.markdown("---")
    st.markdown("Quality Bot by Your Organization")

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- HEADER ---
st.header("Quality Bot 🤖")
st.markdown("Your AI assistant for quality-related questions and tasks.")

# --- DISPLAY CHAT MESSAGES ---
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

# --- INPUT AREA ---
with st.container():
    input_container = st.container()
    
    with input_container:
        user_input = st.text_area("Your message:", key="user_input", height=100)
        col1, col2 = st.columns([6, 1])
        
        with col2:
            submit_button = st.button("Send")

# --- PROCESS INPUT ---
if submit_button and user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Check if API key is available
    if not api_key:
        st.error("API Key not configured. Please set up secrets for this application.")
    else:
        # Initialize OpenAI client
        try:
            client = openai.OpenAI(api_key=api_key)
            
            with st.spinner("Thinking..."):
                # Create messages array for API
                messages = [
                    {"role": m["role"], "content": m["content"]} 
                    for m in st.session_state.messages
                ]
                
                # Call OpenAI API
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                
                # Extract response content
                assistant_response = response.choices[0].message.content
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                
                # Rerun to update UI
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Add sample questions or suggestions
if len(st.session_state.messages) == 0:
    st.info("👋 Hello! Try asking me something like:")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("- How can I improve product quality?")
        st.markdown("- What are common quality assurance techniques?")
    with col2:
        st.markdown("- Help me create a QA checklist")
        st.markdown("- What are ISO 9001 requirements?")
