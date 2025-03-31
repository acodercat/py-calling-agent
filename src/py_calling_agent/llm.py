from abc import ABC, abstractmethod
from typing import List, Dict, Iterator, Optional, Any

class LLMEngine(ABC):
    """
    Abstract base class for language model engines.
    Defines interface for interacting with different LLM providers.
    """
    
    @abstractmethod
    def __call__(self, messages: List[Dict[str, str]]) -> str:
        """Generate response from message history."""
        pass
    
    @abstractmethod
    def stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Stream response tokens from message history."""
        pass

class OpenAILLMEngine(LLMEngine):
    """
    OpenAI-compatible LLM engine implementation.
    Supports OpenAI API and compatible endpoints.
    """
    
    def __init__(
            self, 
            model_id: str, 
            api_key: str,
            base_url: Optional[str] = None,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            top_p: Optional[float] = None,
            presence_penalty: Optional[float] = None,
            frequency_penalty: Optional[float] = None,
            **kwargs
        ):
        """Initialize OpenAI LLM engine.
        
        Args:
            model_id: Model identifier
            api_key: API authentication key
            base_url: Optional API endpoint URL
            temperature: Temperature for the model
            max_tokens: Maximum number of tokens to generate
            top_p: Top-p value for nucleus sampling
            frequency_penalty: Frequency penalty for the model
            presence_penalty: Presence penalty for the model
            **kwargs: Additional parameters to pass to the OpenAI API
        """
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url, **kwargs)
        self.model = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
    

    def _prepare_openai_params(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Prepare parameters for OpenAI API call, including only non-None values."""
        # Start with required parameters
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }
        
        # Remove None values from params
        params = {k: v for k, v in params.items() if v is not None}
            
        return params

    def __call__(self, messages: List[Dict[str, str]]) -> str:
        """Generate response using OpenAI API."""
        response = self.client.chat.completions.create(
            **self._prepare_openai_params(messages),
            stream=False
        )
        return response.choices[0].message.content
    
    def stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Stream response tokens using OpenAI API."""
        response = self.client.chat.completions.create(
            **self._prepare_openai_params(messages),
            stream=True
        )
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content