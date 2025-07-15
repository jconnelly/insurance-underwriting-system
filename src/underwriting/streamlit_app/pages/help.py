"""
Help and documentation page for the Streamlit underwriting application.

This page provides comprehensive documentation, tutorials, and support
information for using the underwriting system.
"""

import streamlit as st
from datetime import datetime

def show_help_page():
    """Display the help and documentation page."""
    
    st.markdown("## 📚 Help & Documentation")
    st.markdown("""
    Welcome to the Insurance Underwriting System documentation. 
    Find guides, tutorials, and support information below.
    """)
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📖 Getting Started", "🎯 User Guide", "🤖 AI Features", "🔧 Technical", "❓ FAQ"
    ])
    
    with tab1:
        show_getting_started_tab()
    
    with tab2:
        show_user_guide_tab()
    
    with tab3:
        show_ai_features_tab()
    
    with tab4:
        show_technical_tab()
    
    with tab5:
        show_faq_tab()

def show_getting_started_tab():
    """Show the getting started documentation."""
    
    st.markdown("### 📖 Getting Started")
    
    # Quick start guide
    st.markdown("#### 🚀 Quick Start Guide")
    
    with st.expander("🎯 1. System Overview", expanded=True):
        st.markdown("""
        The Insurance Underwriting System is a comprehensive platform that provides:
        
        - **AI-Enhanced Evaluation**: Intelligent risk assessment using advanced AI models
        - **Rules-Based Processing**: Traditional rule-based underwriting with customizable rule sets
        - **A/B Testing Framework**: Statistical testing for optimization and comparison
        - **Analytics Dashboard**: Comprehensive reporting and performance insights
        - **Configuration Management**: Flexible system configuration and customization
        
        **Key Benefits:**
        - Faster processing times (average 2.4 seconds)
        - Higher accuracy with AI enhancement (+12% improvement)
        - Comprehensive audit trail and compliance features
        - Scalable architecture for high-volume processing
        """)
    
    with st.expander("📝 2. Creating Your First Evaluation"):
        st.markdown("""
        Follow these steps to evaluate your first application:
        
        1. **Navigate to Application Evaluation**
           - Click on "📝 Application Evaluation" in the sidebar
           - Select your preferred evaluation mode (AI-Enhanced recommended)
        
        2. **Enter Application Data**
           - **Driver Tab**: Complete driver information (name, age, license details)
           - **Vehicle Tab**: Add vehicle information (year, make, model, VIN)
           - **Violations Tab**: Record any traffic violations (optional)
           - **Claims Tab**: Add insurance claims history (optional)
           - **Details Tab**: Complete application metadata
        
        3. **Run Evaluation**
           - Click "🧠 Evaluate Application" button
           - Wait for processing (typically 2-5 seconds)
           - Review the comprehensive results
        
        4. **Export Results**
           - Download evaluation results as JSON
           - Save application data for future reference
           - Create reports for stakeholders
        
        💡 **Tip**: Use the "📋 Load Sample" button to populate the form with sample data for testing.
        """)
    
    with st.expander("🧪 3. Setting Up A/B Tests"):
        st.markdown("""
        A/B testing helps optimize your underwriting performance:
        
        1. **Navigate to A/B Testing**
           - Click on "🧪 A/B Testing" in the sidebar
           - Review existing test configurations
        
        2. **Create a New Test**
           - Go to the "📝 Create Test" tab
           - Select a predefined test configuration
           - Adjust sample size and parameters as needed
           - Choose to generate sample data or use real applications
        
        3. **Monitor Test Progress**
           - Track test progress in "📊 Active Tests" tab
           - View real-time results and statistics
           - Pause or stop tests as needed
        
        4. **Analyze Results**
           - Review detailed results in "📈 Results" tab
           - Examine statistical significance
           - Download comprehensive reports
        
        💡 **Best Practice**: Start with smaller sample sizes to validate test setup before scaling up.
        """)
    
    with st.expander("📊 4. Using Analytics Dashboard"):
        st.markdown("""
        The analytics dashboard provides comprehensive insights:
        
        1. **Overview Metrics**
           - Key performance indicators (KPIs)
           - Decision distribution and trends
           - Processing performance metrics
        
        2. **Performance Analysis**
           - Model accuracy and precision metrics
           - Processing time analysis
           - Error rate monitoring
        
        3. **Trend Analysis**
           - Application volume trends
           - Acceptance rate patterns
           - Regional performance comparison
           - Seasonal analysis
        
        4. **Deep Dive Analytics**
           - Cohort analysis
           - Feature importance
           - Anomaly detection
           - Customer segmentation
        
        5. **Reports and Exports**
           - Executive summaries
           - Performance reports
           - Custom report builder
           - Multiple export formats
        
        💡 **Navigation Tip**: Use the time period selector to focus on specific date ranges.
        """)
    
    # System requirements
    st.markdown("#### 💻 System Requirements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Minimum Requirements:**")
        st.markdown("""
        - **Browser**: Chrome 90+, Firefox 88+, Safari 14+
        - **RAM**: 4GB available memory
        - **CPU**: Dual-core processor 2.0GHz+
        - **Network**: Stable internet connection
        - **Screen**: 1024x768 resolution minimum
        """)
    
    with col2:
        st.markdown("**Recommended Setup:**")
        st.markdown("""
        - **Browser**: Latest Chrome or Firefox
        - **RAM**: 8GB+ available memory
        - **CPU**: Quad-core processor 2.5GHz+
        - **Network**: High-speed broadband
        - **Screen**: 1920x1080 resolution or higher
        """)
    
    # Support contact
    st.markdown("#### 📞 Getting Support")
    
    support_info = {
        "Documentation": "This help system and user guides",
        "Email Support": "support@underwriting-system.com",
        "Phone Support": "1-800-UNDERWRITE (business hours)",
        "Live Chat": "Available in the bottom-right corner",
        "Training": "Schedule training sessions with our team"
    }
    
    for support_type, details in support_info.items():
        st.markdown(f"**{support_type}**: {details}")

