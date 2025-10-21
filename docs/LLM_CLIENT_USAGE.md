# LLM Client Usage Guide

## Overview

The LLM client (`sapthame/utils/llm_client.py`) provides a centralized interface for making LLM API calls using LiteLLM with OpenRouter support.

## Features

- **OpenRouter Integration**: Uses OpenRouter as the default API gateway
- **Anthropic Prompt Caching**: Automatically applies prompt caching for Anthropic models to reduce costs
- **Retry Logic**: Exponential backoff with jitter for handling rate limits and overloaded errors
- **Token Counting**: Accurate token counting with fallback mechanisms
- **Type-Safe**: Full type hints for better IDE support

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Required: OpenRouter API Key
export OPENROUTER_API_KEY="your-openrouter-api-key"

# Optional: Default model
export LITELLM_MODEL="openrouter/anthropic/claude-3.5-sonnet"

# Optional: Default temperature
export LITELLM_TEMPERATURE="0.7"

# Optional: Custom API base (defaults to https://openrouter.ai/api/v1)
export OPENROUTER_API_BASE="https://openrouter.ai/api/v1"
```

## Usage Examples

### Basic Usage

```python
from sapthame.utils.llm_client import get_llm_response

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
]

response = get_llm_response(
    messages=messages,
    model="openrouter/anthropic/claude-3.5-sonnet",
    temperature=0.7,
    max_tokens=4096
)

print(response)
```

### Using Environment Variables

```python
from sapthame.utils.llm_client import get_llm_response

# Model and temperature will be read from env vars
messages = [
    {"role": "user", "content": "Explain quantum computing in simple terms."}
]

response = get_llm_response(messages=messages)
print(response)
```

### With Custom API Key

```python
from sapthame.utils.llm_client import get_llm_response

response = get_llm_response(
    messages=messages,
    model="openrouter/anthropic/claude-3.5-sonnet",
    api_key="your-custom-api-key"
)
```

### Token Counting

```python
from sapthame.utils.llm_client import count_input_tokens, count_output_tokens

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi! How can I help you today?"}
]

# Count input tokens (system + user messages)
input_tokens = count_input_tokens(messages, model="openrouter/anthropic/claude-3.5-sonnet")
print(f"Input tokens: {input_tokens}")

# Count output tokens (assistant messages)
output_tokens = count_output_tokens(messages, model="openrouter/anthropic/claude-3.5-sonnet")
print(f"Output tokens: {output_tokens}")
```

## Supported Models

OpenRouter supports many models. Common examples:

- `openrouter/anthropic/claude-3.5-sonnet`
- `openrouter/anthropic/claude-3-opus`
- `openrouter/openai/gpt-4-turbo`
- `openrouter/openai/gpt-3.5-turbo`
- `openrouter/google/gemini-pro`

See [OpenRouter's model list](https://openrouter.ai/models) for all available models.

## Anthropic Prompt Caching

For Anthropic models (models containing "anthropic/" in the name), the client automatically applies prompt caching to:

1. The system message
2. The last two user messages

This can significantly reduce costs for conversations with repeated context.

## Error Handling

The client includes robust error handling:

- **Rate Limiting**: Automatically retries with exponential backoff (up to 10 retries by default)
- **Overloaded Errors**: Handles provider overload errors gracefully
- **Token Counting Timeouts**: Falls back to character-based estimation if token counting fails

```python
try:
    response = get_llm_response(messages=messages)
except ValueError as e:
    print(f"Configuration error: {e}")
except RuntimeError as e:
    print(f"Failed after retries: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Configuration Options

### `get_llm_response` Parameters

- **messages** (required): List of message dictionaries with 'role' and 'content'
- **model**: Model name (defaults to `LITELLM_MODEL` env var)
- **temperature**: Sampling temperature (defaults to `LITELLM_TEMPERATURE` or 0.7)
- **max_tokens**: Maximum tokens in response (default: 4096)
- **api_key**: API key (defaults to `OPENROUTER_API_KEY` env var)
- **api_base**: API base URL (defaults to `OPENROUTER_API_BASE` or OpenRouter's URL)
- **max_retries**: Maximum retry attempts (default: 10)

## Best Practices

1. **Set environment variables** for API keys rather than hardcoding them
2. **Use appropriate models** for your use case (balance cost vs. capability)
3. **Monitor token usage** to optimize costs
4. **Handle errors gracefully** in production code
5. **Use Anthropic models** when possible to benefit from automatic prompt caching
