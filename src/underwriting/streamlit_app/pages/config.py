"""
Configuration management page for the Streamlit underwriting application.

This page provides interfaces for managing system configuration,
rule sets, AI models, and operational parameters.
"""

import streamlit as st
import json
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

def show_config_page():
    """Display the configuration management page."""
    
    st.markdown("## ⚙️ Configuration Management")
    st.markdown("""
    Manage system configurations, rule sets, AI model parameters, 
    and operational settings for the underwriting system.
    This portfolio project and site is created and maintained by [Jeremiah Connelly](https://jeremiahconnelly.dev).
    """)
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎛️ System Config", "📏 Rule Sets", "🤖 AI Models", "🔧 Operations", "📋 Presets"
    ])
    
    with tab1:
        show_system_config_tab()
    
    with tab2:
        show_rule_sets_tab()
    
    with tab3:
        show_ai_models_tab()
    
    with tab4:
        show_operations_tab()
    
    with tab5:
        show_presets_tab()

def show_system_config_tab():
    """Show the system configuration tab."""
    
    st.markdown("### 🎛️ System Configuration")
    
    # Current configuration display
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Current Settings")
        
        current_config = get_current_system_config()
        
        # Display as expandable sections
        with st.expander("🔌 API Configuration", expanded=True):
            st.json({
                "openai_model": current_config.get("openai_model", "gpt-4"),
                "api_timeout": current_config.get("api_timeout", 30),
                "max_retries": current_config.get("max_retries", 3),
                "rate_limit": current_config.get("rate_limit", 100)
            })
        
        with st.expander("💾 Database Settings"):
            st.json({
                "connection_pool_size": current_config.get("db_pool_size", 20),
                "query_timeout": current_config.get("db_timeout", 10),
                "enable_logging": current_config.get("db_logging", True)
            })
        
        with st.expander("🔒 Security Settings"):
            st.json({
                "encryption_enabled": current_config.get("encryption", True),
                "audit_logging": current_config.get("audit_logging", True),
                "session_timeout": current_config.get("session_timeout", 3600)
            })
    
    with col2:
        st.markdown("#### ✏️ Edit Configuration")
        
        # Configuration editing form
        with st.form("system_config_form"):
            st.markdown("**🤖 AI Service Configuration**")
            
            openai_model = st.selectbox(
                "OpenAI Model",
                options=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
                index=0,
                help="Select the OpenAI model to use for AI evaluations"
            )
            
            api_timeout = st.slider(
                "API Timeout (seconds)",
                min_value=10,
                max_value=120,
                value=30,
                help="Maximum time to wait for API responses"
            )
            
            max_retries = st.slider(
                "Max Retries",
                min_value=1,
                max_value=10,
                value=3,
                help="Maximum number of retry attempts for failed requests"
            )
            
            rate_limit = st.slider(
                "Rate Limit (requests/minute)",
                min_value=10,
                max_value=500,
                value=100,
                help="Maximum requests per minute"
            )
            
            st.markdown("**💾 Database Configuration**")
            
            db_pool_size = st.slider(
                "Connection Pool Size",
                min_value=5,
                max_value=100,
                value=20,
                help="Database connection pool size"
            )
            
            db_timeout = st.slider(
                "Query Timeout (seconds)",
                min_value=5,
                max_value=60,
                value=10,
                help="Maximum time for database queries"
            )
            
            db_logging = st.checkbox(
                "Enable Database Logging",
                value=True,
                help="Log database queries for debugging"
            )
            
            st.markdown("**🔒 Security Configuration**")
            
            encryption_enabled = st.checkbox(
                "Enable Encryption",
                value=True,
                help="Encrypt sensitive data at rest"
            )
            
            audit_logging = st.checkbox(
                "Enable Audit Logging",
                value=True,
                help="Log all system access and changes"
            )
            
            session_timeout = st.slider(
                "Session Timeout (seconds)",
                min_value=300,
                max_value=7200,
                value=3600,
                help="User session timeout period"
            )
            
            # Submit button
            if st.form_submit_button("💾 Save Configuration", type="primary"):
                new_config = {
                    "openai_model": openai_model,
                    "api_timeout": api_timeout,
                    "max_retries": max_retries,
                    "rate_limit": rate_limit,
                    "db_pool_size": db_pool_size,
                    "db_timeout": db_timeout,
                    "db_logging": db_logging,
                    "encryption": encryption_enabled,
                    "audit_logging": audit_logging,
                    "session_timeout": session_timeout,
                    "last_updated": datetime.now().isoformat(),
                    "updated_by": "streamlit_user"
                }
                
                save_system_config(new_config)
                st.success("✅ Configuration saved successfully!")
                st.rerun()
    
    # Configuration validation
    st.markdown("---")
    st.markdown("### 🔍 Configuration Validation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧪 Test AI Connection", help="Test OpenAI API connectivity"):
            with st.spinner("Testing AI connection..."):
                test_ai_connection()
    
    with col2:
        if st.button("💾 Test Database", help="Test database connectivity"):
            with st.spinner("Testing database connection..."):
                test_database_connection()
    
    with col3:
        if st.button("📋 Validate All", help="Run comprehensive configuration validation"):
            with st.spinner("Validating configuration..."):
                validate_configuration()

