"""
Tests for the underwriting engine.
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

from underwriting.core.engine import UnderwritingEngine
from underwriting.core.models import (
    Application,
    Driver,
    Vehicle,
    DecisionType,
    LicenseStatus,
    VehicleCategory,
)
from underwriting.config.loader import ConfigurationLoader


class TestUnderwritingEngine:
    """Test UnderwritingEngine class."""
    
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
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = UnderwritingEngine()
        
        assert engine.config_loader is not None
        assert isinstance(engine.config_loader, ConfigurationLoader)
        assert len(engine._rule_evaluators) > 0
    
    def test_engine_initialization_with_config_loader(self):
        """Test engine initialization with provided config loader."""
        mock_config_loader = Mock(spec=ConfigurationLoader)
        mock_config_loader.get_available_rule_sets.return_value = ["standard", "conservative"]
        
        engine = UnderwritingEngine(config_loader=mock_config_loader)
        
        assert engine.config_loader == mock_config_loader
    
    def test_process_application_standard_rules(self):
        """Test processing application with standard rules."""
        application = self.create_sample_application()
        engine = UnderwritingEngine()
        
        decision = engine.process_application(application, "standard")
        
        assert decision is not None
        assert decision.application_id == application.id
        assert decision.decision in [DecisionType.ACCEPT, DecisionType.DENY, DecisionType.ADJUDICATE]
        assert decision.risk_score is not None
        assert decision.rule_set == "standard"
    
    def test_process_application_conservative_rules(self):
        """Test processing application with conservative rules."""
        application = self.create_sample_application()
        engine = UnderwritingEngine()
        
        decision = engine.process_application(application, "conservative")
        
        assert decision is not None
        assert decision.application_id == application.id
        assert decision.rule_set == "conservative"
    
    def test_process_application_liberal_rules(self):
        """Test processing application with liberal rules."""
        application = self.create_sample_application()
        engine = UnderwritingEngine()
        
        decision = engine.process_application(application, "liberal")
        
        assert decision is not None
        assert decision.application_id == application.id
        assert decision.rule_set == "liberal"
    
    def test_process_application_invalid_rule_set(self):
        """Test processing application with invalid rule set."""
        application = self.create_sample_application()
        engine = UnderwritingEngine()
        
        with pytest.raises(ValueError, match="Rule set 'invalid' not available"):
            engine.process_application(application, "invalid")
    
    def test_batch_process_applications(self):
        """Test batch processing of applications."""
        applications = [
            self.create_sample_application(),
            self.create_sample_application(),
            self.create_sample_application()
        ]
        
        engine = UnderwritingEngine()
        decisions = engine.batch_process_applications(applications, "standard")
        
        assert len(decisions) == 3
        for decision in decisions:
            assert decision.rule_set == "standard"
            assert decision.decision in [DecisionType.ACCEPT, DecisionType.DENY, DecisionType.ADJUDICATE]
    
    def test_batch_process_empty_list(self):
        """Test batch processing with empty list."""
        engine = UnderwritingEngine()
        decisions = engine.batch_process_applications([], "standard")
        
        assert len(decisions) == 0
    
    def test_compare_rule_sets(self):
        """Test comparing rule sets for same application."""
        application = self.create_sample_application()
        engine = UnderwritingEngine()
        
        results = engine.compare_rule_sets(application)
        
        assert len(results) > 0
        assert "standard" in results
        assert "conservative" in results
        assert "liberal" in results
        
        for rule_set_name, decision in results.items():
            assert decision.application_id == application.id
            assert decision.rule_set == rule_set_name
    
    def test_get_decision_statistics(self):
        """Test getting decision statistics."""
        applications = [
            self.create_sample_application(),
            self.create_sample_application(),
            self.create_sample_application()
        ]
        
        engine = UnderwritingEngine()
        decisions = engine.batch_process_applications(applications, "standard")
        stats = engine.get_decision_statistics(decisions)
        
        assert "total_applications" in stats
        assert "decisions" in stats
        assert "average_risk_score" in stats
        assert "most_triggered_rules" in stats
        
        assert stats["total_applications"] == 3
        assert "accept" in stats["decisions"]
        assert "deny" in stats["decisions"]
        assert "adjudicate" in stats["decisions"]
    
    def test_get_decision_statistics_empty_list(self):
        """Test getting statistics with empty decision list."""
        engine = UnderwritingEngine()
        stats = engine.get_decision_statistics([])
        
        assert stats == {}
    
    def test_validate_application_valid(self):
        """Test application validation with valid data."""
        application = self.create_sample_application()
        engine = UnderwritingEngine()
        
        # Should not raise any exception
        engine._validate_application(application)
    
    def test_validate_application_no_applicant(self):
        """Test application validation with no applicant."""
        application = self.create_sample_application()
        application.applicant = None
        engine = UnderwritingEngine()
        
        with pytest.raises(ValueError, match="Application must have an applicant"):
            engine._validate_application(application)
    
    def test_validate_application_no_vehicles(self):
        """Test application validation with no vehicles."""
        application = self.create_sample_application()
        application.vehicles = []
        engine = UnderwritingEngine()
        
        with pytest.raises(ValueError, match="Application must have at least one vehicle"):
            engine._validate_application(application)
    
    def test_validate_application_young_driver(self):
        """Test application validation with underage driver."""
        application = self.create_sample_application()
        application.applicant.date_of_birth = date(2010, 1, 1)  # Very young
        engine = UnderwritingEngine()
        
        with pytest.raises(ValueError, match="is under 16 years old"):
            engine._validate_application(application)
    
    def test_validate_application_old_driver(self):
        """Test application validation with very old driver."""
        application = self.create_sample_application()
        application.applicant.date_of_birth = date(1920, 1, 1)  # Very old
        engine = UnderwritingEngine()
        
        with pytest.raises(ValueError, match="is over 100 years old"):
            engine._validate_application(application)
    
    def test_validate_application_invalid_vehicle_value(self):
        """Test application validation with invalid vehicle value."""
        application = self.create_sample_application()
        application.vehicles[0].value = Decimal("0")  # Invalid value
        engine = UnderwritingEngine()
        
        with pytest.raises(ValueError, match="has invalid value"):
            engine._validate_application(application)
    
    def test_validate_application_invalid_vehicle_year(self):
        """Test application validation with invalid vehicle year."""
        application = self.create_sample_application()
        application.vehicles[0].year = 1800  # Very old year
        engine = UnderwritingEngine()
        
        with pytest.raises(ValueError, match="has invalid year"):
            engine._validate_application(application)
    
    def test_get_available_rule_sets(self):
        """Test getting available rule sets."""
        engine = UnderwritingEngine()
        rule_sets = engine.get_available_rule_sets()
        
        assert isinstance(rule_sets, list)
        assert len(rule_sets) > 0
        assert "standard" in rule_sets
        assert "conservative" in rule_sets
        assert "liberal" in rule_sets
    
    def test_get_rule_set_info(self):
        """Test getting rule set information."""
        engine = UnderwritingEngine()
        info = engine.get_rule_set_info("standard")
        
        assert "name" in info
        assert "version" in info
        assert "description" in info
        assert "last_updated" in info
        assert "hard_stops_count" in info
        assert "adjudication_triggers_count" in info
        assert "acceptance_criteria_count" in info
        assert "lookback_periods" in info
        
        assert info["name"] == "standard"
    
    def test_get_rule_set_info_invalid(self):
        """Test getting info for invalid rule set."""
        engine = UnderwritingEngine()
        
        with pytest.raises(ValueError, match="Rule set 'invalid' not found"):
            engine.get_rule_set_info("invalid")
    
    def test_validate_rule_set_valid(self):
        """Test validating a valid rule set."""
        engine = UnderwritingEngine()
        
        assert engine.validate_rule_set("standard") is True
        assert engine.validate_rule_set("conservative") is True
        assert engine.validate_rule_set("liberal") is True
    
    def test_validate_rule_set_invalid(self):
        """Test validating an invalid rule set."""
        engine = UnderwritingEngine()
        
        # Should return False for invalid rule set
        assert engine.validate_rule_set("invalid") is False
    
    @patch('underwriting.core.engine.logger')
    def test_process_application_logging(self, mock_logger):
        """Test that application processing is logged."""
        application = self.create_sample_application()
        engine = UnderwritingEngine()
        
        engine.process_application(application, "standard")
        
        # Check that info logs were called
        mock_logger.info.assert_called()
    
    def test_reload_configurations(self):
        """Test reloading configurations."""
        engine = UnderwritingEngine()
        
        # Store original count
        original_count = len(engine._rule_evaluators)
        
        # Reload configurations
        engine.reload_configurations()
        
        # Should still have the same number of evaluators
        assert len(engine._rule_evaluators) == original_count
    
    def test_process_application_with_violations(self):
        """Test processing application with driver violations."""
        from underwriting.core.models import Violation, ViolationType, ViolationSeverity
        
        application = self.create_sample_application()
        
        # Add a violation to the driver
        violation = Violation(
            violation_type=ViolationType.SPEEDING_15_OVER,
            violation_date=date(2023, 1, 1),
            description="Speeding violation",
            severity=ViolationSeverity.MODERATE
        )
        application.applicant.violations.append(violation)
        
        engine = UnderwritingEngine()
        decision = engine.process_application(application, "standard")
        
        assert decision is not None
        # Risk score should be higher due to violation
        assert decision.risk_score.overall_score > 0
    
    def test_process_application_with_claims(self):
        """Test processing application with driver claims."""
        from underwriting.core.models import Claim, ClaimType
        
        application = self.create_sample_application()
        
        # Add a claim to the driver
        claim = Claim(
            claim_type=ClaimType.AT_FAULT,
            claim_date=date(2023, 1, 1),
            description="At-fault accident",
            amount=Decimal("5000.00"),
            at_fault=True
        )
        application.applicant.claims.append(claim)
        
        engine = UnderwritingEngine()
        decision = engine.process_application(application, "standard")
        
        assert decision is not None
        # Risk score should be higher due to claim
        assert decision.risk_score.overall_score > 0
    
    def test_process_application_with_poor_credit(self):
        """Test processing application with poor credit score."""
        application = self.create_sample_application()
        application.credit_score = 400  # Poor credit
        
        engine = UnderwritingEngine()
        decision = engine.process_application(application, "standard")
        
        assert decision is not None
        # Decision might be adjudication or denial due to poor credit
        assert decision.decision in [DecisionType.ADJUDICATE, DecisionType.DENY]
    
    def test_process_application_with_fraud_conviction(self):
        """Test processing application with fraud conviction."""
        application = self.create_sample_application()
        application.fraud_conviction = True
        
        engine = UnderwritingEngine()
        decision = engine.process_application(application, "standard")
        
        assert decision is not None
        # Should be denied due to fraud conviction
        assert decision.decision == DecisionType.DENY
    
    def test_process_application_with_coverage_lapse(self):
        """Test processing application with coverage lapse."""
        application = self.create_sample_application()
        application.coverage_lapse_days = 120  # Extended lapse
        
        engine = UnderwritingEngine()
        decision = engine.process_application(application, "standard")
        
        assert decision is not None
        # Decision might be adjudication or denial due to coverage lapse
        assert decision.decision in [DecisionType.ADJUDICATE, DecisionType.DENY]