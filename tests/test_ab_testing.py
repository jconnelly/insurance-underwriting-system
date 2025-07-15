"""
Tests for A/B testing framework.

This module provides comprehensive tests for the A/B testing framework
including statistical analysis, sample generation, and configuration management.
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from underwriting.ab_testing.framework import (
    ABTestFramework, ABTest, ABTestConfiguration, ABTestStatus, ABTestVariant, ABTestResult
)
from underwriting.ab_testing.config import ABTestConfigManager, ABTestConfig, ABTestType
from underwriting.ab_testing.statistics import StatisticalAnalyzer, StatisticalTestType
from underwriting.ab_testing.sample_generator import ABTestSampleGenerator, ABTestSampleProfile
from underwriting.ab_testing.results import ABTestResultsManager, ReportFormat
from underwriting.core.models import Application, Driver, Vehicle, DecisionType, Gender, MaritalStatus, LicenseStatus, VehicleCategory
from underwriting.core.engine import UnderwritingDecision, RiskScore


class TestABTestConfiguration:
    """Test A/B test configuration management."""
    
    def test_create_configuration(self):
        """Test creating A/B test configuration."""
        config = ABTestConfiguration(
            test_id="test_001",
            name="Test Configuration",
            description="Test description",
            control_config={"rule_set": "conservative"},
            treatment_config={"rule_set": "standard"},
            sample_size=1000
        )
        
        assert config.test_id == "test_001"
        assert config.name == "Test Configuration"
        assert config.sample_size == 1000
        assert config.confidence_level == 0.95
        assert config.minimum_effect_size == 0.05
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test invalid configuration
        with pytest.raises(ValueError):
            ABTestConfiguration(
                test_id="",  # Invalid empty ID
                name="Test",
                description="Test",
                control_config={},
                treatment_config={},
                sample_size=0  # Invalid sample size
            )


class TestABTestConfigManager:
    """Test A/B test configuration manager."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_ab_configs.json")
        self.config_manager = ABTestConfigManager(self.config_file)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_list_predefined_configs(self):
        """Test listing predefined configurations."""
        configs = self.config_manager.list_configs()
        
        assert len(configs) > 0
        
        # Check for expected predefined configs
        config_ids = [c.test_id for c in configs]
        assert "conservative_vs_standard" in config_ids
        assert "ai_vs_standard_rules" in config_ids
    
    def test_get_predefined_config(self):
        """Test getting predefined configuration."""
        config = self.config_manager.get_config("conservative_vs_standard")
        
        assert config is not None
        assert config.test_id == "conservative_vs_standard"
        assert config.test_type == ABTestType.RULE_SET_COMPARISON
        assert config.control_config["rule_set"] == "conservative"
        assert config.treatment_config["rule_set"] == "standard"
    
    def test_create_custom_config(self):
        """Test creating custom configuration."""
        config = ABTestConfig(
            test_id="custom_test_001",
            name="Custom Test",
            description="Custom test description",
            test_type=ABTestType.RULE_SET_COMPARISON,
            control_config={"rule_set": "conservative"},
            treatment_config={"rule_set": "liberal"},
            sample_size=500
        )
        
        created_config = self.config_manager.create_config(config)
        
        assert created_config.test_id == "custom_test_001"
        assert created_config.name == "Custom Test"
        
        # Verify it can be retrieved
        retrieved_config = self.config_manager.get_config("custom_test_001")
        assert retrieved_config is not None
        assert retrieved_config.name == "Custom Test"
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid rule set comparison
        config = ABTestConfig(
            test_id="invalid_test",
            name="Invalid Test",
            description="Test",
            test_type=ABTestType.RULE_SET_COMPARISON,
            control_config={"rule_set": "invalid_rule_set"},
            treatment_config={"rule_set": "standard"},
            sample_size=100
        )
        
        with pytest.raises(ValueError):
            self.config_manager.create_config(config)
    
    def test_clone_config(self):
        """Test cloning configuration."""
        cloned_config = self.config_manager.clone_config(
            "conservative_vs_standard",
            "cloned_test",
            "Cloned Test",
            sample_size=2000
        )
        
        assert cloned_config.test_id == "cloned_test"
        assert cloned_config.name == "Cloned Test"
        assert cloned_config.sample_size == 2000
        assert cloned_config.test_type == ABTestType.RULE_SET_COMPARISON


