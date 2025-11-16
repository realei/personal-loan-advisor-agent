## Logging System Guide

The Personal Loan Advisor Agent uses a centralized logging system for better debugging, monitoring, and production operations.

---

## Features

### 1. **Colored Console Output**
- Different colors for different log levels
- Easy to spot errors and warnings
- Can be disabled for production

### 2. **File Logging**
- Optional file output with rotation
- Detailed logs with module, function, and line numbers
- Always logs DEBUG level to files (even if console is INFO)

### 3. **Structured Logging**
- Consistent format across all modules
- Timestamps, levels, module names
- Stack traces for errors

### 4. **Environment-Based Configuration**
- Configure via environment variables
- `LOG_LEVEL` - Set logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_FILE` - Optional log file path

---

## Quick Start

### Basic Usage

```python
from src.utils.logger import get_logger

# Get logger for your module
logger = get_logger(__name__)

# Log messages
logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error!")
```

### With Context Information

```python
logger.info(f"User {user_id} started session {session_id}")
logger.warning(f"High DTI ratio: {dti_ratio:.2%}")
logger.error(f"Failed to process request: {error}", exc_info=True)
```

### Exception Logging

```python
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", exc_info=True)  # Includes stack trace
```

---

## Configuration

### Environment Variables

```bash
# Set log level
export LOG_LEVEL=DEBUG

# Enable file logging
export LOG_FILE=/var/log/loan_advisor/app.log

# Run application
uv run python main.py
```

### Programmatic Configuration

```python
from src.utils.logger import setup_logger

# Custom logger with file output
logger = setup_logger(
    name="my_module",
    level="INFO",
    log_file="logs/application.log",
    console_output=True,
    colored=True
)
```

---

## Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| **DEBUG** | Detailed diagnostic info | `logger.debug(f"Evaluating with context: {context}")` |
| **INFO** | General informational messages | `logger.info("Session started successfully")` |
| **WARNING** | Warning messages | `logger.warning("DTI ratio approaching limit")` |
| **ERROR** | Error messages | `logger.error("Failed to connect to MongoDB")` |
| **CRITICAL** | Critical errors | `logger.critical("System shutdown required")` |

---

## Examples from the Codebase

### Agent Logging

```python
# src/agent/personal_loan_agent.py
logger.debug(f"Evaluation submitted: {evaluation_id}")
logger.info(f"Evaluation {evaluation_id} queued for session {self.session_id}")
```

### Evaluation Logging

```python
# src/evaluation/evaluation_manager.py
logger.info(
    f"Evaluation {evaluation_id} completed - "
    f"Overall: {'PASSED' if overall_passed else 'FAILED'}, "
    f"Scores: {scores}"
)
logger.error(f"Evaluation {evaluation_id} failed: {str(e)}", exc_info=True)
```

### Memory Logging

```python
# src/utils/memory.py
logger.info(f"Started new session: {session_id} for user: {user_id}")
logger.warning(f"Failed to resume session: {session_id} (not found)")
logger.debug(f"Submitting evaluation for session {self.session_id}")
```

---

## Production Configuration

### Recommended Setup

```python
# For production
logger = setup_logger(
    name=__name__,
    level="INFO",                      # INFO for production
    log_file="/var/log/app/loan_advisor.log",
    console_output=True,
    colored=False                       # Disable colors in production
)
```

### Log Rotation (Optional)

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "logs/app.log",
    maxBytes=10485760,  # 10MB
    backupCount=5
)
```

---

## Testing

Run logger tests:

```bash
uv run pytest tests/test_logger.py -v
```

---

## Output Examples

### Console Output (Colored)

```
INFO | personal_loan_agent | Session started for user: alice_2024
DEBUG | evaluation_manager | Starting evaluation eval_xxx_yyy
INFO | evaluation_manager | Evaluation eval_xxx_yyy completed - Overall: PASSED
ERROR | memory | Failed to connect to MongoDB: Connection refused
```

### File Output (Detailed)

```
2024-01-15 14:30:22 | INFO     | src.agent.personal_loan_agent | run:628 | Evaluation eval_xxx queued for session user123_20240115
2024-01-15 14:30:23 | DEBUG    | src.evaluation.evaluation_manager | _run_evaluation:142 | Starting evaluation eval_xxx
2024-01-15 14:30:28 | INFO     | src.evaluation.evaluation_manager | _run_evaluation:193 | Evaluation eval_xxx completed - Overall: PASSED, Scores: {...}
```

---

## Migration from print()

### Before

```python
if self.agent.debug_mode:
    print(f"[DEBUG] Evaluation submitted: {evaluation_id}")
```

### After

```python
logger.debug(f"Evaluation submitted: {evaluation_id}")
if self.agent.debug_mode:
    logger.info(f"Evaluation {evaluation_id} queued for session {self.session_id}")
```

---

## Best Practices

### 1. **Use Appropriate Levels**

```python
# ✅ Good
logger.info("User logged in")
logger.warning("Low memory")
logger.error("Database connection failed")

# ❌ Bad
logger.info("CRITICAL ERROR!")  # Should use logger.critical()
logger.debug("User logged in")  # Should use logger.info()
```

### 2. **Include Context**

```python
# ✅ Good
logger.error(f"Failed to process user {user_id}: {error}")

# ❌ Bad
logger.error("Failed to process")
```

### 3. **Use exc_info for Exceptions**

```python
# ✅ Good
try:
    process()
except Exception as e:
    logger.error("Processing failed", exc_info=True)

# ❌ Bad
except Exception as e:
    logger.error(str(e))  # Loses stack trace
```

### 4. **Avoid Logging Sensitive Data**

```python
# ✅ Good
logger.info(f"User {user_id} requested loan")

# ❌ Bad
logger.info(f"User SSN: {ssn}")  # Don't log PII
```

---

## Integration with Monitoring

### Sending Logs to External Services

```python
# Example: Sentry integration
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.ERROR
)

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[sentry_logging]
)
```

### Prometheus Metrics from Logs

```python
from prometheus_client import Counter

error_counter = Counter('loan_advisor_errors', 'Total errors')

# In your code
try:
    process()
except Exception as e:
    logger.error("Error occurred", exc_info=True)
    error_counter.inc()
```

---

## Troubleshooting

### No Logs Appearing

```python
# Check logger level
logger = get_logger(__name__)
print(f"Logger level: {logger.level}")

# Check handlers
print(f"Handlers: {logger.handlers}")
```

### Too Many Logs

```bash
# Increase log level
export LOG_LEVEL=WARNING  # Only show warnings and errors
```

### Log File Not Created

```bash
# Check directory permissions
mkdir -p logs
chmod 755 logs

# Verify LOG_FILE path
export LOG_FILE=logs/app.log
```

---

## Summary

The logging system provides:
- ✅ Centralized configuration
- ✅ Colored console output
- ✅ File logging with rotation
- ✅ Environment-based setup
- ✅ Consistent format across modules
- ✅ Production-ready

All `print()` statements in source code have been replaced with appropriate logger calls for better debugging and monitoring.
