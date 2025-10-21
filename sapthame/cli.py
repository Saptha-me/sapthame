# |---------------------------------------------------------------|
# |                                                               |
# |                  Give Feedback / Get Help                     |
# |    https://github.com/Saptha-me/sapthame/issues/new/choose    |
# |                                                               |
# |---------------------------------------------------------------|
#
#  Thank you users! We ❤️ you! - 🌻

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


from .utils.cli_utils import CliDisplay, parse_agent_args, validate_stage_requirements
from .utils.config import RunConfig
from .utils.logging import get_logger
from .utils.stage_executor import StageExecutor

console = Console()
logger = get_logger("sapthame.cli")
display = CliDisplay(console)
executor = StageExecutor()


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
        agents = parse_agent_args(list(agent_args)) if agent_args else {}
        
        is_valid, error_msg = validate_stage_requirements(stage, agents, plan_in, plan_out)
        if not is_valid:
            display.show_error(error_msg)
            sys.exit(1)
        
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
        
        config.save_metadata()
        display.show_stage_header(config)
        
        if config.plan_in and config.plan_in.exists() and stage in ["plan", "implement"]:
            display.show_info(f"Loaded existing plan from {config.plan_in}")
        
        result = _execute_stage_with_progress(stage, config)
        
        results_file = f"{stage}_results.json"
        display.show_success(f"{stage.capitalize()} complete", str(config.output_dir / results_file))
        display.show_result_summary(stage, result)
        
        sys.exit(0 if result.get("success") else 1)
        
    except Exception as e:
        display.show_error(str(e))
        logger.exception("CLI execution failed")
        sys.exit(1)


def _execute_stage_with_progress(stage: str, config: RunConfig) -> dict:
    """Execute stage with progress indicator."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing...", total=None)
        
        def update_progress(description: str):
            progress.update(task, description=description)
        
        stage_executors = {
            "research": executor.execute_research,
            "plan": executor.execute_plan,
            "implement": executor.execute_implement,
        }
        
        execute_fn = stage_executors.get(stage)
        if not execute_fn:
            raise ValueError(f"Unknown stage: {stage}")
        
        return execute_fn(config, progress_callback=update_progress)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