def show_user_guide_tab():
    """Show the detailed user guide."""
    
    st.markdown("### 🎯 User Guide")
    
    # Feature selector
    feature = st.selectbox(
        "Select Feature",
        options=[
            "Application Evaluation",
            "A/B Testing",
            "Analytics Dashboard", 
            "Configuration Management",
            "Data Export & Import",
            "User Management",
            "Reporting"
        ]
    )
    
    if feature == "Application Evaluation":
        show_evaluation_guide()
    elif feature == "A/B Testing":
        show_ab_testing_guide()
    elif feature == "Analytics Dashboard":
        show_analytics_guide()
    elif feature == "Configuration Management":
        show_config_guide()
    elif feature == "Data Export & Import":
        show_data_guide()
    elif feature == "User Management":
        show_user_management_guide()
    elif feature == "Reporting":
        show_reporting_guide()

def show_evaluation_guide():
    """Show detailed evaluation guide."""
    
    st.markdown("#### 📝 Application Evaluation Guide")
    
    st.markdown("**Evaluation Modes:**")
    
    modes_info = {
        "AI-Enhanced (Recommended)": {
            "description": "Combines AI intelligence with rules-based logic",
            "accuracy": "Highest accuracy (+12% improvement)",
            "speed": "Fast processing (2-4 seconds)",
            "use_case": "Best for most applications"
        },
        "Rules Only": {
            "description": "Traditional rules-based processing only",
            "accuracy": "Good baseline accuracy",
            "speed": "Fastest processing (<1 second)",
            "use_case": "High-volume, simple cases"
        },
        "AI Only": {
            "description": "Pure AI evaluation without rules",
            "accuracy": "High accuracy but may be inconsistent",
            "speed": "Moderate processing (3-6 seconds)",
            "use_case": "Complex or edge cases"
        }
    }
    
    for mode, info in modes_info.items():
        with st.expander(f"🎯 {mode}"):
            for key, value in info.items():
                st.markdown(f"**{key.title()}**: {value}")
    
    st.markdown("**Rule Sets:**")
    
    rule_sets = {
        "Standard": "Balanced approach for general underwriting",
        "Conservative": "Risk-averse with higher acceptance thresholds",
        "Liberal": "Growth-focused with lower thresholds"
    }
    
    for rule_set, description in rule_sets.items():
        st.markdown(f"- **{rule_set}**: {description}")
    
    st.markdown("**Form Completion Tips:**")
    st.markdown("""
    - **Required Fields**: All fields marked with * must be completed
    - **VIN Validation**: Vehicle VIN numbers are automatically validated
    - **Age Calculation**: Driver age is calculated from date of birth
    - **License Status**: Ensure license status is current and valid
    - **Violation Details**: Include specific violation types and dates
    - **Claim Amounts**: Enter claim amounts without currency symbols
    """)

