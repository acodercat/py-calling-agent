from typing import Callable, List, Dict, Any
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

class PythonRuntime:
    """
    A Python runtime that executes code snippets in an IPython environment.
    Provides a controlled execution environment with registered functions and objects.
    """
    def __init__(self, functions: List[Callable] = [], objects: Dict[str, Any] = {}):
        """Initialize runtime with available functions and objects."""
        self.ipython_shell = InteractiveShell.instance()        
        for function in functions:
            self.register_function(function)
            
        for name, value in objects.items():
            self.register_object(name, value)

    def register_function(self, func: Callable):
        """Register a function in the IPython namespace."""
        self.ipython_shell.user_ns[func.__name__] = func
    
    def register_object(self, name: str, value: Any):
        """Register an object in the IPython namespace."""
        self.ipython_shell.user_ns[name] = value

    def run(self, code_snippet: str) -> str:
        """Execute a code snippet and capture its output."""
        with capture_output() as output:
            self.ipython_shell.run_cell(code_snippet)
        return output.stdout

    def get_from_namespace(self, name: str) -> Any:
        """Retrieve any value (object, function, etc.) from the runtime's namespace."""
        return self.ipython_shell.user_ns.get(name)
