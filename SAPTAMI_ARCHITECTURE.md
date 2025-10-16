# Saptami Architecture Design

## Overview

Saptami is a multi-agent orchestrator that coordinates remote agents through a **Research → Plan → Implement** workflow. It follows the architectural patterns from the multi-agent-coding-system project.

## Core Design Decisions

### 1. **Orchestrator-Driven (Saptami has the LLM)**
- Saptami contains the intelligence/LLM
- Remote agents are execution endpoints (tools/workers)
- Saptami reads agent capabilities via `get-info.json` and decides task delegation
- Agents receive specific instructions via A2A protocol

### 2. **Strict Sequential Phases (Waterfall)**
- **Research Phase** must complete 100% first (internal reasoning, no agent calls)
- **Plan Phase** starts only after research is done
- **Implement Phase** starts only after plan is complete
- Clean phase boundaries, no overlap

### 3. **Simple Text-Based Data Flow**
- Research outputs text findings
- Plan receives text, creates text plan
- Implement receives text plan, executes
- No complex structured contexts (simpler than Context Store)

## High-Level System Flow

```
User Query
    ↓
┌─────────────────────────────────────┐
│         SAPTAMI (with LLM)          │
│  1. Fetch all get-info.json files   │
│  2. Load agent capabilities         │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│   RESEARCH PHASE (Internal Only)    │
│  - NO agent calls                   │
│  - Saptami's LLM analyzes:          │
│    • User query                     │
│    • Agent capabilities             │
│    • Problem domain                 │
│  - Output: Research summary (text)  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│    PLAN PHASE (Create Sequence)     │
│  - Input: Research summary          │
│  - Saptami's LLM creates plan:      │
│    1. Call Agent2 (analyzer) with X │
│    2. Call Agent4 (writer) with Y   │
│    3. Call Agent1 (validator) with Z│
│  - Output: Execution plan (text)    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  IMPLEMENT PHASE (Execute Sequence) │
│  - Follow plan step-by-step         │
│  - Step 1: A2A call to Agent2       │
│  - Step 2: A2A call to Agent4       │
│  - Step 3: A2A call to Agent1       │
│  - Aggregate results                │
└─────────────────────────────────────┘
    ↓
Final Result to User
```

## Project Structure (Following Current Style)

```
saptami/
├── src/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── saptami_orchestrator.py      # Main orchestrator (like OrchestratorAgent)
│   │   └── saptami_state.py             # State management (like OrchestratorState)
│   │
│   ├── phases/
│   │   ├── __init__.py
│   │   ├── research_phase.py            # Research engine
│   │   ├── planning_phase.py            # Planning engine
│   │   └── implementation_phase.py      # Implementation engine
│   │
│   ├── discovery/
│   │   ├── __init__.py
│   │   ├── agent_registry.py            # Agent discovery (like OrchestratorHub)
│   │   └── entities/
│   │       ├── __init__.py
│   │       ├── agent_info.py            # AgentInfo dataclass
│   │       └── skill.py                 # Skill dataclass
│   │
│   ├── protocol/
│   │   ├── __init__.py
│   │   ├── a2a_client.py                # A2A communication (like CommandExecutor)
│   │   └── entities/
│   │       ├── __init__.py
│   │       ├── a2a_message.py           # Message format
│   │       └── a2a_response.py          # Response format
│   │
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── phase_executor.py            # Executes phases (like TurnExecutor)
│   │   └── entities/
│   │       ├── __init__.py
│   │       ├── phase_result.py          # PhaseResult (like ExecutionResult)
│   │       └── execution_context.py     # Context passed between phases
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── llm_client.py                # LLM client (reuse from current project)
│   │   └── prompt_loader.py             # Load prompt templates
│   │
│   └── system_msgs/
│       ├── research_prompt.md           # Research phase prompt
│       ├── planning_prompt.md           # Planning phase prompt
│       └── implementation_prompt.md     # Implementation phase prompt
│
├── tests/
│   ├── test_saptami_orchestrator.py
│   ├── test_phases.py
│   └── test_a2a_client.py
│
└── misc/
    ├── __init__.py
    └── log_setup.py                     # Logging setup
```

