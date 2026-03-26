"""AI Client Factory for Novelaist.

This module provides a factory function to create the appropriate
AI client based on configuration.
"""

import logging
import os
from typing import Optional, Dict, Any

from .base import BaseAIClient
from .ollama_client import OllamaClient
from .anthropic_client import AnthropicClient

logger = logging.getLogger("novelaist.clients")


def create_ai_client(
    model: str,
    provider: Optional[str] = None,
    host: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseAIClient:
    """Create an AI client based on the model and configuration.
    
    This factory function automatically detects the appropriate client
    based on the model name or explicit provider configuration.
    
    Args:
        model: The model identifier (e.g., 'llama3', 'claude-3-opus-20240229')
        provider: Explicit provider name ('ollama' or 'anthropic'). 
                  If not provided, auto-detected from model name.
        host: Host URL for Ollama (e.g., 'http://localhost:11434')
        api_key: API key for cloud providers (can also use env vars)
        **kwargs: Additional configuration options
        
    Returns:
        Configured AI client instance
        
    Raises:
        ValueError: If provider cannot be determined or is unsupported
        RuntimeError: If required dependencies are not installed
    """
    # Detect provider from model name if not explicitly provided
    if provider is None:
        provider = _detect_provider_from_model(model)
    
    provider = provider.lower().strip()
    
    if provider == 'ollama':
        logger.info(f"Creating Ollama client for model: {model}")
        return OllamaClient(model=model, host=host, **kwargs)
    
    elif provider == 'anthropic':
        # Use API key from config or environment variable
        anthropic_api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not anthropic_api_key:
            logger.warning("ANTHROPIC_API_KEY not set. Set it in config.json or as environment variable.")
        
        logger.info(f"Creating Anthropic client for model: {model}")
        return AnthropicClient(model=model, api_key=anthropic_api_key, **kwargs)
    
    else:
        raise ValueError(f"Unknown AI provider: {provider}. "
                        f"Supported providers: ollama, anthropic")


def _detect_provider_from_model(model: str) -> str:
    """Auto-detect provider from model name.
    
    Args:
        model: The model identifier
        
    Returns:
        Provider name ('ollama' or 'anthropic')
    """
    model_lower = model.lower()
    
    # Anthropic model patterns
    if 'claude' in model_lower:
        return 'anthropic'
    
    # Default to Ollama for common local models
    ollama_models = [
        'llama', 'mistral', 'mixtral', 'codellama', 'vicuna', 
        'orca', 'command', 'llava', 'dolphin', 'solar',
        'qwen', 'yi', 'stablelm', 'wizardlm', 'phi'
    ]
    
    for ollama_model in ollama_models:
        if ollama_model in model_lower:
            return 'ollama'
    
    # If model contains '/', it's likely an Ollama model reference
    if '/' in model:
        return 'ollama'
    
    # Default to Ollama if we can't determine
    logger.warning(f"Cannot determine provider for model '{model}'. Assuming Ollama.")
    logger.warning("Explicitly set 'provider' in config.json to avoid this warning.")
    return 'ollama'


def get_client_from_config(config: Dict[str, Any]) -> BaseAIClient:
    """Create an AI client from a configuration dictionary.
    
    Args:
        config: Dictionary with configuration options
        
    Returns:
        Configured AI client instance
    """
    model = config.get('model', 'llama3')
    provider = config.get('provider')
    host = config.get('host')
    api_key = config.get('api_key')
    
    return create_ai_client(
        model=model,
        provider=provider,
        host=host,
        api_key=api_key
    )
