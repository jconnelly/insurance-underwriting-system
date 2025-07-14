"""
Base prompt template system for AI underwriting services.

This module provides the foundation for creating and managing prompts
across different rule sets and AI providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ...core.models import Application, Driver, Vehicle, Violation, Claim


class BasePromptTemplate(ABC):
    """Abstract base class for prompt templates."""
    
    def __init__(self, rule_set: str):
        """Initialize prompt template for specific rule set.
        
        Args:
            rule_set: Rule set name (conservative, standard, liberal)
        """
        self.rule_set = rule_set
        self.system_prompt = self._build_system_prompt()
    
    @abstractmethod
    def _build_system_prompt(self) -> str:
        """Build the system prompt for this rule set."""
        pass
    
    @abstractmethod
    def get_evaluation_prompt(self, application: Application, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate evaluation prompt for an application.
        
        Args:
            application: Insurance application to evaluate
            context: Additional context information
            
        Returns:
            Formatted prompt string
        """
        pass
    
    def format_application_data(self, application: Application) -> str:
        """Format application data for inclusion in prompts.
        
        Args:
            application: Application to format
            
        Returns:
            Formatted application string
        """
        data = {
            "application_id": application.id,
            "applicant": self._format_driver(application.applicant),
            "additional_drivers": [self._format_driver(d) for d in application.additional_drivers],
            "vehicles": [self._format_vehicle(v) for v in application.vehicles],
            "coverage_details": {
                "coverage_lapse_days": application.coverage_lapse_days,
                "credit_score": application.credit_score,
                "fraud_conviction": application.fraud_conviction
            }
        }
        
        return json.dumps(data, indent=2, default=str)
    
    def _format_driver(self, driver: Driver) -> Dict[str, Any]:
        """Format driver information."""
        return {
            "age": driver.age,
            "gender": driver.gender.value,
            "marital_status": driver.marital_status.value,
            "license_status": driver.license_status.value,
            "years_licensed": driver.years_licensed,
            "violations": [self._format_violation(v) for v in driver.violations],
            "claims": [self._format_claim(c) for c in driver.claims]
        }
    
    def _format_vehicle(self, vehicle: Vehicle) -> Dict[str, Any]:
        """Format vehicle information."""
        return {
            "year": vehicle.year,
            "make": vehicle.make,
            "model": vehicle.model,
            "category": vehicle.category.value,
            "value": vehicle.value,
            "safety_rating": vehicle.safety_rating
        }
    
    def _format_violation(self, violation: Violation) -> Dict[str, Any]:
        """Format violation information."""
        return {
            "type": violation.violation_type.value,
            "date": violation.violation_date.isoformat(),
            "conviction_date": violation.conviction_date.isoformat() if violation.conviction_date else None,
            "fine_amount": violation.fine_amount
        }
    
    def _format_claim(self, claim: Claim) -> Dict[str, Any]:
        """Format claim information."""
        return {
            "type": claim.claim_type.value,
            "date": claim.claim_date.isoformat(),
            "amount": claim.amount,
            "at_fault": claim.at_fault,
            "description": claim.description
        }
    
    def get_common_instructions(self) -> str:
        """Get common instructions for all prompts."""
        return """
RESPONSE FORMAT REQUIREMENTS:
You must respond with a valid JSON object containing the following structure:

{
  "decision": "ACCEPT" | "DENY" | "ADJUDICATE",
  "confidence_level": "HIGH" | "MEDIUM" | "LOW",
  "reasoning": "Detailed explanation of your decision",
  "risk_assessment": {
    "overall_risk_score": <integer 0-1000>,
    "risk_level": "LOW" | "MEDIUM" | "HIGH" | "VERY_HIGH",
    "key_risk_factors": ["factor1", "factor2", ...],
    "risk_mitigation_suggestions": ["suggestion1", "suggestion2", ...],
    "confidence_score": <float 0.0-1.0>
  },
  "alternative_considerations": ["consideration1", "consideration2", ...],
  "recommended_premium_adjustment": <float percentage, can be null>
}

DECISION CRITERIA:
- ACCEPT: Low risk applicant meeting acceptance criteria
- DENY: High risk applicant failing hard stop criteria  
- ADJUDICATE: Moderate risk requiring manual review

RISK SCORING:
- 0-250: Low Risk
- 251-500: Medium Risk
- 501-750: High Risk
- 751-1000: Very High Risk

Be thorough but concise in your analysis.
"""


class PromptManager:
    """Manages prompt templates for different rule sets."""
    
    def __init__(self):
        """Initialize prompt manager."""
        self._templates: Dict[str, BasePromptTemplate] = {}
    
    def register_template(self, rule_set: str, template: BasePromptTemplate):
        """Register a prompt template for a rule set.
        
        Args:
            rule_set: Rule set name
            template: Prompt template instance
        """
        self._templates[rule_set] = template
    
    def get_template(self, rule_set: str) -> BasePromptTemplate:
        """Get prompt template for a rule set.
        
        Args:
            rule_set: Rule set name
            
        Returns:
            Prompt template instance
            
        Raises:
            ValueError: If rule set not found
        """
        if rule_set not in self._templates:
            raise ValueError(f"No prompt template found for rule set: {rule_set}")
        
        return self._templates[rule_set]
    
    def get_available_rule_sets(self) -> List[str]:
        """Get list of available rule sets.
        
        Returns:
            List of rule set names
        """
        return list(self._templates.keys())
    
    def generate_prompt(
        self, 
        rule_set: str, 
        application: Application, 
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """Generate system and user prompts for an application.
        
        Args:
            rule_set: Rule set to use
            application: Application to evaluate
            context: Additional context
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        template = self.get_template(rule_set)
        system_prompt = template.system_prompt
        user_prompt = template.get_evaluation_prompt(application, context)
        
        return system_prompt, user_prompt