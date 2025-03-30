import pytest
from dataclasses import dataclass
from py_calling_agent import PyCallingAgent

@dataclass
class DataProcessor:
    """A utility class for processing and filtering data collections.
    
    This class provides methods for basic data processing operations such as
    sorting, removing duplicates, and filtering based on thresholds.
    
    Example:
        >>> processor = DataProcessor()
        >>> processor.process_list([3, 1, 2, 1, 3])
        [1, 2, 3]
        >>> processor.filter_numbers([1, 5, 3, 8, 2], 4)
        [5, 8]
    """
    def process_list(self, data: list) -> list:
        """Sort a list and remove duplicates"""
        return sorted(set(data))
    
    def filter_numbers(self, data: list, threshold: int) -> list:
        """Filter numbers greater than threshold"""
        return [x for x in data if x > threshold]
    
@pytest.fixture
def processor():
    return DataProcessor()

@pytest.fixture
def numbers():
    return [3, 1, 4, 1, 5, 9, 2, 6, 5]

@pytest.fixture
def objects(processor, numbers):
    return {
        'processor': processor,
        'numbers': numbers,
        'processed_data': None,
        'filtered_data': None
    }

@pytest.fixture
def object_descriptions():
    return {
        'processor': {
            'description': 'Data processing tool with various methods',
            'example': 'processed_data = processor.process_list(numbers)'
        },
        'numbers': {
            'description': 'Input list of numbers',
            'example': 'filtered_data = processor.filter_numbers(numbers, 5)'
        },
        'processed_data': {
            'description': 'Store processed data in this variable',
            'example': 'processed_data = processor.process_list(numbers)'
        },
        'filtered_data': {
            'description': 'Store filtered data in this variable',
            'example': 'filtered_data = processor.filter_numbers(numbers, 5)'
        }
    }

@pytest.fixture
def object_agent(llm_engine, objects, object_descriptions):
    return PyCallingAgent(
        llm_engine,
        objects=objects,
        object_descriptions=object_descriptions
    )

def test_process_and_deduplicate(object_agent):
    object_agent.run("Use processor to sort and deduplicate numbers")
    processed_data = object_agent.get_object('processed_data')
    assert processed_data == [1, 2, 3, 4, 5, 6, 9]

def test_filter_numbers(object_agent):
    object_agent.run("Filter numbers greater than 4")
    filtered_data = object_agent.get_object('filtered_data')
    assert filtered_data == [5, 9, 6, 5] 