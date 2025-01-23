# PyAgent

PyAgent is a tool-augmented agent framework that enables function-calling through LLM code generation and provides runtime state management. Unlike traditional JSON-schema approaches, PyAgent leverages LLM's coding capabilities to interact with tools through a Python runtime environment, allowing direct access to execution results and runtime state.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/py-agent.svg)](https://badge.fury.io/py/py-agent)

## Features

- **Code-Based Function Calling**: Uses LLM's code generation capabilities instead of JSON schemas
- **Rich Runtime Environment**: 
  - Inject Python objects and variables
  - Register functions as tools
  - Access execution results from runtime
- **Multi-Turn Conversations**: Maintains context and state across interactions
- **Flexible LLM Support**: Works with various LLM providers through a unified interface

## Roadmap

We're actively working on expanding PyAgent's capabilities, including:
- Streaming response support
- Asynchronous execution
- Enhanced test coverage

## Installation

### From PyPI (Recommended)
```bash
pip install py-agent
```

### From Source
```bash
# Clone the repository
git clone https://github.com/acodercat/PyAgent.git
cd py-agent
# Or install in development mode with pip
pip install -e .
```

## Quick Start

### Basic Function Calling

```python
from py_agent import PyAgent, OpenAILLMEngine

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
agent = PyAgent(
    llm_engine,
    functions=[add, multiply]
)

# Run calculations
result = agent.run("Calculate 5 plus 3")
print("Result:", result)
```

### Object Methods and State Management

```python
from py_agent import PyAgent, OpenAILLMEngine
from dataclasses import dataclass

# Initialize LLM engine
llm_engine = OpenAILLMEngine(
    model_id="your-model",
    api_key="your-api-key",
    base_url="your-base-url"
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
```

## Advanced Usage

For more examples, check out the [examples](examples) directory:

- [Basic Usage](examples/basic_usage.py): Simple function calling
- [Variable State](examples/variable_state.py): Managing runtime variables
- [Object Methods](examples/object_methods.py): Using class methods
- [Multi-Turn](examples/multi_turn.py): Complex analysis conversations

## Contributing

Contributions are welcome! Please feel free to submit a PR.
For more details, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
