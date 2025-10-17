#!/usr/bin/env python3
"""Saptami CLI - Multi-stage agent orchestration.

Usage:
    saptami run --stage research --id <run_id> --client-question "<question>" --agent <name>=<path> [--concurrency N] [--deadline-sec N] [--out <dir>]
    saptami run --stage plan --id <run_id> --plan-in <path> --plan-out <path> --client-question "<question>"
    saptami run --stage implement --id <run_id> --plan-in <path> --agent <name>=<path> [--out <dir>]
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from sapthame.orchestrator.conductor import Conductor
from sapthame.utils.logging import get_logger

console = Console()
logger = get_logger("sapthame.cli")


class AgentConfig:
    """Agent configuration from command line."""
    
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
        
        # Create output directory
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


def parse_agent_args(agent_args: List[str]) -> Dict[str, AgentConfig]:
    """Parse agent arguments from command line.
    
    Args:
        agent_args: List of "name=path" strings
        
    Returns:
        Dictionary mapping agent names to AgentConfig objects
    """
    agents = {}
    for arg in agent_args:
        if "=" not in arg:
            raise ValueError(f"Invalid agent argument: {arg}. Expected format: name=path")
        
        name, path = arg.split("=", 1)
        agents[name] = AgentConfig(name, path)
    
    return agents


def run_research_stage(config: RunConfig) -> Dict:
    """Execute research stage.
    
    Args:
        config: Run configuration
        
    Returns:
        Research results
    """
    console.print(Panel.fit(
        f"[bold cyan]Research Stage[/bold cyan]\n"
        f"Run ID: {config.run_id}\n"
        f"Question: {config.client_question}\n"
        f"Agents: {', '.join(config.agents.keys())}\n"
        f"Concurrency: {config.concurrency}",
        border_style="cyan"
    ))
    
    # Get agent URLs
    agent_urls = [agent.url for agent in config.agents.values()]
    
    # Initialize conductor
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing conductor...", total=None)
        
        conductor = Conductor(
            system_message_path=None,  # Will use default research prompt
            model="claude-sonnet-4-5-20250929",
            temperature=0.0,
        )
        
        progress.update(task, description="Discovering agents...")
        conductor.setup(agent_urls=agent_urls, logging_dir=config.output_dir)
        
        progress.update(task, description="Executing research phase...")
        result = conductor.execute(config.client_question)
    
    # Save results
    results_path = config.output_dir / "research_results.json"
    with open(results_path, "w") as f:
        json.dump(result, f, indent=2)
    
    console.print(f"\n[green]✓[/green] Research complete. Results saved to {results_path}")
    
    # Display summary
    if result.get("success"):
        console.print(Panel(
            result.get("research_output", "No output"),
            title="Research Summary",
            border_style="green"
        ))
    else:
        console.print(f"[red]Error:[/red] {result.get('error', 'Unknown error')}")
    
    return result


def run_plan_stage(config: RunConfig) -> Dict:
    """Execute planning stage.
    
    Args:
        config: Run configuration
        
    Returns:
        Planning results
    """
    console.print(Panel.fit(
        f"[bold yellow]Planning Stage[/bold yellow]\n"
        f"Run ID: {config.run_id}\n"
        f"Question: {config.client_question}\n"
        f"Plan Input: {config.plan_in}\n"
        f"Plan Output: {config.plan_out}",
        border_style="yellow"
    ))
    
    # Read existing plan if provided
    existing_plan = None
    if config.plan_in and config.plan_in.exists():
        with open(config.plan_in) as f:
            existing_plan = f.read()
        console.print(f"[dim]Loaded existing plan from {config.plan_in}[/dim]")
    
    # Initialize conductor
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing conductor...", total=None)
        
        conductor = Conductor(
            system_message_path=None,  # Will use default planning prompt
            model="claude-sonnet-4-5-20250929",
            temperature=0.0,
        )
        
        # For planning, we don't need agents but we need to set up the conductor
        progress.update(task, description="Setting up planning phase...")
        conductor.setup(agent_urls=[], logging_dir=config.output_dir)
        
        # Construct planning query
        query = f"{config.client_question}\n\n"
        if existing_plan:
            query += f"Existing Plan:\n{existing_plan}\n\n"
        query += "Please create or update the implementation plan."
        
        progress.update(task, description="Executing planning phase...")
        result = conductor.execute(query)
    
    # Save plan to output file
    if config.plan_out:
        config.plan_out.parent.mkdir(parents=True, exist_ok=True)
        with open(config.plan_out, "w") as f:
            f.write(result.get("plan_output", ""))
        console.print(f"\n[green]✓[/green] Plan saved to {config.plan_out}")
    
    # Save full results
    results_path = config.output_dir / "plan_results.json"
    with open(results_path, "w") as f:
        json.dump(result, f, indent=2)
    
    console.print(f"[green]✓[/green] Planning complete. Results saved to {results_path}")
    
    # Display summary
    if result.get("success"):
        console.print(Panel(
            result.get("plan_output", "No output")[:500] + "...",
            title="Plan Preview",
            border_style="yellow"
        ))
    else:
        console.print(f"[red]Error:[/red] {result.get('error', 'Unknown error')}")
    
    return result


def run_implement_stage(config: RunConfig) -> Dict:
    """Execute implementation stage.
    
    Args:
        config: Run configuration
        
    Returns:
        Implementation results
    """
    console.print(Panel.fit(
        f"[bold green]Implementation Stage[/bold green]\n"
        f"Run ID: {config.run_id}\n"
        f"Plan: {config.plan_in}\n"
        f"Agents: {', '.join(config.agents.keys())}",
        border_style="green"
    ))
    
    # Read plan
    if not config.plan_in or not config.plan_in.exists():
        console.print(f"[red]Error:[/red] Plan file not found: {config.plan_in}")
        return {"success": False, "error": "Plan file not found"}
    
    with open(config.plan_in) as f:
        plan = f.read()
    
    # Get agent URLs
    agent_urls = [agent.url for agent in config.agents.values()]
    
    # Initialize conductor
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing conductor...", total=None)
        
        conductor = Conductor(
            system_message_path=None,  # Will use default implementation prompt
            model="claude-sonnet-4-5-20250929",
            temperature=0.0,
        )
        
        progress.update(task, description="Discovering agents...")
        conductor.setup(agent_urls=agent_urls, logging_dir=config.output_dir)
        
        # Construct implementation query
        query = f"Execute the following plan:\n\n{plan}"
        
        progress.update(task, description="Executing implementation phase...")
        result = conductor.execute(query)
    
    # Save results
    results_path = config.output_dir / "implementation_results.json"
    with open(results_path, "w") as f:
        json.dump(result, f, indent=2)
    
    console.print(f"\n[green]✓[/green] Implementation complete. Results saved to {results_path}")
    
    # Display summary
    if result.get("success"):
        console.print(Panel(
            result.get("implementation_output", "No output"),
            title="Implementation Summary",
            border_style="green"
        ))
    else:
        console.print(f"[red]Error:[/red] {result.get('error', 'Unknown error')}")
    
    return result


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Saptami - Multi-stage agent orchestration system."""
    pass


