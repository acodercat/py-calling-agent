from enum import Enum
from typing import List

class SegmentType(Enum):
    """Types of content segments."""
    TEXT = "text"
    CODE = "code"

class Segment:
    """Represents a parsed content segment."""
    
    def __init__(self, type: SegmentType, content: str):
        self.type = type
        self.content = content

class StreamingTextParser:
    """Parser for streaming text that identifies Python code blocks."""
    
    class Mode(Enum):
        TEXT = "text"
        BACKTICK_COUNT = "backtick_count"
        LANGUAGE_MATCH = "language_match" 
        CODE = "code"
        CODE_END_CHECK = "code_end_check"
    
    def __init__(self, python_block_identifier: str = "python"):
        """Initialize the parser with clean state."""
        self.mode = self.Mode.TEXT
        self.text_buffer = ""
        self.code_buffer = ""
        self.backtick_count = 0
        self.language_match_buffer = ""
        self.in_code_block = False
        self.python_block_identifier = python_block_identifier
        self.pending_backticks = ""
        
    def process_chunk(self, chunk: str) -> List[Segment]:
        """
        Process a chunk of streaming text.
        
        Args:
            chunk: Text chunk to process
            
        Returns:
            List of parsed segments
        """
        parsed_segments = []
        
        for char in chunk:
            segments = self._process_character(char)
            parsed_segments.extend(segments)
        
        return parsed_segments
    
    def flush(self) -> List[Segment]:
        """
        Flush all buffers and return remaining segments.
        Should be called when the stream ends.
        
        Returns:
            List of remaining parsed segments
        """
        segments = []
        
        if self.in_code_block:
            if self.code_buffer:
                segments.append(Segment(SegmentType.CODE, self.code_buffer.strip()))
            warning_text = "\n[Warning: Unclosed code block]"
            segments.append(Segment(SegmentType.TEXT, warning_text))
        
        if self.mode == self.Mode.BACKTICK_COUNT:
            self.text_buffer += "`" * self.backtick_count
        elif self.mode == self.Mode.LANGUAGE_MATCH:
            self.text_buffer += "```" + self.language_match_buffer
        elif self.mode == self.Mode.CODE_END_CHECK:
            self.code_buffer += "`" * self.backtick_count
            if self.code_buffer:
                segments.append(Segment(SegmentType.CODE, self.code_buffer.strip()))
        
        if self.text_buffer:
            segments.append(Segment(SegmentType.TEXT, self.text_buffer))
        
        # Reset state
        self._reset_state()
        
        return segments
    
    def _reset_state(self):
        """Reset parser to initial state."""
        self.mode = self.Mode.TEXT
        self.text_buffer = ""
        self.code_buffer = ""
        self.backtick_count = 0
        self.language_match_buffer = ""
        self.in_code_block = False
        self.pending_backticks = ""
    
    def _process_character(self, char: str) -> List[Segment]:
        """Process a single character and return any completed segments."""
        segments = []
        
        if self.mode == self.Mode.TEXT:
            segments.extend(self._handle_text_mode(char))
        elif self.mode == self.Mode.BACKTICK_COUNT:
            segments.extend(self._handle_backtick_count_mode(char))
        elif self.mode == self.Mode.LANGUAGE_MATCH:
            segments.extend(self._handle_language_match_mode(char))
        elif self.mode == self.Mode.CODE:
            segments.extend(self._handle_code_mode(char))
        elif self.mode == self.Mode.CODE_END_CHECK:
            segments.extend(self._handle_code_end_check_mode(char))
        
        return segments
    
    def _handle_text_mode(self, char: str) -> List[Segment]:
        """Handle character in TEXT mode."""
        if char == '`':
            self.mode = self.Mode.BACKTICK_COUNT
            self.backtick_count = 1
        else:
            self.text_buffer += char
        return []
    
    def _handle_backtick_count_mode(self, char: str) -> List[Segment]:
        """Handle character in BACKTICK_COUNT mode."""
        segments = []
        
        if char == '`':
            self.backtick_count += 1
            if self.backtick_count == 3:
                # Three backticks - possibly a code block
                if self.text_buffer:
                    segments.append(Segment(SegmentType.TEXT, self.text_buffer))
                    self.text_buffer = ""
                self.mode = self.Mode.LANGUAGE_MATCH
                self.language_match_buffer = ""
                self.backtick_count = 0
        else:
            # Not a consecutive backtick - add to text buffer
            self.text_buffer += "`" * self.backtick_count + char
            self.mode = self.Mode.TEXT
            self.backtick_count = 0
        
        return segments
    
    def _handle_language_match_mode(self, char: str) -> List[Segment]:
        """Handle character in LANGUAGE_MATCH mode."""
        segments = []
        
        # Check if it matches the language identifier
        if len(self.language_match_buffer) < len(self.python_block_identifier):
            if char == self.python_block_identifier[len(self.language_match_buffer)]:
                self.language_match_buffer += char
                
                # Fully matches the language identifier
                if self.language_match_buffer == self.python_block_identifier:
                    # Continue reading until a newline
                    pass  # The next character will be processed
            elif char == '\n' and self.language_match_buffer == self.python_block_identifier:
                # Match successful, enter code mode
                self._enter_code_block()
            else:
                # Not a match - this is not the code block we're looking for
                self.text_buffer += "```" + self.language_match_buffer + char
                self.mode = self.Mode.TEXT
                self.language_match_buffer = ""
        else:
            # Already matched the language identifier, check the next character
            if char == '\n' or char == ' ' or char == '\r':
                # Valid code block start
                self._enter_code_block()
                if char == '\n':
                    pass  # Do not add a newline to the code buffer
                elif char == ' ':
                    # Ignore the space after the language identifier
                    pass
            else:
                # Not a valid code block (e.g. ```pythonscript)
                self.text_buffer += "```" + self.language_match_buffer + char
                self.mode = self.Mode.TEXT
                self.language_match_buffer = ""
        
        return segments
    
    def _handle_code_mode(self, char: str) -> List[Segment]:
        """Handle character in CODE mode."""
        if char == '`':
            self.mode = self.Mode.CODE_END_CHECK
            self.backtick_count = 1
        else:
            self.code_buffer += char
        return []
    
    def _handle_code_end_check_mode(self, char: str) -> List[Segment]:
        """Check if we're at the end of a code block."""
        segments = []
        
        if char == '`':
            self.backtick_count += 1
            if self.backtick_count == 3:
                # Code block end
                if self.code_buffer:
                    segments.append(Segment(SegmentType.CODE, self.code_buffer.strip()))
                    self.code_buffer = ""
                self._exit_code_block()
        else:
            # Not a code block end - add backticks to the code buffer
            self.code_buffer += "`" * self.backtick_count + char
            self.mode = self.Mode.CODE
            self.backtick_count = 0
        
        return segments
    
    def _enter_code_block(self):
        """Enter code block mode."""
        self.in_code_block = True
        self.mode = self.Mode.CODE
        self.language_match_buffer = ""
    
    def _exit_code_block(self):
        """Exit code block mode."""
        self.in_code_block = False
        self.mode = self.Mode.TEXT
        self.backtick_count = 0