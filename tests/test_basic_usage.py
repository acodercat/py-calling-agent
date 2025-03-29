import pytest
from py_calling_agent import PyCallingAgent

@pytest.fixture
def basic_agent(llm_engine):
    def add(a: int, b: int) -> int:
        """Add two numbers together"""
        return a + b

    def multiply(a: int, b: int) -> int:
        """Multiply two numbers together"""
        return a * b

    return PyCallingAgent(
        llm_engine,
        functions=[add, multiply]
    )

def test_basic_calculation(basic_agent):
    result = basic_agent.run("Calculate 5 plus 3")
    assert any(str(8) in part.lower() for part in result.split())

def test_multiple_calculations(basic_agent):
    result1 = basic_agent.run("Calculate 4 times 6")
    assert any(str(24) in part.lower() for part in result1.split())
    
    result2 = basic_agent.run("Add 10 and 20")
    assert any(str(30) in part.lower() for part in result2.split()) 