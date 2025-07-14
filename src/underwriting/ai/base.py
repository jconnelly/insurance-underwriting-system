"""
Abstract base interface for AI underwriting services.

This module defines the interface that all AI service providers must implement,
ensuring consistent behavior across different AI backends.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field

from ..core.models import Application, DecisionType


class AIProviderType(Enum):
    """Supported AI provider types."""
    OPENAI = "openai"
    GOOGLE = "google"
    CLAUDE = "claude"
    AZURE_OPENAI = "azure_openai"


class AIConfidenceLevel(Enum):
    """AI decision confidence levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AIRiskAssessment(BaseModel):
    """AI-generated risk assessment for an application."""
    overall_risk_score: int = Field(..., ge=0, le=1000, description="Overall risk score 0-1000")
    risk_level: str = Field(..., description="Risk level categorization")
    key_risk_factors: List[str] = Field(default_factory=list, description="Primary risk factors identified")
    risk_mitigation_suggestions: List[str] = Field(default_factory=list, description="Suggested risk mitigations")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence in assessment")


class AIUnderwritingDecision(BaseModel):
    """AI-generated underwriting decision."""
    application_id: str = Field(..., description="Application identifier")
    decision: DecisionType = Field(..., description="AI recommended decision")
    reasoning: str = Field(..., description="Detailed reasoning for the decision")
    confidence_level: AIConfidenceLevel = Field(..., description="Confidence in the decision")
    risk_assessment: AIRiskAssessment = Field(..., description="Detailed risk assessment")
    alternative_considerations: List[str] = Field(default_factory=list, description="Alternative considerations")
    recommended_premium_adjustment: Optional[float] = Field(None, description="Premium adjustment percentage")
    decision_timestamp: datetime = Field(default_factory=datetime.now, description="When decision was made")
    model_version: str = Field(..., description="AI model version used")
    provider: AIProviderType = Field(..., description="AI provider used")
    langsmith_run_id: Optional[str] = Field(None, description="LangSmith run ID for tracing")
    langsmith_run_url: Optional[str] = Field(None, description="LangSmith run URL for tracing")


class AIServiceInterface(ABC):
    """Abstract interface for AI underwriting services."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize AI service with configuration.
        
        Args:
            config: Configuration dictionary containing API keys, model settings, etc.
        """
        self.config = config
        self.provider_type = self._get_provider_type()
    
    @abstractmethod
    def _get_provider_type(self) -> AIProviderType:
        """Return the provider type for this service."""
        pass
    
    @abstractmethod
    async def evaluate_application(
        self, 
        application: Application,
        rule_set: str = "standard",
        context: Optional[Dict[str, Any]] = None
    ) -> AIUnderwritingDecision:
        """Evaluate an application using AI.
        
        Args:
            application: The insurance application to evaluate
            rule_set: Rule set context (conservative, standard, liberal)
            context: Additional context for the evaluation
            
        Returns:
            AI-generated underwriting decision
            
        Raises:
            AIServiceError: If AI evaluation fails
        """
        pass
    
    @abstractmethod
    async def batch_evaluate_applications(
        self,
        applications: List[Application],
        rule_set: str = "standard",
        context: Optional[Dict[str, Any]] = None
    ) -> List[AIUnderwritingDecision]:
        """Evaluate multiple applications in batch.
        
        Args:
            applications: List of applications to evaluate
            rule_set: Rule set context
            context: Additional context
            
        Returns:
            List of AI-generated decisions
        """
        pass
    
    @abstractmethod
    def validate_configuration(self) -> bool:
        """Validate the AI service configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check the health and availability of the AI service.
        
        Returns:
            Dictionary containing health status information
        """
        pass
    
    def get_supported_features(self) -> List[str]:
        """Get list of features supported by this AI service.
        
        Returns:
            List of supported feature names
        """
        return [
            "single_evaluation",
            "batch_evaluation", 
            "risk_assessment",
            "premium_recommendations"
        ]


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    
    def __init__(self, message: str, provider: AIProviderType, error_code: Optional[str] = None):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code
        self.timestamp = datetime.now()


class AIServiceUnavailableError(AIServiceError):
    """Raised when AI service is unavailable."""
    pass


class AIRateLimitError(AIServiceError):
    """Raised when AI service rate limit is exceeded."""
    pass


class AIInvalidResponseError(AIServiceError):
    """Raised when AI service returns invalid response."""
    pass


class AIConfigurationError(AIServiceError):
    """Raised when AI service configuration is invalid."""
    pass