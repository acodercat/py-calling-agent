from py_calling_agent import PyCallingAgent, OpenAILLMEngine
import os

# Initialize LLM engine
llm_engine = OpenAILLMEngine(
    model_id=os.getenv("LLM_MODEL_ID"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

# Define data processing class
class DataAnalyzer:
    """A data analyzer that provides statistical analysis for numerical data.
    
    This analyzer calculates basic descriptive statistics including:
    - Minimum value
    - Maximum value
    - Average (mean)
    - Length of data
    
    Example:
        >>> analyzer = DataAnalyzer()
        >>> stats = analyzer.analyze([1, 2, 3, 4, 5])
        >>> print(stats)
        {'min': 1, 'max': 5, 'avg': 3.0, 'len': 5}
    """
    
    def analyze(self, data: list) -> dict:
        """Calculate basic statistical measures for a list of numbers."""
        return {
            'min': min(data),
            'max': max(data),
            'avg': sum(data) / len(data),
            'len': len(data)
        }

# Setup context
analyzer = DataAnalyzer()
numbers = [3, 1, 4, 1, 5, 9, 2, 6, 5]

objects = {
    'analyzer': analyzer,
    'numbers': numbers,
    'stats': None
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

# Create agent
agent = PyCallingAgent(
    llm_engine,
    objects=objects,
    object_descriptions=object_descriptions
)

# Multi-turn conversation
print("Starting analysis conversation...")

# First turn - get basic stats
agent.run("Analyze the numbers")
stats = agent.get_object('stats')
print("\nBasic stats:", stats)

# Second turn - ask about specific stat
result = agent.run("What is the average value in the stats?")
print("\nAverage value:", result)

# Third turn - ask for interpretation
result = agent.run("Is the maximum value (9) significantly higher than the average?")
print("\nInterpretation:", result) 