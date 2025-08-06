# src/risk_management.py
# Comprehensive risk management system for ISO14971 and ISO13485 compliance

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import streamlit as st
from .ai_integration import DualAPIManager

class RiskCategory(Enum):
    """Risk categories per ISO14971."""
    BIOLOGICAL = "Biological and Chemical"
    ENVIRONMENTAL = "Environmental"
    HUMAN_FACTORS = "Human Factors/Usability"
    FUNCTIONAL = "Functional"
    MECHANICAL = "Mechanical"
    THERMAL = "Thermal"
    ELECTRICAL = "Electrical"
    SOFTWARE = "Software"
    MANUFACTURING = "Manufacturing/Quality"

class SeverityLevel(Enum):
    """Severity levels with numerical values."""
    NEGLIGIBLE = (1, "No injury or impairment to health")
    MINOR = (2, "Temporary injury or impairment requiring minor medical intervention")
    SERIOUS = (3, "Injury or impairment requiring professional medical intervention")
    CRITICAL = (4, "Permanent impairment or life-threatening injury")
    CATASTROPHIC = (5, "Patient death")

class ProbabilityLevel(Enum):
    """Probability levels with numerical values and frequency ranges."""
    INCREDIBLE = (1, "So unlikely, it can be assumed occurrence may not be experienced", "< 1 in 10,000,000")
    IMPROBABLE = (2, "Unlikely to occur but possible", "1 in 1,000,000 to 1 in 10,000,000")
    REMOTE = (3, "Likely to occur sometime in the life of the product", "1 in 100,000 to 1 in 1,000,000")
    OCCASIONAL = (4, "Likely to occur several times in the life of the product", "1 in 10,000 to 1 in 100,000")
    FREQUENT = (5, "Likely to occur frequently", "> 1 in 10,000")

@dataclass
class HazardousState:
    """Represents a hazardous state in the risk analysis."""
    id: str
    description: str
    category: RiskCategory
    sequence_of_events: List[str]
    harm: str
    severity: SeverityLevel
    probability: ProbabilityLevel
    detectability: Optional[int] = None  # 1-5 scale for FMECA
    risk_priority_number: Optional[int] = None
    
    def calculate_risk_score(self) -> int:
        """Calculate basic risk score (Severity × Probability)."""
        return self.severity.value[0] * self.probability.value[0]
    
    def calculate_rpn(self) -> int:
        """Calculate Risk Priority Number for FMECA (S × P × D)."""
        if self.detectability:
            return self.severity.value[0] * self.probability.value[0] * self.detectability
        return 0
    
    def get_risk_level(self) -> str:
        """Determine risk level based on score."""
        score = self.calculate_risk_score()
        if score >= 15:
            return "UNACCEPTABLE"
        elif score >= 8:
            return "UNDESIRABLE"
        elif score >= 4:
            return "ACCEPTABLE"
        else:
            return "ACCEPTABLE"

@dataclass
class RiskControlMeasure:
    """Risk control measure implementation."""
    id: str
    hazard_id: str
    description: str
    control_type: str  # "Prevention", "Protection", "Information"
    implementation_status: str  # "Planned", "Implemented", "Verified"
    verification_method: str
    verification_date: Optional[datetime] = None
    effectiveness: Optional[str] = None
    residual_risk_severity: Optional[SeverityLevel] = None
    residual_risk_probability: Optional[ProbabilityLevel] = None
    responsible_person: Optional[str] = None
    due_date: Optional[datetime] = None
    
    def calculate_residual_risk_score(self) -> int:
        """Calculate residual risk score after control implementation."""
        if self.residual_risk_severity and self.residual_risk_probability:
            return self.residual_risk_severity.value[0] * self.residual_risk_probability.value[0]
        return 0

