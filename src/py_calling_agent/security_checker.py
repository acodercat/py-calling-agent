"""Security checker for PyCallingAgent code execution.

Provides AST-based analysis to detect potentially dangerous operations
in Python code before execution, with configurable security levels and
custom rule support.
"""

import ast
import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field


class SecurityLevel(Enum):
    """Security levels for code execution.
    
    STRICT: Maximum security, blocks most operations
    STANDARD: Balanced security for general use
    RELAXED: Minimal restrictions for trusted environments
    """
    STRICT = "strict"
    STANDARD = "standard"
    RELAXED = "relaxed"


class ViolationType(Enum):
    """Types of security violations."""
    DANGEROUS_IMPORT = "dangerous_import"
    DANGEROUS_FUNCTION = "dangerous_function"
    DANGEROUS_ATTRIBUTE = "dangerous_attribute"
    EVAL_EXEC = "eval_exec"
    CUSTOM_RULE = "custom_rule"


@dataclass(frozen=True)
class SecurityViolation:
    """Represents a security violation found in code."""
    type: ViolationType
    message: str
    line_number: Optional[int] = None
    severity: str = "high"
    
    def __str__(self) -> str:
        """Human-readable representation of the violation."""
        location = f"Line {self.line_number}" if self.line_number else "Unknown location"
        return f"{location}: {self.message} [{self.type.value}]"


@dataclass
class SecurityReport:
    """Security analysis report containing violations found during code analysis."""
    violations: List[SecurityViolation] = field(default_factory=list)
    security_level: SecurityLevel = SecurityLevel.STANDARD
    
    @property
    def is_safe(self) -> bool:
        """True if no violations were found."""
        return len(self.violations) == 0
    
    @property
    def critical_violations(self) -> List[SecurityViolation]:
        """Get only critical severity violations."""
        return [v for v in self.violations if v.severity == "critical"]
    
    @property
    def summary(self) -> str:
        """Get a summary of the security report."""
        if self.is_safe:
            return "Code passed security analysis"
        
        critical_count = len(self.critical_violations)
        total_count = len(self.violations)
        
        return f"Found {total_count} violations ({critical_count} critical)"
    
    def add_violation(self, violation: SecurityViolation) -> None:
        """Add a violation to the report."""
        self.violations.append(violation)


