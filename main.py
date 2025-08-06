# main.py - ISO13485 Expert Consultant
# Enhanced medical device quality management system with dual AI integration

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
import json
import os
import base64
from typing import Dict, List, Optional, Any
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Import enhanced custom modules (we'll need to update these)
from src.parsers import AIFileParser, parse_file
from src.data_processing import DataProcessor, standardize_sales_data, standardize_returns_data
from src.analysis import run_full_analysis
from src.compliance import validate_capa_data, generate_compliance_checklist, get_regulatory_guidelines
from src.document_generator import CapaDocumentGenerator, ISO13485DocumentGenerator
from src.ai_integration import DualAPIManager, ExpertConsultant
from src.risk_management import RiskAssessment, RiskMatrix
from src.training_modules import TrainingLibrary, CompetencyTracker
from src.regulatory_tracker import RegulatoryTracker, AuditManager

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ISO13485 Expert Consultant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ENHANCED STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
    }
    
    .main-header h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    .feature-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border-color: #3b82f6;
    }
    
    .metric-container {
        display: flex;
        justify-content: space-around;
        flex-wrap: wrap;
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .metric-box {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        min-width: 150px;
        border: 1px solid #cbd5e1;
    }
    
    .success-badge {
        background: #10b981;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .warning-badge {
        background: #f59e0b;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .error-badge {
        background: #ef4444;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .sidebar-section {
        background: #f8fafc;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
    }
    
    .chat-message {
        background: #f1f5f9;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #3b82f6;
    }
    
    .ai-response {
        background: #ecfdf5;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #10b981;
    }
    
    .document-preview {
        background: #fafafa;
        border: 1px dashed #d1d5db;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #f1f5f9;
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
def initialize_session_state():
    """Initialize comprehensive session state for ISO13485 features."""
    defaults = {
        # Core data
        'analysis_results': None,
        'capa_data': {},
        'nonconformance_data': {},
        'audit_data': {},
        'risk_assessments': {},
        'training_records': {},
        
        # File handling
        'uploaded_files': {},
        'document_library': {},
        'templates': {},
        
        # AI Integration
        'ai_manager': None,
        'expert_consultant': None,
        'chat_history': [],
        'active_model': 'anthropic',
        
        # User preferences
        'user_role': 'Quality Manager',
        'company_info': {},
        'regulatory_regions': ['FDA', 'EU MDR', 'ISO13485'],
        
        # Dashboard data
        'dashboard_metrics': {},
        'alerts': [],
        'recent_activities': [],
        
        # Document generation
        'document_generator': None,
        'generated_documents': {},
        
        # Compliance tracking
        'compliance_status': {},
        'audit_findings': [],
        'regulatory_updates': [],
        
        # Training system
        'competency_matrix': pd.DataFrame(),
        'training_library': None,
        
        # Risk management
        'risk_register': pd.DataFrame(),
        'risk_assessments_history': []
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- AI INTEGRATION SETUP ---
def initialize_ai_systems():
    """Initialize dual AI system (OpenAI + Anthropic)."""
    if st.session_state.ai_manager is None:
        try:
            openai_key = st.secrets.get("OPENAI_API_KEY")
            anthropic_key = st.secrets.get("ANTHROPIC_API_KEY")
            
            if openai_key or anthropic_key:
                st.session_state.ai_manager = DualAPIManager(
                    openai_key=openai_key,
                    anthropic_key=anthropic_key
                )
                st.session_state.expert_consultant = ExpertConsultant(st.session_state.ai_manager)
                st.session_state.document_generator = ISO13485DocumentGenerator(
                    ai_manager=st.session_state.ai_manager
                )
                return True
            else:
                st.error("No AI API keys found in secrets. Please configure OPENAI_API_KEY and/or ANTHROPIC_API_KEY.")
                return False
        except Exception as e:
            st.error(f"Failed to initialize AI systems: {str(e)}")
            return False
    return True

# --- MAIN APPLICATION HEADER ---
def render_main_header():
    """Render the main application header."""
    st.markdown("""
    <div class="main-header">
        <h1>🏥 ISO13485 Expert Consultant</h1>
        <p>Comprehensive Medical Device Quality Management System with AI-Powered Expertise</p>
    </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
def render_sidebar():
    """Render enhanced sidebar with comprehensive navigation."""
    with st.sidebar:
        st.markdown("### 🎯 Navigation")
        
        # User profile section
        with st.expander("👤 User Profile", expanded=False):
            st.session_state.user_role = st.selectbox(
                "Your Role",
                ["Quality Manager", "Quality Engineer", "Regulatory Affairs", "QA Analyst", "Management Representative"],
                index=0
            )
            
            company_name = st.text_input("Company Name", value=st.session_state.company_info.get('name', ''))
            if company_name:
                st.session_state.company_info['name'] = company_name
        
        # AI Model Selection
        st.markdown("### 🤖 AI Configuration")
        st.session_state.active_model = st.radio(
            "Select AI Model",
            ["anthropic", "openai", "auto"],
            help="Auto mode uses the best model for each task"
        )
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        if st.button("🚨 Create CAPA", use_container_width=True):
            st.session_state.current_tab = "CAPA Management"
        
        if st.button("📋 New Nonconformance", use_container_width=True):
            st.session_state.current_tab = "Nonconformance"
        
        if st.button("🔍 Risk Assessment", use_container_width=True):
            st.session_state.current_tab = "Risk Management"
        
        if st.button("📚 Training Record", use_container_width=True):
            st.session_state.current_tab = "Training"
        
        # System Status
        st.markdown("### 📊 System Status")
        ai_status = "🟢 Active" if st.session_state.ai_manager else "🔴 Inactive"
        st.write(f"AI Systems: {ai_status}")
        
        if st.session_state.ai_manager:
            st.write(f"OpenAI: {'🟢' if st.session_state.ai_manager.openai_client else '🔴'}")
            st.write(f"Anthropic: {'🟢' if st.session_state.ai_manager.anthropic_client else '🔴'}")

# --- DASHBOARD TAB ---
def render_dashboard_tab():
    """Render comprehensive dashboard with KPIs and insights."""
    st.markdown("## 📊 Quality Management Dashboard")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🚨 Open CAPAs",
            value="12",
            delta="-2 from last month",
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            label="📋 Nonconformances",
            value="8",
            delta="+3 this week",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="✅ Compliance Score",
            value="94%",
            delta="+2% this quarter",
            delta_color="normal"
        )
    
    with col4:
        st.metric(
            label="🎯 Training Completion",
            value="87%",
            delta="+5% this month",
            delta_color="normal"
        )
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 CAPA Trends")
        # Sample data - replace with real data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        opened = [15, 12, 18, 10, 8, 12]
        closed = [10, 15, 16, 12, 15, 10]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=opened, mode='lines+markers', name='Opened', line=dict(color='#ef4444')))
        fig.add_trace(go.Scatter(x=months, y=closed, mode='lines+markers', name='Closed', line=dict(color='#10b981')))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Nonconformance Categories")
        # Sample data
        categories = ['Design Controls', 'Manufacturing', 'Supplier Quality', 'Documentation', 'Training']
        values = [25, 35, 20, 15, 5]
        
        fig = px.pie(values=values, names=categories, height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent activities
    st.markdown("### 🔔 Recent Activities")
    activities = [
        {"time": "2 hours ago", "action": "CAPA-2024-001 created for supplier quality issue", "status": "new"},
        {"time": "1 day ago", "action": "Training module 'Risk Management' completed by 15 employees", "status": "complete"},
        {"time": "2 days ago", "action": "Nonconformance NC-2024-045 closed after verification", "status": "complete"},
        {"time": "3 days ago", "action": "Internal audit scheduled for next week", "status": "pending"},
        {"time": "1 week ago", "action": "Management review meeting conducted", "status": "complete"}
    ]
    
    for activity in activities:
        badge_class = {
            "new": "warning-badge",
            "complete": "success-badge",
            "pending": "error-badge"
        }.get(activity["status"], "success-badge")
        
        st.markdown(f"""
        <div class="feature-card">
            <span class="{badge_class}">{activity["status"].upper()}</span>
            <strong>{activity["time"]}</strong>: {activity["action"]}
        </div>
        """, unsafe_allow_html=True)

# --- EXPERT CONSULTANT TAB ---
def render_expert_consultant_tab():
    """AI-powered ISO13485 expert consultation interface."""
    st.markdown("## 🤖 ISO13485 Expert Consultant")
    st.markdown("*Ask me anything about ISO13485, medical device regulations, quality management, or get help with document generation.*")
    
    if not st.session_state.expert_consultant:
        st.error("Expert consultant not available. Please check AI configuration.")
        return
    
    # Chat interface
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message">
                <strong>You:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="ai-response">
                <strong>ISO13485 Expert:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
    
    # Input area
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask your question:",
            placeholder="e.g., How do I perform a management review? What are the CAPA requirements?",
            key="expert_input"
        )
    
    with col2:
        if st.button("Send", key="send_expert"):
            if user_input:
                # Add user message
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                # Get AI response
                with st.spinner("Consulting ISO13485 expert..."):
                    response = st.session_state.expert_consultant.get_expert_advice(
                        question=user_input,
                        context={
                            "user_role": st.session_state.user_role,
                            "company": st.session_state.company_info
                        },
                        model=st.session_state.active_model
                    )
                
                # Add AI response
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
    
    # Quick consultation buttons
    st.markdown("### 🎯 Quick Consultations")
    
    quick_questions = [
        "What are the key requirements for Design Controls?",
        "How do I conduct a Management Review?",
        "What's required for CAPA effectiveness verification?",
        "Explain risk management requirements for medical devices",
        "What documentation is needed for supplier evaluation?"
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(quick_questions):
        with cols[i % 2]:
            if st.button(question, key=f"quick_{i}"):
                st.session_state.chat_history.append({"role": "user", "content": question})
                with st.spinner("Consulting expert..."):
                    response = st.session_state.expert_consultant.get_expert_advice(
                        question=question,
                        context={"user_role": st.session_state.user_role},
                        model=st.session_state.active_model
                    )
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()

# --- DOCUMENT GENERATION TAB ---
def render_document_generation_tab():
    """Comprehensive document generation with templates."""
    st.markdown("## 📄 Document Generation Center")
    
    # Document type selection
    doc_categories = {
        "🚨 CAPA Documents": [
            "CAPA Request Form",
            "CAPA Investigation Report", 
            "CAPA Effectiveness Review",
            "CAPA Closure Report"
        ],
        "📋 Nonconformance": [
            "Nonconformance Report",
            "Supplier Nonconformance",
            "Customer Complaint Form",
            "Material Review Board Report"
        ],
        "🔍 Audit & Assessment": [
            "Internal Audit Checklist",
            "Supplier Audit Report",
            "Management Review Agenda",
            "Regulatory Compliance Assessment"
        ],
        "📚 SOPs & Procedures": [
            "Document Control Procedure",
            "Training Procedure",
            "Risk Management Procedure",
            "Complaint Handling SOP"
        ],
        "🎯 Risk Management": [
            "Risk Assessment Form",
            "Risk Analysis Report",
            "Post-Market Surveillance Plan",
            "Clinical Evaluation Report"
        ]
    }
    
    selected_category = st.selectbox("Select Document Category", list(doc_categories.keys()))
    selected_document = st.selectbox("Select Document Type", doc_categories[selected_category])
    
    # Document generation form
    with st.form("document_generation_form"):
        st.markdown(f"### Generate: {selected_document}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            product_name = st.text_input("Product/Device Name")
            product_id = st.text_input("Product ID/SKU")
            department = st.selectbox("Department", ["Quality", "Engineering", "Manufacturing", "Regulatory", "Clinical"])
        
        with col2:
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            due_date = st.date_input("Due Date", value=datetime.now().date() + timedelta(days=30))
            assigned_to = st.text_input("Assigned To")
        
        issue_description = st.text_area("Issue Description / Background", height=150)
        additional_context = st.text_area("Additional Context (optional)", height=100)
        
        generate_button = st.form_submit_button("🚀 Generate Document", use_container_width=True)
        
        if generate_button and st.session_state.document_generator:
            with st.spinner(f"Generating {selected_document}..."):
                document_data = {
                    "document_type": selected_document,
                    "product_name": product_name,
                    "product_id": product_id,
                    "department": department,
                    "priority": priority,
                    "due_date": due_date.strftime("%Y-%m-%d"),
                    "assigned_to": assigned_to,
                    "issue_description": issue_description,
                    "additional_context": additional_context,
                    "generated_by": st.session_state.user_role,
                    "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                try:
                    generated_doc = st.session_state.document_generator.generate_document(
                        document_type=selected_document,
                        data=document_data,
                        model=st.session_state.active_model
                    )
                    
                    st.success(f"✅ {selected_document} generated successfully!")
                    
                    # Preview generated content
                    with st.expander("📄 Document Preview", expanded=True):
                        st.markdown(generated_doc['content'])
                    
                    # Download options
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Generate Word document
                        docx_buffer = st.session_state.document_generator.export_to_docx(generated_doc)
                        st.download_button(
                            label="📥 Download Word",
                            data=docx_buffer.getvalue(),
                            file_name=f"{selected_document.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    
                    with col2:
                        # Generate PDF (if implemented)
                        st.button("📥 Download PDF", disabled=True, help="PDF export coming soon")
                    
                    with col3:
                        # Save to library
                        if st.button("💾 Save to Library"):
                            if "generated_documents" not in st.session_state:
                                st.session_state.generated_documents = {}
                            
                            doc_id = f"{selected_document}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            st.session_state.generated_documents[doc_id] = generated_doc
                            st.success("Document saved to library!")
                
                except Exception as e:
                    st.error(f"Failed to generate document: {str(e)}")

# --- MAIN APPLICATION ---
def main():
    """Main application entry point."""
    # Initialize systems
    initialize_session_state()
    
    # Render header
    render_main_header()
    
    # Initialize AI systems
    ai_initialized = initialize_ai_systems()
    
    if not ai_initialized:
        st.warning("Some AI features may be limited. Please configure API keys in Streamlit secrets.")
    
    # Render sidebar
    render_sidebar()
    
    # Main content area with tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📊 Dashboard",
        "🤖 Expert Consultant", 
        "📄 Document Generation",
        "🚨 CAPA Management",
        "📋 Nonconformance",
        "🔍 Risk Management",
        "📚 Training & Competency",
        "⚙️ System Settings"
    ])
    
    with tab1:
        render_dashboard_tab()
    
    with tab2:
        render_expert_consultant_tab()
    
    with tab3:
        render_document_generation_tab()
    
    with tab4:
        st.markdown("## 🚨 CAPA Management")
        st.info("Enhanced CAPA management interface - Building on your existing functionality")
        # Your existing CAPA functionality would be enhanced here
    
    with tab5:
        st.markdown("## 📋 Nonconformance Management")
        st.info("Comprehensive nonconformance tracking and management")
        # New nonconformance functionality
    
    with tab6:
        st.markdown("## 🔍 Risk Management")
        st.info("Risk assessment and management tools")
        # Risk management functionality
    
    with tab7:
        st.markdown("## 📚 Training & Competency")
        st.info("Training management and competency tracking")
        # Training functionality
    
    with tab8:
        st.markdown("## ⚙️ System Settings")
        st.info("System configuration and preferences")
        # Settings functionality

if __name__ == "__main__":
    main()
