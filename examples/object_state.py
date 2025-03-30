from py_calling_agent import PyCallingAgent, OpenAILLMEngine
import os

# Initialize LLM engine
llm_engine = OpenAILLMEngine(
    model_id=os.getenv("LLM_MODEL_ID"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

# Define input data and expected outputs
numbers = [3, 1, 4, 1, 5, 9, 2, 6, 5]
objects = {
    'numbers': numbers,
    'sorted_numbers': None,
    'sum_result': None
}

object_descriptions = {
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

# Create agent
agent = PyCallingAgent(
    llm_engine,
    objects=objects,
    object_descriptions=object_descriptions
)

# Sort numbers and get result
agent.run("Sort the numbers list")
sorted_result = agent.get_object('sorted_numbers')
print("Sorted numbers:", sorted_result)

# Calculate sum and get result
agent.run("Calculate the sum of all numbers")
total = agent.get_object('sum_result')
print("Sum:", total) 