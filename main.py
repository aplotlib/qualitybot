import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import io
from typing import Dict, List, Optional, Any
import openai
import anthropic
import json
import base64

# Configure page
st.set_page_config(
    page_title="ISO 13485 Expert Consultant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for medical device theme
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
    
    .compliance-status {
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        color: white;
    }
    
    .status-compliant { background-color: #28a745; }
    .status-partial { background-color: #ffc107; color: black; }
    .status-non-compliant { background-color: #dc3545; }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
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
</style>
""", unsafe_allow_html=True)

class ISO13485Expert:
    """ISO 13485 Expert Consultant with AI integration"""
    
    def __init__(self):
        self.anthropic_client = None
        self.openai_client = None
        self._initialize_ai_clients()
        
        # ISO 13485 knowledge base structure
        self.iso_sections = {
            "4": "Quality Management System",
            "5": "Management Responsibility", 
            "6": "Resource Management",
            "7": "Product Realization",
            "8": "Measurement & Improvement"
        }
        
        self.document_types = {
            "CAPA": "Corrective and Preventive Action",
            "NCR": "Nonconformance Report", 
            "DHR": "Device History Record",
            "DMR": "Device Master Record",
            "Risk Assessment": "ISO 14971 Risk Management",
            "Validation Protocol": "Process Validation Protocol",
            "SOP": "Standard Operating Procedure",
            "Quality Manual": "Quality Management System Manual",
            "Design Controls": "Design Control Documentation",
            "Audit Checklist": "Internal Audit Checklist"
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
    
    def get_ai_response(self, prompt: str, model_choice: str = "anthropic") -> str:
        """Get AI response from selected model"""
        try:
            if model_choice == "anthropic" and self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    system="You are an expert ISO 13485 consultant for medical device quality management. Provide detailed, accurate, and actionable guidance based on ISO 13485:2016 requirements.",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            elif model_choice == "openai" and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert ISO 13485 consultant for medical device quality management. Provide detailed, accurate, and actionable guidance based on ISO 13485:2016 requirements."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000
                )
                return response.choices[0].message.content
            else:
                return "AI service not available. Please check API configuration."
        except Exception as e:
            return f"Error getting AI response: {str(e)}"

def main():
    expert = ISO13485Expert()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏥 ISO 13485 Expert Consultant</h1>
        <p>Medical Device Quality Management System Specialist</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("🔧 Navigation")
    
    pages = {
        "🏠 Dashboard": "dashboard",
        "📋 CAPA Generator": "capa", 
        "⚠️ Nonconformance Reports": "ncr",
        "📐 Design Controls": "design_controls",
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
    
    # Main content area
    if page_key == "dashboard":
        show_dashboard(expert)
    elif page_key == "capa":
        show_capa_generator(expert, ai_model)
    elif page_key == "ncr":
        show_ncr_generator(expert, ai_model)
    elif page_key == "design_controls":
        show_design_controls(expert, ai_model)
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
        st.metric("Overdue Items", "3", "-1")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("CAPA Trend Analysis")
        dates = pd.date_range(start='2024-01-01', periods=12, freq='M')
        capa_data = pd.DataFrame({
            'Month': dates,
            'Opened': [5, 8, 6, 10, 7, 9, 12, 8, 6, 11, 9, 7],
            'Closed': [3, 6, 8, 7, 9, 8, 10, 12, 8, 9, 11, 10]
        })
        
        fig = px.line(capa_data, x='Month', y=['Opened', 'Closed'], 
                     title="Monthly CAPA Activity")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Compliance by ISO Section")
        compliance_data = pd.DataFrame({
            'Section': ['4. QMS', '5. Management', '6. Resources', '7. Product', '8. Measurement'],
            'Compliance': [98, 92, 95, 88, 94]
        })
        
        fig = px.bar(compliance_data, x='Section', y='Compliance',
                    title="ISO 13485 Section Compliance", color='Compliance',
                    color_continuous_scale='RdYlGn')
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent activities
    st.subheader("📋 Recent Quality Activities")
    activities = pd.DataFrame({
        'Date': [datetime.now() - timedelta(days=x) for x in range(5)],
        'Activity': ['CAPA-2024-001 Initiated', 'NCR-2024-015 Closed', 'Internal Audit Completed', 'Risk Assessment Updated', 'SOP Revised'],
        'Status': ['Open', 'Closed', 'Complete', 'Complete', 'Under Review'],
        'Priority': ['High', 'Medium', 'Low', 'Medium', 'High']
    })
    st.dataframe(activities, use_container_width=True)

def show_capa_generator(expert, ai_model):
    st.header("📋 CAPA Generator")
    st.markdown("Generate ISO 13485 compliant Corrective and Preventive Action reports")
    
    with st.form("capa_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Basic Information")
            capa_number = st.text_input("CAPA Number", value=f"CAPA-{datetime.now().strftime('%Y%m%d')}-001")
            product_name = st.text_input("Product Name")
            product_id = st.text_input("Product ID/SKU") 
            department = st.selectbox("Department", ["Quality", "Engineering", "Manufacturing", "R&D"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            
        with col2:
            st.subheader("Assignment")
            assigned_to = st.text_input("Assigned To")
            due_date = st.date_input("Due Date", value=datetime.now() + timedelta(days=30))
            source = st.selectbox("Source", ["Internal Audit", "Customer Complaint", "Nonconformance", "Management Review", "Risk Assessment"])
        
        st.subheader("Problem Description")
        issue_description = st.text_area("Issue Description", height=100,
                                       placeholder="Describe the nonconformance, issue, or observation that requires corrective action...")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Root Cause Analysis")
            root_cause = st.text_area("Root Cause", height=100,
                                    placeholder="Provide thorough root cause analysis using systematic methodology...")
        
        with col2:
            st.subheader("Impact Assessment")
            impact = st.text_area("Impact Assessment", height=100,
                                placeholder="Assess potential impact on safety, efficacy, and compliance...")
        
        st.subheader("Actions")
        corrective_action = st.text_area("Corrective Actions", height=100,
                                       placeholder="Define specific actions to eliminate the root cause...")
        preventive_action = st.text_area("Preventive Actions", height=100,
                                       placeholder="Define actions to prevent recurrence...")
        
        # AI Enhancement options
        st.subheader("🤖 AI Enhancement")
        col1, col2 = st.columns(2)
        with col1:
            enhance_root_cause = st.checkbox("Enhance Root Cause Analysis")
            enhance_actions = st.checkbox("Suggest Corrective Actions")
        with col2:
            enhance_preventive = st.checkbox("Suggest Preventive Actions") 
            validate_compliance = st.checkbox("Validate ISO 13485 Compliance")
        
        submitted = st.form_submit_button("Generate CAPA", type="primary")
        
        if submitted:
            # Collect form data
            capa_data = {
                'capa_number': capa_number,
                'product_name': product_name,
                'product_id': product_id,
                'department': department,
                'priority': priority,
                'assigned_to': assigned_to,
                'due_date': due_date.strftime('%Y-%m-%d'),
                'source': source,
                'issue_description': issue_description,
                'root_cause': root_cause,
                'impact': impact,
                'corrective_action': corrective_action,
                'preventive_action': preventive_action,
                'generated_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            # AI Enhancement
            if any([enhance_root_cause, enhance_actions, enhance_preventive, validate_compliance]):
                st.subheader("🤖 AI Analysis")
                
                if enhance_root_cause and issue_description:
                    prompt = f"""Based on this medical device quality issue: "{issue_description}", provide a comprehensive root cause analysis following ISO 13485 requirements. Use systematic methodology like 5 Whys or fishbone diagram."""
                    with st.spinner("Enhancing root cause analysis..."):
                        enhanced_rca = expert.get_ai_response(prompt, ai_model)
                        st.markdown("**Enhanced Root Cause Analysis:**")
                        st.markdown(enhanced_rca)
                        if st.button("Use Enhanced Root Cause"):
                            capa_data['root_cause'] = enhanced_rca
                
                if enhance_actions and root_cause:
                    prompt = f"""Given this root cause: "{root_cause}", suggest specific corrective actions that comply with ISO 13485 requirements. Actions should be measurable, time-bound, and eliminate the root cause."""
                    with st.spinner("Generating corrective actions..."):
                        suggested_actions = expert.get_ai_response(prompt, ai_model)
                        st.markdown("**Suggested Corrective Actions:**")
                        st.markdown(suggested_actions)
                
                if enhance_preventive and issue_description:
                    prompt = f"""For this medical device issue: "{issue_description}", suggest preventive actions to prevent similar issues across all products/processes. Focus on systemic improvements per ISO 13485."""
                    with st.spinner("Generating preventive actions..."):
                        preventive_suggestions = expert.get_ai_response(prompt, ai_model)
                        st.markdown("**Suggested Preventive Actions:**")
                        st.markdown(preventive_suggestions)
                
                if validate_compliance:
                    prompt = f"""Review this CAPA for ISO 13485:2016 compliance: {json.dumps(capa_data, indent=2)}. Check completeness, identify missing elements, and suggest improvements."""
                    with st.spinner("Validating compliance..."):
                        compliance_check = expert.get_ai_response(prompt, ai_model)
                        st.markdown("**Compliance Validation:**")
                        st.markdown(compliance_check)
            
            # Generate final document
            st.subheader("📄 Generated CAPA Document")
            capa_document = generate_capa_document(capa_data)
            st.markdown(capa_document)
            
            # Download button
            st.download_button(
                label="Download CAPA Document",
                data=capa_document,
                file_name=f"{capa_number}_CAPA.md",
                mime="text/markdown"
            )

def generate_capa_document(data):
    """Generate formatted CAPA document"""
    return f"""
# CORRECTIVE AND PREVENTIVE ACTION (CAPA) REQUEST

## Document Information
- **CAPA Number:** {data.get('capa_number', 'TBD')}
- **Date Initiated:** {data.get('generated_date', datetime.now().strftime('%Y-%m-%d'))}
- **Prepared By:** {data.get('assigned_to', 'TBD')}
- **Department:** {data.get('department', 'Quality')}
- **Priority:** {data.get('priority', 'Medium')}
- **Due Date:** {data.get('due_date', 'TBD')}

## Product Information
- **Product Name:** {data.get('product_name', 'TBD')}
- **Product ID/SKU:** {data.get('product_id', 'TBD')}
- **Source:** {data.get('source', 'TBD')}

## Problem Description
**Issue Description:**
{data.get('issue_description', 'Issue description to be provided')}

**Impact Assessment:**
{data.get('impact', 'Impact assessment to be provided')}

## Root Cause Analysis
**Root Cause:**
{data.get('root_cause', 'Root cause analysis to be completed')}

## Corrective Actions
**Corrective Action Plan:**
{data.get('corrective_action', 'Corrective actions to be determined')}

**Implementation Timeline:** {data.get('due_date', 'TBD')}
**Responsible Person:** {data.get('assigned_to', 'TBD')}

## Preventive Actions
**Preventive Action Plan:**
{data.get('preventive_action', 'Preventive actions to be determined')}

## Effectiveness Verification
**Verification Method:** 
- Monitoring and measurement
- Internal audit verification
- Management review

**Success Criteria:** Elimination of root cause and prevention of recurrence

**Verification Timeline:** 90 days post-implementation

## Approval
**Quality Manager Approval:**
Name: _________________ Signature: _________________ Date: _______

**Management Representative Approval:** 
Name: _________________ Signature: _________________ Date: _______

---
*This document is controlled per ISO 13485:2016 Section 8.5.2 requirements*
*Document generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

def show_ncr_generator(expert, ai_model):
    st.header("⚠️ Nonconformance Report Generator")
    st.markdown("Generate ISO 13485 compliant nonconformance reports")
    
    # Implementation similar to CAPA generator but for NCRs
    st.info("🚧 NCR Generator - Coming in next update")

def show_design_controls(expert, ai_model):
    st.header("📐 Design Controls Assistant")
    st.markdown("ISO 13485 Section 7.3 Design Control Management")
    
    st.info("🚧 Design Controls Module - Coming in next update")

def show_risk_management(expert, ai_model):
    st.header("🔍 Risk Management (ISO 14971)")
    st.markdown("Integrated risk management for medical devices")
    
    st.info("🚧 Risk Management Module - Coming in next update")

def show_audit_tools(expert, ai_model):
    st.header("📊 Internal Audit Tools")
    st.markdown("ISO 13485 audit planning and execution tools")
    
    st.info("🚧 Audit Tools - Coming in next update")

def show_ai_consultant(expert, ai_model):
    st.header("💬 AI ISO 13485 Consultant")
    st.markdown(f"Chat with your AI consultant using **{ai_model.title()}**")
    
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
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Consulting ISO 13485 expertise..."):
                enhanced_prompt = f"""
                ISO 13485:2016 Question: {prompt}
                
                Please provide a detailed response based on ISO 13485:2016 requirements, including:
                - Specific section references where applicable
                - Practical implementation guidance
                - Common pitfalls to avoid
                - Best practices for medical device companies
                """
                
                response = expert.get_ai_response(enhanced_prompt, ai_model)
                st.write(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})

def show_document_library(expert):
    st.header("📚 Document Library")
    st.markdown("ISO 13485 templates and reference documents")
    
    # Document categories
    tabs = st.tabs(["📋 Templates", "📖 Procedures", "🔍 Checklists", "📊 Forms"])
    
    with tabs[0]:  # Templates
        st.subheader("Document Templates")
        for doc_type, description in expert.document_types.items():
            with st.expander(f"{doc_type} - {description}"):
                st.write(f"Template for {description}")
                st.button(f"Generate {doc_type}", key=f"gen_{doc_type}")
    
    with tabs[1]:  # Procedures
        st.subheader("Standard Operating Procedures")
        st.info("SOP templates for common ISO 13485 processes")
    
    with tabs[2]:  # Checklists
        st.subheader("Audit and Compliance Checklists")
        st.info("Internal audit checklists by ISO 13485 section")
    
    with tabs[3]:  # Forms
        st.subheader("Quality Forms")
        st.info("Standardized forms for quality processes")

def show_compliance_checker(expert, ai_model):
    st.header("🎯 ISO 13485 Compliance Checker")
    st.markdown("Comprehensive compliance assessment tool")
    
    # Section-by-section compliance check
    st.subheader("Compliance Assessment by Section")
    
    sections = {
        "4. Quality Management System": ["4.1 General", "4.2 Documentation"],
        "5. Management Responsibility": ["5.1 Management Commitment", "5.2 Customer Focus", "5.3 Quality Policy"],
        "6. Resource Management": ["6.1 Resources", "6.2 Human Resources", "6.3 Infrastructure"],
        "7. Product Realization": ["7.1 Planning", "7.2 Customer Processes", "7.3 Design Controls"],
        "8. Measurement & Improvement": ["8.1 General", "8.2 Monitoring", "8.3 Nonconforming Product", "8.4 Analysis", "8.5 Improvement"]
    }
    
    for section, subsections in sections.items():
        with st.expander(section):
            for subsection in subsections:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(subsection)
                with col2:
                    status = st.selectbox("Status", ["Compliant", "Partial", "Non-Compliant"], key=f"status_{subsection}")
                with col3:
                    if st.button("Check", key=f"check_{subsection}"):
                        prompt = f"Provide a detailed compliance checklist for ISO 13485:2016 {subsection}. Include specific requirements, documentation needed, and common gaps."
                        with st.spinner("Analyzing compliance requirements..."):
                            response = expert.get_ai_response(prompt, ai_model)
                            st.markdown(f"**{subsection} Requirements:**")
                            st.markdown(response)

if __name__ == "__main__":
    main()
