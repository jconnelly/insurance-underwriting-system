"""
Form components for the Streamlit underwriting application.

This module provides reusable form components for collecting and validating
application data in the web interface.
"""

import streamlit as st
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional
import uuid
from decimal import Decimal

from underwriting.core.models import (
    Application, Driver, Vehicle, Violation, Claim,
    Gender, MaritalStatus, LicenseStatus, ViolationType, ViolationSeverity,
    ClaimType, VehicleCategory
)

def create_driver_form(key_prefix: str = "driver") -> Optional[Driver]:
    """Create a form for driver information."""
    
    st.markdown("### 👤 Driver Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        first_name = st.text_input(
            "First Name",
            key=f"{key_prefix}_first_name",
            help="Driver's first name"
        )
        
        last_name = st.text_input(
            "Last Name", 
            key=f"{key_prefix}_last_name",
            help="Driver's last name"
        )
        
        age = st.number_input(
            "Age",
            min_value=16,
            max_value=100,
            value=30,
            key=f"{key_prefix}_age",
            help="Driver's age"
        )
        
        gender = st.selectbox(
            "Gender",
            options=[g.value for g in Gender],
            key=f"{key_prefix}_gender",
            help="Driver's gender"
        )
        
        marital_status = st.selectbox(
            "Marital Status",
            options=[ms.value for ms in MaritalStatus],
            key=f"{key_prefix}_marital_status",
            help="Driver's marital status"
        )
    
    with col2:
        date_of_birth = st.date_input(
            "Date of Birth",
            value=date.today() - timedelta(days=age*365),
            max_value=date.today() - timedelta(days=16*365),
            key=f"{key_prefix}_dob",
            help="Driver's date of birth"
        )
        
        license_number = st.text_input(
            "License Number",
            key=f"{key_prefix}_license_number",
            help="Driver's license number"
        )
        
        license_state = st.text_input(
            "License State",
            value="CA",
            max_chars=2,
            key=f"{key_prefix}_license_state",
            help="State that issued the license"
        )
        
        license_status = st.selectbox(
            "License Status",
            options=[ls.value for ls in LicenseStatus],
            key=f"{key_prefix}_license_status",
            help="Current license status"
        )
        
        years_licensed = st.number_input(
            "Years Licensed",
            min_value=0,
            max_value=age - 16,
            value=min(10, age - 16),
            key=f"{key_prefix}_years_licensed",
            help="Years of driving experience"
        )
    
    # Validation
    if not first_name or not last_name:
        if st.session_state.get(f"{key_prefix}_submit", False):
            st.error("First name and last name are required")
        return None
    
    if not license_number:
        if st.session_state.get(f"{key_prefix}_submit", False):
            st.error("License number is required")
        return None
    
    try:
        driver = Driver(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            age=age,
            gender=Gender(gender),
            marital_status=MaritalStatus(marital_status),
            license_number=license_number,
            license_state=license_state,
            license_status=LicenseStatus(license_status),
            years_licensed=years_licensed,
            violations=[],  # Will be added separately
            claims=[]       # Will be added separately
        )
        return driver
    except Exception as e:
        st.error(f"Error creating driver: {str(e)}")
        return None

