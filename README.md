# MCP Telemetry Logger

A Python package for logging MCP (Model Context Protocol) tool calls with detailed execution information. This package provides automatic interception and logging of tool executions with API integration for centralized monitoring.

## Features

- **Automatic Tool Call Interception**: Seamlessly wraps MCP tool functions to capture execution details
- **Detailed Logging**: Captures execution ID, timestamps, duration, status, and error information
- **API Integration**: Posts logs to specified API endpoints for centralized collection
- **JSON Output**: Structured logging output for easy parsing and analysis
- **Error Handling**: Graceful error handling with fallback logging to stderr

## Installation

### Install from GitHub

You can install this package directly from GitHub using pip:

```bash
pip install git+https://github.com/Anish701/mcp-telemetry.git
```

Make sure to add the package to your requirements.txt file as:

```txt
git+https://github.com/Anish701/mcp-telemetry.git
```

Add the package to your pyproject.toml file's dependencies array as:

```json
"mcp-telemetry @ git+https://github.com/Anish701/mcp-telemetry.git"
```

### Install from Local Clone

```bash
git clone https://github.com/Anish701/mcp-telemetry.git
cd mcp-telemetry
pip install .
```

### Development Installation

```bash
git clone https://github.com/Anish701/mcp-telemetry.git
cd mcp-telemetry
pip install -e .
```

## Usage

### Basic Usage

The main function you'll use is `enable_tool_logging` which patches your MCP instance to automatically log all tool calls:

```python
from mcp_telemetry import enable_tool_logging
from fastmcp import FastMCP

# Create your MCP instance
mcp = FastMCP("My MCP Server", host="0.0.0.0", port=8000)

# Enable automatic logging for all tools
enable_tool_logging(
    mcp_instance=mcp, 
    server_name="My MCP Server",
    api_url="http://example-mcp-logs-deployment.openshiftapps.com/logs"
)

# Now all your @mcp.tool decorated functions will be automatically logged
@mcp.tool()
def my_tool(param1: str) -> str:
    """Example tool that will be logged automatically."""
    return f"Processed: {param1}"
```

### Manual Tool Wrapping

If you prefer to manually wrap specific functions:

```python
from mcp_telemetry import tool_call_interceptor

def my_function():
    return "Hello, World!"

# Wrap the function with logging
logged_function = tool_call_interceptor(
    my_function, 
    server_name="My MCP Server", 
    api_url="https://api.example.com/logs"
)

# Call the wrapped function
result = logged_function()
```

## Log Output Format

The package outputs structured JSON logs to stdout with the following format:

```json
{
    "execution_id": "550e8400-e29b-41d4-a716-446655440000",
    "tool_name": "my_tool",
    "start_timestamp": "2025-01-15 10:30:45.123",
    "end_timestamp": "2025-01-15 10:30:45.456",
    "duration_ms": 333,
    "server_host": "My MCP Server",
    "status": "SUCCESS",
    "error_message": null
}
```

### Log Fields

- `execution_id`: Unique UUID for each tool execution
- `tool_name`: Name of the executed tool/function
- `start_timestamp`: ISO formatted start time with milliseconds
- `end_timestamp`: ISO formatted end time with milliseconds  
- `duration_ms`: Execution duration in milliseconds
- `server_host`: Server name provided during setup
- `status`: Either "SUCCESS" or "FAILURE"
- `error_message`: Error details if status is "FAILURE", null otherwise

## API Integration

Logs are automatically posted to the configured API endpoint as JSON payloads. The API should accept POST requests with `Content-Type: application/json`.

If API posting fails, error information is logged to stderr:

```json
{
    "LOGGER_ERROR": "Failed to post to API: Connection timeout",
    "API_URL": "https://api.example.com/logs",
    "TIMESTAMP": "2024-01-15 10:30:45.789"
}
```

## Error Handling

- Tool execution errors are properly propagated while still being logged
- API failures are logged to stderr but don't interrupt tool execution
- Network timeouts are set to 5 seconds for API calls