@cli.command()
@click.option("--id", "run_id", required=True, help="Unique run identifier")
@click.option("--stage", required=True, type=click.Choice(["research", "plan", "implement"]), help="Stage to execute")
@click.option("--client-question", required=True, help="Client question or task description")
@click.option("--agent", "agent_args", multiple=True, help="Agent configuration: name=path/to/config.json")
@click.option("--plan-in", type=click.Path(exists=False), help="Input plan file path (for plan/implement stages)")
@click.option("--plan-out", type=click.Path(exists=False), help="Output plan file path (for plan stage)")
@click.option("--out", "output_dir", type=click.Path(exists=False), help="Output directory for results")
@click.option("--concurrency", default=1, type=int, help="Number of concurrent agent calls")
@click.option("--deadline-sec", type=int, help="Deadline in seconds for execution")
def run(
    run_id: str,
    stage: str,
    client_question: str,
    agent_args: tuple,
    plan_in: Optional[str],
    plan_out: Optional[str],
    output_dir: Optional[str],
    concurrency: int,
    deadline_sec: Optional[int],
):
    """Run a saptami orchestration stage."""
    try:
        # Parse agent configurations
        agents = parse_agent_args(list(agent_args)) if agent_args else {}
        
        # Validate stage-specific requirements
        if stage == "research" and not agents:
            console.print("[red]Error:[/red] Research stage requires at least one agent (--agent)")
            sys.exit(1)
        
        if stage == "plan" and not plan_out:
            console.print("[red]Error:[/red] Plan stage requires --plan-out")
            sys.exit(1)
        
        if stage == "implement" and not plan_in:
            console.print("[red]Error:[/red] Implement stage requires --plan-in")
            sys.exit(1)
        
        if stage == "implement" and not agents:
            console.print("[red]Error:[/red] Implement stage requires at least one agent (--agent)")
            sys.exit(1)
        
        # Create run configuration
        config = RunConfig(
            run_id=run_id,
            stage=stage,
            client_question=client_question,
            agents=agents,
            plan_in=Path(plan_in) if plan_in else None,
            plan_out=Path(plan_out) if plan_out else None,
            output_dir=Path(output_dir) if output_dir else None,
            concurrency=concurrency,
            deadline_sec=deadline_sec,
        )
        
        # Save metadata
        config.save_metadata()
        
        # Execute stage
        if stage == "research":
            result = run_research_stage(config)
        elif stage == "plan":
            result = run_plan_stage(config)
        elif stage == "implement":
            result = run_implement_stage(config)
        else:
            console.print(f"[red]Error:[/red] Unknown stage: {stage}")
            sys.exit(1)
        
        # Exit with appropriate code
        sys.exit(0 if result.get("success") else 1)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        logger.exception("CLI execution failed")
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
