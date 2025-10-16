"""Prompt loading utilities."""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def load_prompt_from_file(file_path: Path) -> str:
    """Load prompt from markdown file.
    
    Args:
        file_path: Path to prompt file
        
    Returns:
        Prompt content
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {file_path}")
        raise


def load_research_prompt() -> str:
    """Load research phase prompt.
    
    Returns:
        Research prompt content
    """
    prompt_path = Path(__file__).parent.parent / "system_msgs" / "research_prompt.md"
    return load_prompt_from_file(prompt_path)


def load_planning_prompt() -> str:
    """Load planning phase prompt.
    
    Returns:
        Planning prompt content
    """
    prompt_path = Path(__file__).parent.parent / "system_msgs" / "planning_prompt.md"
    return load_prompt_from_file(prompt_path)


def load_implementation_prompt() -> str:
    """Load implementation phase prompt.
    
    Returns:
        Implementation prompt content
    """
    prompt_path = Path(__file__).parent.parent / "system_msgs" / "implementation_prompt.md"
    return load_prompt_from_file(prompt_path)
