from py_calling_agent import PyCallingAgent, OpenAILLMEngine, LogLevel, Logger
import os
from rich.syntax import Syntax
from rich.console import Console
from rich.text import Text

# Initialize LLM engine
llm_engine = OpenAILLMEngine(
    model_id=os.getenv("LLM_MODEL_ID"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

# Define tools and context
class DataProcessor:
    """A data processor object that can sort lists of numbers"""
    def process(self, data: list) -> list:
        """Sort a list of numbers"""
        return sorted(data)

processor = DataProcessor()

numbers = [3, 1, 4, 1, 5, 9]

objects = {
    'processor': processor,
    'numbers': numbers,
    'result': None
}

object_descriptions = {
    'processor': {
        'description': 'A data processor object that can sort lists of numbers',
        'example': 'result = processor.process([3, 1, 4])'
    },
    'numbers': {
        'description': 'Input list of numbers to be processed',
        'example': 'print(numbers)  # Access the list directly'
    },
    'result': {
        'description': 'Store the result of the processing in this variable.',
        'example': 'result = processor.process([3, 1, 4])'
    }
}

agent = PyCallingAgent(
    llm_engine,
    objects=objects,
    object_descriptions=object_descriptions,
    log_level=LogLevel.ERROR
)

logger = Logger(LogLevel.DEBUG)

console = Console()
logger.info("User Prompt", "Use processor to sort the numbers", 'yellow')
for event in agent.stream("Use processor to sort the numbers"):
    if event.type.name == 'TEXT':
        text = Text(event.content)
        text.stylize("cyan")
        console.print(text, end="", highlight=True)

    if event.type.name == 'CODE':
        logger.debug("Executing Code", Syntax(event.content, "python", theme="monokai"))
    
    if event.type.name == 'EXECUTION_RESULT':
        logger.info("Execution Result", event.content, 'yellow')
    
    if event.type.name == 'EXECUTION_ERROR':
        logger.error("Execution Error", event.content, 'yellow')

print("\n")
logger.info("Runtime State", str({
    'processor': agent.get_object('processor'),
    'numbers': agent.get_object('numbers'),
    'result': agent.get_object('result')
}), 'yellow')
