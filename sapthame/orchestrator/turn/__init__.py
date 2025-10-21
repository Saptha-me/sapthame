# |---------------------------------------------------------------|
# |                                                               |
# |                  Give Feedback / Get Help                     |
# |    https://github.com/Saptha-me/sapthame/issues/new/choose    |
# |                                                               |
# |---------------------------------------------------------------|
#
#  Thank you users! We ❤️ you! - 🌻

"""
Turn-based execution components for the Sapthame Conductor.

This module provides the following components:

1. Turn: Represents a single turn in the conversation history. Each turn encapsulates the LLM's output, 
   the list of actions executed, environment responses received, and optional subagent trajectories. 
   Provides serialization to both dictionary format (for structured logging) and prompt format (for 
   context injection with automatic truncation of long outputs).

2. TurnExecutor: Stateless executor for single-turn agent execution with state management. Parses actions 
   from LLM output, executes them sequentially through the action handler, collects environment responses, 
   and tracks completion status. Handles parsing errors gracefully and supports finish actions to signal 
   stage completion. Returns an ExecutionResult containing all execution details and agent trajectories.
"""

from .turn import Turn
from .turn_executor import TurnExecutor

__all__ = ["Turn", "TurnExecutor"]
