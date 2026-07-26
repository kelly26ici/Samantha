import sys
from loguru import logger
from pydantic import BaseModel, Field
from typing import Optional, Literal, Callable, Dict, List, Any, Type

logger.remove(0)
logger.add(sys.stderr, format="{level} | {message} | {time} | {extra}")

class ToolRegistry:
    
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]]
        
    def register(self, name: str, schema: Type[BaseModel]):
        """This is automatically adds tools to the registry instead of me manually doing it"""
        def decorator(func: Callable):
            self._tools[name] = {
                "schema": schema, 
                "function": func,
                "declaration": {
                    "name": name,
                    "description": func.__doc__,
                    "parameters": schema.model_json_schema()
                }
            }
            return func
        return decorator
    
    def get_llm_declarations(self) -> List:
        """Returns a list of tool definitions to pass to the llm"""
        return [tool["declaration"] for tool in self._tools.values()]
    
    def execute(self, tool_name: str, raw_llm_args: dict) -> any:
        if tool_name not in self._tools:
            raise ValueError(logger.error("Tool '{tool_name}' is not registered"))
        
        tool = self._tools[tool_name]
        
        validated_args = tool["schema"](**raw_llm_args)
        
        return tool["function"](validated_args)
    
registry = ToolRegistry()