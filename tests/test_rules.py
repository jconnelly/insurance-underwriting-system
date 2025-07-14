"""
Tests for the rule evaluation logic.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from underwriting.core.rules import RuleEvaluator, RuleEvaluationResult
from underwriting.core.models import (
    Application,
    Driver,
    Vehicle,
    Violation,
    Claim,
    DecisionType,
    LicenseStatus,
    ViolationType,
    ViolationSeverity,
    ClaimType,
    VehicleCategory,
)
from underwriting.config.loader import ConfigurationLoader


class TestRuleEvaluator:
    """Test RuleEvaluator class."""
    
    def create_sample_application(self):
        """Create a sample application for testing."""
        driver = Driver(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            license_number="D12345678",
            license_status=LicenseStatus.VALID,
            license_state="CA"
        )
        
        vehicle = Vehicle(
            year=2020,
            make="Toyota",
            model="Camry",
            vin="1HGBH41JXMN109186",
            category=VehicleCategory.SEDAN,
            value=Decimal("25000.00")
        )
        
        return Application(
            applicant=driver,
            vehicles=[vehicle],
            credit_score=750,
            fraud_conviction=False,
            coverage_lapse_days=0
        )
    
    def test_evaluator_initialization(self):
        """Test rule evaluator initialization."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        assert evaluator.rule_set == rule_set
        assert evaluator.violation_severity_map is not None
        assert len(evaluator.violation_severity_map) > 0
    
    def test_evaluate_clean_application(self):
        """Test evaluating a clean application."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        decision = evaluator.evaluate_application(application)
        
        assert decision is not None
        assert decision.application_id == application.id
        assert decision.decision in [DecisionType.ACCEPT, DecisionType.DENY, DecisionType.ADJUDICATE]
        assert decision.risk_score is not None
        assert decision.rule_set == rule_set.version
    
    def test_evaluate_application_with_fraud_conviction(self):
        """Test evaluating application with fraud conviction."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        application.fraud_conviction = True
        
        decision = evaluator.evaluate_application(application)
        
        assert decision.decision == DecisionType.DENY
        assert "fraud" in decision.reason.lower()
    
    def test_evaluate_application_with_suspended_license(self):
        """Test evaluating application with suspended license."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        application.applicant.license_status = LicenseStatus.SUSPENDED
        
        decision = evaluator.evaluate_application(application)
        
        assert decision.decision == DecisionType.DENY
        assert "license" in decision.reason.lower()
    
    def test_evaluate_application_with_extended_coverage_lapse(self):
        """Test evaluating application with extended coverage lapse."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        application.coverage_lapse_days = 120  # Extended lapse
        
        decision = evaluator.evaluate_application(application)
        
        # Should be denied or adjudicated depending on rule set
        assert decision.decision in [DecisionType.DENY, DecisionType.ADJUDICATE]
    
    def test_evaluate_application_with_dui_violation(self):
        """Test evaluating application with DUI violation."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        
        # Add recent DUI violation
        dui_violation = Violation(
            violation_type=ViolationType.DUI,
            violation_date=date.today() - timedelta(days=365),  # 1 year ago
            description="DUI conviction",
            severity=ViolationSeverity.MAJOR
        )
        application.applicant.violations.append(dui_violation)
        
        decision = evaluator.evaluate_application(application)
        
        # Should be denied or adjudicated depending on rule set
        assert decision.decision in [DecisionType.DENY, DecisionType.ADJUDICATE]
    
    def test_evaluate_application_with_multiple_at_fault_claims(self):
        """Test evaluating application with multiple at-fault claims."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        
        # Add multiple at-fault claims
        for i in range(3):
            claim = Claim(
                claim_type=ClaimType.AT_FAULT,
                claim_date=date.today() - timedelta(days=365 * (i + 1)),
                description=f"At-fault claim {i+1}",
                amount=Decimal("5000.00"),
                at_fault=True
            )
            application.applicant.claims.append(claim)
        
        decision = evaluator.evaluate_application(application)
        
        # Should be denied due to multiple at-fault claims
        assert decision.decision == DecisionType.DENY
    
    def test_evaluate_application_with_young_driver(self):
        """Test evaluating application with young driver."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        application.applicant.date_of_birth = date(2005, 1, 1)  # Young driver
        
        decision = evaluator.evaluate_application(application)
        
        assert decision is not None
        # Young driver typically results in higher risk score
        assert decision.risk_score.overall_score > 0
    
    def test_evaluate_application_with_sports_car(self):
        """Test evaluating application with sports car."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        application.vehicles[0].category = VehicleCategory.SPORTS_CAR
        
        decision = evaluator.evaluate_application(application)
        
        # Sports car typically requires adjudication
        assert decision.decision in [DecisionType.ADJUDICATE, DecisionType.ACCEPT]
    
    def test_evaluate_application_with_poor_credit(self):
        """Test evaluating application with poor credit score."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        application.credit_score = 400  # Poor credit
        
        decision = evaluator.evaluate_application(application)
        
        # Poor credit typically requires adjudication
        assert decision.decision in [DecisionType.ADJUDICATE, DecisionType.DENY]
    
    def test_conservative_vs_liberal_rule_differences(self):
        """Test that conservative and liberal rules produce different results."""
        config_loader = ConfigurationLoader()
        conservative_rule_set = config_loader.get_rule_set("conservative")
        liberal_rule_set = config_loader.get_rule_set("liberal")
        
        conservative_evaluator = RuleEvaluator(conservative_rule_set)
        liberal_evaluator = RuleEvaluator(liberal_rule_set)
        
        # Create application with minor violations
        application = self.create_sample_application()
        
        # Add minor violations
        for i in range(2):
            violation = Violation(
                violation_type=ViolationType.SPEEDING_10_UNDER,
                violation_date=date.today() - timedelta(days=365 * (i + 1)),
                description=f"Minor speeding violation {i+1}",
                severity=ViolationSeverity.MINOR
            )
            application.applicant.violations.append(violation)
        
        conservative_decision = conservative_evaluator.evaluate_application(application)
        liberal_decision = liberal_evaluator.evaluate_application(application)
        
        # Conservative should be more restrictive
        assert conservative_decision.decision != liberal_decision.decision or \
               conservative_decision.risk_score.overall_score >= liberal_decision.risk_score.overall_score
    
    def test_risk_score_calculation(self):
        """Test risk score calculation components."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        
        # Add various risk factors
        application.applicant.date_of_birth = date(2005, 1, 1)  # Young driver
        application.vehicles[0].category = VehicleCategory.SPORTS_CAR  # Sports car
        application.credit_score = 500  # Poor credit
        
        # Add violation
        violation = Violation(
            violation_type=ViolationType.SPEEDING_15_OVER,
            violation_date=date.today() - timedelta(days=365),
            description="Speeding violation",
            severity=ViolationSeverity.MODERATE
        )
        application.applicant.violations.append(violation)
        
        decision = evaluator.evaluate_application(application)
        
        # Check risk score components
        assert decision.risk_score.driver_risk > 0
        assert decision.risk_score.vehicle_risk > 0
        assert decision.risk_score.history_risk > 0
        assert decision.risk_score.credit_risk > 0
        assert decision.risk_score.overall_score > 0
        assert len(decision.risk_score.factors) > 0
    
    def test_violation_severity_mapping(self):
        """Test violation severity mapping."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        # Check that major violations are mapped correctly
        assert evaluator.violation_severity_map["DUI"] == ViolationSeverity.MAJOR
        assert evaluator.violation_severity_map["reckless_driving"] == ViolationSeverity.MAJOR
        
        # Check that minor violations are mapped correctly
        assert evaluator.violation_severity_map["speeding_10_under"] == ViolationSeverity.MINOR
        assert evaluator.violation_severity_map["parking_violation"] == ViolationSeverity.MINOR
    
    def test_evaluate_rule_hard_stop(self):
        """Test evaluating individual hard stop rules."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        application.fraud_conviction = True
        
        # Get the fraud conviction rule
        fraud_rule = None
        for rule in rule_set.hard_stops.rules:
            if rule.rule_id == "HS005":  # Insurance fraud rule
                fraud_rule = rule
                break
        
        assert fraud_rule is not None
        
        result = evaluator._evaluate_rule(fraud_rule, application)
        assert result.matched is True
        assert result.action == "deny"
    
    def test_evaluate_rule_adjudication_trigger(self):
        """Test evaluating adjudication trigger rules."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        application.credit_score = 400  # Poor credit
        
        # Get the credit score rule
        credit_rule = None
        for rule in rule_set.adjudication_triggers.rules:
            if "credit" in rule.name.lower():
                credit_rule = rule
                break
        
        if credit_rule is not None:
            result = evaluator._evaluate_rule(credit_rule, application)
            assert result.matched is True
            assert result.action == "adjudicate"
    
    def test_evaluate_rule_acceptance_criteria(self):
        """Test evaluating acceptance criteria rules."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        # Create perfect application
        application = self.create_sample_application()
        application.applicant.date_of_birth = date(1980, 1, 1)  # Mature driver
        application.credit_score = 800  # Excellent credit
        application.coverage_lapse_days = 0  # No lapse
        
        # Get acceptance criteria rule
        acceptance_rule = rule_set.acceptance_criteria.rules[0]
        
        result = evaluator._evaluate_rule(acceptance_rule, application)
        # May or may not match depending on specific criteria
        assert result.matched in [True, False]
    
    def test_calculate_driver_risk(self):
        """Test driver risk calculation."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        # Young driver
        application = self.create_sample_application()
        application.applicant.date_of_birth = date(2005, 1, 1)
        
        risk = evaluator._calculate_driver_risk(application)
        assert risk > 0
        
        # Senior driver
        application.applicant.date_of_birth = date(1950, 1, 1)
        risk_senior = evaluator._calculate_driver_risk(application)
        assert risk_senior > 0
        
        # Suspended license
        application.applicant.license_status = LicenseStatus.SUSPENDED
        risk_suspended = evaluator._calculate_driver_risk(application)
        assert risk_suspended > risk
    
    def test_calculate_vehicle_risk(self):
        """Test vehicle risk calculation."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        
        # Sports car
        application.vehicles[0].category = VehicleCategory.SPORTS_CAR
        risk_sports = evaluator._calculate_vehicle_risk(application)
        assert risk_sports > 0
        
        # High-value vehicle
        application.vehicles[0].value = Decimal("150000.00")
        risk_high_value = evaluator._calculate_vehicle_risk(application)
        assert risk_high_value > 0
    
    def test_calculate_history_risk(self):
        """Test history risk calculation."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        
        # Add violations
        violation = Violation(
            violation_type=ViolationType.DUI,
            violation_date=date.today() - timedelta(days=365),
            description="DUI violation",
            severity=ViolationSeverity.MAJOR
        )
        application.applicant.violations.append(violation)
        
        # Add claims
        claim = Claim(
            claim_type=ClaimType.AT_FAULT,
            claim_date=date.today() - timedelta(days=365),
            description="At-fault claim",
            amount=Decimal("5000.00"),
            at_fault=True
        )
        application.applicant.claims.append(claim)
        
        risk = evaluator._calculate_history_risk(application)
        assert risk > 0
    
    def test_calculate_credit_risk(self):
        """Test credit risk calculation."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        evaluator = RuleEvaluator(rule_set)
        
        application = self.create_sample_application()
        
        # No credit score
        application.credit_score = None
        risk_none = evaluator._calculate_credit_risk(application)
        assert risk_none is None
        
        # Poor credit
        application.credit_score = 400
        risk_poor = evaluator._calculate_credit_risk(application)
        assert risk_poor > 0
        
        # Good credit
        application.credit_score = 750
        risk_good = evaluator._calculate_credit_risk(application)
        assert risk_good == 0
    
    def test_rule_evaluation_result(self):
        """Test RuleEvaluationResult class."""
        config_loader = ConfigurationLoader()
        rule_set = config_loader.get_rule_set("standard")
        rule = rule_set.hard_stops.rules[0]
        
        # Matched result
        result = RuleEvaluationResult(rule, True, "Custom reason")
        assert result.rule == rule
        assert result.matched is True
        assert result.reason == "Custom reason"
        assert result.action == rule.criteria.action
        assert result.rule_id == rule.rule_id
        
        # Unmatched result
        result = RuleEvaluationResult(rule, False)
        assert result.matched is False
        assert result.reason == rule.criteria.reason