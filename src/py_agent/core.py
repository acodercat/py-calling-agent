from .prompts import DEFAULT_SYSTEM_PROMPT, DEFAULT_NEXT_STEP_PROMPT
from .interpreter import PythonInterpreter
from typing import Callable, Optional, List, Dict, Any
from .llm import LLMEngine
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from .utils import extract_python_code
import inspect
from enum import Enum, IntEnum

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LogLevel(IntEnum):
    """Log levels for controlling output verbosity."""
    ERROR = 0  # Only errors
    INFO = 1   # Normal output
    DEBUG = 2  # Detailed output

class Logger:
    """
    A structured logger for PyAgent that provides leveled logging with rich formatting.
    
    Handles different types of log messages (debug, info, error) with customizable 
    styling and visibility levels. Uses rich library for enhanced console output.

    Log Levels:
    - ERROR (0): Only critical errors
    - INFO (1): Standard operation information
    - DEBUG (2): Detailed execution traces
    """

    def __init__(self, level: LogLevel = LogLevel.INFO):
        """Initialize logger with specified verbosity level.

        Args:
            level: Minimum log level to display. Defaults to INFO.
        """
        self.console = Console()
        self.level = level

    def __log(self, title: str, content: str = None, style: str = None, level: LogLevel = LogLevel.INFO):
        """Internal method to handle log message formatting and display.

        Args:
            title: Section title for the log message
            content: Main message content
            style: Rich text style (color/formatting)
            level: Message's log level
        """
        if level <= self.level:
            panel = Panel(content, title=title, style=style)
            self.console.print(panel)

    def debug(self, title: str, message: str, style: str = "yellow"):
        self.__log(title, message, style, LogLevel.DEBUG)

    def info(self, title: str, message: str, style: str = "blue"):
        self.__log(title, message, style, LogLevel.INFO)

    def error(self, title: str, message: str, style: str = "red"):
        self.__log(title, message, style, LogLevel.ERROR)


class SystemPromptFormatter:
    """
    Formats the system prompt by injecting descriptions of available functions, variables, and libraries.
    
    This formatter structures information about the Python runtime environment into a format
    that helps the LLM understand what tools and variables are available for use.

    Key responsibilities:
    - Format function descriptions with signatures and docstrings
    - Format variable descriptions with types, metadata, and examples
    - Format available library information
    
    Example:
        >>> formatter = SystemPromptFormatter(
        ...     system_prompt_template="Functions:\n{functions}\nVariables:\n{variables}",
        ...     variables_metadata={
        ...         'data': {'description': 'Input data', 'example': 'print(data)'}
        ...     },
        ...     functions=[sort_list],
        ...     variables={'data': [3,1,4]},
        ...     libraries=['numpy', 'pandas']
        ... )
        >>> formatted_prompt = formatter.format()
    """

    def __init__(self, 
        system_prompt_template: str, 
        variables_metadata: Dict[str, Dict[str, str]], 
        functions: List[Callable], 
        variables: Dict[str, Any], 
        libraries: List[str]
    ):
        """Initialize the formatter with runtime environment information.

        Args:
            system_prompt_template: Template string with {functions}, {variables}, {libraries} placeholders
            variables_metadata: Metadata describing each variable's purpose and usage
            functions: List of available functions in the runtime
            variables: Dictionary of available variables in the runtime
            libraries: List of available Python libraries
        """
        self.system_prompt_template = system_prompt_template
        self.variables_metadata = variables_metadata
        self.functions = functions
        self.variables = variables
        self.libraries = libraries

    def format(self) -> str:
        """Format system prompt with functions, variables and libraries descriptions."""
        functions_description = self.format_functions()
        variables_description = self.format_variables()
        libraries_description = self.format_libraries()
        return self.system_prompt_template.format(functions=functions_description, variables=variables_description, libraries=libraries_description)
    
    def format_functions(self) -> str:
        """Format description of functions with signatures and docstrings."""
        descriptions = [
            f"Function: {func.__name__}{inspect.signature(func)}\n"
            f"Description: {func.__doc__ or f'Function {func.__name__}'}"
            for func in self.functions
        ]
        return "\n".join(descriptions) if descriptions else "No functions available"
    
    def format_variables(self) -> str:
        """Format description of variables with their metadata."""
        descriptions = []
        
        for name, value in self.variables.items():
            var_info = [f"- {name} ({type(value).__name__}):"]
            
            if meta := self.variables_metadata.get(name, {}):
                if desc := meta.get("description"):
                    var_info.append(f"  Description: {desc}")
                if example := meta.get("example"): 
                    var_info.append(f"  Example usage: {example}")
                    
            if doc := (value.__doc__ or "").strip():
                var_info.append(f"  Documentation: {doc}")
                
            descriptions.append("\n".join(var_info))

        
        return "\n".join(descriptions) if descriptions else "No variables available"
    
    def format_libraries(self) -> str:
        """Format description of libraries."""
        return "\n".join(self.libraries) if self.libraries else "No libraries available"


