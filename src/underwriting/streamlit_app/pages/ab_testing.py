"""
A/B Testing interface for the Streamlit underwriting application.

This page provides a comprehensive interface for managing A/B tests,
viewing results, and analyzing performance.
"""

import streamlit as st
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

from underwriting.ab_testing.config import ABTestConfigManager, ABTestType
from underwriting.ab_testing.framework import ABTestFramework
from underwriting.ab_testing.sample_generator import ABTestSampleGenerator, ABTestSampleProfile
from underwriting.ab_testing.results import ABTestResultsManager, ReportFormat
from underwriting.streamlit_app.components.charts import (
    create_ab_test_results_chart,
    create_decision_distribution_pie,
    create_performance_metrics_chart,
    create_comparison_bar_chart,
    display_metric_cards
)

def show_ab_testing_page():
    """Display the A/B testing page."""
    
    st.markdown("## 🧪 A/B Testing Interface")
    st.markdown("""
    Create, manage, and analyze A/B tests to optimize underwriting performance.
    Compare different rule sets, AI configurations, and processing approaches.
    """)
    
    # Initialize session state
    if "selected_ab_test" not in st.session_state:
        st.session_state.selected_ab_test = None
    if "ab_test_results" not in st.session_state:
        st.session_state.ab_test_results = {}
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Create Test", "📊 Active Tests", "📈 Results", "⚙️ Configurations", "📚 Analysis"
    ])
    
    with tab1:
        show_create_test_tab()
    
    with tab2:
        show_active_tests_tab()
    
    with tab3:
        show_results_tab()
    
    with tab4:
        show_configurations_tab()
    
    with tab5:
        show_analysis_tab()

def show_create_test_tab():
    """Show the create test tab."""
    
    st.markdown("### 🆕 Create New A/B Test")
    
    # Configuration selection
    config_manager = ABTestConfigManager()
    configs = config_manager.list_configs()
    
    col1, col2 = st.columns(2)
    
    with col1:
        config_options = {f"{config.test_id}: {config.name}": config for config in configs}
        selected_config_key = st.selectbox(
            "Select Test Configuration",
            options=list(config_options.keys()),
            help="Choose a predefined test configuration"
        )
        
        selected_config = config_options[selected_config_key]
        
        # Display configuration details
        st.markdown("#### Configuration Details")
        st.markdown(f"**Type:** {selected_config.test_type.value}")
        st.markdown(f"**Description:** {selected_config.description}")
        st.markdown(f"**Sample Size:** {selected_config.sample_size}")
        st.markdown(f"**Metrics:** {', '.join(selected_config.success_metrics[:3])}")
    
    with col2:
        # Test parameters
        st.markdown("#### Test Parameters")
        
        sample_size = st.number_input(
            "Sample Size",
            min_value=10,
            max_value=10000,
            value=selected_config.sample_size,
            step=10,
            help="Number of applications to test"
        )
        
        sample_profile = st.selectbox(
            "Sample Profile",
            options=[profile.value for profile in ABTestSampleProfile],
            help="Risk profile for sample generation"
        )
        
        auto_start = st.checkbox(
            "Auto-start test",
            value=True,
            help="Automatically start the test after creation"
        )
        
        generate_samples = st.checkbox(
            "Generate sample data",
            value=True,
            help="Generate sample applications for testing"
        )
    
    # Control and treatment preview
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🅰️ Control Configuration")
        st.json(selected_config.control_config)
    
    with col2:
        st.markdown("#### 🅱️ Treatment Configuration")
        st.json(selected_config.treatment_config)
    
    # Create test button
    if st.button("🚀 Create A/B Test", type="primary"):
        with st.spinner("Creating A/B test..."):
            try:
                # Update configuration
                test_config = selected_config
                test_config.sample_size = sample_size
                
                # Create framework and test
                framework = ABTestFramework("streamlit_ab_tests")
                test = framework.create_test(test_config)
                
                st.success(f"✅ A/B test created: {test.test_id}")
                
                # Generate sample data if requested
                if generate_samples:
                    with st.spinner("Generating sample data..."):
                        generator = ABTestSampleGenerator()
                        applications = generator.generate_test_samples(
                            ABTestSampleProfile(sample_profile),
                            sample_size
                        )
                        
                        st.success(f"✅ Generated {len(applications)} sample applications")
                
                # Auto-start if requested
                if auto_start:
                    framework.start_test(test.test_id)
                    st.success("✅ A/B test started successfully")
                
                # Store in session state
                st.session_state.selected_ab_test = test.test_id
                
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error creating A/B test: {str(e)}")

