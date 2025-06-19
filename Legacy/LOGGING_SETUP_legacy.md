# Advanced Logging System

The Spotify Recommendation System now includes a comprehensive logging framework for monitoring, debugging, and performance analysis.

## Overview

The logging system provides:
- **Multiple log levels** (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **File rotation** to manage disk space
- **Structured logging** with JSON output option
- **Performance monitoring** with timing metrics
- **User action tracking** for analytics
- **Spotify API call monitoring**
- **Error tracking** with detailed context
- **Environment-based configuration**

## Configuration

### Environment Variables

Add these to your `.env` file to customize logging:

```bash
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Enable/disable file logging (true/false)
ENABLE_FILE_LOGGING=true

# Enable/disable JSON structured logging (true/false)
ENABLE_JSON_LOGGING=false

# Enable/disable performance logging (true/false)
ENABLE_PERFORMANCE_LOGGING=true

# Maximum number of log files to keep (rotation)
MAX_LOG_FILES=30

# Maximum log file size in MB before rotation
MAX_LOG_SIZE_MB=50
```

## Log Files

The system creates several log files in the `logs/` directory:

### Main Log Files

1. **`spotify_recommender.log`** - Main application log with all events
2. **`spotify_recommender_errors.log`** - Error-only log for quick issue identification
3. **`spotify_recommender_performance.log`** - Performance metrics and timing data
4. **`spotify_recommender_structured.json`** - JSON structured logs (if enabled)

### Log Rotation

- Files automatically rotate when they reach the size limit
- Old files are numbered (.1, .2, etc.)
- Configurable retention period

## Logging Features

### 1. Performance Monitoring

Tracks timing for key operations:
- Data loading
- Model loading
- Recommendation generation
- Spotify API calls
- Search operations

```python
# Example performance log entry
2024-01-15 10:30:45 - spotify_recommender.performance - INFO - Generated 5 global_knn recommendations for song 1234 in 0.045s
```

### 2. User Action Tracking

Logs user interactions:
- Song selections
- Search queries
- Feature toggles
- Button clicks

```python
# Example user action log
2024-01-15 10:30:45 - spotify_recommender.user_actions - INFO - User action: song_selected - {'song_index': 1234, 'song_name': 'Bohemian Rhapsody'}
```

### 3. Spotify API Monitoring

Tracks all API calls:
- Endpoint URLs
- Response times
- Success/failure rates
- Error details

```python
# Example API call log
2024-01-15 10:30:45 - spotify_recommender.spotify_api - INFO - Spotify API artists/4Z8W4fKeB5YxbusRsdQVPb: SUCCESS (0.234s)
```

### 4. Structured JSON Logging

When enabled, creates machine-readable logs:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "logger": "spotify_recommender.recommendations",
  "module": "app",
  "function": "get_global_recommendations",
  "line": 456,
  "message": "Generated 5 global recommendations",
  "extra": {
    "song_idx": 1234,
    "processing_time": 0.045,
    "method": "global_knn"
  }
}
```

## Logging Dashboard

The application includes a real-time logging dashboard in the sidebar:

### Features:
- **System Status** - Current log level, handlers, and configuration
- **File Information** - Log file sizes and modification times
- **Configuration View** - Environment variables and settings
- **Test Actions** - Generate test log entries

### Access:
1. Open the Streamlit app
2. Look for "📊 Logging Dashboard" in the sidebar
3. Expand to view logging information

## Usage Examples

### Viewing Logs

```bash
# View latest application logs
tail -f logs/spotify_recommender.log

# View only errors
tail -f logs/spotify_recommender_errors.log

# View performance metrics
tail -f logs/spotify_recommender_performance.log

# Search for specific events
grep "recommendation" logs/spotify_recommender.log

# View JSON logs (if enabled)
tail -f logs/spotify_recommender_structured.json | jq '.'
```

### Log Analysis

```bash
# Count recommendation types
grep "recommendation" logs/spotify_recommender.log | cut -d' ' -f8 | sort | uniq -c

# Average recommendation generation time
grep "Generated.*recommendations" logs/spotify_recommender_performance.log | grep -o "[0-9]\+\.[0-9]\+s" | sed 's/s//' | awk '{sum+=$1; count++} END {print "Average:", sum/count, "seconds"}'

# Most searched songs
grep "User search:" logs/spotify_recommender.log | cut -d':' -f4 | sort | uniq -c | sort -nr | head -10

# API success rate
grep "Spotify API" logs/spotify_recommender.log | grep -c "SUCCESS\|FAILED"
```

### Troubleshooting

#### Common Issues:

1. **Logs directory not created**
   ```bash
   mkdir -p logs
   chmod 755 logs
   ```

2. **Permission errors**
   ```bash
   chown -R $USER:$USER logs/
   ```

3. **Large log files**
   - Reduce `MAX_LOG_SIZE_MB` in environment
   - Decrease `MAX_LOG_FILES` retention
   - Set `LOG_LEVEL=WARNING` to reduce verbosity

4. **Missing performance logs**
   - Ensure `ENABLE_PERFORMANCE_LOGGING=true`
   - Check log level is INFO or DEBUG

## Development

### Adding Custom Logging

```python
# Import logging functions
from logging_config import get_logger, log_user_action, log_performance

# Get a logger for your module
logger = get_logger("my_module")

# Log regular events
logger.info("Processing user request")
logger.debug("Detailed processing info")
logger.warning("Something unusual happened")
logger.error("An error occurred")

# Log user actions
log_user_action("button_clicked", {"button": "recommend", "user_id": "123"})

# Log performance metrics
import time
start = time.time()
# ... do work ...
duration = time.time() - start
log_performance("my_operation", duration, {"items_processed": 100})
```

### Custom Log Formatters

The system supports custom formatters for different output formats:

```python
# JSON structured logging
from logging_config import StructuredFormatter

# Performance-aware logging
from logging_config import PerformanceFilter
```

## Monitoring and Alerts

### Log Monitoring

Set up monitoring for:
- Error rates exceeding threshold
- Performance degradation
- API failure rates
- Disk space usage

### Example Monitoring Script

```bash
#!/bin/bash
# Simple error rate monitor
ERROR_COUNT=$(grep -c "ERROR\|CRITICAL" logs/spotify_recommender.log)
if [ $ERROR_COUNT -gt 10 ]; then
    echo "High error rate detected: $ERROR_COUNT errors"
    # Send alert
fi
```

## Best Practices

1. **Log Levels**
   - DEBUG: Detailed diagnostic information
   - INFO: General application flow
   - WARNING: Unexpected but recoverable events
   - ERROR: Serious problems that need attention
   - CRITICAL: Very serious errors that may abort

2. **Sensitive Data**
   - Never log passwords or API keys
   - Truncate long URLs or data
   - Use hashing for user identifiers

3. **Performance**
   - Use appropriate log levels in production
   - Consider async logging for high-volume applications
   - Monitor disk space usage

4. **Structured Data**
   - Use JSON logging for machine analysis
   - Include relevant context in log messages
   - Use consistent field names

## Security Considerations

- Log files may contain sensitive information
- Secure log file access with proper permissions
- Consider log encryption for sensitive environments
- Implement log retention policies
- Sanitize user input before logging

## Future Enhancements

Planned improvements:
- Real-time log streaming dashboard
- Automatic anomaly detection
- Integration with external monitoring systems
- Advanced log analysis and visualization
- Automated performance regression detection 