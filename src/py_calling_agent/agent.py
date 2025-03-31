from py_calling_agent.prompts import DEFAULT_SYSTEM_PROMPT, DEFAULT_NEXT_STEP_PROMPT, DEFAULT_INSTRUCTIONS, DEFAULT_ROLE_DEFINITION, DEFAULT_EXAMPLES
from py_calling_agent.python_runtime import PythonRuntime
from typing import Callable, Optional, List, Dict, Any, Generator, Tuple
from py_calling_agent.llm import LLMEngine
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from py_calling_agent.utils import extract_python_code, process_streaming_text, StreamingParserState
import inspect
from enum import Enum, IntEnum
from datetime import datetime

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    CODE_EXECUTION = "code_execution"
    EXECUTION_RESULT = "execution_result"

class Message:
    """Base class for all message types in the agent conversation."""
    def __init__(self, content: str):
        self.content = content
        
    def to_dict(self) -> Dict[str, str]:
        """Convert message to dictionary format for LLM API."""
        raise NotImplementedError("Subclasses must implement to_dict()")

class SystemMessage(Message):
    """System message that provides instructions to the LLM."""
    def to_dict(self) -> Dict[str, str]:
        return {"role": MessageRole.SYSTEM, "content": self.content}


class UserMessage(Message):
    """Message from the user to the agent."""
    def to_dict(self) -> Dict[str, str]:
        return {"role": MessageRole.USER, "content": self.content}

class AssistantMessage(Message):
    """Message from the assistant (LLM) to the user."""
    def to_dict(self) -> Dict[str, str]:
        return {"role": MessageRole.ASSISTANT, "content": self.content}


class CodeExecutionMessage(Message):
    """Message representing code to be executed by the agent."""
    def to_dict(self) -> Dict[str, str]:
        return {"role": MessageRole.CODE_EXECUTION, "content": self.content}


class ExecutionResultMessage(Message):
    """Message representing the result from code execution."""
    def to_dict(self) -> Dict[str, str]:
        return {"role": MessageRole.EXECUTION_RESULT, "content": self.content}


class LogLevel(IntEnum):
    """Log levels for controlling output verbosity."""
    ERROR = 0  # Only errors
    INFO = 1   # Normal output
    DEBUG = 2  # Detailed output

class EventType(Enum):
    TEXT = "text"
    CODE = "code"
    EXECUTION_RESULT = "execution_result"
    EXECUTION_ERROR = "execution_error"
    FINAL_RESPONSE = "final_response"

class Event:
    def __init__(self, type: EventType, content: str):
        self.type = type
        self.content = content

class AgentState(IntEnum):
    """Agent state enumeration."""
    INITIALIZED = 0
    RUNNING = 1
    COMPLETED = 2
    ERROR = 3
    MAX_STEPS_REACHED = 4

class Logger:
    """
    A structured logger for Agent that provides leveled logging with rich formatting.
    
    Handles different types of log messages (debug, info, error) with customizable 
    styling and visibility levels. Uses rich library for enhanced console output.

    Log Levels:
    - ERROR (0): Only critical errors
    - INFO (1): Standard operation information
    - DEBUG (2): Detailed execution traces
    """

    def __init__(self, level: LogLevel = LogLevel.INFO):
        """Initialize logger with specified verbosity level."""
        self.console = Console()
        self.level = level

    def __log(self, title: str, content: str = None, style: str = None, level: LogLevel = LogLevel.INFO):
        """Internal method to handle log message formatting and display."""
        if level <= self.level:
            panel = Panel(content, title=title, style=style)
            self.console.print(panel)

    def debug(self, title: str, message: str, style: str = "yellow"):
        self.__log(title, message, style, LogLevel.DEBUG)

    def info(self, title: str, message: str, style: str = "blue"):
        self.__log(title, message, style, LogLevel.INFO)

    def error(self, title: str, message: str, style: str = "red"):
        self.__log(title, message, style, LogLevel.ERROR)


