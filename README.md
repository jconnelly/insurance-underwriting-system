# Insurance Underwriting System

A comprehensive Python-based automobile insurance underwriting system with configurable rules, A/B testing capabilities, and CLI interface for testing and demonstration.

## Features

- **Modular Architecture**: Clean separation of concerns with core models, rule evaluation, and configuration management
- **Three Rule Sets**: Conservative, Standard, and Liberal rule configurations for A/B testing
- **Comprehensive Models**: Pydantic-based data models for applications, drivers, vehicles, violations, and claims
- **Risk Scoring**: Intelligent risk assessment with detailed scoring breakdown
- **CLI Interface**: Full-featured command-line interface for testing and batch processing
- **Structured Logging**: Configurable logging with performance metrics and structured output
- **Extensive Testing**: Unit tests with >80% code coverage
- **Sample Data Generation**: Realistic sample data generator for testing

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Generate Sample Data

```bash
underwriting-cli generate --count 10 --output sample_data
```

### 2. Evaluate Single Application

```bash
underwriting-cli evaluate sample_data/application_001.json --rule-set standard
```

### 3. Batch Process Applications

```bash
underwriting-cli batch sample_data --rule-set conservative --output results.json
```

### 4. Compare Rule Sets

```bash
underwriting-cli compare sample_data/application_001.json --output comparison.json
```

## Architecture

### Core Components

```
src/underwriting/
├── core/                    # Core business logic
│   ├── models.py           # Pydantic data models
│   ├── engine.py           # Main underwriting engine
│   └── rules.py            # Rule evaluation logic
├── config/                 # Configuration management
│   ├── loader.py          # Configuration loader
│   └── rules/             # Rule configuration files
│       ├── conservative.json
│       ├── standard.json
│       └── liberal.json
├── utils/                  # Utility modules
│   ├── logging.py         # Structured logging
│   └── validation.py      # Data validation
└── cli/                   # Command-line interface
    └── main.py            # CLI implementation
```

### Data Models

The system uses Pydantic models for type safety and validation:

- **Application**: Main application container
- **Driver**: Driver information with violations and claims
- **Vehicle**: Vehicle details and specifications
- **Violation**: Traffic violations with severity levels
- **Claim**: Insurance claims with amounts and fault determination
- **UnderwritingDecision**: Final decision with risk score and reasoning

### Rule Configuration

Rules are stored in JSON files with three categories:

- **Hard Stops**: Automatic denial criteria
- **Adjudication Triggers**: Manual review requirements
- **Acceptance Criteria**: Automatic approval conditions

## CLI Usage

### Available Commands

```bash
underwriting-cli --help
```

### Command Examples

#### System Information
```bash
underwriting-cli info
```

#### Generate Sample Data
```bash
underwriting-cli generate --count 50 --output test_data --seed 42
```

#### Evaluate Application
```bash
underwriting-cli evaluate application.json --rule-set liberal --verbose
```

#### Batch Processing
```bash
underwriting-cli batch applications/ --rule-set conservative --stats
```

#### Rule Set Comparison
```bash
underwriting-cli compare application.json --output comparison_results.json
```

#### Validate Application
```bash
underwriting-cli validate application.json
```

## Rule Sets

### Conservative Rules
- **Strictest criteria** for acceptance
- **Lower thresholds** for denial and adjudication
- **Shorter lookback periods** for some violations
- **Examples**: Single DUI denial, 60-day coverage lapse limit

### Standard Rules
- **Balanced approach** between risk and acceptance
- **Moderate thresholds** for most criteria
- **Standard lookback periods** (3-5 years)
- **Examples**: Two DUI denials, 90-day coverage lapse limit

### Liberal Rules
- **Most accepting** criteria
- **Higher thresholds** for denial
- **Longer lookback periods** for some violations
- **Examples**: Three DUI denials, 180-day coverage lapse limit

## Decision Types

- **ACCEPT**: Automatic approval with calculated risk score
- **DENY**: Automatic denial due to hard stop rules
- **ADJUDICATE**: Manual review required

## Risk Scoring

The system calculates comprehensive risk scores (0-1000) with components:

- **Driver Risk**: Age, license status, experience
- **Vehicle Risk**: Category, value, safety features
- **History Risk**: Violations, claims, driving record
- **Credit Risk**: Credit score impact (optional)

