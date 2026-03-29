"""Ollama client implementation for Novelaist."""

import logging
from typing import List, Dict, Any, Optional

from .base import BaseAIClient

logger = logging.getLogger("novelaist.clients.ollama")


class OllamaClient(BaseAIClient):
    """Client for Ollama local AI models."""
    
    def __init__(self, model: str, host: Optional[str] = None, **kwargs):
        """Initialize Ollama client.
        
        Args:
            model: The Ollama model name (e.g., 'llama3', 'command-r')
            host: Optional host URL (e.g., 'http://localhost:11434')
            **kwargs: Additional configuration options
        """
        super().__init__(model, **kwargs)
        self.host = host
        self._client = None
    
    @property
    def client(self):
        """Lazy loader for ollama client."""
        if self._client is None:
            self._import_ollama()
        return self._client

    def _import_ollama(self):
        """Import ollama module and initialize client."""
        try:
            import ollama
            if self.host:
                self._client = ollama.Client(host=self.host)
                logger.info(f"Initialized Ollama client with host: {self.host}")
            else:
                self._client = ollama
                logger.info("Initialized Ollama client with default settings")
        except ImportError:
            logger.error("ollama package not installed. Run: pip install ollama")
            raise
    
    def chat(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Any:
        """Send chat request to Ollama.
        
        Args:
            model: The Ollama model name
            messages: List of message dictionaries
            **kwargs: Additional parameters
            
        Returns:
            Ollama response object with 'message' attribute containing 'content'
        """
        try:
            response = self.client.chat(
                model=model,
                messages=messages,
                **kwargs
            )
            return response
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Ollama is available.
        
        Returns:
            True if Ollama can be reached, False otherwise
        """
        try:
            # Try to list models to verify connection
            if hasattr(self.client, 'list'):
                self.client.list()
            return True
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False
    
    @property
    def provider_name(self) -> str:
        """Return provider name.
        
        Returns:
            'ollama'
        """
        return "ollama"