class SystemPromptFormatter:
    """
    Formats the system prompt by injecting descriptions of available functions, objects, and libraries.
    
    This formatter structures information about the Python runtime environment into a format
    that helps the LLM understand what tools and capabilities are available for use.

    Key responsibilities:
    - Format function descriptions with signatures and docstrings
    - Format object descriptions with types, metadata, and examples
    - Format available library information
    - Include role definition, instructions, and additional context
    
    Example:
        >>> formatter = SystemPromptFormatter(
        ...     system_prompt_template="Functions:\n{functions}\nObjects:\n{objects}\nLibraries:\n{libraries}",
        ...     object_descriptions={
        ...         'data': {'description': 'Input data', 'example': 'print(data)'}
        ...     },
        ...     functions=[sort_list],
        ...     objects={'data': [3,1,4]},
        ...     libraries=['numpy', 'pandas'],
        ...     role_definition="You are a data analyst",
        ...     instructions="Analyze the data",
        ...     current_time="2023-05-01 12:00:00",
        ...     additional_context="This is a test"
        ... )
        >>> formatted_prompt = formatter.format()
    """

    def __init__(self, 
        system_prompt_template: str, 
        object_descriptions: Dict[str, Dict[str, str]], 
        functions: List[Callable], 
        objects: Dict[str, Any], 
        libraries: List[str],
        role_definition: str,
        current_time: str,
        instructions: str,
        additional_context: str,
        examples: str,
    ):
        """Initialize the formatter with runtime environment information."""
        self.system_prompt_template = system_prompt_template
        self.object_descriptions = object_descriptions
        self.functions = functions
        self.objects = objects
        self.libraries = libraries
        self.role_definition = role_definition
        self.instructions = instructions
        self.additional_context = additional_context
        self.current_time = current_time
        self.examples = examples
    
    def format(self) -> str:
        """Format system prompt with functions, objects and libraries descriptions."""
        functions_description = self._format_functions()
        objects_description = self._format_objects()
        libraries_description = self._format_libraries()
        return self.system_prompt_template.format(
            functions=functions_description, 
            objects=objects_description,
            libraries=libraries_description,
            role_definition=self.role_definition,
            instructions=self.instructions,
            current_time=self.current_time,
            additional_context=self.additional_context,
            examples=self.examples
        )
    
    def _format_functions(self) -> str:
        """Format description of functions with signatures and docstrings."""
        descriptions = [
            f"Function: {func.__name__}{inspect.signature(func)}\n"
            f"Description: {func.__doc__ or f'Function {func.__name__}'}"
            for func in self.functions
        ]
        return "\n".join(descriptions) if descriptions else "No functions available"
    
    def _format_objects(self) -> str:
        """Format description of objects with their metadata."""
        descriptions = []
        
        for name, value in self.objects.items():
            object_info = [f"- {name} ({type(value).__name__}):"]
            
            if meta := self.object_descriptions.get(name, {}):
                if desc := meta.get("description"):
                    object_info.append(f"  Description: {desc}")
                if example := meta.get("example"): 
                    object_info.append(f"  Example usage: {example}")
                    
            if hasattr(value, "__doc__") and value.__doc__ and value.__doc__.strip():
                doc = value.__doc__.strip()
                object_info.append(f"  Documentation: {doc}")
                
            descriptions.append("\n".join(object_info))

        return "\n".join(descriptions) if descriptions else "No objects available"
    
    def _format_libraries(self) -> str:
        """Format description of libraries."""
        return "\n".join(self.libraries) if self.libraries else "No libraries available"

class ChunkType(Enum):
    """Types of chunks that can be parsed from LLM streaming response."""
    
    TEXT = "text"
    CODE = "code"
    COMPLETE = "complete"

class ResponseChunk:
    """Represents a parsed chunk from the LLM streaming response."""
    
    def __init__(self, type, content):
        self.type = type
        self.content = content

