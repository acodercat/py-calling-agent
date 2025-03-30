# 🤖 PyCallingAgent
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/py-calling-agent.svg?color=%2334D058&label=pypi%20package)](https://pypi.org/project/py-calling-agent)

PyCallingAgent is a tool-augmented agent framework that enables function-calling through LLM code generation and provides runtime state management. Unlike traditional JSON-schema approaches, It leverages LLM's inherent coding capabilities to interact with tools through a Python runtime environment, allowing direct access to execution results and runtime state.

## Features

- **Code-Based Function Calling**: Uses LLM's code generation capabilities instead of JSON schemas
- **Runtime Environment**: 
  - Inject Python objects
  - Register functions as tools
  - Access execution results from runtime
- **Multi-Turn Conversations**: Maintains context and runtime state across multiple interactions
- **Flexible LLM Support**: Works with various LLM providers through a unified interface

## Roadmap

We're actively working on expanding PyCallingAgent's capabilities, including:

- Streaming response support
- Asynchronous execution
- Enhanced test coverage

## Installation

### From PyPI (Recommended)

```bash
pip install py-calling-agent
```

### From Source

```bash
# Clone the repository
git clone https://github.com/acodercat/py-calling-agent.git
cd py-calling-agent
pip install -e .
```

## Example Usage

### Basic Function Calling

```python
from py_calling_agent import PyCallingAgent, OpenAILLMEngine

# Initialize LLM engine
llm_engine = OpenAILLMEngine(
    model_id="your-model",
    api_key="your-api-key",
    base_url="your-base-url"
)

# Define tool functions
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers together"""
    return a * b

# Create agent with functions
agent = PyCallingAgent(
    llm_engine,
    functions=[add, multiply]
)

# Run calculations
result = agent.run("Calculate 5 plus 3")
print("Result:", result)
```

### Object Methods and State Management

```python
from py_calling_agent import PyCallingAgent, OpenAILLMEngine

# Initialize LLM engine
llm_engine = OpenAILLMEngine(
    model_id="your-model",
    api_key="your-api-key",
    base_url="your-base-url"
)

# Define a class with methods
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

objects = {
    'processor': processor,
    'numbers': numbers,
    'processed_data': None,
    'filtered_data': None
}

object_descriptions = {
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

# Create agent
agent = PyCallingAgent(
    llm_engine,
    objects=objects,
    object_descriptions=object_descriptions
)

# Process data
agent.run("Use processor to sort and deduplicate numbers")
processed_data = agent.get_object('processed_data')
print("Processed data:", processed_data)

# Filter data
agent.run("Filter numbers greater than 4")
filtered_data = agent.get_object('filtered_data')
print("Filtered data:", filtered_data)
```
### Streaming Responses

```python
from py_calling_agent import PyCallingAgent, OpenAILLMEngine, LogLevel

# Initialize LLM engine
llm_engine = OpenAILLMEngine(
    model_id="your-model",
    api_key="your-api-key",
    base_url="your-base-url"
)

# Define tool functions
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers"""
    return a + b

# Define data processor class
class DataProcessor:
    def process_list(self, data: list) -> list:
        """Sort a list and remove duplicates"""
        return sorted(set(data))

# Prepare context
processor = DataProcessor()
numbers = [3, 1, 4, 1, 5, 9, 2, 6, 5]

objects = {
    'processor': processor,
    'numbers': numbers,
    'result': None
}

object_descriptions = {
    'processor': {'description': 'Data processing tool'},
    'numbers': {'description': 'Input list of numbers'},
    'result': {
        'description': 'Store results here',
        'example': 'result = processor.process_list(numbers)'
    }
}

# Create agent with streaming support
agent = PyCallingAgent(
    llm_engine,
    objects=objects,
    object_descriptions=object_descriptions,
    functions=[calculate_sum],
    log_level=LogLevel.ERROR
)

# Stream the response in real-time with event type handling
for event in agent.stream("Sort the numbers and calculate sum of the first two elements"):
    
    if event.type.name == 'TEXT':
        print(event.content, end="", flush=True)

    if event.type.name == 'CODE':
        print("Executing Code:", event.content)
    
    if event.type.name == 'EXECUTION_RESULT':
        print("Execution Result:", event.content)
    
    if event.type.name == 'EXECUTION_ERROR':
        print("Execution Error:", event.content)
```


## Advanced Usage

For more examples, check out the [examples](examples) directory:

- [Basic Usage](examples/basic_usage.py): Simple function calling
- [Object State](examples/object_state.py): Managing runtime objects
- [Object Methods](examples/object_methods.py): Using class methods
- [Multi-Turn](examples/multi_turn.py): Complex analysis conversations
- [Stream](examples/stream.py): Streaming responses

## Contributing

Contributions are welcome! Please feel free to submit a PR.
For more details, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.