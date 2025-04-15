import streamlit as st
import os
from datetime import datetime
import requests
import json
import io
import tempfile
from pathlib import Path

# Document processing libraries
import PyPDF2
import docx
import pandas as pd
from docx import Document
from docx.shared import Pt

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
    page_title="Quality Bot & Document Translator",
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
    .main-tabs .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .main-tabs .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding: 10px 16px;
        margin-right: 4px;
    }
    .main-tabs .stTabs [aria-selected="true"] {
        background-color: #e3f2fd;
        border-bottom: 2px solid #4285F4;
    }
    .progress-container {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 20px;
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
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload)
    )
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        error_message = f"API Error: {response.status_code} - {response.text}"
        raise Exception(error_message)

# --- DOCUMENT PROCESSING FUNCTIONS ---
def extract_text_from_pdf(file):
    """Extract text from a PDF file"""
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    num_pages = len(pdf_reader.pages)
    
    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        text += page.extract_text() + "\n\n"
    
    return text, num_pages

def extract_text_from_docx(file):
    """Extract text from a DOCX file"""
    doc = docx.Document(file)
    full_text = []
    
    for para in doc.paragraphs:
        full_text.append(para.text)
    
    return "\n".join(full_text), len(doc.paragraphs)

def extract_text_from_txt(file):
    """Extract text from a TXT file"""
    text = file.getvalue().decode("utf-8")
    lines = text.split("\n")
    return text, len(lines)

def extract_text_from_csv(file):
    """Extract text from a CSV file"""
    df = pd.read_csv(file)
    csv_text = df.to_csv(index=False)
    return csv_text, len(df)

def extract_text_from_xlsx(file):
    """Extract text from an Excel file"""
    df = pd.read_excel(file)
    excel_text = df.to_csv(index=False)
    return excel_text, len(df)

def process_document(uploaded_file):
    """Process the uploaded document and extract text"""
    file_extension = Path(uploaded_file.name).suffix.lower()
    
    if file_extension == ".pdf":
        text, pages = extract_text_from_pdf(uploaded_file)
    elif file_extension == ".docx":
        text, pages = extract_text_from_docx(uploaded_file)
    elif file_extension == ".txt":
        text, pages = extract_text_from_txt(uploaded_file)
    elif file_extension == ".csv":
        text, pages = extract_text_from_csv(uploaded_file)
    elif file_extension in [".xlsx", ".xls"]:
        text, pages = extract_text_from_xlsx(uploaded_file)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")
    
    return text, pages

def translate_text(text, source_lang, target_lang, model, temperature, api_key, progress_bar=None, status_text=None):
    """Translate text using OpenAI API"""
    
    # Split the text into chunks (approx 4000 tokens per chunk)
    chunk_size = 4000  # Adjust based on token limits
    chunks = []
    words = text.split()
    current_chunk = []
    current_chunk_size = 0
    
    for word in words:
        current_chunk_size += len(word) + 1  # +1 for space
        if current_chunk_size > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_chunk_size = len(word) + 1
        else:
            current_chunk.append(word)
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    translated_chunks = []
    total_chunks = len(chunks)
    
    if progress_bar is not None:
        progress_bar.empty()
        progress_bar.progress(0)
    
    for i, chunk in enumerate(chunks):
        if status_text is not None:
            status_text.text(f"Translating chunk {i+1}/{total_chunks}...")
        
        messages = [
            {"role": "system", "content": f"You are a professional translator. Translate the following text from {source_lang} to {target_lang}. Maintain the original formatting as much as possible."},
            {"role": "user", "content": chunk}
        ]
        
        translated_chunk = call_openai_api(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=4096,  # Maximum allowed by API
            api_key=api_key
        )
        
        translated_chunks.append(translated_chunk)
        
        if progress_bar is not None:
            progress_bar.progress((i + 1) / total_chunks)
    
    if status_text is not None:
        status_text.text("Translation completed!")
    
    return "\n".join(translated_chunks)

