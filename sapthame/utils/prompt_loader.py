"""Prompt loading utilities."""

from pathlib import Path
from logging import getLogger


logger = getLogger(__name__)


def load_prompt_from_file(file_path: Path) -> str:
    """Load prompt from markdown file.
    
    Args:
        file_path: Path to prompt file
        
    Returns:
        Prompt content
    """
    try:
        logger.info(f"Loading prompt from {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {file_path}")
        raise