def show_ab_testing_guide():
    """Show A/B testing guide."""
    
    st.markdown("#### 🧪 A/B Testing Guide")
    
    st.markdown("**Test Types:**")
    
    test_types = {
        "Rule Set Comparison": "Compare different rule sets (e.g., Standard vs Conservative)",
        "AI Model Comparison": "Test different AI models or configurations",
        "Threshold Testing": "Optimize acceptance/denial thresholds",
        "Feature Testing": "Test new features or algorithms"
    }
    
    for test_type, description in test_types.items():
        st.markdown(f"- **{test_type}**: {description}")
    
    st.markdown("**Sample Size Guidelines:**")
    st.markdown("""
    - **Minimum**: 100 applications per group
    - **Recommended**: 500+ applications per group
    - **High Volume**: 1000+ applications for precise results
    - **Statistical Power**: Use the built-in calculator for optimal sizes
    """)
    
    st.markdown("**Best Practices:**")
    st.markdown("""
    1. **Clear Hypothesis**: Define what you're testing and expected outcomes
    2. **Control Variables**: Change only one factor at a time
    3. **Random Assignment**: Ensure random distribution between groups
    4. **Statistical Significance**: Wait for p-value < 0.05 before concluding
    5. **Business Impact**: Consider practical significance, not just statistical
    6. **Documentation**: Record test parameters and results for future reference
    """)

def show_analytics_guide():
    """Show analytics dashboard guide."""
    
    st.markdown("#### 📊 Analytics Dashboard Guide")
    
    st.markdown("**Dashboard Sections:**")
    
    sections = {
        "Overview": "Key metrics and high-level performance indicators",
        "Performance": "Detailed accuracy, precision, and processing metrics",
        "Trends": "Time-based analysis and pattern identification",
        "Deep Dive": "Advanced analytics and specialized analysis",
        "Reports": "Formatted reports and export capabilities"
    }
    
    for section, description in sections.items():
        st.markdown(f"- **{section}**: {description}")
    
    st.markdown("**Key Metrics Explained:**")
    
    metrics = {
        "Acceptance Rate": "Percentage of applications automatically accepted",
        "Risk Score": "Calculated risk level (0-100, higher = safer)",
        "Processing Time": "Average time to complete evaluation",
        "Accuracy": "Percentage of correct predictions vs actual outcomes",
        "Precision": "True positives / (True positives + False positives)",
        "Recall": "True positives / (True positives + False negatives)"
    }
    
    for metric, definition in metrics.items():
        st.markdown(f"- **{metric}**: {definition}")

def show_config_guide():
    """Show configuration management guide."""
    
    st.markdown("#### ⚙️ Configuration Management Guide")
    
    st.markdown("**Configuration Categories:**")
    
    categories = {
        "System Config": "Core system settings, API configurations, timeouts",
        "Rule Sets": "Underwriting rules, thresholds, and weights",
        "AI Models": "AI model selection, parameters, and prompts",
        "Operations": "Monitoring, alerts, backup, and performance settings",
        "Presets": "Pre-configured settings for different environments"
    }
    
    for category, description in categories.items():
        st.markdown(f"- **{category}**: {description}")
    
    st.markdown("**Configuration Best Practices:**")
    st.markdown("""
    1. **Test Changes**: Always test configuration changes in a non-production environment
    2. **Backup First**: Create configuration backups before making changes
    3. **Document Changes**: Record what changes were made and why
    4. **Gradual Rollout**: Implement changes gradually, not all at once
    5. **Monitor Impact**: Watch system performance after configuration changes
    6. **Use Presets**: Leverage presets for consistent environment setup
    """)

