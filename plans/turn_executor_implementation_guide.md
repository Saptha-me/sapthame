# Turn Executor Implementation Guide

## Overview

Step-by-step guide for implementing turn-based executor for Sapthame's research stage.

## Directory Structure

```
sapthame/
├── orchestrator/
│   ├── actions/
│   │   ├── entities/
│   │   │   └── actions.py
│   │   ├── parser.py
│   │   └── handler.py
│   ├── entities/
│   │   └── execution_result.py
│   ├── state_managers/
│   │   ├── scratchpad.py
│   │   └── todo.py
│   └── turn_executor.py (update existing)
```

## Implementation Steps

### 1. Create Action Types
File: `sapthame/orchestrator/actions/entities/actions.py`
- QueryAgentAction
- UpdateScratchpadAction  
- UpdateTodoAction
- FinishStageAction

### 2. Create ExecutionResult
File: `sapthame/orchestrator/entities/execution_result.py`
- Captures actions executed, responses, errors, completion status

### 3. Create ActionParser
File: `sapthame/orchestrator/actions/parser.py`
- Parse XML action blocks from LLM output
- Extract action parameters
- Return actions + parsing errors

### 4. Create State Managers
Files: `sapthame/orchestrator/state_managers/scratchpad.py` and `todo.py`
- ScratchpadManager: append/replace/clear operations
- TodoManager: add/complete/remove operations

### 5. Create ActionHandler
File: `sapthame/orchestrator/actions/handler.py`
- Execute QueryAgentAction via BinduClient
- Execute state manager actions
- Track agent trajectories

### 6. Update TurnExecutor
File: `sapthame/orchestrator/turn_executor.py`
- Use ActionParser to parse LLM output
- Use ActionHandler to execute actions
- Return ExecutionResult

### 7. Update Conductor
File: `sapthame/orchestrator/conductor.py`
- Initialize state managers in setup()
- Initialize action parser/handler/executor
- Add run_research_stage() method

## Key Patterns from Reference Code

### TurnExecutor Pattern
```python
class TurnExecutor:
    def __init__(self, action_parser, action_handler):
        self.action_parser = action_parser
        self.action_handler = action_handler
    
    def execute(self, llm_output: str) -> ExecutionResult:
        actions, errors, found = self.action_parser.parse_response(llm_output)
        # Execute each action
        # Return ExecutionResult
```

### Conductor Pattern
```python
class Conductor:
    def setup(self, agent_urls):
        self.action_parser = ActionParser()
        self.action_handler = ActionHandler(...)
        self.executor = TurnExecutor(
            action_parser=self.action_parser,
            action_handler=self.action_handler
        )
    
    def execute_turn(self, instruction, turn_num):
        user_message = self._build_prompt(...)
        llm_response = self._get_llm_response(user_message)
        result = self.executor.execute(llm_response)
        # Track in conversation history
        return result
```

## Action Format (XML)

```xml
<action type="query_agent">
<agent_id>market-intel-agent</agent_id>
<query>What is the market size?</query>
</action>

<action type="update_scratchpad">
<content>Market size: $50B</content>
<operation>append</operation>
</action>

<action type="finish_stage">
<message>Research complete</message>
<summary>Comprehensive findings...</summary>
</action>
```

## CLI Integration

```bash
saptami run \
  --stage research \
  --id vc_research \
  --client-question "Market opportunity for AI diagnostics?" \
  --agent market=./agents/market-intel-agent.get-info.json \
  --max-turns 20
```

## Testing Strategy

1. Unit test each component independently
2. Mock BinduClient for action handler tests
3. Integration test with mock agents
4. End-to-end test with real agents

## Next Steps

1. Review architecture documents
2. Create directory structure
3. Implement Phase 1 (core infrastructure)
4. Test with mocks
5. Integrate with real Bindu protocol
6. Iterate based on usage
