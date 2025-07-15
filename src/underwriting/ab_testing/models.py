"""
Shared models for A/B testing framework.

This module contains shared data models and enums used across the A/B testing framework.
"""

import uuid
from datetime import datetime
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum

from ..core.models import UnderwritingDecision


class ABTestStatus(Enum):
    """A/B test status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ABTestVariant(Enum):
    """A/B test variant enumeration."""
    CONTROL = "control"
    TREATMENT = "treatment"


@dataclass
class ABTestResult:
    """Result of an A/B test evaluation."""
    test_id: str
    variant: ABTestVariant
    application_id: str
    decision: UnderwritingDecision
    processing_time: float
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ABTestConfiguration:
    """Configuration for an A/B test."""
    test_id: str
    name: str
    description: str
    control_config: Dict[str, Any]
    treatment_config: Dict[str, Any]
    sample_size: int
    confidence_level: float = 0.95
    minimum_effect_size: float = 0.05
    test_duration_hours: int = None
    traffic_allocation: float = 0.5  # 50/50 split
    success_metrics: list = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.success_metrics is None:
            self.success_metrics = ["acceptance_rate", "avg_risk_score"]
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.test_id is None:
            self.test_id = str(uuid.uuid4())