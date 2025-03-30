import pytest
from py_calling_agent import PyCallingAgent

class DataAnalyzer:
    """A data analyzer that provides statistical analysis for numerical data."""
    
    def analyze(self, data: list) -> dict:
        """Calculate basic statistical measures for a list of numbers."""
        return {
            'min': min(data),
            'max': max(data),
            'avg': sum(data) / len(data),
            'len': len(data)
        }

@pytest.fixture
def analyzer():
    return DataAnalyzer()

@pytest.fixture
def numbers():
    return [3, 1, 4, 1, 5, 9, 2, 6, 5]

@pytest.fixture
def multi_turn_agent(llm_engine, analyzer, numbers):
    objects = {
        'analyzer': analyzer,
        'numbers': numbers
    }
    
    object_descriptions = {
        'analyzer': {
            'description': 'Tool for analyzing numerical data',
            'example': 'stats = analyzer.analyze(numbers)'
        },
        'numbers': {
            'description': 'Input data to analyze',
            'example': 'print(numbers)'
        },
        'stats': {
            'description': 'Store analysis results here',
            'example': 'stats = analyzer.analyze(numbers)'
        }
    }
    
    return PyCallingAgent(
        llm_engine,
        objects=objects,
        object_descriptions=object_descriptions
    )

def test_basic_analysis(multi_turn_agent):
    multi_turn_agent.run("Analyze the numbers and store results in 'stats'")
    stats = multi_turn_agent.get_object('stats')
    
    assert stats['min'] == 1
    assert stats['max'] == 9
    assert stats['avg'] == 4.0
    assert stats['len'] == 9

def test_multi_turn_conversation(multi_turn_agent):
    # First turn
    multi_turn_agent.run("Analyze the numbers and store results in 'stats'")
    stats = multi_turn_agent.get_object('stats')
    assert stats is not None
    assert all(k in stats for k in ['min', 'max', 'avg', 'len'])
    
    # Second turn
    result = multi_turn_agent.run("What is the average value in the stats?")
    assert result is not None
    assert "4" in result.lower() or "four" in result.lower()
    
    # Third turn
    result = multi_turn_agent.run("Is the maximum value (9) significantly higher than the average?")
    assert result is not None
    assert any(word in result.lower() for word in ['yes', 'higher', 'greater', 'more']) 