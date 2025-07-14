"""
Configuration loader for underwriting rules and system settings.

This module handles loading and validation of rule configurations from JSON files,
providing a centralized way to manage different rule sets for A/B testing.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator
from loguru import logger


class RuleCriteria(BaseModel):
    """Model for rule criteria configuration."""
    license_status: Optional[Union[str, List[str]]] = None
    violation_type: Optional[str] = None
    claim_type: Optional[str] = None
    count_threshold: Optional[int] = None
    lookback_years: Optional[int] = None
    coverage_lapse_days: Optional[int] = None
    coverage_lapse_days_min: Optional[int] = None
    coverage_lapse_days_max: Optional[int] = None
    credit_score_min: Optional[int] = None
    credit_score_max: Optional[int] = None
    driver_age_min: Optional[int] = None
    driver_age_max: Optional[int] = None
    vehicle_category: Optional[List[str]] = None
    vehicle_value_min: Optional[int] = None
    vehicle_value_max: Optional[int] = None
    fraud_conviction: Optional[bool] = None
    violations_count: Optional[int] = None
    at_fault_claims_count: Optional[int] = None
    at_fault_claims_max: Optional[int] = None
    minor_violations_count: Optional[int] = None
    minor_violations_max: Optional[int] = None
    major_violations: Optional[bool] = None
    major_violation_count: Optional[int] = None
    violation_types: Optional[List[str]] = None
    any_violations: Optional[bool] = None
    action: str
    reason: str


class Rule(BaseModel):
    """Model for individual underwriting rules."""
    rule_id: str
    name: str
    description: str
    criteria: RuleCriteria


class RuleCategory(BaseModel):
    """Model for rule categories (hard_stops, adjudication_triggers, etc.)."""
    description: str
    rules: List[Rule]


class AgeCategory(BaseModel):
    """Model for age category definitions."""
    min: int
    max: int


class EvaluationParameters(BaseModel):
    """Model for evaluation parameters."""
    lookback_periods: Dict[str, int]
    age_categories: Dict[str, AgeCategory]
    violation_severity: Dict[str, List[str]]
    vehicle_categories: Dict[str, List[str]]


class RuleSet(BaseModel):
    """Model for complete rule set configuration."""
    version: str
    last_updated: str
    description: str
    hard_stops: RuleCategory
    adjudication_triggers: RuleCategory
    acceptance_criteria: RuleCategory
    evaluation_parameters: EvaluationParameters
    
    @field_validator('version')
    @classmethod
    def validate_version_format(cls, v):
        """Validate version format."""
        if not v or len(v.split('.')) < 2:
            raise ValueError('Version must be in format X.Y or X.Y.Z')
        return v


class ConfigurationLoader:
    """Loads and manages underwriting rule configurations."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration loader.
        
        Args:
            config_dir: Directory containing configuration files.
                       If None, uses default config directory.
        """
        if config_dir is None:
            self.config_dir = Path(__file__).parent / "rules"
        else:
            self.config_dir = Path(config_dir)
        
        self._rule_sets: Dict[str, RuleSet] = {}
        self._load_all_rule_sets()
    
    def _load_all_rule_sets(self) -> None:
        """Load all available rule sets from configuration directory."""
        rule_files = {
            "conservative": self.config_dir / "conservative.json",
            "standard": self.config_dir / "standard.json", 
            "liberal": self.config_dir / "liberal.json"
        }
        
        for rule_name, file_path in rule_files.items():
            if file_path.exists():
                try:
                    self._rule_sets[rule_name] = self._load_rule_set(file_path)
                    logger.info(f"Loaded {rule_name} rule set from {file_path}")
                except Exception as e:
                    logger.error(f"Failed to load {rule_name} rule set: {e}")
                    raise
            else:
                logger.warning(f"Rule set file not found: {file_path}")
    
    def _load_rule_set(self, file_path: Path) -> RuleSet:
        """Load a single rule set from JSON file.
        
        Args:
            file_path: Path to the JSON rule configuration file.
            
        Returns:
            Loaded and validated RuleSet instance.
            
        Raises:
            ValueError: If file format is invalid.
            FileNotFoundError: If file doesn't exist.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract the underwriting_rules section
            if "underwriting_rules" not in data:
                raise ValueError("Missing 'underwriting_rules' section in configuration")
            
            rules_data = data["underwriting_rules"]
            
            # Convert age categories to proper format
            age_categories = {}
            for category, values in rules_data["evaluation_parameters"]["age_categories"].items():
                age_categories[category] = AgeCategory(**values)
            
            # Build the rule set
            rule_set_data = {
                "version": rules_data["version"],
                "last_updated": rules_data["last_updated"],
                "description": rules_data["description"],
                "hard_stops": RuleCategory(**rules_data["hard_stops"]),
                "adjudication_triggers": RuleCategory(**rules_data["adjudication_triggers"]),
                "acceptance_criteria": RuleCategory(**rules_data["acceptance_criteria"]),
                "evaluation_parameters": EvaluationParameters(
                    lookback_periods=rules_data["evaluation_parameters"]["lookback_periods"],
                    age_categories=age_categories,
                    violation_severity=rules_data["evaluation_parameters"]["violation_severity"],
                    vehicle_categories=rules_data["evaluation_parameters"]["vehicle_categories"]
                )
            }
            
            return RuleSet(**rule_set_data)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading rule set from {file_path}: {e}")
    
    def get_rule_set(self, rule_set_name: str) -> RuleSet:
        """Get a specific rule set by name.
        
        Args:
            rule_set_name: Name of the rule set (conservative, standard, liberal).
            
        Returns:
            RuleSet instance.
            
        Raises:
            ValueError: If rule set name is not found.
        """
        if rule_set_name not in self._rule_sets:
            available = list(self._rule_sets.keys())
            raise ValueError(f"Rule set '{rule_set_name}' not found. Available: {available}")
        
        return self._rule_sets[rule_set_name]
    
    def get_available_rule_sets(self) -> List[str]:
        """Get list of available rule set names.
        
        Returns:
            List of rule set names.
        """
        return list(self._rule_sets.keys())
    
    def reload_rule_sets(self) -> None:
        """Reload all rule sets from configuration files."""
        self._rule_sets.clear()
        self._load_all_rule_sets()
        logger.info("Reloaded all rule sets")
    
    def validate_rule_set(self, rule_set_name: str) -> bool:
        """Validate a rule set configuration.
        
        Args:
            rule_set_name: Name of the rule set to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        try:
            rule_set = self.get_rule_set(rule_set_name)
            
            # Basic validation checks
            if not rule_set.hard_stops.rules:
                logger.warning(f"Rule set '{rule_set_name}' has no hard stop rules")
                return False
            
            if not rule_set.adjudication_triggers.rules:
                logger.warning(f"Rule set '{rule_set_name}' has no adjudication triggers")
                return False
            
            # Check for required rule IDs
            required_hard_stops = ["HS001", "HS002", "HS003", "HS004", "HS005"]
            hard_stop_ids = [rule.rule_id for rule in rule_set.hard_stops.rules]
            
            missing_rules = [rule_id for rule_id in required_hard_stops if rule_id not in hard_stop_ids]
            if missing_rules:
                logger.warning(f"Rule set '{rule_set_name}' missing required rules: {missing_rules}")
                return False
            
            logger.info(f"Rule set '{rule_set_name}' validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Rule set '{rule_set_name}' validation failed: {e}")
            return False