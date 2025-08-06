"""
Enhanced ISO 13485 Compliance Module
Comprehensive compliance validation and document generation
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import json
import re

class ISO13485ComplianceValidator:
    """Enhanced compliance validator with comprehensive ISO 13485:2016 knowledge"""
    
    def __init__(self):
        self.iso_requirements = self._load_iso_requirements()
        self.required_documents = self._load_required_documents()
        self.validation_criteria = self._load_validation_criteria()
    
    def _load_iso_requirements(self) -> Dict[str, Dict]:
        """Load ISO 13485:2016 requirements structure"""
        return {
            "4.1": {
                "title": "General requirements",
                "requirements": [
                    "Document quality management system",
                    "Maintain effectiveness in accordance with ISO 13485",
                    "Document role(s) undertaken by organization",
                    "Determine processes needed for QMS",
                    "Apply risk-based approach to process control",
                    "Determine sequence and interaction of processes"
                ],
                "documents": ["Quality Manual", "Process Map", "Quality Policy"]
            },
            "4.2": {
                "title": "Documentation requirements",
                "requirements": [
                    "Quality policy and objectives",
                    "Quality manual",
                    "Documented procedures required by standard",
                    "Documents for effective planning, operation, control",
                    "Medical device files",
                    "Control of documents",
                    "Control of records"
                ],
                "documents": ["Quality Manual", "Document Control Procedure", "Record Control Procedure"]
            },
            "7.3": {
                "title": "Design and development",
                "requirements": [
                    "Design and development planning",
                    "Design inputs determination", 
                    "Design outputs definition",
                    "Design reviews conducted",
                    "Design verification performed",
                    "Design validation completed",
                    "Design transfer documented",
                    "Design changes controlled",
                    "Design files maintained"
                ],
                "documents": ["Design Control Procedure", "Design History File", "Design Transfer Protocol"]
            },
            "8.3": {
                "title": "Control of nonconforming product",
                "requirements": [
                    "Identify and control nonconforming product",
                    "Document procedure for nonconformance control",
                    "Evaluate nonconformity and need for investigation",
                    "Take appropriate action for nonconforming product",
                    "Handle product detected after delivery",
                    "Document procedures for advisory notices"
                ],
                "documents": ["Nonconformance Control Procedure", "NCR Forms", "Advisory Notice Procedure"]
            },
            "8.5": {
                "title": "Improvement",
                "requirements": [
                    "Identify and implement necessary changes",
                    "Take corrective action without undue delay",
                    "Document corrective action procedure",
                    "Determine preventive actions",
                    "Document preventive action procedure",
                    "Verify effectiveness of actions taken"
                ],
                "documents": ["CAPA Procedure", "CAPA Forms", "Effectiveness Review Protocol"]
            }
        }
    
    def _load_required_documents(self) -> Dict[str, List[str]]:
        """Load required documents by ISO section"""
        return {
            "Quality Management System": [
                "Quality Manual",
                "Quality Policy",
                "Quality Objectives",
                "Process Map",
                "Document Control Procedure",
                "Record Control Procedure"
            ],
            "Management Responsibility": [
                "Management Review Procedure",
                "Management Review Records",
                "Quality Policy Communication",
                "Resource Planning"
            ],
            "Resource Management": [
                "Training Procedures",
                "Competency Records",
                "Infrastructure Requirements",
                "Work Environment Controls",
                "Contamination Control (for sterile devices)"
            ],
            "Product Realization": [
                "Design Control Procedure",
                "Design History File",
                "Device Master Record",
                "Device History Record",
                "Risk Management File",
                "Clinical Evaluation/Performance Evaluation",
                "Purchasing Procedures",
                "Supplier Evaluation",
                "Production Procedures",
                "Installation Procedures",
                "Servicing Procedures"
            ],
            "Measurement and Improvement": [
                "Customer Feedback Procedure",
                "Complaint Handling Procedure",
                "Post-Market Surveillance Procedure",
                "Internal Audit Procedure",
                "CAPA Procedure",
                "Nonconformance Control Procedure",
                "Data Analysis Procedure"
            ]
        }
    
    def _load_validation_criteria(self) -> Dict[str, Dict]:
        """Load validation criteria for different document types"""
        return {
            "CAPA": {
                "required_fields": [
                    "capa_number", "date_initiated", "problem_description",
                    "root_cause", "corrective_action", "preventive_action",
                    "assigned_to", "due_date", "effectiveness_verification"
                ],
                "format_rules": {
                    "capa_number": r"^CAPA-\d{8}-\d{3}$",
                    "date_initiated": "YYYY-MM-DD",
                    "due_date": "Must be future date"
                },
                "content_requirements": {
                    "problem_description": "Must be specific and detailed",
                    "root_cause": "Must use systematic methodology",
                    "corrective_action": "Must eliminate root cause",
                    "preventive_action": "Must prevent recurrence"
                }
            },
            "NCR": {
                "required_fields": [
                    "ncr_number", "date_identified", "nonconformance_description",
                    "disposition", "investigation_required", "corrective_action_required"
                ],
                "dispositions": [
                    "Accept As Is", "Rework", "Repair", "Return to Vendor", 
                    "Scrap", "Use Alternative Application"
                ],
                "investigation_triggers": [
                    "Customer complaint", "Safety issue", "Regulatory requirement",
                    "Repeat nonconformance", "Significant impact"
                ]
            },
            "Risk_Assessment": {
                "required_fields": [
                    "product_name", "hazards_identified", "risk_analysis",
                    "risk_evaluation", "risk_controls", "residual_risk"
                ],
                "risk_levels": ["Negligible", "Low", "Medium", "High", "Very High"],
                "control_measures": [
                    "Inherent safety by design", "Protective measures",
                    "Information for safety"
                ]
            }
        }

    def validate_capa_comprehensive(self, capa_data: Dict) -> Dict[str, Any]:
        """Comprehensive CAPA validation against ISO 13485:2016"""
        validation_result = {
            "is_valid": True,
            "compliance_score": 0,
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "iso_references": [],
            "missing_elements": []
        }
        
        # Check required fields (ISO 13485 Section 8.5.2)
        required_fields = self.validation_criteria["CAPA"]["required_fields"]
        missing_fields = [field for field in required_fields if not capa_data.get(field)]
        
        if missing_fields:
            validation_result["errors"].extend([
                f"Missing required field per ISO 13485 Section 8.5.2: {field.replace('_', ' ').title()}"
                for field in missing_fields
            ])
            validation_result["is_valid"] = False
        
        # Validate CAPA number format
        capa_number = capa_data.get("capa_number", "")
        expected_format = self.validation_criteria["CAPA"]["format_rules"]["capa_number"]
        if not re.match(expected_format, capa_number):
            validation_result["warnings"].append(
                f"CAPA number format should follow: CAPA-YYYYMMDD-XXX (e.g., CAPA-20240702-001)"
            )
        
        # Content quality assessment
        problem_desc = capa_data.get("problem_description", "").lower()
        if len(problem_desc) < 50:
            validation_result["warnings"].append(
                "Problem description appears too brief. ISO 13485 requires thorough documentation of nonconformities."
            )
        
        root_cause = capa_data.get("root_cause", "").lower()
        systematic_methods = ["5 whys", "fishbone", "fault tree", "why-why", "cause and effect"]
        if not any(method in root_cause for method in systematic_methods):
            validation_result["recommendations"].append(
                "Consider using systematic root cause analysis methods (5 Whys, Fishbone diagram, etc.) per ISO 13485 best practices."
            )
        
        # Check for vague language
        vague_terms = ["unknown", "unclear", "tbd", "to be determined", "possibly", "maybe"]
        if any(term in root_cause for term in vague_terms):
            validation_result["errors"].append(
                "Root cause analysis contains vague language. ISO 13485 Section 8.5.2 requires thorough cause determination."
            )
            validation_result["is_valid"] = False
        
        # Corrective action assessment
        corrective_action = capa_data.get("corrective_action", "").lower()
        action_verbs = ["implement", "update", "revise", "train", "modify", "install", "develop"]
        if not any(verb in corrective_action for verb in action_verbs):
            validation_result["warnings"].append(
                "Corrective actions should include specific, measurable actions with clear deliverables."
            )
        
        # Timeline validation
        if capa_data.get("due_date"):
            try:
                due_date = datetime.strptime(capa_data["due_date"], "%Y-%m-%d")
                if due_date <= datetime.now():
                    validation_result["warnings"].append(
                        "Due date should be in the future to allow adequate time for implementation."
                    )
                elif due_date > datetime.now() + timedelta(days=365):
                    validation_result["warnings"].append(
                        "Due date is more than 1 year out. ISO 13485 Section 8.5.2 requires timely corrective action."
                    )
            except ValueError:
                validation_result["errors"].append(
                    "Invalid due date format. Use YYYY-MM-DD format."
                )
                validation_result["is_valid"] = False
        
        # ISO 13485 specific requirements check
        iso_requirements = [
            "Review nonconformities (8.5.2.a)",
            "Determine causes of nonconformities (8.5.2.b)", 
            "Evaluate need for action (8.5.2.c)",
            "Plan and implement action (8.5.2.d)",
            "Verify action effectiveness (8.5.2.f)"
        ]
        
        validation_result["iso_references"] = iso_requirements
        
        # Calculate compliance score
        total_checks = len(required_fields) + 5  # 5 additional quality checks
        passed_checks = total_checks - len(validation_result["errors"]) - len(validation_result["warnings"])
        validation_result["compliance_score"] = max(0, (passed_checks / total_checks) * 100)
        
        return validation_result

    def validate_document_completeness(self, document_type: str, document_data: Dict) -> Dict[str, Any]:
        """Validate document completeness against ISO requirements"""
        if document_type not in self.validation_criteria:
            return {"error": f"Unknown document type: {document_type}"}
        
        criteria = self.validation_criteria[document_type]
        validation_result = {
            "document_type": document_type,
            "is_complete": True,
            "completeness_score": 0,
            "missing_fields": [],
            "format_issues": [],
            "content_issues": []
        }
        
        # Check required fields
        required_fields = criteria.get("required_fields", [])
        missing_fields = [field for field in required_fields if not document_data.get(field)]
        validation_result["missing_fields"] = missing_fields
        
        if missing_fields:
            validation_result["is_complete"] = False
        
        # Calculate completeness score
        if required_fields:
            provided_fields = len(required_fields) - len(missing_fields)
            validation_result["completeness_score"] = (provided_fields / len(required_fields)) * 100
        
        return validation_result

    def generate_compliance_report(self, organization_data: Dict) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        report = {
            "organization": organization_data.get("name", "Unknown"),
            "assessment_date": datetime.now().strftime("%Y-%m-%d"),
            "overall_compliance": 0,
            "section_compliance": {},
            "critical_gaps": [],
            "recommendations": [],
            "action_items": []
        }
        
        # Assess each ISO section
        total_score = 0
        section_count = 0
        
        for section_id, section_info in self.iso_requirements.items():
            section_score = self._assess_section_compliance(section_id, organization_data)
            report["section_compliance"][section_id] = {
                "title": section_info["title"],
                "score": section_score,
                "status": self._get_compliance_status(section_score)
            }
            total_score += section_score
            section_count += 1
        
        report["overall_compliance"] = total_score / section_count if section_count > 0 else 0
        
        # Identify critical gaps
        for section_id, compliance_info in report["section_compliance"].items():
            if compliance_info["score"] < 70:
                report["critical_gaps"].append({
                    "section": f"{section_id} - {compliance_info['title']}",
                    "score": compliance_info["score"],
                    "priority": "High" if compliance_info["score"] < 50 else "Medium"
                })
        
        return report

    def _assess_section_compliance(self, section_id: str, org_data: Dict) -> float:
        """Assess compliance for a specific ISO section"""
        # Placeholder assessment logic - in real implementation, 
        # this would check against actual documentation and processes
        section_data = org_data.get(f"section_{section_id}", {})
        
        required_items = len(self.iso_requirements.get(section_id, {}).get("requirements", []))
        implemented_items = len(section_data.get("implemented", []))
        
        if required_items == 0:
            return 100.0
        
        return min(100.0, (implemented_items / required_items) * 100)

    def _get_compliance_status(self, score: float) -> str:
        """Get compliance status based on score"""
        if score >= 95:
            return "Fully Compliant"
        elif score >= 85:
            return "Substantially Compliant"
        elif score >= 70:
            return "Partially Compliant"
        else:
            return "Non-Compliant"

    def generate_iso_checklist(self, section: str) -> Dict[str, Any]:
        """Generate detailed checklist for specific ISO section"""
        if section not in self.iso_requirements:
            return {"error": f"Unknown ISO section: {section}"}
        
        section_info = self.iso_requirements[section]
        checklist = {
            "section": section,
            "title": section_info["title"],
            "requirements": [],
            "documents_needed": section_info.get("documents", []),
            "checkpoints": []
        }
        
        for req in section_info.get("requirements", []):
            checklist["requirements"].append({
                "requirement": req,
                "status": "Not Assessed",
                "evidence": "",
                "notes": ""
            })
        
        return checklist

class DocumentGenerator:
    """Enhanced document generator for ISO 13485 compliance"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load document templates"""
        return {
            "quality_manual": self._get_quality_manual_template(),
            "sop": self._get_sop_template(),
            "audit_checklist": self._get_audit_checklist_template(),
            "training_record": self._get_training_record_template()
        }
    
    def _get_quality_manual_template(self) -> str:
        """Quality Manual template per ISO 13485 Section 4.2.2"""
        return """
# QUALITY MANUAL

**Document ID:** QM-001  
**Revision:** {revision}  
**Effective Date:** {effective_date}  
**Prepared by:** {prepared_by}  
**Approved by:** {approved_by}  

## 1. SCOPE OF QUALITY MANAGEMENT SYSTEM

### 1.1 Organization Role
{organization_name} operates as a {role} under applicable regulatory requirements.

### 1.2 Scope Statement
This Quality Management System applies to {scope_statement}

### 1.3 Exclusions and Justifications
{exclusions}

## 2. QUALITY POLICY

{quality_policy}

## 3. QMS DOCUMENTATION STRUCTURE

### 3.1 Level 1: Quality Manual
This document defines the quality management system structure.

### 3.2 Level 2: Procedures
Standard Operating Procedures define how processes are executed.

### 3.3 Level 3: Work Instructions
Detailed instructions for specific tasks.

### 3.4 Level 4: Forms and Records
Templates and records that provide evidence of conformity.

## 4. PROCESS INTERACTION

{process_map_description}

## 5. REFERENCES TO PROCEDURES

{procedure_references}

---
*This document is controlled per ISO 13485:2016 Section 4.2*
"""
    
    def _get_sop_template(self) -> str:
        """Standard Operating Procedure template"""
        return """
# STANDARD OPERATING PROCEDURE

**Document ID:** {document_id}  
**Title:** {title}  
**Revision:** {revision}  
**Effective Date:** {effective_date}  

## 1. PURPOSE
{purpose}

## 2. SCOPE
{scope}

## 3. RESPONSIBILITIES
{responsibilities}

## 4. PROCEDURE
{procedure_steps}

## 5. RECORDS
{records_required}

## 6. REFERENCES
- ISO 13485:2016
- {additional_references}

---
**Revision History:**
| Revision | Date | Description | Approved By |
|----------|------|-------------|-------------|
| {revision} | {effective_date} | {change_description} | {approver} |
"""
    
    def _get_audit_checklist_template(self) -> str:
        """Internal audit checklist template"""
        return """
# INTERNAL AUDIT CHECKLIST

**Audit Date:** {audit_date}  
**Auditor:** {auditor}  
**Area/Process:** {audit_area}  
**ISO Section:** {iso_section}  

## AUDIT CRITERIA
ISO 13485:2016 Section {iso_section}: {section_title}

## AUDIT QUESTIONS

{audit_questions}

## FINDINGS

### Conformities
{conformities}

### Nonconformities  
{nonconformities}

### Opportunities for Improvement
{improvements}

## CONCLUSION
{conclusion}

**Auditor Signature:** _________________ **Date:** _______
**Auditee Signature:** _________________ **Date:** _______
"""
    
    def _get_training_record_template(self) -> str:
        """Training record template per ISO 13485 Section 6.2"""
        return """
# TRAINING RECORD

**Employee:** {employee_name}  
**Position:** {position}  
**Department:** {department}  
**Training Date:** {training_date}  

## TRAINING DETAILS
**Training Topic:** {training_topic}  
**Duration:** {duration}  
**Trainer:** {trainer}  
**Training Method:** {method}

## COMPETENCY ASSESSMENT
{assessment_criteria}

## RESULTS
**Assessment Score:** {score}  
**Pass/Fail:** {result}  
**Comments:** {comments}

## EFFECTIVENESS EVALUATION
**Evaluation Date:** {eval_date}  
**Effectiveness:** {effectiveness}  
**Additional Training Required:** {additional_training}

**Supervisor Signature:** _________________ **Date:** _______
**Employee Signature:** _________________ **Date:** _______
"""

    def generate_document(self, doc_type: str, data: Dict) -> str:
        """Generate document from template"""
        if doc_type not in self.templates:
            return f"Error: Unknown document type '{doc_type}'"
        
        template = self.templates[doc_type]
        
        try:
            return template.format(**data)
        except KeyError as e:
            return f"Error: Missing required data field {e}"

# Usage examples and helper functions
def create_iso13485_dashboard_data():
    """Create sample data for ISO 13485 dashboard"""
    return {
        "sections": {
            "4": {"name": "QMS", "compliance": 95, "status": "Compliant"},
            "5": {"name": "Management", "compliance": 88, "status": "Substantial"}, 
            "6": {"name": "Resources", "compliance": 92, "status": "Compliant"},
            "7": {"name": "Product", "compliance": 78, "status": "Partial"},
            "8": {"name": "Measurement", "compliance": 85, "status": "Substantial"}
        },
        "recent_capas": [
            {"number": "CAPA-20241201-001", "status": "Open", "priority": "High"},
            {"number": "CAPA-20241125-002", "status": "Closed", "priority": "Medium"},
            {"number": "CAPA-20241120-003", "status": "Under Review", "priority": "Low"}
        ],
        "metrics": {
            "total_nonconformances": 23,
            "open_capas": 12,
            "overdue_actions": 3,
            "compliance_score": 87.6
        }
    }
