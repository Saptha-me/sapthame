"""Executes Saptami phases sequentially."""

import logging
from typing import Optional

from src.phases.research_phase import ResearchPhase
from src.phases.planning_phase import PlanningPhase
from src.phases.implementation_phase import ImplementationPhase
from src.discovery.agent_registry import AgentRegistry
from src.orchestrator.saptami_state import SaptamiState
from src.execution.entities.phase_result import PhaseResult

logger = logging.getLogger(__name__)


class PhaseExecutor:
    """Executes research, planning, and implementation phases sequentially."""
    
    def __init__(
        self,
        research_phase: ResearchPhase,
        planning_phase: PlanningPhase,
        implementation_phase: ImplementationPhase
    ):
        """Initialize phase executor.
        
        Args:
            research_phase: Research phase engine
            planning_phase: Planning phase engine
            implementation_phase: Implementation phase engine
        """
        self.research_phase = research_phase
        self.planning_phase = planning_phase
        self.implementation_phase = implementation_phase
    
    def execute(
        self,
        query: str,
        agent_registry: AgentRegistry,
        state: SaptamiState
    ) -> PhaseResult:
        """Execute all phases sequentially.
        
        Args:
            query: User query
            agent_registry: Registry of available agents
            state: Saptami state
            
        Returns:
            PhaseResult with outputs from all phases
        """
        state.query = query
        
        try:
            # Phase 1: Research
            logger.info("=" * 60)
            logger.info("🔍 PHASE 1: RESEARCH - Starting...")
            logger.info("=" * 60)
            state.current_phase = "research"
            research_output = self.research_phase.execute(query, agent_registry)
            state.research_summary = research_output
            logger.info("🔍 PHASE 1: RESEARCH - Complete\n")
            
            # Phase 2: Planning
            logger.info("=" * 60)
            logger.info("📋 PHASE 2: PLANNING - Starting...")
            logger.info("=" * 60)
            state.current_phase = "planning"
            plan_output = self.planning_phase.execute(research_output, agent_registry)
            state.execution_plan = plan_output
            logger.info("📋 PHASE 2: PLANNING - Complete\n")
            
            # Phase 3: Implementation
            logger.info("=" * 60)
            logger.info("⚙️  PHASE 3: IMPLEMENTATION - Starting...")
            logger.info("=" * 60)
            state.current_phase = "implementation"
            impl_output = self.implementation_phase.execute(plan_output, agent_registry)
            state.implementation_results = impl_output
            logger.info("⚙️  PHASE 3: IMPLEMENTATION - Complete\n")
            
            state.done = True
            
            return PhaseResult(
                success=True,
                summary=impl_output,
                research_output=research_output,
                plan_output=plan_output,
                implementation_output=impl_output
            )
            
        except Exception as e:
            logger.error(f"Error during phase execution: {e}", exc_info=True)
            return PhaseResult(
                success=False,
                summary="",
                research_output=state.research_summary or "",
                plan_output=state.execution_plan or "",
                implementation_output=state.implementation_results or "",
                error=str(e)
            )
