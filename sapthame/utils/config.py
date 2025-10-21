"""Configuration utilities for Saptami CLI."""

import json
from pathlib import Path
from typing import Dict, Optional

from sapthame.utils.logging import get_logger

logger = get_logger("sapthame.utils.config")


class AgentConfig:
    """Agent configuration loader."""
    
    def __init__(self, name: str, config_path: str):
        self.name = name
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load agent configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Agent config not found: {self.config_path}")
        
        with open(self.config_path) as f:
            return json.load(f)
    
    @property
    def url(self) -> str:
        """Get agent URL from config."""
        return self.config.get("url", "")


class RunConfig:
    """Configuration for a saptami run."""
    
    def __init__(
        self,
        run_id: str,
        stage: str,
        client_question: str,
        agents: Dict[str, AgentConfig],
        plan_in: Optional[Path] = None,
        plan_out: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        concurrency: int = 1,
        deadline_sec: Optional[int] = None,
    ):
        self.run_id = run_id
        self.stage = stage
        self.client_question = client_question
        self.agents = agents
        self.plan_in = plan_in
        self.plan_out = plan_out
        self.output_dir = output_dir or Path(f"./runs/{run_id}")
        self.concurrency = concurrency
        self.deadline_sec = deadline_sec
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_metadata(self):
        """Save run metadata to output directory."""
        metadata = {
            "run_id": self.run_id,
            "stage": self.stage,
            "client_question": self.client_question,
            "agents": {name: str(agent.config_path) for name, agent in self.agents.items()},
            "plan_in": str(self.plan_in) if self.plan_in else None,
            "plan_out": str(self.plan_out) if self.plan_out else None,
            "concurrency": self.concurrency,
            "deadline_sec": self.deadline_sec,
        }
        
        metadata_path = self.output_dir / "run_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved run metadata to {metadata_path}")
    
    def get_agent_urls(self) -> list[str]:
        """Get list of agent URLs."""
        return [agent.url for agent in self.agents.values()]