def show_data_guide():
    """Show data export and import guide."""
    
    st.markdown("#### 💾 Data Export & Import Guide")
    
    st.markdown("**Export Options:**")
    st.markdown("""
    - **JSON**: Structured data format, ideal for APIs and integrations
    - **CSV**: Spreadsheet format, good for data analysis and reporting
    - **PDF**: Formatted reports for printing and presentation
    - **Excel**: Advanced spreadsheet format with multiple sheets
    """)
    
    st.markdown("**Import Capabilities:**")
    st.markdown("""
    - **Bulk Applications**: Import multiple applications from CSV/Excel
    - **Configuration**: Import rule sets and system configurations
    - **Historical Data**: Import past evaluation results for analysis
    - **User Data**: Import user accounts and permissions
    """)

def show_user_management_guide():
    """Show user management guide."""
    
    st.markdown("#### 👥 User Management Guide")
    
    st.markdown("**User Roles:**")
    
    roles = {
        "Administrator": "Full system access, configuration management",
        "Underwriter": "Evaluate applications, view analytics, limited config",
        "Analyst": "View analytics and reports, no evaluation access",
        "Reviewer": "Review and approve high-risk applications",
        "Auditor": "Read-only access to audit trails and reports"
    }
    
    for role, permissions in roles.items():
        st.markdown(f"- **{role}**: {permissions}")

def show_reporting_guide():
    """Show reporting guide."""
    
    st.markdown("#### 📄 Reporting Guide")
    
    st.markdown("**Available Reports:**")
    
    reports = {
        "Executive Summary": "High-level metrics and key insights",
        "Performance Report": "Detailed accuracy and processing metrics",
        "Risk Analysis": "Risk distribution and component analysis",
        "A/B Test Report": "Statistical analysis of test results",
        "Audit Report": "System access and change tracking"
    }
    
    for report, description in reports.items():
        st.markdown(f"- **{report}**: {description}")

def show_ai_features_tab():
    """Show AI features documentation."""
    
    st.markdown("### 🤖 AI Features")
    
    # AI capabilities overview
    st.markdown("#### 🧠 AI Capabilities")
    
    with st.expander("🎯 Risk Assessment", expanded=True):
        st.markdown("""
        **Advanced Risk Evaluation**: Our AI system analyzes multiple data points to provide comprehensive risk assessment:
        
        - **Driver Profile Analysis**: Age, experience, history, behavior patterns
        - **Vehicle Risk Scoring**: Safety ratings, theft risk, repair costs
        - **Historical Pattern Recognition**: Claims history, violation patterns
        - **Credit Risk Integration**: Financial stability indicators
        - **Contextual Understanding**: Geographic, seasonal, and market factors
        
        **Key Benefits:**
        - More nuanced risk assessment than traditional rules
        - Ability to identify complex patterns and correlations
        - Continuous learning from new data and outcomes
        - Reduced bias through data-driven decisions
        """)
    
    with st.expander("💡 Decision Reasoning"):
        st.markdown("""
        **Explainable AI**: Our system provides clear reasoning for every AI decision:
        
        - **Factor Identification**: Which factors most influenced the decision
        - **Risk Contribution**: How each component contributed to the overall risk
        - **Confidence Scoring**: How confident the AI is in its assessment
        - **Alternative Scenarios**: What would change the decision outcome
        - **Regulatory Compliance**: Explanations meet regulatory requirements
        
        **Transparency Features:**
        - Natural language explanations for business users
        - Technical details for data scientists and engineers
        - Audit trails for compliance and review processes
        """)
    
    with st.expander("🔄 Continuous Learning"):
        st.markdown("""
        **Adaptive Intelligence**: The AI system improves over time through:
        
        - **Outcome Feedback**: Learning from actual claim results
        - **A/B Testing Integration**: Systematic performance comparison
        - **Model Updates**: Regular retraining with new data
        - **Bias Detection**: Monitoring for and correcting biases
        - **Performance Monitoring**: Tracking accuracy and drift over time
        
        **Learning Mechanisms:**
        - Reinforcement learning from successful/unsuccessful decisions
        - Transfer learning from similar insurance domains
        - Ensemble methods for robust predictions
        - Anomaly detection for unusual cases
        """)
    
    # AI model information
    st.markdown("#### 🤖 AI Models")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Available Models:**")
        models = {
            "GPT-4": "Most advanced reasoning and analysis",
            "GPT-4 Turbo": "Faster processing with high accuracy",
            "GPT-3.5 Turbo": "Cost-effective for standard cases",
            "Claude-3 Sonnet": "Strong analytical capabilities",
            "Claude-3 Haiku": "Fast processing for simple cases"
        }
        
        for model, description in models.items():
            st.markdown(f"- **{model}**: {description}")
    
    with col2:
        st.markdown("**Model Selection Criteria:**")
        st.markdown("""
        - **Accuracy Requirements**: More complex models for higher accuracy
        - **Processing Speed**: Faster models for high-volume processing
        - **Cost Considerations**: Balance cost vs. performance needs
        - **Compliance Requirements**: Models that provide required explanations
        - **Integration Capabilities**: API compatibility and features
        """)
    
    # AI configuration
    st.markdown("#### ⚙️ AI Configuration")
    
    config_params = {
        "Temperature": "Controls randomness (0.0 = deterministic, 2.0 = very random)",
        "Max Tokens": "Maximum length of AI response (affects detail level)",
        "Top P": "Nucleus sampling parameter (affects response diversity)",
        "Prompt Template": "Structured prompts for consistent AI behavior",
        "Custom Instructions": "Domain-specific guidance for the AI model"
    }
    
    for param, description in config_params.items():
        st.markdown(f"- **{param}**: {description}")
    
    # Performance metrics
    st.markdown("#### 📊 AI Performance Metrics")
    
    performance_data = {
        "Current Accuracy": "85.2%",
        "Improvement vs Rules": "+12.3%",
        "Average Confidence": "78.9%",
        "Processing Time": "2.4s average",
        "False Positive Rate": "3.8%",
        "False Negative Rate": "4.1%"
    }
    
    col1, col2, col3 = st.columns(3)
    for i, (metric, value) in enumerate(performance_data.items()):
        with [col1, col2, col3][i % 3]:
            st.metric(metric, value)

