# Workflow Logger

A Python package for logging errors and events to Axiom with built-in data redaction and monitoring capabilities.

## Features

- 🔐 **Secure logging** with automatic field redaction
- 📊 **Axiom integration** for centralized logging and monitoring  
- ⚡ **Error deduplication** to prevent spam from repeated errors
- 🛡️ **Allowlist-based redaction** for sensitive data protection
- 📝 **Multiple log levels** (error, warning, info)

## Installation

Install from PyPI:

```bash
pip install workflow-logger
```

Or install from source:

```bash
git clone https://github.com/GO-SQUAD-AI/workflow-logger.git
cd workflow-logger
pip install .
```

## Quick Start

```python
from src import AxiomLogger

# Initialize the logger
logger = AxiomLogger(
    service_name="my-service",
    allowed_fields=["id", "name"]  # Only these fields will be shown, others redacted
)

# Log an error
try:
    # Your code here
    raise ValueError("Something went wrong")
except Exception as e:
    logger.error(
        error=e,
        context={"function": "process_data", "user_id": "123"},
        event_data={"sensitive_data": "hidden", "id": "visible"}
    )

# Log info messages
logger.info(
    message="Processing started",
    context={"stage": "initialization"},
    event_data={"batch_size": 100}
)
```

## Configuration

Set up your environment variables:

```bash
export AXIOM_TOKEN="your-axiom-token"
export AXIOM_DATASET="your-dataset-name"  # Optional, defaults to "local"
```

## Security Features

### Data Redaction

The logger uses an allowlist approach for data security:

```python
# Only "id" and "email" will be visible
logger = AxiomLogger(
    service_name="my-service", 
    allowed_fields=["id", "email"]
)

data = {
    "id": "123",
    "email": "user@example.com", 
    "password": "secret123",
    "credit_card": "4111-1111-1111-1111"
}

# Result: {"id": "123", "email": "user@example.com", "password": "[REDACTED]", "credit_card": "[REDACTED]"}
```

### Error Deduplication

The logger automatically prevents spam by excluding repeated errors from Slack notifications when they occur within 5 seconds of each other.

## API Reference

### AxiomLogger

#### `__init__(service_name: str, allowed_fields: Optional[List[str]] = None)`

Initialize the Axiom logger.

- **service_name**: Name of your service for log identification
- **allowed_fields**: List of field names that won't be redacted (defaults to `["id"]`)

#### `error(error: Exception, context: Optional[Dict], event_data: Optional[Dict]) -> bool`

Log an error with context and event data.

#### `info(message: str, context: Optional[Dict], event_data: Optional[Dict]) -> bool`

Log an informational message.

#### `warning(message: str, context: Optional[Dict], event_data: Optional[Dict]) -> bool`

Log a warning message.

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Format code:

```bash
black .
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- 🐛 [Report bugs](https://github.com/GO-SQUAD-AI/workflow-logger/issues)
- 💡 [Request features](https://github.com/GO-SQUAD-AI/workflow-logger/issues)
- 📚 [Documentation](https://github.com/GO-SQUAD-AI/workflow-logger)