class TestStatisticalAnalyzer:
    """Test statistical analysis engine."""
    
    def setup_method(self):
        """Set up test environment."""
        self.analyzer = StatisticalAnalyzer(confidence_level=0.95)
    
    def create_mock_result(self, variant: ABTestVariant, decision: DecisionType, risk_score: int, processing_time: float = 0.1):
        """Create mock A/B test result."""
        # Create mock decision
        mock_decision = MagicMock()
        mock_decision.decision = decision
        mock_decision.risk_score = MagicMock()
        mock_decision.risk_score.overall_score = risk_score
        
        return ABTestResult(
            test_id="test_001",
            variant=variant,
            application_id=f"app_{variant.value}_{risk_score}",
            decision=mock_decision,
            processing_time=processing_time,
            timestamp=datetime.now()
        )
    
    def test_proportion_test(self):
        """Test proportion test for acceptance rates."""
        # Create control and treatment results
        control_results = [
            self.create_mock_result(ABTestVariant.CONTROL, DecisionType.ACCEPT, 100) for _ in range(70)
        ] + [
            self.create_mock_result(ABTestVariant.CONTROL, DecisionType.DENY, 800) for _ in range(30)
        ]
        
        treatment_results = [
            self.create_mock_result(ABTestVariant.TREATMENT, DecisionType.ACCEPT, 100) for _ in range(80)
        ] + [
            self.create_mock_result(ABTestVariant.TREATMENT, DecisionType.DENY, 800) for _ in range(20)
        ]
        
        # Analyze results
        analysis = self.analyzer.analyze_results(
            control_results, 
            treatment_results, 
            ["acceptance_rate"]
        )
        
        assert "acceptance_rate" in analysis
        
        acceptance_analysis = analysis["acceptance_rate"]
        assert "control_rate" in acceptance_analysis
        assert "treatment_rate" in acceptance_analysis
        assert "significant" in acceptance_analysis
        assert "effect_size" in acceptance_analysis
        
        # Check that treatment has higher acceptance rate
        assert acceptance_analysis["treatment_rate"] > acceptance_analysis["control_rate"]
    
    def test_t_test(self):
        """Test t-test for continuous variables."""
        # Create results with different risk scores
        control_results = [
            self.create_mock_result(ABTestVariant.CONTROL, DecisionType.ACCEPT, 500 + i) for i in range(-50, 51)
        ]
        
        treatment_results = [
            self.create_mock_result(ABTestVariant.TREATMENT, DecisionType.ACCEPT, 400 + i) for i in range(-50, 51)
        ]
        
        # Analyze results
        analysis = self.analyzer.analyze_results(
            control_results,
            treatment_results,
            ["avg_risk_score"]
        )
        
        assert "avg_risk_score" in analysis
        
        risk_analysis = analysis["avg_risk_score"]
        assert "control_mean" in risk_analysis
        assert "treatment_mean" in risk_analysis
        assert "significant" in risk_analysis
        
        # Treatment should have lower risk scores
        assert risk_analysis["treatment_mean"] < risk_analysis["control_mean"]
    
    def test_chi_square_test(self):
        """Test chi-square test for decision distribution."""
        # Create results with different decision distributions
        control_results = (
            [self.create_mock_result(ABTestVariant.CONTROL, DecisionType.ACCEPT, 100) for _ in range(60)] +
            [self.create_mock_result(ABTestVariant.CONTROL, DecisionType.DENY, 800) for _ in range(30)] +
            [self.create_mock_result(ABTestVariant.CONTROL, DecisionType.ADJUDICATE, 500) for _ in range(10)]
        )
        
        treatment_results = (
            [self.create_mock_result(ABTestVariant.TREATMENT, DecisionType.ACCEPT, 100) for _ in range(70)] +
            [self.create_mock_result(ABTestVariant.TREATMENT, DecisionType.DENY, 800) for _ in range(20)] +
            [self.create_mock_result(ABTestVariant.TREATMENT, DecisionType.ADJUDICATE, 500) for _ in range(10)]
        )
        
        # Analyze results
        analysis = self.analyzer.analyze_results(
            control_results,
            treatment_results,
            ["decision_distribution"]
        )
        
        assert "decision_distribution" in analysis
        
        decision_analysis = analysis["decision_distribution"]
        assert "control_distribution" in decision_analysis
        assert "treatment_distribution" in decision_analysis
        assert "significant" in decision_analysis
    
    def test_sample_size_calculation(self):
        """Test sample size calculation."""
        # Test for proportion test
        sample_size = self.analyzer.calculate_required_sample_size(
            effect_size=0.1,
            power=0.8,
            test_type=StatisticalTestType.PROPORTION_TEST
        )
        
        assert sample_size > 0
        assert isinstance(sample_size, int)
        
        # Larger effect size should require smaller sample
        smaller_sample_size = self.analyzer.calculate_required_sample_size(
            effect_size=0.2,
            power=0.8,
            test_type=StatisticalTestType.PROPORTION_TEST
        )
        
        assert smaller_sample_size < sample_size
    
    def test_power_calculation(self):
        """Test statistical power calculation."""
        power = self.analyzer.calculate_power(
            sample_size=1000,
            effect_size=0.1,
            test_type=StatisticalTestType.PROPORTION_TEST
        )
        
        assert 0 <= power <= 1
        
        # Larger sample size should give higher power
        higher_power = self.analyzer.calculate_power(
            sample_size=2000,
            effect_size=0.1,
            test_type=StatisticalTestType.PROPORTION_TEST
        )
        
        assert higher_power >= power


