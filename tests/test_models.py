"""
Tests for the Pydantic models.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from underwriting.core.models import (
    Application,
    Driver,
    Vehicle,
    Violation,
    Claim,
    UnderwritingDecision,
    RiskScore,
    LicenseStatus,
    ViolationType,
    ViolationSeverity,
    ClaimType,
    VehicleCategory,
    DecisionType,
)


class TestViolation:
    """Test Violation model."""
    
    def test_valid_violation(self):
        """Test creating a valid violation."""
        violation = Violation(
            violation_type=ViolationType.SPEEDING_15_OVER,
            violation_date=date(2023, 1, 15),
            description="Speeding 15 mph over limit",
            severity=ViolationSeverity.MODERATE,
            fine_amount=Decimal("150.00"),
            points=3,
            conviction_date=date(2023, 2, 1)
        )
        
        assert violation.violation_type == ViolationType.SPEEDING_15_OVER
        assert violation.violation_date == date(2023, 1, 15)
        assert violation.fine_amount == Decimal("150.00")
        assert violation.points == 3
    
    def test_violation_future_date_invalid(self):
        """Test that future violation dates are invalid."""
        future_date = date(2030, 1, 1)
        
        with pytest.raises(ValueError, match="Violation date cannot be in the future"):
            Violation(
                violation_type=ViolationType.SPEEDING_15_OVER,
                violation_date=future_date,
                description="Future violation",
                severity=ViolationSeverity.MODERATE
            )
    
    def test_conviction_before_violation_invalid(self):
        """Test that conviction date before violation date is invalid."""
        with pytest.raises(ValueError, match="Conviction date cannot be before violation date"):
            Violation(
                violation_type=ViolationType.SPEEDING_15_OVER,
                violation_date=date(2023, 2, 1),
                description="Invalid dates",
                severity=ViolationSeverity.MODERATE,
                conviction_date=date(2023, 1, 1)
            )


class TestClaim:
    """Test Claim model."""
    
    def test_valid_claim(self):
        """Test creating a valid claim."""
        claim = Claim(
            claim_type=ClaimType.AT_FAULT,
            claim_date=date(2023, 1, 15),
            description="Rear-end collision",
            amount=Decimal("5000.00"),
            at_fault=True,
            closed_date=date(2023, 2, 1),
            settlement_amount=Decimal("4500.00")
        )
        
        assert claim.claim_type == ClaimType.AT_FAULT
        assert claim.amount == Decimal("5000.00")
        assert claim.at_fault is True
        assert claim.settlement_amount == Decimal("4500.00")
    
    def test_claim_future_date_invalid(self):
        """Test that future claim dates are invalid."""
        future_date = date(2030, 1, 1)
        
        with pytest.raises(ValueError, match="Claim date cannot be in the future"):
            Claim(
                claim_type=ClaimType.AT_FAULT,
                claim_date=future_date,
                description="Future claim",
                amount=Decimal("1000.00"),
                at_fault=True
            )
    
    def test_closed_before_claim_invalid(self):
        """Test that closed date before claim date is invalid."""
        with pytest.raises(ValueError, match="Closed date cannot be before claim date"):
            Claim(
                claim_type=ClaimType.AT_FAULT,
                claim_date=date(2023, 2, 1),
                description="Invalid dates",
                amount=Decimal("1000.00"),
                at_fault=True,
                closed_date=date(2023, 1, 1)
            )


class TestVehicle:
    """Test Vehicle model."""
    
    def test_valid_vehicle(self):
        """Test creating a valid vehicle."""
        vehicle = Vehicle(
            year=2020,
            make="Toyota",
            model="Camry",
            vin="1HGBH41JXMN109186",
            category=VehicleCategory.SEDAN,
            value=Decimal("25000.00"),
            usage="personal",
            annual_mileage=12000,
            anti_theft_device=True
        )
        
        assert vehicle.year == 2020
        assert vehicle.make == "Toyota"
        assert vehicle.model == "Camry"
        assert vehicle.vin == "1HGBH41JXMN109186"
        assert vehicle.category == VehicleCategory.SEDAN
        assert vehicle.value == Decimal("25000.00")
        assert vehicle.anti_theft_device is True
    
    def test_vin_validation(self):
        """Test VIN validation."""
        # Valid VIN
        vehicle = Vehicle(
            year=2020,
            make="Toyota",
            model="Camry",
            vin="1hgbh41jxmn109186",  # lowercase
            category=VehicleCategory.SEDAN,
            value=Decimal("25000.00")
        )
        
        # Should be converted to uppercase
        assert vehicle.vin == "1HGBH41JXMN109186"
        
        # Invalid VIN with non-alphanumeric characters
        with pytest.raises(ValueError, match="VIN must contain only alphanumeric characters"):
            Vehicle(
                year=2020,
                make="Toyota",
                model="Camry",
                vin="1HGBH41JXMN109-86",  # contains dash
                category=VehicleCategory.SEDAN,
                value=Decimal("25000.00")
            )


class TestDriver:
    """Test Driver model."""
    
    def test_valid_driver(self):
        """Test creating a valid driver."""
        driver = Driver(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            license_number="D12345678",
            license_status=LicenseStatus.VALID,
            license_state="ca",  # lowercase
            license_issue_date=date(2008, 1, 1),
            license_expiration_date=date(2028, 1, 1),
            years_licensed=15
        )
        
        assert driver.first_name == "John"
        assert driver.last_name == "Doe"
        assert driver.license_status == LicenseStatus.VALID
        assert driver.license_state == "CA"  # Should be uppercase
        assert driver.age > 30  # Should calculate current age
    
    def test_driver_age_calculation(self):
        """Test age calculation property."""
        # Create driver born 30 years ago
        birth_date = date(date.today().year - 30, 1, 1)
        driver = Driver(
            first_name="John",
            last_name="Doe",
            date_of_birth=birth_date,
            license_number="D12345678",
            license_status=LicenseStatus.VALID,
            license_state="CA"
        )
        
        # Age should be approximately 30 (might be 29 or 30 depending on current date)
        assert driver.age >= 29
        assert driver.age <= 30
    
    def test_driver_too_young_invalid(self):
        """Test that drivers under 16 are invalid."""
        young_date = date(date.today().year - 15, 1, 1)  # 15 years old
        
        with pytest.raises(ValueError, match="Driver must be at least 16 years old"):
            Driver(
                first_name="Too",
                last_name="Young",
                date_of_birth=young_date,
                license_number="D12345678",
                license_status=LicenseStatus.VALID,
                license_state="CA"
            )
    
    def test_driver_too_old_invalid(self):
        """Test that drivers over 100 are invalid."""
        old_date = date(date.today().year - 101, 1, 1)  # 101 years old
        
        with pytest.raises(ValueError, match="Driver age cannot exceed 100 years"):
            Driver(
                first_name="Too",
                last_name="Old",
                date_of_birth=old_date,
                license_number="D12345678",
                license_status=LicenseStatus.VALID,
                license_state="CA"
            )


class TestApplication:
    """Test Application model."""
    
    def create_sample_driver(self):
        """Create a sample driver for testing."""
        return Driver(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            license_number="D12345678",
            license_status=LicenseStatus.VALID,
            license_state="CA"
        )
    
    def create_sample_vehicle(self):
        """Create a sample vehicle for testing."""
        return Vehicle(
            year=2020,
            make="Toyota",
            model="Camry",
            vin="1HGBH41JXMN109186",
            category=VehicleCategory.SEDAN,
            value=Decimal("25000.00")
        )
    
    def test_valid_application(self):
        """Test creating a valid application."""
        applicant = self.create_sample_driver()
        vehicle = self.create_sample_vehicle()
        
        application = Application(
            applicant=applicant,
            vehicles=[vehicle],
            credit_score=750,
            fraud_conviction=False,
            coverage_lapse_days=0,
            previous_carrier="State Farm",
            policy_limit=Decimal("500000.00"),
            deductible=Decimal("500.00")
        )
        
        assert application.applicant == applicant
        assert len(application.vehicles) == 1
        assert application.vehicles[0] == vehicle
        assert application.credit_score == 750
        assert application.fraud_conviction is False
        assert application.coverage_lapse_days == 0
    
    def test_application_all_drivers_property(self):
        """Test all_drivers property."""
        applicant = self.create_sample_driver()
        additional_driver = Driver(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=date(1995, 1, 1),
            license_number="D87654321",
            license_status=LicenseStatus.VALID,
            license_state="CA"
        )
        vehicle = self.create_sample_vehicle()
        
        application = Application(
            applicant=applicant,
            additional_drivers=[additional_driver],
            vehicles=[vehicle]
        )
        
        all_drivers = application.all_drivers
        assert len(all_drivers) == 2
        assert applicant in all_drivers
        assert additional_driver in all_drivers
    
    def test_application_primary_vehicle_property(self):
        """Test primary_vehicle property."""
        applicant = self.create_sample_driver()
        vehicle1 = self.create_sample_vehicle()
        vehicle2 = Vehicle(
            year=2019,
            make="Honda",
            model="Civic",
            vin="2HGBH41JXMN109187",
            category=VehicleCategory.SEDAN,
            value=Decimal("20000.00")
        )
        
        application = Application(
            applicant=applicant,
            vehicles=[vehicle1, vehicle2]
        )
        
        assert application.primary_vehicle == vehicle1
    
    def test_application_no_vehicles_invalid(self):
        """Test that application without vehicles is invalid."""
        applicant = self.create_sample_driver()
        
        with pytest.raises(ValueError, match="At least one vehicle is required"):
            Application(
                applicant=applicant,
                vehicles=[]
            )


class TestRiskScore:
    """Test RiskScore model."""
    
    def test_valid_risk_score(self):
        """Test creating a valid risk score."""
        risk_score = RiskScore(
            overall_score=450,
            driver_risk=200,
            vehicle_risk=100,
            history_risk=150,
            credit_risk=50,
            factors=["Young driver", "Minor violations"]
        )
        
        assert risk_score.overall_score == 450
        assert risk_score.driver_risk == 200
        assert risk_score.vehicle_risk == 100
        assert risk_score.history_risk == 150
        assert risk_score.credit_risk == 50
        assert "Young driver" in risk_score.factors
    
    def test_risk_level_property(self):
        """Test risk_level property calculation."""
        # Low risk
        low_risk = RiskScore(overall_score=200, driver_risk=100, vehicle_risk=100, history_risk=0)
        assert low_risk.risk_level == "LOW"
        
        # Moderate risk
        moderate_risk = RiskScore(overall_score=450, driver_risk=200, vehicle_risk=150, history_risk=100)
        assert moderate_risk.risk_level == "MODERATE"
        
        # High risk
        high_risk = RiskScore(overall_score=700, driver_risk=300, vehicle_risk=200, history_risk=200)
        assert high_risk.risk_level == "HIGH"
        
        # Very high risk
        very_high_risk = RiskScore(overall_score=900, driver_risk=400, vehicle_risk=300, history_risk=200)
        assert very_high_risk.risk_level == "VERY_HIGH"


class TestUnderwritingDecision:
    """Test UnderwritingDecision model."""
    
    def test_valid_decision(self):
        """Test creating a valid decision."""
        application_id = uuid4()
        risk_score = RiskScore(
            overall_score=450,
            driver_risk=200,
            vehicle_risk=100,
            history_risk=150
        )
        
        decision = UnderwritingDecision(
            application_id=application_id,
            decision=DecisionType.ACCEPT,
            reason="Clean record mature driver",
            risk_score=risk_score,
            rule_set="standard",
            triggered_rules=["ACC001"],
            additional_notes="Approved with standard rates"
        )
        
        assert decision.application_id == application_id
        assert decision.decision == DecisionType.ACCEPT
        assert decision.reason == "Clean record mature driver"
        assert decision.risk_score == risk_score
        assert decision.rule_set == "standard"
        assert "ACC001" in decision.triggered_rules
    
    def test_is_approved_property(self):
        """Test is_approved property."""
        application_id = uuid4()
        risk_score = RiskScore(overall_score=300, driver_risk=100, vehicle_risk=100, history_risk=100)
        
        # Approved decision
        approved_decision = UnderwritingDecision(
            application_id=application_id,
            decision=DecisionType.ACCEPT,
            reason="Approved",
            risk_score=risk_score,
            rule_set="standard"
        )
        assert approved_decision.is_approved is True
        
        # Denied decision
        denied_decision = UnderwritingDecision(
            application_id=application_id,
            decision=DecisionType.DENY,
            reason="High risk",
            risk_score=risk_score,
            rule_set="standard"
        )
        assert denied_decision.is_approved is False
        
        # Adjudication decision
        adjudication_decision = UnderwritingDecision(
            application_id=application_id,
            decision=DecisionType.ADJUDICATE,
            reason="Requires review",
            risk_score=risk_score,
            rule_set="standard"
        )
        assert adjudication_decision.is_approved is False
    
    def test_requires_review_property(self):
        """Test requires_review property."""
        application_id = uuid4()
        risk_score = RiskScore(overall_score=300, driver_risk=100, vehicle_risk=100, history_risk=100)
        
        # Adjudication decision
        adjudication_decision = UnderwritingDecision(
            application_id=application_id,
            decision=DecisionType.ADJUDICATE,
            reason="Requires review",
            risk_score=risk_score,
            rule_set="standard"
        )
        assert adjudication_decision.requires_review is True
        
        # Approved decision
        approved_decision = UnderwritingDecision(
            application_id=application_id,
            decision=DecisionType.ACCEPT,
            reason="Approved",
            risk_score=risk_score,
            rule_set="standard"
        )
        assert approved_decision.requires_review is False