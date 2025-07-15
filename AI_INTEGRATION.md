# AI Integration Guide

## Overview

The Insurance Underwriting System now includes comprehensive AI integration capabilities that enhance traditional rule-based underwriting with artificial intelligence. This integration provides more sophisticated risk assessment, decision reasoning, and flexible evaluation strategies.

## Features

### 🤖 AI Service Abstraction Layer
- **Multi-Provider Support**: Designed to support OpenAI, Google AI, Claude, and Azure OpenAI
- **Pluggable Architecture**: Easy to add new AI providers
- **Robust Error Handling**: Comprehensive fallback mechanisms
- **Rate Limiting**: Built-in rate limiting and request management

### 📊 LangSmith Tracing Integration
- **Automatic Tracing**: All AI evaluations are automatically traced with LangSmith
- **Shareable Run URLs**: Each evaluation generates a unique, shareable URL for analysis
- **A/B Testing Traces**: Special tracing for rule set comparisons and A/B testing
- **Batch Processing Traces**: Comprehensive tracing for batch evaluations
- **Run ID Tracking**: Access to unique run IDs for programmatic access

### 🎯 Prompt Engineering System
- **Rule Set Specific Prompts**: Tailored prompts for Conservative, Standard, and Liberal rule sets
- **Context-Aware Templates**: Dynamic prompt generation based on application data
- **Consistent Response Format**: Structured JSON responses with validation

### 🔄 Decision Combination Strategies
- **Rules Only**: Traditional rule-based decisions only
- **AI Only**: Pure AI-driven decisions
- **Weighted Average**: Combine rule and AI decisions with configurable weights
- **AI Override**: Allow high-confidence AI decisions to override rules
- **Consensus Required**: Require agreement between rules and AI

### 📊 Enhanced Analytics
- **AI Coverage Metrics**: Track AI evaluation availability
- **Agreement Analysis**: Measure rule-AI consensus rates
- **Confidence Tracking**: Monitor AI decision confidence levels
- **Performance Insights**: Detailed decision combination analytics

## Quick Start

### 1. Configuration

Set up your AI configuration in `src/underwriting/config/ai_config.json`:

```json
{
  "ai_services": {
    "openai": {
      "enabled": true,
      "api_key": "${OPENAI_API_KEY}",
      "model": "gpt-4-turbo",
      "max_tokens": 2000,
      "temperature": 0.1
    }
  },
  "decision_combination": {
    "strategy": "weighted_average",
    "ai_weight": 0.3,
    "rules_weight": 0.7
  }
}
```

### 2. Environment Variables

Set your API keys for AI services and LangSmith:
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
export LANGSMITH_API_KEY="your-langsmith-api-key-here"
export LANGSMITH_ENDPOINT="https://api.smith.langchain.com"  # Optional
```

### 3. Basic Usage

#### CLI Commands

**AI-Enhanced Single Evaluation:**
```bash
python -m src.underwriting.cli.main ai-evaluate sample_data/application_001.json --rule-set standard --verbose
```

**AI-Enhanced Batch Processing:**
```bash
python -m src.underwriting.cli.main ai-batch sample_data/ --rule-set conservative --use-ai
```

**Rule Set Comparison with AI:**
```bash
python -m src.underwriting.cli.main ai-compare sample_data/application_001.json --include-ai
```

**AI Service Health Check:**
```bash
python -m src.underwriting.cli.main ai-health
```

#### Python API

```python
from src.underwriting import AIEnhancedUnderwritingEngine, Application

# Initialize AI-enhanced engine
engine = AIEnhancedUnderwritingEngine()

# Process application with AI enhancement
enhanced_decision = engine.process_application_enhanced_sync(
    application, 
    rule_set="standard", 
    use_ai=True
)

