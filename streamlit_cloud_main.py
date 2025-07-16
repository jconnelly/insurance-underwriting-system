#!/usr/bin/env python3
"""
Streamlit Cloud optimized entry point for the Insurance Underwriting System.

This version includes error handling for missing dependencies and graceful degradation.
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Error handling for missing dependencies
def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []
    
    try:
        import openai
        AI_AVAILABLE = True
    except ImportError:
        AI_AVAILABLE = False
        missing_deps.append("openai")
    
    try:
        import langchain
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
        missing_deps.append("langchain")
    
    try:
        import scipy
        SCIPY_AVAILABLE = True
    except ImportError:
        SCIPY_AVAILABLE = False
        missing_deps.append("scipy")
    
    return {
        'ai_available': AI_AVAILABLE,
        'langchain_available': LANGCHAIN_AVAILABLE,
        'scipy_available': SCIPY_AVAILABLE,
        'missing_deps': missing_deps
    }

# Check dependencies
deps = check_dependencies()

# Set environment variables for graceful degradation
if not deps['ai_available']:
    os.environ['AI_DISABLED'] = 'true'
if not deps['langchain_available']:
    os.environ['LANGCHAIN_DISABLED'] = 'true'
if not deps['scipy_available']:
    os.environ['SCIPY_DISABLED'] = 'true'

# Show dependency status
if deps['missing_deps']:
    st.sidebar.warning(f"⚠️ Some features disabled due to missing dependencies: {', '.join(deps['missing_deps'])}")
    st.sidebar.info("💡 The rules-based underwriting system will still work perfectly!")

# Import and run the main app
try:
    from underwriting.streamlit_app.app import main
    main()
except Exception as e:
    st.error(f"❌ Error starting application: {str(e)}")
    st.info("💡 This might be due to memory limitations on Streamlit Community Cloud")
    st.markdown("""
    **Possible solutions:**
    1. Use the lightweight requirements file: `requirements-streamlit.txt`
    2. Remove heavy dependencies like langchain, scipy
    3. Run locally with full features
    """)