def show_active_tests_tab():
    """Show the active tests tab."""
    
    st.markdown("### 🔄 Active A/B Tests")
    
    # Mock active tests data (in real app, this would come from the framework)
    active_tests = [
        {
            "test_id": "conservative_vs_standard_001",
            "name": "Conservative vs Standard Rule Set",
            "status": "Running",
            "progress": 75,
            "control_results": 375,
            "treatment_results": 385,
            "start_time": datetime.now() - timedelta(hours=4),
            "estimated_completion": datetime.now() + timedelta(hours=1)
        },
        {
            "test_id": "ai_vs_rules_002",
            "name": "AI Enhanced vs Rules Only",
            "status": "Completed",
            "progress": 100,
            "control_results": 500,
            "treatment_results": 500,
            "start_time": datetime.now() - timedelta(days=2),
            "estimated_completion": datetime.now() - timedelta(hours=6)
        },
        {
            "test_id": "gpt4_vs_gpt35_003",
            "name": "GPT-4 vs GPT-3.5 Turbo",
            "status": "Planning",
            "progress": 15,
            "control_results": 0,
            "treatment_results": 0,
            "start_time": None,
            "estimated_completion": datetime.now() + timedelta(days=1)
        }
    ]
    
    # Tests overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tests", len(active_tests))
    
    with col2:
        running_tests = sum(1 for test in active_tests if test["status"] == "Running")
        st.metric("Running", running_tests, f"+{running_tests}")
    
    with col3:
        completed_tests = sum(1 for test in active_tests if test["status"] == "Completed")
        st.metric("Completed", completed_tests)
    
    with col4:
        planning_tests = sum(1 for test in active_tests if test["status"] == "Planning")
        st.metric("Planning", planning_tests)
    
    st.markdown("---")
    
    # Tests table
    for test in active_tests:
        with st.expander(f"📊 {test['name']} ({test['status']})", expanded=test["status"] == "Running"):
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Test Information**")
                st.markdown(f"ID: `{test['test_id']}`")
                st.markdown(f"Status: {get_status_badge(test['status'])}")
                
                if test['start_time']:
                    st.markdown(f"Started: {test['start_time'].strftime('%Y-%m-%d %H:%M')}")
                
                st.markdown(f"Estimated Completion: {test['estimated_completion'].strftime('%Y-%m-%d %H:%M')}")
            
            with col2:
                st.markdown("**Progress**")
                st.progress(test['progress'] / 100)
                st.markdown(f"{test['progress']}% Complete")
                
                st.markdown("**Sample Sizes**")
                st.markdown(f"Control: {test['control_results']}")
                st.markdown(f"Treatment: {test['treatment_results']}")
            
            with col3:
                st.markdown("**Actions**")
                
                if test['status'] == "Running":
                    if st.button(f"⏸️ Pause", key=f"pause_{test['test_id']}"):
                        st.info("Pausing test...")
                    
                    if st.button(f"⏹️ Stop", key=f"stop_{test['test_id']}"):
                        st.info("Stopping test...")
                
                elif test['status'] == "Completed":
                    if st.button(f"📊 View Results", key=f"results_{test['test_id']}"):
                        st.session_state.selected_ab_test = test['test_id']
                        st.rerun()
                
                elif test['status'] == "Planning":
                    if st.button(f"▶️ Start", key=f"start_{test['test_id']}"):
                        st.info("Starting test...")
                
                if st.button(f"📄 Report", key=f"report_{test['test_id']}"):
                    st.info("Generating report...")