# Access results
print(f"Final Decision: {enhanced_decision.final_decision.decision}")
print(f"Rule Decision: {enhanced_decision.rule_decision.decision}")
if enhanced_decision.ai_decision:
    print(f"AI Decision: {enhanced_decision.ai_decision.decision}")
    print(f"AI Confidence: {enhanced_decision.ai_decision.confidence_level}")

# Access LangSmith tracing information
if enhanced_decision.langsmith_run_id:
    print(f"LangSmith Run ID: {enhanced_decision.langsmith_run_id}")
    print(f"LangSmith Trace URL: {enhanced_decision.langsmith_run_url}")
```

## LangSmith Integration

### Automatic Tracing

All AI evaluations are automatically traced in LangSmith when enabled:

- **Single Evaluations**: Each `ai-evaluate` command creates a trace
- **Batch Processing**: Each `ai-batch` command creates a batch trace
- **A/B Testing**: Each `ai-compare` command creates comparison traces

### Viewing Traces

Traces are displayed in the CLI output and saved to result files:

```bash
# Single evaluation with trace URL
python -m src.underwriting.cli.main ai-evaluate app.json --verbose

# Output includes:
# LangSmith Trace:
#   Run ID: 550e8400-e29b-41d4-a716-446655440000
#   Trace URL: https://smith.langchain.com/public/550e8400-e29b-41d4-a716-446655440000/r
```

### Programmatic Access

Access run IDs and URLs in your code:

```python
from src.underwriting import AIEnhancedUnderwritingEngine

engine = AIEnhancedUnderwritingEngine()
enhanced_decision = await engine.process_application_enhanced(application)

# Get tracing information
run_id = enhanced_decision.langsmith_run_id
trace_url = enhanced_decision.langsmith_run_url

# Share trace URL with stakeholders
print(f"View detailed AI evaluation: {trace_url}")
```

### Configuration

Configure LangSmith in `ai_config.json`:

```json
{
  "langsmith": {
    "enabled": true,
    "api_key": "${LANGSMITH_API_KEY}",
    "project_name": "insurance-underwriting",
    "tracing": {
      "trace_evaluations": true,
      "trace_batch_processing": true,
      "trace_ab_testing": true
    }
  }
}
```

## Architecture

### AI Service Interface

All AI providers implement the `AIServiceInterface`:

```python
class AIServiceInterface(ABC):
    async def evaluate_application(self, application: Application, rule_set: str) -> AIUnderwritingDecision
    async def batch_evaluate_applications(self, applications: List[Application]) -> List[AIUnderwritingDecision]
    def validate_configuration(self) -> bool
    def health_check(self) -> Dict[str, Any]
```

### Decision Flow

1. **Rule Evaluation**: Traditional rule-based underwriting
2. **AI Evaluation**: Parallel AI assessment (if enabled)
3. **Decision Combination**: Merge decisions using configured strategy
4. **Result Generation**: Create enhanced decision with metadata

### Prompt Templates

Each rule set has specialized prompts:

- **Conservative**: Emphasizes loss prevention and strict criteria
- **Standard**: Balances risk and profitability
- **Liberal**: Focuses on market expansion and growth

## Configuration

### AI Services Configuration

```json
{
  "ai_services": {
    "openai": {
      "enabled": true,
      "api_key": "${OPENAI_API_KEY}",
      "model": "gpt-4-turbo",
      "max_tokens": 2000,
      "temperature": 0.1,
      "timeout": 30,
      "retry_attempts": 3,
      "rate_limit": {
        "requests_per_minute": 60,
        "tokens_per_minute": 150000
      }
    }
  }
}
```

### Decision Combination Settings

```json
{
  "decision_combination": {
    "strategy": "weighted_average",
    "ai_weight": 0.3,
    "rules_weight": 0.7,
    "confidence_threshold": 0.7,
    "fallback_to_rules": true,
    "override_rules": {
      "high_confidence_threshold": 0.9,
      "allow_ai_override": false
    }
  }
}
```

### Performance Tuning

```json
{
  "performance": {
    "cache_responses": true,
    "cache_duration_minutes": 60,
    "parallel_processing": true,
    "max_concurrent_requests": 5
  }
}
```

## Error Handling & Fallbacks

### Automatic Fallbacks
- **AI Service Unavailable**: Falls back to rule-based decisions
- **API Rate Limits**: Implements exponential backoff with retries
- **Invalid Responses**: Uses response parser with fallback extraction
- **Configuration Errors**: Graceful degradation to rules-only mode

### Error Types
- `AIServiceError`: Base AI service error
- `AIServiceUnavailableError`: Service connectivity issues
- `AIRateLimitError`: Rate limit exceeded
- `AIInvalidResponseError`: Response parsing failures
- `AIConfigurationError`: Configuration problems

## Testing

### Running AI Tests

```bash
# Run all AI component tests
python -m pytest tests/test_ai_components.py -v