class RiskAssessment:
    """Comprehensive risk assessment management."""
    
    def __init__(self, ai_manager: Optional[DualAPIManager] = None):
        self.ai_manager = ai_manager
        self.hazards: Dict[str, HazardousState] = {}
        self.control_measures: Dict[str, RiskControlMeasure] = {}
        self.risk_register = pd.DataFrame()
        
        # ISO14971 risk acceptability criteria
        self.risk_acceptability_matrix = self._create_risk_matrix()
    
    def _create_risk_matrix(self) -> pd.DataFrame:
        """Create risk acceptability matrix per ISO14971."""
        severity_levels = [level.value[0] for level in SeverityLevel]
        probability_levels = [level.value[0] for level in ProbabilityLevel]
        
        # Create matrix with risk acceptability
        matrix = []
        for s in severity_levels:
            row = []
            for p in probability_levels:
                score = s * p
                if score >= 15:
                    level = "UNACCEPTABLE"
                elif score >= 8:
                    level = "UNDESIRABLE"
                else:
                    level = "ACCEPTABLE"
                row.append(level)
            matrix.append(row)
        
        return pd.DataFrame(
            matrix,
            index=[f"Severity {s}" for s in severity_levels],
            columns=[f"Probability {p}" for p in probability_levels]
        )
    
    def add_hazard(
        self,
        hazard_id: str,
        description: str,
        category: RiskCategory,
        sequence_of_events: List[str],
        harm: str,
        severity: SeverityLevel,
        probability: ProbabilityLevel,
        detectability: Optional[int] = None
    ) -> HazardousState:
        """Add a new hazardous state to the assessment."""
        
        hazard = HazardousState(
            id=hazard_id,
            description=description,
            category=category,
            sequence_of_events=sequence_of_events,
            harm=harm,
            severity=severity,
            probability=probability,
            detectability=detectability
        )
        
        self.hazards[hazard_id] = hazard
        return hazard
    
    def add_control_measure(
        self,
        control_id: str,
        hazard_id: str,
        description: str,
        control_type: str,
        verification_method: str,
        responsible_person: Optional[str] = None,
        due_date: Optional[datetime] = None
    ) -> RiskControlMeasure:
        """Add a risk control measure."""
        
        if hazard_id not in self.hazards:
            raise ValueError(f"Hazard {hazard_id} not found")
        
        control = RiskControlMeasure(
            id=control_id,
            hazard_id=hazard_id,
            description=description,
            control_type=control_type,
            implementation_status="Planned",
            verification_method=verification_method,
            responsible_person=responsible_person,
            due_date=due_date
        )
        
        self.control_measures[control_id] = control
        return control
    
    def analyze_hazards_with_ai(
        self, 
        product_description: str,
        intended_use: str,
        user_groups: List[str],
        use_environment: str
    ) -> List[Dict[str, Any]]:
        """Use AI to identify potential hazards and risks."""
        
        if not self.ai_manager:
            return self._template_hazard_analysis(product_description)
        
        prompt = f"""
As a medical device risk management expert following ISO14971, perform a comprehensive hazard analysis for:

Product: {product_description}
Intended Use: {intended_use}
User Groups: {', '.join(user_groups)}
Use Environment: {use_environment}

Identify potential hazards in these categories:
1. Biological and Chemical hazards
2. Environmental hazards  
3. Human Factors/Usability hazards
4. Functional hazards
5. Mechanical hazards
6. Thermal hazards
7. Electrical hazards
8. Software hazards (if applicable)
9. Manufacturing/Quality hazards

For each identified hazard, provide:
- Hazard description
- Hazardous state
- Sequence of events leading to harm
- Potential harm
- Estimated severity (1-5, Negligible to Catastrophic)
- Estimated probability (1-5, Incredible to Frequent)

Format response as JSON array with objects containing: category, hazard_description, hazardous_state, sequence_of_events, harm, severity, probability
"""
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert in medical device risk management and ISO14971. Provide thorough, professional risk analysis."
            },
            {"role": "user", "content": prompt}
        ]
        
        try:
            provider, model_name = self.ai_manager.select_best_model("analysis", "auto")
            response = self.ai_manager.generate_completion(
                messages=messages,
                provider=provider,
                model=model_name,
                temperature=0.3
            )
            
            return json.loads(response.content)
            
        except Exception as e:
            st.warning(f"AI hazard analysis failed: {str(e)}")
            return self._template_hazard_analysis(product_description)
    
    def _template_hazard_analysis(self, product_description: str) -> List[Dict[str, Any]]:
        """Template-based hazard analysis when AI is not available."""
        return [
            {
                "category": "Mechanical",
                "hazard_description": "Sharp edges or points",
                "hazardous_state": "User contact with sharp components",
                "sequence_of_events": ["Product handling", "Contact with sharp edge", "Skin puncture"],
                "harm": "Minor laceration or puncture wound",
                "severity": 2,
                "probability": 3
            },
            {
                "category": "Functional", 
                "hazard_description": "Device malfunction",
                "hazardous_state": "Device fails to perform intended function",
                "sequence_of_events": ["Device operation", "Component failure", "Loss of function"],
                "harm": "Delayed or inadequate treatment",
                "severity": 3,
                "probability": 2
            },
            {
                "category": "Human Factors",
                "hazard_description": "Use error",
                "hazardous_state": "Incorrect device operation by user",
                "sequence_of_events": ["User training inadequate", "Incorrect operation", "Unintended result"],
                "harm": "Patient injury from misuse",
                "severity": 3,
                "probability": 3
            }
        ]
    
    def generate_risk_register(self) -> pd.DataFrame:
        """Generate comprehensive risk register DataFrame."""
        
        register_data = []
        
        for hazard_id, hazard in self.hazards.items():
            # Get associated control measures
            controls = [cm for cm in self.control_measures.values() if cm.hazard_id == hazard_id]
            
            # Calculate residual risk if controls are implemented
            residual_score = hazard.calculate_risk_score()
            residual_level = hazard.get_risk_level()
            
            if controls:
                # Use the most effective control measure for residual risk calculation
                implemented_controls = [c for c in controls if c.implementation_status == "Implemented"]
                if implemented_controls:
                    best_control = min(implemented_controls, key=lambda c: c.calculate_residual_risk_score())
                    if best_control.residual_risk_severity and best_control.residual_risk_probability:
                        residual_score = best_control.calculate_residual_risk_score()
                        if residual_score >= 15:
                            residual_level = "UNACCEPTABLE"
                        elif residual_score >= 8:
                            residual_level = "UNDESIRABLE"
                        else:
                            residual_level = "ACCEPTABLE"
            
            register_data.append({
                'Hazard_ID': hazard_id,
                'Category': hazard.category.value,
                'Hazard_Description': hazard.description,
                'Harm': hazard.harm,
                'Severity': hazard.severity.name,
                'Severity_Score': hazard.severity.value[0],
                'Probability': hazard.probability.name,
                'Probability_Score': hazard.probability.value[0],
                'Initial_Risk_Score': hazard.calculate_risk_score(),
                'Initial_Risk_Level': hazard.get_risk_level(),
                'Control_Measures': len(controls),
                'Implemented_Controls': len([c for c in controls if c.implementation_status == "Implemented"]),
                'Residual_Risk_Score': residual_score,
                'Residual_Risk_Level': residual_level,
                'RPN': hazard.calculate_rpn() if hazard.detectability else None,
                'Status': 'Controlled' if residual_level == 'ACCEPTABLE' else 'Requires Action'
            })
        
        self.risk_register = pd.DataFrame(register_data)
        return self.risk_register
    
    def get_high_priority_risks(self, threshold: int = 8) -> pd.DataFrame:
        """Get high priority risks requiring immediate attention."""
        if self.risk_register.empty:
            self.generate_risk_register()
        
        return self.risk_register[
            (self.risk_register['Initial_Risk_Score'] >= threshold) |
            (self.risk_register['Residual_Risk_Score'] >= threshold)
        ].sort_values('Initial_Risk_Score', ascending=False)
    
    def generate_risk_control_plan(self, hazard_id: str) -> Dict[str, Any]:
        """Generate comprehensive risk control plan for a specific hazard."""
        
        if hazard_id not in self.hazards:
            raise ValueError(f"Hazard {hazard_id} not found")
        
        hazard = self.hazards[hazard_id]
        controls = [cm for cm in self.control_measures.values() if cm.hazard_id == hazard_id]
        
        plan = {
            'hazard_details': {
                'id': hazard.id,
                'description': hazard.description,
                'category': hazard.category.value,
                'harm': hazard.harm,
                'initial_risk_score': hazard.calculate_risk_score(),
                'initial_risk_level': hazard.get_risk_level()
            },
            'control_measures': [],
            'implementation_timeline': [],
            'verification_plan': [],
            'residual_risk_assessment': {}
        }
        
        for control in controls:
            plan['control_measures'].append({
                'id': control.id,
                'description': control.description,
                'type': control.control_type,
                'status': control.implementation_status,
                'responsible': control.responsible_person,
                'due_date': control.due_date.strftime('%Y-%m-%d') if control.due_date else None
            })
            
            plan['verification_plan'].append({
                'control_id': control.id,
                'method': control.verification_method,
                'status': 'Planned' if not control.verification_date else 'Complete'
            })
        
        return plan
    
    def export_risk_management_file(self) -> Dict[str, pd.DataFrame]:
        """Export complete risk management documentation."""
        
        # Generate all necessary DataFrames
        risk_register = self.generate_risk_register()
        
        # Control measures summary
        controls_data = []
        for control_id, control in self.control_measures.items():
            controls_data.append({
                'Control_ID': control.id,
                'Hazard_ID': control.hazard_id,
                'Description': control.description,
                'Type': control.control_type,
                'Status': control.implementation_status,
                'Verification_Method': control.verification_method,
                'Responsible_Person': control.responsible_person,
                'Due_Date': control.due_date.strftime('%Y-%m-%d') if control.due_date else None,
                'Verification_Date': control.verification_date.strftime('%Y-%m-%d') if control.verification_date else None
            })
        
        controls_df = pd.DataFrame(controls_data)
        
        # Risk summary by category
        category_summary = risk_register.groupby('Category').agg({
            'Initial_Risk_Score': ['count', 'mean', 'max'],
            'Residual_Risk_Score': ['mean', 'max']
        }).round(2)
        
        # High priority actions
        high_priority = self.get_high_priority_risks()
        
        return {
            'Risk_Register': risk_register,
            'Control_Measures': controls_df,
            'Category_Summary': category_summary,
            'High_Priority_Risks': high_priority,
            'Risk_Matrix': self.risk_acceptability_matrix
        }

