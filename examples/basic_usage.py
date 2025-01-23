from py_agent import PyAgent, OpenAILLMEngine
import os

# Initialize LLM engine
llm_engine = OpenAILLMEngine(
    model_id=os.getenv("LLM_MODEL_ID"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

# Define some tool functions
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

# Run simple calculations
result = agent.run("Calculate 5 plus 3")
print("Result:", result)

result = agent.run("What is 4 times 6?")
print("Result:", result)

def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers"""
    print(f"Calculating the sum of {a} and {b}")
    return a + b

# Define tools and context
class DataProcessor:
    """A data processor object that can sort lists of numbers"""
    def process(self, data: list) -> list:
        """Sort a list of numbers"""
        return sorted(data)

processor = DataProcessor()

numbers = [3, 1, 4, 1, 5, 9]

variables = {
    'processor': processor,
    'numbers': numbers,
    'result': None
}

variables_metadata = {
    'processor': {
        'description': 'A data processor object that can sort lists of numbers',
        'example': 'result = processor.process([3, 1, 4])'
    },
    'numbers': {
        'description': 'Input list of numbers to be processed',
        'example': 'print(numbers)  # Access the list directly'
    },
    'result': {
        'description': 'Store the result of the processing in this variable.'
    }
}

# Create agent with injected variables and metadata
agent = PyAgent(
    llm_engine,
    functions=[calculate_sum],
    variables=variables,
    variables_metadata=variables_metadata
)

# Run task using injected variables
agent.run("Use processor to sort the numbers")

# Retrieve results from Python environment
sorted_result = agent.get_object_from_runtime('result')
print(sorted_result)  # [1, 1, 3, 4, 5, 9]
