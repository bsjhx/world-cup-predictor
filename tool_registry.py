from dataclasses import dataclass
from typing import Callable, get_type_hints, get_origin, get_args
import inspect
import json


@dataclass
class ToolInfo:
    name: str
    description: str
    schema: dict

    @classmethod
    def from_callable(cls, func: Callable):
        """
        Automatically extract tool information from a Python function.

        Expected function format:
        - Must have type hints for all parameters
        - Should have a docstring describing what it does
        - Return type is optional but recommended
        """
        func_name = func.__name__
        func_description = (func.__doc__ or "").strip()

        # Get function signature
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        # Build parameters schema
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name in type_hints:
                param_type = type_hints[param_name]
                param_schema = cls._python_type_to_json_schema(param_type)

                # Extract parameter description from docstring if available
                param_description = cls._extract_param_description(func_description, param_name)
                if param_description:
                    param_schema["description"] = param_description

                properties[param_name] = param_schema

                # Check if parameter has a default value
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
                else:
                    # Add default to schema
                    param_schema["default"] = param.default

        schema = {
            "type": "function",
            "function": {
                "name": func_name,
                "description": func_description.split('\n')[0] if func_description else f"Call {func_name}",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

        return cls(name=func_name, description=func_description, schema=schema)

    @staticmethod
    def _python_type_to_json_schema(python_type) -> dict:
        """Convert Python type hints to JSON schema types."""
        origin = get_origin(python_type)

        # Handle Optional types
        if origin is type(None) or python_type is type(None):
            return {"type": "null"}

        # Handle Union types (including Optional)
        if origin is type(None):
            return {"type": "null"}

        # Basic type mappings
        type_map = {
            str: {"type": "string"},
            int: {"type": "integer"},
            float: {"type": "number"},
            bool: {"type": "boolean"},
            list: {"type": "array"},
            dict: {"type": "object"},
        }

        # Check if it's a basic type
        if python_type in type_map:
            return type_map[python_type]

        # Handle generic types like List[str], Dict[str, int], etc.
        if origin is list:
            args = get_args(python_type)
            schema = {"type": "array"}
            if args:
                schema["items"] = ToolInfo._python_type_to_json_schema(args[0])
            return schema

        if origin is dict:
            return {"type": "object"}

        # Default to string if type is unknown
        return {"type": "string"}

    @staticmethod
    def _extract_param_description(docstring: str, param_name: str) -> str:
        """Extract parameter description from docstring (supports various formats)."""
        if not docstring:
            return ""

        # Look for common docstring formats
        # Format 1: "param_name: description"
        # Format 2: ":param param_name: description"
        # Format 3: "Args:\n    param_name: description"

        lines = docstring.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()

            # Check various formats
            if f"{param_name}:" in line:
                # Extract description after the colon
                parts = line.split(f"{param_name}:", 1)
                if len(parts) > 1:
                    return parts[1].strip()

            if f":param {param_name}:" in line:
                parts = line.split(f":param {param_name}:", 1)
                if len(parts) > 1:
                    return parts[1].strip()

        return ""

    def to_openai_schema(self) -> dict:
        """Return the OpenAI-compatible schema."""
        return self.schema

    def __str__(self):
        return f"Tool: {self.name}\nDescription: {self.description}\nSchema: {json.dumps(self.schema, indent=2)}"


class ToolRegistry:
    """Registry to manage and automatically register tools."""

    def __init__(self):
        self.tools = {}
        self.schemas = []

    def register(self, func: Callable) -> Callable:
        """
        Register a function as a tool.
        Can be used as a decorator.

        Example:
            @registry.register
            def my_tool(arg1: str, arg2: int = 10) -> dict:
                '''Tool description'''
                return {"result": "success"}
        """
        tool_info = ToolInfo.from_callable(func)
        self.tools[tool_info.name] = func
        self.schemas.append(tool_info.to_openai_schema())
        return func

    def get_schemas(self) -> list:
        """Get all tool schemas in OpenAI format."""
        return self.schemas

    def execute_tool(self, name: str, **kwargs):
        """Execute a tool by name with given arguments."""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found in registry")
        return self.tools[name](**kwargs)

    def __str__(self):
        tools_list = "\n".join([f"  - {name}" for name in self.tools.keys()])
        return f"ToolRegistry with {len(self.tools)} tools:\n{tools_list}"