class PyAgent:
    """
    A tool-augmented agent framework that enables function-calling through LLM code generation.
    
    Unlike traditional JSON-schema approaches, PyAgent leverages LLM's coding capabilities 
    to interact with tools through a Python runtime environment. It follows an 
    observation-planning-action pattern and allows variable/object injection and retrieval.

    Key features:
    - Code-based function calling instead of JSON schemas
    - Direct Python object/variable injection into runtime
    - Multi-turn conversation with observation feedback
    - Runtime state management and result retrieval
    
    Example:
        >>> # Define a tool and data to process
        >>> def sort_list(data: list) -> list:
        ...     '''Sort a list of numbers'''
        ...     return sorted(data)
        ...
        >>> numbers = [3, 1, 4]
        >>> 
        >>> # Create agent with injected function and variable
        >>> agent = PyAgent(
        ...     llm_engine,
        ...     functions=[sort_list],
        ...     variables={'numbers': numbers},
        ...     variables_metadata={
        ...         'numbers': {
        ...             'description': 'Input list to sort',
        ...             'example': 'result = sort_list(numbers)'
        ...         },
        ...         'sorted_result': {
        ...             'description': 'Store the result of the sorting in this variable.'
        ...         }
        ...     }
        ... )
        >>> 
        >>> # Run task and get sorted_result from runtime
        >>> agent.run("Sort the numbers and store as 'sorted_result'")
        >>> result = agent.get_object_from_runtime('sorted_result')
    """

    def __init__(
        self,
        llm_engine: LLMEngine,
        system_prompt_template: Optional[str] = None,
        functions: List[Callable] = [],
        libraries: Optional[List[str]] = [],
        variables: Optional[Dict[str, Any]] = {},
        variables_metadata: Optional[Dict[str, Dict[str, str]]] = None,
        max_iterations: int = 5,
        log_level: LogLevel = LogLevel.DEBUG,
        next_step_prompt_template: Optional[str] = None,
    ):
        """Initialize a new PyAgent instance.

        Args:
            llm_engine (LLMEngine): The language model engine to use
            system_prompt_template (Optional[str], optional): Custom system prompt template. Defaults to None.
            functions (List[Callable], optional): Available functions. Defaults to [].
            libraries (Optional[List[str]], optional): Available libraries. Defaults to [].
            variables (Optional[Dict[str, Any]], optional): Variables to inject into the Python environment. Defaults to {}.
            variables_metadata (Optional[Dict[str, Dict[str, str]]], optional): 
                Metadata for variables including description and expected usage.
                Format: {
                    "variable_name": {
                        "description": "Description of the variable",
                        "type": "Expected type",
                        "example": "Usage example"
                    }
                }
            max_iterations (int, optional): Max conversation turns. Defaults to 5.
            log_level (LogLevel, optional): Logging verbosity. Defaults to LogLevel.DEBUG.
            next_step_prompt_template (Optional[str], optional): Custom continuation prompt template. Defaults to None.
        """
        self.llm_engine = llm_engine
        self.system_prompt_template = system_prompt_template or DEFAULT_SYSTEM_PROMPT
        self.next_step_prompt_template = next_step_prompt_template or DEFAULT_NEXT_STEP_PROMPT
        self.python_interpreter = PythonInterpreter(functions, variables)
        self.max_iterations = max_iterations
        self.system_prompt_formatter = SystemPromptFormatter(self.system_prompt_template, variables_metadata, functions, variables, libraries)
        self.system_prompt = self.system_prompt_formatter.format()
        self.loger = Logger(log_level)

    def run(self, user_prompt: str) -> str:
        """Execute the agent with the given user prompt.

        This method:
        1. Initializes a conversation with the system prompt
        2. Sends the user prompt to the LLM
        3. Extracts and executes any Python code in the response
        4. Continues the conversation based on execution results
        5. Repeats until completion or max_iterations reached

        Args:
            user_prompt (str): The initial user query or instruction

        Returns:
            str: The final response from the LLM, or a message indicating
                max iterations were reached

        Example:
            >>> agent.run("Sort this list: [3,1,4,1,5,9,2,6,5]")
            "Here's the sorted list: [1, 1, 2, 3, 4, 5, 5, 6, 9]"
        """
        messages = [
            {"role": MessageRole.SYSTEM, "content": self.system_prompt},
            {"role": MessageRole.USER, "content": user_prompt}
        ]
        self.loger.debug("System Prompt", self.system_prompt, "blue")
        self.loger.debug("Initial Prompt", user_prompt, "blue")
        
        for iteration in range(self.max_iterations):
            self.loger.debug(f"Iteration {iteration + 1}/{self.max_iterations}", f"Processing...", "yellow")
            
            llm_response = self.llm_engine(messages)
            code_block = extract_python_code(llm_response)
            
            if not code_block:
                self.loger.debug("Final Response", llm_response, "green")
                return llm_response
                
            
            self.loger.debug("Executing Code", Syntax(code_block, "python", theme="monokai"))
            
            execution_result = self.python_interpreter.run(code_block)
            self.loger.debug("Execution Result", execution_result or "No output", "cyan")
            
            messages.extend([
                {"role": MessageRole.ASSISTANT, "content": llm_response},
                {"role": MessageRole.USER, "content": self.next_step_prompt_template.format(execution_result=execution_result)}
            ])
            
            next_step = self.llm_engine(messages)
            self.loger.debug("LLM Response", next_step, "magenta")
            
            if not extract_python_code(next_step):
                return next_step
        
        final_response = f"Max iterations ({self.max_iterations}) reached. Last response: {messages[-1]['content']}"
        self.loger.debug("Warning", final_response, "red")
        return final_response

    def get_object_from_runtime(self, name: str) -> Any:
        """Get an object from the agent's runtime environment.
        
        Args:
            name (str): The name of the object to retrieve
            
        Returns:
            Any: The object if found, or None if not found
        """
        return self.python_interpreter.get_from_namespace(name)