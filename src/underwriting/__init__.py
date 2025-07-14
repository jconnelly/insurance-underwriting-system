"""
Insurance Underwriting System

A comprehensive automobile insurance underwriting system with configurable rules,
A/B testing capabilities, and AI-powered risk assessment.
"""

__version__ = "1.0.0"
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
from .config.loader import ConfigurationLoader

try:
    import sys
    from pathlib import Path
    # Add data directory to path
    data_dir = Path(__file__).parent.parent.parent / "data"
    sys.path.insert(0, str(data_dir))
except ImportError:
    pass

__all__ = [
    "Application",
    "Driver", 
    "Vehicle",
    "Violation",
    "Claim",
    "UnderwritingDecision",
    "RiskScore",
    "UnderwritingEngine",
    "ConfigurationLoader",
]