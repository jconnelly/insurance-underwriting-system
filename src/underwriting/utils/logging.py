"""
Logging configuration and utilities for the underwriting system.

This module provides centralized logging setup with structured logging,
configurable levels, and file output options.
"""

import sys
from pathlib import Path
from typing import Optional, Union

from loguru import logger


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    rotation: str = "10 MB",
    retention: str = "30 days",
    format_string: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
) -> None:
    """Set up structured logging for the underwriting system.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Path to log file. If None, uses default location.
        rotation: Log file rotation policy.
        retention: Log file retention policy.
        format_string: Custom log format string.
        enable_console: Whether to enable console logging.
        enable_file: Whether to enable file logging.
    """
    # Remove default handler
    logger.remove()
    
    # Default format with structured information
    if format_string is None:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # Console handler
    if enable_console:
        logger.add(
            sys.stdout,
            format=format_string,
            level=level,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
    
    # File handler
    if enable_file:
        if log_file is None:
            log_file = Path("logs/underwriting.log")
        
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format=format_string,
            level=level,
            rotation=rotation,
            retention=retention,
            backtrace=True,
            diagnose=True,
            serialize=False,
        )
    
    # Log startup message
    logger.info("Logging initialized")
    logger.info(f"Log level: {level}")
    if enable_file:
        logger.info(f"Log file: {log_file}")


def get_logger(name: str) -> "logger":
    """Get a logger instance with the specified name.
    
    Args:
        name: Name for the logger (usually __name__).
        
    Returns:
        Logger instance.
    """
    return logger.bind(name=name)


def log_application_processing(application_id: str, rule_set: str, decision: str) -> None:
    """Log application processing with structured data.
    
    Args:
        application_id: ID of the application being processed.
        rule_set: Name of the rule set used.
        decision: Final decision (ACCEPT, DENY, ADJUDICATE).
    """
    logger.info(
        "Application processed",
        extra={
            "application_id": application_id,
            "rule_set": rule_set,
            "decision": decision,
            "event_type": "application_processed"
        }
    )


def log_rule_triggered(rule_id: str, rule_name: str, application_id: str) -> None:
    """Log when a rule is triggered during evaluation.
    
    Args:
        rule_id: ID of the triggered rule.
        rule_name: Name of the triggered rule.
        application_id: ID of the application being processed.
    """
    logger.info(
        "Rule triggered",
        extra={
            "rule_id": rule_id,
            "rule_name": rule_name,
            "application_id": application_id,
            "event_type": "rule_triggered"
        }
    )


def log_risk_score_calculated(application_id: str, overall_score: int, components: dict) -> None:
    """Log risk score calculation results.
    
    Args:
        application_id: ID of the application.
        overall_score: Overall risk score.
        components: Dictionary of risk score components.
    """
    logger.info(
        "Risk score calculated",
        extra={
            "application_id": application_id,
            "overall_score": overall_score,
            "components": components,
            "event_type": "risk_score_calculated"
        }
    )


def log_batch_processing(total_applications: int, successful: int, failed: int) -> None:
    """Log batch processing results.
    
    Args:
        total_applications: Total number of applications processed.
        successful: Number of successful applications.
        failed: Number of failed applications.
    """
    logger.info(
        "Batch processing completed",
        extra={
            "total_applications": total_applications,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_applications * 100 if total_applications > 0 else 0,
            "event_type": "batch_processing_completed"
        }
    )


def log_configuration_loaded(rule_set_name: str, version: str, rules_count: int) -> None:
    """Log configuration loading.
    
    Args:
        rule_set_name: Name of the rule set.
        version: Version of the rule set.
        rules_count: Total number of rules loaded.
    """
    logger.info(
        "Configuration loaded",
        extra={
            "rule_set_name": rule_set_name,
            "version": version,
            "rules_count": rules_count,
            "event_type": "configuration_loaded"
        }
    )


def log_validation_error(application_id: str, error_type: str, error_message: str) -> None:
    """Log validation errors.
    
    Args:
        application_id: ID of the application with validation errors.
        error_type: Type of validation error.
        error_message: Detailed error message.
    """
    logger.error(
        "Validation error",
        extra={
            "application_id": application_id,
            "error_type": error_type,
            "error_message": error_message,
            "event_type": "validation_error"
        }
    )


def log_performance_metrics(operation: str, duration_ms: float, **kwargs) -> None:
    """Log performance metrics.
    
    Args:
        operation: Name of the operation being measured.
        duration_ms: Duration in milliseconds.
        **kwargs: Additional metrics to log.
    """
    logger.info(
        "Performance metrics",
        extra={
            "operation": operation,
            "duration_ms": duration_ms,
            "event_type": "performance_metrics",
            **kwargs
        }
    )


class LoggingContext:
    """Context manager for adding structured logging context."""
    
    def __init__(self, **context):
        """Initialize logging context.
        
        Args:
            **context: Key-value pairs to add to log context.
        """
        self.context = context
        self.token = None
    
    def __enter__(self):
        """Enter logging context."""
        self.token = logger.contextualize(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit logging context."""
        if self.token:
            self.token.__exit__(exc_type, exc_val, exc_tb)