def show_technical_tab():
    """Show technical documentation."""
    
    st.markdown("### 🔧 Technical Documentation")
    
    # Technical overview
    tech_section = st.selectbox(
        "Select Technical Topic",
        options=[
            "System Architecture",
            "API Documentation", 
            "Data Models",
            "Security & Compliance",
            "Performance & Scaling",
            "Integration Guide",
            "Troubleshooting"
        ]
    )
    
    if tech_section == "System Architecture":
        show_architecture_docs()
    elif tech_section == "API Documentation":
        show_api_docs()
    elif tech_section == "Data Models":
        show_data_models()
    elif tech_section == "Security & Compliance":
        show_security_docs()
    elif tech_section == "Performance & Scaling":
        show_performance_docs()
    elif tech_section == "Integration Guide":
        show_integration_docs()
    elif tech_section == "Troubleshooting":
        show_troubleshooting_docs()

def show_architecture_docs():
    """Show system architecture documentation."""
    
    st.markdown("#### 🏗️ System Architecture")
    
    st.markdown("**Core Components:**")
    st.markdown("""
    - **Web Interface**: Streamlit-based user interface
    - **Underwriting Engine**: Core business logic and rules processing
    - **AI Engine**: AI model integration and enhancement layer
    - **A/B Testing Framework**: Statistical testing and analysis
    - **Analytics Engine**: Data processing and visualization
    - **Configuration Manager**: System settings and rule management
    """)
    
    st.markdown("**Technology Stack:**")
    stack = {
        "Frontend": "Streamlit, Plotly, HTML/CSS/JavaScript",
        "Backend": "Python, Pydantic, AsyncIO",
        "AI/ML": "OpenAI GPT models, LangChain, LangSmith",
        "Data": "Pandas, NumPy, SciPy",
        "Testing": "pytest, A/B testing framework",
        "Monitoring": "Logging, metrics collection"
    }
    
    for component, technologies in stack.items():
        st.markdown(f"- **{component}**: {technologies}")

def show_api_docs():
    """Show API documentation."""
    
    st.markdown("#### 🔌 API Documentation")
    
    st.markdown("**Core APIs:**")
    
    apis = {
        "Evaluation API": {
            "endpoint": "/api/v1/evaluate",
            "method": "POST", 
            "description": "Submit application for underwriting evaluation"
        },
        "A/B Testing API": {
            "endpoint": "/api/v1/ab-test",
            "method": "POST",
            "description": "Create and manage A/B tests"
        },
        "Analytics API": {
            "endpoint": "/api/v1/analytics",
            "method": "GET",
            "description": "Retrieve analytics data and metrics"
        },
        "Configuration API": {
            "endpoint": "/api/v1/config",
            "method": "GET/PUT",
            "description": "Manage system configuration"
        }
    }
    
    for api_name, details in apis.items():
        with st.expander(f"🔌 {api_name}"):
            st.markdown(f"**Endpoint**: `{details['endpoint']}`")
            st.markdown(f"**Method**: `{details['method']}`")
            st.markdown(f"**Description**: {details['description']}")

