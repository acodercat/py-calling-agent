from py_calling_agent import PyCallingAgent, EventType
from py_calling_agent.python_runtime import PythonRuntime, Variable, SecurityViolation
import pytest

@pytest.fixture
def basic_agent(model):
    numbers = [3, 1, 4, 1, 5, 9]
    numbers_var = Variable(
        name="numbers",
        value=numbers,
        description="Input list of numbers to be processed"
    )
    runtime = PythonRuntime(variables=[numbers_var])
    return PyCallingAgent(model, runtime=runtime)

@pytest.mark.asyncio
async def test_security_violation_detection(basic_agent):
    """Test that security violations are properly detected and reported"""
    async for event in basic_agent.stream_events("Write code to import os and use threading"):
        if event.type == EventType.EXECUTION_ERROR:
            # Should catch security violation for blocked imports
            assert "Security violations found" in str(event.content)
            assert "Blocked import" in str(event.content)
            return
    assert False, "Expected security violation was not raised"

@pytest.mark.asyncio
async def test_syntax_error_with_source_line(basic_agent):
    """Test that syntax errors show the problematic source code line"""
    async for event in basic_agent.stream_events("Write code with a syntax error like: print('Hello world' without closing quote"):
        if event.type == EventType.EXECUTION_ERROR:
            # Should catch syntax error and show source line
            assert "Syntax error" in str(event.content)
            assert "source_line" in str(event.content) or "'print('Hello world'" in str(event.content)
            return
    assert False, "Expected syntax error was not raised"