"""
Custom validation utilities for the underwriting system.

This module provides additional validation functions beyond what's included
in the Pydantic models, focusing on business logic validation.
"""

from datetime import date, timedelta
from typing import List, Optional, Tuple

from loguru import logger

from ..core.models import Application, Driver, Vehicle, Violation, Claim


def validate_application_data(application: Application) -> Tuple[bool, List[str]]:
    """Comprehensive validation of application data.
    
    Args:
        application: The application to validate.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    
    # Validate basic application structure
    if not application.applicant:
        errors.append("Application must have a primary applicant")
    
    if not application.vehicles:
        errors.append("Application must have at least one vehicle")
    
    # Validate applicant
    if application.applicant:
        driver_errors = validate_driver(application.applicant, is_primary=True)
        errors.extend(driver_errors)
    
    # Validate additional drivers
    for i, driver in enumerate(application.additional_drivers):
        driver_errors = validate_driver(driver, is_primary=False)
        errors.extend([f"Additional driver {i+1}: {error}" for error in driver_errors])
    
    # Validate vehicles
    for i, vehicle in enumerate(application.vehicles):
        vehicle_errors = validate_vehicle(vehicle)
        errors.extend([f"Vehicle {i+1}: {error}" for error in vehicle_errors])
    
    # Validate business logic
    business_errors = validate_business_logic(application)
    errors.extend(business_errors)
    
    is_valid = len(errors) == 0
    
    if not is_valid:
        logger.warning(f"Application {application.id} validation failed with {len(errors)} errors")
    
    return is_valid, errors


def validate_driver(driver: Driver, is_primary: bool = False) -> List[str]:
    """Validate driver data.
    
    Args:
        driver: The driver to validate.
        is_primary: Whether this is the primary applicant.
        
    Returns:
        List of validation errors.
    """
    errors = []
    
    # Age validation
    if driver.age < 16:
        errors.append(f"Driver {driver.first_name} {driver.last_name} is under minimum age (16)")
    elif driver.age > 100:
        errors.append(f"Driver {driver.first_name} {driver.last_name} is over maximum age (100)")
    
    # License validation
    if driver.license_status.value in ["suspended", "revoked", "expired", "invalid"]:
        errors.append(f"Driver {driver.first_name} {driver.last_name} has invalid license status")
    
    # License state validation
    if len(driver.license_state) != 2:
        errors.append(f"Driver {driver.first_name} {driver.last_name} has invalid license state format")
    
    # Validate violations
    for i, violation in enumerate(driver.violations):
        violation_errors = validate_violation(violation)
        errors.extend([f"Violation {i+1}: {error}" for error in violation_errors])
    
    # Validate claims
    for i, claim in enumerate(driver.claims):
        claim_errors = validate_claim(claim)
        errors.extend([f"Claim {i+1}: {error}" for error in claim_errors])
    
    return errors


def validate_vehicle(vehicle: Vehicle) -> List[str]:
    """Validate vehicle data.
    
    Args:
        vehicle: The vehicle to validate.
        
    Returns:
        List of validation errors.
    """
    errors = []
    
    # Year validation
    current_year = date.today().year
    if vehicle.year < 1900:
        errors.append(f"Vehicle year {vehicle.year} is too old")
    elif vehicle.year > current_year + 1:
        errors.append(f"Vehicle year {vehicle.year} is in the future")
    
    # Value validation
    if vehicle.value <= 0:
        errors.append("Vehicle value must be positive")
    elif vehicle.value > 1000000:
        errors.append("Vehicle value exceeds maximum ($1,000,000)")
    
    # VIN validation
    if len(vehicle.vin) != 17:
        errors.append("VIN must be exactly 17 characters")
    elif not vehicle.vin.isalnum():
        errors.append("VIN must contain only alphanumeric characters")
    
    # Mileage validation
    if vehicle.annual_mileage is not None:
        if vehicle.annual_mileage < 0:
            errors.append("Annual mileage cannot be negative")
        elif vehicle.annual_mileage > 100000:
            errors.append("Annual mileage exceeds maximum (100,000)")
    
    return errors


def validate_violation(violation: Violation) -> List[str]:
    """Validate violation data.
    
    Args:
        violation: The violation to validate.
        
    Returns:
        List of validation errors.
    """
    errors = []
    
    # Date validation
    if violation.violation_date > date.today():
        errors.append("Violation date cannot be in the future")
    
    # Check if violation is too old (more than 10 years)
    ten_years_ago = date.today() - timedelta(days=10 * 365)
    if violation.violation_date < ten_years_ago:
        errors.append("Violation is more than 10 years old")
    
    # Conviction date validation
    if violation.conviction_date:
        if violation.conviction_date > date.today():
            errors.append("Conviction date cannot be in the future")
        if violation.conviction_date < violation.violation_date:
            errors.append("Conviction date cannot be before violation date")
    
    # Fine amount validation
    if violation.fine_amount is not None:
        if violation.fine_amount < 0:
            errors.append("Fine amount cannot be negative")
        elif violation.fine_amount > 50000:
            errors.append("Fine amount exceeds maximum ($50,000)")
    
    # Points validation
    if violation.points is not None:
        if violation.points < 0:
            errors.append("Points cannot be negative")
        elif violation.points > 12:
            errors.append("Points exceed maximum (12)")
    
    return errors


def validate_claim(claim: Claim) -> List[str]:
    """Validate claim data.
    
    Args:
        claim: The claim to validate.
        
    Returns:
        List of validation errors.
    """
    errors = []
    
    # Date validation
    if claim.claim_date > date.today():
        errors.append("Claim date cannot be in the future")
    
    # Check if claim is too old (more than 10 years)
    ten_years_ago = date.today() - timedelta(days=10 * 365)
    if claim.claim_date < ten_years_ago:
        errors.append("Claim is more than 10 years old")
    
    # Closed date validation
    if claim.closed_date:
        if claim.closed_date > date.today():
            errors.append("Closed date cannot be in the future")
        if claim.closed_date < claim.claim_date:
            errors.append("Closed date cannot be before claim date")
    
    # Amount validation
    if claim.amount < 0:
        errors.append("Claim amount cannot be negative")
    elif claim.amount > 1000000:
        errors.append("Claim amount exceeds maximum ($1,000,000)")
    
    # Settlement amount validation
    if claim.settlement_amount is not None:
        if claim.settlement_amount < 0:
            errors.append("Settlement amount cannot be negative")
        elif claim.settlement_amount > claim.amount:
            errors.append("Settlement amount cannot exceed claim amount")
    
    return errors


def validate_business_logic(application: Application) -> List[str]:
    """Validate business logic rules.
    
    Args:
        application: The application to validate.
        
    Returns:
        List of validation errors.
    """
    errors = []
    
    # Check credit score consistency
    if application.credit_score is not None:
        if application.credit_score < 300 or application.credit_score > 850:
            errors.append("Credit score must be between 300 and 850")
    
    # Check coverage lapse
    if application.coverage_lapse_days < 0:
        errors.append("Coverage lapse days cannot be negative")
    elif application.coverage_lapse_days > 365 * 5:
        errors.append("Coverage lapse exceeds maximum (5 years)")
    
    # Check vehicle count vs driver count
    if len(application.vehicles) > len(application.all_drivers) * 3:
        errors.append("Too many vehicles for number of drivers")
    
    # Check for duplicate license numbers
    license_numbers = [driver.license_number for driver in application.all_drivers]
    if len(license_numbers) != len(set(license_numbers)):
        errors.append("Duplicate license numbers found")
    
    # Check for duplicate VINs
    vins = [vehicle.vin for vehicle in application.vehicles]
    if len(vins) != len(set(vins)):
        errors.append("Duplicate VINs found")
    
    # Validate young driver restrictions
    for driver in application.all_drivers:
        if driver.age < 18:
            # Young drivers should have limited violation history
            major_violations = [v for v in driver.violations 
                             if v.severity.value == "major"]
            if major_violations:
                errors.append(f"Driver {driver.first_name} {driver.last_name} is under 18 with major violations")
    
    # Validate high-value vehicles
    for vehicle in application.vehicles:
        if vehicle.value > 100000:
            # High-value vehicles may require additional verification
            if not vehicle.anti_theft_device:
                errors.append(f"High-value vehicle {vehicle.make} {vehicle.model} should have anti-theft device")
    
    return errors


def validate_date_range(start_date: date, end_date: date, field_name: str) -> List[str]:
    """Validate date range.
    
    Args:
        start_date: Start date.
        end_date: End date.
        field_name: Name of the field being validated.
        
    Returns:
        List of validation errors.
    """
    errors = []
    
    if start_date > end_date:
        errors.append(f"{field_name} start date cannot be after end date")
    
    if start_date > date.today():
        errors.append(f"{field_name} start date cannot be in the future")
    
    if end_date > date.today():
        errors.append(f"{field_name} end date cannot be in the future")
    
    return errors


def validate_vin_format(vin: str) -> bool:
    """Validate VIN format using basic rules.
    
    Args:
        vin: Vehicle Identification Number.
        
    Returns:
        True if VIN format is valid.
    """
    if len(vin) != 17:
        return False
    
    # VIN should not contain I, O, Q
    invalid_chars = ['I', 'O', 'Q']
    if any(char in vin.upper() for char in invalid_chars):
        return False
    
    # VIN should be alphanumeric
    if not vin.isalnum():
        return False
    
    return True


def validate_license_number_format(license_number: str, state: str) -> bool:
    """Validate license number format (basic validation).
    
    Args:
        license_number: Driver license number.
        state: State that issued the license.
        
    Returns:
        True if license number format appears valid.
    """
    if not license_number:
        return False
    
    # Basic validation - should be alphanumeric and reasonable length
    if not license_number.replace('-', '').replace(' ', '').isalnum():
        return False
    
    if len(license_number) < 4 or len(license_number) > 20:
        return False
    
    return True