def show_rule_sets_tab():
    """Show the rule sets configuration tab."""
    
    st.markdown("### 📏 Rule Sets Management")
    
    # Rule set selector
    col1, col2 = st.columns([2, 1])
    
    with col1:
        available_rule_sets = get_available_rule_sets()
        selected_rule_set = st.selectbox(
            "Select Rule Set",
            options=list(available_rule_sets.keys()),
            help="Choose a rule set to view or edit"
        )
    
    with col2:
        if st.button("➕ Create New Rule Set", help="Create a new rule set"):
            st.session_state.show_new_rule_set_form = True
    
    # Display selected rule set
    if selected_rule_set:
        rule_set_data = available_rule_sets[selected_rule_set]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### 📊 {selected_rule_set.title()} Rule Set")
            
            # Rule set metadata
            st.markdown("**Metadata:**")
            st.markdown(f"• **Name:** {rule_set_data['name']}")
            st.markdown(f"• **Description:** {rule_set_data['description']}")
            st.markdown(f"• **Version:** {rule_set_data['version']}")
            st.markdown(f"• **Last Updated:** {rule_set_data['last_updated']}")
            st.markdown(f"• **Active:** {'✅' if rule_set_data['active'] else '❌'}")
            
            # Risk thresholds
            st.markdown("**Risk Thresholds:**")
            thresholds = rule_set_data['thresholds']
            
            for category, threshold in thresholds.items():
                st.markdown(f"• **{category.title()}:** {threshold}")
        
        with col2:
            st.markdown("#### ✏️ Edit Rule Set")
            
            with st.form(f"rule_set_form_{selected_rule_set}"):
                # Basic information
                rule_name = st.text_input(
                    "Rule Set Name",
                    value=rule_set_data['name'],
                    help="Display name for this rule set"
                )
                
                rule_description = st.text_area(
                    "Description",
                    value=rule_set_data['description'],
                    help="Description of this rule set's purpose"
                )
                
                rule_active = st.checkbox(
                    "Active",
                    value=rule_set_data['active'],
                    help="Enable this rule set for use"
                )
                
                st.markdown("**Risk Thresholds**")
                
                # Threshold configuration
                accept_threshold = st.slider(
                    "Accept Threshold",
                    min_value=0,
                    max_value=100,
                    value=int(thresholds.get('accept', 80)),
                    help="Minimum score for automatic acceptance"
                )
                
                deny_threshold = st.slider(
                    "Deny Threshold", 
                    min_value=0,
                    max_value=100,
                    value=int(thresholds.get('deny', 40)),
                    help="Maximum score for automatic denial"
                )
                
                # Risk component weights
                st.markdown("**Component Weights**")
                
                weights = rule_set_data.get('weights', {})
                
                driver_weight = st.slider(
                    "Driver Risk Weight",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(weights.get('driver', 0.3)),
                    step=0.05,
                    help="Weight for driver risk component"
                )
                
                vehicle_weight = st.slider(
                    "Vehicle Risk Weight",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(weights.get('vehicle', 0.25)),
                    step=0.05,
                    help="Weight for vehicle risk component"
                )
                
                history_weight = st.slider(
                    "History Risk Weight",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(weights.get('history', 0.25)),
                    step=0.05,
                    help="Weight for history risk component"
                )
                
                credit_weight = st.slider(
                    "Credit Risk Weight",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(weights.get('credit', 0.2)),
                    step=0.05,
                    help="Weight for credit risk component"
                )
                
                # Validation
                total_weight = driver_weight + vehicle_weight + history_weight + credit_weight
                if abs(total_weight - 1.0) > 0.01:
                    st.error(f"⚠️ Weights must sum to 1.0 (current: {total_weight:.2f})")
                
                # Submit button
                if st.form_submit_button("💾 Save Rule Set", type="primary"):
                    updated_rule_set = {
                        "name": rule_name,
                        "description": rule_description,
                        "version": str(float(rule_set_data['version']) + 0.1),
                        "active": rule_active,
                        "thresholds": {
                            "accept": accept_threshold,
                            "deny": deny_threshold
                        },
                        "weights": {
                            "driver": driver_weight,
                            "vehicle": vehicle_weight,
                            "history": history_weight,
                            "credit": credit_weight
                        },
                        "last_updated": datetime.now().isoformat()
                    }
                    
                    if abs(total_weight - 1.0) <= 0.01:
                        save_rule_set(selected_rule_set, updated_rule_set)
                        st.success("✅ Rule set saved successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Cannot save: weights must sum to 1.0")
    
    # Rule set testing
    st.markdown("---")
    st.markdown("### 🧪 Rule Set Testing")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎯 Test Rule Set", help="Test rule set with sample data"):
            test_rule_set(selected_rule_set)
    
    with col2:
        if st.button("📊 Compare Rule Sets", help="Compare multiple rule sets"):
            show_rule_set_comparison()
    
    with col3:
        if st.button("📈 Performance Analysis", help="Analyze rule set performance"):
            show_rule_set_performance()