class PyCallingAgent:
    """
    A tool-augmented agent framework that enables function-calling through LLM code generation.
    
    Unlike traditional JSON-schema approaches, Agent leverages LLM's coding capabilities 
    to interact with tools through a Python runtime environment. It follows an 
    observation-planning-action pattern and allows object injection and retrieval.

    Key features:
    - Code-based function calling instead of JSON schemas
    - Direct Python object injection into runtime
    - Multi-turn conversation with observation feedback
    - Runtime state management and result retrieval
    - Dynamic system prompt management with customizable sections
    
    Example:
        >>> # Define a tool and data to process
        >>> def sort_list(data: list) -> list:
        ...     '''Sort a list of numbers'''
        ...     return sorted(data)
        ...
        >>> numbers = [3, 1, 4]
        >>> 
        >>> # Create agent with injected function and object
        >>> agent = PyCallingAgent(
        ...     llm_engine,
        ...     functions=[sort_list],
        ...     objects={'numbers': numbers},
        ...     object_descriptions={
        ...         'numbers': {
        ...             'description': 'Input list to sort',
        ...             'example': 'result = sort_list(numbers)'
        ...         },
        ...         'sorted_result': {
        ...             'description': 'Store the result of the sorting in this object.'
        ...         }
        ...     }
        ... )
        >>> 
        >>> # Run task and get sorted_result from runtime
        >>> agent.run("Sort the numbers and store as 'sorted_result'")
        >>> result = agent.get_object('sorted_result')
    """

    def __init__(
        self,
        llm_engine: LLMEngine,
        system_prompt_template: str = DEFAULT_SYSTEM_PROMPT,
        functions: List[Callable] = [],
        libraries: List[str] = [],
        objects: Dict[str, Any] = {},
        object_descriptions: Dict[str, Dict[str, str]] = None,
        max_steps: int = 5,
        log_level: LogLevel = LogLevel.DEBUG,
        next_step_prompt_template: str = DEFAULT_NEXT_STEP_PROMPT,
        initial_code: str = None,
        agent_role: str = DEFAULT_ROLE_DEFINITION,
        task_instructions: str = DEFAULT_INSTRUCTIONS,
        additional_context: str = None,
        examples: str = DEFAULT_EXAMPLES,
    ):
        """Initialize a new Agent instance."""
        self.llm_engine = llm_engine
        self.system_prompt_template = system_prompt_template
        self.next_step_prompt_template = next_step_prompt_template
        self.python_runtime = PythonRuntime(functions, objects)
        if initial_code:
            self.python_runtime.run(initial_code)
        self.max_steps = max_steps
        
        self.system_prompt_formatter = SystemPromptFormatter(
            system_prompt_template=self.system_prompt_template, 
            object_descriptions=object_descriptions, 
            functions=functions, 
            objects=objects, 
            libraries=libraries, 
            role_definition=agent_role, 
            instructions=task_instructions, 
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            additional_context=additional_context,
            examples=examples
        )
        self.system_prompt = self.system_prompt_formatter.format()
        
        self.messages = [SystemMessage(self.system_prompt)]
        
        self.__state = AgentState.INITIALIZED
        self.logger = Logger(log_level)
    
    def run(self, query: str) -> str:
        """Execute the agent with the given user query."""
        self._initialize_conversation(query)
        
        for step in range(self.max_steps):
            self.logger.debug(f"Step {step + 1}/{self.max_steps}", "Processing...", "yellow")
            result = self._execute_step()
            if result:
                return result
        
        return self._handle_max_steps()

    def stream(self, query: str) -> Generator[Event, None, None]:
        """Stream events during agent execution."""
        self._initialize_conversation(query)
        
        for step in range(self.max_steps):
            self.logger.debug(f"Step {step + 1}/{self.max_steps}", "Processing...", "yellow")
            
            for event in self._stream_step():
                if event:  # Filter out None events
                    yield event
                if self.__state == AgentState.COMPLETED:
                    return
        
        # Handle reaching max steps
        final_response = self._handle_max_steps()
        yield Event(EventType.FINAL_RESPONSE, final_response)
    
    def get_messages(self) -> List[Message]:
        """Get the message history."""
        return self.messages

    def get_state(self) -> AgentState:
        """Get the current state of the agent."""
        return self.__state

    def _process_llm_response(self, response: str):
        """Process an LLM response and determine if it contains executable code."""
        code_snippet = extract_python_code(response)
        
        if not code_snippet:
            self.logger.debug("Final Response", response, "green")
            self.__state = AgentState.COMPLETED
            self.messages.append(AssistantMessage(response))
        else:
            self.logger.debug("LLM Response", response, "magenta")
            self.messages.append(CodeExecutionMessage(response))
            
        return code_snippet

    def _handle_max_steps(self):
        """Handle the case when maximum steps are reached."""
        final_response = f"Max steps ({self.max_steps}) reached. Last response: {self.messages[-1].content}"
        self.logger.debug("Warning", final_response, "red")
        self.__state = AgentState.MAX_STEPS_REACHED
        self.messages.append(AssistantMessage(final_response))
        return final_response

    def _execute_step(self) -> Optional[str]:
        """Execute a single step of the workflow and return final response if complete."""
        # Phase 1: Get LLM response and check if it's a final response
        initial_response = self.llm_engine(self._prepare_messages_for_llm())
        code_snippet = self._process_llm_response(initial_response)
        
        if self.__state == AgentState.COMPLETED:
            return initial_response
        
        # Phase 2: Execute code
        try:
            execution_result = self._execute_code(code_snippet)
        except Exception as e:
            execution_result = str(e)

        self.messages.append(ExecutionResultMessage(execution_result))
        
        return None  # Continue to next step

    def _stream_step(self) -> Generator[Optional[Event], None, None]:
        """Execute a streaming step and yield events with a flag indicating completion."""
        # Phase 1: Get initial LLM response and stream events
        initial_response = None
        for chunk in self._stream_llm_parsed_chunks():
            if chunk.type == ChunkType.CODE:
                yield Event(EventType.CODE, chunk.content)
            elif chunk.type == ChunkType.TEXT:
                yield Event(EventType.TEXT, chunk.content)
            elif chunk.type == ChunkType.COMPLETE:
                initial_response = chunk.content
        
        # Process the complete response
        code_snippet = self._process_llm_response(initial_response)
        
        if self.__state == AgentState.COMPLETED:
            yield Event(EventType.FINAL_RESPONSE, initial_response)
            return
        
        # Phase 2: Execute code and stream results
        try:
            execution_result = self._execute_code(code_snippet)
            yield Event(EventType.EXECUTION_RESULT, execution_result or "No output")
        except Exception as e:
            execution_result = str(e)
            yield Event(EventType.EXECUTION_ERROR, execution_result)  

        self.messages.append(ExecutionResultMessage(execution_result))
        
        yield None  # Continue to next step

    def _stream_llm_parsed_chunks(self):
        """Stream parsed chunks from LLM response."""
        parser_state = StreamingParserState()
        raw_chunks = []
        
        for raw_chunk in self.llm_engine.stream(self._prepare_messages_for_llm()):
            raw_chunks.append(raw_chunk)

            parsed_data, parser_state = process_streaming_text(raw_chunk, parser_state)
            for item in parsed_data:
                if item["type"] == "text":
                    yield ResponseChunk(ChunkType.TEXT, item["content"])
                elif item["type"] == "code":
                    yield ResponseChunk(ChunkType.CODE, item["content"])                    
        # Yield the complete response as final chunk
        yield ResponseChunk(ChunkType.COMPLETE, "".join(raw_chunks))

    def _prepare_messages_for_llm(self):
        """Convert internal message objects to dict format for LLM API."""
        converted_messages = []
        
        for message in self.messages:
            match message:
                case SystemMessage():
                    role = "system"
                case AssistantMessage():
                    role = "assistant"
                case UserMessage() | CodeExecutionMessage() | ExecutionResultMessage():
                    role = "user"
                case _:
                    continue
                    
            converted_messages.append({"role": role, "content": message.content})
                
        return converted_messages

    def _initialize_conversation(self, query: str):
        """Initialize the conversation with the user prompt."""
        self.__state = AgentState.RUNNING
        self.logger.debug("System Prompt", self.system_prompt, "blue")
        self.logger.debug("User query", query, "blue")
        self.messages.append(UserMessage(query))

    def _execute_code(self, code_snippet: str) -> str:
        """Execute code and handle errors."""
        self.logger.debug("Executing Code", Syntax(code_snippet, "python", theme="monokai"))
        
        try:
            result = self.python_runtime.run(code_snippet)
            self.logger.debug("Execution Result", result or "No output", "cyan")
            return result
        except Exception as e:
            error_msg = f"Error executing code: {str(e)}"
            self.logger.error("Execution Error", error_msg)
            raise Exception(error_msg)

    def get_object(self, name: str) -> Any:
        """Get an object from the agent's runtime environment."""
        return self.python_runtime.get_from_namespace(name)