def show_data_models():
    """Show data models documentation."""
    
    st.markdown("#### 📊 Data Models")
    
    st.markdown("**Core Data Structures:**")
    
    with st.expander("👤 Driver Model"):
        st.code("""
class Driver:
    first_name: str
    last_name: str
    age: int
    gender: Gender
    marital_status: MaritalStatus
    license_number: str
    license_state: str
    years_licensed: int
    license_status: LicenseStatus
        """, language="python")
    
    with st.expander("🚗 Vehicle Model"):
        st.code("""
class Vehicle:
    year: int
    make: str
    model: str
    vin: str
    category: VehicleCategory
    value: float
    usage: VehicleUsage
    annual_mileage: int
    anti_theft_device: bool
    safety_rating: int
        """, language="python")
    
    with st.expander("📋 Application Model"):
        st.code("""
class Application:
    id: UUID
    applicant: Driver
    vehicle: Vehicle
    violations: List[TrafficViolation]
    claims: List[InsuranceClaim]
    credit_score: int
    previous_insurance: bool
    coverage_lapse: bool
    submitted_at: datetime
    metadata: Dict[str, Any]
        """, language="python")

def show_security_docs():
    """Show security and compliance documentation."""
    
    st.markdown("#### 🔒 Security & Compliance")
    
    st.markdown("**Security Features:**")
    security_features = [
        "End-to-end encryption for sensitive data",
        "Role-based access control (RBAC)",
        "Audit logging for all system activities", 
        "Session management and timeout controls",
        "Input validation and sanitization",
        "Secure API authentication and authorization"
    ]
    
    for feature in security_features:
        st.markdown(f"- {feature}")
    
    st.markdown("**Compliance Standards:**")
    compliance = [
        "GDPR compliance for data protection",
        "SOX compliance for financial controls",
        "PCI DSS for payment data security",
        "HIPAA for health information protection",
        "SOC 2 Type II for security controls"
    ]
    
    for standard in compliance:
        st.markdown(f"- {standard}")

def show_performance_docs():
    """Show performance and scaling documentation."""
    
    st.markdown("#### ⚡ Performance & Scaling")
    
    st.markdown("**Performance Characteristics:**")
    performance = {
        "Average Processing Time": "2.4 seconds per application",
        "Throughput": "150+ applications per minute",
        "Concurrent Users": "100+ simultaneous users",
        "Uptime": "99.9% availability SLA",
        "Response Time": "<500ms for UI interactions"
    }
    
    for metric, value in performance.items():
        st.markdown(f"- **{metric}**: {value}")
    
    st.markdown("**Scaling Strategies:**")
    scaling = [
        "Horizontal scaling with load balancing",
        "Caching for frequently accessed data",
        "Asynchronous processing for AI calls",
        "Database connection pooling",
        "CDN for static content delivery"
    ]
    
    for strategy in scaling:
        st.markdown(f"- {strategy}")

def show_integration_docs():
    """Show integration guide."""
    
    st.markdown("#### 🔗 Integration Guide")
    
    st.markdown("**Integration Options:**")
    integrations = {
        "REST API": "Standard HTTP API for application integration",
        "Webhooks": "Real-time notifications for events",
        "File Import/Export": "Batch processing via CSV/Excel files",
        "Database Integration": "Direct database connections",
        "Message Queues": "Asynchronous processing integration"
    }
    
    for integration, description in integrations.items():
        st.markdown(f"- **{integration}**: {description}")