## Core Components

### 1. SaptamiOrchestrator (Main Entry Point)

**Responsibilities:**
- Initialize all components (registry, phases, executor)
- Coordinate phase execution
- Manage LLM configuration
- Track execution state

**Key Methods:**
- `setup(agent_urls)` - Discover agents and initialize components
- `execute(query)` - Run all phases sequentially
- `_get_llm_response(user_message, system_message)` - LLM interaction

**Pattern:** Mirrors `OrchestratorAgent` from current project

### 2. SaptamiState (State Management)

**Responsibilities:**
- Track current phase
- Store outputs from each phase
- Provide state serialization for logging
- Generate prompts with state context

**Key Attributes:**
- `query` - User's original query
- `current_phase` - "research", "planning", or "implementation"
- `research_summary` - Output from research phase
- `execution_plan` - Output from planning phase
- `implementation_results` - Output from implementation phase
- `done` - Completion flag

**Pattern:** Mirrors `OrchestratorState` from current project

### 3. AgentRegistry (Agent Discovery & Management)

**Responsibilities:**
- Fetch `get-info.json` from all agent URLs
- Parse agent capabilities and skills
- Index agents by skills for quick lookup
- Provide formatted views of available agents

**Key Methods:**
- `discover_agents(agent_urls)` - Fetch and register all agents
- `add_agent(agent_info)` - Add agent and index its skills
- `get_agent(agent_id)` - Retrieve agent by ID
- `get_agents_by_skill(skill_name)` - Find agents with specific skill
- `view_all_agents()` - Formatted string of all agents

**Pattern:** Mirrors `OrchestratorHub` from current project

### 4. PhaseExecutor (Phase Coordination)

**Responsibilities:**
- Execute phases in strict sequence
- Pass outputs between phases
- Update state after each phase
- Handle phase-level errors

**Key Method:**
- `execute(query, agent_registry, state)` - Run all three phases

**Pattern:** Mirrors `TurnExecutor` from current project

### 5. Phase Engines

#### ResearchPhase
**Responsibilities:**
- Analyze user query internally
- Review available agent capabilities
- Generate research summary (text)
- **NO agent calls**

**Input:** Query + AgentRegistry
**Output:** Research summary (text)

#### PlanningPhase
**Responsibilities:**
- Create step-by-step execution plan
- Select which agents to use
- Define sequence of agent invocations
- Specify what to ask each agent

**Input:** Research summary + AgentRegistry
**Output:** Execution plan (text)

#### ImplementationPhase
**Responsibilities:**
- Execute plan steps sequentially
- Call agents via A2A protocol
- Collect and aggregate results
- Handle agent communication errors

**Input:** Execution plan + AgentRegistry
**Output:** Implementation results (text)

### 6. A2AClient (Agent Communication)

**Responsibilities:**
- Fetch `get-info.json` from agents
- Send A2A messages to agent `/chat` endpoints
- Handle HTTP communication
- Parse agent responses

**Key Methods:**
- `fetch_agent_info(url)` - GET agent's get-info.json
- `send_message(agent_url, message, context)` - POST to /chat endpoint

**Pattern:** Mirrors `CommandExecutor` from current project

## Data Flow Example

### Scenario: "Fix the login bug"

#### Phase 1: Research (Internal)
```
Input: "Fix the login bug"

Saptami's LLM analyzes:
- Available agents:
  * Agent1: code-reader (python specialization)
  * Agent2: bug-finder (security specialization)
  * Agent3: code-writer (python specialization)
  * Agent4: tester (integration specialization)

Research Summary Output:
"To fix a login bug, I need to:
1. Read the authentication code
2. Identify the bug
3. Implement a fix
4. Verify with tests

Recommended workflow: read → analyze → fix → test
Agents needed: Agent1, Agent2, Agent3, Agent4"
```

