"""
Main underwriting engine for processing insurance applications.

This module provides the core UnderwritingEngine class that orchestrates
the entire underwriting process, from application intake to decision rendering.
"""

from typing import Dict, List, Optional
from uuid import UUID

from loguru import logger

from ..config.loader import ConfigurationLoader
from .models import Application, UnderwritingDecision, DecisionType
from .rules import RuleEvaluator


class UnderwritingEngine:
    """Main engine for processing insurance applications."""
    
    def __init__(self, config_loader: Optional[ConfigurationLoader] = None):
        """Initialize the underwriting engine.
        
        Args:
            config_loader: Configuration loader instance. If None, creates a new one.
        """
        self.config_loader = config_loader or ConfigurationLoader()
        self._rule_evaluators: Dict[str, RuleEvaluator] = {}
        self._initialize_evaluators()
    
    def _initialize_evaluators(self) -> None:
        """Initialize rule evaluators for all available rule sets."""
        for rule_set_name in self.config_loader.get_available_rule_sets():
            try:
                rule_set = self.config_loader.get_rule_set(rule_set_name)
                self._rule_evaluators[rule_set_name] = RuleEvaluator(rule_set)
                logger.info(f"Initialized rule evaluator for {rule_set_name}")
            except Exception as e:
                logger.error(f"Failed to initialize rule evaluator for {rule_set_name}: {e}")
    
    def process_application(
        self, 
        application: Application, 
        rule_set_name: str = "standard"
    ) -> UnderwritingDecision:
        """Process an insurance application through the underwriting engine.
        
        Args:
            application: The insurance application to process.
            rule_set_name: Name of the rule set to use for evaluation.
            
        Returns:
            UnderwritingDecision with the final decision and supporting data.
            
        Raises:
            ValueError: If rule set is not available.
        """
        logger.info(f"Processing application {application.id} with rule set {rule_set_name}")
        
        # Validate rule set
        if rule_set_name not in self._rule_evaluators:
            available_sets = list(self._rule_evaluators.keys())
            raise ValueError(f"Rule set '{rule_set_name}' not available. Available: {available_sets}")
        
        # Get the appropriate rule evaluator
        evaluator = self._rule_evaluators[rule_set_name]
        
        # Validate application
        self._validate_application(application)
        
        # Process the application
        try:
            decision = evaluator.evaluate_application(application)
            
            # Log the decision
            logger.info(
                f"Application {application.id} processed: {decision.decision.value} "
                f"(Score: {decision.risk_score.overall_score}, Rules: {len(decision.triggered_rules)})"
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"Error processing application {application.id}: {e}")
            raise
    
    def batch_process_applications(
        self, 
        applications: List[Application], 
        rule_set_name: str = "standard"
    ) -> List[UnderwritingDecision]:
        """Process multiple applications in batch.
        
        Args:
            applications: List of applications to process.
            rule_set_name: Name of the rule set to use for evaluation.
            
        Returns:
            List of UnderwritingDecision objects.
        """
        logger.info(f"Batch processing {len(applications)} applications with rule set {rule_set_name}")
        
        results = []
        for application in applications:
            try:
                decision = self.process_application(application, rule_set_name)
                results.append(decision)
            except Exception as e:
                logger.error(f"Failed to process application {application.id}: {e}")
                # Continue processing other applications
                continue
        
        logger.info(f"Batch processing completed: {len(results)} successful, {len(applications) - len(results)} failed")
        return results
    
    def compare_rule_sets(self, application: Application) -> Dict[str, UnderwritingDecision]:
        """Compare how an application would be evaluated under different rule sets.
        
        Args:
            application: The application to evaluate.
            
        Returns:
            Dictionary mapping rule set names to their decisions.
        """
        logger.info(f"Comparing rule sets for application {application.id}")
        
        results = {}
        for rule_set_name in self._rule_evaluators.keys():
            try:
                decision = self.process_application(application, rule_set_name)
                results[rule_set_name] = decision
            except Exception as e:
                logger.error(f"Failed to evaluate with rule set {rule_set_name}: {e}")
                continue
        
        return results
    
    def get_decision_statistics(self, decisions: List[UnderwritingDecision]) -> Dict[str, any]:
        """Generate statistics from a batch of decisions.
        
        Args:
            decisions: List of underwriting decisions.
            
        Returns:
            Dictionary with decision statistics.
        """
        if not decisions:
            return {}
        
        total_count = len(decisions)
        accept_count = sum(1 for d in decisions if d.decision == DecisionType.ACCEPT)
        deny_count = sum(1 for d in decisions if d.decision == DecisionType.DENY)
        adjudicate_count = sum(1 for d in decisions if d.decision == DecisionType.ADJUDICATE)
        
        avg_risk_score = sum(d.risk_score.overall_score for d in decisions) / total_count
        
        # Most common triggered rules
        all_triggered_rules = []
        for decision in decisions:
            all_triggered_rules.extend(decision.triggered_rules)
        
        rule_counts = {}
        for rule in all_triggered_rules:
            rule_counts[rule] = rule_counts.get(rule, 0) + 1
        
        top_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_applications": total_count,
            "decisions": {
                "accept": {"count": accept_count, "percentage": accept_count / total_count * 100},
                "deny": {"count": deny_count, "percentage": deny_count / total_count * 100},
                "adjudicate": {"count": adjudicate_count, "percentage": adjudicate_count / total_count * 100}
            },
            "average_risk_score": avg_risk_score,
            "most_triggered_rules": top_rules
        }
    
    def _validate_application(self, application: Application) -> None:
        """Validate application data before processing.
        
        Args:
            application: The application to validate.
            
        Raises:
            ValueError: If application data is invalid.
        """
        # Check required fields
        if not application.applicant:
            raise ValueError("Application must have an applicant")
        
        if not application.vehicles:
            raise ValueError("Application must have at least one vehicle")
        
        # Validate driver ages
        for driver in application.all_drivers:
            if driver.age < 16:
                raise ValueError(f"Driver {driver.first_name} {driver.last_name} is under 16 years old")
            if driver.age > 100:
                raise ValueError(f"Driver {driver.first_name} {driver.last_name} is over 100 years old")
        
        # Validate vehicle data
        for vehicle in application.vehicles:
            if vehicle.value <= 0:
                raise ValueError(f"Vehicle {vehicle.make} {vehicle.model} has invalid value")
            if vehicle.year < 1900 or vehicle.year > 2030:
                raise ValueError(f"Vehicle {vehicle.make} {vehicle.model} has invalid year")
        
        logger.debug(f"Application {application.id} validation passed")
    
    def get_available_rule_sets(self) -> List[str]:
        """Get list of available rule sets.
        
        Returns:
            List of rule set names.
        """
        return list(self._rule_evaluators.keys())
    
    def reload_configurations(self) -> None:
        """Reload all rule configurations and reinitialize evaluators."""
        logger.info("Reloading rule configurations")
        
        self.config_loader.reload_rule_sets()
        self._rule_evaluators.clear()
        self._initialize_evaluators()
        
        logger.info("Rule configurations reloaded successfully")
    
    def get_rule_set_info(self, rule_set_name: str) -> Dict[str, any]:
        """Get information about a specific rule set.
        
        Args:
            rule_set_name: Name of the rule set.
            
        Returns:
            Dictionary with rule set information.
            
        Raises:
            ValueError: If rule set is not found.
        """
        if rule_set_name not in self._rule_evaluators:
            available_sets = list(self._rule_evaluators.keys())
            raise ValueError(f"Rule set '{rule_set_name}' not found. Available: {available_sets}")
        
        rule_set = self.config_loader.get_rule_set(rule_set_name)
        
        return {
            "name": rule_set_name,
            "version": rule_set.version,
            "description": rule_set.description,
            "last_updated": rule_set.last_updated,
            "hard_stops_count": len(rule_set.hard_stops.rules),
            "adjudication_triggers_count": len(rule_set.adjudication_triggers.rules),
            "acceptance_criteria_count": len(rule_set.acceptance_criteria.rules),
            "lookback_periods": rule_set.evaluation_parameters.lookback_periods,
        }
    
    def validate_rule_set(self, rule_set_name: str) -> bool:
        """Validate a specific rule set.
        
        Args:
            rule_set_name: Name of the rule set to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        return self.config_loader.validate_rule_set(rule_set_name)