def show_results_tab():
    """Show the results tab."""
    
    st.markdown("### 📈 Test Results & Analysis")
    
    # Test selection
    test_options = [
        "conservative_vs_standard_001: Conservative vs Standard (Completed)",
        "ai_vs_rules_002: AI Enhanced vs Rules Only (Completed)",
        "gpt4_vs_gpt35_003: GPT-4 vs GPT-3.5 (Running)"
    ]
    
    selected_test = st.selectbox(
        "Select Test to Analyze",
        options=test_options,
        help="Choose a test to view detailed results"
    )
    
    test_id = selected_test.split(":")[0]
    
    # Generate mock results for demonstration
    results_data = generate_mock_ab_test_results(test_id)
    
    if results_data:
        display_ab_test_results(results_data)
    else:
        st.info("📊 Select a test to view results and analysis.")

def show_configurations_tab():
    """Show the configurations tab."""
    
    st.markdown("### ⚙️ Test Configurations")
    
    config_manager = ABTestConfigManager()
    configs = config_manager.list_configs()
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        test_type_filter = st.selectbox(
            "Filter by Type",
            options=["All"] + [t.value for t in ABTestType],
            help="Filter configurations by test type"
        )
    
    with col2:
        search_term = st.text_input(
            "Search Configurations",
            placeholder="Search by name or description...",
            help="Search configurations by name or description"
        )
    
    with col3:
        tags_filter = st.text_input(
            "Filter by Tags",
            placeholder="e.g., baseline, ai_comparison",
            help="Filter by tags (comma-separated)"
        )
    
    # Apply filters
    filtered_configs = configs
    
    if test_type_filter != "All":
        filtered_configs = [c for c in filtered_configs if c.test_type.value == test_type_filter]
    
    if search_term:
        filtered_configs = [c for c in filtered_configs 
                          if search_term.lower() in c.name.lower() 
                          or search_term.lower() in c.description.lower()]
    
    if tags_filter:
        tag_list = [tag.strip().lower() for tag in tags_filter.split(',')]
        filtered_configs = [c for c in filtered_configs 
                          if any(tag in [t.lower() for t in c.tags] for tag in tag_list)]
    
    st.markdown(f"**Found {len(filtered_configs)} configurations**")
    
    # Display configurations
    for config in filtered_configs:
        with st.expander(f"⚙️ {config.name}", expanded=False):
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Configuration Details**")
                st.markdown(f"**ID:** `{config.test_id}`")
                st.markdown(f"**Type:** {config.test_type.value}")
                st.markdown(f"**Sample Size:** {config.sample_size}")
                st.markdown(f"**Confidence Level:** {config.confidence_level}")
                st.markdown(f"**Min Effect Size:** {config.minimum_effect_size}")
                st.markdown(f"**Tags:** {', '.join(config.tags)}")
            
            with col2:
                st.markdown("**Description**")
                st.markdown(config.description)
                
                st.markdown("**Success Metrics**")
                for metric in config.success_metrics:
                    st.markdown(f"• {metric}")
            
            # Configuration comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🅰️ Control Configuration**")
                st.json(config.control_config)
            
            with col2:
                st.markdown("**🅱️ Treatment Configuration**")
                st.json(config.treatment_config)
            
            # Actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"🚀 Create Test", key=f"create_{config.test_id}"):
                    st.info(f"Creating test with configuration: {config.name}")
            
            with col2:
                if st.button(f"📋 Copy Config", key=f"copy_{config.test_id}"):
                    st.info("Configuration copied to clipboard!")
            
            with col3:
                if st.button(f"📄 Export", key=f"export_{config.test_id}"):
                    st.download_button(
                        "Download Config",
                        data=json.dumps(config.__dict__, indent=2, default=str),
                        file_name=f"{config.test_id}_config.json",
                        mime="application/json",
                        key=f"download_{config.test_id}"
                    )

