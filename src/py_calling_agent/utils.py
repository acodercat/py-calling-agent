import re
from .streaming_text_parser import PYTHON_BLOCK_IDENTIFIER
from typing import Union

def extract_python_code(response) -> Union[str, None]:
    """Extract python code block from LLM output"""
    pattern = r'```(?i:{})\n(.*?)```'.format(PYTHON_BLOCK_IDENTIFIER)
    matches = re.findall(pattern, response, re.DOTALL)
    return "\n\n".join(match.strip() for match in matches)