def show_troubleshooting_docs():
    """Show troubleshooting documentation."""
    
    st.markdown("#### 🔧 Troubleshooting")
    
    st.markdown("**Common Issues:**")
    
    issues = {
        "Slow Processing": {
            "symptoms": "Applications taking >10 seconds to process",
            "causes": "High API load, network issues, large file uploads",
            "solutions": "Check system status, retry request, contact support"
        },
        "AI Service Errors": {
            "symptoms": "AI evaluation failures or timeouts",
            "causes": "API rate limits, service outages, configuration issues",
            "solutions": "Switch to rules-only mode, check API status, verify configuration"
        },
        "Form Validation Errors": {
            "symptoms": "Unable to submit application forms",
            "causes": "Missing required fields, invalid data formats",
            "solutions": "Check required fields, verify data formats, clear form and retry"
        }
    }
    
    for issue, details in issues.items():
        with st.expander(f"❌ {issue}"):
            st.markdown(f"**Symptoms**: {details['symptoms']}")
            st.markdown(f"**Possible Causes**: {details['causes']}")
            st.markdown(f"**Solutions**: {details['solutions']}")

def show_faq_tab():
    """Show frequently asked questions."""
    
    st.markdown("### ❓ Frequently Asked Questions")
    
    # FAQ categories
    faq_category = st.selectbox(
        "Select FAQ Category",
        options=["General", "Technical", "AI Features", "Troubleshooting", "Billing & Support"]
    )
    
    if faq_category == "General":
        show_general_faq()
    elif faq_category == "Technical":
        show_technical_faq()
    elif faq_category == "AI Features":
        show_ai_faq()
    elif faq_category == "Troubleshooting":
        show_troubleshooting_faq()
    elif faq_category == "Billing & Support":
        show_billing_faq()

def show_general_faq():
    """Show general FAQ."""
    
    general_faqs = {
        "What is the Insurance Underwriting System?": """
        The Insurance Underwriting System is a comprehensive platform that automates and enhances 
        the insurance underwriting process using AI technology, rules-based logic, and advanced 
        analytics to make faster, more accurate underwriting decisions.
        """,
        
        "How accurate is the AI evaluation?": """
        Our AI-enhanced evaluation shows 85.2% accuracy with a 12.3% improvement over traditional 
        rules-only approaches. The system continuously learns and improves from new data and outcomes.
        """,
        
        "Can I customize the underwriting rules?": """
        Yes, the system provides comprehensive rule set management. You can modify thresholds, 
        weights, and criteria to match your specific underwriting guidelines and risk appetite.
        """,
        
        "How fast is the evaluation process?": """
        Most applications are processed in 2-4 seconds with AI enhancement, or under 1 second 
        with rules-only processing. Complex cases may take slightly longer but typically complete 
        within 10 seconds.
        """,
        
        "Is the system compliant with regulations?": """
        Yes, the system is designed to meet various regulatory requirements including GDPR, SOX, 
        and industry-specific compliance standards. All decisions include audit trails and explanations.
        """
    }
    
    for question, answer in general_faqs.items():
        with st.expander(f"❓ {question}"):
            st.markdown(answer)

def show_technical_faq():
    """Show technical FAQ."""
    
    technical_faqs = {
        "What browsers are supported?": """
        The system supports Chrome 90+, Firefox 88+, Safari 14+, and Edge 90+. We recommend 
        using the latest version of Chrome or Firefox for the best experience.
        """,
        
        "Can I integrate with my existing systems?": """
        Yes, the system provides REST APIs, webhooks, and file import/export capabilities for 
        integration with existing policy management, CRM, and claims systems.
        """,
        
        "How is data stored and secured?": """
        All data is encrypted at rest and in transit. The system uses industry-standard security 
        practices including role-based access control, audit logging, and secure authentication.
        """,
        
        "What AI models are available?": """
        The system supports OpenAI GPT models (GPT-4, GPT-3.5 Turbo) and Anthropic Claude models. 
        You can configure which model to use based on your accuracy and performance requirements.
        """,
        
        "Can I export data and reports?": """
        Yes, you can export data in multiple formats including JSON, CSV, Excel, and PDF. 
        Custom reports can be generated and scheduled for automatic delivery.
        """
    }
    
    for question, answer in technical_faqs.items():
        with st.expander(f"🔧 {question}"):
            st.markdown(answer)

