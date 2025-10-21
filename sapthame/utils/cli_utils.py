"""CLI utilities for Saptami - UI display and validation."""

from typing import Dict, List
from rich.console import Console
from rich.panel import Panel

from sapthame.utils.config import AgentConfig, RunConfig


class CliDisplay:
    """Handles Rich console display for CLI."""
    
    def __init__(self, console: Console):
        self.console = console
    
    def show_stage_header(self, config: RunConfig):
        """Display stage header based on configuration."""
        stage_config = {
            "research": {
                "title": "Research Stage",
                "color": "cyan",
                "fields": [
                    f"Run ID: {config.run_id}",
                    f"Question: {config.client_question}",
                    f"Agents: {', '.join(config.agents.keys())}",
                    f"Concurrency: {config.concurrency}",
                ]
            },
            "plan": {
                "title": "Planning Stage",
                "color": "yellow",
                "fields": [
                    f"Run ID: {config.run_id}",
                    f"Question: {config.client_question}",
                    f"Plan Input: {config.plan_in}",
                    f"Plan Output: {config.plan_out}",
                ]
            },
            "implement": {
                "title": "Implementation Stage",
                "color": "green",
                "fields": [
                    f"Run ID: {config.run_id}",
                    f"Plan: {config.plan_in}",
                    f"Agents: {', '.join(config.agents.keys())}",
                ]
            }
        }
        
        stage = stage_config.get(config.stage)
        if stage:
            content = f"[bold {stage['color']}]{stage['title']}[/bold {stage['color']}]\n"
            content += "\n".join(stage['fields'])
            self.console.print(Panel.fit(content, border_style=stage['color']))
    
    def show_success(self, message: str, results_path: str):
        """Display success message."""
        self.console.print(f"\n[green]✓[/green] {message}. Results saved to {results_path}")
    
    def show_error(self, error: str):
        """Display error message."""
        self.console.print(f"[red]Error:[/red] {error}")
    
    def show_result_summary(self, stage: str, result: Dict):
        """Display result summary based on stage."""
        if not result.get("success"):
            self.show_error(result.get("error", "Unknown error"))
            return
        
        summaries = {
            "research": {
                "title": "Research Summary",
                "color": "green",
                "key": "research_output",
            },
            "plan": {
                "title": "Plan Preview",
                "color": "yellow",
                "key": "plan_output",
                "truncate": 500,
            },
            "implement": {
                "title": "Implementation Summary",
                "color": "green",
                "key": "implementation_output",
            }
        }
        
        summary = summaries.get(stage)
        if summary:
            output = result.get(summary["key"], "No output")
            if summary.get("truncate"):
                output = output[:summary["truncate"]] + "..."
            
            self.console.print(Panel(
                output,
                title=summary["title"],
                border_style=summary["color"]
            ))
    
    def show_info(self, message: str):
        """Display info message."""
        self.console.print(f"[dim]{message}[/dim]")


def parse_agent_args(agent_args: List[str]) -> Dict[str, AgentConfig]:
    """Parse agent arguments from command line.
    
    Args:
        agent_args: List of "name=path" strings
        
    Returns:
        Dictionary mapping agent names to AgentConfig objects
        
    Raises:
        ValueError: If agent argument format is invalid
    """
    agents = {}
    for arg in agent_args:
        if "=" not in arg:
            raise ValueError(f"Invalid agent argument: {arg}. Expected format: name=path")
        
        name, path = arg.split("=", 1)
        agents[name] = AgentConfig(name, path)
    
    return agents


def validate_stage_requirements(stage: str, agents: Dict, plan_in: str, plan_out: str) -> tuple[bool, str]:
    """Validate stage-specific requirements.
    
    Args:
        stage: Stage name
        agents: Agent configurations
        plan_in: Input plan path
        plan_out: Output plan path
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if stage == "research" and not agents:
        return False, "Research stage requires at least one agent (--agent)"
    
    if stage == "plan" and not plan_out:
        return False, "Plan stage requires --plan-out"
    
    if stage == "implement" and not plan_in:
        return False, "Implement stage requires --plan-in"
    
    if stage == "implement" and not agents:
        return False, "Implement stage requires at least one agent (--agent)"
    
    return True, ""
