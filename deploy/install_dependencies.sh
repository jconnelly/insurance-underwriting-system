#!/bin/bash

# =============================================================================
# Install Dependencies Script
# =============================================================================
# This script installs all required dependencies for the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

APP_DIR="/opt/insurance-underwriting-system"

echo -e "${GREEN}=== Installing Application Dependencies ===${NC}"

# Change to application directory
cd $APP_DIR

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install wheel for faster builds
pip install wheel

# Install dependencies based on availability
echo -e "${YELLOW}Installing Python dependencies...${NC}"

# Try full requirements first
if pip install -r requirements.txt; then
    echo -e "${GREEN}Full requirements installed successfully!${NC}"
    echo "All features including AI and LangSmith tracing are available"
else
    echo -e "${YELLOW}Full requirements failed, trying streamlit requirements...${NC}"
    if pip install -r requirements-streamlit.txt; then
        echo -e "${GREEN}Streamlit requirements installed successfully!${NC}"
        echo "Core features available, AI features may be limited"
    else
        echo -e "${YELLOW}Streamlit requirements failed, trying minimal requirements...${NC}"
        if pip install -r requirements-minimal.txt; then
            echo -e "${GREEN}Minimal requirements installed successfully!${NC}"
            echo "Basic features available, AI features disabled"
        else
            echo -e "${RED}Failed to install even minimal requirements!${NC}"
            exit 1
        fi
    fi
fi

# Verify installation
echo -e "${YELLOW}Verifying installation...${NC}"

# Check core packages
python -c "import streamlit; print(f'Streamlit: {streamlit.__version__}')"
python -c "import pandas; print(f'Pandas: {pandas.__version__}')"
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python -c "import pydantic; print(f'Pydantic: {pydantic.__version__}')"

# Check optional packages
echo -e "\n${YELLOW}Checking optional packages...${NC}"

# Check OpenAI
if python -c "import openai; print(f'OpenAI: {openai.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✓ OpenAI package available${NC}"
else
    echo -e "${YELLOW}⚠ OpenAI package not available${NC}"
fi

# Check LangChain
if python -c "import langchain; print(f'LangChain: {langchain.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✓ LangChain package available${NC}"
else
    echo -e "${YELLOW}⚠ LangChain package not available${NC}"
fi

# Check LangSmith
if python -c "import langsmith; print(f'LangSmith: {langsmith.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✓ LangSmith package available${NC}"
else
    echo -e "${YELLOW}⚠ LangSmith package not available${NC}"
fi

# Check SciPy
if python -c "import scipy; print(f'SciPy: {scipy.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✓ SciPy package available${NC}"
else
    echo -e "${YELLOW}⚠ SciPy package not available${NC}"
fi

# Check Plotly
if python -c "import plotly; print(f'Plotly: {plotly.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✓ Plotly package available${NC}"
else
    echo -e "${YELLOW}⚠ Plotly package not available${NC}"
fi

# Test application import
echo -e "\n${YELLOW}Testing application import...${NC}"
if python -c "import sys; sys.path.insert(0, 'src'); from underwriting.streamlit_app.app import main; print('✓ Application imports successfully')"; then
    echo -e "${GREEN}✓ Application can be imported${NC}"
else
    echo -e "${RED}✗ Application import failed${NC}"
    exit 1
fi

# Show disk usage
echo -e "\n${YELLOW}Disk usage:${NC}"
du -sh venv/
df -h /

echo -e "\n${GREEN}=== Dependencies Installation Complete ===${NC}"
echo ""
echo "Installed packages:"
pip list | grep -E "(streamlit|pandas|numpy|pydantic|openai|langchain|langsmith|scipy|plotly)"
echo ""
echo "Next steps:"
echo "1. Configure environment variables in .env file"
echo "2. Start the application with: ./deploy/start_app.sh"