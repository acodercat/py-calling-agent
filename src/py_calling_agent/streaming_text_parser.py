from enum import Enum
from typing import List


PYTHON_BLOCK_IDENTIFIER = "py_calling"

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
        PYTHON_MATCH = "python_match" 
        CODE = "code"
    
    def __init__(self):
        """Initialize the parser with clean state."""
        self.mode = self.Mode.TEXT
        self.text_buffer = ""
        self.code_buffer = ""
        self.backtick_count = 0
        self.python_match_progress = ""
        self.in_code_block = False
        self.skip_next_triple_backtick = False

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
        
        # Flush any remaining text buffer
        if self.mode == self.Mode.TEXT and self.text_buffer:
            parsed_segments.append(Segment(SegmentType.TEXT, self.text_buffer))
            self.text_buffer = ""
        
        return parsed_segments
    
    def _process_character(self, char: str) -> List[Segment]:
        """Process a single character and return any completed segments."""
        segments = []
        
        if self.mode == self.Mode.TEXT:
            self._handle_text_mode(char)
        elif self.mode == self.Mode.BACKTICK_COUNT:
            segments.extend(self._handle_backtick_count_mode(char))
        elif self.mode == self.Mode.PYTHON_MATCH:
            self._handle_python_match_mode(char)
        elif self.mode == self.Mode.CODE:
            self._handle_code_mode(char)
        
        return segments
    
    def _handle_text_mode(self, char: str):
        """Handle character in TEXT mode."""
        if char == '`':
            self.mode = self.Mode.BACKTICK_COUNT
            self.backtick_count = 1
        else:
            self.text_buffer += char
    
    def _handle_backtick_count_mode(self, char: str) -> List[Segment]:
        """Handle character in BACKTICK_COUNT mode."""
        segments = []
        
        if char == '`':
            self.backtick_count += 1
            if self.backtick_count == 3:
                segments.extend(self._handle_triple_backtick())
        else:
            # Not a sequence of backticks - add to appropriate buffer
            buffer_content = "`" * self.backtick_count + char
            if self.in_code_block:
                self.code_buffer += buffer_content
            else:
                self.text_buffer += buffer_content
            self._reset_backtick_count()
        
        return segments
    
    def _handle_python_match_mode(self, char: str):
        """Handle character in PYTHON_MATCH mode."""
        expected_sequence = PYTHON_BLOCK_IDENTIFIER
        current_pos = len(self.python_match_progress)
        
        if current_pos < len(expected_sequence) and char == expected_sequence[current_pos]:
            # Match the next character in "python"
            self.python_match_progress += char
            if self.python_match_progress == expected_sequence:
                # Complete match - we're now in a code block
                self._enter_code_block()
        else:
            # Not a match for "python" - treat as regular text
            self.text_buffer += "```" + self.python_match_progress + char
            self.mode = self.Mode.TEXT
            self.python_match_progress = ""
            self.skip_next_triple_backtick = True
    
    def _handle_code_mode(self, char: str):
        """Handle character in CODE mode."""
        if char == '`':
            self.mode = self.Mode.BACKTICK_COUNT
            self.backtick_count = 1
        else:
            self.code_buffer += char
    
    def _handle_triple_backtick(self) -> List[Segment]:
        """Handle encountering three backticks."""
        segments = []
    
        if self.skip_next_triple_backtick:
            self.text_buffer += "```"
            self.skip_next_triple_backtick = False
            self.mode = self.Mode.TEXT
            self.backtick_count = 0
            return segments
        
        if self.in_code_block:
            # End of code block
            segments.append(Segment(SegmentType.CODE, self.code_buffer.strip()))
            self.code_buffer = ""
            self._exit_code_block()
        else:
            # Potential start of code block - flush text and check for "python"
            if self.text_buffer:
                segments.append(Segment(SegmentType.TEXT, self.text_buffer))
                self.text_buffer = ""
            self.mode = self.Mode.PYTHON_MATCH
            self.python_match_progress = ""
        
        return segments
    
    def _enter_code_block(self):
        """Enter code block mode."""
        self.in_code_block = True
        self.mode = self.Mode.CODE
        self.python_match_progress = ""
    
    def _exit_code_block(self):
        """Exit code block mode."""
        self.in_code_block = False
        self.mode = self.Mode.TEXT
        self._reset_backtick_count()
    
    def _reset_backtick_count(self):
        """Reset backtick counting state."""
        self.mode = self.Mode.CODE if self.in_code_block else self.Mode.TEXT
        self.backtick_count = 0