def create_docx_from_text(text, filename):
    """Create a DOCX file from text"""
    doc = Document()
    
    # Add styles
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
    # Split text by paragraphs and add to document
    paragraphs = text.split('\n')
    for para in paragraphs:
        if para.strip():  # Skip empty paragraphs
            doc.add_paragraph(para)
    
    # Save to a BytesIO object
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    
    return doc_io

# --- SIDEBAR ---
with st.sidebar:
    st.title("Settings")
    
    # API Key Status
    if api_key:
        st.success("API Key configured ✅")
    else:
        st.warning("API Key not configured ⚠️")
    
    # Model Selection
    model = st.selectbox(
        "Choose a model",
        ["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo"],
        index=1  # Default to gpt-4o for better translation
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
        if "messages" in st.session_state:
            st.session_state.messages = []
        st.experimental_rerun()
    
    # Download Conversation
    if "messages" in st.session_state and st.session_state.messages:
        if st.button("Download Conversation"):
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
    st.markdown("Quality Bot & Document Translator by Vive Quality")

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- MAIN CONTENT WITH TABS ---
st.markdown('<div class="main-tabs">', unsafe_allow_html=True)
tab1, tab2 = st.tabs(["Chat Bot 🤖", "Document Translator 🔄"])
st.markdown('</div>', unsafe_allow_html=True)

with tab1:
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
            # Call OpenAI API directly without using the client library
            try:
                with st.spinner("Thinking..."):
                    # Create messages array for API
                    messages = [
                        {"role": m["role"], "content": m["content"]} 
                        for m in st.session_state.messages
                    ]
                    
                    # Direct API call instead of using the client
                    assistant_response = call_openai_api(
                        messages=messages,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        api_key=api_key
                    )
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    
                    # Rerun to update UI
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Add sample questions or suggestions
    if len(st.session_state.messages) == 0:
        st.info("👋 Hello! Please use 4o. Try asking me something like:")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("- How can I improve product quality?")
            st.markdown("- What are common quality assurance techniques?")
        with col2:
            st.markdown("- Help me create a QA checklist")
            st.markdown("- What are ISO 13485 requirements?")

with tab2:
    st.header("Document Translator 🔄")
    st.markdown("Upload large documents (up to 100+ pages) and translate them to any language.")
    
    # File upload
    uploaded_file = st.file_uploader("Choose a document to translate", 
                                     type=["pdf", "docx", "txt", "csv", "xlsx", "xls"])
    
    if uploaded_file is not None:
        # Display file info
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / (1024*1024):.2f} MB"
        }
        st.write(file_details)
        
        # Translation settings
        col1, col2 = st.columns(2)
        with col1:
            source_language = st.selectbox(
                "Source Language",
                ["Auto-detect", "English", "Spanish", "French", "German", "Chinese", 
                 "Japanese", "Korean", "Russian", "Arabic", "Portuguese", "Italian"]
            )
        with col2:
            target_language = st.selectbox(
                "Target Language",
                ["English", "Spanish", "French", "German", "Chinese", 
                 "Japanese", "Korean", "Russian", "Arabic", "Portuguese", "Italian"]
            )
        
        # Output format
        output_format = st.radio(
            "Output Format",
            ["Text", "DOCX"],
            horizontal=True
        )
        
        # Process and translate button
        if st.button("Process and Translate"):
            if not api_key:
                st.error("API Key not configured. Please set up secrets for this application.")
            else:
                try:
                    # Create progress indicators
                    progress_container = st.container()
                    with progress_container:
                        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
                        status_text = st.empty()
                        progress_bar = st.empty()
                        status_text.text("Processing document...")
                        progress_bar.progress(0)
                        
                        # Process document
                        text, size_info = process_document(uploaded_file)
                        
                        # Calculate and display stats
                        word_count = len(text.split())
                        char_count = len(text)
                        estimated_tokens = word_count * 1.3  # Rough estimate
                        
                        status_text.text("Document processed! Preparing for translation...")
                        file_type = Path(uploaded_file.name).suffix
                        
                        if file_type == ".pdf":
                            size_desc = f"{size_info} pages"
                        elif file_type == ".docx":
                            size_desc = f"{size_info} paragraphs"
                        elif file_type in [".csv", ".xlsx", ".xls"]:
                            size_desc = f"{size_info} rows"
                        else:
                            size_desc = f"{size_info} lines"
                        
                        st.markdown(f"""
                        **Document Stats:**
                        - {size_desc}
                        - {word_count:,} words
                        - {char_count:,} characters
                        - ~{estimated_tokens:,.0f} estimated tokens
                        """)
                        
                        # Calculate cost and time estimates
                        if model == "gpt-3.5-turbo":
                            cost_estimate = estimated_tokens / 1000 * 0.0010  # $0.0010 per 1K input tokens
                            time_estimate = (estimated_tokens / 4000) * 5  # ~5 seconds per 4K tokens
                        else:  # gpt-4 models
                            cost_estimate = estimated_tokens / 1000 * 0.01  # $0.01 per 1K input tokens
                            time_estimate = (estimated_tokens / 4000) * 10  # ~10 seconds per 4K tokens
                        
                        st.markdown(f"""
                        **Estimated Processing:**
                        - Cost: ~${cost_estimate:.2f}
                        - Time: ~{int(time_estimate)} seconds
                        """)
                        
                        # Translate text
                        status_text.text("Translating document...")
                        translated_text = translate_text(
                            text=text,
                            source_lang=source_language if source_language != "Auto-detect" else "",
                            target_lang=target_language,
                            model=model,
                            temperature=temperature,
                            api_key=api_key,
                            progress_bar=progress_bar,
                            status_text=status_text
                        )
                        
                        status_text.text("Translation completed! Preparing download...")
                        
                        # Prepare download
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        base_filename = f"{Path(uploaded_file.name).stem}_translated_{target_language}_{timestamp}"
                        
                        if output_format == "Text":
                            st.download_button(
                                label="Download Translated Text",
                                data=translated_text,
                                file_name=f"{base_filename}.txt",
                                mime="text/plain"
                            )
                        else:  # DOCX
                            docx_file = create_docx_from_text(translated_text, base_filename)
                            st.download_button(
                                label="Download Translated DOCX",
                                data=docx_file,
                                file_name=f"{base_filename}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                        
                        status_text.text("✅ Translation completed! Download available.")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Show preview
                        with st.expander("Preview Translation"):
                            preview_length = min(2000, len(translated_text))
                            st.text_area(
                                "Translation Preview (first 2000 chars)",
                                translated_text[:preview_length] + ("..." if len(translated_text) > preview_length else ""),
                                height=300
                            )
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Display helpful tips
        with st.expander("Tips for better translations"):
            st.markdown("""
            - For large documents, GPT-4o is recommended for better quality and context handling
            - Clean formatting in the original document improves translation quality
            - If your document contains specialized terminology, consider mentioning it in the chat tab first
            - The translation maintains formatting but may not preserve complex layouts
            - For very large documents (100+ pages), the system will break it into manageable chunks and process them sequentially
            """)
    
    else:
        # Show supported formats when no file is uploaded
        st.info("""
        **Supported file formats:**
        - PDF (.pdf) - Handles large multi-page documents
        - Word (.docx) - Preserves basic formatting in translation
        - Text (.txt) - Fast processing for plain text
        - Spreadsheets (.csv, .xlsx, .xls) - Translates tabular data
        
        Upload files up to 100+ pages. For best results with very large documents, use GPT-4o.
        """)

# Add floating help button
st.markdown("""
<div class="floating-button">
    <a href="mailto:support@vivequality.com" target="_blank" style="text-decoration:none;">
        <button style="background-color:#4285F4; color:white; border:none; padding:10px 15px; border-radius:50%; font-size:16px;">
            ?
        </button>
    </a>
</div>
""", unsafe_allow_html=True)
