# src/ai_integration.py
# Dual AI integration supporting both OpenAI and Anthropic APIs

import openai
import anthropic
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import streamlit as st

@dataclass
class AIResponse:
    """Standardized AI response format."""
    content: str
    model: str
    provider: str
    tokens_used: int
    response_time: float
    metadata: Dict[str, Any]

class DualAPIManager:
    """Manages both OpenAI and Anthropic API clients."""
    
    def __init__(self, openai_key: Optional[str] = None, anthropic_key: Optional[str] = None):
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize OpenAI client
        if openai_key:
            try:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                self.openai_models = [
                    "gpt-4o",
                    "gpt-4o-mini", 
                    "gpt-4-turbo",
                    "gpt-3.5-turbo"
                ]
            except Exception as e:
                st.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Initialize Anthropic client
        if anthropic_key:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                self.anthropic_models = [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307"
                ]
            except Exception as e:
                st.warning(f"Failed to initialize Anthropic client: {e}")
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available models for each provider."""
        models = {}
        if self.openai_client:
            models["openai"] = self.openai_models
        if self.anthropic_client:
            models["anthropic"] = self.anthropic_models
        return models
    
    def select_best_model(self, task_type: str, provider_preference: str = "auto") -> tuple[str, str]:
        """
        Select the best model based on task type and provider preference.
        Returns (provider, model_name)
        """
        # Task-specific model preferences
        model_preferences = {
            "document_generation": {
                "anthropic": "claude-3-5-sonnet-20241022",
                "openai": "gpt-4o"
            },
            "analysis": {
                "anthropic": "claude-3-opus-20240229", 
                "openai": "gpt-4o"
            },
            "quick_questions": {
                "anthropic": "claude-3-haiku-20240307",
                "openai": "gpt-4o-mini"
            },
            "compliance_check": {
                "anthropic": "claude-3-5-sonnet-20241022",
                "openai": "gpt-4-turbo"
            }
        }
        
        if provider_preference == "auto":
            # Auto-select best provider for task
            if task_type in model_preferences:
                if self.anthropic_client and "anthropic" in model_preferences[task_type]:
                    return "anthropic", model_preferences[task_type]["anthropic"]
                elif self.openai_client and "openai" in model_preferences[task_type]:
                    return "openai", model_preferences[task_type]["openai"]
        elif provider_preference == "anthropic" and self.anthropic_client:
            return "anthropic", model_preferences.get(task_type, {}).get("anthropic", "claude-3-5-sonnet-20241022")
        elif provider_preference == "openai" and self.openai_client:
            return "openai", model_preferences.get(task_type, {}).get("openai", "gpt-4o")
        
        # Fallback to first available
        if self.anthropic_client:
            return "anthropic", "claude-3-5-sonnet-20241022"
        elif self.openai_client:
            return "openai", "gpt-4o"
        else:
            raise Exception("No AI providers available")
    
    def generate_completion(
        self, 
        messages: List[Dict[str, str]], 
        provider: str = None, 
        model: str = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        **kwargs
    ) -> AIResponse:
        """Generate completion using specified provider and model."""
        
        start_time = datetime.now()
        
        if provider == "anthropic" and self.anthropic_client:
            return self._anthropic_completion(messages, model, max_tokens, temperature, start_time, **kwargs)
        elif provider == "openai" and self.openai_client:
            return self._openai_completion(messages, model, max_tokens, temperature, start_time, **kwargs)
        else:
            raise ValueError(f"Provider {provider} not available or not initialized")
    
    def _anthropic_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        max_tokens: int, 
        temperature: float,
        start_time: datetime,
        **kwargs
    ) -> AIResponse:
        """Generate completion using Anthropic."""
        try:
            # Convert messages format for Anthropic
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    user_messages.append(msg)
            
            response = self.anthropic_client.messages.create(
                model=model or "claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=user_messages
            )
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            return AIResponse(
                content=response.content[0].text,
                model=model,
                provider="anthropic",
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                response_time=response_time,
                metadata={"usage": response.usage.__dict__}
            )
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def _openai_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        max_tokens: int, 
        temperature: float,
        start_time: datetime,
        **kwargs
    ) -> AIResponse:
        """Generate completion using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model=model or "gpt-4o",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            return AIResponse(
                content=response.choices[0].message.content,
                model=model,
                provider="openai", 
                tokens_used=response.usage.total_tokens,
                response_time=response_time,
                metadata={"usage": response.usage.__dict__}
            )
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