# Test specific components
python -m pytest tests/test_ai_components.py::TestAIResponseParser -v
python -m pytest tests/test_ai_components.py::TestPromptTemplates -v
```

### Mock Testing

Tests include comprehensive mocking for:
- OpenAI API responses
- Configuration loading
- Error scenarios
- Rate limiting behavior

## Monitoring & Analytics

### Key Metrics

- **AI Coverage**: Percentage of applications evaluated by AI
- **Agreement Rate**: Rule-AI decision consensus
- **Confidence Distribution**: AI confidence level patterns
- **Response Times**: AI evaluation performance
- **Error Rates**: Service reliability metrics

### CLI Analytics

```bash
# Enhanced statistics with AI metrics
python -m src.underwriting.cli.main ai-batch sample_data/ --stats
```

Output includes:
- Traditional underwriting statistics
- AI coverage percentage
- Rule-AI agreement rates
- Decision combination strategy usage

## Best Practices

### 1. Configuration Management
- Use environment variables for sensitive data
- Test configurations in non-production environments
- Monitor API usage and costs

### 2. Error Handling
- Always configure fallback to rules-only mode
- Implement proper logging for AI failures
- Set appropriate timeout values

### 3. Performance Optimization
- Use batch processing for multiple applications
- Configure appropriate rate limits
- Enable response caching where applicable

### 4. Security
- Protect API keys and credentials
- Enable request/response logging for auditing
- Implement proper access controls

## Troubleshooting

### Common Issues

**AI Service Not Available**
```
Check: API key configuration, network connectivity, service health
Solution: Use ai-health command to diagnose issues
```

**Rate Limit Exceeded**
```
Check: Request frequency, batch sizes
Solution: Adjust rate_limit settings in configuration
```

**Invalid AI Responses**
```
Check: Model configuration, prompt templates
Solution: Review response_parser logs for details
```

**High Error Rates**
```
Check: Service status, configuration validity
Solution: Enable fallback_to_rules for reliability
```

### Debugging Commands

```bash
# Check AI service health
python -m src.underwriting.cli.main ai-health

# Test with rules-only mode
python -m src.underwriting.cli.main ai-evaluate app.json --rules-only

# Verbose AI evaluation
python -m src.underwriting.cli.main ai-evaluate app.json --verbose --ai-only
```

## Future Enhancements

### Planned Features
- **Google AI Integration**: Support for Gemini models
- **Claude Integration**: Anthropic Claude API support
- **Custom Model Training**: Fine-tuning capabilities
- **Advanced Analytics**: ML-powered insights
- **A/B Testing Framework**: Systematic strategy comparison

### Extension Points
- Additional AI providers via `AIServiceInterface`
- Custom decision combination strategies
- Specialized prompt templates
- Enhanced response parsing logic

## Support

For AI integration support:
- Review logs in the underwriting system
- Use `ai-health` command for diagnostics
- Check configuration against this guide
- Monitor API usage and limits

The AI integration is designed to enhance, not replace, traditional underwriting wisdom. It provides powerful tools for risk assessment while maintaining the reliability and transparency of rule-based systems.