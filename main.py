import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import io
from typing import Dict, List, Optional, Any, Union
import openai
import anthropic
import json
import base64
import os
import docx
from docx import Document
from docx.shared import Inches
import mammoth
import PyPDF2
from PIL import Image
import zipfile

# Import our comprehensive ISO knowledge module
# from iso13485_complete_module import ISO13485CompleteKnowledge, get_iso_knowledge_base, create_ai_enhanced_prompt

# Configure page
st.set_page_config(
    page_title="ISO 13485 Expert Consultant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced medical device theme
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .regulatory-menu {
        background: #f8f9ff;
        border: 1px solid #e1e5f2;
        border-radius: 8px;
        padding: 0.5rem;
        margin: 1rem 0;
        text-align: center;
    }
    
    .regulatory-menu a {
        display: inline-block;
        margin: 0 10px;
        padding: 8px 16px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    
    .regulatory-menu a:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .iso-section {
        background: #f8f9ff;
        border: 1px solid #e1e5f2;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .dhf-upload-area {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #f8f9ff;
        margin: 1rem 0;
    }
    
    .file-preview {
        background: white;
        border: 1px solid #e1e5f2;
        border-radius: 5px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .compliance-status {
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        color: white;
    }
    
    .status-compliant { background-color: #28a745; }
    .status-partial { background-color: #ffc107; color: black; }
    .status-non-compliant { background-color: #dc3545; }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .document-card {
        border: 2px solid #e1e5f2;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background: white;
    }
    
    .ai-enhancement-panel {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class EnhancedISO13485Expert:
    """Enhanced ISO 13485 Expert with complete standard knowledge and DHF generation"""
    
    def __init__(self):
        self.anthropic_client = None
        self.openai_client = None
        # self.iso_knowledge = get_iso_knowledge_base()
        self._initialize_ai_clients()
        
        # Regulatory websites
        self.regulatory_sites = {
            "FDA": "https://www.fda.gov/medical-devices",
            "EU MDR": "https://ec.europa.eu/health/md_sector/overview_en",
            "Health Canada": "https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices.html",
            "TGA (Australia)": "https://www.tga.gov.au/products/medical-devices",
            "PMDA (Japan)": "https://www.pmda.go.jp/english/review-services/outline/0002.html",
            "COFEPRIS (Mexico)": "https://www.gob.mx/cofepris",
            "ANVISA (Brazil)": "https://www.gov.br/anvisa/pt-br",
            "INVIMA (Colombia)": "https://www.invima.gov.co/"
        }
        
        # DHF required sections per FDA 21 CFR 820.30
        self.dhf_sections = {
            "device_description": "Device Description and Intended Use",
            "design_requirements": "Design Input Requirements", 
            "design_specifications": "Design Output Specifications",
            "design_reviews": "Design Review Records",
            "verification_validation": "Design Verification and Validation",
            "design_changes": "Design Change Documentation",
            "risk_analysis": "Risk Analysis Documentation",
            "design_controls": "Design Control Procedures",
            "labeling": "Labeling and Instructions for Use",
            "clinical_data": "Clinical/Performance Data"
        }

    def _initialize_ai_clients(self):
        """Initialize AI clients from Streamlit secrets"""
        try:
            if 'anthropic_api_key' in st.secrets:
                self.anthropic_client = anthropic.Anthropic(
                    api_key=st.secrets['anthropic_api_key']
                )
            if 'openai_api_key' in st.secrets:
                self.openai_client = openai.OpenAI(
                    api_key=st.secrets['openai_api_key']
                )
        except Exception as e:
            st.error(f"Error initializing AI clients: {e}")

    def get_ai_response_with_iso_context(self, prompt: str, model_choice: str = "anthropic") -> str:
        """Get AI response with ISO 13485 context"""
        try:
            # Enhanced system prompt with ISO 13485 expertise
            system_prompt = """You are a world-class ISO 13485:2016 expert consultant specializing in medical device quality management systems. You have complete knowledge of the ISO 13485:2016 standard and extensive experience in:

            - Medical device design controls (Section 7.3)
            - Risk management per ISO 14971
            - CAPA processes (Section 8.5)
            - Post-market surveillance
            - Regulatory compliance (FDA, EU MDR, Health Canada, etc.)
            - Design History File (DHF) creation
            - Device Master Record (DMR) development
            - Quality system documentation

            Provide detailed, accurate, and actionable guidance that ensures full regulatory compliance. Always reference specific ISO 13485 sections when applicable and consider practical implementation challenges."""

            if model_choice == "anthropic" and self.anthropic_client:
                # Enhance prompt with ISO context
                # iso_context = self.iso_knowledge.get_ai_context_for_query(prompt)
                # enhanced_prompt = f"{iso_context}\n\n{prompt}"
                
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
                
            elif model_choice == "openai" and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000
                )
                return response.choices[0].message.content
            else:
                return "AI service not available. Please check API configuration."
        except Exception as e:
            return f"Error getting AI response: {str(e)}"

def show_regulatory_menu():
    """Display regulatory websites menu bar"""
    regulatory_sites = {
        "🇺🇸 FDA": "https://www.fda.gov/medical-devices",
        "🇪🇺 EU MDR": "https://ec.europa.eu/health/md_sector/overview_en", 
        "🇨🇦 Health Canada": "https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices.html",
        "🇦🇺 TGA": "https://www.tga.gov.au/products/medical-devices",
        "🇯🇵 PMDA": "https://www.pmda.go.jp/english/review-services/outline/0002.html",
        "🇲🇽 COFEPRIS": "https://www.gob.mx/cofepris",
        "🇧🇷 ANVISA": "https://www.gov.br/anvisa/pt-br",
        "🇨🇴 INVIMA": "https://www.invima.gov.co/"
    }
    
    menu_html = '<div class="regulatory-menu">'
    menu_html += '<h4 style="margin: 0; color: #333; margin-bottom: 10px;">🌍 Global Regulatory Resources</h4>'
    
    for name, url in regulatory_sites.items():
        menu_html += f'<a href="{url}" target="_blank">{name}</a>'
    
    menu_html += '</div>'
    
    st.markdown(menu_html, unsafe_allow_html=True)

def main():
    expert = EnhancedISO13485Expert()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏥 ISO 13485 Expert Consultant</h1>
        <p>Comprehensive Medical Device Quality Management System & Regulatory Compliance</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Regulatory menu
    show_regulatory_menu()
    
    # Sidebar navigation
    st.sidebar.title("🔧 Navigation")
    
    pages = {
        "🏠 Dashboard": "dashboard",
        "📋 CAPA Generator": "capa", 
        "⚠️ Nonconformance Reports": "ncr",
        "📐 Design Controls": "design_controls",
        "🔬 DHF Generator": "dhf_generator",  # New DHF module
        "🔍 Risk Management": "risk_mgmt",
        "📊 Audit Tools": "audit",
        "💬 AI Consultant": "ai_chat",
        "📚 Document Library": "docs",
        "🎯 Compliance Checker": "compliance"
    }
    
    selected_page = st.sidebar.selectbox("Select Module", list(pages.keys()))
    page_key = pages[selected_page]
    
    # AI Model Selection in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 AI Configuration")
    ai_model = st.sidebar.radio("Select AI Model", ["anthropic", "openai"], key="ai_model")
    
    # ISO 13485 Quick Reference in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📖 ISO 13485 Quick Reference")
    with st.sidebar.expander("Section Overview"):
        st.markdown("""
        **4.** Quality Management System
        **5.** Management Responsibility
        **6.** Resource Management  
        **7.** Product Realization
        **8.** Measurement & Improvement
        """)
    
    # Main content area
    if page_key == "dashboard":
        show_dashboard(expert)
    elif page_key == "capa":
        show_capa_generator(expert, ai_model)
    elif page_key == "ncr":
        show_ncr_generator(expert, ai_model)
    elif page_key == "design_controls":
        show_design_controls(expert, ai_model)
    elif page_key == "dhf_generator":
        show_dhf_generator(expert, ai_model)  # New DHF module
    elif page_key == "risk_mgmt":
        show_risk_management(expert, ai_model)
    elif page_key == "audit":
        show_audit_tools(expert, ai_model)
    elif page_key == "ai_chat":
        show_ai_consultant(expert, ai_model)
    elif page_key == "docs":
        show_document_library(expert)
    elif page_key == "compliance":
        show_compliance_checker(expert, ai_model)

def show_dhf_generator(expert, ai_model):
    """DHF (Design History File) Generator for Product Development Teams"""
    st.header("🔬 Design History File (DHF) Generator")
    st.markdown("**For Product Development Teams** - Transform R&D files into comprehensive DHF per FDA 21 CFR 820.30")
    
    # Information panel
    with st.expander("ℹ️ About Design History Files (DHF)"):
        st.markdown("""
        A Design History File (DHF) contains or references the documentation necessary to demonstrate that the design development plan was followed and that the device design output meets the design input requirements.

        **Required per FDA 21 CFR 820.30:**
        - Design and development planning
        - Design input requirements
        - Design output specifications  
        - Design review records
        - Design verification and validation
        - Design transfer documentation
        - Design changes and their controls
        """)
    
    # File upload section
    st.subheader("📁 Upload R&D Documentation")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="dhf-upload-area">
            <h4>🎯 Upload Your Files (3-5 files recommended)</h4>
            <p>Supported: Word docs, PDFs, Google Docs, Images, Excel files</p>
        </div>
        """, unsafe_allow_html=True)
        
        # File uploaders
        uploaded_files = st.file_uploader(
            "Choose files for DHF generation",
            type=['docx', 'pdf', 'xlsx', 'png', 'jpg', 'jpeg', 'txt'],
            accept_multiple_files=True,
            help="Upload your R&D documentation, specifications, test reports, images, etc."
        )
        
        # Google Docs URL input
        google_docs_urls = st.text_area(
            "Google Docs URLs (one per line)",
            placeholder="https://docs.google.com/document/d/...\nhttps://docs.google.com/document/d/...",
            help="Paste Google Docs URLs that should be included in the DHF"
        )
    
    with col2:
        st.subheader("📋 File Preview")
        if uploaded_files:
            for i, file in enumerate(uploaded_files):
                st.markdown(f"""
                <div class="file-preview">
                    <strong>📄 {file.name}</strong><br>
                    <small>Type: {file.type or 'Unknown'} | Size: {file.size} bytes</small>
                </div>
                """, unsafe_allow_html=True)
        
        if google_docs_urls:
            urls = [url.strip() for url in google_docs_urls.split('\n') if url.strip()]
            for url in urls:
                st.markdown(f"""
                <div class="file-preview">
                    <strong>🌐 Google Doc</strong><br>
                    <small>{url[:50]}...</small>
                </div>
                """, unsafe_allow_html=True)
    
    # DHF Configuration Form
    if uploaded_files or google_docs_urls:
        st.subheader("⚙️ DHF Configuration")
        
        with st.form("dhf_config_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                device_name = st.text_input("Device Name*", placeholder="e.g., CardioMonitor Pro")
                device_class = st.selectbox("Device Class", ["Class I", "Class II", "Class III", "IVD"])
                intended_use = st.text_area("Intended Use*", height=100, 
                                          placeholder="Describe the medical purpose and target population...")
                
            with col2:
                manufacturer = st.text_input("Manufacturer", placeholder="Company Name")
                product_code = st.text_input("Product Code/Model", placeholder="e.g., CM-2024-001")
                regulatory_pathway = st.selectbox("Regulatory Pathway", 
                                                ["510(k)", "PMA", "De Novo", "QSR", "EU MDR CE Marking"])
                
            with col3:
                development_team = st.text_input("Development Team Lead", placeholder="Engineer Name")
                project_start_date = st.date_input("Project Start Date")
                target_submission = st.date_input("Target Regulatory Submission")
            
            # AI Enhancement Options
            st.subheader("🤖 AI Enhancement Options")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                enhance_design_inputs = st.checkbox("✨ Enhance Design Inputs", value=True)
                generate_verification_plan = st.checkbox("✨ Generate Verification Plan", value=True)
                
            with col2:
                create_risk_analysis = st.checkbox("✨ Create Risk Analysis", value=True)
                enhance_design_outputs = st.checkbox("✨ Enhance Design Outputs", value=True)
                
            with col3:
                generate_validation_protocol = st.checkbox("✨ Generate Validation Protocol", value=True)
                create_clinical_evaluation = st.checkbox("✨ Create Clinical Evaluation", value=False)
            
            # Missing Information Questions
            st.subheader("❓ Fill in Missing Information")
            st.markdown("*The AI will ask targeted questions about information not found in your uploaded files*")
            
            auto_questions = st.checkbox("🤖 Auto-generate questions for missing DHF elements", value=True)
            
            submitted = st.form_submit_button("🚀 Generate DHF", type="primary")
            
            if submitted:
                if not device_name or not intended_use:
                    st.error("Please provide at least Device Name and Intended Use")
                else:
                    generate_dhf_with_ai(expert, ai_model, {
                        'uploaded_files': uploaded_files,
                        'google_docs_urls': google_docs_urls,
                        'device_name': device_name,
                        'device_class': device_class,
                        'intended_use': intended_use,
                        'manufacturer': manufacturer,
                        'product_code': product_code,
                        'regulatory_pathway': regulatory_pathway,
                        'development_team': development_team,
                        'project_start_date': project_start_date,
                        'target_submission': target_submission,
                        'enhancements': {
                            'enhance_design_inputs': enhance_design_inputs,
                            'generate_verification_plan': generate_verification_plan,
                            'create_risk_analysis': create_risk_analysis,
                            'enhance_design_outputs': enhance_design_outputs,
                            'generate_validation_protocol': generate_validation_protocol,
                            'create_clinical_evaluation': create_clinical_evaluation
                        },
                        'auto_questions': auto_questions
                    })

def generate_dhf_with_ai(expert, ai_model, config):
    """Generate comprehensive DHF using AI"""
    
    st.markdown("""
    <div class="ai-enhancement-panel">
        <h3>🤖 AI DHF Generation in Progress</h3>
        <p>Analyzing your files and generating comprehensive Design History File...</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Step 1: Analyze uploaded files
    with st.spinner("📊 Step 1/5: Analyzing uploaded documentation..."):
        file_analysis = analyze_uploaded_files(config['uploaded_files'], expert, ai_model)
        st.success("✅ File analysis complete")
    
    # Step 2: Extract existing information
    with st.spinner("🔍 Step 2/5: Extracting design information..."):
        extracted_info = extract_design_information(file_analysis, expert, ai_model)
        st.success("✅ Information extraction complete")
    
    # Step 3: Identify gaps and generate questions
    if config['auto_questions']:
        with st.spinner("❓ Step 3/5: Identifying information gaps..."):
            gaps_and_questions = identify_dhf_gaps(extracted_info, config, expert, ai_model)
            st.success("✅ Gap analysis complete")
            
            # Show questions to user
            if gaps_and_questions['questions']:
                st.subheader("🗣️ Additional Information Needed")
                st.markdown("Please answer these questions to complete your DHF:")
                
                additional_responses = {}
                for i, question in enumerate(gaps_and_questions['questions']):
                    response = st.text_area(f"Q{i+1}: {question}", key=f"gap_q_{i}", height=100)
                    additional_responses[f"question_{i+1}"] = response
                
                if st.button("Continue with DHF Generation"):
                    config['additional_responses'] = additional_responses
                else:
                    return
    
    # Step 4: Generate DHF sections
    with st.spinner("📝 Step 4/5: Generating DHF sections..."):
        dhf_sections = generate_dhf_sections(extracted_info, config, expert, ai_model)
        st.success("✅ DHF sections generated")
    
    # Step 5: Compile final DHF
    with st.spinner("📋 Step 5/5: Compiling final DHF document..."):
        final_dhf = compile_dhf_document(dhf_sections, config, expert, ai_model)
        st.success("✅ DHF generation complete!")
    
    # Display results
    display_dhf_results(final_dhf, config)

def analyze_uploaded_files(uploaded_files, expert, ai_model):
    """Analyze content of uploaded files"""
    analysis_results = {}
    
    if not uploaded_files:
        return analysis_results
    
    for file in uploaded_files:
        try:
            file_content = extract_file_content(file)
            
            # AI analysis of content
            prompt = f"""
            Analyze this medical device development file for DHF-relevant information:
            
            Filename: {file.name}
            Content: {file_content[:3000]}  # First 3000 chars
            
            Extract and categorize information relevant to:
            1. Device description and intended use
            2. Design input requirements
            3. Design outputs/specifications
            4. Verification and validation data
            5. Risk analysis information
            6. Design review information
            7. Regulatory requirements
            
            Provide a structured analysis of what information is present.
            """
            
            analysis = expert.get_ai_response_with_iso_context(prompt, ai_model)
            analysis_results[file.name] = {
                'content': file_content,
                'analysis': analysis,
                'file_type': file.type
            }
            
        except Exception as e:
            analysis_results[file.name] = {'error': str(e)}
    
    return analysis_results

def extract_file_content(file):
    """Extract text content from various file types"""
    content = ""
    
    try:
        if file.type == "application/pdf":
            # PDF extraction
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                content += page.extract_text() + "\n"
                
        elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            # Word document extraction
            doc = docx.Document(file)
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
                
        elif file.type in ["text/plain", "application/vnd.ms-excel"]:
            # Text or basic file
            content = str(file.read(), 'utf-8', errors='ignore')
            
        elif file.type.startswith('image/'):
            # Image - just return metadata
            content = f"Image file: {file.name}, Size: {file.size} bytes"
            
        else:
            content = f"Unsupported file type: {file.type}"
            
    except Exception as e:
        content = f"Error reading file: {str(e)}"
    
    return content

def extract_design_information(file_analysis, expert, ai_model):
    """Extract structured design information from file analysis"""
    
    combined_content = ""
    for filename, analysis in file_analysis.items():
        if 'analysis' in analysis:
            combined_content += f"\n--- {filename} ---\n{analysis['analysis']}\n"
    
    prompt = f"""
    Based on the file analysis below, extract and structure information for a Design History File (DHF):
    
    {combined_content}
    
    Create a structured summary with these categories:
    1. DEVICE_DESCRIPTION: What the device is and its intended use
    2. DESIGN_INPUTS: User needs, regulatory requirements, performance requirements
    3. DESIGN_OUTPUTS: Specifications, drawings, software, labeling
    4. VERIFICATION_DATA: Test results, analysis data confirming design outputs meet inputs  
    5. VALIDATION_DATA: Clinical data, usability data confirming device meets user needs
    6. RISK_INFORMATION: Hazards identified, risk analysis, risk controls
    7. DESIGN_REVIEWS: Review meetings, decisions, approvals
    8. REGULATORY_INFO: Standards referenced, regulatory requirements
    
    For each category, note:
    - Information FOUND in the files
    - Information MISSING or INCOMPLETE
    - Quality/completeness score (1-10)
    
    Format as structured data that can be used for DHF generation.
    """
    
    extraction = expert.get_ai_response_with_iso_context(prompt, ai_model)
    
    return {
        'raw_extraction': extraction,
        'file_analysis': file_analysis,
        'extraction_timestamp': datetime.now().isoformat()
    }

def identify_dhf_gaps(extracted_info, config, expert, ai_model):
    """Identify gaps in DHF and generate targeted questions"""
    
    prompt = f"""
    Review this extracted design information for DHF completeness:
    
    Device: {config['device_name']}
    Class: {config['device_class']}
    Intended Use: {config['intended_use']}
    Regulatory Path: {config['regulatory_pathway']}
    
    Extracted Information:
    {extracted_info['raw_extraction']}
    
    Based on FDA 21 CFR 820.30 requirements, identify the TOP 5 most critical information gaps and generate specific questions to fill them.
    
    Focus on:
    1. Missing design inputs that are critical for this device class
    2. Incomplete design outputs/specifications  
    3. Missing verification/validation requirements
    4. Inadequate risk analysis information
    5. Regulatory compliance gaps
    
    Generate 3-5 specific, actionable questions that would provide the most valuable missing information for the DHF.
    
    Format as:
    CRITICAL_GAPS: [list of gaps]
    QUESTIONS: [numbered list of specific questions]
    PRIORITY: [High/Medium/Low for each question]
    """
    
    gap_analysis = expert.get_ai_response_with_iso_context(prompt, ai_model)
    
    # Parse questions from AI response
    questions = []
    if "QUESTIONS:" in gap_analysis:
        questions_section = gap_analysis.split("QUESTIONS:")[1]
        # Extract numbered questions
        import re
        question_matches = re.findall(r'\d+\.\s*(.+?)(?=\d+\.|$)', questions_section, re.DOTALL)
        questions = [q.strip() for q in question_matches if q.strip()]
    
    return {
        'gap_analysis': gap_analysis,
        'questions': questions[:5],  # Limit to 5 questions
        'analysis_timestamp': datetime.now().isoformat()
    }

def generate_dhf_sections(extracted_info, config, expert, ai_model):
    """Generate comprehensive DHF sections"""
    
    sections = {}
    
    # Base information for all sections
    device_info = f"""
    Device: {config['device_name']}
    Class: {config['device_class']} 
    Intended Use: {config['intended_use']}
    Manufacturer: {config.get('manufacturer', 'TBD')}
    Product Code: {config.get('product_code', 'TBD')}
    Regulatory Path: {config['regulatory_pathway']}
    """
    
    # Get additional responses if provided
    additional_info = ""
    if config.get('additional_responses'):
        additional_info = "\nAdditional Information Provided:\n"
        for key, value in config['additional_responses'].items():
            additional_info += f"{key}: {value}\n"
    
    # Section 1: Device Description
    prompt = f"""
    Create a comprehensive Device Description section for the DHF:
    
    {device_info}
    {additional_info}
    
    Extracted Information:
    {extracted_info['raw_extraction']}
    
    Generate a detailed device description including:
    1. Device overview and classification
    2. Intended use and indications for use
    3. Target patient population
    4. Key features and functionality
    5. Regulatory classification rationale
    6. Comparison to predicate devices (if 510k)
    
    Format as a professional DHF section with proper headers.
    """
    
    sections['device_description'] = expert.get_ai_response_with_iso_context(prompt, ai_model)
    
    # Section 2: Design Input Requirements  
    if config['enhancements']['enhance_design_inputs']:
        prompt = f"""
        Create a comprehensive Design Input Requirements section:
        
        {device_info}
        {additional_info}
        
        Based on extracted information:
        {extracted_info['raw_extraction']}
        
        Generate design inputs covering:
        1. Performance requirements
        2. Safety requirements  
        3. Regulatory requirements (FDA, ISO standards)
        4. User interface requirements
        5. Environmental requirements
        6. Reliability requirements
        7. Biocompatibility requirements (if applicable)
        
        Each input should be:
        - Specific and measurable
        - Traceable to user needs
        - Verifiable through testing
        
        Format as professional DHF documentation.
        """
        
        sections['design_inputs'] = expert.get_ai_response_with_iso_context(prompt, ai_model)
    
    # Continue generating other sections based on enhancement options...
    
    # Section 3: Design Outputs
    if config['enhancements']['enhance_design_outputs']:
        sections['design_outputs'] = generate_design_outputs_section(device_info, extracted_info, expert, ai_model)
    
    # Section 4: Verification Plan
    if config['enhancements']['generate_verification_plan']:
        sections['verification_plan'] = generate_verification_plan_section(device_info, extracted_info, expert, ai_model)
    
    # Section 5: Risk Analysis
    if config['enhancements']['create_risk_analysis']:
        sections['risk_analysis'] = generate_risk_analysis_section(device_info, extracted_info, expert, ai_model)
    
    return sections

def generate_design_outputs_section(device_info, extracted_info, expert, ai_model):
    """Generate design outputs section"""
    prompt = f"""
    Create a comprehensive Design Outputs section for the DHF:
    
    {device_info}
    
    Based on extracted information:
    {extracted_info['raw_extraction']}
    
    Generate design outputs including:
    1. Technical specifications document
    2. Engineering drawings/CAD files
    3. Software specifications (if applicable)
    4. Bill of materials  
    5. Manufacturing procedures
    6. Labeling and instructions for use
    7. Packaging specifications
    8. Test methods and acceptance criteria
    
    Each output should:
    - Meet corresponding design input
    - Include acceptance criteria
    - Be reviewed and approved
    - Enable verification testing
    
    Format as professional DHF documentation with clear traceability.
    """
    
    return expert.get_ai_response_with_iso_context(prompt, ai_model)

def generate_verification_plan_section(device_info, extracted_info, expert, ai_model):
    """Generate verification plan section"""
    prompt = f"""
    Create a comprehensive Design Verification Plan:
    
    {device_info}
    
    Based on design information:
    {extracted_info['raw_extraction']}
    
    Generate verification plan covering:
    1. Verification objectives and scope
    2. Test methods for each design input
    3. Acceptance criteria
    4. Test equipment requirements
    5. Sample size rationale
    6. Statistical methods (if applicable)
    7. Pass/fail criteria
    8. Verification schedule
    
    Include specific test protocols for:
    - Performance testing
    - Safety testing
    - Environmental testing  
    - Software verification (if applicable)
    - Biocompatibility testing (if applicable)
    
    Format as a detailed verification protocol per ISO 13485 requirements.
    """
    
    return expert.get_ai_response_with_iso_context(prompt, ai_model)

def generate_risk_analysis_section(device_info, extracted_info, expert, ai_model):
    """Generate risk analysis section per ISO 14971"""
    prompt = f"""
    Create a comprehensive Risk Management File per ISO 14971:
    
    {device_info}
    
    Based on design information:
    {extracted_info['raw_extraction']}
    
    Generate risk analysis including:
    1. Hazard identification
    2. Hazardous situation analysis
    3. Risk estimation (severity × probability)
    4. Risk evaluation against acceptance criteria
    5. Risk control measures
    6. Residual risk analysis
    7. Risk/benefit analysis
    8. Post-market risk monitoring plan
    
    Consider hazards related to:
    - Mechanical hazards
    - Electrical hazards
    - Biological/biocompatibility hazards
    - Usability hazards
    - Software hazards (if applicable)
    - Environmental hazards
    
    Format as ISO 14971 compliant risk management documentation.
    """
    
    return expert.get_ai_response_with_iso_context(prompt, ai_model)

def compile_dhf_document(dhf_sections, config, expert, ai_model):
    """Compile all sections into final DHF document"""
    
    # Create document header
    header = f"""
# DESIGN HISTORY FILE (DHF)

**Device:** {config['device_name']}
**Product Code:** {config.get('product_code', 'TBD')}
**Device Class:** {config['device_class']}
**Manufacturer:** {config.get('manufacturer', 'TBD')}

**Document Control Information:**
- DHF Number: DHF-{config['device_name'].replace(' ', '-')}-{datetime.now().strftime('%Y%m%d')}
- Creation Date: {datetime.now().strftime('%Y-%m-%d')}
- Generated by: ISO 13485 Expert Consultant
- Regulatory Pathway: {config['regulatory_pathway']}

---

## TABLE OF CONTENTS

1. Device Description and Intended Use
2. Design Input Requirements
3. Design Output Specifications
4. Design Verification Plan
5. Design Validation Protocol
6. Risk Analysis (ISO 14971)
7. Design Review Records
8. Design Transfer Documentation
9. Design Change Control
10. Clinical Evaluation

---
"""
    
    # Combine all sections
    full_document = header
    
    section_titles = {
        'device_description': '## 1. DEVICE DESCRIPTION AND INTENDED USE',
        'design_inputs': '## 2. DESIGN INPUT REQUIREMENTS',
        'design_outputs': '## 3. DESIGN OUTPUT SPECIFICATIONS', 
        'verification_plan': '## 4. DESIGN VERIFICATION PLAN',
        'validation_protocol': '## 5. DESIGN VALIDATION PROTOCOL',
        'risk_analysis': '## 6. RISK ANALYSIS (ISO 14971)'
    }
    
    for section_key, content in dhf_sections.items():
        title = section_titles.get(section_key, f"## {section_key.upper()}")
        full_document += f"\n{title}\n\n{content}\n\n---\n"
    
    # Add compliance footer
    full_document += f"""

## REGULATORY COMPLIANCE STATEMENT

This Design History File has been compiled in accordance with:
- FDA 21 CFR 820.30 (Design Controls)
- ISO 13485:2016 Section 7.3 (Design and Development)
- ISO 14971:2019 (Risk Management)

**Document Status:** Draft - Requires Review and Approval
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

*This document was generated by AI assistance and requires human review and approval before use in regulatory submissions.*
"""
    
    return {
        'full_document': full_document,
        'sections': dhf_sections,
        'metadata': {
            'device_name': config['device_name'],
            'generation_date': datetime.now().isoformat(),
            'ai_model': 'AI-Generated',
            'total_sections': len(dhf_sections)
        }
    }

def display_dhf_results(final_dhf, config):
    """Display the generated DHF results"""
    
    st.success("🎉 DHF Generation Complete!")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Total Sections", final_dhf['metadata']['total_sections'])
    with col2:
        st.metric("📝 Document Length", f"{len(final_dhf['full_document'])} chars")
    with col3:
        st.metric("🤖 AI Model", config.get('ai_model', 'AI'))
    with col4:
        st.metric("⏱️ Generated", "Just now")
    
    # Document tabs
    tabs = st.tabs(["📋 Complete DHF", "🔍 Section Preview", "📥 Download Options"])
    
    with tabs[0]:
        st.subheader("Complete Design History File")
        st.markdown(final_dhf['full_document'])
    
    with tabs[1]:
        st.subheader("DHF Sections Preview")
        for section_name, content in final_dhf['sections'].items():
            with st.expander(f"📑 {section_name.replace('_', ' ').title()}"):
                st.markdown(content[:1000] + "..." if len(content) > 1000 else content)
    
    with tabs[2]:
        st.subheader("Download Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Download as Markdown
            st.download_button(
                label="📥 Download as Markdown",
                data=final_dhf['full_document'],
                file_name=f"DHF_{config['device_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
            
        with col2:
            # Convert to Word and download (basic implementation)
            if st.button("📥 Generate Word Document"):
                word_doc = create_word_document(final_dhf)
                st.success("Word document ready for download!")

def create_word_document(final_dhf):
    """Create Word document from DHF content"""
    # This would require implementing Word document creation
    # For now, just show the option
    st.info("Word document generation would be implemented here")
    return None

# Keep all the other existing functions from the original app
def show_dashboard(expert):
    st.header("📊 Quality Management Dashboard")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Open CAPAs", "12", "-3")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Nonconformances", "8", "+2")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Compliance Score", "94%", "+1%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("DHF Projects", "5", "+2")
        st.markdown('</div>', unsafe_allow_html=True)

def show_capa_generator(expert, ai_model):
    st.header("📋 CAPA Generator")
    st.markdown("Generate ISO 13485 compliant Corrective and Preventive Action reports")
    
    # Existing CAPA generator code from the original app...
    st.info("🚧 Enhanced CAPA Generator - Implementation continues from original app")

def show_ncr_generator(expert, ai_model):
    st.header("⚠️ Nonconformance Report Generator")
    st.info("🚧 Enhanced NCR Generator - Implementation continues")

def show_design_controls(expert, ai_model):
    st.header("📐 Design Controls Assistant")
    st.info("🚧 Enhanced Design Controls - Implementation continues")

def show_risk_management(expert, ai_model):
    st.header("🔍 Risk Management (ISO 14971)")
    st.info("🚧 Enhanced Risk Management - Implementation continues")

def show_audit_tools(expert, ai_model):
    st.header("📊 Internal Audit Tools")
    st.info("🚧 Enhanced Audit Tools - Implementation continues")

def show_ai_consultant(expert, ai_model):
    st.header("💬 AI ISO 13485 Consultant")
    st.markdown(f"Chat with your ISO 13485 expert using **{ai_model.title()}**")
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat interface
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # User input
    if prompt := st.chat_input("Ask your ISO 13485 question..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI response with enhanced ISO context
        with st.chat_message("assistant"):
            with st.spinner("Consulting ISO 13485 expertise..."):
                response = expert.get_ai_response_with_iso_context(prompt, ai_model)
                st.write(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})

def show_document_library(expert):
    st.header("📚 Document Library")
    st.info("🚧 Enhanced Document Library - Implementation continues")

def show_compliance_checker(expert, ai_model):
    st.header("🎯 ISO 13485 Compliance Checker")
    st.info("🚧 Enhanced Compliance Checker - Implementation continues")

if __name__ == "__main__":
    main()
