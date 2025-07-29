import re
from typing import Union

def extract_python_code(response, python_block_identifier: str) -> Union[str, None]:
    """Extract python code block from LLM output"""
    pattern = r'```(?i:{})\n(.*?)```'.format(python_block_identifier)
    matches = re.findall(pattern, response, re.DOTALL)
    return "\n\n".join(match.strip() for match in matches)