from abc import ABC, abstractmethod
from typing import List, Dict

class LLMEngine(ABC):
    """
    Abstract base class for language model engines.
    Defines interface for interacting with different LLM providers.
    """
    
    @abstractmethod
    def __call__(self, messages: List[Dict[str, str]]) -> str:
        """Generate response from message history.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Generated response text
        """
        pass

class OpenAILLMEngine(LLMEngine):
    """
    OpenAI-compatible LLM engine implementation.
    Supports OpenAI API and compatible endpoints.
    """

    def __init__(self, model_id: str, api_key: str, base_url: str = None):
        """Initialize OpenAI LLM engine.

        Args:
            model_id: Model identifier
            api_key: API authentication key
            base_url: Optional API endpoint URL
        """
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model_id

    def __call__(self, messages: List[Dict[str, str]]) -> str:
        """Generate response using OpenAI API.

        Args:
            messages: Conversation history as list of message dicts

        Returns:
            Generated response content
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content