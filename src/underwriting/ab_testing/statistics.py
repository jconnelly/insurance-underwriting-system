"""
Statistical analysis engine for A/B testing framework.

This module provides comprehensive statistical analysis capabilities for
A/B testing results, including significance testing, confidence intervals,
and effect size calculations.
"""

import math
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import scipy.stats as stats
from scipy.stats import chi2_contingency, ttest_ind, mannwhitneyu
from loguru import logger

from .models import ABTestResult, ABTestVariant
from ..core.models import DecisionType


class StatisticalTestType(Enum):
    """Statistical test types."""
    CHI_SQUARE = "chi_square"
    T_TEST = "t_test"
    MANN_WHITNEY = "mann_whitney"
    PROPORTION_TEST = "proportion_test"


@dataclass
class StatisticalTest:
    """Statistical test result."""
    test_type: StatisticalTestType
    statistic: float
    p_value: float
    significant: bool
    confidence_level: float
    effect_size: float
    confidence_interval: Tuple[float, float]
    power: Optional[float] = None
    metadata: Dict[str, Any] = None


class StatisticalAnalyzer:
    """Statistical analysis engine for A/B testing."""
    
    def __init__(self, confidence_level: float = 0.95, minimum_effect_size: float = 0.05):
        """Initialize statistical analyzer.
        
        Args:
            confidence_level: Confidence level for significance testing
            minimum_effect_size: Minimum effect size to consider meaningful
        """
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level
        self.minimum_effect_size = minimum_effect_size
        
        logger.info(f"Statistical analyzer initialized with confidence level: {confidence_level}")
    
    def analyze_results(
        self, 
        control_results: List[ABTestResult], 
        treatment_results: List[ABTestResult],
        metrics: List[str]
    ) -> Dict[str, Any]:
        """Analyze A/B test results for specified metrics.
        
        Args:
            control_results: Control group results
            treatment_results: Treatment group results
            metrics: List of metrics to analyze
            
        Returns:
            Statistical analysis results
        """
        analysis = {}
        
        # Calculate sample sizes
        control_n = len(control_results)
        treatment_n = len(treatment_results)
        
        logger.info(f"Analyzing A/B test results: control={control_n}, treatment={treatment_n}")
        
        # Analyze each metric
        for metric in metrics:
            try:
                if metric == "acceptance_rate":
                    analysis[metric] = self._analyze_acceptance_rate(control_results, treatment_results)
                elif metric == "avg_risk_score":
                    analysis[metric] = self._analyze_avg_risk_score(control_results, treatment_results)
                elif metric == "decision_distribution":
                    analysis[metric] = self._analyze_decision_distribution(control_results, treatment_results)
                elif metric == "processing_time":
                    analysis[metric] = self._analyze_processing_time(control_results, treatment_results)
                else:
                    logger.warning(f"Unknown metric: {metric}")
            except Exception as e:
                logger.error(f"Error analyzing metric {metric}: {e}")
                analysis[metric] = {"error": str(e)}
        
        # Add metadata
        analysis["metadata"] = {
            "control_sample_size": control_n,
            "treatment_sample_size": treatment_n,
            "total_sample_size": control_n + treatment_n,
            "confidence_level": self.confidence_level,
            "minimum_effect_size": self.minimum_effect_size
        }
        
        return analysis
    
    def _analyze_acceptance_rate(
        self, 
        control_results: List[ABTestResult], 
        treatment_results: List[ABTestResult]
    ) -> Dict[str, Any]:
        """Analyze acceptance rate difference between groups."""
        # Calculate acceptance rates
        control_accepts = sum(1 for r in control_results if r.decision.decision == DecisionType.ACCEPT)
        treatment_accepts = sum(1 for r in treatment_results if r.decision.decision == DecisionType.ACCEPT)
        
        control_rate = control_accepts / len(control_results) if control_results else 0
        treatment_rate = treatment_accepts / len(treatment_results) if treatment_results else 0
        
        # Perform proportion test
        test_result = self._proportion_test(
            control_accepts, len(control_results),
            treatment_accepts, len(treatment_results)
        )
        
        return {
            "control_rate": control_rate,
            "treatment_rate": treatment_rate,
            "difference": treatment_rate - control_rate,
            "relative_improvement": ((treatment_rate - control_rate) / control_rate * 100) if control_rate > 0 else 0,
            "test_result": test_result.__dict__,
            "significant": test_result.significant,
            "effect_size": test_result.effect_size,
            "confidence_interval": test_result.confidence_interval,
            "p_value": test_result.p_value
        }
    
    def _analyze_avg_risk_score(
        self, 
        control_results: List[ABTestResult], 
        treatment_results: List[ABTestResult]
    ) -> Dict[str, Any]:
        """Analyze average risk score difference between groups."""
        # Extract risk scores
        control_scores = [r.decision.risk_score.overall_score for r in control_results]
        treatment_scores = [r.decision.risk_score.overall_score for r in treatment_results]
        
        # Calculate means and standard deviations
        control_mean = np.mean(control_scores) if control_scores else 0
        treatment_mean = np.mean(treatment_scores) if treatment_scores else 0
        control_std = np.std(control_scores, ddof=1) if len(control_scores) > 1 else 0
        treatment_std = np.std(treatment_scores, ddof=1) if len(treatment_scores) > 1 else 0
        
        # Perform t-test
        test_result = self._t_test(control_scores, treatment_scores)
        
        return {
            "control_mean": control_mean,
            "treatment_mean": treatment_mean,
            "control_std": control_std,
            "treatment_std": treatment_std,
            "difference": treatment_mean - control_mean,
            "relative_improvement": ((treatment_mean - control_mean) / control_mean * 100) if control_mean > 0 else 0,
            "test_result": test_result.__dict__,
            "significant": test_result.significant,
            "effect_size": test_result.effect_size,
            "confidence_interval": test_result.confidence_interval,
            "p_value": test_result.p_value
        }
    
    def _analyze_decision_distribution(
        self, 
        control_results: List[ABTestResult], 
        treatment_results: List[ABTestResult]
    ) -> Dict[str, Any]:
        """Analyze decision distribution difference between groups."""
        # Count decisions for each group
        control_decisions = {"ACCEPT": 0, "DENY": 0, "ADJUDICATE": 0}
        treatment_decisions = {"ACCEPT": 0, "DENY": 0, "ADJUDICATE": 0}
        
        for result in control_results:
            control_decisions[result.decision.decision.value] += 1
        
        for result in treatment_results:
            treatment_decisions[result.decision.decision.value] += 1
        
        # Calculate proportions
        control_total = len(control_results)
        treatment_total = len(treatment_results)
        
        control_props = {k: v / control_total for k, v in control_decisions.items()} if control_total > 0 else {}
        treatment_props = {k: v / treatment_total for k, v in treatment_decisions.items()} if treatment_total > 0 else {}
        
        # Perform chi-square test
        test_result = self._chi_square_test(control_decisions, treatment_decisions)
        
        return {
            "control_distribution": control_decisions,
            "treatment_distribution": treatment_decisions,
            "control_proportions": control_props,
            "treatment_proportions": treatment_props,
            "test_result": test_result.__dict__,
            "significant": test_result.significant,
            "effect_size": test_result.effect_size,
            "p_value": test_result.p_value
        }
    
    def _analyze_processing_time(
        self, 
        control_results: List[ABTestResult], 
        treatment_results: List[ABTestResult]
    ) -> Dict[str, Any]:
        """Analyze processing time difference between groups."""
        # Extract processing times
        control_times = [r.processing_time for r in control_results]
        treatment_times = [r.processing_time for r in treatment_results]
        
        # Calculate means and standard deviations
        control_mean = np.mean(control_times) if control_times else 0
        treatment_mean = np.mean(treatment_times) if treatment_times else 0
        control_std = np.std(control_times, ddof=1) if len(control_times) > 1 else 0
        treatment_std = np.std(treatment_times, ddof=1) if len(treatment_times) > 1 else 0
        
        # Perform Mann-Whitney U test (non-parametric)
        test_result = self._mann_whitney_test(control_times, treatment_times)
        
        return {
            "control_mean": control_mean,
            "treatment_mean": treatment_mean,
            "control_std": control_std,
            "treatment_std": treatment_std,
            "difference": treatment_mean - control_mean,
            "relative_improvement": ((treatment_mean - control_mean) / control_mean * 100) if control_mean > 0 else 0,
            "test_result": test_result.__dict__,
            "significant": test_result.significant,
            "effect_size": test_result.effect_size,
            "confidence_interval": test_result.confidence_interval,
            "p_value": test_result.p_value
        }
    
    def _proportion_test(
        self, 
        control_success: int, 
        control_total: int,
        treatment_success: int, 
        treatment_total: int
    ) -> StatisticalTest:
        """Perform two-proportion z-test."""
        if control_total == 0 or treatment_total == 0:
            return StatisticalTest(
                test_type=StatisticalTestType.PROPORTION_TEST,
                statistic=0,
                p_value=1.0,
                significant=False,
                confidence_level=self.confidence_level,
                effect_size=0,
                confidence_interval=(0, 0)
            )
        
        # Calculate proportions
        p1 = control_success / control_total
        p2 = treatment_success / treatment_total
        
        # Pool proportion
        p_pool = (control_success + treatment_success) / (control_total + treatment_total)
        
        # Calculate standard error
        se = math.sqrt(p_pool * (1 - p_pool) * (1/control_total + 1/treatment_total))
        
        # Calculate z-statistic
        z_stat = (p2 - p1) / se if se > 0 else 0
        
        # Calculate p-value (two-tailed)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        # Calculate effect size (Cohen's h)
        effect_size = 2 * (math.asin(math.sqrt(p2)) - math.asin(math.sqrt(p1)))
        
        # Calculate confidence interval for difference
        se_diff = math.sqrt(p1 * (1 - p1) / control_total + p2 * (1 - p2) / treatment_total)
        z_critical = stats.norm.ppf(1 - self.alpha / 2)
        margin_error = z_critical * se_diff
        diff = p2 - p1
        confidence_interval = (diff - margin_error, diff + margin_error)
        
        return StatisticalTest(
            test_type=StatisticalTestType.PROPORTION_TEST,
            statistic=z_stat,
            p_value=p_value,
            significant=p_value < self.alpha,
            confidence_level=self.confidence_level,
            effect_size=effect_size,
            confidence_interval=confidence_interval,
            metadata={
                "control_proportion": p1,
                "treatment_proportion": p2,
                "pooled_proportion": p_pool
            }
        )
    
    def _t_test(self, control_data: List[float], treatment_data: List[float]) -> StatisticalTest:
        """Perform independent t-test."""
        if len(control_data) < 2 or len(treatment_data) < 2:
            return StatisticalTest(
                test_type=StatisticalTestType.T_TEST,
                statistic=0,
                p_value=1.0,
                significant=False,
                confidence_level=self.confidence_level,
                effect_size=0,
                confidence_interval=(0, 0)
            )
        
        # Perform t-test
        t_stat, p_value = ttest_ind(treatment_data, control_data)
        
        # Calculate effect size (Cohen's d)
        control_mean = np.mean(control_data)
        treatment_mean = np.mean(treatment_data)
        pooled_std = math.sqrt(((len(control_data) - 1) * np.var(control_data, ddof=1) + 
                               (len(treatment_data) - 1) * np.var(treatment_data, ddof=1)) / 
                              (len(control_data) + len(treatment_data) - 2))
        
        effect_size = (treatment_mean - control_mean) / pooled_std if pooled_std > 0 else 0
        
        # Calculate confidence interval for difference
        se = math.sqrt(np.var(control_data, ddof=1) / len(control_data) + 
                      np.var(treatment_data, ddof=1) / len(treatment_data))
        df = len(control_data) + len(treatment_data) - 2
        t_critical = stats.t.ppf(1 - self.alpha / 2, df)
        margin_error = t_critical * se
        diff = treatment_mean - control_mean
        confidence_interval = (diff - margin_error, diff + margin_error)
        
        return StatisticalTest(
            test_type=StatisticalTestType.T_TEST,
            statistic=t_stat,
            p_value=p_value,
            significant=p_value < self.alpha,
            confidence_level=self.confidence_level,
            effect_size=effect_size,
            confidence_interval=confidence_interval,
            metadata={
                "degrees_of_freedom": df,
                "pooled_std": pooled_std
            }
        )
    
    def _mann_whitney_test(self, control_data: List[float], treatment_data: List[float]) -> StatisticalTest:
        """Perform Mann-Whitney U test."""
        if len(control_data) < 2 or len(treatment_data) < 2:
            return StatisticalTest(
                test_type=StatisticalTestType.MANN_WHITNEY,
                statistic=0,
                p_value=1.0,
                significant=False,
                confidence_level=self.confidence_level,
                effect_size=0,
                confidence_interval=(0, 0)
            )
        
        # Perform Mann-Whitney U test
        u_stat, p_value = mannwhitneyu(treatment_data, control_data, alternative='two-sided')
        
        # Calculate effect size (rank-biserial correlation)
        n1, n2 = len(control_data), len(treatment_data)
        effect_size = 1 - (2 * u_stat) / (n1 * n2)
        
        # Calculate confidence interval for medians difference (approximation)
        control_median = np.median(control_data)
        treatment_median = np.median(treatment_data)
        diff = treatment_median - control_median
        
        # Simple approximation for confidence interval
        confidence_interval = (diff - abs(diff) * 0.2, diff + abs(diff) * 0.2)
        
        return StatisticalTest(
            test_type=StatisticalTestType.MANN_WHITNEY,
            statistic=u_stat,
            p_value=p_value,
            significant=p_value < self.alpha,
            confidence_level=self.confidence_level,
            effect_size=effect_size,
            confidence_interval=confidence_interval,
            metadata={
                "control_median": control_median,
                "treatment_median": treatment_median
            }
        )
    
    def _chi_square_test(self, control_counts: Dict[str, int], treatment_counts: Dict[str, int]) -> StatisticalTest:
        """Perform chi-square test of independence."""
        # Create contingency table
        categories = list(set(control_counts.keys()) | set(treatment_counts.keys()))
        
        control_values = [control_counts.get(cat, 0) for cat in categories]
        treatment_values = [treatment_counts.get(cat, 0) for cat in categories]
        
        contingency_table = np.array([control_values, treatment_values])
        
        # Check if test is valid (expected frequencies >= 5)
        if np.any(contingency_table < 5):
            logger.warning("Chi-square test may not be valid due to low expected frequencies")
        
        # Perform chi-square test
        try:
            chi2_stat, p_value, dof, expected = chi2_contingency(contingency_table)
            
            # Calculate effect size (Cramer's V)
            n = np.sum(contingency_table)
            min_dim = min(contingency_table.shape) - 1
            effect_size = math.sqrt(chi2_stat / (n * min_dim)) if n > 0 and min_dim > 0 else 0
            
            return StatisticalTest(
                test_type=StatisticalTestType.CHI_SQUARE,
                statistic=chi2_stat,
                p_value=p_value,
                significant=p_value < self.alpha,
                confidence_level=self.confidence_level,
                effect_size=effect_size,
                confidence_interval=(0, 0),  # Not applicable for chi-square
                metadata={
                    "degrees_of_freedom": dof,
                    "expected_frequencies": expected.tolist(),
                    "contingency_table": contingency_table.tolist()
                }
            )
            
        except Exception as e:
            logger.error(f"Chi-square test failed: {e}")
            return StatisticalTest(
                test_type=StatisticalTestType.CHI_SQUARE,
                statistic=0,
                p_value=1.0,
                significant=False,
                confidence_level=self.confidence_level,
                effect_size=0,
                confidence_interval=(0, 0),
                metadata={"error": str(e)}
            )
    
    def calculate_required_sample_size(
        self, 
        effect_size: float, 
        power: float = 0.8, 
        test_type: StatisticalTestType = StatisticalTestType.PROPORTION_TEST
    ) -> int:
        """Calculate required sample size for given effect size and power."""
        if test_type == StatisticalTestType.PROPORTION_TEST:
            # For proportion test
            z_alpha = stats.norm.ppf(1 - self.alpha / 2)
            z_beta = stats.norm.ppf(power)
            
            # Assuming equal sample sizes and baseline proportion of 0.5
            p1 = 0.5
            p2 = p1 + effect_size
            p_avg = (p1 + p2) / 2
            
            n = (z_alpha * math.sqrt(2 * p_avg * (1 - p_avg)) + 
                 z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / (effect_size ** 2)
            
            return max(int(math.ceil(n)), 10)
        
        else:
            # For t-test (Cohen's d)
            z_alpha = stats.norm.ppf(1 - self.alpha / 2)
            z_beta = stats.norm.ppf(power)
            
            n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
            return max(int(math.ceil(n)), 10)
    
    def calculate_power(
        self, 
        sample_size: int, 
        effect_size: float, 
        test_type: StatisticalTestType = StatisticalTestType.PROPORTION_TEST
    ) -> float:
        """Calculate statistical power for given sample size and effect size."""
        if test_type == StatisticalTestType.PROPORTION_TEST:
            # For proportion test
            z_alpha = stats.norm.ppf(1 - self.alpha / 2)
            
            # Assuming equal sample sizes and baseline proportion of 0.5
            p1 = 0.5
            p2 = p1 + effect_size
            p_avg = (p1 + p2) / 2
            
            se_null = math.sqrt(2 * p_avg * (1 - p_avg) / sample_size)
            se_alt = math.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / sample_size)
            
            z_beta = (z_alpha * se_null - effect_size) / se_alt
            power = 1 - stats.norm.cdf(z_beta)
            
            return max(0, min(1, power))
        
        else:
            # For t-test
            z_alpha = stats.norm.ppf(1 - self.alpha / 2)
            z_beta = effect_size * math.sqrt(sample_size / 2) - z_alpha
            power = 1 - stats.norm.cdf(z_beta)
            
            return max(0, min(1, power))