def create_vehicle_form(key_prefix: str = "vehicle") -> Optional[Vehicle]:
    """Create a form for vehicle information."""
    
    st.markdown("### 🚗 Vehicle Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        year = st.number_input(
            "Year",
            min_value=1990,
            max_value=datetime.now().year + 1,
            value=2020,
            key=f"{key_prefix}_year",
            help="Vehicle year"
        )
        
        make = st.text_input(
            "Make",
            key=f"{key_prefix}_make",
            placeholder="e.g., Toyota",
            help="Vehicle manufacturer"
        )
        
        model = st.text_input(
            "Model",
            key=f"{key_prefix}_model",
            placeholder="e.g., Camry",
            help="Vehicle model"
        )
        
        vin = st.text_input(
            "VIN",
            key=f"{key_prefix}_vin",
            max_chars=17,
            placeholder="17-character VIN",
            help="Vehicle identification number"
        )
        
        category = st.selectbox(
            "Category",
            options=[vc.value for vc in VehicleCategory],
            key=f"{key_prefix}_category",
            help="Vehicle category"
        )
    
    with col2:
        value = st.number_input(
            "Vehicle Value ($)",
            min_value=1000,
            max_value=500000,
            value=25000,
            step=1000,
            key=f"{key_prefix}_value",
            help="Current market value of the vehicle"
        )
        
        usage = st.selectbox(
            "Usage",
            options=["personal", "business", "commercial"],
            key=f"{key_prefix}_usage",
            help="Primary use of the vehicle"
        )
        
        annual_mileage = st.number_input(
            "Annual Mileage",
            min_value=1000,
            max_value=100000,
            value=12000,
            step=1000,
            key=f"{key_prefix}_annual_mileage",
            help="Estimated annual mileage"
        )
        
        anti_theft_device = st.checkbox(
            "Anti-theft Device",
            key=f"{key_prefix}_anti_theft",
            help="Vehicle has anti-theft device installed"
        )
        
        safety_rating = st.slider(
            "Safety Rating",
            min_value=1,
            max_value=5,
            value=3,
            key=f"{key_prefix}_safety_rating",
            help="NHTSA safety rating (1-5 stars)"
        )
    
    # Validation
    if not make or not model:
        if st.session_state.get(f"{key_prefix}_submit", False):
            st.error("Make and model are required")
        return None
    
    if not vin or len(vin) != 17:
        if st.session_state.get(f"{key_prefix}_submit", False):
            st.error("Valid 17-character VIN is required")
        return None
    
    try:
        vehicle = Vehicle(
            year=year,
            make=make,
            model=model,
            vin=vin,
            category=VehicleCategory(category),
            value=Decimal(str(value)),
            usage=usage,
            annual_mileage=annual_mileage,
            anti_theft_device=anti_theft_device,
            safety_rating=safety_rating
        )
        return vehicle
    except Exception as e:
        st.error(f"Error creating vehicle: {str(e)}")
        return None

def create_violations_form(key_prefix: str = "violations") -> list[Violation]:
    """Create a form for traffic violations."""
    
    st.markdown("### 🚨 Traffic Violations")
    
    violations = []
    
    # Number of violations
    num_violations = st.number_input(
        "Number of Violations",
        min_value=0,
        max_value=10,
        value=0,
        key=f"{key_prefix}_count",
        help="Total number of traffic violations"
    )
    
    for i in range(num_violations):
        st.markdown(f"#### Violation {i + 1}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            violation_type = st.selectbox(
                "Type",
                options=[vt.value for vt in ViolationType],
                key=f"{key_prefix}_{i}_type",
                help="Type of violation"
            )
            
            severity = st.selectbox(
                "Severity",
                options=[vs.value for vs in ViolationSeverity],
                key=f"{key_prefix}_{i}_severity",
                help="Severity of violation"
            )
        
        with col2:
            violation_date = st.date_input(
                "Violation Date",
                value=date.today() - timedelta(days=365),
                max_value=date.today(),
                key=f"{key_prefix}_{i}_date",
                help="Date of violation"
            )
            
            conviction_date = st.date_input(
                "Conviction Date",
                value=violation_date + timedelta(days=30),
                min_value=violation_date,
                max_value=date.today(),
                key=f"{key_prefix}_{i}_conviction_date",
                help="Date of conviction"
            )
        
        with col3:
            description = st.text_area(
                "Description",
                key=f"{key_prefix}_{i}_description",
                placeholder="Brief description of the violation",
                help="Detailed description"
            )
            
            fine_amount = st.number_input(
                "Fine Amount ($)",
                min_value=0,
                value=150,
                key=f"{key_prefix}_{i}_fine",
                help="Fine amount in dollars"
            )
        
        try:
            violation = Violation(
                violation_type=ViolationType(violation_type),
                violation_date=violation_date,
                description=description or f"{violation_type.replace('_', ' ').title()} violation",
                severity=ViolationSeverity(severity),
                fine_amount=Decimal(str(fine_amount)),
                conviction_date=conviction_date
            )
            violations.append(violation)
        except Exception as e:
            st.error(f"Error creating violation {i + 1}: {str(e)}")
    
    return violations

