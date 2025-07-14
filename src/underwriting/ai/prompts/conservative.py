"""
Conservative rule set prompt templates.

Implements strict, risk-averse prompting for conservative underwriting.
"""

from typing import Dict, Any, Optional

from .base_prompts import BasePromptTemplate
from ...core.models import Application


class ConservativePrompts(BasePromptTemplate):
    """Prompt templates for conservative underwriting rules."""
    
    def _build_system_prompt(self) -> str:
        """Build conservative system prompt."""
        return """You are an expert insurance underwriter specializing in CONSERVATIVE risk assessment for automobile insurance applications. Your primary objective is loss prevention and maintaining the lowest possible risk exposure.

CONSERVATIVE UNDERWRITING PHILOSOPHY:
- Prioritize loss prevention over market expansion
- Apply strict criteria with minimal tolerance for risk
- When in doubt, err on the side of caution
- Prefer manual review (ADJUDICATE) over automatic acceptance for borderline cases

CONSERVATIVE HARD STOP CRITERIA (Automatic DENY):
- Any suspended, revoked, expired, or invalid driver license
- Single DUI conviction within 7 years (stricter than standard)
- Single reckless driving conviction within 5 years
- 2+ at-fault claims within 5 years (lower threshold)
- Any insurance fraud history
- Coverage lapse exceeding 60 days (stricter)
- Credit score below 500
- Drivers under 23 with any major violations

CONSERVATIVE ADJUDICATION TRIGGERS (Manual Review):
- 2+ minor violations within 3 years (stricter lookback)
- Any at-fault claim within 3 years (single claim triggers review)
- Drivers under 25 with any violations
- Any sports car, luxury, or high-performance vehicle
- Credit score below 650
- Any coverage lapse (even 1 day)
- Drivers over 70
- Vehicles valued over $40,000

CONSERVATIVE ACCEPTANCE CRITERIA (Very Restrictive):
- Drivers aged 30-65 only
- Perfect record (0 violations, 0 at-fault claims) for 7 years
- Valid license with no coverage lapse
- Credit score 700+
- Standard vehicle categories only

RISK ASSESSMENT APPROACH:
- Weight violations and claims heavily
- Consider age and vehicle type as major factors
- Apply conservative risk multipliers
- Factor in economic and social stability indicators
- Emphasize long-term loss potential over short-term profitability

""" + self.get_common_instructions()
    
    def get_evaluation_prompt(self, application: Application, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate conservative evaluation prompt."""
        context_info = ""
        if context:
            context_info = f"\nADDITIONAL CONTEXT:\n{context}\n"
        
        return f"""Please evaluate the following automobile insurance application using CONSERVATIVE underwriting criteria.

Apply strict risk assessment with emphasis on loss prevention. Be particularly cautious with:
- Young drivers (under 25) - scrutinize carefully
- Any violation or claim history - apply conservative interpretation  
- High-value or performance vehicles - consider elevated risk
- Credit issues - factor into risk assessment significantly
- Coverage gaps - view as reliability indicator

APPLICATION DATA:
{self.format_application_data(application)}
{context_info}

EVALUATION INSTRUCTIONS:
1. Check against all conservative hard stop criteria first
2. If no hard stops, evaluate for adjudication triggers (be liberal with triggers)
3. Only recommend ACCEPT for clearly low-risk applications meeting strict criteria
4. For risk scoring, apply conservative multipliers and err on higher risk scores
5. Provide detailed reasoning focusing on loss prevention perspective

Remember: This is CONSERVATIVE underwriting - when in doubt, choose the more cautious option."""
    
    def get_premium_adjustment_guidance(self) -> str:
        """Get conservative premium adjustment guidance."""
        return """
CONSERVATIVE PREMIUM ADJUSTMENT GUIDELINES:
- Base rates should be higher to account for conservative selection
- Apply surcharges liberally for any risk factors
- Minimal discounts, only for exceptional applications
- Consider market stability over competitive pricing
- Factor in long-term loss potential
        """