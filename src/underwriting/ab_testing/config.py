"""
Configuration management for A/B testing framework.

This module provides configuration management for A/B tests, including
predefined test configurations, validation, and persistence.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import uuid

from loguru import logger


class ABTestType(Enum):
    """A/B test types."""
    RULE_SET_COMPARISON = "rule_set_comparison"
    AI_VS_RULES = "ai_vs_rules"
    AI_MODEL_COMPARISON = "ai_model_comparison"
    CONFIGURATION_COMPARISON = "configuration_comparison"
    PERFORMANCE_COMPARISON = "performance_comparison"


@dataclass
class ABTestConfig:
    """A/B test configuration."""
    test_id: str
    name: str
    description: str
    test_type: ABTestType
    control_config: Dict[str, Any]
    treatment_config: Dict[str, Any]
    sample_size: int
    confidence_level: float = 0.95
    minimum_effect_size: float = 0.05
    test_duration_hours: Optional[int] = None
    traffic_allocation: float = 0.5
    success_metrics: List[str] = field(default_factory=lambda: ["acceptance_rate", "avg_risk_score"])
    stratification: Optional[Dict[str, Any]] = None
    stop_criteria: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)


class ABTestConfigManager:
    """A/B test configuration manager."""
    
    def __init__(self, config_file: str = "src/underwriting/config/ab_tests.json"):
        """Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.predefined_configs = self._load_predefined_configs()
        self.custom_configs: Dict[str, ABTestConfig] = {}
        
        # Load existing configurations
        self._load_configurations()
        
        logger.info(f"A/B test configuration manager initialized with {len(self.predefined_configs)} predefined configs")
    
    def _load_predefined_configs(self) -> Dict[str, ABTestConfig]:
        """Load predefined A/B test configurations."""
        configs = {}
        
        # Rule set comparison tests
        configs["conservative_vs_standard"] = ABTestConfig(
            test_id="conservative_vs_standard",
            name="Conservative vs Standard Rule Set",
            description="Compare conservative and standard rule sets with AI-enhanced processing",
            test_type=ABTestType.RULE_SET_COMPARISON,
            control_config={
                "engine_type": "ai_enhanced",
                "rule_set": "conservative",
                "ai_enabled": True,
                "ai_model": "gpt-4-turbo"
            },
            treatment_config={
                "engine_type": "ai_enhanced",
                "rule_set": "standard",
                "ai_enabled": True,
                "ai_model": "gpt-4-turbo"
            },
            sample_size=1000,
            success_metrics=["acceptance_rate", "avg_risk_score", "decision_distribution"],
            tags=["rule_comparison", "baseline"]
        )
        
        configs["standard_vs_liberal"] = ABTestConfig(
            test_id="standard_vs_liberal",
            name="Standard vs Liberal Rule Set",
            description="Compare standard and liberal rule sets with AI-enhanced processing",
            test_type=ABTestType.RULE_SET_COMPARISON,
            control_config={
                "engine_type": "ai_enhanced",
                "rule_set": "standard",
                "ai_enabled": True,
                "ai_model": "gpt-4-turbo"
            },
            treatment_config={
                "engine_type": "ai_enhanced",
                "rule_set": "liberal",
                "ai_enabled": True,
                "ai_model": "gpt-4-turbo"
            },
            sample_size=1000,
            success_metrics=["acceptance_rate", "avg_risk_score", "decision_distribution"],
            tags=["rule_comparison", "business_impact"]
        )
        
        # AI vs Rules tests
        configs["ai_vs_standard_rules"] = ABTestConfig(
            test_id="ai_vs_standard_rules",
            name="AI Enhanced vs Standard Rules",
            description="Compare AI-enhanced underwriting against standard rules-only approach",
            test_type=ABTestType.AI_VS_RULES,
            control_config={
                "engine_type": "standard",
                "rule_set": "standard",
                "ai_enabled": False
            },
            treatment_config={
                "engine_type": "ai_enhanced",
                "rule_set": "standard",
                "ai_enabled": True,
                "ai_model": "gpt-4-turbo"
            },
            sample_size=1500,
            success_metrics=["acceptance_rate", "avg_risk_score", "processing_time"],
            tags=["ai_comparison", "performance"]
        )
        
        configs["ai_conservative_vs_liberal_rules"] = ABTestConfig(
            test_id="ai_conservative_vs_liberal_rules",
            name="AI + Conservative vs Liberal Rules",
            description="Compare AI-enhanced conservative approach against liberal rules",
            test_type=ABTestType.AI_VS_RULES,
            control_config={
                "engine_type": "standard",
                "rule_set": "liberal",
                "ai_enabled": False
            },
            treatment_config={
                "engine_type": "ai_enhanced",
                "rule_set": "conservative",
                "ai_enabled": True,
                "ai_model": "gpt-4-turbo"
            },
            sample_size=1200,
            success_metrics=["acceptance_rate", "avg_risk_score", "decision_distribution"],
            tags=["ai_comparison", "risk_management"]
        )
        
        # AI model comparison tests
        configs["gpt4_vs_gpt35_turbo"] = ABTestConfig(
            test_id="gpt4_vs_gpt35_turbo",
            name="GPT-4 vs GPT-3.5 Turbo",
            description="Compare GPT-4 and GPT-3.5 Turbo models for underwriting decisions",
            test_type=ABTestType.AI_MODEL_COMPARISON,
            control_config={
                "engine_type": "ai_enhanced",
                "rule_set": "standard",
                "ai_enabled": True,
                "ai_model": "gpt-3.5-turbo"
            },
            treatment_config={
                "engine_type": "ai_enhanced",
                "rule_set": "standard",
                "ai_enabled": True,
                "ai_model": "gpt-4-turbo"
            },
            sample_size=800,
            success_metrics=["acceptance_rate", "avg_risk_score", "processing_time"],
            tags=["ai_model_comparison", "cost_analysis"]
        )
        
        # Configuration comparison tests
        configs["rate_limiting_impact"] = ABTestConfig(
            test_id="rate_limiting_impact",
            name="Rate Limiting Impact Analysis",
            description="Analyze impact of rate limiting on system performance",
            test_type=ABTestType.CONFIGURATION_COMPARISON,
            control_config={
                "engine_type": "ai_enhanced",
                "rule_set": "standard",
                "ai_enabled": True,
                "rate_limiting_enabled": False
            },
            treatment_config={
                "engine_type": "ai_enhanced",
                "rule_set": "standard",
                "ai_enabled": True,
                "rate_limiting_enabled": True
            },
            sample_size=1000,
            success_metrics=["acceptance_rate", "processing_time"],
            tags=["performance", "rate_limiting"]
        )
        
        # Performance comparison tests
        configs["high_volume_performance"] = ABTestConfig(
            test_id="high_volume_performance",
            name="High Volume Performance Test",
            description="Test AI-enhanced system performance under different volume conditions",
            test_type=ABTestType.PERFORMANCE_COMPARISON,
            control_config={
                "engine_type": "ai_enhanced",
                "rule_set": "standard",
                "ai_enabled": True,
                "ai_model": "gpt-4-turbo",
                "batch_size": 5
            },
            treatment_config={
                "engine_type": "ai_enhanced",
                "rule_set": "standard",
                "ai_enabled": True,
                "ai_model": "gpt-4-turbo",
                "batch_size": 10
            },
            sample_size=2000,
            success_metrics=["processing_time", "acceptance_rate"],
            tags=["performance", "scalability"]
        )
        
        return configs
    
    def _load_configurations(self) -> None:
        """Load configurations from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                for config_data in data.get("custom_configs", []):
                    config = self._dict_to_config(config_data)
                    self.custom_configs[config.test_id] = config
                
                logger.info(f"Loaded {len(self.custom_configs)} custom configurations")
                
            except Exception as e:
                logger.error(f"Error loading configurations: {e}")
    
    def _save_configurations(self) -> None:
        """Save configurations to file."""
        try:
            data = {
                "custom_configs": [
                    self._config_to_dict(config) 
                    for config in self.custom_configs.values()
                ],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Saved {len(self.custom_configs)} custom configurations")
            
        except Exception as e:
            logger.error(f"Error saving configurations: {e}")
    
    def _config_to_dict(self, config: ABTestConfig) -> Dict[str, Any]:
        """Convert config to dictionary."""
        config_dict = asdict(config)
        config_dict["test_type"] = config.test_type.value
        config_dict["created_at"] = config.created_at.isoformat()
        return config_dict
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> ABTestConfig:
        """Convert dictionary to config."""
        config_dict = config_dict.copy()
        config_dict["test_type"] = ABTestType(config_dict["test_type"])
        config_dict["created_at"] = datetime.fromisoformat(config_dict["created_at"])
        return ABTestConfig(**config_dict)
    
    def get_config(self, test_id: str) -> Optional[ABTestConfig]:
        """Get configuration by test ID.
        
        Args:
            test_id: Test identifier
            
        Returns:
            Configuration or None if not found
        """
        # Check predefined configs first
        if test_id in self.predefined_configs:
            return self.predefined_configs[test_id]
        
        # Check custom configs
        return self.custom_configs.get(test_id)
    
    def create_config(self, config: ABTestConfig) -> ABTestConfig:
        """Create new configuration.
        
        Args:
            config: Configuration to create
            
        Returns:
            Created configuration
        """
        if config.test_id in self.predefined_configs or config.test_id in self.custom_configs:
            raise ValueError(f"Configuration {config.test_id} already exists")
        
        # Set creation timestamp
        config.created_at = datetime.now()
        
        # Validate configuration
        self._validate_config(config)
        
        # Add to custom configs
        self.custom_configs[config.test_id] = config
        
        # Save to file
        self._save_configurations()
        
        logger.info(f"Created configuration: {config.test_id}")
        return config
    
    def update_config(self, test_id: str, updates: Dict[str, Any]) -> ABTestConfig:
        """Update existing configuration.
        
        Args:
            test_id: Test identifier
            updates: Updates to apply
            
        Returns:
            Updated configuration
        """
        config = self.get_config(test_id)
        if not config:
            raise ValueError(f"Configuration {test_id} not found")
        
        # Don't allow updating predefined configs
        if test_id in self.predefined_configs:
            raise ValueError(f"Cannot update predefined configuration {test_id}")
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # Validate updated configuration
        self._validate_config(config)
        
        # Save to file
        self._save_configurations()
        
        logger.info(f"Updated configuration: {test_id}")
        return config
    
    def delete_config(self, test_id: str) -> bool:
        """Delete configuration.
        
        Args:
            test_id: Test identifier
            
        Returns:
            True if deleted, False if not found
        """
        if test_id in self.predefined_configs:
            raise ValueError(f"Cannot delete predefined configuration {test_id}")
        
        if test_id in self.custom_configs:
            del self.custom_configs[test_id]
            self._save_configurations()
            logger.info(f"Deleted configuration: {test_id}")
            return True
        
        return False
    
    def list_configs(self, test_type: Optional[ABTestType] = None, tags: Optional[List[str]] = None) -> List[ABTestConfig]:
        """List configurations with optional filtering.
        
        Args:
            test_type: Filter by test type
            tags: Filter by tags
            
        Returns:
            List of configurations
        """
        all_configs = list(self.predefined_configs.values()) + list(self.custom_configs.values())
        
        # Filter by test type
        if test_type:
            all_configs = [c for c in all_configs if c.test_type == test_type]
        
        # Filter by tags
        if tags:
            all_configs = [c for c in all_configs if any(tag in c.tags for tag in tags)]
        
        return all_configs
    
    def clone_config(self, source_test_id: str, new_test_id: str, name: str, **overrides) -> ABTestConfig:
        """Clone existing configuration with modifications.
        
        Args:
            source_test_id: Source configuration ID
            new_test_id: New configuration ID
            name: New configuration name
            **overrides: Fields to override
            
        Returns:
            Cloned configuration
        """
        source_config = self.get_config(source_test_id)
        if not source_config:
            raise ValueError(f"Source configuration {source_test_id} not found")
        
        # Create new config from source
        config_dict = asdict(source_config)
        config_dict["test_id"] = new_test_id
        config_dict["name"] = name
        config_dict["created_at"] = datetime.now()
        
        # Apply overrides
        for key, value in overrides.items():
            if key in config_dict:
                config_dict[key] = value
        
        new_config = ABTestConfig(**config_dict)
        
        # Create the new configuration
        return self.create_config(new_config)
    
    def _validate_config(self, config: ABTestConfig) -> None:
        """Validate configuration.
        
        Args:
            config: Configuration to validate
        """
        # Basic validation
        if not config.test_id:
            raise ValueError("test_id is required")
        
        if not config.name:
            raise ValueError("name is required")
        
        if config.sample_size <= 0:
            raise ValueError("sample_size must be positive")
        
        if not (0 < config.confidence_level < 1):
            raise ValueError("confidence_level must be between 0 and 1")
        
        if not (0 < config.traffic_allocation < 1):
            raise ValueError("traffic_allocation must be between 0 and 1")
        
        # Validate success metrics
        valid_metrics = ["acceptance_rate", "avg_risk_score", "decision_distribution", "processing_time"]
        for metric in config.success_metrics:
            if metric not in valid_metrics:
                raise ValueError(f"Invalid success metric: {metric}")
        
        # Validate configurations based on test type
        if config.test_type == ABTestType.RULE_SET_COMPARISON:
            self._validate_rule_set_config(config)
        elif config.test_type == ABTestType.AI_VS_RULES:
            self._validate_ai_vs_rules_config(config)
        elif config.test_type == ABTestType.AI_MODEL_COMPARISON:
            self._validate_ai_model_config(config)
    
    def _validate_rule_set_config(self, config: ABTestConfig) -> None:
        """Validate rule set comparison configuration."""
        valid_rule_sets = ["conservative", "standard", "liberal"]
        
        control_rule_set = config.control_config.get("rule_set")
        treatment_rule_set = config.treatment_config.get("rule_set")
        
        if control_rule_set not in valid_rule_sets:
            raise ValueError(f"Invalid control rule set: {control_rule_set}")
        
        if treatment_rule_set not in valid_rule_sets:
            raise ValueError(f"Invalid treatment rule set: {treatment_rule_set}")
        
        if control_rule_set == treatment_rule_set:
            raise ValueError("Control and treatment rule sets must be different")
    
    def _validate_ai_vs_rules_config(self, config: ABTestConfig) -> None:
        """Validate AI vs rules configuration."""
        control_ai = config.control_config.get("ai_enabled", False)
        treatment_ai = config.treatment_config.get("ai_enabled", False)
        
        if control_ai == treatment_ai:
            raise ValueError("One variant must have AI enabled and the other disabled")
    
    def _validate_ai_model_config(self, config: ABTestConfig) -> None:
        """Validate AI model comparison configuration."""
        valid_models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        
        control_model = config.control_config.get("ai_model")
        treatment_model = config.treatment_config.get("ai_model")
        
        if control_model not in valid_models:
            raise ValueError(f"Invalid control AI model: {control_model}")
        
        if treatment_model not in valid_models:
            raise ValueError(f"Invalid treatment AI model: {treatment_model}")
        
        if control_model == treatment_model:
            raise ValueError("Control and treatment AI models must be different")
    
    def get_config_summary(self, test_id: str) -> Dict[str, Any]:
        """Get configuration summary.
        
        Args:
            test_id: Test identifier
            
        Returns:
            Configuration summary
        """
        config = self.get_config(test_id)
        if not config:
            return {"error": f"Configuration {test_id} not found"}
        
        return {
            "test_id": config.test_id,
            "name": config.name,
            "description": config.description,
            "test_type": config.test_type.value,
            "sample_size": config.sample_size,
            "confidence_level": config.confidence_level,
            "success_metrics": config.success_metrics,
            "created_at": config.created_at.isoformat(),
            "created_by": config.created_by,
            "tags": config.tags,
            "is_predefined": test_id in self.predefined_configs
        }
    
    def export_config(self, test_id: str, file_path: str) -> None:
        """Export configuration to file.
        
        Args:
            test_id: Test identifier
            file_path: Output file path
        """
        config = self.get_config(test_id)
        if not config:
            raise ValueError(f"Configuration {test_id} not found")
        
        config_dict = self._config_to_dict(config)
        
        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        logger.info(f"Exported configuration {test_id} to {file_path}")
    
    def import_config(self, file_path: str) -> ABTestConfig:
        """Import configuration from file.
        
        Args:
            file_path: Input file path
            
        Returns:
            Imported configuration
        """
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        
        config = self._dict_to_config(config_dict)
        
        # Generate new ID if already exists
        if config.test_id in self.predefined_configs or config.test_id in self.custom_configs:
            original_id = config.test_id
            config.test_id = f"{original_id}_{uuid.uuid4().hex[:8]}"
            logger.warning(f"Configuration ID {original_id} already exists, using {config.test_id}")
        
        return self.create_config(config)