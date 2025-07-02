from .prompts import DEFAULT_SYSTEM_PROMPT, NEXT_STEP_PROMPT, DEFAULT_INSTRUCTIONS, DEFAULT_ROLE_DEFINITION, DEFAULT_ADDITIONAL_CONTEXT
from .python_runtime import PythonRuntime
from typing import List, Dict, Any, AsyncGenerator
from .models import Model
from rich.console import Console
from rich.text import Text
from rich.style import Style
from .utils import extract_python_code
from .streaming_text_parser import SegmentType, StreamingTextParser
from enum import Enum, IntEnum
from datetime import datetime
class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    CODE_EXECUTION = "code_execution"
    EXECUTION_RESULT = "execution_result"


role_conversions = {
    MessageRole.CODE_EXECUTION: MessageRole.ASSISTANT,
    MessageRole.EXECUTION_RESULT: MessageRole.USER,
}

class Message():
    """Base class for all message types in the agent conversation."""
    def __init__(self, content: str, role: MessageRole):
        self.content = content
        self.role = role
        
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}
    
class SystemMessage(Message):
    """System message that provides instructions to the LLM."""
    def __init__(self, content: str):
        super().__init__(content, MessageRole.SYSTEM)

class UserMessage(Message):
    """Message from the user to the agent."""
    def __init__(self, content: str):
        super().__init__(content, MessageRole.USER)
class AssistantMessage(Message):

    """Message from the assistant (LLM) to the user."""
    def __init__(self, content: str):
        super().__init__(content, MessageRole.ASSISTANT)

class CodeExecutionMessage(Message):
    """Message representing code to be executed by the agent."""
    def __init__(self, content: str):
        super().__init__(content, MessageRole.CODE_EXECUTION)

class ExecutionResultMessage(Message):
    """Message representing the result from code execution."""
    def __init__(self, content: str):
        super().__init__(content, MessageRole.EXECUTION_RESULT)

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
    MAX_STEPS_REACHED = "max_steps_reached"

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
        self.level_styles = {
            LogLevel.DEBUG: Style(color="yellow", bold=False),
            LogLevel.INFO: Style(color="bright_blue", bold=False),
            LogLevel.ERROR: Style(color="bright_red", bold=True)
        }
        
        self.level_prefix = {
            LogLevel.DEBUG: "DEBUG",
            LogLevel.INFO: "INFO",
            LogLevel.ERROR: "ERROR"
        }
    
    def __log(self, title: str, content: Any, style: str, level: LogLevel = LogLevel.INFO):
        if level <= self.level:
            # Create composite log message with improved formatting
            message = Text()

            # Add log level indicator
            message.append(f"[{self.level_prefix[level]}] ", self.level_styles[level])
            
            style = Style.parse(style)
            message.append(f"{title}: \n", style)
            
            message.append(content, style)

            self.console.print(message)

    def debug(self, title: str, content: Any, style: str = "yellow"):
        self.__log(title, content, style, LogLevel.DEBUG)

    def info(self, title: str, content: Any, style: str = "blue"):
        self.__log(title, content, style, LogLevel.INFO)

    def error(self, title: str, content: Any, style: str = "red"):
        self.__log(title, content, style, LogLevel.ERROR)

class ContextState(IntEnum):
    """Execution context state enumeration."""
    INITIALIZED = 0
    RUNNING = 1
    COMPLETED = 2
    MAX_STEPS_REACHED = 3

class ExecutionContext:
    """Manages execution state with max steps limit."""
    
    def __init__(self, max_steps: int = 10):
        self.max_steps = max_steps
        self.total_steps = 0
        self.state = ContextState.INITIALIZED
    
    def start(self) -> None:
        """Initialize execution context."""
        self.total_steps = 0
        self.state = ContextState.RUNNING
    
    def next_step(self) -> bool:
        """Record a step execution. Returns False if max steps reached."""
        if self.total_steps >= self.max_steps:
            self.state = ContextState.MAX_STEPS_REACHED
            return False
        
        self.total_steps += 1
        return True
    
    def complete(self) -> None:
        """Mark execution as completed successfully."""
        self.state = ContextState.COMPLETED
    
    @property
    def is_running(self) -> bool:
        return self.state == ContextState.RUNNING
    
class ExecutionStatus(Enum):
    """Status of agent execution."""
    SUCCESS = "success"
    MAX_STEPS_REACHED = "max_steps_reached"

class Event:
    def __init__(self, type: EventType, content: str):
        self.type = type
        self.content = content

class AgentResponse:
    """Response from the agent."""
    
    def __init__(
        self,
        content: str,
        status: ExecutionStatus,
        steps_taken: int = 0,
        max_steps: int = 0,
    ):
        self.content = content
        self.status = status
        self.steps_taken = steps_taken
        self.max_steps = max_steps
    
    def __str__(self) -> str:
        """String representation of the response."""
        return f"AgentResponse(status={self.status.value}, steps={self.steps_taken}/{self.max_steps}, content={self.content})"