Risk levels: LOW (0-300), MODERATE (301-600), HIGH (601-800), VERY_HIGH (801-1000)

## Configuration

### Logging Configuration

```python
from underwriting.utils.logging import setup_logging

setup_logging(
    level="INFO",
    log_file="logs/underwriting.log",
    enable_console=True,
    enable_file=True
)
```

### Custom Rule Sets

You can create custom rule sets by following the JSON schema in the existing rule files. Place them in the `src/underwriting/config/rules/` directory.

## API Usage

### Basic Usage

```python
from underwriting import UnderwritingEngine, Application

# Initialize engine
engine = UnderwritingEngine()

# Process application
decision = engine.process_application(application, rule_set="standard")

print(f"Decision: {decision.decision}")
print(f"Risk Score: {decision.risk_score.overall_score}")
print(f"Reason: {decision.reason}")
```

### Batch Processing

```python
from underwriting import UnderwritingEngine

engine = UnderwritingEngine()

# Process multiple applications
decisions = engine.batch_process_applications(applications, "conservative")

# Get statistics
stats = engine.get_decision_statistics(decisions)
print(f"Accept Rate: {stats['decisions']['accept']['percentage']:.1f}%")
```

### Rule Set Comparison

```python
from underwriting import UnderwritingEngine

engine = UnderwritingEngine()

# Compare all rule sets
results = engine.compare_rule_sets(application)

for rule_set, decision in results.items():
    print(f"{rule_set}: {decision.decision} (Score: {decision.risk_score.overall_score})")
```

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=src/underwriting --cov-report=html
```

### Run Specific Test Module

```bash
pytest tests/test_models.py -v
```

## Sample Data

The system includes a comprehensive sample data generator that creates realistic applications with:

- **Diverse Demographics**: Various ages, locations, and backgrounds
- **Realistic Violations**: Traffic violations with appropriate severity levels
- **Claim Histories**: Insurance claims with varying amounts and fault status
- **Vehicle Variety**: Different makes, models, and categories
- **Risk Profiles**: Low, medium, and high-risk applications

### Generate Sample Data

```python
from underwriting.data.sample_generator import SampleDataGenerator

generator = SampleDataGenerator(seed=42)

# Generate single application
application = generator.generate_application(risk_profile="high")

# Generate batch with risk distribution
applications = generator.generate_batch_applications(
    count=100,
    risk_distribution={"low": 0.3, "medium": 0.5, "high": 0.2}
)
```

## Development

### Project Structure

```
insurance-underwriting-system/
├── src/underwriting/           # Main package
├── tests/                      # Unit tests
├── data/                       # Sample data generation
├── pyproject.toml             # Project configuration
├── requirements.txt           # Dependencies
└── README.md                  # Documentation
```

### Development Setup

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black src/ tests/
isort src/ tests/
flake8 src/ tests/

# Type checking
mypy src/
```

## Performance

The system is optimized for performance with:

- **Efficient Rule Evaluation**: Short-circuit evaluation for hard stops
- **Caching**: Configuration caching for repeated evaluations
- **Batch Processing**: Optimized batch processing capabilities
- **Structured Logging**: Performance metrics and timing information

## Security

- **Input Validation**: Comprehensive validation using Pydantic
- **No Sensitive Data**: No hardcoded credentials or sensitive information
- **Secure Defaults**: Safe default configurations
- **Audit Trail**: Complete logging of all decisions and rule triggers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For support and questions:

- **Issues**: Report issues on the GitHub repository
- **Documentation**: Refer to this README and inline documentation
- **Testing**: Use the CLI interface for testing and validation

## Rate Limiting System

### Overview

The insurance underwriting system includes a comprehensive rate limiting system to control usage and ensure fair access to resources. The system provides:

- **Multiple Time Windows**: Daily, weekly, monthly, and burst limits
- **File-based Storage**: Persistent storage for rate limiting data
- **Usage Analytics**: Detailed tracking and reporting
- **Admin Override**: Emergency and testing override capabilities
- **Graceful Degradation**: Fallback mechanisms when limits are exceeded

### Rate Limiting Configuration

Rate limits are configured in `src/underwriting/config/rate_limits.json`:

