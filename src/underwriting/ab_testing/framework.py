"""
Core A/B testing framework for insurance underwriting system.

This module provides the main A/B testing framework for comparing different
underwriting approaches, rule sets, and AI configurations.
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from loguru import logger

from ..core.models import Application, UnderwritingDecision
from ..core.engine import UnderwritingEngine
from ..core.ai_engine import AIEnhancedUnderwritingEngine
from .models import ABTestStatus, ABTestVariant, ABTestResult, ABTestConfiguration
from .statistics import StatisticalAnalyzer




@dataclass
class ABTestSummary:
    """Summary of A/B test results."""
    test_id: str
    status: ABTestStatus
    start_time: datetime
    end_time: Optional[datetime]
    control_results: List[ABTestResult]
    treatment_results: List[ABTestResult]
    statistical_analysis: Optional[Dict[str, Any]] = None
    conclusions: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ABTest:
    """Individual A/B test instance."""
    
    def __init__(self, config: ABTestConfiguration):
        """Initialize A/B test.
        
        Args:
            config: Test configuration
        """
        self.config = config
        self.test_id = config.test_id
        self.status = ABTestStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.control_results: List[ABTestResult] = []
        self.treatment_results: List[ABTestResult] = []
        
        # Initialize engines
        self.control_engine = self._create_engine(config.control_config)
        self.treatment_engine = self._create_engine(config.treatment_config)
        
        # Initialize statistical analyzer
        self.statistical_analyzer = StatisticalAnalyzer(
            confidence_level=config.confidence_level,
            minimum_effect_size=config.minimum_effect_size
        )
        
        logger.info(f"A/B test initialized: {self.test_id}")
    
    def _create_engine(self, config: Dict[str, Any]) -> UnderwritingEngine:
        """Create underwriting engine based on configuration."""
        engine_type = config.get("engine_type", "standard")
        
        if engine_type == "ai_enhanced":
            return AIEnhancedUnderwritingEngine(
                ai_enabled=config.get("ai_enabled", True),
                rate_limiting_enabled=config.get("rate_limiting_enabled", True)
            )
        else:
            return UnderwritingEngine()
    
    def _assign_variant(self, application_id: str) -> ABTestVariant:
        """Assign application to control or treatment variant."""
        # Use deterministic assignment based on application ID
        hash_value = hash(application_id + self.test_id)
        return ABTestVariant.CONTROL if hash_value % 2 == 0 else ABTestVariant.TREATMENT
    
    async def evaluate_application(self, application: Application) -> ABTestResult:
        """Evaluate application using A/B test configuration."""
        if self.status != ABTestStatus.RUNNING:
            raise ValueError(f"Test {self.test_id} is not running")
        
        # Assign variant
        variant = self._assign_variant(str(application.id))
        
        # Select engine
        engine = self.control_engine if variant == ABTestVariant.CONTROL else self.treatment_engine
        
        # Evaluate application
        start_time = time.time()
        
        if isinstance(engine, AIEnhancedUnderwritingEngine):
            # AI-enhanced evaluation
            rule_set = self.config.control_config.get("rule_set", "standard") if variant == ABTestVariant.CONTROL else self.config.treatment_config.get("rule_set", "standard")
            enhanced_decision = await engine.process_application_enhanced(application, rule_set)
            decision = enhanced_decision.final_decision
        else:
            # Standard evaluation
            rule_set = self.config.control_config.get("rule_set", "standard") if variant == ABTestVariant.CONTROL else self.config.treatment_config.get("rule_set", "standard")
            decision = engine.process_application(application, rule_set)
        
        processing_time = time.time() - start_time
        
        # Create result
        result = ABTestResult(
            test_id=self.test_id,
            variant=variant,
            application_id=str(application.id),
            decision=decision,
            processing_time=processing_time,
            timestamp=datetime.now(),
            metadata={
                "rule_set": rule_set,
                "engine_type": self.config.control_config.get("engine_type") if variant == ABTestVariant.CONTROL else self.config.treatment_config.get("engine_type")
            }
        )
        
        # Store result
        if variant == ABTestVariant.CONTROL:
            self.control_results.append(result)
        else:
            self.treatment_results.append(result)
        
        logger.debug(f"A/B test evaluation completed: {self.test_id}, variant: {variant.value}, decision: {decision.decision.value}")
        
        return result
    
    def start_test(self) -> None:
        """Start the A/B test."""
        if self.status != ABTestStatus.PENDING:
            raise ValueError(f"Test {self.test_id} cannot be started from status {self.status.value}")
        
        self.status = ABTestStatus.RUNNING
        self.start_time = datetime.now()
        logger.info(f"A/B test started: {self.test_id}")
    
    def stop_test(self) -> None:
        """Stop the A/B test."""
        if self.status != ABTestStatus.RUNNING:
            raise ValueError(f"Test {self.test_id} cannot be stopped from status {self.status.value}")
        
        self.status = ABTestStatus.COMPLETED
        self.end_time = datetime.now()
        logger.info(f"A/B test completed: {self.test_id}")
    
    def get_summary(self) -> ABTestSummary:
        """Get test summary with results."""
        # Run statistical analysis if test is completed
        statistical_analysis = None
        if self.status == ABTestStatus.COMPLETED and len(self.control_results) > 0 and len(self.treatment_results) > 0:
            statistical_analysis = self.statistical_analyzer.analyze_results(
                self.control_results, 
                self.treatment_results,
                self.config.success_metrics
            )
        
        return ABTestSummary(
            test_id=self.test_id,
            status=self.status,
            start_time=self.start_time,
            end_time=self.end_time,
            control_results=self.control_results,
            treatment_results=self.treatment_results,
            statistical_analysis=statistical_analysis,
            conclusions=self._generate_conclusions(statistical_analysis),
            recommendations=self._generate_recommendations(statistical_analysis)
        )
    
    def _generate_conclusions(self, statistical_analysis: Optional[Dict[str, Any]]) -> List[str]:
        """Generate conclusions based on statistical analysis."""
        if not statistical_analysis:
            return ["Test incomplete - no statistical analysis available"]
        
        conclusions = []
        
        for metric, analysis in statistical_analysis.items():
            if metric == "metadata":
                continue
                
            significance = analysis.get("significant", False)
            effect_size = analysis.get("effect_size", 0)
            
            if significance:
                direction = "higher" if effect_size > 0 else "lower"
                conclusions.append(f"Treatment variant shows significantly {direction} {metric} (p < {self.config.confidence_level})")
            else:
                conclusions.append(f"No significant difference found in {metric}")
        
        return conclusions
    
    def _generate_recommendations(self, statistical_analysis: Optional[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on results."""
        if not statistical_analysis:
            return ["Complete test to get recommendations"]
        
        recommendations = []
        
        # Check if treatment is better overall
        significant_improvements = []
        significant_degradations = []
        
        for metric, analysis in statistical_analysis.items():
            if metric == "metadata":
                continue
                
            if analysis.get("significant", False):
                effect_size = analysis.get("effect_size", 0)
                if effect_size > 0:
                    significant_improvements.append(metric)
                else:
                    significant_degradations.append(metric)
        
        if significant_improvements and not significant_degradations:
            recommendations.append("Recommend rolling out treatment variant - shows significant improvements")
        elif significant_degradations and not significant_improvements:
            recommendations.append("Recommend keeping control variant - treatment shows significant degradation")
        elif significant_improvements and significant_degradations:
            recommendations.append("Mixed results - further analysis needed to determine best approach")
        else:
            recommendations.append("No significant differences found - either variant can be used")
        
        # Add sample size recommendations
        total_samples = len(self.control_results) + len(self.treatment_results)
        if total_samples < self.config.sample_size:
            recommendations.append(f"Consider increasing sample size (current: {total_samples}, target: {self.config.sample_size})")
        
        return recommendations


