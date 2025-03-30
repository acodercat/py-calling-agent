import pytest
import os
from py_calling_agent import OpenAILLMEngine

@pytest.fixture
def llm_engine():
    """Provide a real LLM engine for testing."""
    return OpenAILLMEngine(
        model_id="qwen2.5-72b-instruct",
        api_key="sk-8898a87b8e7b4e399d6fc5ee804c4666",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    ) 