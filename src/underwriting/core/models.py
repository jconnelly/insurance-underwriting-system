"""
Pydantic models for the insurance underwriting system.

This module contains all data models used throughout the underwriting process,
including applications, drivers, vehicles, violations, claims, and decisions.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.types import conint, constr


class LicenseStatus(str, Enum):
    """Driver license status enumeration."""
    VALID = "valid"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"
    INVALID = "invalid"


class ViolationType(str, Enum):
    """Traffic violation types."""
    DUI = "DUI"
    RECKLESS_DRIVING = "reckless_driving"
    HIT_AND_RUN = "hit_and_run"
    VEHICULAR_HOMICIDE = "vehicular_homicide"
    SPEEDING_15_OVER = "speeding_15_over"
    IMPROPER_PASSING = "improper_passing"
    FOLLOWING_TOO_CLOSE = "following_too_close"
    SPEEDING_10_UNDER = "speeding_10_under"
    IMPROPER_TURN = "improper_turn"
    PARKING_VIOLATION = "parking_violation"


class ViolationSeverity(str, Enum):
    """Violation severity levels."""
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"


class ClaimType(str, Enum):
    """Insurance claim types."""
    AT_FAULT = "at_fault"
    NOT_AT_FAULT = "not_at_fault"
    COMPREHENSIVE = "comprehensive"
    COLLISION = "collision"
    PROPERTY_DAMAGE = "property_damage"
    BODILY_INJURY = "bodily_injury"


class VehicleCategory(str, Enum):
    """Vehicle category classifications."""
    SEDAN = "sedan"
    SUV = "suv"
    MINIVAN = "minivan"
    PICKUP = "pickup"
    SPORTS_CAR = "sports_car"
    CONVERTIBLE = "convertible"
    PERFORMANCE = "performance"
    LUXURY_SEDAN = "luxury_sedan"
    LUXURY_SUV = "luxury_suv"
    SUPERCAR = "supercar"
    RACING = "racing"
    MODIFIED = "modified"


class DecisionType(str, Enum):
    """Underwriting decision types."""
    ACCEPT = "ACCEPT"
    DENY = "DENY"
    ADJUDICATE = "ADJUDICATE"


class Violation(BaseModel):
    """Traffic violation model."""
    id: UUID = Field(default_factory=uuid4)
    violation_type: ViolationType
    violation_date: date
    description: str
    severity: ViolationSeverity
    fine_amount: Optional[Decimal] = None
    points: Optional[int] = None
    conviction_date: Optional[date] = None
    
    @field_validator('violation_date', 'conviction_date')
    @classmethod
    def validate_dates(cls, v):
        if v and v > date.today():
            raise ValueError('Violation date cannot be in the future')
        return v
    
    @model_validator(mode='after')
    def validate_conviction_after_violation(self):
        if self.violation_date and self.conviction_date and self.conviction_date < self.violation_date:
            raise ValueError('Conviction date cannot be before violation date')
        return self


class Claim(BaseModel):
    """Insurance claim model."""
    id: UUID = Field(default_factory=uuid4)
    claim_type: ClaimType
    claim_date: date
    description: str
    amount: Decimal = Field(ge=0)
    at_fault: bool
    closed_date: Optional[date] = None
    settlement_amount: Optional[Decimal] = None
    
    @field_validator('claim_date', 'closed_date')
    @classmethod
    def validate_dates(cls, v):
        if v and v > date.today():
            raise ValueError('Claim date cannot be in the future')
        return v
    
    @model_validator(mode='after')
    def validate_closed_after_claim(self):
        if self.claim_date and self.closed_date and self.closed_date < self.claim_date:
            raise ValueError('Closed date cannot be before claim date')
        return self


class Vehicle(BaseModel):
    """Vehicle model."""
    id: UUID = Field(default_factory=uuid4)
    year: conint(ge=1900, le=2030)
    make: constr(min_length=1, max_length=50)
    model: constr(min_length=1, max_length=50)
    vin: constr(min_length=17, max_length=17)
    category: VehicleCategory
    value: Decimal = Field(ge=0)
    usage: str = Field(default="personal")
    annual_mileage: Optional[conint(ge=0, le=100000)] = None
    anti_theft_device: bool = Field(default=False)
    
    @field_validator('vin')
    @classmethod
    def validate_vin(cls, v):
        if not v.isalnum():
            raise ValueError('VIN must contain only alphanumeric characters')
        return v.upper()


class Driver(BaseModel):
    """Driver model."""
    id: UUID = Field(default_factory=uuid4)
    first_name: constr(min_length=1, max_length=50)
    last_name: constr(min_length=1, max_length=50)
    date_of_birth: date
    license_number: constr(min_length=1, max_length=20)
    license_status: LicenseStatus
    license_state: constr(min_length=2, max_length=2)
    license_issue_date: Optional[date] = None
    license_expiration_date: Optional[date] = None
    violations: List[Violation] = Field(default_factory=list)
    claims: List[Claim] = Field(default_factory=list)
    years_licensed: Optional[conint(ge=0)] = None
    
    @property
    def age(self) -> int:
        """Calculate driver's current age."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_age(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 16:
            raise ValueError('Driver must be at least 16 years old')
        if age > 100:
            raise ValueError('Driver age cannot exceed 100 years')
        return v
    
    @field_validator('license_state')
    @classmethod
    def validate_license_state(cls, v):
        return v.upper()


