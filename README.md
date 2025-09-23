# Saptha.me ✨  
**Cloud-native swarm intelligence**  

Saptha.me is an swarm platform for building, deploying, and orchestrating LLM agents on the cloud.  
We believe single agents are useful, but true intelligence emerges when **agents collaborate as a swarm** like human.  

---

## 🔥 What We’re Building
- **Framework-agnostic agent runtime**  
  Bring your own agent (LangChain, Agno, CrewAI, LangGraph, custom FastAPI) — Saptha treats them equally.  

- **Cloud-native orchestration**  
  Agents run as pods, services, or serverless functions. Swarms can scale across clusters.  

- **Decentralized Identity (DID)**  
  Every agent gets a DID + public key in a DID document. This forms the trust layer for authentication.

- **We respect A2A**  
  Every agent will talk with each other - language communication menthod will be A2A. 

- **Payments & Costs**  
  Native support for **x402** / **AP2** protocols.  
  - Billable vs non-billable functions  
  - Credit wallets + micropayments for developers  

- **Developer-first experience**  
  - CLI (`saptha deploy`, `saptha run`)  
  - Simple REST + gRPC APIs  
  - DID + cost schema baked into the protocol  

---

## 🚀 Quick Start (Coming Soon)
```bash
# Install CLI
pip install sapthame

# Init a new agent
sapthame init my-agent

# Connect to another agent
# Saptha - Distributed Agent Orchestrator

A distributed agent orchestration system that coordinates multiple AI agents using the A2A (Agent-to-Agent) protocol. Built with type-safe Python and following DRY principles.

## Overview

Saptha transforms the in-process agent coordination pattern (like Agno Team) into a distributed architecture where agents run as separate services and communicate via A2A protocol. The orchestrator acts as the "brain" that coordinates agent selection, execution, and response aggregation.

## Architecture

```
┌─────────────────────────────────────┐
│           Orchestrator              │
│  ┌─────────────────────────────────┐│
│  │      Team Reasoning Engine      ││  
│  │   (Ported from Agno Team)       ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │       A2A Client                ││
│  │   (FastA2A TaskManager)         ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │     Context Manager             ││
│  │   (PostgreSQL Interface)        ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
              │ A2A Protocol
              ▼
┌─────────────────────────────────────┐
│        Agent Services               │
│     (Separate pods/containers)      │
└─────────────────────────────────────┘
```

## Key Features

### Intelligent Task Routing
- Analyzes task content to determine required capabilities
- Selects appropriate agents based on capabilities and availability
- Supports load balancing across agent instances

### Flexible Execution Modes
- **Sequential**: Agents execute one after another, building on previous results
- **Parallel**: Multiple agents work simultaneously for faster processing
- **Collaborative**: Agents work together iteratively to refine responses

### A2A Protocol Integration
- Based on FastA2A for reliable agent communication
- Retry logic and error handling for robust distributed execution
- Health monitoring and automatic failover

### Persistent Context Management
- PostgreSQL-based context storage
- Conversation history and task state tracking
- Shared context across distributed agents

### Agent Capabilities
- Web Search
- Knowledge Base
- Data Analysis
- Code Generation
- Text Processing
- Image Processing
- Reasoning

## Project Structure

```
saptha/
├── core/
│   ├── types.py           # Core data models and enums
│   └── orchestrator.py    # Main orchestration logic
├── protocol/
│   └── a2a_client.py      # A2A protocol client
├── context/
│   ├── models.py          # SQLAlchemy database models
│   └── manager.py         # Context management interface
└── routing/
    └── router.py          # Task routing and agent selection
```

## Installation

```bash
# Install dependencies
uv sync

# Install with development dependencies
uv sync --extra dev
```

## Usage

### Basic Example

```python
import asyncio
from saptha.context.manager import ContextManager
from saptha.core.orchestrator import DistributedOrchestrator
from saptha.core.types import Message

async def main():
    # Initialize components
    context_manager = ContextManager("postgresql+asyncpg://user:pass@localhost/saptha")
    orchestrator = DistributedOrchestrator(context_manager)
    
    await orchestrator.initialize()
    
    # Process a message
    message = Message(content="What is the latest news about AI?", role="user")
    result = await orchestrator.process_message(message)
    
    print(f"Final response: {result.final_response}")
    
    await orchestrator.close()

asyncio.run(main())
```

### Running the Demo

```bash
python main.py
```

This will demonstrate the orchestration logic without requiring actual agent services.

## Configuration

### Database Setup

1. Install PostgreSQL
2. Create a database for Saptha
3. Update the connection string in your code:

```python
database_url = "postgresql+asyncpg://username:password@localhost:5432/saptha"
```

### Agent Registration

Agents are registered with their capabilities and endpoints:

```python
agent_info = AgentInfo(
    id="my-agent",
    name="My Agent",
    description="Does amazing things",
    capabilities=[AgentCapability.WEB_SEARCH, AgentCapability.REASONING],
    endpoint="http://localhost:8001"
)

await context_manager.register_agent(agent_info)
```

## Development

### Running Tests

```bash
uv run pytest
```

### Code Quality

```bash
# Format code
uv run black saptha/

# Lint code
uv run ruff check saptha/

# Type checking
uv run mypy saptha/
```

## Design Principles

### DRY (Don't Repeat Yourself)
- Shared base classes and utilities
- Reusable components across modules
- Configuration-driven behavior

### Type Safety
- Full type hints throughout
- Pydantic models for data validation
- SQLAlchemy with typed models

### Best Practices
- Structured logging with context
- Async/await for I/O operations
- Proper error handling and retry logic
- Clean separation of concerns

## Comparison with Agno Team

| Aspect | Agno Team | Saptha |
|--------|-----------|---------|
| **Architecture** | In-process | Distributed |
| **Communication** | Function calls | A2A Protocol |
| **Scalability** | Single process | Multi-pod/container |
| **State Management** | In-memory | PostgreSQL |
| **Agent Deployment** | Code-based | Service-based |
| **Fault Tolerance** | Process-level | Service-level |

## Contributing

1. Follow the existing code style and patterns
2. Add type hints to all functions
3. Write tests for new functionality
4. Update documentation as needed

## License

This project is licensed under the MIT License.
