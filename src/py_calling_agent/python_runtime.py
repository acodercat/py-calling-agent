from typing import Callable, List, Dict, Any, Optional, Set, Tuple
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
from dataclasses import dataclass
import inspect
import ast
import re

class SecurityViolation(Exception):
    """Raised when code violates security policies."""
    def __init__(self, message: str, violation_type: str, line_number: int = None):
        self.violation_type = violation_type
        self.line_number = line_number
        super().__init__(message)


@dataclass
class SecurityPolicy:
    """Configuration for code security policies."""
    # Dangerous modules/functions that should never be allowed
    blocked_imports: Set[str]
    blocked_functions: Set[str]
    blocked_attributes: Set[str]
    
    # Dangerous patterns (regex)
    blocked_patterns: List[str]
    
    # File system restrictions
    allow_file_operations: bool = False
    allow_network_operations: bool = False
    allow_subprocess: bool = False
    

SECURITY_POLICIE = SecurityPolicy(
    blocked_imports={
        'os', 'sys', 'subprocess', 'importlib', 'builtins',
        'socket', 'urllib', 'requests', 'http', 'ftplib',
        'smtplib', 'telnetlib', 'ssl', 'hashlib', 'hmac',
        'secrets', 'tempfile', 'shutil', 'glob', 'pathlib',
        'ctypes', 'multiprocessing', 'threading', 'concurrent',
        'pickle', 'marshal', 'shelve', 'dbm', 'sqlite3',
        'webbrowser', 'platform', 'getpass'
    },
    blocked_functions={
        'exec', 'eval', 'compile', 'open', 'input', 'raw_input',
        '__import__', 'getattr', 'setattr', 'delattr', 'hasattr',
        'globals', 'locals', 'vars', 'dir', 'help', 'memoryview',
        'breakpoint', 'exit', 'quit'
    },
    blocked_attributes={
        '__import__', '__builtins__', '__globals__', '__locals__',
        '__code__', '__func__', '__self__', '__dict__', '__class__',
        '__bases__', '__mro__', '__subclasses__'
    },
    blocked_patterns=[
        r'__.*__',  # Dunder methods/attributes
        r'eval\s*\(',  # eval calls
        r'exec\s*\(',  # exec calls
        r'open\s*\(',  # file operations
        r'\.system\(',  # os.system calls
        r'\.popen\(',   # os.popen calls
        r'\.call\(',    # subprocess.call
        r'\.run\(',     # subprocess.run
        r'\.Popen\(',   # subprocess.Popen
    ],
    allow_file_operations=False,
    allow_network_operations=False,
    allow_subprocess=False,
)
class CodeSecurityChecker:
    """
    AST-based security checker for Python code.
    """
    
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
        
    def check_code(self, code: str) -> Tuple[bool, List[SecurityViolation]]:
        """
        Check code for security violations.
        Returns (is_safe, violations_list)
        """
        violations = []
        
        # Pattern-based checks (fast, but can have false positives)
        violations.extend(self._check_patterns(code))
        
        # AST-based checks (more accurate)
        try:
            tree = ast.parse(code)
            violations.extend(self._check_ast(tree))
        except SyntaxError as e:
            # Get the problematic source code line
            lines = code.split('\n')
            source_line = lines[e.lineno - 1].strip() if 1 <= e.lineno <= len(lines) else ""
            violations.append(SecurityViolation(
                f"Syntax error: {e.msg}: '{source_line}'",
                "syntax_error",
                e.lineno
            ))
        
        return len(violations) == 0, violations
    
    
    def _check_patterns(self, code: str) -> List[SecurityViolation]:
        """Check for dangerous patterns using regex."""
        violations = []
        
        for pattern in self.policy.blocked_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                violations.append(SecurityViolation(
                    f"Blocked pattern '{pattern}' found: {match.group()}",
                    "blocked_pattern",
                    line_num
                ))
        
        return violations
    
    def _check_ast(self, tree: ast.AST) -> List[SecurityViolation]:
        """Check AST for security violations."""
        violations = []
        
        for node in ast.walk(tree):
            violations.extend(self._check_node(node))
        
        return violations
    
    def _check_node(self, node: ast.AST) -> List[SecurityViolation]:
        """Check individual AST node for violations."""
        violations = []
        
        # Check imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in self.policy.blocked_imports:
                    violations.append(SecurityViolation(
                        f"Blocked import: {alias.name}",
                        "blocked_import",
                        node.lineno
                    ))
        
        elif isinstance(node, ast.ImportFrom):
            if node.module in self.policy.blocked_imports:
                violations.append(SecurityViolation(
                    f"Blocked import from: {node.module}",
                    "blocked_import",
                    node.lineno
                ))
        
        # Check function calls
        elif isinstance(node, ast.Call):
            func_name = self._get_function_name(node.func)
            if func_name in self.policy.blocked_functions:
                violations.append(SecurityViolation(
                    f"Blocked function call: {func_name}",
                    "blocked_function",
                    node.lineno
                ))
        
        # Check attribute access
        elif isinstance(node, ast.Attribute):
            if node.attr in self.policy.blocked_attributes:
                violations.append(SecurityViolation(
                    f"Blocked attribute access: {node.attr}",
                    "blocked_attribute",
                    node.lineno
                ))
        
        # Check file operations
        elif isinstance(node, ast.Call) and not self.policy.allow_file_operations:
            func_name = self._get_function_name(node.func)
            if func_name in {'open', 'file'}:
                violations.append(SecurityViolation(
                    f"File operation not allowed: {func_name}",
                    "file_operation",
                    node.lineno
                ))
        
        return violations
    
    def _get_function_name(self, func_node: ast.AST) -> str:
        """Extract function name from call node."""
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            return func_node.attr
        else:
            return ""

