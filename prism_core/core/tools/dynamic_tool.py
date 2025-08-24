import time
import json
import requests
from typing import Any, Dict, Optional
from .base import BaseTool
from .schemas import ToolRequest, ToolResponse


class DynamicTool(BaseTool):
    """
    A dynamically created tool that can be registered by clients.
    
    This tool can handle different types of operations based on the tool_type:
    - 'api': Makes HTTP API calls
    - 'calculation': Performs calculations using eval (with safety checks)
    - 'custom': Custom logic defined by the client
    """
    
    def __init__(self, name: str, description: str, parameters_schema: Dict[str, Any], 
                 tool_type: str, config: Dict[str, Any] = None):
        """
        Initialize a dynamic tool.
        
        Args:
            name: Tool name
            description: Tool description
            parameters_schema: JSON schema for parameters
            tool_type: Type of tool ('api', 'calculation', 'custom')
            config: Additional configuration for the tool
        """
        super().__init__(name, description, parameters_schema)
        self.tool_type = tool_type
        self.config = config or {}
    
    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute the dynamic tool based on its type."""
        start_time = time.time()
        
        try:
            if not self.validate_parameters(request.parameters):
                return ToolResponse(
                    success=False,
                    error_message="Invalid parameters provided"
                )
            
            if self.tool_type == "api":
                result = await self._execute_api_call(request.parameters)
            elif self.tool_type == "calculation":
                result = await self._execute_calculation(request.parameters)
            elif self.tool_type == "custom":
                result = await self._execute_custom(request.parameters)
            else:
                return ToolResponse(
                    success=False,
                    error_message=f"Unknown tool type: {self.tool_type}"
                )
            
            execution_time = (time.time() - start_time) * 1000
            
            return ToolResponse(
                success=True,
                result=result,
                execution_time_ms=round(execution_time, 2)
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResponse(
                success=False,
                error_message=str(e),
                execution_time_ms=round(execution_time, 2)
            )
    
    async def _execute_api_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an API call."""
        url = params.get("url") or self.config.get("base_url", "")
        method = params.get("method", "GET").upper()
        headers = params.get("headers", {})
        data = params.get("data", {})
        
        if not url:
            raise ValueError("URL is required for API calls")
        
        # Add default headers from config
        default_headers = self.config.get("headers", {})
        headers = {**default_headers, **headers}
        
        # Make the API call
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data if method in ["POST", "PUT", "PATCH"] else None,
            params=data if method == "GET" else None,
            timeout=self.config.get("timeout", 30)
        )
        
        response.raise_for_status()
        
        try:
            result_data = response.json()
        except:
            result_data = response.text
        
        return {
            "status_code": response.status_code,
            "data": result_data,
            "headers": dict(response.headers)
        }
    
    async def _execute_calculation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a calculation safely."""
        expression = params.get("expression")
        variables = params.get("variables", {})
        
        if not expression:
            raise ValueError("Expression is required for calculations")
        
        # Simple safety check - only allow basic mathematical operations
        allowed_chars = set("0123456789+-*/.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
        forbidden_keywords = ["import", "exec", "eval", "open", "file", "__"]
        
        if not set(expression).issubset(allowed_chars):
            raise ValueError("Expression contains forbidden characters")
        
        for keyword in forbidden_keywords:
            if keyword in expression:
                raise ValueError(f"Expression contains forbidden keyword: {keyword}")
        
        # Create a safe namespace with only math functions and provided variables
        import math
        safe_namespace = {
            "__builtins__": {},
            "math": math,
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "round": round,
            **variables
        }
        
        try:
            result = eval(expression, safe_namespace)
            return {
                "expression": expression,
                "result": result,
                "variables_used": variables
            }
        except Exception as e:
            raise ValueError(f"Calculation error: {str(e)}")
    
    async def _execute_custom(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute custom logic - supports user-defined functions."""
        action = params.get("action", "default")
        
        # Check if custom function code is provided in config
        if "function_code" in self.config and action == "execute_function":
            return await self._execute_user_function(params)
        
        # Built-in actions for backward compatibility
        if action == "echo":
            return {"message": params.get("message", "Hello from custom tool!")}
        elif action == "transform":
            data = params.get("data", {})
            # Simple data transformation example
            transformed = {k: str(v).upper() if isinstance(v, str) else v for k, v in data.items()}
            return {"original": data, "transformed": transformed}
        else:
            return {"action": action, "parameters": params, "message": "Custom tool executed successfully"}
    
    async def _execute_user_function(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute user-defined function code safely."""
        function_code = self.config.get("function_code", "")
        if not function_code:
            raise ValueError("No function code provided in tool configuration")
        
        # Extract function parameters from the request
        func_params = params.get("function_params", {})
        
        # Create a safe execution environment
        safe_globals = {
            "__builtins__": {
                # Safe built-ins
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "abs": abs,
                "min": min,
                "max": max,
                "sum": sum,
                "round": round,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "sorted": sorted,
                "reversed": reversed,
                "print": print,  # For debugging
            },
            # Safe modules
            "math": __import__("math"),
            "json": __import__("json"),
            "datetime": __import__("datetime"),
            "re": __import__("re"),
            # Function parameters
            **func_params
        }
        
        # Basic security checks (relaxed for internal trusted environment)
        forbidden_keywords = [
            "exec", "eval", "open", "file", "input", "raw_input",
            "__import__", "__builtins__", "__globals__", "__locals__",
            "compile", "globals", "locals", "vars", "dir", "getattr", "setattr",
            "delattr", "hasattr", "callable", "isinstance", "issubclass",
            "subprocess", "os", "sys", "socket", "urllib", "requests"
        ]
        
        for keyword in forbidden_keywords:
            if keyword in function_code:
                raise ValueError(f"Forbidden keyword '{keyword}' found in function code")
        
        # Execute the user function
        try:
            # Create a local namespace for execution
            local_namespace = {}
            
            # Execute the function definition
            exec(function_code, safe_globals, local_namespace)
            
            # Look for a function named 'main' or the first function defined
            main_function = None
            if "main" in local_namespace and callable(local_namespace["main"]):
                main_function = local_namespace["main"]
            else:
                # Find the first callable function
                for name, obj in local_namespace.items():
                    if callable(obj) and not name.startswith("_"):
                        main_function = obj
                        break
            
            if not main_function:
                raise ValueError("No callable function found in the provided code")
            
            # Execute the function
            result = main_function()
            
            return {
                "function_executed": True,
                "result": result,
                "function_params": func_params
            }
            
        except Exception as e:
            raise ValueError(f"Function execution error: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters_schema": self.parameters_schema,
            "tool_type": self.tool_type,
            "config": self.config
        } 