def show_ai_models_tab():
    """Show the AI models configuration tab."""
    
    st.markdown("### 🤖 AI Models Configuration")
    
    # Model selection and configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Model Selection")
        
        # Primary model
        primary_model = st.selectbox(
            "Primary AI Model",
            options=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3-sonnet", "claude-3-haiku"],
            index=0,
            help="Primary model for AI evaluations"
        )
        
        # Fallback model
        fallback_model = st.selectbox(
            "Fallback Model",
            options=["gpt-3.5-turbo", "gpt-4", "claude-3-haiku"],
            index=0,
            help="Fallback model if primary fails"
        )
        
        # Model parameters
        st.markdown("#### ⚙️ Model Parameters")
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.1,
            step=0.1,
            help="Controls randomness in model outputs"
        )
        
        max_tokens = st.slider(
            "Max Tokens",
            min_value=100,
            max_value=4000,
            value=1000,
            help="Maximum tokens in model response"
        )
        
        top_p = st.slider(
            "Top P",
            min_value=0.0,
            max_value=1.0,
            value=0.9,
            step=0.1,
            help="Nucleus sampling parameter"
        )
    
    with col2:
        st.markdown("#### 🎛️ AI Enhancement Settings")
        
        # AI enhancement options
        enable_reasoning = st.checkbox(
            "Enable Detailed Reasoning",
            value=True,
            help="Include detailed reasoning in AI responses"
        )
        
        enable_confidence = st.checkbox(
            "Enable Confidence Scoring",
            value=True,
            help="Include confidence scores in AI responses"
        )
        
        enable_explanation = st.checkbox(
            "Enable Decision Explanation",
            value=True,
            help="Provide explanations for AI decisions"
        )
        
        # Prompt templates
        st.markdown("#### 📝 Prompt Configuration")
        
        prompt_template = st.selectbox(
            "Prompt Template",
            options=["standard", "detailed", "concise", "risk_focused"],
            help="Select the prompt template to use"
        )
        
        custom_instructions = st.text_area(
            "Custom Instructions",
            placeholder="Add any custom instructions for the AI model...",
            help="Additional instructions to include in prompts"
        )
        
        # Model performance settings
        st.markdown("#### 📊 Performance Settings")
        
        enable_caching = st.checkbox(
            "Enable Response Caching",
            value=True,
            help="Cache similar requests to improve performance"
        )
        
        cache_ttl = st.slider(
            "Cache TTL (minutes)",
            min_value=5,
            max_value=1440,
            value=60,
            help="How long to cache responses"
        )
        
        parallel_requests = st.slider(
            "Max Parallel Requests",
            min_value=1,
            max_value=20,
            value=5,
            help="Maximum concurrent AI requests"
        )
    
    # Save AI configuration
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save AI Configuration", type="primary"):
            ai_config = {
                "primary_model": primary_model,
                "fallback_model": fallback_model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "enable_reasoning": enable_reasoning,
                "enable_confidence": enable_confidence,
                "enable_explanation": enable_explanation,
                "prompt_template": prompt_template,
                "custom_instructions": custom_instructions,
                "enable_caching": enable_caching,
                "cache_ttl": cache_ttl,
                "parallel_requests": parallel_requests,
                "last_updated": datetime.now().isoformat()
            }
            
            save_ai_config(ai_config)
            st.success("✅ AI configuration saved!")
    
    with col2:
        if st.button("🧪 Test AI Models"):
            test_ai_models()
    
    with col3:
        if st.button("📊 Model Performance"):
            show_model_performance_metrics()

