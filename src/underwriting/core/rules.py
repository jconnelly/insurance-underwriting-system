"""
Rule evaluation logic for insurance underwriting.

This module contains the core logic for evaluating underwriting rules against
applications, determining decisions, and calculating risk scores.
"""

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from loguru import logger

from ..config.loader import Rule, RuleSet
from .models import (
    Application,
    Driver,
    Vehicle,
    Violation,
    Claim,
    DecisionType,
    ViolationType,
    ViolationSeverity,
    ClaimType,
    LicenseStatus,
    UnderwritingDecision,
    RiskScore,
)


class RuleEvaluationResult:
    """Result of evaluating a single rule."""
    
    def __init__(self, rule: Rule, matched: bool, reason: Optional[str] = None):
        self.rule = rule
        self.matched = matched
        self.reason = reason or rule.criteria.reason
        self.action = rule.criteria.action
        self.rule_id = rule.rule_id


class RuleEvaluator:
    """Evaluates underwriting rules against applications."""
    
    def __init__(self, rule_set: RuleSet):
        """Initialize rule evaluator with a specific rule set.
        
        Args:
            rule_set: The rule set to use for evaluation.
        """
        self.rule_set = rule_set
        self.violation_severity_map = self._build_violation_severity_map()
    
    def _build_violation_severity_map(self) -> Dict[str, ViolationSeverity]:
        """Build mapping of violation types to severity levels."""
        severity_map = {}
        
        for severity, violation_types in self.rule_set.evaluation_parameters.violation_severity.items():
            for violation_type in violation_types:
                severity_map[violation_type] = ViolationSeverity(severity)
        
        return severity_map
    
    def evaluate_application(self, application: Application) -> UnderwritingDecision:
        """Evaluate an application against the rule set.
        
        Args:
            application: The insurance application to evaluate.
            
        Returns:
            UnderwritingDecision with the result of evaluation.
        """
        logger.info(f"Evaluating application {application.id} with rule set {self.rule_set.version}")
        
        triggered_rules = []
        
        # Check hard stops first - these result in immediate denial
        for rule in self.rule_set.hard_stops.rules:
            result = self._evaluate_rule(rule, application)
            if result.matched:
                triggered_rules.append(result.rule_id)
                risk_score = self._calculate_risk_score(application, triggered_rules)
                
                logger.info(f"Hard stop triggered: {result.rule_id} - {result.reason}")
                
                return UnderwritingDecision(
                    application_id=application.id,
                    decision=DecisionType.DENY,
                    reason=result.reason,
                    risk_score=risk_score,
                    rule_set=self.rule_set.version,
                    triggered_rules=triggered_rules
                )
        
        # Check adjudication triggers - these require manual review
        for rule in self.rule_set.adjudication_triggers.rules:
            result = self._evaluate_rule(rule, application)
            if result.matched:
                triggered_rules.append(result.rule_id)
                risk_score = self._calculate_risk_score(application, triggered_rules)
                
                logger.info(f"Adjudication trigger: {result.rule_id} - {result.reason}")
                
                return UnderwritingDecision(
                    application_id=application.id,
                    decision=DecisionType.ADJUDICATE,
                    reason=result.reason,
                    risk_score=risk_score,
                    rule_set=self.rule_set.version,
                    triggered_rules=triggered_rules
                )
        
        # Check acceptance criteria - these allow automatic approval
        for rule in self.rule_set.acceptance_criteria.rules:
            result = self._evaluate_rule(rule, application)
            if result.matched:
                triggered_rules.append(result.rule_id)
                risk_score = self._calculate_risk_score(application, triggered_rules)
                
                logger.info(f"Acceptance criteria met: {result.rule_id} - {result.reason}")
                
                return UnderwritingDecision(
                    application_id=application.id,
                    decision=DecisionType.ACCEPT,
                    reason=result.reason,
                    risk_score=risk_score,
                    rule_set=self.rule_set.version,
                    triggered_rules=triggered_rules
                )
        
        # If no specific rules matched, default to adjudication
        risk_score = self._calculate_risk_score(application, triggered_rules)
        
        return UnderwritingDecision(
            application_id=application.id,
            decision=DecisionType.ADJUDICATE,
            reason="Application requires manual review - no automatic decision criteria met",
            risk_score=risk_score,
            rule_set=self.rule_set.version,
            triggered_rules=triggered_rules
        )
    
    def _evaluate_rule(self, rule: Rule, application: Application) -> RuleEvaluationResult:
        """Evaluate a single rule against an application.
        
        Args:
            rule: The rule to evaluate.
            application: The application to evaluate against.
            
        Returns:
            RuleEvaluationResult indicating if the rule matched.
        """
        criteria = rule.criteria
        
        # Check license status
        if criteria.license_status:
            license_statuses = criteria.license_status if isinstance(criteria.license_status, list) else [criteria.license_status]
            for driver in application.all_drivers:
                if driver.license_status.value in license_statuses:
                    return RuleEvaluationResult(rule, True)
        
        # Check fraud conviction
        if criteria.fraud_conviction is not None:
            if application.fraud_conviction == criteria.fraud_conviction:
                return RuleEvaluationResult(rule, True)
        
        # Check coverage lapse
        if criteria.coverage_lapse_days is not None:
            if application.coverage_lapse_days >= criteria.coverage_lapse_days:
                return RuleEvaluationResult(rule, True)
        
        # Check coverage lapse range
        if criteria.coverage_lapse_days_min is not None and criteria.coverage_lapse_days_max is not None:
            if criteria.coverage_lapse_days_min <= application.coverage_lapse_days <= criteria.coverage_lapse_days_max:
                return RuleEvaluationResult(rule, True)
        
        # Check credit score
        if criteria.credit_score_min is not None and application.credit_score is not None:
            if application.credit_score < criteria.credit_score_min:
                return RuleEvaluationResult(rule, True)
        
        if criteria.credit_score_max is not None and application.credit_score is not None:
            if application.credit_score <= criteria.credit_score_max:
                return RuleEvaluationResult(rule, True)
        
        # Check violations
        if self._check_violation_criteria(criteria, application):
            return RuleEvaluationResult(rule, True)
        
        # Check claims
        if self._check_claim_criteria(criteria, application):
            return RuleEvaluationResult(rule, True)
        
        # Check driver age
        if self._check_driver_age_criteria(criteria, application):
            return RuleEvaluationResult(rule, True)
        
        # Check vehicle criteria
        if self._check_vehicle_criteria(criteria, application):
            return RuleEvaluationResult(rule, True)
        
        # Check acceptance criteria (opposite logic)
        if self._check_acceptance_criteria(criteria, application):
            return RuleEvaluationResult(rule, True)
        
        return RuleEvaluationResult(rule, False)
    
    def _check_violation_criteria(self, criteria, application: Application) -> bool:
        """Check violation-related criteria."""
        lookback_years = criteria.lookback_years or self.rule_set.evaluation_parameters.lookback_periods.get("violations", 5)
        cutoff_date = date.today() - timedelta(days=lookback_years * 365)
        
        for driver in application.all_drivers:
            recent_violations = [v for v in driver.violations if v.violation_date >= cutoff_date]
            
            # Check specific violation type and count
            if criteria.violation_type and criteria.count_threshold:
                violation_count = sum(1 for v in recent_violations if v.violation_type.value == criteria.violation_type)
                if violation_count >= criteria.count_threshold:
                    return True
            
            # Check minor violations count
            if criteria.minor_violations_count:
                minor_count = sum(1 for v in recent_violations 
                                if self.violation_severity_map.get(v.violation_type.value) == ViolationSeverity.MINOR)
                if minor_count >= criteria.minor_violations_count:
                    return True
            
            # Check major violations presence
            if criteria.major_violations:
                major_count = sum(1 for v in recent_violations 
                                if self.violation_severity_map.get(v.violation_type.value) == ViolationSeverity.MAJOR)
                if major_count > 0:
                    return True
            
            # Check major violation count
            if criteria.major_violation_count:
                if criteria.violation_types:
                    major_count = sum(1 for v in recent_violations 
                                    if v.violation_type.value in criteria.violation_types)
                else:
                    major_count = sum(1 for v in recent_violations 
                                    if self.violation_severity_map.get(v.violation_type.value) == ViolationSeverity.MAJOR)
                if major_count >= criteria.major_violation_count:
                    return True
            
            # Check any violations
            if criteria.any_violations and recent_violations:
                return True
            
            # Check total violations count
            if criteria.violations_count is not None:
                if len(recent_violations) != criteria.violations_count:
                    return True
        
        return False
    
    def _check_claim_criteria(self, criteria, application: Application) -> bool:
        """Check claim-related criteria."""
        lookback_years = criteria.lookback_years or self.rule_set.evaluation_parameters.lookback_periods.get("claims", 5)
        cutoff_date = date.today() - timedelta(days=lookback_years * 365)
        
        for driver in application.all_drivers:
            recent_claims = [c for c in driver.claims if c.claim_date >= cutoff_date]
            
            # Check at-fault claims count
            if criteria.at_fault_claims_count is not None:
                at_fault_count = sum(1 for c in recent_claims if c.at_fault)
                if at_fault_count >= criteria.at_fault_claims_count:
                    return True
            
            # Check at-fault claims max (for acceptance criteria)
            if criteria.at_fault_claims_max is not None:
                at_fault_count = sum(1 for c in recent_claims if c.at_fault)
                if at_fault_count > criteria.at_fault_claims_max:
                    return True
            
            # Check specific claim type
            if criteria.claim_type and criteria.count_threshold:
                claim_count = sum(1 for c in recent_claims 
                                if c.claim_type.value == criteria.claim_type)
                if claim_count >= criteria.count_threshold:
                    return True
        
        return False
    
    def _check_driver_age_criteria(self, criteria, application: Application) -> bool:
        """Check driver age-related criteria."""
        for driver in application.all_drivers:
            # Check maximum age
            if criteria.driver_age_max is not None:
                if driver.age <= criteria.driver_age_max:
                    return True
            
            # Check minimum age
            if criteria.driver_age_min is not None:
                if driver.age >= criteria.driver_age_min:
                    return True
        
        return False
    
    def _check_vehicle_criteria(self, criteria, application: Application) -> bool:
        """Check vehicle-related criteria."""
        for vehicle in application.vehicles:
            # Check vehicle category
            if criteria.vehicle_category:
                if vehicle.category.value in criteria.vehicle_category:
                    return True
            
            # Check vehicle value
            if criteria.vehicle_value_min is not None:
                if vehicle.value >= criteria.vehicle_value_min:
                    return True
            
            if criteria.vehicle_value_max is not None:
                if vehicle.value <= criteria.vehicle_value_max:
                    return True
        
        return False
    
    def _check_acceptance_criteria(self, criteria, application: Application) -> bool:
        """Check acceptance criteria (all conditions must be met)."""
        # This is for acceptance rules where ALL criteria must be satisfied
        if criteria.action != "accept":
            return False
        
        # Check age range
        if criteria.driver_age_min is not None and criteria.driver_age_max is not None:
            for driver in application.all_drivers:
                if not (criteria.driver_age_min <= driver.age <= criteria.driver_age_max):
                    return False
        
        # Check violations count (must be exactly this number)
        if criteria.violations_count is not None:
            lookback_years = criteria.lookback_years or 5
            cutoff_date = date.today() - timedelta(days=lookback_years * 365)
            
            for driver in application.all_drivers:
                recent_violations = [v for v in driver.violations if v.violation_date >= cutoff_date]
                if len(recent_violations) != criteria.violations_count:
                    return False
        
        # Check at-fault claims count (must be exactly this number)
        if criteria.at_fault_claims_count is not None:
            lookback_years = criteria.lookback_years or 5
            cutoff_date = date.today() - timedelta(days=lookback_years * 365)
            
            for driver in application.all_drivers:
                recent_claims = [c for c in driver.claims if c.claim_date >= cutoff_date]
                at_fault_count = sum(1 for c in recent_claims if c.at_fault)
                if at_fault_count != criteria.at_fault_claims_count:
                    return False
        
        # Check license status
        if criteria.license_status:
            license_statuses = criteria.license_status if isinstance(criteria.license_status, list) else [criteria.license_status]
            for driver in application.all_drivers:
                if driver.license_status.value not in license_statuses:
                    return False
        
        # Check coverage lapse
        if criteria.coverage_lapse_days is not None:
            if application.coverage_lapse_days != criteria.coverage_lapse_days:
                return False
        
        if criteria.coverage_lapse_days_max is not None:
            if application.coverage_lapse_days > criteria.coverage_lapse_days_max:
                return False
        
        # Check credit score
        if criteria.credit_score_min is not None and application.credit_score is not None:
            if application.credit_score < criteria.credit_score_min:
                return False
        
        # Check minor violations max
        if criteria.minor_violations_max is not None:
            lookback_years = criteria.lookback_years or 5
            cutoff_date = date.today() - timedelta(days=lookback_years * 365)
            
            for driver in application.all_drivers:
                recent_violations = [v for v in driver.violations if v.violation_date >= cutoff_date]
                minor_count = sum(1 for v in recent_violations 
                                if self.violation_severity_map.get(v.violation_type.value) == ViolationSeverity.MINOR)
                if minor_count > criteria.minor_violations_max:
                    return False
        
        return True
    
    def _calculate_risk_score(self, application: Application, triggered_rules: List[str]) -> RiskScore:
        """Calculate risk score based on application data and triggered rules.
        
        Args:
            application: The application to score.
            triggered_rules: List of rule IDs that were triggered.
            
        Returns:
            RiskScore with calculated values.
        """
        # Base scoring logic
        driver_risk = self._calculate_driver_risk(application)
        vehicle_risk = self._calculate_vehicle_risk(application)
        history_risk = self._calculate_history_risk(application)
        credit_risk = self._calculate_credit_risk(application)
        
        # Adjust based on triggered rules
        rule_penalty = len(triggered_rules) * 50
        
        # Calculate overall score
        overall_score = min(1000, driver_risk + vehicle_risk + history_risk + (credit_risk or 0) + rule_penalty)
        
        # Identify risk factors
        factors = []
        if driver_risk > 200:
            factors.append("High driver risk")
        if vehicle_risk > 200:
            factors.append("High vehicle risk")
        if history_risk > 200:
            factors.append("Poor driving history")
        if credit_risk and credit_risk > 200:
            factors.append("Poor credit score")
        if triggered_rules:
            factors.append(f"Triggered {len(triggered_rules)} rules")
        
        return RiskScore(
            overall_score=overall_score,
            driver_risk=driver_risk,
            vehicle_risk=vehicle_risk,
            history_risk=history_risk,
            credit_risk=credit_risk,
            factors=factors
        )
    
    def _calculate_driver_risk(self, application: Application) -> int:
        """Calculate driver-related risk score."""
        risk = 0
        
        for driver in application.all_drivers:
            # Age-based risk
            if driver.age < 25:
                risk += 100
            elif driver.age > 70:
                risk += 50
            
            # License status risk
            if driver.license_status != LicenseStatus.VALID:
                risk += 200
        
        return min(1000, risk)
    
    def _calculate_vehicle_risk(self, application: Application) -> int:
        """Calculate vehicle-related risk score."""
        risk = 0
        
        for vehicle in application.vehicles:
            # Vehicle category risk
            if vehicle.category.value in ["sports_car", "supercar", "racing"]:
                risk += 150
            elif vehicle.category.value in ["luxury_sedan", "luxury_suv"]:
                risk += 75
            
            # Vehicle value risk
            if vehicle.value > 100000:
                risk += 100
            elif vehicle.value > 50000:
                risk += 50
        
        return min(1000, risk)
    
    def _calculate_history_risk(self, application: Application) -> int:
        """Calculate history-related risk score."""
        risk = 0
        
        for driver in application.all_drivers:
            # Violations risk
            recent_violations = [v for v in driver.violations 
                               if v.violation_date >= date.today() - timedelta(days=5*365)]
            
            for violation in recent_violations:
                severity = self.violation_severity_map.get(violation.violation_type.value)
                if severity == ViolationSeverity.MAJOR:
                    risk += 200
                elif severity == ViolationSeverity.MODERATE:
                    risk += 100
                elif severity == ViolationSeverity.MINOR:
                    risk += 50
            
            # Claims risk
            recent_claims = [c for c in driver.claims 
                           if c.claim_date >= date.today() - timedelta(days=5*365)]
            
            for claim in recent_claims:
                if claim.at_fault:
                    risk += 150
                else:
                    risk += 50
        
        return min(1000, risk)
    
    def _calculate_credit_risk(self, application: Application) -> Optional[int]:
        """Calculate credit-related risk score."""
        if application.credit_score is None:
            return None
        
        if application.credit_score < 500:
            return 300
        elif application.credit_score < 600:
            return 200
        elif application.credit_score < 700:
            return 100
        else:
            return 0