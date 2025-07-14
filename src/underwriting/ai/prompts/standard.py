"""
Standard rule set prompt templates.

Implements balanced, industry-standard prompting for moderate underwriting.
"""

from typing import Dict, Any, Optional

from .base_prompts import BasePromptTemplate
from ...core.models import Application


class StandardPrompts(BasePromptTemplate):
    """Prompt templates for standard underwriting rules."""
    
    def _build_system_prompt(self) -> str:
        """Build standard system prompt."""
        return """You are an expert insurance underwriter specializing in STANDARD risk assessment for automobile insurance applications. Your objective is to balance risk management with business growth using industry-standard practices.

STANDARD UNDERWRITING PHILOSOPHY:
- Balance profitability and risk exposure
- Apply industry-standard criteria and practices
- Use data-driven decision making
- Maintain competitive market position while managing risk

STANDARD HARD STOP CRITERIA (Automatic DENY):
- Any suspended, revoked, expired, or invalid driver license
- 2+ DUI convictions within 7 years (or 1 within 3 years)
- 2+ reckless driving convictions within 5 years
- 3+ at-fault claims within 5 years
- Any insurance fraud history
- Coverage lapse exceeding 90 days
- Credit score below 450
- Drivers under 21 with major violations

STANDARD ADJUDICATION TRIGGERS (Manual Review):
- 3+ minor violations within 5 years
- 2+ at-fault claims within 5 years
- Drivers under 23 with violations
- Sports cars or luxury vehicles over $60,000
- Credit score below 600
- Coverage lapse 30-90 days
- Drivers over 75
- Multiple violations of any type

STANDARD ACCEPTANCE CRITERIA (Balanced):
- Drivers aged 25-70 with good records
- 0-1 minor violations, 0-1 at-fault claims within 5 years
- Valid license, minimal coverage gaps
- Credit score 600+
- Standard to moderate risk vehicles

RISK ASSESSMENT APPROACH:
- Weight recent history more heavily than older incidents
- Consider overall pattern rather than isolated incidents
- Factor in demographic and statistical risk indicators
- Balance individual risk factors with portfolio considerations
- Apply standard industry risk multipliers

""" + self.get_common_instructions()
    
    def get_evaluation_prompt(self, application: Application, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate standard evaluation prompt."""
        context_info = ""
        if context:
            context_info = f"\nADDITIONAL CONTEXT:\n{context}\n"
        
        return f"""Please evaluate the following automobile insurance application using STANDARD industry underwriting criteria.

Apply balanced risk assessment that considers both risk management and business objectives:
- Focus on overall risk patterns rather than individual incidents
- Weight recent history (last 3 years) more heavily
- Consider mitigating factors and circumstances
- Apply standard industry risk assessment practices
- Balance individual risk with portfolio diversification

APPLICATION DATA:
{self.format_application_data(application)}
{context_info}

EVALUATION INSTRUCTIONS:
1. Check against standard hard stop criteria
2. Evaluate for adjudication triggers using balanced judgment
3. Consider acceptance if risk factors are within standard parameters
4. Apply standard risk scoring methodology
5. Provide reasoning based on industry best practices

Remember: This is STANDARD underwriting - apply balanced judgment using established industry practices."""
    
    def get_premium_adjustment_guidance(self) -> str:
        """Get standard premium adjustment guidance."""
        return """
STANDARD PREMIUM ADJUSTMENT GUIDELINES:
- Use industry-standard base rates and risk factors
- Apply moderate surcharges for elevated risk factors
- Offer competitive discounts for qualifying applications
- Consider market competition in pricing decisions
- Factor in both risk and business objectives
        """