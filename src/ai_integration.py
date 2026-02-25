# src/ai_integration.py
# OpenAI-only AI integration for regulatory intelligence

import openai
from typing import Dict, List, Optional, Any
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


OPENAI_MODEL = "gpt-4o"


class AIManager:
    """Manages OpenAI API client for regulatory intelligence."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = None
        if api_key:
            try:
                self.client = openai.OpenAI(api_key=api_key)
            except Exception as e:
                st.warning(f"Failed to initialize OpenAI client: {e}")

    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = OPENAI_MODEL,
        max_tokens: int = 4000,
        temperature: float = 0.4,
        **kwargs,
    ) -> AIResponse:
        """Generate completion using OpenAI."""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized. Check your API key.")

        start_time = datetime.now()

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()

        return AIResponse(
            content=response.choices[0].message.content,
            model=model,
            provider="openai",
            tokens_used=response.usage.total_tokens,
            response_time=response_time,
            metadata={"usage": response.usage.__dict__},
        )


class ExpertConsultant:
    """Regulatory expert consultant using OpenAI."""

    def __init__(self, ai_manager: AIManager):
        self.ai_manager = ai_manager
        self.conversation_history: List[Dict[str, str]] = []

    def get_expert_advice(
        self,
        question: str,
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get expert regulatory advice."""
        messages = [{"role": "system", "content": system_prompt}]

        if context:
            context_prompt = (
                f"User Context:\n"
                f"- Role: {context.get('user_role', 'Quality Professional')}\n"
                f"- Company: {context.get('company', 'Medical Device Company')}\n"
                f"Please tailor your response to this context.\n"
            )
            messages.append({"role": "system", "content": context_prompt})

        # Add recent conversation history (last 10 messages)
        if self.conversation_history:
            messages.extend(self.conversation_history[-10:])

        messages.append({"role": "user", "content": question})

        try:
            response = self.ai_manager.generate_completion(
                messages=messages,
                temperature=0.4,
            )
            self.conversation_history.extend([
                {"role": "user", "content": question},
                {"role": "assistant", "content": response.content},
            ])
            return response.content
        except Exception as e:
            return f"AI request failed: {e}"