class TestABTestSampleGenerator:
    """Test A/B test sample generator."""
    
    def setup_method(self):
        """Set up test environment."""
        self.generator = ABTestSampleGenerator(seed=42)
    
    def test_generate_low_risk_samples(self):
        """Test generating low-risk samples."""
        applications = self.generator.generate_test_samples(
            ABTestSampleProfile.LOW_RISK,
            sample_size=100
        )
        
        assert len(applications) == 100
        
        # Check that applications are generally low risk
        for app in applications[:10]:  # Check first 10
            assert isinstance(app, Application)
            assert app.applicant.age >= 25  # Should be mature drivers
            assert len(app.applicant.violations) <= 1  # Low violations
            assert app.credit_score >= 700  # Good credit
    
    def test_generate_high_risk_samples(self):
        """Test generating high-risk samples."""
        applications = self.generator.generate_test_samples(
            ABTestSampleProfile.HIGH_RISK,
            sample_size=100
        )
        
        assert len(applications) == 100
        
        # Check that applications are generally high risk
        high_risk_indicators = 0
        for app in applications:
            if (app.applicant.age < 25 or app.applicant.age > 70 or 
                len(app.applicant.violations) >= 2 or 
                len(app.applicant.claims) >= 1 or
                app.credit_score < 650):
                high_risk_indicators += 1
        
        # Should have more high-risk indicators than low-risk profile
        assert high_risk_indicators > 50  # More than 50% should have risk indicators
    
    def test_generate_mixed_samples(self):
        """Test generating mixed risk samples."""
        applications = self.generator.generate_test_samples(
            ABTestSampleProfile.MIXED,
            sample_size=300
        )
        
        assert len(applications) == 300
        
        # Should have a mix of risk levels
        low_risk_count = 0
        high_risk_count = 0
        
        for app in applications:
            if (app.applicant.age >= 30 and app.applicant.age <= 60 and
                len(app.applicant.violations) == 0 and
                app.credit_score >= 700):
                low_risk_count += 1
            elif (app.applicant.age < 25 or app.applicant.age > 70 or
                  len(app.applicant.violations) >= 2 or
                  app.credit_score < 600):
                high_risk_count += 1
        
        # Should have both low and high risk applications
        assert low_risk_count > 0
        assert high_risk_count > 0
    
    def test_stratified_samples(self):
        """Test generating stratified samples."""
        strata_config = {
            "young_drivers": 50,
            "senior_drivers": 50,
            "high_value_vehicles": 30
        }
        
        applications = self.generator.generate_stratified_samples(strata_config)
        
        assert len(applications) == 130  # Total of all strata
        
        # Check that we have applications from different strata
        young_drivers = [app for app in applications if app.applicant.age <= 25]
        senior_drivers = [app for app in applications if app.applicant.age >= 65]
        
        assert len(young_drivers) > 0
        assert len(senior_drivers) > 0
    
    def test_power_analysis_samples(self):
        """Test generating samples for power analysis."""
        sample_size, applications = self.generator.generate_power_analysis_samples(
            effect_size=0.1,
            power=0.8
        )
        
        assert sample_size > 0
        assert len(applications) == sample_size
        assert all(isinstance(app, Application) for app in applications)


