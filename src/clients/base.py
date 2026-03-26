"""Base AI Client interface for Novelaist."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseAIClient(ABC):
    """Abstract base class for AI clients.
    
    This class defines the interface that all AI clients must implement,
    allowing Novelaist to work with different AI providers (Ollama, Anthropic, etc.)
    """
    
    def __init__(self, model: str, **kwargs):
        """Initialize the AI client.
        
        Args:
            model: The model identifier to use
            **kwargs: Additional provider-specific configuration
        """
        self.model = model
        self.config = kwargs
    
    @abstractmethod
    def chat(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Any:
        """Send a chat request to the AI model.
        
        Args:
            model: The model identifier
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Response object or dict with 'message' key containing 'content'
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI service is available and properly configured.
        
        Returns:
            True if the service is available, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the AI provider.
        
        Returns:
            Provider name (e.g., 'ollama', 'anthropic')
        """
        pass
