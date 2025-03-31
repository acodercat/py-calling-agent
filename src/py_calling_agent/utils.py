import re
from typing import Union, Tuple, List, Dict
from enum import Enum, auto

def extract_python_code(response) -> Union[str, None]:
    """Extract python code block from LLM output"""
    pattern = r'```(?i:python)\n(.*?)```'
    matches = re.findall(pattern, response, re.DOTALL)
    return "\n\n".join(match.strip() for match in matches)

class StreamingParserState:
    """
    Represents the current state of text stream processing.
    
    This class tracks the state machine for parsing Python code blocks 
    from streaming text input.
    """
    # State machine constants
    class Mode(Enum):
        TEXT = auto()               # Processing regular text
        CODE = auto()               # Inside code block
        BACKTICK_COUNT = auto()     # Counting backticks
        PYTHON_MATCH = auto()       # Matching "python" after backticks
    
    def __init__(self):
        """Initialize a new streaming state."""
        self.mode = self.Mode.TEXT
        self.text_buffer = ""
        self.code_buffer = ""
        self.backtick_count = 0
        self.python_match_progress = ""  # Tracks how much of "python" we've matched
        self.in_code_block = False
    
    def reset_backtick_count(self):
        """Reset backtick counter and return to previous mode."""
        self.backtick_count = 0
        if self.in_code_block:
            self.mode = self.Mode.CODE
        else:
            self.mode = self.Mode.TEXT
    
    def complete_python_match(self):
        """Handle completion of "python" match after backticks."""
        self.mode = self.Mode.CODE
        self.in_code_block = True
        self.python_match_progress = ""
    
    def exit_code_block(self):
        """Exit code block mode."""
        self.mode = self.Mode.TEXT
        self.in_code_block = False
        # In case there are more backticks in the text immediately after
        self.backtick_count = 0 


def process_streaming_text(chunk: str, state: StreamingParserState) -> Tuple[List[Dict[str, str]], StreamingParserState]:
    """Process streaming text to identify Python code blocks."""
    
    events = []
    
    # Process the chunk character by character
    for char in chunk:
        # Handle different states of the state machine
        if state.mode == StreamingParserState.Mode.TEXT:
            if char == '`':
                state.mode = StreamingParserState.Mode.BACKTICK_COUNT
                state.backtick_count = 1
            else:
                state.text_buffer += char
                
        elif state.mode == StreamingParserState.Mode.BACKTICK_COUNT:
            if char == '`':
                state.backtick_count += 1
                if state.backtick_count == 3:
                    # We've reached three backticks
                    if state.in_code_block:
                        # End of code block
                        events.append({
                            "type": "code",
                            "content": state.code_buffer.strip()
                        })
                        state.code_buffer = ""
                        state.exit_code_block()
                    else:
                        # Potential start of code block - now check for "python"
                        # First emit any accumulated text
                        if state.text_buffer:
                            events.append({
                                "type": "text",
                                "content": state.text_buffer
                            })
                            state.text_buffer = ""
                        state.mode = StreamingParserState.Mode.PYTHON_MATCH
                        state.python_match_progress = ""
            else:
                # Not a sequence of backticks - add to appropriate buffer
                buffer_content = "`" * state.backtick_count + char
                if state.in_code_block:
                    state.code_buffer += buffer_content
                else:
                    state.text_buffer += buffer_content
                state.reset_backtick_count()
                
        elif state.mode == StreamingParserState.Mode.PYTHON_MATCH:
            expected_sequence = "python"
            current_pos = len(state.python_match_progress)
            
            if current_pos < len(expected_sequence) and char == expected_sequence[current_pos]:
                # Match the next character in "python"
                state.python_match_progress += char
                if state.python_match_progress == expected_sequence:
                    # Complete match - we're now in a code block
                    state.complete_python_match()
            else:
                # Not a match for "python" - revert to text mode
                state.text_buffer += "```" + state.python_match_progress + char
                state.mode = StreamingParserState.Mode.TEXT
                state.python_match_progress = ""
                
        elif state.mode == StreamingParserState.Mode.CODE:
            if char == '`':
                state.mode = StreamingParserState.Mode.BACKTICK_COUNT
                state.backtick_count = 1
            else:
                state.code_buffer += char
    
    if state.mode == StreamingParserState.Mode.TEXT and state.text_buffer:
        events.append({
            "type": "text",
            "content": state.text_buffer
        })
        state.text_buffer = ""
    
    return events, state

