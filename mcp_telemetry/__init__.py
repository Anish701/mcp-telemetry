import sys
import datetime
import functools
import json
import uuid
import time
import requests

def post_to_api(log_data: dict, api_url: str) -> bool:
    """
    Posts execution log data to the specified API endpoint.
    
    Args:
        log_data (dict): The log data to post
        api_url (str): The API endpoint URL
        
    Returns:
        bool: True if successful, False otherwise
    """
    
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            api_url,
            json=log_data,
            headers=headers,
            timeout=5
        )
        
        response.raise_for_status()
        return True
        
    except requests.exceptions.RequestException as e:
        error_log = {
            "LOGGER_ERROR": f"Failed to post to API: {str(e)}",
            "API_URL": api_url,
            "TIMESTAMP": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        }
        return False

def tool_call_interceptor(func, server_name: str, api_url: str):
    """
    Decorator to intercept tool calls and capture detailed execution information.
    Outputs JSON with execution details for logging and posts to API if configured.
    
    Args:
        func: The function to wrap
        server_name (str): Name of the server
        api_url (str): API endpoint URL for logging
        
    Returns:
        Wrapped function with logging capabilities
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Generate unique execution ID
        execution_id = str(uuid.uuid4())
        
        server_host = server_name
        
        start_time = time.time()
        start_timestamp = datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        status = "SUCCESS"
        error_message = None
        result = None
        
        try:
            # Execute the actual tool function
            result = func(*args, **kwargs)
        except Exception as e:
            status = "FAILURE"
            error_message = str(e)
            raise
        finally:
            end_time = time.time()
            end_timestamp = datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            duration_ms = int((end_time - start_time) * 1000)
            
            execution_log = {
                "execution_id": execution_id,
                "tool_name": func.__name__,
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "duration_ms": duration_ms,
                "server_host": server_host,
                "status": status,
                "error_message": error_message
            }
                        
            post_to_api(execution_log, api_url)
        
        return result
    return wrapper

def enable_tool_logging(mcp_instance, server_name: str, api_url: str):
    """
    Patches the MCP instance to automatically log all tool calls.
    
    Args:
        mcp_instance: The MCP instance to patch
        server_name (str): Name of the server for logging
        api_url (str): API endpoint URL for posting logs
    """
    original_tool = mcp_instance.tool
    
    def auto_logging_tool(*decorator_args, **decorator_kwargs):
        original_decorator = original_tool(*decorator_args, **decorator_kwargs)
        
        def decorator(func):
            wrapped_func = tool_call_interceptor(func, server_name, api_url)
            return original_decorator(wrapped_func)
            
        return decorator
    
    mcp_instance.tool = auto_logging_tool

# Make the main function available at package level
__all__ = ['enable_tool_logging']
