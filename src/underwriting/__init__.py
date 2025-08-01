"""
Insurance Underwriting System

A comprehensive automobile insurance underwriting system with configurable rules,
A/B testing capabilities, and AI-powered risk assessment.
"""

__version__ = "3.0.0"
__author__ = "Insurance Underwriting System"
__email__ = "contact@jeremiahconnelly.dev"

from .core.models import (
    Application,
    Driver,
    Vehicle,
    Violation,
    Claim,
    UnderwritingDecision,
    RiskScore,
)
from .core.engine import UnderwritingEngine
from .core.ai_engine import AIEnhancedUnderwritingEngine, EnhancedUnderwritingDecision
from .config.loader import ConfigurationLoader
from .ai.base import AIServiceInterface, AIUnderwritingDecision, AIRiskAssessment
from .ai.openai_service import OpenAIService

# A/B Testing Framework
from .ab_testing.framework import ABTestFramework, ABTest, ABTestResult
from .ab_testing.config import ABTestConfigManager, ABTestConfig, ABTestType
from .ab_testing.statistics import StatisticalAnalyzer
from .ab_testing.sample_generator import ABTestSampleGenerator, ABTestSampleProfile
from .ab_testing.results import ABTestResultsManager, ABTestReport

try:
    import sys
    from pathlib import Path
    # Add data directory to path
    data_dir = Path(__file__).parent.parent.parent / "data"
    sys.path.insert(0, str(data_dir))
except ImportError:
    pass

__all__ = [
    # Core Models and Engine
    "Application",
    "Driver", 
    "Vehicle",
    "Violation",
    "Claim",
    "UnderwritingDecision",
    "RiskScore",
    "UnderwritingEngine",
    "AIEnhancedUnderwritingEngine",
    "EnhancedUnderwritingDecision",
    "ConfigurationLoader",
    
    # AI Components
    "AIServiceInterface",
    "AIUnderwritingDecision",
    "AIRiskAssessment",
    "OpenAIService",
    
    # A/B Testing Framework
    "ABTestFramework",
    "ABTest",
    "ABTestResult",
    "ABTestConfigManager",
    "ABTestConfig",
    "ABTestType",
    "StatisticalAnalyzer",
    "ABTestSampleGenerator",
    "ABTestSampleProfile",
    "ABTestResultsManager",
    "ABTestReport",
]