class PythonExecutor:
    """
    Handles Python code execution using IPython.
    """

    def __init__(self):
        """Initialize IPython shell for code execution."""
        self._shell = InteractiveShell.instance()
        self.security_checker = CodeSecurityChecker(SECURITY_POLICIE)
        
    def inject_into_namespace(self, name: str, value: Any) -> None:
        """Inject a value into the execution namespace."""
        self._shell.user_ns[name] = value
    
    async def execute(self, code: str) -> str:
        """Execute code snippet with security checks."""
        # Perform security check
        is_safe, violations = self.security_checker.check_code(code)
        if not is_safe:
            violation_messages = [
                f"Line {v.line_number}: {v}" if v.line_number else str(v)
                for v in violations
            ]
            error_msg = "Security violations found:\n" + "\n".join(violation_messages)
            raise SecurityViolation(error_msg, "multiple_violations")
        
        # Execute if safe
        with capture_output() as output:
            transformed_code = self._shell.transform_cell(code)
            await self._shell.run_cell_async(transformed_code, transformed_cell=transformed_code)
        
        return output.stdout
    
    def get_from_namespace(self, name: str) -> Any:
        """Get a value from the execution namespace."""
        return self._shell.user_ns.get(name)

    def check_code_safety(self, code: str) -> Tuple[bool, List[str]]:
        """Check if code is safe without executing it."""
        is_safe, violations = self.security_checker.check_code(code)
        messages = [str(v) for v in violations]
        return is_safe, messages
class Variable:
    """Represents a variable in the Python runtime environment."""
    name: str
    description: Optional[str] = None
    value: Optional[Any] = None
    doc: Optional[str] = None
    type: str

    def __init__(self, name: str, value: Optional[Any] = None, description: Optional[str] = None):
        """Initialize the variable."""
        self.name = name
        self.value = value
        self.description = description
        self.type = type(self.value).__name__

        if hasattr(self.value, "__doc__") and self.value.__doc__ and self.value.__doc__.strip():
            self.doc = self.value.__doc__.strip()
        
    def __str__(self):
        """Return a string representation of the variable."""
        parts = [f"- name: {self.name}"]
        parts.append(f"  type: {self.type}")
        if self.description:
            parts.append(f"  description: {self.description}")
        if self.doc:
            parts.append(f"  doc: {self.doc}")

        return "\n".join(parts)

class Function:
    """Represents a function in the Python runtime environment."""
    func: Callable
    description: Optional[str] = None
    doc: Optional[str] = None
    name: str
    signature: str


    def __init__(self, func: Callable, description: Optional[str] = None):
        """Initialize the function."""
        self.func = func
        self.description = description
        self.name = func.__name__
        self.signature = f"{self.name}{inspect.signature(self.func)}"
        if hasattr(self.func, "__doc__") and self.func.__doc__ and self.func.__doc__.strip():
            self.doc = self.func.__doc__
        
    
    def __str__(self):
        """Return a string representation of the function."""
        parts = [f"- signature: {self.signature}"]
        if self.description:
            parts.append(f"  description: {self.description}")
        if self.doc:
            parts.append(f"  doc: {self.doc}")

        return "\n".join(parts)
    
class PythonRuntime:
    """
    A Python runtime that executes code snippets in an IPython environment.
    Provides a controlled execution environment with registered functions and objects.
    """
    def __init__(
        self,
        functions: Optional[List[Function]] = None,
        variables: Optional[List[Variable]] = None
    ):
        """Initialize runtime with executor and optional initial resources."""
        self._executor = PythonExecutor()
        self._functions: Dict[str, Function] = {}
        self._variables: Dict[str, Variable] = {}

        if functions:
            for function in functions:
                self.inject_function(function)
            
        if variables:
            for variable in variables:
                self.inject_variable(variable)

    def inject_function(self, function: Function) -> 'PythonRuntime':
        """Inject a function in both metadata and execution namespace."""
        self._functions[function.name] = function
        self._executor.inject_into_namespace(function.name, function.func)
        return self
    
    def inject_variable(self, variable: Variable) -> 'PythonRuntime':
        """Inject a variable in both metadata and execution namespace."""
        self._variables[variable.name] = variable
        self._executor.inject_into_namespace(variable.name, variable.value)
        return self

    async def execute(self, code: str) -> str:
        """Execute code using the executor."""
        return await self._executor.execute(code)

    def get_variable_value(self, name: str) -> Any:
        """Get current value of a variable."""
        if name not in self._variables:
            raise KeyError(f"Variable '{name}' is not managed by this runtime. Available variables: {list(self._variables.keys())}")
        return self._executor.get_from_namespace(name)
    
    def describe_variables(self) -> str:
        """Generate formatted variable descriptions for system prompt."""
        if not self._variables:
            return "No variables available"
        
        descriptions = []
        for variable in self._variables.values():
            descriptions.append(str(variable))
        
        return "\n".join(descriptions)
    
    def describe_functions(self) -> str:
        """Generate formatted function descriptions for system prompt."""
        if not self._functions:
            return "No functions available"
        
        descriptions = []
        for function in self._functions.values():
            descriptions.append(str(function))
        
        return "\n".join(descriptions)