def show_analysis_tab():
    """Show the analysis tab."""
    
    st.markdown("### 📚 Statistical Analysis & Insights")
    
    # Analysis type selection
    analysis_type = st.radio(
        "Analysis Type",
        options=["Power Analysis", "Effect Size Calculator", "Sample Size Calculator", "Historical Trends"],
        horizontal=True
    )
    
    if analysis_type == "Power Analysis":
        show_power_analysis()
    elif analysis_type == "Effect Size Calculator":
        show_effect_size_calculator()
    elif analysis_type == "Sample Size Calculator":
        show_sample_size_calculator()
    elif analysis_type == "Historical Trends":
        show_historical_trends()

def show_power_analysis():
    """Show power analysis tools."""
    
    st.markdown("#### 🔋 Statistical Power Analysis")
    st.markdown("""
    Calculate the statistical power of your A/B tests to ensure reliable results.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Input Parameters**")
        
        effect_size = st.slider(
            "Effect Size",
            min_value=0.01,
            max_value=0.5,
            value=0.1,
            step=0.01,
            help="Expected difference between groups"
        )
        
        sample_size = st.number_input(
            "Sample Size (per group)",
            min_value=10,
            max_value=10000,
            value=500,
            step=10
        )
        
        alpha = st.slider(
            "Significance Level (α)",
            min_value=0.01,
            max_value=0.1,
            value=0.05,
            step=0.01
        )
    
    with col2:
        # Calculate power (simplified calculation for demo)
        from scipy import stats
        import numpy as np
        
        # Simplified power calculation
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = effect_size * np.sqrt(sample_size/2) - z_alpha
        power = 1 - stats.norm.cdf(z_beta)
        power = max(0, min(1, power))
        
        st.markdown("**Calculated Power**")
        st.metric("Statistical Power", f"{power:.1%}")
        
        if power >= 0.8:
            st.success("✅ Adequate power (≥80%)")
        elif power >= 0.7:
            st.warning("⚠️ Moderate power (70-80%)")
        else:
            st.error("❌ Low power (<70%)")
        
        # Recommendations
        st.markdown("**Recommendations**")
        if power < 0.8:
            required_n = int((z_alpha + stats.norm.ppf(0.8))**2 * 2 / effect_size**2)
            st.markdown(f"• Increase sample size to ~{required_n} per group")
        
        st.markdown(f"• Current setup can detect effects ≥{effect_size:.1%}")

def show_effect_size_calculator():
    """Show effect size calculator."""
    
    st.markdown("#### 📏 Effect Size Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Group Statistics**")
        
        mean1 = st.number_input("Control Group Mean", value=65.0)
        std1 = st.number_input("Control Group Std Dev", value=10.0, min_value=0.1)
        n1 = st.number_input("Control Sample Size", value=500, min_value=1)
        
        mean2 = st.number_input("Treatment Group Mean", value=68.0)
        std2 = st.number_input("Treatment Group Std Dev", value=10.0, min_value=0.1)
        n2 = st.number_input("Treatment Sample Size", value=500, min_value=1)
    
    with col2:
        # Calculate effect sizes
        pooled_std = np.sqrt(((n1-1)*std1**2 + (n2-1)*std2**2) / (n1+n2-2))
        cohens_d = (mean2 - mean1) / pooled_std
        
        st.markdown("**Effect Sizes**")
        st.metric("Cohen's d", f"{cohens_d:.3f}")
        
        # Interpret effect size
        if abs(cohens_d) >= 0.8:
            interpretation = "Large effect"
            color = "🟢"
        elif abs(cohens_d) >= 0.5:
            interpretation = "Medium effect"
            color = "🟡"
        elif abs(cohens_d) >= 0.2:
            interpretation = "Small effect"
            color = "🟠"
        else:
            interpretation = "Negligible effect"
            color = "🔴"
        
        st.markdown(f"{color} **{interpretation}**")
        
        # Additional metrics
        st.metric("Difference", f"{mean2 - mean1:.2f}")
        st.metric("Percent Change", f"{((mean2 - mean1) / mean1 * 100):.1f}%")

def show_sample_size_calculator():
    """Show sample size calculator."""
    
    st.markdown("#### 🎯 Sample Size Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Test Parameters**")
        
        baseline_rate = st.slider(
            "Baseline Conversion Rate",
            min_value=0.01,
            max_value=0.99,
            value=0.15,
            step=0.01,
            format="%.2f"
        )
        
        min_detectable_effect = st.slider(
            "Minimum Detectable Effect",
            min_value=0.01,
            max_value=0.5,
            value=0.05,
            step=0.01,
            format="%.2f"
        )
        
        power = st.slider(
            "Desired Power",
            min_value=0.7,
            max_value=0.99,
            value=0.8,
            step=0.01,
            format="%.2f"
        )
        
        alpha = st.slider(
            "Significance Level",
            min_value=0.01,
            max_value=0.1,
            value=0.05,
            step=0.01,
            format="%.2f"
        )
    
    with col2:
        # Calculate required sample size (simplified)
        from scipy import stats
        
        p1 = baseline_rate
        p2 = baseline_rate + min_detectable_effect
        p_avg = (p1 + p2) / 2
        
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = stats.norm.ppf(power)
        
        n = 2 * (z_alpha * np.sqrt(2 * p_avg * (1 - p_avg)) + 
                z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))**2 / (p2 - p1)**2
        
        n = int(np.ceil(n))
        
        st.markdown("**Required Sample Size**")
        st.metric("Per Group", f"{n:,}")
        st.metric("Total", f"{2*n:,}")
        
        # Test duration estimate
        daily_rate = st.number_input(
            "Applications per Day",
            min_value=1,
            value=100,
            help="Expected daily application volume"
        )
        
        days_needed = (2 * n) / daily_rate
        st.metric("Estimated Duration", f"{days_needed:.1f} days")

def show_historical_trends():
    """Show historical trends analysis."""
    
    st.markdown("#### 📈 Historical Trends Analysis")
    
    # Generate sample historical data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='W')
    
    historical_data = pd.DataFrame({
        'date': dates,
        'tests_created': np.random.poisson(2, len(dates)),
        'avg_sample_size': np.random.normal(1000, 200, len(dates)),
        'success_rate': np.random.beta(2, 1, len(dates)) * 0.4 + 0.6,
        'avg_effect_size': np.random.normal(0.05, 0.02, len(dates))
    })
    
    # Time period selection
    time_period = st.selectbox(
        "Time Period",
        options=["Last 3 months", "Last 6 months", "Last year", "All time"],
        help="Select time period for analysis"
    )
    
    # Metrics over time
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Tests Created Over Time**")
        st.line_chart(historical_data.set_index('date')[['tests_created']])
    
    with col2:
        st.markdown("**Average Success Rate Over Time**")
        st.line_chart(historical_data.set_index('date')[['success_rate']])
    
    # Summary statistics
    st.markdown("#### Summary Statistics")
    
    display_metric_cards({
        "Total Tests": f"{historical_data['tests_created'].sum():,}",
        "Avg Sample Size": f"{historical_data['avg_sample_size'].mean():.0f}",
        "Avg Success Rate": f"{historical_data['success_rate'].mean():.1%}",
        "Avg Effect Size": f"{historical_data['avg_effect_size'].mean():.3f}"
    })

def generate_mock_ab_test_results(test_id: str) -> Dict[str, Any]:
    """Generate mock A/B test results for demonstration."""
    
    np.random.seed(42)  # For consistent demo data
    
    # Generate sample data
    control_scores = np.random.normal(65, 12, 500)
    treatment_scores = np.random.normal(68, 12, 500)
    
    control_decisions = np.random.choice(['ACCEPT', 'DENY', 'ADJUDICATE'], 500, p=[0.6, 0.25, 0.15])
    treatment_decisions = np.random.choice(['ACCEPT', 'DENY', 'ADJUDICATE'], 500, p=[0.65, 0.2, 0.15])
    
    return {
        'test_id': test_id,
        'name': 'Conservative vs Standard Rule Set',
        'status': 'Completed',
        'control_data': {
            'scores': control_scores,
            'decisions': control_decisions,
            'sample_size': 500
        },
        'treatment_data': {
            'scores': treatment_scores,
            'decisions': treatment_decisions,
            'sample_size': 500
        },
        'metrics': {
            'acceptance_rate': {
                'control': 0.60,
                'treatment': 0.65,
                'p_value': 0.023,
                'significant': True
            },
            'avg_risk_score': {
                'control': 65.2,
                'treatment': 68.1,
                'p_value': 0.001,
                'significant': True
            }
        },
        'conclusions': [
            'Treatment variant shows significantly higher acceptance rate',
            'Average risk score increased by 2.9 points',
            'No significant change in adjudication rate'
        ]
    }

def display_ab_test_results(results_data: Dict[str, Any]):
    """Display detailed A/B test results."""
    
    st.markdown(f"#### Test: {results_data['name']}")
    st.markdown(f"**Status:** {get_status_badge(results_data['status'])}")
    
    # Key metrics
    control_data = results_data['control_data']
    treatment_data = results_data['treatment_data']
    metrics = results_data['metrics']
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Control Sample", f"{control_data['sample_size']:,}")
    
    with col2:
        st.metric("Treatment Sample", f"{treatment_data['sample_size']:,}")
    
    with col3:
        acceptance_metric = metrics['acceptance_rate']
        delta = f"+{(acceptance_metric['treatment'] - acceptance_metric['control']):.1%}"
        st.metric("Acceptance Rate Lift", delta)
    
    with col4:
        score_metric = metrics['avg_risk_score']
        delta = f"+{(score_metric['treatment'] - score_metric['control']):.1f}"
        st.metric("Risk Score Change", delta)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Risk Score Distribution**")
        fig = create_ab_test_results_chart(control_data['scores'], treatment_data['scores'])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Decision Distribution**")
        
        # Combine decision data
        control_decisions = pd.Series(control_data['decisions']).value_counts()
        treatment_decisions = pd.Series(treatment_data['decisions']).value_counts()
        
        comparison_data = {
            'Control': control_decisions.to_dict(),
            'Treatment': treatment_decisions.to_dict()
        }
        
        fig = create_comparison_bar_chart(comparison_data, "Decision Distribution Comparison")
        st.plotly_chart(fig, use_container_width=True)
    
    # Statistical significance
    st.markdown("#### 📊 Statistical Analysis")
    
    for metric_name, metric_data in metrics.items():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"**{metric_name.replace('_', ' ').title()}**")
        
        with col2:
            st.markdown(f"Control: {metric_data['control']:.3f}")
        
        with col3:
            st.markdown(f"Treatment: {metric_data['treatment']:.3f}")
        
        with col4:
            significance = "✅ Significant" if metric_data['significant'] else "❌ Not Significant"
            st.markdown(f"{significance} (p={metric_data['p_value']:.3f})")
    
    # Conclusions
    st.markdown("#### 💡 Conclusions")
    for conclusion in results_data['conclusions']:
        st.markdown(f"• {conclusion}")
    
    # Export options
    st.markdown("#### 💾 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download Report"):
            st.info("Generating detailed report...")
    
    with col2:
        if st.button("📊 Export Data"):
            st.info("Preparing data export...")
    
    with col3:
        if st.button("📈 Create Dashboard"):
            st.info("Creating dashboard...")

def get_status_badge(status: str) -> str:
    """Get a colored status badge."""
    
    badges = {
        "Running": "🟢 Running",
        "Completed": "✅ Completed", 
        "Planning": "🟡 Planning",
        "Paused": "⏸️ Paused",
        "Failed": "❌ Failed"
    }
    
    return badges.get(status, f"⚪ {status}")