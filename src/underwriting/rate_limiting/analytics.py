"""
Usage analytics and reporting for rate limiting system.

This module provides comprehensive analytics and reporting capabilities including:
- Usage trend analysis
- Performance metrics
- Alert generation
- Reporting dashboards
- Predictive analytics
"""

import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from .storage import RateLimitStorage, UsageRecord


@dataclass
class UsageAlert:
    """Alert for unusual usage patterns."""
    alert_type: str
    identifier: str
    operation_type: str
    message: str
    severity: str  # low, medium, high, critical
    threshold_value: float
    current_value: float
    timestamp: float
    details: Dict[str, Any]


@dataclass
class UsageTrend:
    """Usage trend analysis."""
    identifier: str
    operation_type: str
    period: str  # hour, day, week, month
    trend_direction: str  # increasing, decreasing, stable
    trend_strength: float  # 0.0 to 1.0
    current_rate: float
    predicted_rate: float
    confidence: float


@dataclass
class PerformanceMetric:
    """Performance metric for rate limiting."""
    metric_name: str
    value: float
    unit: str
    timestamp: float
    metadata: Dict[str, Any]


class UsageAnalytics:
    """Usage analytics and reporting system."""
    
    def __init__(self, storage: RateLimitStorage, config: Dict[str, Any]):
        """Initialize usage analytics.
        
        Args:
            storage: Rate limit storage instance
            config: Analytics configuration
        """
        self.storage = storage
        self.config = config
        self.enabled = config.get("enabled", True)
        self.detailed_tracking = config.get("detailed_tracking", True)
        self.retention_days = config.get("retention_days", 365)
        
        # Alert configuration
        self.alert_config = config.get("alerts", {})
        self.usage_threshold = self.alert_config.get("usage_threshold_percent", 80)
        self.burst_threshold = self.alert_config.get("burst_threshold_percent", 90)
        self.consecutive_hits = self.alert_config.get("consecutive_limit_hits", 5)
        
        # Analytics storage
        self.analytics_dir = storage.data_directory / "analytics"
        self.analytics_dir.mkdir(exist_ok=True)
        
        # Initialize analytics data
        self._initialize_analytics()
        
        logger.info("Usage analytics system initialized")
    
    def _initialize_analytics(self):
        """Initialize analytics data structures."""
        # Create analytics files if they don't exist
        files_to_create = [
            "usage_trends.json",
            "performance_metrics.json",
            "alerts.json",
            "reports.json"
        ]
        
        for filename in files_to_create:
            file_path = self.analytics_dir / filename
            if not file_path.exists():
                initial_data = {
                    "created": time.time(),
                    "last_updated": time.time(),
                    "data": []
                }
                with open(file_path, 'w') as f:
                    json.dump(initial_data, f, indent=2)
    
    def analyze_usage_patterns(self, identifier: str, operation_type: str,
                             hours_back: int = 24) -> Dict[str, Any]:
        """Analyze usage patterns for an identifier and operation type.
        
        Args:
            identifier: Unique identifier
            operation_type: Operation type
            hours_back: Hours of history to analyze
            
        Returns:
            Dictionary containing usage pattern analysis
        """
        try:
            end_time = time.time()
            start_time = end_time - (hours_back * 3600)
            
            # Get usage records in the time window
            usage_records = self.storage.get_usage_in_window(
                identifier, operation_type, start_time, end_time
            )
            
            if not usage_records:
                return {
                    "identifier": identifier,
                    "operation_type": operation_type,
                    "analysis_period_hours": hours_back,
                    "total_usage": 0,
                    "patterns": {}
                }
            
            # Basic statistics
            total_usage = sum(record.resource_consumed for record in usage_records)
            usage_rate = total_usage / hours_back  # usage per hour
            
            # Time-based patterns
            hourly_usage = self._analyze_hourly_patterns(usage_records)
            peak_hours = self._identify_peak_hours(hourly_usage)
            
            # Usage distribution
            usage_distribution = self._analyze_usage_distribution(usage_records)
            
            # Anomaly detection
            anomalies = self._detect_anomalies(usage_records)
            
            # Trend analysis
            trend = self._analyze_trend(usage_records)
            
            return {
                "identifier": identifier,
                "operation_type": operation_type,
                "analysis_period_hours": hours_back,
                "total_usage": total_usage,
                "usage_rate_per_hour": usage_rate,
                "patterns": {
                    "hourly_usage": hourly_usage,
                    "peak_hours": peak_hours,
                    "usage_distribution": usage_distribution,
                    "anomalies": anomalies,
                    "trend": trend
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing usage patterns: {e}")
            return {"error": str(e)}
    
    def _analyze_hourly_patterns(self, usage_records: List[UsageRecord]) -> Dict[int, int]:
        """Analyze hourly usage patterns."""
        hourly_usage = {}
        
        for record in usage_records:
            hour = datetime.fromtimestamp(record.timestamp).hour
            if hour not in hourly_usage:
                hourly_usage[hour] = 0
            hourly_usage[hour] += record.resource_consumed
        
        return hourly_usage
    
    def _identify_peak_hours(self, hourly_usage: Dict[int, int]) -> List[int]:
        """Identify peak usage hours."""
        if not hourly_usage:
            return []
        
        # Calculate average usage
        avg_usage = sum(hourly_usage.values()) / len(hourly_usage)
        
        # Find hours with usage above average
        peak_hours = [
            hour for hour, usage in hourly_usage.items()
            if usage > avg_usage * 1.5  # 50% above average
        ]
        
        return sorted(peak_hours)
    
    def _analyze_usage_distribution(self, usage_records: List[UsageRecord]) -> Dict[str, float]:
        """Analyze usage distribution statistics."""
        if not usage_records:
            return {}
        
        usage_values = [record.resource_consumed for record in usage_records]
        
        return {
            "mean": statistics.mean(usage_values),
            "median": statistics.median(usage_values),
            "std_dev": statistics.stdev(usage_values) if len(usage_values) > 1 else 0,
            "min": min(usage_values),
            "max": max(usage_values),
            "total_requests": len(usage_records)
        }
    
    def _detect_anomalies(self, usage_records: List[UsageRecord]) -> List[Dict[str, Any]]:
        """Detect anomalies in usage patterns."""
        anomalies = []
        
        if len(usage_records) < 10:  # Need minimum data for anomaly detection
            return anomalies
        
        usage_values = [record.resource_consumed for record in usage_records]
        mean_usage = statistics.mean(usage_values)
        std_dev = statistics.stdev(usage_values) if len(usage_values) > 1 else 0
        
        # Z-score based anomaly detection
        threshold = 2.5  # Standard deviations
        
        for record in usage_records:
            if std_dev > 0:
                z_score = abs(record.resource_consumed - mean_usage) / std_dev
                if z_score > threshold:
                    anomalies.append({
                        "timestamp": record.timestamp,
                        "timestamp_human": datetime.fromtimestamp(record.timestamp).isoformat(),
                        "usage": record.resource_consumed,
                        "z_score": z_score,
                        "type": "outlier"
                    })
        
        return anomalies
    
    def _analyze_trend(self, usage_records: List[UsageRecord]) -> Dict[str, Any]:
        """Analyze usage trend over time."""
        if len(usage_records) < 5:
            return {"trend": "insufficient_data"}
        
        # Sort by timestamp
        sorted_records = sorted(usage_records, key=lambda x: x.timestamp)
        
        # Calculate moving averages
        window_size = min(len(sorted_records) // 4, 10)
        if window_size < 2:
            return {"trend": "insufficient_data"}
        
        early_avg = statistics.mean([r.resource_consumed for r in sorted_records[:window_size]])
        late_avg = statistics.mean([r.resource_consumed for r in sorted_records[-window_size:]])
        
        # Determine trend direction
        if late_avg > early_avg * 1.1:  # 10% increase
            trend = "increasing"
        elif late_avg < early_avg * 0.9:  # 10% decrease
            trend = "decreasing"
        else:
            trend = "stable"
        
        # Calculate trend strength
        if early_avg > 0:
            trend_strength = abs(late_avg - early_avg) / early_avg
        else:
            trend_strength = 0
        
        return {
            "trend": trend,
            "trend_strength": min(trend_strength, 1.0),
            "early_average": early_avg,
            "late_average": late_avg,
            "confidence": min(len(sorted_records) / 100, 1.0)  # More data = higher confidence
        }
    
    def generate_usage_alerts(self, identifier: str, operation_type: str,
                             rate_limits: Dict[str, Any]) -> List[UsageAlert]:
        """Generate alerts based on usage patterns.
        
        Args:
            identifier: Unique identifier
            operation_type: Operation type
            rate_limits: Rate limit configuration
            
        Returns:
            List of usage alerts
        """
        alerts = []
        
        try:
            current_time = time.time()
            
            # Check various time windows for alerts
            windows = [
                ("daily", 24 * 3600, rate_limits.get("daily_limit", 1000)),
                ("weekly", 7 * 24 * 3600, rate_limits.get("weekly_limit", 5000)),
                ("monthly", 30 * 24 * 3600, rate_limits.get("monthly_limit", 20000)),
                ("burst", rate_limits.get("burst_window_minutes", 60) * 60, rate_limits.get("burst_limit", 100))
            ]
            
            for window_name, window_seconds, limit in windows:
                window_start = current_time - window_seconds
                current_usage = self.storage.get_total_usage_in_window(
                    identifier, operation_type, window_start, current_time
                )
                
                usage_percent = (current_usage / limit * 100) if limit > 0 else 0
                
                # Usage threshold alert
                if usage_percent >= self.usage_threshold:
                    severity = "high" if usage_percent >= 95 else "medium"
                    
                    alert = UsageAlert(
                        alert_type=f"{window_name}_usage_threshold",
                        identifier=identifier,
                        operation_type=operation_type,
                        message=f"{window_name.title()} usage at {usage_percent:.1f}% of limit",
                        severity=severity,
                        threshold_value=self.usage_threshold,
                        current_value=usage_percent,
                        timestamp=current_time,
                        details={
                            "window": window_name,
                            "current_usage": current_usage,
                            "limit": limit,
                            "remaining": limit - current_usage
                        }
                    )
                    alerts.append(alert)
                
                # Burst threshold alert (for burst window only)
                if window_name == "burst" and usage_percent >= self.burst_threshold:
                    alert = UsageAlert(
                        alert_type="burst_threshold",
                        identifier=identifier,
                        operation_type=operation_type,
                        message=f"Burst usage at {usage_percent:.1f}% of limit",
                        severity="critical",
                        threshold_value=self.burst_threshold,
                        current_value=usage_percent,
                        timestamp=current_time,
                        details={
                            "window": window_name,
                            "current_usage": current_usage,
                            "limit": limit,
                            "window_minutes": rate_limits.get("burst_window_minutes", 60)
                        }
                    )
                    alerts.append(alert)
            
            # Check for consecutive limit hits
            entry = self.storage.get_usage_data(identifier, operation_type)
            if entry and entry.blocked_count >= self.consecutive_hits:
                alert = UsageAlert(
                    alert_type="consecutive_blocks",
                    identifier=identifier,
                    operation_type=operation_type,
                    message=f"Consecutive blocks: {entry.blocked_count}",
                    severity="high",
                    threshold_value=self.consecutive_hits,
                    current_value=entry.blocked_count,
                    timestamp=current_time,
                    details={
                        "blocked_count": entry.blocked_count,
                        "threshold": self.consecutive_hits
                    }
                )
                alerts.append(alert)
            
            # Save alerts to storage
            if alerts:
                self._save_alerts(alerts)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating usage alerts: {e}")
            return []
    
    def _save_alerts(self, alerts: List[UsageAlert]):
        """Save alerts to storage."""
        try:
            alerts_file = self.analytics_dir / "alerts.json"
            
            # Load existing alerts
            with open(alerts_file, 'r') as f:
                alerts_data = json.load(f)
            
            # Add new alerts
            for alert in alerts:
                alert_dict = {
                    "alert_type": alert.alert_type,
                    "identifier": alert.identifier,
                    "operation_type": alert.operation_type,
                    "message": alert.message,
                    "severity": alert.severity,
                    "threshold_value": alert.threshold_value,
                    "current_value": alert.current_value,
                    "timestamp": alert.timestamp,
                    "timestamp_human": datetime.fromtimestamp(alert.timestamp).isoformat(),
                    "details": alert.details
                }
                alerts_data["data"].append(alert_dict)
            
            # Keep only recent alerts (last 1000)
            alerts_data["data"] = alerts_data["data"][-1000:]
            alerts_data["last_updated"] = time.time()
            
            # Save updated alerts
            with open(alerts_file, 'w') as f:
                json.dump(alerts_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving alerts: {e}")
    
    def get_usage_statistics(self, operation_type: Optional[str] = None,
                           hours_back: int = 24) -> Dict[str, Any]:
        """Get comprehensive usage statistics.
        
        Args:
            operation_type: Optional filter by operation type
            hours_back: Hours of history to analyze
            
        Returns:
            Dictionary containing usage statistics
        """
        try:
            analytics_data = self.storage.get_analytics_data(
                operation_type=operation_type,
                start_time=time.time() - (hours_back * 3600),
                end_time=time.time()
            )
            
            # Add derived metrics
            total_requests = analytics_data.get("total_requests", 0)
            total_blocked = analytics_data.get("total_blocked", 0)
            
            success_rate = (total_requests - total_blocked) / total_requests * 100 if total_requests > 0 else 0
            block_rate = total_blocked / total_requests * 100 if total_requests > 0 else 0
            
            # Calculate request rate
            request_rate = total_requests / hours_back if hours_back > 0 else 0
            
            return {
                "period_hours": hours_back,
                "operation_type_filter": operation_type,
                "summary": {
                    "total_requests": total_requests,
                    "total_blocked": total_blocked,
                    "success_rate_percent": success_rate,
                    "block_rate_percent": block_rate,
                    "request_rate_per_hour": request_rate
                },
                "breakdown": {
                    "unique_identifiers": analytics_data.get("unique_identifiers", 0),
                    "operation_types": analytics_data.get("operation_types", {}),
                    "top_users": analytics_data.get("top_users", {}),
                    "hourly_distribution": analytics_data.get("hourly_distribution", {}),
                    "daily_distribution": analytics_data.get("daily_distribution", {})
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting usage statistics: {e}")
            return {"error": str(e)}
    
    def generate_usage_report(self, report_type: str = "daily",
                            operation_type: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive usage report.
        
        Args:
            report_type: Type of report (daily, weekly, monthly)
            operation_type: Optional filter by operation type
            
        Returns:
            Dictionary containing usage report
        """
        try:
            # Determine time window
            hours_map = {
                "daily": 24,
                "weekly": 7 * 24,
                "monthly": 30 * 24
            }
            
            hours_back = hours_map.get(report_type, 24)
            
            # Get usage statistics
            stats = self.get_usage_statistics(operation_type, hours_back)
            
            # Get recent alerts
            alerts = self.get_recent_alerts(hours_back)
            
            # Generate insights
            insights = self._generate_insights(stats, alerts)
            
            # Create report
            report = {
                "report_type": report_type,
                "generated_at": time.time(),
                "generated_at_human": datetime.now().isoformat(),
                "operation_type_filter": operation_type,
                "statistics": stats,
                "alerts": {
                    "total": len(alerts),
                    "by_severity": self._count_alerts_by_severity(alerts),
                    "recent": alerts[:10]  # Top 10 recent alerts
                },
                "insights": insights,
                "recommendations": self._generate_recommendations(stats, alerts)
            }
            
            # Save report
            self._save_report(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating usage report: {e}")
            return {"error": str(e)}
    
    def _generate_insights(self, stats: Dict[str, Any], alerts: List[Dict[str, Any]]) -> List[str]:
        """Generate insights from statistics and alerts."""
        insights = []
        
        summary = stats.get("summary", {})
        
        # Success rate insights
        success_rate = summary.get("success_rate_percent", 0)
        if success_rate < 90:
            insights.append(f"Success rate is low at {success_rate:.1f}%, indicating potential rate limiting issues")
        elif success_rate > 98:
            insights.append(f"Excellent success rate of {success_rate:.1f}%, rate limits are well-configured")
        
        # Block rate insights
        block_rate = summary.get("block_rate_percent", 0)
        if block_rate > 10:
            insights.append(f"High block rate of {block_rate:.1f}%, consider reviewing rate limits")
        
        # Request rate insights
        request_rate = summary.get("request_rate_per_hour", 0)
        if request_rate > 100:
            insights.append(f"High request rate of {request_rate:.1f} requests/hour, monitor for unusual activity")
        
        # Alert insights
        if len(alerts) > 20:
            insights.append(f"High number of alerts ({len(alerts)}), investigate potential issues")
        
        # Top users insights
        top_users = stats.get("breakdown", {}).get("top_users", {})
        if top_users:
            top_user, top_usage = next(iter(top_users.items()))
            total_requests = summary.get("total_requests", 0)
            if total_requests > 0 and top_usage / total_requests > 0.3:
                insights.append(f"Top user ({top_user}) accounts for {top_usage/total_requests*100:.1f}% of usage")
        
        return insights
    
    def _generate_recommendations(self, stats: Dict[str, Any], alerts: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        summary = stats.get("summary", {})
        
        # Success rate recommendations
        success_rate = summary.get("success_rate_percent", 0)
        if success_rate < 95:
            recommendations.append("Consider increasing rate limits or optimizing client usage patterns")
        
        # Block rate recommendations
        block_rate = summary.get("block_rate_percent", 0)
        if block_rate > 5:
            recommendations.append("Review rate limit policies and consider implementing graceful degradation")
        
        # Alert recommendations
        critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
        if critical_alerts:
            recommendations.append("Address critical alerts immediately to prevent service disruption")
        
        # Usage pattern recommendations
        hourly_dist = stats.get("breakdown", {}).get("hourly_distribution", {})
        if hourly_dist:
            peak_hours = sorted(hourly_dist.items(), key=lambda x: x[1], reverse=True)[:3]
            if peak_hours:
                recommendations.append(f"Consider implementing time-based rate limiting for peak hours: {[h[0] for h in peak_hours]}")
        
        return recommendations
    
    def _count_alerts_by_severity(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count alerts by severity level."""
        severity_counts = {}
        
        for alert in alerts:
            severity = alert.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return severity_counts
    
    def _save_report(self, report: Dict[str, Any]):
        """Save report to storage."""
        try:
            reports_file = self.analytics_dir / "reports.json"
            
            # Load existing reports
            with open(reports_file, 'r') as f:
                reports_data = json.load(f)
            
            # Add new report
            reports_data["data"].append(report)
            
            # Keep only recent reports (last 100)
            reports_data["data"] = reports_data["data"][-100:]
            reports_data["last_updated"] = time.time()
            
            # Save updated reports
            with open(reports_file, 'w') as f:
                json.dump(reports_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving report: {e}")
    
    def get_recent_alerts(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts within time window.
        
        Args:
            hours_back: Hours of history to retrieve
            
        Returns:
            List of recent alerts
        """
        try:
            alerts_file = self.analytics_dir / "alerts.json"
            
            with open(alerts_file, 'r') as f:
                alerts_data = json.load(f)
            
            cutoff_time = time.time() - (hours_back * 3600)
            
            recent_alerts = [
                alert for alert in alerts_data.get("data", [])
                if alert.get("timestamp", 0) > cutoff_time
            ]
            
            # Sort by timestamp (newest first)
            recent_alerts.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            
            return recent_alerts
            
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []
    
    def cleanup_old_analytics(self) -> int:
        """Clean up old analytics data based on retention policy.
        
        Returns:
            Number of records cleaned up
        """
        try:
            cleanup_count = 0
            cutoff_time = time.time() - (self.retention_days * 24 * 3600)
            
            # Clean up alerts
            alerts_file = self.analytics_dir / "alerts.json"
            if alerts_file.exists():
                with open(alerts_file, 'r') as f:
                    alerts_data = json.load(f)
                
                original_count = len(alerts_data.get("data", []))
                alerts_data["data"] = [
                    alert for alert in alerts_data.get("data", [])
                    if alert.get("timestamp", 0) > cutoff_time
                ]
                cleanup_count += original_count - len(alerts_data["data"])
                
                with open(alerts_file, 'w') as f:
                    json.dump(alerts_data, f, indent=2)
            
            # Clean up reports
            reports_file = self.analytics_dir / "reports.json"
            if reports_file.exists():
                with open(reports_file, 'r') as f:
                    reports_data = json.load(f)
                
                original_count = len(reports_data.get("data", []))
                reports_data["data"] = [
                    report for report in reports_data.get("data", [])
                    if report.get("generated_at", 0) > cutoff_time
                ]
                cleanup_count += original_count - len(reports_data["data"])
                
                with open(reports_file, 'w') as f:
                    json.dump(reports_data, f, indent=2)
            
            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} old analytics records")
            
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old analytics: {e}")
            return 0