"""
Main rate limiter implementation with configurable limits and time windows.

This module provides the core rate limiting functionality including:
- Multiple time window support (daily, weekly, monthly, burst)
- Configurable limits per operation type
- Graceful degradation when limits are exceeded
- Integration with file-based storage
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from .storage import RateLimitStorage


class RateLimitResult(Enum):
    """Rate limit check results."""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    OVERRIDE_ACTIVE = "override_active"
    LIMIT_DISABLED = "limit_disabled"


@dataclass
class RateLimitConfig:
    """Configuration for a specific rate limit."""
    enabled: bool = True
    daily_limit: int = 1000
    weekly_limit: int = 5000
    monthly_limit: int = 20000
    burst_limit: int = 100
    burst_window_minutes: int = 60
    max_batch_size: Optional[int] = None
    description: str = ""


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str, limit_type: str, current_usage: int, 
                 limit_value: int, reset_time: float):
        super().__init__(message)
        self.limit_type = limit_type
        self.current_usage = current_usage
        self.limit_value = limit_value
        self.reset_time = reset_time
        self.reset_datetime = datetime.fromtimestamp(reset_time)


class RateLimiter:
    """Main rate limiter with configurable limits and time windows."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize rate limiter.
        
        Args:
            config_path: Path to rate limits configuration file
        """
        self.config_path = config_path or "src/underwriting/config/rate_limits.json"
        self.config = self._load_config()
        
        # Initialize storage
        storage_config = self.config.get("storage", {})
        self.storage = RateLimitStorage(storage_config)
        
        # Parse rate limit configurations
        self.rate_limits = self._parse_rate_limits()
        
        # Admin and graceful degradation settings
        self.admin_config = self.config.get("admin", {})
        self.degradation_config = self.config.get("graceful_degradation", {})
        
        logger.info(f"Rate limiter initialized with {len(self.rate_limits)} operation types")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load rate limits configuration from file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"Rate limits config not found at {self.config_path}, using defaults")
                return self._get_default_config()
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            logger.info(f"Rate limits configuration loaded from {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load rate limits config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default rate limits configuration."""
        return {
            "rate_limits": {
                "default": {
                    "enabled": True,
                    "daily_limit": 1000,
                    "weekly_limit": 5000,
                    "monthly_limit": 20000,
                    "burst_limit": 100,
                    "burst_window_minutes": 60,
                    "description": "Default rate limits"
                }
            },
            "storage": {
                "data_directory": "rate_limit_data",
                "cleanup_interval_hours": 24,
                "retention_days": 90
            },
            "admin": {
                "override_enabled": True,
                "override_expiry_hours": 24
            },
            "graceful_degradation": {
                "enabled": True,
                "fallback_to_rules_only": True
            }
        }
    
    def _parse_rate_limits(self) -> Dict[str, RateLimitConfig]:
        """Parse rate limit configurations from config."""
        rate_limits = {}
        
        for operation_type, config in self.config.get("rate_limits", {}).items():
            rate_limits[operation_type] = RateLimitConfig(
                enabled=config.get("enabled", True),
                daily_limit=config.get("daily_limit", 1000),
                weekly_limit=config.get("weekly_limit", 5000),
                monthly_limit=config.get("monthly_limit", 20000),
                burst_limit=config.get("burst_limit", 100),
                burst_window_minutes=config.get("burst_window_minutes", 60),
                max_batch_size=config.get("max_batch_size"),
                description=config.get("description", "")
            )
        
        return rate_limits
    
    def check_rate_limit(self, identifier: str, operation_type: str, 
                        resource_amount: int = 1) -> Tuple[RateLimitResult, Optional[str]]:
        """Check if request is within rate limits.
        
        Args:
            identifier: Unique identifier (e.g., user ID, IP address)
            operation_type: Type of operation being rate limited
            resource_amount: Amount of resource being consumed
            
        Returns:
            Tuple of (result, error_message)
        """
        try:
            # Get rate limit config for operation type
            limit_config = self.rate_limits.get(operation_type)
            if not limit_config:
                # Use default config if operation type not found
                limit_config = self.rate_limits.get("default")
                if not limit_config:
                    return RateLimitResult.ALLOWED, None
            
            # Check if rate limiting is disabled for this operation
            if not limit_config.enabled:
                return RateLimitResult.LIMIT_DISABLED, None
            
            # Check for admin override
            if self._check_admin_override(identifier, operation_type):
                return RateLimitResult.OVERRIDE_ACTIVE, None
            
            # Get current usage data
            current_time = time.time()
            
            # Check burst limit
            burst_result, burst_error = self._check_burst_limit(
                identifier, operation_type, resource_amount, limit_config, current_time
            )
            if burst_result != RateLimitResult.ALLOWED:
                return burst_result, burst_error
            
            # Check daily limit
            daily_result, daily_error = self._check_daily_limit(
                identifier, operation_type, resource_amount, limit_config, current_time
            )
            if daily_result != RateLimitResult.ALLOWED:
                return daily_result, daily_error
            
            # Check weekly limit
            weekly_result, weekly_error = self._check_weekly_limit(
                identifier, operation_type, resource_amount, limit_config, current_time
            )
            if weekly_result != RateLimitResult.ALLOWED:
                return weekly_result, weekly_error
            
            # Check monthly limit
            monthly_result, monthly_error = self._check_monthly_limit(
                identifier, operation_type, resource_amount, limit_config, current_time
            )
            if monthly_result != RateLimitResult.ALLOWED:
                return monthly_result, monthly_error
            
            return RateLimitResult.ALLOWED, None
            
        except Exception as e:
            logger.error(f"Error checking rate limit for {identifier}:{operation_type}: {e}")
            # In case of error, allow request but log the issue
            return RateLimitResult.ALLOWED, None
    
    def consume_rate_limit(self, identifier: str, operation_type: str, 
                          resource_amount: int = 1, user_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Consume rate limit if allowed.
        
        Args:
            identifier: Unique identifier
            operation_type: Type of operation
            resource_amount: Amount of resource being consumed
            user_id: Optional user identifier
            metadata: Optional metadata
            
        Returns:
            True if consumed successfully, False if rate limited
        """
        try:
            # Check rate limit
            result, error_message = self.check_rate_limit(identifier, operation_type, resource_amount)
            
            if result == RateLimitResult.BLOCKED:
                # Record the block
                self.storage.record_block(identifier, operation_type)
                logger.warning(f"Rate limit exceeded for {identifier}:{operation_type}: {error_message}")
                
                # Handle graceful degradation
                if self._should_degrade_gracefully(operation_type):
                    logger.info(f"Graceful degradation triggered for {identifier}:{operation_type}")
                    return False
                
                # Raise exception for hard limits
                raise RateLimitExceeded(
                    error_message, 
                    operation_type, 
                    0,  # Current usage would need to be calculated
                    0,  # Limit value would need to be calculated
                    time.time() + 3600  # Reset time estimate
                )
            
            # Record successful usage
            self.storage.record_usage(
                identifier, operation_type, user_id, resource_amount, metadata
            )
            
            # Trigger cleanup if needed
            self.storage.cleanup_old_data()
            self.storage.backup_data()
            
            return True
            
        except RateLimitExceeded:
            raise
        except Exception as e:
            logger.error(f"Error consuming rate limit for {identifier}:{operation_type}: {e}")
            return False
    
    def _check_burst_limit(self, identifier: str, operation_type: str, 
                          resource_amount: int, limit_config: RateLimitConfig, 
                          current_time: float) -> Tuple[RateLimitResult, Optional[str]]:
        """Check burst rate limit."""
        window_start = current_time - (limit_config.burst_window_minutes * 60)
        current_usage = self.storage.get_total_usage_in_window(
            identifier, operation_type, window_start, current_time
        )
        
        if current_usage + resource_amount > limit_config.burst_limit:
            reset_time = current_time + (limit_config.burst_window_minutes * 60)
            error_msg = (
                f"Burst limit exceeded for {operation_type}. "
                f"Current: {current_usage}, Limit: {limit_config.burst_limit}, "
                f"Reset: {datetime.fromtimestamp(reset_time)}"
            )
            return RateLimitResult.BLOCKED, error_msg
        
        return RateLimitResult.ALLOWED, None
    
    def _check_daily_limit(self, identifier: str, operation_type: str, 
                          resource_amount: int, limit_config: RateLimitConfig, 
                          current_time: float) -> Tuple[RateLimitResult, Optional[str]]:
        """Check daily rate limit."""
        # Get start of today
        today = datetime.fromtimestamp(current_time).replace(hour=0, minute=0, second=0, microsecond=0)
        window_start = today.timestamp()
        
        current_usage = self.storage.get_total_usage_in_window(
            identifier, operation_type, window_start, current_time
        )
        
        if current_usage + resource_amount > limit_config.daily_limit:
            # Reset time is start of next day
            tomorrow = today + timedelta(days=1)
            reset_time = tomorrow.timestamp()
            
            error_msg = (
                f"Daily limit exceeded for {operation_type}. "
                f"Current: {current_usage}, Limit: {limit_config.daily_limit}, "
                f"Reset: {datetime.fromtimestamp(reset_time)}"
            )
            return RateLimitResult.BLOCKED, error_msg
        
        return RateLimitResult.ALLOWED, None
    
    def _check_weekly_limit(self, identifier: str, operation_type: str, 
                           resource_amount: int, limit_config: RateLimitConfig, 
                           current_time: float) -> Tuple[RateLimitResult, Optional[str]]:
        """Check weekly rate limit."""
        # Get start of this week (Monday)
        current_date = datetime.fromtimestamp(current_time)
        days_since_monday = current_date.weekday()
        week_start = current_date - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        window_start = week_start.timestamp()
        
        current_usage = self.storage.get_total_usage_in_window(
            identifier, operation_type, window_start, current_time
        )
        
        if current_usage + resource_amount > limit_config.weekly_limit:
            # Reset time is start of next week
            next_week = week_start + timedelta(weeks=1)
            reset_time = next_week.timestamp()
            
            error_msg = (
                f"Weekly limit exceeded for {operation_type}. "
                f"Current: {current_usage}, Limit: {limit_config.weekly_limit}, "
                f"Reset: {datetime.fromtimestamp(reset_time)}"
            )
            return RateLimitResult.BLOCKED, error_msg
        
        return RateLimitResult.ALLOWED, None
    
    def _check_monthly_limit(self, identifier: str, operation_type: str, 
                            resource_amount: int, limit_config: RateLimitConfig, 
                            current_time: float) -> Tuple[RateLimitResult, Optional[str]]:
        """Check monthly rate limit."""
        # Get start of this month
        current_date = datetime.fromtimestamp(current_time)
        month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        window_start = month_start.timestamp()
        
        current_usage = self.storage.get_total_usage_in_window(
            identifier, operation_type, window_start, current_time
        )
        
        if current_usage + resource_amount > limit_config.monthly_limit:
            # Reset time is start of next month
            if month_start.month == 12:
                next_month = month_start.replace(year=month_start.year + 1, month=1)
            else:
                next_month = month_start.replace(month=month_start.month + 1)
            reset_time = next_month.timestamp()
            
            error_msg = (
                f"Monthly limit exceeded for {operation_type}. "
                f"Current: {current_usage}, Limit: {limit_config.monthly_limit}, "
                f"Reset: {datetime.fromtimestamp(reset_time)}"
            )
            return RateLimitResult.BLOCKED, error_msg
        
        return RateLimitResult.ALLOWED, None
    
    def _check_admin_override(self, identifier: str, operation_type: str) -> bool:
        """Check if admin override is active for identifier."""
        if not self.admin_config.get("override_enabled", True):
            return False
        
        try:
            entry = self.storage.get_usage_data(identifier, operation_type)
            if entry and entry.override_active:
                # Check if override has expired
                if entry.override_expiry and time.time() > entry.override_expiry:
                    # Override expired, remove it
                    entry.override_active = False
                    entry.override_expiry = None
                    self.storage.save_usage_data(entry)
                    return False
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking admin override: {e}")
            return False
    
    def _should_degrade_gracefully(self, operation_type: str) -> bool:
        """Check if graceful degradation should be applied."""
        if not self.degradation_config.get("enabled", True):
            return False
        
        # Check if this operation type supports graceful degradation
        if operation_type in ["ai_evaluations"] and self.degradation_config.get("fallback_to_rules_only", True):
            return True
        
        return False
    
    def get_usage_status(self, identifier: str, operation_type: str) -> Dict[str, Any]:
        """Get current usage status for identifier and operation type.
        
        Args:
            identifier: Unique identifier
            operation_type: Type of operation
            
        Returns:
            Dictionary containing usage status
        """
        try:
            limit_config = self.rate_limits.get(operation_type, self.rate_limits.get("default"))
            if not limit_config:
                return {"error": "No rate limit configuration found"}
            
            current_time = time.time()
            
            # Calculate usage for different time windows
            # Burst window
            burst_start = current_time - (limit_config.burst_window_minutes * 60)
            burst_usage = self.storage.get_total_usage_in_window(
                identifier, operation_type, burst_start, current_time
            )
            
            # Daily window
            today = datetime.fromtimestamp(current_time).replace(hour=0, minute=0, second=0, microsecond=0)
            daily_usage = self.storage.get_total_usage_in_window(
                identifier, operation_type, today.timestamp(), current_time
            )
            
            # Weekly window
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
            weekly_usage = self.storage.get_total_usage_in_window(
                identifier, operation_type, week_start.timestamp(), current_time
            )
            
            # Monthly window
            month_start = today.replace(day=1)
            monthly_usage = self.storage.get_total_usage_in_window(
                identifier, operation_type, month_start.timestamp(), current_time
            )
            
            # Get entry for additional info
            entry = self.storage.get_usage_data(identifier, operation_type)
            
            return {
                "identifier": identifier,
                "operation_type": operation_type,
                "enabled": limit_config.enabled,
                "burst": {
                    "usage": burst_usage,
                    "limit": limit_config.burst_limit,
                    "remaining": max(0, limit_config.burst_limit - burst_usage),
                    "window_minutes": limit_config.burst_window_minutes
                },
                "daily": {
                    "usage": daily_usage,
                    "limit": limit_config.daily_limit,
                    "remaining": max(0, limit_config.daily_limit - daily_usage),
                    "reset_time": (today + timedelta(days=1)).timestamp()
                },
                "weekly": {
                    "usage": weekly_usage,
                    "limit": limit_config.weekly_limit,
                    "remaining": max(0, limit_config.weekly_limit - weekly_usage),
                    "reset_time": (week_start + timedelta(weeks=1)).timestamp()
                },
                "monthly": {
                    "usage": monthly_usage,
                    "limit": limit_config.monthly_limit,
                    "remaining": max(0, limit_config.monthly_limit - monthly_usage),
                    "reset_time": (month_start + timedelta(days=32)).replace(day=1).timestamp()
                },
                "total_blocked": entry.blocked_count if entry else 0,
                "override_active": entry.override_active if entry else False,
                "override_expiry": entry.override_expiry if entry else None
            }
            
        except Exception as e:
            logger.error(f"Error getting usage status: {e}")
            return {"error": str(e)}
    
    def get_all_usage_status(self) -> Dict[str, Any]:
        """Get usage status for all identifiers and operation types.
        
        Returns:
            Dictionary containing all usage status information
        """
        try:
            all_identifiers = self.storage.get_all_identifiers()
            status = {}
            
            for identifier, operation_type in all_identifiers:
                key = f"{identifier}:{operation_type}"
                status[key] = self.get_usage_status(identifier, operation_type)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting all usage status: {e}")
            return {"error": str(e)}
    
    def reload_config(self) -> bool:
        """Reload configuration from file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.config = self._load_config()
            self.rate_limits = self._parse_rate_limits()
            self.admin_config = self.config.get("admin", {})
            self.degradation_config = self.config.get("graceful_degradation", {})
            
            logger.info("Rate limiter configuration reloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False