#### Phase 2: Planning
```
Input: Research summary + Agent capabilities

Plan Output:
"Step 1: Use Agent1 (code-reader) to read /app/auth.py
 Step 2: Use Agent2 (bug-finder) to analyze the code for security bugs
 Step 3: Use Agent3 (code-writer) to implement the fix
 Step 4: Use Agent4 (tester) to run integration tests"
```

#### Phase 3: Implementation
```
Input: Execution plan

Execution:
1. A2A → Agent1: "Read /app/auth.py"
   Response: "Code content: [auth.py contents]"

2. A2A → Agent2: "Find bugs in: [code from step 1]"
   Response: "Bug found at line 45: missing null check for user object"

3. A2A → Agent3: "Fix line 45 in auth.py: add null check before accessing user.email"
   Response: "Fixed. Added: if user is None: return error"

4. A2A → Agent4: "Run login integration tests"
   Response: "All 12 tests passed"

Implementation Output:
"Login bug fixed successfully. Added null check at line 45. All tests passing."
```

## Key Design Patterns from Current Project

### 1. Entity-Based Data Modeling
- Use `@dataclass` for all data structures
- Separate entities into dedicated files
- Provide `to_dict()` and `from_dict()` methods

### 2. Centralized LLM Client
- Reuse `get_llm_response()` from current project
- Support multiple LLM backends (Claude, GPT, etc.)
- Track messages for token counting

### 3. Comprehensive Logging
- Use Python's `logging` module
- Log phase transitions
- Log agent interactions
- Save execution traces to disk

### 4. State Serialization
- All state objects have `to_dict()` for JSON serialization
- Enable debugging and post-execution analysis
- Support state persistence

### 5. Prompt Management
- Store prompts in `system_msgs/` directory as markdown files
- Load prompts dynamically
- Support prompt templating

## A2A Protocol Integration

### Agent Discovery (get-info.json)
```json
{
  "id": "agent-001",
  "name": "Code Analyzer",
  "description": "Analyzes code for bugs and security issues",
  "url": "https://agent1.example.com",
  "version": "1.0.0",
  "protocolVersion": "1.0",
  "skills": [
    {
      "name": "code_analysis",
      "description": "Analyze code for bugs"
    },
    {
      "name": "security_audit",
      "description": "Security vulnerability detection"
    }
  ],
  "capabilities": {
    "languages": ["python", "javascript"],
    "max_file_size": 100000
  },
  "extraData": {
    "specialization": "security"
  },
  "agentTrust": "high"
}
```

### Agent Communication (/chat endpoint)
```json
{
  "message": "Analyze this code for security bugs: [code content]",
  "context": {
    "task_id": "task_001",
    "phase": "implementation",
    "step": 2
  }
}
```

## Error Handling Strategy

### Phase-Level Errors
- If research fails → abort execution
- If planning fails → retry with different prompt
- If implementation fails → log error, continue to next step

### Agent Communication Errors
- Network timeout → retry up to 3 times
- Agent returns error → log and continue
- Invalid response → log and skip step

### State Recovery
- Save state after each phase
- Enable resumption from last successful phase
- Provide detailed error logs

## Extensibility Points

### 1. New Phases
- Add new phase engines in `phases/`
- Update `PhaseExecutor` to include new phase
- Create corresponding prompt in `system_msgs/`

### 2. Different LLM Backends
- Swap LLM client implementation
- Maintain same interface
- Support local models, cloud APIs

### 3. Enhanced Agent Selection
- Implement skill-based ranking
- Add agent performance tracking
- Support agent preferences

### 4. Advanced Planning
- Multi-step lookahead
- Parallel agent execution
- Dynamic replanning

## Next Steps

1. Implement core components following this architecture
2. Create prompt templates for each phase
3. Build A2A client with proper error handling
4. Add comprehensive tests
5. Create CLI interface
6. Document usage and examples

## Questions to Address

1. **LLM Backend**: Which LLM(s) to support initially? (Claude, GPT-4, local models?)
2. **A2A Message Format**: Specific schema for messages and responses?
3. **Prompt Management**: Embedded in code or separate files?
4. **Configuration**: Config file, environment variables, or CLI arguments?
5. **Logging Level**: What granularity of logging is needed?
