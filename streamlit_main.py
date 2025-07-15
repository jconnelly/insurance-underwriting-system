#!/usr/bin/env python3
"""
Streamlit entry point for the Insurance Underwriting System.

Run this file to start the Streamlit web application:
    streamlit run streamlit_main.py
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and run the main app
if __name__ == "__main__":
    from underwriting.streamlit_app.app import main
    main()