class TestABTestFramework:
    """Test A/B testing framework."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.framework = ABTestFramework(self.temp_dir)
        
        # Create test configuration
        self.test_config = ABTestConfiguration(
            test_id="framework_test_001",
            name="Framework Test",
            description="Test framework functionality",
            control_config={"engine_type": "standard", "rule_set": "conservative", "ai_enabled": False},
            treatment_config={"engine_type": "standard", "rule_set": "standard", "ai_enabled": False},
            sample_size=10
        )
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_create_test(self):
        """Test creating A/B test."""
        test = self.framework.create_test(self.test_config)
        
        assert test.test_id == "framework_test_001"
        assert test.status == ABTestStatus.PENDING
        assert test.config.name == "Framework Test"
    
    def test_start_and_stop_test(self):
        """Test starting and stopping A/B test."""
        test = self.framework.create_test(self.test_config)
        
        # Start test
        self.framework.start_test(test.test_id)
        assert test.status == ABTestStatus.RUNNING
        assert test.start_time is not None
        
        # Stop test
        self.framework.stop_test(test.test_id)
        assert test.status == ABTestStatus.COMPLETED
        assert test.end_time is not None
    
    @pytest.mark.asyncio
    async def test_evaluate_application(self):
        """Test evaluating application in A/B test."""
        test = self.framework.create_test(self.test_config)
        self.framework.start_test(test.test_id)
        
        # Create test application
        driver = Driver(
            age=35,
            gender=Gender.MALE,
            marital_status=MaritalStatus.MARRIED,
            license_status=LicenseStatus.VALID,
            years_licensed=15,
            violations=[],
            claims=[]
        )
        
        vehicle = Vehicle(
            year=2020,
            make="Toyota",
            model="Camry",
            category=VehicleCategory.SEDAN,
            value=25000,
            safety_rating=5
        )
        
        application = Application(
            applicant=driver,
            additional_drivers=[],
            vehicles=[vehicle],
            coverage_lapse_days=0,
            credit_score=750,
            fraud_conviction=False
        )
        
        # Evaluate application
        result = await self.framework.evaluate_application(test.test_id, application)
        
        assert result.test_id == test.test_id
        assert result.variant in [ABTestVariant.CONTROL, ABTestVariant.TREATMENT]
        assert result.application_id == str(application.id)
        assert result.decision is not None
        assert result.processing_time > 0
    
    def test_get_test_summary(self):
        """Test getting test summary."""
        test = self.framework.create_test(self.test_config)
        summary = self.framework.get_test_summary(test.test_id)
        
        assert summary.test_id == test.test_id
        assert summary.status == ABTestStatus.PENDING
        assert len(summary.control_results) == 0
        assert len(summary.treatment_results) == 0
    
    def test_list_tests(self):
        """Test listing tests."""
        # Create multiple tests
        config1 = self.test_config
        config2 = ABTestConfiguration(
            test_id="framework_test_002",
            name="Framework Test 2",
            description="Second test",
            control_config={"rule_set": "standard"},
            treatment_config={"rule_set": "liberal"},
            sample_size=20
        )
        
        test1 = self.framework.create_test(config1)
        test2 = self.framework.create_test(config2)
        
        tests = self.framework.list_tests()
        
        assert len(tests) == 2
        test_ids = [t["test_id"] for t in tests]
        assert "framework_test_001" in test_ids
        assert "framework_test_002" in test_ids


class TestABTestResultsManager:
    """Test A/B test results manager."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.results_manager = ABTestResultsManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_test_config(self):
        """Test saving and loading test configuration."""
        config = ABTestConfiguration(
            test_id="results_test_001",
            name="Results Test",
            description="Test results management",
            control_config={"rule_set": "conservative"},
            treatment_config={"rule_set": "standard"},
            sample_size=100
        )
        
        # Save configuration
        self.results_manager.save_test_config(config)
        
        # Verify file exists
        config_file = Path(self.temp_dir) / "configs" / "results_test_001_config.json"
        assert config_file.exists()
    
    def test_save_test_result(self):
        """Test saving individual test result."""
        # Create mock result
        mock_decision = MagicMock()
        mock_decision.decision = DecisionType.ACCEPT
        mock_decision.risk_score = MagicMock()
        mock_decision.risk_score.overall_score = 250
        mock_decision.reason = "Test reason"
        
        result = ABTestResult(
            test_id="results_test_001",
            variant=ABTestVariant.CONTROL,
            application_id="app_001",
            decision=mock_decision,
            processing_time=0.1,
            timestamp=datetime.now()
        )
        
        # Save result
        self.results_manager.save_test_result(result)
        
        # Verify file exists
        result_file = Path(self.temp_dir) / "results" / "results_test_001" / "app_001.json"
        assert result_file.exists()
    
    def test_generate_test_report(self):
        """Test generating comprehensive test report."""
        # Create mock test summary data
        test_dir = Path(self.temp_dir) / "results" / "report_test_001"
        test_dir.mkdir(parents=True)
        
        # Create summary file
        summary_data = {
            "test_id": "report_test_001",
            "status": "completed",
            "start_time": "2024-01-01T10:00:00",
            "end_time": "2024-01-01T12:00:00",
            "control_results_count": 100,
            "treatment_results_count": 100,
            "statistical_analysis": {
                "acceptance_rate": {
                    "control_rate": 0.7,
                    "treatment_rate": 0.8,
                    "significant": True,
                    "effect_size": 0.2,
                    "p_value": 0.01
                }
            },
            "conclusions": ["Treatment shows significant improvement"],
            "recommendations": ["Consider rolling out treatment"]
        }
        
        with open(test_dir / "summary.json", 'w') as f:
            json.dump(summary_data, f)
        
        # Create CSV file
        import pandas as pd
        results_data = [
            {"test_id": "report_test_001", "variant": "control", "decision": "ACCEPT", "risk_score": 250},
            {"test_id": "report_test_001", "variant": "treatment", "decision": "ACCEPT", "risk_score": 200}
        ]
        df = pd.DataFrame(results_data)
        df.to_csv(test_dir / "results.csv", index=False)
        
        # Generate report
        report = self.results_manager.generate_test_report("report_test_001")
        
        assert report.test_id == "report_test_001"
        assert report.sample_sizes["control"] == 100
        assert report.sample_sizes["treatment"] == 100
        assert "acceptance_rate" in report.significance_summary
        assert report.significance_summary["acceptance_rate"] == True
        assert len(report.conclusions) > 0
        assert len(report.recommendations) > 0
    
    def test_list_completed_tests(self):
        """Test listing completed tests."""
        # Create mock test directories
        for i in range(3):
            test_dir = Path(self.temp_dir) / "results" / f"completed_test_{i:03d}"
            test_dir.mkdir(parents=True)
            
            summary_data = {
                "test_id": f"completed_test_{i:03d}",
                "status": "completed",
                "start_time": "2024-01-01T10:00:00",
                "end_time": "2024-01-01T12:00:00",
                "control_results_count": 50,
                "treatment_results_count": 50
            }
            
            with open(test_dir / "summary.json", 'w') as f:
                json.dump(summary_data, f)
        
        # List completed tests
        tests = self.results_manager.list_completed_tests()
        
        assert len(tests) == 3
        test_ids = [t["test_id"] for t in tests]
        assert "completed_test_000" in test_ids
        assert "completed_test_001" in test_ids
        assert "completed_test_002" in test_ids