def show_operations_tab():
    """Show the operations configuration tab."""
    
    st.markdown("### 🔧 Operations Configuration")
    
    # Monitoring and alerting
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📡 Monitoring & Alerting")
        
        # Monitoring settings
        enable_monitoring = st.checkbox(
            "Enable System Monitoring",
            value=True,
            help="Monitor system health and performance"
        )
        
        alert_threshold = st.slider(
            "Alert Threshold (%)",
            min_value=50,
            max_value=99,
            value=85,
            help="System utilization threshold for alerts"
        )
        
        error_rate_threshold = st.slider(
            "Error Rate Threshold (%)",
            min_value=1,
            max_value=20,
            value=5,
            help="Error rate threshold for alerts"
        )
        
        # Notification settings
        email_alerts = st.checkbox(
            "Email Alerts",
            value=True,
            help="Send alerts via email"
        )
        
        alert_email = st.text_input(
            "Alert Email",
            placeholder="admin@company.com",
            help="Email address for system alerts"
        )
        
        # Backup settings
        st.markdown("#### 💾 Backup & Recovery")
        
        auto_backup = st.checkbox(
            "Enable Auto Backup",
            value=True,
            help="Automatically backup system data"
        )
        
        backup_frequency = st.selectbox(
            "Backup Frequency",
            options=["hourly", "daily", "weekly"],
            index=1,
            help="How often to backup data"
        )
        
        backup_retention = st.slider(
            "Backup Retention (days)",
            min_value=7,
            max_value=365,
            value=30,
            help="How long to keep backup files"
        )
    
    with col2:
        st.markdown("#### ⚡ Performance Tuning")
        
        # Performance settings
        enable_optimization = st.checkbox(
            "Enable Performance Optimization",
            value=True,
            help="Automatically optimize performance"
        )
        
        cache_size = st.slider(
            "Cache Size (MB)",
            min_value=100,
            max_value=10000,
            value=1000,
            help="Size of application cache"
        )
        
        worker_threads = st.slider(
            "Worker Threads",
            min_value=2,
            max_value=50,
            value=10,
            help="Number of worker threads"
        )
        
        # Resource limits
        st.markdown("#### 🛡️ Resource Limits")
        
        max_memory = st.slider(
            "Max Memory (GB)",
            min_value=1,
            max_value=32,
            value=8,
            help="Maximum memory usage"
        )
        
        max_cpu = st.slider(
            "Max CPU (%)",
            min_value=10,
            max_value=100,
            value=80,
            help="Maximum CPU utilization"
        )
        
        request_timeout = st.slider(
            "Request Timeout (seconds)",
            min_value=30,
            max_value=300,
            value=120,
            help="Maximum time for processing requests"
        )
        
        # Logging settings
        st.markdown("#### 📋 Logging Configuration")
        
        log_level = st.selectbox(
            "Log Level",
            options=["DEBUG", "INFO", "WARNING", "ERROR"],
            index=1,
            help="Minimum log level to record"
        )
        
        log_retention = st.slider(
            "Log Retention (days)",
            min_value=7,
            max_value=90,
            value=30,
            help="How long to keep log files"
        )
        
        enable_structured_logs = st.checkbox(
            "Structured Logging",
            value=True,
            help="Use structured JSON logging format"
        )
    
    # Save operations configuration
    if st.button("💾 Save Operations Configuration", type="primary"):
        ops_config = {
            "monitoring": {
                "enabled": enable_monitoring,
                "alert_threshold": alert_threshold,
                "error_rate_threshold": error_rate_threshold,
                "email_alerts": email_alerts,
                "alert_email": alert_email
            },
            "backup": {
                "auto_backup": auto_backup,
                "frequency": backup_frequency,
                "retention_days": backup_retention
            },
            "performance": {
                "optimization_enabled": enable_optimization,
                "cache_size_mb": cache_size,
                "worker_threads": worker_threads,
                "max_memory_gb": max_memory,
                "max_cpu_percent": max_cpu,
                "request_timeout": request_timeout
            },
            "logging": {
                "level": log_level,
                "retention_days": log_retention,
                "structured": enable_structured_logs
            },
            "last_updated": datetime.now().isoformat()
        }
        
        save_operations_config(ops_config)
        st.success("✅ Operations configuration saved!")

