"""
A/B testing framework for insurance underwriting system.

This module provides comprehensive A/B testing capabilities for comparing
different underwriting rule sets, AI models, and system configurations.
"""

from .framework import ABTestFramework, ABTest, ABTestResult
from .config import ABTestConfig, ABTestConfigManager
from .statistics import StatisticalAnalyzer, StatisticalTest
from .sample_generator import ABTestSampleGenerator
from .results import ABTestResultsManager, ABTestReport

__all__ = [
    # Core framework
    'ABTestFramework',
    'ABTest',
    'ABTestResult',
    
    # Configuration
    'ABTestConfig',
    'ABTestConfigManager',
    
    # Statistics
    'StatisticalAnalyzer',
    'StatisticalTest',
    
    # Sample generation
    'ABTestSampleGenerator',
    
    # Results management
    'ABTestResultsManager',
    'ABTestReport'
]