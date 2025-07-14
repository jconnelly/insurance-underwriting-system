"""
AI-Enhanced Underwriting Engine for processing insurance applications.

This module extends the core underwriting engine with AI capabilities,
providing decision combination logic and fallback mechanisms.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from loguru import logger

from .engine import UnderwritingEngine
from .models import Application, UnderwritingDecision, DecisionType, RiskScore
from ..ai.base import AIServiceInterface, AIUnderwritingDecision, AIServiceError
from ..ai.openai_service import OpenAIService
from ..ai.langsmith_tracing import get_tracer, trace_ai_evaluation, trace_batch_evaluation, trace_ab_testing
from ..rate_limiting import RateLimiter, RateLimitExceeded, UsageAnalytics, AdminOverride


class DecisionCombinationStrategy(Enum):
    """Strategies for combining AI and rule-based decisions."""
    RULES_ONLY = "rules_only"
    AI_ONLY = "ai_only"
    WEIGHTED_AVERAGE = "weighted_average"
    AI_OVERRIDE = "ai_override"
    CONSENSUS_REQUIRED = "consensus_required"


class EnhancedUnderwritingDecision:
    """Enhanced decision containing both rule-based and AI assessments."""
    
    def __init__(
        self, 
        rule_decision: UnderwritingDecision,
        ai_decision: Optional[AIUnderwritingDecision] = None,
        combined_decision: Optional[UnderwritingDecision] = None,
        combination_metadata: Optional[Dict[str, Any]] = None,
        langsmith_run_id: Optional[str] = None,
        langsmith_run_url: Optional[str] = None
    ):
        """Initialize enhanced decision.
        
        Args:
            rule_decision: Rule-based underwriting decision
            ai_decision: AI underwriting decision (if available)
            combined_decision: Final combined decision
            combination_metadata: Metadata about decision combination process
            langsmith_run_id: LangSmith run ID for tracing
            langsmith_run_url: LangSmith run URL for sharing
        """
        self.rule_decision = rule_decision
        self.ai_decision = ai_decision
        self.combined_decision = combined_decision or rule_decision
        self.combination_metadata = combination_metadata or {}
        self.langsmith_run_id = langsmith_run_id
        self.langsmith_run_url = langsmith_run_url
        
        # Also copy LangSmith info from AI decision if available
        if ai_decision and hasattr(ai_decision, 'langsmith_run_id'):
            self.langsmith_run_id = self.langsmith_run_id or ai_decision.langsmith_run_id
            self.langsmith_run_url = self.langsmith_run_url or ai_decision.langsmith_run_url
    
    @property
    def final_decision(self) -> UnderwritingDecision:
        """Get the final combined decision."""
        return self.combined_decision


class AIEnhancedUnderwritingEngine(UnderwritingEngine):
    """AI-enhanced underwriting engine with decision combination capabilities."""
    
    def __init__(
        self, 
        config_loader=None,
        ai_config_path: Optional[str] = None,
        ai_enabled: bool = True,
        rate_limiting_enabled: bool = True
    ):
        """Initialize AI-enhanced underwriting engine.
        
        Args:
            config_loader: Configuration loader instance
            ai_config_path: Path to AI configuration file
            ai_enabled: Whether AI features are enabled
            rate_limiting_enabled: Whether rate limiting is enabled
        """
        super().__init__(config_loader)
        
        self.ai_enabled = ai_enabled
        self.ai_service: Optional[AIServiceInterface] = None
        self.ai_config = {}
        self.combination_strategy = DecisionCombinationStrategy.WEIGHTED_AVERAGE
        
        # Initialize rate limiting
        self.rate_limiting_enabled = rate_limiting_enabled
        self.rate_limiter: Optional[RateLimiter] = None
        self.usage_analytics: Optional[UsageAnalytics] = None
        self.admin_override: Optional[AdminOverride] = None
        
        if ai_enabled:
            self._initialize_ai_service(ai_config_path)
        
        if rate_limiting_enabled:
            self._initialize_rate_limiting()
    
    def _initialize_ai_service(self, config_path: Optional[str] = None) -> None:
        """Initialize AI service with configuration."""
        try:
            # Load AI configuration
            if config_path is None:
                config_path = Path(__file__).parent.parent / "config" / "ai_config.json"
            
            with open(config_path, 'r') as f:
                self.ai_config = json.load(f)
            
            # Set combination strategy
            strategy_str = self.ai_config.get("decision_combination", {}).get("strategy", "weighted_average")
            self.combination_strategy = DecisionCombinationStrategy(strategy_str)
            
            # Initialize AI service (currently only OpenAI)
            ai_services_config = self.ai_config.get("ai_services", {})
            openai_config = ai_services_config.get("openai", {})
            
            if openai_config.get("enabled", False):
                self.ai_service = OpenAIService(ai_services_config)
                
                # Validate configuration
                if self.ai_service.validate_configuration():
                    logger.info("AI service initialized successfully")
                else:
                    logger.warning("AI service configuration validation failed")
                    self.ai_service = None
            else:
                logger.info("AI service disabled in configuration")
                
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            self.ai_service = None
    
    def _initialize_rate_limiting(self) -> None:
        """Initialize rate limiting system."""
        try:
            # Initialize rate limiter with default config path
            rate_limits_config_path = Path(__file__).parent.parent / "config" / "rate_limits.json"
            self.rate_limiter = RateLimiter(str(rate_limits_config_path))
            
            # Initialize usage analytics
            analytics_config = self.rate_limiter.config.get("analytics", {})
            self.usage_analytics = UsageAnalytics(self.rate_limiter.storage, analytics_config)
            
            # Initialize admin override
            admin_config = self.rate_limiter.config.get("admin", {})
            self.admin_override = AdminOverride(self.rate_limiter.storage, admin_config)
            
            logger.info("Rate limiting system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize rate limiting: {e}")
            self.rate_limiting_enabled = False
            self.rate_limiter = None
            self.usage_analytics = None
            self.admin_override = None
    
    @trace_ai_evaluation(
        name="ai_enhanced_process_application",
        metadata={"engine": "ai_enhanced", "type": "single_application"},
        tags=["ai_enhanced", "single_evaluation"]
    )
    async def process_application_enhanced(
        self,
        application: Application,
        rule_set_name: str = "standard",
        use_ai: bool = True
    ) -> EnhancedUnderwritingDecision:
        """Process application with both rule-based and AI evaluation.
        
        Args:
            application: Application to process
            rule_set_name: Rule set to use
            use_ai: Whether to use AI evaluation
            
        Returns:
            Enhanced decision with both rule and AI assessments
        """
        logger.info(f"Processing enhanced application {application.id}")
        
        # Check rate limits for underwriting evaluations
        identifier = str(application.id)
        if self.rate_limiting_enabled and self.rate_limiter:
            try:
                # Check and consume rate limit for underwriting evaluations
                if not self.rate_limiter.consume_rate_limit(
                    identifier, "underwriting_evaluations", 
                    user_id=str(application.applicant.id) if hasattr(application.applicant, 'id') else None,
                    metadata={"rule_set": rule_set_name, "use_ai": use_ai}
                ):
                    logger.warning(f"Rate limit exceeded for underwriting evaluation: {identifier}")
                    # Continue with processing but log the limit hit
                    
            except RateLimitExceeded as e:
                logger.error(f"Rate limit exceeded for {identifier}: {e}")
                # For underwriting evaluations, we'll continue but handle gracefully
                # In production, you might want to return an error or queue the request
        
        # Get rule-based decision
        rule_decision = self.process_application(application, rule_set_name)
        
        # Get AI decision if enabled and available
        ai_decision = None
        if use_ai and self.ai_enabled and self.ai_service:
            # Check rate limits for AI evaluations specifically
            if self.rate_limiting_enabled and self.rate_limiter:
                try:
                    # Check and consume rate limit for AI evaluations
                    if not self.rate_limiter.consume_rate_limit(
                        identifier, "ai_evaluations",
                        user_id=str(application.applicant.id) if hasattr(application.applicant, 'id') else None,
                        metadata={"rule_set": rule_set_name}
                    ):
                        logger.warning(f"Rate limit exceeded for AI evaluation: {identifier}")
                        # Check if graceful degradation is enabled
                        if self.rate_limiter.degradation_config.get("fallback_to_rules_only", True):
                            logger.info(f"Graceful degradation: falling back to rules-only for {identifier}")
                            use_ai = False
                        
                except RateLimitExceeded as e:
                    logger.error(f"AI rate limit exceeded for {identifier}: {e}")
                    # Enable graceful degradation - fall back to rules only
                    if self.rate_limiter.degradation_config.get("fallback_to_rules_only", True):
                        logger.info(f"Graceful degradation: falling back to rules-only due to rate limit")
                        use_ai = False
                    else:
                        # Re-raise if graceful degradation is disabled
                        raise
            
            if use_ai:  # Only proceed with AI if rate limits allow
                try:
                    ai_decision = await self.ai_service.evaluate_application(
                        application, rule_set_name
                    )
                    logger.info(f"AI evaluation completed for application {application.id}")
                except AIServiceError as e:
                    logger.error(f"AI evaluation failed for application {application.id}: {e}")
                    # Continue with rule-based decision only
                except Exception as e:
                    logger.error(f"Unexpected AI error for application {application.id}: {e}")
        
        # Combine decisions
        combined_decision, metadata = self._combine_decisions(
            rule_decision, ai_decision, rule_set_name
        )
        
        return EnhancedUnderwritingDecision(
            rule_decision=rule_decision,
            ai_decision=ai_decision,
            combined_decision=combined_decision,
            combination_metadata=metadata
        )
    
    def process_application_enhanced_sync(
        self,
        application: Application,
        rule_set_name: str = "standard",
        use_ai: bool = True
    ) -> EnhancedUnderwritingDecision:
        """Synchronous wrapper for enhanced application processing."""
        return asyncio.run(self.process_application_enhanced(application, rule_set_name, use_ai))
    
    @trace_batch_evaluation(
        name="ai_enhanced_batch_process_applications",
        metadata={"engine": "ai_enhanced", "type": "batch_processing"},
        tags=["ai_enhanced", "batch_evaluation"]
    )
    async def batch_process_applications_enhanced(
        self,
        applications: List[Application],
        rule_set_name: str = "standard",
        use_ai: bool = True
    ) -> List[EnhancedUnderwritingDecision]:
        """Process multiple applications with AI enhancement.
        
        Args:
            applications: Applications to process
            rule_set_name: Rule set to use
            use_ai: Whether to use AI evaluation
            
        Returns:
            List of enhanced decisions
        """
        logger.info(f"Batch processing {len(applications)} enhanced applications")
        
        # Check rate limits for batch processing
        batch_identifier = f"batch_{int(time.time())}"
        if self.rate_limiting_enabled and self.rate_limiter:
            try:
                # Check batch size limit
                batch_config = self.rate_limiter.rate_limits.get("batch_processing")
                if batch_config and batch_config.max_batch_size:
                    if len(applications) > batch_config.max_batch_size:
                        raise RateLimitExceeded(
                            f"Batch size {len(applications)} exceeds limit {batch_config.max_batch_size}",
                            "batch_processing",
                            len(applications),
                            batch_config.max_batch_size,
                            time.time() + 3600
                        )
                
                # Check and consume rate limit for batch processing
                if not self.rate_limiter.consume_rate_limit(
                    batch_identifier, "batch_processing",
                    resource_amount=len(applications),
                    metadata={"rule_set": rule_set_name, "use_ai": use_ai, "batch_size": len(applications)}
                ):
                    logger.warning(f"Rate limit exceeded for batch processing: {batch_identifier}")
                    
            except RateLimitExceeded as e:
                logger.error(f"Batch processing rate limit exceeded: {e}")
                raise
        
        # Process rule-based decisions first
        rule_decisions = self.batch_process_applications(applications, rule_set_name)
        
        # Create application-to-decision mapping
        rule_decision_map = {d.application_id: d for d in rule_decisions}
        
        # Get AI decisions if enabled
        ai_decisions = []
        if use_ai and self.ai_enabled and self.ai_service:
            try:
                ai_decisions = await self.ai_service.batch_evaluate_applications(
                    applications, rule_set_name
                )
                logger.info(f"AI batch evaluation completed: {len(ai_decisions)} decisions")
            except Exception as e:
                logger.error(f"AI batch evaluation failed: {e}")
        
        # Create AI decision mapping
        ai_decision_map = {d.application_id: d for d in ai_decisions}
        
        # Combine decisions
        enhanced_decisions = []
        for app in applications:
            rule_decision = rule_decision_map.get(app.id)
            ai_decision = ai_decision_map.get(app.id)
            
            if rule_decision:
                combined_decision, metadata = self._combine_decisions(
                    rule_decision, ai_decision, rule_set_name
                )
                
                enhanced_decisions.append(EnhancedUnderwritingDecision(
                    rule_decision=rule_decision,
                    ai_decision=ai_decision,
                    combined_decision=combined_decision,
                    combination_metadata=metadata
                ))
        
        return enhanced_decisions
    
    @trace_ab_testing(
        name="ai_enhanced_compare_rule_sets",
        metadata={"engine": "ai_enhanced", "type": "ab_testing"},
        tags=["ai_enhanced", "ab_testing", "comparison"]
    )
    async def compare_rule_sets_enhanced(
        self,
        application: Application,
        include_ai: bool = True
    ) -> Dict[str, EnhancedUnderwritingDecision]:
        """Compare rule sets with AI enhancement for A/B testing.
        
        Args:
            application: Application to evaluate
            include_ai: Whether to include AI evaluation
            
        Returns:
            Dictionary mapping rule set names to enhanced decisions
        """
        logger.info(f"Comparing enhanced rule sets for application {application.id}")
        
        results = {}
        for rule_set_name in ["conservative", "standard", "liberal"]:
            try:
                enhanced_decision = await self.process_application_enhanced(
                    application, rule_set_name, use_ai=include_ai
                )
                results[rule_set_name] = enhanced_decision
            except Exception as e:
                logger.error(f"Failed to evaluate with enhanced rule set {rule_set_name}: {e}")
                continue
        
        return results
    
    def compare_rule_sets_enhanced_sync(
        self,
        application: Application,
        include_ai: bool = True
    ) -> Dict[str, EnhancedUnderwritingDecision]:
        """Synchronous wrapper for enhanced rule set comparison."""
        return asyncio.run(self.compare_rule_sets_enhanced(application, include_ai))
    
    def _combine_decisions(
        self,
        rule_decision: UnderwritingDecision,
        ai_decision: Optional[AIUnderwritingDecision],
        rule_set_name: str
    ) -> tuple[UnderwritingDecision, Dict[str, Any]]:
        """Combine rule-based and AI decisions using configured strategy.
        
        Args:
            rule_decision: Rule-based decision
            ai_decision: AI decision (may be None)
            rule_set_name: Rule set used
            
        Returns:
            Tuple of (combined_decision, metadata)
        """
        metadata = {
            "combination_strategy": self.combination_strategy.value,
            "ai_available": ai_decision is not None,
            "rule_set": rule_set_name,
            "timestamp": rule_decision.decision_date.isoformat()
        }
        
        # If no AI decision, return rule decision
        if ai_decision is None:
            metadata["fallback_reason"] = "ai_unavailable"
            return rule_decision, metadata
        
        # Apply combination strategy
        if self.combination_strategy == DecisionCombinationStrategy.RULES_ONLY:
            return self._combine_rules_only(rule_decision, ai_decision, metadata)
        
        elif self.combination_strategy == DecisionCombinationStrategy.AI_ONLY:
            return self._combine_ai_only(rule_decision, ai_decision, metadata)
        
        elif self.combination_strategy == DecisionCombinationStrategy.WEIGHTED_AVERAGE:
            return self._combine_weighted_average(rule_decision, ai_decision, metadata)
        
        elif self.combination_strategy == DecisionCombinationStrategy.AI_OVERRIDE:
            return self._combine_ai_override(rule_decision, ai_decision, metadata)
        
        elif self.combination_strategy == DecisionCombinationStrategy.CONSENSUS_REQUIRED:
            return self._combine_consensus_required(rule_decision, ai_decision, metadata)
        
        else:
            # Default to rules only
            metadata["fallback_reason"] = "unknown_strategy"
            return rule_decision, metadata
    
    def _combine_rules_only(
        self, 
        rule_decision: UnderwritingDecision, 
        ai_decision: AIUnderwritingDecision,
        metadata: Dict[str, Any]
    ) -> tuple[UnderwritingDecision, Dict[str, Any]]:
        """Use only rule-based decision."""
        metadata["ai_decision"] = ai_decision.decision.value
        metadata["ai_risk_score"] = ai_decision.risk_assessment.overall_risk_score
        return rule_decision, metadata
    
    def _combine_ai_only(
        self,
        rule_decision: UnderwritingDecision,
        ai_decision: AIUnderwritingDecision,
        metadata: Dict[str, Any]
    ) -> tuple[UnderwritingDecision, Dict[str, Any]]:
        """Use only AI decision, converted to UnderwritingDecision format."""
        metadata["rule_decision"] = rule_decision.decision.value
        metadata["rule_risk_score"] = rule_decision.risk_score.overall_score
        
        # Convert AI decision to UnderwritingDecision format
        combined_decision = UnderwritingDecision(
            application_id=rule_decision.application_id,
            decision=ai_decision.decision,
            reason=ai_decision.reasoning,
            risk_score=self._convert_ai_risk_score(ai_decision.risk_assessment),
            rule_set=rule_decision.rule_set,
            triggered_rules=[]  # AI doesn't use rule IDs
        )
        
        return combined_decision, metadata
    
    def _combine_weighted_average(
        self,
        rule_decision: UnderwritingDecision,
        ai_decision: AIUnderwritingDecision,
        metadata: Dict[str, Any]
    ) -> tuple[UnderwritingDecision, Dict[str, Any]]:
        """Combine decisions using weighted average of risk scores."""
        config = self.ai_config.get("decision_combination", {})
        ai_weight = config.get("ai_weight", 0.3)
        rules_weight = config.get("rules_weight", 0.7)
        confidence_threshold = config.get("confidence_threshold", 0.7)
        
        metadata.update({
            "ai_weight": ai_weight,
            "rules_weight": rules_weight,
            "rule_decision": rule_decision.decision.value,
            "ai_decision": ai_decision.decision.value,
            "rule_risk_score": rule_decision.risk_score.overall_score,
            "ai_risk_score": ai_decision.risk_assessment.overall_risk_score,
            "ai_confidence": ai_decision.risk_assessment.confidence_score
        })
        
        # Calculate weighted risk score
        weighted_score = (
            rule_decision.risk_score.overall_score * rules_weight +
            ai_decision.risk_assessment.overall_risk_score * ai_weight
        )
        weighted_score = int(round(weighted_score))
        
        # Determine final decision based on weighted score and confidence
        if ai_decision.risk_assessment.confidence_score < confidence_threshold:
            # Low AI confidence, prefer rule decision
            final_decision = rule_decision.decision
            final_reason = f"Rule-based decision (low AI confidence: {ai_decision.risk_assessment.confidence_score:.2f})"
            metadata["decision_basis"] = "rules_low_ai_confidence"
        else:
            # High AI confidence, use weighted approach
            if weighted_score <= 300:
                final_decision = DecisionType.ACCEPT
            elif weighted_score >= 700:
                final_decision = DecisionType.DENY
            else:
                final_decision = DecisionType.ADJUDICATE
            
            final_reason = f"Weighted decision (Rules: {rules_weight}, AI: {ai_weight}, Score: {weighted_score})"
            metadata["decision_basis"] = "weighted_average"
        
        metadata["weighted_risk_score"] = weighted_score
        
        # Create combined risk score
        combined_risk_score = RiskScore(
            overall_score=weighted_score,
            driver_risk=rule_decision.risk_score.driver_risk,
            vehicle_risk=rule_decision.risk_score.vehicle_risk,
            history_risk=rule_decision.risk_score.history_risk,
            credit_risk=rule_decision.risk_score.credit_risk,
            factors=list(set(
                rule_decision.risk_score.factors + 
                ai_decision.risk_assessment.key_risk_factors
            ))
        )
        
        combined_decision = UnderwritingDecision(
            application_id=rule_decision.application_id,
            decision=final_decision,
            reason=final_reason,
            risk_score=combined_risk_score,
            rule_set=rule_decision.rule_set,
            triggered_rules=rule_decision.triggered_rules
        )
        
        return combined_decision, metadata
    
    def _combine_ai_override(
        self,
        rule_decision: UnderwritingDecision,
        ai_decision: AIUnderwritingDecision,
        metadata: Dict[str, Any]
    ) -> tuple[UnderwritingDecision, Dict[str, Any]]:
        """Allow AI to override rule decision under certain conditions."""
        config = self.ai_config.get("decision_combination", {}).get("override_rules", {})
        high_confidence_threshold = config.get("high_confidence_threshold", 0.9)
        allow_ai_override = config.get("allow_ai_override", False)
        
        metadata.update({
            "rule_decision": rule_decision.decision.value,
            "ai_decision": ai_decision.decision.value,
            "ai_confidence": ai_decision.risk_assessment.confidence_score,
            "override_allowed": allow_ai_override,
            "high_confidence_threshold": high_confidence_threshold
        })
        
        # Check if AI can override
        if (allow_ai_override and 
            ai_decision.risk_assessment.confidence_score >= high_confidence_threshold and
            ai_decision.decision != rule_decision.decision):
            
            metadata["override_applied"] = True
            metadata["override_reason"] = f"High AI confidence ({ai_decision.risk_assessment.confidence_score:.2f})"
            
            # Use AI decision
            combined_decision = UnderwritingDecision(
                application_id=rule_decision.application_id,
                decision=ai_decision.decision,
                reason=f"AI Override: {ai_decision.reasoning}",
                risk_score=self._convert_ai_risk_score(ai_decision.risk_assessment),
                rule_set=rule_decision.rule_set,
                triggered_rules=rule_decision.triggered_rules
            )
            
            return combined_decision, metadata
        else:
            metadata["override_applied"] = False
            return rule_decision, metadata
    
    def _combine_consensus_required(
        self,
        rule_decision: UnderwritingDecision,
        ai_decision: AIUnderwritingDecision,
        metadata: Dict[str, Any]
    ) -> tuple[UnderwritingDecision, Dict[str, Any]]:
        """Require consensus between rule and AI decisions."""
        metadata.update({
            "rule_decision": rule_decision.decision.value,
            "ai_decision": ai_decision.decision.value,
            "decisions_match": rule_decision.decision == ai_decision.decision
        })
        
        if rule_decision.decision == ai_decision.decision:
            # Consensus reached
            metadata["consensus_reached"] = True
            return rule_decision, metadata
        else:
            # No consensus, force adjudication
            metadata["consensus_reached"] = False
            metadata["forced_adjudication"] = True
            
            combined_decision = UnderwritingDecision(
                application_id=rule_decision.application_id,
                decision=DecisionType.ADJUDICATE,
                reason=f"No consensus: Rules={rule_decision.decision.value}, AI={ai_decision.decision.value}",
                risk_score=rule_decision.risk_score,
                rule_set=rule_decision.rule_set,
                triggered_rules=rule_decision.triggered_rules
            )
            
            return combined_decision, metadata
    
    def _convert_ai_risk_score(self, ai_risk: Any) -> RiskScore:
        """Convert AI risk assessment to RiskScore format."""
        return RiskScore(
            overall_score=ai_risk.overall_risk_score,
            driver_risk=ai_risk.overall_risk_score // 4,  # Approximate breakdown
            vehicle_risk=ai_risk.overall_risk_score // 4,
            history_risk=ai_risk.overall_risk_score // 4,
            credit_risk=ai_risk.overall_risk_score // 4,
            factors=ai_risk.key_risk_factors
        )
    
    def get_ai_service_health(self) -> Dict[str, Any]:
        """Get AI service health status."""
        if not self.ai_enabled or not self.ai_service:
            return {
                "ai_enabled": self.ai_enabled,
                "service_available": False,
                "status": "disabled"
            }
        
        health_info = self.ai_service.health_check()
        health_info["ai_enabled"] = self.ai_enabled
        return health_info
    
    def get_enhanced_statistics(
        self, 
        enhanced_decisions: List[EnhancedUnderwritingDecision]
    ) -> Dict[str, Any]:
        """Generate statistics from enhanced decisions."""
        if not enhanced_decisions:
            return {}
        
        # Basic statistics
        basic_stats = self.get_decision_statistics([ed.final_decision for ed in enhanced_decisions])
        
        # AI-specific statistics
        ai_decisions_count = sum(1 for ed in enhanced_decisions if ed.ai_decision is not None)
        ai_agreement_count = sum(
            1 for ed in enhanced_decisions 
            if ed.ai_decision and ed.rule_decision.decision == ed.ai_decision.decision
        )
        
        combination_strategies = {}
        for ed in enhanced_decisions:
            strategy = ed.combination_metadata.get("combination_strategy", "unknown")
            combination_strategies[strategy] = combination_strategies.get(strategy, 0) + 1
        
        ai_stats = {
            "ai_decisions_available": ai_decisions_count,
            "ai_coverage_percentage": ai_decisions_count / len(enhanced_decisions) * 100,
            "rule_ai_agreement_count": ai_agreement_count,
            "rule_ai_agreement_percentage": ai_agreement_count / ai_decisions_count * 100 if ai_decisions_count > 0 else 0,
            "combination_strategies_used": combination_strategies
        }
        
        basic_stats.update(ai_stats)
        return basic_stats
    
    # Rate limiting management methods
    
    def get_rate_limit_status(self, identifier: str, operation_type: str) -> Dict[str, Any]:
        """Get rate limit status for identifier and operation type.
        
        Args:
            identifier: Unique identifier
            operation_type: Operation type
            
        Returns:
            Rate limit status dictionary
        """
        if not self.rate_limiting_enabled or not self.rate_limiter:
            return {"error": "Rate limiting not enabled"}
        
        return self.rate_limiter.get_usage_status(identifier, operation_type)
    
    def get_all_rate_limit_status(self) -> Dict[str, Any]:
        """Get rate limit status for all identifiers and operation types.
        
        Returns:
            All rate limit status information
        """
        if not self.rate_limiting_enabled or not self.rate_limiter:
            return {"error": "Rate limiting not enabled"}
        
        return self.rate_limiter.get_all_usage_status()
    
    def generate_usage_analytics(self, operation_type: Optional[str] = None,
                                hours_back: int = 24) -> Dict[str, Any]:
        """Generate usage analytics report.
        
        Args:
            operation_type: Optional filter by operation type
            hours_back: Hours of history to analyze
            
        Returns:
            Usage analytics report
        """
        if not self.rate_limiting_enabled or not self.usage_analytics:
            return {"error": "Usage analytics not enabled"}
        
        return self.usage_analytics.get_usage_statistics(operation_type, hours_back)
    
    def generate_usage_report(self, report_type: str = "daily",
                             operation_type: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive usage report.
        
        Args:
            report_type: Type of report (daily, weekly, monthly)
            operation_type: Optional filter by operation type
            
        Returns:
            Usage report
        """
        if not self.rate_limiting_enabled or not self.usage_analytics:
            return {"error": "Usage analytics not enabled"}
        
        return self.usage_analytics.generate_usage_report(report_type, operation_type)
    
    def request_admin_override(self, identifier: str, operation_type: str,
                              justification: str, duration_hours: int = 24,
                              admin_user: str = "admin") -> bool:
        """Request admin override for rate limiting.
        
        Args:
            identifier: Unique identifier
            operation_type: Operation type
            justification: Justification for override
            duration_hours: Duration in hours
            admin_user: Admin user requesting override
            
        Returns:
            True if override granted, False otherwise
        """
        if not self.rate_limiting_enabled or not self.admin_override:
            return False
        
        from ..rate_limiting.admin import AdminOverrideRequest
        
        request = AdminOverrideRequest(
            identifier=identifier,
            operation_type=operation_type,
            justification=justification,
            duration_hours=duration_hours,
            requested_by=admin_user
        )
        
        return self.admin_override.request_override(request)
    
    def revoke_admin_override(self, identifier: str, operation_type: str,
                             admin_user: str = "admin") -> bool:
        """Revoke admin override.
        
        Args:
            identifier: Unique identifier
            operation_type: Operation type
            admin_user: Admin user performing action
            
        Returns:
            True if successfully revoked, False otherwise
        """
        if not self.rate_limiting_enabled or not self.admin_override:
            return False
        
        return self.admin_override.revoke_override(identifier, operation_type, admin_user)
    
    def get_admin_override_status(self, identifier: Optional[str] = None,
                                 operation_type: Optional[str] = None) -> Dict[str, Any]:
        """Get admin override status.
        
        Args:
            identifier: Optional specific identifier
            operation_type: Optional specific operation type
            
        Returns:
            Override status information
        """
        if not self.rate_limiting_enabled or not self.admin_override:
            return {"error": "Admin override not enabled"}
        
        return self.admin_override.get_override_status(identifier, operation_type)
    
    def cleanup_rate_limiting_data(self) -> Dict[str, int]:
        """Cleanup old rate limiting data.
        
        Returns:
            Cleanup statistics
        """
        if not self.rate_limiting_enabled:
            return {"error": "Rate limiting not enabled"}
        
        cleanup_stats = {}
        
        if self.rate_limiter:
            cleanup_stats["usage_records"] = self.rate_limiter.storage.cleanup_old_data()
            self.rate_limiter.storage.backup_data()
        
        if self.usage_analytics:
            cleanup_stats["analytics_records"] = self.usage_analytics.cleanup_old_analytics()
        
        if self.admin_override:
            cleanup_stats["expired_overrides"] = self.admin_override.cleanup_expired_overrides()
        
        return cleanup_stats
    
    def reload_rate_limiting_config(self) -> bool:
        """Reload rate limiting configuration.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.rate_limiting_enabled or not self.rate_limiter:
            return False
        
        return self.rate_limiter.reload_config()