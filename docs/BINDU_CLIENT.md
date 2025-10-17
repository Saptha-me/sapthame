# Bindu Client Documentation

## Overview

The `BinduClient` is a Python client for communicating with agents following the **Bindu A2A Task-First pattern** with JSON-RPC 2.0 protocol.

## Architecture

### Core Components

1. **BinduClient** (`sapthame/protocol/bindu_client.py`)
   - Main client for agent communication
   - Handles JSON-RPC 2.0 requests/responses
   - Built-in task state management
   - Support for authentication via bearer tokens

2. **TaskStateManager** (`sapthame/protocol/state_manager.py`)
   - Tracks tasks by ID, context, and state
   - Groups tasks by context for conversation continuity
   - Monitors active vs terminal states
   - Provides summary and visualization

3. **Entity Models** (`sapthame/protocol/entities/`)
   - `bindu_message.py` - Message structure with parts (text, image, file)
   - `bindu_task.py` - Task states and lifecycle management
   - `jsonrpc.py` - JSON-RPC 2.0 request/response handling

## Usage

### Basic Example

```python
from sapthame.protocol import BinduClient

# Initialize client
client = BinduClient(
    agent_url="http://localhost:8030",
    auth_token="your-token-here"  # Optional
)

# Send message and wait for completion
task = client.send_and_wait(
    text="provide sunset quote",
    poll_interval=2.0,
    max_wait=60.0
)

# Check result
if task.state == "completed":
    for artifact in task.artifacts:
        print(f"Result: {artifact.data}")
```

### Multi-Turn Conversation

```python
# First message
task1 = client.send_and_wait(text="provide sunset quote")
context_id = task1.contextId

# Follow-up message in same context
task2 = client.send_and_wait(
    text="make it shorter",
    context_id=context_id,
    reference_task_ids=[task1.taskId]
)
```

### Async Task Handling

```python
# Send message without waiting
task = client.send_message(text="analyze this data")

# Do other work...

# Poll for completion later
final_task = client.wait_for_task(
    task_id=task.taskId,
    poll_interval=2.0,
    max_wait=300.0
)
```

### Task Management

```python
# Get task status
task = client.get_task(task_id="550e8400-e29b-41d4-a716-446655440041")

# List all tasks
tasks = client.list_tasks()

# List tasks by context
context_tasks = client.list_tasks(context_id="550e8400-e29b-41d4-a716-446655440027")

# Cancel a task
canceled_task = client.cancel_task(task_id="550e8400-e29b-41d4-a716-446655440041")
```

### State Manager

```python
# Access built-in state manager
state_mgr = client.state_manager

# View all tracked tasks
print(state_mgr.view_all())

# Get active tasks
active = state_mgr.get_active_tasks()

# Get context summary
summary = state_mgr.get_context_summary(context_id)
print(f"Completed: {summary['completed']}, Failed: {summary['failed']}")
```

## Task States

### Non-Terminal States (Task Open)
- `submitted` - Initial state
- `working` - Agent processing
- `input-required` - Waiting for user input
- `auth-required` - Waiting for authentication

### Terminal States (Task Immutable)
- `completed` - Success with artifacts
- `failed` - Error occurred
- `canceled` - User canceled
- `rejected` - Agent rejected

## API Methods

### BinduClient Methods

| Method | Description |
|--------|-------------|
| `send_message()` | Send message to agent, returns task immediately |
| `get_task()` | Get current task status and details |
| `list_tasks()` | List all tasks, optionally filtered by context |
| `cancel_task()` | Cancel a running task |
| `wait_for_task()` | Poll task until terminal state reached |
| `send_and_wait()` | Send message and wait for completion |
| `fetch_agent_info()` | Get agent's get-info.json metadata |

### TaskStateManager Methods

| Method | Description |
|--------|-------------|
| `add_task()` | Add or update a task |
| `get_task()` | Get task by ID |
| `get_context_tasks()` | Get all tasks for a context |
| `get_active_tasks()` | Get tasks in non-terminal states |
| `get_completed_tasks()` | Get all completed tasks |
| `get_failed_tasks()` | Get all failed tasks |
| `update_task_state()` | Update task state and fields |
| `is_context_complete()` | Check if all context tasks are terminal |
| `get_context_summary()` | Get state counts for a context |
| `view_all()` | Get formatted view of all tasks |
| `reset()` | Clear all tracked tasks |

## Integration with AgentRegistry

The `AgentRegistry` now uses `BinduClient` for agent discovery:

```python
from sapthame.protocol import BinduClient
from sapthame.discovery.agent_registry import AgentRegistry

# Create client
client = BinduClient(agent_url="http://localhost:8030")

# Create registry
registry = AgentRegistry(bindu_client=client)

# Discover agents
registry.discover_agents([
    "http://localhost:8030",
    "http://localhost:8031",
])
```

## Protocol Compliance

The client implements:
- ✅ **JSON-RPC 2.0** - Standard request/response format
- ✅ **Task-First Pattern** - Messages create immutable tasks
- ✅ **Task Immutability** - Terminal states cannot be modified
- ✅ **Context Continuity** - Multi-turn conversations via context_id
- ✅ **Parallel Tasks** - Multiple tasks per context
- ✅ **Artifact Versioning** - Immutable task outputs
- ✅ **Reference Tasks** - Link related tasks together

## Error Handling

```python
try:
    task = client.send_and_wait(text="process this")
    if task.state == "failed":
        print(f"Task failed: {task.error}")
except TimeoutError:
    print("Task did not complete in time")
except Exception as e:
    print(f"Communication error: {e}")
```

## Configuration

### Client Initialization

```python
client = BinduClient(
    agent_url="http://localhost:8030",  # Required: Agent base URL
    timeout=30,                          # Optional: Request timeout (seconds)
    auth_token="your-token"              # Optional: Bearer token
)
```

### Message Configuration

```python
task = client.send_message(
    text="your message",
    context_id="optional-context-id",
    task_id="optional-task-id",
    reference_task_ids=["ref-task-1", "ref-task-2"],
    accepted_output_modes=["application/json", "text/plain"]
)
```

## References

- [Bindu Repository](https://github.com/Saptha-me/Bindu)
- [Hybrid Agent Pattern Documentation](https://github.com/Saptha-me/Bindu/blob/main/docs/hybrid-agent-pattern.md)
- [Postman Collection Examples](https://github.com/Saptha-me/Bindu/blob/main/sapthame.postman_collection.json)