class ExpertConsultant:
    """ISO13485 Expert Consultant using dual AI capabilities."""
    
    def __init__(self, ai_manager: DualAPIManager):
        self.ai_manager = ai_manager
        self.conversation_history = []
        
        # ISO13485 knowledge base prompts
        self.system_prompt = """
You are a world-class ISO13485 expert consultant specializing in medical device quality management systems. You have deep expertise in:

- ISO13485:2016 requirements and implementation
- FDA 21 CFR Part 820 Quality System Regulation  
- EU MDR (Medical Device Regulation) 2017/745
- CAPA (Corrective and Preventive Action) processes
- Risk management per ISO14971
- Design controls and verification/validation
- Document and record control systems
- Management responsibility and review
- Supplier and purchasing controls
- Production and service provision
- Measurement, analysis and improvement
- Internal audits and regulatory inspections

Provide expert, practical advice that is:
- Accurate and compliant with current regulations
- Actionable with specific next steps
- Tailored to the medical device industry
- Professional yet accessible
- Backed by regulatory references when appropriate

Always consider the user's role and company context when providing guidance.
"""
    
    def get_expert_advice(
        self, 
        question: str, 
        context: Dict[str, Any] = None,
        model: str = "auto"
    ) -> str:
        """Get expert advice on ISO13485/medical device quality topics."""
        
        # Build context-aware prompt
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add context if provided
        if context:
            context_prompt = f"""
User Context:
- Role: {context.get('user_role', 'Quality Professional')}
- Company: {context.get('company', {}).get('name', 'Medical Device Company')}
- Regulatory Focus: {', '.join(context.get('regulatory_regions', ['ISO13485']))}

Please tailor your response to this context.
"""
            messages.append({"role": "system", "content": context_prompt})
        
        # Add conversation history (last 6 messages to maintain context)
        if self.conversation_history:
            messages.extend(self.conversation_history[-6:])
        
        # Add current question
        messages.append({"role": "user", "content": question})
        
        # Select appropriate model
        provider, model_name = self.ai_manager.select_best_model("quick_questions", model)
        
        try:
            response = self.ai_manager.generate_completion(
                messages=messages,
                provider=provider,
                model=model_name,
                temperature=0.3  # Lower temperature for more consistent expert advice
            )
            
            # Update conversation history
            self.conversation_history.extend([
                {"role": "user", "content": question},
                {"role": "assistant", "content": response.content}
            ])
            
            return response.content
            
        except Exception as e:
            return f"I apologize, but I'm experiencing technical difficulties. Error: {str(e)}"
    
    def generate_compliance_guidance(
        self, 
        regulation: str, 
        specific_requirement: str,
        company_context: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """Generate specific compliance guidance for a regulation and requirement."""
        
        prompt = f"""
Provide comprehensive compliance guidance for:

Regulation: {regulation}
Specific Requirement: {specific_requirement}

Please provide:
1. Summary of the requirement
2. Specific implementation steps
3. Required documentation
4. Common pitfalls to avoid
5. Verification/validation approach
6. Example evidence of compliance

Format as JSON with these keys: summary, implementation_steps, documentation, pitfalls, verification, examples
"""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        provider, model_name = self.ai_manager.select_best_model("compliance_check", "auto")
        
        try:
            response = self.ai_manager.generate_completion(
                messages=messages,
                provider=provider,
                model=model_name,
                temperature=0.2
            )
            
            # Parse JSON response
            return json.loads(response.content)
            
        except Exception as e:
            return {
                "error": f"Failed to generate compliance guidance: {str(e)}",
                "summary": "Unable to generate guidance at this time",
                "implementation_steps": [],
                "documentation": [],
                "pitfalls": [],
                "verification": "Manual review required",
                "examples": []
            }

class SmartDocumentAnalyzer:
    """Analyze uploaded documents using AI for quality insights."""
    
    def __init__(self, ai_manager: DualAPIManager):
        self.ai_manager = ai_manager
    
    def analyze_document(
        self, 
        document_content: str, 
        document_type: str,
        analysis_type: str = "quality_review"
    ) -> Dict[str, Any]:
        """Analyze document content and provide quality insights."""
        
        analysis_prompts = {
            "quality_review": """
Analyze this document for ISO13485 compliance and quality management best practices.
Identify:
1. Compliance strengths
2. Potential compliance gaps
3. Recommended improvements
4. Risk areas
5. Documentation completeness
""",
            "capa_analysis": """
Review this CAPA document and assess:
1. Root cause analysis adequacy
2. Corrective action effectiveness
3. Preventive action comprehensiveness
4. Timeline feasibility
5. Verification plan completeness
""",
            "audit_preparation": """
Prepare this document for regulatory audit by identifying:
1. Audit-ready sections
2. Areas needing strengthening
3. Missing evidence/documentation
4. Potential auditor questions
5. Response recommendations
"""
        }
        
        prompt = f"""
Document Type: {document_type}
Analysis Type: {analysis_type}

{analysis_prompts.get(analysis_type, analysis_prompts["quality_review"])}

Document Content:
{document_content[:8000]}  # Limit content to avoid token limits

Provide analysis as JSON with appropriate keys for the analysis type.
"""
        
        messages = [
            {"role": "system", "content": "You are an expert medical device quality analyst."},
            {"role": "user", "content": prompt}
        ]
        
        provider, model_name = self.ai_manager.select_best_model("analysis", "auto")
        
        try:
            response = self.ai_manager.generate_completion(
                messages=messages,
                provider=provider,
                model=model_name,
                temperature=0.3
            )
            
            return json.loads(response.content)
            
        except Exception as e:
            return {
                "error": f"Document analysis failed: {str(e)}",
                "analysis_type": analysis_type,
                "document_type": document_type,
                "recommendations": ["Manual review recommended due to analysis error"]
            }