class Application(BaseModel):
    """Insurance application model."""
    id: UUID = Field(default_factory=uuid4)
    application_date: datetime = Field(default_factory=datetime.now)
    applicant: Driver
    additional_drivers: List[Driver] = Field(default_factory=list)
    vehicles: List[Vehicle] = Field(min_items=1)
    credit_score: Optional[conint(ge=300, le=850)] = None
    fraud_conviction: bool = Field(default=False)
    coverage_lapse_days: conint(ge=0) = Field(default=0)
    previous_carrier: Optional[str] = None
    policy_limit: Optional[Decimal] = None
    deductible: Optional[Decimal] = None
    
    @property
    def all_drivers(self) -> List[Driver]:
        """Get all drivers (applicant + additional drivers)."""
        return [self.applicant] + self.additional_drivers
    
    @property
    def primary_vehicle(self) -> Vehicle:
        """Get the primary vehicle (first vehicle in list)."""
        return self.vehicles[0]
    
    @field_validator('vehicles')
    @classmethod
    def validate_vehicles_not_empty(cls, v):
        if not v:
            raise ValueError('At least one vehicle is required')
        return v


class RiskScore(BaseModel):
    """Risk assessment score model."""
    overall_score: conint(ge=0, le=1000)
    driver_risk: conint(ge=0, le=1000)
    vehicle_risk: conint(ge=0, le=1000)
    history_risk: conint(ge=0, le=1000)
    credit_risk: Optional[conint(ge=0, le=1000)] = None
    factors: List[str] = Field(default_factory=list)
    
    @property
    def risk_level(self) -> str:
        """Determine risk level based on overall score."""
        if self.overall_score <= 300:
            return "LOW"
        elif self.overall_score <= 600:
            return "MODERATE"
        elif self.overall_score <= 800:
            return "HIGH"
        else:
            return "VERY_HIGH"


class UnderwritingDecision(BaseModel):
    """Underwriting decision model."""
    id: UUID = Field(default_factory=uuid4)
    application_id: UUID
    decision: DecisionType
    decision_date: datetime = Field(default_factory=datetime.now)
    reason: str
    risk_score: RiskScore
    rule_set: str
    triggered_rules: List[str] = Field(default_factory=list)
    additional_notes: Optional[str] = None
    underwriter_id: Optional[str] = None
    
    @property
    def is_approved(self) -> bool:
        """Check if decision is approved."""
        return self.decision == DecisionType.ACCEPT
    
    @property
    def requires_review(self) -> bool:
        """Check if decision requires manual review."""
        return self.decision == DecisionType.ADJUDICATE