class RiskMatrix:
    """Interactive risk matrix visualization and management."""
    
    def __init__(self):
        self.severity_levels = [(s.name, s.value[0], s.value[1]) for s in SeverityLevel]
        self.probability_levels = [(p.name, p.value[0], p.value[1]) for p in ProbabilityLevel]
    
    def create_risk_matrix_plot(self, risks: List[HazardousState]) -> Any:
        """Create interactive risk matrix plot using Plotly."""
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            
            # Prepare data for plotting
            severity_scores = [risk.severity.value[0] for risk in risks]
            probability_scores = [risk.probability.value[0] for risk in risks]
            risk_scores = [risk.calculate_risk_score() for risk in risks]
            risk_descriptions = [risk.description for risk in risks]
            
            # Create color scale based on risk scores
            colors = []
            for score in risk_scores:
                if score >= 15:
                    colors.append('red')
                elif score >= 8:
                    colors.append('orange')
                else:
                    colors.append('green')
            
            # Create scatter plot
            fig = go.Figure(data=go.Scatter(
                x=probability_scores,
                y=severity_scores,
                mode='markers+text',
                marker=dict(
                    size=15,
                    color=colors,
                    line=dict(width=2, color='black')
                ),
                text=[f"R{i+1}" for i in range(len(risks))],
                textposition="middle center",
                textfont=dict(color='white', size=10),
                hovertemplate=(
                    "<b>%{text}</b><br>" +
                    "Severity: %{y}<br>" +
                    "Probability: %{x}<br>" +
                    "Risk Score: %{customdata}<br>" +
                    "<extra></extra>"
                ),
                customdata=risk_scores,
                hovertext=risk_descriptions
            ))
            
            # Add background regions
            # Unacceptable region
            fig.add_shape(
                type="rect",
                x0=3, y0=5, x1=5, y1=5,
                fillcolor="rgba(255, 0, 0, 0.2)",
                layer="below",
                line_width=0
            )
            
            # Update layout
            fig.update_layout(
                title="Risk Matrix - ISO14971 Risk Assessment",
                xaxis_title="Probability",
                yaxis_title="Severity",
                xaxis=dict(range=[0.5, 5.5], tick0=1, dtick=1),
                yaxis=dict(range=[0.5, 5.5], tick0=1, dtick=1),
                width=600,
                height=500,
                showlegend=False
            )
            
            # Add grid
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            
            return fig
            
        except ImportError:
            return None
    
    def generate_risk_heatmap(self, risk_assessment: RiskAssessment) -> pd.DataFrame:
        """Generate risk heatmap data for visualization."""
        
        # Create empty heatmap matrix
        heatmap_data = np.zeros((5, 5))
        
        for hazard in risk_assessment.hazards.values():
            sev_idx = hazard.severity.value[0] - 1
            prob_idx = hazard.probability.value[0] - 1
            heatmap_data[sev_idx][prob_idx] += 1
        
        # Create DataFrame
        severity_labels = [s[0] for s in self.severity_levels]
        probability_labels = [p[0] for p in self.probability_levels]
        
        heatmap_df = pd.DataFrame(
            heatmap_data,
            index=severity_labels,
            columns=probability_labels
        )
        
        return heatmap_df
