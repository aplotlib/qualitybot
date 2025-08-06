"""
AI-Enhanced Document Generation Engine for ISO 13485
Integrates with OpenAI and Anthropic for intelligent document creation
"""

import openai
import anthropic
from typing import Dict, List, Optional, Any, Union
import json
import re
from datetime import datetime, timedelta
import streamlit as st

class AIDocumentEngine:
    """AI-powered document generation for ISO 13485 compliance"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self._initialize_clients()
        
        self.iso_expertise = {
            "sections": {
                "4.1": "Quality Management System - General Requirements",
                "4.2": "Documentation Requirements",
                "5.1": "Management Commitment",
                "5.2": "Customer Focus", 
                "5.3": "Quality Policy",
                "5.4": "Planning",
                "5.5": "Responsibility and Authority",
                "5.6": "Management Review",
                "6.1": "Provision of Resources",
                "6.2": "Human Resources",
                "6.3": "Infrastructure",
                "6.4": "Work Environment",
                "7.1": "Planning of Product Realization",
                "7.2": "Customer-related Processes",
                "7.3": "Design and Development",
                "7.4": "Purchasing",
                "7.5": "Production and Service Provision",
                "7.6": "Control of Monitoring and Measuring Equipment",
                "8.1": "General (Measurement)",
                "8.2": "Monitoring and Measurement",
                "8.3": "Control of Nonconforming Product",
                "8.4": "Analysis of Data",
                "8.5": "Improvement"
            },
            "key_concepts": {
                "risk_management": "ISO 14971 - Application of risk management to medical devices",
                "design_controls": "7.3 - Systematic approach to design and development",
                "capa": "8.5 - Corrective and Preventive Action processes",
                "post_market": "8.2.2 - Complaint handling and post-market surveillance",
                "validation": "Process validation and software validation requirements",
                "sterile_devices": "Special requirements for sterile medical devices"
            }
        }
        
        self.document_templates = {
            "capa": self._get_capa_template(),
            "ncr": self._get_ncr_template(),
            "risk_assessment": self._get_risk_template(),
            "sop": self._get_sop_template(),
            "validation_protocol": self._get_validation_template()
        }

    def _initialize_clients(self):
        """Initialize AI clients"""
        try:
            if 'openai_api_key' in st.secrets:
                self.openai_client = openai.OpenAI(api_key=st.secrets['openai_api_key'])
            if 'anthropic_api_key' in st.secrets:
                self.anthropic_client = anthropic.Anthropic(api_key=st.secrets['anthropic_api_key'])
        except Exception as e:
            print(f"Warning: Could not initialize AI clients: {e}")

    def generate_enhanced_capa(self, basic_data: Dict, ai_model: str = "anthropic") -> Dict[str, str]:
        """Generate AI-enhanced CAPA with comprehensive analysis"""
        
        enhancements = {
            "enhanced_problem_description": "",
            "comprehensive_root_cause": "",
            "systematic_corrective_actions": "",
            "preventive_action_strategy": "",
            "risk_assessment": "",
            "effectiveness_measures": "",
            "regulatory_considerations": ""
        }
        
        # Enhance problem description
        if basic_data.get("issue_description"):
            prompt = f"""
            As an ISO 13485 expert, enhance this medical device quality issue description to ensure it meets regulatory documentation standards:
            
            Original: {basic_data['issue_description']}
            Product: {basic_data.get('product_name', 'Medical Device')}
            
            Provide a comprehensive problem description that includes:
            1. Clear identification of the nonconformance
            2. Impact on product safety and efficacy
            3. Scope and extent of the issue
            4. Regulatory implications
            5. Patient safety considerations
            
            Format as a professional quality management document.
            """
            
            enhancements["enhanced_problem_description"] = self._get_ai_response(prompt, ai_model)
        
        # Generate comprehensive root cause analysis
        if basic_data.get("issue_description"):
            prompt = f"""
            Conduct a systematic root cause analysis for this medical device quality issue using ISO 13485 methodology:
            
            Issue: {basic_data['issue_description']}
            Initial Root Cause (if provided): {basic_data.get('root_cause', 'Not specified')}
            
            Provide:
            1. 5 Whys analysis
            2. Potential contributing factors (Man, Machine, Material, Method, Environment)
            3. System-level causes
            4. Process breakdown analysis
            5. Evidence requirements for verification
            
            Ensure the analysis is thorough enough to support effective corrective action per ISO 13485 Section 8.5.2.
            """
            
            enhancements["comprehensive_root_cause"] = self._get_ai_response(prompt, ai_model)
        
        # Generate systematic corrective actions
        if basic_data.get("root_cause") or enhancements.get("comprehensive_root_cause"):
            root_cause = basic_data.get("root_cause") or "See comprehensive analysis above"
            prompt = f"""
            Based on this root cause analysis for a medical device quality issue, provide systematic corrective actions per ISO 13485:
            
            Root Cause: {root_cause}
            Product Type: {basic_data.get('product_name', 'Medical Device')}
            Department: {basic_data.get('department', 'Quality')}
            
            Provide corrective actions that:
            1. Directly eliminate the root cause
            2. Are specific, measurable, and time-bound
            3. Include responsibility assignments
            4. Address immediate and long-term solutions
            5. Consider regulatory requirements
            6. Include verification methods
            
            Structure as actionable steps with clear deliverables.
            """
            
            enhancements["systematic_corrective_actions"] = self._get_ai_response(prompt, ai_model)
        
        # Generate preventive action strategy
        if basic_data.get("issue_description"):
            prompt = f"""
            Develop a comprehensive preventive action strategy for this medical device quality issue per ISO 13485 Section 8.5.3:
            
            Issue: {basic_data['issue_description']}
            Product: {basic_data.get('product_name', 'Medical Device')}
            
            Provide preventive actions that:
            1. Prevent similar issues across all products/processes
            2. Address systemic vulnerabilities
            3. Include process improvements
            4. Consider training and competency
            5. Address supplier/vendor considerations
            6. Include monitoring and detection systems
            
            Focus on system-wide improvements and risk mitigation.
            """
            
            enhancements["preventive_action_strategy"] = self._get_ai_response(prompt, ai_model)
        
        # Generate risk assessment
        prompt = f"""
        Conduct a risk assessment for this medical device quality issue per ISO 14971 principles:
        
        Issue: {basic_data.get('issue_description', 'Medical device quality issue')}
        Product: {basic_data.get('product_name', 'Medical Device')}
        Severity: {basic_data.get('priority', 'Medium')}
        
        Assess:
        1. Patient safety risk
        2. Product performance risk  
        3. Regulatory compliance risk
        4. Business/reputation risk
        5. Risk controls needed
        6. Residual risk after controls
        
        Provide risk level (Low/Medium/High) with justification.
        """
        
        enhancements["risk_assessment"] = self._get_ai_response(prompt, ai_model)
        
        # Generate effectiveness measures
        prompt = f"""
        Define effectiveness verification measures for this CAPA per ISO 13485 Section 8.5.2(f):
        
        Corrective Actions: {basic_data.get('corrective_action', 'To be defined')}
        Preventive Actions: {basic_data.get('preventive_action', 'To be defined')}
        
        Provide:
        1. Objective success criteria
        2. Measurable performance indicators
        3. Monitoring methods and frequency
        4. Timeline for effectiveness review
        5. Verification responsibilities
        6. Documentation requirements
        
        Ensure measures can definitively prove action effectiveness.
        """
        
        enhancements["effectiveness_measures"] = self._get_ai_response(prompt, ai_model)
        
        # Generate regulatory considerations
        prompt = f"""
        Identify regulatory considerations for this medical device CAPA:
        
        Issue Type: {basic_data.get('issue_description', 'Quality issue')}
        Product: {basic_data.get('product_name', 'Medical Device')}
        Severity: {basic_data.get('priority', 'Medium')}
        
        Consider:
        1. FDA reporting requirements (MDR, 21 CFR 803)
        2. EU MDR requirements  
        3. Notified body notifications
        4. ISO 13485 audit implications
        5. Customer notifications
        6. Regulatory submission impacts
        
        Provide specific regulatory actions required.
        """
        
        enhancements["regulatory_considerations"] = self._get_ai_response(prompt, ai_model)
        
        return enhancements

    def generate_comprehensive_ncr(self, basic_data: Dict, ai_model: str = "anthropic") -> Dict[str, str]:
        """Generate comprehensive NCR with AI enhancement"""
        
        prompt = f"""
        Generate a comprehensive Nonconformance Report for this medical device quality issue per ISO 13485 Section 8.3:
        
        Issue: {basic_data.get('issue_description', 'Nonconformance identified')}
        Product: {basic_data.get('product_name', 'Medical Device')}
        Detected: {basic_data.get('detection_stage', 'During process')}
        
        Provide:
        1. Clear nonconformance description
        2. Immediate containment actions
        3. Investigation plan
        4. Disposition recommendation with justification
        5. Corrective action requirements
        6. Verification plan
        
        Ensure compliance with ISO 13485:2016 documentation requirements.
        """
        
        comprehensive_ncr = self._get_ai_response(prompt, ai_model)
        
        return {"comprehensive_ncr": comprehensive_ncr}

    def generate_risk_management_file(self, product_data: Dict, ai_model: str = "anthropic") -> Dict[str, str]:
        """Generate risk management file per ISO 14971"""
        
        prompt = f"""
        Create a comprehensive Risk Management File structure for this medical device per ISO 14971:
        
        Product: {product_data.get('product_name', 'Medical Device')}
        Intended Use: {product_data.get('intended_use', 'Medical treatment')}
        User Group: {product_data.get('user_group', 'Healthcare professionals')}
        Use Environment: {product_data.get('environment', 'Clinical setting')}
        
        Provide:
        1. Hazard identification and analysis
        2. Risk analysis methodology
        3. Risk evaluation criteria  
        4. Risk control measures hierarchy
        5. Residual risk assessment
        6. Risk/benefit analysis
        7. Post-market risk monitoring
        
        Structure as a complete risk management framework.
        """
        
        risk_file = self._get_ai_response(prompt, ai_model)
        
        return {"risk_management_file": risk_file}

    def generate_validation_protocol(self, process_data: Dict, ai_model: str = "anthropic") -> Dict[str, str]:
        """Generate process validation protocol"""
        
        prompt = f"""
        Create a Process Validation Protocol per ISO 13485 Section 7.5.6:
        
        Process: {process_data.get('process_name', 'Manufacturing Process')}
        Product: {process_data.get('product_name', 'Medical Device')}
        Critical Parameters: {process_data.get('critical_params', 'To be identified')}
        
        Include:
        1. Validation objectives and scope
        2. Acceptance criteria definition
        3. Process parameter identification
        4. Statistical methodology
        5. Sampling plan rationale
        6. Test methods and equipment
        7. Documentation requirements
        8. Re-validation triggers
        
        Ensure statistical rigor and regulatory compliance.
        """
        
        protocol = self._get_ai_response(prompt, ai_model)
        
        return {"validation_protocol": protocol}

    def generate_audit_checklist(self, section: str, ai_model: str = "anthropic") -> Dict[str, str]:
        """Generate detailed audit checklist for ISO section"""
        
        section_title = self.iso_expertise["sections"].get(section, f"ISO Section {section}")
        
        prompt = f"""
        Create a detailed internal audit checklist for ISO 13485:2016 Section {section} - {section_title}:
        
        Include:
        1. Audit objectives specific to this section
        2. Key requirements to verify
        3. Evidence to examine
        4. Interview questions
        5. Observation points
        6. Documentation to review
        7. Common nonconformances
        8. Best practice indicators
        
        Structure as a practical auditor tool with scoring methodology.
        """
        
        checklist = self._get_ai_response(prompt, ai_model)
        
        return {"audit_checklist": checklist}

    def analyze_compliance_gaps(self, current_state: Dict, target_section: str, ai_model: str = "anthropic") -> Dict[str, str]:
        """Analyze compliance gaps and provide roadmap"""
        
        prompt = f"""
        Analyze compliance gaps for ISO 13485:2016 Section {target_section}:
        
        Current State: {json.dumps(current_state, indent=2)}
        Target Section: {self.iso_expertise["sections"].get(target_section, target_section)}
        
        Provide:
        1. Gap analysis summary
        2. Priority ranking of gaps
        3. Implementation roadmap
        4. Resource requirements
        5. Timeline recommendations
        6. Risk assessment of gaps
        7. Quick wins identification
        8. Long-term strategic recommendations
        
        Focus on practical, actionable guidance.
        """
        
        analysis = self._get_ai_response(prompt, ai_model)
        
        return {"gap_analysis": analysis}

    def _get_ai_response(self, prompt: str, model: str = "anthropic") -> str:
        """Get response from specified AI model"""
        try:
            if model == "anthropic" and self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    system="You are a world-class ISO 13485 expert consultant specializing in medical device quality management systems. Provide detailed, accurate, and actionable guidance that ensures full regulatory compliance.",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
                
            elif model == "openai" and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a world-class ISO 13485 expert consultant specializing in medical device quality management systems. Provide detailed, accurate, and actionable guidance that ensures full regulatory compliance."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000
                )
                return response.choices[0].message.content
                
            else:
                return f"AI service not available. Model: {model}"
                
        except Exception as e:
            return f"Error generating AI response: {str(e)}"

    def _get_capa_template(self) -> str:
        """CAPA document template"""
        return """
