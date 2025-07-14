"""
Tests for AI underwriting components.

This module contains comprehensive tests for the AI integration features
including response parsing, prompt templates, and decision combination.
"""

import asyncio
import json
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.underwriting.ai.base import (
    AIUnderwritingDecision, 
    AIRiskAssessment, 
    AIConfidenceLevel, 
    AIProviderType,
    AIServiceError,
    AIInvalidResponseError
)
from src.underwriting.ai.response_parser import AIResponseParser
from src.underwriting.ai.prompts import PromptManager
from src.underwriting.ai.prompts.conservative import ConservativePrompts
from src.underwriting.ai.prompts.standard import StandardPrompts
from src.underwriting.ai.prompts.liberal import LiberalPrompts
from src.underwriting.ai.openai_service import OpenAIService
from src.underwriting.core.ai_engine import (
    AIEnhancedUnderwritingEngine, 
    DecisionCombinationStrategy,
    EnhancedUnderwritingDecision
)
from src.underwriting.core.models import (
    Application, Driver, Vehicle, DecisionType, 
    LicenseStatus, MaritalStatus, Gender, VehicleCategory
)


class TestAIResponseParser:
    """Test AI response parser functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = AIResponseParser(AIProviderType.OPENAI, "gpt-4-turbo")
    
    def test_parse_valid_json_response(self):
        """Test parsing valid JSON response."""
        response = '''
        {
            "decision": "ACCEPT",
            "confidence_level": "HIGH",
            "reasoning": "Low risk applicant with clean record",
            "risk_assessment": {
                "overall_risk_score": 250,
                "risk_level": "LOW",
                "key_risk_factors": ["Young driver"],
                "risk_mitigation_suggestions": ["Defensive driving course"],
                "confidence_score": 0.9
            },
            "alternative_considerations": ["Consider premium discount"],
            "recommended_premium_adjustment": -5.0
        }
        '''
        
        decision = self.parser.parse_decision(response, "test-app-123")
        
        assert decision.application_id == "test-app-123"
        assert decision.decision == DecisionType.ACCEPT
        assert decision.confidence_level == AIConfidenceLevel.HIGH
        assert decision.reasoning == "Low risk applicant with clean record"
        assert decision.risk_assessment.overall_risk_score == 250
        assert decision.recommended_premium_adjustment == -5.0
    
    def test_parse_markdown_json_response(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        response = '''
        Here's my analysis:
        
        ```json
        {
            "decision": "DENY",
            "confidence_level": "HIGH",
            "reasoning": "Multiple DUI violations",
            "risk_assessment": {
                "overall_risk_score": 850,
                "risk_level": "VERY_HIGH",
                "key_risk_factors": ["DUI history", "Poor credit"],
                "risk_mitigation_suggestions": [],
                "confidence_score": 0.95
            }
        }
        ```
        '''
        
        decision = self.parser.parse_decision(response, "test-app-456")
        
        assert decision.decision == DecisionType.DENY
        assert decision.risk_assessment.overall_risk_score == 850
        assert len(decision.risk_assessment.key_risk_factors) == 2
    
    def test_parse_invalid_response(self):
        """Test handling of invalid response."""
        response = "This is not a valid JSON response at all."
        
        with pytest.raises(AIInvalidResponseError):
            self.parser.parse_decision(response, "test-app-789")
    
    def test_parse_partial_response(self):
        """Test parsing response with missing fields."""
        response = '''
        {
            "decision": "ADJUDICATE",
            "reasoning": "Moderate risk factors present"
        }
        '''
        
        decision = self.parser.parse_decision(response, "test-app-partial")
        
        assert decision.decision == DecisionType.ADJUDICATE
        assert decision.confidence_level == AIConfidenceLevel.MEDIUM  # Default
        assert decision.risk_assessment.overall_risk_score == 500  # Default
    
    def test_extract_key_value_pairs_fallback(self):
        """Test fallback key-value extraction."""
        response = '''
        Decision: ACCEPT
        Confidence Level: HIGH
        Reasoning: Good driving record with no violations
        Risk Score: 300
        Risk Level: LOW
        '''
        
        data = self.parser._extract_key_value_pairs(response)
        
        assert data["decision"] == "ACCEPT"
        assert data["overall_risk_score"] == 300
    
    def test_batch_response_validation(self):
        """Test batch response validation."""
        responses = [
            '{"decision": "ACCEPT", "reasoning": "Good", "risk_assessment": {"overall_risk_score": 200, "risk_level": "LOW", "key_risk_factors": [], "risk_mitigation_suggestions": [], "confidence_score": 0.8}}',
            'Invalid response',
            '{"decision": "DENY", "reasoning": "Bad", "risk_assessment": {"overall_risk_score": 800, "risk_level": "HIGH", "key_risk_factors": [], "risk_mitigation_suggestions": [], "confidence_score": 0.9}}'
        ]
        app_ids = ["app1", "app2", "app3"]
        
        successful, failed = self.parser.validate_batch_responses(responses, app_ids)
        
        assert len(successful) == 2
        assert len(failed) == 1
        assert failed[0][0] == "app2"


class TestPromptTemplates:
    """Test prompt template functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.prompt_manager = PromptManager()
        self.prompt_manager.register_template("conservative", ConservativePrompts("conservative"))
        self.prompt_manager.register_template("standard", StandardPrompts("standard"))
        self.prompt_manager.register_template("liberal", LiberalPrompts("liberal"))
        
        # Create test application
        self.test_application = Application(
            id="test-123",
            applicant=Driver(
                first_name="John",
                last_name="Doe",
                age=30,
                gender=Gender.MALE,
                marital_status=MaritalStatus.MARRIED,
                license_status=LicenseStatus.VALID,
                years_licensed=12
            ),
            vehicles=[
                Vehicle(
                    year=2020,
                    make="Toyota",
                    model="Camry",
                    category=VehicleCategory.SEDAN,
                    value=25000,
                    safety_rating=5
                )
            ],
            coverage_lapse_days=0,
            credit_score=750
        )
    
    def test_conservative_prompt_generation(self):
        """Test conservative prompt template."""
        system_prompt, user_prompt = self.prompt_manager.generate_prompt(
            "conservative", self.test_application
        )
        
        assert "CONSERVATIVE" in system_prompt
        assert "strict" in system_prompt.lower()
        assert "loss prevention" in system_prompt.lower()
        assert self.test_application.id in user_prompt
        assert "Toyota" in user_prompt
    
    def test_standard_prompt_generation(self):
        """Test standard prompt template."""
        system_prompt, user_prompt = self.prompt_manager.generate_prompt(
            "standard", self.test_application
        )
        
        assert "STANDARD" in system_prompt
        assert "balance" in system_prompt.lower()
        assert "industry-standard" in system_prompt.lower()
    
    def test_liberal_prompt_generation(self):
        """Test liberal prompt template."""
        system_prompt, user_prompt = self.prompt_manager.generate_prompt(
            "liberal", self.test_application
        )
        
        assert "LIBERAL" in system_prompt
        assert "growth" in system_prompt.lower()
        assert "market expansion" in system_prompt.lower()
    
    def test_prompt_with_context(self):
        """Test prompt generation with additional context."""
        context = {"market_conditions": "competitive", "business_goal": "growth"}
        
        system_prompt, user_prompt = self.prompt_manager.generate_prompt(
            "standard", self.test_application, context
        )
        
        assert "competitive" in user_prompt
        assert "growth" in user_prompt
    
    def test_invalid_rule_set(self):
        """Test handling of invalid rule set."""
        with pytest.raises(ValueError):
            self.prompt_manager.generate_prompt("invalid", self.test_application)
    
    def test_application_data_formatting(self):
        """Test application data formatting."""
        template = StandardPrompts("standard")
        formatted_data = template.format_application_data(self.test_application)
        
        data = json.loads(formatted_data)
        assert data["application_id"] == "test-123"
        assert data["applicant"]["age"] == 30
        assert data["vehicles"][0]["make"] == "Toyota"