```json
{
  "rate_limits": {
    "underwriting_evaluations": {
      "daily_limit": 1000,
      "weekly_limit": 5000,
      "monthly_limit": 20000,
      "burst_limit": 100,
      "burst_window_minutes": 60
    },
    "ai_evaluations": {
      "daily_limit": 500,
      "weekly_limit": 2000,
      "monthly_limit": 8000,
      "burst_limit": 50,
      "burst_window_minutes": 60
    }
  }
}
```

### Rate Limiting CLI Commands

#### Check Rate Limit Status
```bash
# Check all rate limits
python -m underwriting.cli.main rate-status --all

# Check specific identifier and operation
python -m underwriting.cli.main rate-status --identifier user123 --operation ai_evaluations
```

#### Generate Usage Analytics
```bash
# Generate analytics for last 24 hours
python -m underwriting.cli.main rate-analytics --hours 24

# Generate analytics for specific operation type
python -m underwriting.cli.main rate-analytics --operation ai_evaluations --hours 12
```

#### Generate Usage Reports
```bash
# Generate daily usage report
python -m underwriting.cli.main rate-report --type daily

# Generate weekly report for specific operation
python -m underwriting.cli.main rate-report --type weekly --operation underwriting_evaluations
```

#### Admin Override Management
```bash
# Request admin override
python -m underwriting.cli.main rate-override user123 ai_evaluations --justification "Testing" --duration 24

# Check override status
python -m underwriting.cli.main rate-override-status

# Revoke override
python -m underwriting.cli.main rate-override user123 ai_evaluations --revoke
```

#### System Maintenance
```bash
# Clean up old rate limiting data
python -m underwriting.cli.main rate-cleanup

# Reload configuration
python -m underwriting.cli.main rate-config-reload
```

### Rate Limiting Integration

The rate limiting system is automatically integrated with the AI-enhanced underwriting engine:

```python
from underwriting.core.ai_engine import AIEnhancedUnderwritingEngine

# Initialize with rate limiting enabled (default)
engine = AIEnhancedUnderwritingEngine(rate_limiting_enabled=True)

# Process application with automatic rate limiting
decision = await engine.process_application_enhanced(application, use_ai=True)
```

### Graceful Degradation

When AI evaluation rate limits are exceeded, the system can gracefully degrade:

- **Fallback to Rules**: Fall back to rules-only evaluation
- **Queue Requests**: Queue requests for later processing (optional)
- **Error Handling**: Comprehensive error handling with meaningful messages

### Analytics and Monitoring

The system provides comprehensive analytics:

- **Usage Patterns**: Hourly, daily, weekly, and monthly usage patterns
- **Top Users**: Identify high-usage identifiers
- **Success Rates**: Track success vs. blocked request rates
- **Anomaly Detection**: Detect unusual usage patterns
- **Trend Analysis**: Analyze usage trends over time

### Admin Features

- **Override System**: Emergency and testing overrides
- **Bulk Operations**: Bulk reset and override management
- **Audit Trail**: Complete logging of all admin actions
- **Usage Alerts**: Automated alerts for unusual usage

### File Storage Structure

Rate limiting data is stored in the following structure:

```
rate_limit_data/
├── usage/                    # Usage data files
├── analytics/               # Analytics reports
├── backups/                 # Automatic backups
├── overrides/               # Override data
├── admin_log.json          # Admin action log
└── index.json              # Master index
```

### Security Considerations

- **No Sensitive Data**: Rate limiting data contains no sensitive information
- **Audit Trail**: Complete audit trail of all admin actions
- **Configurable Limits**: All limits are configurable via JSON files
- **Automatic Cleanup**: Old data is automatically cleaned up

## AI Integration

### Overview

The system includes comprehensive AI integration with OpenAI GPT-4 and LangSmith tracing:

- **AI-Enhanced Evaluations**: Combine rule-based and AI decisions
- **LangSmith Tracing**: Full tracing with shareable URLs
- **Graceful Degradation**: Fallback to rules when AI is unavailable
- **Rate Limiting**: Separate rate limits for AI operations

### AI Configuration

AI features are configured in `src/underwriting/config/ai_config.json`:

