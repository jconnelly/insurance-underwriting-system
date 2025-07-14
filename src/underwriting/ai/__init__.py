"""
AI Integration Module for Insurance Underwriting System

This module provides AI-enhanced underwriting capabilities with support for
multiple AI providers including OpenAI, Google AI, and Claude.
"""

from .base import AIServiceInterface, AIUnderwritingDecision, AIRiskAssessment
from .openai_service import OpenAIService
from .response_parser import AIResponseParser

__all__ = [
    "AIServiceInterface",
    "AIUnderwritingDecision", 
    "AIRiskAssessment",
    "OpenAIService",
    "AIResponseParser",
]