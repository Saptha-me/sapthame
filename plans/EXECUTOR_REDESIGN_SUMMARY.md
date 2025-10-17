# Executor Redesign Summary

## What We're Changing

### Current: Phase-Based Executor
```python
self.executor = Executor(
    research_phase=research_phase,
    planning_phase=planning_phase,
    implementation_phase=implementation_phase
)
```

**Problem**: Single-pass execution, no iterative refinement, can't explore before committing.

### Proposed: Turn-Based Executor
```python
self.executor = TurnExecutor(
    action_parser=action_parser,
    action_handler=action_handler
)
```

**Benefit**: Iterative, exploratory, transparent, follows open-source philosophy.

## Key Inspiration

From [multi-agent-coding-system](https://github.com/Danau5tin/multi-agent-coding-system):

1. **Stateless TurnExecutor**: Executes one turn at a time
2. **Action-based**: LLM outputs structured actions (XML/JSON)
3. **ActionParser**: Extracts actions from LLM output
4. **ActionHandler**: Executes actions (query agents, update state, etc.)
5. **ExecutionResult**: Returns what happened in the turn

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Conductor                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              run_research_stage()                      │  │
│  │  Loop: while not done and turns < max_turns           │  │
│  │    1. Build prompt with current state                 │  │
│  │    2. Get LLM response                                │  │
│  │    3. executor.execute(llm_response)                  │  │
│  │    4. Track in conversation history                   │  │
│  │    5. Check if done                                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   TurnExecutor                         │  │
│  │  execute(llm_output: str) -> ExecutionResult          │  │
│  │    1. Parse actions from LLM output                   │  │
│  │    2. Execute each action                             │  │
│  │    3. Return ExecutionResult                          │  │
│  └───────────────────────────────────────────────────────┘  │
│           ↓                              ↓                   │
│  ┌──────────────────┐         ┌──────────────────────────┐  │
│  │  ActionParser    │         │    ActionHandler         │  │
│  │  - Parse XML     │         │  - QueryAgentAction      │  │
│  │  - Extract       │         │  - UpdateScratchpad      │  │
│  │    actions       │         │  - UpdateTodo            │  │
│  │  - Return list   │         │  - FinishStage           │  │
│  └──────────────────┘         └──────────────────────────┘  │
│                                         ↓                    │
│                               ┌──────────────────────────┐  │
│                               │    BinduClient           │  │
│                               │  - send_message()        │  │
│                               │  - wait_for_task()       │  │
│                               └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Action Types for Research Stage

### 1. QueryAgentAction
Query a research agent via Bindu protocol.

```xml
<action type="query_agent">
<agent_id>market-intel-agent</agent_id>
<query>What is the market size?</query>
</action>
```

### 2. UpdateScratchpadAction
Organize findings in scratchpad.

```xml
<action type="update_scratchpad">
<content>Market size: $50B, growing 25% CAGR</content>
<operation>append</operation>
</action>
```

### 3. UpdateTodoAction
Track remaining research tasks.

```xml
<action type="update_todo">
<item>Research competitive landscape</item>
<operation>add</operation>
</action>
```

### 4. FinishStageAction
Complete the research stage.

```xml
<action type="finish_stage">
<message>Research complete</message>
<summary>Comprehensive research findings...</summary>
</action>
```

## Example Execution Flow

### Turn 1
```
LLM: "Let me start by understanding market size"
Action: QueryAgent(market-intel-agent, "What is market size?")
Response: "$50B market, 25% CAGR"
```

### Turn 2
```
LLM: "Interesting growth. What drives it?"
Action: QueryAgent(market-intel-agent, "What drives 25% growth?")
Response: "Aging population, radiologist shortage, AI accuracy"
Action: UpdateScratchpad("Key drivers: aging, shortage, accuracy")
```

### Turn 3
```
LLM: "Radiologist shortage is interesting. Let me explore"
Action: QueryAgent(market-intel-agent, "How severe is radiologist shortage?")
Response: "30% shortage in US, 50% in rural areas"
Action: UpdateTodo("Research rural market opportunity")
```

### Turn N
```
LLM: "I have comprehensive understanding. Time to finish"
Action: UpdateScratchpad("Key finding: $5B rural opportunity")
Action: FinishStage(
  message="Research complete",
  summary="Market: $50B, 25% CAGR. Key opportunity: $5B rural market..."
)
```

## State Management

### Scratchpad
- Temporary notes and findings
- Operations: append, replace, clear
- Included in LLM prompt each turn

### Todo List
- Track remaining research questions
- Operations: add, complete, remove
- Helps LLM stay organized

### Conversation History
- Full record of all turns
- LLM output + actions + responses
- Audit trail for transparency

## CLI Usage

```bash
saptami run \
  --stage research \
  --id vc_research \
  --client-question "What is the market opportunity for AI healthcare diagnostics?" \
  --agent market=./agents/market-intel-agent.get-info.json \
  --agent competitive=./agents/competitive-analysis-agent.get-info.json \
  --max-turns 20
```

## Implementation Files

### New Files to Create
```
sapthame/orchestrator/actions/entities/actions.py
sapthame/orchestrator/actions/parser.py
sapthame/orchestrator/actions/handler.py
sapthame/orchestrator/entities/execution_result.py
sapthame/orchestrator/state_managers/scratchpad.py
sapthame/orchestrator/state_managers/todo.py
```

### Files to Update
```
sapthame/orchestrator/conductor.py
  - Update setup() to initialize new components
  - Add run_research_stage() method

sapthame/orchestrator/turn_executor.py
  - Already exists, needs adaptation to new pattern

sapthame/orchestrator/turn.py
  - Already exists, compatible with new pattern
```

## Benefits

### 1. Iterative Research
- Query agents multiple times
- Refine questions based on responses
- Explore tangents and return

### 2. Transparency
- Every turn logged with actions and responses
- Clear audit trail
- Easy to debug

### 3. Flexibility
- Easy to add new action types
- LLM decides execution strategy
- Can adapt mid-execution

### 4. Open Source Philosophy
- "Explore, discuss, research, plan" before coding
- Inspectable decision-making
- Community can understand and contribute

## Next Steps

1. **Review** these documents with team
2. **Decide** on action format (XML vs JSON)
3. **Implement** Phase 1: Core infrastructure
4. **Test** with mock agents
5. **Integrate** with real Bindu protocol
6. **Iterate** based on usage

## Documents Created

1. **turn_executor_architecture.md** - Detailed architecture design
2. **turn_vs_phase_comparison.md** - Comparison of approaches
3. **turn_executor_implementation_guide.md** - Step-by-step implementation
4. **EXECUTOR_REDESIGN_SUMMARY.md** - This summary

## Questions to Resolve

1. **Action Format**: XML (as shown) or JSON blocks?
2. **Error Handling**: How to handle agent timeouts?
3. **Context Window**: How much history to include?
4. **Parallel Actions**: Support multiple agent queries in parallel?
5. **Stage Transitions**: How to move from research → planning → implementation?

---

**Status**: Ready for discussion and implementation
**Estimated Effort**: 2-3 weeks for full implementation
**Priority**: High (enables core open-source workflow)
