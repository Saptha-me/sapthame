# Turn-Based Executor Architecture for Sapthame

## Overview

This document outlines the architecture for implementing a turn-based executor system for Sapthame, inspired by the [multi-agent-coding-system](https://github.com/Danau5tin/multi-agent-coding-system) pattern but adapted for our Bindu protocol and research-first workflow.

## Philosophy: Turn-Based Execution

The turn-based approach enables:
- **Iterative Refinement**: Research agents can be queried multiple times to refine understanding
- **State Tracking**: Each turn captures what was asked, what was learned, and what to do next
- **Transparency**: Full audit trail of agent interactions
- **Flexibility**: Can switch between agents or strategies based on intermediate results
- **Open Source Friendly**: Clear, inspectable execution flow

## Current vs. Proposed Architecture

### Current Architecture (Phase-Based)
```
Conductor
  └─> PhaseExecutor
       ├─> ResearchPhase (executes once)
       ├─> PlanningPhase (executes once)
       └─> ImplementationPhase (executes once)
```

**Limitations:**
- Single-pass execution per phase
- No iterative refinement
- Hard to explore/discuss/research before committing to a plan

### Proposed Architecture (Turn-Based)
```
Conductor
  └─> TurnExecutor (stateless, reusable)
       ├─> ActionParser (parse LLM output into actions)
       ├─> ActionHandler (execute actions)
       │    ├─> QueryResearchAgent (via BinduClient)
       │    ├─> UpdateScratchpad
       │    ├─> UpdateTodoList
       │    └─> FinishStage
       └─> ExecutionResult (actions + responses)
```

## Key Components

### 1. TurnExecutor (Stateless)
**Location**: `sapthame/orchestrator/turn_executor.py` (already exists, needs adaptation)

**Responsibilities:**
- Parse LLM output into structured actions
- Execute actions via ActionHandler
- Return ExecutionResult with what happened

**Interface:**
```python
class TurnExecutor:
    def __init__(
        self,
        action_parser: ActionParser,
        action_handler: ActionHandler
    ):
        pass
    
    def execute(self, llm_output: str) -> ExecutionResult:
        """Execute one turn of interaction."""
        pass
```

### 2. Action Types for Research Stage

**Location**: `sapthame/orchestrator/actions/` (new directory)

```python
# Base Action
@dataclass
class Action:
    """Base class for all actions."""
    action_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        pass

# Research-specific actions
@dataclass
class QueryAgentAction(Action):
    """Query a research agent via Bindu protocol."""
    agent_id: str  # e.g., "market-intel-agent"
    query: str
    context_id: Optional[str] = None
    
@dataclass
class UpdateScratchpadAction(Action):
    """Update the scratchpad with findings."""
    content: str
    operation: str = "append"  # append, replace, clear

@dataclass
class UpdateTodoAction(Action):
    """Update the todo list."""
    item: str
    operation: str = "add"  # add, complete, remove

@dataclass
class FinishStageAction(Action):
    """Mark the current stage as complete."""
    message: str
    summary: str
```

### 3. ActionParser

**Location**: `sapthame/orchestrator/actions/parser.py` (new)

**Responsibilities:**
- Parse LLM output (likely structured as XML or JSON blocks)
- Extract action tags/blocks
- Return list of Action objects + any parsing errors

**Example LLM Output Format:**
```xml
<thought>
I need to understand the market landscape first.
Let me query the market intelligence agent.
</thought>

<action type="query_agent">
<agent_id>market-intel-agent</agent_id>
<query>What is the current market size and growth rate for B2B SaaS in the healthcare sector?</query>
</action>

<action type="update_scratchpad">
<content>Starting market research for healthcare B2B SaaS opportunity</content>
</action>
```

### 4. ActionHandler

**Location**: `sapthame/orchestrator/actions/handler.py` (new)

**Responsibilities:**
- Execute each action type
- Interact with BinduClient for agent queries
- Manage scratchpad and todo state
- Return (output: str, is_error: bool) for each action

**Key Methods:**
```python
class ActionHandler:
    def __init__(
        self,
        agent_registry: AgentRegistry,
        bindu_client: BinduClient,
        scratchpad_manager: ScratchpadManager,
        todo_manager: TodoManager
    ):
        pass
    
    def handle_action(self, action: Action) -> Tuple[str, bool]:
        """Execute an action and return (output, is_error)."""
        if isinstance(action, QueryAgentAction):
            return self._handle_query_agent(action)
        elif isinstance(action, UpdateScratchpadAction):
            return self._handle_update_scratchpad(action)
        # ... etc
    
    def _handle_query_agent(self, action: QueryAgentAction) -> Tuple[str, bool]:
        """Query a research agent via Bindu protocol."""
        # 1. Get agent from registry
        # 2. Create BinduClient for that agent
        # 3. Send message via Bindu protocol
        # 4. Wait for response
        # 5. Return formatted response
        pass
```

### 5. ExecutionResult

**Location**: `sapthame/orchestrator/entities/execution_result.py` (new)

```python
@dataclass
class ExecutionResult:
    """Result of executing a turn."""
    actions_executed: List[Action]
    env_responses: List[str]  # Response for each action
    has_error: bool
    done: bool  # True if FinishStage action was executed
    finish_message: Optional[str] = None
    agent_trajectories: Optional[Dict[str, Dict[str, Any]]] = None
```

### 6. State Managers

**Location**: `sapthame/orchestrator/state_managers/` (new directory)

```python
class ScratchpadManager:
    """Manages the scratchpad for temporary notes and findings."""
    def __init__(self):
        self.content: List[str] = []
    
    def append(self, text: str):
        self.content.append(text)
    
    def get_content(self) -> str:
        return "\n".join(self.content)
    
    def clear(self):
        self.content = []

class TodoManager:
    """Manages the todo list for tracking research tasks."""
    def __init__(self):
        self.items: List[Dict[str, Any]] = []
    
    def add_item(self, item: str):
        self.items.append({"text": item, "completed": False})
    
    def complete_item(self, index: int):
        if 0 <= index < len(self.items):
            self.items[index]["completed"] = True
    
    def get_status(self) -> str:
        # Return formatted todo list
        pass
```

## Updated Conductor Flow

### For Research Stage

```python
class Conductor:
    def setup(self, agent_urls: List[str], logging_dir: Optional[Path] = None):
        # ... existing setup ...
        
        # Initialize state managers
        self.scratchpad_manager = ScratchpadManager()
        self.todo_manager = TodoManager()
        
        # Initialize action components
        self.action_parser = ActionParser()
        self.action_handler = ActionHandler(
            agent_registry=self.agent_registry,
            bindu_client=self.bindu_client,
            scratchpad_manager=self.scratchpad_manager,
            todo_manager=self.todo_manager
        )
        
        # Initialize turn executor
        self.executor = TurnExecutor(
            action_parser=self.action_parser,
            action_handler=self.action_handler
        )
    
    def run_research_stage(
        self,
        client_question: str,
        max_turns: int = 20
    ) -> Dict[str, Any]:
        """Run research stage with turn-based execution."""
        turns_executed = 0
        
        while not self.state.done and turns_executed < max_turns:
            turns_executed += 1
            logger.info(f"Research Turn {turns_executed}/{max_turns}")
            
            # Build user message with current state
            user_message = self._build_research_prompt(
                client_question=client_question,
                scratchpad=self.scratchpad_manager.get_content(),
                todo=self.todo_manager.get_status(),
                conversation_history=self.conversation_history.to_prompt()
            )
            
            # Get LLM response
            llm_response = self._get_llm_response(user_message)
            
            # Execute turn
            result = self.executor.execute(llm_response)
            
            # Create turn for history
            turn = Turn(
                llm_output=llm_response,
                actions_executed=result.actions_executed,
                env_responses=result.env_responses,
                agent_trajectories=result.agent_trajectories
            )
            
            # Add to conversation history
            self.conversation_history.add_turn(turn)
            
            # Check if done
            if result.done:
                self.state.done = True
                self.state.finish_message = result.finish_message
                logger.info(f"Research stage complete: {result.finish_message}")
                break
        
        return {
            'completed': self.state.done,
            'finish_message': self.state.finish_message,
            'turns_executed': turns_executed,
            'scratchpad': self.scratchpad_manager.get_content(),
            'todo': self.todo_manager.get_status()
        }
```

## CLI Integration

### Command Structure
```bash
# Run research stage only
saptami run \
  --stage research \
  --id vc_research \
  --client-question "What is the market opportunity for AI-powered healthcare diagnostics?" \
  --agent market=./agents/market-intel-agent.get-info.json \
  --agent competitive=./agents/competitive-analysis-agent.get-info.json \
  --max-turns 20
```

### CLI Arguments
- `--stage`: Which stage to run (research, planning, implementation)
- `--id`: Unique identifier for this run
- `--client-question`: The question/problem to research
- `--agent`: Agent specification (can be repeated)
  - Format: `<alias>=<path-to-get-info.json>`
  - Alias is used in action queries: `<agent_id>market</agent_id>`
- `--max-turns`: Maximum number of turns before stopping

## System Prompt for Research Stage

The conductor's system prompt should include:

1. **Available Actions**: List all action types with examples
2. **Available Agents**: List discovered agents with their capabilities
3. **State Information**: Current scratchpad, todo list, conversation history
4. **Guidelines**:
   - Explore thoroughly before concluding
   - Query multiple agents for different perspectives
   - Use scratchpad to organize findings
   - Use todo list to track remaining questions
   - Only finish when confident in the research

## Benefits of This Architecture

### 1. **Iterative Research**
- Can query agents multiple times with refined questions
- Can switch between agents based on findings
- Can explore tangents and return to main thread

### 2. **Transparency**
- Every turn is logged with actions and responses
- Clear audit trail of what was asked and learned
- Easy to debug and understand decision-making

### 3. **Flexibility**
- Easy to add new action types (e.g., SearchWeb, ReadDocument)
- Can adapt strategy mid-execution
- Can pause/resume research sessions

### 4. **Testability**
- Each component is independently testable
- Can mock BinduClient for unit tests
- Can replay turns for debugging

### 5. **Extensibility**
- Same pattern works for planning and implementation stages
- Just define different action types for each stage
- Reuse TurnExecutor, ActionParser infrastructure

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Create action types (`sapthame/orchestrator/actions/entities/`)
- [ ] Implement ActionParser (`sapthame/orchestrator/actions/parser.py`)
- [ ] Implement ActionHandler (`sapthame/orchestrator/actions/handler.py`)
- [ ] Create ExecutionResult (`sapthame/orchestrator/entities/execution_result.py`)
- [ ] Update TurnExecutor to use new components

### Phase 2: State Management (Week 1)
- [ ] Implement ScratchpadManager
- [ ] Implement TodoManager
- [ ] Update State class to include these managers
- [ ] Update State.to_prompt() to include scratchpad/todo

### Phase 3: Conductor Integration (Week 2)
- [ ] Update Conductor.setup() to initialize new components
- [ ] Implement run_research_stage() method
- [ ] Create research stage system prompt
- [ ] Update CLI to support --stage research

### Phase 4: Testing & Refinement (Week 2)
- [ ] Unit tests for each component
- [ ] Integration test with mock agents
- [ ] End-to-end test with real agents
- [ ] Documentation and examples

### Phase 5: Planning & Implementation Stages (Week 3+)
- [ ] Define action types for planning stage
- [ ] Define action types for implementation stage
- [ ] Implement stage-specific handlers
- [ ] Create stage-specific system prompts

## Example Execution Flow

### Turn 1
**LLM Output:**
```xml
<thought>
I need to understand the market landscape. Let me start by querying the market intelligence agent.
</thought>

<action type="query_agent">
<agent_id>market-intel-agent</agent_id>
<query>What is the current market size for AI-powered healthcare diagnostics?</query>
</action>

<action type="update_todo">
<operation>add</operation>
<item>Research competitive landscape</item>
</action>
```

**Execution:**
1. Parser extracts 2 actions
2. Handler executes QueryAgentAction → calls BinduClient → gets response
3. Handler executes UpdateTodoAction → adds to todo list
4. ExecutionResult returned with both responses

### Turn 2
**LLM Output:**
```xml
<thought>
The market size is $X billion. Now I need to understand the competitive landscape.
</thought>

<action type="update_scratchpad">
<content>Market size: $X billion, growing at Y% CAGR</content>
</action>

<action type="query_agent">
<agent_id>competitive-analysis-agent</agent_id>
<query>Who are the top 5 competitors in AI healthcare diagnostics?</query>
</action>
```

**Execution:**
1. Parser extracts 2 actions
2. Handler updates scratchpad
3. Handler queries competitive analysis agent
4. Both responses added to conversation history

### Turn N (Final)
**LLM Output:**
```xml
<thought>
I have gathered sufficient information about the market, competitors, and trends.
Time to summarize and finish the research stage.
</thought>

<action type="update_scratchpad">
<content>Key finding: Strong market opportunity with $X billion TAM and limited competition in the AI diagnostics space.</content>
</action>

<action type="finish_stage">
<message>Research stage complete</message>
<summary>
Market Analysis:
- TAM: $X billion
- Growth: Y% CAGR
- Key competitors: A, B, C
- Opportunity: AI-powered diagnostics for underserved segment
</summary>
</action>
```

**Execution:**
1. Scratchpad updated
2. FinishStageAction sets done=True
3. Research stage completes
4. Summary available for next stage

## Next Steps

1. **Review this architecture** with the team
2. **Decide on action format**: XML tags vs JSON blocks vs custom syntax
3. **Start with Phase 1**: Implement core action infrastructure
4. **Test with mock agents** before integrating real Bindu protocol
5. **Iterate based on feedback** from actual usage

## Questions to Resolve

1. **Action Format**: Should we use XML tags, JSON blocks, or a custom format?
2. **Error Handling**: How should we handle agent timeouts or failures?
3. **Context Management**: How much conversation history to include in each turn?
4. **Agent Selection**: Should LLM specify agent by ID or should we have an agent router?
5. **Parallel Actions**: Should we support executing multiple agent queries in parallel?

---

**Document Status**: Draft for Discussion
**Last Updated**: 2025-01-17
**Author**: Sapthame Team