class TestOpenAIService:
    """Test OpenAI service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "openai": {
                "enabled": True,
                "api_key": "test-key",
                "model": "gpt-4-turbo",
                "max_tokens": 2000,
                "temperature": 0.1,
                "timeout": 30,
                "retry_attempts": 3,
                "retry_delay": 1.0,
                "rate_limit": {
                    "requests_per_minute": 60,
                    "tokens_per_minute": 150000
                }
            }
        }
        
        self.test_application = Application(
            id="test-openai-123",
            applicant=Driver(
                first_name="Jane",
                last_name="Smith",
                age=25,
                gender=Gender.FEMALE,
                marital_status=MaritalStatus.SINGLE,
                license_status=LicenseStatus.VALID,
                years_licensed=7
            ),
            vehicles=[
                Vehicle(
                    year=2019,
                    make="Honda",
                    model="Civic",
                    category=VehicleCategory.SEDAN,
                    value=20000,
                    safety_rating=5
                )
            ],
            coverage_lapse_days=0,
            credit_score=700
        )
    
    def test_service_initialization(self):
        """Test OpenAI service initialization."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            service = OpenAIService(self.config)
            
            assert service.provider_type == AIProviderType.OPENAI
            assert service.model == "gpt-4-turbo"
            assert service.api_key == "test-key"
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            service = OpenAIService(self.config)
            
            # Should pass with valid config
            assert service.validate_configuration() == True
            
            # Should fail with invalid temperature
            service.temperature = 5.0
            assert service.validate_configuration() == False
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            service = OpenAIService(self.config)
            
            # Simulate hitting rate limit
            for _ in range(65):  # Exceed 60 requests per minute
                service._track_request()
            
            # This should trigger rate limiting
            start_time = datetime.now()
            await service._check_rate_limits()
            end_time = datetime.now()
            
            # Should have waited
            assert (end_time - start_time).total_seconds() > 0
    
    def test_health_check(self):
        """Test health check functionality."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            service = OpenAIService(self.config)
            
            health = service.health_check()
            
            assert "service" in health
            assert "provider" in health
            assert "status" in health
            assert health["service"] == "OpenAI"


class TestAIEnhancedEngine:
    """Test AI-enhanced underwriting engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_application = Application(
            id="test-enhanced-123",
            applicant=Driver(
                first_name="Bob",
                last_name="Johnson",
                age=35,
                gender=Gender.MALE,
                marital_status=MaritalStatus.MARRIED,
                license_status=LicenseStatus.VALID,
                years_licensed=15
            ),
            vehicles=[
                Vehicle(
                    year=2021,
                    make="Ford",
                    model="F-150",
                    category=VehicleCategory.PICKUP,
                    value=35000,
                    safety_rating=4
                )
            ],
            coverage_lapse_days=0,
            credit_score=720
        )
    
    @patch('src.underwriting.core.ai_engine.Path.exists')
    @patch('builtins.open')
    def test_engine_initialization_without_ai(self, mock_open, mock_exists):
        """Test engine initialization with AI disabled."""
        engine = AIEnhancedUnderwritingEngine(ai_enabled=False)
        
        assert engine.ai_enabled == False
        assert engine.ai_service is None
    
    @patch('src.underwriting.core.ai_engine.Path.exists')
    @patch('builtins.open')
    def test_ai_config_loading(self, mock_open, mock_exists):
        """Test AI configuration loading."""
        mock_exists.return_value = True
        mock_config = {
            "ai_services": {
                "openai": {"enabled": False}
            },
            "decision_combination": {
                "strategy": "weighted_average",
                "ai_weight": 0.3,
                "rules_weight": 0.7
            }
        }
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_config)
        
        engine = AIEnhancedUnderwritingEngine()
        
        assert engine.combination_strategy == DecisionCombinationStrategy.WEIGHTED_AVERAGE
        assert engine.ai_config["decision_combination"]["ai_weight"] == 0.3
    
    def test_decision_combination_rules_only(self):
        """Test rules-only decision combination."""
        engine = AIEnhancedUnderwritingEngine(ai_enabled=False)
        engine.combination_strategy = DecisionCombinationStrategy.RULES_ONLY
        
        # Create mock decisions
        from src.underwriting.core.models import UnderwritingDecision, RiskScore
        
        rule_decision = UnderwritingDecision(
            application_id="test-123",
            decision=DecisionType.ACCEPT,
            reason="Good risk profile",
            risk_score=RiskScore(overall_score=300, driver_risk=100, vehicle_risk=100, history_risk=100),
            rule_set="standard",
            triggered_rules=[]
        )
        
        ai_decision = AIUnderwritingDecision(
            application_id="test-123",
            decision=DecisionType.DENY,
            reasoning="Different assessment",
            confidence_level=AIConfidenceLevel.HIGH,
            risk_assessment=AIRiskAssessment(
                overall_risk_score=700,
                risk_level="HIGH",
                key_risk_factors=["Test factor"],
                risk_mitigation_suggestions=[],
                confidence_score=0.9
            ),
            model_version="gpt-4-turbo",
            provider=AIProviderType.OPENAI
        )
        
        combined_decision, metadata = engine._combine_decisions(rule_decision, ai_decision, "standard")
        
        assert combined_decision.decision == DecisionType.ACCEPT  # Should use rule decision
        assert metadata["combination_strategy"] == "rules_only"
        assert metadata["ai_decision"] == "DENY"
    
    def test_decision_combination_weighted_average(self):
        """Test weighted average decision combination."""
        engine = AIEnhancedUnderwritingEngine(ai_enabled=False)
        engine.combination_strategy = DecisionCombinationStrategy.WEIGHTED_AVERAGE
        engine.ai_config = {
            "decision_combination": {
                "ai_weight": 0.4,
                "rules_weight": 0.6,
                "confidence_threshold": 0.7
            }
        }
        
        from src.underwriting.core.models import UnderwritingDecision, RiskScore
        
        rule_decision = UnderwritingDecision(
            application_id="test-123",
            decision=DecisionType.ACCEPT,
            reason="Good risk profile",
            risk_score=RiskScore(overall_score=200, driver_risk=50, vehicle_risk=50, history_risk=50),
            rule_set="standard",
            triggered_rules=[]
        )
        
        ai_decision = AIUnderwritingDecision(
            application_id="test-123",
            decision=DecisionType.ACCEPT,
            reasoning="Low risk assessment",
            confidence_level=AIConfidenceLevel.HIGH,
            risk_assessment=AIRiskAssessment(
                overall_risk_score=300,
                risk_level="LOW",
                key_risk_factors=[],
                risk_mitigation_suggestions=[],
                confidence_score=0.8
            ),
            model_version="gpt-4-turbo",
            provider=AIProviderType.OPENAI
        )
        
        combined_decision, metadata = engine._combine_decisions(rule_decision, ai_decision, "standard")
        
        # Weighted score should be 200 * 0.6 + 300 * 0.4 = 240
        assert metadata["weighted_risk_score"] == 240
        assert metadata["decision_basis"] == "weighted_average"
    
    def test_health_check_no_ai(self):
        """Test health check with no AI service."""
        engine = AIEnhancedUnderwritingEngine(ai_enabled=False)
        
        health = engine.get_ai_service_health()
        
        assert health["ai_enabled"] == False
        assert health["service_available"] == False
        assert health["status"] == "disabled"


