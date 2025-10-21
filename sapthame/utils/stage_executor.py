"""Stage execution logic for Saptami CLI."""

import json
from pathlib import Path
from typing import Dict, Optional, Callable

from sapthame.orchestrator.conductor import Conductor
from sapthame.utils.config import RunConfig
from sapthame.utils.logging import get_logger

logger = get_logger("sapthame.utils.stage_executor")


class StageExecutor:
    """Executes orchestration stages."""
    
    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.0,
    ):
        self.model = model
        self.temperature = temperature
    
    def _create_conductor(self) -> Conductor:
        """Create a conductor instance."""
        return Conductor(
            system_message_path=None,
            model=self.model,
            temperature=self.temperature,
        )
    
    def _save_results(self, results: Dict, output_path: Path):
        """Save results to JSON file."""
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved results to {output_path}")
    
    def _prepare_query_research(self, config: RunConfig) -> str:
        """Prepare query for research stage."""
        return config.client_question
    
    def _prepare_query_plan(self, config: RunConfig) -> str:
        """Prepare query for planning stage."""
        query = f"{config.client_question}\n\n"
        if config.plan_in and config.plan_in.exists():
            with open(config.plan_in) as f:
                query += f"Existing Plan:\n{f.read()}\n\n"
        query += "Please create or update the implementation plan."
        return query
    
    def _prepare_query_implement(self, config: RunConfig) -> str:
        """Prepare query for implementation stage."""
        if not config.plan_in or not config.plan_in.exists():
            raise FileNotFoundError("Plan file not found")
        
        with open(config.plan_in) as f:
            return f"Execute the following plan:\n\n{f.read()}"
    
    def _post_process_plan(self, config: RunConfig, result: Dict):
        """Save plan output to file."""
        if config.plan_out and result.get("plan_output"):
            config.plan_out.parent.mkdir(parents=True, exist_ok=True)
            with open(config.plan_out, "w") as f:
                f.write(result["plan_output"])
    
    def _execute_stage(
        self,
        stage: str,
        config: RunConfig,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict:
        """Generic stage execution logic."""
        try:
            query_preparers = {
                "research": self._prepare_query_research,
                "plan": self._prepare_query_plan,
                "implement": self._prepare_query_implement,
            }
            
            agent_urls = config.get_agent_urls() if stage != "plan" else []
            query = query_preparers[stage](config)
            
            conductor = self._create_conductor()
            
            if progress_callback:
                progress_callback(f"Setting up {stage} phase...")
            conductor.setup(agent_urls=agent_urls, logging_dir=config.output_dir)
            
            if progress_callback:
                progress_callback(f"Executing {stage} phase...")
            result = conductor.execute(query)
            
            if stage == "plan":
                self._post_process_plan(config, result)
            
            results_path = config.output_dir / f"{stage}_results.json"
            self._save_results(result, results_path)
            
            return result
            
        except FileNotFoundError as e:
            return {"success": False, "error": str(e)}
    
    def execute_research(
        self,
        config: RunConfig,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict:
        """Execute research stage."""
        return self._execute_stage("research", config, progress_callback)
    
    def execute_plan(
        self,
        config: RunConfig,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict:
        """Execute planning stage."""
        return self._execute_stage("plan", config, progress_callback)
    
    def execute_implement(
        self,
        config: RunConfig,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict:
        """Execute implementation stage."""
        return self._execute_stage("implement", config, progress_callback)
