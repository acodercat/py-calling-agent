import re
from typing import Union

def extract_python_code(response) -> Union[str, None]:
    """Extract python code block from LLM output"""
    pattern = r'```(?i:python)\n(.*?)```'
    matches = re.findall(pattern, response, re.DOTALL)
    return "\n\n".join(match.strip() for match in matches)