# Integration test fixtures
@pytest.fixture
def sample_application():
    """Create a sample application for testing."""
    return Application(
        id="integration-test-123",
        applicant=Driver(
            first_name="Alice",
            last_name="Cooper",
            age=28,
            gender=Gender.FEMALE,
            marital_status=MaritalStatus.SINGLE,
            license_status=LicenseStatus.VALID,
            years_licensed=10
        ),
        vehicles=[
            Vehicle(
                year=2020,
                make="Nissan",
                model="Altima",
                category=VehicleCategory.SEDAN,
                value=22000,
                safety_rating=5
            )
        ],
        coverage_lapse_days=5,
        credit_score=680
    )


class TestIntegration:
    """Integration tests for AI components."""
    
    def test_end_to_end_processing_without_ai(self, sample_application):
        """Test end-to-end processing without AI."""
        engine = AIEnhancedUnderwritingEngine(ai_enabled=False)
        
        enhanced_decision = engine.process_application_enhanced_sync(
            sample_application, "standard", use_ai=False
        )
        
        assert isinstance(enhanced_decision, EnhancedUnderwritingDecision)
        assert enhanced_decision.rule_decision is not None
        assert enhanced_decision.ai_decision is None
        assert enhanced_decision.final_decision is not None
    
    def test_statistics_generation(self, sample_application):
        """Test enhanced statistics generation."""
        engine = AIEnhancedUnderwritingEngine(ai_enabled=False)
        
        enhanced_decisions = [
            engine.process_application_enhanced_sync(sample_application, "standard", use_ai=False)
        ]
        
        stats = engine.get_enhanced_statistics(enhanced_decisions)
        
        assert "ai_decisions_available" in stats
        assert "ai_coverage_percentage" in stats
        assert "combination_strategies_used" in stats
        assert stats["total_applications"] == 1