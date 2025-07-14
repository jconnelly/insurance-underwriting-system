"""
Sample data generator for testing the underwriting system.

This module provides utilities to generate realistic sample applications
for testing and demonstration purposes.
"""

import random
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from underwriting.core.models import (
    Application,
    Driver,
    Vehicle,
    Violation,
    Claim,
    LicenseStatus,
    ViolationType,
    ViolationSeverity,
    ClaimType,
    VehicleCategory,
)


class SampleDataGenerator:
    """Generates realistic sample data for testing."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the sample data generator.
        
        Args:
            seed: Random seed for reproducibility.
        """
        if seed is not None:
            random.seed(seed)
        
        # Sample data for generation
        self.first_names = [
            "John", "Jane", "Michael", "Sarah", "David", "Lisa", "Robert", "Jennifer",
            "William", "Mary", "James", "Patricia", "Christopher", "Linda", "Daniel",
            "Elizabeth", "Matthew", "Barbara", "Anthony", "Susan", "Mark", "Jessica",
            "Donald", "Helen", "Steven", "Nancy", "Paul", "Betty", "Andrew", "Dorothy"
        ]
        
        self.last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
            "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
            "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
        ]
        
        self.vehicle_makes = [
            "Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "Hyundai", "Kia", "Volkswagen",
            "BMW", "Mercedes-Benz", "Audi", "Lexus", "Acura", "Infiniti", "Cadillac",
            "Porsche", "Ferrari", "Lamborghini", "Maserati", "Jaguar", "Land Rover",
            "Volvo", "Subaru", "Mazda", "Mitsubishi", "Jeep", "Dodge", "Chrysler"
        ]
        
        self.vehicle_models = {
            "Toyota": ["Camry", "Corolla", "Prius", "Rav4", "Highlander", "Sienna"],
            "Honda": ["Civic", "Accord", "CR-V", "Pilot", "Odyssey", "Fit"],
            "Ford": ["F-150", "Mustang", "Explorer", "Escape", "Focus", "Fusion"],
            "Chevrolet": ["Silverado", "Malibu", "Equinox", "Tahoe", "Cruze", "Impala"],
            "BMW": ["3 Series", "5 Series", "X3", "X5", "7 Series", "Z4"],
            "Mercedes-Benz": ["C-Class", "E-Class", "S-Class", "GLE", "GLC", "AMG GT"],
            "Audi": ["A4", "A6", "Q5", "Q7", "A3", "TT"],
            "Porsche": ["911", "Cayenne", "Macan", "Panamera", "Boxster", "Cayman"],
            "Ferrari": ["488", "F8", "Portofino", "Roma", "812", "SF90"],
            "Lamborghini": ["Huracan", "Aventador", "Urus", "Gallardo", "Murcielago"],
        }
        
        self.states = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
            "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
            "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
            "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
            "WI", "WY"
        ]
        
        self.carriers = [
            "State Farm", "Allstate", "Progressive", "GEICO", "Farmers", "Liberty Mutual",
            "Nationwide", "USAA", "Travelers", "American Family", "Auto-Owners", "Erie"
        ]
    
    def generate_application(self, risk_profile: str = "random") -> Application:
        """Generate a sample application.
        
        Args:
            risk_profile: Risk profile (low, medium, high, or random).
            
        Returns:
            Generated Application instance.
        """
        # Generate primary applicant
        applicant = self.generate_driver(risk_profile)
        
        # Generate additional drivers (0-2)
        additional_drivers = []
        num_additional = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
        for _ in range(num_additional):
            additional_drivers.append(self.generate_driver(risk_profile))
        
        # Generate vehicles (1-3)
        vehicles = []
        num_vehicles = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
        for _ in range(num_vehicles):
            vehicles.append(self.generate_vehicle(risk_profile))
        
        # Generate application data
        credit_score = self.generate_credit_score(risk_profile)
        fraud_conviction = self.generate_fraud_conviction(risk_profile)
        coverage_lapse_days = self.generate_coverage_lapse(risk_profile)
        previous_carrier = random.choice(self.carriers) if random.random() < 0.8 else None
        
        return Application(
            applicant=applicant,
            additional_drivers=additional_drivers,
            vehicles=vehicles,
            credit_score=credit_score,
            fraud_conviction=fraud_conviction,
            coverage_lapse_days=coverage_lapse_days,
            previous_carrier=previous_carrier,
            policy_limit=Decimal(str(random.choice([250000, 500000, 1000000]))),
            deductible=Decimal(str(random.choice([250, 500, 1000, 2000])))
        )
    
    def generate_driver(self, risk_profile: str = "random") -> Driver:
        """Generate a sample driver.
        
        Args:
            risk_profile: Risk profile (low, medium, high, or random).
            
        Returns:
            Generated Driver instance.
        """
        # Generate basic info
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        
        # Generate age based on risk profile
        if risk_profile == "low":
            age = random.randint(30, 65)
        elif risk_profile == "high":
            age = random.choice(list(range(16, 25)) + list(range(70, 85)))
        else:
            age = random.randint(16, 80)
        
        date_of_birth = date.today() - timedelta(days=age * 365 + random.randint(0, 365))
        
        # Generate license info
        license_number = self.generate_license_number()
        license_state = random.choice(self.states)
        
        # License status based on risk profile
        if risk_profile == "high":
            license_status = random.choices(
                [LicenseStatus.VALID, LicenseStatus.SUSPENDED, LicenseStatus.EXPIRED],
                weights=[0.7, 0.2, 0.1]
            )[0]
        else:
            license_status = random.choices(
                [LicenseStatus.VALID, LicenseStatus.EXPIRED],
                weights=[0.95, 0.05]
            )[0]
        
        # Generate violations and claims
        violations = self.generate_violations(risk_profile)
        claims = self.generate_claims(risk_profile)
        
        return Driver(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            license_number=license_number,
            license_status=license_status,
            license_state=license_state,
            license_issue_date=date_of_birth + timedelta(days=16*365),
            license_expiration_date=date.today() + timedelta(days=random.randint(30, 1095)),
            violations=violations,
            claims=claims,
            years_licensed=max(0, age - 16)
        )
    
    def generate_vehicle(self, risk_profile: str = "random") -> Vehicle:
        """Generate a sample vehicle.
        
        Args:
            risk_profile: Risk profile (low, medium, high, or random).
            
        Returns:
            Generated Vehicle instance.
        """
        # Generate make and model
        make = random.choice(self.vehicle_makes)
        if make in self.vehicle_models:
            model = random.choice(self.vehicle_models[make])
        else:
            model = f"Model {random.randint(1, 9)}"
        
        # Generate year
        current_year = date.today().year
        year = random.randint(current_year - 15, current_year + 1)
        
        # Generate category based on risk profile
        if risk_profile == "low":
            category = random.choice([
                VehicleCategory.SEDAN, VehicleCategory.SUV, VehicleCategory.MINIVAN
            ])
        elif risk_profile == "high":
            category = random.choices(
                [VehicleCategory.SPORTS_CAR, VehicleCategory.SUPERCAR, VehicleCategory.PERFORMANCE,
                 VehicleCategory.CONVERTIBLE, VehicleCategory.SEDAN],
                weights=[0.3, 0.1, 0.2, 0.2, 0.2]
            )[0]
        else:
            category = random.choice(list(VehicleCategory))
        
        # Generate value based on category and year
        base_value = {
            VehicleCategory.SEDAN: 25000,
            VehicleCategory.SUV: 35000,
            VehicleCategory.MINIVAN: 30000,
            VehicleCategory.PICKUP: 40000,
            VehicleCategory.SPORTS_CAR: 60000,
            VehicleCategory.CONVERTIBLE: 50000,
            VehicleCategory.PERFORMANCE: 80000,
            VehicleCategory.LUXURY_SEDAN: 70000,
            VehicleCategory.LUXURY_SUV: 90000,
            VehicleCategory.SUPERCAR: 200000,
            VehicleCategory.RACING: 150000,
            VehicleCategory.MODIFIED: 45000,
        }.get(category, 30000)
        
        # Adjust for year
        age_factor = max(0.1, 1.0 - (current_year - year) * 0.1)
        value = Decimal(str(int(base_value * age_factor * random.uniform(0.8, 1.2))))
        
        # Generate VIN
        vin = self.generate_vin()
        
        return Vehicle(
            year=year,
            make=make,
            model=model,
            vin=vin,
            category=category,
            value=value,
            usage="personal",
            annual_mileage=random.randint(5000, 25000),
            anti_theft_device=random.random() < 0.6
        )
    
    def generate_violations(self, risk_profile: str = "random") -> List[Violation]:
        """Generate sample violations for a driver.
        
        Args:
            risk_profile: Risk profile (low, medium, high, or random).
            
        Returns:
            List of Violation instances.
        """
        violations = []
        
        # Determine number of violations based on risk profile
        if risk_profile == "low":
            num_violations = random.choices([0, 1], weights=[0.8, 0.2])[0]
        elif risk_profile == "high":
            num_violations = random.choices([2, 3, 4, 5], weights=[0.3, 0.3, 0.2, 0.2])[0]
        else:
            num_violations = random.choices([0, 1, 2, 3], weights=[0.4, 0.3, 0.2, 0.1])[0]
        
        for _ in range(num_violations):
            # Generate violation type based on risk profile
            if risk_profile == "high":
                violation_type = random.choices(
                    [ViolationType.DUI, ViolationType.RECKLESS_DRIVING, ViolationType.SPEEDING_15_OVER,
                     ViolationType.HIT_AND_RUN, ViolationType.IMPROPER_PASSING],
                    weights=[0.2, 0.2, 0.3, 0.1, 0.2]
                )[0]
            else:
                violation_type = random.choices(
                    [ViolationType.SPEEDING_10_UNDER, ViolationType.IMPROPER_TURN, 
                     ViolationType.SPEEDING_15_OVER, ViolationType.FOLLOWING_TOO_CLOSE],
                    weights=[0.4, 0.3, 0.2, 0.1]
                )[0]
            
            # Generate violation date (within last 7 years)
            violation_date = date.today() - timedelta(
                days=random.randint(30, 7*365)
            )
            
            # Determine severity
            if violation_type in [ViolationType.DUI, ViolationType.RECKLESS_DRIVING, 
                                ViolationType.HIT_AND_RUN, ViolationType.VEHICULAR_HOMICIDE]:
                severity = ViolationSeverity.MAJOR
            elif violation_type in [ViolationType.SPEEDING_15_OVER, ViolationType.IMPROPER_PASSING,
                                  ViolationType.FOLLOWING_TOO_CLOSE]:
                severity = ViolationSeverity.MODERATE
            else:
                severity = ViolationSeverity.MINOR
            
            # Generate fine and points
            fine_amount = Decimal(str(random.randint(50, 1000)))
            points = random.randint(1, 6) if severity != ViolationSeverity.MINOR else random.randint(1, 3)
            
            violation = Violation(
                violation_type=violation_type,
                violation_date=violation_date,
                description=f"{violation_type.value.replace('_', ' ').title()} violation",
                severity=severity,
                fine_amount=fine_amount,
                points=points,
                conviction_date=violation_date + timedelta(days=random.randint(30, 90))
            )
            
            violations.append(violation)
        
        return violations
    
    def generate_claims(self, risk_profile: str = "random") -> List[Claim]:
        """Generate sample claims for a driver.
        
        Args:
            risk_profile: Risk profile (low, medium, high, or random).
            
        Returns:
            List of Claim instances.
        """
        claims = []
        
        # Determine number of claims based on risk profile
        if risk_profile == "low":
            num_claims = random.choices([0, 1], weights=[0.7, 0.3])[0]
        elif risk_profile == "high":
            num_claims = random.choices([2, 3, 4], weights=[0.4, 0.3, 0.3])[0]
        else:
            num_claims = random.choices([0, 1, 2], weights=[0.5, 0.3, 0.2])[0]
        
        for _ in range(num_claims):
            # Generate claim type
            claim_type = random.choice([
                ClaimType.AT_FAULT, ClaimType.NOT_AT_FAULT, ClaimType.COMPREHENSIVE,
                ClaimType.COLLISION, ClaimType.PROPERTY_DAMAGE
            ])
            
            # Generate claim date (within last 7 years)
            claim_date = date.today() - timedelta(
                days=random.randint(30, 7*365)
            )
            
            # Generate amount based on claim type
            if claim_type in [ClaimType.AT_FAULT, ClaimType.COLLISION]:
                amount = Decimal(str(random.randint(2000, 25000)))
            elif claim_type == ClaimType.COMPREHENSIVE:
                amount = Decimal(str(random.randint(500, 10000)))
            else:
                amount = Decimal(str(random.randint(1000, 15000)))
            
            # Determine at-fault status
            at_fault = claim_type == ClaimType.AT_FAULT or \
                      (claim_type == ClaimType.COLLISION and random.random() < 0.5)
            
            # Generate settlement amount
            settlement_amount = amount * Decimal(str(random.uniform(0.8, 1.0)))
            
            claim = Claim(
                claim_type=claim_type,
                claim_date=claim_date,
                description=f"{claim_type.value.replace('_', ' ').title()} claim",
                amount=amount,
                at_fault=at_fault,
                closed_date=claim_date + timedelta(days=random.randint(30, 180)),
                settlement_amount=settlement_amount
            )
            
            claims.append(claim)
        
        return claims
    
    def generate_credit_score(self, risk_profile: str = "random") -> Optional[int]:
        """Generate a credit score based on risk profile.
        
        Args:
            risk_profile: Risk profile (low, medium, high, or random).
            
        Returns:
            Credit score or None.
        """
        if random.random() < 0.1:  # 10% chance of no credit score
            return None
        
        if risk_profile == "low":
            return random.randint(700, 850)
        elif risk_profile == "high":
            return random.randint(300, 600)
        else:
            return random.randint(500, 750)
    
    def generate_fraud_conviction(self, risk_profile: str = "random") -> bool:
        """Generate fraud conviction status.
        
        Args:
            risk_profile: Risk profile (low, medium, high, or random).
            
        Returns:
            True if fraud conviction exists.
        """
        if risk_profile == "high":
            return random.random() < 0.05  # 5% chance
        else:
            return random.random() < 0.001  # 0.1% chance
    
    def generate_coverage_lapse(self, risk_profile: str = "random") -> int:
        """Generate coverage lapse days.
        
        Args:
            risk_profile: Risk profile (low, medium, high, or random).
            
        Returns:
            Number of days without coverage.
        """
        if risk_profile == "low":
            return random.choices([0, 1, 2, 3], weights=[0.8, 0.1, 0.05, 0.05])[0]
        elif risk_profile == "high":
            return random.choices([0, 30, 60, 90, 120, 180], weights=[0.3, 0.2, 0.2, 0.1, 0.1, 0.1])[0]
        else:
            return random.choices([0, 1, 7, 14, 30], weights=[0.6, 0.2, 0.1, 0.05, 0.05])[0]
    
    def generate_license_number(self) -> str:
        """Generate a realistic license number."""
        # Format: Letter + 8 digits
        letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        digits = "".join([str(random.randint(0, 9)) for _ in range(8)])
        return f"{letter}{digits}"
    
    def generate_vin(self) -> str:
        """Generate a realistic VIN number."""
        # Simplified VIN generation (17 characters, alphanumeric, no I, O, Q)
        chars = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
        return "".join([random.choice(chars) for _ in range(17)])
    
    def generate_batch_applications(self, count: int, risk_distribution: Optional[dict] = None) -> List[Application]:
        """Generate a batch of applications with specified risk distribution.
        
        Args:
            count: Number of applications to generate.
            risk_distribution: Dictionary with risk profile weights.
                             Default: {"low": 0.3, "medium": 0.5, "high": 0.2}
            
        Returns:
            List of Application instances.
        """
        if risk_distribution is None:
            risk_distribution = {"low": 0.3, "medium": 0.5, "high": 0.2}
        
        applications = []
        
        for _ in range(count):
            # Select risk profile based on distribution
            risk_profile = random.choices(
                list(risk_distribution.keys()),
                weights=list(risk_distribution.values())
            )[0]
            
            application = self.generate_application(risk_profile)
            applications.append(application)
        
        return applications