class TestIntegration:
    """Integration tests for A/B testing framework."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_complete_ab_test_workflow(self):
        """Test complete A/B test workflow."""
        # 1. Create configuration manager
        config_file = os.path.join(self.temp_dir, "ab_configs.json")
        config_manager = ABTestConfigManager(config_file)
        
        # 2. Get predefined configuration
        config = config_manager.get_config("conservative_vs_standard")
        assert config is not None
        
        # Reduce sample size for testing
        config.sample_size = 10
        
        # 3. Create framework
        framework = ABTestFramework(self.temp_dir)
        
        # 4. Create and start test
        test = framework.create_test(config)
        framework.start_test(test.test_id)
        
        # 5. Generate sample applications
        sample_generator = ABTestSampleGenerator(seed=42)
        applications = sample_generator.generate_test_samples(
            ABTestSampleProfile.MIXED,
            sample_size=config.sample_size
        )
        
        # 6. Process applications
        for app in applications:
            result = await framework.evaluate_application(test.test_id, app)
            assert result.variant in [ABTestVariant.CONTROL, ABTestVariant.TREATMENT]
        
        # 7. Stop test
        framework.stop_test(test.test_id)
        
        # 8. Get test summary
        summary = framework.get_test_summary(test.test_id)
        assert summary.status == ABTestStatus.COMPLETED
        assert len(summary.control_results) + len(summary.treatment_results) == config.sample_size
        
        # 9. Generate report
        results_manager = ABTestResultsManager(self.temp_dir)
        
        # Wait a moment for file operations to complete
        import time
        time.sleep(0.1)
        
        # We need to manually save the test results since the integration might not be complete
        results_manager.save_test_results(test.test_id, summary)
        
        # Generate report
        report = results_manager.generate_test_report(test.test_id, ReportFormat.JSON)
        
        assert report.test_id == test.test_id
        assert report.sample_sizes["total"] == config.sample_size
        assert len(report.conclusions) > 0
        assert len(report.recommendations) > 0
    
    def test_configuration_persistence(self):
        """Test configuration persistence across sessions."""
        config_file = os.path.join(self.temp_dir, "persistent_configs.json")
        
        # Create first config manager and add custom config
        config_manager1 = ABTestConfigManager(config_file)
        
        custom_config = ABTestConfig(
            test_id="persistent_test",
            name="Persistent Test",
            description="Test persistence",
            test_type=ABTestType.RULE_SET_COMPARISON,
            control_config={"rule_set": "conservative"},
            treatment_config={"rule_set": "liberal"},
            sample_size=200
        )
        
        config_manager1.create_config(custom_config)
        
        # Create second config manager (simulating new session)
        config_manager2 = ABTestConfigManager(config_file)
        
        # Verify custom config is loaded
        loaded_config = config_manager2.get_config("persistent_test")
        assert loaded_config is not None
        assert loaded_config.name == "Persistent Test"
        assert loaded_config.sample_size == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])