```json
{
  "ai_services": {
    "openai": {
      "enabled": true,
      "api_key": "${OPENAI_API_KEY}",
      "model": "gpt-4-turbo"
    }
  },
  "langsmith": {
    "enabled": true,
    "api_key": "${LANGSMITH_API_KEY}",
    "project_name": "insurance-underwriting"
  }
}
```

### AI CLI Commands

```bash
# AI-enhanced evaluation
python -m underwriting.cli.main ai-evaluate application.json

# AI-only evaluation
python -m underwriting.cli.main ai-evaluate application.json --ai-only

# Batch AI processing
python -m underwriting.cli.main ai-batch sample_data/

# AI service health check
python -m underwriting.cli.main ai-health

# OpenAI token usage tracking
python -m underwriting.cli.main ai-token-usage --hours 24 --detailed
```

### OpenAI Token Usage Tracking

The system includes comprehensive token usage tracking with cost estimation:

```bash
# View token usage for last 24 hours
python -m underwriting.cli.main ai-token-usage --hours 24

# View detailed token usage with breakdown
python -m underwriting.cli.main ai-token-usage --hours 12 --detailed

# Export token usage data to file
python -m underwriting.cli.main ai-token-usage --hours 24 --output token_usage.json
```

**Token Usage Features:**
- **Cost Estimation**: Real-time cost calculation based on OpenAI pricing
- **Detailed Breakdown**: Input vs output token usage
- **Usage History**: Track usage over time windows
- **Rate Limiting Integration**: Automatic rate limit enforcement
- **Export Capability**: Export usage data for analysis

**Example Output:**
```
OpenAI Token Usage Summary (Last 24 hours)
Model: gpt-4-turbo
Total Requests: 15
Total Tokens: 12,450
Total Cost: $0.185750 USD
Average Tokens/Request: 830.0
Prompt Tokens: 8,200
Completion Tokens: 4,250
```

## A/B Testing Framework

### Overview

The insurance underwriting system includes a comprehensive A/B testing framework for comparing different underwriting approaches, rule sets, and AI configurations:

- **Statistical Analysis**: Chi-square, t-tests, proportion tests with scipy
- **Sample Generation**: Realistic sample data with different risk profiles
- **Test Configuration**: Predefined and custom test configurations
- **Results Management**: Comprehensive reporting and analysis
- **CLI Integration**: Full command-line interface for test management

### A/B Testing Configuration

A/B tests are configured in `src/underwriting/config/ab_tests.json` with predefined test templates:

```json
{
  "predefined_test_templates": {
    "rule_comparison": {
      "description": "Template for comparing different rule sets",
      "test_type": "rule_set_comparison",
      "recommended_metrics": ["acceptance_rate", "avg_risk_score", "decision_distribution"]
    },
    "ai_comparison": {
      "description": "Template for comparing AI vs rules-based approaches", 
      "test_type": "ai_vs_rules",
      "recommended_metrics": ["acceptance_rate", "avg_risk_score", "processing_time"]
    }
  }
}
```

### A/B Testing CLI Commands

#### Configuration Management
```bash
# List available test configurations
python -m underwriting.cli.main ab-list-configs

# Show detailed configuration
python -m underwriting.cli.main ab-show-config conservative_vs_standard

# Filter configurations by type
python -m underwriting.cli.main ab-list-configs --type rule_set_comparison
```

#### Test Management
```bash
# Create and start a new A/B test
python -m underwriting.cli.main ab-create-test conservative_vs_standard --sample-size 1000 --profile mixed

# Run A/B test by processing applications
python -m underwriting.cli.main ab-run-test conservative_vs_standard --batch-size 100

# Check test status and preliminary results
python -m underwriting.cli.main ab-test-status conservative_vs_standard --detailed

# Stop a running test
python -m underwriting.cli.main ab-stop-test conservative_vs_standard
```

#### Results and Reporting
```bash
# Generate comprehensive test report
python -m underwriting.cli.main ab-generate-report conservative_vs_standard --format html

# List all A/B tests
python -m underwriting.cli.main ab-list-tests

# Clean up old test data
python -m underwriting.cli.main ab-cleanup --days 30
```

### Predefined A/B Test Configurations

**Rule Set Comparisons:**
- `conservative_vs_standard`: Compare conservative and standard rule sets
- `standard_vs_liberal`: Compare standard and liberal rule sets

