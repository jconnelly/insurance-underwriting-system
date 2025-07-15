"""
Results management and reporting for A/B testing framework.

This module provides comprehensive results storage, analysis, and reporting
capabilities for A/B testing experiments.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import pandas as pd
from loguru import logger

from .models import ABTestResult, ABTestStatus, ABTestConfiguration
from .statistics import StatisticalAnalyzer

# Late import to avoid circular dependencies
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .framework import ABTestSummary


class ReportFormat(Enum):
    """Report format options."""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    MARKDOWN = "markdown"


@dataclass
class ABTestReport:
    """Comprehensive A/B test report."""
    test_id: str
    test_name: str
    test_type: str
    generated_at: datetime
    test_duration: Optional[timedelta]
    sample_sizes: Dict[str, int]
    
    # Statistical results
    statistical_results: Dict[str, Any]
    significance_summary: Dict[str, bool]
    effect_sizes: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    
    # Business metrics
    business_impact: Dict[str, Any]
    cost_analysis: Optional[Dict[str, Any]] = None
    risk_analysis: Optional[Dict[str, Any]] = None
    
    # Recommendations
    conclusions: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class ABTestResultsManager:
    """A/B test results management system."""
    
    def __init__(self, storage_path: str = "ab_test_data"):
        """Initialize results manager.
        
        Args:
            storage_path: Path to store test results
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.results_dir = self.storage_path / "results"
        self.reports_dir = self.storage_path / "reports"
        self.configs_dir = self.storage_path / "configs"
        
        for dir_path in [self.results_dir, self.reports_dir, self.configs_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Initialize statistical analyzer
        self.statistical_analyzer = StatisticalAnalyzer()
        
        logger.info(f"A/B test results manager initialized at {storage_path}")
    
    def save_test_config(self, config: ABTestConfiguration) -> None:
        """Save test configuration.
        
        Args:
            config: Test configuration to save
        """
        config_file = self.configs_dir / f"{config.test_id}_config.json"
        
        config_data = asdict(config)
        config_data["created_at"] = config.created_at.isoformat()
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
        
        logger.debug(f"Saved test configuration: {config.test_id}")
    
    def save_test_result(self, result: ABTestResult) -> None:
        """Save individual test result.
        
        Args:
            result: Test result to save
        """
        # Create test-specific directory
        test_dir = self.results_dir / result.test_id
        test_dir.mkdir(exist_ok=True)
        
        # Save individual result
        result_file = test_dir / f"{result.application_id}.json"
        
        result_data = {
            "test_id": result.test_id,
            "variant": result.variant.value,
            "application_id": result.application_id,
            "decision": {
                "decision": result.decision.decision.value,
                "risk_score": result.decision.risk_score.overall_score,
                "reason": result.decision.reason
            },
            "processing_time": result.processing_time,
            "timestamp": result.timestamp.isoformat(),
            "metadata": result.metadata
        }
        
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        logger.debug(f"Saved test result: {result.test_id}/{result.application_id}")
    
    def save_test_results(self, test_id: str, summary: 'ABTestSummary') -> None:
        """Save complete test results.
        
        Args:
            test_id: Test identifier
            summary: Test summary with all results
        """
        # Create test-specific directory
        test_dir = self.results_dir / test_id
        test_dir.mkdir(exist_ok=True)
        
        # Save summary
        summary_file = test_dir / "summary.json"
        
        summary_data = {
            "test_id": summary.test_id,
            "status": summary.status.value,
            "start_time": summary.start_time.isoformat() if summary.start_time else None,
            "end_time": summary.end_time.isoformat() if summary.end_time else None,
            "control_results_count": len(summary.control_results),
            "treatment_results_count": len(summary.treatment_results),
            "statistical_analysis": summary.statistical_analysis,
            "conclusions": summary.conclusions,
            "recommendations": summary.recommendations,
            "generated_at": datetime.now().isoformat()
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        # Save detailed results as CSV for analysis
        self._save_results_csv(test_id, summary)
        
        logger.info(f"Saved test results: {test_id}")
    
    def _save_results_csv(self, test_id: str, summary: 'ABTestSummary') -> None:
        """Save results as CSV for analysis."""
        test_dir = self.results_dir / test_id
        
        # Prepare data for CSV
        data = []
        
        # Control results
        for result in summary.control_results:
            data.append({
                "test_id": result.test_id,
                "variant": result.variant.value,
                "application_id": result.application_id,
                "decision": result.decision.decision.value,
                "risk_score": result.decision.risk_score.overall_score,
                "processing_time": result.processing_time,
                "timestamp": result.timestamp.isoformat(),
                "rule_set": result.metadata.get("rule_set", ""),
                "engine_type": result.metadata.get("engine_type", "")
            })
        
        # Treatment results
        for result in summary.treatment_results:
            data.append({
                "test_id": result.test_id,
                "variant": result.variant.value,
                "application_id": result.application_id,
                "decision": result.decision.decision.value,
                "risk_score": result.decision.risk_score.overall_score,
                "processing_time": result.processing_time,
                "timestamp": result.timestamp.isoformat(),
                "rule_set": result.metadata.get("rule_set", ""),
                "engine_type": result.metadata.get("engine_type", "")
            })
        
        # Save as CSV
        df = pd.DataFrame(data)
        csv_file = test_dir / "results.csv"
        df.to_csv(csv_file, index=False)
        
        logger.debug(f"Saved results CSV: {csv_file}")
    
    def save_test_status(self, test_id: str, status: ABTestStatus) -> None:
        """Save test status.
        
        Args:
            test_id: Test identifier
            status: Test status
        """
        test_dir = self.results_dir / test_id
        test_dir.mkdir(exist_ok=True)
        
        status_file = test_dir / "status.json"
        
        status_data = {
            "test_id": test_id,
            "status": status.value,
            "updated_at": datetime.now().isoformat()
        }
        
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
        
        logger.debug(f"Updated test status: {test_id} -> {status.value}")
    
    def load_test_summary(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Load test summary.
        
        Args:
            test_id: Test identifier
            
        Returns:
            Test summary data or None if not found
        """
        summary_file = self.results_dir / test_id / "summary.json"
        
        if not summary_file.exists():
            return None
        
        try:
            with open(summary_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading test summary {test_id}: {e}")
            return None
    
    def load_test_results_csv(self, test_id: str) -> Optional[pd.DataFrame]:
        """Load test results as DataFrame.
        
        Args:
            test_id: Test identifier
            
        Returns:
            DataFrame with results or None if not found
        """
        csv_file = self.results_dir / test_id / "results.csv"
        
        if not csv_file.exists():
            return None
        
        try:
            return pd.read_csv(csv_file)
        except Exception as e:
            logger.error(f"Error loading test results CSV {test_id}: {e}")
            return None
    
    def generate_test_report(
        self, 
        test_id: str, 
        format: ReportFormat = ReportFormat.JSON,
        include_raw_data: bool = False
    ) -> ABTestReport:
        """Generate comprehensive test report.
        
        Args:
            test_id: Test identifier
            format: Report format
            include_raw_data: Include raw data in report
            
        Returns:
            Generated report
        """
        logger.info(f"Generating test report for {test_id}")
        
        # Load test data
        summary_data = self.load_test_summary(test_id)
        if not summary_data:
            raise ValueError(f"Test {test_id} not found")
        
        config_data = self._load_test_config(test_id)
        results_df = self.load_test_results_csv(test_id)
        
        # Calculate test duration
        test_duration = None
        if summary_data.get("start_time") and summary_data.get("end_time"):
            start_time = datetime.fromisoformat(summary_data["start_time"])
            end_time = datetime.fromisoformat(summary_data["end_time"])
            test_duration = end_time - start_time
        
        # Extract sample sizes
        sample_sizes = {
            "control": summary_data.get("control_results_count", 0),
            "treatment": summary_data.get("treatment_results_count", 0),
            "total": summary_data.get("control_results_count", 0) + summary_data.get("treatment_results_count", 0)
        }
        
        # Process statistical results
        statistical_analysis = summary_data.get("statistical_analysis", {})
        
        significance_summary = {}
        effect_sizes = {}
        confidence_intervals = {}
        
        for metric, analysis in statistical_analysis.items():
            if metric == "metadata":
                continue
            
            significance_summary[metric] = analysis.get("significant", False)
            effect_sizes[metric] = analysis.get("effect_size", 0.0)
            
            # Extract confidence interval
            ci = analysis.get("confidence_interval", [0, 0])
            if isinstance(ci, list) and len(ci) >= 2:
                confidence_intervals[metric] = (ci[0], ci[1])
            else:
                confidence_intervals[metric] = (0, 0)
        
        # Calculate business impact
        business_impact = self._calculate_business_impact(results_df, statistical_analysis)
        
        # Generate cost analysis if available
        cost_analysis = self._generate_cost_analysis(results_df, config_data)
        
        # Generate risk analysis
        risk_analysis = self._generate_risk_analysis(results_df, statistical_analysis)
        
        # Create report
        report = ABTestReport(
            test_id=test_id,
            test_name=config_data.get("name", test_id) if config_data else test_id,
            test_type=config_data.get("test_type", "unknown") if config_data else "unknown",
            generated_at=datetime.now(),
            test_duration=test_duration,
            sample_sizes=sample_sizes,
            statistical_results=statistical_analysis,
            significance_summary=significance_summary,
            effect_sizes=effect_sizes,
            confidence_intervals=confidence_intervals,
            business_impact=business_impact,
            cost_analysis=cost_analysis,
            risk_analysis=risk_analysis,
            conclusions=summary_data.get("conclusions", []),
            recommendations=summary_data.get("recommendations", []),
            next_steps=self._generate_next_steps(significance_summary, effect_sizes),
            metadata={
                "config": config_data,
                "raw_data_included": include_raw_data,
                "generated_by": "ABTestResultsManager"
            }
        )
        
        # Save report
        self._save_report(report, format)
        
        return report
    
    def _load_test_config(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Load test configuration."""
        config_file = self.configs_dir / f"{test_id}_config.json"
        
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading test config {test_id}: {e}")
            return None
    
    def _calculate_business_impact(self, results_df: Optional[pd.DataFrame], statistical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate business impact metrics."""
        if results_df is None:
            return {"error": "No results data available"}
        
        business_impact = {}
        
        # Calculate acceptance rate impact
        if "acceptance_rate" in statistical_analysis:
            acceptance_analysis = statistical_analysis["acceptance_rate"]
            control_rate = acceptance_analysis.get("control_rate", 0)
            treatment_rate = acceptance_analysis.get("treatment_rate", 0)
            
            business_impact["acceptance_rate"] = {
                "control_rate": control_rate,
                "treatment_rate": treatment_rate,
                "absolute_difference": treatment_rate - control_rate,
                "relative_improvement": acceptance_analysis.get("relative_improvement", 0),
                "projected_impact": f"{(treatment_rate - control_rate) * 100:.1f}% change in acceptance rate"
            }
        
        # Calculate risk score impact
        if "avg_risk_score" in statistical_analysis:
            risk_analysis = statistical_analysis["avg_risk_score"]
            control_score = risk_analysis.get("control_mean", 0)
            treatment_score = risk_analysis.get("treatment_mean", 0)
            
            business_impact["risk_score"] = {
                "control_avg": control_score,
                "treatment_avg": treatment_score,
                "absolute_difference": treatment_score - control_score,
                "relative_improvement": risk_analysis.get("relative_improvement", 0),
                "projected_impact": f"{treatment_score - control_score:.1f} point change in average risk score"
            }
        
        # Calculate processing time impact
        if "processing_time" in statistical_analysis:
            time_analysis = statistical_analysis["processing_time"]
            control_time = time_analysis.get("control_mean", 0)
            treatment_time = time_analysis.get("treatment_mean", 0)
            
            business_impact["processing_time"] = {
                "control_avg": control_time,
                "treatment_avg": treatment_time,
                "absolute_difference": treatment_time - control_time,
                "relative_improvement": time_analysis.get("relative_improvement", 0),
                "projected_impact": f"{(treatment_time - control_time) * 1000:.0f}ms change in processing time"
            }
        
        return business_impact
    
    def _generate_cost_analysis(self, results_df: Optional[pd.DataFrame], config_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate cost analysis."""
        if not results_df is not None or not config_data:
            return None
        
        cost_analysis = {}
        
        # Analyze AI costs if applicable
        if config_data.get("treatment_config", {}).get("ai_enabled"):
            # Estimate AI costs based on processing time and requests
            treatment_results = results_df[results_df['variant'] == 'treatment']
            
            if len(treatment_results) > 0:
                avg_processing_time = treatment_results['processing_time'].mean()
                total_requests = len(treatment_results)
                
                # Rough cost estimation (this would need real pricing data)
                estimated_cost_per_request = 0.001  # $0.001 per request
                total_estimated_cost = total_requests * estimated_cost_per_request
                
                cost_analysis["ai_costs"] = {
                    "total_requests": total_requests,
                    "avg_processing_time": avg_processing_time,
                    "estimated_cost_per_request": estimated_cost_per_request,
                    "total_estimated_cost": total_estimated_cost,
                    "cost_per_application": total_estimated_cost / total_requests if total_requests > 0 else 0
                }
        
        return cost_analysis if cost_analysis else None
    
    def _generate_risk_analysis(self, results_df: Optional[pd.DataFrame], statistical_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate risk analysis."""
        if results_df is None:
            return None
        
        risk_analysis = {}
        
        # Analyze decision distribution
        control_results = results_df[results_df['variant'] == 'control']
        treatment_results = results_df[results_df['variant'] == 'treatment']
        
        if len(control_results) > 0 and len(treatment_results) > 0:
            control_decisions = control_results['decision'].value_counts(normalize=True)
            treatment_decisions = treatment_results['decision'].value_counts(normalize=True)
            
            risk_analysis["decision_distribution"] = {
                "control": control_decisions.to_dict(),
                "treatment": treatment_decisions.to_dict(),
                "changes": {}
            }
            
            # Calculate changes
            for decision in ["ACCEPT", "DENY", "ADJUDICATE"]:
                control_pct = control_decisions.get(decision, 0)
                treatment_pct = treatment_decisions.get(decision, 0)
                risk_analysis["decision_distribution"]["changes"][decision] = treatment_pct - control_pct
        
        # Analyze risk score distribution
        if len(control_results) > 0 and len(treatment_results) > 0:
            control_risk_scores = control_results['risk_score']
            treatment_risk_scores = treatment_results['risk_score']
            
            risk_analysis["risk_score_distribution"] = {
                "control": {
                    "mean": control_risk_scores.mean(),
                    "std": control_risk_scores.std(),
                    "median": control_risk_scores.median(),
                    "min": control_risk_scores.min(),
                    "max": control_risk_scores.max()
                },
                "treatment": {
                    "mean": treatment_risk_scores.mean(),
                    "std": treatment_risk_scores.std(),
                    "median": treatment_risk_scores.median(),
                    "min": treatment_risk_scores.min(),
                    "max": treatment_risk_scores.max()
                }
            }
        
        return risk_analysis if risk_analysis else None
    
    def _generate_next_steps(self, significance_summary: Dict[str, bool], effect_sizes: Dict[str, float]) -> List[str]:
        """Generate next steps based on results."""
        next_steps = []
        
        # Check for significant results
        significant_metrics = [metric for metric, significant in significance_summary.items() if significant]
        
        if significant_metrics:
            next_steps.append(f"Significant results found for: {', '.join(significant_metrics)}")
            
            # Check effect sizes
            large_effects = [metric for metric in significant_metrics if abs(effect_sizes.get(metric, 0)) > 0.2]
            if large_effects:
                next_steps.append(f"Large effect sizes detected for: {', '.join(large_effects)} - consider rollout")
            
            next_steps.append("Validate results with additional testing if needed")
            next_steps.append("Consider gradual rollout to production")
        else:
            next_steps.append("No significant differences found")
            next_steps.append("Consider increasing sample size or effect size")
            next_steps.append("Evaluate if the test design needs refinement")
        
        next_steps.append("Document learnings for future tests")
        next_steps.append("Plan follow-up experiments if needed")
        
        return next_steps
    
    def _save_report(self, report: ABTestReport, format: ReportFormat) -> None:
        """Save report in specified format."""
        report_file = self.reports_dir / f"{report.test_id}_report.{format.value}"
        
        if format == ReportFormat.JSON:
            with open(report_file, 'w') as f:
                json.dump(asdict(report), f, indent=2, default=str)
        
        elif format == ReportFormat.HTML:
            html_content = self._generate_html_report(report)
            with open(report_file, 'w') as f:
                f.write(html_content)
        
        elif format == ReportFormat.MARKDOWN:
            md_content = self._generate_markdown_report(report)
            with open(report_file, 'w') as f:
                f.write(md_content)
        
        logger.info(f"Saved report: {report_file}")
    
    def _generate_html_report(self, report: ABTestReport) -> str:
        """Generate HTML report."""
        html = f"""
        <html>
        <head>
            <title>A/B Test Report: {report.test_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333; }}
                .metric {{ margin: 10px 0; }}
                .significant {{ color: green; font-weight: bold; }}
                .not-significant {{ color: red; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>A/B Test Report: {report.test_name}</h1>
            
            <h2>Test Overview</h2>
            <p><strong>Test ID:</strong> {report.test_id}</p>
            <p><strong>Test Type:</strong> {report.test_type}</p>
            <p><strong>Generated:</strong> {report.generated_at}</p>
            <p><strong>Duration:</strong> {report.test_duration or 'N/A'}</p>
            
            <h2>Sample Sizes</h2>
            <table>
                <tr><th>Variant</th><th>Sample Size</th></tr>
                <tr><td>Control</td><td>{report.sample_sizes.get('control', 0)}</td></tr>
                <tr><td>Treatment</td><td>{report.sample_sizes.get('treatment', 0)}</td></tr>
                <tr><td>Total</td><td>{report.sample_sizes.get('total', 0)}</td></tr>
            </table>
            
            <h2>Statistical Results</h2>
            <table>
                <tr><th>Metric</th><th>Significant</th><th>Effect Size</th></tr>
        """
        
        for metric in report.significance_summary:
            significant = report.significance_summary[metric]
            effect_size = report.effect_sizes.get(metric, 0)
            sig_class = "significant" if significant else "not-significant"
            
            html += f"""
                <tr>
                    <td>{metric}</td>
                    <td class="{sig_class}">{'Yes' if significant else 'No'}</td>
                    <td>{effect_size:.4f}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>Conclusions</h2>
            <ul>
        """
        
        for conclusion in report.conclusions:
            html += f"<li>{conclusion}</li>"
        
        html += """
            </ul>
            
            <h2>Recommendations</h2>
            <ul>
        """
        
        for recommendation in report.recommendations:
            html += f"<li>{recommendation}</li>"
        
        html += """
            </ul>
            </body>
        </html>
        """
        
        return html
    
    def _generate_markdown_report(self, report: ABTestReport) -> str:
        """Generate Markdown report."""
        md = f"""# A/B Test Report: {report.test_name}

## Test Overview
- **Test ID:** {report.test_id}
- **Test Type:** {report.test_type}
- **Generated:** {report.generated_at}
- **Duration:** {report.test_duration or 'N/A'}

## Sample Sizes
| Variant | Sample Size |
|---------|-------------|
| Control | {report.sample_sizes.get('control', 0)} |
| Treatment | {report.sample_sizes.get('treatment', 0)} |
| Total | {report.sample_sizes.get('total', 0)} |

## Statistical Results
| Metric | Significant | Effect Size |
|--------|-------------|-------------|
"""
        
        for metric in report.significance_summary:
            significant = "✓" if report.significance_summary[metric] else "✗"
            effect_size = report.effect_sizes.get(metric, 0)
            md += f"| {metric} | {significant} | {effect_size:.4f} |\n"
        
        md += "\n## Conclusions\n"
        for conclusion in report.conclusions:
            md += f"- {conclusion}\n"
        
        md += "\n## Recommendations\n"
        for recommendation in report.recommendations:
            md += f"- {recommendation}\n"
        
        md += "\n## Next Steps\n"
        for step in report.next_steps:
            md += f"- {step}\n"
        
        return md
    
    def list_completed_tests(self) -> List[Dict[str, Any]]:
        """List all completed tests.
        
        Returns:
            List of test information
        """
        tests = []
        
        for test_dir in self.results_dir.iterdir():
            if test_dir.is_dir():
                summary_file = test_dir / "summary.json"
                if summary_file.exists():
                    try:
                        with open(summary_file, 'r') as f:
                            summary = json.load(f)
                        
                        tests.append({
                            "test_id": summary["test_id"],
                            "status": summary["status"],
                            "start_time": summary.get("start_time"),
                            "end_time": summary.get("end_time"),
                            "control_results": summary.get("control_results_count", 0),
                            "treatment_results": summary.get("treatment_results_count", 0)
                        })
                    except Exception as e:
                        logger.error(f"Error reading test summary {test_dir.name}: {e}")
        
        return tests
    
    def cleanup_old_results(self, days: int = 30) -> int:
        """Clean up old test results.
        
        Args:
            days: Number of days to keep results
            
        Returns:
            Number of tests cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        for test_dir in self.results_dir.iterdir():
            if test_dir.is_dir():
                # Check if test is old enough to clean up
                if test_dir.stat().st_mtime < cutoff_date.timestamp():
                    try:
                        import shutil
                        shutil.rmtree(test_dir)
                        cleaned_count += 1
                        logger.info(f"Cleaned up old test results: {test_dir.name}")
                    except Exception as e:
                        logger.error(f"Error cleaning up {test_dir.name}: {e}")
        
        return cleaned_count