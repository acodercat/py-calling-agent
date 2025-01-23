from py_agent import PyAgent, OpenAILLMEngine

# Initialize LLM engine
llm_engine = OpenAILLMEngine(
    model_id="qwen-coder-plus",
    api_key="sk-8456e73b5a554c40aacc69de607d4ab5",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
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

variables = {
    'analyzer': analyzer,
    'numbers': numbers,
    'stats': None
}

variables_metadata = {
    'analyzer': {
        'description': 'Tool for analyzing numerical data',
        'example': 'stats = analyzer.analyze(numbers)'
    },
    'numbers': {
        'description': 'Input data to analyze',
        'example': 'print(numbers)'
    },
    'stats': {
        'description': 'Store analysis results here'
    }
}

# Create agent
agent = PyAgent(
    llm_engine,
    variables=variables,
    variables_metadata=variables_metadata
)

# Multi-turn conversation
print("Starting analysis conversation...")

# First turn - get basic stats
agent.run("Analyze the numbers")
stats = agent.get_object_from_runtime('stats')
print("\nBasic stats:", stats)

# Second turn - ask about specific stat
result = agent.run("What is the average value in the stats?")
print("\nAverage value:", result)

# Third turn - ask for interpretation
result = agent.run("Is the maximum value (9) significantly higher than the average?")
print("\nInterpretation:", result) 