def create_claims_form(key_prefix: str = "claims") -> list[Claim]:
    """Create a form for insurance claims."""
    
    st.markdown("### 💰 Insurance Claims")
    
    claims = []
    
    # Number of claims
    num_claims = st.number_input(
        "Number of Claims",
        min_value=0,
        max_value=10,
        value=0,
        key=f"{key_prefix}_count",
        help="Total number of insurance claims"
    )
    
    for i in range(num_claims):
        st.markdown(f"#### Claim {i + 1}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            claim_type = st.selectbox(
                "Claim Type",
                options=[ct.value for ct in ClaimType],
                key=f"{key_prefix}_{i}_type",
                help="Type of insurance claim"
            )
            
            claim_date = st.date_input(
                "Claim Date",
                value=date.today() - timedelta(days=365),
                max_value=date.today(),
                key=f"{key_prefix}_{i}_date",
                help="Date of claim"
            )
            
            amount = st.number_input(
                "Claim Amount ($)",
                min_value=0,
                value=5000,
                step=100,
                key=f"{key_prefix}_{i}_amount",
                help="Total claim amount"
            )
        
        with col2:
            at_fault = st.checkbox(
                "At Fault",
                key=f"{key_prefix}_{i}_at_fault",
                help="Driver was at fault for this claim"
            )
            
            description = st.text_area(
                "Description",
                key=f"{key_prefix}_{i}_description",
                placeholder="Brief description of the claim",
                help="Detailed description of the claim"
            )
        
        try:
            claim = Claim(
                claim_type=ClaimType(claim_type),
                claim_date=claim_date,
                amount=Decimal(str(amount)),
                at_fault=at_fault,
                description=description or f"{claim_type.replace('_', ' ').title()} claim"
            )
            claims.append(claim)
        except Exception as e:
            st.error(f"Error creating claim {i + 1}: {str(e)}")
    
    return claims

def create_application_metadata_form(key_prefix: str = "metadata") -> Dict[str, Any]:
    """Create a form for application metadata."""
    
    st.markdown("### 📋 Application Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        credit_score = st.number_input(
            "Credit Score",
            min_value=300,
            max_value=850,
            value=700,
            key=f"{key_prefix}_credit_score",
            help="Applicant's credit score"
        )
        
        has_previous_insurance = st.checkbox(
            "Had Previous Insurance",
            value=True,
            key=f"{key_prefix}_has_previous_insurance",
            help="Applicant had previous insurance coverage"
        )
        
        previous_carrier = None
        if has_previous_insurance:
            previous_carrier = st.text_input(
                "Previous Insurance Carrier",
                value="State Farm",
                key=f"{key_prefix}_previous_carrier",
                help="Name of previous insurance company"
            )
        
        coverage_lapse_days = st.number_input(
            "Coverage Lapse (Days)",
            min_value=0,
            max_value=365,
            value=0,
            key=f"{key_prefix}_coverage_lapse_days",
            help="Number of days without insurance coverage in the past year"
        )
    
    with col2:
        payment_method = st.selectbox(
            "Payment Method",
            options=["monthly", "quarterly", "semi_annual", "annual"],
            key=f"{key_prefix}_payment_method",
            help="Preferred payment frequency"
        )
        
        requested_coverage = st.selectbox(
            "Requested Coverage",
            options=["liability", "full_coverage", "comprehensive"],
            key=f"{key_prefix}_coverage",
            help="Type of coverage requested"
        )
        
        agent_id = st.text_input(
            "Agent ID",
            value="AGT-001",
            key=f"{key_prefix}_agent_id",
            help="Insurance agent identifier"
        )
    
    return {
        "credit_score": credit_score,
        "previous_carrier": previous_carrier,
        "coverage_lapse": coverage_lapse_days,
        "payment_method": payment_method,
        "requested_coverage": requested_coverage,
        "agent_id": agent_id
    }

def validate_application_form(driver: Optional[Driver], vehicle: Optional[Vehicle]) -> bool:
    """Validate the complete application form."""
    
    if not driver:
        st.error("❌ Driver information is required and must be valid")
        return False
    
    if not vehicle:
        st.error("❌ Vehicle information is required and must be valid")
        return False
    
    # Additional validation rules
    if driver.age < 18:
        st.error("❌ Driver must be at least 18 years old")
        return False
    
    if vehicle.year < 1990:
        st.error("❌ Vehicle must be 1990 or newer")
        return False
    
    return True

def create_complete_application(
    driver: Driver,
    vehicle: Vehicle, 
    violations: list[Violation],
    claims: list[Claim],
    metadata: Dict[str, Any]
) -> Application:
    """Create a complete application from form data."""
    
    # Update driver with violations and claims
    driver.violations = violations
    driver.claims = claims
    
    # Create application
    application = Application(
        applicant=driver,
        vehicles=[vehicle],
        credit_score=metadata["credit_score"],
        coverage_lapse_days=metadata["coverage_lapse"],
        previous_carrier=metadata["previous_carrier"]
    )
    
    return application