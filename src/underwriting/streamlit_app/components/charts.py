"""
Chart components for the Streamlit underwriting application.

This module provides reusable chart components using Plotly and Altair
for data visualization throughout the application.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

def create_risk_score_gauge(score: float, title: str = "Risk Score") -> go.Figure:
    """Create a gauge chart for risk scores."""
    
    # Determine color based on score
    if score >= 80:
        color = "green"
    elif score >= 60:
        color = "yellow"
    else:
        color = "red"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': 70},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 40], 'color': "lightgray"},
                {'range': [40, 70], 'color': "gray"},
                {'range': [70, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        font={'color': "darkblue", 'family': "Arial"}
    )
    
    return fig

def create_risk_breakdown_chart(risk_components: Dict[str, float]) -> go.Figure:
    """Create a horizontal bar chart for risk component breakdown."""
    
    components = list(risk_components.keys())
    scores = list(risk_components.values())
    
    # Color mapping for risk levels
    colors = []
    for score in scores:
        if score >= 80:
            colors.append('#28a745')  # Green
        elif score >= 60:
            colors.append('#ffc107')  # Yellow
        else:
            colors.append('#dc3545')  # Red
    
    fig = go.Figure(go.Bar(
        x=scores,
        y=components,
        orientation='h',
        marker_color=colors,
        text=[f'{score}' for score in scores],
        textposition='inside'
    ))
    
    fig.update_layout(
        title="Risk Score Breakdown",
        xaxis_title="Score",
        yaxis_title="Risk Component",
        height=300,
        showlegend=False
    )
    
    return fig

def create_decision_distribution_pie(decisions: Dict[str, int]) -> go.Figure:
    """Create a pie chart showing decision distribution."""
    
    labels = list(decisions.keys())
    values = list(decisions.values())
    
    colors = {
        'ACCEPT': '#28a745',
        'DENY': '#dc3545',
        'ADJUDICATE': '#ffc107'
    }
    
    pie_colors = [colors.get(label, '#6c757d') for label in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.3,
        marker_colors=pie_colors
    )])
    
    fig.update_layout(
        title="Decision Distribution",
        annotations=[dict(text='Decisions', x=0.5, y=0.5, font_size=16, showarrow=False)],
        height=400
    )
    
    return fig

def create_time_series_chart(data: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
    """Create a time series line chart."""
    
    fig = px.line(
        data, 
        x=x_col, 
        y=y_col,
        title=title,
        markers=True
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        hovermode='x unified'
    )
    
    return fig

def create_ab_test_results_chart(control_data: List[float], treatment_data: List[float]) -> go.Figure:
    """Create a comparison chart for A/B test results."""
    
    fig = go.Figure()
    
    # Add control group
    fig.add_trace(go.Histogram(
        x=control_data,
        name='Control',
        opacity=0.7,
        nbinsx=20,
        marker_color='blue'
    ))
    
    # Add treatment group
    fig.add_trace(go.Histogram(
        x=treatment_data,
        name='Treatment',
        opacity=0.7,
        nbinsx=20,
        marker_color='red'
    ))
    
    fig.update_layout(
        title="A/B Test Results Distribution",
        xaxis_title="Value",
        yaxis_title="Frequency",
        barmode='overlay',
        height=400
    )
    
    return fig

def create_conversion_funnel_chart(stages: List[str], values: List[int]) -> go.Figure:
    """Create a funnel chart for conversion analysis."""
    
    fig = go.Figure(go.Funnel(
        y = stages,
        x = values,
        textinfo = "value+percent initial",
        marker = dict(color = ["deepskyblue", "lightsalmon", "tan", "teal", "silver"]),
        connector = dict(line = dict(color = "royalblue", dash = "dot", width = 3))
    ))
    
    fig.update_layout(
        title="Application Processing Funnel",
        height=500
    )
    
    return fig

def create_heatmap_chart(data: pd.DataFrame, title: str = "Correlation Heatmap") -> go.Figure:
    """Create a correlation heatmap."""
    
    correlation_matrix = data.corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix.values,
        x=correlation_matrix.columns,
        y=correlation_matrix.index,
        colorscale='RdYlBu',
        zmid=0
    ))
    
    fig.update_layout(
        title=title,
        height=500
    )
    
    return fig

def create_box_plot_chart(data: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
    """Create a box plot for statistical analysis."""
    
    fig = px.box(
        data, 
        x=x_col, 
        y=y_col,
        title=title,
        color=x_col
    )
    
    fig.update_layout(height=400)
    
    return fig

def create_scatter_plot_with_trend(data: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
    """Create a scatter plot with trend line."""
    
    fig = px.scatter(
        data, 
        x=x_col, 
        y=y_col,
        title=title,
        trendline="ols"
    )
    
    fig.update_layout(height=400)
    
    return fig

def create_performance_metrics_chart(metrics: Dict[str, float]) -> go.Figure:
    """Create a radar chart for performance metrics."""
    
    categories = list(metrics.keys())
    values = list(metrics.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Performance Metrics'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="Performance Metrics",
        height=400
    )
    
    return fig

def create_comparison_bar_chart(data: Dict[str, Dict[str, float]], title: str) -> go.Figure:
    """Create a grouped bar chart for comparisons."""
    
    fig = go.Figure()
    
    for group_name, group_data in data.items():
        fig.add_trace(go.Bar(
            name=group_name,
            x=list(group_data.keys()),
            y=list(group_data.values())
        ))
    
    fig.update_layout(
        title=title,
        barmode='group',
        height=400
    )
    
    return fig

def create_waterfall_chart(categories: List[str], values: List[float], title: str) -> go.Figure:
    """Create a waterfall chart for sequential analysis."""
    
    fig = go.Figure(go.Waterfall(
        name = "Waterfall",
        orientation = "v",
        measure = ["relative"] * (len(categories) - 1) + ["total"],
        x = categories,
        textposition = "outside",
        text = [f"+{v}" if v > 0 else str(v) for v in values],
        y = values,
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title=title,
        showlegend=True,
        height=400
    )
    
    return fig

def display_metric_cards(metrics: Dict[str, Any], columns: int = 4):
    """Display metric cards in a grid layout."""
    
    cols = st.columns(columns)
    
    for i, (label, value) in enumerate(metrics.items()):
        with cols[i % columns]:
            if isinstance(value, dict):
                st.metric(
                    label=label,
                    value=value.get('value', 'N/A'),
                    delta=value.get('delta', None),
                    help=value.get('help', None)
                )
            else:
                st.metric(label=label, value=value)

def create_sample_data_for_demo():
    """Create sample data for demonstration purposes."""
    
    # Sample time series data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    time_series_data = pd.DataFrame({
        'date': dates,
        'applications': np.random.poisson(50, len(dates)),
        'acceptance_rate': np.random.beta(2, 1, len(dates)) * 0.3 + 0.6,
        'avg_risk_score': np.random.normal(70, 15, len(dates))
    })
    
    # Sample A/B test data
    control_results = np.random.normal(65, 12, 1000)
    treatment_results = np.random.normal(68, 12, 1000)
    
    # Sample decision distribution
    decision_dist = {
        'ACCEPT': 650,
        'DENY': 200,
        'ADJUDICATE': 150
    }
    
    # Sample risk components
    risk_components = {
        'Driver Risk': 75,
        'Vehicle Risk': 85,
        'History Risk': 60,
        'Credit Risk': 80
    }
    
    # Sample performance metrics
    performance_metrics = {
        'Accuracy': 85,
        'Precision': 78,
        'Recall': 82,
        'F1-Score': 80,
        'AUC-ROC': 88
    }
    
    return {
        'time_series': time_series_data,
        'control_results': control_results,
        'treatment_results': treatment_results,
        'decisions': decision_dist,
        'risk_components': risk_components,
        'performance': performance_metrics
    }

def show_chart_gallery():
    """Display a gallery of available charts for demonstration."""
    
    st.markdown("## 📊 Chart Gallery")
    st.markdown("Explore the various chart types available in the application.")
    
    # Get sample data
    sample_data = create_sample_data_for_demo()
    
    # Chart selection
    chart_type = st.selectbox(
        "Select Chart Type",
        [
            "Risk Score Gauge",
            "Risk Breakdown",
            "Decision Distribution",
            "Time Series",
            "A/B Test Results",
            "Performance Metrics",
            "Correlation Heatmap"
        ]
    )
    
    if chart_type == "Risk Score Gauge":
        score = st.slider("Risk Score", 0, 100, 75)
        fig = create_risk_score_gauge(score)
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Risk Breakdown":
        fig = create_risk_breakdown_chart(sample_data['risk_components'])
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Decision Distribution":
        fig = create_decision_distribution_pie(sample_data['decisions'])
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Time Series":
        fig = create_time_series_chart(
            sample_data['time_series'], 
            'date', 
            'applications', 
            'Daily Applications Over Time'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "A/B Test Results":
        fig = create_ab_test_results_chart(
            sample_data['control_results'], 
            sample_data['treatment_results']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Performance Metrics":
        fig = create_performance_metrics_chart(sample_data['performance'])
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Correlation Heatmap":
        # Create sample correlation data
        corr_data = pd.DataFrame(np.random.randn(100, 5), 
                               columns=['Risk Score', 'Age', 'Credit Score', 'Claims', 'Violations'])
        fig = create_heatmap_chart(corr_data)
        st.plotly_chart(fig, use_container_width=True)