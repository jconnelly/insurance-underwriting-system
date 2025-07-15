# Insurance Underwriting System - Claude Development Notes

## Project Overview
A comprehensive AI-enhanced insurance underwriting system built with Python, featuring a complete Streamlit web interface, A/B testing framework, and advanced analytics.

## Current Status ✅
- **Streamlit Web App**: Fully functional at http://localhost:8502
- **Core Engine**: Complete with AI integration
- **A/B Testing**: Implemented with statistical framework
- **Analytics**: Dashboard with rate limiting and metrics
- **Configuration**: JSON-based rule management

## System Architecture

### Core Components
```
src/underwriting/
├── core/
│   ├── models.py           # Pydantic data models
│   ├── engine.py           # Rules-based underwriting engine
│   ├── ai_engine.py        # AI-enhanced processing
│   └── rules.py            # Rule evaluation logic
├── ai/
│   ├── base.py             # AI models and types
│   ├── openai_service.py   # OpenAI integration
│   ├── response_parser.py  # AI response parsing
│   └── prompts/            # AI prompt templates
├── streamlit_app/
│   ├── app.py              # Main Streamlit application
│   ├── pages/              # Individual page modules
│   └── components/         # Reusable UI components
├── ab_testing/             # A/B testing framework
├── rate_limiting/          # Rate limiting system
└── config/                 # Configuration management
```

### Key Models
- `Application`: Main application data structure
- `UnderwritingDecision`: Final decision with risk scores
- `AIUnderwritingDecision`: AI-generated recommendations
- `Driver`, `Vehicle`, `Violation`, `Claim`: Core entities

## Running the System

### Start Streamlit App
```bash
streamlit run streamlit_main.py --server.port 8502
```

### CLI Usage
```bash
python -m underwriting.cli.main evaluate --file sample_data/application_001.json
```

### Requirements
All dependencies are in `requirements.txt` and are installed.

## Recent Fixes Applied ⚡

### 1. Streamlit App Issues Fixed
- **Pydantic Model Mapping**: Fixed `Application` constructor
  - `vehicle` → `vehicles=[vehicle]` (expects List)
  - `coverage_lapse` → `coverage_lapse_days` (expects int)
  - `previous_insurance` → `previous_carrier` (expects string)

- **Deprecated Methods**: Updated throughout codebase
  - `st.experimental_rerun()` → `st.rerun()`

- **AI Decision Access**: Corrected attribute chains
  - `ai_decision.decision.decision.value` → `ai_decision.decision.value`
  - `ai_decision.confidence` → `ai_decision.confidence_level.value.title()`

- **Type Safety**: Added decision type checking in display functions
- **Unicode Issues**: Replaced problematic characters (⚪ → O)

### 2. Form Component Updates
- Enhanced metadata collection with proper field types
- Added conditional previous carrier input
- Improved validation and error handling

## Configuration Files

### Environment Variables
- `OPENAI_API_KEY`: Required for AI features
- `LANGSMITH_API_KEY`: Optional for tracing

### Key Config Files
- `src/underwriting/config/ai_config.json`: AI service settings
- `src/underwriting/config/rate_limits.json`: Rate limiting rules
- `src/underwriting/config/ab_tests.json`: A/B test configurations
- `src/underwriting/config/rules/`: Rule sets (conservative, standard, liberal)

## Testing & Development

### Test Commands
```bash
# Run all tests
pytest tests/

# Test specific components
python -c "from underwriting.core.engine import UnderwritingEngine; print('✅ Engine import OK')"
```

### Debug Mode
```bash
streamlit run streamlit_main.py --logger.level=debug --server.port 8502
```

## Common Issues & Solutions

### Port Conflicts
If port 8501 is busy, use 8502:
```bash
streamlit run streamlit_main.py --server.port 8502
```

### Import Errors
Ensure you're in the project root and src is in path:
```bash
cd C:\Development\AI_Development\insurance-underwriting-system\insurance-underwriting-system
python -c "import sys; sys.path.insert(0, 'src'); from underwriting.streamlit_app.app import main"
```

### Model Validation Errors
Check field mappings in `forms.py` match model definitions in `models.py`.

## Development Notes

### Code Standards
- Use Pydantic for data validation
- Follow existing naming conventions
- Add type hints consistently
- Update both sync and async methods

### UI Guidelines
- Use st.columns() for layouts
- Add help text to form fields
- Include progress indicators for long operations
- Handle errors gracefully with st.error()

## Next Steps / TODO
- [ ] Add user authentication
- [ ] Implement policy generation
- [ ] Add audit trail logging
- [ ] Create admin dashboard
- [ ] Add more visualization charts
- [ ] Implement batch processing UI

## File Locations

### Entry Points
- `streamlit_main.py`: Streamlit app launcher
- `src/underwriting/cli/main.py`: CLI interface

### Critical Files for Troubleshooting
- `src/underwriting/streamlit_app/components/forms.py`: Form validation logic
- `src/underwriting/streamlit_app/pages/evaluation.py`: Main evaluation page
- `src/underwriting/core/models.py`: All data models
- `src/underwriting/core/ai_engine.py`: AI integration

## Environment Info
- **Python**: 3.13.3
- **Streamlit**: 1.46.0
- **Platform**: Windows (win32)
- **Project Path**: `C:\Development\AI_Development\insurance-underwriting-system\insurance-underwriting-system`

---
*Last Updated: 2025-07-14*
*Status: Fully Functional ✅*