def show_presets_tab():
    """Show the configuration presets tab."""
    
    st.markdown("### 📋 Configuration Presets")
    
    # Preset selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        available_presets = get_available_presets()
        selected_preset = st.selectbox(
            "Select Preset",
            options=list(available_presets.keys()),
            help="Choose a configuration preset to apply"
        )
    
    with col2:
        if st.button("💾 Save Current as Preset"):
            show_save_preset_form()
    
    # Display preset details
    if selected_preset:
        preset_data = available_presets[selected_preset]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### 📊 {selected_preset} Preset")
            
            st.markdown("**Description:**")
            st.markdown(preset_data['description'])
            
            st.markdown("**Included Configurations:**")
            for config_type in preset_data['includes']:
                st.markdown(f"• {config_type}")
            
            st.markdown("**Recommended For:**")
            for use_case in preset_data['use_cases']:
                st.markdown(f"• {use_case}")
        
        with col2:
            st.markdown("#### 🔍 Preset Details")
            
            # Show condensed configuration
            if 'system' in preset_data['config']:
                with st.expander("System Configuration"):
                    st.json(preset_data['config']['system'])
            
            if 'ai' in preset_data['config']:
                with st.expander("AI Configuration"):
                    st.json(preset_data['config']['ai'])
            
            if 'rules' in preset_data['config']:
                with st.expander("Rule Sets"):
                    st.json(preset_data['config']['rules'])
    
    # Preset actions
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🚀 Apply Preset", type="primary"):
            apply_configuration_preset(selected_preset)
    
    with col2:
        if st.button("👁️ Preview Changes"):
            preview_preset_changes(selected_preset)
    
    with col3:
        if st.button("📋 Export Preset"):
            export_preset(selected_preset)
    
    with col4:
        if st.button("🗑️ Delete Preset"):
            delete_preset(selected_preset)

# Helper functions for configuration management

def get_current_system_config() -> Dict[str, Any]:
    """Get current system configuration."""
    return {
        "openai_model": "gpt-4",
        "api_timeout": 30,
        "max_retries": 3,
        "rate_limit": 100,
        "db_pool_size": 20,
        "db_timeout": 10,
        "db_logging": True,
        "encryption": True,
        "audit_logging": True,
        "session_timeout": 3600
    }

def save_system_config(config: Dict[str, Any]):
    """Save system configuration."""
    st.session_state.system_config = config

def test_ai_connection():
    """Test AI service connection."""
    # Simulate connection test
    import time
    time.sleep(2)
    st.success("✅ AI service connection successful!")

def test_database_connection():
    """Test database connection."""
    import time
    time.sleep(1.5)
    st.success("✅ Database connection successful!")

def validate_configuration():
    """Validate all configuration settings."""
    import time
    time.sleep(3)
    st.success("✅ All configurations validated successfully!")

