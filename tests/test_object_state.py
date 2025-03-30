import pytest
from py_calling_agent import PyCallingAgent

@pytest.fixture
def numbers():
    return [3, 1, 4, 1, 5, 9, 2, 6, 5]

@pytest.fixture
def objects(numbers):
    return {
        'numbers': numbers,
        'sorted_numbers': None,
        'sum_result': None
    }

@pytest.fixture
def object_descriptions():
    return {
        'numbers': {
            'description': 'List of numbers to process',
            'example': 'print(numbers)'
        },
        'sorted_numbers': {
            'description': 'Store the sorted numbers in this variable',
            'example': 'sorted_numbers = sorted(numbers)'
        },
        'sum_result': {
            'description': 'Store the sum of numbers in this variable',
            'example': 'sum_result = sum(numbers)'
        }
    }

@pytest.fixture
def state_agent(llm_engine, objects, object_descriptions):
    return PyCallingAgent(
        llm_engine,
        objects=objects,
        object_descriptions=object_descriptions
    )

def test_sort_numbers(state_agent):
    state_agent.run("Sort the numbers list")
    sorted_result = state_agent.get_object('sorted_numbers')
    assert sorted_result == sorted([1, 1, 2, 3, 4, 5, 5, 6, 9])

def test_calculate_sum(state_agent):
    state_agent.run("Calculate the sum of all numbers")
    total = state_agent.get_object('sum_result')
    assert total == 36  # sum of [3,1,4,1,5,9,2,6,5] 