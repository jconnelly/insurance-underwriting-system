"""
Sample data generation for A/B testing framework.

This module provides algorithms for generating realistic sample data
for A/B testing different underwriting configurations.
"""

import random
import uuid
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from loguru import logger

from ..core.models import (
    Application, Driver, Vehicle, Violation, Claim,
    Gender, MaritalStatus, LicenseStatus, ViolationType, ViolationSeverity,
    ClaimType, VehicleCategory
)
# Note: SampleDataGenerator not needed as we implement generation internally


class ABTestSampleProfile(Enum):
    """A/B test sample profiles."""
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    MIXED = "mixed"
    EDGE_CASES = "edge_cases"


@dataclass
class ABTestSampleConfig:
    """Configuration for A/B test sample generation."""
    sample_size: int
    profile: ABTestSampleProfile
    risk_distribution: Dict[str, float]
    age_distribution: Dict[str, Tuple[int, int]]
    vehicle_categories: List[VehicleCategory]
    geographic_regions: List[str]
    seed: Optional[int] = None
    metadata: Dict[str, Any] = None


class ABTestSampleGenerator:
    """Advanced sample data generator for A/B testing."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize A/B test sample generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # Random seed for reproducible generation
        self.random = random.Random(seed)
        
        # A/B test specific configurations
        self.profile_configs = self._initialize_profile_configs()
        
        logger.info(f"A/B test sample generator initialized with seed: {seed}")
    
    def _initialize_profile_configs(self) -> Dict[ABTestSampleProfile, ABTestSampleConfig]:
        """Initialize predefined sample profile configurations."""
        return {
            ABTestSampleProfile.LOW_RISK: ABTestSampleConfig(
                sample_size=1000,
                profile=ABTestSampleProfile.LOW_RISK,
                risk_distribution={"low": 0.8, "medium": 0.2, "high": 0.0},
                age_distribution={"young": (25, 35), "middle": (35, 55), "senior": (55, 70)},
                vehicle_categories=[VehicleCategory.SEDAN, VehicleCategory.SUV, VehicleCategory.MINIVAN],
                geographic_regions=["suburban", "rural"]
            ),
            ABTestSampleProfile.MEDIUM_RISK: ABTestSampleConfig(
                sample_size=1000,
                profile=ABTestSampleProfile.MEDIUM_RISK,
                risk_distribution={"low": 0.3, "medium": 0.5, "high": 0.2},
                age_distribution={"young": (21, 30), "middle": (30, 50), "senior": (50, 75)},
                vehicle_categories=[cat for cat in VehicleCategory],
                geographic_regions=["urban", "suburban", "rural"]
            ),
            ABTestSampleProfile.HIGH_RISK: ABTestSampleConfig(
                sample_size=1000,
                profile=ABTestSampleProfile.HIGH_RISK,
                risk_distribution={"low": 0.1, "medium": 0.3, "high": 0.6},
                age_distribution={"young": (18, 25), "middle": (25, 40), "senior": (70, 85)},
                vehicle_categories=[VehicleCategory.SPORTS_CAR, VehicleCategory.LUXURY_SEDAN, VehicleCategory.CONVERTIBLE],
                geographic_regions=["urban", "high_crime"]
            ),
            ABTestSampleProfile.MIXED: ABTestSampleConfig(
                sample_size=1000,
                profile=ABTestSampleProfile.MIXED,
                risk_distribution={"low": 0.33, "medium": 0.34, "high": 0.33},
                age_distribution={"young": (18, 30), "middle": (30, 60), "senior": (60, 85)},
                vehicle_categories=[cat for cat in VehicleCategory],
                geographic_regions=["urban", "suburban", "rural", "high_crime"]
            ),
            ABTestSampleProfile.EDGE_CASES: ABTestSampleConfig(
                sample_size=500,
                profile=ABTestSampleProfile.EDGE_CASES,
                risk_distribution={"low": 0.2, "medium": 0.3, "high": 0.5},
                age_distribution={"very_young": (16, 21), "very_old": (80, 90)},
                vehicle_categories=[VehicleCategory.SPORTS_CAR, VehicleCategory.LUXURY_SEDAN, VehicleCategory.PICKUP],
                geographic_regions=["high_crime", "rural_remote"]
            )
        }
    
    def generate_test_samples(
        self, 
        profile: ABTestSampleProfile,
        sample_size: Optional[int] = None,
        custom_config: Optional[ABTestSampleConfig] = None
    ) -> List[Application]:
        """Generate sample applications for A/B testing.
        
        Args:
            profile: Sample profile to use
            sample_size: Override sample size
            custom_config: Custom configuration
            
        Returns:
            List of generated applications
        """
        # Get configuration
        if custom_config:
            config = custom_config
        else:
            config = self.profile_configs[profile]
        
        if sample_size:
            config.sample_size = sample_size
        
        logger.info(f"Generating {config.sample_size} samples for profile: {profile.value}")
        
        applications = []
        
        # Generate samples based on risk distribution
        for risk_level, proportion in config.risk_distribution.items():
            count = int(config.sample_size * proportion)
            
            for _ in range(count):
                application = self._generate_application_for_risk_level(
                    risk_level, config
                )
                applications.append(application)
        
        # Shuffle to randomize order
        random.shuffle(applications)
        
        logger.info(f"Generated {len(applications)} applications for A/B testing")
        return applications
    
    def _generate_application_for_risk_level(
        self, 
        risk_level: str, 
        config: ABTestSampleConfig
    ) -> Application:
        """Generate application for specific risk level."""
        if risk_level == "low":
            return self._generate_low_risk_application(config)
        elif risk_level == "medium":
            return self._generate_medium_risk_application(config)
        elif risk_level == "high":
            return self._generate_high_risk_application(config)
        else:
            # Fallback to medium risk
            return self._generate_medium_risk_application(config)
    
    def _generate_low_risk_application(self, config: ABTestSampleConfig) -> Application:
        """Generate low-risk application."""
        # Create driver with good profile
        driver = self._create_driver(
            age_range=(30, 60),
            license_years_range=(10, 40),
            violation_count_range=(0, 1),
            claim_count_range=(0, 0),
            credit_score_range=(700, 850)
        )
        
        # Create safe vehicle
        vehicle = self._create_vehicle(
            categories=[VehicleCategory.SEDAN, VehicleCategory.SUV, VehicleCategory.MINIVAN],
            value_range=(15000, 35000),
            safety_rating_range=(4, 5)
        )
        
        return Application(
            id=uuid.uuid4(),
            applicant=driver,
            additional_drivers=[],
            vehicles=[vehicle],
            coverage_lapse_days=random.randint(0, 30),
            credit_score=random.randint(700, 850),
            fraud_conviction=False
        )
    
    def _generate_medium_risk_application(self, config: ABTestSampleConfig) -> Application:
        """Generate medium-risk application."""
        # Create driver with moderate profile
        driver = self._create_driver(
            age_range=(25, 65),
            license_years_range=(5, 25),
            violation_count_range=(1, 3),
            claim_count_range=(0, 2),
            credit_score_range=(600, 750)
        )
        
        # Create moderate vehicle
        vehicle = self._create_vehicle(
            categories=[cat for cat in VehicleCategory if cat not in [VehicleCategory.SPORTS_CAR, VehicleCategory.LUXURY_SEDAN]],
            value_range=(20000, 50000),
            safety_rating_range=(3, 4)
        )
        
        return Application(
            id=uuid.uuid4(),
            applicant=driver,
            additional_drivers=[],
            vehicles=[vehicle],
            coverage_lapse_days=random.randint(0, 90),
            credit_score=random.randint(600, 750),
            fraud_conviction=False
        )
    
    def _generate_high_risk_application(self, config: ABTestSampleConfig) -> Application:
        """Generate high-risk application."""
        # Create driver with risky profile
        driver = self._create_driver(
            age_range=(18, 25) if random.random() < 0.6 else (70, 85),
            license_years_range=(1, 5) if random.random() < 0.7 else (10, 30),
            violation_count_range=(2, 5),
            claim_count_range=(1, 3),
            credit_score_range=(450, 650)
        )
        
        # Create risky vehicle
        vehicle = self._create_vehicle(
            categories=[VehicleCategory.SPORTS_CAR, VehicleCategory.LUXURY_SEDAN, VehicleCategory.CONVERTIBLE, VehicleCategory.PICKUP],
            value_range=(40000, 100000),
            safety_rating_range=(2, 3)
        )
        
        return Application(
            id=uuid.uuid4(),
            applicant=driver,
            additional_drivers=[],
            vehicles=[vehicle],
            coverage_lapse_days=random.randint(30, 180),
            credit_score=random.randint(450, 650),
            fraud_conviction=random.random() < 0.05
        )
    
    def _create_driver(
        self,
        age_range: Tuple[int, int],
        license_years_range: Tuple[int, int],
        violation_count_range: Tuple[int, int],
        claim_count_range: Tuple[int, int],
        credit_score_range: Tuple[int, int]
    ) -> Driver:
        """Create driver with specified characteristics."""
        age = random.randint(*age_range)
        license_years = min(random.randint(*license_years_range), age - 16)
        
        # Generate violations
        violations = []
        violation_count = random.randint(*violation_count_range)
        for _ in range(violation_count):
            violation_date = date.today() - timedelta(days=random.randint(120, 1825))  # 4 months to 5 years ago
            conviction_date = violation_date + timedelta(days=random.randint(30, 90))
            # Ensure conviction date is not in the future
            if conviction_date > date.today():
                conviction_date = date.today() - timedelta(days=random.randint(1, 30))
            violation_type = random.choice(list(ViolationType))
            
            violation = Violation(
                violation_type=violation_type,
                violation_date=violation_date,
                description=f"{violation_type.value.replace('_', ' ').title()} violation",
                severity=random.choice(list(ViolationSeverity)),
                conviction_date=conviction_date,
                fine_amount=random.randint(50, 500)
            )
            violations.append(violation)
        
        # Generate claims
        claims = []
        claim_count = random.randint(*claim_count_range)
        for _ in range(claim_count):
            claim_date = date.today() - timedelta(days=random.randint(30, 1825))
            claim = Claim(
                claim_type=random.choice(list(ClaimType)),
                claim_date=claim_date,
                amount=random.randint(1000, 25000),
                at_fault=random.random() < 0.6,
                description=f"Claim from {claim_date.strftime('%Y-%m-%d')}"
            )
            claims.append(claim)
        
        # Generate required fields
        birth_date = date.today() - timedelta(days=age*365)
        
        return Driver(
            first_name=f"Driver{random.randint(1000, 9999)}",
            last_name=f"Test{random.randint(100, 999)}",
            date_of_birth=birth_date,
            age=age,
            gender=random.choice(list(Gender)),
            marital_status=random.choice(list(MaritalStatus)),
            license_number=f"DL{random.randint(10000000, 99999999)}",
            license_status=LicenseStatus.VALID,
            license_state="CA",
            years_licensed=license_years,
            violations=violations,
            claims=claims
        )
    
    def _create_vehicle(
        self,
        categories: List[VehicleCategory],
        value_range: Tuple[int, int],
        safety_rating_range: Tuple[int, int]
    ) -> Vehicle:
        """Create vehicle with specified characteristics."""
        # Vehicle makes and models by category
        vehicle_data = {
            VehicleCategory.SEDAN: [
                ("Toyota", "Camry"), ("Honda", "Accord"), ("Nissan", "Altima"),
                ("Ford", "Fusion"), ("Chevrolet", "Malibu")
            ],
            VehicleCategory.SUV: [
                ("Toyota", "RAV4"), ("Honda", "CR-V"), ("Ford", "Explorer"),
                ("Chevrolet", "Tahoe"), ("Jeep", "Grand Cherokee")
            ],
            VehicleCategory.MINIVAN: [
                ("Honda", "Odyssey"), ("Toyota", "Sienna"), ("Chrysler", "Pacifica"),
                ("Mazda", "5"), ("Nissan", "Quest")
            ],
            VehicleCategory.SPORTS_CAR: [
                ("Chevrolet", "Corvette"), ("Ford", "Mustang"), ("Dodge", "Challenger"),
                ("BMW", "M3"), ("Porsche", "911")
            ],
            VehicleCategory.LUXURY_SEDAN: [
                ("BMW", "7 Series"), ("Mercedes-Benz", "S-Class"), ("Audi", "A8"),
                ("Lexus", "LS"), ("Cadillac", "Escalade")
            ],
            VehicleCategory.CONVERTIBLE: [
                ("Mazda", "MX-5 Miata"), ("BMW", "Z4"), ("Mercedes-Benz", "SLK"),
                ("Audi", "TT"), ("Chevrolet", "Camaro")
            ],
            VehicleCategory.PICKUP: [
                ("Ford", "F-150"), ("Chevrolet", "Silverado"), ("Toyota", "Tacoma"),
                ("Ram", "1500"), ("Nissan", "Frontier")
            ]
        }
        
        category = random.choice(categories)
        make, model = random.choice(vehicle_data.get(category, [("Generic", "Car")]))
        
        # Generate VIN (17 characters)
        vin = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=17))
        
        return Vehicle(
            year=random.randint(2015, 2024),
            make=make,
            model=model,
            vin=vin,
            category=category,
            value=random.randint(*value_range),
            safety_rating=random.randint(*safety_rating_range)
        )
    
    def generate_stratified_samples(
        self, 
        strata_config: Dict[str, int],
        base_profile: ABTestSampleProfile = ABTestSampleProfile.MIXED
    ) -> List[Application]:
        """Generate stratified samples for more controlled testing.
        
        Args:
            strata_config: Dictionary mapping strata names to sample sizes
            base_profile: Base profile for generation
            
        Returns:
            List of stratified applications
        """
        logger.info(f"Generating stratified samples: {strata_config}")
        
        all_applications = []
        
        for stratum, count in strata_config.items():
            applications = self._generate_stratum_samples(stratum, count, base_profile)
            all_applications.extend(applications)
        
        return all_applications
    
    def _generate_stratum_samples(
        self, 
        stratum: str, 
        count: int, 
        base_profile: ABTestSampleProfile
    ) -> List[Application]:
        """Generate samples for a specific stratum."""
        if stratum == "young_drivers":
            config = ABTestSampleConfig(
                sample_size=count,
                profile=base_profile,
                risk_distribution={"low": 0.2, "medium": 0.5, "high": 0.3},
                age_distribution={"young": (18, 25)},
                vehicle_categories=[cat for cat in VehicleCategory],
                geographic_regions=["urban", "suburban"]
            )
        elif stratum == "senior_drivers":
            config = ABTestSampleConfig(
                sample_size=count,
                profile=base_profile,
                risk_distribution={"low": 0.4, "medium": 0.4, "high": 0.2},
                age_distribution={"senior": (65, 85)},
                vehicle_categories=[VehicleCategory.SEDAN, VehicleCategory.SUV],
                geographic_regions=["suburban", "rural"]
            )
        elif stratum == "high_value_vehicles":
            config = ABTestSampleConfig(
                sample_size=count,
                profile=base_profile,
                risk_distribution={"low": 0.3, "medium": 0.4, "high": 0.3},
                age_distribution={"middle": (30, 60)},
                vehicle_categories=[VehicleCategory.LUXURY_SEDAN, VehicleCategory.SPORTS_CAR],
                geographic_regions=["urban", "suburban"]
            )
        else:
            # Default to mixed profile
            config = self.profile_configs[base_profile]
            config.sample_size = count
        
        return self.generate_test_samples(base_profile, count, config)
    
    def generate_power_analysis_samples(
        self, 
        effect_size: float,
        power: float = 0.8,
        alpha: float = 0.05
    ) -> Tuple[int, List[Application]]:
        """Generate samples sized for power analysis.
        
        Args:
            effect_size: Expected effect size
            power: Statistical power desired
            alpha: Significance level
            
        Returns:
            Tuple of (calculated_sample_size, generated_applications)
        """
        # Simple power analysis calculation
        from scipy import stats
        import math
        
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)
        
        # For proportion test (acceptance rate)
        n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
        sample_size = max(int(math.ceil(n)), 100)
        
        logger.info(f"Power analysis: effect_size={effect_size}, power={power}, calculated_n={sample_size}")
        
        # Generate samples
        applications = self.generate_test_samples(
            ABTestSampleProfile.MIXED,
            sample_size
        )
        
        return sample_size, applications
    
    def generate_sequential_samples(
        self, 
        batch_size: int,
        profile: ABTestSampleProfile = ABTestSampleProfile.MIXED
    ) -> List[Application]:
        """Generate samples for sequential testing.
        
        Args:
            batch_size: Size of each batch
            profile: Sample profile
            
        Returns:
            Batch of applications
        """
        return self.generate_test_samples(profile, batch_size)