# CORRECTIVE AND PREVENTIVE ACTION (CAPA)

**CAPA Number:** {capa_number}
**Date Initiated:** {date_initiated}
**Priority:** {priority}
**Assigned To:** {assigned_to}
**Due Date:** {due_date}

## PROBLEM IDENTIFICATION
{problem_description}

## ROOT CAUSE ANALYSIS
{root_cause_analysis}

## CORRECTIVE ACTIONS
{corrective_actions}

## PREVENTIVE ACTIONS  
{preventive_actions}

## RISK ASSESSMENT
{risk_assessment}

## EFFECTIVENESS VERIFICATION
{effectiveness_verification}

## REGULATORY CONSIDERATIONS
{regulatory_considerations}

---
*Generated with AI assistance for ISO 13485:2016 compliance*
"""

    def _get_ncr_template(self) -> str:
        """NCR template"""
        return """
# NONCONFORMANCE REPORT

**NCR Number:** {ncr_number}
**Date:** {date}
**Product:** {product}
**Detected By:** {detected_by}

## NONCONFORMANCE DESCRIPTION
{description}

## IMMEDIATE ACTIONS
{immediate_actions}

## DISPOSITION
{disposition}

## INVESTIGATION REQUIRED
{investigation}

## FOLLOW-UP ACTIONS
{followup_actions}

