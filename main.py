import streamlit as st
import os
import hashlib
import requests
import json
import io
import tempfile
from pathlib import Path
from datetime import datetime
import pandas as pd

# Document processing libraries
import PyPDF2
import docx
from docx import Document
from docx.shared import Pt

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Quality Control Assistant",
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

# --- API KEY HANDLING ---
try:
    api_key = st.secrets["openai_api_key"]
except (FileNotFoundError, KeyError):
    api_key = os.environ.get("OPENAI_API_KEY", "")

# --- PASSWORD VERIFICATION ---
def verify_password(password):
    """Temporary simplified password check"""
    return password == "MPFvive8955@#@"  # Just check direct equality

# --- TRANSLATIONS ---
translations = {
    "zh": {
        # Login page
        "app_title": "质量控制助手",
        "welcome": "欢迎使用宁海威斐质量控制系统",
        "password": "密码",
        "enter_password": "请输入密码访问系统",
        "login_button": "登录系统",
        "incorrect_password": "密码不正确，请重试",
        
        # Settings
        "settings": "设置",
        "language_setting": "语言",
        "logout": "退出登录",
        "new_conversation": "新对话",
        "model_info": "使用专门训练的质量控制模型",
        "by_vive": "宁海威斐质量控制系统",
        
        # Tabs
        "chat_bot": "聊天机器人 🤖",
        "sop_library": "SOP标准库 📚",
        "faq": "常见问题 ❓",
        "doc_translator": "文档翻译 🔄",
        
        # Chat interface
        "quality_assistant": "您的质量相关问题和任务的AI助手。",
        "your_message": "您的消息：",
        "send": "发送",
        "thinking": "思考中...",
        
        # Translator interface
        "translator_title": "文档翻译",
        "translator_desc": "上传大型文档（最多100多页）并将其翻译成任何语言。",
        "choose_document": "选择要翻译的文档",
        "filename": "文件名",
        "file_size": "文件大小",
        "source_language": "源语言",
        "target_language": "目标语言",
        "output_format": "输出格式",
        "process_translate": "处理并翻译",
        "processing_doc": "处理文档...",
        "doc_processed": "文档已处理！正在准备翻译...",
        "translating_doc": "正在翻译文档...",
        "translation_completed": "翻译完成！正在准备下载...",
        "download_text": "下载翻译文本",
        "download_docx": "下载翻译DOCX",
        "translation_complete": "✅ 翻译完成！下载可用。",
        "preview_translation": "预览翻译",
        "preview_first": "翻译预览（前2000个字符）",
        "translation_tips": "更好翻译的提示",
        "supported_formats": "支持的文件格式",
        
        # Document stats
        "document_stats": "文档统计：",
        "pages": "页",
        "paragraphs": "段落",
        "rows": "行",
        "lines": "行",
        "words": "字",
        "characters": "字符",
        "estimated_tokens": "估计的标记",
        "estimated_processing": "预计处理：",
        "cost": "成本",
        "time": "时间",
        "seconds": "秒",
        
        # SOP library
        "product_groups": "产品组",
        "group1": "第一组：高负载转移产品",
        "group2": "第二组：支撑设备",
        "group3": "第三组：个人支撑物品",
        "material_testing": "材料测试",
        
        # FAQ
        "faq_load_testing": "转移吊带需要什么负载测试？",
        "faq_defect": "如果在检验过程中发现缺陷，我应该怎么做？",
        "faq_load_test_meaning": "'120%负载测试'是什么意思？",
        "faq_material_testing": "生产前的材料测试要求是什么？",
        
        # Sample questions
        "sample_question_1": "如何测试转移吊带？",
        "sample_question_2": "抽样检验水平是什么？",
        "sample_question_3": "发现缺陷时应该怎么做？",
        
        # Languages
        "auto_detect": "自动检测",
        "english": "英语",
        "spanish": "西班牙语",
        "french": "法语",
        "german": "德语",
        "chinese": "中文",
        "japanese": "日语",
        "korean": "韩语",
        "russian": "俄语",
        "arabic": "阿拉伯语",
        "portuguese": "葡萄牙语",
        "italian": "意大利语",
        
        # Tips
        "tip_1": "对于大型文档，建议使用GPT-4o以获得更好的质量和上下文处理",
        "tip_2": "原始文档中的清晰格式可以提高翻译质量",
        "tip_3": "如果您的文档包含专业术语，请考虑先在聊天选项卡中提及",
        "tip_4": "翻译保持格式但可能无法保留复杂布局",
        "tip_5": "对于非常大的文档（100多页），系统将其分解为可管理的块并按顺序处理",
        
        # File formats
        "formats_info": "支持的文件格式：",
        "format_pdf": "PDF (.pdf) - 处理大型多页文档",
        "format_docx": "Word (.docx) - 在翻译中保留基本格式",
        "format_txt": "文本 (.txt) - 快速处理纯文本",
        "format_spreadsheets": "电子表格 (.csv, .xlsx, .xls) - 翻译表格数据",
        "format_upload_info": "上传最多100多页的文件。对于非常大的文档，请使用GPT-4o获得最佳结果。",
        
        # Categories
        "category": "类别",
        "all": "全部",
        "testing": "测试",
        "inspection": "检验",
        "materials": "材料",
        
        # Other
        "hello": "👋 您好！请向我询问有关质量控制程序的问题。",
        "sample_questions": "示例问题:"
    },
    "en": {
        # Login page
        "app_title": "Quality Control Assistant",
        "welcome": "Welcome to Ninghai Vive Quality Control System",
        "password": "Password",
        "enter_password": "Enter password to access the system",
        "login_button": "Login to System",
        "incorrect_password": "Incorrect password, please try again",
        
        # Settings
        "settings": "Settings",
        "language_setting": "Language",
        "logout": "Logout",
        "new_conversation": "New Conversation",
        "model_info": "Using fine-tuned quality control model",
        "by_vive": "Ninghai Vive Quality Control System",
        
        # Tabs
        "chat_bot": "Chat Bot 🤖",
        "sop_library": "SOP Library 📚",
        "faq": "FAQ ❓",
        "doc_translator": "Document Translator 🔄",
        
        # Chat interface
        "quality_assistant": "Your AI assistant for quality-related questions and tasks.",
        "your_message": "Your message:",
        "send": "Send",
        "thinking": "Thinking...",
        
        # Translator interface
        "translator_title": "Document Translator",
        "translator_desc": "Upload large documents (up to 100+ pages) and translate them to any language.",
        "choose_document": "Choose a document to translate",
        "filename": "Filename",
        "file_size": "File size",
        "source_language": "Source Language",
        "target_language": "Target Language",
        "output_format": "Output Format",
        "process_translate": "Process and Translate",
        "processing_doc": "Processing document...",
        "doc_processed": "Document processed! Preparing for translation...",
        "translating_doc": "Translating document...",
        "translation_completed": "Translation completed! Preparing download...",
        "download_text": "Download Translated Text",
        "download_docx": "Download Translated DOCX",
        "translation_complete": "✅ Translation completed! Download available.",
        "preview_translation": "Preview Translation",
        "preview_first": "Translation Preview (first 2000 chars)",
        "translation_tips": "Tips for better translations",
        "supported_formats": "Supported file formats",
        
        # Document stats
        "document_stats": "Document Stats:",
        "pages": "pages",
        "paragraphs": "paragraphs",
        "rows": "rows",
        "lines": "lines",
        "words": "words",
        "characters": "characters",
        "estimated_tokens": "estimated tokens",
        "estimated_processing": "Estimated Processing:",
        "cost": "Cost",
        "time": "Time",
        "seconds": "seconds",
        
        # SOP library
        "product_groups": "Product Groups",
        "group1": "GROUP 1: HIGH LOAD TRANSFER PRODUCTS",
        "group2": "GROUP 2: SUPPORT DEVICES",
        "group3": "GROUP 3: PERSONAL SUPPORT ITEMS",
        "material_testing": "Material Testing",
        
        # FAQ
        "faq_load_testing": "What load testing is required for transfer slings?",
        "faq_defect": "What should I do if I find a defect during inspection?",
        "faq_load_test_meaning": "What does '120% load test' mean?",
        "faq_material_testing": "What are the material testing requirements before production?",
        
        # Sample questions
        "sample_question_1": "How do I test transfer slings?",
        "sample_question_2": "What is the sampling inspection level?",
        "sample_question_3": "What should I do when I find defects?",
        
        # Languages
        "auto_detect": "Auto-detect",
        "english": "English",
        "spanish": "Spanish",
        "french": "French",
        "german": "German",
        "chinese": "Chinese",
        "japanese": "Japanese",
        "korean": "Korean",
        "russian": "Russian",
        "arabic": "Arabic",
        "portuguese": "Portuguese",
        "italian": "Italian",
        
        # Tips
        "tip_1": "For large documents, GPT-4o is recommended for better quality and context handling",
        "tip_2": "Clean formatting in the original document improves translation quality",
        "tip_3": "If your document contains specialized terminology, consider mentioning it in the chat tab first",
        "tip_4": "The translation maintains formatting but may not preserve complex layouts",
        "tip_5": "For very large documents (100+ pages), the system will break it into manageable chunks and process them sequentially",
        
        # File formats
        "formats_info": "Supported file formats:",
        "format_pdf": "PDF (.pdf) - Handles large multi-page documents",
        "format_docx": "Word (.docx) - Preserves basic formatting in translation",
        "format_txt": "Text (.txt) - Fast processing for plain text",
        "format_spreadsheets": "Spreadsheets (.csv, .xlsx, .xls) - Translates tabular data",
        "format_upload_info": "Upload files up to 100+ pages. For best results with very large documents, use GPT-4o.",
        
        # Categories
        "category": "Category",
        "all": "All",
        "testing": "Testing",
        "inspection": "Inspection",
        "materials": "Materials",
        
        # Other
        "hello": "👋 Hello! Ask me questions about quality control procedures.",
        "sample_questions": "Sample questions:"
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
/* Main styles with both light and dark mode support */
:root {
    --text-color: #1A1A1A;
    --bg-color: #FFFFFF;
    --primary-color: #0d47a1;
    --secondary-color: #e3f2fd;
    --accent-color: #4285F4;
    --card-bg: #f0f2f6;
    --shadow-color: rgba(0,0,0,0.1);
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    :root {
        --text-color: #F0F0F0;
        --bg-color: #1A1A1A;
        --primary-color: #5c9eff;
        --secondary-color: #132f4c;
        --accent-color: #5c9eff;
        --card-bg: #242A38;
        --shadow-color: rgba(0,0,0,0.3);
    }
}

body {
    font-family: 'Arial', sans-serif;
    color: var(--text-color);
    background-color: var(--bg-color);
}

/* Login page */
.login-container {
    max-width: 400px;
    margin: 40px auto;
    padding: 2rem;
    border-radius: 10px;
    background-color: var(--card-bg);
    box-shadow: 0 4px 10px var(--shadow-color);
    text-align: center;
}

.login-title {
    margin-bottom: 1.5rem;
    color: var(--primary-color);
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
    background-color: var(--card-bg);
}

.chat-message.assistant {
    background-color: var(--secondary-color);
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
    background-color: var(--accent-color);
    color: white;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    box-shadow: 0 2px 10px var(--shadow-color);
    z-index: 1000;
    text-decoration: none;
}

/* Translation Progress */
.progress-container {
    padding: 20px;
    border-radius: 10px;
    background-color: var(--card-bg);
    margin-bottom: 20px;
    box-shadow: 0 2px 6px var(--shadow-color);
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

/* Ensure good contrast in dark mode */
.stMarkdown, .stMarkdown p, .stMarkdown span {
    color: var(--text-color) !important;
}
</style>
""", unsafe_allow_html=True)

# --- API FUNCTIONS ---
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
            status_text.text(f"{t('translating_doc')} ({i+1}/{total_chunks})")
        
        messages = [
            {"role": "system", "content": f"You are a professional translator. Translate the following text from {source_lang} to {target_lang}. Maintain the original formatting as much as possible."},
            {"role": "user", "content": chunk}
        ]
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096
        }
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            
            if response.status_code == 200:
                translated_chunk = response.json()["choices"][0]["message"]["content"]
                translated_chunks.append(translated_chunk)
            else:
                translated_chunks.append(f"Error translating chunk {i+1}: {response.status_code} - {response.text}")
                
        except Exception as e:
            translated_chunks.append(f"Error translating chunk {i+1}: {str(e)}")
        
        if progress_bar is not None:
            progress_bar.progress((i + 1) / total_chunks)
    
    if status_text is not None:
        status_text.text(t("translation_complete"))
    
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

# --- LOGIN PAGE ---
if not st.session_state.authenticated:
    # Center the login content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    # Language selector at the top of login page
    with col2:
        st.markdown("<div style='text-align: center; margin-bottom: 20px;'>", unsafe_allow_html=True)
        lang_col1, lang_col2 = st.columns(2)
        with lang_col1:
            if st.button("🇨🇳 中文", key="login_zh", use_container_width=True):
                st.session_state.language = "zh"
                st.rerun()
        with lang_col2:
            if st.button("🇺🇸 English", key="login_en", use_container_width=True):
                st.session_state.language = "en"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="login-container">
            <h1>{t('app_title')}</h1>
            <p style="margin-top: 20px; margin-bottom: 20px;">
                {t('welcome')}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Two-column layout for login form
        login_col1, login_col2 = st.columns([3, 1])
        
        with login_col1:
            st.markdown(f"##### {t('password')}")
            password = st.text_input(
                t('enter_password'), 
                type="password", 
                help=t('enter_password'),
                label_visibility="collapsed"
            )
        
        with login_col2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)  # Spacer
        
        # Login button
        if st.button(t('login_button'), use_container_width=True):
            if verify_password(password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error(t('incorrect_password'))
        
        # Login page footer with version info
        st.markdown("""
        <div style="text-align: center; margin-top: 30px;">
            <img src="https://api.dicebear.com/7.x/bottts/svg?seed=gpt" width="120" />
            <p style="margin-top: 20px; color: #666; font-size: 0.8em;">
                Version 1.1.0 | Vive Health Quality Department<br>
                Using custom trained model for Quality Control
            </p>
        </div>
        """, unsafe_allow_html=True)

else:
    # --- MAIN APPLICATION AFTER LOGIN ---
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.title(t('settings'))
        
        # Language selector
        st.subheader(t('language_setting'))
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
        
        with st.expander("Model details"):
            st.code("ft:gpt-4o-2024-08-06:vive-health-quality-department:1vive-quality-training-data:BQqHZoPo")
        
        # Conversation controls
        if st.button(t('new_conversation'), use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        # Logout button
        if st.button(t('logout'), type="primary", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
        
        st.markdown("---")
        st.markdown(t('by_vive'))
    
    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs([
        t('chat_bot'), 
        t('sop_library'), 
        t('faq'),
        t('doc_translator')
    ])
    
    # --- CHAT TAB ---
    with tab1:
        st.header(f"{t('app_title')} 🤖")
        st.markdown(t('quality_assistant'))
        
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
        user_input = st.text_area(t('your_message'), height=100)
        
        # Send button
        if st.button(t('send'), key="send_button"):
            if user_input:
                # Add user message to chat
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                with st.spinner(t('thinking')):
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
            st.info(t('hello'))
            
            # Sample questions
            st.markdown(f"**{t('sample_questions')}**")
            st.markdown(f"- {t('sample_question_1')}")
            st.markdown(f"- {t('sample_question_2')}")
            st.markdown(f"- {t('sample_question_3')}")
    
    # --- SOP LIBRARY TAB ---
    with tab2:
        st.header(t('sop_library'))
        
        # Simple SOP library with tabs for different categories
        sop_types = st.radio(
            t('category'),
            [t('all'), t('testing'), t('inspection'), t('materials')],
            horizontal=True
        )
        
        st.subheader(t('product_groups'))
        
        with st.expander(t('group1'), expanded=True):
            st.markdown("**S-3 Level, 408kg load, 20 min test, 0.1% AQL**")
            st.markdown("""
            - Transfer Sling (MI487/LVA2056BLK)
            - Transfer Blanket Small (MI621/MOB1022WHTLS)
            - Transfer Blanket with Handles (MI624/LVA2000)
            - Lift Sling with Opening (MI645/LVA2057BLU)
            - Wooden Transfer Board (RHB1037WOOD/L)
            - Core Hydraulic Patient Lift (MOB1120)
            - Hydraulic Patient Lift Systems (MOB1068PMP, MOB1068SLG)
            - Transfer Blanket Large (MI621-L/MOB1022WHTL)
            """)
        
        with st.expander(t('group2')):
            st.markdown("**S-2 Level, 0.1% AQL, 5 min test**")
            st.markdown("""
            - Car Assist Handle (MI474/LVA2098) - 137kg
            - Portable Stand Assist (MI524-LVA3016BLK) - 115kg
            """)
        
        with st.expander(t('group3')):
            st.markdown("**S-1 Level, 0.1% AQL**")
            st.markdown("""
            - Transfer Harness (MI471/RHB1054) - 181kg, 5 min - 4 handles each test
            - All Transfer Belts - 225kg, 5 min
            """)
        
        # Material testing section
        if sop_types in [t('all'), t('materials')]:
            st.subheader(t('material_testing'))
            
            material_data = {
                "Material": ["Straps/Webbing", "Hardware", "Fabric/Mesh"],
                "Test Method": ["Visual + 120% load test", 
                               "Visual + 120% load test", 
                               "Visual + 100% load test"],
                "Acceptance": ["No tears/deformation", 
                               "No breakage", 
                               "No tears"]
            }
            
            st.table(pd.DataFrame(material_data))
    
    # --- FAQ TAB ---
    with tab3:
        st.header(t('faq'))
        
        with st.expander(t('faq_load_testing'), expanded=True):
            if st.session_state.language == "zh":
                st.markdown("""
                转移吊带（MI487/LVA2056BLK）需要S-3级别检验，进行408kg静态负载测试，持续20分钟。AQL为0.1%，这对于正常批量大小实际上意味着零缺陷。
                """)
            else:
                st.markdown("""
                Transfer slings (MI487/LVA2056BLK) require S-3 level inspection with a 408kg static load test for 20 minutes. The AQL is 0.1%, which essentially means zero defects for normal batch sizes.
                """)
        
        with st.expander(t('faq_defect')):
            if st.session_state.language == "zh":
                st.markdown("""
                如果发现缺陷：
                1. 使用更高检验水平重新检验批次（例如，S-2变为S-3）。
                2. 如果发现问题源于原材料而非MPF工艺，联系材料供应商。
                3. 对于高风险产品如病人升降吊带，不允许放宽标准。
                4. 对于较低风险产品，如果缺陷是孤立的且能确认安全单元，在咨询Alex后可能接受一些调整。
                
                如有不确定，请务必通知质量经理Alex。
                """)
            else:
                st.markdown("""
                If a defect is found:
                1. Reinspect the lot at the next higher inspection level (e.g., S-2 becomes S-3).
                2. Contact material vendors if defects are traced to incoming materials.
                3. For high-risk products like patient lift slings, no relaxation of standards is allowed.
                4. For lower-risk products, if defects are isolated and safe units can be confirmed, some adjustments may be acceptable.
                
                Always inform Quality Manager Alex if you're uncertain.
                """)
        
        with st.expander(t('faq_load_test_meaning')):
            if st.session_state.language == "zh":
                st.markdown("""
                120%负载测试是指在产品宣传的最大承重的120%下测试材料。例如，如果产品宣传的最大承重是200kg，则材料应在240kg下测试。
                """)
            else:
                st.markdown("""
                The 120% load test refers to testing materials at 120% of the advertised maximum weight for the product. For example, if a product's advertised maximum weight is 200kg, the materials should be tested at 240kg.
                """)
        
        with st.expander(t('faq_material_testing')):
            if st.session_state.language == "zh":
                st.markdown("""
                生产前，使用与最终产品相同的抽样水平测试关键组件：
                1. 织带/带子：目视+120%负载测试，不允许有撕裂/变形。
                2. 硬件：目视+120%负载测试，不允许有断裂。
                3. 面料/网布：目视+100%负载测试，不允许有撕裂。
                """)
            else:
                st.markdown("""
                Before production, test critical components using the same sampling level as the final product:
                1. Straps/Webbing: Visual + 120% load test with no tears/deformation allowed.
                2. Hardware: Visual + 120% load test with no breakage allowed.
                3. Fabric/Mesh: Visual + 100% load test with no tears allowed.
                """)
    
    # --- DOCUMENT TRANSLATOR TAB ---
    with tab4:
        st.header(t('translator_title'))
        st.markdown(t('translator_desc'))
        
        # File upload
        uploaded_file = st.file_uploader(t('choose_document'), 
                                        type=["pdf", "docx", "txt", "csv", "xlsx", "xls"])
        
        if uploaded_file is not None:
            # Display file info
            file_details = {
                t('filename'): uploaded_file.name,
                t('file_size'): f"{uploaded_file.size / (1024*1024):.2f} MB"
            }
            st.write(file_details)
            
            # Translation settings
            col1, col2 = st.columns(2)
            
            # Language options - translated from dictionary
            language_options = [
                t('auto_detect'), t('english'), t('spanish'), t('french'), 
                t('german'), t('chinese'), t('japanese'), t('korean'), 
                t('russian'), t('arabic'), t('portuguese'), t('italian')
            ]
            
            # Same options without auto-detect for target
            target_language_options = language_options.copy()
            if t('auto_detect') in target_language_options:
                target_language_options.remove(t('auto_detect'))
            
            with col1:
                source_language = st.selectbox(
                    t('source_language'),
                    language_options
                )
            with col2:
                target_language = st.selectbox(
                    t('target_language'),
                    target_language_options
                )
            
            # Output format
            output_format = st.radio(
                t('output_format'),
                ["Text", "DOCX"],
                horizontal=True
            )
            
            # Map to OpenAI model
            model_options = {
                "gpt-3.5-turbo": "gpt-3.5-turbo",
                "gpt-4o": "gpt-4o",
                "gpt-4-turbo": "gpt-4-turbo"
            }
            
            # Default to GPT-4o for translations
            model = "gpt-4o"
            temperature = 0.7
            
            # Process and translate button
            if st.button(t('process_translate')):
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
                            status_text.text(t('processing_doc'))
                            progress_bar.progress(0)
                            
                            # Process document
                            text, size_info = process_document(uploaded_file)
                            
                            # Calculate and display stats
                            word_count = len(text.split())
                            char_count = len(text)
                            estimated_tokens = word_count * 1.3  # Rough estimate
                            
                            status_text.text(t('doc_processed'))
                            file_type = Path(uploaded_file.name).suffix
                            
                            if file_type == ".pdf":
                                size_desc = f"{size_info} {t('pages')}"
                            elif file_type == ".docx":
                                size_desc = f"{size_info} {t('paragraphs')}"
                            elif file_type in [".csv", ".xlsx", ".xls"]:
                                size_desc = f"{size_info} {t('rows')}"
                            else:
                                size_desc = f"{size_info} {t('lines')}"
                            
                            st.markdown(f"""
                            **{t('document_stats')}**
                            - {size_desc}
                            - {word_count:,} {t('words')}
                            - {char_count:,} {t('characters')}
                            - ~{estimated_tokens:,.0f} {t('estimated_tokens')}
                            """)
                            
                            # Calculate cost and time estimates
                            if model == "gpt-3.5-turbo":
                                cost_estimate = estimated_tokens / 1000 * 0.0010  # $0.0010 per 1K input tokens
                                time_estimate = (estimated_tokens / 4000) * 5  # ~5 seconds per 4K tokens
                            else:  # gpt-4 models
                                cost_estimate = estimated_tokens / 1000 * 0.01  # $0.01 per 1K input tokens
                                time_estimate = (estimated_tokens / 4000) * 10  # ~10 seconds per 4K tokens
                            
                            st.markdown(f"""
                            **{t('estimated_processing')}**
                            - {t('cost')}: ~${cost_estimate:.2f}
                            - {t('time')}: ~{int(time_estimate)} {t('seconds')}
                            """)
                            
                            # Map the selected language to English for the API
                            lang_mapping = {
                                t('auto_detect'): "Auto-detect",
                                t('english'): "English",
                                t('spanish'): "Spanish",
                                t('french'): "French",
                                t('german'): "German",
                                t('chinese'): "Chinese",
                                t('japanese'): "Japanese",
                                t('korean'): "Korean",
                                t('russian'): "Russian",
                                t('arabic'): "Arabic",
                                t('portuguese'): "Portuguese",
                                t('italian'): "Italian"
                            }
                            
                            source_lang_en = lang_mapping.get(source_language, source_language)
                            target_lang_en = lang_mapping.get(target_language, target_language)
                            
                            # Translate text
                            status_text.text(t('translating_doc'))
                            translated_text = translate_text(
                                text=text,
                                source_lang=source_lang_en,
                                target_lang=target_lang_en,
                                model=model,
                                temperature=temperature,
                                api_key=api_key,
                                progress_bar=progress_bar,
                                status_text=status_text
                            )
                            
                            status_text.text(t('translation_completed'))
                            
                            # Prepare download
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            base_filename = f"{Path(uploaded_file.name).stem}_translated_{target_lang_en}_{timestamp}"
                            
                            if output_format == "Text":
                                st.download_button(
                                    label=t('download_text'),
                                    data=translated_text,
                                    file_name=f"{base_filename}.txt",
                                    mime="text/plain"
                                )
                            else:  # DOCX
                                docx_file = create_docx_from_text(translated_text, base_filename)
                                st.download_button(
                                    label=t('download_docx'),
                                    data=docx_file,
                                    file_name=f"{base_filename}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )
                            
                            status_text.text(t('translation_complete'))
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Show preview
                            with st.expander(t('preview_translation')):
                                preview_length = min(2000, len(translated_text))
                                st.text_area(
                                    t('preview_first'),
                                    translated_text[:preview_length] + ("..." if len(translated_text) > preview_length else ""),
                                    height=300
                                )
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            # Display helpful tips
            with st.expander(t('translation_tips')):
                st.markdown(f"""
                - {t('tip_1')}
                - {t('tip_2')}
                - {t('tip_3')}
                - {t('tip_4')}
                - {t('tip_5')}
                """)
        
        else:
            # Show supported formats when no file is uploaded
            st.info(f"""
            **{t('formats_info')}**
            - {t('format_pdf')}
            - {t('format_docx')}
            - {t('format_txt')}
            - {t('format_spreadsheets')}
            
            {t('format_upload_info')}
            """)
    
    # Contact button
    st.markdown("""
    <a href="mailto:alexander.popoff@vivehealth.com" class="help-button">?</a>
    """, unsafe_allow_html=True)
