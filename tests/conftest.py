import pytest
import os
from py_calling_agent import OpenAILLMEngine

@pytest.fixture
def llm_engine():
    """Provide a real LLM engine for testing."""
    return OpenAILLMEngine(
        model_id=os.getenv("LLM_MODEL_ID"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL")
    ) 