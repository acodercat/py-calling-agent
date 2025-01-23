from py_agent import PyAgent, OpenAILLMEngine
from dataclasses import dataclass

# Initialize LLM engine
llm_engine = OpenAILLMEngine(
    model_id="qwen-coder-plus",
    api_key="sk-8456e73b5a554c40aacc69de607d4ab5",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# Define a class with methods
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

# Prepare context
processor = DataProcessor()
numbers = [3, 1, 4, 1, 5, 9, 2, 6, 5]

variables = {
    'processor': processor,
    'numbers': numbers,
    'processed_data': None,
    'filtered_data': None
}

variables_metadata = {
    'processor': {
        'description': 'Data processing tool with various methods',
        'example': 'result = processor.process_list(numbers)'
    },
    'numbers': {
        'description': 'Input list of numbers',
        'example': 'filtered = processor.filter_numbers(numbers, 5)'
    },
    'processed_data': {
        'description': 'Store processed data here'
    },
    'filtered_data': {
        'description': 'Store filtered data here'
    }
}

# Create agent
agent = PyAgent(
    llm_engine,
    variables=variables,
    variables_metadata=variables_metadata
)

# Process data
agent.run("Use processor to sort and deduplicate numbers")
processed_data = agent.get_object_from_runtime('processed_data')
print("Processed data:", processed_data)

# Filter data
agent.run("Filter numbers greater than 4")
filtered_data = agent.get_object_from_runtime('filtered_data')
print("Filtered data:", filtered_data)