---
*Per ISO 13485:2016 Section 8.3*
"""

    def _get_risk_template(self) -> str:
        """Risk assessment template"""
        return """
# RISK ASSESSMENT

**Product:** {product_name}
**Assessment Date:** {date}
**Conducted By:** {assessor}

## HAZARD IDENTIFICATION
{hazards}

## RISK ANALYSIS
{risk_analysis}

## RISK EVALUATION
{risk_evaluation}

## RISK CONTROLS
{risk_controls}

## RESIDUAL RISK
{residual_risk}

---
*Per ISO 14971 Risk Management*
"""

    def _get_sop_template(self) -> str:
        """SOP template"""
        return """
# STANDARD OPERATING PROCEDURE

**Document ID:** {doc_id}
**Title:** {title}
**Revision:** {revision}
**Effective Date:** {date}

## PURPOSE
{purpose}

## SCOPE
{scope}

## PROCEDURE
{procedure}

## RECORDS
{records}

---
*ISO 13485 Controlled Document*
"""

    def _get_validation_template(self) -> str:
        """Validation protocol template"""
        return """
# PROCESS VALIDATION PROTOCOL

**Process:** {process_name}
**Protocol Number:** {protocol_number}
**Date:** {date}

## OBJECTIVES
{objectives}

## SCOPE
{scope}

