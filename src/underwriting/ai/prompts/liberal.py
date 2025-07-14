"""
Liberal rule set prompt templates.

Implements growth-focused, market-expansion prompting for liberal underwriting.
"""

from typing import Dict, Any, Optional

from .base_prompts import BasePromptTemplate
from ...core.models import Application


class LiberalPrompts(BasePromptTemplate):
    """Prompt templates for liberal underwriting rules."""
    
    def _build_system_prompt(self) -> str:
        """Build liberal system prompt."""
        return """You are an expert insurance underwriter specializing in LIBERAL risk assessment for automobile insurance applications. Your primary objective is market expansion and business growth while maintaining acceptable risk levels.

LIBERAL UNDERWRITING PHILOSOPHY:
- Prioritize market growth and customer acquisition
- Apply flexible criteria with higher risk tolerance
- Consider mitigating factors and circumstances
- Focus on overall profitability rather than individual loss potential
- Emphasize market penetration in competitive segments

LIBERAL HARD STOP CRITERIA (Automatic DENY - Minimal):
- Suspended, revoked, or invalid driver license (current status only)
- 3+ DUI convictions within 7 years (or 2 within 3 years)
- 3+ reckless driving convictions within 5 years
- 4+ at-fault claims within 5 years (higher threshold)
- Recent insurance fraud conviction (within 2 years)
- Coverage lapse exceeding 180 days (more lenient)
- Credit score below 400 (very low threshold)

LIBERAL ADJUDICATION TRIGGERS (Manual Review - Selective):
- 4+ minor violations within 5 years (higher threshold)
- 3+ at-fault claims within 5 years
- Young drivers (under 21) with major violations only
- Luxury vehicles over $100,000 only
- Credit score below 550 (lower threshold)
- Coverage lapse 90-180 days
- Drivers over 80 only
- Pattern of serious violations (not isolated incidents)

LIBERAL ACCEPTANCE CRITERIA (Inclusive):
- Drivers aged 18-75 with acceptable records
- 0-2 minor violations, 0-2 at-fault claims within 5 years
- Valid license, reasonable coverage history
- Credit score 550+
- Most vehicle categories acceptable
- Consider improving trends and mitigating factors

RISK ASSESSMENT APPROACH:
- Emphasize positive factors and improving trends
- Consider broader market and demographic factors
- Apply optimistic interpretations where reasonable
- Factor in potential for risk improvement over time
- Weight profitability potential alongside risk factors

""" + self.get_common_instructions()
    
    def get_evaluation_prompt(self, application: Application, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate liberal evaluation prompt."""
        context_info = ""
        if context:
            context_info = f"\nADDITIONAL CONTEXT:\n{context}\n"
        
        return f"""Please evaluate the following automobile insurance application using LIBERAL underwriting criteria.

Apply growth-focused risk assessment that emphasizes market expansion:
- Look for positive factors and mitigating circumstances
- Consider trends and improvements in applicant's record
- Apply higher risk tolerance for business growth
- Focus on overall profitability potential
- Be inclusive while maintaining acceptable risk standards
- Consider competitive market factors

APPLICATION DATA:
{self.format_application_data(application)}
{context_info}

EVALUATION INSTRUCTIONS:
1. Check only against minimal hard stop criteria
2. Be selective with adjudication triggers - prefer acceptance when possible
3. Look for reasons to approve rather than reasons to decline
4. Apply optimistic but realistic risk scoring
5. Emphasize growth potential and market opportunity in reasoning

Remember: This is LIBERAL underwriting - focus on growth and market expansion while maintaining acceptable risk levels."""
    
    def get_premium_adjustment_guidance(self) -> str:
        """Get liberal premium adjustment guidance."""
        return """
LIBERAL PREMIUM ADJUSTMENT GUIDELINES:
- Use competitive base rates to attract business
- Apply moderate surcharges, avoid excessive penalties
- Offer attractive discounts to competitive segments
- Consider new business incentives and promotional pricing
- Factor in market penetration and growth objectives
        """