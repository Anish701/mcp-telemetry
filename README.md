# MCP Telemetry Logger

A Python package for logging MCP (Model Context Protocol) tool calls with detailed execution information. This package provides automatic interception and logging of tool executions with API integration for centralized monitoring.

## Features

- **Automatic Tool Call Interception**: Seamlessly wraps MCP tool functions to capture execution details
- **Detailed Logging**: Captures execution ID, timestamps, duration, status, and error information
- **API Integration**: Posts logs to specified API endpoints for centralized collection
- **JSON Output**: Structured logging output for easy parsing and analysis
- **Error Handling**: Graceful error handling with fallback logging to stderr

### Development installation through pyproject.toml

Add the package to your pyproject.toml file's dependencies array as:

```json
"mcp-telemetry @ git+https://github.com/Anish701/mcp-telemetry.git"
```

Here is an example:

```toml
[tool.hatch.metadata]
allow-direct-references = true

[project]
name = "template-mcp-server"
version = "0.1.0"
description = "A template for Model Context Protocol (MCP) server development"
readme = "README.md"
keywords = ["mcp", "template", "server"]
requires-python = ">=3.12"
dependencies = [
    "fastmcp==2.10.4",
    "httpx==0.28.1",
    "pydantic==2.11.7",
    "pydantic-settings==2.10.1",
    "structlog==25.4.0",
    "python-dotenv==1.1.1",
    "fastapi==0.116.0",
    "uvicorn==0.35.0",
    "asyncpg==0.29.0",
    "psycopg2-binary==2.9.9",
    "itsdangerous==2.2.0",
    "requests-oauthlib==2.0.0",
    "mcp-telemetry @ git+https://github.com/Anish701/mcp-telemetry.git"
]
```

Rerun the installation from pyproject.toml

```bash
uv pip install -r pyproject.toml
```

If you get any errors related to tool.hatch.metadata, please add the following near the top of your pyproject.toml

```toml
[tool.hatch.metadata]
allow-direct-references = true
```

### Development installation through requirements.txt

Add the package to your requirements.txt file as:

```txt
git+https://github.com/Anish701/mcp-telemetry.git
```
Rerun the installation from requirements.txt

```bash
pip install -r requirements.txt
```

### Personal installation from GitHub

You can install this package directly from GitHub using pip:

```bash
pip install git+https://github.com/Anish701/mcp-telemetry.git
```

## Usage

### Basic Usage

The main function you'll use is `enable_tool_logging` which patches your MCP instance to automatically log all tool calls. Notice how the 
`/logs` route is included in the `api_url` parameter.

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

### Usage with class structured MCP (Template MCP Server)

Notice how `enable_tool_logging` is called *before* the MCP tools are registered.

```python
class TemplateMCPServer:
    """Main Template MCP Server implementation following tools-first architecture.

    This server provides only tools, not resources or prompts, adhering to
    the tools-first architectural pattern for MCP servers.
    """

    def __init__(self):
        """Initialize the MCP server with template tools following tools-first architecture."""
        try:
            # Initialize FastMCP server
            self.mcp = FastMCP("template")

            # Force reconfigure all loggers after FastMCP initialization to ensure structured logging
            force_reconfigure_all_loggers(settings.PYTHON_LOG_LEVEL)

            enable_tool_logging(
                mcp_instance=self.mcp, 
                server_name="Template MCP Server", 
                api_url="http://example-mcp-logs-deployment.openshiftapps.com/logs"
            )

            self._register_mcp_tools()

            logger.info("Template MCP Server initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Template MCP Server: {e}")
            raise
```

## Log Output Format

The package outputs structured JSON logs to the configured API with the following format:

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
