import pytest
from py_agent import PyAgent

@pytest.fixture
def numbers():
    return [3, 1, 4, 1, 5, 9, 2, 6, 5]

@pytest.fixture
def variables(numbers):
    return {
        'numbers': numbers,
        'sorted_numbers': None,
        'sum_result': None
    }

@pytest.fixture
def variables_metadata():
    return {
        'numbers': {
            'description': 'List of numbers to process',
            'example': 'print(numbers)'
        },
        'sorted_numbers': {
            'description': 'Store the sorted numbers here',
        },
        'sum_result': {
            'description': 'Store the sum of numbers here',
        }
    }

@pytest.fixture
def state_agent(llm_engine, variables, variables_metadata):
    return PyAgent(
        llm_engine,
        variables=variables,
        variables_metadata=variables_metadata
    )

def test_sort_numbers(state_agent):
    state_agent.run("Sort the numbers list")
    sorted_result = state_agent.get_object_from_runtime('sorted_numbers')
    assert sorted(sorted_result) == sorted([1, 1, 2, 3, 4, 5, 5, 6, 9])

def test_calculate_sum(state_agent):
    state_agent.run("Calculate the sum of all numbers")
    total = state_agent.get_object_from_runtime('sum_result')
    assert total == 36  # sum of [3,1,4,1,5,9,2,6,5] 