## ACCEPTANCE CRITERIA
{acceptance_criteria}

## TEST METHODS
{test_methods}

## SAMPLING PLAN
{sampling_plan}

## STATISTICAL ANALYSIS
{statistical_analysis}

---
*Per ISO 13485:2016 Section 7.5.6*
"""

# Utility functions for integration with Streamlit app

def create_ai_enhanced_capa_form():
    """Create Streamlit form for AI-enhanced CAPA generation"""
    st.subheader("🤖 AI-Enhanced CAPA Generator")
    st.markdown("Generate comprehensive CAPA with AI analysis and recommendations")
    
    with st.form("ai_capa_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            product_name = st.text_input("Product Name")
            issue_description = st.text_area("Issue Description", height=100)
            department = st.selectbox("Department", ["Quality", "Engineering", "Manufacturing", "R&D"])
            
        with col2:
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            assigned_to = st.text_input("Assigned To")
            due_date = st.date_input("Due Date")
        
        st.subheader("AI Enhancement Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            enhance_problem = st.checkbox("Enhance Problem Description")
            enhance_root_cause = st.checkbox("Generate Root Cause Analysis")
            
        with col2:
            enhance_corrective = st.checkbox("Generate Corrective Actions")
            enhance_preventive = st.checkbox("Generate Preventive Actions")
            
        with col3:
            add_risk_assessment = st.checkbox("Add Risk Assessment")
            add_effectiveness = st.checkbox("Add Effectiveness Measures")
        
        ai_model = st.selectbox("AI Model", ["anthropic", "openai"])
        
        submitted = st.form_submit_button("Generate AI-Enhanced CAPA", type="primary")
        
        return {
            "submitted": submitted,
            "data": {
                "product_name": product_name,
                "issue_description": issue_description,
                "department": department,
                "priority": priority,
                "assigned_to": assigned_to,
                "due_date": due_date.strftime("%Y-%m-%d") if due_date else "",
            },
            "enhancements": {
                "enhance_problem": enhance_problem,
                "enhance_root_cause": enhance_root_cause,
                "enhance_corrective": enhance_corrective,
                "enhance_preventive": enhance_preventive,
                "add_risk_assessment": add_risk_assessment,
                "add_effectiveness": add_effectiveness
            },
            "ai_model": ai_model
        }

def display_ai_generated_content(content: Dict[str, str]):
    """Display AI-generated content in organized tabs"""
    if not content:
        st.warning("No AI-generated content to display")
        return
    
    tabs = st.tabs(list(content.keys()))
    
    for i, (key, value) in enumerate(content.items()):
        with tabs[i]:
            st.markdown(value)
            
            # Add copy button for each section
            if st.button(f"Copy {key.replace('_', ' ').title()}", key=f"copy_{key}"):
                st.success(f"Content copied to clipboard!")
