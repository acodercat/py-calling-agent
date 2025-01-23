from typing import Callable, List, Dict, Any
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

class PythonInterpreter:
    """
    A Python interpreter that executes code snippets in an IPython environment.
    Provides a controlled execution environment with registered functions and variables.
    """
    def __init__(self, functions: List[Callable] = [], variables: Dict[str, Any] = {}):
        """Initialize interpreter with available functions and variables.

        Args:
            functions: List of callable functions to register
            variables: Dictionary of variables to inject into the interpreter
        """
        self.ipython_shell = InteractiveShell.instance()
        
        for function in functions:
            self.register_function(function)
            
        for name, value in variables.items():
            self.register_variable(name, value)

    def register_function(self, func: Callable):
        """Register a function in the IPython namespace.

        Args:
            func: Function to make available in the interpreter
        """
        self.ipython_shell.user_ns[func.__name__] = func
    
    def register_variable(self, name: str, value: Any):
        """Register a variable in the IPython namespace.

        Args:
            name: Name of the variable
            value: Value of the variable
        """
        self.ipython_shell.user_ns[name] = value

    def run(self, code_snippet: str) -> str:
        """Execute a code snippet and capture its output.

        Args:
            code_snippet: Python code to execute

        Returns:
            Captured stdout from code execution
        """
        with capture_output() as output:
            self.ipython_shell.run_cell(code_snippet)
        return output.stdout

    def get_from_namespace(self, name: str) -> Any:
        """Retrieve any value (variable, function, etc.) from the interpreter's namespace.
        
        Args:
            name (str): The name of the value to retrieve
            
        Returns:
            Any: The value from the namespace, or None if not found
        """
        return self.ipython_shell.user_ns.get(name)