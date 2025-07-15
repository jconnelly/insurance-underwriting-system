"""
Analytics dashboard for the Streamlit underwriting application.

This page provides comprehensive analytics and reporting capabilities
for underwriting performance, trends, and insights.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from underwriting.streamlit_app.components.charts import (
    create_time_series_chart,
    create_decision_distribution_pie,
    create_risk_breakdown_chart,
    create_performance_metrics_chart,
    create_comparison_bar_chart,
    create_heatmap_chart,
    create_conversion_funnel_chart,
    create_waterfall_chart,
    display_metric_cards
)

def show_analytics_page():
    """Display the analytics dashboard page."""
    
    st.markdown("## 📊 Analytics Dashboard")
    st.markdown("""
    Comprehensive analytics and insights for underwriting performance, 
    trends, and optimization opportunities.
    """)
    
    # Time period selector
    col1, col2, col3 = st.columns(3)
    
    with col1:
        time_period = st.selectbox(
            "Time Period",
            options=["Last 7 days", "Last 30 days", "Last 90 days", "Last year", "All time"],
            index=1,
            help="Select the time period for analysis"
        )
    
    with col2:
        comparison_mode = st.selectbox(
            "Comparison",
            options=["No comparison", "Previous period", "Same period last year"],
            help="Compare with previous time periods"
        )
    
    with col3:
        auto_refresh = st.selectbox(
            "Auto Refresh",
            options=["Off", "30 seconds", "1 minute", "5 minutes"],
            help="Automatically refresh data"
        )
    
    # Generate sample data based on time period
    data = generate_analytics_data(time_period)
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview", "🎯 Performance", "📊 Trends", "🔍 Deep Dive", "📄 Reports"
    ])
    
    with tab1:
        show_overview_tab(data, comparison_mode)
    
    with tab2:
        show_performance_tab(data)
    
    with tab3:
        show_trends_tab(data)
    
    with tab4:
        show_deep_dive_tab(data)
    
    with tab5:
        show_reports_tab(data)

def show_overview_tab(data: Dict[str, Any], comparison_mode: str):
    """Show the overview analytics tab."""
    
    st.markdown("### 📈 Key Performance Indicators")
    
    # KPI metrics
    kpi_data = data['kpis']
    
    # Add comparison deltas if enabled
    if comparison_mode != "No comparison":
        deltas = generate_comparison_deltas(comparison_mode)
        for key in kpi_data:
            kpi_data[key] = {
                'value': kpi_data[key],
                'delta': deltas.get(key, 0)
            }
    
    display_metric_cards(kpi_data, columns=4)
    
    st.markdown("---")
    
    # Overview charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Decision Distribution")
        fig = create_decision_distribution_pie(data['decision_distribution'])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Risk Score Distribution")
        fig = create_risk_score_distribution_chart(data['risk_scores'])
        st.plotly_chart(fig, use_container_width=True)
    
    # Daily trends
    st.markdown("### 📈 Daily Application Volume")
    fig = create_time_series_chart(
        data['daily_stats'], 
        'date', 
        'applications', 
        'Daily Applications Over Time'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Processing funnel
    st.markdown("### 🔄 Application Processing Funnel")
    funnel_stages = ["Received", "Initial Review", "Risk Assessment", "Final Decision", "Completed"]
    funnel_values = [1000, 950, 920, 900, 885]
    
    fig = create_conversion_funnel_chart(funnel_stages, funnel_values)
    st.plotly_chart(fig, use_container_width=True)

def show_performance_tab(data: Dict[str, Any]):
    """Show the performance analytics tab."""
    
    st.markdown("### 🎯 Underwriting Performance")
    
    # Performance metrics radar chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Overall Performance Metrics")
        performance_metrics = {
            'Accuracy': 85.2,
            'Precision': 78.9,
            'Recall': 82.4,
            'F1-Score': 80.6,
            'AUC-ROC': 88.1,
            'Processing Speed': 92.3
        }
        
        fig = create_performance_metrics_chart(performance_metrics)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### ⚡ Processing Time Analysis")
        
        # Processing time metrics
        processing_stats = {
            "Avg Processing Time": "2.4s",
            "P95 Processing Time": "8.7s",
            "P99 Processing Time": "15.2s",
            "Timeout Rate": "0.1%"
        }
        
        display_metric_cards(processing_stats, columns=2)
        
        # Processing time distribution
        processing_times = np.random.lognormal(1, 0.5, 1000)
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=processing_times,
            nbinsx=30,
            name='Processing Time',
            marker_color='skyblue'
        ))
        
        fig.update_layout(
            title="Processing Time Distribution",
            xaxis_title="Time (seconds)",
            yaxis_title="Frequency",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # AI vs Rules comparison
    st.markdown("### 🤖 AI vs Rules Performance Comparison")
    
    comparison_data = {
        'AI-Enhanced': {
            'Accuracy': 88.5,
            'Precision': 82.1,
            'Recall': 84.7,
            'F1-Score': 83.4,
            'Speed (apps/min)': 45.2
        },
        'Rules Only': {
            'Accuracy': 82.1,
            'Precision': 76.3,
            'Recall': 79.8,
            'F1-Score': 78.0,
            'Speed (apps/min)': 127.8
        }
    }
    
    fig = create_comparison_bar_chart(comparison_data, "AI vs Rules Performance Comparison")
    st.plotly_chart(fig, use_container_width=True)
    
    # Error analysis
    st.markdown("### ❌ Error Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Top Error Categories")
        error_data = {
            'Data Validation': 45,
            'AI Service Timeout': 23,
            'Rule Engine Error': 18,
            'External API Failure': 12,
            'Unknown Error': 8
        }
        
        fig = create_decision_distribution_pie(error_data)
        fig.update_layout(title="Error Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Error Trends")
        
        error_trends = generate_error_trend_data()
        fig = create_time_series_chart(
            error_trends,
            'date',
            'error_count',
            'Daily Error Count'
        )
        st.plotly_chart(fig, use_container_width=True)

def show_trends_tab(data: Dict[str, Any]):
    """Show the trends analytics tab."""
    
    st.markdown("### 📊 Trend Analysis")
    
    # Trend selector
    trend_type = st.selectbox(
        "Select Trend Analysis",
        options=[
            "Application Volume",
            "Acceptance Rate",
            "Risk Score Trends",
            "Processing Time",
            "Regional Analysis",
            "Seasonal Patterns"
        ]
    )
    
    if trend_type == "Application Volume":
        show_volume_trends(data)
    elif trend_type == "Acceptance Rate":
        show_acceptance_trends(data)
    elif trend_type == "Risk Score Trends":
        show_risk_score_trends(data)
    elif trend_type == "Processing Time":
        show_processing_time_trends(data)
    elif trend_type == "Regional Analysis":
        show_regional_analysis(data)
    elif trend_type == "Seasonal Patterns":
        show_seasonal_patterns(data)

def show_volume_trends(data: Dict[str, Any]):
    """Show application volume trend analysis."""
    
    st.markdown("#### 📈 Application Volume Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Hourly pattern
        hourly_data = generate_hourly_pattern_data()
        
        fig = px.line(
            hourly_data,
            x='hour',
            y='applications',
            title='Applications by Hour of Day',
            markers=True
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Day of week pattern
        dow_data = generate_day_of_week_data()
        
        fig = px.bar(
            dow_data,
            x='day',
            y='applications',
            title='Applications by Day of Week',
            color='applications',
            color_continuous_scale='viridis'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Monthly trend with forecasting
    st.markdown("#### 📊 Monthly Trends with Forecast")
    
    monthly_data = generate_monthly_trend_data()
    
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=monthly_data['month'][:12],
        y=monthly_data['applications'][:12],
        mode='lines+markers',
        name='Historical',
        line=dict(color='blue')
    ))
    
    # Forecast data
    fig.add_trace(go.Scatter(
        x=monthly_data['month'][11:],
        y=monthly_data['forecast'][11:],
        mode='lines+markers',
        name='Forecast',
        line=dict(color='red', dash='dash')
    ))
    
    fig.update_layout(
        title='Monthly Application Volume with 3-Month Forecast',
        xaxis_title='Month',
        yaxis_title='Applications',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_acceptance_trends(data: Dict[str, Any]):
    """Show acceptance rate trend analysis."""
    
    st.markdown("#### ✅ Acceptance Rate Analysis")
    
    # Acceptance rate by various factors
    col1, col2 = st.columns(2)
    
    with col1:
        # By age group
        age_acceptance = {
            '18-25': 0.45,
            '26-35': 0.62,
            '36-45': 0.71,
            '46-55': 0.68,
            '56-65': 0.64,
            '65+': 0.58
        }
        
        fig = px.bar(
            x=list(age_acceptance.keys()),
            y=list(age_acceptance.values()),
            title='Acceptance Rate by Age Group',
            labels={'x': 'Age Group', 'y': 'Acceptance Rate'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # By risk score range
        risk_acceptance = generate_risk_acceptance_data()
        
        fig = px.scatter(
            risk_acceptance,
            x='risk_score',
            y='acceptance_rate',
            size='applications',
            title='Acceptance Rate vs Risk Score',
            labels={'risk_score': 'Risk Score', 'acceptance_rate': 'Acceptance Rate'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Waterfall chart showing factors affecting acceptance
    st.markdown("#### 🌊 Acceptance Rate Impact Analysis")
    
    factors = ['Baseline', 'Age Factor', 'Credit Score', 'Driving History', 'Vehicle Type', 'Final Rate']
    impacts = [0.65, 0.05, 0.08, -0.12, 0.03, 0.69]
    
    fig = create_waterfall_chart(factors, impacts, "Factors Affecting Acceptance Rate")
    st.plotly_chart(fig, use_container_width=True)

def show_risk_score_trends(data: Dict[str, Any]):
    """Show risk score trend analysis."""
    
    st.markdown("#### 🎯 Risk Score Analysis")
    
    # Risk score distribution over time
    risk_trend_data = generate_risk_trend_data()
    
    fig = px.box(
        risk_trend_data,
        x='month',
        y='risk_score',
        title='Risk Score Distribution by Month'
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk component correlation
    st.markdown("#### 🔗 Risk Component Correlation")
    
    correlation_data = generate_risk_correlation_data()
    fig = create_heatmap_chart(correlation_data, "Risk Component Correlation Matrix")
    st.plotly_chart(fig, use_container_width=True)

def show_processing_time_trends(data: Dict[str, Any]):
    """Show processing time trend analysis."""
    
    st.markdown("#### ⏱️ Processing Time Analysis")
    
    processing_data = generate_processing_time_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = create_time_series_chart(
            processing_data,
            'date',
            'avg_processing_time',
            'Average Processing Time Trend'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.box(
            processing_data,
            x='evaluation_mode',
            y='processing_time',
            title='Processing Time by Evaluation Mode'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def show_regional_analysis(data: Dict[str, Any]):
    """Show regional analysis."""
    
    st.markdown("#### 🗺️ Regional Performance Analysis")
    
    # State-wise performance
    state_data = generate_state_performance_data()
    
    fig = px.choropleth(
        state_data,
        locations='state',
        locationmode='USA-states',
        color='acceptance_rate',
        hover_name='state',
        hover_data=['applications', 'avg_risk_score'],
        color_continuous_scale='viridis',
        scope='usa',
        title='Acceptance Rate by State'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Top performing regions
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏆 Top Performing States")
        top_states = state_data.nlargest(10, 'acceptance_rate')[['state', 'acceptance_rate', 'applications']]
        st.dataframe(top_states, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 Regional Volume Distribution")
        fig = px.pie(
            state_data.head(10),
            values='applications',
            names='state',
            title='Application Volume by Top 10 States'
        )
        st.plotly_chart(fig, use_container_width=True)

def show_seasonal_patterns(data: Dict[str, Any]):
    """Show seasonal pattern analysis."""
    
    st.markdown("#### 🌿 Seasonal Pattern Analysis")
    
    seasonal_data = generate_seasonal_data()
    
    # Seasonal heatmap
    fig = px.imshow(
        seasonal_data.pivot(index='month', columns='year', values='applications'),
        title='Application Volume Heatmap (Monthly)',
        color_continuous_scale='viridis'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Seasonal decomposition
    col1, col2 = st.columns(2)
    
    with col1:
        monthly_avg = seasonal_data.groupby('month')['applications'].mean().reset_index()
        
        fig = px.line(
            monthly_avg,
            x='month',
            y='applications',
            title='Average Applications by Month',
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        quarterly_data = generate_quarterly_data()
        
        fig = px.bar(
            quarterly_data,
            x='quarter',
            y='applications',
            color='year',
            title='Quarterly Application Volume',
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)

def show_deep_dive_tab(data: Dict[str, Any]):
    """Show the deep dive analytics tab."""
    
    st.markdown("### 🔍 Deep Dive Analysis")
    
    analysis_type = st.selectbox(
        "Select Analysis Type",
        options=[
            "Cohort Analysis",
            "Feature Importance",
            "Model Performance",
            "Anomaly Detection",
            "Customer Segmentation"
        ]
    )
    
    if analysis_type == "Cohort Analysis":
        show_cohort_analysis()
    elif analysis_type == "Feature Importance":
        show_feature_importance()
    elif analysis_type == "Model Performance":
        show_model_performance()
    elif analysis_type == "Anomaly Detection":
        show_anomaly_detection()
    elif analysis_type == "Customer Segmentation":
        show_customer_segmentation()

def show_cohort_analysis():
    """Show cohort analysis."""
    
    st.markdown("#### 👥 Cohort Analysis")
    
    cohort_data = generate_cohort_data()
    
    fig = px.imshow(
        cohort_data,
        title='Customer Retention Cohort Analysis',
        color_continuous_scale='blues',
        aspect='auto'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_feature_importance():
    """Show feature importance analysis."""
    
    st.markdown("#### 🎯 Feature Importance Analysis")
    
    features = [
        'Credit Score', 'Age', 'Driving History', 'Vehicle Value', 
        'Previous Claims', 'License Years', 'Marital Status', 'Location'
    ]
    importance = [0.25, 0.18, 0.16, 0.12, 0.10, 0.08, 0.06, 0.05]
    
    fig = px.bar(
        x=importance,
        y=features,
        orientation='h',
        title='Feature Importance for Risk Prediction',
        labels={'x': 'Importance Score', 'y': 'Features'}
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

def show_model_performance():
    """Show model performance analysis."""
    
    st.markdown("#### 🤖 Model Performance Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ROC Curve
        fpr, tpr = generate_roc_data()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=fpr,
            y=tpr,
            mode='lines',
            name='ROC Curve (AUC = 0.88)',
            line=dict(color='blue', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode='lines',
            name='Random Classifier',
            line=dict(color='red', width=1, dash='dash')
        ))
        
        fig.update_layout(
            title='ROC Curve',
            xaxis_title='False Positive Rate',
            yaxis_title='True Positive Rate',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Precision-Recall Curve
        precision, recall = generate_pr_data()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=recall,
            y=precision,
            mode='lines',
            name='PR Curve',
            line=dict(color='green', width=2)
        ))
        
        fig.update_layout(
            title='Precision-Recall Curve',
            xaxis_title='Recall',
            yaxis_title='Precision',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_anomaly_detection():
    """Show anomaly detection analysis."""
    
    st.markdown("#### 🚨 Anomaly Detection")
    
    anomaly_data = generate_anomaly_data()
    
    fig = px.scatter(
        anomaly_data,
        x='risk_score',
        y='processing_time',
        color='is_anomaly',
        title='Anomaly Detection in Risk Score vs Processing Time',
        color_discrete_map={True: 'red', False: 'blue'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Anomaly summary
    anomaly_count = anomaly_data['is_anomaly'].sum()
    total_count = len(anomaly_data)
    
    st.metric("Anomalies Detected", f"{anomaly_count} ({anomaly_count/total_count:.1%})")

def show_customer_segmentation():
    """Show customer segmentation analysis."""
    
    st.markdown("#### 👥 Customer Segmentation")
    
    segment_data = generate_segment_data()
    
    fig = px.scatter(
        segment_data,
        x='risk_score',
        y='premium_willingness',
        color='segment',
        size='frequency',
        title='Customer Segmentation Analysis',
        hover_data=['age_group']
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_reports_tab(data: Dict[str, Any]):
    """Show the reports tab."""
    
    st.markdown("### 📄 Reports & Exports")
    
    # Report type selection
    report_type = st.selectbox(
        "Select Report Type",
        options=[
            "Executive Summary",
            "Performance Report",
            "Risk Analysis Report",
            "A/B Test Report",
            "Custom Report"
        ]
    )
    
    # Report parameters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_range = st.date_input(
            "Date Range",
            value=[datetime.now() - timedelta(days=30), datetime.now()],
            help="Select the date range for the report"
        )
    
    with col2:
        format_type = st.selectbox(
            "Export Format",
            options=["PDF", "Excel", "CSV", "JSON"],
            help="Choose the export format"
        )
    
    with col3:
        include_charts = st.checkbox(
            "Include Charts",
            value=True,
            help="Include visualizations in the report"
        )
    
    # Report preview
    st.markdown("#### 📊 Report Preview")
    
    if report_type == "Executive Summary":
        show_executive_summary_preview(data)
    elif report_type == "Performance Report":
        show_performance_report_preview(data)
    elif report_type == "Risk Analysis Report":
        show_risk_analysis_preview(data)
    elif report_type == "A/B Test Report":
        show_ab_test_report_preview(data)
    elif report_type == "Custom Report":
        show_custom_report_builder()
    
    # Export buttons
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Generate Report", type="primary"):
            st.success("Report generation initiated...")
    
    with col2:
        if st.button("📧 Schedule Report"):
            st.info("Report scheduling coming soon...")
    
    with col3:
        if st.button("🔄 Auto-refresh"):
            st.info("Auto-refresh configured...")
    
    with col4:
        if st.button("⚙️ Report Settings"):
            st.info("Report settings coming soon...")

def show_executive_summary_preview(data: Dict[str, Any]):
    """Show executive summary report preview."""
    
    st.markdown("##### 📈 Executive Summary")
    
    summary_metrics = {
        "Total Applications": "12,547",
        "Acceptance Rate": "64.2%",
        "Avg Risk Score": "67.8",
        "Processing Time": "2.4s avg",
        "AI Enhancement": "+12% accuracy",
        "Revenue Impact": "$2.4M potential"
    }
    
    display_metric_cards(summary_metrics, columns=3)
    
    st.markdown("**Key Insights:**")
    st.markdown("""
    • Application volume increased 15% compared to previous period
    • AI-enhanced evaluations showing 12% improvement in accuracy
    • Processing time improved by 8% with new optimizations
    • Risk score distribution remains stable with slight improvement in quality
    """)

def show_performance_report_preview(data: Dict[str, Any]):
    """Show performance report preview."""
    
    st.markdown("##### 🎯 Performance Analysis")
    
    performance_data = {
        "Model Accuracy": "85.2%",
        "Precision": "78.9%", 
        "Recall": "82.4%",
        "F1-Score": "80.6%",
        "AUC-ROC": "0.881",
        "Processing Speed": "127 apps/min"
    }
    
    display_metric_cards(performance_data, columns=3)

def show_risk_analysis_preview(data: Dict[str, Any]):
    """Show risk analysis report preview."""
    
    st.markdown("##### 🎯 Risk Analysis")
    
    risk_data = {
        "High Risk (80+)": "15.2%",
        "Medium Risk (40-80)": "68.4%",
        "Low Risk (<40)": "16.4%",
        "Avg Driver Risk": "72.1",
        "Avg Vehicle Risk": "65.8",
        "Avg Credit Risk": "69.3"
    }
    
    display_metric_cards(risk_data, columns=3)

def show_ab_test_report_preview(data: Dict[str, Any]):
    """Show A/B test report preview."""
    
    st.markdown("##### 🧪 A/B Test Summary")
    
    ab_data = {
        "Active Tests": "3",
        "Completed Tests": "12", 
        "Success Rate": "67%",
        "Avg Improvement": "+8.4%",
        "Best Performer": "AI vs Rules",
        "Current Focus": "Risk Scoring"
    }
    
    display_metric_cards(ab_data, columns=3)

def show_custom_report_builder():
    """Show custom report builder."""
    
    st.markdown("##### 🛠️ Custom Report Builder")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Select Metrics:**")
        metrics = st.multiselect(
            "Choose metrics to include",
            options=[
                "Application Volume",
                "Acceptance Rate", 
                "Risk Scores",
                "Processing Time",
                "Error Rates",
                "Regional Performance",
                "A/B Test Results"
            ],
            default=["Application Volume", "Acceptance Rate"]
        )
    
    with col2:
        st.markdown("**Select Visualizations:**")
        charts = st.multiselect(
            "Choose chart types",
            options=[
                "Time Series",
                "Bar Charts",
                "Pie Charts", 
                "Heatmaps",
                "Box Plots",
                "Scatter Plots"
            ],
            default=["Time Series", "Bar Charts"]
        )
    
    if st.button("🎨 Preview Custom Report"):
        st.info(f"Generating custom report with {len(metrics)} metrics and {len(charts)} chart types...")

# Data generation functions
def generate_analytics_data(time_period: str) -> Dict[str, Any]:
    """Generate sample analytics data based on time period."""
    
    if time_period == "Last 7 days":
        days = 7
    elif time_period == "Last 30 days":
        days = 30
    elif time_period == "Last 90 days":
        days = 90
    elif time_period == "Last year":
        days = 365
    else:
        days = 365
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Generate daily statistics
    daily_stats = pd.DataFrame({
        'date': dates,
        'applications': np.random.poisson(50, days),
        'acceptances': np.random.poisson(32, days),
        'denials': np.random.poisson(12, days),
        'adjudications': np.random.poisson(6, days),
        'avg_risk_score': np.random.normal(67, 8, days),
        'avg_processing_time': np.random.exponential(2.5, days)
    })
    
    # Calculate KPIs
    total_apps = daily_stats['applications'].sum()
    total_accepts = daily_stats['acceptances'].sum()
    total_denials = daily_stats['denials'].sum()
    total_adjudications = daily_stats['adjudications'].sum()
    
    kpis = {
        "Total Applications": f"{total_apps:,}",
        "Acceptance Rate": f"{total_accepts/total_apps:.1%}",
        "Average Risk Score": f"{daily_stats['avg_risk_score'].mean():.1f}",
        "Processing Time": f"{daily_stats['avg_processing_time'].mean():.1f}s"
    }
    
    # Decision distribution
    decision_distribution = {
        'ACCEPT': total_accepts,
        'DENY': total_denials,
        'ADJUDICATE': total_adjudications
    }
    
    # Risk score distribution
    risk_scores = np.random.normal(67, 12, total_apps)
    
    return {
        'kpis': kpis,
        'daily_stats': daily_stats,
        'decision_distribution': decision_distribution,
        'risk_scores': risk_scores
    }

def generate_comparison_deltas(comparison_mode: str) -> Dict[str, str]:
    """Generate comparison deltas for KPIs."""
    
    return {
        "Total Applications": "+15%",
        "Acceptance Rate": "+2.1%",
        "Average Risk Score": "-1.2",
        "Processing Time": "-8%"
    }

def create_risk_score_distribution_chart(risk_scores: np.ndarray) -> go.Figure:
    """Create a risk score distribution chart."""
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=risk_scores,
        nbinsx=30,
        name='Risk Score Distribution',
        marker_color='lightblue',
        opacity=0.7
    ))
    
    fig.update_layout(
        title="Risk Score Distribution",
        xaxis_title="Risk Score",
        yaxis_title="Frequency",
        height=400
    )
    
    return fig

def generate_error_trend_data() -> pd.DataFrame:
    """Generate error trend data."""
    
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    return pd.DataFrame({
        'date': dates,
        'error_count': np.random.poisson(5, 30)
    })

def generate_hourly_pattern_data() -> pd.DataFrame:
    """Generate hourly pattern data."""
    
    hours = list(range(24))
    # Simulate business hours pattern
    applications = [
        5, 3, 2, 1, 1, 2, 8, 15, 25, 35, 45, 50,
        55, 52, 48, 42, 38, 32, 25, 18, 12, 8, 6, 5
    ]
    
    return pd.DataFrame({
        'hour': hours,
        'applications': applications
    })

def generate_day_of_week_data() -> pd.DataFrame:
    """Generate day of week data."""
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    applications = [520, 580, 590, 600, 550, 250, 180]
    
    return pd.DataFrame({
        'day': days,
        'applications': applications
    })

def generate_monthly_trend_data() -> Dict[str, List]:
    """Generate monthly trend data with forecast."""
    
    months = pd.date_range(start='2024-01-01', periods=15, freq='M')
    applications = list(np.random.poisson(1500, 12)) + [0, 0, 0]  # 12 historical + 3 forecast
    forecast = [0] * 12 + list(np.random.poisson(1600, 3))  # forecast for next 3 months
    
    return {
        'month': months,
        'applications': applications,
        'forecast': forecast
    }

def generate_risk_acceptance_data() -> pd.DataFrame:
    """Generate risk vs acceptance rate data."""
    
    risk_scores = np.arange(20, 101, 5)
    acceptance_rates = 1 / (1 + np.exp(-(risk_scores - 60) / 10))  # Sigmoid curve
    applications = np.random.poisson(100, len(risk_scores))
    
    return pd.DataFrame({
        'risk_score': risk_scores,
        'acceptance_rate': acceptance_rates,
        'applications': applications
    })

def generate_risk_trend_data() -> pd.DataFrame:
    """Generate risk score trend data."""
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    data = []
    for month in months:
        risk_scores = np.random.normal(67, 12, 500)
        for score in risk_scores:
            data.append({'month': month, 'risk_score': score})
    
    return pd.DataFrame(data)

def generate_risk_correlation_data() -> pd.DataFrame:
    """Generate risk component correlation data."""
    
    n_samples = 1000
    
    return pd.DataFrame({
        'Driver Risk': np.random.normal(70, 15, n_samples),
        'Vehicle Risk': np.random.normal(65, 12, n_samples),
        'Credit Risk': np.random.normal(72, 18, n_samples),
        'History Risk': np.random.normal(68, 14, n_samples),
        'Location Risk': np.random.normal(63, 10, n_samples)
    })

def generate_processing_time_data() -> pd.DataFrame:
    """Generate processing time data."""
    
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    data = []
    for date in dates:
        for mode in ['AI-Enhanced', 'Rules Only', 'AI Only']:
            if mode == 'AI-Enhanced':
                times = np.random.exponential(2.5, 50)
            elif mode == 'Rules Only':
                times = np.random.exponential(0.8, 50)
            else:
                times = np.random.exponential(4.2, 50)
            
            for time_val in times:
                data.append({
                    'date': date,
                    'evaluation_mode': mode,
                    'processing_time': time_val,
                    'avg_processing_time': np.mean(times)
                })
    
    return pd.DataFrame(data)

def generate_state_performance_data() -> pd.DataFrame:
    """Generate state performance data."""
    
    states = [
        'CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI',
        'NJ', 'VA', 'WA', 'AZ', 'MA', 'TN', 'IN', 'MO', 'MD', 'WI'
    ]
    
    return pd.DataFrame({
        'state': states,
        'applications': np.random.poisson(500, len(states)),
        'acceptance_rate': np.random.beta(2, 1, len(states)) * 0.4 + 0.5,
        'avg_risk_score': np.random.normal(67, 8, len(states))
    })

def generate_seasonal_data() -> pd.DataFrame:
    """Generate seasonal pattern data."""
    
    data = []
    for year in [2022, 2023, 2024]:
        for month in range(1, 13):
            applications = np.random.poisson(1000 + 200 * np.sin(month * np.pi / 6))
            data.append({
                'year': year,
                'month': month,
                'applications': applications
            })
    
    return pd.DataFrame(data)

def generate_quarterly_data() -> pd.DataFrame:
    """Generate quarterly data."""
    
    data = []
    for year in [2022, 2023, 2024]:
        for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
            base_apps = 3000 + np.random.randint(-500, 500)
            data.append({
                'year': str(year),
                'quarter': quarter,
                'applications': base_apps
            })
    
    return pd.DataFrame(data)

def generate_cohort_data():
    """Generate cohort analysis data."""
    
    cohorts = ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Apr 2024', 'May 2024']
    periods = list(range(1, 7))
    
    cohort_matrix = []
    for i, cohort in enumerate(cohorts):
        row = []
        for period in periods:
            retention = 1.0 * np.exp(-0.3 * (period - 1)) + np.random.normal(0, 0.05)
            retention = max(0, min(1, retention))
            row.append(retention)
        cohort_matrix.append(row)
    
    return pd.DataFrame(cohort_matrix, index=cohorts, columns=[f'Period {p}' for p in periods])

def generate_roc_data():
    """Generate ROC curve data."""
    
    fpr = np.linspace(0, 1, 100)
    tpr = np.sqrt(fpr) * 0.9 + np.random.normal(0, 0.02, 100)
    tpr = np.clip(tpr, 0, 1)
    
    return fpr, tpr

def generate_pr_data():
    """Generate precision-recall curve data."""
    
    recall = np.linspace(0, 1, 100)
    precision = (1 - recall) * 0.8 + 0.2 + np.random.normal(0, 0.02, 100)
    precision = np.clip(precision, 0, 1)
    
    return precision, recall

def generate_anomaly_data():
    """Generate anomaly detection data."""
    
    n_normal = 950
    n_anomaly = 50
    
    # Normal data
    normal_risk = np.random.normal(67, 12, n_normal)
    normal_time = np.random.exponential(2.5, n_normal)
    
    # Anomalous data
    anomaly_risk = np.concatenate([
        np.random.normal(30, 5, n_anomaly // 2),  # Unusually low risk
        np.random.normal(95, 3, n_anomaly // 2)   # Unusually high risk
    ])
    anomaly_time = np.random.exponential(15, n_anomaly)  # Unusually long processing
    
    return pd.DataFrame({
        'risk_score': np.concatenate([normal_risk, anomaly_risk]),
        'processing_time': np.concatenate([normal_time, anomaly_time]),
        'is_anomaly': [False] * n_normal + [True] * n_anomaly
    })

def generate_segment_data():
    """Generate customer segmentation data."""
    
    segments = ['Conservative', 'Balanced', 'Aggressive', 'Premium']
    colors = ['blue', 'green', 'orange', 'red']
    
    data = []
    for i, segment in enumerate(segments):
        for _ in range(100):
            data.append({
                'segment': segment,
                'risk_score': np.random.normal(50 + i * 15, 10),
                'premium_willingness': np.random.normal(0.5 + i * 0.2, 0.1),
                'frequency': np.random.randint(5, 25),
                'age_group': np.random.choice(['18-30', '31-45', '46-60', '60+'])
            })
    
    return pd.DataFrame(data)