def show_ai_faq():
    """Show AI features FAQ."""
    
    ai_faqs = {
        "How does the AI make underwriting decisions?": """
        The AI analyzes multiple data points including driver profile, vehicle information, 
        history, and external factors to assess risk. It uses advanced machine learning models 
        trained on historical underwriting data and outcomes.
        """,
        
        "Can I understand why the AI made a decision?": """
        Yes, every AI decision includes detailed reasoning, confidence scores, and factor 
        contributions. The system provides both business-friendly explanations and technical 
        details for compliance and audit purposes.
        """,
        
        "Does the AI learn from our data?": """
        The AI improves over time through feedback on actual outcomes and A/B testing results. 
        However, your proprietary data remains secure and is not shared with other organizations.
        """,
        
        "What happens if the AI service is unavailable?": """
        The system automatically falls back to rules-based processing to ensure continuous 
        operation. You can also configure the system to use alternative AI models or services.
        """,
        
        "How do I optimize AI performance for my business?": """
        Use the A/B testing framework to compare different AI configurations, adjust model 
        parameters based on your data, and regularly review performance metrics in the 
        analytics dashboard.
        """
    }
    
    for question, answer in ai_faqs.items():
        with st.expander(f"🤖 {question}"):
            st.markdown(answer)

def show_troubleshooting_faq():
    """Show troubleshooting FAQ."""
    
    troubleshooting_faqs = {
        "Why is my application processing slowly?": """
        Slow processing can be caused by high system load, network issues, or complex cases 
        requiring additional analysis. Try refreshing the page, checking your internet connection, 
        or contacting support if the issue persists.
        """,
        
        "I'm getting validation errors on my form": """
        Ensure all required fields are completed correctly. Check data formats (dates, VIN numbers, 
        email addresses) and make sure numeric fields contain valid numbers. Use the sample data 
        feature to see correct formatting.
        """,
        
        "The AI evaluation failed - what should I do?": """
        If AI evaluation fails, the system should automatically fall back to rules-based processing. 
        If this doesn't happen, try switching to "Rules Only" mode manually, or contact support 
        if the issue persists.
        """,
        
        "My A/B test isn't starting": """
        Check that your test configuration is valid, you have sufficient sample size, and all 
        required parameters are set. Ensure you have the necessary permissions to create and 
        run tests.
        """,
        
        "I can't see my analytics data": """
        Verify that you have the correct permissions to view analytics. Check the time period 
        selection and ensure there is data available for the selected date range. Clear your 
        browser cache and try again.
        """
    }
    
    for question, answer in troubleshooting_faqs.items():
        with st.expander(f"⚠️ {question}"):
            st.markdown(answer)

def show_billing_faq():
    """Show billing and support FAQ."""
    
    billing_faqs = {
        "How is usage calculated and billed?": """
        Usage is typically billed based on the number of applications processed and AI evaluations 
        performed. Contact your account manager for specific pricing details and volume discounts.
        """,
        
        "What support options are available?": """
        We offer email support, phone support during business hours, live chat, and comprehensive 
        documentation. Premium support plans include dedicated account management and priority response.
        """,
        
        "How do I request new features?": """
        Submit feature requests through your support portal or contact your account manager. 
        We regularly review requests and prioritize them based on customer needs and business value.
        """,
        
        "Can I get training for my team?": """
        Yes, we offer comprehensive training programs including online tutorials, live training 
        sessions, and custom training for large teams. Contact support to schedule training.
        """,
        
        "What if I need help with integration?": """
        Our technical support team can assist with integration planning and implementation. 
        We also offer professional services for complex integrations and custom development needs.
        """
    }
    
    for question, answer in billing_faqs.items():
        with st.expander(f"💼 {question}"):
            st.markdown(answer)
    
    # Contact information
    st.markdown("---")
    st.markdown("#### 📞 Still Need Help?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📧 Email Support**")
        st.markdown("support@underwriting-system.com")
        st.markdown("Response time: 4-8 hours")
    
    with col2:
        st.markdown("**📞 Phone Support**")
        st.markdown("1-800-UNDERWRITE")
        st.markdown("Mon-Fri 9AM-6PM EST")
    
    with col3:
        st.markdown("**💬 Live Chat**")
        st.markdown("Available in app")
        st.markdown("Mon-Fri 9AM-6PM EST")
    
    # System status
    st.markdown("---")
    st.markdown("#### 📡 System Status")
    
    status_items = {
        "System Health": "🟢 Operational",
        "AI Services": "🟢 Operational", 
        "API Gateway": "🟢 Operational",
        "Database": "🟢 Operational",
        "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    
    for item, status in status_items.items():
        st.markdown(f"**{item}**: {status}")