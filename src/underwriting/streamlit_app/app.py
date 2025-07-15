"""
Main Streamlit application for the Insurance Underwriting System.

This application provides a comprehensive web interface for insurance underwriting,
including application evaluation, A/B testing, analytics, and configuration management.
"""

import streamlit as st
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from underwriting import __version__

# Page configuration
st.set_page_config(
    page_title="Insurance Underwriting System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/anthropics/claude-code',
        'Report a bug': 'https://github.com/anthropics/claude-code/issues',
        'About': f"Insurance Underwriting System v{__version__}"
    }
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f8ff 0%, #e6f3ff 100%);
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    
    .sidebar-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 3px solid #17a2b8;
    }
    
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    
    .status-danger {
        color: #dc3545;
        font-weight: bold;
    }
    
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        text-align: center;
    }
    
    .feature-card h3 {
        margin-bottom: 0.5rem;
        color: white;
    }
    
    .nav-button {
        width: 100%;
        margin: 0.25rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function."""
    
    # Header
    st.markdown(
        '<div class="main-header">🏢 Insurance Underwriting System</div>',
        unsafe_allow_html=True
    )
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### 🧭 Navigation")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Navigation pages
        pages = {
            "🏠 Home": "home",
            "📝 Application Evaluation": "evaluation",
            "🧪 A/B Testing": "ab_testing", 
            "📊 Analytics Dashboard": "analytics",
            "⚙️ Configuration": "config",
            "📚 Help & Documentation": "help"
        }
        
        selected_page = st.selectbox(
            "Select a page:",
            list(pages.keys()),
            index=0,
            key="page_selector"
        )
        
        st.markdown("---")
        
        # System status
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### 📡 System Status")
        
        # Mock system status (in real app, this would check actual services)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<span class="status-success">✅ AI Service</span>', unsafe_allow_html=True)
            st.markdown('<span class="status-success">✅ Database</span>', unsafe_allow_html=True)
        with col2:
            st.markdown('<span class="status-success">✅ API Gateway</span>', unsafe_allow_html=True)
            st.markdown('<span class="status-warning">⚠️ Rate Limiting</span>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick stats
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### 📈 Quick Stats")
        st.metric("Applications Today", "247", "+15%")
        st.metric("AI Evaluations", "156", "+8%")
        st.metric("Active A/B Tests", "3", "→")
        st.markdown('</div>', unsafe_allow_html=True)

    # Main content area
    page_name = pages[selected_page]
    
    if page_name == "home":
        show_home_page()
    elif page_name == "evaluation":
        show_evaluation_page()
    elif page_name == "ab_testing":
        show_ab_testing_page()
    elif page_name == "analytics":
        show_analytics_page()
    elif page_name == "config":
        show_config_page()
    elif page_name == "help":
        show_help_page()

def show_home_page():
    """Display the home page."""
    
    # Welcome section
    st.markdown("## Welcome to the Insurance Underwriting System")
    st.markdown("""
    This comprehensive platform provides AI-enhanced insurance underwriting capabilities
    with advanced analytics, A/B testing, and configuration management.
    """)
    
    # Feature overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📝 Smart Evaluation</h3>
            <p>AI-powered application evaluation with rules-based fallback</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🧪 A/B Testing</h3>
            <p>Statistical testing framework for optimization</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Analytics</h3>
            <p>Comprehensive dashboards and reporting</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent activity
    st.markdown("---")
    st.markdown("## 🕒 Recent Activity")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Latest Evaluations")
        
        # Mock recent evaluations
        recent_data = [
            {"ID": "APP-001", "Decision": "ACCEPT", "Risk Score": 85, "Time": "2 min ago"},
            {"ID": "APP-002", "Decision": "ADJUDICATE", "Risk Score": 65, "Time": "5 min ago"},
            {"ID": "APP-003", "Decision": "DENY", "Risk Score": 25, "Time": "8 min ago"},
            {"ID": "APP-004", "Decision": "ACCEPT", "Risk Score": 92, "Time": "12 min ago"},
        ]
        
        for item in recent_data:
            decision_color = {
                "ACCEPT": "🟢",
                "DENY": "🔴", 
                "ADJUDICATE": "🟡"
            }[item["Decision"]]
            
            st.markdown(f"""
            <div class="metric-card">
                <strong>{item['ID']}</strong> {decision_color} {item['Decision']}<br>
                Risk Score: {item['Risk Score']} | {item['Time']}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### A/B Test Updates")
        
        # Mock A/B test updates
        ab_tests = [
            {"Name": "Conservative vs Standard", "Status": "Running", "Progress": 75},
            {"Name": "AI vs Rules Only", "Status": "Completed", "Progress": 100},
            {"Name": "GPT-4 vs GPT-3.5", "Status": "Planning", "Progress": 15},
        ]
        
        for test in ab_tests:
            status_color = {
                "Running": "🟢",
                "Completed": "✅",
                "Planning": "🟡"
            }[test["Status"]]
            
            st.markdown(f"""
            <div class="metric-card">
                <strong>{test['Name']}</strong><br>
                {status_color} {test['Status']} - {test['Progress']}% complete
            </div>
            """, unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("---")
    st.markdown("## ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📝 New Evaluation", key="quick_eval", help="Start a new application evaluation"):
            st.session_state.page_selector = "📝 Application Evaluation"
            st.rerun()
    
    with col2:
        if st.button("🧪 Create A/B Test", key="quick_ab", help="Set up a new A/B test"):
            st.session_state.page_selector = "🧪 A/B Testing"
            st.rerun()
    
    with col3:
        if st.button("📊 View Analytics", key="quick_analytics", help="Open analytics dashboard"):
            st.session_state.page_selector = "📊 Analytics Dashboard"
            st.rerun()
    
    with col4:
        if st.button("⚙️ Settings", key="quick_config", help="Manage system configuration"):
            st.session_state.page_selector = "⚙️ Configuration"
            st.rerun()

def show_evaluation_page():
    """Display the evaluation page."""
    from underwriting.streamlit_app.pages.evaluation import show_evaluation_page as show_eval
    show_eval()

def show_ab_testing_page():
    """Display the A/B testing page."""
    from underwriting.streamlit_app.pages.ab_testing import show_ab_testing_page as show_ab
    show_ab()

def show_analytics_page():
    """Display the analytics dashboard page."""
    from underwriting.streamlit_app.pages.analytics import show_analytics_page as show_analytics
    show_analytics()

def show_config_page():
    """Display the configuration management page."""
    from underwriting.streamlit_app.pages.config import show_config_page as show_config
    show_config()

def show_help_page():
    """Placeholder for help page."""
    st.markdown("## 📚 Help & Documentation")
    st.info("📍 You are on the Help page. Documentation will be implemented next.")

if __name__ == "__main__":
    main()