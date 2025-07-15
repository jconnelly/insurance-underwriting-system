#!/usr/bin/env python3
"""
A/B Testing Framework Demonstration

This script demonstrates the comprehensive A/B testing capabilities of the
insurance underwriting system.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from underwriting.ab_testing.config import ABTestConfigManager
from underwriting.ab_testing.framework import ABTestFramework
from underwriting.ab_testing.sample_generator import ABTestSampleGenerator, ABTestSampleProfile
from underwriting.ab_testing.results import ABTestResultsManager, ReportFormat


async def demonstrate_ab_testing():
    """Demonstrate the A/B testing framework."""
    
    print("=" * 60)
    print("A/B TESTING FRAMEWORK DEMONSTRATION")
    print("=" * 60)
    
    # 1. Configuration Management
    print("\n1. CONFIGURATION MANAGEMENT")
    print("-" * 30)
    
    config_manager = ABTestConfigManager()
    
    # List predefined configurations
    print("Available predefined configurations:")
    configs = config_manager.list_configs()
    for config in configs[:5]:  # Show first 5
        print(f"  - {config.test_id}: {config.name}")
        print(f"    Type: {config.test_type.value}")
        print(f"    Sample Size: {config.sample_size}")
        print(f"    Metrics: {', '.join(config.success_metrics[:3])}")
        print()
    
    # Get specific configuration
    test_config = config_manager.get_config("conservative_vs_standard")
    print(f"Selected configuration: {test_config.name}")
    print(f"Description: {test_config.description}")
    print(f"Control: {test_config.control_config}")
    print(f"Treatment: {test_config.treatment_config}")
    
    # 2. Sample Generation
    print("\n2. SAMPLE DATA GENERATION")
    print("-" * 30)
    
    # Reduce sample size for demonstration
    test_config.sample_size = 200
    
    generator = ABTestSampleGenerator(seed=42)
    
    print(f"Generating {test_config.sample_size} sample applications...")
    applications = generator.generate_test_samples(
        ABTestSampleProfile.MIXED,
        test_config.sample_size
    )
    
    print(f"Generated {len(applications)} applications")
    
    # Show sample characteristics
    print("\nSample characteristics:")
    ages = [app.applicant.age for app in applications[:20]]
    credit_scores = [app.credit_score for app in applications[:20]]
    violation_counts = [len(app.applicant.violations) for app in applications[:20]]
    
    print(f"  Age range: {min(ages)}-{max(ages)} (avg: {sum(ages)/len(ages):.1f})")
    print(f"  Credit score range: {min(credit_scores)}-{max(credit_scores)}")
    print(f"  Violations: {min(violation_counts)}-{max(violation_counts)} per applicant")
    
    # 3. Framework Usage
    print("\n3. A/B TEST FRAMEWORK")
    print("-" * 30)
    
    framework = ABTestFramework("demo_ab_test_data")
    
    # Create test
    print("Creating A/B test...")
    test = framework.create_test(test_config)
    print(f"Created test: {test.test_id}")
    
    # Start test
    print("Starting test...")
    framework.start_test(test.test_id)
    print(f"Test status: {test.status.value}")
    
    # Process applications
    print(f"\nProcessing {len(applications)} applications...")
    processed_count = 0
    
    for i, application in enumerate(applications):
        try:
            result = await framework.evaluate_application(test.test_id, application)
            processed_count += 1
            
            if i % 50 == 0:  # Progress update every 50 applications
                print(f"  Processed {i+1}/{len(applications)} applications...")
                
        except Exception as e:
            print(f"  Error processing application {i+1}: {e}")
    
    print(f"Successfully processed {processed_count} applications")
    
    # Stop test
    print("\nStopping test...")
    framework.stop_test(test.test_id)
    
    # 4. Statistical Analysis
    print("\n4. STATISTICAL ANALYSIS")
    print("-" * 30)
    
    # Get test summary
    summary = framework.get_test_summary(test.test_id)
    
    print(f"Test completed: {summary.test_id}")
    print(f"Status: {summary.status.value}")
    print(f"Duration: {summary.end_time - summary.start_time}")
    print(f"Control results: {len(summary.control_results)}")
    print(f"Treatment results: {len(summary.treatment_results)}")
    
    # Show statistical analysis
    if summary.statistical_analysis:
        print("\nStatistical Analysis Results:")
        for metric, analysis in summary.statistical_analysis.items():
            if metric == "metadata":
                continue
            
            print(f"\n  {metric.upper()}:")
            print(f"    Significant: {'Yes' if analysis.get('significant', False) else 'No'}")
            print(f"    Effect Size: {analysis.get('effect_size', 0):.4f}")
            print(f"    P-value: {analysis.get('p_value', 1.0):.4f}")
            
            if metric == "acceptance_rate":
                print(f"    Control Rate: {analysis.get('control_rate', 0):.3f}")
                print(f"    Treatment Rate: {analysis.get('treatment_rate', 0):.3f}")
                print(f"    Difference: {analysis.get('difference', 0):.3f}")
            elif metric == "avg_risk_score":
                print(f"    Control Mean: {analysis.get('control_mean', 0):.1f}")
                print(f"    Treatment Mean: {analysis.get('treatment_mean', 0):.1f}")
                print(f"    Difference: {analysis.get('difference', 0):.1f}")
    
    # Show conclusions and recommendations
    if summary.conclusions:
        print("\nConclusions:")
        for conclusion in summary.conclusions:
            print(f"  • {conclusion}")
    
    if summary.recommendations:
        print("\nRecommendations:")
        for recommendation in summary.recommendations:
            print(f"  • {recommendation}")
    
    # 5. Report Generation
    print("\n5. REPORT GENERATION")
    print("-" * 30)
    
    results_manager = ABTestResultsManager("demo_ab_test_data")
    
    # Save test results
    results_manager.save_test_results(test.test_id, summary)
    
    # Generate reports in different formats
    print("Generating reports...")
    
    try:
        # JSON report
        json_report = results_manager.generate_test_report(test.test_id, ReportFormat.JSON)
        print(f"  ✓ JSON report generated: {json_report.test_id}")
        
        # HTML report
        html_report = results_manager.generate_test_report(test.test_id, ReportFormat.HTML)
        print(f"  ✓ HTML report generated: {html_report.test_id}")
        
        # Markdown report
        md_report = results_manager.generate_test_report(test.test_id, ReportFormat.MARKDOWN)
        print(f"  ✓ Markdown report generated: {md_report.test_id}")
        
        print(f"\nReport Summary:")
        print(f"  Test: {json_report.test_name}")
        print(f"  Duration: {json_report.test_duration}")
        print(f"  Total Sample Size: {json_report.sample_sizes['total']}")
        
        print(f"\nSignificance Results:")
        for metric, significant in json_report.significance_summary.items():
            effect_size = json_report.effect_sizes.get(metric, 0)
            print(f"  {metric}: {'✓' if significant else '✗'} (effect: {effect_size:.4f})")
        
        if json_report.business_impact:
            print(f"\nBusiness Impact:")
            for metric, impact in json_report.business_impact.items():
                if isinstance(impact, dict) and "projected_impact" in impact:
                    print(f"  {metric}: {impact['projected_impact']}")
        
    except Exception as e:
        print(f"  Error generating reports: {e}")
    
    # 6. Power Analysis
    print("\n6. POWER ANALYSIS")
    print("-" * 30)
    
    # Calculate required sample size for different effect sizes
    from underwriting.ab_testing.statistics import StatisticalAnalyzer, StatisticalTestType
    
    analyzer = StatisticalAnalyzer()
    
    print("Sample size requirements for proportion test:")
    for effect_size in [0.05, 0.1, 0.15, 0.2]:
        sample_size = analyzer.calculate_required_sample_size(
            effect_size=effect_size,
            power=0.8,
            test_type=StatisticalTestType.PROPORTION_TEST
        )
        print(f"  Effect size {effect_size}: {sample_size} samples needed")
    
    # Calculate power for current test
    actual_sample_size = len(summary.control_results) + len(summary.treatment_results)
    power = analyzer.calculate_power(
        sample_size=actual_sample_size // 2,  # Per group
        effect_size=0.1,
        test_type=StatisticalTestType.PROPORTION_TEST
    )
    print(f"\nActual test power (effect size 0.1): {power:.3f}")
    
    print("\n" + "=" * 60)
    print("A/B TESTING DEMONSTRATION COMPLETE")
    print("=" * 60)
    
    print(f"\nFiles created in 'demo_ab_test_data' directory:")
    print(f"  - Test configuration and results")
    print(f"  - Statistical analysis data")
    print(f"  - Reports in JSON, HTML, and Markdown formats")
    print(f"\nUse the CLI commands to manage A/B tests in production:")
    print(f"  python -m underwriting.cli.main ab-list-configs")
    print(f"  python -m underwriting.cli.main ab-create-test conservative_vs_standard")
    print(f"  python -m underwriting.cli.main ab-test-status <test_id>")


if __name__ == "__main__":
    asyncio.run(demonstrate_ab_testing())