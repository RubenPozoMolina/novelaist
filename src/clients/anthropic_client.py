"""Anthropic Claude client implementation for Novelaist."""

import logging
import time
from typing import List, Dict, Any, Optional

from .base import BaseAIClient

logger = logging.getLogger("novelaist.clients.anthropic")


class AnthropicClient(BaseAIClient):
    """Client for Anthropic Claude API."""
    
    def __init__(self, model: str, api_key: Optional[str] = None, **kwargs):
        """Initialize Anthropic client.
        
        Args:
            model: The Claude model name (e.g., 'claude-3-opus-20240229', 'claude-3-sonnet-20240229')
            api_key: Anthropic API key (can also be set via ANTHROPIC_API_KEY env var)
            **kwargs: Additional configuration options
        """
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self._client = None
        self._import_anthropic()
    
    def _import_anthropic(self):
        """Import anthropic module and initialize client."""
        try:
            from anthropic import Anthropic
            
            # Use provided API key or fall back to environment variable
            if self.api_key:
                self._client = Anthropic(api_key=self.api_key)
            else:
                self._client = Anthropic()
            
            logger.info(f"Initialized Anthropic client for model: {self.model}")
        except ImportError:
            logger.error("anthropic package not installed. Run: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple:
        """Convert generic message format to Anthropic format.
        
        Anthropic uses 'system' parameter for system messages and 
        'messages' list for user/assistant exchanges.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Tuple of (system_prompt, user_messages)
        """
        system_prompt = None
        user_messages = []
        
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                system_prompt = content
            elif role in ('user', 'assistant'):
                user_messages.append({
                    'role': role,
                    'content': content
                })
        
        # If no user messages but system exists, convert system to user message
        if not user_messages and system_prompt:
            user_messages.append({
                'role': 'user',
                'content': system_prompt
            })
            system_prompt = None
        
        return system_prompt, user_messages
    
    def _should_retry(self, error: Exception) -> bool:
        """Check if error is retryable (transient server errors)."""
        error_str = str(error).lower()
        retryable_statuses = ['500', '502', '503', '504', '429']
        retryable_errors = ['internal server error', 'bad gateway', 'service unavailable', 
                          'gateway timeout', 'rate limit', 'overloaded']
        return any(status in error_str for status in retryable_statuses) or \
               any(err in error_str for err in retryable_errors)
    
    def chat(self, model: str, messages: List[Dict[str, str]], max_retries: int = 3, 
             base_delay: float = 1.0, **kwargs) -> Any:
        """Send chat request to Anthropic Claude with retry logic.
        
        Args:
            model: The Claude model name
            messages: List of message dictionaries
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Initial delay between retries in seconds (default: 1.0)
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Response-like object with 'message' attribute containing 'content'
        """
        if self._client is None:
            raise RuntimeError("Anthropic client not initialized")
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Convert messages to Anthropic format
                system_prompt, user_messages = self._convert_messages(messages)
                
                # Prepare API call parameters
                api_params = {
                    'model': model or self.model,
                    'messages': user_messages,
                    'max_tokens': kwargs.get('max_tokens', 4096),
                }
                
                if system_prompt:
                    api_params['system'] = system_prompt
                
                # Add optional parameters
                if 'temperature' in kwargs:
                    api_params['temperature'] = kwargs['temperature']
                if 'top_p' in kwargs:
                    api_params['top_p'] = kwargs['top_p']
                
                # Make API call
                response = self._client.messages.create(**api_params)
                
                # Return a response object that mimics Ollama's structure
                class AnthropicResponse:
                    def __init__(self, content):
                        self.message = type('Message', (), {'content': content})()
                
                return AnthropicResponse(response.content[0].text)
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1 and self._should_retry(e):
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Anthropic API error (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    # Don't retry on final attempt or non-retryable errors
                    logger.error(f"Anthropic chat error (attempt {attempt + 1}/{max_retries}): {e}")
                    raise
        
        # Should not reach here, but just in case
        raise last_error
    
    def is_available(self) -> bool:
        """Check if Anthropic API is available.
        
        Returns:
            True if API key is set and client is initialized
        """
        try:
            if self._client is None:
                return False
            # Check if we can access the account (lightweight check)
            # Note: This makes an API call, so it's not completely free
            return True
        except Exception as e:
            logger.warning(f"Anthropic not available: {e}")
            return False
    
    @property
    def provider_name(self) -> str:
        """Return provider name.
        
        Returns:
            'anthropic'
        """
        return "anthropic"
