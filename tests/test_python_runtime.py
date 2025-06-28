import pytest
from src.py_calling_agent.python_runtime import PythonRuntime, Variable, Function, SecurityViolation


@pytest.fixture
def simple_runtime():
    return PythonRuntime()


@pytest.fixture
def runtime_with_data():
    numbers_var = Variable(
        name="numbers",
        value=[3, 1, 4, 1, 5, 9, 2, 6, 5],
        description="List of numbers to process"
    )
    
    result_var = Variable(
        name="result",
        description="Store calculation results here"
    )
    
    return PythonRuntime(variables=[numbers_var, result_var])


@pytest.fixture
def runtime_with_function():
    def multiply(a, b):
        """Multiply two numbers"""
        return a * b
    
    func = Function(multiply, "Multiplication function")
    return PythonRuntime(functions=[func])


@pytest.mark.asyncio
async def test_basic_execution(simple_runtime):
    """Test basic code execution works"""
    await simple_runtime.execute("x = 5 + 3")
    result = simple_runtime._executor.get_from_namespace('x')
    assert result == 8


@pytest.mark.asyncio
async def test_print_output(simple_runtime):
    """Test code with print output"""
    output = await simple_runtime.execute("print('Hello World')")
    assert "Hello World" in output


@pytest.mark.asyncio
async def test_variable_usage(runtime_with_data):
    """Test using injected variables"""
    await runtime_with_data.execute("result = sum(numbers)")
    total = runtime_with_data.get_variable_value('result')
    assert total == 36


@pytest.mark.asyncio
async def test_function_usage(runtime_with_function):
    """Test using injected functions"""
    await runtime_with_function.execute("result = multiply(6, 7)")
    result = runtime_with_function._executor.get_from_namespace('result')
    assert result == 42


@pytest.mark.asyncio
async def test_security_blocked_import(simple_runtime):
    """Test security blocks dangerous imports"""
    with pytest.raises(SecurityViolation):
        await simple_runtime.execute("import os")


@pytest.mark.asyncio
async def test_security_blocked_eval(simple_runtime):
    """Test security blocks eval"""
    with pytest.raises(SecurityViolation):
        await simple_runtime.execute("eval('2+2')")


@pytest.mark.asyncio
async def test_security_blocked_open(simple_runtime):
    """Test security blocks file operations"""
    with pytest.raises(SecurityViolation):
        await simple_runtime.execute("open('test.txt')")

@pytest.mark.asyncio
async def test_multiple_executions(simple_runtime):
    """Test multiple code executions share state"""
    await simple_runtime.execute("a = 10")
    await simple_runtime.execute("b = a * 2")
    await simple_runtime.execute("c = a + b")
    
    result = simple_runtime._executor.get_from_namespace('c')
    assert result == 30


def test_describe_functions(runtime_with_function):
    """Test function description works"""
    description = runtime_with_function.describe_functions()
    assert "multiply" in description
    assert "signature:" in description


def test_describe_variables(runtime_with_data):
    """Test variable description works"""
    description = runtime_with_data.describe_variables()
    assert "numbers" in description
    assert "result" in description


@pytest.mark.asyncio
async def test_syntax_error(simple_runtime):
    """Test syntax errors are caught"""
    with pytest.raises(SecurityViolation):
        await simple_runtime.execute("if True")  # Missing colon