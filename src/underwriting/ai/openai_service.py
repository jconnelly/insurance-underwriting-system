"""
OpenAI GPT-4 service implementation for AI underwriting.

This module provides OpenAI integration with robust error handling,
rate limiting, and response validation.
"""

import asyncio
import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

import openai
from openai import AsyncOpenAI
from loguru import logger

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .base import (
    AIServiceInterface, 
    AIUnderwritingDecision, 
    AIProviderType,
    AIServiceError,
    AIServiceUnavailableError,
    AIRateLimitError,
    AIInvalidResponseError,
    AIConfigurationError
)
from .response_parser import AIResponseParser
from .prompts import PromptManager, ConservativePrompts, StandardPrompts, LiberalPrompts
from .langsmith_tracing import get_tracer, trace_ai_evaluation, trace_batch_evaluation
from ..core.models import Application


class OpenAIService(AIServiceInterface):
    """OpenAI GPT-4 service for underwriting decisions."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI service.
        
        Args:
            config: Configuration containing OpenAI settings
        """
        super().__init__(config)
        
        # Extract OpenAI configuration
        self.openai_config = config.get("openai", {})
        self.api_key = self._get_api_key()
        self.model = self.openai_config.get("model", "gpt-4-turbo")
        self.max_tokens = self.openai_config.get("max_tokens", 2000)
        self.temperature = self.openai_config.get("temperature", 0.1)
        self.timeout = self.openai_config.get("timeout", 30)
        self.retry_attempts = self.openai_config.get("retry_attempts", 3)
        self.retry_delay = self.openai_config.get("retry_delay", 1.0)
        
        # Rate limiting
        self.rate_limit_config = self.openai_config.get("rate_limit", {})
        self.requests_per_minute = self.rate_limit_config.get("requests_per_minute", 60)
        self.tokens_per_minute = self.rate_limit_config.get("tokens_per_minute", 150000)
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key, timeout=self.timeout)
        
        # Initialize response parser and prompt manager
        self.response_parser = AIResponseParser(self.provider_type, self.model)
        self.prompt_manager = PromptManager()
        self._setup_prompt_templates()
        
        # Initialize LangSmith tracing
        langsmith_config = config.get("langsmith", {})
        self.langsmith_tracer = get_tracer(langsmith_config)
        self.tracing_enabled = langsmith_config.get("enabled", True)
        
        # Rate limiting state
        self._request_timestamps: List[datetime] = []
        self._token_usage: List[tuple[datetime, int]] = []
        
        # Detailed token usage tracking
        self._detailed_token_usage: List[Dict[str, Any]] = []
        
        # Token pricing (per 1K tokens for GPT-4 Turbo)
        self.token_pricing = {
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
        }
        
        logger.info(f"Initialized OpenAI service with model {self.model} (LangSmith: {'enabled' if self.tracing_enabled else 'disabled'})")
    
    def _get_provider_type(self) -> AIProviderType:
        """Return OpenAI provider type."""
        return AIProviderType.OPENAI
    
    def _get_api_key(self) -> str:
        """Get OpenAI API key from config or environment."""
        api_key = self.openai_config.get("api_key")
        
        # Handle environment variable substitution
        if api_key and api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            api_key = os.getenv(env_var)
        
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise AIConfigurationError(
                "OpenAI API key not found in config or environment",
                self.provider_type,
                "MISSING_API_KEY"
            )
        
        return api_key
    
    def _setup_prompt_templates(self):
        """Set up prompt templates for different rule sets."""
        self.prompt_manager.register_template("conservative", ConservativePrompts("conservative"))
        self.prompt_manager.register_template("standard", StandardPrompts("standard"))
        self.prompt_manager.register_template("liberal", LiberalPrompts("liberal"))
    
    @trace_ai_evaluation(
        name="openai_evaluate_application",
        metadata={"provider": "openai", "model": "gpt-4-turbo"},
        tags=["evaluation", "single_application"]
    )
    async def evaluate_application(
        self, 
        application: Application,
        rule_set: str = "standard",
        context: Optional[Dict[str, Any]] = None
    ) -> AIUnderwritingDecision:
        """Evaluate application using OpenAI GPT-4.
        
        Args:
            application: Application to evaluate
            rule_set: Rule set to use (conservative, standard, liberal)
            context: Additional context
            
        Returns:
            AI underwriting decision
        """
        try:
            # Check rate limits
            await self._check_rate_limits()
            
            # Generate prompts
            system_prompt, user_prompt = self.prompt_manager.generate_prompt(
                rule_set, application, context
            )
            
            # Make API call with retries
            raw_response = await self._make_api_call_with_retry(
                system_prompt, user_prompt
            )
            
            # Parse response
            decision = self.response_parser.parse_decision(raw_response, str(application.id))
            
            logger.info(f"OpenAI evaluation completed for application {application.id}")
            return decision
            
        except Exception as e:
            logger.error(f"OpenAI evaluation failed for application {application.id}: {e}")
            if isinstance(e, AIServiceError):
                raise
            else:
                raise AIServiceError(
                    f"Unexpected error during OpenAI evaluation: {str(e)}",
                    self.provider_type,
                    "UNEXPECTED_ERROR"
                )
    
    @trace_batch_evaluation(
        name="openai_batch_evaluate_applications",
        metadata={"provider": "openai", "model": "gpt-4-turbo"},
        tags=["evaluation", "batch_processing"]
    )
    async def batch_evaluate_applications(
        self,
        applications: List[Application],
        rule_set: str = "standard",
        context: Optional[Dict[str, Any]] = None
    ) -> List[AIUnderwritingDecision]:
        """Evaluate multiple applications in batch.
        
        Args:
            applications: Applications to evaluate
            rule_set: Rule set to use
            context: Additional context
            
        Returns:
            List of AI decisions
        """
        logger.info(f"Starting batch evaluation of {len(applications)} applications")
        
        # Create tasks for concurrent processing
        tasks = []
        for app in applications:
            task = self.evaluate_application(app, rule_set, context)
            tasks.append(task)
        
        # Execute with concurrency control
        max_concurrent = self.config.get("performance", {}).get("max_concurrent_requests", 5)
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_evaluate(task):
            async with semaphore:
                return await task
        
        # Process all applications
        results = []
        for i in range(0, len(tasks), max_concurrent):
            batch = tasks[i:i + max_concurrent]
            batch_results = await asyncio.gather(*[limited_evaluate(task) for task in batch], return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch evaluation error: {result}")
                    # Could add fallback decision here
                else:
                    results.append(result)
        
        logger.info(f"Completed batch evaluation: {len(results)}/{len(applications)} successful")
        return results
    
    async def _make_api_call_with_retry(self, system_prompt: str, user_prompt: str) -> str:
        """Make OpenAI API call with retry logic."""
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    timeout=self.timeout
                )
                
                # Track detailed token usage 
                if response.usage:
                    self._track_detailed_token_usage(response.usage)
                    self._track_token_usage(response.usage.total_tokens)
                
                # Track request for rate limiting
                self._track_request()
                
                return response.choices[0].message.content
                
            except openai.RateLimitError as e:
                last_exception = e
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}")
                await asyncio.sleep(wait_time)
                
            except openai.APITimeoutError as e:
                last_exception = e
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"API timeout, retrying in {wait_time}s (attempt {attempt + 1})")
                await asyncio.sleep(wait_time)
                
            except openai.APIError as e:
                last_exception = e
                if e.status_code >= 500:  # Server errors are retryable
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Server error {e.status_code}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    # Client errors are not retryable
                    break
        
        # All retries failed
        if isinstance(last_exception, openai.RateLimitError):
            raise AIRateLimitError(
                "OpenAI rate limit exceeded after retries",
                self.provider_type,
                "RATE_LIMIT_EXCEEDED"
            )
        elif isinstance(last_exception, openai.APITimeoutError):
            raise AIServiceUnavailableError(
                "OpenAI API timeout after retries",
                self.provider_type,
                "API_TIMEOUT"
            )
        else:
            raise AIServiceError(
                f"OpenAI API call failed: {str(last_exception)}",
                self.provider_type,
                "API_ERROR"
            )
    
    async def _check_rate_limits(self):
        """Check and enforce rate limits."""
        now = datetime.now()
        
        # Clean old timestamps
        cutoff = now - timedelta(minutes=1)
        self._request_timestamps = [ts for ts in self._request_timestamps if ts > cutoff]
        self._token_usage = [(ts, tokens) for ts, tokens in self._token_usage if ts > cutoff]
        
        # Check request rate limit
        if len(self._request_timestamps) >= self.requests_per_minute:
            wait_time = 60 - (now - self._request_timestamps[0]).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        # Check token rate limit
        total_tokens = sum(tokens for _, tokens in self._token_usage)
        if total_tokens >= self.tokens_per_minute:
            wait_time = 60 - (now - self._token_usage[0][0]).total_seconds()
            if wait_time > 0:
                logger.info(f"Token limit: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
    
    def _track_request(self):
        """Track API request for rate limiting."""
        self._request_timestamps.append(datetime.now())
    
    def _track_token_usage(self, tokens: int):
        """Track token usage for rate limiting."""
        self._token_usage.append((datetime.now(), tokens))
    
    def _track_detailed_token_usage(self, usage):
        """Track detailed token usage with cost estimation."""
        now = datetime.now()
        
        # Calculate cost based on model pricing
        model_pricing = self.token_pricing.get(self.model, self.token_pricing["gpt-4-turbo"])
        input_cost = (usage.prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (usage.completion_tokens / 1000) * model_pricing["output"]
        total_cost = input_cost + output_cost
        
        usage_record = {
            "timestamp": now.isoformat(),
            "model": self.model,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(total_cost, 6)
        }
        
        self._detailed_token_usage.append(usage_record)
        
        # Keep only last 1000 records to prevent memory issues
        if len(self._detailed_token_usage) > 1000:
            self._detailed_token_usage = self._detailed_token_usage[-1000:]
        
        logger.info(f"Token usage: {usage.total_tokens} tokens (${total_cost:.6f} USD) - Input: {usage.prompt_tokens}, Output: {usage.completion_tokens}")
    
    def get_token_usage_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get token usage summary for the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_usage = [
            record for record in self._detailed_token_usage
            if datetime.fromisoformat(record["timestamp"]) > cutoff
        ]
        
        if not recent_usage:
            return {
                "time_period_hours": hours,
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost_usd": 0,
                "average_tokens_per_request": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "model": self.model,
                "recent_usage": []
            }
        
        total_tokens = sum(record["total_tokens"] for record in recent_usage)
        total_cost = sum(record["total_cost_usd"] for record in recent_usage)
        prompt_tokens = sum(record["prompt_tokens"] for record in recent_usage)
        completion_tokens = sum(record["completion_tokens"] for record in recent_usage)
        
        return {
            "time_period_hours": hours,
            "total_requests": len(recent_usage),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "average_tokens_per_request": round(total_tokens / len(recent_usage), 1),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "model": self.model,
            "recent_usage": recent_usage[-10:]  # Last 10 requests
        }
    
    def validate_configuration(self) -> bool:
        """Validate OpenAI service configuration."""
        try:
            # Check API key
            if not self.api_key:
                logger.error("OpenAI API key not configured")
                return False
            
            # Check required config values
            required_config = ["model", "max_tokens", "temperature"]
            for key in required_config:
                if key not in self.openai_config:
                    logger.error(f"Missing OpenAI config: {key}")
                    return False
            
            # Validate model name
            valid_models = ["gpt-4", "gpt-4-turbo", "gpt-4-turbo-preview", "gpt-3.5-turbo"]
            if self.model not in valid_models:
                logger.warning(f"Unrecognized model: {self.model}")
            
            # Validate ranges
            if not (0.0 <= self.temperature <= 2.0):
                logger.error(f"Invalid temperature: {self.temperature}")
                return False
            
            if not (1 <= self.max_tokens <= 4096):
                logger.error(f"Invalid max_tokens: {self.max_tokens}")
                return False
            
            logger.info("OpenAI configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"OpenAI configuration validation failed: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check OpenAI service health."""
        health_info = {
            "service": "OpenAI",
            "provider": self.provider_type.value,
            "model": self.model,
            "status": "unknown",
            "timestamp": datetime.now().isoformat(),
            "configuration_valid": False,
            "api_accessible": False,
            "rate_limit_status": self._get_rate_limit_status()
        }
        
        try:
            # Check configuration
            health_info["configuration_valid"] = self.validate_configuration()
            
            # Test API accessibility (sync call for health check)
            import openai as sync_openai
            sync_client = sync_openai.OpenAI(api_key=self.api_key, timeout=5)
            
            # Simple test call
            response = sync_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=1,
                temperature=0
            )
            
            health_info["api_accessible"] = True
            health_info["status"] = "healthy"
            
        except Exception as e:
            health_info["status"] = "unhealthy"
            health_info["error"] = str(e)
            logger.warning(f"OpenAI health check failed: {e}")
        
        return health_info
    
    def _get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        recent_requests = len([ts for ts in self._request_timestamps if ts > cutoff])
        recent_tokens = sum(tokens for ts, tokens in self._token_usage if ts > cutoff)
        
        return {
            "requests_used": recent_requests,
            "requests_limit": self.requests_per_minute,
            "tokens_used": recent_tokens,
            "tokens_limit": self.tokens_per_minute,
            "requests_remaining": max(0, self.requests_per_minute - recent_requests),
            "tokens_remaining": max(0, self.tokens_per_minute - recent_tokens)
        }