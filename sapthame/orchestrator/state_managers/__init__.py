# |---------------------------------------------------------------|
# |                                                               |
# |                  Give Feedback / Get Help                     |
# |    https://github.com/Saptha-me/sapthame/issues/new/choose    |
# |                                                               |
# |---------------------------------------------------------------|
#
#  Thank you users! We ❤️ you! - 🌻

"""
The detailed context management related components for the Sapthame Conductor.

This module provides the following components:

1. ConversationHistory: Maintains a rolling window of turn-based interactions between the Conductor and its environment. 
   Each turn captures the LLM's output, actions executed, environment responses, and subagent trajectories. It automatically 
   prunes history to the last 100 turns to prevent context explosion, and formats the history into prompts for the LLM to 
   maintain awareness of past interactions.

2. ScratchpadManager: Provides a temporary working memory for the Conductor to store intermediate findings, notes, and 
   insights during task execution. Supports append, replace, and clear operations. Acts as a persistent notepad across 
   turns where the agent can accumulate research findings, track insights, or maintain working hypotheses before 
   finalizing outputs.

3. State: The central orchestration state that tracks the entire execution lifecycle. Manages phase progression 
   (research → planning → implementation), stores phase outputs, tracks completion status, and maintains references to 
   the agent registry and conversation history. Provides serialization to both dictionary format (for logging) and 
   prompt format (for LLM context injection).

4. TodoManager: A task tracking system that maintains a list of pending and completed items. Each item has a text 
   description and completion status. Supports adding, completing, and removing items with index-based operations. 
   Formats the list with visual indicators (○ for pending, ✓ for completed) and provides a count of pending items 
   for progress tracking.

"""
from .conversation_history import ConversationHistory
from .scratchpad import ScratchpadManager
from .state import State
from .todo import TodoManager


__all__ = [
    "ConversationHistory", 
    "ScratchpadManager", 
    "State", 
    "TodoManager"]