class PyCallingAgent:
    """
    A tool-augmented agent that enables function-calling through LLM code generation.
    
    Instead of JSON schemas, this agent generates Python code to interact with tools
    in a controlled runtime environment. It maintains state across conversations and
    supports streaming responses.

    Args:
        model (Model): LLM model instance implementing the Model interface.
            Supports OpenAIServerModel, LiteLLMModel, or custom implementations.
        system_prompt_template (str, optional): Template string for system prompt.
            Uses placeholders for runtime context. Defaults to DEFAULT_SYSTEM_PROMPT.
        max_steps (int, optional): Maximum execution steps before stopping.
            Prevents infinite loops. Defaults to 5.
        log_level (LogLevel, optional): Logging verbosity level.
            Options: ERROR (0), INFO (1), DEBUG (2). Defaults to DEBUG.
        agent_role (str, optional): Role definition and capabilities description.
            Informs the LLM about the agent's purpose. Defaults to DEFAULT_ROLE_DEFINITION.
        instructions (str, optional): Execution instructions for the agent.
            Guides how the agent should process requests. Defaults to DEFAULT_INSTRUCTIONS.
        additional_context (str, optional): Additional context and usage examples.
            Helps the LLM understand available tools. Defaults to DEFAULT_ADDITIONAL_CONTEXT.
        runtime (PythonRuntime, optional): Python runtime with functions and variables.
            If None, creates an empty runtime. Defaults to None.
        messages (List[Message], optional): Initial conversation history.
            List of Message objects to start with. Defaults to empty list.
        max_history (int, optional): Maximum message history to retain.
            Prevents memory bloat in long conversations. Defaults to 10.

    Example:
        >>> def add(a: int, b: int) -> int:
        ...     return a + b
        >>> 
        >>> agent = PyCallingAgent(
        ...     model=llm_model,
        ...     runtime=PythonRuntime(functions=[Function(add)])
        ... )
        >>> 
        >>> result = await agent.run("Add 5 and 3")
        >>> print(result)  # "The sum is: 8"
    """

    def __init__(
        self,
        model: Model,
        system_prompt_template: str = DEFAULT_SYSTEM_PROMPT,
        max_steps: int = 5,
        log_level: LogLevel = LogLevel.DEBUG,
        agent_role: str = DEFAULT_ROLE_DEFINITION,
        instructions: str = DEFAULT_INSTRUCTIONS,
        additional_context: str = DEFAULT_ADDITIONAL_CONTEXT,
        runtime: PythonRuntime = None,
        messages: List[Message] = [],
        max_history: int = 10
    ):
        """Initialize PyCallingAgent with improved parameter handling."""
        self.model = model
        self.system_prompt_template = system_prompt_template
        self.max_steps = max_steps
        self.runtime = runtime if runtime else PythonRuntime()
        self.agent_role = agent_role
        self.instructions = instructions
        self.additional_context = additional_context
        self.messages = messages.copy()
        self.max_history = max_history
        self.logger = Logger(log_level)

    def build_system_prompt(self) -> str:
        """Build and format the system prompt with current runtime state."""
        return self.system_prompt_template.format(
            functions=self.runtime.describe_functions(), 
            variables=self.runtime.describe_variables(), 
            role_definition=self.agent_role,
            instructions=self.instructions,
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            additional_context=self.additional_context,
        )

    async def run(self, query: str) -> AgentResponse:
        """Execute the agent with the given user query."""
        context = ExecutionContext(self.max_steps)
        context.start()
        self._initialize_conversation(query)

        while context.is_running:
            # Check if we can proceed to next step
            if not context.next_step():
                # Max steps reached
                self.logger.info("Max steps reached", f"Completed {context.total_steps}/{context.max_steps} steps")
                return AgentResponse(
                    content='',
                    status=ExecutionStatus.MAX_STEPS_REACHED,
                    steps_taken=context.total_steps,
                    max_steps=self.max_steps
                )
            
            response = await self._execute_step(context)
            
            if not context.is_running:
                return AgentResponse(
                    content=response,
                    status=ExecutionStatus.SUCCESS,
                    steps_taken=context.total_steps,
                    max_steps=self.max_steps
                )

    async def stream_events(self, query: str) -> AsyncGenerator[Event, None]:
        """Stream events during agent execution."""
        context = ExecutionContext(self.max_steps)
        context.start()
        self._initialize_conversation(query)
        
        while context.is_running:
            # Check if we can proceed to next step
            if not context.next_step():
                # Max steps reached
                self.logger.info("Max steps reached", f"Completed {context.total_steps}/{context.max_steps} steps")
                yield Event(EventType.MAX_STEPS_REACHED, "Max steps reached")
                return
            
            async for event in self._stream_step_execution(context):
                yield event
                
                if not context.is_running:
                    return

    async def _execute_step(self, context: ExecutionContext) -> str:
        """Execute a single step and return result."""
        self._log_step(context)
        
        # Get LLM response
        model_response = await self.model.call(self._prepare_messages())
            
        # Process response
        return await self._process_model_response(model_response, context)

    async def _stream_step_execution(self, context: ExecutionContext) -> AsyncGenerator[Event, None]:
        """Execute a single step with streaming output."""
        self._log_step(context)
        
        # Stream LLM response and collect
        chunks = []
        parser = StreamingTextParser()
        
        async for chunk in self.model.stream(self._prepare_messages()):
            chunks.append(chunk)
            
            # Parse and yield streaming events
            parsed_segments = parser.process_chunk(chunk)
            for segment in parsed_segments:
                if segment.type == SegmentType.TEXT:
                    yield Event(EventType.TEXT, segment.content)
                elif segment.type == SegmentType.CODE:
                    yield Event(EventType.CODE, segment.content)
        
        model_response = "".join(chunks)
        # Process complete response
        async for event in self._process_model_response_streaming(model_response, context):
            yield event

    async def _process_model_response(self, model_response: str, context: ExecutionContext) -> str:
        """Process model response and execute code if needed."""
        code_snippet = extract_python_code(model_response)
        
        if not code_snippet:
            # Final response without code
            self.add_message(AssistantMessage(model_response))
            context.complete()
            return model_response
        
        self.add_message(CodeExecutionMessage(model_response))
            
        try:
            execution_result = await self.runtime.execute(code_snippet)
            self.logger.debug("Code executed", execution_result, "cyan")
            
            next_prompt = NEXT_STEP_PROMPT.format(execution_result=execution_result)
            self.add_message(ExecutionResultMessage(next_prompt))
            
            return model_response
        except Exception as e:
            error_msg = str(e)
            self.logger.debug("Code execution error", error_msg)
            retry_prompt = f"Error: {error_msg}\nPlease fix the code and try again."
            self.add_message(ExecutionResultMessage(retry_prompt))

            return f"Execution failed: {error_msg}"

    async def _process_model_response_streaming(self, model_response: str, 
                                            context: ExecutionContext) -> AsyncGenerator[Event, None]:
        """Process model response with streaming events."""
        code_snippet = extract_python_code(model_response)
        
        if not code_snippet:
            # Final response without code
            self.add_message(AssistantMessage(model_response))
            context.complete()
            yield Event(EventType.FINAL_RESPONSE, model_response)
            return
        
        self.add_message(CodeExecutionMessage(model_response))

        try:
            execution_result = await self.runtime.execute(code_snippet)
            self.logger.debug("Code executed", execution_result, "cyan")
            
            next_prompt = NEXT_STEP_PROMPT.format(execution_result=execution_result)
            self.add_message(ExecutionResultMessage(next_prompt))

            yield Event(EventType.EXECUTION_RESULT, execution_result)
        except Exception as e:
            error_msg = str(e)
            self.logger.debug("Code execution error", error_msg)
            retry_prompt = f"Error: {error_msg}\nPlease fix the code and try again."
            self.add_message(ExecutionResultMessage(retry_prompt))

            yield Event(EventType.EXECUTION_ERROR, error_msg)

    def _log_step(self, context: ExecutionContext) -> None:
        """Log step execution info."""
        self.logger.debug(
            f"Step {context.total_steps}/{context.max_steps}", 
            f"Processing...", 
            "yellow"
        )

    def _initialize_conversation(self, user_query: str) -> None:
        """Initialize the conversation with the user prompt and system prompt."""
        self._update_system_message()
        self.logger.debug("User query received", user_query, "blue")
        self.add_message(UserMessage(user_query))


    def _update_system_message(self) -> None:
        """Update or insert system message."""

        system_prompt = self.build_system_prompt()

        if self.messages and isinstance(self.messages[0], SystemMessage):
            self.messages[0] = SystemMessage(system_prompt)
        else:
            self.messages.insert(0, SystemMessage(system_prompt))
        
        self.logger.debug("System prompt loaded", system_prompt, "blue")

    def _prepare_messages(self) -> List[Dict[str, str]]:
        """Convert internal message objects to dict format for LLM API."""
        return [
            {
                "role": role_conversions.get(message.role, message.role).value,
                "content": message.content
            }
            for message in self.messages
        ]
    
    def add_message(self, message: Message) -> None:
        """Add message with automatic history management."""
        self.messages.append(message)
        self._trim_history()
    
    def _trim_history(self) -> None:
        """Trim message history if needed."""
        if len(self.messages) > self.max_history:
            # Keep system message at index 0 and recent history
            system_msg = self.messages[0]  # Always SystemMessage at index 0
            recent_msgs = self.messages[-(self.max_history - 1):]
            self.messages = [system_msg] + recent_msgs