class ABTestFramework:
    """Main A/B testing framework."""
    
    def __init__(self, storage_path: str = "ab_test_data"):
        """Initialize A/B testing framework.
        
        Args:
            storage_path: Path to store test data
        """
        from .results import ABTestResultsManager
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        self.active_tests: Dict[str, ABTest] = {}
        self.results_manager = ABTestResultsManager(storage_path)
        
        logger.info(f"A/B testing framework initialized with storage: {storage_path}")
    
    def create_test(self, config: ABTestConfiguration) -> ABTest:
        """Create a new A/B test.
        
        Args:
            config: Test configuration
            
        Returns:
            Created A/B test instance
        """
        if config.test_id in self.active_tests:
            raise ValueError(f"Test {config.test_id} already exists")
        
        test = ABTest(config)
        self.active_tests[config.test_id] = test
        
        # Save test configuration
        self.results_manager.save_test_config(config)
        
        logger.info(f"A/B test created: {config.test_id}")
        return test
    
    def get_test(self, test_id: str) -> Optional[ABTest]:
        """Get active test by ID.
        
        Args:
            test_id: Test identifier
            
        Returns:
            A/B test instance or None if not found
        """
        return self.active_tests.get(test_id)
    
    def start_test(self, test_id: str) -> None:
        """Start an A/B test.
        
        Args:
            test_id: Test identifier
        """
        test = self.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        test.start_test()
        self.results_manager.save_test_status(test_id, ABTestStatus.RUNNING)
    
    def stop_test(self, test_id: str) -> None:
        """Stop an A/B test.
        
        Args:
            test_id: Test identifier
        """
        test = self.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        test.stop_test()
        self.results_manager.save_test_status(test_id, ABTestStatus.COMPLETED)
        
        # Save final results
        summary = test.get_summary()
        self.results_manager.save_test_results(test_id, summary)
    
    async def evaluate_application(self, test_id: str, application: Application) -> ABTestResult:
        """Evaluate application using A/B test.
        
        Args:
            test_id: Test identifier
            application: Application to evaluate
            
        Returns:
            A/B test result
        """
        test = self.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        result = await test.evaluate_application(application)
        
        # Save result
        self.results_manager.save_test_result(result)
        
        return result
    
    def get_test_summary(self, test_id: str) -> ABTestSummary:
        """Get test summary.
        
        Args:
            test_id: Test identifier
            
        Returns:
            Test summary
        """
        test = self.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        return test.get_summary()
    
    def list_tests(self) -> List[Dict[str, Any]]:
        """List all active tests.
        
        Returns:
            List of test information
        """
        tests = []
        for test_id, test in self.active_tests.items():
            tests.append({
                "test_id": test_id,
                "name": test.config.name,
                "status": test.status.value,
                "start_time": test.start_time.isoformat() if test.start_time else None,
                "control_results": len(test.control_results),
                "treatment_results": len(test.treatment_results),
                "sample_size": test.config.sample_size
            })
        
        return tests
    
    def cleanup_completed_tests(self) -> int:
        """Clean up completed tests from memory.
        
        Returns:
            Number of tests cleaned up
        """
        completed_tests = [
            test_id for test_id, test in self.active_tests.items()
            if test.status == ABTestStatus.COMPLETED
        ]
        
        for test_id in completed_tests:
            del self.active_tests[test_id]
        
        logger.info(f"Cleaned up {len(completed_tests)} completed A/B tests")
        return len(completed_tests)