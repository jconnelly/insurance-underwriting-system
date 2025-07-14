"""
AI response parser and validator for underwriting decisions.

This module handles parsing and validating AI responses to ensure they conform
to expected formats and contain valid underwriting decisions.
"""

import json
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from loguru import logger
from pydantic import ValidationError

from .base import (
    AIUnderwritingDecision, 
    AIRiskAssessment, 
    AIConfidenceLevel, 
    AIProviderType,
    AIInvalidResponseError
)
from ..core.models import DecisionType


class AIResponseParser:
    """Parses and validates AI responses for underwriting decisions."""
    
    def __init__(self, provider_type: AIProviderType, model_version: str):
        """Initialize response parser.
        
        Args:
            provider_type: AI provider type
            model_version: Model version used
        """
        self.provider_type = provider_type
        self.model_version = model_version
    
    def parse_decision(self, raw_response: str, application_id: str) -> AIUnderwritingDecision:
        """Parse AI response into structured decision object.
        
        Args:
            raw_response: Raw AI response text
            application_id: Application ID being evaluated
            
        Returns:
            Parsed and validated AIUnderwritingDecision
            
        Raises:
            AIInvalidResponseError: If response cannot be parsed or is invalid
        """
        try:
            # Extract JSON from response
            json_data = self._extract_json(raw_response)
            
            # Validate required fields
            self._validate_response_structure(json_data)
            
            # Parse and validate individual components
            decision = self._parse_decision_type(json_data.get("decision"))
            confidence_level = self._parse_confidence_level(json_data.get("confidence_level"))
            risk_assessment = self._parse_risk_assessment(json_data.get("risk_assessment", {}))
            
            # Build decision object
            ai_decision = AIUnderwritingDecision(
                application_id=application_id,
                decision=decision,
                reasoning=json_data.get("reasoning", ""),
                confidence_level=confidence_level,
                risk_assessment=risk_assessment,
                alternative_considerations=json_data.get("alternative_considerations", []),
                recommended_premium_adjustment=json_data.get("recommended_premium_adjustment"),
                decision_timestamp=datetime.now(),
                model_version=self.model_version,
                provider=self.provider_type
            )
            
            # Final validation
            self._validate_decision_consistency(ai_decision)
            
            logger.info(f"Successfully parsed AI decision for application {application_id}")
            return ai_decision
            
        except Exception as e:
            logger.error(f"Failed to parse AI response for application {application_id}: {e}")
            raise AIInvalidResponseError(
                f"Unable to parse AI response: {str(e)}", 
                self.provider_type,
                "PARSE_ERROR"
            )
    
    def _extract_json(self, raw_response: str) -> Dict[str, Any]:
        """Extract JSON object from raw response text."""
        # Try to find JSON in the response
        json_patterns = [
            r'```json\n(.*?)\n```',  # Markdown code block
            r'```\n(.*?)\n```',      # Generic code block
            r'\{.*\}',               # Direct JSON object
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, raw_response, re.DOTALL)
            if matches:
                try:
                    return json.loads(matches[0])
                except json.JSONDecodeError:
                    continue
        
        # Try parsing the entire response as JSON
        try:
            return json.loads(raw_response.strip())
        except json.JSONDecodeError:
            pass
        
        # Last resort: look for key-value pairs
        return self._extract_key_value_pairs(raw_response)
    
    def _extract_key_value_pairs(self, text: str) -> Dict[str, Any]:
        """Extract key-value pairs from unstructured text as fallback."""
        result = {}
        
        # Common patterns for key-value extraction
        patterns = {
            'decision': r'decision[:\s]+([A-Z]+)',
            'confidence_level': r'confidence[_\s]*level[:\s]+([A-Z]+)',
            'reasoning': r'reasoning[:\s]+(.*?)(?=\n[A-Z]|\n\n|$)',
            'overall_risk_score': r'(?:overall[_\s]*)?risk[_\s]*score[:\s]+(\d+)',
            'risk_level': r'risk[_\s]*level[:\s]+([A-Z_]+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                if key in ['overall_risk_score']:
                    try:
                        result[key] = int(value)
                    except ValueError:
                        pass
                else:
                    result[key] = value
        
        # Basic structure for minimum viable response
        if 'decision' in result:
            if 'risk_assessment' not in result:
                result['risk_assessment'] = {
                    'overall_risk_score': result.get('overall_risk_score', 500),
                    'risk_level': result.get('risk_level', 'MEDIUM'),
                    'key_risk_factors': [],
                    'risk_mitigation_suggestions': [],
                    'confidence_score': 0.5
                }
        
        return result
    
    def _validate_response_structure(self, data: Dict[str, Any]) -> None:
        """Validate basic response structure."""
        required_fields = ['decision', 'reasoning', 'risk_assessment']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(data['risk_assessment'], dict):
            raise ValueError("risk_assessment must be a dictionary")
    
    def _parse_decision_type(self, decision_str: str) -> DecisionType:
        """Parse decision string to DecisionType enum."""
        if not decision_str:
            raise ValueError("Decision field is required")
        
        decision_mapping = {
            'ACCEPT': DecisionType.ACCEPT,
            'DENY': DecisionType.DENY,
            'ADJUDICATE': DecisionType.ADJUDICATE,
            'APPROVE': DecisionType.ACCEPT,  # Alternative wording
            'DECLINE': DecisionType.DENY,    # Alternative wording
            'REVIEW': DecisionType.ADJUDICATE,  # Alternative wording
        }
        
        decision_upper = decision_str.upper().strip()
        if decision_upper not in decision_mapping:
            raise ValueError(f"Invalid decision: {decision_str}")
        
        return decision_mapping[decision_upper]
    
    def _parse_confidence_level(self, confidence_str: str) -> AIConfidenceLevel:
        """Parse confidence level string to enum."""
        if not confidence_str:
            return AIConfidenceLevel.MEDIUM  # Default
        
        confidence_mapping = {
            'HIGH': AIConfidenceLevel.HIGH,
            'MEDIUM': AIConfidenceLevel.MEDIUM,
            'LOW': AIConfidenceLevel.LOW,
        }
        
        confidence_upper = confidence_str.upper().strip()
        return confidence_mapping.get(confidence_upper, AIConfidenceLevel.MEDIUM)
    
    def _parse_risk_assessment(self, risk_data: Dict[str, Any]) -> AIRiskAssessment:
        """Parse risk assessment data."""
        try:
            # Set defaults for missing fields
            risk_data.setdefault('overall_risk_score', 500)
            risk_data.setdefault('risk_level', 'MEDIUM')
            risk_data.setdefault('key_risk_factors', [])
            risk_data.setdefault('risk_mitigation_suggestions', [])
            risk_data.setdefault('confidence_score', 0.5)
            
            # Validate and clean risk score
            risk_score = risk_data['overall_risk_score']
            if isinstance(risk_score, str):
                risk_score = int(re.findall(r'\d+', risk_score)[0])
            risk_data['overall_risk_score'] = max(0, min(1000, int(risk_score)))
            
            # Validate and clean confidence score
            confidence = risk_data['confidence_score']
            if isinstance(confidence, str):
                confidence = float(re.findall(r'[\d.]+', confidence)[0])
            risk_data['confidence_score'] = max(0.0, min(1.0, float(confidence)))
            
            # Ensure lists are actually lists
            for list_field in ['key_risk_factors', 'risk_mitigation_suggestions']:
                if not isinstance(risk_data[list_field], list):
                    risk_data[list_field] = []
            
            return AIRiskAssessment(**risk_data)
            
        except (ValueError, KeyError, IndexError) as e:
            logger.warning(f"Error parsing risk assessment, using defaults: {e}")
            return AIRiskAssessment(
                overall_risk_score=500,
                risk_level="MEDIUM",
                key_risk_factors=[],
                risk_mitigation_suggestions=[],
                confidence_score=0.5
            )
    
    def _validate_decision_consistency(self, decision: AIUnderwritingDecision) -> None:
        """Validate consistency between decision components."""
        # Check risk score vs decision consistency
        risk_score = decision.risk_assessment.overall_risk_score
        
        if decision.decision == DecisionType.ACCEPT and risk_score > 600:
            logger.warning(f"Inconsistent: ACCEPT decision with high risk score {risk_score}")
        
        if decision.decision == DecisionType.DENY and risk_score < 400:
            logger.warning(f"Inconsistent: DENY decision with low risk score {risk_score}")
        
        # Check reasoning length
        if len(decision.reasoning) < 10:
            logger.warning("Decision reasoning is very short")
    
    def extract_decision_summary(self, decision: AIUnderwritingDecision) -> Dict[str, Any]:
        """Extract summary information from decision for logging/reporting.
        
        Args:
            decision: AI underwriting decision
            
        Returns:
            Summary dictionary
        """
        return {
            "application_id": decision.application_id,
            "decision": decision.decision.value,
            "confidence": decision.confidence_level.value,
            "risk_score": decision.risk_assessment.overall_risk_score,
            "risk_level": decision.risk_assessment.risk_level,
            "key_factors_count": len(decision.risk_assessment.key_risk_factors),
            "reasoning_length": len(decision.reasoning),
            "premium_adjustment": decision.recommended_premium_adjustment,
            "model_version": decision.model_version,
            "provider": decision.provider.value
        }
    
    def validate_batch_responses(
        self, 
        responses: List[str], 
        application_ids: List[str]
    ) -> Tuple[List[AIUnderwritingDecision], List[Tuple[str, str]]]:
        """Validate a batch of AI responses.
        
        Args:
            responses: List of AI response strings
            application_ids: Corresponding application IDs
            
        Returns:
            Tuple of (successful_decisions, failed_responses)
        """
        successful_decisions = []
        failed_responses = []
        
        for response, app_id in zip(responses, application_ids):
            try:
                decision = self.parse_decision(response, app_id)
                successful_decisions.append(decision)
            except Exception as e:
                failed_responses.append((app_id, str(e)))
                logger.error(f"Failed to parse response for {app_id}: {e}")
        
        success_rate = len(successful_decisions) / len(responses) if responses else 0
        logger.info(f"Batch parsing success rate: {success_rate:.2%}")
        
        return successful_decisions, failed_responses