class SecurityRule(ABC):
    """Abstract base class for security rules.
    
    All security rules must inherit from this class and implement
    the check method to analyze AST nodes for violations.
    """
    
    def __init__(self, name: str, description: str, enabled: bool = True):
        self.name = name
        self.description = description
        self.enabled = enabled
    
    @abstractmethod
    def check(self, node: ast.AST) -> List[SecurityViolation]:
        """Check if the AST node violates this rule.
        
        Args:
            node: AST node to analyze
            
        Returns:
            List of violations found (empty if none)
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"


class DangerousImportRule(SecurityRule):
    """Rule to detect dangerous imports."""
    
    def __init__(self, dangerous_modules: Set[str], security_level: SecurityLevel):
        super().__init__(
            "dangerous_imports",
            "Detects imports of potentially dangerous modules"
        )
        self.dangerous_modules = dangerous_modules
        self.security_level = security_level
    
    def check(self, node: ast.AST) -> List[SecurityViolation]:
        violations = []
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in self.dangerous_modules:
                    violations.append(SecurityViolation(
                        type=ViolationType.DANGEROUS_IMPORT,
                        message=f"Dangerous import detected: {alias.name}",
                        line_number=node.lineno
                    ))
        
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module in self.dangerous_modules:
                violations.append(SecurityViolation(
                    type=ViolationType.DANGEROUS_IMPORT,
                    message=f"Dangerous import detected: from {node.module}",
                    line_number=node.lineno
                ))
        
        return violations


class DangerousFunctionRule(SecurityRule):
    """Rule to detect dangerous function calls."""
    
    def __init__(self, dangerous_functions: Set[str], security_level: SecurityLevel):
        super().__init__(
            "dangerous_functions",
            "Detects calls to potentially dangerous functions"
        )
        self.dangerous_functions = dangerous_functions
        self.security_level = security_level
    
    def check(self, node: ast.AST) -> List[SecurityViolation]:
        violations = []
        
        if isinstance(node, ast.Call):
            func_name = self._get_function_name(node.func)
            if func_name in self.dangerous_functions:
                violations.append(SecurityViolation(
                    type=ViolationType.DANGEROUS_FUNCTION,
                    message=f"Dangerous function call detected: {func_name}",
                    line_number=node.lineno
                ))
        
        return violations
    
    def _get_function_name(self, func_node: ast.AST) -> str:
        """Extract function name from various call patterns.
        
        Handles Name, Attribute, and nested Call nodes to extract
        the actual function name being called.
        """
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            # For calls like obj.method(), return the method name
            return func_node.attr
        elif isinstance(func_node, ast.Call):
            # For nested calls, recurse to find the innermost function
            return self._get_function_name(func_node.func)
        return ""


class DangerousAttributeRule(SecurityRule):
    """Rule to detect dangerous attribute access."""
    
    def __init__(self, dangerous_attributes: Set[str], security_level: SecurityLevel):
        super().__init__(
            "dangerous_attributes",
            "Detects access to potentially dangerous attributes"
        )
        self.dangerous_attributes = dangerous_attributes
        self.security_level = security_level
    
    def check(self, node: ast.AST) -> List[SecurityViolation]:
        violations = []
        
        if isinstance(node, ast.Attribute):
            if node.attr in self.dangerous_attributes:
                violations.append(SecurityViolation(
                    type=ViolationType.DANGEROUS_ATTRIBUTE,
                    message=f"Dangerous attribute access detected: {node.attr}",
                    line_number=node.lineno
                ))
        
        return violations


class EvalExecRule(SecurityRule):
    """Rule to detect eval/exec usage."""
    
    def __init__(self, security_level: SecurityLevel):
        super().__init__(
            "eval_exec",
            "Detects usage of eval() and exec() functions"
        )
        self.security_level = security_level
    
    def check(self, node: ast.AST) -> List[SecurityViolation]:
        violations = []
        
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            
            if func_name in ["eval", "exec", "compile"]:
                violations.append(SecurityViolation(
                    type=ViolationType.EVAL_EXEC,
                    message=f"Dynamic code execution detected: {func_name}()",
                    line_number=node.lineno,
                    severity="critical"
                ))
        
        return violations


class CustomRule(SecurityRule):
    """Custom user-defined security rule using regex patterns.
    
    Allows users to define custom security rules by providing
    a regex pattern that matches against the string representation
    of AST nodes.
    """
    
    def __init__(self, name: str, description: str, pattern: str):
        super().__init__(name, description)
        try:
            self.pattern = re.compile(pattern, re.MULTILINE | re.DOTALL)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{pattern}': {e}")
    
    def check(self, node: ast.AST) -> List[SecurityViolation]:
        violations = []
        
        try:
            # Convert node to string representation
            if hasattr(ast, 'unparse'):
                node_str = ast.unparse(node)
            else:
                # Fallback for older Python versions
                node_str = ast.dump(node)
            
            if self.pattern.search(node_str):
                violations.append(SecurityViolation(
                    type=ViolationType.CUSTOM_RULE,
                    message=f"Custom rule '{self.name}': {self.description}",
                    line_number=getattr(node, 'lineno', None)
                ))
        except Exception:
            # Don't fail analysis due to string conversion issues
            pass
        
        return violations


class SecurityChecker:
    """Main security checker for Python code analysis.
    
    Provides comprehensive security analysis using AST parsing to detect
    potentially dangerous operations before code execution. Supports multiple
    security levels, and custom rules.
    
    Example:
        >>> checker = SecurityChecker(SecurityLevel.STANDARD)
        >>> report = checker.check_code("import os; os.system('ls')")
        >>> print(report.is_safe)  # False
        >>> print(len(report.violations))  # 1+
    """
    
    # Default dangerous operations categorized by security impact
    _DANGEROUS_IMPORTS = {
        SecurityLevel.STRICT: {
            "os", "subprocess", "sys", "shutil", "tempfile", "pathlib",
            "socket", "urllib", "requests", "http", "ftplib", "smtplib",
            "pickle", "marshal", "shelve", "dill", "cloudpickle",
            "ctypes", "platform", "importlib", "runpy", "code",
            "ast", "dis", "inspect", "gc", "weakref", "json", "csv"
        },
        SecurityLevel.STANDARD: {
            "subprocess", "os", "shutil", "ctypes", "platform",
            "pickle", "marshal", "shelve", "dill", "cloudpickle",
            "socket", "urllib", "requests", "http", "ftplib", "smtplib"
        },
        SecurityLevel.RELAXED: {
            "subprocess", "ctypes", "pickle", "marshal", "dill"
        }
    }
    
    _DANGEROUS_FUNCTIONS = {
        SecurityLevel.STRICT: {
            "eval", "exec", "compile", "open", "input", "raw_input",
            "exit", "quit", "help", "license", "credits", "copyright",
            "__import__", "globals", "locals", "vars", "dir",
            "getattr", "setattr", "delattr", "hasattr",
            "callable", "isinstance", "issubclass", "iter", "next",
            "print", "breakpoint"
        },
        SecurityLevel.STANDARD: {
            "eval", "exec", "compile", "__import__", "exit", "quit",
            "globals", "locals", "getattr", "setattr", "delattr"
        },
        SecurityLevel.RELAXED: {
            "eval", "exec", "__import__"
        }
    }
    
    _DANGEROUS_ATTRIBUTES = {
        SecurityLevel.STRICT: {
            "__globals__", "__locals__", "__code__", "__closure__",
            "__defaults__", "__dict__", "__class__", "__bases__",
            "__mro__", "__subclasses__", "__import__", "__builtins__"
        },
        SecurityLevel.STANDARD: {
            "__globals__", "__locals__", "__code__", "__closure__",
            "__import__", "__builtins__"
        },
        SecurityLevel.RELAXED: {
            "__globals__", "__import__", "__builtins__"
        }
    }
    
    @classmethod
    def _get_security_config(cls, level: SecurityLevel) -> Dict[str, Set[str]]:
        """Get security configuration for a given level.
        
        Args:
            level: Security level to get configuration for
            
        Returns:
            Dictionary with sets of dangerous operations for the level
        """
        return {
            "dangerous_imports": cls._DANGEROUS_IMPORTS[level].copy(),
            "dangerous_functions": cls._DANGEROUS_FUNCTIONS[level].copy(),
            "dangerous_attributes": cls._DANGEROUS_ATTRIBUTES[level].copy()
        }
    
    def __init__(
        self,
        security_level: SecurityLevel = SecurityLevel.STANDARD,
        custom_rules: Optional[List[SecurityRule]] = None
    ):
        """Initialize SecurityChecker with specified configuration.
        
        Args:
            security_level: Security strictness level
            custom_rules: List of custom security rules
            
        Raises:
            ValueError: If invalid security level or configuration provided
        """
        if not isinstance(security_level, SecurityLevel):
            raise ValueError(f"Invalid security level: {security_level}")
            
        self.security_level = security_level
        self.config = self._get_security_config(security_level)
        self.custom_rules = list(custom_rules) if custom_rules else []
        
        # Initialize all rules
        self._rules = self._create_builtin_rules() + self.custom_rules

    
    def _create_builtin_rules(self) -> List[SecurityRule]:
        """Create built-in security rules based on current configuration.
        
        Returns:
            List of initialized security rules for current configuration
        """
        return [
            DangerousImportRule(
                self.config["dangerous_imports"],
                self.security_level
            ),
            DangerousFunctionRule(
                self.config["dangerous_functions"],
                self.security_level
            ),
            DangerousAttributeRule(
                self.config["dangerous_attributes"],
                self.security_level
            ),
            EvalExecRule(self.security_level)
        ]
    
    @property
    def rules(self) -> List[SecurityRule]:
        """Get all active security rules."""
        return [rule for rule in self._rules if rule.enabled]
    
    def add_custom_rule(self, rule: SecurityRule) -> None:
        """Add a custom security rule.
        
        Args:
            rule: Security rule to add
            
        Raises:
            ValueError: If rule with same name already exists
        """
        if any(r.name == rule.name for r in self._rules):
            raise ValueError(f"Rule with name '{rule.name}' already exists")
            
        self.custom_rules.append(rule)
        self._rules.append(rule)
    
    def check_code(self, code: str) -> SecurityReport:
        """Analyze Python code for security violations.
        
        Parses the code into an AST and applies all enabled security rules
        to detect potential security issues.
        
        Args:
            code: Python code string to analyze
            
        Returns:
            SecurityReport containing all violations found
            
        Raises:
            ValueError: If code is empty or None
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")
            
        # Create report
        report = SecurityReport(security_level=self.security_level)
        
        try:
            # Parse code into AST
            tree = ast.parse(code)
        except SyntaxError as e:
            report.add_violation(SecurityViolation(
                type=ViolationType.CUSTOM_RULE,
                message=f"Syntax error: {str(e)}",
                line_number=e.lineno,
                severity="critical"
            ))
            return report
        except Exception as e:
            report.add_violation(SecurityViolation(
                type=ViolationType.CUSTOM_RULE,
                message=f"Parse error: {str(e)}",
                severity="critical"
            ))
            return report
        
        # Analyze AST with all enabled rules
        for node in ast.walk(tree):
            for rule in self.rules:
                try:
                    violations = rule.check(node)
                    for violation in violations:
                        report.add_violation(violation)
                except Exception:
                    # Don't let rule failures break analysis
                    continue
        
        return report
    
    def is_code_safe(self, code: str) -> bool:
        """Quick check if code is safe to execute.
        
        Args:
            code: Python code to check
            
        Returns:
            True if code passed all security checks
        """
        try:
            return self.check_code(code).is_safe
        except ValueError:
            return False


class SecurityError(Exception):
    """Exception raised when code fails security checks.
    
    Contains both the error message and the detailed security report
    that caused the failure.
    """
    
    def __init__(self, message: str, report: SecurityReport):
        super().__init__(message)
        self.report = report
    
    @property
    def violation_count(self) -> int:
        """Number of security violations found."""
        return len(self.report.violations)
    
    @property
    def critical_violations(self) -> List[SecurityViolation]:
        """Get only critical violations."""
        return self.report.critical_violations
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        violation_summary = f" ({self.violation_count} violations)"
        return base_msg + violation_summary