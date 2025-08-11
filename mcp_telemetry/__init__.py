import datetime
import functools
import uuid
import time
import threading
import requests

def post_to_api_async(log_data: dict, api_url: str) -> None:
    """
    Posts execution log data asynchronously to the specified API endpoint using a background thread.
    This is a fire-and-forget operation that won't block tool execution.
    
    Args:
        log_data (dict): The log data to post
        api_url (str): The API endpoint URL
    """
    
    def _post():
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
            
        except requests.exceptions.RequestException as e:
            print(f"MCP Telemetry: Failed to post to API: {str(e)}")
            pass
    
    # Start background thread for API posting
    thread = threading.Thread(target=_post, daemon=True)
    thread.start()

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
        
        output_tokens = 0
        
        try:
            # Execute the actual tool function
            result = func(*args, **kwargs)
            
            # Calculate token count (1 token per 4 characters for Claude)
            if result is not None:
                if isinstance(result, str):
                    output_tokens = len(result) // 4
                else:
                    output_tokens = len(str(result)) // 4
                    
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
                "error_message": error_message,
                "output_tokens": output_tokens
            }
                        
            post_to_api_async(execution_log, api_url)
        
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