**AI vs Rules:**
- `ai_vs_standard_rules`: Compare AI-enhanced vs standard rules-only approach
- `ai_conservative_vs_liberal_rules`: Compare AI + conservative vs liberal rules

**AI Model Comparisons:**
- `gpt4_vs_gpt35_turbo`: Compare GPT-4 and GPT-3.5 Turbo models

**Performance Tests:**
- `rate_limiting_impact`: Analyze impact of rate limiting on performance
- `high_volume_performance`: Test system performance under high volume

### Statistical Analysis Features

**Supported Statistical Tests:**
- **Chi-square test**: For categorical variables (decision distribution)
- **Two-proportion test**: For acceptance rate comparisons
- **Independent t-test**: For continuous variables (risk scores)
- **Mann-Whitney U test**: For non-parametric comparisons (processing time)

**Power Analysis:**
```python
from underwriting.ab_testing.sample_generator import ABTestSampleGenerator

generator = ABTestSampleGenerator()
sample_size, applications = generator.generate_power_analysis_samples(
    effect_size=0.1,
    power=0.8
)
```

### Sample Data Profiles

**Risk Profiles for Testing:**
- `low_risk`: Mature drivers, clean records, good credit (80% low risk)
- `medium_risk`: Mixed risk factors, moderate violations (50% medium risk)
- `high_risk`: Young/old drivers, multiple violations, poor credit (60% high risk)
- `mixed`: Balanced distribution across all risk levels
- `edge_cases`: Extreme scenarios for stress testing

**Stratified Sampling:**
```bash
# Generate samples with specific strata
python -m underwriting.cli.main ab-create-test ai_vs_standard_rules --profile mixed
```

### A/B Test Reports

**Report Formats:**
- **JSON**: Machine-readable data with full statistical analysis
- **HTML**: Formatted report with tables and visualizations
- **Markdown**: Documentation-friendly format

**Report Contents:**
- Statistical significance for all metrics
- Effect sizes and confidence intervals
- Business impact analysis with projected changes
- Cost analysis (for AI-enabled tests)
- Risk analysis and decision distribution changes
- Actionable conclusions and recommendations
- Next steps based on results

### Integration with Existing Systems

**Seamless Integration:**
- Works with all rule sets (conservative, standard, liberal)
- Supports both rules-only and AI-enhanced evaluations
- Integrates with rate limiting system
- Uses existing sample data generation
- Maintains audit trails and logging

**API Usage:**
```python
from underwriting.ab_testing.framework import ABTestFramework
from underwriting.ab_testing.config import ABTestConfigManager

# Create and run A/B test
config_manager = ABTestConfigManager()
config = config_manager.get_config("conservative_vs_standard")

framework = ABTestFramework()
test = framework.create_test(config)
framework.start_test(test.test_id)

# Evaluate applications
for application in applications:
    result = await framework.evaluate_application(test.test_id, application)

# Generate report
framework.stop_test(test.test_id)
summary = framework.get_test_summary(test.test_id)
```

## Changelog

### Version 3.0.0

- **A/B Testing Framework**: Comprehensive statistical A/B testing system
- **Statistical Analysis**: Chi-square, t-tests, proportion tests with scipy
- **Sample Generation**: Advanced sample data generation with risk profiles
- **Test Configuration**: Predefined and custom test configurations
- **Results Management**: Detailed reporting with HTML, JSON, and Markdown formats
- **CLI A/B Commands**: 8 new commands for complete A/B test management
- **Power Analysis**: Sample size and statistical power calculations
- **Integration**: Seamless integration with existing AI and rate limiting systems

### Version 2.0.0

- **Rate Limiting System**: Comprehensive rate limiting with file-based storage
- **Usage Analytics**: Detailed analytics and reporting capabilities
- **Admin Override**: Emergency override system for testing and emergencies
- **AI Integration**: OpenAI GPT-4 integration with LangSmith tracing
- **Graceful Degradation**: Fallback mechanisms for high availability
- **Enhanced CLI**: New commands for rate limiting and AI management

### Version 1.0.0

- Initial release with core underwriting functionality
- Three rule sets (Conservative, Standard, Liberal)
- Comprehensive CLI interface
- Sample data generation
- Full test coverage
- Structured logging and monitoring