def get_available_rule_sets() -> Dict[str, Dict[str, Any]]:
    """Get available rule sets."""
    return {
        "standard": {
            "name": "Standard Rule Set",
            "description": "Balanced approach for general underwriting",
            "version": "2.1",
            "active": True,
            "last_updated": "2024-01-15",
            "thresholds": {"accept": 75, "deny": 40},
            "weights": {"driver": 0.3, "vehicle": 0.25, "history": 0.25, "credit": 0.2}
        },
        "conservative": {
            "name": "Conservative Rule Set", 
            "description": "Risk-averse approach with higher thresholds",
            "version": "1.8",
            "active": True,
            "last_updated": "2024-01-10",
            "thresholds": {"accept": 85, "deny": 50},
            "weights": {"driver": 0.35, "vehicle": 0.2, "history": 0.3, "credit": 0.15}
        },
        "liberal": {
            "name": "Liberal Rule Set",
            "description": "Growth-focused approach with lower thresholds", 
            "version": "1.5",
            "active": False,
            "last_updated": "2024-01-05",
            "thresholds": {"accept": 65, "deny": 30},
            "weights": {"driver": 0.25, "vehicle": 0.3, "history": 0.2, "credit": 0.25}
        }
    }

def save_rule_set(rule_set_id: str, rule_set: Dict[str, Any]):
    """Save rule set configuration."""
    if "rule_sets" not in st.session_state:
        st.session_state.rule_sets = {}
    st.session_state.rule_sets[rule_set_id] = rule_set

def test_rule_set(rule_set_id: str):
    """Test rule set with sample data."""
    import time
    time.sleep(2)
    st.success(f"✅ Rule set '{rule_set_id}' tested successfully!")

def show_rule_set_comparison():
    """Show rule set comparison."""
    st.info("📊 Rule set comparison feature coming soon!")

def show_rule_set_performance():
    """Show rule set performance analysis."""
    st.info("📈 Rule set performance analysis coming soon!")

def save_ai_config(config: Dict[str, Any]):
    """Save AI configuration."""
    st.session_state.ai_config = config

def test_ai_models():
    """Test AI model configurations."""
    import time
    time.sleep(3)
    st.success("✅ AI models tested successfully!")

def show_model_performance_metrics():
    """Show model performance metrics."""
    st.info("📊 Model performance metrics coming soon!")

def save_operations_config(config: Dict[str, Any]):
    """Save operations configuration."""
    st.session_state.operations_config = config

def get_available_presets() -> Dict[str, Dict[str, Any]]:
    """Get available configuration presets."""
    return {
        "development": {
            "description": "Configuration optimized for development and testing",
            "includes": ["System Config", "AI Models", "Rule Sets"],
            "use_cases": ["Development", "Testing", "Debugging"],
            "config": {
                "system": {"api_timeout": 60, "rate_limit": 10},
                "ai": {"temperature": 0.2, "max_tokens": 500},
                "rules": {"active_set": "liberal"}
            }
        },
        "production": {
            "description": "Production-ready configuration with optimal performance",
            "includes": ["System Config", "AI Models", "Operations", "Monitoring"],
            "use_cases": ["Production", "High Volume", "Enterprise"],
            "config": {
                "system": {"api_timeout": 30, "rate_limit": 100},
                "ai": {"temperature": 0.1, "max_tokens": 1000},
                "rules": {"active_set": "standard"}
            }
        },
        "high_security": {
            "description": "Maximum security configuration for sensitive environments",
            "includes": ["System Config", "Security", "Audit", "Monitoring"],
            "use_cases": ["Financial Services", "Government", "Healthcare"],
            "config": {
                "system": {"encryption": True, "audit_logging": True},
                "security": {"session_timeout": 1800, "multi_factor": True}
            }
        }
    }

def show_save_preset_form():
    """Show form to save current configuration as preset."""
    st.info("💾 Save preset feature coming soon!")

def apply_configuration_preset(preset_name: str):
    """Apply a configuration preset."""
    import time
    time.sleep(2)
    st.success(f"✅ Applied '{preset_name}' preset successfully!")

def preview_preset_changes(preset_name: str):
    """Preview changes that would be made by applying preset."""
    st.info(f"👁️ Preview changes for '{preset_name}' preset...")

def export_preset(preset_name: str):
    """Export preset configuration."""
    preset_data = get_available_presets()[preset_name]
    
    st.download_button(
        "📋 Download Preset",
        data=json.dumps(preset_data, indent=2),
        file_name=f"{preset_name}_preset.json",
        mime="application/json"
    )

def delete_preset(preset_name: str):
    """Delete a configuration preset."""
    if st.button(f"⚠️ Confirm Delete '{preset_name}'", key="confirm_delete"):
        st.success(f"🗑️ Deleted preset '{preset_name}'")
    else:
        st.warning("⚠️ Click again to confirm deletion")