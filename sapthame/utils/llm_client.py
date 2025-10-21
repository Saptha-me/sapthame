"""Centralized LLM client for making LiteLLM calls with OpenRouter support."""

import os
import copy
import time
import random
import logging
import threading
from typing import List, Dict, Optional, Any

import litellm
from litellm.exceptions import InternalServerError
from litellm.utils import token_counter

logger = logging.getLogger(__name__)


def _apply_anthropic_caching_if_possible(messages: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
    """Apply prompt caching for Anthropic models.

    Args:
        messages: List of message dictionaries
        model: Model name

    Returns:
        Messages with cache_control applied for Anthropic models
    """
    # Only apply caching for Anthropic models
    if not (model and "anthropic/" in model):
        return messages

    # Deep copy messages to avoid modifying the original
    cached_messages = copy.deepcopy(messages)

    # Find indices of system and user messages
    system_idx = None
    user_indices = []

    for i, msg in enumerate(cached_messages):
        if msg.get("role") == "system":
            system_idx = i
        elif msg.get("role") == "user":
            user_indices.append(i)

    # Apply cache control to system message
    if system_idx is not None:
        msg = cached_messages[system_idx]
        # Convert content to the format required for caching
        if isinstance(msg.get("content"), str):
            msg["content"] = [
                {
                    "type": "text",
                    "text": msg["content"],
                    "cache_control": {"type": "ephemeral"}
                }
            ]
        elif isinstance(msg.get("content"), list):
            # Add cache_control to existing content items
            for item in msg["content"]:
                if isinstance(item, dict) and "text" in item:
                    item["cache_control"] = {"type": "ephemeral"}

    # Apply cache control to last 2 user messages
    if len(user_indices) >= 1:
        # Cache the last user message
        last_user_idx = user_indices[-1]
        msg = cached_messages[last_user_idx]
        if isinstance(msg.get("content"), str):
            msg["content"] = [
                {
                    "type": "text",
                    "text": msg["content"],
                    "cache_control": {"type": "ephemeral"}
                }
            ]
        elif isinstance(msg.get("content"), list):
            for item in msg["content"]:
                if isinstance(item, dict) and "text" in item:
                    item["cache_control"] = {"type": "ephemeral"}

    if len(user_indices) >= 2:
        # Cache the second-to-last user message
        second_last_user_idx = user_indices[-2]
        msg = cached_messages[second_last_user_idx]
        if isinstance(msg.get("content"), str):
            msg["content"] = [
                {
                    "type": "text",
                    "text": msg["content"],
                    "cache_control": {"type": "ephemeral"}
                }
            ]
        elif isinstance(msg.get("content"), list):
            for item in msg["content"]:
                if isinstance(item, dict) and "text" in item:
                    item["cache_control"] = {"type": "ephemeral"}

    return cached_messages


def get_llm_response(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: int = 4096,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    max_retries: int = 10
) -> str:
    """Get response from LLM via LiteLLM.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Model name (e.g., 'openrouter/anthropic/claude-3.5-sonnet')
        temperature: Temperature for sampling
        max_tokens: Maximum tokens in response
        api_key: API key for LLM provider (defaults to OPENROUTER_API_KEY env var)
        api_base: Base URL for API (defaults to https://openrouter.ai/api/v1)
        max_retries: Maximum number of retries for rate limiting
        
    Returns:
        LLM response text
    """
    # Use provided params or fall back to env vars
    model = model or os.getenv("LITELLM_MODEL", None)
    if not model:
        raise ValueError("Model must be specified either as argument or via LITELLM_MODEL env var.")
    temperature = temperature if temperature is not None else float(os.getenv("LITELLM_TEMPERATURE", "0.7"))

    # Set API configuration for OpenRouter
    if api_key or (api_key := os.getenv("OPENROUTER_API_KEY")):
        litellm.api_key = api_key
    if api_base or (api_base := os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")):
        litellm.api_base = api_base

    # Apply Anthropic caching if applicable
    processed_messages = _apply_anthropic_caching_if_possible(messages, model)

    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            # Call LiteLLM
            response = litellm.completion(
                model=model,
                messages=processed_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content  # type: ignore

        except InternalServerError as e:
            # Check if it's an overloaded error
            if "overloaded_error" in str(e):
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    base_delay = 2 ** attempt  # 1, 2, 4, 8, 16, 32, 64
                    jitter = random.uniform(0, base_delay * 0.1)  # Add up to 10% jitter
                    delay = min(base_delay + jitter, 60)  # Cap at 60 seconds

                    logger.warning(
                        f"LLM overloaded, retrying in {delay:.2f} seconds (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                else:
                    # Max retries reached, re-raise the exception
                    raise
            else:
                # Not an overloaded error, re-raise immediately
                raise

        except Exception:
            # Any other exception, re-raise immediately
            raise

    # Should never reach here, but just in case
    raise RuntimeError("Failed to get LLM response after maximum retries.")


def _try_token_counter_with_timeout(model: str, messages: List[Dict[str, Any]], 
                                     timeout: float = 2.0) -> Optional[int]:
    """Try to count tokens with a timeout.

    Args:
        model: Model name for token counting
        messages: List of message dictionaries
        timeout: Timeout in seconds

    Returns:
        Token count if successful, None if failed or timed out
    """
    result = [None]
    exception = [None]

    def run_token_counter():
        try:
            result[0] = token_counter(model=model, messages=messages)
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=run_token_counter)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        # Thread is still running, timeout occurred
        logger.warning(
            f"Token counting timed out for model {model} after {timeout}s"
        )
        return None
    elif exception[0]:
        # An exception occurred
        logger.warning(
            f"Failed to count tokens with model {model}: {exception[0]}"
        )
        return None
    else:
        # Success
        return result[0]


def count_tokens_for_messages(messages: List[Dict[str, Any]], 
                               model: Optional[str] = None) -> int:
    """Count total tokens in a list of messages.

    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Model name for accurate token counting (defaults to gpt-3.5-turbo)

    Returns:
        Total token count for all messages
    """
    if not messages:
        return 0

    model = model or os.getenv("LITELLM_MODEL", "gpt-3.5-turbo")

    # Try with the specified model first
    token_count = _try_token_counter_with_timeout(model, messages)
    if token_count is not None:
        return token_count

    # Try with gpt-3.5-turbo as fallback
    logger.info("Retrying token counting with gpt-3.5-turbo")
    token_count = _try_token_counter_with_timeout("gpt-3.5-turbo", messages)
    if token_count is not None:
        return token_count

    # Final fallback: estimate ~4 chars per token
    logger.warning("Using character-based token estimation")
    total_chars = sum(len(str(msg.get("content", ""))) for msg in messages)
    return total_chars // 4


def count_input_tokens(messages: List[Dict[str, Any]], model: Optional[str] = None) -> int:
    """Count tokens for input messages (system and user roles).

    Args:
        messages: List of message dictionaries
        model: Model name for accurate token counting

    Returns:
        Token count for system and user messages
    """
    input_messages = [
        msg for msg in messages 
        if msg.get("role") in ["system", "user"]
    ]
    return count_tokens_for_messages(input_messages, model)


def count_output_tokens(messages: List[Dict[str, Any]], model: Optional[str] = None) -> int:
    """Count tokens for output messages (assistant role).

    Args:
        messages: List of message dictionaries
        model: Model name for accurate token counting

    Returns:
        Token count for assistant messages
    """
    output_messages = [
        msg for msg in messages
        if msg.get("role") == "assistant"
    ]
    return count_tokens_for_messages(output_messages, model)
