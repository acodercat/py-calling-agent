from py_agent import PyAgent, OpenAILLMEngine

# Initialize LLM engine
llm_engine = OpenAILLMEngine(
    model_id="qwen-coder-plus",
    api_key="sk-8456e73b5a554c40aacc69de607d4ab5",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# Define input data and expected outputs
numbers = [3, 1, 4, 1, 5, 9, 2, 6, 5]
variables = {
    'numbers': numbers,  # Input data
    'sorted_numbers': None,
    'sum_result': None
}

variables_metadata = {
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

# Create agent
agent = PyAgent(
    llm_engine,
    variables=variables,
    variables_metadata=variables_metadata
)

# Sort numbers and get result
agent.run("Sort the numbers list")
sorted_result = agent.get_object_from_runtime('sorted_numbers')
print("Sorted numbers:", sorted_result)

# Calculate sum and get result
agent.run("Calculate the sum of all numbers")
total = agent.get_object_from_runtime('sum_result')
print("Sum:", total) 